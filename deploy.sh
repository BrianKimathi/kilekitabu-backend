#!/bin/bash

echo "🚀 Deploying KileKitabu Backend to Render.com"

# Check if we're in the right directory
if [ ! -f "app.py" ]; then
    echo "❌ Error: app.py not found. Please run this script from the backend directory."
    exit 1
fi

# Check if requirements.txt exists
if [ ! -f "requirements.txt" ]; then
    echo "❌ Error: requirements.txt not found."
    exit 1
fi

# Check if Firebase credentials exist
if [ ! -f "kile-kitabu-firebase-adminsdk-pjk21-d2e073c9ae.json" ]; then
    echo "⚠️  Warning: Firebase credentials file not found."
    echo "   Make sure to upload the credentials file to Render.com"
fi

# Check if render.yaml exists
if [ ! -f "render.yaml" ]; then
    echo "❌ Error: render.yaml not found."
    exit 1
fi

echo "✅ All required files found"

# Test the app locally (optional)
echo "🧪 Testing app locally..."
python3 -c "
import sys
sys.path.append('.')
try:
    from app import app
    print('✅ App imports successfully')
except Exception as e:
    print(f'❌ App import failed: {e}')
    sys.exit(1)
"

echo "📋 Deployment Checklist:"
echo "1. ✅ All files present"
echo "2. ✅ App imports successfully"
echo "3. 🔄 Push to Git repository"
echo "4. 🔄 Deploy on Render.com dashboard"
echo "5. 🔄 Check logs for any errors"

echo ""
echo "📝 Next Steps:"
echo "1. Commit and push your changes to Git"
echo "2. Go to Render.com dashboard"
echo "3. Find your kilekitabu-backend service"
echo "4. Click 'Manual Deploy'"
echo "5. Wait for deployment to complete"
echo "6. Check the logs for any errors"

echo ""
echo "🔍 Troubleshooting:"
echo "- If you see 503 errors, check the Render.com logs"
echo "- Make sure Firebase credentials are uploaded to Render.com"
echo "- Verify environment variables are set correctly"
echo "- Check that the service is not hibernated"

echo ""
echo "🌐 Test URLs after deployment:"
echo "- Health check: https://kilekitabu-backend.onrender.com/"
echo "- Test endpoint: https://kilekitabu-backend.onrender.com/test"
echo "- Credit endpoint: https://kilekitabu-backend.onrender.com/api/user/credit"

echo ""
echo "🎯 Ready for deployment!" 