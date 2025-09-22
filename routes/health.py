from flask import Blueprint, jsonify, current_app

bp = Blueprint('health', __name__, url_prefix='/health')


@bp.route('/live', methods=['GET'])
def live():
    return jsonify({'status': 'ok'}), 200


@bp.route('/ready', methods=['GET'])
def ready():
    db = current_app.config.get('DB')
    fcm = current_app.config.get('FCM_SERVICE')
    ready = db is not None and fcm is not None
    return jsonify({'ready': ready}), (200 if ready else 503)


