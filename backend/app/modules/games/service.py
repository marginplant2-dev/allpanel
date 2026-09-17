"""Game catalogue service. Public reads flow through the provider layer;
admin writes persist to MongoDB with audit logging.
"""
from __future__ import annotations

from typing import Any

from motor.motor_asyncio import AsyncIOMotorDatabase

from app.core.dependencies import CurrentUser
from app.core.exceptions import ConflictError, NotFoundError
from app.modules.audit.models import AuditAction
from app.modules.audit.service import record_audit
from app.modules.games.repository import GameRepository
from app.modules.games.schema import CategoryCreate, GameCreate, GameUpdate
from app.modules.providers.provider_factory import get_game_provider
from app.utils.ids import serialize
from app.utils.time import utcnow


class GameService:
    def __init__(self, db: AsyncIOMotorDatabase):
        self.db = db
        self.repo = GameRepository(db)
        self.provider = get_game_provider(db)

    # ---- public reads (provider-backed) ----
    async def catalogue(
        self, *, category: str | None, featured: bool | None, search: str | None
    ) -> list[dict[str, Any]]:
        return await self.provider.get_games(category=category, featured=featured, search=search)

    async def categories(self) -> list[dict[str, Any]]:
        return await self.provider.get_categories()

    async def game_by_slug(self, slug: str) -> dict[str, Any]:
        doc = await self.provider.get_game_details(slug)
        if doc is None:
            raise NotFoundError("Game not found")
        return doc

    # ---- admin writes ----
    async def create_game(self, actor: CurrentUser, payload: GameCreate, *, ip: str | None = None) -> dict[str, Any]:
        if await self.repo.get_by_slug(payload.slug):
            raise ConflictError("A game with this slug already exists")
        now = utcnow()
        doc = {**payload.model_dump(), "created_at": now, "updated_at": now}
        game_id = await self.repo.insert_game(doc)
        await record_audit(
            self.db, actor_id=actor.id, action=AuditAction.GAME_CREATED, target_id=game_id,
            metadata={"slug": payload.slug}, ip_address=ip,
        )
        return serialize(await self.repo.get_game(game_id))  # type: ignore[return-value]

    async def update_game(self, actor: CurrentUser, game_id: str, payload: GameUpdate, *, ip: str | None = None) -> dict[str, Any]:
        existing = await self.repo.get_game(game_id)
        if existing is None:
            raise NotFoundError("Game not found")
        changes = {k: v for k, v in payload.model_dump(exclude_unset=True).items() if v is not None}
        changes["updated_at"] = utcnow()
        updated = await self.repo.update_game(game_id, changes)
        await record_audit(
            self.db, actor_id=actor.id, action=AuditAction.GAME_UPDATED, target_id=game_id,
            metadata=changes, ip_address=ip,
        )
        return serialize(updated)  # type: ignore[return-value]

    async def delete_game(self, actor: CurrentUser, game_id: str, *, ip: str | None = None) -> None:
        deleted = await self.repo.delete_game(game_id)
        if not deleted:
            raise NotFoundError("Game not found")
        await record_audit(
            self.db, actor_id=actor.id, action=AuditAction.GAME_UPDATED, target_id=game_id,
            metadata={"deleted": True}, ip_address=ip,
        )

    async def list_admin(self, *, query: dict[str, Any], skip: int, limit: int) -> tuple[list[dict[str, Any]], int]:
        docs, total = await self.repo.list_games_admin(query=query, skip=skip, limit=limit)
        return [serialize(d) for d in docs], total  # type: ignore[misc]

    async def create_category(self, payload: CategoryCreate) -> dict[str, Any]:
        existing = await self.db.game_categories.find_one({"key": payload.key})
        if existing:
            raise ConflictError("Category key already exists")
        game_id = await self.repo.insert_category(payload.model_dump())
        return serialize(await self.db.game_categories.find_one({"_id": _oid(game_id)}))  # type: ignore[return-value]


def _oid(value: str):
    from app.utils.ids import to_object_id

    return to_object_id(value)
