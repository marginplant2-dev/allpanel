"""Provider interfaces for sports and games data sources.

These abstractions let the platform swap the underlying data source (mock,
external API, etc.) without changing route contracts or frontend logic.
"""
from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any


def best_h2h_odds(bookmakers: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Best available h2h price per outcome, tagged with the bookmaker offering it.

    List events carry this so the exchange grid can show 1 / X / 2 without a
    per-event odds call, and the bet endpoint re-validates against `bookmaker_key`.
    """
    best: dict[str, dict[str, Any]] = {}
    for b in bookmakers:
        for m in b.get("markets", []):
            if m.get("key") != "h2h":
                continue
            for o in m.get("outcomes", []):
                name, price = o.get("name"), o.get("price")
                if not name or not isinstance(price, (int, float)):
                    continue
                current = best.get(name)
                if current is None or price > current["price"]:
                    best[name] = {
                        "name": name,
                        "price": float(price),
                        "bookmaker_key": b.get("key"),
                        "bookmaker_title": b.get("title") or b.get("key"),
                    }
    return list(best.values())


class BaseSportsProvider(ABC):
    key: str = "base"

    @abstractmethod
    async def get_sports(self) -> list[dict[str, Any]]: ...

    @abstractmethod
    async def get_events(self, *, sport_id: str | None = None, status: str | None = None) -> list[dict[str, Any]]: ...

    @abstractmethod
    async def get_event_detail(self, event_id: str) -> dict[str, Any] | None: ...

    @abstractmethod
    async def get_live_data(self, event_id: str) -> dict[str, Any] | None: ...


class BaseGameProvider(ABC):
    key: str = "base"

    @abstractmethod
    async def get_categories(self) -> list[dict[str, Any]]: ...

    @abstractmethod
    async def get_games(
        self, *, category: str | None = None, featured: bool | None = None, search: str | None = None
    ) -> list[dict[str, Any]]: ...

    @abstractmethod
    async def get_game_details(self, slug: str) -> dict[str, Any] | None: ...
