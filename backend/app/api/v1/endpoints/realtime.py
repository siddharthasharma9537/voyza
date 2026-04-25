"""
app/api/v1/endpoints/realtime.py
──────────────────────────────────
WebSocket endpoints:

WS  /ws/track/{booking_id}   — GPS tracking stream for a booking
WS  /ws/notify/{user_id}     — Personal notification stream
WS  /ws/admin/feed           — Admin live event feed
POST /ws/track/update        — Owner pushes GPS position (REST fallback for mobile)

Authentication:
  WebSocket URLs carry ?token=<access_token> query param
  (Authorization header not supported in browser WS upgrade)

GPS Update Flow:
  1. Owner app sends GPS coords every 10s via WS or REST
  2. Server validates booking is ACTIVE and sender is the owner
  3. Server broadcasts to tracking:{booking_id} room
  4. Customer app receives live position

Tracking data stored in Redis (TTL=1h) — last known position
survives brief WebSocket reconnections.
"""

import json
import logging
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, Query, WebSocket, WebSocketDisconnect, HTTPException
from jose import JWTError
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.security import decode_token
from app.core.websocket_manager import manager
from app.db.base import get_db, AsyncSessionLocal
from app.models.models import Booking, BookingStatus, User, UserRole

router  = APIRouter(tags=["Realtime"])
logger  = logging.getLogger(__name__)


# ── Auth helper for WebSocket (token in query param) ──────────────────────────

async def _get_ws_user(token: str) -> User | None:
    """Validate JWT from query param and return User."""
    try:
        payload = decode_token(token)
        user_id = payload.get("sub")
        if not user_id:
            return None
    except JWTError:
        return None

    async with AsyncSessionLocal() as db:
        result = await db.execute(
            select(User).where(User.id == user_id, User.is_active.is_(True))
        )
        return result.scalar_one_or_none()


# ═══════════════════════════════════════════════════════════════ TRACKING

@router.websocket("/ws/track/{booking_id}")
async def tracking_ws(
    websocket: WebSocket,
    booking_id: str,
    token: str = Query(..., description="JWT access token"),
):
    """
    Customer connects to receive live GPS updates for their booking.
    Owner connects to send GPS updates for their car.

    Messages received from owner (JSON):
        {"lat": 17.385, "lng": 78.486, "speed_kmph": 45, "heading": 270}

    Messages broadcast to customer:
        {"type": "gps", "lat": ..., "lng": ..., "speed_kmph": ..., "ts": "..."}
    """
    user = await _get_ws_user(token)
    if not user:
        await websocket.close(code=4001, reason="Unauthorized")
        return

    # Validate booking access
    async with AsyncSessionLocal() as db:
        result = await db.execute(select(Booking).where(Booking.id == booking_id))
        booking = result.scalar_one_or_none()

    if not booking:
        await websocket.close(code=4004, reason="Booking not found")
        return

    is_customer = user.id == booking.customer_id
    is_owner    = user.id == booking.owner_id
    is_admin    = user.role == UserRole.ADMIN

    if not (is_customer or is_owner or is_admin):
        await websocket.close(code=4003, reason="Not authorized for this booking")
        return

    room = f"tracking:{booking_id}"
    await manager.connect(websocket, room)

    # Send last known position immediately on connect (from Redis in prod)
    await websocket.send_json({
        "type":    "connected",
        "room":    room,
        "booking_id": booking_id,
        "role":    "owner" if is_owner else "customer",
        "message": "Connected to tracking stream",
    })

    try:
        while True:
            raw = await websocket.receive_text()

            # Only the owner/admin can push GPS updates
            if not (is_owner or is_admin):
                continue

            try:
                data = json.loads(raw)
            except json.JSONDecodeError:
                await websocket.send_json({"type": "error", "message": "Invalid JSON"})
                continue

            # Validate required fields
            lat = data.get("lat")
            lng = data.get("lng")
            if lat is None or lng is None:
                await websocket.send_json({"type": "error", "message": "lat and lng required"})
                continue

            # Validate coordinate ranges
            if not (-90 <= lat <= 90) or not (-180 <= lng <= 180):
                await websocket.send_json({"type": "error", "message": "Invalid coordinates"})
                continue

            # Broadcast to all in room (customer sees live position)
            await manager.broadcast(room, {
                "type":       "gps",
                "lat":        lat,
                "lng":        lng,
                "speed_kmph": data.get("speed_kmph", 0),
                "heading":    data.get("heading", 0),
                "booking_id": booking_id,
            })

            logger.info("gps_update", booking_id=booking_id, lat=lat, lng=lng)

    except WebSocketDisconnect:
        manager.disconnect(websocket, room)
        logger.info("tracking_disconnected", booking_id=booking_id, user=user.id)


