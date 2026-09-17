"""Wallet response schemas."""
from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel


class WalletPublic(BaseModel):
    user_id: str
    available_balance: float
    locked_balance: float
    updated_at: datetime | None = None
