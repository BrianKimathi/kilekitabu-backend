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
        # IMPORTANT: CyberSource uses 'request-target' WITHOUT parentheses (non-standard format)
        # IMPORTANT: requests library normalizes headers to Title-Case, so we must use Title-Case
        # in the signature string to match what's actually sent:
        # - 'v-c-date' becomes 'V-C-Date'
        # - 'digest' becomes 'Digest'
        # - 'v-c-merchant-id' becomes 'V-C-Merchant-Id'
        # - 'host' stays as 'host' (requests doesn't change it, but we use lowercase in signature)
        host_name = self.api_base.split('//')[1]
        if method in ['POST', 'PATCH', 'PUT']:
            signature_string = (
                f"host: {host_name}\n"
                f"V-C-Date: {timestamp}\n"  # Title-Case to match requests library
                f"request-target: {method.lower()} {resource}\n"  # NO parentheses - CyberSource format
                f"Digest: SHA-256={digest}\n"  # Title-Case to match requests library
                f"V-C-Merchant-Id: {self.merchant_id}"  # Title-Case to match requests library
            )
            headers_list = "host V-C-Date request-target Digest V-C-Merchant-Id"  # Title-Case to match requests
        else:
            signature_string = (
                f"host: {host_name}\n"
                f"V-C-Date: {timestamp}\n"  # Title-Case to match requests library
                f"request-target: {method.lower()} {resource}\n"  # NO parentheses - CyberSource format
                f"V-C-Merchant-Id: {self.merchant_id}"  # Title-Case to match requests library
            )
            headers_list = "host V-C-Date request-target V-C-Merchant-Id"  # Title-Case to match requests
        
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
        # IMPORTANT: Use lowercase header names when setting them - requests will normalize to Title-Case
        # But the signature string must use Title-Case to match what requests actually sends
        headers = {
            # Note: Don't set 'Host' header - requests library sets it automatically from URL
            # The 'host' in signature string refers to the Host header that will be sent (lowercase in signature)
            'v-c-date': timestamp,  # requests will send as 'V-C-Date'
            'v-c-merchant-id': self.merchant_id,  # requests will send as 'V-C-Merchant-Id'
        }
        
        if method in ['POST', 'PATCH', 'PUT'] and payload:
            payload_json = json.dumps(payload)
            digest = self._generate_digest(payload_json)
            headers['digest'] = f'SHA-256={digest}'  # requests will send as 'Digest'
            headers['Content-Type'] = 'application/json'
            signature = self._generate_signature(method, resource, timestamp, digest)
        else:
            signature = self._generate_signature(method, resource, timestamp)
        
        headers['signature'] = signature  # requests will send as 'Signature'
        
        return headers
    
    def create_flex_capture_context(self) -> Dict[str, Any]:
        """
        Create a Flex Sessions capture context for card tokenization (Flex SDK).

        This calls the /flex/v2/sessions endpoint and returns the raw JWT in
        the 'captureContext' field.
        """
        resource = "/flex/v2/sessions"
        payload: Dict[str, Any] = {
            "fields": {
                "paymentInformation": {
                    "card": {
                        "number": {"required": True},
                        "securityCode": {"required": True},
                        "expirationMonth": {"required": True},
                        "expirationYear": {"required": True},
                        "type": {"required": False},
                    }
                }
            }
        }
        try:
            headers = self._get_headers("POST", resource, payload)
            url = f"{self.api_base}{resource}"
            print(f"[CyberSourceClient] [FlexSessions] POST {url}")
            try:
                print(f"[CyberSourceClient] [FlexSessions] Payload: {json.dumps(payload)}")
            except Exception:
                print("[CyberSourceClient] [FlexSessions] Payload: <unserializable>")

            response = requests.post(url, json=payload, headers=headers, timeout=(10, 30))
            print(f"[CyberSourceClient] [FlexSessions] Response status: {response.status_code}")
            if response.status_code in [200, 201]:
                # /flex/v2/sessions returns JWT as plain string body
                jwt_raw = response.text.strip().strip('"')
                print("[CyberSourceClient] [FlexSessions] ✅ Capture context created")
                return {"ok": True, "captureContext": jwt_raw, "status_code": response.status_code}
            error_data = response.json() if response.text else {}
            print(f"[CyberSourceClient] [FlexSessions] ❌ Failed: {error_data}")
            return {"ok": False, "error": error_data, "status_code": response.status_code}
        except requests.exceptions.RequestException as e:
            print(f"[CyberSourceClient] [FlexSessions] ❌ Request error: {e}")
            return {"ok": False, "error": str(e), "status_code": 500}
        except Exception as e:
            print(f"[CyberSourceClient] [FlexSessions] ❌ Unexpected error: {e}")
            import traceback

            print(traceback.format_exc())
            return {"ok": False, "error": str(e), "status_code": 500}
    
    def create_capture_context(
        self,
        target_origins: list,
        allowed_card_networks: Optional[list] = None,
        allowed_payment_types: Optional[list] = None,
        country: str = "KE",
        locale: str = "en_KE",
        client_version: Optional[str] = None,
        amount: Optional[float] = None,
        currency: Optional[str] = None,
        extra: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Create a Unified Checkout capture context for browser/app flows (e.g., Google Pay).
        """
        resource = '/up/v1/capture-contexts'
        payload: Dict[str, Any] = {
            'targetOrigins': target_origins,
            'country': country,
            'locale': locale,
            'allowedCardNetworks': allowed_card_networks or ['VISA', 'MASTERCARD', 'AMEX'],
            'allowedPaymentTypes': allowed_payment_types or ['GOOGLEPAY'],
        }
        # orderInformation is required at top level (not inside data)
        if amount is not None and currency:
            payload['orderInformation'] = {
                'amountDetails': {
                    'totalAmount': f"{float(amount):.2f}",
                    'currency': currency
                }
            }
        else:
            # Provide defaults if not specified
            payload['orderInformation'] = {
                'amountDetails': {
                    'totalAmount': "1.00",
                    'currency': 'USD'
                }
            }
        if client_version:
            payload['clientVersion'] = client_version
        else:
            # Provide a reasonable default to satisfy API validation
            payload['clientVersion'] = '0.31'
        if extra:
            payload.update(extra)
        try:
            headers = self._get_headers('POST', resource, payload)
            url = f"{self.api_base}{resource}"
            print(f"[CyberSourceClient] [CaptureContext] POST {url}")
            try:
                # Safe header preview without leaking secrets
                sig_hdr = headers.get('Signature', '')
                key_id = ''
                if sig_hdr:
                    try:
                        # keyid="..."
                        start = sig_hdr.find('keyid="')
                        if start != -1:
                            start += len('keyid="')
                            end = sig_hdr.find('"', start)
                            key_id = sig_hdr[start:end]
                    except Exception:
                        key_id = ''
                # Check headers in both cases (requests normalizes to Title-Case)
                vc_date = headers.get('v-c-date', '') or headers.get('V-C-Date', '')
                vc_merchant = headers.get('v-c-merchant-id', '') or headers.get('V-C-Merchant-Id', '')
                digest_set = bool(headers.get('digest') or headers.get('Digest'))
                print("[CyberSourceClient] [CaptureContext] Headers preview: "
                      f"Host={headers.get('Host', 'auto')}, v-c-date={vc_date[:20]}..., "
                      f"v-c-merchant-id={vc_merchant[:20]}..., Digest={'set' if digest_set else 'missing'}, "
                      f"keyid={key_id}")
            except Exception as _:
                pass
            try:
                print(f"[CyberSourceClient] [CaptureContext] Payload: {json.dumps(payload)}")
            except Exception as _:
                print("[CyberSourceClient] [CaptureContext] Payload: <unserializable>")
            # Retry logic for connection issues
            max_retries = 3
            retry_delay = 2
            last_exception = None
            
            for attempt in range(max_retries):
                try:
                    response = requests.post(url, json=payload, headers=headers, timeout=(10, 30))
                    break
                except (requests.exceptions.ConnectTimeout, requests.exceptions.ConnectionError, requests.exceptions.Timeout) as e:
                    last_exception = e
                    if attempt < max_retries - 1:
                        print(f"[CyberSourceClient] [CaptureContext] ⚠️ Connection attempt {attempt + 1} failed, retrying...")
                        import time
                        time.sleep(retry_delay)
                        retry_delay *= 2
                    else:
                        raise
            
            if 'response' not in locals():
                raise last_exception
            print(f"[CyberSourceClient] [CaptureContext] Response status: {response.status_code}")
            if response.status_code in [200, 201]:
                # Success: Response is a JWT token string (not JSON)
                capture_context_token = response.text.strip()
                print(f"[CyberSourceClient] [CaptureContext] ✅ Success - JWT token length: {len(capture_context_token)}")
                # Log the full JWT so we can inspect the complete Unified Checkout configuration
                # This is sandbox-only debug logging; for production you should remove or mask this.
                try:
                    print(f"[CyberSourceClient] [CaptureContext] Full JWT captureContext:\n{capture_context_token}")
                except Exception:
                    # Fallback in case of any encoding/printing issues
                    print("[CyberSourceClient] [CaptureContext] Full JWT captureContext: <unprintable>")
                # Return the token in the expected format
                return {
                    'ok': True,
                    'response': {'captureContext': capture_context_token},
                    'status_code': response.status_code
                }
            # Log full response body and headers for diagnostics
            try:
                print(f"[CyberSourceClient] [CaptureContext] Response headers: {dict(response.headers)}")
            except Exception as _:
                pass
            try:
                print(f"[CyberSourceClient] [CaptureContext] Response body: {response.text}")
            except Exception as _:
                pass
            return {
                'ok': False,
                'error': (response.json() if response.headers.get('content-type','').startswith('application/json') else {'raw': response.text}),
                'status_code': response.status_code
            }
        except requests.exceptions.RequestException as e:
            print(f"[CyberSourceClient] [CaptureContext] ❌ Request error: {e}")
            return {'ok': False, 'error': str(e), 'status_code': 500}
        except Exception as e:
            print(f"[CyberSourceClient] [CaptureContext] ❌ Unexpected error: {e}")
            import traceback
            print(traceback.format_exc())
            return {'ok': False, 'error': str(e), 'status_code': 500}
    
    def create_payment_with_transient_token(
        self,
        amount: float,
        currency: str,
        transient_token: str,
        reference_code: str,
        capture: bool = True,
    ) -> Dict[str, Any]:
        """
        Process a payment using a Unified Checkout transient token (e.g., Google Pay).
        """
        print(f"[CyberSourceClient] [Payment] Creating payment with transient token")
        resource = '/pts/v2/payments'
        payload = {
            'clientReferenceInformation': {'code': reference_code},
            'processingInformation': {'capture': capture},
            'orderInformation': {
                'amountDetails': {
                    'totalAmount': str(amount),
                    'currency': currency,
                }
            },
            'tokenInformation': {
                'transientToken': transient_token
            }
        }
        try:
            headers = self._get_headers('POST', resource, payload)
            url = f"{self.api_base}{resource}"
            print(f"[CyberSourceClient] [Payment] POST {url}")
            # Retry logic for connection issues
            max_retries = 3
            retry_delay = 2
            last_exception = None
            
            for attempt in range(max_retries):
                try:
                    response = requests.post(url, json=payload, headers=headers, timeout=(10, 30))
                    break
                except (requests.exceptions.ConnectTimeout, requests.exceptions.ConnectionError, requests.exceptions.Timeout) as e:
                    last_exception = e
                    if attempt < max_retries - 1:
                        print(f"[CyberSourceClient] [CaptureContext] ⚠️ Connection attempt {attempt + 1} failed, retrying...")
                        import time
                        time.sleep(retry_delay)
                        retry_delay *= 2
                    else:
                        raise
            
            if 'response' not in locals():
                raise last_exception
            print(f"[CyberSourceClient] [Payment] Response status: {response.status_code}")
            if response.status_code in [200, 201]:
                result = response.json()
                print(f"[CyberSourceClient] [Payment] ✅ Payment successful (transientToken)")
                return {'ok': True, 'response': result, 'status_code': response.status_code}
            error_data = response.json() if response.text else {}
            print(f"[CyberSourceClient] [Payment] ❌ Payment failed: {error_data}")
            return {'ok': False, 'error': error_data, 'status_code': response.status_code}
        except requests.exceptions.RequestException as e:
            print(f"[CyberSourceClient] [Payment] ❌ Request error: {e}")
            return {'ok': False, 'error': str(e), 'status_code': 500}
        except Exception as e:
            print(f"[CyberSourceClient] [Payment] ❌ Unexpected error: {e}")
            import traceback
            print(traceback.format_exc())
            return {'ok': False, 'error': str(e), 'status_code': 500}

    def create_googlepay_payment_from_blob(
        self,
        amount: float,
        currency: str,
        googlepay_blob_base64: str,
        reference_code: str,
        capture: bool = True,
    ) -> Dict[str, Any]:
        """
        Process a Google Pay payment using the encrypted payment blob (Barclays decryption option).

        The blob must be a Base64-encoded Google Pay payment token as described in the
        Cybersource Google Pay documentation (paymentInformation.fluidData.value +
        processingInformation.paymentSolution = "012").
        """
        print(
            "[CyberSourceClient] [Payment][GooglePay] Creating payment from Google Pay blob "
            f"(amount={amount} {currency}, ref={reference_code}, blob_len={len(googlepay_blob_base64 or '')})"
        )
        resource = "/pts/v2/payments"
        payload = {
            "clientReferenceInformation": {"code": reference_code},
            "processingInformation": {
                "capture": capture,
                # Payment solution 012 = Google Pay via Barclays decryption
                "paymentSolution": "012",
            },
            "orderInformation": {
                "amountDetails": {
                    "totalAmount": str(amount),
                    "currency": currency,
                }
            },
            "paymentInformation": {
                "fluidData": {
                    "value": googlepay_blob_base64,
                }
            },
        }

        try:
            headers = self._get_headers("POST", resource, payload)
            url = f"{self.api_base}{resource}"
            print(f"[CyberSourceClient] [Payment][GooglePay] POST {url}")

            # Retry logic for connection issues
            max_retries = 3
            retry_delay = 2
            last_exception = None

            for attempt in range(max_retries):
                try:
                    response = requests.post(
                        url, json=payload, headers=headers, timeout=(10, 30)
                    )
                    break
                except (
                    requests.exceptions.ConnectTimeout,
                    requests.exceptions.ConnectionError,
                    requests.exceptions.Timeout,
                ) as e:
                    last_exception = e
                    if attempt < max_retries - 1:
                        print(
                            f"[CyberSourceClient] [Payment][GooglePay] ⚠️ Connection attempt {attempt + 1} failed, retrying..."
                        )
                        import time

                        time.sleep(retry_delay)
                        retry_delay *= 2
                    else:
                        raise

            if "response" not in locals():
                raise last_exception

            print(
                f"[CyberSourceClient] [Payment][GooglePay] Response status: {response.status_code}"
            )
            if response.status_code in [200, 201]:
                result = response.json()
                print(
                    "[CyberSourceClient] [Payment][GooglePay] ✅ Payment successful (Google Pay blob)"
                )
                return {"ok": True, "response": result, "status_code": response.status_code}

            # Log as much as possible on failure to help diagnose 4xx/5xx
            try:
                error_data = response.json() if response.text else {}
            except Exception:
                error_data = {"raw": response.text[:1000]}

            print(
                f"[CyberSourceClient] [Payment][GooglePay] ❌ Payment failed: "
                f"status_code={response.status_code}, error={error_data}"
            )
            try:
                print(
                    "[CyberSourceClient] [Payment][GooglePay] ❌ Response headers: "
                    f"{dict(response.headers)}"
                )
            except Exception:
                pass
            try:
                print(
                    "[CyberSourceClient] [Payment][GooglePay] ❌ Raw response body: "
                    f"{response.text[:2000]}"
                )
            except Exception:
                pass
            # Highlight common auth issues for easier debugging
            if response.status_code == 401:
                print(
                    "[CyberSourceClient] [Payment][GooglePay] ⚠️ 401 Authentication Failed – "
                    "check CYBERSOURCE_MERCHANT_ID / API_KEY_ID / SECRET_KEY and that Google Pay "
                    "is enabled for this merchant in the sandbox environment."
                )
            return {"ok": False, "error": error_data, "status_code": response.status_code}
        except requests.exceptions.RequestException as e:
            print(f"[CyberSourceClient] [Payment][GooglePay] ❌ Request error: {e}")
            return {"ok": False, "error": str(e), "status_code": 500}
        except Exception as e:
            print(f"[CyberSourceClient] [Payment][GooglePay] ❌ Unexpected error: {e}")
            import traceback

            print(traceback.format_exc())
            return {"ok": False, "error": str(e), "status_code": 500}

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
        print(f"[CyberSourceClient] [Payment] ========== Creating Card Payment ==========")
        print(f"[CyberSourceClient] [Payment] Amount: {amount} {currency}")
        print(f"[CyberSourceClient] [Payment] Reference: {reference_code}")
        print(f"[CyberSourceClient] [Payment] Card: ****{card_number[-4:] if len(card_number) >= 4 else 'N/A'}")
        print(f"[CyberSourceClient] [Payment] Expiry: {expiration_month}/{expiration_year}")
        print(f"[CyberSourceClient] [Payment] Billing: {billing_info.get('firstName', 'N/A')} {billing_info.get('lastName', 'N/A')}")
        
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
                    # securityCode conditionally added below
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

        # Conditionally include CVV/securityCode. In CyberSource test defaults, CVV may cause INVALID_DATA.
        # Use config flag CYBERSOURCE_SEND_CVV to control. Default to False in test environments.
        try:
            send_cvv = getattr(Config, 'CYBERSOURCE_SEND_CVV', False)
        except Exception:
            send_cvv = False
        if send_cvv and isinstance(cvv, str) and 3 <= len(cvv.strip()) <= 4 and cvv.strip().isdigit():
            payload['paymentInformation']['card']['securityCode'] = cvv.strip()
        
        # Create a safe payload copy for logging (mask sensitive data)
        safe_payload = payload.copy()
        if 'paymentInformation' in safe_payload and 'card' in safe_payload['paymentInformation']:
            safe_card = safe_payload['paymentInformation']['card'].copy()
            safe_card['number'] = f"****{card_number[-4:]}" if len(card_number) >= 4 else "****"
            if 'securityCode' in safe_card:
                safe_card['securityCode'] = "***"
            safe_payload['paymentInformation']['card'] = safe_card
        
        try:
            print(f"[CyberSourceClient] [Payment] 📤 Preparing request...")
            headers = self._get_headers('POST', resource, payload)
            url = f"{self.api_base}{resource}"
            
            # Log safe payload
            try:
                print(f"[CyberSourceClient] [Payment] 📤 Request payload (safe): {json.dumps(safe_payload, indent=2)}")
            except Exception:
                print(f"[CyberSourceClient] [Payment] 📤 Request payload: <unserializable>")
            
            # Log headers (safe) - check both lowercase and Title-Case since requests normalizes
            try:
                safe_headers = {}
                for k, v in headers.items():
                    # Skip sensitive headers (check both cases)
                    if k.lower() not in ['signature', 'digest']:
                        safe_headers[k] = v
                
                # Add safe versions of signature and digest
                sig_key = 'signature' if 'signature' in headers else 'Signature'
                digest_key = 'digest' if 'digest' in headers else 'Digest'
                
                if sig_key in headers:
                    safe_headers['Signature'] = f"<{len(headers.get(sig_key, ''))} chars>"
                if digest_key in headers:
                    safe_headers['Digest'] = f"<{len(headers.get(digest_key, ''))} chars>"
                
                print(f"[CyberSourceClient] [Payment] 📤 Request headers (safe): {json.dumps(safe_headers, indent=2)}")
            except Exception:
                print(f"[CyberSourceClient] [Payment] 📤 Request headers: <unserializable>")
            
            print(f"[CyberSourceClient] [Payment] 🌐 POST {url}")
            print(f"[CyberSourceClient] [Payment] ⏳ Sending request to CyberSource...")
            
            # Retry logic for connection issues
            max_retries = 3
            retry_delay = 2  # seconds
            last_exception = None
            
            for attempt in range(max_retries):
                try:
                    response = requests.post(url, json=payload, headers=headers, timeout=(10, 30))
                    break  # Success, exit retry loop
                except (requests.exceptions.ConnectTimeout, requests.exceptions.ConnectionError, requests.exceptions.Timeout) as e:
                    last_exception = e
                    if attempt < max_retries - 1:
                        print(f"[CyberSourceClient] [Payment] ⚠️ Connection attempt {attempt + 1} failed: {type(e).__name__}")
                        print(f"[CyberSourceClient] [Payment] ⏳ Retrying in {retry_delay} seconds... (attempt {attempt + 2}/{max_retries})")
                        import time
                        time.sleep(retry_delay)
                        retry_delay *= 2  # Exponential backoff
                    else:
                        print(f"[CyberSourceClient] [Payment] ❌ All {max_retries} connection attempts failed")
                        raise
                except requests.exceptions.RequestException as e:
                    # Other request exceptions (not connection-related) - don't retry
                    raise
            
            # If we get here and response is not defined, raise the last exception
            if 'response' not in locals():
                raise last_exception
            
            print(f"[CyberSourceClient] [Payment] 📥 Response received")
            print(f"[CyberSourceClient] [Payment]   - Status code: {response.status_code}")
            print(f"[CyberSourceClient] [Payment]   - Content-Type: {response.headers.get('Content-Type', 'N/A')}")
            print(f"[CyberSourceClient] [Payment]   - Content-Length: {len(response.content)} bytes")
            
            if response.status_code in [200, 201]:
                try:
                    result = response.json()
                    print(f"[CyberSourceClient] [Payment] ✅ Payment successful")
                    print(f"[CyberSourceClient] [Payment] 📋 Response details:")
                    print(f"[CyberSourceClient] [Payment]   - Transaction ID: {result.get('id', 'N/A')}")
                    print(f"[CyberSourceClient] [Payment]   - Status: {result.get('status', 'N/A')}")
                    print(f"[CyberSourceClient] [Payment]   - Response keys: {list(result.keys())}")
                    
                    # Log processor information if available
                    if 'processorInformation' in result:
                        proc_info = result['processorInformation']
                        print(f"[CyberSourceClient] [Payment]   - Processor:")
                        print(f"[CyberSourceClient] [Payment]     * Response Code: {proc_info.get('responseCode', 'N/A')}")
                        print(f"[CyberSourceClient] [Payment]     * Approval Code: {proc_info.get('approvalCode', 'N/A')}")
                        print(f"[CyberSourceClient] [Payment]     * Transaction ID: {proc_info.get('transactionId', 'N/A')}")
                    
                    # Log order information if available
                    if 'orderInformation' in result and 'amountDetails' in result['orderInformation']:
                        amt_details = result['orderInformation']['amountDetails']
                        print(f"[CyberSourceClient] [Payment]   - Amount Details:")
                        print(f"[CyberSourceClient] [Payment]     * Authorized: {amt_details.get('authorizedAmount', 'N/A')} {amt_details.get('currency', 'N/A')}")
                    
                    return {
                        'ok': True,
                        'response': result,
                        'status_code': response.status_code,
                    }
                except Exception as json_err:
                    print(f"[CyberSourceClient] [Payment] ⚠️ Failed to parse JSON response: {json_err}")
                    print(f"[CyberSourceClient] [Payment]   - Raw response: {response.text[:500]}")
                    return {
                        'ok': False,
                        'error': f'Invalid JSON response: {str(json_err)}',
                        'status_code': response.status_code,
                    }
            else:
                print(f"[CyberSourceClient] [Payment] ❌ Payment failed (HTTP {response.status_code})")
                try:
                    error_data = response.json() if response.text else {}
                    print(f"[CyberSourceClient] [Payment] 📋 Error response:")
                    print(f"[CyberSourceClient] [Payment]   - Error type: {type(error_data)}")
                    if isinstance(error_data, dict):
                        print(f"[CyberSourceClient] [Payment]   - Error keys: {list(error_data.keys())}")
                        print(f"[CyberSourceClient] [Payment]   - Message: {error_data.get('message', 'N/A')}")
                        print(f"[CyberSourceClient] [Payment]   - Reason: {error_data.get('reason', 'N/A')}")
                        if 'details' in error_data:
                            print(f"[CyberSourceClient] [Payment]   - Details: {error_data['details']}")
                    else:
                        print(f"[CyberSourceClient] [Payment]   - Error: {error_data}")
                    
                    # Log full error response for debugging
                    try:
                        print(f"[CyberSourceClient] [Payment] 📋 Full error response: {json.dumps(error_data, indent=2)}")
                    except Exception:
                        print(f"[CyberSourceClient] [Payment] 📋 Full error response: {error_data}")
                except Exception as parse_err:
                    error_data = {'raw': response.text[:500]}
                    print(f"[CyberSourceClient] [Payment] ⚠️ Failed to parse error response: {parse_err}")
                    print(f"[CyberSourceClient] [Payment]   - Raw response: {response.text[:500]}")
                
                return {
                    'ok': False,
                    'error': error_data,
                    'status_code': response.status_code,
                }
                
        except requests.exceptions.RequestException as e:
            print(f"[CyberSourceClient] [Payment] ❌ Request exception occurred")
            print(f"[CyberSourceClient] [Payment]   - Exception type: {type(e).__name__}")
            print(f"[CyberSourceClient] [Payment]   - Error message: {str(e)}")
            if hasattr(e, 'response') and e.response is not None:
                print(f"[CyberSourceClient] [Payment]   - Response status: {e.response.status_code}")
                try:
                    print(f"[CyberSourceClient] [Payment]   - Response body: {e.response.text[:500]}")
                except Exception:
                    pass
            import traceback
            print(f"[CyberSourceClient] [Payment] Traceback: {traceback.format_exc()}")
            return {
                'ok': False,
                'error': str(e),
                'status_code': 500,
            }
        except Exception as e:
            print(f"[CyberSourceClient] [Payment] ❌ Unexpected error: {e}")
            print(f"[CyberSourceClient] [Payment]   - Exception type: {type(e).__name__}")
            import traceback
            print(f"[CyberSourceClient] [Payment] Full traceback: {traceback.format_exc()}")
            return {
                'ok': False,
                'error': str(e),
                'status_code': 500,
            }
    
    def check_payment_status(
        self,
        transaction_id: str,
    ) -> Dict[str, Any]:
        """
        Check and refresh payment status using CyberSource refresh-payment-status endpoint.
        
        Args:
            transaction_id: CyberSource transaction ID (from payment response)
            
        Returns:
            Payment status response from CyberSource
        """
        print(f"[CyberSourceClient] [PaymentStatus] ========== Checking Payment Status ==========")
        print(f"[CyberSourceClient] [PaymentStatus] Transaction ID: {transaction_id}")
        
        resource = f'/pts/v2/refresh-payment-status/{transaction_id}'
        
        try:
            headers = self._get_headers('POST', resource)
            url = f"{self.api_base}{resource}"
            
            print(f"[CyberSourceClient] [PaymentStatus] 🌐 POST {url}")
            print(f"[CyberSourceClient] [PaymentStatus] ⏳ Sending request to CyberSource...")
            
            # Retry logic for connection issues
            max_retries = 3
            retry_delay = 2
            last_exception = None
            
            for attempt in range(max_retries):
                try:
                    response = requests.post(url, headers=headers, timeout=(10, 30))
                    break
                except (requests.exceptions.ConnectTimeout, requests.exceptions.ConnectionError, requests.exceptions.Timeout) as e:
                    last_exception = e
                    if attempt < max_retries - 1:
                        print(f"[CyberSourceClient] [PaymentStatus] ⚠️ Connection attempt {attempt + 1} failed, retrying...")
                        import time
                        time.sleep(retry_delay)
                        retry_delay *= 2
                    else:
                        raise
            
            if 'response' not in locals():
                raise last_exception
            
            print(f"[CyberSourceClient] [PaymentStatus] 📥 Response received")
            print(f"[CyberSourceClient] [PaymentStatus]   - Status code: {response.status_code}")
            print(f"[CyberSourceClient] [PaymentStatus]   - Content-Type: {response.headers.get('Content-Type', 'N/A')}")
            
            if response.status_code in [200, 201]:
                try:
                    result = response.json()
                    status = result.get('status', 'UNKNOWN')
                    print(f"[CyberSourceClient] [PaymentStatus] ✅ Status check successful")
                    print(f"[CyberSourceClient] [PaymentStatus] 📋 Response details:")
                    print(f"[CyberSourceClient] [PaymentStatus]   - Transaction ID: {result.get('id', 'N/A')}")
                    print(f"[CyberSourceClient] [PaymentStatus]   - Status: {status}")
                    print(f"[CyberSourceClient] [PaymentStatus]   - Response keys: {list(result.keys())}")
                    
                    # Log processor information if available
                    if 'processorInformation' in result:
                        proc_info = result['processorInformation']
                        print(f"[CyberSourceClient] [PaymentStatus]   - Processor:")
                        print(f"[CyberSourceClient] [PaymentStatus]     * Response Code: {proc_info.get('responseCode', 'N/A')}")
                        print(f"[CyberSourceClient] [PaymentStatus]     * Approval Code: {proc_info.get('approvalCode', 'N/A')}")
                    
                    return {
                        'ok': True,
                        'response': result,
                        'status_code': response.status_code,
                    }
                except Exception as json_err:
                    print(f"[CyberSourceClient] [PaymentStatus] ⚠️ Failed to parse JSON response: {json_err}")
                    print(f"[CyberSourceClient] [PaymentStatus]   - Raw response: {response.text[:500]}")
                    return {
                        'ok': False,
                        'error': f'Invalid JSON response: {str(json_err)}',
                        'status_code': response.status_code,
                    }
            else:
                print(f"[CyberSourceClient] [PaymentStatus] ❌ Status check failed (HTTP {response.status_code})")
                try:
                    error_data = response.json() if response.text else {}
                    print(f"[CyberSourceClient] [PaymentStatus] 📋 Error response:")
                    print(f"[CyberSourceClient] [PaymentStatus]   - Error: {error_data}")
                    return {
                        'ok': False,
                        'error': error_data,
                        'status_code': response.status_code,
                    }
                except Exception:
                    return {
                        'ok': False,
                        'error': {'raw': response.text[:500]},
                        'status_code': response.status_code,
                    }
                
        except requests.exceptions.RequestException as e:
            print(f"[CyberSourceClient] [PaymentStatus] ❌ Request exception occurred")
            print(f"[CyberSourceClient] [PaymentStatus]   - Exception type: {type(e).__name__}")
            print(f"[CyberSourceClient] [PaymentStatus]   - Error message: {str(e)}")
            import traceback
            print(f"[CyberSourceClient] [PaymentStatus] Traceback: {traceback.format_exc()}")
            return {
                'ok': False,
                'error': str(e),
                'status_code': 500,
            }
        except Exception as e:
            print(f"[CyberSourceClient] [PaymentStatus] ❌ Unexpected error: {e}")
            import traceback
            print(f"[CyberSourceClient] [PaymentStatus] Full traceback: {traceback.format_exc()}")
            return {
                'ok': False,
                'error': str(e),
                'status_code': 500,
            }
    
    def search_transactions_by_reference(
        self,
        reference_code: str,
        limit: int = 10,
    ) -> Dict[str, Any]:
        """
        Search for transactions by reference code using CyberSource Transaction Search API.
        
        Args:
            reference_code: The client reference code used in the payment
            limit: Maximum number of results to return (default: 10)
            
        Returns:
            Dict with 'ok', 'response' (containing search results), 'status_code', 'error'
        """
        print(f"[CyberSourceClient] [TransactionSearch] ========== Searching Transactions ==========")
        print(f"[CyberSourceClient] [TransactionSearch] Reference Code: {reference_code}")
        print(f"[CyberSourceClient] [TransactionSearch] Limit: {limit}")
        
        # Step 1: Create search request
        create_search_resource = '/tss/v2/searches'
        search_query = f'clientReferenceInformation.code:{reference_code}'
        
        create_search_payload = {
            'save': False,  # Don't save the search
            'name': f'Search_{reference_code}',
            'timezone': 'UTC',
            'query': search_query,
            'offset': 0,
            'limit': limit,
            'sort': 'id:desc,submitTimeUtc:desc',  # Most recent first
        }
        
        try:
            print(f"[CyberSourceClient] [TransactionSearch] 📤 Creating search request...")
            headers = self._get_headers('POST', create_search_resource, create_search_payload)
            url = f"{self.api_base}{create_search_resource}"
            
            print(f"[CyberSourceClient] [TransactionSearch] 🌐 POST {url}")
            print(f"[CyberSourceClient] [TransactionSearch] Query: {search_query}")
            
            response = requests.post(url, json=create_search_payload, headers=headers, timeout=(10, 30))
            
            print(f"[CyberSourceClient] [TransactionSearch] 📥 Create search response: {response.status_code}")
            
            if response.status_code not in [200, 201]:
                error_data = response.json() if response.text else {}
                print(f"[CyberSourceClient] [TransactionSearch] ❌ Failed to create search: {error_data}")
                return {
                    'ok': False,
                    'error': error_data,
                    'status_code': response.status_code,
                }
            
            search_result = response.json()
            search_id = search_result.get('searchId')
            
            if not search_id:
                print(f"[CyberSourceClient] [TransactionSearch] ❌ No searchId in response")
                return {
                    'ok': False,
                    'error': 'No searchId returned from search creation',
                    'status_code': response.status_code,
                }
            
            print(f"[CyberSourceClient] [TransactionSearch] ✅ Search created: {search_id}")
            
            # Step 2: Get search results
            get_search_resource = f'/tss/v2/searches/{search_id}'
            
            print(f"[CyberSourceClient] [TransactionSearch] 📤 Retrieving search results...")
            headers = self._get_headers('GET', get_search_resource)
            url = f"{self.api_base}{get_search_resource}"
            
            print(f"[CyberSourceClient] [TransactionSearch] 🌐 GET {url}")
            
            # Wait a moment for search to complete (CyberSource may need time to process)
            import time
            time.sleep(1)
            
            response = requests.get(url, headers=headers, timeout=(10, 30))
            
            print(f"[CyberSourceClient] [TransactionSearch] 📥 Get results response: {response.status_code}")
            
            if response.status_code not in [200, 201]:
                error_data = response.json() if response.text else {}
                print(f"[CyberSourceClient] [TransactionSearch] ❌ Failed to get results: {error_data}")
                return {
                    'ok': False,
                    'error': error_data,
                    'status_code': response.status_code,
                }
            
            results = response.json()
            transactions = results.get('transactions', [])
            count = len(transactions)
            
            print(f"[CyberSourceClient] [TransactionSearch] ✅ Search completed")
            print(f"[CyberSourceClient] [TransactionSearch]   - Found {count} transaction(s)")
            
            if transactions:
                for idx, tx in enumerate(transactions, 1):
                    tx_id = tx.get('id', 'N/A')
                    tx_status = tx.get('status', 'N/A')
                    tx_ref = tx.get('clientReferenceInformation', {}).get('code', 'N/A')
                    print(f"[CyberSourceClient] [TransactionSearch]   [{idx}] ID: {tx_id}, Status: {tx_status}, Ref: {tx_ref}")
            
            return {
                'ok': True,
                'response': results,
                'transactions': transactions,
                'count': count,
                'status_code': response.status_code,
            }
            
        except requests.exceptions.RequestException as e:
            print(f"[CyberSourceClient] [TransactionSearch] ❌ Request error: {e}")
            import traceback
            print(f"[CyberSourceClient] [TransactionSearch] Traceback: {traceback.format_exc()}")
            return {
                'ok': False,
                'error': str(e),
                'status_code': 500,
            }
        except Exception as e:
            print(f"[CyberSourceClient] [TransactionSearch] ❌ Unexpected error: {e}")
            import traceback
            print(f"[CyberSourceClient] [TransactionSearch] Full traceback: {traceback.format_exc()}")
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


