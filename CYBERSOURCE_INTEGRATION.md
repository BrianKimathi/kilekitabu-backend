# CyberSource Payment Integration

## Overview

This document describes the CyberSource payment gateway integration for card payments in KileKitabu backend and Android app.

## Architecture

### Components

1. **Backend Service** (`services/cybersource_integration.py`)
   - CyberSource REST API client
   - HTTP signature authentication (HmacSHA256)
   - Payment processing
   - Webhook signature validation

2. **Backend Controller** (`controllers/cybersource_controller.py`)
   - Payment initiation endpoint
   - Webhook notification handler
   - Firebase integration for credit management

3. **Backend Routes** (`routes/cybersource.py`)
   - `POST /api/cybersource/initiate` - Process card payment (authenticated)
   - `POST /api/cybersource/webhook` - Receive payment notifications

4. **Android App**
   - `CardPaymentDialogFragment` - Card info collection UI
   - `ApiService` - Retrofit interface for API calls
   - Payment models for request/response

## Configuration

### Backend Environment Variables

Add these to your `.env` file:

```env
# CyberSource Configuration
CYBERSOURCE_ENV=sandbox                    # sandbox | production
CYBERSOURCE_MERCHANT_ID=your_merchant_id
CYBERSOURCE_API_KEY_ID=your_api_key_id
CYBERSOURCE_SECRET_KEY=your_base64_secret_key
CYBERSOURCE_WEBHOOK_SECRET=your_webhook_secret_key
```

### How to Get Credentials

1. **Sign up for CyberSource Account**
   - Sandbox: https://developer.cybersource.com/hello-world/sandbox.html
   - Production: Contact CyberSource sales

2. **Create REST API Keys**
   - Log in to Business Center
   - Navigate to Payment Configuration → Key Management
   - Create new REST API Shared Secret Key
   - Save the merchant ID, key ID, and secret key (base64 encoded)

3. **Create Webhook Secret Key**
   - Navigate to Webhook Configuration
   - Create Digital Signature Key
   - Use the POST `/reporting/v3/key-management/keys` endpoint
   - Save the returned `key` value for webhook validation

## API Endpoints

### 1. Initiate Card Payment

**Endpoint:** `POST /api/cybersource/initiate`

**Headers:**
```
Authorization: Bearer <firebase_id_token>
Content-Type: application/json
```

**Request Body:**
```json
{
  "amount": 100.0,
  "currency": "KES",
  "card": {
    "number": "4111111111111111",
    "expirationMonth": "12",
    "expirationYear": "2031",
    "cvv": "123"
  },
  "billingInfo": {
    "firstName": "John",
    "lastName": "Doe",
    "address1": "123 Main St",
    "locality": "Nairobi",
    "administrativeArea": "Nairobi",
    "postalCode": "00100",
    "country": "KE",
    "email": "john@example.com",
    "phoneNumber": "254712345678"
  }
}
```

**Success Response (200):**
```json
{
  "success": true,
  "payment_id": "CS_abc123_def456",
  "transaction_id": "6789012345678901234",
  "status": "AUTHORIZED",
  "amount": 100.0,
  "currency": "KES"
}
```

**Error Response (400/500):**
```json
{
  "success": false,
  "error": "Payment declined",
  "payment_id": "CS_abc123_def456"
}
```

### 2. Webhook Notification

**Endpoint:** `POST /api/cybersource/webhook`

**Headers:**
```
V-C-Signature: t=<timestamp>;keyId=<key_id>;sig=<signature>
V-C-Event-Type: payByLink.merchant.payment
V-C-Organization-Id: your_org_id
V-C-Product-Name: payByLink
V-C-Webhook-Id: webhook_subscription_id
```

**Webhook Body:**
```json
{
  "notificationId": "uuid",
  "eventType": "payByLink.merchant.payment",
  "eventDate": "2025-11-07T12:00:00Z",
  "webhookId": "webhook_id",
  "payloads": [
    {
      "data": {
        "transactionId": "6789012345678901234",
        "amount": 100.0,
        "currency": "KES",
        "status": "AUTHORIZED",
        "email": "customer@example.com",
        "referenceCode": "CS_abc123_def456"
      },
      "organizationId": "your_org_id"
    }
  ]
}
```

## Webhook Events

### Supported Event Types

1. **`payByLink.merchant.payment`**
   - Triggered when customer completes Pay by Link payment
   - Used for Pay by Link integration (future)

2. **`payments.capture.status.accepted`**
   - Payment capture request accepted
   - Used for direct API payments (current implementation)

3. **`payments.capture.status.updated`**
   - Payment capture status updated
   - Used for monitoring payment status changes

## Security

### 1. HTTP Signature Authentication (API Requests)

CyberSource uses HTTP signature authentication with HmacSHA256:

```
Signature: keyid="<api_key_id>", 
           algorithm="HmacSHA256", 
           headers="host date (request-target) digest v-c-merchant-id", 
           signature="<base64_signature>"
```

**Signature String Format:**
```
host: apitest.cybersource.com
date: Thu, 07 Nov 2025 12:00:00 GMT
(request-target): post /pts/v2/payments
digest: SHA-256=<base64_digest_of_body>
v-c-merchant-id: your_merchant_id
```

### 2. Webhook Signature Validation

Webhooks are signed with HMAC-SHA256:

```
signature = Base64(HMAC-SHA256(webhook_secret, timestamp + "." + payload))
```

**Validation Steps:**
1. Extract timestamp, keyId, and signature from `V-C-Signature` header
2. Check timestamp is within 60-minute tolerance
3. Reconstruct signature using webhook secret
4. Compare with received signature using constant-time comparison

