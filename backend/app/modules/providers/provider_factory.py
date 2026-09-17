"""Factory selecting the active sports/games providers from settings."""
from __future__ import annotations

import logging
import time
from typing import Any, Awaitable, Callable, TypeVar

from motor.motor_asyncio import AsyncIOMotorDatabase

from app.core.config import settings
from app.modules.providers.base import BaseGameProvider, BaseSportsProvider
from app.modules.providers.mock_provider import MockGameProvider, MockSportsProvider
from app.modules.providers.proexch_provider import ProexchProvider
from app.modules.providers.the_odds_provider import TheOddsProvider

logger = logging.getLogger(__name__)

T = TypeVar("T")


COOLDOWN_SECONDS = 300.0
_backup_until = 0.0  # process-local; a restart retries the live provider immediately


class FallbackSportsProvider(BaseSportsProvider):
    """Serves seeded data whenever the live provider fails.

    An expired key, an exhausted quota or a network blip must not take the whole
    board down — every consumer (sports service, bet placement, settlement worker)
    goes through the factory, so the guard lives here rather than in each caller.

    The switch is sticky for `COOLDOWN_SECONDS`: a per-call fallback would serve
    the live sports list alongside seeded events, and the two id spaces don't
    match — the board would lose its sport grouping. It also stops every request
    re-hitting a provider that is known to be down.
    """

    key = "fallback"

    def __init__(self, primary: BaseSportsProvider, backup: BaseSportsProvider):
        self.primary = primary
        self.backup = backup

    async def _try(self, call: Callable[[BaseSportsProvider], Awaitable[T]]) -> T:
        global _backup_until
        if time.monotonic() < _backup_until:
            return await call(self.backup)
        try:
            return await call(self.primary)
        except Exception as exc:  # noqa: BLE001 — any provider failure degrades the same way
            _backup_until = time.monotonic() + COOLDOWN_SECONDS
            logger.warning(
                "sports provider %r failed (%s); serving seeded data for %.0fs",
                self.primary.key,
                exc,
                COOLDOWN_SECONDS,
            )
            return await call(self.backup)

    async def get_sports(self) -> list[dict[str, Any]]:
        return await self._try(lambda p: p.get_sports())

    async def get_events(
        self, *, sport_id: str | None = None, status: str | None = None
    ) -> list[dict[str, Any]]:
        return await self._try(lambda p: p.get_events(sport_id=sport_id, status=status))

    async def get_event_detail(self, event_id: str) -> dict[str, Any] | None:
        # A live provider returns None for ids it does not own (a seeded event id),
        # so an empty result has to fall through to the backup as well.
        return await self._try_with_none_fallback(lambda p: p.get_event_detail(event_id))

    async def get_live_data(self, event_id: str) -> dict[str, Any] | None:
        return await self._try_with_none_fallback(lambda p: p.get_live_data(event_id))

    async def _try_with_none_fallback(
        self, call: Callable[[BaseSportsProvider], Awaitable[dict[str, Any] | None]]
    ) -> dict[str, Any] | None:
        result = await self._try(call)
        if result is None:
            return await call(self.backup)
        return result


def sports_data_source() -> str:
    """Where sports data is coming from right now: "live" or "seeded" (cooldown)."""
    if settings.sports_provider not in ("theodds", "proexch"):
        return "seeded"
    return "seeded" if time.monotonic() < _backup_until else "live"


def get_sports_provider(db: AsyncIOMotorDatabase) -> BaseSportsProvider:
    if settings.sports_provider == "proexch":
        return FallbackSportsProvider(ProexchProvider(db), MockSportsProvider(db))
    if settings.sports_provider == "theodds":
        return FallbackSportsProvider(TheOddsProvider(db), MockSportsProvider(db))
    # Future: external providers keyed by settings.sports_provider
    return MockSportsProvider(db)


def get_game_provider(db: AsyncIOMotorDatabase) -> BaseGameProvider:
    if settings.games_provider == "mock":
        return MockGameProvider(db)
    return MockGameProvider(db)
