"""Helper client for the Node-based CyberSource microservice."""
import json
import time
from typing import Any, Dict, Optional

import requests


class CyberSourceHelperError(Exception):
    """Raised when the helper microservice returns an error."""

    def __init__(
        self,
        message: str,
        status_code: Optional[int] = None,
        response: Optional[Any] = None,
    ):
        super().__init__(message)
        self.status_code = status_code
        self.response = response


class CyberSourceHelperClient:
    """Small HTTP client that proxies card and Google Pay calls to the Node service."""

    def __init__(self, base_url: str, timeout: Optional[tuple] = None, max_retries: int = 2):
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout or (10, 60)  # (connect, read) - Increased read timeout to 60s for Render wake-up
        self.max_retries = max_retries
        print(f"[CyberSourceHelperClient] Configured helper URL: {self.base_url}")
        print(f"[CyberSourceHelperClient] Timeout: {self.timeout}, Max retries: {self.max_retries}")

    def _post(self, path: str, payload: Dict[str, Any]) -> Dict[str, Any]:
        url = f"{self.base_url}{path}"
        
        # Headers to make requests look like legitimate server-to-server API calls
        # This helps bypass Cloudflare bot protection
        headers = {
            'Content-Type': 'application/json',
            'Accept': 'application/json',
            'User-Agent': 'KileKitabu-Backend/1.0',
            'Accept-Language': 'en-US,en;q=0.9',
            'Accept-Encoding': 'gzip, deflate, br',
            'Connection': 'keep-alive',
            'Cache-Control': 'no-cache',
        }
        
        # Create a session to maintain cookies (helps with Cloudflare)
        session = requests.Session()
        session.headers.update(headers)
        
        # Wake up Render.com service if it's sleeping (ping health endpoint first)
        # This helps reduce timeouts on the first request after inactivity
        try:
            health_url = f"{self.base_url}/health"
            session.get(health_url, timeout=(5, 5))
            print(f"[CyberSourceHelperClient] ✅ Health check successful - service is awake")
        except Exception as health_exc:
            print(f"[CyberSourceHelperClient] ⚠️ Health check failed (service may be waking up): {health_exc}")
            # Continue anyway - the actual request will retry if needed
        
        # Retry logic for Render.com spin-down issues and Cloudflare challenges
        last_exception = None
        for attempt in range(self.max_retries + 1):
            try:
                if attempt > 0:
                    # Wait before retry (exponential backoff: 2s, 4s)
                    wait_time = 2 ** attempt
                    print(f"[CyberSourceHelperClient] ⏳ Retry attempt {attempt}/{self.max_retries} after {wait_time}s...")
                    time.sleep(wait_time)
                
                response = session.post(url, json=payload, timeout=self.timeout)
                
                # Check if Cloudflare challenge page was returned
                if response.status_code == 429 or response.status_code == 403:
                    response_text = response.text
                    if 'challenge-platform' in response_text or 'Just a moment' in response_text:
                        print(f"[CyberSourceHelperClient] ⚠️ Cloudflare challenge detected on attempt {attempt + 1}")
                        if attempt < self.max_retries:
                            # Wait longer for Cloudflare to allow the request
                            wait_time = 5 * (attempt + 1)
                            print(f"[CyberSourceHelperClient] ⏳ Waiting {wait_time}s for Cloudflare to allow request...")
                            time.sleep(wait_time)
                            continue
                        else:
                            raise CyberSourceHelperError(
                                "Cloudflare protection is blocking server requests. The helper service may need to whitelist server IPs or adjust Cloudflare settings.",
                                status_code=response.status_code,
                                response={"raw": response_text[:500]}
                            )
                
                # Success - process response
                break
                
            except requests.exceptions.Timeout as exc:
                last_exception = exc
                print(f"[CyberSourceHelperClient] ⚠️ Timeout on attempt {attempt + 1}/{self.max_retries + 1}: {exc}")
                if attempt < self.max_retries:
                    continue
                # If this was the last attempt, raise the error
                print(f"[CyberSourceHelperClient] ❌ Request timeout after {self.max_retries + 1} attempts")
                raise CyberSourceHelperError(
                    f"Service timeout - the payment service may be starting up. Please try again in a few seconds.",
                    status_code=504
                ) from exc
            except requests.RequestException as exc:
                last_exception = exc
                print(f"[CyberSourceHelperClient] ❌ Request error on attempt {attempt + 1}: {exc}")
                if attempt < self.max_retries:
                    continue
                # If this was the last attempt, raise the error
                print(f"[CyberSourceHelperClient] ❌ Request failed after {self.max_retries + 1} attempts")
                raise CyberSourceHelperError(str(exc), status_code=503) from exc
        
        # Process response (only reached if request succeeded)
        if 'response' not in locals():
            if last_exception:
                raise CyberSourceHelperError(str(last_exception), status_code=503) from last_exception
            raise CyberSourceHelperError("Request failed after retries", status_code=503)

        # Try to decode JSON even on error status codes
        try:
            data = response.json()
        except ValueError:
            data = {"raw": response.text}

        if response.status_code >= 400:
            message = data.get("error") if isinstance(data, dict) else response.text
            print(
                f"[CyberSourceHelperClient] ❌ Helper error {response.status_code}: {message}"
            )
            print(
                f"[CyberSourceHelperClient]   - URL: {url}"
            )
            print(
                f"[CyberSourceHelperClient]   - Response body: {data if isinstance(data, dict) else response.text[:200]}"
            )
            raise CyberSourceHelperError(
                message=message or f"Helper request failed (HTTP {response.status_code})",
                status_code=response.status_code,
                response=data,
            )

        return data

    def create_card_payment(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Proxy to POST /api/cards/pay"""
        return self._post("/api/cards/pay", payload)

    def generate_capture_context(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Proxy to POST /api/googlepay/capture-context"""
        return self._post("/api/googlepay/capture-context", payload)
    
    def generate_unified_checkout_capture_context(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Proxy to POST /api/unified-checkout/capture-context"""
        return self._post("/api/unified-checkout/capture-context", payload)

    def charge_googlepay_token(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Proxy to POST /api/googlepay/charge"""
        return self._post("/api/googlepay/charge", payload)
    
    def charge_unified_checkout_token(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Proxy to POST /api/unified-checkout/charge"""
        return self._post("/api/unified-checkout/charge", payload)

    def check_payer_auth_enrollment(
        self, payload: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Proxy to POST /api/payer-auth/enroll - Check if 3D Secure is required"""
        return self._post("/api/payer-auth/enroll", payload)

    def payer_auth_setup(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Proxy to POST /api/payer-auth/setup - Setup payer authentication"""
        return self._post("/api/payer-auth/setup", payload)

    def validate_authentication_results(
        self, payload: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Proxy to POST /api/payer-auth/validate - Validate 3D Secure results"""
        return self._post("/api/payer-auth/validate", payload)

    def search_transactions_by_reference(
        self, reference_code: str, limit: int = 10
    ) -> Dict[str, Any]:
        """Proxy to POST /api/transactions/search - Search transactions by reference code"""
        print(f"[CyberSourceHelperClient] 🔍 Searching transactions by reference: {reference_code}")
        print(f"[CyberSourceHelperClient]   - Endpoint: /api/transactions/search")
        print(f"[CyberSourceHelperClient]   - Limit: {limit}")
        payload = {
            "referenceCode": reference_code,
            "limit": limit,
        }
        result = self._post("/api/transactions/search", payload)
        print(f"[CyberSourceHelperClient] ✅ Search completed via Node.js backend")
        return result


