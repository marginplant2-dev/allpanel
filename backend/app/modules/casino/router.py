"""Casino endpoints: launch a provider game, and take the provider's wallet callbacks."""
from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Request

from app.core.database import get_database
from app.core.dependencies import CurrentUserDep
from app.core.responses import ok
from app.modules.casino.service import CasinoService
from app.utils.pagination import PageParams, build_page

router = APIRouter(prefix="/casino", tags=["casino"])


@router.post("/launch/{slug}")
async def launch_game(slug: str, user: CurrentUserDep):
    service = CasinoService(get_database())
    return ok(await service.launch(user, slug))


@router.post("/callback")
async def provider_callback(request: Request) -> dict[str, Any]:
    """Seamless wallet hook.

    Answers the provider's own envelope (a bare `balance`), not the platform one —
    the provider reads `balance` and nothing else.
    """
    payload = await request.json()
    service = CasinoService(get_database())
    result = await service.handle_callback(payload)
    return {**result, "data": {"balance": result["balance"]}}


@router.get("/rounds")
async def my_rounds(user: CurrentUserDep, page: int = 1, page_size: int = 20):
    service = CasinoService(get_database())
    params = PageParams(page=page, page_size=page_size)
    rows, total = await service.history(user.id, skip=params.skip, limit=params.limit)
    return ok(build_page(rows, total, params))
