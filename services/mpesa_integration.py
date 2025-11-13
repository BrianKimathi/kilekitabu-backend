import base64
import datetime
import requests
from typing import Optional, Dict, Any


class MpesaClient:
    """Minimal M-Pesa Daraja STK Push client.

    Expects env/config to supply consumer key/secret, short code, passkey and callback URL.
    """

    def __init__(
        self,
        consumer_key: str,
        consumer_secret: str,
        short_code: str,
        passkey: str,
        callback_url: str,
        env: str = "sandbox",
        till_number: str = None,
    ) -> None:
        print(f"[MpesaClient] Initializing M-Pesa client")
        print(f"[MpesaClient] Environment: {env}")
        print(f"[MpesaClient] Base URL: {'https://sandbox.safaricom.co.ke' if env == 'sandbox' else 'https://api.safaricom.co.ke'}")
        print(f"[MpesaClient] Consumer Key: {consumer_key[:10]}..." if consumer_key else "[MpesaClient] Consumer Key: NOT SET")
        print(f"[MpesaClient] Consumer Secret: {'*' * len(consumer_secret) if consumer_secret else 'NOT SET'}")
        print(f"[MpesaClient] Short Code (BusinessShortCode): {short_code}")
        print(f"[MpesaClient] Till Number (PartyB): {till_number or short_code}")
        print(f"[MpesaClient] Passkey: {'*' * len(passkey) if passkey else 'NOT SET'}")
        print(f"[MpesaClient] Callback URL: {callback_url}")
        
        self.consumer_key = consumer_key
        self.consumer_secret = consumer_secret
        self.short_code = short_code
        self.till_number = till_number or short_code  # Default to short_code if not provided
        self.passkey = passkey
        self.callback_url = callback_url
        self.env = env  # Store environment for later use
        self.base = (
            "https://sandbox.safaricom.co.ke" if env == "sandbox" else "https://api.safaricom.co.ke"
        )
        print(f"[MpesaClient] Initialization complete")

    def _access_token(self) -> Optional[str]:
        print(f"[MpesaClient] [Token] ========== OAuth Token Request ==========")
        print(f"[MpesaClient] [Token] Base URL: {self.base}")
        print(f"[MpesaClient] [Token] Full URL: {self.base}/oauth/v1/generate?grant_type=client_credentials")
        print(f"[MpesaClient] [Token] Consumer Key: {self.consumer_key[:10]}..." if self.consumer_key else "[MpesaClient] [Token] Consumer Key: NOT SET")
        print(f"[MpesaClient] [Token] Consumer Key length: {len(self.consumer_key) if self.consumer_key else 0}")
        print(f"[MpesaClient] [Token] Consumer Secret: {'*' * min(20, len(self.consumer_secret)) if self.consumer_secret else 'NOT SET'}")
        print(f"[MpesaClient] [Token] Consumer Secret length: {len(self.consumer_secret) if self.consumer_secret else 0}")
        print(f"[MpesaClient] [Token] Authentication: Basic Auth (Consumer Key + Secret)")
        print(f"[MpesaClient] [Token] Timeout: 20 seconds")
        
        try:
            import time
            request_start = time.time()
            print(f"[MpesaClient] [Token] 📤 Sending GET request to Safaricom OAuth endpoint...")
            
            resp = requests.get(
                f"{self.base}/oauth/v1/generate?grant_type=client_credentials",
                auth=(self.consumer_key, self.consumer_secret),
                timeout=20,
            )
            
            request_duration = time.time() - request_start
            print(f"[MpesaClient] [Token] ⏱️ Request duration: {request_duration:.3f} seconds")
            print(f"[MpesaClient] [Token] 📥 Response received")
            print(f"[MpesaClient] [Token]   Status Code: {resp.status_code}")
            print(f"[MpesaClient] [Token]   Status Text: {resp.reason}")
            print(f"[MpesaClient] [Token]   Response Headers:")
            for key, value in resp.headers.items():
                print(f"[MpesaClient] [Token]     {key}: {value}")
            
            if resp.ok:
                try:
                    token_data = resp.json()
                    print(f"[MpesaClient] [Token]   Response Body (JSON): {token_data}")
                    access_token = token_data.get("access_token")
                    expires_in = token_data.get("expires_in", "unknown")
                    token_type = token_data.get("token_type", "unknown")
                    
                    print(f"[MpesaClient] [Token] ✅ Token generated successfully")
                    print(f"[MpesaClient] [Token]   Token Type: {token_type}")
                    print(f"[MpesaClient] [Token]   Access Token: {access_token[:30]}..." if access_token else "[MpesaClient] [Token]   Access Token: NOT FOUND")
                    print(f"[MpesaClient] [Token]   Access Token length: {len(access_token) if access_token else 0}")
                    print(f"[MpesaClient] [Token]   Expires in: {expires_in} seconds ({int(expires_in) // 60 if isinstance(expires_in, (int, float)) else 'N/A'} minutes)")
                    return access_token
                except Exception as json_error:
                    print(f"[MpesaClient] [Token] ❌ Failed to parse JSON response")
                    print(f"[MpesaClient] [Token]   Response text: {resp.text}")
                    print(f"[MpesaClient] [Token]   JSON error: {type(json_error).__name__}: {str(json_error)}")
                    return None
            else:
                print(f"[MpesaClient] [Token] ❌ Token generation failed (HTTP {resp.status_code})")
                print(f"[MpesaClient] [Token]   Response text: {resp.text}")
                print(f"[MpesaClient] [Token]   Response headers: {dict(resp.headers)}")
                try:
                    error_body = resp.json()
                    print(f"[MpesaClient] [Token]   Error body (JSON): {error_body}")
                except:
                    pass
                return None
        except requests.exceptions.Timeout:
            print(f"[MpesaClient] [Token] ❌ Request timeout after 20 seconds")
            return None
        except requests.exceptions.ConnectionError as e:
            print(f"[MpesaClient] [Token] ❌ Connection error: {type(e).__name__}: {str(e)}")
            return None
        except Exception as e:
            print(f"[MpesaClient] [Token] ❌ Exception during token generation: {type(e).__name__}: {str(e)}")
            import traceback
            print(f"[MpesaClient] [Token] Traceback: {traceback.format_exc()}")
            return None
        finally:
            print(f"[MpesaClient] [Token] ========== OAuth Token Request Complete ==========")

    def _password(self, timestamp: str) -> str:
        print(f"[MpesaClient] [Password] Generating password")
        print(f"[MpesaClient] [Password] Timestamp: {timestamp}")
        # Password = Base64(BusinessShortCode + Passkey + Timestamp)
        business_short_code = str(self.short_code)
        print(f"[MpesaClient] [Password] BusinessShortCode: {business_short_code}")
        print(f"[MpesaClient] [Password] Passkey length: {len(self.passkey) if self.passkey else 0}")
        print(f"[MpesaClient] [Password] Passkey preview: {self.passkey[:20] if self.passkey else 'NOT SET'}...")
        
        raw_string = f"{business_short_code}{self.passkey}{timestamp}"
        print(f"[MpesaClient] [Password] Raw string length: {len(raw_string)}")
        print(f"[MpesaClient] [Password] Raw string (first 30 chars): {raw_string[:30]}...")
        
        raw = raw_string.encode("utf-8")
        password = base64.b64encode(raw).decode("utf-8")
        print(f"[MpesaClient] [Password] ✅ Password generated: {password[:30]}...")
        return password

    def initiate_stk_push(self, amount: float, phone_e164: str, account_ref: str, description: str) -> Dict[str, Any]:
        print(f"[MpesaClient] [STK Push] ========== Starting STK Push Request ==========")
        print(f"[MpesaClient] [STK Push] Input parameters:")
        print(f"[MpesaClient] [STK Push]   Amount: {amount}")
        print(f"[MpesaClient] [STK Push]   Phone (raw): {phone_e164}")
        print(f"[MpesaClient] [STK Push]   Account Reference: {account_ref}")
        print(f"[MpesaClient] [STK Push]   Description: {description}")
        
        print(f"[MpesaClient] [STK Push] Step 1: Generating OAuth token...")
        token = self._access_token()
        if not token:
            print(f"[MpesaClient] [STK Push] ❌ Failed to get access token, aborting")
            return {"ok": False, "error": "token_failed"}
        print(f"[MpesaClient] [STK Push] ✅ Access token obtained")

        print(f"[MpesaClient] [STK Push] Step 2: Generating timestamp...")
        timestamp = datetime.datetime.now().strftime("%Y%m%d%H%M%S")
        print(f"[MpesaClient] [STK Push] ✅ Timestamp: {timestamp}")
        
        print(f"[MpesaClient] [STK Push] Step 3: Processing phone number...")
        # Convert phone to E.164 digits only (remove + and any non-digits)
        phone_clean = phone_e164.replace("+", "").replace("-", "").replace(" ", "")
        print(f"[MpesaClient] [STK Push]   Phone (cleaned): {phone_clean}")
        print(f"[MpesaClient] [STK Push]   Environment: {self.env}")
        
        # Sandbox uses strings, production uses integers
        if self.env == "sandbox":
            # Sandbox: Keep as string
            phone_value = phone_clean
            print(f"[MpesaClient] [STK Push] ✅ Phone (string for sandbox): {phone_value}")
        else:
            # Production: Convert to integer
            try:
                phone_value = int(phone_clean)
                print(f"[MpesaClient] [STK Push] ✅ Phone (integer for production): {phone_value}")
            except ValueError:
                print(f"[MpesaClient] [STK Push] ❌ Failed to convert phone to integer: {phone_clean}")
                return {"ok": False, "error": "invalid_phone_format"}
        
        print(f"[MpesaClient] [STK Push] Step 4: Generating password...")
        password = self._password(timestamp)
        print(f"[MpesaClient] [STK Push] ✅ Password generated")
        
        print(f"[MpesaClient] [STK Push] Step 5: Constructing payload...")
        # Sandbox uses strings, production uses integers
        if self.env == "sandbox":
            # Sandbox: Use strings for numeric fields
            short_code_value = str(self.short_code)
            till_number_value = str(self.till_number)
            amount_value = str(int(round(amount)))
            print(f"[MpesaClient] [STK Push]   Using string format for sandbox")
        else:
            # Production: Use integers
            short_code_value = int(self.short_code)
            till_number_value = int(self.till_number)
            amount_value = int(round(amount))
            print(f"[MpesaClient] [STK Push]   Using integer format for production")

        payload = {
            "BusinessShortCode": short_code_value,
            "Password": password,
            "Timestamp": timestamp,
            "TransactionType": "CustomerBuyGoodsOnline",
            "Amount": amount_value,
            "PartyA": phone_value,
            "PartyB": till_number_value,
            "PhoneNumber": phone_value,
            "CallBackURL": self.callback_url,
            "AccountReference": account_ref[:12] if len(account_ref) > 12 else account_ref,
            "TransactionDesc": description[:20] if len(description) > 20 else description,
        }
        print(f"[MpesaClient] [STK Push] ✅ Payload constructed: {payload}")
        try:
            import json as _json
            print(f"[MpesaClient] [STK Push]   Full JSON payload: {_json.dumps(payload, ensure_ascii=False)}")
        except Exception:
            print(f"[MpesaClient] [STK Push]   BusinessShortCode: {payload['BusinessShortCode']}")
            print(f"[MpesaClient] [STK Push]   Password: {payload['Password'][:30]}...")
            print(f"[MpesaClient] [STK Push]   Timestamp: {payload['Timestamp']}")
            print(f"[MpesaClient] [STK Push]   TransactionType: {payload['TransactionType']}")
            print(f"[MpesaClient] [STK Push]   Amount: {payload['Amount']}")
            print(f"[MpesaClient] [STK Push]   PartyA: {payload['PartyA']}")
            print(f"[MpesaClient] [STK Push]   PartyB (Till Number): {payload['PartyB']}")
            print(f"[MpesaClient] [STK Push]   PhoneNumber: {payload['PhoneNumber']}")
            print(f"[MpesaClient] [STK Push]   CallBackURL: {payload['CallBackURL']}")
            print(f"[MpesaClient] [STK Push]   AccountReference: {payload['AccountReference']}")
            print(f"[MpesaClient] [STK Push]   TransactionDesc: {payload['TransactionDesc']}")
        
        print(f"[MpesaClient] [STK Push] Step 6: Sending STK Push request...")
        request_url = f"{self.base}/mpesa/stkpush/v1/processrequest"
        print(f"[MpesaClient] [STK Push]   Base URL: {self.base}")
        print(f"[MpesaClient] [STK Push]   Full URL: {request_url}")
        print(f"[MpesaClient] [STK Push]   Method: POST")
        print(f"[MpesaClient] [STK Push]   Content-Type: application/json")
        print(f"[MpesaClient] [STK Push]   Authorization: Bearer {token[:30]}...")
        print(f"[MpesaClient] [STK Push]   Token length: {len(token)}")
        print(f"[MpesaClient] [STK Push]   Timeout: 30 seconds")
        
        try:
            import time
            import json as _json
            request_start = time.time()
            
            # Log the exact request being sent
            print(f"[MpesaClient] [STK Push] 📤 Sending POST request to Safaricom STK Push endpoint...")
            print(f"[MpesaClient] [STK Push]   Request payload size: {len(_json.dumps(payload))} bytes")
            
            resp = requests.post(
                request_url,
                json=payload,
                headers={"Authorization": f"Bearer {token}"},
                timeout=30,
            )
            
            request_duration = time.time() - request_start
            print(f"[MpesaClient] [STK Push] ⏱️ Request duration: {request_duration:.3f} seconds")
            print(f"[MpesaClient] [STK Push] ✅ Request sent")
            print(f"[MpesaClient] [STK Push] Step 7: Processing response...")
            print(f"[MpesaClient] [STK Push] 📥 Response received")
            print(f"[MpesaClient] [STK Push]   Status Code: {resp.status_code}")
            print(f"[MpesaClient] [STK Push]   Status Text: {resp.reason}")
            print(f"[MpesaClient] [STK Push]   Response Headers:")
            for key, value in resp.headers.items():
                print(f"[MpesaClient] [STK Push]     {key}: {value}")
            
            ok = resp.ok
            body = {}
            try:
                body = resp.json()
                print(f"[MpesaClient] [STK Push]   Response Body (JSON):")
                print(f"[MpesaClient] [STK Push]     {_json.dumps(body, indent=2, ensure_ascii=False)}")
            except Exception as json_error:
                body = {"text": resp.text}
                print(f"[MpesaClient] [STK Push]   Response Body (Text): {resp.text}")
                print(f"[MpesaClient] [STK Push]   Response Body length: {len(resp.text)} bytes")
                print(f"[MpesaClient] [STK Push]   JSON parse error: {type(json_error).__name__}: {str(json_error)}")
            
            if ok:
                print(f"[MpesaClient] [STK Push] ✅ STK Push request successful (HTTP {resp.status_code})")
                if "ResponseCode" in body:
                    response_code = body.get('ResponseCode')
                    print(f"[MpesaClient] [STK Push]   ResponseCode: {response_code} (type: {type(response_code).__name__})")
                    if response_code == 0 or response_code == "0":
                        print(f"[MpesaClient] [STK Push]   ✅ ResponseCode 0 = Success")
                    else:
                        print(f"[MpesaClient] [STK Push]   ⚠️ ResponseCode {response_code} = Non-zero (may indicate issue)")
                if "CheckoutRequestID" in body:
                    checkout_id = body.get('CheckoutRequestID')
                    print(f"[MpesaClient] [STK Push]   CheckoutRequestID: {checkout_id}")
                if "CustomerMessage" in body:
                    customer_msg = body.get('CustomerMessage')
                    print(f"[MpesaClient] [STK Push]   CustomerMessage: {customer_msg}")
                if "MerchantRequestID" in body:
                    merchant_req_id = body.get('MerchantRequestID')
                    print(f"[MpesaClient] [STK Push]   MerchantRequestID: {merchant_req_id}")
                if "ResponseDescription" in body:
                    response_desc = body.get('ResponseDescription')
                    print(f"[MpesaClient] [STK Push]   ResponseDescription: {response_desc}")
            else:
                print(f"[MpesaClient] [STK Push] ❌ STK Push request failed (HTTP {resp.status_code})")
                if "errorMessage" in body:
                    print(f"[MpesaClient] [STK Push]   Error Message: {body.get('errorMessage')}")
                if "errorCode" in body:
                    print(f"[MpesaClient] [STK Push]   Error Code: {body.get('errorCode')}")
                if "requestId" in body:
                    print(f"[MpesaClient] [STK Push]   Request ID: {body.get('requestId')}")
            
            print(f"[MpesaClient] [STK Push] ========== STK Push Request Complete ==========")
            return {"ok": ok, "response": body, "status_code": resp.status_code}
        except requests.exceptions.Timeout:
            print(f"[MpesaClient] [STK Push] ❌ Request timeout after 30 seconds")
            print(f"[MpesaClient] [STK Push] ========== STK Push Request Failed ==========")
            return {"ok": False, "error": "timeout"}
        except requests.exceptions.ConnectionError as e:
            print(f"[MpesaClient] [STK Push] ❌ Connection error: {type(e).__name__}: {str(e)}")
            print(f"[MpesaClient] [STK Push] ========== STK Push Request Failed ==========")
            return {"ok": False, "error": f"connection_error: {str(e)}"}
        except Exception as e:
            print(f"[MpesaClient] [STK Push] ❌ Exception during STK Push request: {type(e).__name__}: {str(e)}")
            import traceback
            print(f"[MpesaClient] [STK Push] Traceback: {traceback.format_exc()}")
            print(f"[MpesaClient] [STK Push] ========== STK Push Request Failed ==========")
            return {"ok": False, "error": str(e)}


