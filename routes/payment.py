"""Payment routes."""
from flask import Blueprint, current_app
from controllers.payment_controller import PaymentController, require_auth

bp = Blueprint('payment', __name__, url_prefix='/api')


@bp.route('/mpesa/initiate', methods=['POST'])
@require_auth
def initiate_payment():
    """Initiate M-Pesa payment."""
    db = current_app.config.get('DB')
    mpesa_client = current_app.config.get('MPESA_CLIENT')
    config = current_app.config.get('CONFIG')
    controller = PaymentController(db, mpesa_client, config)
    return controller.initiate_payment()


@bp.route('/mpesa/callback', methods=['POST'])
def mpesa_callback():
    """Handle M-Pesa callback."""
    db = current_app.config.get('DB')
    mpesa_client = current_app.config.get('MPESA_CLIENT')
    config = current_app.config.get('CONFIG')
    controller = PaymentController(db, mpesa_client, config)
    return controller.handle_callback()

