# Render Environment Variables Fix

## Current Issues

Your Render environment variables have these problems:

1. **PESAPAL_BASE_URL**: `https://pay.pesapal.com/v3/api` ❌
   - Should be: `https://pay.pesapal.com/v3` ✅

2. **Firebase credentials file**: `kile-kitabu-firebase-adminsdk-pjk21-d2e073c9ae.json`
   - Make sure this file is uploaded to your Render deployment

## Fix Steps

### 1. Update Environment Variables in Render Dashboard

Go to your Render service dashboard and update:

```bash
# Change this:
PESAPAL_BASE_URL=https://pay.pesapal.com/v3/api

# To this:
PESAPAL_BASE_URL=https://pay.pesapal.com/v3
```

### 2. Verify Firebase Credentials File

Make sure the file `kile-kitabu-firebase-adminsdk-pjk21-d2e073c9ae.json` is in your repository root and gets deployed to Render.

### 3. Redeploy

After updating the environment variable, redeploy your service.

## Expected Logs After Fix

You should see:
```
Original PESAPAL_BASE_URL: https://pay.pesapal.com/v3/api
Fixed PESAPAL_BASE_URL: https://pay.pesapal.com/v3
Looking for Firebase credentials at: kile-kitabu-firebase-adminsdk-pjk21-d2e073c9ae.json
Firebase credentials file found, initializing...
Firebase initialized successfully
Token request status: 200
PesaPal integration initialized successfully
```

## Test After Fix

1. **Health Check**: `GET https://kilekitabu-backend.onrender.com/`
2. **Usage Record**: `POST https://kilekitabu-backend.onrender.com/api/usage/record` (with Firebase token)
3. **Payment Initiate**: `POST https://kilekitabu-backend.onrender.com/api/payment/initiate` (with Firebase token)

All should return 200 status codes instead of 401/503.
