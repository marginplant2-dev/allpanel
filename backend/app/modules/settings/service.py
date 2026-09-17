"""System settings & feature flags (singleton document)."""
from __future__ import annotations

from typing import Any

from motor.motor_asyncio import AsyncIOMotorDatabase

from app.modules.audit.models import AuditAction
from app.modules.audit.service import record_audit
from app.utils.time import utcnow

_SETTINGS_ID = "system"

DEFAULTS: dict[str, Any] = {
    "feature_flags": {
        "realtime_updates": True,
        "casino_catalogue": True,
        "sports_live": True,
        "two_factor": False,
    },
    "api_config": {
        "sports_provider": "mock",
        "games_provider": "mock",
    },
}


class SettingsService:
    def __init__(self, db: AsyncIOMotorDatabase):
        self.db = db

    async def get(self) -> dict[str, Any]:
        doc = await self.db.system_settings.find_one({"_id": _SETTINGS_ID})
        if doc is None:
            return {"id": _SETTINGS_ID, **DEFAULTS}
        doc["id"] = doc.pop("_id")
        return doc

    async def update(self, actor_id: str, changes: dict[str, Any], *, ip: str | None = None) -> dict[str, Any]:
        changes = {**changes, "updated_at": utcnow()}
        await self.db.system_settings.update_one(
            {"_id": _SETTINGS_ID}, {"$set": changes, "$setOnInsert": DEFAULTS}, upsert=True
        )
        await record_audit(
            self.db, actor_id=actor_id, action=AuditAction.SETTINGS_CHANGED,
            metadata={"keys": list(changes.keys())}, ip_address=ip,
        )
        return await self.get()
