"""Sports betting endpoints: place, list mine, detail, admin settle-now."""
from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, Query, Request

from app.core.database import get_database
from app.core.dependencies import AdminUserDep, CurrentUserDep
from app.core.responses import ok
from app.modules.bets.schema import PlaceBetRequest
from app.modules.bets.service import BetService
from app.utils.pagination import PageParams, build_page, pagination_params

router = APIRouter(prefix="/bets", tags=["bets"])


@router.post("", status_code=201)
async def place_bet(payload: PlaceBetRequest, actor: CurrentUserDep, request: Request):
    service = BetService(get_database())
    doc = await service.place_bet(actor, payload, ip=getattr(request.state, "client_ip", None))
    return ok(doc, message="Bet placed")


@router.get("/mine")
async def my_bets(
    actor: CurrentUserDep,
    params: Annotated[PageParams, Depends(pagination_params)],
    status: str | None = Query(default=None, pattern="^(PENDING|WON|LOST)$"),
):
    service = BetService(get_database())
    docs, total = await service.my_bets(actor.id, status=status, skip=params.skip, limit=params.limit)
    return ok(build_page(docs, total, params))


@router.get("/{bet_id}")
async def bet_detail(bet_id: str, actor: CurrentUserDep):
    service = BetService(get_database())
    return ok(await service.get_bet(actor, bet_id))


@router.post("/settle")
async def settle_now(actor: AdminUserDep):
    service = BetService(get_database())
    count = await service.settle_pending()
    return ok({"settled": count}, message=f"Settled {count} bet(s)")
