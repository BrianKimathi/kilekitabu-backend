"""Config info routes for exposing runtime configuration needed by clients."""
from flask import Blueprint, current_app, jsonify

bp = Blueprint('config_info', __name__, url_prefix='/api/config')


@bp.route('/info', methods=['GET'])
def info():
    """Return minimal configuration info for client verification."""
    cfg = current_app.config.get('CONFIG')
    base_url = getattr(cfg, 'BASE_URL', None)
    callback = getattr(cfg, 'MPESA_CALLBACK_URL', None)
    return jsonify({
        'base_url': base_url,
        'mpesa_callback_url': callback,
        'service': 'KileKitabu Backend'
    })


