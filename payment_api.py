from flask import Flask, request, jsonify
from pesapal_integration_v2 import PesaPalIntegration
import uuid
import datetime
from config import Config

app = Flask(__name__)
pesapal = PesaPalIntegration()

@app.route('/api/payment/create', methods=['POST'])
def create_payment():
    """Create a new payment request"""
    try:
        data = request.get_json()
        
        # Validate required fields
        required_fields = ['amount', 'credit_days', 'email', 'phone', 'first_name', 'last_name']
        for field in required_fields:
            if not data.get(field):
                return jsonify({'error': f'Missing required field: {field}'}), 400
        
        # Generate unique payment ID
        payment_id = f"KK_{uuid.uuid4().hex[:8].upper()}"
        
        # Prepare payment data
        payment_data = {
            'payment_id': payment_id,
            'amount': float(data['amount']),
            'credit_days': data['credit_days'],
            'email': data['email'],
            'phone': data['phone'],
            'first_name': data['first_name'],
            'last_name': data['last_name'],
            'address': data.get('address', ''),
            'city': data.get('city', ''),
            'state': data.get('state', ''),
            'postal_code': data.get('postal_code', ''),
            'is_subscription': data.get('is_subscription', False)
        }
        
        # Add subscription details if this is a recurring payment
        if payment_data['is_subscription']:
            payment_data.update({
                'subscription_start_date': data.get('subscription_start_date', ''),
                'subscription_end_date': data.get('subscription_end_date', ''),
                'subscription_frequency': data.get('subscription_frequency', 'MONTHLY')
            })
        
        # Create payment request with Pesapal
        result = pesapal.create_payment_request(payment_data)
        
        if not result:
            return jsonify({'error': 'Failed to create payment request'}), 500
        
        # Store payment information in database (you should implement this)
        # payment_record = {
        #     'payment_id': payment_id,
        #     'amount': payment_data['amount'],
        #     'credit_days': payment_data['credit_days'],
        #     'user_email': payment_data['email'],
        #     'user_phone': payment_data['phone'],
        #     'order_tracking_id': result['order_tracking_id'],
        #     'status': 'pending',
        #     'created_at': datetime.datetime.now()
        # }
        # db.payments.insert_one(payment_record)
        
        return jsonify({
            'success': True,
            'payment_id': payment_id,
            'payment_url': result['payment_url'],
            'order_tracking_id': result['order_tracking_id'],
            'message': 'Payment request created successfully'
        })
        
    except Exception as e:
        print(f"Error creating payment: {e}")
        return jsonify({'error': 'Internal server error'}), 500

@app.route('/api/payment/status/<order_tracking_id>', methods=['GET'])
def check_payment_status(order_tracking_id):
    """Check payment status"""
    try:
        result = pesapal.check_payment_status(order_tracking_id)
        
        if not result:
            return jsonify({'error': 'Failed to check payment status'}), 500
        
        return jsonify({
            'success': True,
            'status': result['status'],
            'status_code': result['status_code'],
            'amount': result['amount'],
            'currency': result['currency'],
            'payment_method': result['payment_method'],
            'confirmation_code': result['confirmation_code'],
            'created_date': result['created_date'],
            'payment_account': result['payment_account']
        })
        
    except Exception as e:
        print(f"Error checking payment status: {e}")
        return jsonify({'error': 'Internal server error'}), 500

@app.route('/api/payment/callback', methods=['GET'])
def payment_callback():
    """Handle payment callback from Pesapal"""
    try:
        # Get parameters from callback URL
        order_tracking_id = request.args.get('OrderTrackingId')
        order_merchant_reference = request.args.get('OrderMerchantReference')
        order_notification_type = request.args.get('OrderNotificationType')
        
        if not order_tracking_id:
            return jsonify({'error': 'Missing OrderTrackingId'}), 400
        
        # Check payment status
        result = pesapal.check_payment_status(order_tracking_id)
        
        if not result:
            return jsonify({'error': 'Failed to check payment status'}), 500
        
        # Update payment record in database (you should implement this)
        # payment_update = {
        #     'status': result['status'],
        #     'status_code': result['status_code'],
        #     'payment_method': result['payment_method'],
        #     'confirmation_code': result['confirmation_code'],
        #     'updated_at': datetime.datetime.now()
        # }
        # db.payments.update_one(
        #     {'order_tracking_id': order_tracking_id},
        #     {'$set': payment_update}
        # )
        
        # Redirect user based on payment status
        if result['status'] == 'COMPLETED':
            # Redirect to success page
            return jsonify({
                'success': True,
                'status': 'completed',
                'message': 'Payment completed successfully',
                'redirect_url': f"{Config.FRONTEND_URL}/payment/success?order_id={order_tracking_id}"
            })
        elif result['status'] == 'FAILED':
            # Redirect to failure page
            return jsonify({
                'success': False,
                'status': 'failed',
                'message': 'Payment failed',
                'redirect_url': f"{Config.FRONTEND_URL}/payment/failed?order_id={order_tracking_id}"
            })
        else:
            # Redirect to pending page
            return jsonify({
                'success': True,
                'status': 'pending',
                'message': 'Payment is being processed',
                'redirect_url': f"{Config.FRONTEND_URL}/payment/pending?order_id={order_tracking_id}"
            })
        
    except Exception as e:
        print(f"Error handling payment callback: {e}")
        return jsonify({'error': 'Internal server error'}), 500

