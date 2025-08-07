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
        self.ipn_id = None
    
    def _get_access_token(self):
        """Get access token from PesaPal API 3.0"""
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
        
        print(f"Getting PesaPal access token from: {url}")
        print(f"Consumer key: {self.consumer_key[:10]}...")
        print(f"Consumer secret: {self.consumer_secret[:10]}...")
        
        try:
            response = requests.post(url, headers=headers, json=data)
            print(f"Token request status: {response.status_code}")
            print(f"Token response: {response.text}")
            
            response.raise_for_status()
            
            result = response.json()
            self.access_token = result.get('token')
            # Token expires in 5 minutes according to documentation
            self.token_expiry = time.time() + 300
            
            print(f"Access token obtained: {self.access_token[:20]}...")
            return self.access_token
        except requests.exceptions.RequestException as e:
            print(f"Request error getting access token: {e}")
            return None
        except Exception as e:
            print(f"Error getting access token: {e}")
            return None
    
    def register_ipn_url(self, ipn_url):
        """Register IPN URL with PesaPal API 3.0"""
        token = self._get_access_token()
        if not token:
            print("Failed to get PesaPal access token for IPN registration")
            return None
        
        url = f"{self.base_url}/api/URLSetup/RegisterIPN"
        headers = {
            'Content-Type': 'application/json',
            'Accept': 'application/json',
            'Authorization': f'Bearer {token}'
        }
        
        data = {
            'url': ipn_url,
            'ipn_notification_type': 'POST'  # Using POST for better security
        }
        
        try:
            response = requests.post(url, headers=headers, json=data)
            print(f"IPN registration status: {response.status_code}")
            print(f"IPN registration response: {response.text}")
            
            response.raise_for_status()
            
            result = response.json()
            self.ipn_id = result.get('ipn_id')
            
            print(f"IPN registered successfully with ID: {self.ipn_id}")
            return self.ipn_id
        except requests.exceptions.RequestException as e:
            print(f"Request error registering IPN: {e}")
            return None
        except Exception as e:
            print(f"Error registering IPN: {e}")
            return None
    
    def create_payment_request(self, payment_data):
        """Create a payment request with PesaPal API 3.0"""
        token = self._get_access_token()
        if not token:
            print("Failed to get PesaPal access token")
            return None
        
        # Register IPN URL if not already registered
        if not self.ipn_id:
            ipn_url = f"{Config.BASE_URL}/api/payment/ipn"
            self.ipn_id = self.register_ipn_url(ipn_url)
            if not self.ipn_id:
                print("Failed to register IPN URL")
                return None
        
        # Use the correct PesaPal API 3.0 endpoint
        url = f"{self.base_url}/api/Transactions/SubmitOrderRequest"
        headers = {
            'Content-Type': 'application/json',
            'Accept': 'application/json',
            'Authorization': f'Bearer {token}'
        }
        
        # Prepare payment data for API 3.0
        payment_request = {
            'id': payment_data['payment_id'],
            'currency': 'KES',
            'amount': payment_data['amount'],
            'description': f"KileKitabu Credit - {payment_data['credit_days']} days",
            'callback_url': f"{Config.BASE_URL}/api/payment/callback",
            'redirect_mode': 'TOP_WINDOW',
            'notification_id': self.ipn_id,  # Use registered IPN ID
            'cancellation_url': f"{Config.BASE_URL}/api/payment/cancel",
            'billing_address': {
                'email_address': payment_data.get('email', ''),
                'phone_number': payment_data.get('phone', ''),
                'country_code': 'KE',
                'first_name': payment_data.get('first_name', ''),
                'last_name': payment_data.get('last_name', ''),
                'line_1': payment_data.get('address', ''),
                'city': payment_data.get('city', ''),
                'state': payment_data.get('state', ''),
                'postal_code': payment_data.get('postal_code', '')
            }
        }
        
        # Add subscription details if this is a recurring payment
        if payment_data.get('is_subscription', False):
            payment_request['account_number'] = payment_data['payment_id']
            payment_request['subscription_details'] = {
                'start_date': payment_data.get('subscription_start_date', ''),
                'end_date': payment_data.get('subscription_end_date', ''),
                'frequency': payment_data.get('subscription_frequency', 'MONTHLY')
            }
        
        print(f"Making PesaPal request to: {url}")
        print(f"Request data: {payment_request}")
        
        try:
            response = requests.post(url, headers=headers, json=payment_request)
            print(f"PesaPal response status: {response.status_code}")
            print(f"PesaPal response: {response.text}")
            
            response.raise_for_status()
            
            result = response.json()
            print(f"PesaPal result: {result}")
            return {
                'payment_url': result.get('redirect_url'),
                'order_tracking_id': result.get('order_tracking_id'),
                'merchant_reference': result.get('merchant_reference'),
                'status': 'pending'
            }
        except requests.exceptions.RequestException as e:
            print(f"Request error creating payment request: {e}")
            return None
        except Exception as e:
            print(f"Error creating payment request: {e}")
            return None
    
    def check_payment_status(self, order_tracking_id):
        """Check payment status from PesaPal API 3.0 using the correct endpoint"""
        token = self._get_access_token()
        if not token:
            return None
        
        # Use the correct endpoint as per documentation
        url = f"{self.base_url}/api/Transactions/GetTransactionStatus"
        headers = {
            'Content-Type': 'application/json',
            'Accept': 'application/json',
            'Authorization': f'Bearer {token}'
        }
        
        # Add orderTrackingId as query parameter
        url = f"{url}?orderTrackingId={order_tracking_id}"
        
        try:
            response = requests.get(url, headers=headers)
            print(f"Payment status check response: {response.status_code}")
            print(f"Payment status response: {response.text}")
            
            response.raise_for_status()
            
            result = response.json()
            return {
                'status': result.get('payment_status_description'),
                'status_code': result.get('status_code'),
                'amount': result.get('amount'),
                'currency': result.get('currency'),
                'payment_method': result.get('payment_method'),
                'confirmation_code': result.get('confirmation_code'),
                'created_date': result.get('created_date'),
                'payment_account': result.get('payment_account'),
                'merchant_reference': result.get('merchant_reference'),
                'subscription_transaction_info': result.get('subscription_transaction_info'),
                'error': result.get('error')
            }
        except requests.exceptions.RequestException as e:
            print(f"Request error checking payment status: {e}")
            return None
        except Exception as e:
            print(f"Error checking payment status: {e}")
            return None
    
    def get_ipn_data(self, ipn_data):
        """Process IPN (Instant Payment Notification) data from PesaPal"""
        try:
            # Extract data from IPN request
            order_tracking_id = ipn_data.get('OrderTrackingId')
            order_notification_type = ipn_data.get('OrderNotificationType')
            order_merchant_reference = ipn_data.get('OrderMerchantReference')
            
            # Check if this is a recurring payment notification
            is_recurring = order_notification_type == 'RECURRING'
            
            return {
                'payment_id': order_merchant_reference,
                'order_tracking_id': order_tracking_id,
                'notification_type': order_notification_type,
                'is_recurring': is_recurring
            }
        except Exception as e:
            print(f"Error processing IPN data: {e}")
            return None
    
    def cancel_order(self, order_tracking_id):
        """Cancel an order using PesaPal API 3.0"""
        token = self._get_access_token()
        if not token:
            return None
        
        url = f"{self.base_url}/api/Transactions/CancelOrder"
        headers = {
            'Content-Type': 'application/json',
            'Accept': 'application/json',
            'Authorization': f'Bearer {token}'
        }
        
        data = {
            'order_tracking_id': order_tracking_id
        }
        
        try:
            response = requests.post(url, headers=headers, json=data)
            print(f"Cancel order response: {response.status_code}")
            print(f"Cancel order response: {response.text}")
            
            response.raise_for_status()
            
            result = response.json()
            return {
                'status': result.get('status'),
                'message': result.get('message')
            }
        except requests.exceptions.RequestException as e:
            print(f"Request error cancelling order: {e}")
            return None
        except Exception as e:
            print(f"Error cancelling order: {e}")
            return None
    
    def request_refund(self, confirmation_code, amount, username, remarks):
        """Request a refund using PesaPal API 3.0"""
        token = self._get_access_token()
        if not token:
            return None
        
        url = f"{self.base_url}/api/Transactions/RefundRequest"
        headers = {
            'Content-Type': 'application/json',
            'Accept': 'application/json',
            'Authorization': f'Bearer {token}'
        }
        
        data = {
            'confirmation_code': confirmation_code,
            'amount': str(amount),
            'username': username,
            'remarks': remarks
        }
        
        try:
            response = requests.post(url, headers=headers, json=data)
            print(f"Refund request response: {response.status_code}")
            print(f"Refund request response: {response.text}")
            
            response.raise_for_status()
            
            result = response.json()
            return {
                'status': result.get('status'),
                'message': result.get('message')
            }
        except requests.exceptions.RequestException as e:
            print(f"Request error requesting refund: {e}")
            return None
        except Exception as e:
            print(f"Error requesting refund: {e}")
            return None 