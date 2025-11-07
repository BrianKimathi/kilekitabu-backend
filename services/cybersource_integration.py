"""CyberSource Payment Gateway Integration."""
import json
import requests
import base64
import hmac
import hashlib
import datetime
from typing import Dict, Optional, Any
from config import Config


class CyberSourceClient:
    """Client for CyberSource REST API integration."""
    
    def __init__(
        self,
        merchant_id: str,
        api_key_id: str,
        secret_key: str,
        api_base: str,
    ):
        """
        Initialize CyberSource client.
        
        Args:
            merchant_id: CyberSource merchant ID
            api_key_id: API key ID for authentication
            secret_key: Secret key for signing requests
            api_base: Base URL for CyberSource API
        """
        self.merchant_id = merchant_id
        self.api_key_id = api_key_id
        self.secret_key = secret_key.strip()  # Remove any whitespace
        self.api_base = api_base.rstrip('/')
        
        # Validate secret key format (should be base64, typically 44+ characters)
        if len(self.secret_key) < 20:
            print(f"[CyberSourceClient] ⚠️ WARNING: Secret key seems too short ({len(self.secret_key)} chars). Expected base64 string (typically 44+ chars).")
        
        print(f"[CyberSourceClient] Initialized")
        print(f"[CyberSourceClient] Merchant ID: {self.merchant_id}")
        print(f"[CyberSourceClient] API Key ID: {self.api_key_id[:20]}...")
        print(f"[CyberSourceClient] Secret Key Length: {len(self.secret_key)} chars")
        print(f"[CyberSourceClient] API Base: {self.api_base}")
    
    def _generate_digest(self, payload: str) -> str:
        """
        Generate SHA256 digest for request body.
        
        Args:
            payload: Request body as JSON string
            
        Returns:
            Base64 encoded SHA256 digest
        """
        payload_bytes = payload.encode('utf-8')
        digest = hashlib.sha256(payload_bytes).digest()
        return base64.b64encode(digest).decode('utf-8')
    
    def _generate_signature(
        self,
        method: str,
        resource: str,
        timestamp: str,
        digest: str = '',
    ) -> str:
        """
        Generate HTTP signature for authentication.
        
        Args:
            method: HTTP method (GET, POST, etc.)
            resource: API resource path
            timestamp: GMT timestamp
            digest: Request digest (for POST/PATCH)
            
        Returns:
            Base64 encoded signature
        """
        # Signature data format for HTTP signature (CyberSource format)
        if method in ['POST', 'PATCH', 'PUT']:
            signature_string = (
                f"host: {self.api_base.split('//')[1]}\n"
                f"v-c-date: {timestamp}\n"
                f"(request-target): {method.lower()} {resource}\n"
                f"digest: SHA-256={digest}\n"
                f"v-c-merchant-id: {self.merchant_id}"
            )
            headers_list = "host v-c-date (request-target) digest v-c-merchant-id"
        else:
            signature_string = (
                f"host: {self.api_base.split('//')[1]}\n"
                f"v-c-date: {timestamp}\n"
                f"(request-target): {method.lower()} {resource}\n"
                f"v-c-merchant-id: {self.merchant_id}"
            )
            headers_list = "host v-c-date (request-target) v-c-merchant-id"
        
        # Sign with HMAC-SHA256
        # Ensure secret key is properly padded for base64 decoding
        secret_key_padded = self.secret_key
        # Base64 strings must be a multiple of 4 in length (with padding)
        missing_padding = len(secret_key_padded) % 4
        if missing_padding:
            secret_key_padded += '=' * (4 - missing_padding)
        
        try:
            secret_bytes = base64.b64decode(secret_key_padded)
        except Exception as e:
            raise ValueError(f"Invalid base64 secret key: {str(e)}. Please check your CYBERSOURCE_SECRET_KEY in .env file.")
        
        signature_bytes = hmac.new(
            secret_bytes,
            signature_string.encode('utf-8'),
            hashlib.sha256
        ).digest()
        signature = base64.b64encode(signature_bytes).decode('utf-8')
        
        # Return signature header value
        return (
            f'keyid="{self.api_key_id}", '
            f'algorithm="HmacSHA256", '
            f'headers="{headers_list}", '
            f'signature="{signature}"'
        )
    
    def _get_headers(
        self,
        method: str,
        resource: str,
        payload: Optional[Dict] = None
    ) -> Dict[str, str]:
        """
        Generate headers for CyberSource API request.
        
        Args:
            method: HTTP method
            resource: API resource path
            payload: Request payload (for POST/PATCH)
            
        Returns:
            Dictionary of headers
        """
        timestamp = datetime.datetime.utcnow().strftime('%a, %d %b %Y %H:%M:%S GMT')
        headers = {
            'Host': self.api_base.split('//')[1],
            'v-c-date': timestamp,
            'v-c-merchant-id': self.merchant_id,
        }
        
        if method in ['POST', 'PATCH', 'PUT'] and payload:
            payload_json = json.dumps(payload)
            digest = self._generate_digest(payload_json)
            headers['Digest'] = f'SHA-256={digest}'
            headers['Content-Type'] = 'application/json'
            signature = self._generate_signature(method, resource, timestamp, digest)
        else:
            signature = self._generate_signature(method, resource, timestamp)
        
        headers['Signature'] = signature
        
        return headers
    
    def create_payment(
        self,
        amount: float,
        currency: str,
        card_number: str,
        expiration_month: str,
        expiration_year: str,
        cvv: str,
        billing_info: Dict[str, str],
        reference_code: str,
    ) -> Dict[str, Any]:
        """
        Process a card payment.
        
        Args:
            amount: Transaction amount
            currency: Currency code (e.g., 'KES', 'USD')
            card_number: Card number
            expiration_month: Card expiration month (MM)
            expiration_year: Card expiration year (YYYY)
            cvv: Card CVV
            billing_info: Dict with firstName, lastName, address1, locality, 
                         administrativeArea, postalCode, country, email, phoneNumber
            reference_code: Unique reference for this transaction
            
        Returns:
            Payment response from CyberSource
        """
        print(f"[CyberSourceClient] [Payment] Creating payment")
        print(f"[CyberSourceClient] [Payment] Amount: {amount} {currency}")
        print(f"[CyberSourceClient] [Payment] Reference: {reference_code}")
        
        resource = '/pts/v2/payments'
        payload = {
            'clientReferenceInformation': {
                'code': reference_code,
            },
            'processingInformation': {
                'capture': True,  # Authorize and capture immediately
            },
            'paymentInformation': {
                'card': {
                    'number': card_number,
                    'expirationMonth': expiration_month,
                    'expirationYear': expiration_year,
                    'securityCode': cvv,
                }
            },
            'orderInformation': {
                'amountDetails': {
                    'totalAmount': str(amount),
                    'currency': currency,
                },
                'billTo': billing_info,
            }
        }
        
        try:
            headers = self._get_headers('POST', resource, payload)
            url = f"{self.api_base}{resource}"
            
            print(f"[CyberSourceClient] [Payment] POST {url}")
            response = requests.post(url, json=payload, headers=headers, timeout=30)
            
            print(f"[CyberSourceClient] [Payment] Response status: {response.status_code}")
            
            if response.status_code in [200, 201]:
                result = response.json()
                print(f"[CyberSourceClient] [Payment] ✅ Payment successful")
                print(f"[CyberSourceClient] [Payment]   Transaction ID: {result.get('id')}")
                print(f"[CyberSourceClient] [Payment]   Status: {result.get('status')}")
                return {
                    'ok': True,
                    'response': result,
                    'status_code': response.status_code,
                }
            else:
                error_data = response.json() if response.text else {}
                print(f"[CyberSourceClient] [Payment] ❌ Payment failed: {error_data}")
                return {
                    'ok': False,
                    'error': error_data,
                    'status_code': response.status_code,
                }
                
        except requests.exceptions.RequestException as e:
            print(f"[CyberSourceClient] [Payment] ❌ Request error: {e}")
            return {
                'ok': False,
                'error': str(e),
                'status_code': 500,
            }
        except Exception as e:
            print(f"[CyberSourceClient] [Payment] ❌ Unexpected error: {e}")
            import traceback
            print(f"[CyberSourceClient] [Payment] Traceback: {traceback.format_exc()}")
            return {
                'ok': False,
                'error': str(e),
                'status_code': 500,
            }
    
    def validate_webhook_signature(
        self,
        signature_header: str,
        payload: str,
        webhook_secret: str,
    ) -> bool:
        """
        Validate webhook notification signature.
        
        Args:
            signature_header: v-c-signature header value
            payload: Raw webhook payload body
            webhook_secret: Shared secret key for webhooks
            
        Returns:
            True if signature is valid, False otherwise
        """
        print(f"[CyberSourceClient] [Webhook] Validating signature")
        
        try:
            # Parse signature header: t=<timestamp>;keyId=<keyId>;sig=<signature>
            parts = {}
            for part in signature_header.split(';'):
                key, value = part.strip().split('=', 1)
                parts[key] = value
            
            timestamp = parts.get('t', '')
            key_id = parts.get('keyId', '')
            received_signature = parts.get('sig', '')
            
            print(f"[CyberSourceClient] [Webhook] Timestamp: {timestamp}")
            print(f"[CyberSourceClient] [Webhook] Key ID: {key_id}")
            
            # Check timestamp tolerance (60 minutes)
            try:
                timestamp_ms = int(timestamp)
                current_ms = int(datetime.datetime.utcnow().timestamp() * 1000)
                tolerance_ms = 60 * 60 * 1000  # 60 minutes
                
                if abs(current_ms - timestamp_ms) > tolerance_ms:
                    print(f"[CyberSourceClient] [Webhook] ❌ Timestamp outside tolerance")
                    return False
            except ValueError:
                print(f"[CyberSourceClient] [Webhook] ❌ Invalid timestamp format")
                return False
            
            # Regenerate signature
            timestamped_payload = f"{timestamp}.{payload}"
            secret_bytes = base64.b64decode(webhook_secret)
            signature_bytes = hmac.new(
                secret_bytes,
                timestamped_payload.encode('utf-8'),
                hashlib.sha256
            ).digest()
            expected_signature = base64.b64encode(signature_bytes).decode('utf-8')
            
            # Compare signatures
            is_valid = hmac.compare_digest(expected_signature, received_signature)
            
            if is_valid:
                print(f"[CyberSourceClient] [Webhook] ✅ Signature valid")
            else:
                print(f"[CyberSourceClient] [Webhook] ❌ Signature mismatch")
            
            return is_valid
            
        except Exception as e:
            print(f"[CyberSourceClient] [Webhook] ❌ Validation error: {e}")
            import traceback
            print(f"[CyberSourceClient] [Webhook] Traceback: {traceback.format_exc()}")
            return False