@app.route('/api/payment/ipn', methods=['POST'])
def payment_ipn():
    """Handle IPN (Instant Payment Notification) from Pesapal"""
    try:
        # Get IPN data
        ipn_data = request.get_json() or request.form.to_dict()
        
        # Process IPN data
        processed_data = pesapal.get_ipn_data(ipn_data)
        
        if not processed_data:
            return jsonify({'error': 'Invalid IPN data'}), 400
        
        # Check payment status
        result = pesapal.check_payment_status(processed_data['order_tracking_id'])
        
        if not result:
            return jsonify({'error': 'Failed to check payment status'}), 500
        
        # Update payment record in database (you should implement this)
        # payment_update = {
        #     'status': result['status'],
        #     'status_code': result['status_code'],
        #     'payment_method': result['payment_method'],
        #     'confirmation_code': result['confirmation_code'],
        #     'updated_at': datetime.datetime.now()
        # }
        # db.payments.update_one(
        #     {'order_tracking_id': processed_data['order_tracking_id']},
        #     {'$set': payment_update}
        # )
        
        # Handle recurring payment if applicable
        if processed_data['is_recurring'] and result.get('subscription_transaction_info'):
            subscription_info = result['subscription_transaction_info']
            # Process recurring payment (you should implement this)
            # process_recurring_payment(subscription_info)
        
        # Respond to Pesapal with success
        response_data = {
            'orderNotificationType': processed_data['notification_type'],
            'orderTrackingId': processed_data['order_tracking_id'],
            'orderMerchantReference': processed_data['payment_id'],
            'status': 200
        }
        
        return jsonify(response_data)
        
    except Exception as e:
        print(f"Error handling IPN: {e}")
        # Respond to Pesapal with error
        response_data = {
            'orderNotificationType': ipn_data.get('OrderNotificationType', 'IPNCHANGE'),
            'orderTrackingId': ipn_data.get('OrderTrackingId', ''),
            'orderMerchantReference': ipn_data.get('OrderMerchantReference', ''),
            'status': 500
        }
        return jsonify(response_data), 500

@app.route('/api/payment/cancel', methods=['GET'])
def payment_cancel():
    """Handle payment cancellation"""
    try:
        order_tracking_id = request.args.get('OrderTrackingId')
        
        if order_tracking_id:
            # Cancel the order
            result = pesapal.cancel_order(order_tracking_id)
            
            if result and result['status'] == '200':
                return jsonify({
                    'success': True,
                    'message': 'Payment cancelled successfully',
                    'redirect_url': f"{Config.FRONTEND_URL}/payment/cancelled?order_id={order_tracking_id}"
                })
        
        return jsonify({
            'success': True,
            'message': 'Payment cancelled',
            'redirect_url': f"{Config.FRONTEND_URL}/payment/cancelled"
        })
        
    except Exception as e:
        print(f"Error handling payment cancellation: {e}")
        return jsonify({'error': 'Internal server error'}), 500

@app.route('/api/payment/refund', methods=['POST'])
def request_refund():
    """Request a refund"""
    try:
        data = request.get_json()
        
        # Validate required fields
        required_fields = ['confirmation_code', 'amount', 'username', 'remarks']
        for field in required_fields:
            if not data.get(field):
                return jsonify({'error': f'Missing required field: {field}'}), 400
        
        # Request refund
        result = pesapal.request_refund(
            data['confirmation_code'],
            data['amount'],
            data['username'],
            data['remarks']
        )
        
        if not result:
            return jsonify({'error': 'Failed to request refund'}), 500
        
        return jsonify({
            'success': True,
            'status': result['status'],
            'message': result['message']
        })
        
    except Exception as e:
        print(f"Error requesting refund: {e}")
        return jsonify({'error': 'Internal server error'}), 500

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000) 