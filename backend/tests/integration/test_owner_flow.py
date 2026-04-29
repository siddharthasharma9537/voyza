"""
tests/integration/test_owner_flow.py
────────────────────────────────────
Integration tests for owner vehicle management:
  1. Creating vehicle listings
  2. Updating vehicle details
  3. Managing availability slots
  4. Viewing owner earnings and bookings
  5. Authorization checks (owner-only endpoints)

Uses async_client fixture with in-memory SQLite.
Run with: pytest tests/integration/test_owner_flow.py -v
"""

import pytest
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import datetime, timedelta, timezone

from app.models.models import User, UserRole, Vehicle, VehicleStatus, Availability
from app.core.security import create_access_token, hash_password


@pytest.fixture
async def test_owner(db_session: AsyncSession) -> User:
    """Create a test owner in DB."""
    owner = User(
        id="owner-mgmt-test-1",
        full_name="Test Owner Manager",
        phone="+919812345671",
        email="owner@mgmt.test",
        hashed_password=hash_password("Test@1234"),
        role=UserRole.OWNER,
        is_active=True,
        is_verified=True,
    )
    db_session.add(owner)
    await db_session.flush()
    return owner


@pytest.fixture
async def other_owner(db_session: AsyncSession) -> User:
    """Create another owner for authorization tests."""
    owner = User(
        id="other-owner-mgmt-test-1",
        full_name="Other Owner",
        phone="+919812345672",
        email="other-owner@mgmt.test",
        hashed_password=hash_password("Test@1234"),
        role=UserRole.OWNER,
        is_active=True,
        is_verified=True,
    )
    db_session.add(owner)
    await db_session.flush()
    return owner


@pytest.fixture
def owner_auth_header(test_owner: User) -> dict:
    """Auth header for test owner."""
    token = create_access_token(subject=test_owner.id, role=test_owner.role)
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def other_owner_auth_header(other_owner: User) -> dict:
    """Auth header for other owner."""
    token = create_access_token(subject=other_owner.id, role=other_owner.role)
    return {"Authorization": f"Bearer {token}"}


# ── Test Classes ───────────────────────────────────────────────────────────────

class TestVehicleCreation:
    """Test vehicle listing creation."""

    async def test_create_vehicle_listing(self, async_client, test_owner, owner_auth_header, db_session):
        """Owner can create a new vehicle listing."""
        response = await async_client.post(
            "/api/v1/owner/cars",
            headers=owner_auth_header,
            json={
                "make": "Maruti",
                "model": "Baleno",
                "variant": "1.2 Petrol MT",
                "year": 2023,
                "city": "Bangalore",
                "fuel_type": "petrol",
                "transmission": "manual",
                "seating": 5,
                "price_per_day": 3000,
                "price_per_hour": 150,
                "security_deposit": 5000,
                "registration_number": "KA01AB5678",
            }
        )
        assert response.status_code == 201
        data = response.json()
        assert data["status"] == "draft"
        assert "id" in data

        # Verify in DB
        result = await db_session.execute(
            select(Vehicle).where(Vehicle.id == data["id"])
        )
        vehicle = result.scalar_one_or_none()
        assert vehicle is not None
        assert vehicle.owner_id == test_owner.id
        assert vehicle.make == "Maruti"

    async def test_create_vehicle_requires_owner_role(self, async_client):
        """Only owners can create vehicles."""
        from app.core.security import create_access_token, hash_password
        from app.models import UserRole

        # Create customer
        customer = User(
            id="customer-car-test-1",
            full_name="Test Customer",
            phone="+919876543211",
            email="customer.car@test",
            hashed_password=hash_password("Test@1234"),
            role=UserRole.CUSTOMER,
            is_active=True,
            is_verified=True,
        )
        token = create_access_token(subject=customer.id, role=customer.role)
        headers = {"Authorization": f"Bearer {token}"}

        response = await async_client.post(
            "/api/v1/owner/cars",
            headers=headers,
            json={
                "make": "Maruti",
                "model": "Baleno",
                "variant": "1.2 Petrol MT",
                "year": 2023,
                "city": "Bangalore",
                "fuel_type": "petrol",
                "transmission": "manual",
                "seating": 5,
                "price_per_day": 3000,
                "price_per_hour": 150,
                "security_deposit": 5000,
                "registration_number": "KA01AB5678",
            }
        )
        assert response.status_code == 403


