"""CyberSource payment controller."""
import datetime
import uuid
from flask import request, jsonify
from functools import wraps
from firebase_admin import auth, db
from config import Config


def require_auth(f):
    """Decorator to require Firebase authentication."""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        auth_header = request.headers.get('Authorization', '')
        
        print(f"[Auth] Checking authentication for {request.path}")
        print(f"[Auth] Authorization header present: {bool(auth_header)}")
        
        if not auth_header or not auth_header.startswith('Bearer '):
            print(f"[Auth] ❌ Missing or malformed Authorization header")
            return jsonify({'error': 'Unauthorized - Missing token'}), 401
        
        token = auth_header.split('Bearer ')[1]
        print(f"[Auth] Token extracted (length: {len(token)})")
        
        try:
            print(f"[Auth] Attempting to verify Firebase ID token...")
            decoded_token = auth.verify_id_token(token)
            user_id = decoded_token['uid']
            print(f"[Auth] ✅ Token verified successfully, User ID: {user_id}")
            request.user_id = user_id
            return f(*args, **kwargs)
        except Exception as e:
            error_str = str(e).lower()
            print(f"[Auth] ❌ Token verification failed: {e}")
            
            # Handle clock skew errors
            if 'clock' in error_str or 'too early' in error_str or 'too late' in error_str:
                print(f"[Auth] ⚠️ Clock skew detected, waiting 2 seconds and retrying...")
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
            
            return jsonify({'error': f'Unauthorized - {str(e)}'}), 401
    
    return decorated_function


