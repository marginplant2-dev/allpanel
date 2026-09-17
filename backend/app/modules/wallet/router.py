"""Wallet endpoints for the authenticated user."""
from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, Query

from app.core.database import get_database
from app.core.dependencies import CurrentUserDep
from app.core.responses import ok
from app.modules.ledger.service import LedgerService
from app.modules.wallet.service import WalletService
from app.utils.ids import serialize_many
from app.utils.pagination import PageParams, build_page, pagination_params

router = APIRouter(prefix="/wallet", tags=["wallet"])


@router.get("")
async def my_wallet(actor: CurrentUserDep):
    service = WalletService(get_database())
    return ok(await service.get_wallet(actor.id))


@router.get("/transactions")
async def my_transactions(
    actor: CurrentUserDep,
    params: Annotated[PageParams, Depends(pagination_params)],
    direction: str | None = Query(default=None, pattern="^(in|out)$"),
    transaction_type: str | None = Query(default=None),
):
    service = LedgerService(get_database())
    docs, total = await service.history(
        actor.id,
        skip=params.skip,
        limit=params.limit,
        direction=direction,
        transaction_type=transaction_type,
    )
    return ok(build_page(serialize_many(docs), total, params))
