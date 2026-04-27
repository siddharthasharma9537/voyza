# Railway Deployment Guide - With SendGrid Email OTP

## Current Status
✅ All code committed and pushed to GitHub  
✅ Backend ready for deployment  
✅ Frontend ready for deployment  
✅ SendGrid email OTP integrated  
⏸️ Twilio SMS (optional, can add later)

---

## Step 1: Get SendGrid API Key (2 minutes)

### Create Free SendGrid Account
1. Go to [sendgrid.com](https://sendgrid.com)
2. Sign up for free (25,000 emails/month)
3. Verify your email
4. Go to **Settings → API Keys**
5. Click **Create API Key**
6. Name it: `Voyza Backend`
7. Select **Mail Send** permission
8. **Copy the key** (you won't see it again)

### Verify Sender Email
1. Go to **Senders** in SendGrid
2. Create sender: `noreply@voyzacar.online`
3. Verify the email (check inbox)

---

## Step 2: Deploy to Railway (3 minutes)

### 2a. Go to Railway Dashboard
1. Open [railway.app](https://railway.app)
2. Select your Voyza backend project
3. Click on the **backend** service

### 2b. Add Environment Variables
1. Go to **Variables** tab
2. Add these variables:

```
SENDGRID_API_KEY=SG.your_api_key_here
EMAILS_FROM_EMAIL=noreply@voyzacar.online
EMAILS_FROM_NAME=Voyza
```

Replace `SG.your_api_key_here` with your actual SendGrid key.

### 2c. Deploy
1. Railway **auto-deploys** when you add variables
2. Wait for deployment to complete (2-3 minutes)
3. Check build logs for any errors

---

## Step 3: Verify Deployment (2 minutes)

### Test Health Check
```bash
curl https://api.voyzacar.online/health
# Expected: {"status":"ok","version":"1.0.0"}
```

### Test Email OTP
```bash
curl -X POST https://api.voyzacar.online/api/v1/auth/register/send-email-otp \
  -H "Content-Type: application/json" \
  -d '{"email": "your-test@gmail.com"}'
```

Check your email for the OTP code!

---

## Step 4: Test All Auth Flows (5 minutes)

Run the comprehensive test script:

```bash
API_URL=https://api.voyzacar.online/api/v1 bash test_all_auth_flows.sh
```

Tests:
- ✅ Phone registration with OTP
- ✅ Email + password registration
- ✅ Phone + OTP login
- ✅ Email + password login
- ✅ Token refresh
- ✅ Logout
- ✅ User profile fetch

---

## Frontend Deployment (Optional)

### Update Frontend Environment
1. Go to frontend service in Railway
2. Update variables:

```
NEXT_PUBLIC_API_URL=https://api.voyzacar.online/api/v1
NEXT_PUBLIC_GOOGLE_CLIENT_ID=<your_google_client_id>
```

3. Railway auto-deploys

---

## What's Now Live

### ✅ Working Features
- Phone registration with OTP verification
- Email + password registration
- Email optional field during signup
- Phone + OTP login
- Phone + password login
- Email + password login
- Google OAuth infrastructure (ready for Client ID)
- Token refresh mechanism
- Logout with token revocation
- Real email delivery via SendGrid

### 📧 Email OTP Flow
1. User enters email during registration
2. System sends OTP via SendGrid (real email)
3. User verifies OTP
4. Email marked as verified
5. Can use for password reset later

### 🔄 Email in Login
If user has email on file:
- OTP sent to both phone (SMS ready) and email
- Provides backup channel if phone unavailable

---

## Troubleshooting

### Email Not Received?
1. Check spam/junk folder
2. Verify sender email is verified in SendGrid
3. Check SendGrid dashboard → Activity Feed
4. Ensure DEBUG=false in production

### Health Check Fails?
1. Wait 5 minutes for deployment
2. Check Railway logs: **Logs** tab
3. Verify SENDGRID_API_KEY is set correctly

### OTP Endpoint Returns Error?
1. Verify `SENDGRID_API_KEY` starts with `SG.`
2. Verify `EMAILS_FROM_EMAIL` matches verified sender
3. Restart Railway service (redeploy)

---

## Next Steps

### Immediate
- [ ] Test all auth flows
- [ ] Verify emails arrive
- [ ] Test frontend registration
- [ ] Test frontend login

### Soon (When Ready)
- [ ] Add Twilio SMS ($15 free trial)
- [ ] Update frontend with Google OAuth Client ID
- [ ] Test OAuth flows
- [ ] Set up password reset flow

### Future
- [ ] Apple OAuth
- [ ] Facebook OAuth
- [ ] Email verification templates
- [ ] SMS templates for Twilio

---

## Environment Variables Reference

```bash
# ─────── SendGrid (Required for Email OTP) ─────────
SENDGRID_API_KEY=SG.your_key_here          # Email delivery
EMAILS_FROM_EMAIL=noreply@voyzacar.online  # Sender email
EMAILS_FROM_NAME=Voyza                     # Sender name

# ─────── Database (Auto-set by Railway) ───────────
POSTGRES_SERVER=postgres.railway.internal
POSTGRES_DB=railway
POSTGRES_USER=postgres
POSTGRES_PASSWORD=(auto-set)
POSTGRES_PORT=5432

# ─────── API Config ──────────────────────────────
DEBUG=false                    # Production
ENVIRONMENT=production
APP_NAME=Voyza API
API_V1_PREFIX=/api/v1
RATE_LIMIT_PER_MINUTE=60

# ─────── Optional (Add Later) ────────────────────
TWILIO_ACCOUNT_SID=           # SMS OTP (future)
TWILIO_AUTH_TOKEN=            # SMS OTP (future)
TWILIO_FROM_NUMBER=           # SMS OTP (future)
GOOGLE_CLIENT_ID=             # OAuth (future)
GOOGLE_CLIENT_SECRET=         # OAuth (future)
```

---

## Support

**Issues?** Check:
1. Railway deployment logs
2. SendGrid activity feed (email status)
3. Backend error logs in Railway
4. Test endpoints with curl (see Step 3)

**Still stuck?** Refer to:
- [SendGrid Setup Guide](./backend/SENDGRID_SETUP.md)
- [Twilio Setup Guide](./backend/TWILIO_SETUP.md) (for later)
- Test scripts: `test_all_auth_flows.sh`

---

## Success Checklist

- [ ] SendGrid API key added to Railway
- [ ] Backend deployment completed
- [ ] Health check passes
- [ ] Email OTP test successful
- [ ] All auth flows tested
- [ ] Frontend connected to backend
- [ ] Registration works end-to-end
- [ ] Login works end-to-end

🎉 **Once all checked: System is production-ready!**
