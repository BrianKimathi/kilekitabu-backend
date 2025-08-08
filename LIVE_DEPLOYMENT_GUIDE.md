# 🚀 Live PesaPal Deployment Guide

## 📋 Prerequisites

1. **PesaPal Live Account**: You need a live PesaPal merchant account
2. **Live Credentials**: Get your live consumer key and secret from PesaPal
3. **Public Domain**: Your backend must be accessible via HTTPS
4. **Firebase Setup**: Ensure Firebase is properly configured

## 🔧 Environment Variables Setup

### Render.com Environment Variables

Set these in your Render.com dashboard:

```bash
# PesaPal Live Credentials
PESAPAL_CONSUMER_KEY=your_live_consumer_key_here
PESAPAL_CONSUMER_SECRET=your_live_consumer_secret_here
PESAPAL_ENVIRONMENT=production

# Firebase Configuration
FIREBASE_CREDENTIALS_PATH=kile-kitabu-firebase-adminsdk-pjk21-d2e073c9ae.json
FIREBASE_DATABASE_URL=https://kile-kitabu-default-rtdb.firebaseio.com

# Application URLs
BASE_URL=https://kilekitabu-backend.onrender.com
FRONTEND_URL=https://kilekitabu.com

# Other Settings
DEBUG=false
DAILY_RATE=10.0
FREE_TRIAL_DAYS=7
```

## 📁 Required Files

Ensure these files are in your backend directory:

1. ✅ `app.py` - Main Flask application
2. ✅ `config.py` - Configuration settings
3. ✅ `pesapal_integration_v2.py` - PesaPal integration
4. ✅ `requirements.txt` - Python dependencies
5. ✅ `render.yaml` - Render.com deployment config
6. ✅ `kile-kitabu-firebase-adminsdk-pjk21-d2e073c9ae.json` - Firebase credentials

## 🚀 Deployment Steps

### 1. Update Configuration

The app is now configured for live environment:
- ✅ PesaPal environment: `production`
- ✅ Base URL: `https://pay.pesapal.com/v3`
- ✅ IPN URL: `https://kilekitabu-backend.onrender.com/api/payment/ipn`

### 2. Deploy to Render.com

```bash
# 1. Commit your changes
git add .
git commit -m "Configure for live PesaPal environment"
git push origin main

# 2. Deploy on Render.com
# - Go to your Render.com dashboard
# - Find your kilekitabu-backend service
# - Click "Manual Deploy"
```

### 3. Verify Deployment

Test these endpoints after deployment:

```bash
# Health check
curl https://kilekitabu-backend.onrender.com/

# Test endpoint
curl https://kilekitabu-backend.onrender.com/test

# IPN endpoint (should return 405 for GET)
curl https://kilekitabu-backend.onrender.com/api/payment/ipn
```

## 🔍 IPN Configuration

### What is IPN?

IPN (Instant Payment Notification) allows PesaPal to notify your server when payment status changes.

### IPN Registration

The app automatically registers the IPN URL on startup:
- **URL**: `https://kilekitabu-backend.onrender.com/api/payment/ipn`
- **Method**: POST
- **Format**: Form data

### IPN Data Format

PesaPal sends these fields:
```json
{
  "OrderTrackingId": "ABC123",
  "PaymentStatus": "COMPLETED",
  "PaymentMethod": "MPESA",
  "Amount": "100.00",
  "MerchantReference": "REF123"
}
```

## 🧪 Testing Live Payments

### 1. Test Payment Flow

1. **Initiate Payment**: POST to `/api/payment/initiate`
2. **Redirect User**: Send user to payment URL
3. **Payment Processing**: User completes payment on PesaPal
4. **IPN Notification**: PesaPal notifies your server
5. **Credit Addition**: Credit is automatically added to user

### 2. Test Endpoints

```bash
# Test payment initiation
curl -X POST https://kilekitabu-backend.onrender.com/api/payment/initiate \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_FIREBASE_TOKEN" \
  -d '{
    "amount": 100,
    "email": "test@example.com",
    "phone": "+254700000000",
    "first_name": "Test",
    "last_name": "User"
  }'
```

## 🔒 Security Considerations

### 1. IPN Security

- ✅ IPN endpoint accepts only POST requests
- ✅ Validates OrderTrackingId
- ✅ Logs all IPN data for debugging
- ✅ Returns proper HTTP status codes

### 2. Payment Validation

- ✅ Verifies payment exists in database
- ✅ Updates payment status securely
- ✅ Adds credit only for completed payments
- ✅ Logs all payment activities

## 📊 Monitoring

### 1. Logs to Monitor

```bash
# Check Render.com logs for:
- "IPN Notification Received"
- "Payment Callback Received"
- "Payment Cancellation Received"
- "Access token obtained"
- "IPN registered successfully"
```

### 2. Common Issues

| Issue | Solution |
|-------|----------|
| 503 errors | Check if service is hibernated |
| IPN not received | Verify IPN URL is accessible |
| Payment not updating | Check Firebase connection |
| Token errors | Verify PesaPal credentials |

## 🆘 Troubleshooting

### 1. IPN Not Working

```bash
# Check if IPN endpoint is accessible
curl -X POST https://kilekitabu-backend.onrender.com/api/payment/ipn \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "OrderTrackingId=TEST123&PaymentStatus=COMPLETED"
```

### 2. Payment Status Issues

```bash
# Check payment status
curl https://kilekitabu-backend.onrender.com/api/payment/status/PAYMENT_ID \
  -H "Authorization: Bearer YOUR_FIREBASE_TOKEN"
```

### 3. PesaPal Integration Issues

```bash
# Check PesaPal credentials
curl -X POST https://pay.pesapal.com/v3/api/Auth/RequestToken \
  -H "Content-Type: application/json" \
  -d '{
    "consumer_key": "YOUR_CONSUMER_KEY",
    "consumer_secret": "YOUR_CONSUMER_SECRET"
  }'
```

## 📞 Support

If you encounter issues:

1. **Check Render.com logs** for error messages
2. **Verify PesaPal credentials** are correct
3. **Test IPN endpoint** manually
4. **Contact PesaPal support** for payment issues
5. **Check Firebase logs** for database issues

## ✅ Deployment Checklist

- [ ] PesaPal live credentials configured
- [ ] Environment variables set in Render.com
- [ ] Firebase credentials uploaded
- [ ] Backend deployed successfully
- [ ] Health check endpoint working
- [ ] IPN endpoint accessible
- [ ] Test payment flow completed
- [ ] Credit system working
- [ ] Logs monitored for errors

## 🎯 Next Steps

1. **Deploy the updated backend**
2. **Test with small payment amounts**
3. **Monitor logs for any issues**
4. **Update Android app if needed**
5. **Go live with real payments**

---

**⚠️ Important**: Always test with small amounts first before processing real payments! 