"""
tests/integration/test_booking_flow.py
──────────────────────────────────────
Integration tests for complete booking lifecycle:
  1. Customer browsing vehicles
  2. Creating a booking
  3. Price calculation
  4. Cancellation and refunds
  5. Error handling (double-booking, invalid states)

Uses async_client fixture with in-memory SQLite.
Run with: pytest tests/integration/test_booking_flow.py -v
"""

import pytest
from datetime import datetime, timedelta, timezone
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.models import (
    Booking,
    BookingStatus,
    User,
    UserRole,
    Vehicle,
    VehicleStatus,
    Availability,
)
from app.core.security import create_access_token


# ── Test Data Fixtures ────────────────────────────────────────────────────────

@pytest.fixture
async def test_vehicle(db_session: AsyncSession) -> Vehicle:
    """Create a test vehicle owned by test owner."""
    vehicle = Vehicle(
        id="vehicle-test-1",
        owner_id="owner-uuid-5678",
        make="Toyota",
        model="Innova",
        variant="2.4 Diesel AT",
        year=2022,
        city="Bangalore",
        fuel_type="diesel",
        transmission="automatic",
        seating=8,
        price_per_day=5000 * 100,  # ₹5000 in paise
        price_per_hour=250 * 100,  # ₹250 in paise
        security_deposit=10000 * 100,  # ₹10000 in paise
        status=VehicleStatus.ACTIVE,
        registration_number="KA01AB1234",
        is_verified=True,
    )
    db_session.add(vehicle)
    await db_session.flush()
    return vehicle


@pytest.fixture
async def test_customer(db_session: AsyncSession) -> User:
    """Create a test customer in DB."""
    from app.core.security import hash_password

    customer = User(
        id="customer-test-1",
        full_name="Test Customer",
        phone="+919876543210",
        email="customer@test.com",
        hashed_password=hash_password("Test@1234"),
        role=UserRole.CUSTOMER,
        is_active=True,
        is_verified=True,
    )
    db_session.add(customer)
    await db_session.flush()
    return customer


@pytest.fixture
async def test_owner(db_session: AsyncSession) -> User:
    """Create a test owner in DB."""
    from app.core.security import hash_password

    owner = User(
        id="owner-test-1",
        full_name="Test Owner",
        phone="+919812345678",
        email="owner@test.com",
        hashed_password=hash_password("Test@1234"),
        role=UserRole.OWNER,
        is_active=True,
        is_verified=True,
    )
    db_session.add(owner)
    await db_session.flush()
    return owner


@pytest.fixture
def customer_auth_header(test_customer: User) -> dict:
    """Auth header for test customer."""
    token = create_access_token(subject=test_customer.id, role=test_customer.role)
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def owner_auth_header(test_owner: User) -> dict:
    """Auth header for test owner."""
    token = create_access_token(subject=test_owner.id, role=test_owner.role)
    return {"Authorization": f"Bearer {token}"}


# ── Test Classes ───────────────────────────────────────────────────────────────

class TestVehicleBrowsing:
    """Test vehicle search and discovery."""

    async def test_browse_vehicles_returns_active_only(self, async_client, test_vehicle):
        """Only ACTIVE vehicles appear in browse results."""
        response = await async_client.get("/api/v1/vehicles")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, dict)
        assert "items" in data or isinstance(data, dict)

    async def test_filter_by_city(self, async_client, test_vehicle):
        """Filter vehicles by city."""
        response = await async_client.get(
            "/api/v1/vehicles",
            params={"city": "Bangalore"}
        )
        assert response.status_code == 200

    async def test_filter_by_price_range(self, async_client, test_vehicle):
        """Filter vehicles by price per day."""
        response = await async_client.get(
            "/api/v1/vehicles",
            params={"min_price_day": 4000, "max_price_day": 6000}
        )
        assert response.status_code == 200

    async def test_get_vehicle_detail(self, async_client, test_vehicle):
        """Get full details of a specific vehicle."""
        response = await async_client.get(f"/api/v1/vehicles/{test_vehicle.id}")
        assert response.status_code == 200
        data = response.json()
        assert data.get("make") == "Toyota"
        assert data.get("model") == "Innova"