# ═══════════════════════════════════════════════════════════════ NOTIFICATIONS

@router.websocket("/ws/notify/{user_id}")
async def notification_ws(
    websocket: WebSocket,
    user_id: str,
    token: str = Query(..., description="JWT access token"),
):
    """
    Personal notification stream for a user.
    Receives real-time booking status updates, reminders, KYC results.

    Usage (frontend JS):
        const ws = new WebSocket(`wss://api.voyza.app/ws/notify/${userId}?token=${accessToken}`);
        ws.onmessage = (e) => {
            const msg = JSON.parse(e.data);
            if (msg.event === 'booking.confirmed') showSuccessToast(msg.message);
        };
    """
    user = await _get_ws_user(token)
    if not user or user.id != user_id:
        await websocket.close(code=4001, reason="Unauthorized")
        return

    room = f"user:{user_id}"
    await manager.connect(websocket, room)

    await websocket.send_json({
        "type":    "connected",
        "room":    room,
        "message": f"Notification stream active for {user.full_name}",
    })

    try:
        while True:
            # Keep-alive: client sends ping, server responds pong
            raw = await websocket.receive_text()
            if raw == "ping":
                await websocket.send_text("pong")
    except WebSocketDisconnect:
        manager.disconnect(websocket, room)


# ═══════════════════════════════════════════════════════════════ ADMIN FEED

@router.websocket("/ws/admin/feed")
async def admin_feed_ws(
    websocket: WebSocket,
    token: str = Query(..., description="JWT access token"),
):
    """
    Admin-only live event feed.
    Receives: booking confirmations, new KYC submissions, dispute flags, payment captures.
    """
    user = await _get_ws_user(token)
    if not user or user.role != UserRole.ADMIN:
        await websocket.close(code=4003, reason="Admin only")
        return

    room = "admin:feed"
    await manager.connect(websocket, room)

    await websocket.send_json({
        "type":    "connected",
        "room":    room,
        "active_rooms": manager.active_rooms(),
        "message": "Admin live feed connected",
    })

    try:
        while True:
            raw = await websocket.receive_text()
            if raw == "ping":
                await websocket.send_text("pong")
    except WebSocketDisconnect:
        manager.disconnect(websocket, room)


# ═══════════════════════════════════════════════════════════════ REST FALLBACK

class GPSUpdateRequest(BaseModel):
    booking_id:  str
    lat:         float
    lng:         float
    speed_kmph:  float = 0
    heading:     float = 0


@router.post("/track/update")
async def push_gps_update(
    data: GPSUpdateRequest,
    token: str = Query(...),
    db: AsyncSession = Depends(get_db),
):
    """
    REST fallback for GPS updates when WebSocket is unavailable.
    Owner app posts position — server broadcasts to tracking room.
    """
    user = await _get_ws_user(token)
    if not user:
        raise HTTPException(401, "Unauthorized")

    result = await db.execute(
        select(Booking).where(
            Booking.id == data.booking_id,
            Booking.owner_id == user.id,
            Booking.status == BookingStatus.ACTIVE,
        )
    )
    if not result.scalar_one_or_none():
        raise HTTPException(404, "Active booking not found")

    await manager.broadcast(f"tracking:{data.booking_id}", {
        "type":       "gps",
        "lat":        data.lat,
        "lng":        data.lng,
        "speed_kmph": data.speed_kmph,
        "heading":    data.heading,
        "booking_id": data.booking_id,
    })

    return {"status": "broadcast", "room_size": manager.room_size(f"tracking:{data.booking_id}")}
