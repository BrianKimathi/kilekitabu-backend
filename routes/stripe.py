"""Stripe payment routes."""
from flask import Blueprint
from controllers.stripe_controller import StripeController
from firebase_admin import db
from config import Config

bp = Blueprint('stripe', __name__, url_prefix='/api/stripe')

# Initialize controller
stripe_controller = StripeController(db, Config)

# Routes
@bp.route('/create-intent', methods=['POST'])
def create_payment_intent():
    """Create a Stripe PaymentIntent."""
    return stripe_controller.create_payment_intent()

@bp.route('/confirm', methods=['POST'])
def confirm_payment():
    """Confirm a PaymentIntent."""
    return stripe_controller.confirm_payment()

@bp.route('/charge-card', methods=['POST'])
def charge_card():
    """Charge a card directly."""
    return stripe_controller.charge_card()

@bp.route('/webhook', methods=['POST'])
def webhook():
    """Handle Stripe webhook events."""
    return stripe_controller.handle_webhook()

