"""Payment controller for handling M-Pesa payments."""
import datetime
import uuid
from flask import request, jsonify, current_app
from functools import wraps
from firebase_admin import auth


def require_auth(f):
    """Decorator to require Firebase authentication."""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        print(f"[Auth] ========== Authentication Check ==========")
        print(f"[Auth] Endpoint: {request.endpoint}")
        print(f"[Auth] Method: {request.method}")
        print(f"[Auth] Headers: {dict(request.headers)}")
        
        try:
            db = current_app.config.get('DB')
            if db is None:
                print(f"[Auth] ❌ DB is None - Authentication service unavailable")
                return jsonify({'error': 'Authentication service unavailable'}), 503
            
            auth_header = request.headers.get('Authorization')
            print(f"[Auth] Authorization header: {auth_header[:30] + '...' if auth_header and len(auth_header) > 30 else auth_header}")
            
            if not auth_header or not auth_header.startswith('Bearer '):
                print(f"[Auth] ⚠️ No Bearer token found")
                # Allow unauth testing when enabled
                cfg = current_app.config.get('CONFIG')
                allow_test = getattr(cfg, 'ALLOW_UNAUTH_TEST', False)
                print(f"[Auth] ALLOW_UNAUTH_TEST: {allow_test}")
                
                if allow_test:
                    test_user = request.args.get('user_id')
                    if not test_user and request.is_json:
                        body = request.get_json(silent=True) or {}
                        test_user = body.get('user_id')
                    if test_user:
                        print(f"[Auth] ✅ Test mode: Using user_id={test_user}")
                        request.user_id = test_user
                        return f(*args, **kwargs)
                    else:
                        print(f"[Auth] ❌ Test mode enabled but no user_id provided")
                else:
                    print(f"[Auth] ❌ No token and test mode disabled")
                return jsonify({'error': 'No token provided'}), 401
            
            token = auth_header.split('Bearer ')[1]
            print(f"[Auth] Token extracted (length: {len(token)}, preview: {token[:20]}...)")
            
            try:
                print(f"[Auth] Verifying Firebase token...")
                decoded_token = auth.verify_id_token(token)
                user_id = decoded_token['uid']
                print(f"[Auth] ✅ Token verified successfully")
                print(f"[Auth] User ID: {user_id}")
                request.user_id = user_id
                return f(*args, **kwargs)
            except Exception as e:
                error_str = str(e)
                error_type = type(e).__name__
                print(f"[Auth] ❌ Token verification failed: {error_type}: {error_str}")
                
                # Handle clock skew errors (token used too early/late)
                # For small clock skews (1-5 seconds), wait and retry
                if 'clock' in error_str.lower() or 'too early' in error_str.lower() or 'too late' in error_str.lower():
                    print(f"[Auth] ⚠️ Clock skew detected, checking time difference...")
                    import re
                    time_match = re.search(r'(\d+) < (\d+)', error_str)
                    if time_match:
                        server_time = int(time_match.group(1))
                        token_time = int(time_match.group(2))
                        diff = abs(token_time - server_time)
                        print(f"[Auth] ⚠️ Time difference: {diff} seconds")
                        
                        if diff <= 5:  # Allow up to 5 seconds difference
                            print(f"[Auth] ⚠️ Small clock skew ({diff}s) detected, waiting {diff + 1} seconds and retrying...")
                            import time as time_module
                            time_module.sleep(diff + 1)  # Wait for the time difference + 1 second buffer
                            try:
                                print(f"[Auth] Retrying token verification after delay...")
                                decoded_token = auth.verify_id_token(token)
                                user_id = decoded_token['uid']
                                print(f"[Auth] ✅ Token verified after delay, User ID: {user_id}")
                                request.user_id = user_id
                                return f(*args, **kwargs)
                            except Exception as retry_error:
                                print(f"[Auth] ❌ Retry after delay also failed: {retry_error}")
                        else:
                            print(f"[Auth] ❌ Clock skew too large ({diff}s), rejecting token")
                    else:
                        print(f"[Auth] ⚠️ Clock skew detected but couldn't parse time difference, waiting 2 seconds and retrying...")
                        import time as time_module
                        time_module.sleep(2)
                        try:
                            decoded_token = auth.verify_id_token(token)
                            user_id = decoded_token['uid']
                            print(f"[Auth] ✅ Token verified after delay, User ID: {user_id}")
                            request.user_id = user_id
                            return f(*args, **kwargs)
                        except Exception as retry_error:
                            print(f"[Auth] ❌ Retry after delay failed: {retry_error}")
                
                import traceback
                print(f"[Auth] Traceback: {traceback.format_exc()}")
                return jsonify({'error': 'Invalid Firebase token', 'details': error_str}), 401
        except Exception as e:
            print(f"[Auth] ❌ Authentication service error: {type(e).__name__}: {str(e)}")
            import traceback
            print(f"[Auth] Traceback: {traceback.format_exc()}")
            return jsonify({'error': 'Authentication service error', 'details': str(e)}), 500
    
    return decorated_function


