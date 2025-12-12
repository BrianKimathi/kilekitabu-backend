"""Unified Checkout controller for both card and Google Pay payments."""
import datetime
import json
import uuid
from flask import request, jsonify, current_app
from controllers.subscription_controller import require_auth
from services.cybersource_helper_client import CyberSourceHelperError
from services.exchange_rate_service import convert_amount_to_kes, compute_credit_days_from_kes


@require_auth
def unified_checkout_capture_context():
    """Create a Unified Checkout capture context for both card and Google Pay."""
    import traceback
    try:
        print(f"[UC:CAPTURE_CONTEXT] ========== STEP 1: REQUEST RECEIVED ==========")
        print(f"[UC:CAPTURE_CONTEXT] Timestamp: {datetime.datetime.now(datetime.timezone.utc).isoformat()}")
        print(f"[UC:CAPTURE_CONTEXT] Request method: {request.method}")
        print(f"[UC:CAPTURE_CONTEXT] Request headers: {dict(request.headers)}")
        
        raw_payload = request.get_json(silent=True) or {}
        print(f"[UC:CAPTURE_CONTEXT] 🔍 STEP 2: Parsing request payload")
        print(f"[UC:CAPTURE_CONTEXT] Raw payload keys: {list(raw_payload.keys())}")
        print(f"[UC:CAPTURE_CONTEXT] Raw payload: {json.dumps(raw_payload, indent=2)}")
        
        helper_client = current_app.config.get('cybersource_helper')
        if not helper_client:
            print(f"[UC:CAPTURE_CONTEXT] ❌ ERROR: CyberSource helper not configured")
            return jsonify({'error': 'CyberSource helper not configured'}), 503
        print(f"[UC:CAPTURE_CONTEXT] ✅ STEP 3: Helper client available")

        data = raw_payload
        # Derive default origin from BASE_URL
        config = current_app.config.get('CONFIG')
        base_url = getattr(config, 'BASE_URL', 'https://kilekitabu-backend.onrender.com')
        default_origin = base_url if base_url.startswith('http') else f"https://{base_url}"
        target_origins = data.get('targetOrigins') or [default_origin]
        allowed_networks = data.get('allowedCardNetworks') or ['VISA', 'MASTERCARD', 'AMEX']
        # Default to both PANENTRY (card) and GOOGLEPAY for Unified Checkout
        # Note: CyberSource Unified Checkout uses "PANENTRY" for card payments, not "CARD"
        allowed_types = data.get('allowedPaymentTypes') or ['PANENTRY', 'GOOGLEPAY']
        # Map "CARD" to "PANENTRY" if provided
        allowed_types = ['PANENTRY' if t == 'CARD' else t for t in allowed_types]
        country = (data.get('country') or 'KE').upper()
        locale_in = data.get('locale') or 'en-KE'
        # CyberSource requires locale like en_US (underscore, region upper)
        try:
            parts = locale_in.replace('-', '_').split('_', 1)
            if len(parts) == 2:
                locale = f"{parts[0].lower()}_{parts[1].upper()}"
            else:
                locale = locale_in.replace('-', '_')
        except Exception:
            locale = 'en_KE'
        client_version = data.get('clientVersion') or '0.31'
        amount = None
        currency = None
        try:
            if 'amount' in data:
                amount = str(data.get('amount'))
            if 'currency' in data and data.get('currency'):
                currency = str(data.get('currency')).upper()
        except Exception:
            amount = None
            currency = None

        # Get user billing info for pre-fill (optional)
        user_id = getattr(request, 'user_id', None)
        billing_info = None
        if user_id:
            try:
                db = current_app.config.get('DB')
                if db:
                    user_ref = db.reference(f'registeredUser/{user_id}')
                    user_data = user_ref.get() or {}
                    billing_info = _build_billing_info(user_data)
                    print(f"[UC:CAPTURE_CONTEXT]   - Billing info loaded for pre-fill: {bool(billing_info)}")
            except Exception as err:
                print(f"[UC:CAPTURE_CONTEXT] ⚠️ WARNING: Unable to load user billing info: {err}")
        
        # Complete Mandate options (enable service orchestration)
        use_complete_mandate = data.get('useCompleteMandate', False)  # Default to False for backward compatibility
        complete_mandate_type = data.get('completeMandateType', 'CAPTURE')  # 'CAPTURE', 'AUTH', or 'PREFER_AUTH'
        enable_decision_manager = data.get('enableDecisionManager', True)
        enable_consumer_auth = data.get('enableConsumerAuthentication', True)

        print(f"[UC:CAPTURE_CONTEXT] ✅ STEP 4: Parameters extracted")
        print(f"[UC:CAPTURE_CONTEXT]   - targetOrigins: {target_origins}")
        print(f"[UC:CAPTURE_CONTEXT]   - allowedPaymentTypes: {allowed_types}")
        print(f"[UC:CAPTURE_CONTEXT]   - allowedCardNetworks: {allowed_networks}")
        print(f"[UC:CAPTURE_CONTEXT]   - country: {country}")
        print(f"[UC:CAPTURE_CONTEXT]   - locale: {locale}")
        print(f"[UC:CAPTURE_CONTEXT]   - clientVersion: {client_version}")
        print(f"[UC:CAPTURE_CONTEXT]   - amount: {amount}")
        print(f"[UC:CAPTURE_CONTEXT]   - currency: {currency}")
        print(f"[UC:CAPTURE_CONTEXT]   - useCompleteMandate: {use_complete_mandate}")
        print(f"[UC:CAPTURE_CONTEXT]   - completeMandateType: {complete_mandate_type}")
        print(f"[UC:CAPTURE_CONTEXT]   - enableDecisionManager: {enable_decision_manager}")
        print(f"[UC:CAPTURE_CONTEXT]   - enableConsumerAuthentication: {enable_consumer_auth}")
        print(f"[UC:CAPTURE_CONTEXT]   - billingInfo provided: {bool(billing_info)}")
        if billing_info:
            print(f"[UC:CAPTURE_CONTEXT]   - billingInfo keys: {list(billing_info.keys())}")
            print(f"[UC:CAPTURE_CONTEXT]   - billingInfo (sanitized): {json.dumps({k: (v[:50] + '...' if isinstance(v, str) and len(v) > 50 else v) for k, v in billing_info.items()}, indent=2)}")

        helper_payload = {
            'targetOrigins': target_origins,
            'allowedCardNetworks': allowed_networks,
            'allowedPaymentTypes': allowed_types,
            'country': country,
            'locale': locale,
            'clientVersion': client_version,
        }
        if amount is not None:
            helper_payload['amount'] = amount
        if currency:
            helper_payload['currency'] = currency
        if billing_info:
            helper_payload['billingInfo'] = billing_info
        if use_complete_mandate:
            helper_payload['useCompleteMandate'] = True
            helper_payload['completeMandateType'] = complete_mandate_type
            helper_payload['enableDecisionManager'] = enable_decision_manager
            helper_payload['enableConsumerAuthentication'] = enable_consumer_auth

        print(f"[UC:CAPTURE_CONTEXT] ✅ STEP 5: Helper payload prepared")
        print(f"[UC:CAPTURE_CONTEXT] Helper payload: {json.dumps(helper_payload, indent=2)}")
        print(f"[UC:CAPTURE_CONTEXT] ⏩ STEP 6: Forwarding to Node.js helper service")
        
        print(f"[UC:CAPTURE_CONTEXT] ⏩ STEP 6: Forwarding to Node.js helper service")
        print(f"[UC:CAPTURE_CONTEXT] Helper URL: {helper_client.base_url}/api/unified-checkout/capture-context")
        print(f"[UC:CAPTURE_CONTEXT] Helper payload size: {len(json.dumps(helper_payload))} bytes")
        
        capture_context = helper_client.generate_unified_checkout_capture_context(helper_payload)
        
        print(f"[UC:CAPTURE_CONTEXT] ✅ STEP 7: Response received from Node.js helper")
        print(f"[UC:CAPTURE_CONTEXT] Response type: {type(capture_context)}")
        print(f"[UC:CAPTURE_CONTEXT] Response keys: {list(capture_context.keys()) if isinstance(capture_context, dict) else 'N/A'}")
        if isinstance(capture_context, dict):
            for key, value in capture_context.items():
                if key == 'captureContext' and isinstance(value, str):
                    print(f"[UC:CAPTURE_CONTEXT]   - {key}: length={len(value)}, preview={value[:50]}...")
                elif isinstance(value, str) and len(value) > 100:
                    print(f"[UC:CAPTURE_CONTEXT]   - {key}: length={len(value)}, preview={value[:50]}...")
                else:
                    print(f"[UC:CAPTURE_CONTEXT]   - {key}: {value}")
        
        response_payload = dict(capture_context or {})
        if isinstance(response_payload.get('captureContext'), str):
            cleaned = response_payload['captureContext'].strip().strip('"')
            response_payload['captureContext'] = cleaned
            print(f"[UC:CAPTURE_CONTEXT] ✅ STEP 8: Capture context cleaned (removed quotes)")
        
        # Include clientLibraryIntegrity if available (for SRI checking)
        if 'clientLibraryIntegrity' in response_payload:
            print(f"[UC:CAPTURE_CONTEXT] ✅ Client Library Integrity included for SRI checking")
        
        capture_len = len(response_payload.get('captureContext') or '')
        print(f"[UC:CAPTURE_CONTEXT] ✅ STEP 9: Final response prepared")
        print(f"[UC:CAPTURE_CONTEXT] Capture context length: {capture_len} characters")
        print(f"[UC:CAPTURE_CONTEXT] First 100 chars: {response_payload.get('captureContext', '')[:100]}...")
        print(f"[UC:CAPTURE_CONTEXT] ========== SUCCESS: Returning capture context ==========")
        
        return jsonify(response_payload), 200
    except CyberSourceHelperError as helper_err:
        print(f"[UC:CAPTURE_CONTEXT] ❌ STEP X: Helper error occurred")
        print(f"[UC:CAPTURE_CONTEXT] Error type: CyberSourceHelperError")
        print(f"[UC:CAPTURE_CONTEXT] Error message: {helper_err}")
        print(f"[UC:CAPTURE_CONTEXT] Status code: {helper_err.status_code}")
        print(f"[UC:CAPTURE_CONTEXT] Error response: {json.dumps(helper_err.response, indent=2) if helper_err.response else 'None'}")
        print(f"[UC:CAPTURE_CONTEXT] ========== FAILED: Helper error ==========")
        
        # Check if this is a Cloudflare challenge
        error_response = helper_err.response or {}
        error_raw = error_response.get('raw', '') if isinstance(error_response, dict) else str(error_response)
        is_cloudflare_challenge = (
            helper_err.status_code in [429, 403] and 
            ('challenge-platform' in error_raw or 'Just a moment' in error_raw)
        )
        
        if is_cloudflare_challenge:
            error_message = (
                'Cloudflare protection is blocking the payment service. '
                'Please configure Cloudflare to allow API requests from mobile apps, '
                'or whitelist the helper service IP addresses.'
            )
        else:
            error_message = 'capture-context failed'
        
        return jsonify({
            'error': error_message,
            'details': helper_err.response or helper_err.args[0],
            'status_code': helper_err.status_code,
        }), helper_err.status_code or 500
    except Exception as e:
        import traceback
        print(f"[UC:CAPTURE_CONTEXT] ❌ STEP X: Unexpected error occurred")
        print(f"[UC:CAPTURE_CONTEXT] Error type: {type(e).__name__}")
        print(f"[UC:CAPTURE_CONTEXT] Error message: {str(e)}")
        print(f"[UC:CAPTURE_CONTEXT] Full traceback:")
        traceback.print_exc()
        print(f"[UC:CAPTURE_CONTEXT] ========== FAILED: Internal error ==========")
        return jsonify({'error': 'Internal server error', 'message': str(e)}), 500


