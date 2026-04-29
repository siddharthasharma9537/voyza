#!/bin/bash
# 🚀 Pre-Deployment Testing Script for Voyza
# ──────────────────────────────────────────
# Runs all checks before deploying to production.
# Usage: bash scripts/pre_deploy_tests.sh

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Counters
PASSED=0
FAILED=0
WARNINGS=0

# Helper functions
log_info() {
    echo -e "${BLUE}ℹ️  $1${NC}"
}

log_success() {
    echo -e "${GREEN}✅ $1${NC}"
    ((PASSED++))
}

log_error() {
    echo -e "${RED}❌ $1${NC}"
    ((FAILED++))
}

log_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
    ((WARNINGS++))
}

separator() {
    echo -e "${BLUE}────────────────────────────────────────────────${NC}"
}

# ═══════════════════════════════════════════════════════════════════════════

echo -e "${BLUE}"
echo "╔════════════════════════════════════════════════════════╗"
echo "║  🚀 Voyza Pre-Deployment Test Suite                   ║"
echo "╚════════════════════════════════════════════════════════╝"
echo -e "${NC}"

# Check if we're in the right directory
if [ ! -f "requirements.txt" ]; then
    log_error "requirements.txt not found. Run from backend directory."
    exit 1
fi

# ═══════════════════════════════════════════════════════════════════════════
echo ""
separator
echo -e "${BLUE}📦 Step 1: Environment Setup${NC}"
separator

log_info "Checking Python version..."
python --version || log_error "Python not found"

log_info "Checking pip..."
pip --version || log_error "pip not found"

log_info "Checking virtual environment..."
if [[ "$VIRTUAL_ENV" != "" ]]; then
    log_success "Virtual environment activated: $VIRTUAL_ENV"
else
    log_warning "Virtual environment not activated (optional)"
fi

# ═══════════════════════════════════════════════════════════════════════════
echo ""
separator
echo -e "${BLUE}📚 Step 2: Dependency Check${NC}"
separator

log_info "Checking required packages..."

REQUIRED_PACKAGES=("fastapi" "sqlalchemy" "pytest" "pydantic" "jose")
for package in "${REQUIRED_PACKAGES[@]}"; do
    python -c "import ${package}" 2>/dev/null && \
        log_success "$package is installed" || \
        log_error "$package is NOT installed"
done

# ═══════════════════════════════════════════════════════════════════════════
echo ""
separator
echo -e "${BLUE}🔍 Step 3: Syntax & Import Check${NC}"
separator

log_info "Checking Python syntax in app code..."
SYNTAX_ERRORS=0
for file in $(find app -name "*.py" -type f); do
    python -m py_compile "$file" 2>&1 || ((SYNTAX_ERRORS++))
done

if [ $SYNTAX_ERRORS -eq 0 ]; then
    log_success "All Python files have valid syntax"
else
    log_error "$SYNTAX_ERRORS files have syntax errors"
fi

log_info "Checking test file syntax..."
TEST_SYNTAX_ERRORS=0
for file in $(find tests -name "*.py" -type f 2>/dev/null); do
    python -m py_compile "$file" 2>&1 || ((TEST_SYNTAX_ERRORS++))
done

if [ $TEST_SYNTAX_ERRORS -eq 0 ]; then
    log_success "All test files have valid syntax"
else
    log_error "$TEST_SYNTAX_ERRORS test files have syntax errors"
fi

# ═══════════════════════════════════════════════════════════════════════════
echo ""
separator
echo -e "${BLUE}🔐 Step 4: Security Checks${NC}"
separator

log_info "Checking for hardcoded secrets..."
SECRETS_FOUND=0
# Check for common secret patterns in app code
grep -r "password.*=" app --include="*.py" | grep -v "hashed" | grep -v "verify" | grep -v "hash_password" | wc -l > /tmp/secret_check.txt
if [ $(cat /tmp/secret_check.txt) -gt 0 ]; then
    log_warning "Found potential hardcoded passwords (review manually)"
    ((WARNINGS++))
else
    log_success "No obvious hardcoded passwords detected"
fi

log_info "Checking for API keys in code..."
if grep -r "sk_live" app --include="*.py" > /dev/null 2>&1; then
    log_error "CRITICAL: Live API keys found in code!"
else
    log_success "No live API keys detected in code"
fi

# ═══════════════════════════════════════════════════════════════════════════
echo ""
separator
echo -e "${BLUE}🧪 Step 5: Unit & Integration Tests${NC}"
separator

if command -v pytest &> /dev/null; then
    log_info "Running integration tests (this may take a minute)..."

    # Run tests with timeout
    if timeout 180 pytest tests/integration/ -v --tb=short 2>&1 | tee /tmp/pytest_output.txt; then
        log_success "All integration tests passed"
    else
        log_error "Some tests failed (see details above)"
        echo ""
        log_info "Failed test output:"
        tail -50 /tmp/pytest_output.txt
    fi

    # Count test results
    TEST_COUNT=$(grep -c "PASSED" /tmp/pytest_output.txt || echo "0")
    if [ "$TEST_COUNT" -gt 0 ]; then
        log_success "Ran $TEST_COUNT tests"
    fi
