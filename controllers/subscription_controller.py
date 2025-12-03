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
                print("[Auth] ❌ DB not configured; auth unavailable")
                return jsonify({'error': 'Authentication service unavailable'}), 503
            
            auth_header = request.headers.get('Authorization')
            print(f"[Auth] Checking authentication for {request.path}")
            print(f"[Auth] Authorization header present: {bool(auth_header)}")
            if not auth_header or not auth_header.startswith('Bearer '):
                # Allow unauth testing when enabled
                cfg = current_app.config.get('CONFIG')
                if getattr(cfg, 'ALLOW_UNAUTH_TEST', False):
                    test_user = request.args.get('user_id') or (request.json or {}).get('user_id') if request.is_json else None
                    if test_user:
                        print(f"[Auth] ALLOW_UNAUTH_TEST enabled, using test user_id={test_user}")
                        request.user_id = test_user
                        return f(*args, **kwargs)
                print("[Auth] ❌ No Bearer token provided")
                return jsonify({'error': 'No token provided'}), 401
            
            token = auth_header.split('Bearer ')[1]
            try:
                print(f"[Auth] Attempting to verify Firebase ID token...")
                decoded_token = auth.verify_id_token(token)
                request.user_id = decoded_token['uid']
                print(f"[Auth] ✅ Token verified successfully, User ID: {request.user_id}")
                return f(*args, **kwargs)
            except Exception as e:
                error_str = str(e)
                error_type = type(e).__name__
                print(f"[Auth] ❌ Firebase token verification failed: {error_type}: {error_str}")
                
                # Handle clock skew errors (token used too early/late)
                # For small clock skews (1-5 seconds), wait and retry
                if 'clock' in error_str.lower() or 'too early' in error_str.lower() or 'too late' in error_str.lower():
                    print(f"[Auth] ⚠️ Clock skew detected, checking time difference...")
                    import re
                    time_match = re.search(r'(\d+) < (\d+)', error_str)
                    if time_match:
                        token_time = int(time_match.group(1))
                        server_time = int(time_match.group(2))
                        diff = abs(server_time - token_time)
                        print(f"[Auth] ⚠️ Time difference: {diff} seconds (token_time={token_time}, server_time={server_time})")
                        
                        if diff <= 5:  # Allow up to 5 seconds difference
                            print(f"[Auth] ⚠️ Small clock skew ({diff}s) detected, waiting {diff + 1} seconds and retrying...")
                            import time as time_module
                            time_module.sleep(diff + 1)  # Wait for the time difference + 1 second buffer
                            try:
                                print(f"[Auth] Retrying token verification after delay...")
                                decoded_token = auth.verify_id_token(token)
                                request.user_id = decoded_token['uid']
                                print(f"[Auth] ✅ Token verified after delay, User ID: {request.user_id}")
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
                            request.user_id = decoded_token['uid']
                            print(f"[Auth] ✅ Token verified after delay, User ID: {request.user_id}")
                            return f(*args, **kwargs)
                        except Exception as retry_error:
                            print(f"[Auth] ❌ Retry after delay failed: {retry_error}")
                
                return jsonify({'error': 'Invalid Firebase token', 'details': error_str}), 401
        except Exception as e:
            print(f"[Auth] ❌ Authentication service error: {e}")
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
        
        current_time = datetime.datetime.now(datetime.timezone.utc)
        
        if not user_data:
            # Auto-register new user with fresh trial
            try:
                user_info = auth.get_user(user_id)
                
                user_data = {
                    'user_id': user_id,
                    'email': user_info.email,
                    'registration_date': current_time.isoformat(),  # Start fresh trial
                    'credit_balance': 0,
                    'total_payments': 0,
                    'created_at': current_time.isoformat(),
                    'updated_at': current_time.isoformat()
                }
                
                user_ref.set(user_data)
                print(f"[get_credit_info] New user {user_id} registered with fresh trial starting {current_time.isoformat()}")
            except Exception as e:
                return jsonify({'error': f'Failed to create user: {str(e)}'}), 500
        
        # Check if user needs a fresh trial reset
        # Strategy: Reset ALL users (existing and new) to get fresh 14-day trial
        registration_date_str = user_data.get('registration_date')
        should_reset = False
        
        # Always reset if user doesn't have registration_date (old users from export)
        if not registration_date_str:
            should_reset = True
            print(f"[get_credit_info] User {user_id} missing registration_date - resetting for fresh trial")
        
        # Also reset if RESET_USERS_ON_LOGIN is enabled (for all existing users)
        elif getattr(self.config, 'RESET_USERS_ON_LOGIN', False):
            # Check if user has already been reset in this reset cycle
            trial_reset_date_str = user_data.get('trial_reset_date')
            if not trial_reset_date_str:
                # User hasn't been reset yet in this cycle, reset them now
                should_reset = True
                print(f"[get_credit_info] User {user_id} needs reset (RESET_USERS_ON_LOGIN enabled)")
            else:
                # Check if reset was before the current reset date threshold
                try:
                    reset_date = datetime.datetime.fromisoformat(trial_reset_date_str.replace('Z', '+00:00'))
                    # If reset was more than 14 days ago, allow another reset
                    days_since_reset = (current_time - reset_date).days
                    if days_since_reset >= self.config.FREE_TRIAL_DAYS:
                        should_reset = True
                        print(f"[get_credit_info] User {user_id} trial expired ({days_since_reset} days ago) - resetting")
                except Exception as e:
                    print(f"[get_credit_info] Error parsing trial_reset_date: {e}")
                    should_reset = True  # Reset if we can't parse the date
        
        # Reset user for fresh trial if needed
        if should_reset:
            print(f"[get_credit_info] 🔄 Resetting user {user_id} for fresh 14-day trial")
            reset_time = datetime.datetime.now(datetime.timezone.utc)
            
            # Reset trial-related fields but keep payment history and user info
            update_data = {
                'registration_date': reset_time.isoformat(),  # New registration date = now (starts fresh trial)
                'trial_reset_date': reset_time.isoformat(),  # Track when reset happened
                'credit_balance': 0,  # Reset credit balance to 0
                'last_usage_date': None,  # Reset usage tracking
                'updated_at': reset_time.isoformat(),
                # Keep payment history (total_payments, monthly_paid) for accounting
                # Keep user info (name, email, phone, profileImageUri, etc.)
            }
            
            user_ref.update(update_data)
            user_data.update(update_data)
            print(f"[get_credit_info] ✅ User {user_id} reset successfully. Fresh trial starts: {reset_time.isoformat()}")
        
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
        max_prepay_months = getattr(self.config, 'MAX_PREPAY_MONTHS', 12)
        response_data = {
            'credit_balance': credit_balance,
            'is_in_trial': is_in_trial,
            'trial_days_remaining': trial_days_remaining,
            'last_usage_date': user_data.get('last_usage_date'),
            'total_payments': user_data.get('total_payments', 0),
            'billing_config': {
                'daily_rate_kes': self.config.DAILY_RATE,
                'monthly_cap_kes': self.config.MONTHLY_CAP_KES,
                'max_prepay_months': max_prepay_months,
                'max_top_up_kes': self.config.MONTHLY_CAP_KES * max_prepay_months
            }
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

