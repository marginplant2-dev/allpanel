"""Authentication service: register, login, refresh, logout."""
from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Any

import jwt
from motor.motor_asyncio import AsyncIOMotorDatabase

from app.core.config import settings
from app.core.enums import Role, UserStatus
from app.core.exceptions import AuthenticationError, ConflictError
from app.core.security import (
    create_access_token,
    create_refresh_token,
    decode_token,
    hash_password,
    verify_password,
)
from app.modules.audit.models import AuditAction
from app.modules.audit.service import record_audit
from app.modules.auth.repository import SessionRepository
from app.modules.auth.schema import RegisterRequest
from app.modules.users.repository import UserRepository
from app.modules.users.service import public_user
from app.utils.time import utcnow


class AuthService:
    def __init__(self, db: AsyncIOMotorDatabase):
        self.db = db
        self.users = UserRepository(db)
        self.sessions = SessionRepository(db)

    async def register(self, payload: RegisterRequest, *, ip: str | None = None) -> dict[str, Any]:
        if await self.users.get_by_username(payload.username):
            raise ConflictError("Username already exists")
        now = utcnow()
        # A self-registered player still needs an upline: without one it shows up
        # in nobody's panel and no account can fund it. The root owns them.
        root = await self.db.users.find_one({"role": Role.MOTHER_ADMIN.value, "parent_id": None}, {"_id": 1})
        root_id = str(root["_id"]) if root else None
        doc = {
            "username": payload.username,
            "password_hash": hash_password(payload.password),
            "full_name": payload.full_name,
            "role": Role.USER.value,
            "parent_id": root_id,
            "hierarchy_path": [root_id] if root_id else [],
            "status": UserStatus.ACTIVE.value,
            "credit_limit": 0.0,
            "notes": None,
            "two_factor_enabled": False,
            "created_at": now,
            "updated_at": now,
            "last_login": None,
        }
        user_id = await self.users.insert(doc)
        await self.db.wallets.update_one(
            {"_id": user_id},
            {"$setOnInsert": {"available_balance": 0.0, "locked_balance": 0.0, "updated_at": now}},
            upsert=True,
        )
        created = await self.users.get_by_id(user_id)
        return await self._issue_session(created, ip=ip)  # type: ignore[arg-type]

    async def login(self, username: str, password: str, *, ip: str | None = None, ua: str | None = None) -> dict[str, Any]:
        doc = await self.users.get_by_username(username)
        if doc is None or not verify_password(password, doc.get("password_hash", "")):
            raise AuthenticationError("Invalid username or password")
        if doc.get("status") == UserStatus.SUSPENDED.value:
            raise AuthenticationError("Account is suspended")
        await self.users.update(str(doc["_id"]), {"last_login": utcnow()})
        await record_audit(self.db, actor_id=str(doc["_id"]), action=AuditAction.LOGIN, ip_address=ip)
        return await self._issue_session(doc, ip=ip, ua=ua)

    async def refresh(self, refresh_token: str) -> dict[str, Any]:
        try:
            payload = decode_token(refresh_token)
        except jwt.PyJWTError as exc:
            raise AuthenticationError("Invalid refresh token") from exc
        if payload.get("type") != "refresh":
            raise AuthenticationError("Invalid token type")

        token_id = payload.get("jti")
        session = await self.sessions.get(token_id)
        if session is None or session.get("revoked"):
            raise AuthenticationError("Session is no longer valid")

        user_id = payload.get("sub")
        doc = await self.users.get_by_id(user_id)
        if doc is None or doc.get("status") == UserStatus.SUSPENDED.value:
            raise AuthenticationError("Account is unavailable")

        access = create_access_token(user_id, {"role": doc["role"]})
        return {"access_token": access, "refresh_token": refresh_token, "token_type": "bearer"}

    async def logout(self, refresh_token: str | None, *, actor_id: str | None, ip: str | None = None) -> None:
        if refresh_token:
            try:
                payload = decode_token(refresh_token)
                if payload.get("jti"):
                    await self.sessions.revoke(payload["jti"])
            except jwt.PyJWTError:
                pass
        if actor_id:
            await record_audit(self.db, actor_id=actor_id, action=AuditAction.LOGOUT, ip_address=ip)

    async def _issue_session(self, doc: dict[str, Any], *, ip: str | None = None, ua: str | None = None) -> dict[str, Any]:
        user_id = str(doc["_id"])
        access = create_access_token(user_id, {"role": doc["role"]})
        refresh, token_id = create_refresh_token(user_id)
        expires_at = datetime.now(timezone.utc) + timedelta(days=settings.refresh_token_expire_days)
        await self.sessions.create(
            token_id=token_id, user_id=user_id, expires_at=expires_at, ip=ip, user_agent=ua
        )
        return {
            "access_token": access,
            "refresh_token": refresh,
            "token_type": "bearer",
            "user": public_user(doc),
        }
