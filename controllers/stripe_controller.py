"""Stripe payment controller."""
import datetime
import uuid
from flask import request, jsonify, current_app
from controllers.subscription_controller import require_auth


class StripeController:
    """Controller for Stripe payment operations."""
    
    def __init__(self, db, config):
        self.db = db
        self.config = config
    
    @require_auth
    def create_payment_intent(self):
        """
        Create a Stripe PaymentIntent for card or Google Pay.
        
        Expected request body:
        {
            "amount": 10.0,
            "currency": "USD",
            "payment_method_id": "pm_...",  // Optional, for Google Pay or saved cards
            "metadata": {}  // Optional
        }
        """
        try:
            if not self.db:
                return jsonify({'error': 'Database unavailable'}), 503
            
            stripe_client = current_app.config.get('stripe_client')
            if not stripe_client:
                return jsonify({'error': 'Stripe not configured'}), 503
            
            data = request.get_json(force=True) or {}
            amount = float(data.get('amount') or 0)
            currency = (data.get('currency') or 'USD').upper()
            payment_method_id = data.get('payment_method_id')
            metadata = data.get('metadata') or {}
            
            user_id = getattr(request, 'user_id', None)
            payment_id = str(uuid.uuid4())
            
            # Add metadata
            metadata['user_id'] = user_id
            metadata['payment_id'] = payment_id
            
            print(f"[stripe_create_intent] user_id={user_id} amount={amount} {currency}")
            
            # Create PaymentIntent
            result = stripe_client.create_payment_intent(
                amount=amount,
                currency=currency.lower(),
                payment_method_id=payment_method_id,
                payment_method_types=['card'],
                metadata=metadata,
            )
            
            if not result.get('ok'):
                return jsonify({
                    'success': False,
                    'error': result.get('error', 'Payment intent creation failed'),
                }), result.get('status_code', 500)
            
            # Store payment record
            payment_info = {
                'payment_id': payment_id,
                'user_id': user_id,
                'amount': amount,
                'currency': currency,
                'status': 'pending',
                'provider': 'stripe',
                'stripe_payment_intent_id': result['response']['id'],
                'created_at': datetime.datetime.now(datetime.timezone.utc).isoformat(),
            }
            self.db.reference(f'payments/{payment_id}').set(payment_info)
            
            return jsonify({
                'success': True,
                'payment_intent': {
                    'id': result['response']['id'],
                    'client_secret': result['response']['client_secret'],
                    'status': result['response']['status'],
                },
                'payment_id': payment_id,
            }), 200
            
        except Exception as e:
            import traceback
            print(f"[stripe_create_intent] ERROR: {e}")
            traceback.print_exc()
            return jsonify({'error': 'Internal server error', 'message': str(e)}), 500
    
    @require_auth
    def confirm_payment(self):
        """
        Confirm a PaymentIntent (for Google Pay or card payments).
        
        Expected request body:
        {
            "payment_intent_id": "pi_...",
            "payment_method_id": "pm_..."  // Optional
        }
        """
        try:
            if not self.db:
                return jsonify({'error': 'Database unavailable'}), 503
            
            stripe_client = current_app.config.get('stripe_client')
            if not stripe_client:
                return jsonify({'error': 'Stripe not configured'}), 503
            
            data = request.get_json(force=True) or {}
            payment_intent_id = data.get('payment_intent_id')
            payment_method_id = data.get('payment_method_id')
            
            if not payment_intent_id:
                return jsonify({'error': 'payment_intent_id is required'}), 400
            
            user_id = getattr(request, 'user_id', None)
            
            print(f"[stripe_confirm] user_id={user_id} payment_intent_id={payment_intent_id}")
            
            # Confirm PaymentIntent
            result = stripe_client.confirm_payment_intent(
                payment_intent_id=payment_intent_id,
                payment_method_id=payment_method_id,
            )
            
            if not result.get('ok'):
                return jsonify({
                    'success': False,
                    'error': result.get('error', 'Payment confirmation failed'),
                }), result.get('status_code', 500)
            
            # Retrieve payment intent to get metadata
            intent_result = stripe_client.retrieve_payment_intent(payment_intent_id)
            if not intent_result.get('ok'):
                return jsonify({
                    'success': False,
                    'error': 'Failed to retrieve payment intent',
                }), 500
            
            intent_data = intent_result['response']
            metadata = intent_data.get('metadata', {})
            payment_id = metadata.get('payment_id')
            user_id_from_metadata = metadata.get('user_id')
            
            # Use user_id from metadata if available, otherwise from request
            effective_user_id = user_id_from_metadata or user_id
            
            resp = result.get('response', {})
            status = (resp.get('status') or '').lower()
            credit_days = None
            
            # If payment succeeded, update credits
            if status == 'succeeded' and payment_id and effective_user_id:
                now_iso = datetime.datetime.now(datetime.timezone.utc).isoformat()
                amount = intent_data.get('amount', 0) / 100  # Convert from cents
                currency = intent_data.get('currency', 'USD').upper()
                
                # Compute credit days
                daily_rate = float(getattr(self.config, 'DAILY_RATE', 5.0))
                credit_days = max(1, int(amount / daily_rate)) if daily_rate > 0 else int(amount)
                
                # Update user credit
                try:
                    user_ref = self.db.reference(f'users/{effective_user_id}')
                    user_data = user_ref.get() or {}
                    current_credit = int(float(user_data.get('credit_balance', 0) or 0))
                    
                    # Monthly spend tracking
                    month_key = datetime.datetime.now(datetime.timezone.utc).strftime('%Y-%m')
                    monthly = user_data.get('monthly_paid', {}) or {}
                    monthly[month_key] = float(monthly.get(month_key, 0) or 0) + float(amount)
                    
                    new_credit = current_credit + credit_days
                    user_ref.update({
                        'credit_balance': int(new_credit),
                        'total_payments': float(user_data.get('total_payments', 0) or 0) + float(amount),
                        'monthly_paid': monthly,
                        'last_payment_date': now_iso,
                        'updated_at': now_iso,
                    })
                    
                    print(f"[stripe_confirm] ✅ Updated user credit: {effective_user_id}, added {credit_days} days")
                except Exception as ue:
                    print(f"[stripe_confirm] ⚠️ User credit update error: {ue}")
                
                # Update payment record
                if payment_id:
                    try:
                        payment_ref = self.db.reference(f'payments/{payment_id}')
                        payment_ref.update({
                            'status': 'completed',
                            'provider': 'stripe',
                            'stripe_payment_intent_id': payment_intent_id,
                            'credit_days': credit_days,
                            'completed_at': now_iso,
                            'updated_at': now_iso,
                        })
                        print(f"[stripe_confirm] ✅ Updated payment record: {payment_id}")
                    except Exception as pe:
                        print(f"[stripe_confirm] ⚠️ Payment record update error: {pe}")
            
            return jsonify({
                'success': True,
                'payment_intent': {
                    'id': result['response']['id'],
                    'status': result['response']['status'],
                },
                'payment_id': payment_id,
                'credit_days': credit_days,
            }), 200
            
        except Exception as e:
            import traceback
            print(f"[stripe_confirm] ERROR: {e}")
            traceback.print_exc()
            return jsonify({'error': 'Internal server error', 'message': str(e)}), 500
    
    @require_auth
    def charge_card(self):
        """
        Charge a card directly (create and confirm in one step).
        
        Expected request body:
        {
            "amount": 10.0,
            "currency": "USD",
            "payment_method_id": "pm_...",
            "metadata": {}  // Optional
        }
        """
        try:
            if not self.db:
                return jsonify({'error': 'Database unavailable'}), 503
            
            stripe_client = current_app.config.get('stripe_client')
            if not stripe_client:
                return jsonify({'error': 'Stripe not configured'}), 503
            
            data = request.get_json(force=True) or {}
            amount = float(data.get('amount') or 0)
            currency = (data.get('currency') or 'USD').upper()
            payment_method_id = data.get('payment_method_id')
            metadata = data.get('metadata') or {}
            
            if not payment_method_id:
                return jsonify({'error': 'payment_method_id is required'}), 400
            
            user_id = getattr(request, 'user_id', None)
            payment_id = str(uuid.uuid4())
            
            # Add metadata
            metadata['user_id'] = user_id
            metadata['payment_id'] = payment_id
            
            print(f"[stripe_charge_card] user_id={user_id} amount={amount} {currency}")
            
            # Create and confirm payment
            result = stripe_client.create_payment_with_card(
                amount=amount,
                currency=currency.lower(),
                payment_method_id=payment_method_id,
                metadata=metadata,
            )
            
            if not result.get('ok'):
                # Store failed payment
                payment_info = {
                    'payment_id': payment_id,
                    'user_id': user_id,
                    'amount': amount,
                    'currency': currency,
                    'status': 'failed',
                    'provider': 'stripe',
                    'provider_error': result.get('error'),
                    'created_at': datetime.datetime.now(datetime.timezone.utc).isoformat(),
                }
                self.db.reference(f'payments/{payment_id}').set(payment_info)
                
                return jsonify({
                    'success': False,
                    'payment_id': payment_id,
                    'error': result.get('error', 'Payment failed'),
                }), result.get('status_code', 500)
            
            # Success - update user credit
            now_iso = datetime.datetime.now(datetime.timezone.utc).isoformat()
            daily_rate = float(getattr(self.config, 'DAILY_RATE', 5.0))
            credit_days = max(1, int(amount / daily_rate)) if daily_rate > 0 else int(amount)
            
            try:
                user_ref = self.db.reference(f'users/{user_id}')
                user_data = user_ref.get() or {}
                current_credit = int(float(user_data.get('credit_balance', 0) or 0))
                
                # Monthly spend tracking
                month_key = datetime.datetime.now(datetime.timezone.utc).strftime('%Y-%m')
                monthly = user_data.get('monthly_paid', {}) or {}
                monthly[month_key] = float(monthly.get(month_key, 0) or 0) + float(amount)
                
                new_credit = current_credit + credit_days
                user_ref.update({
                    'credit_balance': int(new_credit),
                    'total_payments': float(user_data.get('total_payments', 0) or 0) + float(amount),
                    'monthly_paid': monthly,
                    'last_payment_date': now_iso,
                    'updated_at': now_iso,
                })
            except Exception as ue:
                print(f"[stripe_charge_card] ⚠️ User credit update error: {ue}")
            
            # Store payment record
            payment_info = {
                'payment_id': payment_id,
                'user_id': user_id,
                'amount': amount,
                'currency': currency,
                'status': 'completed',
                'provider': 'stripe',
                'stripe_payment_intent_id': result['response']['id'],
                'credit_days': credit_days,
                'created_at': now_iso,
                'completed_at': now_iso,
            }
            self.db.reference(f'payments/{payment_id}').set(payment_info)
            
            return jsonify({
                'success': True,
                'payment_id': payment_id,
                'status': 'completed',
                'credit_days': credit_days,
            }), 200
            
        except Exception as e:
            import traceback
            print(f"[stripe_charge_card] ERROR: {e}")
            traceback.print_exc()
            return jsonify({'error': 'Internal server error', 'message': str(e)}), 500
    
    def handle_webhook(self):
        """
        Handle Stripe webhook events.
        
        This endpoint should NOT require authentication (Stripe signs the request).
        """
        try:
            if not self.db:
                return jsonify({'error': 'Database unavailable'}), 503
            
            stripe_client = current_app.config.get('stripe_client')
            if not stripe_client:
                return jsonify({'error': 'Stripe not configured'}), 503
            
            # Get raw request body and signature
            payload = request.get_data()
            signature = request.headers.get('Stripe-Signature')
            
            if not signature:
                return jsonify({'error': 'Missing Stripe-Signature header'}), 400
            
            # Verify webhook signature
            event = stripe_client.verify_webhook_signature(payload, signature)
            
            if not event:
                return jsonify({'error': 'Invalid webhook signature'}), 400
            
            print(f"[stripe_webhook] Processing event: {event.type} (ID: {event.id})")
            
            # Handle different event types
            if event.type == 'payment_intent.succeeded':
                payment_intent = event.data.object
                payment_intent_id = payment_intent.id
                
                # Get metadata
                metadata = payment_intent.metadata or {}
                payment_id = metadata.get('payment_id')
                user_id = metadata.get('user_id')
                
                if payment_id and user_id:
                    # Update payment record
                    payment_ref = self.db.reference(f'payments/{payment_id}')
                    payment_data = payment_ref.get() or {}
                    
                    amount = payment_intent.amount / 100  # Convert from cents
                    currency = payment_intent.currency.upper()
                    
                    now_iso = datetime.datetime.now(datetime.timezone.utc).isoformat()
                    daily_rate = float(getattr(self.config, 'DAILY_RATE', 5.0))
                    credit_days = max(1, int(amount / daily_rate)) if daily_rate > 0 else int(amount)
                    
                    # Update payment status
                    payment_ref.update({
                        'status': 'completed',
                        'stripe_payment_intent_id': payment_intent_id,
                        'credit_days': credit_days,
                        'completed_at': now_iso,
                        'updated_at': now_iso,
                    })
                    
                    # Update user credit if not already updated
                    if payment_data.get('status') != 'completed':
                        try:
                            user_ref = self.db.reference(f'users/{user_id}')
                            user_data = user_ref.get() or {}
                            current_credit = int(float(user_data.get('credit_balance', 0) or 0))
                            
                            # Monthly spend tracking
                            month_key = datetime.datetime.now(datetime.timezone.utc).strftime('%Y-%m')
                            monthly = user_data.get('monthly_paid', {}) or {}
                            monthly[month_key] = float(monthly.get(month_key, 0) or 0) + float(amount)
                            
                            new_credit = current_credit + credit_days
                            user_ref.update({
                                'credit_balance': int(new_credit),
                                'total_payments': float(user_data.get('total_payments', 0) or 0) + float(amount),
                                'monthly_paid': monthly,
                                'last_payment_date': now_iso,
                                'updated_at': now_iso,
                            })
                        except Exception as ue:
                            print(f"[stripe_webhook] ⚠️ User credit update error: {ue}")
                
                print(f"[stripe_webhook] ✅ Payment succeeded: {payment_intent_id}")
                
            elif event.type == 'payment_intent.payment_failed':
                payment_intent = event.data.object
                payment_intent_id = payment_intent.id
                
                metadata = payment_intent.metadata or {}
                payment_id = metadata.get('payment_id')
                
                if payment_id:
                    payment_ref = self.db.reference(f'payments/{payment_id}')
                    payment_ref.update({
                        'status': 'failed',
                        'stripe_payment_intent_id': payment_intent_id,
                        'provider_error': payment_intent.last_payment_error.message if payment_intent.last_payment_error else 'Payment failed',
                        'updated_at': datetime.datetime.now(datetime.timezone.utc).isoformat(),
                    })
                
                print(f"[stripe_webhook] ❌ Payment failed: {payment_intent_id}")
            
            # Return success to Stripe
            return jsonify({'received': True}), 200
            
        except Exception as e:
            import traceback
            print(f"[stripe_webhook] ERROR: {e}")
            traceback.print_exc()
            return jsonify({'error': 'Webhook processing failed', 'message': str(e)}), 500

