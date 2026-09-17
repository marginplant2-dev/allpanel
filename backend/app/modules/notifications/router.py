"""Notification endpoints for the authenticated user."""
from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends

from app.core.database import get_database
from app.core.dependencies import CurrentUserDep
from app.core.responses import ok
from app.modules.notifications.service import NotificationService
from app.utils.pagination import PageParams, build_page, pagination_params

router = APIRouter(prefix="/notifications", tags=["notifications"])


@router.get("")
async def list_notifications(
    actor: CurrentUserDep,
    params: Annotated[PageParams, Depends(pagination_params)],
):
    service = NotificationService(get_database())
    items, total, unread = await service.list(actor.id, skip=params.skip, limit=params.limit)
    page = build_page(items, total, params)
    page["unread"] = unread
    return ok(page)


@router.post("/{notification_id}/read")
async def mark_read(notification_id: str, actor: CurrentUserDep):
    service = NotificationService(get_database())
    await service.mark_read(actor.id, notification_id)
    return ok(message="Marked as read")


@router.post("/read-all")
async def mark_all_read(actor: CurrentUserDep):
    service = NotificationService(get_database())
    count = await service.mark_all_read(actor.id)
    return ok({"updated": count}, message="All marked as read")
