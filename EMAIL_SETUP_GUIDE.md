# 📧 Email Notification Setup Guide

**For:** Dr. April Crenshaw
**Purpose:** Activate email notifications for Math 1710 AI Tutor problem reports

---

## ✅ Already Configured

Your email address is already set in `config.py`:
- **Your Email:** april.crenshaw@chattanoogastate.edu
- **SMTP Server:** Gmail (smtp.gmail.com)
- **Reports sent to:** april.crenshaw@chattanoogastate.edu

## 🔑 What You Need to Do: Create Gmail App Password

**⚠️ IMPORTANT:** Do NOT use your regular Gmail password. You need an "App Password."

### Step 1: Enable 2-Step Verification (if not already enabled)

1. Go to your Google Account: https://myaccount.google.com/
2. Click **Security** in the left sidebar
3. Under "How you sign in to Google," click **2-Step Verification**
4. Follow the prompts to set it up (you'll need your phone)

### Step 2: Create App Password

1. Go to: https://myaccount.google.com/apppasswords
   - Or: Google Account → Security → 2-Step Verification → App passwords (at bottom)

2. You'll be asked to sign in again

3. Under "Select app," choose **Mail**

4. Under "Select device," choose **Other (Custom name)**
   - Type: `MATH 1710 Tutor`

5. Click **GENERATE**

6. Google will show you a 16-character password like: `abcd efgh ijkl mnop`

7. **COPY THIS PASSWORD** (you won't see it again!)

### Step 3: Add Password to config.py

1. Open `config.py` in a text editor

2. Find the EMAIL_SETTINGS section (around line 420)

3. Replace the empty password:
   ```python
   "smtp_password": "",  # TODO: Add your Gmail app-specific password here
   ```

   With your generated password:
   ```python
   "smtp_password": "abcdefghijklmnop",  # App password from Google
   ```
   ⚠️ **Remove spaces** from the password when pasting!

4. Save the file

### Step 4: Restart Your Server

```bash
# Stop your current server (Ctrl+C)
# Then restart it
python app_updated.py
```

You should see:
```
[EMAIL] Service initialized successfully
```

---

## 🧪 Test the Email System

### Test 1: Send a Test Alert

```bash
cd /path/to/STEMConference25
python email_service.py
```

This will send test emails to april.crenshaw@chattanoogastate.edu

### Test 2: Report a Problem from Student Interface

1. Open the tutor interface
2. Click "Report Issue"
3. Select "Math appears incorrect"
4. Submit the report
5. Check your email - you should get an immediate alert! 🚨

---

## 📧 What Emails You'll Receive

### **Immediate Alerts** (Critical Issues)
Sent instantly when students report:
- ✅ Math errors
- ✅ Accessibility issues

**Subject:** `🚨 MATH ERROR - MATH 1710 Tutor Report`

### **Weekly Digest** (Non-Critical Issues)
Sent every Friday with:
- Unclear explanations
- UI/button bugs
- Other feedback

**Subject:** `📊 MATH 1710 Tutor - Weekly Report (Date Range)`

---

## 🔧 Alternative: Use Chattanooga State Email Server

If you prefer to use Chattanooga State's email server instead of Gmail:

1. Contact Chattanooga State IT and ask for:
   - SMTP server hostname (e.g., `smtp.chattanoogastate.edu`)
   - SMTP port (usually 587 or 465)
   - Authentication method

2. Update `config.py`:
   ```python
   "smtp_host": "smtp.chattanoogastate.edu",  # From IT
   "smtp_port": 587,  # From IT
   "smtp_user": "april.crenshaw@chattanoogastate.edu",
   "smtp_password": "your-institutional-password",
   ```

---

## ❓ Troubleshooting

### "Authentication failed" error
- **Problem:** Wrong password
- **Solution:** Generate a new App Password and update config.py

### "SMTP connection failed" error
- **Problem:** Gmail blocking sign-in
- **Solution:** Make sure 2-Step Verification is enabled and you're using an App Password (not regular password)

### No emails received
- **Check spam folder** - first email might go to spam
- **Verify email in config.py** - make sure it's spelled correctly
- **Check server logs** - look for `[EMAIL]` messages

### "Less secure app access" message
- **Problem:** Old Gmail setting
- **Solution:** You don't need this anymore - just use App Passwords instead

---

## 📞 Need Help?

If you have issues:
1. Check the server console for `[EMAIL ERROR]` messages
2. Verify your App Password is correct (no spaces)
3. Make sure 2-Step Verification is enabled on your Google Account

---

## ✅ Checklist

- [ ] 2-Step Verification enabled on Google Account
- [ ] App Password generated
- [ ] Password added to `config.py` (no spaces)
- [ ] Server restarted
- [ ] Test email received
- [ ] Ready to use!

---

**Once set up, the system runs automatically:**
- Critical issues → Instant email
- Non-critical issues → Queued for Friday digest
- No manual intervention needed!
