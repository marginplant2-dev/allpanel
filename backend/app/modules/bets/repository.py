"""Data access for the bets collection."""
from __future__ import annotations

from typing import Any

from bson import ObjectId
from motor.motor_asyncio import AsyncIOMotorDatabase
from pymongo import DESCENDING

from app.core.enums import BetStatus
from app.utils.ids import to_object_id


class BetRepository:
    def __init__(self, db: AsyncIOMotorDatabase):
        self.col = db.bets

    async def insert(self, doc: dict[str, Any]) -> None:
        result = await self.col.insert_one(doc)
        doc["_id"] = result.inserted_id

    async def get(self, bet_id: str) -> dict[str, Any] | None:
        return await self.col.find_one({"_id": to_object_id(bet_id)})

    async def list_for_user(
        self, user_id: str, *, status: str | None, skip: int, limit: int
    ) -> tuple[list[dict[str, Any]], int]:
        query: dict[str, Any] = {"user_id": user_id}
        if status:
            query["status"] = status
        total = await self.col.count_documents(query)
        cursor = self.col.find(query).sort("placed_at", DESCENDING).skip(skip).limit(limit)
        docs = await cursor.to_list(length=limit)
        return docs, total

    async def pending_event_ids(self) -> list[str]:
        return await self.col.distinct("event_id", {"status": BetStatus.PENDING.value})

    async def pending_for_event(self, event_id: str) -> list[dict[str, Any]]:
        cursor = self.col.find({"event_id": event_id, "status": BetStatus.PENDING.value})
        return await cursor.to_list(length=1000)

    async def claim_settlement(
        self, bet_id: ObjectId, *, status: str, payout: float, settled_at: Any
    ) -> dict[str, Any] | None:
        """Atomically move a PENDING bet to its final status; None if already settled (race guard)."""
        return await self.col.find_one_and_update(
            {"_id": bet_id, "status": BetStatus.PENDING.value},
            {"$set": {"status": status, "payout": payout, "settled_at": settled_at}},
        )
