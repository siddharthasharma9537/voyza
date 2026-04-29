# 🚀 Deployment Guide for Voyza

Complete guide for testing and deploying Voyza backend to production.

## Pre-Deployment Testing

Before deploying any code to production, **always run the pre-deployment test suite**.

### Option 1: Python Script (Recommended - Cross-Platform)

Works on Windows, Mac, and Linux:

```bash
cd backend
python scripts/pre_deploy_tests.py
```

This runs:
- ✅ Environment checks (Python, pip, virtual env)
- ✅ Dependency verification
- ✅ Python syntax validation
- ✅ Security checks (no hardcoded secrets)
- ✅ Integration test suite
- ✅ Code quality analysis
- ✅ Configuration validation

### Option 2: Bash Script (Mac/Linux Only)

```bash
cd backend
bash scripts/pre_deploy_tests.sh
```

### Option 3: Manual Testing

Run tests individually:

```bash
cd backend

# Install dependencies
pip install -r requirements.txt

# Run all integration tests
pytest tests/integration/ -v

# Run specific test module
pytest tests/integration/test_booking_flow.py -v

# Run with coverage
pytest tests/integration/ --cov=app --cov-report=html
```

## Test Results Interpretation

### ✅ Ready for Deployment

```
Results:
  ✅ Passed:   45
  ❌ Failed:   0
  ⚠️  Warnings: 0

✅ READY FOR DEPLOYMENT
All checks passed with no issues!
```

**Next Steps:**
1. Merge branch to `main`
2. Tag release: `git tag v1.0.0`
3. Push to production
4. Run post-deployment verification

### ⚠️ Minor Issues (Still Safe)

```
Results:
  ✅ Passed:   45
  ❌ Failed:   0
  ⚠️  Warnings: 2

✅ READY FOR DEPLOYMENT
Passed all critical checks. Review 2 warnings above.
```

**Action:** Review warnings but safe to deploy.

### ❌ Critical Issues (Do Not Deploy)

```
Results:
  ✅ Passed:   40
  ❌ Failed:   3
  ⚠️  Warnings: 1

❌ NOT READY FOR DEPLOYMENT
Fix 3 errors before deploying.
```

**Action:** 
1. Fix all errors shown
2. Re-run tests
3. Only deploy after all tests pass

## Continuous Integration / CD

### GitHub Actions

Tests automatically run on every PR and push to `main`:

```bash
# View test results
git log --oneline
# Look for ✅ or ❌ status on commits
```

The workflow (`.github/workflows/pre-deploy-tests.yml`) runs:
- Syntax validation
- Integration tests
- Unit tests
- Security checks
- Creates deployment summary

## Deployment Checklist

Before deploying to production, ensure:

### Code Preparation
- ☐ All tests pass: `pytest tests/integration/ -v`
- ☐ No syntax errors
- ☐ No hardcoded secrets or API keys
- ☐ Changes are committed and pushed
- ☐ Branch is merged to `main`

### Environment Setup
- ☐ `.env` file configured with all variables
- ☐ Database connection string set
- ☐ Twilio credentials configured
- ☐ Razorpay credentials configured
- ☐ OAuth credentials (Google, Apple, Facebook)
- ☐ S3/MinIO bucket configured
- ☐ SendGrid API key configured
- ☐ Redis connection configured
- ☐ JWT secret key set

### Infrastructure
- ☐ Database migrations ready: `alembic upgrade head`
- ☐ PostgreSQL version compatible
- ☐ Redis server running
- ☐ S3/MinIO accessible
- ☐ Load balancer configured
- ☐ SSL/TLS certificates valid
- ☐ CORS origins configured

### Monitoring & Logging
- ☐ Log aggregation configured
- ☐ Error tracking setup (e.g., Sentry)
- ☐ Monitoring alerts configured
- ☐ Health check endpoint `/health` accessible
- ☐ Backup strategy in place

## Deployment Steps

### 1. Merge to Main

