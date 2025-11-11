"""Google Pay controller - scaffolding for Google Pay payments."""
import datetime
import uuid
from flask import request, jsonify, current_app
from controllers.subscription_controller import require_auth


class GooglePayController:
    """Controller for Google Pay payment operations (structure only)."""

    def __init__(self, db, config):
        self.db = db
        self.config = config

    def capture_context(self):
        """Create a Unified Checkout capture-context via CyberSource."""
        try:
            cs_client = current_app.config.get('cybersource_client')
            if not cs_client:
                return jsonify({'error': 'CyberSource not configured'}), 503

            data = request.get_json(silent=True) or {}
            # Derive default origin from BASE_URL
            base_url = getattr(self.config, 'BASE_URL', 'https://kilekitabu-backend.onrender.com')
            default_origin = base_url if base_url.startswith('http') else f"https://{base_url}"
            target_origins = data.get('targetOrigins') or [default_origin]
            allowed_networks = data.get('allowedCardNetworks')
            allowed_types = data.get('allowedPaymentTypes') or ['GOOGLEPAY']
            country = (data.get('country') or 'KE').upper()
            locale_in = data.get('locale') or 'en-KE'
            # CyberSource requires locale like en_US (underscore, region upper)
            try:
                parts = locale_in.replace('-', '_').split('_', 1)
                if len(parts) == 2:
                    locale = f"{parts[0].lower()}_{parts[1].upper()}"
                else:
                    locale = locale_in.replace('-', '_')
            except Exception:
                locale = 'en_KE'
            client_version = data.get('clientVersion') or '0.31'
            amount = None
            currency = None
            try:
                if 'amount' in data:
                    amount = float(data.get('amount'))
                if 'currency' in data and data.get('currency'):
                    currency = str(data.get('currency')).upper()
            except Exception:
                amount = None
                currency = None
            extra = data.get('extra')

            print("[googlepay_capture_context] Preparing request")
            print(f"[googlepay_capture_context] BASE_URL={base_url}")
            print(f"[googlepay_capture_context] targetOrigins={target_origins}")
            print(f"[googlepay_capture_context] allowedPaymentTypes={allowed_types}")
            print(f"[googlepay_capture_context] allowedCardNetworks={allowed_networks}")
            print(f"[googlepay_capture_context] country={country} locale={locale} clientVersion={client_version}")
            print(f"[googlepay_capture_context] orderInformation.amount={amount} currency={currency}")

            result = cs_client.create_capture_context(
                target_origins=target_origins,
                allowed_card_networks=allowed_networks,
                allowed_payment_types=allowed_types,
                country=country,
                locale=locale,
                client_version=client_version,
                amount=amount,
                currency=currency,
                extra=extra,
            )
            status = result.get('status_code', 500)
            if result.get('ok'):
                print("[googlepay_capture_context] ✅ capture-context success")
                return jsonify(result.get('response') or {}), status
            print(f"[googlepay_capture_context] ❌ capture-context failed: {result.get('error')}")
            return jsonify({'error': 'capture-context failed', 'details': result.get('error')}), status
        except Exception as e:
            import traceback
            print(f"[googlepay_capture_context] ERROR: {e}")
            traceback.print_exc()
            return jsonify({'error': 'Internal server error', 'message': str(e)}), 500

    @require_auth
    def charge(self):
        """Accept Google Pay transient token and create/capture a payment via configured processor."""
        try:
            if not self.db:
                return jsonify({'error': 'Database unavailable'}), 503

            data = request.get_json(force=True) or {}
            amount = float(data.get('amount') or 0)
            currency = (data.get('currency') or 'USD').upper()
            transient_token = data.get('transientToken')  # Unified Checkout token
            google_pay_token = data.get('googlePayToken') or data.get('paymentData')  # fallback (not preferred)

            min_amount = float(getattr(self.config, 'GOOGLE_PAY_MIN_AMOUNT', 1.0))
            enabled = getattr(self.config, 'GOOGLE_PAY_ENABLED', True)
            processor = getattr(self.config, 'GOOGLE_PAY_PROCESSOR', '')  # e.g., 'cybersource', 'stripe'

            print(f"[googlepay_charge] user_id={getattr(request, 'user_id', None)} amount={amount} {currency} enabled={enabled} processor={processor or 'NONE'}")

            if not enabled:
                return jsonify({'error': 'Google Pay disabled'}), 503

            if amount < min_amount:
                return jsonify({'error': f"Minimum amount is {currency} {min_amount:.2f}"}), 400

            if not (transient_token or google_pay_token):
                return jsonify({'error': 'transientToken (preferred) or googlePayToken is required'}), 400

            # Create a payment record (pending) - will be updated after processor capture
            user_id = getattr(request, 'user_id', None)
            payment_id = str(uuid.uuid4())

            payment_info = {
                'payment_id': payment_id,
                'user_id': user_id,
                'amount': amount,
                'currency': currency,
                'status': 'pending',
                'provider': 'googlepay',
                'created_at': datetime.datetime.now(datetime.timezone.utc).isoformat(),
                'transientToken_present': bool(transient_token),
                'googlePayToken_present': bool(google_pay_token),
            }
            self.db.reference(f'payments/{payment_id}').set(payment_info)
            print(f"[googlepay_charge] payment created id={payment_id}")

            if (processor or '').strip().lower() == 'cybersource':
                cs_client = current_app.config.get('cybersource_client')
                if not cs_client:
                    return jsonify({'error': 'CyberSource not configured'}), 503

                reference_code = payment_id[:27]  # keep within sample limits

                if transient_token:
                    result = cs_client.create_payment_with_transient_token(
                        amount=amount,
                        currency=currency,
                        transient_token=transient_token,
                        reference_code=reference_code,
                        capture=True,
                    )
                else:
                    # Fallback path is not recommended; return 400 to enforce transient token usage
                    return jsonify({'error': 'Provide transientToken obtained via capture-context'}), 400

                status_code = result.get('status_code', 500)
                if not result.get('ok'):
                    # Mark as failed
                    self.db.reference(f'payments/{payment_id}').update({
                        'status': 'failed',
                        'provider_error': result.get('error'),
                        'updated_at': datetime.datetime.now(datetime.timezone.utc).isoformat(),
                    })
                    return jsonify({'success': False, 'payment_id': payment_id, 'error': result.get('error')}), status_code

                # Success path
                resp = result.get('response') or {}
                status = (resp.get('status') or '').upper()
                now_iso = datetime.datetime.now(datetime.timezone.utc).isoformat()

                # Compute credit days (same heuristic as other flows)
                daily_rate = float(getattr(self.config, 'DAILY_RATE', 5.0))
                credit_days = max(1, int(amount / daily_rate)) if daily_rate > 0 else int(amount)

                # Update user credit
                try:
                    user_ref = self.db.reference(f'users/{user_id}')
                    user_data = user_ref.get() or {}
                    current_credit = int(float(user_data.get('credit_balance', 0) or 0))

                    # Monthly spend tracking
                    month_key = datetime.datetime.now(datetime.timezone.utc).strftime('%Y-%m')
                    monthly = user_data.get('monthly_paid', {}) or {}
                    monthly[month_key] = float(monthly.get(month_key, 0) or 0) + float(amount)

                    new_credit = current_credit + credit_days
                    user_ref.update({
                        'credit_balance': int(new_credit),
                        'total_payments': float(user_data.get('total_payments', 0) or 0) + float(amount),
                        'monthly_paid': monthly,
                        'last_payment_date': now_iso,
                        'updated_at': now_iso,
                    })
                except Exception as ue:
                    print(f"[googlepay_charge] ⚠️ User credit update error: {ue}")

                # Update payment record
                self.db.reference(f'payments/{payment_id}').update({
                    'status': 'completed' if status in ['AUTHORIZED', 'PENDING', 'SETTLED'] else status.lower() or 'completed',
                    'provider_data': resp,
                    'credit_days': credit_days,
                    'completed_at': now_iso,
                    'updated_at': now_iso,
                })

                return jsonify({
                    'success': True,
                    'payment_id': payment_id,
                    'status': 'completed',
                    'credit_days': credit_days,
                }), 200

            # No processor configured
            return jsonify({'error': 'GOOGLE_PAY_PROCESSOR not configured'}), 501
        except Exception as e:
            import traceback
            print(f"[googlepay_charge] ERROR: {e}")
            traceback.print_exc()
            return jsonify({'error': 'Internal server error', 'message': str(e)}), 500


