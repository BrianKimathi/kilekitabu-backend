# Updated .env File Template (Lines 1-28)

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
```

## Key Changes

1. **Added User Reset Configuration section** (lines 17-24):
   - `RESET_USERS_ON_LOGIN=True` - Enables automatic reset for all users on login
   - This ensures every user (existing and new) gets a fresh 14-day trial

2. **Organized sections** with clear headers for better readability

3. **Default value**: `RESET_USERS_ON_LOGIN=True` (enabled by default)

## Usage

Copy these lines (1-28) to your `.env` file in the `kilekitabu-backend/` directory, then add the remaining configuration (M-Pesa, CyberSource, etc.) from `ENV_PRODUCTION_TEMPLATE.md`.


