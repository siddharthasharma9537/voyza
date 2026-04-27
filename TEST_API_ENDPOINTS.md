# Test API Endpoints - Google OAuth + Authentication

Complete curl commands to test all login/registration methods.

## 🔧 Prerequisites

```bash
export API_URL="https://api.voyzacar.online/api/v1"
```

---

## 📋 Test 1: Phone + OTP Registration

### 1a. Send Phone OTP for Registration
```bash
curl -X POST "$API_URL/auth/register/send-phone-otp" \
  -H "Content-Type: application/json" \
  -d '{"phone":"9876543210"}'
```

**Response (dev mode shows OTP):**
```json
{
  "message": "OTP sent successfully to phone",
  "otp": "123456"
}
```

### 1b. Verify Phone OTP & Create Account
```bash
curl -X POST "$API_URL/auth/register/verify-phone" \
  -H "Content-Type: application/json" \
  -d '{
    "phone": "9876543210",
    "otp": "123456",
    "full_name": "John Doe",
    "email": "john@example.com",
    "role": "customer"
  }'
```

**Response:**
```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "full_name": "John Doe",
  "email": "john@example.com",
  "phone": "+919876543210",
  "role": "customer",
  "is_verified": true,
  "email_verified": false,
  "oauth_provider": "phone",
  "avatar_url": null
}
```

---

## 🔑 Test 2: Phone + OTP Login

### 2a. Send OTP for Login
```bash
curl -X POST "$API_URL/auth/send-otp" \
  -H "Content-Type: application/json" \
  -d '{"phone":"9876543210"}'
```

### 2b. Verify OTP & Get Tokens
```bash
curl -X POST "$API_URL/auth/verify-otp" \
  -H "Content-Type: application/json" \
  -d '{
    "phone": "9876543210",
    "otp": "123456",
    "purpose": "login"
  }'
```

**Response:**
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer",
  "expires_in": 1800
}
```

---

## 📧 Test 3: Email + Password Login

### 3a. First Set a Password
You need a user with a password. Either:

**Option A:** Register with phone and then use phone+password login
```bash
curl -X POST "$API_URL/auth/login" \
  -H "Content-Type: application/json" \
  -d '{
    "phone": "9876543210",
    "password": "SecurePass123!"
  }'
```

**Option B:** Or use email+password if you've set a password for that user
```bash
curl -X POST "$API_URL/auth/login" \
  -H "Content-Type: application/json" \
  -d '{
    "email": "john@example.com",
    "password": "SecurePass123!"
  }'
```

**Response:**
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer",
  "expires_in": 1800
}
```

---

## 🌐 Test 4: Google OAuth Flow

### 4a. Get Google Authorization Code
```
Go to browser (replace CLIENT_ID with your Google Client ID):
https://accounts.google.com/o/oauth2/v2/auth?client_id=CLIENT_ID&redirect_uri=https%3A%2F%2Fapi.voyzacar.online%2Fapi%2Fv1%2Fauth%2Foauth%2Fgoogle%2Fcallback&response_type=code&scope=openid%20email%20profile
```

This will redirect back with: `?code=AUTHORIZATION_CODE`

Copy the code.

### 4b. Exchange Code for OAuth Token
```bash
curl -X GET "$API_URL/auth/oauth/google/callback?code=AUTHORIZATION_CODE"
```

Replace `AUTHORIZATION_CODE` with the actual code.

**Response:**
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer",
  "expires_in": 1800,
  "message": "Phone verification required to complete signup"
}
```

Store this `access_token` for the next steps.

### 4c. Send Phone OTP for OAuth Phone Linking
```bash
curl -X POST "$API_URL/auth/send-otp" \
  -H "Content-Type: application/json" \
  -d '{"phone":"9876543210"}'
```

### 4d. Link Phone to Google Account
```bash
curl -X POST "$API_URL/auth/oauth/link-phone" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_OAUTH_ACCESS_TOKEN" \
  -d '{
    "phone": "9876543210",
    "otp": "123456"
  }'
