"""Audit logging service. Writes immutable action records."""
from __future__ import annotations

from typing import Any

from motor.motor_asyncio import AsyncIOMotorDatabase

from app.utils.time import utcnow


async def record_audit(
    db: AsyncIOMotorDatabase,
    *,
    actor_id: str | None,
    action: str,
    target_id: str | None = None,
    metadata: dict[str, Any] | None = None,
    ip_address: str | None = None,
) -> None:
    await db.audit_logs.insert_one(
        {
            "actor_id": actor_id,
            "action": action,
            "target_id": target_id,
            "metadata": metadata or {},
            "ip_address": ip_address,
            "created_at": utcnow(),
        }
    )
