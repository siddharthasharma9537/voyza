#!/bin/bash

set -e

BASE_URL="https://api.voyzacar.online"
PHONE1="+919999999999"
PHONE2="+919999999998"
EMAIL="testuser@example.com"
PASSWORD="TestPass123!"

echo "========================================"
echo "Voyza Auth Comprehensive Test Suite"
echo "========================================"
echo ""

# ============================================================================
# TEST 1: Phone+OTP Registration Flow
# ============================================================================
echo "TEST 1: Phone+OTP Registration"
echo "─────────────────────────────"

echo "Step 1a: Send phone OTP for registration..."
REG_OTP_RESPONSE=$(curl -s -X POST \
  "$BASE_URL/api/v1/auth/register/send-phone-otp" \
  -H "Content-Type: application/json" \
  -d "{\"phone\": \"$PHONE1\"}")

echo "Response: $REG_OTP_RESPONSE"
REG_OTP=$(echo "$REG_OTP_RESPONSE" | grep -o '"otp":"[^"]*"' | cut -d'"' -f4)
if [ -z "$REG_OTP" ]; then
  echo "✗ Failed to get registration OTP"
  exit 1
fi
echo "✓ Registration OTP: $REG_OTP"
echo ""

echo "Step 1b: Verify phone OTP and create account..."
REG_VERIFY_RESPONSE=$(curl -s -X POST \
  "$BASE_URL/api/v1/auth/register/verify-phone" \
  -H "Content-Type: application/json" \
  -d "{\"phone\": \"$PHONE1\", \"otp\": \"$REG_OTP\", \"full_name\": \"Test User\", \"email\": \"testuser1@example.com\", \"role\": \"customer\"}")

echo "Response: $REG_VERIFY_RESPONSE"
if echo "$REG_VERIFY_RESPONSE" | grep -q '"id"'; then
  echo "✓ Phone registration successful"
  REG_USER_ID=$(echo "$REG_VERIFY_RESPONSE" | grep -o '"id":"[^"]*"' | cut -d'"' -f4 | head -1)
  echo "  User ID: $REG_USER_ID"
else
  echo "✗ Phone registration failed"
fi
echo ""
echo ""

# ============================================================================
# TEST 2: Phone+OTP Login Flow (with already registered user)
# ============================================================================
echo "TEST 2: Phone+OTP Login"
echo "──────────────────────"

echo "Step 2a: Send OTP for login..."
LOGIN_OTP_RESPONSE=$(curl -s -X POST \
  "$BASE_URL/api/v1/auth/send-otp" \
  -H "Content-Type: application/json" \
  -d "{\"phone\": \"$PHONE1\"}")

echo "Response: $LOGIN_OTP_RESPONSE"
LOGIN_OTP=$(echo "$LOGIN_OTP_RESPONSE" | grep -o '"otp":"[^"]*"' | cut -d'"' -f4)
if [ -z "$LOGIN_OTP" ]; then
  echo "✗ Failed to get login OTP"
  exit 1
fi
echo "✓ Login OTP: $LOGIN_OTP"
echo ""

echo "Step 2b: Verify OTP and login..."
LOGIN_RESPONSE=$(curl -s -X POST \
  "$BASE_URL/api/v1/auth/verify-otp" \
  -H "Content-Type: application/json" \
  -d "{\"phone\": \"$PHONE1\", \"otp\": \"$LOGIN_OTP\", \"purpose\": \"login\"}")

echo "Response: $LOGIN_RESPONSE"
ACCESS_TOKEN=$(echo "$LOGIN_RESPONSE" | grep -o '"access_token":"[^"]*"' | cut -d'"' -f4 | head -1)
REFRESH_TOKEN=$(echo "$LOGIN_RESPONSE" | grep -o '"refresh_token":"[^"]*"' | cut -d'"' -f4 | head -1)

if [ -n "$ACCESS_TOKEN" ]; then
  echo "✓ Phone+OTP login successful"
  echo "  Access Token: ${ACCESS_TOKEN:0:20}..."
  echo "  Refresh Token: ${REFRESH_TOKEN:0:20}..."
