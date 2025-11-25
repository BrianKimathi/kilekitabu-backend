"""Stripe Payment Gateway Integration."""
import stripe
from typing import Dict, Optional, Any
from config import Config


class StripeClient:
    """Client for Stripe API integration."""
    
    def __init__(
        self,
        secret_key: str,
        publishable_key: str = None,
        webhook_secret: str = None,
    ):
        """
        Initialize Stripe client.
        
        Args:
            secret_key: Stripe secret key (sk_test_... or sk_live_...)
            publishable_key: Stripe publishable key (pk_test_... or pk_live_...)
            webhook_secret: Webhook signing secret (whsec_...)
        """
        self.secret_key = secret_key
        self.publishable_key = publishable_key
        self.webhook_secret = webhook_secret
        
        # Set Stripe API key
        stripe.api_key = secret_key
        
        # Determine environment from key
        self.environment = 'test' if secret_key.startswith('sk_test') else 'live'
        
        print(f"[StripeClient] Initialized")
        print(f"[StripeClient] Environment: {self.environment}")
        print(f"[StripeClient] Secret Key: {secret_key[:20]}...")
        if publishable_key:
            print(f"[StripeClient] Publishable Key: {publishable_key[:20]}...")
    
    def create_payment_intent(
        self,
        amount: float,
        currency: str,
        payment_method_id: str = None,
        payment_method_types: list = None,
        metadata: Dict[str, str] = None,
        customer_id: str = None,
    ) -> Dict[str, Any]:
        """
        Create a Stripe PaymentIntent.
        
        Args:
            amount: Amount in smallest currency unit (e.g., cents for USD)
            currency: Currency code (e.g., 'usd', 'kes')
            payment_method_id: Payment method ID (for card or Google Pay)
            payment_method_types: List of payment method types ['card', 'google_pay']
            metadata: Additional metadata
            customer_id: Stripe customer ID (optional)
        
        Returns:
            Dict with 'ok', 'status_code', 'response', 'error'
        """
        try:
            # Convert amount to smallest currency unit
            amount_in_cents = int(amount * 100) if currency.lower() in ['usd', 'kes'] else int(amount)
            
            intent_params = {
                'amount': amount_in_cents,
                'currency': currency.lower(),
                'payment_method_types': payment_method_types or ['card'],
                'metadata': metadata or {},
                'confirmation_method': 'automatic' if payment_method_id else 'manual',
            }
            
            if payment_method_id:
                intent_params['payment_method'] = payment_method_id
                # If payment method is provided, set to confirm automatically
                intent_params['confirm'] = True
            
            if customer_id:
                intent_params['customer'] = customer_id
            
            print(f"[StripeClient] [PaymentIntent] Creating PaymentIntent")
            print(f"[StripeClient] [PaymentIntent] Amount: {amount} {currency.upper()} ({amount_in_cents} {currency.lower()})")
            print(f"[StripeClient] [PaymentIntent] Payment Method: {payment_method_id or 'None (will confirm later)'}")
            
            intent = stripe.PaymentIntent.create(**intent_params)
            
            print(f"[StripeClient] [PaymentIntent] ✅ Created: {intent.id}")
            print(f"[StripeClient] [PaymentIntent] Status: {intent.status}")
            print(f"[StripeClient] [PaymentIntent] Client Secret: {intent.client_secret[:20]}...")
            
            # If payment method was provided and confirm=True, check if it needs action
            if payment_method_id and intent_params.get('confirm'):
                if intent.status == 'requires_action':
                    print(f"[StripeClient] [PaymentIntent] ⚠️ Requires action (3D Secure, etc.)")
                elif intent.status == 'succeeded':
                    print(f"[StripeClient] [PaymentIntent] ✅ Payment succeeded immediately")
                elif intent.status == 'requires_payment_method':
                    print(f"[StripeClient] [PaymentIntent] ⚠️ Requires payment method")
            
            return {
                'ok': True,
                'status_code': 200,
                'response': {
                    'id': intent.id,
                    'client_secret': intent.client_secret,
                    'status': intent.status,
                    'amount': intent.amount,
                    'currency': intent.currency,
                    'next_action': getattr(intent, 'next_action', None),
                },
            }
            
        except stripe.error.StripeError as e:
            print(f"[StripeClient] [PaymentIntent] ❌ Stripe Error: {e}")
            return {
                'ok': False,
                'status_code': 400,
                'error': str(e),
                'stripe_error': {
                    'type': e.__class__.__name__,
                    'code': getattr(e, 'code', None),
                    'param': getattr(e, 'param', None),
                },
            }
        except Exception as e:
            print(f"[StripeClient] [PaymentIntent] ❌ Error: {e}")
            import traceback
            traceback.print_exc()
            return {
                'ok': False,
                'status_code': 500,
                'error': str(e),
            }
    
    def confirm_payment_intent(
        self,
        payment_intent_id: str,
        payment_method_id: str = None,
    ) -> Dict[str, Any]:
        """
        Confirm a PaymentIntent.
        
        Args:
            payment_intent_id: PaymentIntent ID
            payment_method_id: Payment method ID (optional, if not already attached)
        
        Returns:
            Dict with 'ok', 'status_code', 'response', 'error'
        """
        try:
            print(f"[StripeClient] [Confirm] Confirming PaymentIntent: {payment_intent_id}")
            
            intent = stripe.PaymentIntent.retrieve(payment_intent_id)
            
            if payment_method_id:
                intent.payment_method = payment_method_id
            
            intent = intent.confirm()
            
            print(f"[StripeClient] [Confirm] ✅ Confirmed: {intent.id}")
            print(f"[StripeClient] [Confirm] Status: {intent.status}")
            
            return {
                'ok': True,
                'status_code': 200,
                'response': {
                    'id': intent.id,
                    'status': intent.status,
                    'amount': intent.amount,
                    'currency': intent.currency,
                },
            }
            
        except stripe.error.StripeError as e:
            print(f"[StripeClient] [Confirm] ❌ Stripe Error: {e}")
            return {
                'ok': False,
                'status_code': 400,
                'error': str(e),
                'stripe_error': {
                    'type': e.__class__.__name__,
                    'code': getattr(e, 'code', None),
                },
            }
        except Exception as e:
            print(f"[StripeClient] [Confirm] ❌ Error: {e}")
            return {
                'ok': False,
                'status_code': 500,
                'error': str(e),
            }
    
    def create_payment_with_google_pay(
        self,
        amount: float,
        currency: str,
        payment_method_id: str,
        metadata: Dict[str, str] = None,
    ) -> Dict[str, Any]:
        """
        Create and confirm a payment using Google Pay payment method.
        
        Args:
            amount: Amount in currency units
            currency: Currency code
            payment_method_id: Google Pay payment method ID from Stripe
            metadata: Additional metadata
        
        Returns:
            Dict with 'ok', 'status_code', 'response', 'error'
        """
        try:
            # Create PaymentIntent with Google Pay
            result = self.create_payment_intent(
                amount=amount,
                currency=currency,
                payment_method_id=payment_method_id,
                payment_method_types=['card'],  # Google Pay uses card payment method
                metadata=metadata or {},
            )
            
            if not result.get('ok'):
                return result
            
            payment_intent_id = result['response']['id']
            status = result['response'].get('status', '')
            
            # If already confirmed (succeeded or requires_action), return the result
            if status in ['succeeded', 'requires_action', 'processing']:
                return result
            
            # Otherwise, confirm the PaymentIntent
            confirm_result = self.confirm_payment_intent(
                payment_intent_id=payment_intent_id,
            )
            
            return confirm_result
            
        except Exception as e:
            print(f"[StripeClient] [GooglePay] ❌ Error: {e}")
            import traceback
            traceback.print_exc()
            return {
                'ok': False,
                'status_code': 500,
                'error': str(e),
            }
    
    def create_payment_with_card(
        self,
        amount: float,
        currency: str,
        card_token: str = None,
        payment_method_id: str = None,
        metadata: Dict[str, str] = None,
    ) -> Dict[str, Any]:
        """
        Create and confirm a payment using card.
        
        Args:
            amount: Amount in currency units
            currency: Currency code
            card_token: Card token (from Stripe.js) - deprecated, use payment_method_id
            payment_method_id: Payment method ID from Stripe
            metadata: Additional metadata
        
        Returns:
            Dict with 'ok', 'status_code', 'response', 'error'
        """
        try:
            # Use payment_method_id if provided, otherwise card_token
            pm_id = payment_method_id or card_token
            
            if not pm_id:
                return {
                    'ok': False,
                    'status_code': 400,
                    'error': 'payment_method_id or card_token is required',
                }
            
            # Create PaymentIntent
            result = self.create_payment_intent(
                amount=amount,
                currency=currency,
                payment_method_id=pm_id,
                payment_method_types=['card'],
                metadata=metadata or {},
            )
            
            if not result.get('ok'):
                return result
            
            payment_intent_id = result['response']['id']
            status = result['response'].get('status', '')
            
            # If already confirmed (succeeded or requires_action), return the result
            if status in ['succeeded', 'requires_action', 'processing']:
                return result
            
            # Otherwise, confirm the PaymentIntent
            confirm_result = self.confirm_payment_intent(
                payment_intent_id=payment_intent_id,
            )
            
            return confirm_result
            
        except Exception as e:
            print(f"[StripeClient] [Card] ❌ Error: {e}")
            import traceback
            traceback.print_exc()
            return {
                'ok': False,
                'status_code': 500,
                'error': str(e),
            }
    
    def retrieve_payment_intent(
        self,
        payment_intent_id: str,
    ) -> Dict[str, Any]:
        """
        Retrieve a PaymentIntent.
        
        Args:
            payment_intent_id: PaymentIntent ID
        
        Returns:
            Dict with 'ok', 'status_code', 'response', 'error'
        """
        try:
            intent = stripe.PaymentIntent.retrieve(payment_intent_id)
            
            return {
                'ok': True,
                'status_code': 200,
                'response': {
                    'id': intent.id,
                    'status': intent.status,
                    'amount': intent.amount,
                    'currency': intent.currency,
                    'payment_method': intent.payment_method,
                    'metadata': intent.metadata,
                },
            }
            
        except stripe.error.StripeError as e:
            return {
                'ok': False,
                'status_code': 400,
                'error': str(e),
            }
        except Exception as e:
            return {
                'ok': False,
                'status_code': 500,
                'error': str(e),
            }
    
    def verify_webhook_signature(
        self,
        payload: bytes,
        signature: str,
    ) -> Optional[stripe.Event]:
        """
        Verify Stripe webhook signature.
        
        Args:
            payload: Raw request body as bytes
            signature: Stripe-Signature header value
        
        Returns:
            Stripe Event object if valid, None otherwise
        """
        try:
            if not self.webhook_secret:
                print(f"[StripeClient] [Webhook] ⚠️ Webhook secret not configured")
                return None
            
            event = stripe.Webhook.construct_event(
                payload,
                signature,
                self.webhook_secret,
            )
            
            print(f"[StripeClient] [Webhook] ✅ Signature verified")
            print(f"[StripeClient] [Webhook] Event ID: {event.id}")
            print(f"[StripeClient] [Webhook] Event Type: {event.type}")
            
            return event
            
        except ValueError as e:
            print(f"[StripeClient] [Webhook] ❌ Invalid payload: {e}")
            return None
        except stripe.error.SignatureVerificationError as e:
            print(f"[StripeClient] [Webhook] ❌ Invalid signature: {e}")
            return None
        except Exception as e:
            print(f"[StripeClient] [Webhook] ❌ Error: {e}")
            return None

