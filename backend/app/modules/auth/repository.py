"""Session persistence for refresh-token tracking."""
from __future__ import annotations

from datetime import datetime
from typing import Any

from motor.motor_asyncio import AsyncIOMotorDatabase

from app.utils.time import utcnow


class SessionRepository:
    def __init__(self, db: AsyncIOMotorDatabase):
        self.col = db.sessions

    async def create(
        self,
        *,
        token_id: str,
        user_id: str,
        expires_at: datetime,
        ip: str | None,
        user_agent: str | None,
    ) -> None:
        await self.col.insert_one(
            {
                "token_id": token_id,
                "user_id": user_id,
                "ip": ip,
                "user_agent": user_agent,
                "created_at": utcnow(),
                "expires_at": expires_at,
                "revoked": False,
            }
        )

    async def get(self, token_id: str) -> dict[str, Any] | None:
        return await self.col.find_one({"token_id": token_id})

    async def revoke(self, token_id: str) -> None:
        await self.col.update_one({"token_id": token_id}, {"$set": {"revoked": True}})

    async def revoke_all_for_user(self, user_id: str) -> None:
        await self.col.update_many({"user_id": user_id}, {"$set": {"revoked": True}})