```

Replace `YOUR_OAUTH_ACCESS_TOKEN` with the token from step 4b.

**Response:**
```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "full_name": "John Doe",
  "email": "john@example.com",
  "phone": "+919876543210",
  "role": "customer",
  "is_verified": true,
  "oauth_provider": "google"
}
```

### 4e. Set Password for Google User
```bash
curl -X POST "$API_URL/auth/oauth/set-password" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_OAUTH_ACCESS_TOKEN" \
  -d '{
    "password": "SecurePass123!"
  }'
```

**Response:**
```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "full_name": "John Doe",
  "email": "john@example.com",
  "phone": "+919876543210",
  "role": "customer",
  "is_verified": true,
  "oauth_provider": "google"
}
```

✅ Google OAuth account setup complete!

---

## 🔄 Test 5: Token Refresh

```bash
curl -X POST "$API_URL/auth/refresh" \
  -H "Content-Type: application/json" \
  -d '{
    "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
  }'
```

**Response:**
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer",
  "expires_in": 1800
}
```

---

## 👤 Test 6: Get Current User Profile

```bash
curl -X GET "$API_URL/auth/me" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN"
```

Replace `YOUR_ACCESS_TOKEN` with the access token from login/registration.

**Response:**
```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "full_name": "John Doe",
  "email": "john@example.com",
  "phone": "+919876543210",
  "role": "customer",
  "is_verified": true,
  "avatar_url": null
}
```

---

## 🚪 Test 7: Logout

```bash
curl -X POST "$API_URL/auth/logout" \
  -H "Content-Type: application/json" \
  -d '{
    "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
  }'
```

**Response:** `204 No Content`

---

## 📧 Test 8: Email Verification (Optional)

### 8a. Send Email OTP
```bash
curl -X POST "$API_URL/auth/register/send-email-otp" \
  -H "Content-Type: application/json" \
  -d '{"email":"john@example.com"}'
```

### 8b. Verify Email OTP
```bash
curl -X POST "$API_URL/auth/register/verify-email" \
  -H "Content-Type: application/json" \
  -d '{
    "email": "john@example.com",
    "otp": "123456"
  }'
```

---

## ✅ Complete Test Sequence

```bash
# 1. Register with phone
curl -X POST "$API_URL/auth/register/send-phone-otp" \
  -H "Content-Type: application/json" \
  -d '{"phone":"9876543210"}'

# (Copy OTP from response if in dev mode)

# 2. Verify phone and create account
curl -X POST "$API_URL/auth/register/verify-phone" \
  -H "Content-Type: application/json" \
  -d '{
    "phone": "9876543210",
    "otp": "123456",
    "full_name": "Test User",
    "email": "test@example.com",
    "role": "customer"
  }'

# 3. Login with phone+OTP
curl -X POST "$API_URL/auth/send-otp" \
  -H "Content-Type: application/json" \
  -d '{"phone":"9876543210"}'

curl -X POST "$API_URL/auth/verify-otp" \
  -H "Content-Type: application/json" \
  -d '{"phone": "9876543210", "otp": "123456", "purpose": "login"}'

# 4. Get user profile
curl -X GET "$API_URL/auth/me" \
  -H "Authorization: Bearer ACCESS_TOKEN"

# 5. Logout
curl -X POST "$API_URL/auth/logout" \
  -H "Content-Type: application/json" \
  -d '{"refresh_token": "REFRESH_TOKEN"}'
```

---

## 🐛 Troubleshooting

**"password authentication failed"**
- Make sure POSTGRES_USER and POSTGRES_DB are set on Railway
- Check Railway variables for voyza service

**"Invalid or expired OTP"**
- OTP expires after 10 minutes
- In production mode (DEBUG=false), OTP is not returned in response

**"Email already registered"**
- User already exists with that email
- Use different email or reset account

**"Phone number already registered"**
- Phone is unique per user
- Use different phone number

---

Done! You can now test all authentication methods. 🎉
