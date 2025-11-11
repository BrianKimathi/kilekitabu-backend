"""Google Pay routes."""
from flask import Blueprint, current_app
from controllers.googlepay_controller import GooglePayController
from controllers.subscription_controller import require_auth

bp = Blueprint('googlepay', __name__, url_prefix='/api/googlepay')


@bp.route('/capture-context', methods=['POST'])
def capture_context():
    """Create Unified Checkout capture-context via CyberSource for Google Pay."""
    db = current_app.config.get('DB')
    config = current_app.config.get('CONFIG')
    controller = GooglePayController(db, config)
    return controller.capture_context()

@bp.route('/charge', methods=['POST'])
@require_auth
def charge():
    """Accept Google Pay transient token and charge via configured processor."""
    db = current_app.config.get('DB')
    config = current_app.config.get('CONFIG')
    controller = GooglePayController(db, config)
    return controller.charge()


