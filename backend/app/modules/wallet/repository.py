"""Data access for the wallets collection.

A wallet document uses the owning user's id as its `_id` (1:1 with the user).
Balances are only ever changed through atomic operations here.
"""
from __future__ import annotations

from typing import Any

from motor.motor_asyncio import AsyncIOMotorDatabase

from app.utils.time import utcnow


class WalletRepository:
    def __init__(self, db: AsyncIOMotorDatabase):
        self.col = db.wallets

    async def ensure(self, user_id: str) -> dict[str, Any]:
        await self.col.update_one(
            {"_id": user_id},
            {"$setOnInsert": {"available_balance": 0.0, "locked_balance": 0.0, "updated_at": utcnow()}},
            upsert=True,
        )
        return await self.col.find_one({"_id": user_id})  # type: ignore[return-value]

    async def get(self, user_id: str) -> dict[str, Any] | None:
        return await self.col.find_one({"_id": user_id})

    async def try_debit(self, user_id: str, amount: float) -> bool:
        """Atomically debit `amount` iff sufficient available balance exists."""
        result = await self.col.find_one_and_update(
            {"_id": user_id, "available_balance": {"$gte": amount}},
            {"$inc": {"available_balance": -amount}, "$set": {"updated_at": utcnow()}},
        )
        return result is not None

    async def credit(self, user_id: str, amount: float) -> None:
        await self.col.update_one(
            {"_id": user_id},
            {
                "$inc": {"available_balance": amount},
                "$set": {"updated_at": utcnow()},
                "$setOnInsert": {"locked_balance": 0.0},
            },
            upsert=True,
        )

    async def try_lock(self, user_id: str, amount: float) -> bool:
        """Atomically move `amount` from available to locked (a bet stake hold)."""
        result = await self.col.find_one_and_update(
            {"_id": user_id, "available_balance": {"$gte": amount}},
            {"$inc": {"available_balance": -amount, "locked_balance": amount}, "$set": {"updated_at": utcnow()}},
        )
        return result is not None

    async def unlock(self, user_id: str, amount: float) -> None:
        """Reverse a try_lock (used only if the bet record fails to persist after the hold)."""
        await self.col.update_one(
            {"_id": user_id},
            {"$inc": {"available_balance": amount, "locked_balance": -amount}, "$set": {"updated_at": utcnow()}},
        )

    async def settle_win(self, user_id: str, *, stake: float, payout: float) -> None:
        await self.col.update_one(
            {"_id": user_id},
            {"$inc": {"locked_balance": -stake, "available_balance": payout}, "$set": {"updated_at": utcnow()}},
        )

    async def settle_loss(self, user_id: str, *, stake: float) -> None:
        await self.col.update_one(
            {"_id": user_id},
            {"$inc": {"locked_balance": -stake}, "$set": {"updated_at": utcnow()}},
        )
