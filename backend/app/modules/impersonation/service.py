"""Controlled 'view as' impersonation for higher-level admins.

Never exposes passwords. Issues a short-lived access token scoped to the target
account while recording the original admin id so the session can be reverted and
fully audited.
"""
from __future__ import annotations

from typing import Any

from motor.motor_asyncio import AsyncIOMotorDatabase

from app.core.dependencies import CurrentUser
from app.core.enums import ADMIN_ROLES, Role
from app.core.exceptions import NotFoundError, PermissionDeniedError, ValidationError
from app.core.security import create_access_token
from app.modules.audit.models import AuditAction
from app.modules.audit.service import record_audit
from app.modules.users.service import public_user
from app.utils.ids import to_object_id
from app.utils.time import utcnow


class ImpersonationService:
    def __init__(self, db: AsyncIOMotorDatabase):
        self.db = db

    async def start(self, actor: CurrentUser, target_id: str, *, ip: str | None = None) -> dict[str, Any]:
        if actor.impersonator_id:
            raise ValidationError("Already impersonating; end the current session first")
        if actor.role not in ADMIN_ROLES or actor.role is Role.AGENT:
            raise PermissionDeniedError("Your role cannot impersonate accounts")
        if target_id == actor.id:
            raise ValidationError("Cannot impersonate yourself")

        target = await self.db.users.find_one({"_id": to_object_id(target_id)})
        if target is None:
            raise NotFoundError("Target account not found")
        target_user = CurrentUser(target)
        if not target_user.is_downline_of(actor):
            raise PermissionDeniedError("Target is outside your hierarchy")

        now = utcnow()
        await self.db.impersonation_sessions.insert_one(
            {"admin_id": actor.id, "target_id": target_id, "started_at": now, "ended_at": None}
        )
        await record_audit(
            self.db, actor_id=actor.id, action=AuditAction.IMPERSONATION_STARTED,
            target_id=target_id, ip_address=ip,
        )
        token = create_access_token(target_id, {"role": target["role"], "impersonator_id": actor.id})
        return {"access_token": token, "token_type": "bearer", "user": public_user(target), "impersonator_id": actor.id}

    async def end(self, actor: CurrentUser, *, ip: str | None = None) -> dict[str, Any]:
        if not actor.impersonator_id:
            raise ValidationError("Not currently impersonating")
        admin = await self.db.users.find_one({"_id": to_object_id(actor.impersonator_id)})
        if admin is None:
            raise NotFoundError("Original account not found")

        await self.db.impersonation_sessions.update_one(
            {"admin_id": actor.impersonator_id, "target_id": actor.id, "ended_at": None},
            {"$set": {"ended_at": utcnow()}},
        )
        await record_audit(
            self.db, actor_id=actor.impersonator_id, action=AuditAction.IMPERSONATION_ENDED,
            target_id=actor.id, ip_address=ip,
        )
        token = create_access_token(actor.impersonator_id, {"role": admin["role"]})
        return {"access_token": token, "token_type": "bearer", "user": public_user(admin)}
