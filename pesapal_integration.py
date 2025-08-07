import requests
import json
import hashlib
import time
from config import Config

class PesaPalIntegration:
    def __init__(self):
        self.consumer_key = Config.PESAPAL_CONSUMER_KEY
        self.consumer_secret = Config.PESAPAL_CONSUMER_SECRET
        self.base_url = Config.PESAPAL_BASE_URL
        self.access_token = None
        self.token_expiry = None
    
    def _get_access_token(self):
        """Get access token from PesaPal"""
        if self.access_token and self.token_expiry and time.time() < self.token_expiry:
            return self.access_token
        
        url = f"{self.base_url}/api/Auth/RequestToken"
        headers = {
            'Content-Type': 'application/json',
            'Accept': 'application/json'
        }
        
        data = {
            'consumer_key': self.consumer_key,
            'consumer_secret': self.consumer_secret
        }
        
        try:
            response = requests.post(url, headers=headers, json=data)
            response.raise_for_status()
            
            result = response.json()
            self.access_token = result.get('token')
            # Token expires in 1 hour
            self.token_expiry = time.time() + 3600
            
            return self.access_token
        except Exception as e:
            print(f"Error getting access token: {e}")
            return None
    
    def create_payment_request(self, payment_data):
        """Create a payment request with PesaPal"""
        token = self._get_access_token()
        if not token:
            return None
        
        url = f"{self.base_url}/api/PostPesapalDirectOrderV4"
        headers = {
            'Content-Type': 'application/json',
            'Accept': 'application/json',
            'Authorization': f'Bearer {token}'
        }
        
        # Prepare payment data
        payment_request = {
            'id': payment_data['payment_id'],
            'currency': 'KES',
            'amount': payment_data['amount'],
            'description': f"KileKitabu Credit - {payment_data['credit_days']} days",
            'callback_url': f"{Config.BASE_URL}/api/payment/callback",
            'notification_id': payment_data['payment_id'],
            'billing_address': {
                'email_address': payment_data.get('email', ''),
                'phone_number': payment_data.get('phone', ''),
                'country_code': 'KE',
                'first_name': payment_data.get('first_name', ''),
                'last_name': payment_data.get('last_name', '')
            }
        }
        
        # Add payment method if specified
        payment_method = payment_data.get('payment_method', 'ALL')
        if payment_method and payment_method != 'ALL':
            payment_request['payment_method'] = payment_method
        
        try:
            response = requests.post(url, headers=headers, json=payment_request)
            response.raise_for_status()
            
            result = response.json()
            return {
                'payment_url': result.get('redirect_url'),
                'order_tracking_id': result.get('order_tracking_id'),
                'status': 'pending'
            }
        except Exception as e:
            print(f"Error creating payment request: {e}")
            return None
    
    def check_payment_status(self, order_tracking_id):
        """Check payment status from PesaPal"""
        token = self._get_access_token()
        if not token:
            return None
        
        url = f"{self.base_url}/api/QueryPaymentStatus"
        headers = {
            'Content-Type': 'application/json',
            'Accept': 'application/json',
            'Authorization': f'Bearer {token}'
        }
        
        data = {
            'pesapal_merchant_reference': order_tracking_id,
            'pesapal_transaction_tracking_id': order_tracking_id
        }
        
        try:
            response = requests.post(url, headers=headers, json=data)
            response.raise_for_status()
            
            result = response.json()
            return {
                'status': result.get('payment_status_description'),
                'amount': result.get('amount'),
                'currency': result.get('currency'),
                'payment_method': result.get('payment_method_description')
            }
        except Exception as e:
            print(f"Error checking payment status: {e}")
            return None
    
    def get_ipn_data(self, ipn_data):
        """Process IPN (Instant Payment Notification) data from PesaPal"""
        try:
            # Verify IPN signature if needed
            # This is a simplified version - you should add proper signature verification
            
            return {
                'payment_id': ipn_data.get('pesapal_merchant_reference'),
                'order_tracking_id': ipn_data.get('pesapal_transaction_tracking_id'),
                'status': ipn_data.get('payment_status_description'),
                'amount': ipn_data.get('amount'),
                'currency': ipn_data.get('currency'),
                'payment_method': ipn_data.get('payment_method_description')
            }
        except Exception as e:
            print(f"Error processing IPN data: {e}")
            return None 