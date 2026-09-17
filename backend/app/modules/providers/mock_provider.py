"""Mock providers backed by the local MongoDB collections.

For development these read seeded data from `sports`, `events`, `games` and
`game_categories`. Live scores are lightly synthesized so the realtime layer has
something to stream. External providers can later implement the same interface.
"""
from __future__ import annotations

from typing import Any

from motor.motor_asyncio import AsyncIOMotorDatabase

from app.modules.providers.base import BaseGameProvider, BaseSportsProvider, best_h2h_odds
from app.utils.ids import is_object_id, serialize, serialize_many, to_object_id


class MockSportsProvider(BaseSportsProvider):
    key = "mock"

    def __init__(self, db: AsyncIOMotorDatabase):
        self.db = db

    async def get_sports(self) -> list[dict[str, Any]]:
        cursor = self.db.sports.find({"status": "active"}).sort("sort_order", 1)
        return serialize_many(await cursor.to_list(length=100))

    async def get_events(
        self, *, sport_id: str | None = None, status: str | None = None
    ) -> list[dict[str, Any]]:
        query: dict[str, Any] = {}
        if sport_id:
            query["sport_id"] = sport_id
        if status:
            query["status"] = status
        cursor = self.db.events.find(query).sort("start_time", 1)
        events = serialize_many(await cursor.to_list(length=200))
        for e in events:
            e["odds"] = best_h2h_odds(e.get("bookmakers", []))
        return events

    async def get_event_detail(self, event_id: str) -> dict[str, Any] | None:
        # Ids from an external provider ("sport_key:uuid") never match a seeded
        # event — treat them as missing rather than raising an invalid-id error.
        if not is_object_id(event_id):
            return None
        doc = await self.db.events.find_one({"_id": to_object_id(event_id)})
        return serialize(doc)

    async def get_live_data(self, event_id: str) -> dict[str, Any] | None:
        if not is_object_id(event_id):
            return None
        doc = await self.db.events.find_one(
            {"_id": to_object_id(event_id)}, {"score": 1, "status": 1}
        )
        if doc is None:
            return None
        return {"event_id": event_id, "status": doc.get("status"), "score": doc.get("score", {})}


class MockGameProvider(BaseGameProvider):
    key = "mock"

    def __init__(self, db: AsyncIOMotorDatabase):
        self.db = db

    async def get_categories(self) -> list[dict[str, Any]]:
        cursor = self.db.game_categories.find({"status": "active"}).sort("sort_order", 1)
        return serialize_many(await cursor.to_list(length=100))

    async def get_games(
        self, *, category: str | None = None, featured: bool | None = None, search: str | None = None
    ) -> list[dict[str, Any]]:
        query: dict[str, Any] = {"status": "active"}
        if category:
            query["category"] = category
        if featured is not None:
            query["featured"] = featured
        if search:
            query["name"] = {"$regex": search, "$options": "i"}
        cursor = self.db.games.find(query).sort([("sort_order", 1), ("name", 1)])
        return serialize_many(await cursor.to_list(length=200))

    async def get_game_details(self, slug: str) -> dict[str, Any] | None:
        doc = await self.db.games.find_one({"slug": slug})
        return serialize(doc)
