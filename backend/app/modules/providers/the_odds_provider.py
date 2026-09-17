"""The Odds API sports provider."""
from __future__ import annotations

import time
from datetime import datetime, timezone
from typing import Any

import httpx

from app.core.config import settings
from app.modules.providers.base import BaseSportsProvider, best_h2h_odds


BASE_URL = "https://api.the-odds-api.com"

# Every odds request costs a usage credit (the free plan has 500 a month), and the
# board polls on a timer for every visitor — without this cache one open tab burns
# ~60 credits an hour. Prices are re-read at bet placement anyway, so a short TTL
# costs nothing in correctness.
#
# ponytail: per-process dict, so N workers = N times the calls. Move to Redis if
# the app is ever run with more than one worker.
SPORTS_TTL = 24 * 3600.0
ODDS_TTL = 90.0
SCORES_TTL = 30.0

_cache: dict[str, tuple[float, Any]] = {}


def cached(key: str, ttl: float, value_factory):
    """Memoize one provider response for `ttl` seconds."""

    async def run():
        hit = _cache.get(key)
        if hit is not None and hit[0] > time.monotonic():
            return hit[1]
        value = await value_factory()
        _cache[key] = (time.monotonic() + ttl, value)
        return value

    return run()


class TheOddsProvider(BaseSportsProvider):
    key = "theodds"

    def __init__(self, db: Any):
        # db unused; kept to match provider interface
        self.db = db

    async def get_sports(self) -> list[dict[str, Any]]:
        return await cached("sports", SPORTS_TTL, self._fetch_sports)

    async def _fetch_sports(self) -> list[dict[str, Any]]:
        async with httpx.AsyncClient(timeout=15.0) as client:
            r = await client.get(
                f"{BASE_URL}/v4/sports",
                params={"apiKey": settings.sports_api_key},
            )
            r.raise_for_status()
            data = r.json()
        return [
            {
                "id": s["key"],
                "key": s["key"],
                "name": s["title"],
                "group": s["group"],
                "active": s.get("active", True),
                "has_outrights": s.get("has_outrights", False),
            }
            for s in data
        ]

    async def get_events(
        self, *, sport_id: str | None = None, status: str | None = None
    ) -> list[dict[str, Any]]:
        events = await cached(
            f"events:{sport_id or 'upcoming'}", ODDS_TTL, lambda: self._fetch_events(sport_id)
        )
        if status:
            return [e for e in events if e["status"] == status]
        return events

    async def _fetch_events(self, sport_id: str | None) -> list[dict[str, Any]]:
        # /odds carries prices for the grid; the "upcoming" pseudo key has no /events
        # support (verified: returns []) but does work here. Costs 1 quota credit.
        async with httpx.AsyncClient(timeout=15.0) as client:
            r = await client.get(
                f"{BASE_URL}/v4/sports/{sport_id or 'upcoming'}/odds",
                params={
                    "apiKey": settings.sports_api_key,
                    "regions": "eu",
                    "markets": "h2h",
                    "oddsFormat": "decimal",
                },
            )
            if r.status_code >= 400 and sport_id:
                # Quota reached / no odds for this sport — fall back to the free
                # /events listing so the grid still shows fixtures without prices.
                r = await client.get(
                    f"{BASE_URL}/v4/sports/{sport_id}/events",
                    params={"apiKey": settings.sports_api_key},
                )
            r.raise_for_status()
            data = r.json()
        now = datetime.now(timezone.utc)
        events: list[dict[str, Any]] = []
        for e in data:
            start_str = e.get("commence_time")
            if start_str:
                start = datetime.fromisoformat(start_str.replace("Z", "+00:00"))
                event_status = "live" if start < now else "upcoming"
            else:
                event_status = "upcoming"
            events.append(
                {
                    "id": f"{e['sport_key']}:{e['id']}",
                    "sport_id": e["sport_key"],
                    "name": f"{e['home_team']} vs {e['away_team']}",
                    "home_team": e["home_team"],
                    "away_team": e["away_team"],
                    "participants": [e["home_team"], e["away_team"]],
                    "league": e.get("sport_title"),
                    "start_time": start_str,
                    "status": event_status,
                    "odds": best_h2h_odds(e.get("bookmakers", [])),
                }
            )
        return events

    async def get_event_detail(self, event_id: str) -> dict[str, Any] | None:
        return await cached(f"event:{event_id}", ODDS_TTL, lambda: self._fetch_event_detail(event_id))

    async def _fetch_event_detail(self, event_id: str) -> dict[str, Any] | None:
        if ":" not in event_id:
            return None
        sport, eid = event_id.split(":", 1)
        async with httpx.AsyncClient(timeout=15.0) as client:
            r = await client.get(
                f"{BASE_URL}/v4/sports/{sport}/events/{eid}/odds",
                params={
                    "apiKey": settings.sports_api_key,
                    "regions": "eu",
                    "markets": "h2h",
                    "oddsFormat": "decimal",
                },
            )
            if r.status_code == 404:
                return None
            if r.status_code >= 400:
                # Odds fetch failed (e.g. usage quota reached) — degrade to basic
                # match info from the free /events endpoint instead of erroring out.
                return await self._event_detail_fallback(client, sport, eid, event_id)
            data = r.json()
        start_str = data.get("commence_time")
        status = "upcoming"
        if start_str:
            start = datetime.fromisoformat(start_str.replace("Z", "+00:00"))
            status = "live" if start < datetime.now(timezone.utc) else "upcoming"
        return {
            "id": event_id,
            "sport_id": data["sport_key"],
            "name": f"{data['home_team']} vs {data['away_team']}",
            "home_team": data["home_team"],
            "away_team": data["away_team"],
            "participants": [data["home_team"], data["away_team"]],
            "league": data.get("sport_title"),
            "start_time": start_str,
            "status": status,
            "bookmakers": data.get("bookmakers", []),
        }

    async def _event_detail_fallback(
        self, client: httpx.AsyncClient, sport: str, eid: str, event_id: str
    ) -> dict[str, Any] | None:
        r = await client.get(
            f"{BASE_URL}/v4/sports/{sport}/events",
            params={"apiKey": settings.sports_api_key, "eventIds": eid},
        )
        if r.status_code >= 400:
            return None
        matches = r.json()
        if not matches:
            return None
        e = matches[0]
        start_str = e.get("commence_time")
        status = "upcoming"
        if start_str:
            start = datetime.fromisoformat(start_str.replace("Z", "+00:00"))
            status = "live" if start < datetime.now(timezone.utc) else "upcoming"
        return {
            "id": event_id,
            "sport_id": e["sport_key"],
            "name": f"{e['home_team']} vs {e['away_team']}",
            "home_team": e["home_team"],
            "away_team": e["away_team"],
            "participants": [e["home_team"], e["away_team"]],
            "league": e.get("sport_title"),
            "start_time": start_str,
            "status": status,
            "bookmakers": [],
        }

    async def get_live_data(self, event_id: str) -> dict[str, Any] | None:
        return await cached(f"live:{event_id}", SCORES_TTL, lambda: self._fetch_live_data(event_id))

    async def _fetch_live_data(self, event_id: str) -> dict[str, Any] | None:
        if ":" not in event_id:
            return None
        sport, eid = event_id.split(":", 1)
        async with httpx.AsyncClient(timeout=15.0) as client:
            r = await client.get(
                f"{BASE_URL}/v4/sports/{sport}/scores",
                params={"apiKey": settings.sports_api_key, "daysFrom": 3},
            )
            if r.status_code >= 400:
                # Scores fetch failed (e.g. usage quota reached) — caller falls
                # back to the event's own status/score instead of erroring out.
                return None
            data = r.json()
        for e in data:
            if e.get("id") == eid:
                return {
                    "event_id": event_id,
                    "status": "live" if not e.get("completed") else "finished",
                    "score": (
                        {
                            e["scores"][0]["name"]: e["scores"][0]["score"],
                            e["scores"][1]["name"]: e["scores"][1]["score"],
                        }
                        if e.get("scores") and len(e["scores"]) == 2
                        else {}
                    ),
                }
        return None