@require_auth
def unified_checkout_charge():
    """Charge a payment using Unified Checkout transient token (for both card and Google Pay)."""
    import traceback
    try:
        print(f"[UC:CHARGE] ========== STEP 1: CHARGE REQUEST RECEIVED ==========")
        print(f"[UC:CHARGE] Timestamp: {datetime.datetime.now(datetime.timezone.utc).isoformat()}")
        print(f"[UC:CHARGE] Request method: {request.method}")
        print(f"[UC:CHARGE] Request headers: {dict(request.headers)}")
        
        if not current_app.config.get('DB'):
            print(f"[UC:CHARGE] ❌ ERROR: Database unavailable")
            return jsonify({'error': 'Database unavailable'}), 503
        print(f"[UC:CHARGE] ✅ STEP 2: Database available")

        data = request.get_json(force=True) or {}
        print(f"[UC:CHARGE] ✅ STEP 3: Request payload parsed")
        print(f"[UC:CHARGE] Payload keys: {list(data.keys())}")
        print(f"[UC:CHARGE] Full payload: {json.dumps({k: (v[:100] + '...' if isinstance(v, str) and len(v) > 100 else v) for k, v in data.items()}, indent=2)}")
        
        transient_token = data.get('transientToken')
        amount_raw = data.get('amount', 0)
        # Ensure amount is a float and format to 2 decimal places
        try:
            amount = float(amount_raw)
            # Format to exactly 2 decimal places as string for CyberSource
            amount_str = f"{amount:.2f}"
            amount = float(amount_str)  # Convert back to float for validation
        except (ValueError, TypeError):
            return jsonify({'error': 'Invalid amount format'}), 400
        
        currency = (data.get('currency') or 'USD').upper()
        payment_type_raw = data.get('paymentType', 'CARD')
        # Map Unified Checkout payment types to charge endpoint types
        # 'PANENTRY' (Unified Checkout card) -> 'CARD' (charge endpoint)
        # 'GOOGLEPAY' stays as 'GOOGLEPAY'
        if payment_type_raw == 'PANENTRY':
            payment_type = 'CARD'
        else:
            payment_type = payment_type_raw.upper()  # 'CARD' or 'GOOGLEPAY'
        
        reference_code = data.get('referenceCode')
        client_billing_info = data.get('billingInfo') or {}
        
        print(f"[UC:CHARGE] ✅ STEP 4: Parameters extracted and validated")
        print(f"[UC:CHARGE]   - amount (raw): {amount_raw}")
        print(f"[UC:CHARGE]   - amount (formatted): {amount_str} {currency}")
        print(f"[UC:CHARGE]   - paymentType (raw): {payment_type_raw}")
        print(f"[UC:CHARGE]   - paymentType (mapped): {payment_type}")
        print(f"[UC:CHARGE]   - transientToken present: {bool(transient_token)}")
        print(f"[UC:CHARGE]   - transientToken length: {len(transient_token) if transient_token else 0}")
        print(f"[UC:CHARGE]   - transientToken preview: {transient_token[:50] + '...' if transient_token and len(transient_token) > 50 else transient_token}")
        
        if not transient_token:
            print(f"[UC:CHARGE] ❌ ERROR: transientToken is required but missing")
            return jsonify({'error': 'transientToken is required'}), 400
        
        if amount < 1.0:
            print(f"[UC:CHARGE] ❌ ERROR: Amount {amount_str} is below minimum 1.0")
            return jsonify({'error': f"Minimum amount is {currency} 1.0"}), 400
        
        # Get user ID
        user_id = getattr(request, 'user_id', None)
        print(f"[UC:CHARGE] ✅ STEP 5: User authentication")
        print(f"[UC:CHARGE]   - user_id: {user_id}")
        if not user_id:
            print(f"[UC:CHARGE] ❌ ERROR: Unauthorized - no user_id")
            return jsonify({'error': 'Unauthorized'}), 401
        
        # Generate payment ID if not provided
        if not reference_code:
            payment_id = f"CS_{user_id[:10]}_{uuid.uuid4().hex[:12]}"
        else:
            payment_id = reference_code
        print(f"[UC:CHARGE] ✅ STEP 6: Payment ID generated")
        print(f"[UC:CHARGE]   - payment_id: {payment_id}")
        
        # Get user billing info
        db = current_app.config.get('DB')
        user_data = {}
        billing_info = {}
        print(f"[UC:CHARGE] ✅ STEP 7: Loading user data from Firebase")
        if user_id:
            try:
                user_ref = db.reference(f'registeredUser/{user_id}')
                user_data = user_ref.get() or {}
                print(f"[UC:CHARGE]   - User data loaded: {bool(user_data)}")
                print(f"[UC:CHARGE]   - User data keys: {list(user_data.keys()) if user_data else []}")
                billing_info = _build_billing_info(user_data)
                print(f"[UC:CHARGE]   - Billing info from user data: {json.dumps(billing_info, indent=2)}")
            except Exception as err:
                print(f"[UC:CHARGE] ⚠️ WARNING: Unable to load user profile: {err}")
                import traceback
                traceback.print_exc()
        
        # Merge client-provided billing info
        print(f"[UC:CHARGE] ✅ STEP 8: Merging billing information")
        print(f"[UC:CHARGE]   - Client billing info: {json.dumps(client_billing_info, indent=2)}")
        billing_info = _merge_billing_sources(billing_info, client_billing_info)
        if not billing_info:
            billing_info = _fallback_billing_from_user(user_data)
            print(f"[UC:CHARGE]   - Using fallback billing info")
        
        # Ensure required billing fields are present
        if not billing_info.get('firstName'):
            billing_info['firstName'] = 'Customer'
        if not billing_info.get('lastName'):
            billing_info['lastName'] = 'User'
        if not billing_info.get('email'):
            billing_info['email'] = user_data.get('email') or 'support@kilekitabu.com'
        if not billing_info.get('country'):
            billing_info['country'] = 'KE'
        if not billing_info.get('address1'):
            billing_info['address1'] = 'Unknown'
        if not billing_info.get('locality'):
            billing_info['locality'] = 'Nairobi'
        if not billing_info.get('postalCode'):
            billing_info['postalCode'] = '00100'
        
        print(f"[UC:CHARGE] ✅ STEP 9: Final billing info prepared")
        print(f"[UC:CHARGE] Final billing info: {json.dumps(billing_info, indent=2)}")
        
        # Create payment record
        payment_info = {
            'payment_id': payment_id,
            'user_id': user_id,
            'amount': amount,
            'currency': currency,
            'status': 'pending',
            'provider': 'unified_checkout',
            'payment_type': payment_type,
            'created_at': datetime.datetime.now(datetime.timezone.utc).isoformat(),
        }
        print(f"[UC:CHARGE] ✅ STEP 10: Creating payment record in Firebase")
        print(f"[UC:CHARGE] Payment record: {json.dumps(payment_info, indent=2)}")
        db.reference(f'payments/{user_id}/{payment_id}').set(payment_info)
        print(f"[UC:CHARGE] 💾 Payment record created: {payment_id}")
        
        # Charge via Node.js helper
        helper_client = current_app.config.get('cybersource_helper')
        if not helper_client:
            print(f"[UC:CHARGE] ❌ ERROR: CyberSource helper not configured")
            return jsonify({'error': 'CyberSource helper not configured'}), 503
        print(f"[UC:CHARGE] ✅ STEP 11: Helper client available")
        
        helper_payload = {
            'transientToken': transient_token,
            'amount': amount_str,  # Use formatted string with 2 decimals
            'currency': currency,
            'referenceCode': payment_id,
            'billingInfo': billing_info,
            'paymentType': payment_type,
        }
        
        print(f"[UC:CHARGE] ✅ STEP 12: Helper payload prepared")
        print(f"[UC:CHARGE] Helper payload (sanitized): {json.dumps({k: (v[:100] + '...' if isinstance(v, str) and len(v) > 100 else v) for k, v in helper_payload.items()}, indent=2)}")
        print(f"[UC:CHARGE] ⏩ STEP 13: Forwarding to Node.js helper service")
        print(f"[UC:CHARGE] Helper URL: {helper_client.base_url}/api/unified-checkout/charge")
        
        try:
            resp = helper_client.charge_unified_checkout_token(helper_payload) or {}
            print(f"[UC:CHARGE] ✅ STEP 14: Response received from Node.js helper")
            print(f"[UC:CHARGE] Response type: {type(resp)}")
            print(f"[UC:CHARGE] Response keys: {list(resp.keys()) if isinstance(resp, dict) else 'N/A'}")
            print(f"[UC:CHARGE] Full response: {json.dumps(resp, indent=2)}")
        except CyberSourceHelperError as helper_err:
            error_payload = helper_err.response or helper_err.args[0]
            status_code = helper_err.status_code or 500
            print(f"[UC:CHARGE] ❌ STEP 14: Helper error occurred")
            print(f"[UC:CHARGE] Error type: CyberSourceHelperError")
            print(f"[UC:CHARGE] Status code: {status_code}")
            print(f"[UC:CHARGE] Error payload: {json.dumps(error_payload, indent=2) if isinstance(error_payload, dict) else error_payload}")
            print(f"[UC:CHARGE] ⏩ Updating payment record status to 'failed'")
            db.reference(f'payments/{user_id}/{payment_id}').update({
                'status': 'failed',
                'provider_error': error_payload,
                'updated_at': datetime.datetime.now(datetime.timezone.utc).isoformat(),
            })
            print(f"[UC:CHARGE] ========== FAILED: Helper error ==========")
            return jsonify({
                'success': False,
                'payment_id': payment_id,
                'error': error_payload,
            }), status_code
        
        # Check for CyberSource error
        print(f"[UC:CHARGE] ✅ STEP 15: Checking for CyberSource errors in response")
        error_info = resp.get('errorInformation')
        if error_info:
            error_reason = error_info.get('reason', 'Unknown error')
            error_message = error_info.get('message', 'Payment declined')
            error_payload = f"{error_reason}: {error_message}"
            print(f"[UC:CHARGE] ❌ STEP 15: CyberSource payment error detected")
            print(f"[UC:CHARGE] Error reason: {error_reason}")
            print(f"[UC:CHARGE] Error message: {error_message}")
            print(f"[UC:CHARGE] Full error info: {json.dumps(error_info, indent=2)}")
            print(f"[UC:CHARGE] ⏩ Updating payment record status to 'failed'")
            db.reference(f'payments/{user_id}/{payment_id}').update({
                'status': 'failed',
                'provider_error': error_payload,
                'provider_data': resp,
                'updated_at': datetime.datetime.now(datetime.timezone.utc).isoformat(),
            })
            print(f"[UC:CHARGE] ========== FAILED: CyberSource error ==========")
            return jsonify({
                'success': False,
                'payment_id': payment_id,
                'error': error_payload,
                'errorInformation': error_info,
            }), 400
        
        status = (resp.get('status') or '').upper()
        transaction_id = resp.get('id')
        print(f"[UC:CHARGE] ✅ STEP 16: Payment successful from CyberSource")
        print(f"[UC:CHARGE]   - Status: {status}")
        print(f"[UC:CHARGE]   - Transaction ID: {transaction_id}")
        print(f"[UC:CHARGE]   - Full response: {json.dumps(resp, indent=2)}")
        
        # Compute credit days
        print(f"[UC:CHARGE] ✅ STEP 17: Computing credit days")
        config = current_app.config.get('CONFIG')
        daily_rate = float(getattr(config, 'DAILY_RATE', 5.0))
        amount_in_kes = convert_amount_to_kes(amount, currency)
        credit_days, rounded_kes = compute_credit_days_from_kes(amount_in_kes, daily_rate)
        print(f"[UC:CHARGE]   - Amount in KES: {amount_in_kes}")
        print(f"[UC:CHARGE]   - Daily rate: {daily_rate}")
        print(f"[UC:CHARGE]   - Credit days: {credit_days}")
        
        # Update user credit
        now_iso = datetime.datetime.now(datetime.timezone.utc).isoformat()
        print(f"[UC:CHARGE] ✅ STEP 18: Updating user credit in Firebase")
        try:
            registered_user_ref = db.reference(f'registeredUser/{user_id}')
            user_data = registered_user_ref.get() or {}
            current_credit = int(float(user_data.get('credit_balance', 0) or 0))
            print(f"[UC:CHARGE]   - Current credit: {current_credit} days")
            
            # Monthly spend tracking
            month_key = datetime.datetime.now(datetime.timezone.utc).strftime('%Y-%m')
            monthly = user_data.get('monthly_paid', {}) or {}
            monthly[month_key] = float(monthly.get(month_key, 0) or 0) + float(amount_in_kes)
            
            new_credit = current_credit + credit_days
            print(f"[UC:CHARGE]   - New credit: {new_credit} days")
            registered_user_ref.update({
                'credit_balance': int(new_credit),
                'total_payments': float(user_data.get('total_payments', 0) or 0) + float(amount),
                'monthly_paid': monthly,
                'last_payment_date': now_iso,
                'updated_at': now_iso,
            })
            print(f"[UC:CHARGE] ✅ User credit updated: {current_credit} -> {new_credit} days")
        except Exception as ue:
            print(f"[UC:CHARGE] ⚠️ WARNING: User credit update error: {ue}")
            import traceback
            traceback.print_exc()
        
        # Update payment record
        print(f"[UC:CHARGE] ✅ STEP 19: Updating payment record status to 'completed'")
        final_status = 'completed' if status in ['AUTHORIZED', 'CAPTURED', 'PENDING', 'SETTLED'] else status.lower() or 'completed'
        print(f"[UC:CHARGE]   - Final status: {final_status}")
        db.reference(f'payments/{user_id}/{payment_id}').update({
            'status': final_status,
            'provider_data': resp,
            'credit_days': credit_days,
            'transaction_id': transaction_id,
            'completed_at': now_iso,
            'updated_at': now_iso,
        })
        
        print(f"[UC:CHARGE] ✅ STEP 20: Preparing final response")
        final_response = {
            'id': transaction_id,
            'status': status,
            'transaction_id': transaction_id,
            'payment_id': payment_id,
            'credit_days': credit_days,
        }
        print(f"[UC:CHARGE] Final response: {json.dumps(final_response, indent=2)}")
        print(f"[UC:CHARGE] ========== SUCCESS: Payment completed ==========")
        
        return jsonify(final_response), 200
        
    except Exception as e:
        import traceback
        print(f"[UC:CHARGE] ❌ STEP X: Unexpected error occurred")
        print(f"[UC:CHARGE] Error type: {type(e).__name__}")
        print(f"[UC:CHARGE] Error message: {str(e)}")
        print(f"[UC:CHARGE] Full traceback:")
        traceback.print_exc()
        print(f"[UC:CHARGE] ========== FAILED: Internal error ==========")
        return jsonify({'error': 'Internal server error', 'message': str(e)}), 500


