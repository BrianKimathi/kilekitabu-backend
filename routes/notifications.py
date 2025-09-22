from flask import Blueprint, jsonify, request, current_app

bp = Blueprint('notifications', __name__, url_prefix='/api/notifications')


@bp.route('/trigger-user', methods=['GET', 'POST'])
def trigger_user():
    db = current_app.config.get('DB')
    fcm_service = current_app.config.get('FCM_SERVICE')
    get_sms_scheduler = current_app.config.get('GET_SMS_SCHEDULER')

    try:
        if not db:
            return jsonify({'error': 'Firebase not available'}), 500
        if fcm_service is None:
            return jsonify({'error': 'FCM service not available'}), 500

        data = request.get_json(silent=True) or {}
        user_id = data.get('user_id') or request.args.get('user_id')
        token = data.get('token') or request.args.get('token')
        if not user_id:
            return jsonify({'error': 'user_id is required'}), 400

        if token:
            db.reference('fcm_tokens').child(user_id).set(token)

        sms_scheduler = get_sms_scheduler()
        if not sms_scheduler:
            return jsonify({'error': 'Reminder service not available'}), 500
        sms_service = sms_scheduler.sms_service

        reminders = sms_service.check_due_reminders(user_id)
        fcm_tokens_ref = db.reference('fcm_tokens')
        final_token = fcm_tokens_ref.child(user_id).get()
        if not final_token:
            return jsonify({'error': 'No token for user'}), 400

        sent = 0
        errors = []
        for r in reminders:
            title = "💰 Debt Due Soon!"
            body = r.get('message') or f"Debt for {r.get('debtor_name','Unknown')} due on {r.get('due_date','')}"
            data_payload = {
                'type': 'debt_due_reminder',
                'debtor_name': r.get('debtor_name','Unknown'),
                'debtor_phone': r.get('debtor_phone',''),
                'amount': str(r.get('amount','0')),
                'due_date': r.get('due_date',''),
                'debt_count': str(r.get('debt_count',1)),
                'user_id': user_id,
                'title': title,
                'body': body,
            }
            ok = fcm_service.send_notification(final_token, title, body, data_payload)
            if ok:
                sent += 1
            else:
                errors.append('send_failed')

        return jsonify({'message': 'ok', 'reminders_found': len(reminders), 'sent': sent, 'errors': errors})
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@bp.route('/cron/due-5days', methods=['GET', 'POST'])
def cron_due_5days():
    db = current_app.config.get('DB')
    fcm_service = current_app.config.get('FCM_SERVICE')
    get_sms_scheduler = current_app.config.get('GET_SMS_SCHEDULER')
    cron_secret = current_app.config.get('CRON_SECRET')

    try:
        # Optional auth
        if cron_secret:
            provided = request.args.get('key') or request.headers.get('X-Cron-Auth')
            if provided != cron_secret:
                return jsonify({'error': 'Unauthorized'}), 401

        if not db:
            return jsonify({'error': 'Firebase not available'}), 500
        if fcm_service is None:
            return jsonify({'error': 'FCM service not available'}), 500

        sms_scheduler = get_sms_scheduler()
        if not sms_scheduler:
            return jsonify({'error': 'Reminder service not available'}), 500
        sms_service = sms_scheduler.sms_service

        tokens = db.reference('fcm_tokens').get() or {}
        total_users = 0
        total_reminders_found = 0
        total_notifications_sent = 0
        results = {}

        for user_id, token in tokens.items():
            total_users += 1
            try:
                reminders = sms_service.check_due_reminders(user_id)
                total_reminders_found += len(reminders)
                sent = 0
                for r in reminders:
                    title = "💰 Debt Due Soon!"
                    body = r.get('message') or f"Debt for {r.get('debtor_name','Unknown')} due on {r.get('due_date','')}"
                    data_payload = {
                        'type': 'debt_due_reminder',
                        'debtor_name': r.get('debtor_name','Unknown'),
                        'debtor_phone': r.get('debtor_phone',''),
                        'amount': str(r.get('amount','0')),
                        'due_date': r.get('due_date',''),
                        'debt_count': str(r.get('debt_count',1)),
                        'user_id': user_id,
                        'title': title,
                        'body': body,
                    }
                    ok = fcm_service.send_notification(token, title, body, data_payload)
                    if ok:
                        sent += 1
                total_notifications_sent += sent
                results[user_id] = {'reminders': len(reminders), 'sent': sent}
            except Exception as e:
                results[user_id] = {'error': str(e)}

        return jsonify({
            'message': 'ok',
            'users_processed': total_users,
            'reminders_found': total_reminders_found,
            'notifications_sent': total_notifications_sent,
            'results': results,
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500


