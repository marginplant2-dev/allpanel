"""Business logic for user management with hierarchy enforcement."""
from __future__ import annotations

from typing import Any

from motor.motor_asyncio import AsyncIOMotorDatabase

from app.core.dependencies import CurrentUser
from app.core.enums import Role, UserStatus
from app.core.exceptions import (
    ConflictError,
    NotFoundError,
    PermissionDeniedError,
    ValidationError,
)
from app.core.security import hash_password
from app.modules.audit.models import AuditAction
from app.modules.audit.service import record_audit
from app.modules.users.repository import UserRepository
from app.modules.users.schema import UserCreate, UserUpdate
from app.utils.ids import serialize
from app.utils.time import utcnow


class UserService:
    def __init__(self, db: AsyncIOMotorDatabase):
        self.db = db
        self.repo = UserRepository(db)

    # ---- reads ----
    async def get_manageable(self, actor: CurrentUser, user_id: str) -> dict[str, Any]:
        doc = await self.repo.get_by_id(user_id)
        if doc is None:
            raise NotFoundError("User not found")
        target = CurrentUser(doc)
        if not actor.can_manage(target):
            raise PermissionDeniedError("This user is outside your hierarchy")
        return doc

    async def list_users(
        self,
        actor: CurrentUser,
        *,
        skip: int,
        limit: int,
        search: str | None,
        role: Role | None,
        status: UserStatus | None,
        sort_field: str,
        sort_dir: int,
    ) -> tuple[list[dict[str, Any]], int]:
        scope = await self.repo.visible_query(actor.role.value, actor.id)
        filters: dict[str, Any] = {}
        if search:
            filters["$or"] = [
                {"username": {"$regex": search, "$options": "i"}},
                {"full_name": {"$regex": search, "$options": "i"}},
            ]
        if role:
            filters["role"] = role.value
        if status:
            filters["status"] = status.value
        return await self.repo.list_scoped(
            scope=scope,
            filters=filters,
            skip=skip,
            limit=limit,
            sort_field=sort_field,
            sort_dir=sort_dir,
        )

    # ---- writes ----
    async def create_user(
        self, actor: CurrentUser, payload: UserCreate, *, ip: str | None = None
    ) -> dict[str, Any]:
        # Resolve parent (defaults to the actor).
        if payload.parent_id:
            parent_doc = await self.repo.get_by_id(payload.parent_id)
            if parent_doc is None:
                raise NotFoundError("Parent account not found")
            parent = CurrentUser(parent_doc)
            if not actor.can_manage(parent):
                raise PermissionDeniedError("Parent account is outside your hierarchy")
        else:
            parent = actor

        # Permission: actor and parent must both be allowed to create this role.
        if not actor.role.can_create(payload.role):
            raise PermissionDeniedError(
                f"{actor.role.value} cannot create a {payload.role.value}"
            )
        if not parent.role.can_create(payload.role):
            raise ValidationError(
                f"A {payload.role.value} cannot be placed under a {parent.role.value}"
            )

        if await self.repo.get_by_username(payload.username):
            raise ConflictError("Username already exists")

        now = utcnow()
        doc = {
            "username": payload.username,
            "password_hash": hash_password(payload.password),
            "full_name": payload.full_name,
            "role": payload.role.value,
            "parent_id": parent.id,
            "hierarchy_path": [*parent.hierarchy_path, parent.id],
            "status": payload.status.value,
            "credit_limit": payload.credit_limit,
            "notes": payload.notes,
            "two_factor_enabled": False,
            "created_at": now,
            "updated_at": now,
            "last_login": None,
        }
        try:
            user_id = await self.repo.insert(doc)
        except Exception as exc:  # duplicate key race
            if "duplicate key" in str(exc).lower():
                raise ConflictError("Username already exists") from exc
            raise

        # Bootstrap an empty wallet (credits are allocated via transfers).
        await self.db.wallets.update_one(
            {"_id": user_id},
            {
                "$setOnInsert": {
                    "available_balance": 0.0,
                    "locked_balance": 0.0,
                    "updated_at": now,
                }
            },
            upsert=True,
        )

        await record_audit(
            self.db,
            actor_id=actor.id,
            action=AuditAction.USER_CREATED,
            target_id=user_id,
            metadata={"role": payload.role.value, "username": payload.username},
            ip_address=ip,
        )
        created = await self.repo.get_by_id(user_id)
        return created  # type: ignore[return-value]

    async def update_user(
        self, actor: CurrentUser, user_id: str, payload: UserUpdate, *, ip: str | None = None
    ) -> dict[str, Any]:
        await self.get_manageable(actor, user_id)
        if actor.id == user_id and payload.status is UserStatus.SUSPENDED:
            raise ValidationError("You cannot suspend your own account")

        changes: dict[str, Any] = {"updated_at": utcnow()}
        if payload.full_name is not None:
            changes["full_name"] = payload.full_name
        if payload.password is not None:
            changes["password_hash"] = hash_password(payload.password)
        if payload.credit_limit is not None:
            changes["credit_limit"] = payload.credit_limit
        if payload.notes is not None:
            changes["notes"] = payload.notes
        if payload.status is not None:
            changes["status"] = payload.status.value

        updated = await self.repo.update(user_id, changes)
        await record_audit(
            self.db,
            actor_id=actor.id,
            action=AuditAction.USER_UPDATED,
            target_id=user_id,
            metadata={k: v for k, v in changes.items() if k != "password_hash"},
            ip_address=ip,
        )
        return updated  # type: ignore[return-value]

    async def set_status(
        self, actor: CurrentUser, user_id: str, status: UserStatus, *, ip: str | None = None
    ) -> dict[str, Any]:
        if actor.id == user_id:
            raise ValidationError("You cannot change the status of your own account")
        await self.get_manageable(actor, user_id)
        updated = await self.repo.update(
            user_id, {"status": status.value, "updated_at": utcnow()}
        )
        action = (
            AuditAction.USER_SUSPENDED
            if status is UserStatus.SUSPENDED
            else AuditAction.USER_ACTIVATED
        )
        await record_audit(
            self.db, actor_id=actor.id, action=action, target_id=user_id, ip_address=ip
        )
        return updated  # type: ignore[return-value]


def public_user(doc: dict[str, Any]) -> dict[str, Any]:
    data = serialize(doc) or {}
    data.pop("password_hash", None)
    return data
