"""CyberSource payment routes."""
from flask import Blueprint, current_app, jsonify
from controllers.cybersource_controller import (
    initiate_card_payment,
    handle_webhook,
    require_auth,
    create_subscription,
    check_payment_status,
)
from controllers.flex_controller import flex_charge

cybersource_bp = Blueprint("cybersource", __name__, url_prefix="/api/cybersource")


# Card payment initiation (requires authentication)
@cybersource_bp.route("/initiate", methods=["POST"])
@require_auth
def initiate():
    """Initiate a card payment using raw card details (legacy flow)."""
    return initiate_card_payment()


# Flex / tokenized card charge (requires authentication)
@cybersource_bp.route("/flex/charge", methods=["POST"])
def flex_charge_route():
    """Charge a card using a Flex / Unified transient token."""
    return flex_charge()


# Flex Sessions capture-context for native card tokenization (requires authentication)
@cybersource_bp.route("/flex/capture-context", methods=["POST"])
@require_auth
def flex_capture_context_route():
    """
    Create a Flex Sessions capture context (JWT) for card tokenization.
    """
    client = current_app.config.get("cybersource_flex_client")
    if not client:
        return (
            jsonify({"error": "CyberSource Flex client not configured"}),
            503,
        )

    result = client.create_flex_capture_context()
    if not result.get("ok"):
        return (
            jsonify(
                {
                    "error": "Failed to create Flex capture context",
                    "details": result.get("error"),
                }
            ),
            int(result.get("status_code") or 500),
        )

    return jsonify({"captureContext": result.get("captureContext")}), 200


# Check payment status (requires authentication)
@cybersource_bp.route("/status", methods=["GET", "POST"])
@require_auth
def status():
    """Check payment status using CyberSource refresh-payment-status endpoint."""
    return check_payment_status()


# Webhook endpoint (no auth - validated by signature)
@cybersource_bp.route("/webhook", methods=["POST"])
def webhook():
    """Handle CyberSource webhook notifications."""
    return handle_webhook()


# Create subscription (requires authentication)
@cybersource_bp.route("/subscriptions/create", methods=["POST"])
@require_auth
def create_sub():
    return create_subscription()


