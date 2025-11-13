"""Payment routes."""
from flask import Blueprint, current_app, request
from controllers.payment_controller import PaymentController, require_auth

bp = Blueprint('payment', __name__, url_prefix='/api')


@bp.route('/mpesa/initiate', methods=['POST'])
@require_auth
def initiate_payment():
    """Initiate M-Pesa payment."""
    print(f"[mpesa_route] ========== /api/mpesa/initiate Request ==========")
    print(f"[mpesa_route] Method: {request.method}")
    print(f"[mpesa_route] Headers: {dict(request.headers)}")
    print(f"[mpesa_route] Content-Type: {request.content_type}")
    print(f"[mpesa_route] Content-Length: {request.content_length}")
    
    db = current_app.config.get('DB')
    mpesa_client = current_app.config.get('MPESA_CLIENT')
    config = current_app.config.get('CONFIG')
    
    print(f"[mpesa_route] DB available: {db is not None}")
    print(f"[mpesa_route] M-Pesa client available: {mpesa_client is not None}")
    print(f"[mpesa_route] Config available: {config is not None}")
    
    controller = PaymentController(db, mpesa_client, config)
    result = controller.initiate_payment()
    
    print(f"[mpesa_route] Response status: {result[1] if isinstance(result, tuple) else 'N/A'}")
    print(f"[mpesa_route] ========== /api/mpesa/initiate Response ==========")
    return result


@bp.route('/mpesa/callback', methods=['POST'])
def mpesa_callback():
    """Handle M-Pesa callback."""
    print(f"[mpesa_route] ========== /api/mpesa/callback Request ==========")
    print(f"[mpesa_route] Method: {request.method}")
    print(f"[mpesa_route] Headers: {dict(request.headers)}")
    print(f"[mpesa_route] Content-Type: {request.content_type}")
    print(f"[mpesa_route] Content-Length: {request.content_length}")
    print(f"[mpesa_route] Remote Address: {request.remote_addr}")
    print(f"[mpesa_route] User-Agent: {request.headers.get('User-Agent', 'N/A')}")
    
    db = current_app.config.get('DB')
    mpesa_client = current_app.config.get('MPESA_CLIENT')
    config = current_app.config.get('CONFIG')
    
    print(f"[mpesa_route] DB available: {db is not None}")
    print(f"[mpesa_route] M-Pesa client available: {mpesa_client is not None}")
    print(f"[mpesa_route] Config available: {config is not None}")
    
    controller = PaymentController(db, mpesa_client, config)
    result = controller.handle_callback()
    
    print(f"[mpesa_route] Response status: {result[1] if isinstance(result, tuple) else 'N/A'}")
    print(f"[mpesa_route] ========== /api/mpesa/callback Response ==========")
    return result

