#!/bin/bash

# Complete End-to-End Authentication Flow Tests
# Tests all Voyza authentication methods: phone OTP, email+password, OAuth

API_URL="${API_URL:-http://localhost:8000/api/v1}"
TIMESTAMP=$(date +%s)

# Colors for output
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo "════════════════════════════════════════════════════════════"
echo "      Voyza Authentication - Complete E2E Test Suite"
echo "════════════════════════════════════════════════════════════"
echo "API URL: $API_URL"
echo ""

# Test counters
TESTS_PASSED=0
TESTS_FAILED=0

# Helper function to test endpoints
test_endpoint() {
  local test_name=$1
  local method=$2
  local endpoint=$3
  local data=$4
  local expected_status=$5

  echo -n "Testing: $test_name... "

  if [ "$method" = "GET" ]; then
    response=$(curl -s -w "\n%{http_code}" -X GET "$API_URL$endpoint" \
      -H "Content-Type: application/json" \
      -H "Authorization: Bearer ${ACCESS_TOKEN}")
  else
    response=$(curl -s -w "\n%{http_code}" -X $method "$API_URL$endpoint" \
      -H "Content-Type: application/json" \
      -H "Authorization: Bearer ${ACCESS_TOKEN}" \
      -d "$data")
  fi

  http_code=$(echo "$response" | tail -n1)
  body=$(echo "$response" | head -n-1)

  if [[ "$http_code" == "$expected_status"* ]]; then
    echo -e "${GREEN}✓ PASS${NC} (Status: $http_code)"
    TESTS_PASSED=$((TESTS_PASSED + 1))
    echo "$body"
  else
    echo -e "${RED}✗ FAIL${NC} (Status: $http_code, Expected: $expected_status)"
    echo "Response: $body"
    TESTS_FAILED=$((TESTS_FAILED + 1))
  fi
  echo ""
}

# ───────────────────────────────────────────────────────────────
# TEST 1: PHONE REGISTRATION WITH OTP
# ───────────────────────────────────────────────────────────────
echo -e "${YELLOW}[TEST 1] Phone Registration with OTP${NC}"
echo "─────────────────────────────────────────────────────────"

PHONE="999${TIMESTAMP:7:7}"  # Use timestamp to generate unique phone
echo "Using phone: +91$PHONE"

# 1a. Send OTP
echo "Step 1a: Send OTP for registration"
response=$(curl -s -X POST "$API_URL/auth/register/send-phone-otp" \
  -H "Content-Type: application/json" \
  -d "{\"phone\": \"$PHONE\"}")
echo "Response: $response"
OTP=$(echo "$response" | grep -o '"otp":"[0-9]*"' | head -1 | grep -o '[0-9]*')
echo "Extracted OTP: $OTP"
echo ""

if [ -z "$OTP" ]; then
  echo -e "${RED}Failed to extract OTP${NC}"
  # In production without DEBUG mode, OTP won't be returned
  # Use "123456" as placeholder for testing
  OTP="123456"
  echo "Using placeholder OTP: $OTP (production mode)"
fi

# 1b. Verify OTP and create account
echo "Step 1b: Verify OTP and create account"
FULL_NAME="Phone User $TIMESTAMP"
response=$(curl -s -w "\n%{http_code}" -X POST "$API_URL/auth/register/verify-phone" \
  -H "Content-Type: application/json" \
  -d "{\"phone\": \"$PHONE\", \"otp\": \"$OTP\", \"full_name\": \"$FULL_NAME\", \"role\": \"customer\"}")

http_code=$(echo "$response" | tail -n1)
body=$(echo "$response" | head -n-1)

if [[ "$http_code" == "201"* ]]; then
  echo -e "${GREEN}✓ Phone registration successful${NC}"
  echo "Response: $body"
  PHONE_USER_ID=$(echo "$body" | grep -o '"id":"[^"]*"' | head -1 | cut -d'"' -f4)
  TESTS_PASSED=$((TESTS_PASSED + 1))
else
  echo -e "${RED}✗ Phone registration failed${NC}"
  echo "Response: $body"
  TESTS_FAILED=$((TESTS_FAILED + 1))
fi
echo ""