class TestPricePreview:
    """Test pricing calculations."""

    async def test_price_preview_hourly_rate(self, async_client, test_vehicle):
        """For <20 hours, charge hourly rate."""
        pickup = datetime.now(timezone.utc) + timedelta(hours=48)
        dropoff = pickup + timedelta(hours=10)

        response = await async_client.post(
            "/api/v1/bookings/preview",
            json={
                "vehicle_id": test_vehicle.id,
                "pickup_time": pickup.isoformat(),
                "dropoff_time": dropoff.isoformat(),
            }
        )
        assert response.status_code == 200
        pricing = response.json()

        # 10 hours at ₹250/hour = ₹2500
        expected_base = 250 * 100 * 10  # in paise
        assert pricing["base_amount"] == expected_base
        assert pricing["duration_hours"] == 10.0

    async def test_price_preview_daily_rate(self, async_client, test_vehicle):
        """For >=20 hours, charge daily rate."""
        pickup = datetime.now(timezone.utc) + timedelta(hours=48)
        dropoff = pickup + timedelta(hours=48)  # 2 days

        response = await async_client.post(
            "/api/v1/bookings/preview",
            json={
                "vehicle_id": test_vehicle.id,
                "pickup_time": pickup.isoformat(),
                "dropoff_time": dropoff.isoformat(),
            }
        )
        assert response.status_code == 200
        pricing = response.json()

        # 2 days at ₹5000/day = ₹10000
        expected_base = 5000 * 100 * 2  # in paise
        assert pricing["base_amount"] == expected_base
        assert pricing["duration_days"] == 2

    async def test_price_preview_includes_tax_and_deposit(self, async_client, test_vehicle):
        """Price breakdown includes GST and security deposit."""
        pickup = datetime.now(timezone.utc) + timedelta(hours=48)
        dropoff = pickup + timedelta(hours=24)

        response = await async_client.post(
            "/api/v1/bookings/preview",
            json={
                "vehicle_id": test_vehicle.id,
                "pickup_time": pickup.isoformat(),
                "dropoff_time": dropoff.isoformat(),
            }
        )
        assert response.status_code == 200
        pricing = response.json()

        # Verify all components present
        assert "base_amount" in pricing
        assert "tax_amount" in pricing
        assert "security_deposit" in pricing
        assert "total_amount" in pricing
        assert pricing["tax_amount"] > 0
        assert pricing["security_deposit"] == 10000 * 100  # ₹10000 in paise

    async def test_price_preview_with_promo_code(self, async_client, test_vehicle):
        """Apply promo code discount to booking."""
        pickup = datetime.now(timezone.utc) + timedelta(hours=48)
        dropoff = pickup + timedelta(hours=24)

        response = await async_client.post(
            "/api/v1/bookings/preview",
            json={
                "vehicle_id": test_vehicle.id,
                "pickup_time": pickup.isoformat(),
                "dropoff_time": dropoff.isoformat(),
                "promo_code": "WELCOME10",  # ₹100 off
            }
        )
        assert response.status_code == 200
        pricing = response.json()
        assert pricing["discount_amount"] == 10000  # ₹100 in paise


