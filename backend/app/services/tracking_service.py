"""
app/services/tracking_service.py
──────────────────────────────────
Real-time GPS tracking for rides.
Receives location pings from drivers (via WebSocket), appends to the
ride's gps_trail, and broadcasts updates to watching customers.

Works alongside app/core/websocket_manager.py — call
  await tracking_service.push_location(ride_id, lat, lng, ws_manager)
from the WebSocket endpoint.
"""

from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.websocket_manager import WebSocketManager
from app.models.driver import Driver
from app.models.ride import Ride, RideStatus


async def push_location(
    ride_id: str,
    driver_id: str,
    latitude: float,
    longitude: float,
    speed_kmph: float | None,
    heading: float | None,
    db: AsyncSession,
    ws_manager: WebSocketManager,
) -> None:
    """
    1. Persist the GPS ping to the ride's gps_trail (JSONB append).
    2. Update the driver's last known location.
    3. Broadcast the update to all clients watching this ride.
    """
    # Load ride
    result = await db.execute(
        select(Ride).where(Ride.id == ride_id, Ride.driver_id == driver_id)
    )
    ride = result.scalar_one_or_none()
    if not ride or ride.status != RideStatus.IN_PROGRESS:
        return   # silently ignore stale pings

    now = datetime.now(timezone.utc)
    ping = {
        "lat": latitude,
        "lng": longitude,
        "ts": now.isoformat(),
        **({"speed": speed_kmph} if speed_kmph is not None else {}),
        **({"heading": heading} if heading is not None else {}),
    }

    # Append to trail (JSONB list)
    trail = list(ride.gps_trail or [])
    trail.append(ping)
    ride.gps_trail = trail

    # Update driver location
    driver_result = await db.execute(select(Driver).where(Driver.id == driver_id))
    driver = driver_result.scalar_one_or_none()
    if driver:
        driver.last_latitude = latitude
        driver.last_longitude = longitude
        driver.location_updated_at = now

    await db.commit()

    # Broadcast to WebSocket room for this ride
    await ws_manager.broadcast_to_room(
        room=f"ride:{ride_id}",
        message={
            "event": "location_update",
            "ride_id": ride_id,
            **ping,
        },
    )


async def get_trail(ride_id: str, db: AsyncSession) -> list[dict]:
    """Return full GPS breadcrumb trail for a completed or active ride."""
    result = await db.execute(select(Ride.gps_trail).where(Ride.id == ride_id))
    row = result.scalar_one_or_none()
    return row or []
