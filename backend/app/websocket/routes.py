"""WebSocket endpoint registration and connection lifecycle."""
from __future__ import annotations

import logging

import jwt
from fastapi import FastAPI, Query, WebSocket, WebSocketDisconnect

from app.core.security import decode_token
from app.websocket.events import CHANNEL_ADMIN, CHANNEL_LIVE
from app.websocket.manager import manager

logger = logging.getLogger(__name__)

_ADMIN_ROLES = {"MOTHER_ADMIN", "SUPER_ADMIN", "ADMIN", "MASTER", "AGENT"}


def register_ws_routes(app: FastAPI) -> None:
    @app.websocket("/ws")
    async def websocket_endpoint(ws: WebSocket, token: str = Query(default="")):
        # Authenticate from the access token supplied as a query parameter.
        try:
            payload = decode_token(token)
            if payload.get("type") != "access":
                raise ValueError("wrong token type")
            user_id = payload["sub"]
            role = payload.get("role", "USER")
        except (jwt.PyJWTError, ValueError, KeyError):
            await ws.close(code=4401)
            return

        await manager.connect(ws, user_id)
        await manager.subscribe(ws, CHANNEL_LIVE)
        if role in _ADMIN_ROLES:
            await manager.subscribe(ws, CHANNEL_ADMIN)

        await ws.send_json({"type": "connected", "data": {"user_id": user_id}})
        try:
            while True:
                # Client messages are used only for keep-alive pings.
                msg = await ws.receive_text()
                if msg == "ping":
                    await ws.send_json({"type": "pong", "data": {}})
        except WebSocketDisconnect:
            await manager.disconnect(ws, user_id)
        except Exception:  # noqa: BLE001
            await manager.disconnect(ws, user_id)
