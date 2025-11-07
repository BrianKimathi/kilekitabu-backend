# Testing Notifications

This document explains how to test notification functionality in the KileKitabu backend.

## Test Endpoints

### 1. Test Low Credit Notifications
**Endpoint:** `POST /api/notifications/test/low-credit`  
**Description:** Manually triggers low credit check for all users

**Example:**
```bash
curl -X POST https://your-app.onrender.com/api/notifications/test/low-credit
```

**Response:**
```json
{
  "status": "success",
  "message": "Low credit check triggered. Check logs for results."
}
```

---

### 2. Test Debt Reminder Notifications
**Endpoint:** `POST /api/notifications/test/debt-reminders`  
**Description:** Manually triggers debt reminder check (debts due in 3 days, 1 day)

**Example:**
```bash
curl -X POST https://your-app.onrender.com/api/notifications/test/debt-reminders
```

**Response:**
```json
{
  "status": "success",
  "message": "Debt reminder check triggered. Check logs for results."
}
```

---

### 3. Send Test Notification to Specific User
**Endpoint:** `POST /api/notifications/test/send`  
**Description:** Sends a test notification to a specific user

**Request Body:**
```json
{
  "user_id": "GI7PPaaRh7hRogozJcDHt33RQEw2",
  "title": "Test Notification",
  "body": "This is a test notification"
}
```

**Example:**
```bash
curl -X POST https://your-app.onrender.com/api/notifications/test/send \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": "GI7PPaaRh7hRogozJcDHt33RQEw2",
    "title": "Test Notification",
    "body": "This is a test notification from KileKitabu"
  }'
```

**Response (Success):**
```json
{
  "status": "success",
  "message": "Test notification sent successfully",
  "user_id": "GI7PPaaRh7hRogozJcDHt33RQEw2"
}
```

**Response (Error - No Token):**
```json
{
  "error": "No FCM token found for user GI7PPaaRh7hRogozJcDHt33RQEw2"
}
```

---

## Keep-Alive Endpoint

**Endpoint:** `GET /api/health/keep-alive`  
**Description:** Health check endpoint pinged every 7 minutes to prevent Render.com spin-down

**Example:**
```bash
curl https://your-app.onrender.com/api/health/keep-alive
```

**Response:**
```json
{
  "status": "alive",
  "timestamp": "2025-11-07T14:30:00.123456",
  "message": "Server is active"
}
```

---

## Testing Checklist

### ✅ Test Low Credit Notifications
1. Set a user's `credit_balance` to 2 or less in Firebase
2. Call `POST /api/notifications/test/low-credit`
3. Check backend logs for notification results
4. Verify notification appears on user's device

### ✅ Test Debt Reminder Notifications
1. Create a debt with due date = today + 3 days (or today + 1 day)
2. Call `POST /api/notifications/test/debt-reminders`
3. Check backend logs for notification results
4. Verify notification appears on user's device

### ✅ Test Individual Notification
1. Get user's FCM token from Firebase (`fcm_tokens/{user_id}`)
2. Call `POST /api/notifications/test/send` with user_id
3. Verify notification appears on user's device

### ✅ Test Keep-Alive
1. Call `GET /api/health/keep-alive`
2. Verify response is 200 OK
3. Check that keep-alive scheduler is running (check logs on startup)

---

## Common Issues

### No FCM Token Found
**Problem:** `No FCM token found for user {user_id}`  
**Solution:** 
- User must have opened the app and registered their FCM token
- Check Firebase: `fcm_tokens/{user_id}` should exist

### FCM Service Not Available
**Problem:** `FCM service not available`  
**Solution:**
- Check Firebase credentials file exists
- Verify `FIREBASE_CREDENTIALS_PATH` in `.env`
- Check backend startup logs

### Notification Not Received
**Possible Causes:**
1. User's device is offline
2. FCM token is invalid/expired
3. App notifications are disabled
4. Firebase project configuration issue

**Debug Steps:**
1. Check backend logs for FCM response
2. Verify FCM token in Firebase
3. Test with a fresh FCM token
4. Check Firebase Console for delivery status

---

## Monitoring

### Backend Logs
All notification operations are logged:
- ✅ Success: `Sent low credit notification to user {user_id}`
- ❌ Errors: `Error sending notification: {error}`
- 📤 Counts: `Sent {count} notifications`

### Firebase Console
Check Firebase Console → Cloud Messaging for:
- Delivery statistics
- Failed deliveries
- Token validity

---

## Keep-Alive Scheduler

The keep-alive scheduler automatically pings the server every 7 minutes to prevent Render.com from spinning down after 10 minutes of inactivity.

**Configuration:**
- Interval: 7 minutes (configurable in `keep_alive_scheduler.py`)
- Endpoint: `/api/health/keep-alive`
- Starts: 1 minute after server startup
- Logs: All ping attempts are logged

**To Disable:**
Remove or comment out the keep-alive scheduler initialization in `app.py`:
```python
# keep_alive_scheduler = KeepAliveScheduler(base_url)
# keep_alive_scheduler.start_scheduler()
```

