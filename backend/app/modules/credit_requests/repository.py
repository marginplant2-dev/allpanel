"""Data access for the credit_requests collection."""
from __future__ import annotations

from typing import Any

from motor.motor_asyncio import AsyncIOMotorDatabase
from pymongo import DESCENDING

from app.core.enums import RequestStatus
from app.utils.ids import to_object_id


class CreditRequestRepository:
    def __init__(self, db: AsyncIOMotorDatabase):
        self.col = db.credit_requests

    async def insert(self, doc: dict[str, Any]) -> None:
        result = await self.col.insert_one(doc)
        doc["_id"] = result.inserted_id

    async def get(self, request_id: str) -> dict[str, Any] | None:
        return await self.col.find_one({"_id": to_object_id(request_id)})

    async def claim(self, request_id: str) -> dict[str, Any] | None:
        """Atomically move a PENDING request to PROCESSING; None if already decided."""
        return await self.col.find_one_and_update(
            {"_id": to_object_id(request_id), "status": RequestStatus.PENDING.value},
            {"$set": {"status": RequestStatus.PROCESSING.value}},
        )

    async def finalize(
        self,
        request_id: str,
        *,
        status: str,
        decision_note: str | None,
        decided_at,
        transaction_id: str | None = None,
    ) -> None:
        update: dict[str, Any] = {"status": status, "decision_note": decision_note, "decided_at": decided_at}
        if transaction_id:
            update["transaction_id"] = transaction_id
        await self.col.update_one({"_id": to_object_id(request_id)}, {"$set": update})

    async def list(
        self, query: dict[str, Any], *, skip: int, limit: int
    ) -> tuple[list[dict[str, Any]], int]:
        total = await self.col.count_documents(query)
        cursor = self.col.find(query).sort("created_at", DESCENDING).skip(skip).limit(limit)
        docs = await cursor.to_list(length=limit)
        return docs, total
