"""Impersonation (view-as) endpoints."""
from __future__ import annotations

from fastapi import APIRouter, Request
from pydantic import BaseModel

from app.core.database import get_database
from app.core.dependencies import CurrentUserDep
from app.core.responses import ok
from app.modules.impersonation.service import ImpersonationService

router = APIRouter(prefix="/impersonation", tags=["impersonation"])


class StartRequest(BaseModel):
    target_id: str


def _ip(request: Request) -> str | None:
    return getattr(request.state, "client_ip", None)


@router.post("/start")
async def start(payload: StartRequest, request: Request, actor: CurrentUserDep):
    service = ImpersonationService(get_database())
    return ok(await service.start(actor, payload.target_id, ip=_ip(request)), message="Impersonation started")


@router.post("/end")
async def end(request: Request, actor: CurrentUserDep):
    service = ImpersonationService(get_database())
    return ok(await service.end(actor, ip=_ip(request)), message="Impersonation ended")
