"""Data access for the users collection."""
from __future__ import annotations

from typing import Any

from motor.motor_asyncio import AsyncIOMotorDatabase
from pymongo import ASCENDING, DESCENDING

from app.core.enums import SEES_GRANDCHILD_PLAYERS, Role
from app.utils.ids import to_object_id


class UserRepository:
    def __init__(self, db: AsyncIOMotorDatabase):
        self.db = db
        self.col = db.users

    async def get_by_id(self, user_id: str) -> dict[str, Any] | None:
        return await self.col.find_one({"_id": to_object_id(user_id)})

    async def get_by_username(self, username: str) -> dict[str, Any] | None:
        return await self.col.find_one({"username": username})

    async def insert(self, doc: dict[str, Any]) -> str:
        result = await self.col.insert_one(doc)
        return str(result.inserted_id)

    async def update(self, user_id: str, changes: dict[str, Any]) -> dict[str, Any] | None:
        return await self.col.find_one_and_update(
            {"_id": to_object_id(user_id)},
            {"$set": changes},
            return_document=True,
        )

    async def child_ids(self, parent_id: str, *, role: str | None = None) -> list[str]:
        query: dict[str, Any] = {"parent_id": parent_id}
        if role:
            query["role"] = role
        cursor = self.col.find(query, {"_id": 1}).limit(1000)
        return [str(d["_id"]) for d in await cursor.to_list(length=1000)]

    async def visible_query(self, actor_role: str, actor_id: str) -> dict[str, Any]:
        """Who appears on this account's own dashboard.

        Direct children only — an upline never sees the players its downline
        signed up; it has to "login as" that account to see them. A MASTER is the
        single exception: it runs its agents' books, so their players roll up.
        """
        parents = [actor_id]
        if Role(actor_role) in SEES_GRANDCHILD_PLAYERS:
            parents += await self.child_ids(actor_id, role=Role.AGENT.value)
        return {"parent_id": {"$in": parents}}

    async def list_scoped(
        self,
        *,
        scope: dict[str, Any],
        filters: dict[str, Any],
        skip: int,
        limit: int,
        sort_field: str = "created_at",
        sort_dir: int = DESCENDING,
    ) -> tuple[list[dict[str, Any]], int]:
        query: dict[str, Any] = {**scope, **filters}
        total = await self.col.count_documents(query)
        cursor = (
            self.col.find(query, {"password_hash": 0})
            .sort(sort_field, sort_dir if sort_dir in (ASCENDING, DESCENDING) else DESCENDING)
            .skip(skip)
            .limit(limit)
        )
        docs = await cursor.to_list(length=limit)
        return docs, total

    async def count_children(self, parent_id: str) -> int:
        return await self.col.count_documents({"parent_id": parent_id})