else
    log_warning "pytest not found - skipping tests (install with: pip install pytest)"
fi

# ═══════════════════════════════════════════════════════════════════════════
echo ""
separator
echo -e "${BLUE}📋 Step 6: Code Quality Checks${NC}"
separator

log_info "Checking for common issues..."

# Check for inline imports (should be minimal)
INLINE_IMPORTS=$(grep -r "^    from " app/api/v1/endpoints/*.py 2>/dev/null | grep -v "settings" | wc -l)
if [ "$INLINE_IMPORTS" -gt 5 ]; then
    log_warning "Found $INLINE_IMPORTS inline imports (should be minimal)"
else
    log_success "Inline imports are minimized"
fi

# Check for print statements (should be removed)
PRINT_STATEMENTS=$(grep -r "^\s*print(" app --include="*.py" | wc -l)
if [ "$PRINT_STATEMENTS" -gt 0 ]; then
    log_warning "Found $PRINT_STATEMENTS print() statements (use logging instead)"
else
    log_success "No print statements found"
fi

# ═══════════════════════════════════════════════════════════════════════════
echo ""
separator
echo -e "${BLUE}🔧 Step 7: Configuration Validation${NC}"
separator

log_info "Checking environment configuration..."

# Check if settings can be imported
if python -c "from app.core.config import settings; print('Settings:', settings.APP_NAME)" > /dev/null 2>&1; then
    log_success "Settings configuration is valid"
else
    log_warning "Settings import failed (may be expected if .env not set)"
fi

# Check database URL pattern
if grep -q "DATABASE_URL\|POSTGRES" app/core/config.py 2>/dev/null; then
    log_success "Database configuration found in settings"
else
    log_warning "Database configuration not found (expected for async setup)"
fi

# Check for required OAuth credentials
if grep -q "GOOGLE_CLIENT_ID\|APPLE_CLIENT_ID" app/core/config.py; then
    log_success "OAuth configurations found"
else
    log_warning "OAuth configuration not found"
fi

# ═══════════════════════════════════════════════════════════════════════════
echo ""
separator
echo -e "${BLUE}📝 Step 8: Documentation Check${NC}"
separator

# Check if key files exist
REQUIRED_DOCS=("tests/README.md" "app/main.py" "app/api/v1/endpoints/auth.py")
for doc in "${REQUIRED_DOCS[@]}"; do
    if [ -f "$doc" ]; then
        log_success "$doc exists"
    else
        log_error "$doc is missing"
    fi
done

# ═══════════════════════════════════════════════════════════════════════════
echo ""
separator
echo -e "${BLUE}📊 Step 9: Deployment Readiness Summary${NC}"
separator

# Calculate overall status
TOTAL=$((PASSED + FAILED + WARNINGS))

echo ""
echo -e "Results:"
echo -e "  ${GREEN}✅ Passed:  $PASSED${NC}"
echo -e "  ${RED}❌ Failed:  $FAILED${NC}"
echo -e "  ${YELLOW}⚠️  Warnings: $WARNINGS${NC}"
echo ""

# Final verdict
echo -e "${BLUE}Deployment Readiness:${NC}"

if [ $FAILED -eq 0 ]; then
    echo -e "${GREEN}✅ READY FOR DEPLOYMENT${NC}"
    if [ $WARNINGS -eq 0 ]; then
        echo "   All checks passed with no issues!"
    else
        echo "   Passed all critical checks. Review $WARNINGS warnings above."
    fi
    EXIT_CODE=0
else
    echo -e "${RED}❌ NOT READY FOR DEPLOYMENT${NC}"
    echo "   Fix $FAILED errors before deploying."
    EXIT_CODE=1
fi

# ═══════════════════════════════════════════════════════════════════════════
echo ""
separator
echo -e "${BLUE}📋 Pre-Deployment Checklist${NC}"
separator

cat << EOF
Before deploying to production:

☐ All tests pass (run: pytest tests/integration/ -v)
☐ No syntax errors in Python files
☐ No hardcoded secrets or API keys
☐ Environment variables configured (.env file)
☐ Database migrations ready (alembic upgrade head)
☐ Twilio credentials configured (SMS delivery)
☐ Razorpay credentials configured (payments)
☐ OAuth credentials configured (Google, Apple, Facebook)
☐ S3/MinIO bucket configured (file uploads)
☐ SendGrid API key configured (email)
☐ Redis configured (caching and job queues)
☐ Log aggregation configured (structured logging)
☐ Monitoring and alerts configured
☐ Backup strategy in place
☐ Load balancer/proxy configured
☐ SSL certificates configured
☐ CORS origins configured correctly

Key Endpoints to Test:
  - POST /api/v1/auth/register/send-phone-otp (phone OTP)
  - POST /api/v1/auth/verify-otp (OTP verification)
  - POST /api/v1/bookings (create booking)
  - GET  /api/v1/vehicles (browse vehicles)
  - POST /api/v1/payments/create-order (payment)
  - GET  /api/v1/owner/cars (owner vehicles)

EOF

separator
echo ""

exit $EXIT_CODE
