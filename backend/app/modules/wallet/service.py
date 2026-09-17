"""Wallet read service."""
from __future__ import annotations

from typing import Any

from motor.motor_asyncio import AsyncIOMotorDatabase

from app.modules.wallet.repository import WalletRepository


class WalletService:
    def __init__(self, db: AsyncIOMotorDatabase):
        self.repo = WalletRepository(db)

    async def get_wallet(self, user_id: str) -> dict[str, Any]:
        doc = await self.repo.ensure(user_id)
        return {
            "user_id": user_id,
            "available_balance": doc.get("available_balance", 0.0),
            "locked_balance": doc.get("locked_balance", 0.0),
            "updated_at": doc.get("updated_at"),
        }
