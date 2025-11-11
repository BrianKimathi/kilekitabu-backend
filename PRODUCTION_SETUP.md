# Production Setup Guide

## M-Pesa Production Credentials

You have received production STK Push credentials from Safaricom:

- **Business Short Code:** `3576603`
- **Passkey:** `bcfeb194a2df8ca55f17c2816a55234c837516ce016dcade10621ce0ffc9e84d`

### Next Steps for M-Pesa Production

1. **Get Consumer Key and Consumer Secret**
   - Log into your Safaricom Daraja portal (production)
   - Navigate to "My Apps" → Select your production app
   - Copy the Consumer Key and Consumer Secret
   - These are different from your sandbox credentials

2. **Update Environment Variables**
   ```env
   MPESA_ENV=production
   MPESA_CONSUMER_KEY=your-production-consumer-key
   MPESA_CONSUMER_SECRET=your-production-consumer-secret
   MPESA_SHORT_CODE=3576603
   MPESA_PASSKEY=bcfeb194a2df8ca55f17c2816a55234c837516ce016dcade10621ce0ffc9e84d
   ```

3. **Verify Callback URL**
   - Ensure your production callback URL is whitelisted in Safaricom portal
   - Callback URL: `https://kilekitabu-backend.onrender.com/api/mpesa/callback`
   - Contact Safaricom support if callback URL needs to be registered

## CyberSource Production Credentials

You have received production API access approval (CRQ000008538668).

### Next Steps for CyberSource Production

1. **Check Your Email**
   - Look for email regarding CRQ000008538668
   - The email should contain production API URLs for your selected products

2. **Access CyberSource Business Center (Production)**
   - Log into CyberSource Business Center (production environment)
   - Select your company from the dropdown in "MY APPS"
   - You should see your production app

3. **Get Production Credentials**
   - Navigate to **Payment Configuration → Key Management**
   - Create or view REST API Shared Secret Key
   - Copy the following:
     - **Merchant ID** (production)
     - **API Key ID** (production)
     - **Secret Key** (base64 encoded, production)

4. **Set Up Webhook Secret**
   - Navigate to **Webhook Configuration**
   - Create Digital Signature Key for production
   - Use the POST `/reporting/v3/key-management/keys` endpoint
   - Save the returned `key` value for webhook validation

5. **Configure Webhook URL**
   - Set webhook URL: `https://kilekitabu-backend.onrender.com/api/cybersource/webhook`
   - Subscribe to `payByLink.merchant.payment` events
   - Save the webhook secret for validation

6. **Update Environment Variables**
   ```env
   CYBERSOURCE_ENV=production
   CYBERSOURCE_MERCHANT_ID=your-production-merchant-id
   CYBERSOURCE_API_KEY_ID=your-production-api-key-id
   CYBERSOURCE_SECRET_KEY=your-production-base64-secret-key
   CYBERSOURCE_WEBHOOK_SECRET=your-production-webhook-secret-key
   ```

## Production Deployment Checklist

### Before Going Live

- [ ] Update `.env` file with all production credentials
- [ ] Verify M-Pesa Consumer Key and Consumer Secret are production credentials
- [ ] Verify M-Pesa Short Code is `3576603` (production)
- [ ] Verify M-Pesa Passkey is correct
- [ ] Verify CyberSource Merchant ID is production
- [ ] Verify CyberSource API Key ID is production
- [ ] Verify CyberSource Secret Key is production (base64 encoded)
- [ ] Verify CyberSource Webhook Secret is set
- [ ] Test M-Pesa STK Push with a small amount
- [ ] Test CyberSource card payment with a test card
- [ ] Verify webhook callbacks are working
- [ ] Verify callback URLs are whitelisted/registered
- [ ] Set `DEBUG=False` in production
- [ ] Set `ALLOW_UNAUTH_TEST=False` in production
- [ ] Verify `BASE_URL` points to production server
- [ ] Set up monitoring and logging
- [ ] Test error handling and edge cases

### Security Checklist

- [ ] `.env` file is in `.gitignore` (not committed to git)
- [ ] All production credentials are secure
- [ ] `SECRET_KEY` is a strong random string
- [ ] `CRON_SECRET_KEY` is set and different from `SECRET_KEY`
- [ ] Firebase credentials file is secure
- [ ] Webhook signatures are validated
- [ ] API endpoints require authentication
- [ ] HTTPS is enabled on production server
- [ ] CORS is configured correctly
- [ ] Rate limiting is in place (if applicable)

### Testing in Production

1. **Test M-Pesa Payment**
   - Initiate a small payment (e.g., 10 KES)
   - Verify STK push is received on phone
   - Complete payment
   - Verify callback is received
   - Verify credits are added to user account

2. **Test CyberSource Payment**
   - Initiate a small card payment
   - Use a test card (if available) or real card
   - Verify payment is processed
   - Verify webhook is received (if applicable)
   - Verify credits are added to user account

3. **Test Webhooks**
   - Verify M-Pesa callback URL is accessible
   - Verify CyberSource webhook URL is accessible
   - Test signature validation
   - Verify error handling

## Environment Variables Summary

### Required for Production

```env
# Application
BASE_URL=https://kilekitabu-backend.onrender.com
SECRET_KEY=your-strong-secret-key
CRON_SECRET_KEY=your-cron-secret-key
DEBUG=False

# Firebase
FIREBASE_CREDENTIALS_PATH=kile-kitabu-firebase-adminsdk-pjk21-68cbd0c3b4.json
FIREBASE_DATABASE_URL=https://kile-kitabu-default-rtdb.firebaseio.com

# M-Pesa (Production)
MPESA_ENV=production
MPESA_CONSUMER_KEY=your-production-consumer-key
MPESA_CONSUMER_SECRET=your-production-consumer-secret
MPESA_SHORT_CODE=3576603
MPESA_PASSKEY=bcfeb194a2df8ca55f17c2816a55234c837516ce016dcade10621ce0ffc9e84d

# CyberSource (Production)
CYBERSOURCE_ENV=production
CYBERSOURCE_MERCHANT_ID=your-production-merchant-id
CYBERSOURCE_API_KEY_ID=your-production-api-key-id
CYBERSOURCE_SECRET_KEY=your-production-base64-secret-key
CYBERSOURCE_WEBHOOK_SECRET=your-production-webhook-secret-key
```

## Troubleshooting

### M-Pesa Issues

- **STK Push not received**: Check Consumer Key/Secret, verify phone number format
- **Callback not received**: Verify callback URL is whitelisted, check server logs
- **Payment fails**: Check Short Code and Passkey, verify account has sufficient balance

### CyberSource Issues

- **Authentication fails**: Verify Secret Key is base64 encoded correctly
- **Webhook not received**: Verify webhook URL is configured, check signature validation
- **Payment fails**: Check Merchant ID, API Key ID, and Secret Key

### General Issues

- **Server errors**: Check server logs, verify all environment variables are set
- **Database errors**: Verify Firebase credentials and database URL
- **Network errors**: Verify server is accessible, check firewall rules

## Support

- **M-Pesa Support**: Contact Safaricom API Support Team
- **CyberSource Support**: Check Business Center or contact CyberSource support
- **Application Issues**: Check server logs and error messages

## Additional Resources

- [M-Pesa Daraja API Documentation](https://developer.safaricom.co.ke/docs)
- [CyberSource API Documentation](https://developer.cybersource.com/)
- [Firebase Documentation](https://firebase.google.com/docs)

