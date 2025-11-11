# M-Pesa Production Credentials & Configuration

## ✅ Credentials Received

### STK Push Credentials
- **Business Short Code**: `3576603`
- **Passkey**: `bcfeb194a2df8ca55f17c2816a55234c837516ce016dcade10621ce0ffc9e84d`

### Production API URLs
The following URLs are configured and ready for production:

#### STK Push (M-PESA EXPRESS)
- **OAuth2Token**: `https://api.safaricom.co.ke/oauth/v1/generate`
- **STKPush**: `https://api.safaricom.co.ke/mpesa/stkpush/v1/processrequest`
- **STKPushQuery**: `https://api.safaricom.co.ke/mpesa/stkpushquery/v1/query`

## ✅ Code Configuration Status

### Already Configured
1. **M-Pesa Integration Service** (`services/mpesa_integration.py`)
   - ✅ Automatically uses `https://api.safaricom.co.ke` when `MPESA_ENV=production`
   - ✅ Uses `https://sandbox.safaricom.co.ke` when `MPESA_ENV=sandbox`

2. **Config File** (`config.py`)
   - ✅ `MPESA_SHORT_CODE=3576603` (production)
   - ✅ `MPESA_PASSKEY=bcfeb194a2df8ca55f17c2816a55234c837516ce016dcade10621ce0ffc9e84d` (production)
   - ✅ `MPESA_ENV=production` (when set in .env)

## ⚠️ Still Required

You need to obtain and add to your `.env` file:

1. **Consumer Key** (Production)
   - Get from: Safaricom Daraja Portal → My Apps → Production App
   - Add to `.env`: `MPESA_CONSUMER_KEY=your-production-consumer-key-here`

2. **Consumer Secret** (Production)
   - Get from: Safaricom Daraja Portal → My Apps → Production App
   - Add to `.env`: `MPESA_CONSUMER_SECRET=your-production-consumer-secret-here`

## 📝 Complete .env Configuration

Add these lines to your `.env` file:

```env
# M-Pesa Daraja Configuration (PRODUCTION)
MPESA_ENV=production
MPESA_CONSUMER_KEY=your-production-consumer-key-here
MPESA_CONSUMER_SECRET=your-production-consumer-secret-here
MPESA_SHORT_CODE=3576603
MPESA_PASSKEY=bcfeb194a2df8ca55f17c2816a55234c837516ce016dcade10621ce0ffc9e84d
```

## 🔍 How to Get Consumer Key & Secret

1. Log into [Safaricom Daraja Portal](https://developer.safaricom.co.ke/)
2. Navigate to **"My Apps"**
3. Select your **Production App** (not sandbox)
4. Copy:
   - **Consumer Key** → `MPESA_CONSUMER_KEY`
   - **Consumer Secret** → `MPESA_CONSUMER_SECRET`

## ✅ Verification Checklist

- [x] Business Short Code: `3576603` (configured)
- [x] Passkey: `bcfeb194a2df8ca55f17c2816a55234c837516ce016dcade10621ce0ffc9e84d` (configured)
- [x] Production API URLs: Correctly configured in code
- [ ] Consumer Key: **Need to add to .env**
- [ ] Consumer Secret: **Need to add to .env**
- [ ] `MPESA_ENV=production` in `.env` file

## 🚀 After Adding Credentials

1. Update your `.env` file with Consumer Key and Secret
2. Set `MPESA_ENV=production` in `.env`
3. Restart your backend server
4. Check logs for: `✅ M-Pesa client initialized successfully`
5. Test with a small payment to verify everything works

## 📞 Support

If you encounter issues:
- Check backend logs for M-Pesa initialization messages
- Verify all credentials are correct (no extra spaces)
- Ensure callback URL is whitelisted in Safaricom portal
- Test with a small amount first (e.g., 10 KES)

