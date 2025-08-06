# KileKitabu Backend

Flask backend with Firebase Realtime Database integration for the KileKitabu debt management app, featuring a usage-based payment system with PesaPal integration.

## Features

- **Usage-based Payment System**: KSH 5 per day per use
- **Free Trial**: 7 days free trial for new users
- **Credit System**: Purchase credit days, only deduct when using the app
- **PesaPal Integration**: Secure payment processing
- **Firebase Authentication**: Uses Firebase ID tokens from the Android app
- **Firebase Realtime Database**: Real-time data storage
- **Payment-Only Backend**: Focused on payment processing and credit management

## Setup Instructions

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Environment Configuration

Create a `.env` file in the backend directory:

```env
# Flask Configuration
SECRET_KEY=your-secret-key-here
FLASK_DEBUG=True
HOST=0.0.0.0
PORT=5000

# Firebase Configuration
FIREBASE_CREDENTIALS_PATH=kile-kitabu-firebase-adminsdk-pjk21-d2e073c9ae.json
FIREBASE_DATABASE_URL=https://kile-kitabu-default-rtdb.firebaseio.com



# PesaPal Configuration
PESAPAL_CONSUMER_KEY=sRE8q61NY+L2TophDXPUsfF/fLZ+Wz7Z
PESAPAL_CONSUMER_SECRET=VgLnSaRRXpuZsH69EMRH62uFmdk=
PESAPAL_BASE_URL=https://www.pesapal.com

# App Configuration
BASE_URL=http://localhost:5000
```

### 3. Firebase Setup

1. Firebase service account key is already configured
2. Firebase Realtime Database URL is set to `https://kile-kitabu-default-rtdb.firebaseio.com`
3. The backend uses Realtime Database instead of Firestore

### 4. PesaPal Setup

1. Register for a PesaPal merchant account
2. Get your Consumer Key and Consumer Secret
3. Update the PesaPal credentials in your `.env` file

### 5. Run the Application

```bash
python app.py
```

The server will start on `http://localhost:5000`

## API Endpoints

### Authentication Required Endpoints

All endpoints require a Firebase ID token in the Authorization header:
```
Authorization: Bearer <firebase-id-token>
```

### User Management



#### Get Credit Information
```
GET /api/user/credit
```
**Response:**
```json
{
    "credit_balance": 10,
    "is_in_trial": false,
    "trial_days_remaining": 0,
    "last_usage_date": "2024-01-15T10:30:00Z",
    "total_payments": 1000
}
```

### Payment Management

#### Initiate Payment
```
POST /api/payment/initiate
```
**Request Body:**
```json
{
    "amount": 1000,
    "email": "user@example.com",
    "phone": "+254700000000",
    "first_name": "John",
    "last_name": "Doe"
}
```

#### Confirm Payment (Webhook)
```
POST /api/payment/confirm
```
**Request Body:**
```json
{
    "payment_id": "payment-uuid",
    "status": "completed"
}
```

### Usage Tracking

#### Record Usage
```
POST /api/usage/record
```
**Request Body:**
```json
{
    "action_type": "add_debt"
}
```

### Protected Endpoints (Require Credit)



## Payment System Logic

### Credit Calculation
- **Daily Rate**: KSH 5 per day
- **Credit Purchase**: Amount ÷ 5 = Credit Days
- **Example**: KSH 1000 = 200 days of credit

### Usage Tracking
- Only deducts credit when user performs actions
- One day credit per day of usage (not per action)
- No deduction if user doesn't use the app

### Free Trial
- 7 days free trial for new users
- No credit required during trial period
- Trial starts from registration date

## Error Responses

### Insufficient Credit (402)
```json
{
    "error": "Insufficient credit",
    "message": "Please purchase credit to continue using the app",
    "required_payment": true
}
```

### Authentication Error (401)
```json
{
    "error": "Invalid token"
}
```

## Deployment

### Using Gunicorn
```bash
gunicorn -w 4 -b 0.0.0.0:5000 app:app
```

### Environment Variables for Production
```env
FLASK_DEBUG=False
SECRET_KEY=your-production-secret-key
BASE_URL=https://your-domain.com
```

## Security Considerations

1. **Firebase Authentication**: All endpoints require valid Firebase tokens
2. **Credit Validation**: Protected endpoints check credit before allowing access
3. **Payment Verification**: PesaPal webhooks should be verified for authenticity
4. **Rate Limiting**: Consider implementing rate limiting for production

## Database Collections (Firebase)

### Users Collection
```json
{
    "uid": "firebase-user-id",
    "email": "user@example.com",
    "name": "John Doe",
    "registration_date": "2024-01-01T00:00:00Z",
    "credit_balance": 10,
    "last_usage_date": "2024-01-15T10:30:00Z",
    "total_payments": 1000,
    "created_at": "2024-01-01T00:00:00Z"
}
```

### Payments Collection
```json
{
    "payment_id": "uuid",
    "user_id": "firebase-user-id",
    "amount": 1000,
    "credit_days": 200,
    "status": "completed",
    "created_at": "2024-01-01T00:00:00Z",
    "completed_at": "2024-01-01T00:05:00Z"
}
```

### Usage Logs Collection
```json
{
    "usage_id": "uuid",
    "user_id": "firebase-user-id",
    "action_type": "add_debt",
    "credit_deducted": 1,
    "remaining_credit": 9,
    "timestamp": "2024-01-15T10:30:00Z"
}
``` 