def initiate_card_payment():
    """
    Initiate a card payment via CyberSource.
    
    Expected request body:
    {
        "amount": 100.0,
        "currency": "KES",
        "card": {
            "number": "4111111111111111",
            "expirationMonth": "12",
            "expirationYear": "2031",
            "cvv": "123"
        },
        "billingInfo": {
            "firstName": "John",
            "lastName": "Doe",
            "address1": "1 Market St",
            "locality": "Nairobi",
            "administrativeArea": "Nairobi",
            "postalCode": "00100",
            "country": "KE",
            "email": "test@example.com",
            "phoneNumber": "254712345678"
        }
    }
    """
    print(f"[cybersource_initiate] ========== Card Payment Initiation ==========")
    
    # Get the CyberSource client from app context
    from flask import current_app
    cybersource_client = current_app.config.get('cybersource_client')
    
    if not cybersource_client:
        print(f"[cybersource_initiate] ❌ CyberSource client not initialized")
        return jsonify({
            'success': False,
            'error': 'Card payments are currently unavailable. Please use M-Pesa for payments.',
            'details': 'CyberSource payment gateway is not configured'
        }), 503
    
    # Get user ID from request
    user_id = getattr(request, 'user_id', None)
    
    if not user_id:
        print(f"[cybersource_initiate] ❌ No user_id found in request")
        return jsonify({'error': 'Unauthorized'}), 401
    
    print(f"[cybersource_initiate] User ID: {user_id}")
    
    # Parse request body
    try:
        data = request.get_json()
        amount = float(data.get('amount', 0))
        currency = data.get('currency', 'KES')
        card = data.get('card', {})
        billing_info = data.get('billingInfo', {})
        
        print(f"[cybersource_initiate] Amount: {amount} {currency}")
        print(f"[cybersource_initiate] Card ending: ****{card.get('number', '')[-4:]}")
        print(f"[cybersource_initiate] Billing: {billing_info.get('firstName')} {billing_info.get('lastName')}")
        
        # Validate amount
        if amount < Config.VALIDATION_RULES['min_amount']:
            return jsonify({
                'error': f"Amount must be at least {Config.VALIDATION_RULES['min_amount']}"
            }), 400
        
        if amount > Config.VALIDATION_RULES['max_amount']:
            return jsonify({
                'error': f"Amount must not exceed {Config.VALIDATION_RULES['max_amount']}"
            }), 400
        
        # Validate card fields
        if not all([
            card.get('number'),
            card.get('expirationMonth'),
            card.get('expirationYear'),
            card.get('cvv'),
        ]):
            return jsonify({'error': 'Missing required card fields'}), 400
        
        # Validate billing info
        required_billing_fields = [
            'firstName', 'lastName', 'email', 'phoneNumber',
            'address1', 'locality', 'country'
        ]
        missing_fields = [f for f in required_billing_fields if not billing_info.get(f)]
        if missing_fields:
            return jsonify({
                'error': f"Missing required billing fields: {', '.join(missing_fields)}"
            }), 400
        
    except (ValueError, TypeError) as e:
        print(f"[cybersource_initiate] ❌ Invalid request data: {e}")
        return jsonify({'error': 'Invalid request data'}), 400
    
    # Fetch user record for monthly spend calculations
    user_ref = db.reference(f'registeredUser/{user_id}')
    user_data = user_ref.get() or {}
    
    now = datetime.datetime.now(datetime.timezone.utc)
    month_key = now.strftime('%Y-%m')
    monthly_paid = user_data.get('monthly_paid', {}) or {}
    month_spend = float(monthly_paid.get(month_key, 0))
    max_monthly_total = Config.MONTHLY_CAP_KES * getattr(Config, 'MAX_PREPAY_MONTHS', 1)
    remaining_cap = max(0.0, max_monthly_total - month_spend)
    print(f"[cybersource_initiate] month_spend={month_spend} remaining_cap={remaining_cap} max_monthly_total={max_monthly_total}")
    
    if remaining_cap <= 0:
        return jsonify({
            'error': 'Monthly cap reached',
            'cap': max_monthly_total,
            'month': month_key
        }), 400
    
    if amount > remaining_cap:
        return jsonify({
            'error': (
                f'Amount exceeds remaining allowance. You can pay up to '
                f'KES {int(remaining_cap)} right now (max {int(max_monthly_total)} per month).'
            ),
            'remaining': remaining_cap,
            'requested': amount
        }), 400
    
    # Generate unique reference
    payment_id = f"CS_{user_id[:8]}_{uuid.uuid4().hex[:12]}"
    print(f"[cybersource_initiate] Payment ID: {payment_id}")
    
    # Store payment initiation in Firebase
    try:
        payments_ref = db.reference(f'payments/{user_id}')
        payment_data = {
            'payment_id': payment_id,
            'user_id': user_id,
            'amount': amount,
            'currency': currency,
            'payment_method': 'CARD',
            'provider': 'CYBERSOURCE',
            'status': 'PENDING',
            'created_at': datetime.datetime.now(datetime.timezone.utc).isoformat(),
            'billing_info': {
                'name': f"{billing_info.get('firstName')} {billing_info.get('lastName')}",
                'email': billing_info.get('email'),
                'phone': billing_info.get('phoneNumber'),
            }
        }
        
        payments_ref.child(payment_id).set(payment_data)
        print(f"[cybersource_initiate] ✅ Payment record created in Firebase")
        
    except Exception as e:
        print(f"[cybersource_initiate] ⚠️ Failed to store payment in Firebase: {e}")
        # Continue anyway - we can still process the payment
    
    # Process payment via CyberSource
    try:
        result = cybersource_client.create_payment(
            amount=amount,
            currency=currency,
            card_number=card['number'],
            expiration_month=card['expirationMonth'],
            expiration_year=card['expirationYear'],
            cvv=card['cvv'],
            billing_info=billing_info,
            reference_code=payment_id,
        )
        
        print(f"[cybersource_initiate] CyberSource response: {result}")
        
        if result.get('ok'):
            # Payment successful
            response_data = result['response']
            transaction_id = response_data.get('id')
            status = response_data.get('status')
            
            # Update payment record
            try:
                payments_ref.child(payment_id).update({
                    'transaction_id': transaction_id,
                    'status': 'COMPLETED' if status == 'AUTHORIZED' else status,
                    'cybersource_response': response_data,
                    'updated_at': datetime.datetime.now(datetime.timezone.utc).isoformat(),
                })
                
                # Add credits to user account
                if status == 'AUTHORIZED':
                    # Re-fetch latest user data for accuracy
                    latest_user_data = user_ref.get() or {}
                    
                    current_credit_raw = latest_user_data.get('credit_balance', 0)
                    if isinstance(current_credit_raw, float):
                        current_credit = int(current_credit_raw)
                    elif isinstance(current_credit_raw, int):
                        current_credit = current_credit_raw
                    else:
                        try:
                            current_credit = int(float(current_credit_raw))
                        except (ValueError, TypeError):
                            current_credit = 0
                    
                    daily_rate = Config.DAILY_RATE if Config.DAILY_RATE else 1
                    credit_days = max(1, int(amount / daily_rate))
                    new_credit = current_credit + credit_days
                    
                    updated_monthly = latest_user_data.get('monthly_paid', {}) or {}
                    latest_month_spend = float(updated_monthly.get(month_key, 0))
                    latest_month_spend += amount
                    updated_monthly[month_key] = latest_month_spend
                    
                    user_ref.update({
                        'credit_balance': int(new_credit),
                        'total_payments': float(latest_user_data.get('total_payments', 0)) + amount,
                        'monthly_paid': updated_monthly,
                        'last_payment_date': datetime.datetime.now(datetime.timezone.utc).isoformat(),
                        'updated_at': datetime.datetime.now(datetime.timezone.utc).isoformat(),
                    })
                    
                    payments_ref.child(payment_id).update({
                        'credit_days': credit_days
                    })
                    
                    print(f"[cybersource_initiate] ✅ Added {credit_days} credit days. New balance: {new_credit}")
                
            except Exception as e:
                print(f"[cybersource_initiate] ⚠️ Failed to update records: {e}")
            
            return jsonify({
                'success': True,
                'payment_id': payment_id,
                'transaction_id': transaction_id,
                'status': status,
                'amount': amount,
                'currency': currency,
            }), 200
        
        else:
            # Payment failed
            error = result.get('error', 'Unknown error')
            
            # Update payment record
            try:
                payments_ref.child(payment_id).update({
                    'status': 'FAILED',
                    'error': str(error),
                    'updated_at': datetime.datetime.now(datetime.timezone.utc).isoformat(),
                })
            except Exception as e:
                print(f"[cybersource_initiate] ⚠️ Failed to update payment record: {e}")
            
            return jsonify({
                'success': False,
                'error': str(error),
                'payment_id': payment_id,
            }), 400
    
    except Exception as e:
        print(f"[cybersource_initiate] ❌ Unexpected error: {e}")
        import traceback
        print(f"[cybersource_initiate] Traceback: {traceback.format_exc()}")
        
        return jsonify({
            'success': False,
            'error': 'Payment processing failed',
        }), 500


