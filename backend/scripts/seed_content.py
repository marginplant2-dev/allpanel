"""Seed mock content: game categories, games, sports and events.

Run with:  python -m scripts.seed_content
Idempotent per key/slug (skips existing).
"""
from __future__ import annotations

import asyncio
import base64
from datetime import timedelta

from app.core.database import (
    close_mongo_connection,
    connect_to_mongo,
    ensure_indexes,
    get_database,
)
from app.utils.time import utcnow

# Category -> (accent color, themed icon). Inline SVG so art always renders,
# no dependency on an external image CDN (picsum.photos was flaky/unreachable here).
CATEGORY_ART = {
    "live": ("#ef4444", "\U0001F534"),  # red dot
    "card": ("#22c55e", "\U0001F0CF"),  # joker/card
    "table": ("#f59e0b", "\U0001F3B0"),  # slot machine
    "virtual": ("#a855f7", "\U0001F3B2"),  # dice
    "featured": ("#3b82f6", "⭐"),  # star
    "popular": ("#ec4899", "\U0001F525"),  # fire
}


def _svg_data_url(svg: str) -> str:
    encoded = base64.b64encode(svg.encode("utf-8")).decode("ascii")
    return f"data:image/svg+xml;base64,{encoded}"


def _art(category: str, w: int, h: int, icon_size: int) -> str:
    color, icon = CATEGORY_ART.get(category, ("#3b82f6", "\U0001F3AE"))
    svg = (
        f"<svg xmlns='http://www.w3.org/2000/svg' width='{w}' height='{h}'>"
        "<defs><linearGradient id='bg' x1='0%' y1='0%' x2='0%' y2='100%'>"
        f"<stop offset='0%' style='stop-color:{color};stop-opacity:0.35'/>"
        "<stop offset='100%' style='stop-color:#0f172a;stop-opacity:1'/>"
        "</linearGradient></defs>"
        "<rect width='100%' height='100%' fill='url(#bg)'/>"
        f"<circle cx='50%' cy='50%' r='{min(w, h) // 3}' fill='{color}' opacity='0.2'/>"
        f"<text x='50%' y='50%' font-size='{icon_size}' text-anchor='middle' dominant-baseline='central'>{icon}</text>"
        "</svg>"
    )
    return _svg_data_url(svg)


def thumb(category: str) -> str:
    return _art(category, 480, 320, 96)


def banner(category: str) -> str:
    return _art(category, 1200, 480, 160)


CATEGORIES = [
    {"key": "live", "name": "Live Games", "sort_order": 1},
    {"key": "card", "name": "Card Games", "sort_order": 2},
    {"key": "table", "name": "Table Games", "sort_order": 3},
    {"key": "virtual", "name": "Virtual Games", "sort_order": 4},
    {"key": "featured", "name": "Featured Games", "sort_order": 5},
    {"key": "popular", "name": "Popular Games", "sort_order": 6},
]

GAMES = [
    ("Queen Card Arena", "queen-card-arena", "card", True),
    ("Royal Roulette", "royal-roulette", "table", True),
    ("Dragon Baccarat", "dragon-baccarat", "live", True),
    ("Lightning Blackjack", "lightning-blackjack", "live", False),
    ("Golden Andar Bahar", "golden-andar-bahar", "card", True),
    ("Neon Teen Patti", "neon-teen-patti", "card", False),
    ("Cosmic Dice", "cosmic-dice", "virtual", False),
    ("Aviator Sky", "aviator-sky", "virtual", True),
    ("Emperor Sic Bo", "emperor-sic-bo", "table", False),
    ("Velvet Poker Room", "velvet-poker-room", "live", False),
    ("Mega Wheel Deluxe", "mega-wheel-deluxe", "virtual", True),
    ("Crystal Keno", "crystal-keno", "popular", False),
]

# `group` mirrors The Odds API grouping so the nav tabs and sidebar tree work the
# same whether the live provider or this seeded data is being served.
SPORTS = [
    {"key": "cricket", "name": "Cricket", "group": "Cricket", "icon": "cricket", "sort_order": 1},
    {"key": "football", "name": "Football", "group": "Soccer", "icon": "football", "sort_order": 2},
    {"key": "tennis", "name": "Tennis", "group": "Tennis", "icon": "tennis", "sort_order": 3},
    {"key": "basketball", "name": "Basketball", "group": "Basketball", "icon": "basketball", "sort_order": 4},
    {"key": "table-tennis", "name": "Table Tennis", "group": "Table Tennis", "icon": "table-tennis", "sort_order": 5},
    {"key": "horse-racing", "name": "Horse Racing", "group": "Horse Racing", "icon": "horse", "sort_order": 6},
]

