"""proexch exchange feed: Betfair-mirror matches, back/lay prices, fancy markets.

Access is granted per server IP + domain (no API key), so every call must leave
from the whitelisted host — see deploy/CO-HOSTING.md.

Shapes (the Swagger declares only Map<string,object>, these come from live calls):

  /api/cricket/matches -> data.data[]          gameId marketId eventName eventTime
                                               runnerName1..3 back1/lay1 back11/lay11
                                               back12/lay12 inPlay tv seriesName
  /api/soccer/matches  -> data.soccerMatches[] eventId marketId eventName eventDate
  /api/tennis/matches  -> data.TennisMatches[] (same as soccer)
  /api/{sport}/odds|data?gameId&marketId
        -> data.{matchOdds,bookMakerOdds,fancyOdds,otherMarketOdds}[]
           each: mid market mname mstatus isPlay min max oddDatas[]
           oddData: sid rname b1 bs1 b2 bs2 b3 bs3 l1 ls1 l2 ls2 l3 ls3 status min max

Times carry no zone and are IST (verified against Europa League kick-offs).
"""
from __future__ import annotations

import asyncio
import logging
import time
from datetime import datetime, timedelta, timezone
from typing import Any

import httpx

from app.core.config import settings
from app.modules.providers.base import BaseSportsProvider

logger = logging.getLogger(__name__)

IST = timezone(timedelta(hours=5, minutes=30))

#: The match lists carry no prices (every back1/lay1 comes through as 0), so the
#: board is filled from the per-event odds endpoint. Only the matches a visitor
#: actually sees first are fetched — in-play, then soonest — and the calls run
#: concurrently behind a small semaphore so one refresh is ~1s, not ~30s.
#: ponytail: if the board ever pages beyond this, enrich per page instead.
MAX_ENRICHED = 30
ENRICH_CONCURRENCY = 8

#: sport key -> (list path, list container key, odds path, display name, group)
SPORTS: dict[str, tuple[str, str, str, str, str]] = {
    "cricket": ("/api/cricket/matches", "data", "/api/cricket/odds", "Cricket", "Cricket"),
    "soccer": ("/api/soccer/matches", "soccerMatches", "/api/soccer/data", "Football", "Soccer"),
    "tennis": ("/api/tennis/matches", "TennisMatches", "/api/tennis/data", "Tennis", "Tennis"),
}

#: odds payload key -> (bookmaker key prefix, fallback title)
MARKET_GROUPS = (
    ("matchOdds", "match_odds", "Match Odds"),
    ("bookMakerOdds", "bookmaker", "Bookmaker"),
    ("fancyOdds", "fancy", "Fancy"),
    ("otherMarketOdds", "other", "Other Market"),
)

MATCHES_TTL = 30.0
ODDS_TTL = 5.0
SCORE_TTL = 10.0

_cache: dict[str, tuple[float, Any]] = {}


def cached(key: str, ttl: float, factory):
    """Memoize a feed response briefly — the board polls, the feed should not."""

    async def run():
        hit = _cache.get(key)
        if hit is not None and hit[0] > time.monotonic():
            return hit[1]
        value = await factory()
        _cache[key] = (time.monotonic() + ttl, value)
        return value

    return run()


def to_utc(value: str | None) -> str | None:
    """Feed timestamps are IST and zone-less; the rest of the app works in UTC."""
    if not value:
        return None
    try:
        naive = datetime.fromisoformat(str(value).replace("Z", ""))
    except ValueError:
        return None
    if naive.tzinfo is None:
        naive = naive.replace(tzinfo=IST)
    return naive.astimezone(timezone.utc).isoformat().replace("+00:00", "Z")


def price(value: Any) -> float:
    """Feed prices are strings, and 0 / "0" means 'no price right now'."""
    try:
        out = float(value)
    except (TypeError, ValueError):
        return 0.0
    return out if out > 1 else 0.0


def runners(row: dict[str, Any]) -> list[str]:
    names = [row.get("runnerName1"), row.get("runnerName3"), row.get("runnerName2")]
    # index 1 is the draw slot: keep it only when the feed actually has one
    return [n for n in names if n]


