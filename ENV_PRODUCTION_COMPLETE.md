# Complete Production .env File

This is your complete production-ready `.env` file with all M-Pesa credentials configured.

## ⚠️ SECURITY WARNING
**DO NOT commit this file to git!** It contains sensitive credentials.

## Complete .env Configuration

```env
# ============================================
# Application Configuration
# ============================================
DEBUG=False
BASE_URL=https://kilekitabu-backend.onrender.com
SECRET_KEY=your-secret-key-here-change-this-to-a-random-string
CRON_SECRET_KEY=your-cron-secret-key-here-change-this-to-a-random-string
LOG_LEVEL=INFO

# ============================================
# Test Flags
# ============================================
ALLOW_UNAUTH_TEST=False
FORCE_TRIAL_END=False

# ============================================
# User Reset Configuration
# ============================================
# RESET_USERS_ON_LOGIN: If True, all users get a fresh 14-day trial on login
# - New users: Automatically get fresh trial
# - Existing users: Reset on next login to get fresh trial
# Set to False to disable automatic reset (users keep their current trial/credit status)
RESET_USERS_ON_LOGIN=True

# ============================================
# Firebase Configuration
# ============================================
FIREBASE_CREDENTIALS_PATH=kile-kitabu-firebase-adminsdk-pjk21-68cbd0c3b4.json
FIREBASE_DATABASE_URL=https://kile-kitabu-default-rtdb.firebaseio.com
FIREBASE_PROJECT_ID=kile-kitabu

# ============================================
# Subscription Configuration
# ============================================
DAILY_RATE=5.0
FREE_TRIAL_DAYS=14
MONTHLY_CAP_KES=150
MAX_PREPAY_MONTHS=12

# ============================================
# M-Pesa Daraja Configuration (PRODUCTION)
# ============================================
# App: Prod-tianka-investments-ltd-1762795997
# Created: Mon, 10th of Nov 2025 at 20:33:19 pm
MPESA_ENV=production
MPESA_CONSUMER_KEY=rs7K6PTbaAzDFIcmkK0Rcg8u6GphrzUTAwfpuyd4DeSv43Og
MPESA_CONSUMER_SECRET=xshsALdAGkdfwjxALLBZCI7udGWB8dDSAubXs6tbbbUABvxqwfPuXml0hb7cbUYV
MPESA_SHORT_CODE=3576603
MPESA_PASSKEY=bcfeb194a2df8ca55f17c2816a55234c837516ce016dcade10621ce0ffc9e84d

# ============================================
# CyberSource Configuration (PRODUCTION)
# ============================================
# Note: You received production API access (CRQ000008538668)
# Check your email for production API URLs and credentials
CYBERSOURCE_ENV=production
CYBERSOURCE_MERCHANT_ID=your-production-merchant-id-here
CYBERSOURCE_API_KEY_ID=your-production-api-key-id-here
CYBERSOURCE_SECRET_KEY=your-production-base64-secret-key-here
CYBERSOURCE_WEBHOOK_SECRET=your-production-webhook-secret-key-here
```

## ✅ M-Pesa Configuration Status

- ✅ **Consumer Key**: Configured
- ✅ **Consumer Secret**: Configured
- ✅ **Short Code**: `3576603` (configured)
- ✅ **Passkey**: Configured
- ✅ **Environment**: `production`
- ✅ **API URLs**: Automatically set to production endpoints

## 🔐 Security Reminders

1. **Generate secure SECRET_KEY and CRON_SECRET_KEY**:
   ```bash
   python -c "import secrets; print(secrets.token_urlsafe(32))"
   ```

2. **Never share these credentials** publicly

3. **Keep `.env` file in `.gitignore`** (should already be there)

4. **Use environment variables** in production hosting (Render.com, etc.)

## 🚀 Next Steps

1. **Copy this configuration** to your `.env` file in `kilekitabu-backend/` directory

2. **Generate and set SECRET_KEY and CRON_SECRET_KEY**:
   - Run: `python -c "import secrets; print(secrets.token_urlsafe(32))"` twice
   - Replace `your-secret-key-here-change-this-to-a-random-string` with first result
   - Replace `your-cron-secret-key-here-change-this-to-a-random-string` with second result

3. **Add CyberSource credentials** (when available):
   - Get from CyberSource Business Center
   - Replace the placeholder values

4. **Restart your backend server**

5. **Test M-Pesa payment**:
   - Check logs for: `✅ M-Pesa client initialized successfully`
   - Try a small test payment (e.g., 10 KES)

## 📋 Verification Checklist

- [x] M-Pesa Consumer Key: Configured
- [x] M-Pesa Consumer Secret: Configured
- [x] M-Pesa Short Code: `3576603`
- [x] M-Pesa Passkey: Configured
- [x] M-Pesa Environment: `production`
- [ ] SECRET_KEY: **Generate and set**
- [ ] CRON_SECRET_KEY: **Generate and set**
- [ ] CyberSource credentials: **Add when available**
- [ ] Backend server restarted
- [ ] M-Pesa initialization verified in logs

## 🧪 Testing

After setup, test with:
1. Small payment (10 KES) via M-Pesa
2. Verify callback is received
3. Check credit balance updates correctly
4. Monitor logs for any errors

