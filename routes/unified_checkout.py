"""Unified Checkout routes for both card and Google Pay."""
from flask import Blueprint, current_app
from controllers.unified_checkout_controller import (
    unified_checkout_capture_context,
    unified_checkout_charge,
)

bp = Blueprint('unified_checkout', __name__, url_prefix='/api/unified-checkout')


@bp.route('/capture-context', methods=['POST'])
def capture_context():
    """Create Unified Checkout capture context for both card and Google Pay."""
    return unified_checkout_capture_context()


@bp.route('/charge', methods=['POST'])
def charge():
    """Charge a payment using Unified Checkout transient token (for both card and Google Pay)."""
    return unified_checkout_charge()