def list_odds(row: dict[str, Any]) -> list[dict[str, Any]]:
    """Top-of-book prices carried on the cricket list (1 / X / 2 in feed order)."""
    pairs = (
        (row.get("runnerName1"), row.get("back1"), row.get("lay1")),
        (row.get("runnerName3"), row.get("back12"), row.get("lay12")),
        (row.get("runnerName2"), row.get("back11"), row.get("lay11")),
    )
    out = []
    for name, back, lay in pairs:
        if not name or not price(back):
            continue
        out.append(
            {
                "name": name,
                "price": price(back),
                "lay": price(lay) or None,
                "bookmaker_key": "match_odds",
                "bookmaker_title": "Match Odds",
            }
        )
    return out


def map_event(sport: str, row: dict[str, Any]) -> dict[str, Any] | None:
    game_id = str(row.get("gameId") or row.get("eventId") or "")
    market_id = str(row.get("marketId") or "")
    if not game_id or not market_id:
        return None

    start = to_utc(row.get("eventTime") or row.get("eventDate") or row.get("startDate"))
    started = bool(start and datetime.fromisoformat(start.replace("Z", "+00:00")) <= datetime.now(timezone.utc))
    in_play = row.get("inPlay") in (True, "true", "True", 1, "1")

    names = runners(row)
    return {
        "id": f"{sport}:{game_id}:{market_id}",
        "sport_id": sport,
        "name": row.get("eventName") or " v ".join(names),
        "home_team": row.get("runnerName1"),
        "away_team": row.get("runnerName2"),
        "participants": names,
        "league": row.get("seriesName"),
        "start_time": start,
        "status": "live" if (in_play or started) else "upcoming",
        "has_tv": bool(row.get("tv")),
        "odds": list_odds(row),
    }


def map_bookmakers(payload: dict[str, Any]) -> list[dict[str, Any]]:
    """Every market in the odds payload becomes one 'bookmaker' block.

    The app renders one box per block, which is exactly how an exchange board
    looks: Match Odds, Bookmaker, then a box per fancy market.
    """
    books: list[dict[str, Any]] = []
    for group_key, prefix, fallback_title in MARKET_GROUPS:
        for market in payload.get(group_key) or []:
            outcomes = []
            for odd in market.get("oddDatas") or []:
                back, lay = price(odd.get("b1")), price(odd.get("l1"))
                if not back and not lay:
                    continue
                outcomes.append(
                    {
                        "name": odd.get("rname") or str(odd.get("sid")),
                        "price": back or lay,
                        "lay": lay or None,
                        "status": odd.get("status"),
                        "size": odd.get("bs1"),
                    }
                )
            if not outcomes:
                continue
            books.append(
                {
                    "key": f"{prefix}:{market.get('mid') or len(books)}",
                    "title": market.get("mname") or market.get("market") or fallback_title,
                    "suspended": str(market.get("mstatus") or "").upper() not in ("", "OPEN"),
                    "min_stake": market.get("min") or 0,
                    "max_stake": market.get("max") or 0,
                    "markets": [{"key": "h2h", "outcomes": outcomes}],
                }
            )
    return books