else
  ERROR=$(echo "$LOGIN_RESPONSE" | grep -o '"detail":"[^"]*"' | cut -d'"' -f4)
  echo "✗ Login failed: $ERROR"
fi
echo ""

# ============================================================================
# TEST 3: Get User Profile
# ============================================================================
if [ -n "$ACCESS_TOKEN" ]; then
  echo "TEST 3: Get User Profile"
  echo "────────────────────────"
  PROFILE_RESPONSE=$(curl -s -X GET \
    "$BASE_URL/api/v1/auth/me" \
    -H "Authorization: Bearer $ACCESS_TOKEN")
  
  echo "Response: $PROFILE_RESPONSE"
  if echo "$PROFILE_RESPONSE" | grep -q '"full_name"'; then
    echo "✓ Profile retrieved successfully"
  else
    echo "✗ Failed to retrieve profile"
  fi
  echo ""
fi
echo ""

# ============================================================================
# TEST 4: Email+Password Registration
# ============================================================================
echo "TEST 4: Email+Password Registration"
echo "───────────────────────────────────"

EMAIL_REG="emailuser@example.com"
REG_EMAIL_RESPONSE=$(curl -s -X POST \
  "$BASE_URL/api/v1/auth/register" \
  -H "Content-Type: application/json" \
  -d "{\"email\": \"$EMAIL_REG\", \"password\": \"$PASSWORD\", \"full_name\": \"Email User\", \"role\": \"customer\"}")

echo "Response: $REG_EMAIL_RESPONSE"
if echo "$REG_EMAIL_RESPONSE" | grep -q '"id"'; then
  echo "✓ Email+password registration successful"
else
  echo "✗ Email+password registration failed"
fi
echo ""
echo ""

# ============================================================================
# TEST 5: Email+Password Login
# ============================================================================
echo "TEST 5: Email+Password Login"
echo "────────────────────────────"

EMAIL_LOGIN_RESPONSE=$(curl -s -X POST \
  "$BASE_URL/api/v1/auth/login" \
  -H "Content-Type: application/json" \
  -d "{\"email\": \"$EMAIL_REG\", \"password\": \"$PASSWORD\"}")

echo "Response: $EMAIL_LOGIN_RESPONSE"
EMAIL_ACCESS_TOKEN=$(echo "$EMAIL_LOGIN_RESPONSE" | grep -o '"access_token":"[^"]*"' | cut -d'"' -f4 | head -1)
EMAIL_REFRESH_TOKEN=$(echo "$EMAIL_LOGIN_RESPONSE" | grep -o '"refresh_token":"[^"]*"' | cut -d'"' -f4 | head -1)

if [ -n "$EMAIL_ACCESS_TOKEN" ]; then
  echo "✓ Email+password login successful"
  echo "  Access Token: ${EMAIL_ACCESS_TOKEN:0:20}..."
else
  echo "✗ Email+password login failed"
fi
echo ""
echo ""

# ============================================================================
# TEST 6: Token Refresh
# ============================================================================
if [ -n "$REFRESH_TOKEN" ]; then
  echo "TEST 6: Token Refresh"
  echo "────────────────────"
  REFRESH_RESPONSE=$(curl -s -X POST \
    "$BASE_URL/api/v1/auth/refresh" \
    -H "Content-Type: application/json" \
    -d "{\"refresh_token\": \"$REFRESH_TOKEN\"}")
  
  echo "Response: $REFRESH_RESPONSE"
  NEW_ACCESS_TOKEN=$(echo "$REFRESH_RESPONSE" | grep -o '"access_token":"[^"]*"' | cut -d'"' -f4 | head -1)
  
  if [ -n "$NEW_ACCESS_TOKEN" ]; then
    echo "✓ Token refresh successful"
    echo "  New Access Token: ${NEW_ACCESS_TOKEN:0:20}..."
  else
    echo "✗ Token refresh failed"
  fi
  echo ""
fi

echo "========================================"
echo "All Tests Complete"
echo "========================================"
