# Voyza Backend Integration Tests

Comprehensive integration tests for the Voyza car rental platform covering authentication, booking, payments, and owner management flows.

## Test Structure

### Unit Tests (`tests/unit/`)
- Isolated service and model tests
- No database required
- Mock dependencies

### Integration Tests (`tests/integration/`)
- End-to-end user journeys
- In-memory SQLite database
- Real API endpoints via async_client

## Test Modules

### 1. `test_auth_security.py` (300+ lines)
Validates authentication and security:
- ✅ Phone number validation (Indian format, prefixes)
- ✅ Password strength validation (8+ chars, uppercase, number, special)
- ✅ OTP request/verification flows
- ✅ OAuth phone linking requirement
- ✅ Token management and refresh
- ✅ Logout and token revocation
- ✅ Error handling and edge cases

**Key Test Classes:**
- `TestPhoneValidation` — Indian phone format validation
- `TestPasswordValidation` — Password strength requirements
- `TestOTPFlow` — OTP generation and verification
- `TestOAuthPhoneVerification` — OAuth users must link phone
- `TestTokenManagement` — JWT token lifecycle
- `TestLogout` — Token revocation on logout

### 2. `test_booking_flow.py` (400+ lines)
Customer booking journeys:
- ✅ Vehicle browsing with filters
- ✅ Price calculation (hourly/daily rates, tax, deposits)
- ✅ Booking creation with atomic transactions
- ✅ Double-booking prevention (concurrency safety)
- ✅ Availability slot blocking
- ✅ Booking cancellation with refunds
- ✅ Authorization checks
- ✅ Booking history

**Key Test Classes:**
- `TestVehicleBrowsing` — Vehicle search and discovery
- `TestPricePreview` — Pricing calculations
- `TestBookingCreation` — Booking creation and slot blocking
- `TestBookingCancellation` — Cancellation workflows
- `TestBookingAuthorization` — Permission checks
- `TestBookingHistory` — Booking history retrieval

### 3. `test_owner_flow.py` (250+ lines)
Owner vehicle management:
- ✅ Creating vehicle listings
- ✅ Updating vehicle details
- ✅ Managing availability slots
- ✅ Viewing owner bookings
- ✅ Earnings tracking
- ✅ Authorization checks (owner-only endpoints)

**Key Test Classes:**
- `TestVehicleCreation` — Listing creation
- `TestVehicleUpdate` — Update and authorization
- `TestOwnerAvailability` — Slot management
- `TestOwnerBookings` — Booking views
- `TestOwnerEarnings` — Earnings tracking
- `TestOwnerAuthorization` — Permission enforcement

### 4. `test_payment_flow.py` (existing)
Payment lifecycle:
- State machine validation
- Signature verification
- Payment transitions

## Running Tests

### Prerequisites
```bash
cd backend
pip install -r requirements.txt
```

### Run All Integration Tests
```bash
pytest tests/integration/ -v
```

### Run Specific Test Module
```bash
pytest tests/integration/test_booking_flow.py -v
pytest tests/integration/test_auth_security.py -v
pytest tests/integration/test_owner_flow.py -v
```

### Run Specific Test Class
```bash
pytest tests/integration/test_booking_flow.py::TestVehicleBrowsing -v
pytest tests/integration/test_auth_security.py::TestPhoneValidation -v
```

### Run Specific Test Case
```bash
pytest tests/integration/test_booking_flow.py::TestBookingCreation::test_create_booking_success -v
```

### Run with Coverage
```bash
pytest tests/integration/ --cov=app --cov-report=html
```

### Run with Output
```bash
pytest tests/integration/ -v -s  # Show print statements
```

## Test Database

All integration tests use **SQLite in-memory** (`sqlite:///:memory:`) via the `async_client` fixture:

```python
@pytest_asyncio.fixture
async def async_client(db_session):
    # Each test gets fresh in-memory DB
    # Rolled back after test completes
```

**Benefits:**
- No external database required
- Tests are isolated (fresh state per test)
- Tests run fast (in-memory)
- No cleanup needed

## Fixtures Available

From `tests/conftest.py`:

```python
# Database
db_session          # Fresh AsyncSession per test
async_client        # FastAPI test client with overridden DB
test_engine         # In-memory SQLite engine

# Users
sample_customer     # Customer User object
sample_owner        # Owner User object
sample_admin        # Admin User object

# Tokens
customer_token      # JWT for customer
owner_token         # JWT for owner
admin_token         # JWT for admin

# Time Helpers
future_pickup       # 48 hours from now
future_dropoff      # 72 hours from now
```

