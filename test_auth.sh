#!/bin/bash

set -e

BASE_URL="https://api.voyzacar.online"
PHONE="+919999999999"
EMAIL="testuser@example.com"
PASSWORD="TestPass123!"

echo "======================================"
echo "Testing Voyza Authentication Flows"
echo "======================================"
echo ""

# Test 1: Send OTP to phone
echo "1. Testing Phone OTP Send..."
OTP_RESPONSE=$(curl -s -X POST \
  "$BASE_URL/api/v1/auth/send-otp" \
  -H "Content-Type: application/json" \
  -d "{\"phone\": \"$PHONE\"}")

echo "Response: $OTP_RESPONSE"
echo ""

# Extract OTP from response (DEBUG=true includes it)
OTP=$(echo "$OTP_RESPONSE" | grep -o '"otp":"[^"]*"' | cut -d'"' -f4)
if [ -z "$OTP" ]; then
  echo "✗ OTP not returned in response"
  exit 1
else
  echo "✓ OTP received in response: $OTP"
fi
echo ""

# Test 2: Verify OTP (correct field name: "otp" not "code")
echo "2. Testing Phone OTP Verification..."
VERIFY_RESPONSE=$(curl -s -X POST \
  "$BASE_URL/api/v1/auth/verify-otp" \
  -H "Content-Type: application/json" \
  -d "{\"phone\": \"$PHONE\", \"otp\": \"$OTP\"}")

echo "Response: $VERIFY_RESPONSE"
echo ""

# Extract tokens if successful
ACCESS_TOKEN=$(echo "$VERIFY_RESPONSE" | grep -o '"access_token":"[^"]*"' | cut -d'"' -f4 | head -1)
REFRESH_TOKEN=$(echo "$VERIFY_RESPONSE" | grep -o '"refresh_token":"[^"]*"' | cut -d'"' -f4 | head -1)

if [ -n "$ACCESS_TOKEN" ]; then
  echo "✓ OTP verification successful"
  echo "  Access Token: ${ACCESS_TOKEN:0:20}..."
  echo "  Refresh Token: ${REFRESH_TOKEN:0:20}..."
  echo ""
  
  # Test 3: Get user profile
  echo "3. Testing Get User Profile..."
  PROFILE_RESPONSE=$(curl -s -X GET \
    "$BASE_URL/api/v1/auth/profile" \
    -H "Authorization: Bearer $ACCESS_TOKEN")
  
  echo "Response: $PROFILE_RESPONSE"
  echo ""
  
  # Test 4: Refresh token
  echo "4. Testing Token Refresh..."
  REFRESH_RESPONSE=$(curl -s -X POST \
    "$BASE_URL/api/v1/auth/refresh" \
    -H "Content-Type: application/json" \
    -d "{\"refresh_token\": \"$REFRESH_TOKEN\"}")
  
  echo "Response: $REFRESH_RESPONSE"
  echo ""
  
  # Test 5: Logout
  echo "5. Testing Logout..."
  LOGOUT_RESPONSE=$(curl -s -X POST \
    "$BASE_URL/api/v1/auth/logout" \
    -H "Authorization: Bearer $ACCESS_TOKEN")
  
  echo "Response: $LOGOUT_RESPONSE"
  echo ""
else
  ERROR=$(echo "$VERIFY_RESPONSE" | grep -o '"detail":"[^"]*"' | cut -d'"' -f4)
  echo "✗ OTP verification failed: $ERROR"
fi

# Test 6: Email+Password Login
echo "6. Testing Email+Password Login..."
LOGIN_RESPONSE=$(curl -s -X POST \
  "$BASE_URL/api/v1/auth/login" \
  -H "Content-Type: application/json" \
  -d "{\"email\": \"$EMAIL\", \"password\": \"$PASSWORD\"}")

echo "Response: $LOGIN_RESPONSE"
echo ""

echo "======================================"
echo "Tests Complete"
echo "======================================"
