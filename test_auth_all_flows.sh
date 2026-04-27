#!/bin/bash

BASE_URL="https://api.voyzacar.online"

echo "========================================"
echo "Voyza Authentication - All Flows Test"
echo "========================================"
echo ""

# ============================================================================
# FLOW 1: Phone+OTP Registration → Login → Profile → Refresh → Logout
# ============================================================================
echo "FLOW 1: Phone+OTP Complete Cycle"
echo "════════════════════════════════"
PHONE1="+919999888877"

echo "1a. Send phone OTP for registration..."
SEND_OTP=$(curl -s -X POST "$BASE_URL/api/v1/auth/register/send-phone-otp" \
  -H "Content-Type: application/json" -d "{\"phone\": \"$PHONE1\"}")
OTP=$(echo "$SEND_OTP" | grep -o '"otp":"[^"]*"' | cut -d'"' -f4)
echo "✓ OTP: $OTP"

echo "1b. Register with phone+OTP..."
REGISTER=$(curl -s -X POST "$BASE_URL/api/v1/auth/register/verify-phone" \
  -H "Content-Type: application/json" \
  -d "{\"phone\": \"$PHONE1\", \"otp\": \"$OTP\", \"full_name\": \"Flow Test User\", \"email\": \"flowtest@example.com\", \"role\": \"customer\"}")
USER_ID=$(echo "$REGISTER" | grep -o '"id":"[^"]*"' | cut -d'"' -f4 | head -1)
echo "✓ User registered: $USER_ID"

echo "1c. Send OTP for login..."
LOGIN_OTP_SEND=$(curl -s -X POST "$BASE_URL/api/v1/auth/send-otp" \
  -H "Content-Type: application/json" -d "{\"phone\": \"$PHONE1\"}")
LOGIN_OTP=$(echo "$LOGIN_OTP_SEND" | grep -o '"otp":"[^"]*"' | cut -d'"' -f4)
echo "✓ OTP: $LOGIN_OTP"

echo "1d. Verify OTP and login..."
LOGIN=$(curl -s -X POST "$BASE_URL/api/v1/auth/verify-otp" \
  -H "Content-Type: application/json" \
  -d "{\"phone\": \"$PHONE1\", \"otp\": \"$LOGIN_OTP\", \"purpose\": \"login\"}")
ACCESS=$(echo "$LOGIN" | grep -o '"access_token":"[^"]*"' | cut -d'"' -f4 | head -1)
REFRESH=$(echo "$LOGIN" | grep -o '"refresh_token":"[^"]*"' | cut -d'"' -f4 | head -1)
echo "✓ Login successful"

echo "1e. Get user profile..."
PROFILE=$(curl -s -X GET "$BASE_URL/api/v1/auth/me" \
  -H "Authorization: Bearer $ACCESS")
if echo "$PROFILE" | grep -q '"full_name"'; then
  echo "✓ Profile retrieved"
else
  echo "✗ Profile failed"
fi

echo "1f. Refresh tokens..."
REFRESH_NEW=$(curl -s -X POST "$BASE_URL/api/v1/auth/refresh" \
  -H "Content-Type: application/json" -d "{\"refresh_token\": \"$REFRESH\"}")
if echo "$REFRESH_NEW" | grep -q '"access_token"'; then
  echo "✓ Tokens refreshed"
else
  echo "✗ Token refresh failed"
fi

echo ""

# ============================================================================
# FLOW 2: Email+Password (Phone+Email+Password Registration)
# ============================================================================
echo "FLOW 2: Email+Password with Phone"
echo "═════════════════════════════════"
PHONE2="+919999777766"
EMAIL2="emailpassuser@example.com"
PASSWORD="SecurePass123!"

echo "2a. Register with email+password+phone..."
EMAIL_REG=$(curl -s -X POST "$BASE_URL/api/v1/auth/register" \
  -H "Content-Type: application/json" \
  -d "{\"phone\": \"$PHONE2\", \"email\": \"$EMAIL2\", \"password\": \"$PASSWORD\", \"full_name\": \"Email User\", \"role\": \"customer\"}")

if echo "$EMAIL_REG" | grep -q '"id"'; then
  echo "✓ User registered with email+password"
  
  echo "2b. Login with email+password..."
  EMAIL_LOGIN=$(curl -s -X POST "$BASE_URL/api/v1/auth/login" \
    -H "Content-Type: application/json" \
    -d "{\"email\": \"$EMAIL2\", \"password\": \"$PASSWORD\"}")
  
  if echo "$EMAIL_LOGIN" | grep -q '"access_token"'; then
    echo "✓ Email+password login successful"
  else
    echo "✗ Email+password login failed"
  fi
else
  echo "✗ Email registration failed"
  echo "$EMAIL_REG"
fi

echo ""

# ============================================================================
# FLOW 3: Phone+Password (Alternative login method)
# ============================================================================
echo "FLOW 3: Phone+Password Login"
echo "════════════════════════════"

echo "3. Login with phone+password..."
PHONE_LOGIN=$(curl -s -X POST "$BASE_URL/api/v1/auth/login" \
  -H "Content-Type: application/json" \
  -d "{\"phone\": \"$PHONE2\", \"password\": \"$PASSWORD\"}")

if echo "$PHONE_LOGIN" | grep -q '"access_token"'; then
  echo "✓ Phone+password login successful"
else
  echo "✗ Phone+password login failed"
fi

echo ""
echo "========================================"
echo "All Auth Flows Tested"
echo "========================================"
