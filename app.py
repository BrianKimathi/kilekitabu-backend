from flask import Flask, request, jsonify
from flask_cors import CORS
import firebase_admin
from firebase_admin import credentials, db, auth
import datetime
import uuid
from functools import wraps
import os
from config import Config
from pesapal_integration_v2 import PesaPalIntegration

app = Flask(__name__)
app.config.from_object(Config)
CORS(app)

# Initialize Firebase Admin SDK with Realtime Database
try:
    cred = credentials.Certificate(Config.FIREBASE_CREDENTIALS_PATH)
    firebase_admin.initialize_app(cred, {
        'databaseURL': Config.FIREBASE_DATABASE_URL
    })
    print("Firebase initialized successfully")
except Exception as e:
    print(f"Firebase initialization error: {e}")
    # Continue without Firebase for now - this will cause issues but won't crash the app

# Initialize PesaPal Integration with error handling
try:
    pesapal = PesaPalIntegration()
    print("PesaPal integration initialized successfully")
except Exception as e:
    print(f"PesaPal initialization error: {e}")
    pesapal = None  # Set to None so we can check if it's available

# Configuration
DAILY_RATE = Config.DAILY_RATE
FREE_TRIAL_DAYS = Config.FREE_TRIAL_DAYS

def require_auth(f):
    """Decorator to require Firebase authentication"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        try:
            auth_header = request.headers.get('Authorization')
            if not auth_header or not auth_header.startswith('Bearer '):
                print("No Authorization header or invalid format")
                return jsonify({'error': 'No token provided'}), 401
            
            token = auth_header.split('Bearer ')[1]
            try:
                # Verify Firebase ID token
                print(f"Verifying token: {token[:20]}...")
                decoded_token = auth.verify_id_token(token)
                request.user_id = decoded_token['uid']
                print(f"Token verified successfully for user: {decoded_token['uid']}")
                return f(*args, **kwargs)
            except Exception as e:
                print(f"Token verification failed: {str(e)}")
                return jsonify({'error': 'Invalid Firebase token'}), 401
        except Exception as e:
            print(f"Authentication decorator error: {e}")
            return jsonify({'error': 'Authentication service error'}), 500
    
    return decorated_function

def check_credit_required(f):
    """Decorator to check if user has credit before allowing action"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        user_id = request.user_id
        
        # Get user data from Realtime Database
        user_ref = db.reference(f'registeredUser/{user_id}')
        user_data = user_ref.get()
        
        if not user_data:
            return jsonify({'error': 'User not found'}), 404
        
        registration_date_str = user_data.get('registration_date')
        
        # Check free trial
        if registration_date_str:
            registration_date = datetime.datetime.fromisoformat(registration_date_str.replace('Z', '+00:00'))
            trial_end = registration_date + datetime.timedelta(days=FREE_TRIAL_DAYS)
            if datetime.datetime.now(datetime.timezone.utc) < trial_end:
                return f(*args, **kwargs)
        
        # Check credit balance
        credit_balance = user_data.get('credit_balance', 0)
        if credit_balance <= 0:
            return jsonify({
                'error': 'Insufficient credit',
                'message': 'Please purchase credit to continue using the app',
                'required_payment': True
            }), 402
        
        return f(*args, **kwargs)
    
    return decorated_function