def handle_webhook():
    """
    Handle CyberSource webhook notifications.
    
    Webhook events:
    - payByLink.merchant.payment: Customer completed payment via Pay by Link
    - payments.capture.status.accepted: Payment capture accepted
    - payments.capture.status.updated: Payment capture status updated
    """
    print(f"[cybersource_webhook] ========== Webhook Received ==========")
    
    # Get the CyberSource client from app context
    from flask import current_app
    cybersource_client = current_app.config.get('cybersource_client')
    webhook_secret = Config.CYBERSOURCE_WEBHOOK_SECRET
    
    if not webhook_secret:
        print(f"[cybersource_webhook] ⚠️ Webhook secret not configured, skipping validation")
    
    # Get headers
    signature_header = request.headers.get('V-C-Signature', '')
    event_type = request.headers.get('V-C-Event-Type', '')
    organization_id = request.headers.get('V-C-Organization-Id', '')
    product_name = request.headers.get('V-C-Product-Name', '')
    webhook_id = request.headers.get('V-C-Webhook-Id', '')
    
    print(f"[cybersource_webhook] Event Type: {event_type}")
    print(f"[cybersource_webhook] Organization ID: {organization_id}")
    print(f"[cybersource_webhook] Product: {product_name}")
    print(f"[cybersource_webhook] Webhook ID: {webhook_id}")
    
    # Get raw body
    raw_body = request.get_data(as_text=True)
    
    # Validate signature if configured
    if webhook_secret and cybersource_client:
        is_valid = cybersource_client.validate_webhook_signature(
            signature_header=signature_header,
            payload=raw_body,
            webhook_secret=webhook_secret,
        )
        
        if not is_valid:
            print(f"[cybersource_webhook] ❌ Invalid signature")
            return jsonify({'error': 'Invalid signature'}), 401
    
    # Parse webhook body
    try:
        webhook_data = request.get_json()
        print(f"[cybersource_webhook] Webhook data: {webhook_data}")
        
        notification_id = webhook_data.get('notificationId')
        event_date = webhook_data.get('eventDate')
        payloads = webhook_data.get('payloads', [])
        
        print(f"[cybersource_webhook] Notification ID: {notification_id}")
        print(f"[cybersource_webhook] Event Date: {event_date}")
        print(f"[cybersource_webhook] Payloads count: {len(payloads)}")
        
        # Process each payload
        for payload_item in payloads:
            data = payload_item.get('data', {})
            organization_id_payload = payload_item.get('organizationId')
            
            # Extract relevant payment information
            if event_type == 'payByLink.merchant.payment':
                # Pay by Link payment completed
                transaction_id = data.get('transactionId') or data.get('id')
                amount = float(data.get('amount', 0))
                currency = data.get('currency', 'USD')
                status = data.get('status', 'UNKNOWN')
                customer_email = data.get('email') or data.get('customerEmail')
                reference_code = data.get('referenceCode') or data.get('clientReferenceCode')
                
                print(f"[cybersource_webhook] Pay by Link Payment:")
                print(f"[cybersource_webhook]   Transaction ID: {transaction_id}")
                print(f"[cybersource_webhook]   Amount: {amount} {currency}")
                print(f"[cybersource_webhook]   Status: {status}")
                print(f"[cybersource_webhook]   Reference: {reference_code}")
                print(f"[cybersource_webhook]   Customer: {customer_email}")
                
                # Find user by email or reference code
                # For now, we'll use reference code to match user
                if reference_code and reference_code.startswith('CS_'):
                    # Extract user_id from reference code format: CS_{user_id}_{random}
                    try:
                        user_id_part = reference_code.split('_')[1]
                        
                        # Search for user
                        users_ref = db.reference('registeredUser')
                        all_users = users_ref.get() or {}
                        
                        matched_user_id = None
                        for uid, user_data in all_users.items():
                            if uid.startswith(user_id_part):
                                matched_user_id = uid
                                break
                        
                        if matched_user_id:
                            print(f"[cybersource_webhook] ✅ Matched user: {matched_user_id}")
                            
                            # Update payment record
                            payments_ref = db.reference(f'payments/{matched_user_id}')
                            payment_record = payments_ref.child(reference_code).get()
                            
                            if payment_record:
                                payments_ref.child(reference_code).update({
                                    'transaction_id': transaction_id,
                                    'status': 'COMPLETED' if status in ['AUTHORIZED', 'COMPLETED'] else status,
                                    'webhook_data': data,
                                    'updated_at': datetime.datetime.now(datetime.timezone.utc).isoformat(),
                                })
                            
                            # Add credits if payment successful
                            if status in ['AUTHORIZED', 'COMPLETED', 'SUCCESS']:
                                user_ref = db.reference(f'registeredUser/{matched_user_id}')
                                user_data = user_ref.get() or {}
                                current_credit = float(user_data.get('credit_balance', 0))
                                new_credit = current_credit + amount
                                
                                user_ref.update({
                                    'credit_balance': new_credit,
                                    'total_payments': float(user_data.get('total_payments', 0)) + amount,
                                    'last_payment_date': datetime.datetime.now(datetime.timezone.utc).isoformat(),
                                    'updated_at': datetime.datetime.now(datetime.timezone.utc).isoformat(),
                                })
                                
                                print(f"[cybersource_webhook] ✅ Added {amount} credits. New balance: {new_credit}")
                        else:
                            print(f"[cybersource_webhook] ⚠️ No user matched for reference: {reference_code}")
                    
                    except Exception as e:
                        print(f"[cybersource_webhook] ❌ Error processing payment: {e}")
                        import traceback
                        print(f"[cybersource_webhook] Traceback: {traceback.format_exc()}")
            
            elif event_type in ['payments.capture.status.accepted', 'payments.capture.status.updated']:
                # Standard payment events
                print(f"[cybersource_webhook] Payment capture event: {event_type}")
                # Similar processing logic as above
                pass
        
        print(f"[cybersource_webhook] ✅ Webhook processed successfully")
        return jsonify({'status': 'success'}), 200
    
    except Exception as e:
        print(f"[cybersource_webhook] ❌ Error processing webhook: {e}")
        import traceback
        print(f"[cybersource_webhook] Traceback: {traceback.format_exc()}")
        return jsonify({'error': 'Webhook processing failed'}), 500