## Payment Flow

### Direct API Flow (Current Implementation)

```
1. User enters card details in Android app
   ↓
2. App sends payment request to backend with Firebase auth token
   ↓
3. Backend validates auth and payment data
   ↓
4. Backend calls CyberSource API with HTTP signature auth
   ↓
5. CyberSource processes payment and returns response
   ↓
6. Backend adds credits to user account in Firebase
   ↓
7. Backend returns success/failure to app
   ↓
8. App shows result and refreshes credit balance
```

### Webhook Flow (For Pay by Link)

```
1. Customer receives Pay by Link URL
   ↓
2. Customer completes payment on CyberSource hosted page
   ↓
3. CyberSource sends webhook notification to backend
   ↓
4. Backend validates webhook signature
   ↓
5. Backend processes payment data
   ↓
6. Backend adds credits to user account
   ↓
7. App's Firebase listener detects credit update
   ↓
8. App refreshes subscription status automatically
```

## Testing

### Test Card Numbers

CyberSource provides test cards for sandbox:

| Card Number         | Type       | Result    |
|---------------------|------------|-----------|
| 4111111111111111    | Visa       | Approved  |
| 5555555555554444    | Mastercard | Approved  |
| 378282246310005     | Amex       | Approved  |
| 4000000000000002    | Visa       | Declined  |

### Test Webhook

To test webhooks manually:

```bash
curl -X POST https://your-ngrok-url.ngrok-free.app/api/cybersource/webhook \
  -H "Content-Type: application/json" \
  -H "V-C-Signature: t=1699368000000;keyId=test-key;sig=test-signature" \
  -H "V-C-Event-Type: payByLink.merchant.payment" \
  -H "V-C-Organization-Id: test-org" \
  -d '{
    "notificationId": "test-123",
    "eventType": "payByLink.merchant.payment",
    "payloads": [{
      "data": {
        "transactionId": "test-txn-123",
        "amount": 100.0,
        "currency": "KES",
        "status": "AUTHORIZED",
        "referenceCode": "CS_test_123"
      }
    }]
  }'
```

## Firebase Database Structure

### Payment Records

```
payments/
  {user_id}/
    {payment_id}/
      payment_id: "CS_abc123_def456"
      user_id: "firebase_user_id"
      amount: 100.0
      currency: "KES"
      payment_method: "CARD"
      provider: "CYBERSOURCE"
      status: "COMPLETED"
      transaction_id: "6789012345678901234"
      created_at: "2025-11-07T12:00:00Z"
      updated_at: "2025-11-07T12:00:05Z"
      billing_info:
        name: "John Doe"
        email: "john@example.com"
        phone: "254712345678"
      cybersource_response: {...}
```

### User Credit Update

```
registeredUser/
  {user_id}/
    credit_balance: 100.0
    total_payments: 250.0
    last_payment_date: "2025-11-07T12:00:05Z"
    updated_at: "2025-11-07T12:00:05Z"
```

## Error Handling

### Common Errors

1. **Missing Credentials**
   ```
   Error: CyberSource not configured; missing: CYBERSOURCE_MERCHANT_ID
   ```
   Solution: Add all required environment variables

2. **Authentication Failed**
   ```
   Error: 401 Unauthorized
   ```
   Solution: Verify API key ID and secret key are correct

3. **Invalid Signature**
   ```
   Error: Invalid signature
   ```
   Solution: Check secret key encoding and signature generation

4. **Card Declined**
   ```
   Error: Payment declined
   ```
   Solution: Use valid test card or check with card issuer

## Logging

All CyberSource operations are logged with detailed information:

```python
[CyberSourceClient] Initialized
[CyberSourceClient] Merchant ID: testmerchant
[CyberSourceClient] [Payment] Creating payment
[CyberSourceClient] [Payment] Amount: 100.0 KES
[CyberSourceClient] [Payment] ✅ Payment successful
[CyberSourceClient] [Payment]   Transaction ID: 6789012345678901234

[cybersource_webhook] ========== Webhook Received ==========
[cybersource_webhook] Event Type: payByLink.merchant.payment
[cybersource_webhook] ✅ Matched user: abc123
[cybersource_webhook] ✅ Added 100.0 credits. New balance: 150.0
```

## Production Checklist

Before going to production:

- [ ] Obtain production CyberSource account
- [ ] Create production REST API keys
- [ ] Create production webhook secret key
- [ ] Update `CYBERSOURCE_ENV=production` in `.env`
- [ ] Update API base URL to `https://api.cybersource.com`
- [ ] Configure webhook subscription in Business Center
- [ ] Set webhook URL to your production endpoint
- [ ] Test with real cards (small amounts first)
- [ ] Monitor logs for any errors
- [ ] Set up alerts for failed payments
- [ ] Implement retry mechanism for failed webhooks
- [ ] Add PCI compliance measures for production

## Support

- **CyberSource Developer Center**: https://developer.cybersource.com
- **API Reference**: https://developer.cybersource.com/api-reference-assets
- **Support**: https://www.cybersource.com/support
- **Webhook Guide**: See `kilekitabu-backend/webhooks.txt`

## References

- `kilekitabu-backend/services/cybersource_integration.py` - API client
- `kilekitabu-backend/controllers/cybersource_controller.py` - Payment logic
- `kilekitabu-backend/routes/cybersource.py` - API routes
- `app/src/main/java/com/jeff/kilekitabu/ui/CardPaymentDialogFragment.kt` - Android UI
- `app/src/main/java/com/jeff/kilekitabu/api/ApiService.kt` - API interface