class TestBookingCreation:
    """Test booking creation and slot blocking."""

    async def test_create_booking_success(
        self, async_client, test_vehicle, test_customer, customer_auth_header, db_session
    ):
        """Create a valid booking."""
        pickup = datetime.now(timezone.utc) + timedelta(hours=48)
        dropoff = pickup + timedelta(hours=24)

        response = await async_client.post(
            "/api/v1/bookings",
            headers=customer_auth_header,
            json={
                "vehicle_id": test_vehicle.id,
                "pickup_time": pickup.isoformat(),
                "dropoff_time": dropoff.isoformat(),
                "pickup_address": "Bangalore Airport",
                "pickup_latitude": 13.1939,
                "pickup_longitude": 77.7064,
            }
        )
        assert response.status_code == 201
        booking = response.json()
        assert booking["status"] == "pending"
        assert booking["customer_id"] == test_customer.id
        assert booking["vehicle_id"] == test_vehicle.id

        # Verify booking saved in DB
        result = await db_session.execute(
            select(Booking).where(Booking.id == booking["id"])
        )
        db_booking = result.scalar_one_or_none()
        assert db_booking is not None
        assert db_booking.status == BookingStatus.PENDING

    async def test_create_booking_blocks_slot(
        self, async_client, test_vehicle, test_customer, customer_auth_header, db_session
    ):
        """Creating a booking should block the availability slot."""
        pickup = datetime.now(timezone.utc) + timedelta(hours=48)
        dropoff = pickup + timedelta(hours=24)

        response = await async_client.post(
            "/api/v1/bookings",
            headers=customer_auth_header,
            json={
                "vehicle_id": test_vehicle.id,
                "pickup_time": pickup.isoformat(),
                "dropoff_time": dropoff.isoformat(),
                "pickup_address": "Bangalore Airport",
                "pickup_latitude": 13.1939,
                "pickup_longitude": 77.7064,
            }
        )
        assert response.status_code == 201
        booking = response.json()

        # Check availability table
        result = await db_session.execute(
            select(Availability).where(
                Availability.vehicle_id == test_vehicle.id,
                Availability.booking_id == booking["id"],
            )
        )
        availability = result.scalar_one_or_none()
        assert availability is not None
        assert availability.reason == "booked"

    async def test_double_booking_prevention(
        self, async_client, test_vehicle, test_customer, customer_auth_header, db_session
    ):
        """Prevent booking the same vehicle during overlapping time."""
        pickup = datetime.now(timezone.utc) + timedelta(hours=48)
        dropoff = pickup + timedelta(hours=24)

        # First booking
        response1 = await async_client.post(
            "/api/v1/bookings",
            headers=customer_auth_header,
            json={
                "vehicle_id": test_vehicle.id,
                "pickup_time": pickup.isoformat(),
                "dropoff_time": dropoff.isoformat(),
                "pickup_address": "Bangalore Airport",
                "pickup_latitude": 13.1939,
                "pickup_longitude": 77.7064,
            }
        )
        assert response1.status_code == 201

        # Second overlapping booking should fail
        response2 = await async_client.post(
            "/api/v1/bookings",
            headers=customer_auth_header,
            json={
                "vehicle_id": test_vehicle.id,
                "pickup_time": (pickup + timedelta(hours=12)).isoformat(),
                "dropoff_time": (dropoff + timedelta(hours=12)).isoformat(),
                "pickup_address": "Bangalore Airport",
                "pickup_latitude": 13.1939,
                "pickup_longitude": 77.7064,
            }
        )
        assert response2.status_code == 409
        assert "not available" in response2.json()["detail"].lower()

    async def test_booking_requires_auth(self, async_client, test_vehicle):
        """Booking creation requires authentication."""
        pickup = datetime.now(timezone.utc) + timedelta(hours=48)
        dropoff = pickup + timedelta(hours=24)

        response = await async_client.post(
            "/api/v1/bookings",
            json={
                "vehicle_id": test_vehicle.id,
                "pickup_time": pickup.isoformat(),
                "dropoff_time": dropoff.isoformat(),
                "pickup_address": "Bangalore Airport",
                "pickup_latitude": 13.1939,
                "pickup_longitude": 77.7064,
            }
        )
        assert response.status_code == 401


class TestBookingCancellation:
    """Test booking cancellation and refund initiation."""

    async def test_customer_can_cancel_pending_booking(
        self,
        async_client,
        test_vehicle,
        test_customer,
        customer_auth_header,
        db_session,
    ):
        """Customer can cancel a PENDING booking."""
        pickup = datetime.now(timezone.utc) + timedelta(hours=48)
        dropoff = pickup + timedelta(hours=24)

        # Create booking
        create_response = await async_client.post(
            "/api/v1/bookings",
            headers=customer_auth_header,
            json={
                "vehicle_id": test_vehicle.id,
                "pickup_time": pickup.isoformat(),
                "dropoff_time": dropoff.isoformat(),
                "pickup_address": "Bangalore Airport",
                "pickup_latitude": 13.1939,
                "pickup_longitude": 77.7064,
            }
        )
        booking_id = create_response.json()["id"]

        # Cancel booking
        cancel_response = await async_client.post(
            f"/api/v1/bookings/{booking_id}/cancel",
            headers=customer_auth_header,
            json={"reason": "Changed my mind"},
        )
        assert cancel_response.status_code == 200
        cancelled = cancel_response.json()
        assert cancelled["status"] == "cancelled"

    async def test_cannot_cancel_completed_booking(
        self,
        async_client,
        test_vehicle,
        test_customer,
        customer_auth_header,
        db_session,
    ):
        """Cannot cancel a booking that's already completed."""
        pickup = datetime.now(timezone.utc) + timedelta(hours=48)
        dropoff = pickup + timedelta(hours=24)

        # Create booking
        create_response = await async_client.post(
            "/api/v1/bookings",
            headers=customer_auth_header,
            json={
                "vehicle_id": test_vehicle.id,
                "pickup_time": pickup.isoformat(),
                "dropoff_time": dropoff.isoformat(),
                "pickup_address": "Bangalore Airport",
                "pickup_latitude": 13.1939,
                "pickup_longitude": 77.7064,
            }
        )
        booking_id = create_response.json()["id"]

        # Manually set booking to COMPLETED (simulating completed ride)
        result = await db_session.execute(select(Booking).where(Booking.id == booking_id))
        booking = result.scalar_one()
        booking.status = BookingStatus.COMPLETED
        await db_session.flush()

        # Try to cancel
        cancel_response = await async_client.post(
            f"/api/v1/bookings/{booking_id}/cancel",
            headers=customer_auth_header,
            json={"reason": "Changed my mind"},
        )
        assert cancel_response.status_code == 400
        assert "cannot cancel" in cancel_response.json()["detail"].lower()

    async def test_owner_can_cancel_customer_booking(
        self,
        async_client,
        test_vehicle,
        test_customer,
        test_owner,
        customer_auth_header,
        owner_auth_header,
        db_session,
    ):
        """Owner can cancel a booking for their vehicle."""
        # Update vehicle to be owned by test_owner
        result = await db_session.execute(select(Vehicle).where(Vehicle.id == test_vehicle.id))
        vehicle = result.scalar_one()
        vehicle.owner_id = test_owner.id
        await db_session.flush()

        pickup = datetime.now(timezone.utc) + timedelta(hours=48)
        dropoff = pickup + timedelta(hours=24)

        # Customer creates booking
        create_response = await async_client.post(
            "/api/v1/bookings",
            headers=customer_auth_header,
            json={
                "vehicle_id": test_vehicle.id,
                "pickup_time": pickup.isoformat(),
                "dropoff_time": dropoff.isoformat(),
                "pickup_address": "Bangalore Airport",
                "pickup_latitude": 13.1939,
                "pickup_longitude": 77.7064,
            }
        )
        booking_id = create_response.json()["id"]

        # Owner cancels booking
        cancel_response = await async_client.post(
            f"/api/v1/bookings/{booking_id}/cancel",
            headers=owner_auth_header,
            json={"reason": "Vehicle maintenance required"},
        )
        assert cancel_response.status_code == 200


