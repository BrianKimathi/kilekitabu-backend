# Render Deployment Fix Guide

## Issues Found and Fixed

### 1. PesaPal API URL Issue (404 Error)
**Problem**: Double `/api` in URL causing 404 errors
- Error URL: `https://pay.pesapal.com/v3/api/api/Auth/RequestToken`
- Correct URL: `https://pay.pesapal.com/v3/api/Auth/RequestToken`

**Fix Applied**: Updated `config.py` to remove trailing `/api` from base URL

### 2. Authentication Issues (401/503 Errors)
**Problem**: Firebase Admin SDK not properly initialized in production
**Fix Applied**: 
- Added robust Firebase initialization with error handling
- Added Firebase availability check in authentication decorator
- Better error messages for debugging

## Environment Variables to Set in Render

Make sure these environment variables are set in your Render dashboard:

```bash
# Firebase Configuration
FIREBASE_CREDENTIALS_PATH=kile-kitabu-firebase-adminsdk-pjk21-68cbd0c3b4.json
FIREBASE_DATABASE_URL=https://kile-kitabu-default-rtdb.firebaseio.com

# PesaPal Configuration
PESAPAL_CONSUMER_KEY=sRE8q61NY+L2TophDXPUsfF/fLZ+Wz7Z
PESAPAL_CONSUMER_SECRET=VgLnSaRRXpuZsH69EMRH62uFmdk=
PESAPAL_ENVIRONMENT=production
PESAPAL_BASE_URL=https://pay.pesapal.com/v3

# Application Configuration
BASE_URL=https://kilekitabu-backend.onrender.com
SECRET_KEY=your-secret-key-here
DEBUG=false
```

## Files to Upload to Render

Make sure these files are in your Render deployment:

1. `kile-kitabu-firebase-adminsdk-pjk21-68cbd0c3b4.json` (Firebase credentials)
2. All Python files in the backend directory
3. `requirements.txt`

## Testing the Fix

After redeploying, test these endpoints:

1. **Health Check**: `GET https://kilekitabu-backend.onrender.com/`
2. **Credit Info**: `GET https://kilekitabu-backend.onrender.com/api/user/credit` (with Firebase token)
3. **Usage Record**: `POST https://kilekitabu-backend.onrender.com/api/usage/record` (with Firebase token)

## Expected Logs After Fix

You should see:
```
Firebase initialized successfully
PesaPal Config Debug:
  Environment: production
  Base URL: https://pay.pesapal.com/v3
Token request status: 200
PesaPal integration initialized successfully
```

## If Issues Persist

1. Check Render logs for specific error messages
2. Verify Firebase credentials file is uploaded correctly
3. Ensure all environment variables are set
4. Check that the Firebase project is active and accessible
