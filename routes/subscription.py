"""Subscription routes."""
from flask import Blueprint, current_app
from controllers.subscription_controller import (
    SubscriptionController,
    require_auth,
    check_credit_required
)

bp = Blueprint('subscription', __name__, url_prefix='/api')


@bp.route('/user/credit', methods=['GET'])
@require_auth
def get_credit_info():
    """Get user credit information."""
    db = current_app.config.get('DB')
    config = current_app.config.get('CONFIG')
    controller = SubscriptionController(db, config)
    return controller.get_credit_info()


@bp.route('/usage/record', methods=['POST'])
@require_auth
@check_credit_required
def record_usage():
    """Record app usage."""
    db = current_app.config.get('DB')
    config = current_app.config.get('CONFIG')
    controller = SubscriptionController(db, config)
    return controller.record_usage()

