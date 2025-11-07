from flask import Blueprint, jsonify, current_app
from datetime import datetime

bp = Blueprint('health', __name__, url_prefix='/api/health')


@bp.route('/live', methods=['GET'])
def live():
    return jsonify({'status': 'ok'}), 200


@bp.route('/ready', methods=['GET'])
def ready():
    db = current_app.config.get('DB')
    fcm = current_app.config.get('FCM_SERVICE')
    ready = db is not None and fcm is not None
    return jsonify({'ready': ready}), (200 if ready else 503)


@bp.route('/keep-alive', methods=['GET'])
def keep_alive():
    """Keep alive endpoint - pinged every 7 minutes to prevent Render.com spin-down"""
    return jsonify({
        'status': 'alive',
        'timestamp': datetime.now().isoformat(),
        'message': 'Server is active'
    }), 200