class TestVehicleUpdate:
    """Test vehicle listing updates."""

    async def test_owner_can_update_own_vehicle(
        self, async_client, test_owner, owner_auth_header, db_session
    ):
        """Owner can update their own vehicle."""
        # Create vehicle
        vehicle = Vehicle(
            id="vehicle-update-test-1",
            owner_id=test_owner.id,
            make="Maruti",
            model="Baleno",
            variant="1.2 Petrol MT",
            year=2023,
            city="Bangalore",
            fuel_type="petrol",
            transmission="manual",
            seating=5,
            price_per_day=3000 * 100,
            price_per_hour=150 * 100,
            security_deposit=5000 * 100,
            registration_number="KA01AB5678",
            status=VehicleStatus.DRAFT,
        )
        db_session.add(vehicle)
        await db_session.flush()

        # Update vehicle
        response = await async_client.patch(
            f"/api/v1/owner/cars/{vehicle.id}",
            headers=owner_auth_header,
            json={
                "price_per_day": 3500,
                "city": "Pune",
            }
        )
        assert response.status_code == 200

        # Verify update
        result = await db_session.execute(
            select(Vehicle).where(Vehicle.id == vehicle.id)
        )
        updated = result.scalar_one()
        assert updated.price_per_day == 3500 * 100  # in paise
        assert updated.city == "Pune"

    async def test_owner_cannot_update_other_vehicles(
        self,
        async_client,
        test_owner,
        other_owner,
        other_owner_auth_header,
        db_session,
    ):
        """Owner cannot update another owner's vehicle."""
        # Create vehicle for test_owner
        vehicle = Vehicle(
            id="vehicle-other-test-1",
            owner_id=test_owner.id,
            make="Toyota",
            model="Fortuner",
            variant="2.4 Diesel AT",
            year=2022,
            city="Bangalore",
            fuel_type="diesel",
            transmission="automatic",
            seating=7,
            price_per_day=5000 * 100,
            price_per_hour=250 * 100,
            security_deposit=10000 * 100,
            registration_number="KA01CD1234",
            status=VehicleStatus.DRAFT,
        )
        db_session.add(vehicle)
        await db_session.flush()

        # Try to update with other_owner
        response = await async_client.patch(
            f"/api/v1/owner/cars/{vehicle.id}",
            headers=other_owner_auth_header,
            json={"price_per_day": 6000}
        )
        assert response.status_code == 403