## Common Test Patterns

### Testing with Authentication
```python
async def test_requires_auth(self, async_client):
    response = await async_client.get(
        "/api/v1/protected-endpoint",
        headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 200
```

### Testing with Database Verification
```python
async def test_creates_record(self, async_client, db_session):
    response = await async_client.post(...)
    
    # Verify in database
    result = await db_session.execute(
        select(Model).where(Model.id == response.json()["id"])
    )
    assert result.scalar_one_or_none() is not None
```

### Testing Error Cases
```python
async def test_double_booking_prevention(self, async_client):
    # First booking
    response1 = await async_client.post(...)
    assert response1.status_code == 201
    
    # Overlapping booking should fail
    response2 = await async_client.post(...)
    assert response2.status_code == 409
    assert "not available" in response2.json()["detail"]
```

## Critical Tests to Watch

These tests verify the core platform requirements:

| Test | Purpose | Impact |
|------|---------|--------|
| `TestBookingCreation::test_double_booking_prevention` | Concurrency safety | Data integrity |
| `TestPasswordValidation::*` | Security | User account security |
| `TestPhoneValidation::*` | Input validation | SMS delivery success |
| `TestBookingCreation::test_create_booking_blocks_slot` | Availability logic | Overbooking prevention |
| `TestOAuthPhoneVerification::*` | OAuth flow | User onboarding |

## Debugging Tips

### Print Test Output
```bash
pytest tests/integration/test_booking_flow.py -v -s
```

### Stop at First Failure
```bash
pytest tests/integration/ -x
```

### Run Only Failed Tests
```bash
pytest tests/integration/ --lf
```

### Verbose Logging
```bash
pytest tests/integration/ -v --log-cli-level=DEBUG
```

### Run with Python Debugger
```python
# Add to test
import pdb; pdb.set_trace()

# Then run
pytest tests/integration/test_file.py -v -s
```

## Continuous Integration

For CI/CD pipelines:

```bash
# Run with JUnit XML output
pytest tests/integration/ --junit-xml=test-results.xml

# Run with JSON report
pytest tests/integration/ --json-report --json-report-file=report.json

# Run all with coverage
pytest tests/ --cov=app --cov-report=xml --cov-report=term
```

## Adding New Tests

### Template for New Test Module
```python
"""
tests/integration/test_feature_name.py
──────────────────────────────────────
Integration tests for [feature description].
"""

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

@pytest.fixture
async def fixture_name(db_session: AsyncSession):
    # Setup test data
    return data

class TestFeatureName:
    """Test [feature] behavior."""
    
    async def test_happy_path(self, async_client, fixture_name):
        response = await async_client.post("/api/v1/endpoint", json={...})
        assert response.status_code == 201
    
    async def test_error_case(self, async_client):
        response = await async_client.post("/api/v1/endpoint", json={...})
        assert response.status_code == 400
```

## Test Coverage Goals

Current coverage:
- ✅ Authentication (phone OTP, OAuth, password validation)
- ✅ Booking (creation, cancellation, double-booking prevention)
- ✅ Owner management (vehicle CRUD, availability, earnings)
- ✅ Pricing (hourly/daily rates, tax, deposits)
- ⏳ Payment processing (Razorpay integration)
- ⏳ KYC verification
- ⏳ Real-time notifications

## Known Limitations

1. **Razorpay Webhooks** — Payment webhook tests mock Razorpay responses
2. **SMS Delivery** — SMS sending is logged but not verified in tests
3. **File Upload** — Document upload tests don't check S3 actually receives files
4. **Email** — Email delivery is mocked, not verified

These are acceptable trade-offs for unit/integration testing.

## Troubleshooting

### Tests Hang
- Check for missing `await` on async functions
- Verify `db_session.commit()` or `await db.flush()` is called
- Check for infinite loops in test logic

### Import Errors
- Ensure `cd backend` before running tests
- Verify `PYTHONPATH` includes backend directory
- Check all model imports are correct

### Database Errors
- Verify all User/Vehicle models are created with required fields
- Check field types match database schema
- Ensure foreign key relationships are set up

## Contributing

When adding tests:
1. Follow existing naming patterns (`test_verb_noun`)
2. Add docstrings explaining what is tested
3. Include both happy path and error cases
4. Update this README with new test classes
5. Verify tests pass: `pytest tests/integration/ -v`