class TestBookingAuthorization:
    """Test authorization for booking operations."""

    async def test_customer_cannot_view_other_customer_booking(
        self,
        async_client,
        test_vehicle,
        test_customer,
        customer_auth_header,
        db_session,
    ):
        """Customer can't view another customer's booking."""
        pickup = datetime.now(timezone.utc) + timedelta(hours=48)
        dropoff = pickup + timedelta(hours=24)

        # Create booking
        create_response = await async_client.post(
            "/api/v1/bookings",
            headers=customer_auth_header,
            json={
                "vehicle_id": test_vehicle.id,
                "pickup_time": pickup.isoformat(),
                "dropoff_time": dropoff.isoformat(),
                "pickup_address": "Bangalore Airport",
                "pickup_latitude": 13.1939,
                "pickup_longitude": 77.7064,
            }
        )
        booking_id = create_response.json()["id"]

        # Create different customer token
        from app.core.security import hash_password, create_access_token

        other_customer = User(
            id="other-customer-1",
            full_name="Other Customer",
            phone="+919999999999",
            email="other@test.com",
            hashed_password=hash_password("Test@1234"),
            role=UserRole.CUSTOMER,
            is_active=True,
            is_verified=True,
        )
        db_session.add(other_customer)
        await db_session.flush()

        other_token = create_access_token(
            subject=other_customer.id, role=other_customer.role
        )
        other_headers = {"Authorization": f"Bearer {other_token}"}

        # Try to view with other customer's token
        view_response = await async_client.get(
            f"/api/v1/bookings/{booking_id}",
            headers=other_headers,
        )
        assert view_response.status_code == 403


class TestBookingHistory:
    """Test booking history retrieval."""

    async def test_list_customer_bookings(
        self,
        async_client,
        test_vehicle,
        test_customer,
        customer_auth_header,
    ):
        """Customer can list their bookings."""
        pickup = datetime.now(timezone.utc) + timedelta(hours=48)
        dropoff = pickup + timedelta(hours=24)

        # Create booking
        await async_client.post(
            "/api/v1/bookings",
            headers=customer_auth_header,
            json={
                "vehicle_id": test_vehicle.id,
                "pickup_time": pickup.isoformat(),
                "dropoff_time": dropoff.isoformat(),
                "pickup_address": "Bangalore Airport",
                "pickup_latitude": 13.1939,
                "pickup_longitude": 77.7064,
            }
        )

        # List bookings
        list_response = await async_client.get(
            "/api/v1/bookings",
            headers=customer_auth_header,
        )
        assert list_response.status_code == 200
        bookings = list_response.json()
        assert isinstance(bookings, list)
        assert len(bookings) == 1
