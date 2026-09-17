"""Bet placement + settlement: stake locking, payout math, win/loss/insufficient-funds."""
from __future__ import annotations

from datetime import timedelta

import pytest

from app.core.config import settings
from app.core.enums import Role
from app.modules.bets.service import BetService
from app.utils.time import utcnow
from tests.conftest import auth_header, login, make_user
from tests.test_ledger import set_wallet


@pytest.fixture(autouse=True)
def _force_mock_provider():
    """These tests seed `db.events` directly, so force the mock provider

    regardless of a developer's local .env (which may point at the real
    TheOddsProvider + API key for manual testing).
    """
    original = settings.sports_provider
    settings.sports_provider = "mock"
    yield
    settings.sports_provider = original


async def _seed_event(db, *, home="Alpha FC", away="Beta United", start_offset=timedelta(hours=-1)):
    doc = {
        "sport_id": "soccer_test",
        "name": f"{home} vs {away}",
        "participants": [home, away],
        "home_team": home,
        "away_team": away,
        "league": "Test League",
        "start_time": utcnow() + start_offset,
        "status": "upcoming",
        "score": None,
        "bookmakers": [
            {
                "key": "testbook",
                "title": "TestBook",
                "markets": [
                    {
                        "key": "h2h",
                        "outcomes": [
                            {"name": home, "price": 2.5},
                            {"name": away, "price": 1.6},
                        ],
                    }
                ],
            }
        ],
    }
    result = await db.events.insert_one(doc)
    return str(result.inserted_id)


async def test_place_bet_locks_stake_and_computes_payout(client, db):
    user = await make_user(db, "bettor1", Role.USER)
    await set_wallet(db, user["_id"], 1000)
    event_id = await _seed_event(db, start_offset=timedelta(hours=1))

    token = await login(client, "bettor1")
    res = await client.post(
        "/bets",
        headers=auth_header(token),
        json={"event_id": event_id, "bookmaker_key": "testbook", "outcome_name": "Alpha FC", "stake": 100},
    )
    assert res.status_code == 201, res.text
    body = res.json()["data"]
    assert body["status"] == "PENDING"
    assert body["price"] == 2.5
    assert body["potential_payout"] == 250.0

    wallet = await db.wallets.find_one({"_id": str(user["_id"])})
    assert wallet["available_balance"] == 900
    assert wallet["locked_balance"] == 100


async def test_place_bet_insufficient_funds(client, db):
    user = await make_user(db, "bettor2", Role.USER)
    await set_wallet(db, user["_id"], 10)
    event_id = await _seed_event(db, start_offset=timedelta(hours=1))

    token = await login(client, "bettor2")
    res = await client.post(
        "/bets",
        headers=auth_header(token),
        json={"event_id": event_id, "bookmaker_key": "testbook", "outcome_name": "Alpha FC", "stake": 100},
    )
    assert res.status_code == 400
    assert res.json()["error"]["code"] == "INSUFFICIENT_FUNDS"


async def test_cannot_bet_on_started_event(client, db):
    user = await make_user(db, "bettor3", Role.USER)
    await set_wallet(db, user["_id"], 1000)
    event_id = await _seed_event(db, start_offset=timedelta(hours=-1))

    token = await login(client, "bettor3")
    res = await client.post(
        "/bets",
        headers=auth_header(token),
        json={"event_id": event_id, "bookmaker_key": "testbook", "outcome_name": "Alpha FC", "stake": 50},
    )
    assert res.status_code == 422


async def test_settlement_pays_winner_and_closes_loser(client, db):
    winner = await make_user(db, "bettor4", Role.USER)
    loser = await make_user(db, "bettor5", Role.USER)
    await set_wallet(db, winner["_id"], 1000)
    await set_wallet(db, loser["_id"], 1000)
    event_id = await _seed_event(db, start_offset=timedelta(hours=1))

    winner_token = await login(client, "bettor4")
    loser_token = await login(client, "bettor5")
    await client.post(
        "/bets",
        headers=auth_header(winner_token),
        json={"event_id": event_id, "bookmaker_key": "testbook", "outcome_name": "Alpha FC", "stake": 100},
    )
    await client.post(
        "/bets",
        headers=auth_header(loser_token),
        json={"event_id": event_id, "bookmaker_key": "testbook", "outcome_name": "Beta United", "stake": 100},
    )

    await db.events.update_one(
        {"_id": __import__("bson").ObjectId(event_id)},
        {"$set": {"status": "finished", "score": {"Alpha FC": 2, "Beta United": 1}}},
    )

    settled = await BetService(db).settle_pending()
    assert settled == 2

    winner_wallet = await db.wallets.find_one({"_id": str(winner["_id"])})
    loser_wallet = await db.wallets.find_one({"_id": str(loser["_id"])})
    assert winner_wallet["available_balance"] == 1150  # 900 + 250 payout
    assert winner_wallet["locked_balance"] == 0
    assert loser_wallet["available_balance"] == 900
    assert loser_wallet["locked_balance"] == 0

    winner_bet = await db.bets.find_one({"user_id": str(winner["_id"])})
    loser_bet = await db.bets.find_one({"user_id": str(loser["_id"])})
    assert winner_bet["status"] == "WON"
    assert loser_bet["status"] == "LOST"

    # Re-running settlement must not double-pay (bets are no longer PENDING).
    assert await BetService(db).settle_pending() == 0
