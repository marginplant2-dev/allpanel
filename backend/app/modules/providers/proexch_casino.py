"""proexch live-casino feed: Teen Patti, Dragon Tiger, Andar Bahar and friends.

Same whitelisted host as the sports feed (server IP + domain, no key).

  /api/tunnel/casino/odds/<CODE>                    the table right now
  /api/tunnel/casino/casino-last-10-results/<CODE>  recent rounds and their winner

The odds payload nests `data` four deep and looks like this (TEEN_20):

  {"mid": 102260921134126,          round id
   "lt": 14,                        seconds left to bet
   "card": "KCC,6DD,QDD,JCC,8SS",   cards dealt so far ("1" = face down)
   "gtype": "teen20",
   "sub": [{"sid": 1, "nat": "Player A", "b": 1.98, "bs": 600000.0,
            "gstatus": "OPEN", "min": 100.0, "max": 500000.0,
            "subtype": "Player", "etype": "fancy"}, ...]}

Results give `[{"mid": ..., "win": "2"}]` — the winning sid for that round, which
is what settles a bet.
"""
from __future__ import annotations

import logging
import time
from typing import Any

import httpx

from app.core.config import settings

logger = logging.getLogger(__name__)

TUNNEL = "/api/tunnel/casino"
ODDS_TTL = 2.0      # a round lasts ~30s and the countdown has to look live
RESULTS_TTL = 10.0

#: code -> (display name, category). The order is the lobby order.
CASINO_GAMES: dict[str, tuple[str, str]] = {
    "TEEN_20": ("20-20 Teen Patti", "teenpatti"),
    "TEEN_9": ("Teen Patti Test", "teenpatti"),
    "TEEN": ("Teen Patti One Day", "teenpatti"),
    "TEEN_8": ("Open Teen Patti", "teenpatti"),
    "POKER_20": ("20-20 Poker", "poker"),
    "POKER_1_DAY": ("Poker 1 Day", "poker"),
    "POKER_9": ("6 Player Poker", "poker"),
    "AB_20": ("Andar Bahar", "card"),
    "ABJ": ("Andar Bahar 2", "card"),
    "DRAGON_TIGER_20": ("20-20 Dragon Tiger", "dragontiger"),
    "DRAGON_TIGER_20_2": ("20-20 Dragon Tiger 2", "dragontiger"),
    "DRAGON_TIGER_6": ("Dragon Tiger 1 Day", "dragontiger"),
    "DRAGON_TIGER_LION_20": ("20-20 Dragon Tiger Lion", "dragontiger"),
    "AAA": ("Amar Akbar Anthony", "card"),
    "LUCKY7": ("Lucky 7 A", "lucky7"),
    "LUCKY7EU": ("Lucky 7 B", "lucky7"),
    "CARD_32": ("32 Cards A", "card32"),
    "CARD32EU": ("32 Cards B", "card32"),
    "BACCARAT": ("Baccarat", "baccarat"),
    "BACCARAT2": ("Baccarat 2", "baccarat"),
    "CASINO_WAR": ("Casino War", "card"),
    "CRICKET_V3": ("Five Five Cricket", "cricket"),
    "SUPEROVER": ("Super Over", "cricket"),
    "CRICKET_MATCH_20": ("20-20 Cricket Match", "cricket"),
    "RACE20": ("Race 20-20", "race"),
    "BOLLYWOOD_TABLE": ("Bollywood Table", "card"),
    "WORLI2": ("Instant Worli", "worli"),
}

_cache: dict[str, tuple[float, Any]] = {}
_client: httpx.AsyncClient | None = None


def _http() -> httpx.AsyncClient:
    """One pooled client: a table refreshes every couple of seconds."""
    global _client
    if _client is None or _client.is_closed:
        headers = {"Accept": "application/json"}
        if settings.proexch_origin:
            headers["Origin"] = settings.proexch_origin
            headers["Referer"] = settings.proexch_origin.rstrip("/") + "/"
        _client = httpx.AsyncClient(
            timeout=httpx.Timeout(8.0, connect=4.0),
            headers=headers,
            limits=httpx.Limits(max_connections=20, max_keepalive_connections=10),
        )
    return _client


def unwrap(payload: Any) -> Any:
    """The feed wraps its body in `data` several times over; dig to the content."""
    while isinstance(payload, dict) and "data" in payload and len(payload) <= 3:
        payload = payload["data"]
    return payload


async def _get(path: str, ttl: float) -> Any:
    hit = _cache.get(path)
    if hit is not None and hit[0] > time.monotonic():
        return hit[1]
    r = await _http().get(settings.proexch_base_url + path)
    r.raise_for_status()
    value = unwrap(r.json())
    _cache[path] = (time.monotonic() + ttl, value)
    return value


def _float(value: Any, default: float = 0.0) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def parse_cards(raw: Any) -> list[str]:
    """"KCC,6DD,1" -> ["KCC", "6DD"]. A bare "1" is a card still face down."""
    if not raw:
        return []
    return [c.strip() for c in str(raw).split(",") if c.strip() and c.strip() != "1"]


def map_table(code: str, payload: Any) -> dict[str, Any]:
    """Normalise one table: the round, its countdown, cards and bet options."""
    body = payload if isinstance(payload, dict) else {}
    name, category = CASINO_GAMES.get(code, (code.replace("_", " ").title(), "card"))
    options = []
    for sub in body.get("sub") or []:
        price = _float(sub.get("b"))
        status = str(sub.get("gstatus") or "").upper() or "OPEN"
        options.append(
            {
                "sid": sub.get("sid"),
                "name": sub.get("nat"),
                "price": price,
                "size": _float(sub.get("bs")),
                "status": status,
                "open": status == "OPEN" and price > 1,
                "min_stake": _float(sub.get("min"), 100.0),
                "max_stake": _float(sub.get("max")),
                "group": sub.get("subtype") or "",
                "sort": sub.get("sr") or 0,
            }
        )
    options.sort(key=lambda o: o["sort"])

    timer = int(_float(body.get("lt")))
    return {
        "code": code,
        "name": name,
        "category": category,
        "gtype": body.get("gtype"),
        "round_id": str(body.get("mid") or ""),
        # `lt` counts down the betting window; 0 means the round is being dealt
        "timer": timer,
        "betting_open": timer > 0,
        "cards": parse_cards(body.get("card")),
        "remark": body.get("remark") or None,
        "options": options,
        "live": bool(options),
    }


async def fetch_table(code: str) -> dict[str, Any]:
    """The table as it stands. A game that is not running returns no options."""
    try:
        payload = await _get(f"{TUNNEL}/odds/{code}", ODDS_TTL)
    except Exception as exc:  # noqa: BLE001 — a dead table is not a broken lobby
        logger.info("casino odds failed for %s: %s", code, exc)
        payload = {}
    return map_table(code, payload)


async def fetch_results(code: str) -> list[dict[str, Any]]:
    """Recent rounds, newest first: `{round_id, winner}` where winner is a sid."""
    try:
        payload = await _get(f"{TUNNEL}/casino-last-10-results/{code}", RESULTS_TTL)
    except Exception as exc:  # noqa: BLE001
        logger.info("casino results failed for %s: %s", code, exc)
        return []
    rows = payload if isinstance(payload, list) else (payload or {}).get("data") or []
    out = []
    for row in rows:
        if not isinstance(row, dict) or not row.get("mid"):
            continue
        out.append(
            {
                "round_id": str(row["mid"]),
                # some tables settle more than one selection in a round
                "winners": [w.strip() for w in str(row.get("win") or "").split(",") if w.strip()],
            }
        )
    return out
