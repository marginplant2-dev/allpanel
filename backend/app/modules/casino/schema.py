"""Casino request schemas."""
from __future__ import annotations

from pydantic import BaseModel, Field


class PlaceCasinoBet(BaseModel):
    code: str = Field(min_length=2, max_length=40)
    #: The round the player was looking at — a stale one is refused, not re-aimed.
    round_id: str = Field(min_length=1, max_length=40)
    sid: str = Field(min_length=1, max_length=20)
    stake: float = Field(gt=0)
