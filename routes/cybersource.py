"""CyberSource payment routes."""
from flask import Blueprint
from controllers.cybersource_controller import (
    initiate_card_payment,
    handle_webhook,
    require_auth,
    create_subscription,
)

cybersource_bp = Blueprint('cybersource', __name__, url_prefix='/api/cybersource')

# Card payment initiation (requires authentication)
@cybersource_bp.route('/initiate', methods=['POST'])
@require_auth
def initiate():
    """Initiate a card payment."""
    return initiate_card_payment()

# Webhook endpoint (no auth - validated by signature)
@cybersource_bp.route('/webhook', methods=['POST'])
def webhook():
    """Handle CyberSource webhook notifications."""
    return handle_webhook()

# Create subscription (requires authentication)
@cybersource_bp.route('/subscriptions/create', methods=['POST'])
@require_auth
def create_sub():
    return create_subscription()


