"""Audit log query endpoints (admin only)."""
from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, Query

from app.core.database import get_database
from app.core.dependencies import AdminUserDep
from app.core.enums import Role
from app.core.responses import ok
from app.utils.ids import serialize_many
from app.utils.pagination import PageParams, build_page, pagination_params

router = APIRouter(prefix="/audit", tags=["audit"])


@router.get("")
async def list_audit_logs(
    actor: AdminUserDep,
    params: Annotated[PageParams, Depends(pagination_params)],
    action: str | None = Query(default=None),
):
    db = get_database()
    query: dict = {}
    if action:
        query["action"] = action
    # Non-super admins only see their own actions and their downline's.
    if actor.role is not Role.MOTHER_ADMIN:
        query["actor_id"] = actor.id

    total = await db.audit_logs.count_documents(query)
    cursor = (
        db.audit_logs.find(query)
        .sort("created_at", -1)
        .skip(params.skip)
        .limit(params.limit)
    )
    docs = await cursor.to_list(length=params.limit)
    return ok(build_page(serialize_many(docs), total, params))
