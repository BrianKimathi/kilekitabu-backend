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
    """Keep alive endpoint - pinged every 7 minutes to prevent Render.com spin-down
    
    Can be used with cron-jobs.org or any external cron service.
    No authentication required for this endpoint.
    """
    return jsonify({
        'status': 'alive',
        'timestamp': datetime.now().isoformat(),
        'message': 'Server is active'
    }), 200


@bp.route('/ping', methods=['GET'])
def ping():
    """Simple ping endpoint for cron-jobs.org - same as keep-alive"""
    return jsonify({
        'status': 'ok',
        'timestamp': datetime.now().isoformat()
    }), 200