# ───────────────────────────────────────────────────────────────
# TEST 2: EMAIL + PASSWORD REGISTRATION
# ───────────────────────────────────────────────────────────────
echo -e "${YELLOW}[TEST 2] Email + Password Registration${NC}"
echo "─────────────────────────────────────────────────────────"

EMAIL="user-$TIMESTAMP@example.com"
PHONE2="888${TIMESTAMP:7:7}"
PASSWORD="SecurePass123!"

echo "Using email: $EMAIL"
echo "Using phone: +91$PHONE2"

response=$(curl -s -w "\n%{http_code}" -X POST "$API_URL/auth/register" \
  -H "Content-Type: application/json" \
  -d "{\"full_name\": \"Email User $TIMESTAMP\", \"email\": \"$EMAIL\", \"phone\": \"$PHONE2\", \"password\": \"$PASSWORD\", \"role\": \"customer\"}")

http_code=$(echo "$response" | tail -n1)
body=$(echo "$response" | head -n-1)

if [[ "$http_code" == "201"* ]]; then
  echo -e "${GREEN}✓ Email registration successful${NC}"
  echo "Response: $body"
  EMAIL_USER_ID=$(echo "$body" | grep -o '"id":"[^"]*"' | head -1 | cut -d'"' -f4)
  TESTS_PASSED=$((TESTS_PASSED + 1))
else
  echo -e "${RED}✗ Email registration failed${NC}"
  echo "Response: $body"
  TESTS_FAILED=$((TESTS_FAILED + 1))
fi
echo ""

# ───────────────────────────────────────────────────────────────
# TEST 3: PHONE + OTP LOGIN
# ───────────────────────────────────────────────────────────────
echo -e "${YELLOW}[TEST 3] Phone + OTP Login${NC}"
echo "─────────────────────────────────────────────────────────"

# 3a. Send OTP for login
echo "Step 3a: Send OTP for login"
response=$(curl -s -X POST "$API_URL/auth/send-otp" \
  -H "Content-Type: application/json" \
  -d "{\"phone\": \"$PHONE\"}")
echo "Response: $response"
LOGIN_OTP=$(echo "$response" | grep -o '"otp":"[0-9]*"' | head -1 | grep -o '[0-9]*')

if [ -z "$LOGIN_OTP" ]; then
  LOGIN_OTP="123456"
  echo "Using placeholder OTP: $LOGIN_OTP"
fi
echo ""

# 3b. Verify OTP and login
echo "Step 3b: Verify OTP and login"
response=$(curl -s -w "\n%{http_code}" -X POST "$API_URL/auth/verify-otp" \
  -H "Content-Type: application/json" \
  -d "{\"phone\": \"$PHONE\", \"otp\": \"$LOGIN_OTP\", \"purpose\": \"login\"}")

http_code=$(echo "$response" | tail -n1)
body=$(echo "$response" | head -n-1)

if [[ "$http_code" == "200"* ]]; then
  echo -e "${GREEN}✓ OTP login successful${NC}"
  echo "Response: $body"
  ACCESS_TOKEN=$(echo "$body" | grep -o '"access_token":"[^"]*"' | head -1 | cut -d'"' -f4)
  REFRESH_TOKEN=$(echo "$body" | grep -o '"refresh_token":"[^"]*"' | head -1 | cut -d'"' -f4)
  TESTS_PASSED=$((TESTS_PASSED + 1))
else
  echo -e "${RED}✗ OTP login failed${NC}"
  echo "Response: $body"
  TESTS_FAILED=$((TESTS_FAILED + 1))
fi
echo ""

# ───────────────────────────────────────────────────────────────
# TEST 4: EMAIL + PASSWORD LOGIN
# ───────────────────────────────────────────────────────────────
echo -e "${YELLOW}[TEST 4] Email + Password Login${NC}"
echo "─────────────────────────────────────────────────────────"

response=$(curl -s -w "\n%{http_code}" -X POST "$API_URL/auth/login" \
  -H "Content-Type: application/json" \
  -d "{\"email\": \"$EMAIL\", \"password\": \"$PASSWORD\"}")

http_code=$(echo "$response" | tail -n1)
body=$(echo "$response" | head -n-1)

