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
    ) -> None:
        print(f"[MpesaClient] Initializing M-Pesa client")
        print(f"[MpesaClient] Environment: {env}")
        print(f"[MpesaClient] Base URL: {'https://sandbox.safaricom.co.ke' if env == 'sandbox' else 'https://api.safaricom.co.ke'}")
        print(f"[MpesaClient] Consumer Key: {consumer_key[:10]}..." if consumer_key else "[MpesaClient] Consumer Key: NOT SET")
        print(f"[MpesaClient] Consumer Secret: {'*' * len(consumer_secret) if consumer_secret else 'NOT SET'}")
        print(f"[MpesaClient] Short Code: {short_code}")
        print(f"[MpesaClient] Passkey: {'*' * len(passkey) if passkey else 'NOT SET'}")
        print(f"[MpesaClient] Callback URL: {callback_url}")
        
        self.consumer_key = consumer_key
        self.consumer_secret = consumer_secret
        self.short_code = short_code
        self.passkey = passkey
        self.callback_url = callback_url
        self.base = (
            "https://sandbox.safaricom.co.ke" if env == "sandbox" else "https://api.safaricom.co.ke"
        )
        print(f"[MpesaClient] Initialization complete")

    def _access_token(self) -> Optional[str]:
        print(f"[MpesaClient] [Token] Starting OAuth token generation")
        print(f"[MpesaClient] [Token] URL: {self.base}/oauth/v1/generate?grant_type=client_credentials")
        print(f"[MpesaClient] [Token] Consumer Key: {self.consumer_key[:10]}..." if self.consumer_key else "[MpesaClient] [Token] Consumer Key: NOT SET")
        
        try:
            resp = requests.get(
                f"{self.base}/oauth/v1/generate?grant_type=client_credentials",
                auth=(self.consumer_key, self.consumer_secret),
                timeout=20,
            )
            print(f"[MpesaClient] [Token] Response status: {resp.status_code}")
            print(f"[MpesaClient] [Token] Response headers: {dict(resp.headers)}")
            
            if resp.ok:
                token_data = resp.json()
                access_token = token_data.get("access_token")
                expires_in = token_data.get("expires_in", "unknown")
                print(f"[MpesaClient] [Token] ✅ Token generated successfully")
                print(f"[MpesaClient] [Token] Token preview: {access_token[:20]}..." if access_token else "[MpesaClient] [Token] Token: NOT FOUND")
                print(f"[MpesaClient] [Token] Expires in: {expires_in} seconds")
                return access_token
            else:
                print(f"[MpesaClient] [Token] ❌ Token generation failed")
                print(f"[MpesaClient] [Token] Response body: {resp.text}")
                return None
        except Exception as e:
            print(f"[MpesaClient] [Token] ❌ Exception during token generation: {type(e).__name__}: {str(e)}")
            import traceback
            print(f"[MpesaClient] [Token] Traceback: {traceback.format_exc()}")
            return None

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
        # Convert phone to integer (remove + and any non-digits)
        phone_clean = phone_e164.replace("+", "").replace("-", "").replace(" ", "")
        print(f"[MpesaClient] [STK Push]   Phone (cleaned): {phone_clean}")
        phone_int = int(phone_clean)
        print(f"[MpesaClient] [STK Push] ✅ Phone (integer): {phone_int}")
        
        print(f"[MpesaClient] [STK Push] Step 4: Generating password...")
        password = self._password(timestamp)
        print(f"[MpesaClient] [STK Push] ✅ Password generated")
        
        print(f"[MpesaClient] [STK Push] Step 5: Constructing payload...")
        # Use configured shortcode
        short_code_int = int(self.short_code)
        payload = {
            "BusinessShortCode": short_code_int,
            "Password": password,
            "Timestamp": timestamp,
            "TransactionType": "CustomerPayBillOnline",
            "Amount": int(amount),
            "PartyA": phone_int,
            "PartyB": short_code_int,
            "PhoneNumber": phone_int,
            "CallBackURL": self.callback_url,
            "AccountReference": account_ref[:12] if len(account_ref) > 12 else account_ref,
            "TransactionDesc": description[:20] if len(description) > 20 else description,
        }
        print(f"[MpesaClient] [STK Push] ✅ Payload constructed:")
        print(f"[MpesaClient] [STK Push]   BusinessShortCode: {payload['BusinessShortCode']}")
        print(f"[MpesaClient] [STK Push]   Password: {payload['Password'][:30]}...")
        print(f"[MpesaClient] [STK Push]   Timestamp: {payload['Timestamp']}")
        print(f"[MpesaClient] [STK Push]   TransactionType: {payload['TransactionType']}")
        print(f"[MpesaClient] [STK Push]   Amount: {payload['Amount']}")
        print(f"[MpesaClient] [STK Push]   PartyA: {payload['PartyA']}")
        print(f"[MpesaClient] [STK Push]   PartyB: {payload['PartyB']}")
        print(f"[MpesaClient] [STK Push]   PhoneNumber: {payload['PhoneNumber']}")
        print(f"[MpesaClient] [STK Push]   CallBackURL: {payload['CallBackURL']}")
        print(f"[MpesaClient] [STK Push]   AccountReference: {payload['AccountReference']}")
        print(f"[MpesaClient] [STK Push]   TransactionDesc: {payload['TransactionDesc']}")
        
        print(f"[MpesaClient] [STK Push] Step 6: Sending STK Push request...")
        request_url = f"{self.base}/mpesa/stkpush/v1/processrequest"
        print(f"[MpesaClient] [STK Push]   URL: {request_url}")
        print(f"[MpesaClient] [STK Push]   Method: POST")
        print(f"[MpesaClient] [STK Push]   Headers: Authorization: Bearer {token[:20]}...")
        
        try:
            resp = requests.post(
                request_url,
                json=payload,
                headers={"Authorization": f"Bearer {token}"},
                timeout=30,
            )
            print(f"[MpesaClient] [STK Push] ✅ Request sent")
            print(f"[MpesaClient] [STK Push] Step 7: Processing response...")
            print(f"[MpesaClient] [STK Push]   Status Code: {resp.status_code}")
            print(f"[MpesaClient] [STK Push]   Response Headers: {dict(resp.headers)}")
            
            ok = resp.ok
            body = {}
            try:
                body = resp.json()
                print(f"[MpesaClient] [STK Push]   Response Body (JSON): {body}")
            except Exception as json_error:
                body = {"text": resp.text}
                print(f"[MpesaClient] [STK Push]   Response Body (Text): {resp.text}")
                print(f"[MpesaClient] [STK Push]   JSON parse error: {json_error}")
            
            if ok:
                print(f"[MpesaClient] [STK Push] ✅ STK Push request successful")
                if "ResponseCode" in body:
                    print(f"[MpesaClient] [STK Push]   ResponseCode: {body.get('ResponseCode')}")
                if "CheckoutRequestID" in body:
                    print(f"[MpesaClient] [STK Push]   CheckoutRequestID: {body.get('CheckoutRequestID')}")
                if "CustomerMessage" in body:
                    print(f"[MpesaClient] [STK Push]   CustomerMessage: {body.get('CustomerMessage')}")
            else:
                print(f"[MpesaClient] [STK Push] ❌ STK Push request failed")
                if "errorMessage" in body:
                    print(f"[MpesaClient] [STK Push]   Error Message: {body.get('errorMessage')}")
                if "errorCode" in body:
                    print(f"[MpesaClient] [STK Push]   Error Code: {body.get('errorCode')}")
            
            print(f"[MpesaClient] [STK Push] ========== STK Push Request Complete ==========")
            return {"ok": ok, "response": body, "status_code": resp.status_code}
        except Exception as e:
            print(f"[MpesaClient] [STK Push] ❌ Exception during STK Push request: {type(e).__name__}: {str(e)}")
            import traceback
            print(f"[MpesaClient] [STK Push] Traceback: {traceback.format_exc()}")
            print(f"[MpesaClient] [STK Push] ========== STK Push Request Failed ==========")
            return {"ok": False, "error": str(e)}


