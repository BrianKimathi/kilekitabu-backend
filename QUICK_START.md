# Quick Start Guide - Pesapal Integration

## 🚀 Get Started in 5 Minutes

### 1. Install Dependencies
```bash
cd backend
pip install -r requirements.txt
```

### 2. Run Setup
```bash
python setup.py
```

### 3. Configure Pesapal Credentials
Edit the `.env` file and update:
```env
PESAPAL_CONSUMER_KEY=your_actual_consumer_key
PESAPAL_CONSUMER_SECRET=your_actual_consumer_secret
BASE_URL=http://localhost:5000
```

### 4. Test the Integration
```bash
python test_pesapal_integration.py
```

### 5. Start the Server
```bash
python run.py
```

## 📋 What's Included

### Backend Files
- ✅ `pesapal_integration_v2.py` - Improved Pesapal API integration
- ✅ `payment_api.py` - Complete payment API endpoints
- ✅ `config.py` - Configuration management
- ✅ `app.py` - Main Flask application
- ✅ `requirements.txt` - Python dependencies

### Features
- ✅ M-Pesa mobile money payments
- ✅ Credit/Debit card payments (Visa, MasterCard)
- ✅ Recurring subscription payments
- ✅ IPN (Instant Payment Notification) handling
- ✅ Payment status tracking
- ✅ Refund processing
- ✅ Order cancellation

## 🔧 Configuration

### Environment Variables
```env
# Required
PESAPAL_CONSUMER_KEY=your_key_here
PESAPAL_CONSUMER_SECRET=your_secret_here
BASE_URL=http://localhost:5000

# Optional
PESAPAL_ENVIRONMENT=sandbox  # or production
FRONTEND_URL=http://localhost:3000
FLASK_DEBUG=True
```

### API Endpoints
| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/payment/create` | POST | Create payment request |
| `/api/payment/status/<id>` | GET | Check payment status |
| `/api/payment/callback` | GET | Handle payment callback |
| `/api/payment/ipn` | POST | Handle IPN notifications |
| `/api/payment/cancel` | GET | Cancel payment |
| `/api/payment/refund` | POST | Request refund |

## 🧪 Testing

### Test Payment Creation
```bash
curl -X POST http://localhost:5000/api/payment/create \
  -H "Content-Type: application/json" \
  -d '{
    "amount": 100.0,
    "credit_days": 30,
    "email": "test@example.com",
    "phone": "+254712345678",
    "first_name": "Test",
    "last_name": "User"
  }'
```

### Test Payment Status
```bash
curl http://localhost:5000/api/payment/status/your_order_tracking_id
```

## 🐛 Troubleshooting

### Common Issues

1. **Import Error**
   ```bash
   python setup.py
   ```

2. **Configuration Error**
   - Check `.env` file exists
   - Verify Pesapal credentials
   - Ensure BASE_URL is set

3. **Payment Creation Fails**
   - Check Pesapal credentials
   - Verify API endpoints
   - Check network connectivity

4. **IPN Notifications Not Received**
   - Verify IPN URL registration
   - Check server accessibility
   - Monitor firewall settings

### Debug Mode
```bash
FLASK_DEBUG=True python run.py
```

## 📱 Frontend Integration

The Flutter payment screen is ready to use:

```dart
Navigator.push(
  context,
  MaterialPageRoute(
    builder: (context) => PaymentScreen(
      amount: 1000.0,
      creditDays: 30,
    ),
  ),
);
```

## 🔒 Security Notes

1. **Never expose credentials** in client-side code
2. **Use HTTPS** in production
3. **Validate all inputs** before processing
4. **Monitor payment logs** for suspicious activity

## 📞 Support

- **Pesapal Documentation**: https://developer.pesapal.com
- **Pesapal Support**: support@pesapal.com
- **Sandbox Testing**: https://cybqa.pesapal.com

## 🎯 Next Steps

1. **Get Pesapal Credentials**
   - Visit: https://cybqa.pesapal.com (sandbox)
   - Register your IPN URL
   - Get consumer key and secret

2. **Test with Sandbox**
   - Use test card numbers
   - Test with small amounts
   - Monitor IPN notifications

3. **Deploy to Production**
   - Update environment to production
   - Use production credentials
   - Enable HTTPS

4. **Monitor Payments**
   - Set up logging
   - Monitor payment status
   - Handle errors gracefully

---

**Ready to start accepting payments! 🎉** 