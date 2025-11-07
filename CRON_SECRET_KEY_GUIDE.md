# Cron Secret Key Guide

## Which Secret Key to Use?

For the cron notification endpoints, you need to use a secret key for authentication. Here are your options:

### Option 1: Use SECRET_KEY (Recommended for simplicity)

Use the `SECRET_KEY` from your `.env` file:

```env
SECRET_KEY=your-actual-secret-key-here
```

Then use it in the cron URLs:
```
https://your-app.onrender.com/api/cron/notifications/low-credit?key=your-actual-secret-key-here
```

### Option 2: Use Dedicated CRON_SECRET_KEY (Recommended for security)

Set a separate `CRON_SECRET_KEY` in your `.env` file:

```env
SECRET_KEY=your-app-secret-key
CRON_SECRET_KEY=your-cron-specific-secret-key
```

Then use `CRON_SECRET_KEY` in the cron URLs:
```
https://your-app.onrender.com/api/cron/notifications/low-credit?key=your-cron-specific-secret-key
```

**Benefits:**
- Separate key for cron jobs
- Can be rotated independently
- More secure (different key for different purposes)

---

## How to Set It Up

### Step 1: Check Your .env File

Open `kilekitabu-backend/.env` and check if you have:

```env
SECRET_KEY=some-secret-value
```

If you don't have `SECRET_KEY` set, add it:

```env
SECRET_KEY=generate-a-random-secret-key-here
```

### Step 2: Generate a Secret Key (if needed)

You can generate a random secret key using:

**Python:**
```python
import secrets
print(secrets.token_urlsafe(32))
```

**Online:**
- Use a password generator
- Or use: https://randomkeygen.com/

**Example secret key:**
```
aB3xK9mP2qR7vT5wY8zA1bC4dE6fG9hI0jK2lM3nO4pQ5rS6tU7vW8xY9z
```

### Step 3: Add to .env File

```env
# Application Secret Key
SECRET_KEY=aB3xK9mP2qR7vT5wY8zA1bC4dE6fG9hI0jK2lM3nO4pQ5rS6tU7vW8xY9z

# Optional: Dedicated Cron Secret Key (if different from SECRET_KEY)
CRON_SECRET_KEY=your-cron-specific-key-here
```

### Step 4: Use in Cron-Jobs.org

When creating cron jobs, use the key in the URL:

**For Low Credit Notifications:**
```
https://your-app.onrender.com/api/cron/notifications/low-credit?key=aB3xK9mP2qR7vT5wY8zA1bC4dE6fG9hI0jK2lM3nO4pQ5rS6tU7vW8xY9z
```

**For Debt Reminders:**
```
https://your-app.onrender.com/api/cron/notifications/debt-reminders?key=aB3xK9mP2qR7vT5wY8zA1bC4dE6fG9hI0jK2lM3nO4pQ5rS6tU7vW8xY9z
```

**For All Notifications:**
```
https://your-app.onrender.com/api/cron/notifications/all?key=aB3xK9mP2qR7vT5wY8zA1bC4dE6fG9hI0jK2lM3nO4pQ5rS6tU7vW8xY9z
```

---

## Security Best Practices

1. **Never commit secrets to Git**
   - `.env` file should be in `.gitignore` ✅ (already done)

2. **Use a strong secret key**
   - At least 32 characters
   - Mix of letters, numbers, and special characters
   - Randomly generated

3. **Use different keys for different purposes**
   - `SECRET_KEY` for app secrets
   - `CRON_SECRET_KEY` for cron jobs (optional but recommended)

4. **Rotate keys periodically**
   - Change keys every few months
   - Update cron-jobs.org URLs when you change keys

5. **Don't share keys publicly**
   - Never post keys in public forums
   - Never commit to public repositories
   - Only use in cron-jobs.org (private service)

---

## Testing Your Key

Test if your key works:

```bash
# Test low credit endpoint
curl "https://your-app.onrender.com/api/cron/notifications/low-credit?key=YOUR_SECRET_KEY"

# Should return:
# {"status": "success", "message": "Low credit check triggered", ...}

# If wrong key:
# {"error": "Unauthorized"}
```

---

## Current Configuration

The cron endpoints check for authentication in this order:

1. **CRON_SECRET_KEY** (if set in `.env`)
2. **SECRET_KEY** (if CRON_SECRET_KEY not set)
3. **No auth required** (if both are default/unset)

**Recommendation:** Set `SECRET_KEY` in your `.env` file and use that value in cron-jobs.org.

---

## Quick Setup Checklist

- [ ] Check if `SECRET_KEY` exists in `.env`
- [ ] If not, generate a random secret key
- [ ] Add `SECRET_KEY=your-key` to `.env`
- [ ] (Optional) Add `CRON_SECRET_KEY=your-cron-key` for separate key
- [ ] Restart your backend server
- [ ] Use the key in cron-jobs.org URLs
- [ ] Test the endpoints to verify they work

---

## Example .env File

```env
# Application Configuration
BASE_URL=https://your-app.onrender.com
SECRET_KEY=aB3xK9mP2qR7vT5wY8zA1bC4dE6fG9hI0jK2lM3nO4pQ5rS6tU7vW8xY9z

# Optional: Dedicated Cron Secret (recommended)
CRON_SECRET_KEY=xY9zA1bC4dE6fG9hI0jK2lM3nO4pQ5rS6tU7vW8xY9zA1bC4dE6f

# Firebase
FIREBASE_CREDENTIALS_PATH=kile-kitabu-firebase-adminsdk-pjk21-68cbd0c3b4.json
FIREBASE_DATABASE_URL=https://kile-kitabu-default-rtdb.firebaseio.com

# M-Pesa
MPESA_CONSUMER_KEY=...
MPESA_CONSUMER_SECRET=...
# ... etc
```

