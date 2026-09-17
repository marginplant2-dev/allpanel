"""Notification service: persist + push over WebSocket."""
from __future__ import annotations

from typing import Any

from motor.motor_asyncio import AsyncIOMotorDatabase

from app.core.exceptions import NotFoundError
from app.utils.ids import serialize, serialize_many, to_object_id
from app.utils.time import utcnow
from app.websocket.events import publish_notification


class NotificationService:
    def __init__(self, db: AsyncIOMotorDatabase):
        self.db = db

    async def create(
        self, user_id: str, *, type_: str, title: str, body: str, metadata: dict[str, Any] | None = None
    ) -> dict[str, Any]:
        doc = {
            "user_id": user_id,
            "type": type_,
            "title": title,
            "body": body,
            "read": False,
            "metadata": metadata or {},
            "created_at": utcnow(),
        }
        result = await self.db.notifications.insert_one(doc)
        doc["_id"] = result.inserted_id
        payload = serialize(doc)
        await publish_notification(user_id, payload)  # type: ignore[arg-type]
        return payload  # type: ignore[return-value]

    async def list(self, user_id: str, *, skip: int, limit: int) -> tuple[list[dict[str, Any]], int, int]:
        query = {"user_id": user_id}
        total = await self.db.notifications.count_documents(query)
        unread = await self.db.notifications.count_documents({**query, "read": False})
        cursor = self.db.notifications.find(query).sort("created_at", -1).skip(skip).limit(limit)
        docs = await cursor.to_list(length=limit)
        return serialize_many(docs), total, unread

    async def mark_read(self, user_id: str, notification_id: str) -> None:
        result = await self.db.notifications.update_one(
            {"_id": to_object_id(notification_id), "user_id": user_id}, {"$set": {"read": True}}
        )
        if result.matched_count == 0:
            raise NotFoundError("Notification not found")

    async def mark_all_read(self, user_id: str) -> int:
        result = await self.db.notifications.update_many(
            {"user_id": user_id, "read": False}, {"$set": {"read": True}}
        )
        return result.modified_count