class ProexchProvider(BaseSportsProvider):
    key = "proexch"

    def __init__(self, db: Any):
        self.db = db  # unused; kept to match the provider interface

    async def _get(self, path: str, **params: Any) -> dict[str, Any]:
        headers = {"Accept": "application/json"}
        if settings.proexch_origin:
            headers["Origin"] = settings.proexch_origin
            headers["Referer"] = settings.proexch_origin.rstrip("/") + "/"
        async with httpx.AsyncClient(timeout=20.0, headers=headers) as client:
            r = await client.get(settings.proexch_base_url + path, params=params or None)
            r.raise_for_status()
            body = r.json()
        return body.get("data") if isinstance(body, dict) else {}

    async def get_sports(self) -> list[dict[str, Any]]:
        return [
            {
                "id": key,
                "key": key,
                "name": name,
                "group": group,
                "sort_order": i,
                "status": "active",
            }
            for i, (key, (_, _, _, name, group)) in enumerate(SPORTS.items())
        ]

    async def _matches(self, sport: str) -> list[dict[str, Any]]:
        list_path, container, *_ = SPORTS[sport]

        async def fetch() -> list[dict[str, Any]]:
            data = await self._get(list_path)
            rows = data.get(container)
            if rows is None:  # container renamed upstream: take the first list we find
                rows = next((v for v in data.values() if isinstance(v, list)), [])
            events = [e for e in (map_event(sport, r) for r in rows) if e]
            await self._enrich(sport, events)
            return events

        return await cached(f"matches:{sport}", MATCHES_TTL, fetch)

    async def _enrich(self, sport: str, events: list[dict[str, Any]]) -> None:
        """Fill in 1/X/2 prices for the events at the top of the board."""
        ranked = sorted(events, key=lambda e: (e["status"] != "live", e["start_time"] or ""))
        gate = asyncio.Semaphore(ENRICH_CONCURRENCY)

        async def one(event: dict[str, Any]) -> None:
            _, game_id, market_id = event["id"].split(":")

            async def fetch() -> dict[str, Any]:
                async with gate:
                    return await self._get(SPORTS[sport][2], gameId=game_id, marketId=market_id)

            try:
                payload = await cached(f"odds:{event['id']}", ODDS_TTL, fetch)
            except Exception as exc:  # noqa: BLE001 — a priceless row is better than no board
                logger.debug("proexch odds failed for %s: %s", event["id"], exc)
                return
            books = map_bookmakers(payload or {})
            # The 1/X/2 columns are the match odds. A fancy market ("4th wkt",
            # "6 over runs") has its own runners and belongs on the event page,
            # never in the board's win columns.
            book = next(
                (b for b in books if b["key"].startswith(("match_odds", "bookmaker"))), None
            )
            if book is None:
                return
            outcomes = book["markets"][0]["outcomes"]
            event["odds"] = [
                {
                    "name": o["name"],
                    "price": o["price"],
                    "lay": o.get("lay"),
                    "bookmaker_key": book["key"],
                    "bookmaker_title": book["title"],
                }
                for o in outcomes
            ]

        await asyncio.gather(*(one(e) for e in ranked[:MAX_ENRICHED]))

    async def get_events(
        self, *, sport_id: str | None = None, status: str | None = None
    ) -> list[dict[str, Any]]:
        wanted = [sport_id] if sport_id in SPORTS else list(SPORTS)
        events: list[dict[str, Any]] = []
        for sport in wanted:
            events.extend(await self._matches(sport))
        events.sort(key=lambda e: (e["status"] != "live", e["start_time"] or ""))
        if status:
            return [e for e in events if e["status"] == status]
        return events

    async def get_event_detail(self, event_id: str) -> dict[str, Any] | None:
        parts = event_id.split(":")
        if len(parts) != 3 or parts[0] not in SPORTS:
            return None
        sport, game_id, market_id = parts

        base = next((e for e in await self._matches(sport) if e["id"] == event_id), None)

        async def fetch() -> dict[str, Any]:
            return await self._get(SPORTS[sport][2], gameId=game_id, marketId=market_id)

        payload = await cached(f"odds:{event_id}", ODDS_TTL, fetch)
        books = map_bookmakers(payload or {})

        if base is None and not books:
            return None
        detail = dict(base or {"id": event_id, "sport_id": sport, "participants": []})
        detail["bookmakers"] = books
        return detail

    async def get_live_data(self, event_id: str) -> dict[str, Any] | None:
        parts = event_id.split(":")
        if len(parts) != 3:
            return None
        sport, game_id, _ = parts

        async def fetch() -> dict[str, Any]:
            return await self._get(f"/api/score3/{game_id}")

        payload = await cached(f"score:{event_id}", SCORE_TTL, fetch) or {}
        inner = payload.get("data") if isinstance(payload.get("data"), dict) else payload
        if not inner:
            return None
        score = {}
        for team_key, run_key in (("team1", "score1"), ("team2", "score2")):
            if inner.get(team_key):
                score[str(inner[team_key])] = inner.get(run_key)
        if not score:
            return None
        return {"event_id": event_id, "status": "live", "score": score}

    async def get_result(self, sport: str, market_id: str, type_: str = "match") -> dict[str, Any] | None:
        """Settled result for a market.

        ponytail: exposed but not wired into settlement yet — the worker still
        settles on live scores. Wire it when in-play bets start settling for real.
        """
        return await self._get("/api/betfair-result", sport=sport, type=type_, marketId=market_id)
