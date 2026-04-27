# SendGrid Email Verification Setup

## Overview
This guide walks you through setting up SendGrid for sending OTP verification emails in Voyza.

## Prerequisites
- SendGrid account (free tier available)
- API Key from SendGrid
- Verified sender email domain

## Step 1: Create SendGrid Account

1. Go to [sendgrid.com](https://sendgrid.com)
2. Sign up for a free account (25,000 emails/month)
3. Verify your email address
4. Complete the account setup wizard

## Step 2: Create and Verify Sender Email

### Option A: Use a Domain (Recommended for Production)

1. In SendGrid Dashboard, go to **Settings → Sender Authentication**
2. Click **Create New Domain**
3. Enter your domain (e.g., `voyza.app`)
4. Add the DNS records provided by SendGrid to your domain provider:
   - CNAME record for authentication
   - CNAME record for click tracking
5. Verify the domain (can take 24-48 hours)
6. Use email format: `noreply@voyza.app`

### Option B: Use Single Sender (Quick for Testing)

1. Go to **Senders** in SendGrid Dashboard
2. Create a new sender with email: `noreply@voyzacar.online`
3. Verify the email address (check your inbox)
4. Once verified, you can use it

## Step 3: Create API Key

1. In SendGrid Dashboard, go to **Settings → API Keys**
2. Click **Create API Key**
3. Name: `Voyza Backend`
4. Permissions: Select "Mail Send" (minimum required)
5. Copy the API key (you won't see it again)

## Step 4: Configure Environment Variables

### Local Development (.env)
```bash
SENDGRID_API_KEY=SG.your_api_key_here
EMAILS_FROM_EMAIL=noreply@yourdomain.com
EMAILS_FROM_NAME=Voyza
```

### Production (Railway Dashboard)

1. Go to your Railway project
2. Select the backend service
3. Go to **Variables** tab
4. Add new variables:
   - `SENDGRID_API_KEY`: Paste your API key
   - `EMAILS_FROM_EMAIL`: Your verified sender email
   - `EMAILS_FROM_NAME`: Voyza

## Step 5: Test Email Sending

1. In DEBUG mode, trigger an email OTP:
   ```bash
   curl -X POST http://localhost:8000/api/v1/auth/register/send-email-otp \
     -H "Content-Type: application/json" \
     -d '{"email": "your-test@gmail.com"}'
   ```

2. Check the response - if `email_sent: true`, the email was sent

3. Check your email inbox for the OTP code

## Troubleshooting

### Issue: "SendGrid API key not configured"
- Check that `SENDGRID_API_KEY` is set in environment variables
- Verify the API key is correct (should start with `SG.`)
- Restart the backend service after adding the key

### Issue: Email not received
- Check spam/junk folder
- Verify sender email is correctly configured in SendGrid
- Check SendGrid dashboard → Activity Feed for delivery status
- Ensure your email domain/sender is verified

### Issue: "Invalid sender email"
- Make sure `EMAILS_FROM_EMAIL` matches a verified sender in SendGrid
- Wait 24-48 hours if you just added a domain

### Rate Limiting
- Free tier: 25,000 emails/month (~800/day)
- OTP codes expire in 10 minutes
- Limit OTP requests to 5 per phone/email per hour (configured in backend)

## Email Templates

The email service automatically sends formatted emails with:
- **Email Verification OTP**: Used when verifying email during registration
- **Login OTP**: Used when logging in via OTP
- **Welcome Email**: Sent after successful registration

All emails include:
- Brand styling (Voyza logo colors)
- Clear instructions
- Expiration time
- Security notice

## Production Checklist

- [ ] Domain verified in SendGrid
- [ ] API Key generated and secure
- [ ] `SENDGRID_API_KEY` added to Railway variables
- [ ] `EMAILS_FROM_EMAIL` set to verified domain
- [ ] Test email sending before going live
- [ ] Monitor SendGrid dashboard for delivery issues
- [ ] Set up email authentication (SPF/DKIM) for better deliverability

## Cost

- **Free Tier**: 25,000 emails/month
- **Paid Plans**: Starting from $19.95/month for higher volumes
- No setup fees
- Pay-as-you-go overage fees available

## Additional Resources

- [SendGrid Docs](https://docs.sendgrid.com)
- [API Reference](https://docs.sendgrid.com/api-reference/mail-send/mail-send)
- [Python SDK](https://github.com/sendgrid/sendgrid-python)

## Next Steps

After setting up email verification:

1. Set up SMS via Twilio for phone OTP (optional but recommended)
2. Customize email templates with your branding
3. Monitor email delivery metrics in SendGrid dashboard
4. Set up bounce/complaint handling
