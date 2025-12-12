"""CyberSource payment routes."""
from flask import Blueprint, current_app, jsonify
from controllers.cybersource_controller import (
    initiate_card_payment,
    handle_webhook,
    require_auth,
    create_subscription,
    check_payment_status,
)
from controllers.flex_controller import flex_charge

cybersource_bp = Blueprint("cybersource", __name__, url_prefix="/api/cybersource")


# Card payment initiation (requires authentication)
@cybersource_bp.route("/initiate", methods=["POST"])
@require_auth
def initiate():
    """Initiate a card payment using raw card details (legacy flow)."""
    return initiate_card_payment()


# Flex / tokenized card charge (requires authentication)
@cybersource_bp.route("/flex/charge", methods=["POST"])
def flex_charge_route():
    """Charge a card using a Flex / Unified transient token."""
    return flex_charge()


# Flex Sessions capture-context for native card tokenization (requires authentication)
@cybersource_bp.route("/flex/capture-context", methods=["POST"])
@require_auth
def flex_capture_context_route():
    """
    Create a Flex Sessions capture context (JWT) for card tokenization.
    """
    client = current_app.config.get("cybersource_flex_client")
    if not client:
        return (
            jsonify({"error": "CyberSource Flex client not configured"}),
            503,
        )

    result = client.create_flex_capture_context()
    if not result.get("ok"):
        return (
            jsonify(
                {
                    "error": "Failed to create Flex capture context",
                    "details": result.get("error"),
                }
            ),
            int(result.get("status_code") or 500),
        )

    return jsonify({"captureContext": result.get("captureContext")}), 200


# Check payment status (requires authentication)
@cybersource_bp.route("/status", methods=["GET", "POST"])
@require_auth
def status():
    """Check payment status using CyberSource refresh-payment-status endpoint."""
    return check_payment_status()


# Search transactions by reference code (requires authentication)
@cybersource_bp.route("/search", methods=["GET", "POST"])
@require_auth
def search_transactions():
    """Search for transactions by reference code via Node.js backend."""
    from flask import request, jsonify
    from services.cybersource_helper_client import CyberSourceHelperError
    
    print(f"[cybersource_search] ========== Search Transactions ==========")
    
    # Get reference code from query params or JSON body
    reference_code = request.args.get('reference_code') or (request.json.get('reference_code') if request.is_json else None)
    limit = int(request.args.get('limit', 10)) or (request.json.get('limit', 10) if request.is_json else 10)
    
    if not reference_code:
        print(f"[cybersource_search] ❌ No reference_code provided")
        return jsonify({
            'success': False,
            'error': 'reference_code is required'
        }), 400
    
    print(f"[cybersource_search] Reference Code: {reference_code}")
    print(f"[cybersource_search] Limit: {limit}")
    
    # Get CyberSource helper client
    cybersource_helper = current_app.config.get('cybersource_helper')
    if not cybersource_helper:
        print(f"[cybersource_search] ❌ CyberSource helper not configured")
        return jsonify({
            'success': False,
            'error': 'Transaction search is unavailable right now. Please try again later.'
        }), 503
    
    try:
        print(f"[cybersource_search] 🔍 Searching via Node.js backend...")
        result = cybersource_helper.search_transactions_by_reference(reference_code, limit=limit)
        
        transactions = result.get('transactions', [])
        count = result.get('count', 0)
        
        print(f"[cybersource_search] ✅ Search completed: {count} transaction(s) found")
        
        return jsonify({
            'success': True,
            'reference_code': reference_code,
            'count': count,
            'transactions': transactions,
            'response': result,
        }), 200
    
    except CyberSourceHelperError as e:
        error = e.response or str(e)
        status_code = e.status_code or 500
        print(f"[cybersource_search] ❌ Search failed: {error}")
        
        return jsonify({
            'success': False,
            'error': str(error),
            'reference_code': reference_code,
        }), status_code
    
    except Exception as e:
        print(f"[cybersource_search] ❌ Unexpected error: {e}")
        import traceback
        print(f"[cybersource_search] Traceback: {traceback.format_exc()}")
        
        return jsonify({
            'success': False,
            'error': 'Search failed',
        }), 500


# Simple webhook logging endpoint (for testing/debugging)
@cybersource_bp.route("/webhook/log", methods=["POST"])
def webhook_log():
    """Simple webhook endpoint that only logs received requests."""
    from flask import request
    import json
    
    print("=" * 80)
    print("[WEBHOOK_LOG] ========== Webhook Request Received ==========")
    print("=" * 80)
    
    # Log all headers
    print("\n[WEBHOOK_LOG] Headers:")
    print("-" * 80)
    for key, value in request.headers:
        print(f"  {key}: {value}")
    
    # Log raw body
    print("\n[WEBHOOK_LOG] Raw Body:")
    print("-" * 80)
    raw_body = request.get_data(as_text=True)
    print(raw_body)
    
    # Log parsed JSON (if available)
    print("\n[WEBHOOK_LOG] Parsed JSON:")
    print("-" * 80)
    try:
        json_data = request.get_json()
        if json_data:
            print(json.dumps(json_data, indent=2))
        else:
            print("  (No JSON data or unable to parse)")
    except Exception as e:
        print(f"  (Error parsing JSON: {e})")
    
    # Log request info
    print("\n[WEBHOOK_LOG] Request Info:")
    print("-" * 80)
    print(f"  Method: {request.method}")
    print(f"  URL: {request.url}")
    print(f"  Remote Address: {request.remote_addr}")
    print(f"  Content Type: {request.content_type}")
    print(f"  Content Length: {request.content_length}")
    
    print("\n" + "=" * 80)
    print("[WEBHOOK_LOG] ========== End of Webhook Log ==========")
    print("=" * 80 + "\n")
    
    # Return success response
    return jsonify({"status": "logged", "message": "Webhook received and logged"}), 200


# Webhook endpoint (no auth - validated by signature)
@cybersource_bp.route("/webhook", methods=["POST"])
def webhook():
    """Handle CyberSource webhook notifications."""
    return handle_webhook()


# Create subscription (requires authentication)
@cybersource_bp.route("/subscriptions/create", methods=["POST"])
@require_auth
def create_sub():
    return create_subscription()


