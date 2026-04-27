# Twilio SMS OTP Setup Guide

## Overview
This guide walks you through setting up Twilio for sending OTP verification via SMS in Voyza.

## Prerequisites
- Twilio account (free trial with $15 credit)
- Verified phone number for receiving test messages
- API credentials from Twilio

## Step 1: Create Twilio Account

1. Go to [twilio.com](https://twilio.com)
2. Sign up for a free account
3. Get $15 free credit for testing
4. Complete phone verification
5. Create a project for Voyza

## Step 2: Get Phone Number

### Option A: Free Trial Number (Recommended for Testing)
1. In Twilio Console, go to **Phone Numbers → Manage Numbers**
2. Click **Get Your Twilio Phone Number**
3. Accept the suggested number or search for your preferred one
4. Click **Choose this Number**
5. Copy the phone number (format: +1234567890)

### Option B: Production Number (When Ready)
- Same steps, but you'll need to upgrade to a paid account
- No per-message cost for free tier
- Pay $1/month per number for production

## Step 3: Get API Credentials

1. Go to **Account Info** in Twilio Console
2. Copy the following:
   - **Account SID** (starts with `AC`)
   - **Auth Token** (keep this secret!)
3. You'll also need your Twilio phone number

## Step 4: Configure Environment Variables

### Local Development (.env)
```bash
TWILIO_ACCOUNT_SID=ACxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
TWILIO_AUTH_TOKEN=your_auth_token_here
TWILIO_FROM_NUMBER=+1234567890
```

### Production (Railway Dashboard)

1. Go to your Railway project
2. Select the backend service
3. Go to **Variables** tab
4. Add new variables:
   - `TWILIO_ACCOUNT_SID`: Your Account SID
   - `TWILIO_AUTH_TOKEN`: Your Auth Token
   - `TWILIO_FROM_NUMBER`: Your Twilio phone number

## Step 5: Test SMS Sending

### Local Testing

1. Update `.env` with your Twilio credentials
2. Run backend:
   ```bash
   uvicorn app.main:app --reload
   ```

3. Send a test OTP (in DEBUG mode):
   ```bash
   curl -X POST http://localhost:8000/api/v1/auth/send-otp \
     -H "Content-Type: application/json" \
     -d '{"phone": "9876543210"}'
   ```

4. Check the response - should include `sms_sent: true`
5. Check your phone for the SMS!

### Test SMS Format
```
Your Voyza login code is: 123456

Valid for 10 minutes. Do not share.
```

## Troubleshooting

### Issue: "Twilio credentials not configured"
- Check that all three Twilio variables are set
- Verify `TWILIO_ACCOUNT_SID` starts with `AC`
- Verify `TWILIO_FROM_NUMBER` is in format `+1234567890`
- Restart the backend service after adding variables

### Issue: "Invalid phone number"
- Make sure phone includes country code: `+919876543210`
- Backend automatically adds `+91` if missing
- Verify the format with Twilio docs

### Issue: SMS not received
- Check Twilio Console → Logs → SMS for delivery status
- Ensure your phone number is in Twilio's country allowlist
- Free trial accounts can only send to verified numbers
- Verify your phone is verified in Twilio account
- Check spam/junk folder

### Issue: "Permission denied"
- Verify Auth Token is exactly correct (no extra spaces)
- Account SID and Auth Token are case-sensitive
- Wait a moment for changes to propagate (up to 60 seconds)

## Pricing

### Free Trial
- $15 free credit
- Enough for ~1,000 SMS (at $0.0075 per SMS in US)
- Must be used within 30 days
- Only send to verified numbers

### Paid Account
- Starts at pay-as-you-go
- US/Canada: ~$0.0075 per outbound SMS
- International: varies by country ($0.008 - $0.10+)
- No monthly minimums
- Phone number: $1/month

## Rate Limiting Best Practices

Twilio allows:
- 1 SMS per second per Twilio number (by default)
- Configurable in Twilio settings

Voyza limits:
- 5 OTP requests per phone/email per hour (backend)
- 10 minutes per OTP validity
- OTP codes expire automatically

## Production Checklist

- [ ] Upgrade to paid account (if ready)
- [ ] Add production phone number
- [ ] Update Twilio credentials in Railway
- [ ] Test SMS delivery with real phone
- [ ] Monitor Twilio logs for failures
- [ ] Set up Twilio alerts for blocked messages
- [ ] Consider message templates for consistency
- [ ] Document phone numbers for support

## SMS Compliance

**India (Telecom Regulatory Authority)**
- Template registration recommended for compliance
- Sender ID must be alphanumeric (not just numbers)
- Keep logs of OTPs sent (Twilio handles this)

**GDPR & Privacy**
- Users can opt-out of SMS
- Store SMS consent records
- Only send to consenting users

## Twilio Account Security

1. **Protect your Auth Token:**
   - Never commit to Git (use `.env`)
   - Use Railway environment variables
   - Rotate regularly in production

2. **Phone Number Filtering:**
   - Twilio can block high-risk numbers by default
   - Configure in Twilio settings if needed

3. **Rate Limiting:**
   - Enable in Twilio console for your account
   - Prevent abuse from malicious actors

## Next Steps

After setting up SMS delivery:

1. Set up email verification (SendGrid)
2. Monitor SMS delivery metrics
3. Set up fallback channels (email if SMS fails)
4. Customize message templates per region
5. Add SMS preferences to user settings

## Additional Resources

- [Twilio Docs](https://www.twilio.com/docs)
- [SMS API Reference](https://www.twilio.com/docs/sms/send-messages)
- [Python SDK](https://www.twilio.com/docs/libraries/python)
- [SMS Best Practices](https://www.twilio.com/docs/sms/best-practices)

## Sample SMS Responses

### Successful Send
```json
{
  "message": "OTP sent successfully",
  "otp": "123456",
  "sms_sent": true
}
```

### Debug Mode Response
In DEBUG=true, OTP is returned for testing:
```json
{
  "message": "OTP sent successfully",
  "otp": "123456",
  "sms_sent": true
}
```

### Production Mode
In production, OTP is NOT returned:
```json
{
  "message": "OTP sent successfully"
}
```
