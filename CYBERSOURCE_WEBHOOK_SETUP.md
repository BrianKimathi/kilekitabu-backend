# CyberSource Webhook Subscription Setup Guide

This guide will help you set up webhook subscriptions in CyberSource Business Center to receive real-time payment notifications.

## Prerequisites

- Access to CyberSource Business Center (test or production)
- Your backend is deployed and accessible (e.g., `https://kilekitabu-backend.onrender.com`)
- Webhook endpoint is ready: `/api/cybersource/webhook`

## Step-by-Step Setup

### 1. Navigate to Webhooks

1. Log in to CyberSource Business Center
2. Go to **Account Management** → **Webhooks** → **Subscriptions**
3. Click **Create Subscription**

### 2. Fill in Subscription Details

#### **Delivery Security**

- **Security Options**: Select **"No Auth"** (for now - you can add signature validation later)
  - Note: Your backend supports signature validation via `CYBERSOURCE_WEBHOOK_SECRET`, but start with "No Auth" for testing

#### **Details**

**Subscription Name** _(Required)_

```
KileKitabu Payment Notifications
```

**Description**

```
Webhook subscription for KileKitabu payment status updates and transaction notifications
```

**Endpoint URL** _(Required)_

```
https://kilekitabu-backend.onrender.com/api/cybersource/webhook
```

**Endpoint Health Check URL** _(Optional but Recommended)_

```
https://kilekitabu-backend.onrender.com/api/health/ping
```

- This allows CyberSource to verify your endpoint is reachable
- Should return HTTP 200 with `{"status": "ok"}`

### 3. Add Products and Events

Click **"Add Products and Events"** and select the following:

#### **Product: Payments**

Select these events:

- ✅ `payments.authorization.status.accepted` - Payment authorization accepted
- ✅ `payments.authorization.status.declined` - Payment authorization declined
- ✅ `payments.capture.status.accepted` - Payment capture accepted
- ✅ `payments.capture.status.declined` - Payment capture declined
- ✅ `payments.credit.status.accepted` - Credit/refund accepted
- ✅ `payments.credit.status.declined` - Credit/refund declined

#### **Product: Pay by Link** (if you use Pay by Link)

Select these events:

- ✅ `payByLink.merchant.payment` - Pay by Link payment completed

### 4. Save Subscription

1. Review all fields
2. Click **"Save"**
3. CyberSource will automatically ping your health check URL to verify the endpoint
4. You should see a success message

## Verification

### Test the Webhook Endpoint

You can manually test your webhook endpoint using curl:

```bash
curl -X POST https://kilekitabu-backend.onrender.com/api/cybersource/webhook \
  -H "Content-Type: application/json" \
  -H "V-C-Event-Type: payments.authorization.status.accepted" \
  -d '{
    "notificationId": "test-123",
    "eventDate": "2025-11-11T12:00:00Z",
    "payloads": [{
      "data": {
        "id": "test-transaction-id",
        "status": "AUTHORIZED",
        "amount": "10.0",
        "currency": "KES"
      }
    }]
  }'
```

Expected response: `{"status": "success"}` with HTTP 200

### Check Backend Logs

After a payment, check your backend logs for:

```
[cybersource_webhook] ========== Webhook Received ==========
[cybersource_webhook] Event Type: payments.authorization.status.accepted
[cybersource_webhook] ✅ Webhook processed successfully
```

## Security (Optional - Recommended for Production)

### Enable Signature Validation

1. In CyberSource Business Center, go to **Key Management**
2. Create a **Digital Signature Key** for webhooks
3. Copy the secret key
4. Add to your `.env` file:
   ```
   CYBERSOURCE_WEBHOOK_SECRET=your-webhook-secret-key-here
   ```
5. Update the webhook subscription to use **"Signature"** security option
6. Your backend will automatically validate all webhook signatures

## Troubleshooting

### Webhook Not Received

1. **Check endpoint URL**: Ensure it's publicly accessible (not localhost)
2. **Check health check URL**: CyberSource pings this first
3. **Check firewall**: Ensure CyberSource IPs are allowed (see CyberSource docs)
4. **Check logs**: Look for webhook requests in your backend logs

### Common Errors

**Error: "Endpoint not reachable"**

- Verify your backend is running and accessible
- Check that the health check URL returns HTTP 200
- Ensure no firewall is blocking CyberSource IPs

**Error: "Invalid signature"**

- Verify `CYBERSOURCE_WEBHOOK_SECRET` matches the key in CyberSource
- Check that signature validation is enabled in the subscription

**Error: "Webhook processed but payment not updated"**

- Check backend logs for error messages
- Verify the payment reference code matches your payment records
- Ensure user matching logic is working correctly

## Webhook Event Details

### Payment Authorization Events

When a payment is authorized or declined, CyberSource sends:

- `payments.authorization.status.accepted` - Payment approved
- `payments.authorization.status.declined` - Payment declined

Your backend will:

1. Receive the webhook
2. Extract transaction ID and status
3. Update payment record in Firebase
4. Add credits to user account (if authorized)

### Payment Capture Events

When a payment is captured:

- `payments.capture.status.accepted` - Capture successful
- `payments.capture.status.declined` - Capture failed

## Production Checklist

- [ ] Webhook subscription created in CyberSource
- [ ] Endpoint URL is publicly accessible
- [ ] Health check URL returns HTTP 200
- [ ] Events selected: authorization, capture, credit
- [ ] Signature validation enabled (production)
- [ ] `CYBERSOURCE_WEBHOOK_SECRET` set in environment
- [ ] Test webhook received and processed
- [ ] Backend logs show successful webhook processing

## Support

If you encounter issues:

1. Check CyberSource Business Center → Webhooks → Subscriptions for delivery status
2. Review backend logs for webhook processing errors
3. Test the endpoint manually using curl
4. Verify all environment variables are set correctly
