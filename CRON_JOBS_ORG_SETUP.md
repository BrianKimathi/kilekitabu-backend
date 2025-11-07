# Cron-Jobs.org Setup Guide

This guide explains how to set up cron jobs on cron-jobs.org to keep your server active and trigger notifications.

## Endpoints for Cron-Jobs.org

### 1. Keep Server Active (Every 7 minutes)
**URL:** `https://your-app.onrender.com/api/health/keep-alive`  
**Method:** GET  
**Authentication:** None required  
**Purpose:** Prevents Render.com from spinning down after 10 minutes of inactivity

**Cron Schedule:** Every 7 minutes
- **Minute:** `*/7` (every 7 minutes)
- **Hour:** `*` (every hour)
- **Day:** `*` (every day)
- **Month:** `*` (every month)
- **Weekday:** `*` (every weekday)

**Full Cron Expression:** `*/7 * * * *`

---

### 2. Low Credit Notifications (Daily at 8:00 AM)
**URL:** `https://your-app.onrender.com/api/cron/notifications/low-credit?key=YOUR_SECRET_KEY`  
**Method:** GET  
**Authentication:** Query parameter `key` (use your SECRET_KEY from .env)  
**Purpose:** Sends notifications to users with credits <= 2

**Cron Schedule:** Daily at 8:00 AM
- **Minute:** `0`
- **Hour:** `8`
- **Day:** `*`
- **Month:** `*`
- **Weekday:** `*`

**Full Cron Expression:** `0 8 * * *`

---

### 3. Debt Reminder Notifications (Daily at 9:00 AM)
**URL:** `https://your-app.onrender.com/api/cron/notifications/debt-reminders?key=YOUR_SECRET_KEY`  
**Method:** GET  
**Authentication:** Query parameter `key` (use your SECRET_KEY from .env)  
**Purpose:** Sends reminders for debts due in 3 days and 1 day

**Cron Schedule:** Daily at 9:00 AM
- **Minute:** `0`
- **Hour:** `9`
- **Day:** `*`
- **Month:** `*`
- **Weekday:** `*`

**Full Cron Expression:** `0 9 * * *`

---

### 4. All Notifications (Daily at 9:00 AM)
**URL:** `https://your-app.onrender.com/api/cron/notifications/all?key=YOUR_SECRET_KEY`  
**Method:** GET  
**Authentication:** Query parameter `key` (use your SECRET_KEY from .env)  
**Purpose:** Triggers both low credit and debt reminder notifications

**Cron Schedule:** Daily at 9:00 AM
- **Minute:** `0`
- **Hour:** `9`
- **Day:** `*`
- **Month:** `*`
- **Weekday:** `*`

**Full Cron Expression:** `0 9 * * *`

---

## Setup Instructions for Cron-Jobs.org

### Step 1: Create Account
1. Go to https://cron-jobs.org
2. Sign up for a free account
3. Verify your email

### Step 2: Add Keep-Alive Job
1. Click "Create Cronjob"
2. **Title:** `Keep Server Active`
3. **URL:** `https://your-app.onrender.com/api/health/keep-alive`
4. **Schedule:** 
   - Select "Every X minutes"
   - Enter `7` minutes
5. **Method:** GET
6. Click "Create"

### Step 3: Add Low Credit Notifications Job
1. Click "Create Cronjob"
2. **Title:** `Low Credit Notifications`
3. **URL:** `https://your-app.onrender.com/api/cron/notifications/low-credit?key=YOUR_SECRET_KEY`
   - Replace `YOUR_SECRET_KEY` with your actual SECRET_KEY from `.env`
4. **Schedule:**
   - Select "Daily"
   - Set time to `08:00` (8:00 AM)
5. **Method:** GET
6. Click "Create"

### Step 4: Add Debt Reminder Notifications Job
1. Click "Create Cronjob"
2. **Title:** `Debt Reminder Notifications`
3. **URL:** `https://your-app.onrender.com/api/cron/notifications/debt-reminders?key=YOUR_SECRET_KEY`
   - Replace `YOUR_SECRET_KEY` with your actual SECRET_KEY from `.env`
4. **Schedule:**
   - Select "Daily"
   - Set time to `09:00` (9:00 AM)
5. **Method:** GET
6. Click "Create"

### Step 5: (Optional) Add All Notifications Job
Instead of separate jobs, you can use one job that triggers all notifications:

