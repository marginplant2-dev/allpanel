"""Data access for games and game categories."""
from __future__ import annotations

from typing import Any

from motor.motor_asyncio import AsyncIOMotorDatabase

from app.utils.ids import to_object_id


class GameRepository:
    def __init__(self, db: AsyncIOMotorDatabase):
        self.db = db
        self.games = db.games
        self.categories = db.game_categories

    async def insert_game(self, doc: dict[str, Any]) -> str:
        result = await self.games.insert_one(doc)
        return str(result.inserted_id)

    async def get_game(self, game_id: str) -> dict[str, Any] | None:
        return await self.games.find_one({"_id": to_object_id(game_id)})

    async def get_by_slug(self, slug: str) -> dict[str, Any] | None:
        return await self.games.find_one({"slug": slug})

    async def update_game(self, game_id: str, changes: dict[str, Any]) -> dict[str, Any] | None:
        return await self.games.find_one_and_update(
            {"_id": to_object_id(game_id)}, {"$set": changes}, return_document=True
        )

    async def delete_game(self, game_id: str) -> int:
        result = await self.games.delete_one({"_id": to_object_id(game_id)})
        return result.deleted_count

    async def list_games_admin(
        self, *, query: dict[str, Any], skip: int, limit: int
    ) -> tuple[list[dict[str, Any]], int]:
        total = await self.games.count_documents(query)
        cursor = self.games.find(query).sort([("sort_order", 1), ("name", 1)]).skip(skip).limit(limit)
        return await cursor.to_list(length=limit), total

    async def insert_category(self, doc: dict[str, Any]) -> str:
        result = await self.categories.insert_one(doc)
        return str(result.inserted_id)