class PaymentController:
    """Controller for payment operations."""
    
    def __init__(self, db, mpesa_client, config):
        self.db = db
        self.mpesa_client = mpesa_client
        self.config = config
    
    def _format_phone_number(self, phone: str):
        """Validate and format phone number to E.164 format (2547xxxxxxxx or 2541xxxxxxxx)."""
        if not phone:
            return None
        
        cleaned = phone.strip().replace(" ", "").replace("-", "")
        
        # +2547xxxxxxxx or +2541xxxxxxxx (13 chars: +254 + 9 digits)
        if cleaned.startswith("+2547") and len(cleaned) == 13:
            return cleaned[1:]  # Remove +
        if cleaned.startswith("+2541") and len(cleaned) == 13:
            return cleaned[1:]  # Remove +
        
        # 2547xxxxxxxx or 2541xxxxxxxx (12 digits)
        if cleaned.startswith("2547") and len(cleaned) == 12:
            return cleaned
        if cleaned.startswith("2541") and len(cleaned) == 12:
            return cleaned
        
        # 07xxxxxxxx (10 digits) -> 2547xxxxxxxx
        if cleaned.startswith("07") and len(cleaned) == 10:
            return f"254{cleaned[1:]}"
        
        # 01xxxxxxxx (10 digits) -> 2541xxxxxxxx
        if cleaned.startswith("01") and len(cleaned) == 10:
            return f"254{cleaned[1:]}"
        
        return None
    
    def initiate_payment(self):
        """Initiate an M-Pesa STK push payment."""
        try:
            print("[mpesa_initiate] handler called")
            if self.mpesa_client is None:
                print("[mpesa_initiate] mpesa_client is None")
                return jsonify({'error': 'M-Pesa not configured'}), 503
        
            data = request.get_json(force=True) or {}
            amount = float(data.get('amount', 0))
            phone_raw = (data.get('phone') or '').strip()
            print(f"[mpesa_initiate] user_id={getattr(request, 'user_id', None)} amount={amount} phone_raw={phone_raw}")
            
            # Validate and format phone number
            phone = self._format_phone_number(phone_raw)
            if not phone:
                print(f"[mpesa_initiate] invalid phone format: {phone_raw}")
                return jsonify({
                    'error': 'Invalid phone number. Must start with +254, 254, 07, or 01'
                }), 400
            
            print(f"[mpesa_initiate] formatted phone: {phone}")
        
            if amount < self.config.VALIDATION_RULES.get('min_amount', 10.0):
                print(f"[mpesa_initiate] amount below minimum: {amount}")
                return jsonify({
                    'error': f"Minimum amount is KES {int(self.config.VALIDATION_RULES.get('min_amount', 10))}"
                }), 400
        
            # Enforce monthly cap
            user_id = request.user_id
            now = datetime.datetime.now(datetime.timezone.utc)
            month_key = now.strftime('%Y-%m')
            user_ref = self.db.reference(f'registeredUser/{user_id}')
            user_data = user_ref.get() or {}
            monthly = user_data.get('monthly_paid', {})
            month_spend = float(monthly.get(month_key, 0))
            remaining_cap = max(0.0, self.config.MONTHLY_CAP_KES - month_spend)
            print(f"[mpesa_initiate] month_spend={month_spend} remaining_cap={remaining_cap}")
        
            if remaining_cap <= 0:
                return jsonify({
                    'error': 'Monthly cap reached',
                    'cap': self.config.MONTHLY_CAP_KES,
                    'month': month_key
                }), 400
        
            if amount > remaining_cap:
                print(f"[mpesa_initiate] ❌ Amount {amount} exceeds remaining cap {remaining_cap}")
                return jsonify({
                    'error': f'Amount exceeds remaining monthly cap. Maximum payment: KES {int(remaining_cap)}',
                    'remaining': remaining_cap,
                    'requested': amount
                }), 400
        
            # Create payment record
            payment_id = str(uuid.uuid4())
            credit_days = int(amount / self.config.DAILY_RATE)
            payment_info = {
                'payment_id': payment_id,
                'user_id': user_id,
                'amount': amount,
                'credit_days': credit_days,
                'status': 'pending',
                'provider': 'mpesa',
                'created_at': datetime.datetime.now().isoformat()
            }
            self.db.reference(f'payments/{payment_id}').set(payment_info)
            print(f"[mpesa_initiate] payment created id={payment_id} credit_days={credit_days}")
        
            # Fire STK push
            description = 'KileKitabu Credits'
            print(f"[mpesa_initiate] initiating STK push -> amount={amount} phone={phone}")
            result = self.mpesa_client.initiate_stk_push(amount, phone, payment_id, description)
            print(f"[mpesa_initiate] STK response: {result}")
            if not result.get('ok'):
                return jsonify({'error': 'Failed to initiate M-Pesa', 'details': result}), 500
            
            # Store CheckoutRequestID for callback matching
            checkout_request_id = result.get('response', {}).get('CheckoutRequestID')
            if checkout_request_id:
                payment_ref = self.db.reference(f'payments/{payment_id}')
                payment_ref.update({'checkout_request_id': checkout_request_id})
                print(f"[mpesa_initiate] Stored CheckoutRequestID: {checkout_request_id}")
            
            return jsonify({
                'payment_id': payment_id,
                'status': 'pending',
                'credit_days': credit_days,
                'mpesa': result.get('response', {})
            })
        except Exception as e:
            import traceback
            print(f"[mpesa_initiate] ERROR: {e}")
            traceback.print_exc()
            return jsonify({'error': 'Internal server error', 'message': str(e)}), 500
    
    def handle_callback(self):
        """Handle M-Pesa STK push callback."""
        print(f"[mpesa_callback] ========== M-Pesa Callback Received ==========")
        print(f"[mpesa_callback] Request method: {request.method}")
        print(f"[mpesa_callback] Request headers: {dict(request.headers)}")
        
        try:
            payload = request.get_json(force=True) or {}
            print(f"[mpesa_callback] Raw payload keys: {list(payload.keys())}")
            
            stk = ((payload or {}).get('Body') or {}).get('stkCallback') or {}
            print(f"[mpesa_callback] STK callback keys: {list(stk.keys())}")
            
            result_code = stk.get('ResultCode')
            print(f"[mpesa_callback] ResultCode: {result_code} (type: {type(result_code)})")
            
            metadata_items = ((stk.get('CallbackMetadata') or {}).get('Item')) or []
            print(f"[mpesa_callback] Metadata items count: {len(metadata_items)}")
            
            # Extract amount and reference
            amount = None
            payment_id = None
            for item in metadata_items:
                name = item.get('Name')
                value = item.get('Value')
                print(f"[mpesa_callback] Metadata item: {name} = {value}")
                if name == 'Amount':
                    amount = float(value) if value else 0
                if name == 'AccountReference':
                    payment_id = value
            
            # M-Pesa doesn't return AccountReference in callback, use CheckoutRequestID instead
            checkout_request_id = stk.get('CheckoutRequestID')
            print(f"[mpesa_callback] Extracted - amount: {amount}, payment_id (AccountReference): {payment_id}, CheckoutRequestID: {checkout_request_id}")
            
            # Find payment by CheckoutRequestID (preferred) or AccountReference
            payment = None
            payment_id = None
            payment_ref = None
            
            if checkout_request_id:
                print(f"[mpesa_callback] Searching for payment by CheckoutRequestID: {checkout_request_id}")
                payments_ref = self.db.reference('payments')
                all_payments = payments_ref.get() or {}
                for pid, pdata in all_payments.items():
                    if pdata.get('checkout_request_id') == checkout_request_id:
                        print(f"[mpesa_callback] ✅ Found payment by CheckoutRequestID: {pid}")
                        payment = pdata
                        payment_id = pid
                        payment_ref = self.db.reference(f'payments/{pid}')
                        break
            
            # Fallback: try AccountReference if available and payment not found
            if not payment and payment_id:
                print(f"[mpesa_callback] Payment not found by CheckoutRequestID, trying AccountReference: {payment_id}")
                payment_ref = self.db.reference(f'payments/{payment_id}')
                payment = payment_ref.get()
                
                # If not found and payment_id is 12 chars, search for payments starting with this prefix
                if not payment and len(payment_id) == 12:
                    print(f"[mpesa_callback] Payment not found with exact ID, searching by prefix: {payment_id}")
                    payments_ref = self.db.reference('payments')
                    all_payments = payments_ref.get() or {}
                    for pid, pdata in all_payments.items():
                        if pid.startswith(payment_id):
                            print(f"[mpesa_callback] Found payment by prefix: {pid}")
                            payment = pdata
                            payment_id = pid
                            payment_ref = self.db.reference(f'payments/{pid}')
                            break
            
            print(f"[mpesa_callback] Payment record: {payment}")
            
            if not payment:
                print(f"[mpesa_callback] ❌ Payment not found - CheckoutRequestID: {checkout_request_id}, AccountReference: {payment_id}")
                return jsonify({'status': 'ignored', 'reason': 'payment_not_found'}), 200
            
            user_id = payment.get('user_id')
            print(f"[mpesa_callback] User ID: {user_id}")
            
            # Check if payment was already processed to prevent duplicate credit additions
            payment_status = payment.get('status', 'pending')
            if payment_status == 'completed':
                print(f"[mpesa_callback] ⚠️ Payment already processed (status: {payment_status}). Skipping credit update.")
                return jsonify({'status': 'ok', 'message': 'already_processed'}), 200
            
            user_ref = self.db.reference(f'registeredUser/{user_id}')
            user_data = user_ref.get() or {}
            print(f"[mpesa_callback] Current user data - credit_balance: {user_data.get('credit_balance')}, total_payments: {user_data.get('total_payments')}")
            
            if result_code == 0 or result_code == '0':
                print(f"[mpesa_callback] ✅ Payment successful (ResultCode: {result_code})")
                
                # Get credit_days from payment record (already calculated during initiation)
                # Fallback to recalculating if not stored
                stored_credit_days = payment.get('credit_days')
                payment_amount = float(payment.get('amount', 0))
                
                if stored_credit_days is not None:
                    credit_days = int(stored_credit_days)
                    print(f"[mpesa_callback] Using stored credit_days: {credit_days}")
                else:
                    # Fallback: recalculate if not stored
                    credit_days = int(payment_amount / self.config.DAILY_RATE)
                    print(f"[mpesa_callback] ⚠️ credit_days not stored, recalculated: {credit_days} (amount={payment_amount}, rate={self.config.DAILY_RATE})")
                
                # Get current credit balance (handle both int and float from Firebase)
                current_credit_raw = user_data.get('credit_balance', 0)
                if isinstance(current_credit_raw, float):
                    current_credit = int(current_credit_raw)
                elif isinstance(current_credit_raw, int):
                    current_credit = current_credit_raw
                else:
                    try:
                        current_credit = int(float(current_credit_raw))
                    except (ValueError, TypeError):
                        current_credit = 0
                
                new_credit = current_credit + credit_days
                
                print(f"[mpesa_callback] Credit calculation: current={current_credit}, adding={credit_days}, new={new_credit}")
                
                # Update monthly spend
                now = datetime.datetime.now(datetime.timezone.utc)
                month_key = now.strftime('%Y-%m')
                monthly = user_data.get('monthly_paid', {}) or {}
                month_spend = float(monthly.get(month_key, 0))
                month_spend += payment_amount
                monthly[month_key] = month_spend
                
                # Update user with credit and payment info
                # Store credit_balance as integer to match app expectations
                now_iso = datetime.datetime.now(datetime.timezone.utc).isoformat()
                update_data = {
                    'credit_balance': int(new_credit),  # Store as integer
                    'total_payments': float(user_data.get('total_payments', 0)) + payment_amount,
                    'monthly_paid': monthly,
                    'last_payment_date': now_iso,  # Prevent credit deduction on payment day
                    'updated_at': now_iso,
                }
                
                print(f"[mpesa_callback] Updating user with: {update_data}")
                user_ref.update(update_data)
                
                # Mark payment complete AFTER updating credits
                payment_ref.update({
                    'status': 'completed',
                    'provider_data': stk,
                    'completed_at': now_iso,
                    'credit_days_added': credit_days,  # Store for audit
                })
                
                print(f"[mpesa_callback] ✅ Payment completed: user_id={user_id}, amount={payment_amount}, credit_days={credit_days}, new_credit={new_credit}")
                
                # Verify the update was successful
                updated_user_data = user_ref.get() or {}
                verified_credit = updated_user_data.get('credit_balance')
                print(f"[mpesa_callback] ✅ Verified update - credit_balance: {verified_credit} (expected: {new_credit})")
                
                if verified_credit != new_credit:
                    print(f"[mpesa_callback] ⚠️ WARNING: Credit balance mismatch! Expected {new_credit}, got {verified_credit}")
                
                return jsonify({'status': 'ok'})
            else:
                print(f"[mpesa_callback] ❌ Payment failed (ResultCode: {result_code})")
                payment_ref.update({
                    'status': 'failed',
                    'provider_data': stk,
                    'completed_at': datetime.datetime.now().isoformat(),
                })
                return jsonify({'status': 'failed', 'result_code': result_code})
        except Exception as e:
            print(f"[mpesa_callback] ❌ Exception: {type(e).__name__}: {str(e)}")
            import traceback
            print(f"[mpesa_callback] Traceback: {traceback.format_exc()}")
            return jsonify({'status': 'error', 'message': str(e)}), 200