def _build_billing_info(user_data):
    """Prepare billTo block for CyberSource using stored profile/billing details."""
    if not user_data:
        return {}

    billing = (user_data.get('billing_details') or {}).copy()
    name = (user_data.get('name') or '').strip()
    first_name = (
        billing.get('firstName')
        or (name.split(' ', 1)[0] if name else user_data.get('firstName'))
        or 'Customer'
    )
    last_name = (
        billing.get('lastName')
        or (name.split(' ', 1)[1] if ' ' in name else user_data.get('lastName'))
        or 'User'
    )
    locality = (
        billing.get('city')
        or billing.get('locality')
        or user_data.get('city')
        or 'Nairobi'
    )
    address1 = billing.get('address') or billing.get('address1') or user_data.get('address') or 'Unknown'
    country = (billing.get('country') or 'KE').upper()
    postal_code = billing.get('postalCode') or '00100'
    email = billing.get('email') or user_data.get('email')
    phone = billing.get('phone') or user_data.get('phone')

    bill_to = {
        'firstName': first_name,
        'lastName': last_name,
        'email': email or 'support@kilekitabu.com',
        'address1': address1,
        'locality': locality,
        'postalCode': postal_code,
        'country': country,
    }
    if phone:
        bill_to['phoneNumber'] = phone
    administrative_area = billing.get('administrativeArea') or billing.get('state') or user_data.get('state') or ''
    if administrative_area:
        bill_to['administrativeArea'] = administrative_area
    return bill_to


def _merge_billing_sources(primary, fallback):
    result = dict(primary or {})
    for key, value in (fallback or {}).items():
        if value and not result.get(key):
            result[key] = value
    return result


def _fallback_billing_from_user(user_data):
    if not user_data:
        return {
            'firstName': 'Customer',
            'lastName': 'User',
            'email': 'support@kilekitabu.com',
            'address1': 'Unknown',
            'locality': 'Nairobi',
            'postalCode': '00100',
            'country': 'KE',
        }
    name = (user_data.get('name') or '').strip()
    parts = name.split(' ', 1)
    first = parts[0] if parts else (user_data.get('firstName') or 'Customer')
    last = parts[1] if len(parts) > 1 else (user_data.get('lastName') or 'User')
    return {
        'firstName': first or 'Customer',
        'lastName': last or 'User',
        'email': user_data.get('email') or 'support@kilekitabu.com',
        'address1': user_data.get('address') or 'Unknown',
        'locality': user_data.get('city') or 'Nairobi',
        'postalCode': user_data.get('postalCode') or '00100',
        'country': (user_data.get('country') or 'KE').upper(),
        'phoneNumber': user_data.get('phone'),
    }

