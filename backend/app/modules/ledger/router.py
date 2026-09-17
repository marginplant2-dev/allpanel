"""Credit transfer & ledger endpoints."""
from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, Header, Query, Request

from app.core.database import get_database
from app.core.dependencies import AdminUserDep, CurrentUserDep
from app.core.responses import ok
from app.modules.ledger.schema import TransferRequest
from app.modules.ledger.service import LedgerService
from app.utils.ids import serialize_many
from app.utils.pagination import PageParams, build_page, pagination_params

router = APIRouter(prefix="/credits", tags=["credits"])


@router.post("/transfer", status_code=201)
async def transfer(
    payload: TransferRequest,
    request: Request,
    actor: AdminUserDep,
    idempotency_key: Annotated[str | None, Header(alias="Idempotency-Key")] = None,
):
    service = LedgerService(get_database())
    txn = await service.transfer(
        actor,
        payload,
        idempotency_key=idempotency_key,
        ip=getattr(request.state, "client_ip", None),
    )
    return ok(txn, message="Transfer completed")


@router.get("/history")
async def history(
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


@router.get("/ledger")
async def ledger(
    actor: AdminUserDep,
    params: Annotated[PageParams, Depends(pagination_params)],
):
    service = LedgerService(get_database())
    docs, total = await service.scoped_ledger(actor, skip=params.skip, limit=params.limit)
    return ok(build_page(serialize_many(docs), total, params))