```bash
# Make sure all tests pass first!
pytest tests/integration/ -v

# Merge branch
git checkout main
git merge claude/continue-mac-project-ZkSQ0

# Push to remote
git push origin main
```

### 2. Create Release Tag

```bash
# Tag the release
git tag -a v1.1.0 -m "Release: SMS OTP, integration tests, security improvements"

# Push tag
git push origin v1.1.0
```

### 3. Deploy Backend

```bash
# Pull latest code on server
ssh user@production.server
cd /app/voyza
git pull origin main
git checkout v1.1.0

# Install dependencies
pip install -r backend/requirements.txt

# Run migrations
cd backend
alembic upgrade head

# Restart application
systemctl restart voyza-api

# Verify
curl https://voyzacar.online/health
```

### 4. Post-Deployment Verification

```bash
# Test critical endpoints
curl -X POST https://voyzacar.online/api/v1/auth/register/send-phone-otp \
  -H "Content-Type: application/json" \
  -d '{"phone": "9876543210"}'

# Should return 200 with OTP sent message

# Test vehicle browsing
curl https://voyzacar.online/api/v1/vehicles

# Should return paginated vehicle list

# Check logs for errors
journalctl -u voyza-api -f
```

## Rollback Plan

If deployment fails:

```bash
# Identify last good version
git log --oneline

# Rollback to previous tag
git checkout v1.0.0
git push -f origin main  # Force push (only in emergency!)

# Restart application
systemctl restart voyza-api

# Verify health
curl https://voyzacar.online/health
```

## Key Features Deployed

This deployment includes:

### 🔐 Authentication Security
- ✅ Phone OTP with SMS delivery via Twilio
- ✅ Password strength validation (8+ chars, uppercase, number, special)
- ✅ OAuth with phone verification requirement
- ✅ JWT with proper signature verification

### 📅 Booking System
- ✅ Vehicle browsing with filters
- ✅ Price calculation (hourly/daily rates, tax, deposits)
- ✅ Double-booking prevention (atomic transactions)
- ✅ Cancellation and refund workflows

### 🏠 Owner Management
- ✅ Vehicle CRUD operations
- ✅ Availability slot management
- ✅ Booking views and earnings tracking

### 💳 Payments
- ✅ Razorpay integration with signature verification
- ✅ Payment state machine

### 🧪 Quality Assurance
- ✅ 1,400+ lines of integration tests
- ✅ 80+ test cases covering critical flows
- ✅ Pre-deployment testing scripts

## Monitoring

After deployment, monitor these metrics:

### Health Checks
```bash
# Every minute
curl https://voyzacar.online/health

# Should return:
# {"status": "ok", "version": "1.1.0"}
```

### Key Endpoints
```bash
# Phone OTP
POST /api/v1/auth/send-otp
Expected: 200, SMS sent

# Create Booking
POST /api/v1/bookings
Expected: 201, booking created

# Owner Vehicles
GET /api/v1/owner/cars
Expected: 200, list of vehicles
```

### Common Issues

| Error | Cause | Fix |
|-------|-------|-----|
| 500 Internal Server | Database connection failed | Check DB_URL and PostgreSQL |
| 401 Unauthorized | JWT secret mismatch | Verify SECRET_KEY in .env |
| 503 Service Unavailable | Redis not running | Start Redis service |
| SMS not sending | Twilio credentials wrong | Verify TWILIO_* variables |
| Payment fails | Razorpay key expired | Update RAZORPAY_KEY_* |

## Support

For deployment issues:
- Check logs: `journalctl -u voyza-api -f`
- Review test results: `pytest tests/integration/ -v`
- Check configuration: `cat .env | grep -E "TWILIO|RAZORPAY|GOOGLE"`

## Related Documentation

- **Test Documentation:** See `backend/tests/README.md`
- **Configuration:** See `backend/app/core/config.py`
- **API Endpoints:** See `backend/app/api/v1/endpoints/`
- **Models:** See `backend/app/models/`

---

**Last Updated:** April 29, 2026
**Version:** 1.1.0
**Status:** Ready for Production Deployment
