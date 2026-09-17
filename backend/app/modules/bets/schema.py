"""Sports bet placement schema. Odds are validated against the live ladder."""
from __future__ import annotations

from pydantic import BaseModel, Field


class PlaceBetRequest(BaseModel):
    event_id: str = Field(min_length=1)
    bookmaker_key: str = Field(min_length=1, max_length=60)
    outcome_name: str = Field(min_length=1, max_length=120)
    stake: float = Field(gt=0)
    #: BACK wins if the runner wins; LAY wins if it does not.
    side: str = Field(default="BACK", pattern="^(BACK|LAY)$")
    #: The exact rung the player clicked. Rejected if the market has moved off it.
    price: float | None = Field(default=None, gt=1)