def create_subscription():
    """
    Create a monthly subscription (KES 150) using card details.
    Processes the payment immediately and records subscription for future renewals.
    """
    print(f"[cybersource_subscription] ========== Create Subscription ==========")
    
    # Get the CyberSource client from app context
    from flask import current_app
    cybersource_client = current_app.config.get('cybersource_client')
    
    if not cybersource_client:
        print(f"[cybersource_subscription] ❌ CyberSource client not initialized")
        return jsonify({
            'success': False,
            'error': 'Card subscriptions are currently unavailable. Please use M-Pesa for payments.',
            'details': 'CyberSource payment gateway is not configured'
        }), 503
    
    user_id = getattr(request, 'user_id', None)
    if not user_id:
        return jsonify({'success': False, 'error': 'Unauthorized'}), 401

    try:
        data = request.get_json() or {}
        amount = float(data.get('amount', 150))
        currency = data.get('currency', 'KES')
        card = data.get('card', {})
        billing_info = data.get('billingInfo', {})
        
        print(f"[cybersource_subscription] User: {user_id} Amount: {amount} {currency}")
        
        # Validate card fields
        if not all([
            card.get('number'),
            card.get('expirationMonth'),
            card.get('expirationYear'),
            card.get('cvv'),
        ]):
            return jsonify({'success': False, 'error': 'Missing required card fields'}), 400
        
        # Validate billing info
        required_billing_fields = [
            'firstName', 'lastName', 'email', 'phoneNumber',
            'address1', 'locality', 'country'
        ]
        missing_fields = [f for f in required_billing_fields if not billing_info.get(f)]
        if missing_fields:
            return jsonify({
                'success': False,
                'error': f"Missing required billing fields: {', '.join(missing_fields)}"
            }), 400
        
        # Generate unique reference for subscription payment
        payment_id = f"SUB_{user_id[:8]}_{uuid.uuid4().hex[:12]}"
        print(f"[cybersource_subscription] Payment ID: {payment_id}")
        
        # Store subscription payment initiation in Firebase
        try:
            payments_ref = db.reference(f'payments/{user_id}')
            payment_data = {
                'payment_id': payment_id,
                'user_id': user_id,
                'amount': amount,
                'currency': currency,
                'payment_method': 'CARD',
                'provider': 'CYBERSOURCE',
                'payment_type': 'SUBSCRIPTION',
                'status': 'PENDING',
                'created_at': datetime.datetime.now(datetime.timezone.utc).isoformat(),
                'billing_info': {
                    'name': f"{billing_info.get('firstName')} {billing_info.get('lastName')}",
                    'email': billing_info.get('email'),
                    'phone': billing_info.get('phoneNumber'),
                }
            }
            payments_ref.child(payment_id).set(payment_data)
            print(f"[cybersource_subscription] ✅ Payment record created in Firebase")
        except Exception as e:
            print(f"[cybersource_subscription] ⚠️ Failed to store payment in Firebase: {e}")
        
        # Process payment via CyberSource (charge 150 KES immediately)
        try:
            result = cybersource_client.create_payment(
                amount=amount,
                currency=currency,
                card_number=card['number'],
                expiration_month=card['expirationMonth'],
                expiration_year=card['expirationYear'],
                cvv=card['cvv'],
                billing_info=billing_info,
                reference_code=payment_id,
            )
            
            print(f"[cybersource_subscription] CyberSource response: {result}")
            
            if result.get('ok'):
                # Payment successful
                response_data = result['response']
                transaction_id = response_data.get('id')
                status = response_data.get('status')
                
                # Update payment record
                try:
                    payments_ref.child(payment_id).update({
                        'transaction_id': transaction_id,
                        'status': 'COMPLETED' if status == 'AUTHORIZED' else status,
                        'cybersource_response': response_data,
                        'updated_at': datetime.datetime.now(datetime.timezone.utc).isoformat(),
                    })
                    
                    # Add credits to user account
                    if status == 'AUTHORIZED':
                        user_ref = db.reference(f'registeredUser/{user_id}')
                        user_data = user_ref.get() or {}
                        current_credit = float(user_data.get('credit_balance', 0))
                        new_credit = current_credit + amount
                        
                        user_ref.update({
                            'credit_balance': new_credit,
                            'total_payments': float(user_data.get('total_payments', 0)) + amount,
                            'last_payment_date': datetime.datetime.now(datetime.timezone.utc).isoformat(),
                            'updated_at': datetime.datetime.now(datetime.timezone.utc).isoformat(),
                        })
                        
                        print(f"[cybersource_subscription] ✅ Added {amount} credits. New balance: {new_credit}")
                    
                    # Record subscription for future renewals
                    subs_ref = db.reference(f'subscriptions/{user_id}')
                    sub_id = f"SUB_{uuid.uuid4().hex[:12]}"
                    subs_ref.child(sub_id).set({
                        'subscription_id': sub_id,
                        'user_id': user_id,
                        'amount': amount,
                        'currency': currency,
                        'status': 'ACTIVE',
                        'provider': 'CYBERSOURCE',
                        'payment_id': payment_id,
                        'transaction_id': transaction_id,
                        'created_at': datetime.datetime.now(datetime.timezone.utc).isoformat(),
                        'next_billing_date': (datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(days=30)).isoformat(),
                        'billing_email': billing_info.get('email'),
                    })
                    
                    print(f"[cybersource_subscription] ✅ Subscription recorded: {sub_id}")
                    
                except Exception as e:
                    print(f"[cybersource_subscription] ⚠️ Failed to update records: {e}")
                
                return jsonify({
                    'success': True,
                    'subscription_id': sub_id,
                    'payment_id': payment_id,
                    'transaction_id': transaction_id,
                    'status': 'ACTIVE',
                    'amount': amount,
                    'currency': currency,
                    'message': 'Subscription created and payment processed successfully',
                }), 200
            
            else:
                # Payment failed
                error = result.get('error', 'Unknown error')
                
                # Update payment record
                try:
                    payments_ref.child(payment_id).update({
                        'status': 'FAILED',
                        'error': str(error),
                        'updated_at': datetime.datetime.now(datetime.timezone.utc).isoformat(),
                    })
                except Exception as e:
                    print(f"[cybersource_subscription] ⚠️ Failed to update payment record: {e}")
                
                return jsonify({
                    'success': False,
                    'error': str(error),
                    'payment_id': payment_id,
                }), 400
        
        except Exception as e:
            print(f"[cybersource_subscription] ❌ Payment processing error: {e}")
            import traceback
            print(f"[cybersource_subscription] Traceback: {traceback.format_exc()}")
            return jsonify({
                'success': False,
                'error': 'Payment processing failed',
            }), 500

    except (ValueError, TypeError) as e:
        print(f"[cybersource_subscription] ❌ Invalid request data: {e}")
        return jsonify({'success': False, 'error': 'Invalid request data'}), 400
    except Exception as e:
        print(f"[cybersource_subscription] ❌ Unexpected error: {e}")
        import traceback
        print(f"[cybersource_subscription] Traceback: {traceback.format_exc()}")
        return jsonify({'success': False, 'error': 'Subscription setup failed'}), 500


