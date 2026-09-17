"""Sports bet placement schema. Single-market (h2h) stake, locked odds at placement time."""
from __future__ import annotations

from pydantic import BaseModel, Field


class PlaceBetRequest(BaseModel):
    event_id: str = Field(min_length=1)
    bookmaker_key: str = Field(min_length=1, max_length=60)
    outcome_name: str = Field(min_length=1, max_length=120)
    stake: float = Field(gt=0)
