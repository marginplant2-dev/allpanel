"""Game catalogue schemas."""
from __future__ import annotations

from pydantic import BaseModel, Field


class GameCreate(BaseModel):
    name: str = Field(min_length=1, max_length=120)
    slug: str = Field(min_length=1, max_length=140, pattern=r"^[a-z0-9-]+$")
    provider: str = Field(min_length=1, max_length=80)
    category: str = Field(min_length=1, max_length=80)
    thumbnail_url: str = Field(min_length=1, max_length=500)
    banner_url: str | None = Field(default=None, max_length=500)
    status: str = Field(default="active", pattern="^(active|inactive)$")
    featured: bool = False
    sort_order: int = 0
    tags: list[str] = Field(default_factory=list)


class GameUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=120)
    provider: str | None = Field(default=None, min_length=1, max_length=80)
    category: str | None = Field(default=None, min_length=1, max_length=80)
    thumbnail_url: str | None = Field(default=None, min_length=1, max_length=500)
    banner_url: str | None = Field(default=None, max_length=500)
    status: str | None = Field(default=None, pattern="^(active|inactive)$")
    featured: bool | None = None
    sort_order: int | None = None
    tags: list[str] | None = None


class PlayRoundRequest(BaseModel):
    stake: float = Field(gt=0)


class CategoryCreate(BaseModel):
    key: str = Field(min_length=1, max_length=60, pattern=r"^[a-z0-9-]+$")
    name: str = Field(min_length=1, max_length=80)
    sort_order: int = 0
    status: str = Field(default="active", pattern="^(active|inactive)$")