1. Click "Create Cronjob"
2. **Title:** `All Notifications`
3. **URL:** `https://your-app.onrender.com/api/cron/notifications/all?key=YOUR_SECRET_KEY`
   - Replace `YOUR_SECRET_KEY` with your actual SECRET_KEY from `.env`
4. **Schedule:**
   - Select "Daily"
   - Set time to `09:00` (9:00 AM)
5. **Method:** GET
6. Click "Create"

---

## Security Notes

### Authentication
- The notification endpoints require a `key` query parameter
- Use your `SECRET_KEY` from `.env` file
- **Never commit your SECRET_KEY to Git!**
- Keep it secret and only use it in cron-jobs.org

### Alternative: Header Authentication
You can also use header authentication:
- **Header Name:** `X-Cron-Auth`
- **Header Value:** Your SECRET_KEY

Example with curl:
```bash
curl -H "X-Cron-Auth: YOUR_SECRET_KEY" \
  https://your-app.onrender.com/api/cron/notifications/low-credit
```

---

## Testing

### Test Keep-Alive Endpoint
```bash
curl https://your-app.onrender.com/api/health/keep-alive
```

Expected response:
```json
{
  "status": "alive",
  "timestamp": "2025-11-07T16:00:00.123456",
  "message": "Server is active"
}
```

### Test Notification Endpoints
```bash
# Low credit notifications
curl "https://your-app.onrender.com/api/cron/notifications/low-credit?key=YOUR_SECRET_KEY"

# Debt reminders
curl "https://your-app.onrender.com/api/cron/notifications/debt-reminders?key=YOUR_SECRET_KEY"

# All notifications
curl "https://your-app.onrender.com/api/cron/notifications/all?key=YOUR_SECRET_KEY"
```

---

## Monitoring

### Check Cron Job Status
1. Log in to cron-jobs.org
2. View your cronjobs dashboard
3. Check execution history
4. View success/failure rates

### Check Backend Logs
Monitor your Render.com logs for:
- `✅ Low credit notifications triggered via cron`
- `✅ Debt reminder notifications triggered via cron`
- `🔄 Pinging server to keep alive`
- `✅ Server ping successful`

---

## Recommended Setup

### Minimal Setup (3 Jobs)
1. **Keep-Alive:** Every 7 minutes
2. **Low Credit:** Daily at 8:00 AM
3. **Debt Reminders:** Daily at 9:00 AM

### Simplified Setup (2 Jobs)
1. **Keep-Alive:** Every 7 minutes
2. **All Notifications:** Daily at 9:00 AM (triggers both low credit and debt reminders)

---

## Troubleshooting

### Cron Job Not Executing
- Check cron-jobs.org dashboard for errors
- Verify URL is correct and accessible
- Check authentication key is correct
- Ensure server is running on Render.com

### Notifications Not Sending
- Check backend logs for errors
- Verify FCM service is configured
- Check Firebase credentials
- Ensure users have FCM tokens registered

### Server Still Spinning Down
- Verify keep-alive job is running every 7 minutes
- Check cron-jobs.org execution history
- Ensure URL is correct
- Check Render.com logs for incoming requests

---

## Timezone Considerations

**Important:** Cron-jobs.org uses UTC timezone by default.

- If you want 8:00 AM in your local timezone, convert to UTC
- Example: 8:00 AM EAT (UTC+3) = 5:00 AM UTC
- Adjust cron schedule accordingly

---

## Cost

- **cron-jobs.org Free Plan:** 
  - Up to 2 cronjobs
  - Execution every 5 minutes minimum
- **cron-jobs.org Paid Plans:**
  - More cronjobs
  - Faster execution intervals
  - Better monitoring

For the keep-alive job (every 7 minutes), you'll need at least the free plan.

---

## Summary

**Required Cron Jobs:**
1. ✅ Keep-Alive: `*/7 * * * *` → `GET /api/health/keep-alive`
2. ✅ Low Credit: `0 8 * * *` → `GET /api/cron/notifications/low-credit?key=SECRET`
3. ✅ Debt Reminders: `0 9 * * *` → `GET /api/cron/notifications/debt-reminders?key=SECRET`

**Or Simplified:**
1. ✅ Keep-Alive: `*/7 * * * *` → `GET /api/health/keep-alive`
2. ✅ All Notifications: `0 9 * * *` → `GET /api/cron/notifications/all?key=SECRET`

