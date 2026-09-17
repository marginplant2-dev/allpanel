"""Authentication endpoints."""
from __future__ import annotations

from fastapi import APIRouter, Request

from app.core.database import get_database
from app.core.dependencies import CurrentUserDep
from app.core.responses import ok
from app.modules.auth.schema import LoginRequest, RefreshRequest, RegisterRequest
from app.modules.auth.service import AuthService
from app.modules.users.service import public_user

router = APIRouter(prefix="/auth", tags=["auth"])


def _ip(request: Request) -> str | None:
    return getattr(request.state, "client_ip", None)


@router.post("/register", status_code=201)
async def register(payload: RegisterRequest, request: Request):
    service = AuthService(get_database())
    session = await service.register(payload, ip=_ip(request))
    return ok(session, message="Registration successful")


@router.post("/login")
async def login(payload: LoginRequest, request: Request):
    service = AuthService(get_database())
    ua = request.headers.get("User-Agent")
    session = await service.login(payload.username, payload.password, ip=_ip(request), ua=ua)
    return ok(session, message="Login successful")


@router.post("/refresh")
async def refresh(payload: RefreshRequest):
    service = AuthService(get_database())
    tokens = await service.refresh(payload.refresh_token)
    return ok(tokens)


@router.post("/logout")
async def logout(payload: RefreshRequest, request: Request, actor: CurrentUserDep):
    service = AuthService(get_database())
    await service.logout(payload.refresh_token, actor_id=actor.id, ip=_ip(request))
    return ok(message="Logged out")


@router.get("/me")
async def me(actor: CurrentUserDep):
    return ok(public_user(actor.raw))
