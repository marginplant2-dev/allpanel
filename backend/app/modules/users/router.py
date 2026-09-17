"""User management endpoints (hierarchy-scoped, admin roles)."""
from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, Query, Request
from pymongo import ASCENDING, DESCENDING

from app.core.database import get_database
from app.core.dependencies import AdminUserDep, CurrentUserDep
from app.core.enums import Role, UserStatus
from app.core.responses import ok
from app.modules.users.schema import UserCreate, UserUpdate
from app.modules.users.service import UserService, public_user
from app.utils.pagination import PageParams, build_page, pagination_params

router = APIRouter(prefix="/users", tags=["users"])

_SORTABLE = {"created_at", "username", "role", "status", "last_login"}


@router.get("")
async def list_users(
    actor: AdminUserDep,
    params: Annotated[PageParams, Depends(pagination_params)],
    search: str | None = Query(default=None),
    role: Role | None = Query(default=None),
    status: UserStatus | None = Query(default=None),
    sort_by: str = Query(default="created_at"),
    order: str = Query(default="desc", pattern="^(asc|desc)$"),
):
    service = UserService(get_database())
    sort_field = sort_by if sort_by in _SORTABLE else "created_at"
    sort_dir = ASCENDING if order == "asc" else DESCENDING
    docs, total = await service.list_users(
        actor,
        skip=params.skip,
        limit=params.limit,
        search=search,
        role=role,
        status=status,
        sort_field=sort_field,
        sort_dir=sort_dir,
    )
    return ok(build_page([public_user(d) for d in docs], total, params))


@router.post("", status_code=201)
async def create_user(payload: UserCreate, request: Request, actor: AdminUserDep):
    service = UserService(get_database())
    doc = await service.create_user(actor, payload, ip=getattr(request.state, "client_ip", None))
    return ok(public_user(doc), message="User created")


@router.get("/{user_id}")
async def get_user(user_id: str, actor: CurrentUserDep):
    service = UserService(get_database())
    # A user may always read themselves; admins may read their downline.
    if actor.id == user_id:
        doc = await service.repo.get_by_id(user_id)
    else:
        doc = await service.get_manageable(actor, user_id)
    return ok(public_user(doc))


@router.patch("/{user_id}")
async def update_user(user_id: str, payload: UserUpdate, request: Request, actor: AdminUserDep):
    service = UserService(get_database())
    doc = await service.update_user(actor, user_id, payload, ip=getattr(request.state, "client_ip", None))
    return ok(public_user(doc), message="User updated")


@router.post("/{user_id}/suspend")
async def suspend_user(user_id: str, request: Request, actor: AdminUserDep):
    service = UserService(get_database())
    doc = await service.set_status(actor, user_id, UserStatus.SUSPENDED, ip=getattr(request.state, "client_ip", None))
    return ok(public_user(doc), message="User suspended")


@router.post("/{user_id}/activate")
async def activate_user(user_id: str, request: Request, actor: AdminUserDep):
    service = UserService(get_database())
    doc = await service.set_status(actor, user_id, UserStatus.ACTIVE, ip=getattr(request.state, "client_ip", None))
    return ok(public_user(doc), message="User activated")


@router.get("/{user_id}/activity")
async def user_activity(
    user_id: str,
    actor: AdminUserDep,
    params: Annotated[PageParams, Depends(pagination_params)],
):
    db = get_database()
    service = UserService(db)
    await service.get_manageable(actor, user_id)
    query = {"$or": [{"actor_id": user_id}, {"target_id": user_id}]}
    total = await db.audit_logs.count_documents(query)
    cursor = db.audit_logs.find(query).sort("created_at", -1).skip(params.skip).limit(params.limit)
    docs = await cursor.to_list(length=params.limit)
    from app.utils.ids import serialize_many

    return ok(build_page(serialize_many(docs), total, params))
