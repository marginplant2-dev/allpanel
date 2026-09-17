"""Ledger / credit-transfer schemas."""
from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field

from app.core.enums import TransactionType


class TransferRequest(BaseModel):
    to_user_id: str
    amount: float = Field(gt=0, description="Virtual credits to transfer (must be positive)")
    transaction_type: TransactionType = TransactionType.CREDIT_TRANSFER
    note: str | None = Field(default=None, max_length=500)
    idempotency_key: str | None = Field(default=None, max_length=128)


class TransactionPublic(BaseModel):
    transaction_id: str
    from_user_id: str | None = None
    to_user_id: str | None = None
    amount: float
    transaction_type: str
    status: str
    idempotency_key: str | None = None
    metadata: dict[str, Any] = {}
    created_at: datetime | None = None
