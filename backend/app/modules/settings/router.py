"""System settings endpoints."""
from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends, Request
from pydantic import BaseModel

from app.core.database import get_database
from app.core.dependencies import AdminUserDep, require_roles
from app.core.enums import Role
from app.core.responses import ok
from app.modules.settings.service import SettingsService

router = APIRouter(prefix="/settings", tags=["settings"])


class SettingsUpdate(BaseModel):
    feature_flags: dict[str, bool] | None = None
    api_config: dict[str, Any] | None = None


@router.get("")
async def get_settings(actor: AdminUserDep):
    service = SettingsService(get_database())
    return ok(await service.get())


@router.patch("")
async def update_settings(
    payload: SettingsUpdate,
    request: Request,
    actor=Depends(require_roles(Role.MOTHER_ADMIN)),
):
    service = SettingsService(get_database())
    changes = payload.model_dump(exclude_none=True)
    result = await service.update(actor.id, changes, ip=getattr(request.state, "client_ip", None))
    return ok(result, message="Settings updated")
