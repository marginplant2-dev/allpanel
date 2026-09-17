"""In-memory WebSocket connection manager.

Tracks live connections per user and per channel. Designed so it can later be
backed by Redis pub/sub and extracted into a dedicated realtime service without
changing call sites (publish/send_to_user/broadcast).
"""
from __future__ import annotations

import asyncio
import logging
from collections import defaultdict
from typing import Any

from fastapi import WebSocket

logger = logging.getLogger(__name__)


class ConnectionManager:
    def __init__(self) -> None:
        self._by_user: dict[str, set[WebSocket]] = defaultdict(set)
        self._channels: dict[str, set[WebSocket]] = defaultdict(set)
        self._lock = asyncio.Lock()

    async def connect(self, ws: WebSocket, user_id: str) -> None:
        await ws.accept()
        async with self._lock:
            self._by_user[user_id].add(ws)

    async def disconnect(self, ws: WebSocket, user_id: str) -> None:
        async with self._lock:
            self._by_user.get(user_id, set()).discard(ws)
            for subs in self._channels.values():
                subs.discard(ws)

    async def subscribe(self, ws: WebSocket, channel: str) -> None:
        async with self._lock:
            self._channels[channel].add(ws)

    async def send_to_user(self, user_id: str, message: dict[str, Any]) -> None:
        await self._send_many(list(self._by_user.get(user_id, set())), message)

    async def broadcast(self, channel: str, message: dict[str, Any]) -> None:
        await self._send_many(list(self._channels.get(channel, set())), message)

    async def _send_many(self, sockets: list[WebSocket], message: dict[str, Any]) -> None:
        dead: list[WebSocket] = []
        for ws in sockets:
            try:
                await ws.send_json(message)
            except Exception:  # noqa: BLE001
                dead.append(ws)
        if dead:
            async with self._lock:
                for ws in dead:
                    for subs in self._by_user.values():
                        subs.discard(ws)
                    for subs in self._channels.values():
                        subs.discard(ws)

    @property
    def connection_count(self) -> int:
        return sum(len(s) for s in self._by_user.values())


manager = ConnectionManager()
