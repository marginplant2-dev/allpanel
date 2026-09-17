"""Credit transfer engine: idempotent, concurrency-safe, ledger-backed.

Design notes
------------
* A ledger transaction is written **before** balances move, so every balance
  change is always backed by a record.
* Idempotency is enforced by the unique `idempotency_key` index: a duplicate
  request replays the original transaction instead of transferring again.
* The sender debit is an atomic guarded update (`available_balance >= amount`),
  which prevents double-spend under concurrency without requiring multi-document
  transactions (so it works on a standalone mongod).
"""
from __future__ import annotations

import uuid
from typing import Any

from motor.motor_asyncio import AsyncIOMotorDatabase
from pymongo.errors import DuplicateKeyError

from app.core.dependencies import CurrentUser
from app.core.enums import Role, TransactionStatus, TransactionType
from app.core.exceptions import (
    AppError,
    NotFoundError,
    PermissionDeniedError,
    ValidationError,
)
from app.modules.audit.models import AuditAction
from app.modules.audit.service import record_audit
from app.modules.ledger.repository import LedgerRepository
from app.modules.ledger.schema import TransferRequest
from app.modules.wallet.repository import WalletRepository
from app.utils.ids import serialize, to_object_id
from app.utils.time import utcnow


class InsufficientFundsError(AppError):
    status_code = 400
    code = "INSUFFICIENT_FUNDS"


class LedgerService:
    def __init__(self, db: AsyncIOMotorDatabase):
        self.db = db
        self.ledger = LedgerRepository(db)
        self.wallets = WalletRepository(db)

    async def transfer(
        self,
        sender: CurrentUser,
        payload: TransferRequest,
        *,
        idempotency_key: str | None = None,
        ip: str | None = None,
    ) -> dict[str, Any]:
        key = payload.idempotency_key or idempotency_key

        # Idempotent replay: return the original transaction if the key was used.
        if key:
            existing = await self.ledger.get_by_idempotency_key(key)
            if existing is not None:
                return serialize(existing)  # type: ignore[return-value]

        if payload.amount <= 0:
            raise ValidationError("Amount must be positive")
        if payload.to_user_id == sender.id:
            raise ValidationError("Cannot transfer credits to yourself")

        receiver = await self.db.users.find_one({"_id": to_object_id(payload.to_user_id)})
        if receiver is None:
            raise NotFoundError("Recipient not found")
        receiver_user = CurrentUser(receiver)

        # Coins move one step at a time: mother admin -> super admin -> admin ->
        # master -> agent -> player. Only the direct parent can top an account up,
        # so an upline cannot bypass a level and every balance has a paper trail.
        if receiver_user.parent_id != sender.id:
            raise PermissionDeniedError("You can only give coins to accounts you created directly")

        return await self._execute_transfer(
            from_id=sender.id,
            to_id=payload.to_user_id,
            amount=float(payload.amount),
            transaction_type=payload.transaction_type or TransactionType.CREDIT_TRANSFER,
            note=payload.note,
            idempotency_key=key,
            actor_id=sender.id,
            ip=ip,
        )

    async def _execute_transfer(
        self,
        *,
        from_id: str,
        to_id: str,
        amount: float,
        transaction_type: TransactionType | str,
        note: str | None = None,
        metadata: dict[str, Any] | None = None,
        idempotency_key: str | None = None,
        actor_id: str,
        ip: str | None = None,
    ) -> dict[str, Any]:
        """Move `amount` credits from `from_id` to `to_id` and record the ledger entry.

        Shared by `transfer()` (direct admin push, hierarchy-guarded) and the
        credit-request approval flow (already authorized by the approver being
        the requester's direct parent).
        """
        transaction_id = uuid.uuid4().hex
        now = utcnow()
        doc: dict[str, Any] = {
            "transaction_id": transaction_id,
            "from_user_id": from_id,
            "to_user_id": to_id,
            "amount": float(amount),
            "transaction_type": transaction_type.value if isinstance(transaction_type, TransactionType) else transaction_type,
            "status": TransactionStatus.PENDING.value,
            "metadata": {**(metadata or {}), **({"note": note} if note else {})},
            "created_at": now,
        }
        if idempotency_key:
            doc["idempotency_key"] = idempotency_key

        try:
            await self.ledger.insert(doc)
        except DuplicateKeyError:
            # Concurrent duplicate with the same idempotency key: replay.
            if idempotency_key:
                existing = await self.ledger.get_by_idempotency_key(idempotency_key)
                if existing is not None:
                    return serialize(existing)  # type: ignore[return-value]
            raise

        # Atomic guarded debit prevents overdraft / double-spend.
        debited = await self.wallets.try_debit(from_id, float(amount))
        if not debited:
            await self.ledger.set_status(transaction_id, TransactionStatus.FAILED.value)
            raise InsufficientFundsError("Insufficient available balance")

        await self.wallets.credit(to_id, float(amount))
        await self.ledger.set_status(transaction_id, TransactionStatus.COMPLETED.value)
        doc["status"] = TransactionStatus.COMPLETED.value

        await record_audit(
            self.db,
            actor_id=actor_id,
            action=AuditAction.CREDIT_TRANSFERRED,
            target_id=to_id,
            metadata={"amount": float(amount), "transaction_id": transaction_id},
            ip_address=ip,
        )

        await self._publish_realtime(from_id, to_id, float(amount))
        return serialize(doc)  # type: ignore[return-value]

    async def _publish_realtime(self, from_id: str, to_id: str, amount: float) -> None:
        """Push wallet updates and a notification to the affected users."""
        from app.modules.notifications.service import NotificationService
        from app.websocket.events import publish_wallet_update

        for uid in (from_id, to_id):
            wallet = await self.wallets.get(uid)
            if wallet is not None:
                await publish_wallet_update(
                    uid,
                    {
                        "user_id": uid,
                        "available_balance": wallet.get("available_balance", 0.0),
                        "locked_balance": wallet.get("locked_balance", 0.0),
                    },
                )
        try:
            await NotificationService(self.db).create(
                to_id,
                type_="CREDIT_RECEIVED",
                title="Credits received",
                body=f"You received {amount:g} virtual credits.",
                metadata={"amount": amount},
            )
        except Exception:  # noqa: BLE001
            pass

    async def history(
        self,
        user_id: str,
        *,
        skip: int,
        limit: int,
        direction: str | None,
        transaction_type: str | None,
    ) -> tuple[list[dict[str, Any]], int]:
        query: dict[str, Any] = {}
        if direction == "in":
            query["to_user_id"] = user_id
        elif direction == "out":
            query["from_user_id"] = user_id
        else:
            query["$or"] = [{"from_user_id": user_id}, {"to_user_id": user_id}]
        if transaction_type:
            query["transaction_type"] = transaction_type
        return await self.ledger.list(query=query, skip=skip, limit=limit)

    async def scoped_ledger(
        self,
        actor: CurrentUser,
        *,
        skip: int,
        limit: int,
    ) -> tuple[list[dict[str, Any]], int]:
        if actor.role is Role.MOTHER_ADMIN:
            query: dict[str, Any] = {}
        else:
            downline = self.db.users.find({"hierarchy_path": actor.id}, {"_id": 1})
            ids = [str(d["_id"]) async for d in downline]
            ids.append(actor.id)
            query = {"$or": [{"from_user_id": {"$in": ids}}, {"to_user_id": {"$in": ids}}]}
        return await self.ledger.list(query=query, skip=skip, limit=limit)
