"""Hierarchy traversal: direct children and bounded subtree."""
from __future__ import annotations

from typing import Any

from motor.motor_asyncio import AsyncIOMotorDatabase

from app.core.dependencies import CurrentUser
from app.core.enums import Role
from app.core.exceptions import PermissionDeniedError

_SUBTREE_NODE_CAP = 1000


class HierarchyService:
    def __init__(self, db: AsyncIOMotorDatabase):
        self.db = db

    def _summary(self, doc: dict[str, Any]) -> dict[str, Any]:
        return {
            "id": str(doc["_id"]),
            "username": doc["username"],
            "full_name": doc.get("full_name"),
            "role": doc["role"],
            "status": doc.get("status"),
            "parent_id": doc.get("parent_id"),
        }

    async def children(self, actor: CurrentUser, parent_id: str | None) -> list[dict[str, Any]]:
        target_parent = parent_id or actor.id
        # The requested parent must be the actor or within the actor's downline.
        if target_parent != actor.id and actor.role is not Role.MOTHER_ADMIN:
            parent_doc = await self.db.users.find_one(
                {"_id": _oid(target_parent)}, {"hierarchy_path": 1}
            )
            if parent_doc is None or actor.id not in parent_doc.get("hierarchy_path", []):
                raise PermissionDeniedError("Node is outside your hierarchy")
        cursor = self.db.users.find({"parent_id": target_parent}, {"password_hash": 0}).sort(
            "username", 1
        )
        docs = await cursor.to_list(length=500)
        return [self._summary(d) for d in docs]

    async def subtree(self, actor: CurrentUser) -> dict[str, Any]:
        query: dict[str, Any] = {} if actor.role is Role.MOTHER_ADMIN else {"hierarchy_path": actor.id}
        cursor = self.db.users.find(query, {"password_hash": 0}).limit(_SUBTREE_NODE_CAP)
        docs = await cursor.to_list(length=_SUBTREE_NODE_CAP)
        # The org chart shows the admin line all the way down, but players belong
        # to whoever signed them up: only the actor's own are listed here.
        docs = [
            d
            for d in docs
            if d.get("role") != Role.USER.value or d.get("parent_id") == actor.id
        ]

        nodes: dict[str, dict[str, Any]] = {}
        for d in docs:
            node = self._summary(d)
            node["children"] = []
            nodes[node["id"]] = node

        roots: list[dict[str, Any]] = []
        for node in nodes.values():
            parent_id = node["parent_id"]
            if parent_id in nodes and parent_id != node["id"]:
                nodes[parent_id]["children"].append(node)
            else:
                roots.append(node)

        # Ensure the actor themselves is the single root for scoped admins.
        actor_doc = await self.db.users.find_one({"_id": _oid(actor.id)}, {"password_hash": 0})
        if actor.role is not Role.MOTHER_ADMIN and actor_doc is not None:
            root = self._summary(actor_doc)
            root["children"] = [n for n in nodes.values() if n["parent_id"] == actor.id]
            return {"nodes": len(docs), "root": root}

        return {"nodes": len(docs), "roots": roots}


def _oid(value: str):
    from app.utils.ids import to_object_id

    return to_object_id(value)