EVENTS = [
    ("cricket", "Mumbai Titans vs Delhi Chargers", ["Mumbai Titans", "Delhi Chargers"], "T20 Premier", "live", {"Mumbai Titans": 142, "Delhi Chargers": 98}),
    ("cricket", "Chennai Kings vs Bengal Warriors", ["Chennai Kings", "Bengal Warriors"], "T20 Premier", "upcoming", None),
    ("football", "Red United vs City Blues", ["Red United", "City Blues"], "Prime League", "live", {"Red United": 2, "City Blues": 1}),
    ("football", "Northside FC vs Harbor Athletic", ["Northside FC", "Harbor Athletic"], "Prime League", "upcoming", None),
    ("tennis", "A. Petrov vs L. Moreau", ["A. Petrov", "L. Moreau"], "Grand Series", "live", {"A. Petrov": 1, "L. Moreau": 1}),
    ("basketball", "Skyline Hawks vs Metro Bolts", ["Skyline Hawks", "Metro Bolts"], "Pro Hoops", "upcoming", None),
    ("table-tennis", "K. Tanaka vs S. Ali", ["K. Tanaka", "S. Ali"], "World Tour", "live", {"K. Tanaka": 2, "S. Ali": 3}),
    ("horse-racing", "Sunday Gold Cup", ["Field of 12"], "Gold Cup", "upcoming", None),
    ("cricket", "Rajasthan Royals vs Punjab Kings", ["Rajasthan Royals", "Punjab Kings"], "T20 Premier", "upcoming", None),
    ("cricket", "Kochi Blue Tigers vs Trivandrum Royals", ["Kochi Blue Tigers", "Trivandrum Royals"], "State League", "upcoming", None),
    ("cricket", "England W vs Ireland W", ["England W", "Ireland W"], "Womens T20", "upcoming", None),
    ("football", "Harbor Athletic vs Red United", ["Harbor Athletic", "Red United"], "Prime Cup", "upcoming", None),
    ("football", "Dublin Guardians vs Rotterdam Dockers", ["Dublin Guardians", "Rotterdam Dockers"], "Euro Series", "upcoming", None),
    ("tennis", "M. Chen vs D. Rossi", ["M. Chen", "D. Rossi"], "Grand Series", "upcoming", None),
    ("basketball", "Coastal Sharks vs Summit Peaks", ["Coastal Sharks", "Summit Peaks"], "Pro Hoops", "upcoming", None),
    ("table-tennis", "R. Novak vs P. Sharma", ["R. Novak", "P. Sharma"], "World Tour", "upcoming", None),
]

DEMO_BOOKMAKER = {"key": "sportx", "title": "SportX Exchange"}


def demo_bookmakers(sport_key: str, participants: list[str], seed: int) -> list[dict]:
    """Deterministic virtual-credit prices for the seeded board.

    No real market sits behind these — they exist so the exchange grid, bet slip
    and settlement flow are exercisable without an external odds key.
    """
    home = round(1.60 + (seed % 5) * 0.12, 2)
    outcomes = [{"name": participants[0], "price": home}]
    if len(participants) > 1:
        if sport_key in {"cricket", "football"}:
            outcomes.append({"name": "Draw", "price": round(3.00 + (seed % 3) * 0.40, 2)})
        outcomes.append({"name": participants[1], "price": round(3.60 - home, 2)})
    return [{**DEMO_BOOKMAKER, "markets": [{"key": "h2h", "outcomes": outcomes}]}]


async def seed() -> None:
    await connect_to_mongo()
    await ensure_indexes()
    db = get_database()
    now = utcnow()

    for idx, cat in enumerate(CATEGORIES):
        await db.game_categories.update_one(
            {"key": cat["key"]}, {"$setOnInsert": {**cat, "status": "active"}}, upsert=True
        )
    print(f"[seed] categories: {len(CATEGORIES)}")

    for order, (name, slug, category, featured) in enumerate(GAMES):
        await db.games.update_one(
            {"slug": slug},
            {
                # Regenerated every run so a fix to thumb()/banner() reaches existing docs too.
                "$set": {
                    "thumbnail_url": thumb(category),
                    "banner_url": banner(category),
                },
                "$setOnInsert": {
                    "name": name,
                    "slug": slug,
                    "provider": "mock_provider",
                    "category": category,
                    "status": "active",
                    "featured": featured,
                    "sort_order": order,
                    "tags": [category],
                    "created_at": now,
                    "updated_at": now,
                },
            },
            upsert=True,
        )
    print(f"[seed] games: {len(GAMES)}")

    sport_ids: dict[str, str] = {}
    for sport in SPORTS:
        await db.sports.update_one(
            {"key": sport["key"]},
            # `group` is refreshed so an already-seeded DB gains the nav grouping.
            {
                "$set": {"group": sport["group"]},
                "$setOnInsert": {
                    **{k: v for k, v in sport.items() if k != "group"},
                    "status": "active",
                },
            },
            upsert=True,
        )
        doc = await db.sports.find_one({"key": sport["key"]})
        sport_ids[sport["key"]] = str(doc["_id"])
    print(f"[seed] sports: {len(SPORTS)}")

    for i, (sport_key, name, participants, league, status, score) in enumerate(EVENTS):
        # Kick-off times are rebased on every run: a board whose "upcoming" games
        # started yesterday rejects every bet ("betting is closed").
        start = now - timedelta(hours=1) if status == "live" else now + timedelta(hours=i + 1)
        await db.events.update_one(
            {"name": name},
            {
                "$set": {
                    "bookmakers": demo_bookmakers(sport_key, participants, i),
                    "start_time": start,
                    "status": status,
                    "updated_at": now,
                },
                "$setOnInsert": {
                    "sport_id": sport_ids[sport_key],
                    "participants": participants,
                    "league": league,
                    "score": score or {},
                    "markets": [],
                    "created_at": now,
                },
            },
            upsert=True,
        )
    print(f"[seed] events: {len(EVENTS)}")

    await close_mongo_connection()
    print("[seed] content seed complete")


if __name__ == "__main__":
    asyncio.run(seed())
