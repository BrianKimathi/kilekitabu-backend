"""Helper client for the Node-based CyberSource microservice."""
import json
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

    def __init__(self, base_url: str, timeout: Optional[tuple] = None):
        self.base_url = base_url.rstrip('/')
        self.timeout = timeout or (10, 30)  # (connect, read)
        print(f"[CyberSourceHelperClient] Configured helper URL: {self.base_url}")

    def _post(self, path: str, payload: Dict[str, Any]) -> Dict[str, Any]:
        url = f"{self.base_url}{path}"
        try:
            response = requests.post(url, json=payload, timeout=self.timeout)
        except requests.RequestException as exc:
            print(f"[CyberSourceHelperClient] ❌ Request error: {exc}")
            raise CyberSourceHelperError(str(exc)) from exc

        # Try to decode JSON even on error status codes
        try:
            data = response.json()
        except ValueError:
            data = {'raw': response.text}

        if response.status_code >= 400:
            message = data.get('error') if isinstance(data, dict) else response.text
            print(
                f"[CyberSourceHelperClient] ❌ Helper error {response.status_code}: {message}"
            )
            raise CyberSourceHelperError(
                message=message or 'Helper request failed',
                status_code=response.status_code,
                response=data,
            )

        return data

    def create_card_payment(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Proxy to POST /api/cards/pay"""
        return self._post('/api/cards/pay', payload)

    def generate_capture_context(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Proxy to POST /api/googlepay/capture-context"""
        return self._post('/api/googlepay/capture-context', payload)

    def charge_googlepay_token(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Proxy to POST /api/googlepay/charge"""
        return self._post('/api/googlepay/charge', payload)

