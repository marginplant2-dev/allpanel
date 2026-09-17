"""Hierarchy endpoints (admin roles)."""
from __future__ import annotations

from fastapi import APIRouter, Query

from app.core.database import get_database
from app.core.dependencies import AdminUserDep
from app.core.responses import ok
from app.modules.hierarchy.service import HierarchyService

router = APIRouter(prefix="/hierarchy", tags=["hierarchy"])


@router.get("/children")
async def children(actor: AdminUserDep, parent_id: str | None = Query(default=None)):
    service = HierarchyService(get_database())
    return ok(await service.children(actor, parent_id))


@router.get("/tree")
async def tree(actor: AdminUserDep):
    service = HierarchyService(get_database())
    return ok(await service.subtree(actor))


@router.get("/downline")
async def downline(actor: AdminUserDep, parent_id: str | None = Query(default=None)):
    service = HierarchyService(get_database())
    return ok(await service.children(actor, parent_id))