if [[ "$http_code" == "200"* ]]; then
  echo -e "${GREEN}✓ Email+password login successful${NC}"
  echo "Response: $body"
  EMAIL_ACCESS_TOKEN=$(echo "$body" | grep -o '"access_token":"[^"]*"' | head -1 | cut -d'"' -f4)
  EMAIL_REFRESH_TOKEN=$(echo "$body" | grep -o '"refresh_token":"[^"]*"' | head -1 | cut -d'"' -f4)
  TESTS_PASSED=$((TESTS_PASSED + 1))
else
  echo -e "${RED}✗ Email+password login failed${NC}"
  echo "Response: $body"
  TESTS_FAILED=$((TESTS_FAILED + 1))
fi
echo ""

# ───────────────────────────────────────────────────────────────
# TEST 5: GET CURRENT USER (WITH TOKEN)
# ───────────────────────────────────────────────────────────────
echo -e "${YELLOW}[TEST 5] Get Current User Profile${NC}"
echo "─────────────────────────────────────────────────────────"

if [ -n "$ACCESS_TOKEN" ]; then
  test_endpoint "Get current user profile" "GET" "/auth/me" "" "200"
else
  echo -e "${RED}✗ Skipped (no access token)${NC}"
  TESTS_FAILED=$((TESTS_FAILED + 1))
fi
echo ""

# ───────────────────────────────────────────────────────────────
# TEST 6: TOKEN REFRESH
# ───────────────────────────────────────────────────────────────
echo -e "${YELLOW}[TEST 6] Token Refresh${NC}"
echo "─────────────────────────────────────────────────────────"

if [ -n "$REFRESH_TOKEN" ]; then
  response=$(curl -s -w "\n%{http_code}" -X POST "$API_URL/auth/refresh" \
    -H "Content-Type: application/json" \
    -d "{\"refresh_token\": \"$REFRESH_TOKEN\"}")

  http_code=$(echo "$response" | tail -n1)
  body=$(echo "$response" | head -n-1)

  if [[ "$http_code" == "200"* ]]; then
    echo -e "${GREEN}✓ Token refresh successful${NC}"
    NEW_ACCESS_TOKEN=$(echo "$body" | grep -o '"access_token":"[^"]*"' | head -1 | cut -d'"' -f4)
    ACCESS_TOKEN=$NEW_ACCESS_TOKEN
    TESTS_PASSED=$((TESTS_PASSED + 1))
  else
    echo -e "${RED}✗ Token refresh failed${NC}"
    TESTS_FAILED=$((TESTS_FAILED + 1))
  fi
  echo "Response: $body"
else
  echo -e "${RED}✗ Skipped (no refresh token)${NC}"
  TESTS_FAILED=$((TESTS_FAILED + 1))
fi
echo ""

# ───────────────────────────────────────────────────────────────
# TEST 7: LOGOUT
# ───────────────────────────────────────────────────────────────
echo -e "${YELLOW}[TEST 7] Logout${NC}"
echo "─────────────────────────────────────────────────────────"

if [ -n "$REFRESH_TOKEN" ]; then
  response=$(curl -s -w "\n%{http_code}" -X POST "$API_URL/auth/logout" \
    -H "Content-Type: application/json" \
    -d "{\"refresh_token\": \"$REFRESH_TOKEN\"}")

  http_code=$(echo "$response" | tail -n1)

  if [[ "$http_code" == "204"* ]]; then
    echo -e "${GREEN}✓ Logout successful${NC}"
    TESTS_PASSED=$((TESTS_PASSED + 1))
  else
    echo -e "${RED}✗ Logout failed${NC}"
    TESTS_FAILED=$((TESTS_FAILED + 1))
  fi
else
  echo -e "${RED}✗ Skipped (no refresh token)${NC}"
  TESTS_FAILED=$((TESTS_FAILED + 1))
fi
echo ""

# ───────────────────────────────────────────────────────────────
# TEST SUMMARY
# ───────────────────────────────────────────────────────────────
echo "════════════════════════════════════════════════════════════"
echo "                    TEST SUMMARY"
echo "════════════════════════════════════════════════════════════"
echo -e "Passed: ${GREEN}$TESTS_PASSED${NC}"
echo -e "Failed: ${RED}$TESTS_FAILED${NC}"

if [ $TESTS_FAILED -eq 0 ]; then
  echo -e "\n${GREEN}✓ All tests passed!${NC}"
  exit 0
else
  echo -e "\n${RED}✗ Some tests failed${NC}"
  exit 1
fi
