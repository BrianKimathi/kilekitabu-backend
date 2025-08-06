# Render Deployment Guide

## Issues Fixed

### 1. Port Configuration Issue
**Problem**: The app was running on port 10000 but Render was expecting it on port 5050.

**Solution**: 
- Modified `app.py` to use the `PORT` environment variable
- Created `gunicorn.conf.py` to properly configure gunicorn with the correct port
- Added `render.yaml` and `Procfile` for proper deployment configuration

### 2. Firebase Credentials Issue
**Problem**: Firebase credentials file was in `.gitignore`, so it wouldn't be deployed to Render.

**Solution**:
- Modified `app.py` to support Firebase credentials from environment variables
- Updated `config.py` to handle both file-based and environment variable-based credentials
- Firebase credentials should be set as environment variables in Render dashboard (not in render.yaml for security)

## Files Modified/Created

### Modified Files:
- `app.py`: Updated to use PORT environment variable and handle Firebase credentials from env vars
- `config.py`: Added support for Firebase credentials JSON from environment variables

### New Files:
- `gunicorn.conf.py`: Gunicorn configuration for proper port binding
- `render.yaml`: Render deployment configuration (without sensitive data)
- `Procfile`: Alternative deployment method
- `DEPLOYMENT_GUIDE.md`: This guide

## Deployment Steps

1. **Commit and push your changes**:
   ```bash
   git add .
   git commit -m "Add Render deployment configuration with secure credential handling"
   git push
   ```

2. **Deploy to Render**:
   - The `render.yaml` file will automatically configure basic settings
   - You'll need to set sensitive environment variables manually in Render dashboard

3. **Set Environment Variables in Render Dashboard**:
   - Go to your Render service dashboard
   - Navigate to "Environment" tab
   - Add the following environment variables:
     - `FIREBASE_CREDENTIALS_JSON`: The Firebase service account JSON (see below)
     - `FIREBASE_DATABASE_URL`: https://kile-kitabu-default-rtdb.firebaseio.com
     - `FLASK_DEBUG`: false
     - `HOST`: 0.0.0.0

4. **Get Firebase Credentials JSON**:
   Run this command to get the JSON string for the `FIREBASE_CREDENTIALS_JSON` environment variable:
   ```bash
   python3 -c "
   import json
   with open('kile-kitabu-firebase-adminsdk-pjk21-d2e073c9ae.json', 'r') as f:
       print(json.dumps(json.load(f)))
   "
   ```
   Copy the entire output and paste it as the value for `FIREBASE_CREDENTIALS_JSON` in Render.

## Testing the Deployment

After deployment, your app should be accessible at your Render URL. Test the health check endpoint:

```bash
curl https://your-app-name.onrender.com/
```

Expected response:
```json
{
  "status": "healthy",
  "service": "KileKitabu Backend",
  "version": "1.0.0",
  "features": [
    "Usage-based payment system",
    "PesaPal integration", 
    "Firebase authentication",
    "Credit management"
  ]
}
```

## Troubleshooting

If you still encounter issues:

1. **Check Render logs** for any error messages
2. **Verify environment variables** are set correctly in Render dashboard
3. **Test locally** with the same environment variables to ensure everything works
4. **Check Firebase credentials** are valid and have proper permissions

## Security Notes

- The Firebase credentials are now stored as environment variables, which is more secure than file-based storage
- Credentials are NOT included in the render.yaml file to prevent them from being committed to version control
- Consider rotating the Firebase service account key periodically
- Never commit sensitive credentials to version control 