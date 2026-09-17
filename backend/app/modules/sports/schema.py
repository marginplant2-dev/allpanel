"""Sports & events schemas."""
from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field


class SportCreate(BaseModel):
    key: str = Field(min_length=1, max_length=60, pattern=r"^[a-z0-9-]+$")
    name: str = Field(min_length=1, max_length=80)
    icon: str | None = None
    sort_order: int = 0
    status: str = Field(default="active", pattern="^(active|inactive)$")


class EventCreate(BaseModel):
    sport_id: str
    name: str = Field(min_length=1, max_length=160)
    participants: list[str] = Field(default_factory=list)
    league: str | None = None
    start_time: datetime
    status: str = Field(default="upcoming", pattern="^(live|upcoming|finished)$")
    score: dict | None = None


class EventUpdate(BaseModel):
    name: str | None = None
    league: str | None = None
    start_time: datetime | None = None
    status: str | None = Field(default=None, pattern="^(live|upcoming|finished)$")
    score: dict | None = None