class TestOwnerAvailability:
    """Test owner availability slot management."""

    async def test_owner_can_block_availability(
        self, async_client, test_owner, owner_auth_header, db_session
    ):
        """Owner can block a time slot for their vehicle."""
        # Create vehicle
        vehicle = Vehicle(
            id="vehicle-avail-test-1",
            owner_id=test_owner.id,
            make="Honda",
            model="City",
            variant="1.5 Petrol AT",
            year=2023,
            city="Bangalore",
            fuel_type="petrol",
            transmission="automatic",
            seating=5,
            price_per_day=2500 * 100,
            price_per_hour=125 * 100,
            security_deposit=5000 * 100,
            registration_number="KA01EF2345",
            status=VehicleStatus.ACTIVE,
        )
        db_session.add(vehicle)
        await db_session.flush()

        start = datetime.now(timezone.utc) + timedelta(days=5)
        end = start + timedelta(days=1)

        response = await async_client.post(
            "/api/v1/owner/availability",
            headers=owner_auth_header,
            json={
                "vehicle_id": vehicle.id,
                "start_time": start.isoformat(),
                "end_time": end.isoformat(),
                "reason": "maintenance",
            }
        )
        assert response.status_code == 201

        # Verify availability slot created
        result = await db_session.execute(
            select(Availability).where(
                Availability.vehicle_id == vehicle.id,
                Availability.reason == "maintenance"
            )
        )
        availability = result.scalar_one_or_none()
        assert availability is not None
        assert availability.start_time == start
        assert availability.end_time == end

    async def test_owner_can_unblock_availability(
        self, async_client, test_owner, owner_auth_header, db_session
    ):
        """Owner can remove an availability block."""
        # Create vehicle and availability slot
        vehicle = Vehicle(
            id="vehicle-unblock-test-1",
            owner_id=test_owner.id,
            make="Honda",
            model="City",
            variant="1.5 Petrol AT",
            year=2023,
            city="Bangalore",
            fuel_type="petrol",
            transmission="automatic",
            seating=5,
            price_per_day=2500 * 100,
            price_per_hour=125 * 100,
            security_deposit=5000 * 100,
            registration_number="KA01GH3456",
            status=VehicleStatus.ACTIVE,
        )
        db_session.add(vehicle)
        await db_session.flush()

        start = datetime.now(timezone.utc) + timedelta(days=5)
        end = start + timedelta(days=1)

        availability = Availability(
            vehicle_id=vehicle.id,
            start_time=start,
            end_time=end,
            reason="maintenance",
        )
        db_session.add(availability)
        await db_session.flush()
        avail_id = availability.id

        # Delete availability
        response = await async_client.delete(
            f"/api/v1/owner/availability/{avail_id}",
            headers=owner_auth_header,
        )
        assert response.status_code == 204

        # Verify deleted
        result = await db_session.execute(
            select(Availability).where(Availability.id == avail_id)
        )
        assert result.scalar_one_or_none() is None


class TestOwnerBookings:
    """Test owner viewing their bookings."""

    async def test_owner_can_list_own_bookings(
        self, async_client, test_owner, owner_auth_header
    ):
        """Owner can list all bookings for their vehicles."""
        response = await async_client.get(
            "/api/v1/owner/bookings",
            headers=owner_auth_header,
        )
        assert response.status_code == 200
        bookings = response.json()
        assert isinstance(bookings, list)


class TestOwnerEarnings:
    """Test owner earnings tracking."""

    async def test_owner_can_view_earnings(
        self, async_client, test_owner, owner_auth_header
    ):
        """Owner can view total earnings summary."""
        response = await async_client.get(
            "/api/v1/owner/earnings",
            headers=owner_auth_header,
        )
        assert response.status_code == 200
        earnings = response.json()
        assert isinstance(earnings, dict)
        assert "total_earnings" in earnings or "completed_bookings" in earnings

    async def test_owner_can_view_monthly_earnings(
        self, async_client, test_owner, owner_auth_header
    ):
        """Owner can view monthly earnings breakdown."""
        response = await async_client.get(
            "/api/v1/owner/earnings/monthly",
            headers=owner_auth_header,
        )
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)


class TestOwnerAuthorization:
    """Test authorization for owner endpoints."""

    async def test_customer_cannot_access_owner_endpoints(
        self, async_client
    ):
        """Customers cannot access owner management endpoints."""
        from app.core.security import create_access_token
        from app.models import UserRole

        token = create_access_token(subject="customer-id", role=UserRole.CUSTOMER)
        headers = {"Authorization": f"Bearer {token}"}

        response = await async_client.get(
            "/api/v1/owner/cars",
            headers=headers,
        )
        assert response.status_code == 403

    async def test_unauthenticated_cannot_access_owner_endpoints(
        self, async_client
    ):
        """Unauthenticated requests cannot access owner endpoints."""
        response = await async_client.get("/api/v1/owner/cars")
        assert response.status_code == 401
