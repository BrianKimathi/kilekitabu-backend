"""Cybersource Unified Checkout - Capture Context scaffolding."""
from flask import request, jsonify, current_app
from controllers.subscription_controller import require_auth


@require_auth
def generate_capture_context():
    """
    Scaffold endpoint to generate Unified Checkout Capture Context.
    Does not call Cybersource yet; validates input and returns 501 with the payload that would be sent.
    """
    try:
        cfg = current_app.config.get('CONFIG')
        cybersource_client = current_app.config.get('cybersource_client')

        if not cybersource_client:
            return jsonify({'error': 'Cybersource client not configured'}), 503

        body = request.get_json(force=True) or {}
        amount = float((body.get('orderInformation') or {}).get('amountDetails', {}).get('totalAmount') or 0)
        currency = (body.get('orderInformation') or {}).get('amountDetails', {}).get('currency') or getattr(cfg, 'GOOGLE_PAY_CURRENCY', 'USD')

        # Enforce $1.00 min for digital wallets like Google Pay
        if amount < getattr(cfg, 'GOOGLE_PAY_MIN_AMOUNT', 1.0):
            return jsonify({'error': f"Minimum amount is {currency} {getattr(cfg, 'GOOGLE_PAY_MIN_AMOUNT', 1.0):.2f}"}), 400

        # Default payload scaffold based on docs, merge client-provided overrides
        payload = {
            "clientVersion": body.get("clientVersion") or "0.31",
            "targetOrigins": body.get("targetOrigins") or [cfg.BASE_URL],
            "allowedCardNetworks": body.get("allowedCardNetworks") or ["VISA", "MASTERCARD", "AMEX"],
            "allowedPaymentTypes": body.get("allowedPaymentTypes") or ["GOOGLEPAY", "PANENTRY", "CLICKTOPAY"],
            "country": body.get("country") or "US",
            "locale": body.get("locale") or "en_US",
            "captureMandate": body.get("captureMandate") or {
                "billingType": "FULL",
                "requestEmail": True,
                "requestPhone": True,
                "requestShipping": False,
                "showAcceptedNetworkIcons": True
            },
            "orderInformation": {
                "amountDetails": {
                    "totalAmount": f"{amount:.2f}",
                    "currency": currency
                }
            }
        }

        # For now, do not call Cybersource. Return 501 with the payload preview.
        return jsonify({
            "success": False,
            "message": "Capture Context generation not wired to Cybersource yet",
            "request_preview": payload
        }), 501
    except Exception as e:
        import traceback
        print(f"[capture_context] ERROR: {e}")
        traceback.print_exc()
        return jsonify({'error': 'Internal server error', 'message': str(e)}), 500


