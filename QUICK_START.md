# 🚀 KileKitabu Backend - Quick Start Guide

## ✅ Setup Complete!

Your backend is now fully configured and ready to use:

### **🔧 What's Configured:**
- ✅ **Firebase Integration** - Service account key loaded
- ✅ **PesaPal Integration** - Credentials configured
- ✅ **Virtual Environment** - Dependencies installed
- ✅ **Environment Variables** - All settings configured

### **🎯 Backend Features:**
- **Usage-based Payment System** - KSH 5 per day per use
- **Free Trial** - 7 days for new users
- **Credit Management** - Buy credit, only deduct when using
- **PesaPal Integration** - Secure payment processing
- **Firebase Authentication** - User management

## **🚀 How to Start the Server:**

### **Option 1: Using Setup Script (Recommended)**
```bash
cd backend
source venv/bin/activate
python setup.py
```

### **Option 2: Direct Start**
```bash
cd backend
source venv/bin/activate
python app.py
```

### **Option 3: Production Mode**
```bash
cd backend
source venv/bin/activate
gunicorn -w 4 -b 0.0.0.0:5000 app:app
```

## **🌐 API Endpoints:**

### **Health Check**
```bash
curl http://localhost:5000/
```

### **Available Endpoints:**
- `GET /` - Health check
- `POST /api/user/register` - Register new user
- `GET /api/user/credit` - Get credit information
- `POST /api/payment/initiate` - Start payment
- `GET /api/payment/status/<id>` - Check payment status
- `POST /api/usage/record` - Record app usage
- `GET /api/debts` - Get user debts
- `POST /api/debts` - Add new debt

## **🔑 Authentication:**

All endpoints (except health check) require Firebase ID token:
```
Authorization: Bearer <firebase-id-token>
```

## **💰 Payment System:**

### **Credit Calculation:**
- **Daily Rate**: KSH 5 per day
- **Credit Purchase**: Amount ÷ 5 = Credit Days
- **Example**: KSH 1000 = 200 days of credit

### **Usage Logic:**
- Only deducts credit when user performs actions
- One day credit per day of usage (not per action)
- No deduction if user doesn't use the app

### **Free Trial:**
- 7 days free trial for new users
- No credit required during trial period

## **📱 Integration with Android App:**

### **1. Check Credit Before Actions:**
```kotlin
// Before any app action, call:
GET /api/user/credit
```

### **2. Record Usage After Actions:**
```kotlin
// After user performs action:
POST /api/usage/record
{
    "action_type": "add_debt"
}
```

### **3. Handle Payment Prompts:**
```kotlin
// When credit is insufficient (402 response):
POST /api/payment/initiate
{
    "amount": 1000,
    "email": "user@example.com",
    "phone": "+254700000000"
}
```

## **🔧 Configuration Files:**

- **`.env`** - Environment variables (auto-created)
- **`kile-kitabu-firebase-adminsdk-pjk21-d2e073c9ae.json`** - Firebase credentials
- **`config.py`** - Application configuration
- **`pesapal_integration.py`** - PesaPal API integration

## **📊 Database Collections (Firebase):**

### **Users Collection:**
```json
{
    "uid": "firebase-user-id",
    "email": "user@example.com",
    "name": "John Doe",
    "registration_date": "2024-01-01T00:00:00Z",
    "credit_balance": 10,
    "last_usage_date": "2024-01-15T10:30:00Z",
    "total_payments": 1000
}
```

### **Payments Collection:**
```json
{
    "payment_id": "uuid",
    "user_id": "firebase-user-id",
    "amount": 1000,
    "credit_days": 200,
    "status": "completed",
    "created_at": "2024-01-01T00:00:00Z"
}
```

## **🛠️ Troubleshooting:**

### **Server Won't Start:**
1. Check if virtual environment is activated: `source venv/bin/activate`
2. Verify dependencies: `pip list`
3. Check Firebase credentials file exists

### **Payment Issues:**
1. Verify PesaPal credentials in `.env`
2. Check PesaPal contract is signed
3. Test with small amounts first

### **Authentication Errors:**
1. Ensure Firebase ID token is valid
2. Check token format: `Bearer <token>`
3. Verify Firebase project configuration

## **📞 Support:**

The backend is now ready for integration with your Android app! 

**Next Steps:**
1. Integrate API calls into your Android app
2. Test payment flow with small amounts
3. Deploy to production server
4. Monitor usage and payments

**🎉 Your KileKitabu payment system is ready to go!** 