"""Game catalogue schemas."""
from __future__ import annotations

from pydantic import BaseModel, Field


class GameCreate(BaseModel):
    name: str = Field(min_length=1, max_length=120)
    #: Provider's game id. Without it a game cannot be launched for real money.
    game_uid: str | None = Field(default=None, max_length=120)
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
    game_uid: str | None = Field(default=None, max_length=120)
    provider: str | None = Field(default=None, min_length=1, max_length=80)
    category: str | None = Field(default=None, min_length=1, max_length=80)
    thumbnail_url: str | None = Field(default=None, min_length=1, max_length=500)
    banner_url: str | None = Field(default=None, max_length=500)
    status: str | None = Field(default=None, pattern="^(active|inactive)$")
    featured: bool | None = None
    sort_order: int | None = None
    tags: list[str] | None = None


class ProviderGame(BaseModel):
    """One row of a provider's game list, as exported from their panel."""

    name: str = Field(min_length=1, max_length=120)
    game_uid: str = Field(min_length=1, max_length=120)
    category: str = Field(default="live", max_length=80)
    provider: str = Field(default="gamblly", max_length=80)
    thumbnail_url: str | None = Field(default=None, max_length=1000)
    banner_url: str | None = Field(default=None, max_length=1000)
    featured: bool = False
    sort_order: int = 0


class GameImportRequest(BaseModel):
    """Bulk upsert of a provider catalogue, keyed by game_uid."""

    games: list[ProviderGame] = Field(min_length=1)
    replace: bool = Field(
        default=False,
        description="Deactivate every game not in this list (use when importing a full catalogue)",
    )


class PlayRoundRequest(BaseModel):
    stake: float = Field(gt=0)


class CategoryCreate(BaseModel):
    key: str = Field(min_length=1, max_length=60, pattern=r"^[a-z0-9-]+$")
    name: str = Field(min_length=1, max_length=80)
    sort_order: int = 0
    status: str = Field(default="active", pattern="^(active|inactive)$")
