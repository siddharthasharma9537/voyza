"""
app/core/websocket_manager.py
──────────────────────────────
WebSocket connection manager for:
  • Live vehicle GPS tracking (owner → server → customer)
  • Real-time booking status push (server → customer/owner)
  • Admin live feed (all platform events)

Architecture:
  Each connected client registers with a room ID.
  Rooms:
    tracking:{booking_id}    — GPS updates for a specific booking
    user:{user_id}           — personal notifications
    admin:feed               — platform-wide event stream (admin only)

Redis pub/sub bridges multiple server instances (horizontal scaling).
Single server: in-memory rooms work fine.
Multi-server (prod): publish to Redis channel, all instances relay to their local sockets.
"""

from __future__ import annotations

import asyncio
import json
import logging
from collections import defaultdict
from datetime import datetime, timezone
from typing import Any

from fastapi import WebSocket

logger = logging.getLogger(__name__)


class ConnectionManager:
    """
    Thread-safe WebSocket room manager.

    Usage:
        manager = ConnectionManager()

        # In WebSocket endpoint:
        await manager.connect(ws, room="tracking:booking_abc")
        await manager.broadcast(room="tracking:booking_abc", data={...})
        manager.disconnect(ws, room="tracking:booking_abc")
    """

    def __init__(self):
        # room_id → set of WebSocket connections
        self._rooms: dict[str, set[WebSocket]] = defaultdict(set)
        # ws → set of rooms (for cleanup on disconnect)
        self._ws_rooms: dict[WebSocket, set[str]] = defaultdict(set)
        self._lock = asyncio.Lock()

    async def connect(self, ws: WebSocket, room: str) -> None:
        await ws.accept()
        async with self._lock:
            self._rooms[room].add(ws)
            self._ws_rooms[ws].add(room)
        logger.info("ws_connected", room=room, total=len(self._rooms[room]))

    def disconnect(self, ws: WebSocket, room: str | None = None) -> None:
        """Remove ws from a specific room, or all rooms if room=None."""
        rooms_to_leave = {room} if room else self._ws_rooms.get(ws, set()).copy()
        for r in rooms_to_leave:
            self._rooms[r].discard(ws)
            if not self._rooms[r]:
                del self._rooms[r]
        self._ws_rooms.pop(ws, None)
        logger.info("ws_disconnected", rooms=list(rooms_to_leave))

    async def broadcast(self, room: str, data: dict[str, Any]) -> None:
        """Send JSON message to all connections in a room."""
        if room not in self._rooms:
            return

        message = json.dumps({**data, "_ts": datetime.now(timezone.utc).isoformat()})
        dead: list[WebSocket] = []

        for ws in list(self._rooms[room]):
            try:
                await ws.send_text(message)
            except Exception:
                dead.append(ws)

        # Clean up dead connections
        for ws in dead:
            self.disconnect(ws)

    async def send_to_user(self, user_id: str, data: dict[str, Any]) -> None:
        """Send notification to a specific user's personal room."""
        await self.broadcast(room=f"user:{user_id}", data=data)

    async def broadcast_admin(self, data: dict[str, Any]) -> None:
        """Broadcast to admin live feed."""
        await self.broadcast(room="admin:feed", data=data)

    def room_size(self, room: str) -> int:
        return len(self._rooms.get(room, set()))

    def active_rooms(self) -> list[str]:
        return list(self._rooms.keys())


# Singleton — imported by all WebSocket endpoints
manager = ConnectionManager()
