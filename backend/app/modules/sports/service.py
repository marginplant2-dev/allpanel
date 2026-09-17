"""Sports & events service. Reads via the sports provider; admin writes to DB."""
from __future__ import annotations

from typing import Any

from motor.motor_asyncio import AsyncIOMotorDatabase

from app.core.exceptions import ConflictError, NotFoundError
from app.modules.providers.provider_factory import get_sports_provider
from app.modules.sports.schema import EventCreate, EventUpdate, SportCreate
from app.utils.ids import serialize, to_object_id
from app.utils.time import utcnow


class SportsService:
    def __init__(self, db: AsyncIOMotorDatabase):
        self.db = db
        self.provider = get_sports_provider(db)

    # ---- public reads ----
    async def sports(self) -> list[dict[str, Any]]:
        return await self.provider.get_sports()

    async def events(self, *, sport_id: str | None, status: str | None) -> list[dict[str, Any]]:
        return await self.provider.get_events(sport_id=sport_id, status=status)

    async def event_detail(self, event_id: str) -> dict[str, Any]:
        doc = await self.provider.get_event_detail(event_id)
        if doc is None:
            raise NotFoundError("Event not found")
        return doc

    async def live_data(self, event_id: str) -> dict[str, Any]:
        data = await self.provider.get_live_data(event_id)
        if data is None:
            raise NotFoundError("Event not found")
        return data

    # ---- admin writes ----
    async def create_sport(self, payload: SportCreate) -> dict[str, Any]:
        if await self.db.sports.find_one({"key": payload.key}):
            raise ConflictError("Sport key already exists")
        result = await self.db.sports.insert_one(payload.model_dump())
        return serialize(await self.db.sports.find_one({"_id": result.inserted_id}))  # type: ignore[return-value]

    async def create_event(self, payload: EventCreate) -> dict[str, Any]:
        doc = {**payload.model_dump(), "created_at": utcnow(), "updated_at": utcnow()}
        result = await self.db.events.insert_one(doc)
        return serialize(await self.db.events.find_one({"_id": result.inserted_id}))  # type: ignore[return-value]

    async def update_event(self, event_id: str, payload: EventUpdate) -> dict[str, Any]:
        changes = {k: v for k, v in payload.model_dump(exclude_unset=True).items() if v is not None}
        changes["updated_at"] = utcnow()
        updated = await self.db.events.find_one_and_update(
            {"_id": to_object_id(event_id)}, {"$set": changes}, return_document=True
        )
        if updated is None:
            raise NotFoundError("Event not found")
        return serialize(updated)  # type: ignore[return-value]
