"""
Cron Job Endpoints
Simple GET endpoints for external cron services like cron-jobs.org
"""
from flask import Blueprint, jsonify, request, current_app
from datetime import datetime
import logging

bp = Blueprint('cron', __name__, url_prefix='/api/cron')
logger = logging.getLogger(__name__)


def _check_cron_auth():
    """Check if cron request is authenticated (optional)"""
    config = current_app.config.get('CONFIG')
    # Use CRON_SECRET_KEY if set, otherwise fall back to SECRET_KEY
    cron_secret = config.CRON_SECRET_KEY if hasattr(config, 'CRON_SECRET_KEY') else config.SECRET_KEY
    provided_secret = request.args.get('key') or request.headers.get('X-Cron-Auth')
    
    # If secret is set and not default, require auth
    if cron_secret and cron_secret != 'your-secret-key-here':
        if not provided_secret or provided_secret != cron_secret:
            return False
    return True


@bp.route('/notifications/low-credit', methods=['GET'])
def cron_low_credit():
    """Cron endpoint to trigger low credit notifications
    
    Usage with cron-jobs.org:
    GET https://your-app.onrender.com/api/cron/notifications/low-credit?key=YOUR_SECRET_KEY
    
    Schedule: Daily at 8:00 AM
    """
    if not _check_cron_auth():
        return jsonify({'error': 'Unauthorized'}), 401
    
    try:
        from services.low_credit_scheduler import LowCreditScheduler
        fcm_service = current_app.config.get('FCM_SERVICE')
        
        if not fcm_service:
            return jsonify({'error': 'FCM service not available'}), 500
        
        scheduler = LowCreditScheduler(fcm_service)
        scheduler.check_low_credits()
        
        logger.info("✅ Low credit notifications triggered via cron")
        return jsonify({
            'status': 'success',
            'message': 'Low credit check triggered',
            'timestamp': datetime.now().isoformat()
        }), 200
    except Exception as e:
        logger.error(f"❌ Error in cron low credit: {e}")
        return jsonify({'error': str(e)}), 500


@bp.route('/notifications/debt-reminders', methods=['GET'])
def cron_debt_reminders():
    """Cron endpoint to trigger debt reminder notifications
    
    Usage with cron-jobs.org:
    GET https://your-app.onrender.com/api/cron/notifications/debt-reminders?key=YOUR_SECRET_KEY
    
    Schedule: Daily at 9:00 AM
    """
    if not _check_cron_auth():
        return jsonify({'error': 'Unauthorized'}), 401
    
    try:
        from services.debt_reminder_scheduler import DebtReminderScheduler
        fcm_service = current_app.config.get('FCM_SERVICE')
        
        if not fcm_service:
            return jsonify({'error': 'FCM service not available'}), 500
        
        scheduler = DebtReminderScheduler(fcm_service)
        scheduler.check_upcoming_debts()
        
        logger.info("✅ Debt reminder notifications triggered via cron")
        return jsonify({
            'status': 'success',
            'message': 'Debt reminder check triggered',
            'timestamp': datetime.now().isoformat()
        }), 200
    except Exception as e:
        logger.error(f"❌ Error in cron debt reminders: {e}")
        return jsonify({'error': str(e)}), 500


@bp.route('/notifications/all', methods=['GET'])
def cron_all_notifications():
    """Cron endpoint to trigger all notification checks
    
    Usage with cron-jobs.org:
    GET https://your-app.onrender.com/api/cron/notifications/all?key=YOUR_SECRET_KEY
    
    This triggers:
    - Low credit notifications
    - Debt reminder notifications
    
    Schedule: Can be used as a single endpoint for all notifications
    """
    if not _check_cron_auth():
        return jsonify({'error': 'Unauthorized'}), 401
    
    try:
        from services.low_credit_scheduler import LowCreditScheduler
        from services.debt_reminder_scheduler import DebtReminderScheduler
        fcm_service = current_app.config.get('FCM_SERVICE')
        
        if not fcm_service:
            return jsonify({'error': 'FCM service not available'}), 500
        
        results = {}
        
        # Trigger low credit notifications
        try:
            low_credit_scheduler = LowCreditScheduler(fcm_service)
            low_credit_scheduler.check_low_credits()
            results['low_credit'] = 'success'
        except Exception as e:
            results['low_credit'] = f'error: {str(e)}'
        
        # Trigger debt reminder notifications
        try:
            debt_reminder_scheduler = DebtReminderScheduler(fcm_service)
            debt_reminder_scheduler.check_upcoming_debts()
            results['debt_reminders'] = 'success'
        except Exception as e:
            results['debt_reminders'] = f'error: {str(e)}'
        
        logger.info("✅ All notifications triggered via cron")
        return jsonify({
            'status': 'success',
            'message': 'All notification checks triggered',
            'results': results,
            'timestamp': datetime.now().isoformat()
        }), 200
    except Exception as e:
        logger.error(f"❌ Error in cron all notifications: {e}")
        return jsonify({'error': str(e)}), 500

