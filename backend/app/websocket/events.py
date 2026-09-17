"""Realtime event types and publishing helpers."""
from __future__ import annotations

from typing import Any

from app.websocket.manager import manager

# Channels
CHANNEL_LIVE = "live_events"
CHANNEL_ADMIN = "admin_alerts"

# Event types
EVENT_WALLET_UPDATE = "wallet_update"
EVENT_NOTIFICATION = "notification"
EVENT_LIVE_EVENT = "live_event"
EVENT_ADMIN_ALERT = "admin_alert"


async def publish_wallet_update(user_id: str, wallet: dict[str, Any]) -> None:
    await manager.send_to_user(user_id, {"type": EVENT_WALLET_UPDATE, "data": wallet})


async def publish_notification(user_id: str, notification: dict[str, Any]) -> None:
    await manager.send_to_user(user_id, {"type": EVENT_NOTIFICATION, "data": notification})


async def publish_live_event(payload: dict[str, Any]) -> None:
    await manager.broadcast(CHANNEL_LIVE, {"type": EVENT_LIVE_EVENT, "data": payload})


async def publish_admin_alert(payload: dict[str, Any]) -> None:
    await manager.broadcast(CHANNEL_ADMIN, {"type": EVENT_ADMIN_ALERT, "data": payload})
