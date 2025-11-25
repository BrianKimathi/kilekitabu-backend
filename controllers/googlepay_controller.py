"""Google Pay controller - scaffolding for Google Pay payments."""
import datetime
import json
import uuid
from flask import request, jsonify, current_app
from controllers.subscription_controller import require_auth
from services.cybersource_helper_client import CyberSourceHelperError


class GooglePayController:
    """Controller for Google Pay payment operations (structure only)."""

    def __init__(self, db, config):
        self.db = db
        self.config = config

    def capture_context(self):
        """Create a Unified Checkout capture-context via CyberSource."""
        try:
            raw_payload = request.get_json(silent=True) or {}
            print(
                "[googlepay_capture_context] 🔍 Incoming request: "
                f"{json.dumps(raw_payload, default=str)}"
            )
            helper_client = current_app.config.get('cybersource_helper')
            if not helper_client:
                return jsonify({'error': 'CyberSource helper not configured'}), 503

            data = raw_payload
            # Derive default origin from BASE_URL
            base_url = getattr(self.config, 'BASE_URL', 'https://kilekitabu-backend.onrender.com')
            default_origin = base_url if base_url.startswith('http') else f"https://{base_url}"
            target_origins = data.get('targetOrigins') or [default_origin]
            allowed_networks = data.get('allowedCardNetworks') or ['VISA', 'MASTERCARD', 'AMEX']
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

            helper_payload = {
                'targetOrigins': target_origins,
                'allowedCardNetworks': allowed_networks,
                'allowedPaymentTypes': allowed_types,
                'country': country,
                'locale': locale,
                'clientVersion': client_version,
            }
            if amount is not None:
                helper_payload['amount'] = amount
            if currency:
                helper_payload['currency'] = currency
            if extra and isinstance(extra, dict):
                helper_payload.update(extra)

            print(
                "[googlepay_capture_context] ⏩ Forwarding payload to helper: "
                f"{json.dumps(helper_payload, default=str)}"
            )
            capture_context = helper_client.generate_capture_context(helper_payload)
            response_payload = dict(capture_context or {})
            if isinstance(response_payload.get('captureContext'), str):
                cleaned = response_payload['captureContext'].strip().strip('"')
                response_payload['captureContext'] = cleaned
            target_origin = None
            if target_origins:
                target_origin = target_origins[0]
            elif isinstance(helper_payload.get('targetOrigins'), list):
                origins_list = helper_payload.get('targetOrigins')
                if origins_list:
                    target_origin = origins_list[0]
            response_payload['targetOrigin'] = target_origin
            response_payload['targetOrigins'] = target_origins
            capture_len = len(response_payload.get('captureContext') or '')
            print(
                "[googlepay_capture_context] ✅ capture-context success via helper "
                f"(origin={target_origin}, len={capture_len})"
            )
            print(
                "[googlepay_capture_context] 🔙 Response payload (excluding captureContext): "
                f"{json.dumps({k: v for k, v in response_payload.items() if k != 'captureContext'}, default=str)}"
            )
            return jsonify(response_payload), 200
        except CyberSourceHelperError as helper_err:
            print(f"[googlepay_capture_context] Helper error: {helper_err}")
            return jsonify({
                'error': 'capture-context failed',
                'details': helper_err.response or helper_err.args[0],
            }), helper_err.status_code or 500
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
            print(
                "[googlepay_charge] 🔍 Incoming request: "
                f"{json.dumps({k: ('***' if 'token' in k.lower() else v) for k, v in data.items()}, default=str)}"
            )
            amount = float(data.get('amount') or 0)
            currency = (data.get('currency') or 'USD').upper()
            transient_token = data.get('transientToken')
            google_pay_token = data.get('googlePayToken') or data.get('paymentData')
            client_billing_info = data.get('billingInfo') or {}

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
            transient_token = transient_token or google_pay_token

            # Create a payment record (pending) - will be updated after processor capture
            user_id = getattr(request, 'user_id', None)
            payment_id = str(uuid.uuid4())

            user_data = {}
            billing_info = {}
            if user_id:
                try:
                    user_ref = self.db.reference(f'registeredUser/{user_id}')
                    user_data = user_ref.get() or {}
                    billing_info = self._build_billing_info(user_data)
                except Exception as err:
                    print(f"[googlepay_charge] ⚠️ Unable to load user profile for billing info: {err}")
            billing_info = self._merge_billing_sources(billing_info, client_billing_info)
            if not billing_info:
                billing_info = self._fallback_billing_from_user(user_data)
            print(f"[googlepay_charge] billing_info resolved: {billing_info}")

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
                helper_client = current_app.config.get('cybersource_helper')
                if not helper_client:
                    return jsonify({'error': 'CyberSource helper not configured'}), 503

                reference_code = payment_id[:27]  # keep within sample limits

                if not transient_token:
                    return jsonify({'error': 'Provide transientToken obtained via capture-context'}), 400

                helper_payload = {
                    'transientToken': transient_token,
                    'amount': amount,
                    'currency': currency,
                    'referenceCode': reference_code,
                }
                if billing_info:
                    helper_payload['billingInfo'] = billing_info
                print(
                    "[googlepay_charge] ⏩ Forwarding to helper: "
                    f"{json.dumps({**helper_payload, 'transientToken': '***'}, default=str)}"
                )

                try:
                    resp = helper_client.charge_googlepay_token(helper_payload) or {}
                    print(
                        "[googlepay_charge] ✅ Helper response: "
                        f"{json.dumps(resp, default=str)}"
                    )
                except CyberSourceHelperError as helper_err:
                    error_payload = helper_err.response or helper_err.args[0]
                    self.db.reference(f'payments/{payment_id}').update({
                        'status': 'failed',
                        'provider_error': error_payload,
                        'updated_at': datetime.datetime.now(datetime.timezone.utc).isoformat(),
                    })
                    return jsonify({
                        'success': False,
                        'payment_id': payment_id,
                        'error': error_payload,
                    }), helper_err.status_code or 500

                status = (resp.get('status') or '').upper()
                now_iso = datetime.datetime.now(datetime.timezone.utc).isoformat()

                # Compute credit days (same heuristic as other flows)
                daily_rate = float(getattr(self.config, 'DAILY_RATE', 5.0))
                credit_days = max(1, int(amount / daily_rate)) if daily_rate > 0 else int(amount)

                # Update user credit
                try:
                    registered_user_ref = self.db.reference(f'registeredUser/{user_id}')
                    legacy_user_ref = self.db.reference(f'users/{user_id}')
                    user_data = registered_user_ref.get() or {}
                    current_credit = int(float(user_data.get('credit_balance', 0) or 0))

                    # Monthly spend tracking
                    month_key = datetime.datetime.now(datetime.timezone.utc).strftime('%Y-%m')
                    monthly = user_data.get('monthly_paid', {}) or {}
                    monthly[month_key] = float(monthly.get(month_key, 0) or 0) + float(amount)

                    new_credit = current_credit + credit_days
                    registered_user_ref.update({
                        'credit_balance': int(new_credit),
                        'total_payments': float(user_data.get('total_payments', 0) or 0) + float(amount),
                        'monthly_paid': monthly,
                        'last_payment_date': now_iso,
                        'updated_at': now_iso,
                    })
                    try:
                        legacy_user_ref.update({
                            'credit_balance': int(new_credit),
                            'total_payments': float(user_data.get('total_payments', 0) or 0) + float(amount),
                            'monthly_paid': monthly,
                            'last_payment_date': now_iso,
                            'updated_at': now_iso,
                        })
                    except Exception as legacy_err:
                        print(f"[googlepay_charge] ⚠️ Legacy users/ path update failed: {legacy_err}")
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

    def _build_billing_info(self, user_data):
        """Prepare billTo block for CyberSource using stored profile/billing details."""
        if not user_data:
            return {}

        billing = (user_data.get('billing_details') or {}).copy()
        name = (user_data.get('name') or '').strip()
        first_name = (
            billing.get('firstName')
            or (name.split(' ', 1)[0] if name else user_data.get('firstName'))
            or 'Customer'
        )
        last_name = (
            billing.get('lastName')
            or (name.split(' ', 1)[1] if ' ' in name else user_data.get('lastName'))
            or 'User'
        )
        locality = (
            billing.get('city')
            or billing.get('locality')
            or user_data.get('city')
            or 'Nairobi'
        )
        address1 = billing.get('address') or billing.get('address1') or user_data.get('address') or 'Unknown'
        country = (billing.get('country') or 'KE').upper()
        postal_code = billing.get('postalCode') or '00100'
        email = billing.get('email') or user_data.get('email')
        phone = billing.get('phone') or user_data.get('phone')

        bill_to = {
            'firstName': first_name,
            'lastName': last_name,
            'email': email or 'support@kilekitabu.com',
            'address1': address1,
            'locality': locality,
            'postalCode': postal_code,
            'country': country,
        }
        if phone:
            bill_to['phoneNumber'] = phone
        administrative_area = billing.get('administrativeArea') or billing.get('state') or user_data.get('state') or ''
        if administrative_area:
            bill_to['administrativeArea'] = administrative_area
        return bill_to

    def _merge_billing_sources(self, primary, fallback):
        result = dict(primary or {})
        for key, value in (fallback or {}).items():
            if value and not result.get(key):
                result[key] = value
        return result

    def _fallback_billing_from_user(self, user_data):
        if not user_data:
            return {
                'firstName': 'Google',
                'lastName': 'Pay',
                'email': 'support@kilekitabu.com',
                'address1': 'Unknown',
                'locality': 'Nairobi',
                'postalCode': '00100',
                'country': 'KE',
            }
        name = (user_data.get('name') or '').strip()
        parts = name.split(' ', 1)
        first = parts[0] if parts else (user_data.get('firstName') or 'Customer')
        last = parts[1] if len(parts) > 1 else (user_data.get('lastName') or 'User')
        return {
            'firstName': first or 'Customer',
            'lastName': last or 'User',
            'email': user_data.get('email') or 'support@kilekitabu.com',
            'address1': user_data.get('address') or 'Unknown',
            'locality': user_data.get('city') or 'Nairobi',
            'postalCode': user_data.get('postalCode') or '00100',
            'country': (user_data.get('country') or 'KE').upper(),
            'phoneNumber': user_data.get('phone'),
        }


