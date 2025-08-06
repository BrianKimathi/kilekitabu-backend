from flask import Flask, request, jsonify
from flask_cors import CORS
import firebase_admin
from firebase_admin import credentials, db, auth
import datetime
import uuid
from functools import wraps
import os
from config import Config
from pesapal_integration import PesaPalIntegration

app = Flask(__name__)
app.config.from_object(Config)
CORS(app)

# Initialize Firebase Admin SDK with Realtime Database
cred = credentials.Certificate(Config.FIREBASE_CREDENTIALS_PATH)
firebase_admin.initialize_app(cred, {
    'databaseURL': Config.FIREBASE_DATABASE_URL
})

# Initialize PesaPal Integration
pesapal = PesaPalIntegration()

# Configuration
DAILY_RATE = Config.DAILY_RATE
FREE_TRIAL_DAYS = Config.FREE_TRIAL_DAYS

def require_auth(f):
    """Decorator to require Firebase authentication"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        auth_header = request.headers.get('Authorization')
        if not auth_header or not auth_header.startswith('Bearer '):
            return jsonify({'error': 'No token provided'}), 401
        
        token = auth_header.split('Bearer ')[1]
        try:
            # Verify Firebase ID token
            decoded_token = auth.verify_id_token(token)
            request.user_id = decoded_token['uid']
            return f(*args, **kwargs)
        except Exception as e:
            return jsonify({'error': 'Invalid Firebase token'}), 401
    
    return decorated_function

def check_credit_required(f):
    """Decorator to check if user has credit before allowing action"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        user_id = request.user_id
        
        # Get user data from Realtime Database
        user_ref = db.reference(f'users/{user_id}')
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



@app.route('/api/user/credit', methods=['GET'])
@require_auth
def get_credit_info():
    """Get user's credit information"""
    user_id = request.user_id
    user_ref = db.reference(f'users/{user_id}')
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

@app.route('/api/user/client', methods=['GET'])
@require_auth
def get_client_info():
    """Get client information (alias for credit info)"""
    user_id = request.user_id
    user_ref = db.reference(f'users/{user_id}')
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
    
    pesapal_response = pesapal.create_payment_request(payment_request_data)
    
    if pesapal_response:
        # Update payment record with PesaPal tracking ID
        db.collection('payments').document(payment_id).update({
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
        # Delete the payment record if PesaPal integration failed
        db.collection('payments').document(payment_id).delete()
        return jsonify({'error': 'Failed to create payment request'}), 500

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
        user_ref = db.reference(f'users/{user_id}')
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
    ipn_data = request.form.to_dict()
    
    # Process IPN data
    processed_data = pesapal.get_ipn_data(ipn_data)
    if not processed_data:
        return jsonify({'error': 'Invalid IPN data'}), 400
    
    payment_id = processed_data['payment_id']
    order_tracking_id = processed_data['order_tracking_id']
    status = processed_data['status']
    
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
        return jsonify({'error': 'Payment not found'}), 404
    
    user_id = payment_info['user_id']
    
    # Update payment status
    db.reference(f'payments/{payment_id}').update({
        'status': 'completed' if status == 'COMPLETED' else 'failed',
        'completed_at': datetime.datetime.now().isoformat(),
        'ipn_data': processed_data
    })
    
    if status == 'COMPLETED':
        # Add credit to user
        user_ref = db.reference(f'users/{user_id}')
        user_data = user_ref.get()
        
        current_credit = user_data.get('credit_balance', 0)
        new_credit = current_credit + payment_info['credit_days']
        total_payments = user_data.get('total_payments', 0) + payment_info['amount']
        
        user_ref.update({
            'credit_balance': new_credit,
            'total_payments': total_payments
        })
    
    return jsonify({'message': 'IPN processed successfully'})

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
        pesapal_status = pesapal.check_payment_status(payment_info['order_tracking_id'])
        if pesapal_status:
            # Update payment status if changed
            if pesapal_status['status'] == 'COMPLETED':
                payment_ref.update({
                    'status': 'completed',
                    'completed_at': datetime.datetime.now().isoformat()
                })
                
                # Add credit to user
                user_ref = db.reference(f'users/{user_id}')
                user_data = user_ref.get()
                
                current_credit = user_data.get('credit_balance', 0)
                new_credit = current_credit + payment_info['credit_days']
                total_payments = user_data.get('total_payments', 0) + payment_info['amount']
                
                user_ref.update({
                    'credit_balance': new_credit,
                    'total_payments': total_payments
                })
                
                return jsonify({
                    'status': 'completed',
                    'credit_added': payment_info['credit_days'],
                    'new_balance': new_credit
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
    
    user_ref = db.reference(f'users/{user_id}')
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



if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
