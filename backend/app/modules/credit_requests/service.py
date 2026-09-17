"""Deposit / withdraw request flow: user requests, direct parent approves.

Approval reuses `LedgerService._execute_transfer` for the actual credit move
(same idempotent, concurrency-safe primitive as a direct admin transfer).
A DEPOSIT moves credits parent -> user; a WITHDRAW moves user -> parent
(virtual credits return to the approver's pool, never real money).
"""
from __future__ import annotations

from typing import Any

from motor.motor_asyncio import AsyncIOMotorDatabase

from app.core.dependencies import CurrentUser
from app.core.enums import RequestStatus, RequestType, TransactionType
from app.core.exceptions import ConflictError, NotFoundError, PermissionDeniedError, ValidationError
from app.modules.credit_requests.repository import CreditRequestRepository
from app.modules.credit_requests.schema import CreditRequestCreate, CreditRequestDecision
from app.modules.ledger.service import InsufficientFundsError, LedgerService
from app.modules.notifications.service import NotificationService
from app.utils.ids import serialize
from app.utils.time import utcnow


class CreditRequestService:
    def __init__(self, db: AsyncIOMotorDatabase):
        self.db = db
        self.repo = CreditRequestRepository(db)

    async def create(self, user: CurrentUser, payload: CreditRequestCreate) -> dict[str, Any]:
        if not user.parent_id:
            raise ValidationError("Your account has no upline to request credits from")

        doc: dict[str, Any] = {
            "user_id": user.id,
            "username": user.username,
            "parent_id": user.parent_id,
            "type": payload.type.value,
            "amount": float(payload.amount),
            "status": RequestStatus.PENDING.value,
            "note": payload.note,
            "decision_note": None,
            "transaction_id": None,
            "created_at": utcnow(),
            "decided_at": None,
        }
        await self.repo.insert(doc)

        await NotificationService(self.db).create(
            user.parent_id,
            type_="CREDIT_REQUEST_CREATED",
            title=f"New {payload.type.value.lower()} request",
            body=f"{user.username} requested {payload.amount:g} credits ({payload.type.value.lower()}).",
            metadata={"request_id": str(doc["_id"]), "amount": payload.amount, "type": payload.type.value},
        )
        return serialize(doc)  # type: ignore[return-value]

    async def my_requests(
        self, user_id: str, *, skip: int, limit: int, status: str | None = None
    ) -> tuple[list[dict[str, Any]], int]:
        query: dict[str, Any] = {"user_id": user_id}
        if status:
            query["status"] = status
        return await self.repo.list(query, skip=skip, limit=limit)

    async def inbox(
        self, actor: CurrentUser, *, skip: int, limit: int, status: str | None = None
    ) -> tuple[list[dict[str, Any]], int]:
        query: dict[str, Any] = {"parent_id": actor.id}
        if status:
            query["status"] = status
        return await self.repo.list(query, skip=skip, limit=limit)

    async def decide(
        self,
        actor: CurrentUser,
        request_id: str,
        *,
        approve: bool,
        decision: CreditRequestDecision,
        ip: str | None = None,
    ) -> dict[str, Any]:
        req = await self.repo.get(request_id)
        if req is None:
            raise NotFoundError("Request not found")
        if req["parent_id"] != actor.id:
            raise PermissionDeniedError("Only the requester's direct parent can decide this request")
        if req["status"] != RequestStatus.PENDING.value:
            raise ConflictError("Request already decided")

        claimed = await self.repo.claim(request_id)
        if claimed is None:
            raise ConflictError("Request already decided")

        now = utcnow()

        if not approve:
            await self.repo.finalize(
                request_id, status=RequestStatus.REJECTED.value, decision_note=decision.note, decided_at=now
            )
            await NotificationService(self.db).create(
                req["user_id"],
                type_="CREDIT_REQUEST_REJECTED",
                title=f"{req['type'].title()} request rejected",
                body=decision.note or "Your request was rejected.",
                metadata={"request_id": request_id},
            )
            return serialize(await self.repo.get(request_id))  # type: ignore[return-value]

        is_deposit = req["type"] == RequestType.DEPOSIT.value
        from_id, to_id = (actor.id, req["user_id"]) if is_deposit else (req["user_id"], actor.id)

        try:
            txn = await LedgerService(self.db)._execute_transfer(
                from_id=from_id,
                to_id=to_id,
                amount=req["amount"],
                transaction_type=TransactionType.CREDIT_ALLOCATION,
                note=decision.note,
                metadata={"request_id": request_id, "request_type": req["type"]},
                actor_id=actor.id,
                ip=ip,
            )
        except InsufficientFundsError:
            await self.repo.finalize(
                request_id,
                status=RequestStatus.REJECTED.value,
                decision_note="Auto-rejected: insufficient balance at approval time",
                decided_at=now,
            )
            raise

        await self.repo.finalize(
            request_id,
            status=RequestStatus.APPROVED.value,
            decision_note=decision.note,
            decided_at=now,
            transaction_id=txn["transaction_id"],
        )
        await NotificationService(self.db).create(
            req["user_id"],
            type_="CREDIT_REQUEST_APPROVED",
            title=f"{req['type'].title()} approved",
            body=f"Your {req['type'].lower()} request for {req['amount']:g} credits was approved.",
            metadata={"request_id": request_id, "amount": req["amount"]},
        )
        return serialize(await self.repo.get(request_id))  # type: ignore[return-value]
