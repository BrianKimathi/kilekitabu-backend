# Cron Jobs Documentation

This document describes all scheduled cron jobs running in the KileKitabu backend.

## Overview

All cron jobs run as background threads and check every minute for their scheduled execution time. They use Firebase Realtime Database to query user data and FCM (Firebase Cloud Messaging) to send push notifications.

## Scheduled Jobs

### 1. Low Credit Notifications
**Schedule:** Daily at 8:00 AM  
**Service:** `LowCreditScheduler`  
**Purpose:** Notify users with credits <= 2  
**File:** `services/low_credit_scheduler.py`

**What it does:**
- Checks all registered users for `credit_balance <= 2`
- Sends push notifications to affected users
- Messages vary based on credit balance:
  - 0 credits: "No Credits Remaining"
  - 1 credit: "Low Credits: 1 Day Remaining"
  - 2 credits: "Low Credits: 2 Days Remaining"
- Stops sending when credits go above 2

**Notification Data:**
```json
{
  "type": "low_credit",
  "user_id": "...",
  "credit_balance": "2",
  "notification_type": "low_credit_alert",
  "click_action": "com.jeff.kilekitabu.PAYMENT"
}
```

---

### 2. Debt Reminders (Upcoming Due Dates)
**Schedule:** Daily at 9:00 AM  
**Service:** `DebtReminderScheduler`  
**Purpose:** Notify users about debts due in 3 days and 1 day  
**File:** `services/debt_reminder_scheduler.py`

**What it does:**
- Checks all user debts for upcoming due dates
- Sends reminders for debts due in:
  - **3 days** before due date
  - **1 day** before due date (tomorrow)
- Consolidates multiple debts into single notifications
- Calculates total amounts for multiple debts

**Notification Messages:**
- **3 days:** "📅 Debt Reminder: 3 Days Left" or "📅 X Debts Due in 3 Days"
- **1 day:** "⏰ Debt Due Tomorrow!" or "⏰ X Debts Due Tomorrow!"

**Notification Data:**
```json
{
  "type": "debt_reminder",
  "user_id": "...",
  "days_until_due": "3",
  "debt_count": "2",
  "total_amount": "5000.00",
  "debts": [...],
  "click_action": "com.jeff.kilekitabu.DEBT_NOTIFICATION"
}
```

---

### 3. Debts Due Today
**Schedule:** Daily at 9:00 AM  
**Service:** `SimpleDebtScheduler`  
**Purpose:** Notify users about debts due today  
**File:** `services/simple_debt_scheduler.py`

**What it does:**
- Checks for debts with due date = today
- Sends consolidated notifications for all debts due today
- Calculates total amount due

---

### 4. Overdue Debts
**Schedule:** Every 3 days at 10:00 AM  
**Service:** `SimpleDebtScheduler`  
**Purpose:** Remind users about overdue debts  
**File:** `services/simple_debt_scheduler.py`

**What it does:**
- Checks for debts with due date < today
- Sends reminders for overdue debts
- Shows how many days overdue

---

### 5. Weekly Debt Summary
**Schedule:** Every Monday at 11:00 AM  
**Service:** `SimpleDebtScheduler`  
**Purpose:** Send weekly summary of all active debts  
**File:** `services/simple_debt_scheduler.py`

**What it does:**
- Summarizes all active (non-completed) debts
- Shows total count and total amount
- Sends weekly reminder

---

### 6. SMS Reminders
**Schedule:** Daily at 9:00 AM and 2:00 PM  
**Service:** `SMSReminderScheduler`  
**Purpose:** Send SMS reminders for debts  
**File:** `services/sms_reminder_scheduler.py`

**What it does:**
- Sends SMS reminders for upcoming debts
- Uses SMS API if configured

---

## Schedule Summary

| Time | Job | Purpose |
|------|-----|---------|
| 8:00 AM | Low Credit Notifications | Credits <= 2 |
| 9:00 AM | Debt Reminders | Debts due in 3 days & 1 day |
| 9:00 AM | Debts Due Today | Debts due today |
| 9:00 AM | SMS Reminders | SMS debt reminders |
| 10:00 AM (every 3 days) | Overdue Debts | Overdue debt reminders |
| 11:00 AM (Mondays) | Weekly Summary | Weekly debt summary |
| 2:00 PM | SMS Reminders | SMS debt reminders (backup) |

## Configuration

All schedulers are initialized in `app.py` during Flask app startup:

```python
# Low credit scheduler
low_credit_scheduler = LowCreditScheduler(fcm_service)
low_credit_scheduler.start_scheduler()

# Debt reminder scheduler
debt_reminder_scheduler = DebtReminderScheduler(fcm_service)
debt_reminder_scheduler.start_scheduler()

# Debt due today scheduler
notification_scheduler = SimpleDebtScheduler(fcm_service)
notification_scheduler.start_scheduler()
```

## Customization

### Change Reminder Days

To change when debt reminders are sent, edit `services/debt_reminder_scheduler.py`:

```python
# Change reminder days (e.g., 7 days, 3 days, 1 day)
self.reminder_days = [7, 3, 1]
```

### Change Schedule Times

Edit the scheduler files to change execution times:

- `low_credit_scheduler.py`: Line 46 - Change `current_time.hour == 8`
- `debt_reminder_scheduler.py`: Line 46 - Change `current_time.hour == 9`
- `simple_debt_scheduler.py`: Lines 44, 48, 54 - Change hour values

## Monitoring

All schedulers log their activities:
- ✅ Success messages
- ❌ Error messages
- 📤 Notification counts
- 🔍 Check operations

Check backend logs to monitor cron job execution.

## Testing

To test cron jobs without waiting:

1. **Temporarily change time checks** in scheduler files
2. **Or create a test endpoint** to manually trigger jobs:

```python
@app.route('/api/test/low-credit-check', methods=['POST'])
def test_low_credit():
    low_credit_scheduler.check_low_credits()
    return jsonify({'status': 'ok'})

@app.route('/api/test/debt-reminders', methods=['POST'])
def test_debt_reminders():
    debt_reminder_scheduler.check_upcoming_debts()
    return jsonify({'status': 'ok'})
```

## Notes

- All schedulers run in daemon threads (won't block app shutdown)
- Schedulers check every minute for their scheduled time
- Each scheduler only runs once per day (tracked by `last_check_date`)
- Notifications are sent via FCM (Firebase Cloud Messaging)
- All operations query Firebase Realtime Database

