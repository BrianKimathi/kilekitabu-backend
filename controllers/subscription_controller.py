"""Subscription controller for managing user credits and usage."""
import datetime
import uuid
from flask import request, jsonify, current_app
from functools import wraps
from firebase_admin import auth


def require_auth(f):
    """Decorator to require Firebase authentication."""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        try:
            db = current_app.config.get('DB')
            if db is None:
                return jsonify({'error': 'Authentication service unavailable'}), 503
            
            auth_header = request.headers.get('Authorization')
            if not auth_header or not auth_header.startswith('Bearer '):
                # Allow unauth testing when enabled
                cfg = current_app.config.get('CONFIG')
                if getattr(cfg, 'ALLOW_UNAUTH_TEST', False):
                    test_user = request.args.get('user_id') or (request.json or {}).get('user_id') if request.is_json else None
                    if test_user:
                        request.user_id = test_user
                        return f(*args, **kwargs)
                return jsonify({'error': 'No token provided'}), 401
            
            token = auth_header.split('Bearer ')[1]
            try:
                decoded_token = auth.verify_id_token(token)
                request.user_id = decoded_token['uid']
                return f(*args, **kwargs)
            except Exception as e:
                return jsonify({'error': 'Invalid Firebase token'}), 401
        except Exception as e:
            return jsonify({'error': 'Authentication service error'}), 500
    
    return decorated_function


def check_credit_required(f):
    """Decorator to check if user has credit before allowing action."""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        db = current_app.config.get('DB')
        config = current_app.config.get('CONFIG')
        user_id = request.user_id
        
        user_ref = db.reference(f'registeredUser/{user_id}')
        user_data = user_ref.get()
        
        if not user_data:
            return jsonify({'error': 'User not found'}), 404
        
        registration_date_str = user_data.get('registration_date')
        
        cfg = current_app.config.get('CONFIG')
        # Check free trial (unless force end enabled)
        if registration_date_str and not getattr(cfg, 'FORCE_TRIAL_END', False):
            registration_date = datetime.datetime.fromisoformat(
                registration_date_str.replace('Z', '+00:00')
            )
            trial_end = registration_date + datetime.timedelta(days=config.FREE_TRIAL_DAYS)
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


class SubscriptionController:
    """Controller for subscription and credit operations."""
    
    def __init__(self, db, config):
        self.db = db
        self.config = config
    
    def get_credit_info(self):
        """Get user's credit information."""
        user_id = request.user_id
        print(f"[get_credit_info] User ID: {user_id}")
        user_ref = self.db.reference(f'registeredUser/{user_id}')
        user_data = user_ref.get()
        print(f"[get_credit_info] User data: {user_data}")
        
        if not user_data:
            # Auto-register user if they don't exist
            try:
                user_info = auth.get_user(user_id)
                current_time = datetime.datetime.now(datetime.timezone.utc)
                
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
            registration_date = datetime.datetime.fromisoformat(
                registration_date_str.replace('Z', '+00:00')
            )
            trial_end = registration_date + datetime.timedelta(days=self.config.FREE_TRIAL_DAYS)
            current_time = datetime.datetime.now(datetime.timezone.utc)
            is_in_trial = current_time < trial_end
            trial_days_remaining = max(0, (trial_end - current_time).days)
        else:
            is_in_trial = False
            trial_days_remaining = 0
        
        credit_balance = user_data.get('credit_balance', 0)
        response_data = {
            'credit_balance': credit_balance,
            'is_in_trial': is_in_trial,
            'trial_days_remaining': trial_days_remaining,
            'last_usage_date': user_data.get('last_usage_date'),
            'total_payments': user_data.get('total_payments', 0)
        }
        print(f"[get_credit_info] Response: credit_balance={credit_balance}, is_in_trial={is_in_trial}, trial_days_remaining={trial_days_remaining}")
        return jsonify(response_data)
    
    def record_usage(self):
        """Record app usage and deduct credit."""
        user_id = request.user_id
        usage_data = request.json
        action_type = usage_data.get('action_type')
        
        user_ref = self.db.reference(f'registeredUser/{user_id}')
        user_data = user_ref.get()
        
        current_date = datetime.datetime.now(datetime.timezone.utc)
        last_usage_date_str = user_data.get('last_usage_date')
        last_payment_date_str = user_data.get('last_payment_date')
        
        # Check if this is a new day of usage
        should_deduct_credit = False
        if not last_usage_date_str:
            should_deduct_credit = True
        else:
            last_usage_date = datetime.datetime.fromisoformat(
                last_usage_date_str.replace('Z', '+00:00')
            )
            last_usage_date_only = last_usage_date.date()
            current_date_only = current_date.date()
            if current_date_only > last_usage_date_only:
                should_deduct_credit = True
        
        # Prevent credit deduction if payment was made today
        if last_payment_date_str:
            last_payment_date = datetime.datetime.fromisoformat(
                last_payment_date_str.replace('Z', '+00:00')
            )
            last_payment_date_only = last_payment_date.date()
            if current_date_only == last_payment_date_only:
                should_deduct_credit = False
        
        # Enforce monthly cap on chargeable usage
        charged_days_cap = int(self.config.MONTHLY_CAP_KES / self.config.DAILY_RATE)
        month_key = current_date.strftime('%Y-%m')
        monthly_charged = int((user_data.get('monthly_charged_days') or {}).get(month_key, 0))
        
        if should_deduct_credit and monthly_charged >= charged_days_cap:
            should_deduct_credit = False
        
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
            
            self.db.reference(f'usage_logs/{usage_id}').set(usage_info)
            
            # Track charged day for monthly cap accounting
            monthly = user_data.get('monthly_charged_days', {})
            monthly[month_key] = monthly_charged + 1
            user_ref.update({'monthly_charged_days': monthly})
        
        return jsonify({
            'message': 'Usage recorded',
            'credit_deducted': 1 if should_deduct_credit else 0,
            'remaining_credit': user_data.get('credit_balance', 0) - (1 if should_deduct_credit else 0)
        })

