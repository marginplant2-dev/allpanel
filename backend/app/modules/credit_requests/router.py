"""Deposit / withdraw request endpoints (virtual credits)."""
from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, Query, Request

from app.core.database import get_database
from app.core.dependencies import AdminUserDep, CurrentUserDep
from app.core.responses import ok
from app.modules.credit_requests.schema import CreditRequestCreate, CreditRequestDecision
from app.modules.credit_requests.service import CreditRequestService
from app.utils.ids import serialize_many
from app.utils.pagination import PageParams, build_page, pagination_params

router = APIRouter(prefix="/credit-requests", tags=["credit-requests"])


@router.post("", status_code=201)
async def create_request(payload: CreditRequestCreate, actor: CurrentUserDep):
    service = CreditRequestService(get_database())
    doc = await service.create(actor, payload)
    return ok(doc, message="Request submitted")


@router.get("/mine")
async def my_requests(
    actor: CurrentUserDep,
    params: Annotated[PageParams, Depends(pagination_params)],
    status: str | None = Query(default=None),
):
    service = CreditRequestService(get_database())
    docs, total = await service.my_requests(actor.id, skip=params.skip, limit=params.limit, status=status)
    return ok(build_page(serialize_many(docs), total, params))


@router.get("/inbox")
async def inbox(
    actor: AdminUserDep,
    params: Annotated[PageParams, Depends(pagination_params)],
    status: str | None = Query(default=None),
):
    service = CreditRequestService(get_database())
    docs, total = await service.inbox(actor, skip=params.skip, limit=params.limit, status=status)
    return ok(build_page(serialize_many(docs), total, params))


@router.post("/{request_id}/approve")
async def approve(request_id: str, payload: CreditRequestDecision, request: Request, actor: AdminUserDep):
    service = CreditRequestService(get_database())
    doc = await service.decide(
        actor, request_id, approve=True, decision=payload, ip=getattr(request.state, "client_ip", None)
    )
    return ok(doc, message="Request approved")


@router.post("/{request_id}/reject")
async def reject(request_id: str, payload: CreditRequestDecision, request: Request, actor: AdminUserDep):
    service = CreditRequestService(get_database())
    doc = await service.decide(
        actor, request_id, approve=False, decision=payload, ip=getattr(request.state, "client_ip", None)
    )
    return ok(doc, message="Request rejected")
