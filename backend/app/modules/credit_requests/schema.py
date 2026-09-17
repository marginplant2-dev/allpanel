"""Deposit / withdraw request schemas (virtual credits, hierarchy-approved)."""
from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field

from app.core.enums import RequestType


class CreditRequestCreate(BaseModel):
    type: RequestType
    amount: float = Field(gt=0, description="Virtual credits to deposit or withdraw")
    note: str | None = Field(default=None, max_length=500)


class CreditRequestDecision(BaseModel):
    note: str | None = Field(default=None, max_length=500)


class CreditRequestPublic(BaseModel):
    id: str
    user_id: str
    username: str
    parent_id: str
    type: str
    amount: float
    status: str
    note: str | None = None
    decision_note: str | None = None
    transaction_id: str | None = None
    created_at: datetime
    decided_at: datetime | None = None
