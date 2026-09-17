"""Data access for the transactions (ledger) collection."""
from __future__ import annotations

from typing import Any

from motor.motor_asyncio import AsyncIOMotorDatabase
from pymongo import DESCENDING


class LedgerRepository:
    def __init__(self, db: AsyncIOMotorDatabase):
        self.col = db.transactions

    async def get_by_idempotency_key(self, key: str) -> dict[str, Any] | None:
        return await self.col.find_one({"idempotency_key": key})

    async def get_by_transaction_id(self, transaction_id: str) -> dict[str, Any] | None:
        return await self.col.find_one({"transaction_id": transaction_id})

    async def insert(self, doc: dict[str, Any]) -> None:
        await self.col.insert_one(doc)

    async def set_status(self, transaction_id: str, status: str) -> None:
        await self.col.update_one(
            {"transaction_id": transaction_id}, {"$set": {"status": status}}
        )

    async def list(
        self,
        *,
        query: dict[str, Any],
        skip: int,
        limit: int,
    ) -> tuple[list[dict[str, Any]], int]:
        total = await self.col.count_documents(query)
        cursor = self.col.find(query).sort("created_at", DESCENDING).skip(skip).limit(limit)
        docs = await cursor.to_list(length=limit)
        return docs, total