@app.route('/', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({
        'status': 'healthy',
        'service': 'KileKitabu Backend',
        'version': '1.0.0',
        'features': [
            'Usage-based payment system',
            'PesaPal integration',
            'Firebase authentication',
            'Credit management'
        ]
    })

@app.route('/test', methods=['GET'])
def test_endpoint():
    """Simple test endpoint without authentication"""
    return jsonify({
        'status': 'ok',
        'message': 'Backend is running',
        'timestamp': datetime.datetime.now().isoformat()
    })


@app.route('/api/user/credit', methods=['GET'])
@require_auth
def get_credit_info():
    """Get user's credit information"""
    user_id = request.user_id
    user_ref = db.reference(f'registeredUser/{user_id}')
    user_data = user_ref.get()
    
    if not user_data:
        # Auto-register user if they don't exist
        try:
            user_info = auth.get_user(user_id)
            current_time = datetime.datetime.now(datetime.timezone.utc)
            
            # Create user record
            user_data = {
                'user_id': user_id,
                'email': user_info.email,
                'registration_date': current_time.isoformat(),
                'credit_balance': 0,
                'total_payments': 0,
                'created_at': current_time.isoformat(),
                'updated_at': current_time.isoformat()
            }
            
            user_ref.set(user_data)
            
        except Exception as e:
            return jsonify({'error': f'Failed to create user: {str(e)}'}), 500
    
    registration_date_str = user_data.get('registration_date')
    
    # Check if in free trial
    if registration_date_str:
        registration_date = datetime.datetime.fromisoformat(registration_date_str.replace('Z', '+00:00'))
        trial_end = registration_date + datetime.timedelta(days=FREE_TRIAL_DAYS)
        current_time = datetime.datetime.now(datetime.timezone.utc)
        is_in_trial = current_time < trial_end
        trial_days_remaining = max(0, (trial_end - current_time).days)
    else:
        is_in_trial = False
        trial_days_remaining = 0
    
    return jsonify({
        'credit_balance': user_data.get('credit_balance', 0),
        'is_in_trial': is_in_trial,
        'trial_days_remaining': trial_days_remaining,
        'last_usage_date': user_data.get('last_usage_date'),
        'total_payments': user_data.get('total_payments', 0)
    })

@app.route('/api/user/client', methods=['GET'])
@require_auth
def get_client_info():
    """Get client information (alias for credit info)"""
    user_id = request.user_id
    user_ref = db.reference(f'registeredUser/{user_id}')
    user_data = user_ref.get()
    
    if not user_data:
        return jsonify({'error': 'User not found'}), 404
    
    registration_date_str = user_data.get('registration_date')
    
    # Check if in free trial
    if registration_date_str:
        registration_date = datetime.datetime.fromisoformat(registration_date_str.replace('Z', '+00:00'))
        trial_end = registration_date + datetime.timedelta(days=FREE_TRIAL_DAYS)
        current_time = datetime.datetime.now(datetime.timezone.utc)
        is_in_trial = current_time < trial_end
        trial_days_remaining = max(0, (trial_end - current_time).days)
    else:
        is_in_trial = False
        trial_days_remaining = 0
    
    return jsonify({
        'credit_balance': user_data.get('credit_balance', 0),
        'is_in_trial': is_in_trial,
        'trial_days_remaining': trial_days_remaining,
        'last_usage_date': user_data.get('last_usage_date'),
        'total_payments': user_data.get('total_payments', 0)
    })

@app.route('/api/payment/initiate', methods=['POST'])
@require_auth
def initiate_payment():
    """Initiate a payment through PesaPal"""
    user_id = request.user_id
    payment_data = request.json
    amount = payment_data.get('amount')
    
    if not amount or amount <= 0:
        return jsonify({'error': 'Invalid amount'}), 400
    # Enforce minimum amount per business rule
    if amount < Config.VALIDATION_RULES.get('min_amount', 10.0):
        return jsonify({'error': f'Minimum amount is KES {int(Config.VALIDATION_RULES.get("min_amount", 10))}'}), 400
    
    # Calculate credit days
    credit_days = int(amount / DAILY_RATE)
    
    # Create payment record
    payment_id = str(uuid.uuid4())
    payment_info = {
        'payment_id': payment_id,
        'user_id': user_id,
        'amount': amount,
        'credit_days': credit_days,
        'status': 'pending',
        'created_at': datetime.datetime.now().isoformat()
    }
    
    db.reference(f'payments/{payment_id}').set(payment_info)
    
    # Check if PesaPal is available
    if pesapal is None:
        return jsonify({
            'error': 'Payment service temporarily unavailable',
            'message': 'Please try again later or contact support'
        }), 503
    
    # Integrate with PesaPal API
    payment_request_data = {
        'payment_id': payment_id,
        'amount': amount,
        'credit_days': credit_days,
        'email': payment_data.get('email'),
        'phone': payment_data.get('phone'),
        'first_name': payment_data.get('first_name'),
        'last_name': payment_data.get('last_name')
    }
    
    try:
        pesapal_response = pesapal.create_payment_request(payment_request_data)
        
        if pesapal_response:
            # Update payment record with PesaPal tracking ID
            db.reference(f'payments/{payment_id}').update({
                'order_tracking_id': pesapal_response['order_tracking_id']
            })
            
            return jsonify({
                'payment_id': payment_id,
                'payment_url': pesapal_response['payment_url'],
                'amount': amount,
                'credit_days': credit_days,
                'status': 'pending'
            })
        else:
            # PesaPal integration failed, create a test payment for development
            print("PesaPal integration failed, creating test payment")
            
            # Update payment record for test payment
            db.reference(f'payments/{payment_id}').update({
                'order_tracking_id': f'test-{payment_id}',
                'status': 'test_payment'
            })
            
            # For development/testing, automatically complete the payment
            # In production, this should not happen
            if Config.DEBUG:
                # Simulate successful payment after 5 seconds
                import threading
                import time
                
                def complete_test_payment():
                    time.sleep(5)
                    # Update payment status
                    db.reference(f'payments/{payment_id}').update({
                        'status': 'completed',
                        'completed_at': datetime.datetime.now().isoformat()
                    })
                    
                    # Add credit to user
                    user_ref = db.reference(f'registeredUser/{user_id}')
                    user_data = user_ref.get()
                    
                    if user_data:
                        current_credit = user_data.get('credit_balance', 0)
                        new_credit = current_credit + credit_days
                        total_payments = user_data.get('total_payments', 0) + amount
                        
                        user_ref.update({
                            'credit_balance': new_credit,
                            'total_payments': total_payments,
                            'updated_at': datetime.datetime.now().isoformat()
                        })
                
                # Start test payment completion in background
                thread = threading.Thread(target=complete_test_payment)
                thread.daemon = True
                thread.start()
            
            return jsonify({
                'payment_id': payment_id,
                'payment_url': f"https://kilekitabu-backend.onrender.com/api/payment/test/{payment_id}",
                'amount': amount,
                'credit_days': credit_days,
                'status': 'test_payment',
                'message': 'Test payment created for development'
            })
            
    except Exception as e:
        print(f"Error in payment initiation: {e}")
        return jsonify({
            'error': 'Payment service error',
            'message': 'Unable to process payment request'
        }), 500

@app.route('/api/payment/confirm', methods=['POST'])
def confirm_payment():
    """Confirm payment from PesaPal webhook"""
    payment_data = request.json
    payment_id = payment_data.get('payment_id')
    status = payment_data.get('status')
    
    if not payment_id:
        return jsonify({'error': 'Payment ID required'}), 400
    
    payment_ref = db.reference(f'payments/{payment_id}')
    payment_data = payment_ref.get()
    if not payment_data:
        return jsonify({'error': 'Payment not found'}), 404
    
    payment_info = payment_data
    user_id = payment_info['user_id']
    
    if status == 'completed':
        # Update payment status
        payment_ref.update({
            'status': 'completed',
            'completed_at': datetime.datetime.now().isoformat()
        })
        
        # Add credit to user
        user_ref = db.reference(f'registeredUser/{user_id}')
        user_data = user_ref.get()
        
        current_credit = user_data.get('credit_balance', 0)
        new_credit = current_credit + payment_info['credit_days']
        total_payments = user_data.get('total_payments', 0) + payment_info['amount']
        
        user_ref.update({
            'credit_balance': new_credit,
            'total_payments': total_payments
        })
        
        return jsonify({
            'message': 'Payment confirmed',
            'credit_added': payment_info['credit_days'],
            'new_balance': new_credit
        })
    
    return jsonify({'message': 'Payment status updated'})

@app.route('/api/payment/ipn', methods=['POST'])
def pesapal_ipn():
    """Handle PesaPal IPN (Instant Payment Notification)"""
    print("🔔 IPN Notification Received")
    print(f"Headers: {dict(request.headers)}")
    print(f"Form data: {request.form.to_dict()}")
    print(f"JSON data: {request.get_json()}")
    
    # PesaPal can send data in either form format or JSON format
    ipn_data = request.form.to_dict()
    if not ipn_data:
        ipn_data = request.get_json() or {}
    
    if not ipn_data:
        print("❌ No IPN data received")
        # Return 200 to PesaPal even if no data (as per documentation)
        return jsonify({
            'status': 'error',
            'message': 'No IPN data received'
        }), 200
    
    print(f"📋 IPN Data: {ipn_data}")
    
    # Extract key information from PesaPal IPN
    order_tracking_id = ipn_data.get('OrderTrackingId')
    order_notification_type = ipn_data.get('OrderNotificationType', 'IPNCHANGE')
    order_merchant_reference = ipn_data.get('OrderMerchantReference')
    
    print(f"🔍 Extracted data:")
    print(f"   Order Tracking ID: {order_tracking_id}")
    print(f"   Order Notification Type: {order_notification_type}")
    print(f"   Order Merchant Reference: {order_merchant_reference}")
    
    if not order_tracking_id:
        print("❌ No OrderTrackingId in IPN data")
        # Return 200 to PesaPal even if missing data (as per documentation)
        return jsonify({
            'status': 'error',
            'message': 'Missing OrderTrackingId'
        }), 200
    
    # Find payment by order tracking ID
    payments_ref = db.reference('payments')
    payments_data = payments_ref.get()
    
    payment_info = None
    payment_id = None
    
    if payments_data:
        for pid, payment in payments_data.items():
            if payment.get('order_tracking_id') == order_tracking_id:
                payment_info = payment
                payment_id = pid
                break
    
    if not payment_info:
        print(f"❌ Payment not found for OrderTrackingId: {order_tracking_id}")
        # Return 200 to PesaPal even if payment not found (as per documentation)
        return jsonify({
            'orderNotificationType': order_notification_type,
            'orderTrackingId': order_tracking_id,
            'orderMerchantReference': order_merchant_reference,
            'status': 200
        }), 200
    
    print(f"✅ Found payment: {payment_id}")
    
    user_id = payment_info['user_id']
    
    try:
        # Use PesaPal API to get actual payment status
        if pesapal is not None:
            payment_status_response = pesapal.check_payment_status(order_tracking_id)
            
            if payment_status_response:
                print(f"📊 PesaPal API Response: {payment_status_response}")
                
                payment_status = payment_status_response.get('status')
                status_code = payment_status_response.get('status_code')
                amount = payment_status_response.get('amount')
                payment_method = payment_status_response.get('payment_method')
                confirmation_code = payment_status_response.get('confirmation_code')
                created_date = payment_status_response.get('created_date')
                payment_account = payment_status_response.get('payment_account')
                
                # Update payment with detailed information
                update_data = {
                    'status': 'completed' if status_code == 1 else 'failed',
                    'completed_at': datetime.datetime.now().isoformat(),
                    'ipn_data': ipn_data,
                    'pesapal_status': payment_status,
                    'pesapal_status_code': status_code,
                    'pesapal_amount': amount,
                    'payment_method': payment_method,
                    'confirmation_code': confirmation_code,
                    'created_date': created_date,
                    'payment_account': payment_account
                }
                
                db.reference(f'payments/{payment_id}').update(update_data)
                print(f"✅ Updated payment status to: {update_data['status']}")
                
                if status_code == 1:  # COMPLETED
                    # Add credit to user
                    user_ref = db.reference(f'registeredUser/{user_id}')
                    user_data = user_ref.get()
                    
                    current_credit = user_data.get('credit_balance', 0)
                    new_credit = current_credit + payment_info['credit_days']
                    total_payments = user_data.get('total_payments', 0) + payment_info['amount']
                    
                    user_ref.update({
                        'credit_balance': new_credit,
                        'total_payments': total_payments,
                        'updated_at': datetime.datetime.now().isoformat()
                    })
                    
                    print(f"✅ Added {payment_info['credit_days']} days credit to user {user_id}")
                    print(f"   New balance: {new_credit} days")
                    
                    # Return success response to PesaPal
                    return jsonify({
                        'orderNotificationType': order_notification_type,
                        'orderTrackingId': order_tracking_id,
                        'orderMerchantReference': order_merchant_reference,
                        'status': 200
                    }), 200
                else:
                    print(f"❌ Payment failed with status: {payment_status}")
                    # Return success response to PesaPal (we received the notification)
                    return jsonify({
                        'orderNotificationType': order_notification_type,
                        'orderTrackingId': order_tracking_id,
                        'orderMerchantReference': order_merchant_reference,
                        'status': 200
                    }), 200
            else:
                print("❌ Failed to get payment status from PesaPal API")
                # Return error response to PesaPal
                return jsonify({
                    'orderNotificationType': order_notification_type,
                    'orderTrackingId': order_tracking_id,
                    'orderMerchantReference': order_merchant_reference,
                    'status': 500
                }), 200
        else:
            print("❌ PesaPal integration not available")
            # Return error response to PesaPal
            return jsonify({
                'orderNotificationType': order_notification_type,
                'orderTrackingId': order_tracking_id,
                'orderMerchantReference': order_merchant_reference,
                'status': 500
            }), 200
            
    except Exception as e:
        print(f"❌ Error processing IPN: {e}")
        import traceback
        traceback.print_exc()
        # Return error response to PesaPal
        return jsonify({
            'orderNotificationType': order_notification_type,
            'orderTrackingId': order_tracking_id,
            'orderMerchantReference': order_merchant_reference,
            'status': 500
        }), 200

@app.route('/api/payment/callback', methods=['GET', 'POST'])
def payment_callback():
    """Handle PesaPal payment callback"""
    print("🔄 Payment Callback Received")
    print(f"Method: {request.method}")
    print(f"Query params: {request.args.to_dict()}")
    print(f"Form data: {request.form.to_dict()}")
    
    # Extract callback data
    order_tracking_id = request.args.get('OrderTrackingId')
    payment_status = request.args.get('PaymentStatus')
    
    print(f"📋 Callback Data:")
    print(f"   Order Tracking ID: {order_tracking_id}")
    print(f"   Payment Status: {payment_status}")
    
    if order_tracking_id:
        # Find and update payment
        payments_ref = db.reference('payments')
        payments_data = payments_ref.get()
        
        if payments_data:
            for pid, payment in payments_data.items():
                if payment.get('order_tracking_id') == order_tracking_id:
                    payment_ref = db.reference(f'payments/{pid}')
                    payment_ref.update({
                        'callback_status': payment_status,
                        'callback_received_at': datetime.datetime.now().isoformat()
                    })
                    print(f"✅ Updated payment {pid} with callback status: {payment_status}")
                    break
    
    # Redirect to frontend with status
    frontend_url = Config.FRONTEND_URL
    redirect_url = f"{frontend_url}/payment/status?orderTrackingId={order_tracking_id}&status={payment_status}"
    
    print(f"🔄 Redirecting to: {redirect_url}")
    return jsonify({
        'redirect_url': redirect_url,
        'message': 'Payment callback processed'
    })

@app.route('/api/payment/cancel', methods=['GET', 'POST'])
def payment_cancel():
    """Handle PesaPal payment cancellation"""
    print("❌ Payment Cancellation Received")
    print(f"Method: {request.method}")
    print(f"Query params: {request.args.to_dict()}")
    print(f"Form data: {request.form.to_dict()}")
    
    # Extract cancellation data
    order_tracking_id = request.args.get('OrderTrackingId')
    
    print(f"📋 Cancellation Data:")
    print(f"   Order Tracking ID: {order_tracking_id}")
    
    if order_tracking_id:
        # Find and update payment
        payments_ref = db.reference('payments')
        payments_data = payments_ref.get()
        
        if payments_data:
            for pid, payment in payments_data.items():
                if payment.get('order_tracking_id') == order_tracking_id:
                    payment_ref = db.reference(f'payments/{pid}')
                    payment_ref.update({
                        'status': 'cancelled',
                        'cancelled_at': datetime.datetime.now().isoformat()
                    })
                    print(f"✅ Updated payment {pid} as cancelled")
                    break
    
    # Redirect to frontend
    frontend_url = Config.FRONTEND_URL
    redirect_url = f"{frontend_url}/payment/cancelled?orderTrackingId={order_tracking_id}"
    
    print(f"🔄 Redirecting to: {redirect_url}")
    return jsonify({
        'redirect_url': redirect_url,
        'message': 'Payment cancelled'
    })

@app.route('/api/payment/status/<payment_id>', methods=['GET'])
@require_auth
def check_payment_status(payment_id):
    """Check payment status from PesaPal"""
    user_id = request.user_id
    
    # Get payment record
    payment_ref = db.reference(f'payments/{payment_id}')
    payment_data = payment_ref.get()
    if not payment_data:
        return jsonify({'error': 'Payment not found'}), 404
    
    payment_info = payment_data
    
    # Verify payment belongs to user
    if payment_info['user_id'] != user_id:
        return jsonify({'error': 'Unauthorized'}), 403
    
    # Check status from PesaPal if payment is pending
    if payment_info['status'] == 'pending' and payment_info.get('order_tracking_id'):
        try:
            pesapal_status = pesapal.check_payment_status(payment_info['order_tracking_id'])
            if pesapal_status:
                print(f"📊 PesaPal API Response for {payment_id}: {pesapal_status}")
                
                # Update payment status if changed
                if pesapal_status['status'] == 'COMPLETED' or pesapal_status.get('status_code') == 1:
                    payment_ref.update({
                        'status': 'completed',
                        'completed_at': datetime.datetime.now().isoformat(),
                        'pesapal_status': pesapal_status.get('status'),
                        'pesapal_status_code': pesapal_status.get('status_code'),
                        'payment_method': pesapal_status.get('payment_method'),
                        'confirmation_code': pesapal_status.get('confirmation_code')
                    })
                    
                    # Add credit to user
                    user_ref = db.reference(f'registeredUser/{user_id}')
                    user_data = user_ref.get()
                    
                    current_credit = user_data.get('credit_balance', 0)
                    new_credit = current_credit + payment_info['credit_days']
                    total_payments = user_data.get('total_payments', 0) + payment_info['amount']
                    
                    user_ref.update({
                        'credit_balance': new_credit,
                        'total_payments': total_payments,
                        'updated_at': datetime.datetime.now().isoformat()
                    })
                    
                    print(f"✅ Added {payment_info['credit_days']} days credit to user {user_id}")
                    print(f"   New balance: {new_credit} days")
                    
                    return jsonify({
                        'status': 'completed',
                        'credit_added': payment_info['credit_days'],
                        'new_balance': new_credit
                    })
                elif pesapal_status['status'] == 'FAILED' or pesapal_status.get('status_code') == 2:
                    payment_ref.update({
                        'status': 'failed',
                        'completed_at': datetime.datetime.now().isoformat(),
                        'pesapal_status': pesapal_status.get('status'),
                        'pesapal_status_code': pesapal_status.get('status_code')
                    })
                    return jsonify({
                        'status': 'failed',
                        'message': 'Payment failed'
                    })
                else:
                    # Payment still pending
                    return jsonify({
                        'status': 'pending',
                        'message': 'Payment is still being processed'
                    })
            else:
                print(f"❌ Failed to get PesaPal status for payment {payment_id}")
                return jsonify({
                    'status': 'pending',
                    'message': 'Unable to check payment status from PesaPal'
                })
        except Exception as e:
            print(f"❌ Error checking PesaPal status for payment {payment_id}: {e}")
            import traceback
            traceback.print_exc()
            return jsonify({
                'status': 'pending',
                'message': 'Error checking payment status'
            })
    
    return jsonify({
        'payment_id': payment_id,
        'status': payment_info['status'],
        'amount': payment_info['amount'],
        'credit_days': payment_info['credit_days'],
        'created_at': payment_info['created_at'].isoformat() if payment_info.get('created_at') else None
    })

@app.route('/api/usage/record', methods=['POST'])
@require_auth
@check_credit_required
def record_usage():
    """Record app usage and deduct credit"""
    user_id = request.user_id
    usage_data = request.json
    action_type = usage_data.get('action_type')  # e.g., 'add_debt', 'view_debt', etc.
    
    user_ref = db.reference(f'registeredUser/{user_id}')
    user_data = user_ref.get()
    
    current_date = datetime.datetime.now(datetime.timezone.utc)
    last_usage_date_str = user_data.get('last_usage_date')
    
    # Check if this is a new day of usage
    should_deduct_credit = False
    if not last_usage_date_str:
        should_deduct_credit = True
    else:
        # Convert to date for comparison
        last_usage_date = datetime.datetime.fromisoformat(last_usage_date_str.replace('Z', '+00:00'))
        last_usage_date_only = last_usage_date.date()
        current_date_only = current_date.date()
        if current_date_only > last_usage_date_only:
            should_deduct_credit = True
    
    if should_deduct_credit:
        # Deduct one day of credit
        current_credit = user_data.get('credit_balance', 0)
        new_credit = current_credit - 1
        
        user_ref.update({
            'credit_balance': new_credit,
            'last_usage_date': current_date.isoformat()
        })
        
        # Record usage
        usage_id = str(uuid.uuid4())
        usage_info = {
            'usage_id': usage_id,
            'user_id': user_id,
            'action_type': action_type,
            'credit_deducted': 1,
            'remaining_credit': new_credit,
            'timestamp': current_date.isoformat()
        }
        
        db.reference(f'usage_logs/{usage_id}').set(usage_info)
    
    return jsonify({
        'message': 'Usage recorded',
        'credit_deducted': 1 if should_deduct_credit else 0,
        'remaining_credit': user_data.get('credit_balance', 0) - (1 if should_deduct_credit else 0)
    })

@app.route('/api/payment/complete/<payment_id>', methods=['POST'])
@require_auth
def manually_complete_payment(payment_id):
    """Manually complete a payment for testing purposes"""
    user_id = request.user_id
    
    # Get payment record
    payment_ref = db.reference(f'payments/{payment_id}')
    payment_data = payment_ref.get()
    if not payment_data:
        return jsonify({'error': 'Payment not found'}), 404
    
    payment_info = payment_data
    
    # Verify payment belongs to user
    if payment_info['user_id'] != user_id:
        return jsonify({'error': 'Unauthorized'}), 403
    
    # Check if payment is already completed
    if payment_info['status'] == 'completed':
        return jsonify({'error': 'Payment already completed'}), 400
    
    try:
        # Mark payment as completed
        payment_ref.update({
            'status': 'completed',
            'completed_at': datetime.datetime.now().isoformat(),
            'manually_completed': True
        })
        
        # Add credit to user
        user_ref = db.reference(f'registeredUser/{user_id}')
        user_data = user_ref.get()
        
        current_credit = user_data.get('credit_balance', 0)
        new_credit = current_credit + payment_info['credit_days']
        total_payments = user_data.get('total_payments', 0) + payment_info['amount']
        
        user_ref.update({
            'credit_balance': new_credit,
            'total_payments': total_payments,
            'updated_at': datetime.datetime.now().isoformat()
        })
        
        print(f"✅ Manually completed payment {payment_id} for user {user_id}")
        print(f"   Added {payment_info['credit_days']} days credit")
        print(f"   New balance: {new_credit} days")
        
        return jsonify({
            'status': 'completed',
            'credit_added': payment_info['credit_days'],
            'new_balance': new_credit,
            'message': 'Payment manually completed for testing'
        })
        
    except Exception as e:
        print(f"❌ Error manually completing payment {payment_id}: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': 'Failed to complete payment'}), 500

@app.route('/api/payment/debug', methods=['GET'])
@require_auth
def debug_payments():
    """Debug endpoint to check all payments for a user"""
    user_id = request.user_id
    
    try:
        # Get all payments for the user
        payments_ref = db.reference('payments')
        payments_data = payments_ref.get()
        
        user_payments = []
        if payments_data:
            for pid, payment in payments_data.items():
                if payment.get('user_id') == user_id:
                    user_payments.append({
                        'payment_id': pid,
                        'status': payment.get('status'),
                        'amount': payment.get('amount'),
                        'credit_days': payment.get('credit_days'),
                        'order_tracking_id': payment.get('order_tracking_id'),
                        'created_at': payment.get('created_at'),
                        'completed_at': payment.get('completed_at'),
                        'pesapal_status': payment.get('pesapal_status'),
                        'pesapal_status_code': payment.get('pesapal_status_code')
                    })
        
        # Get user credit info
        user_ref = db.reference(f'registeredUser/{user_id}')
        user_data = user_ref.get()
        
        credit_info = {
            'credit_balance': user_data.get('credit_balance', 0) if user_data else 0,
            'is_in_trial': user_data.get('is_in_trial', False) if user_data else False,
            'trial_days_remaining': user_data.get('trial_days_remaining', 0) if user_data else 0,
            'total_payments': user_data.get('total_payments', 0) if user_data else 0,
            'last_usage_date': user_data.get('last_usage_date') if user_data else None
        }
        
        return jsonify({
            'user_id': user_id,
            'payments': user_payments,
            'credit_info': credit_info,
            'total_payments_count': len(user_payments)
        })
        
    except Exception as e:
        print(f"❌ Error in debug payments: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': 'Failed to get debug info'}), 500

@app.route('/api/payment/force-ipn/<payment_id>', methods=['POST'])
@require_auth
def force_ipn_retry(payment_id):
    """Force IPN retry for a specific payment"""
    user_id = request.user_id
    
    # Get payment record
    payment_ref = db.reference(f'payments/{payment_id}')
    payment_data = payment_ref.get()
    if not payment_data:
        return jsonify({'error': 'Payment not found'}), 404
    
    payment_info = payment_data
    
    # Verify payment belongs to user
    if payment_info['user_id'] != user_id:
        return jsonify({'error': 'Unauthorized'}), 403
    
    # Check if payment has order tracking ID
    order_tracking_id = payment_info.get('order_tracking_id')
    if not order_tracking_id:
        return jsonify({'error': 'Payment has no order tracking ID'}), 400
    
    try:
        # Force check payment status from PesaPal
        if pesapal is not None:
            payment_status_response = pesapal.check_payment_status(order_tracking_id)
            
            if payment_status_response:
                print(f"📊 Forced PesaPal API Response for {payment_id}: {payment_status_response}")
                
                payment_status = payment_status_response.get('status')
                status_code = payment_status_response.get('status_code')
                
                # Update payment status if changed
                if payment_status == 'COMPLETED' or status_code == 1:
                    payment_ref.update({
                        'status': 'completed',
                        'completed_at': datetime.datetime.now().isoformat(),
                        'pesapal_status': payment_status,
                        'pesapal_status_code': status_code,
                        'force_checked': True
                    })
                    
                    # Add credit to user
                    user_ref = db.reference(f'registeredUser/{user_id}')
                    user_data = user_ref.get()
                    
                    current_credit = user_data.get('credit_balance', 0)
                    new_credit = current_credit + payment_info['credit_days']
                    total_payments = user_data.get('total_payments', 0) + payment_info['amount']
                    
                    user_ref.update({
                        'credit_balance': new_credit,
                        'total_payments': total_payments,
                        'updated_at': datetime.datetime.now().isoformat()
                    })
                    
                    print(f"✅ Force IPN: Added {payment_info['credit_days']} days credit to user {user_id}")
                    print(f"   New balance: {new_credit} days")
                    
                    return jsonify({
                        'status': 'completed',
                        'credit_added': payment_info['credit_days'],
                        'new_balance': new_credit,
                        'message': 'Payment completed via force IPN retry'
                    })
                else:
                    return jsonify({
                        'status': 'pending',
                        'message': f'Payment still pending. PesaPal status: {payment_status}'
                    })
            else:
                return jsonify({
                    'error': 'Failed to get payment status from PesaPal'
                }), 500
        else:
            return jsonify({
                'error': 'PesaPal integration not available'
            }), 500
            
    except Exception as e:
        print(f"❌ Error in force IPN retry for payment {payment_id}: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': 'Failed to force IPN retry'}), 500


if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
