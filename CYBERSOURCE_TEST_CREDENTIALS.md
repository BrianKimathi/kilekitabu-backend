# CyberSource Test Credentials

## Test Environment Configuration

Add these to your `.env` file for **TEST/SANDBOX** environment:

```env
# CyberSource Configuration (TEST/SANDBOX)
CYBERSOURCE_ENV=sandbox
CYBERSOURCE_MERCHANT_ID=tiankainvestmentsltd_qr
CYBERSOURCE_API_KEY_ID=b83c5e8e-cf46-43cd-908e-22e485e75069
CYBERSOURCE_SECRET_KEY=b6RWWLoVb7J2eoVkXqwE+euHKE/amaZvcp6L93LR2kg=
CYBERSOURCE_WEBHOOK_SECRET=  # Optional for test, can be left empty
```

## Test Card Numbers

Use these test card numbers in the CyberSource sandbox:

- **Visa**: `4111111111111111`
- **Mastercard**: `5555555555554444`
- **Amex**: `378282246310005`
- **Expiry**: Any future date (e.g., `12/2031`)
- **CVV**: Any 3-4 digits (e.g., `123`)

## Verification

After adding these credentials to your `.env` file:

1. Restart your backend server
2. Check the logs for: `✅ CyberSource client initialized successfully`
3. Test a card payment in the app

## Next Steps

When ready for production:
1. Switch to production server in CyberSource Business Center
2. Create a new REST - Shared Secret key in production
3. Update `.env` with production credentials:
   - `CYBERSOURCE_ENV=production`
   - `CYBERSOURCE_MERCHANT_ID=<production-merchant-id>`
   - `CYBERSOURCE_API_KEY_ID=<production-key-id>`
   - `CYBERSOURCE_SECRET_KEY=<production-secret-key>`

