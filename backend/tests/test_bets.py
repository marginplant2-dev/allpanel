"""Bet placement + settlement: stake locking, payout math, win/loss/insufficient-funds."""
from __future__ import annotations

from datetime import timedelta

import pytest

from app.core.config import settings
from app.core.enums import Role
from app.modules.bets.service import BetService
from app.utils.time import utcnow
from app.utils.ids import to_object_id
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


async def test_in_play_betting_is_allowed_but_a_suspended_market_is_not(client, db):
    """Exchanges take bets while the match runs — the feed closes a market with its
    own suspended flag, which is what must stop a bet, not the kick-off time."""
    user = await make_user(db, "bettor3", Role.USER)
    await set_wallet(db, user["_id"], 1000)
    event_id = await _seed_event(db, start_offset=timedelta(hours=-1))
    token = await login(client, "bettor3")

    res = await client.post(
        "/bets",
        headers=auth_header(token),
        json={"event_id": event_id, "bookmaker_key": "testbook", "outcome_name": "Alpha FC", "stake": 50},
    )
    assert res.status_code == 201, res.text

    await db.events.update_one(
        {"_id": to_object_id(event_id)}, {"$set": {"bookmakers.0.suspended": True}}
    )
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


async def test_abandoned_event_refunds_the_stake(db, monkeypatch):
    """A market can close with no result and simply drop out of the feed. The
    stake must come back rather than sit locked forever."""
    from datetime import timedelta

    from app.core.enums import BetStatus
    from app.modules.bets.service import BetService
    from app.utils.time import utcnow

    user = await make_user(db, "stuck", Role.USER)
    uid = str(user["_id"])
    await db.wallets.update_one(
        {"_id": uid}, {"$set": {"available_balance": 0.0, "locked_balance": 500.0}}, upsert=True
    )
    await db.bets.insert_one(
        {
            "user_id": uid,
            "event_id": "cricket:1:1.1",
            "event_name": "Gone v Vanished",
            "home_team": "Gone",
            "away_team": "Vanished",
            "start_time": utcnow() - timedelta(hours=9),
            "outcome_name": "Gone",
            "price": 2.0,
            "stake": 500.0,
            "potential_payout": 1000.0,
            "status": BetStatus.PENDING.value,
            "placed_at": utcnow() - timedelta(hours=9),
            "settled_at": None,
            "payout": None,
        }
    )

    service = BetService(db)

    class Gone:
        async def get_live_data(self, event_id):
            return None

        async def get_event_detail(self, event_id):
            return None

    monkeypatch.setattr(service, "provider", Gone())
    assert await service.settle_pending() == 1

    bet = await db.bets.find_one({"user_id": uid})
    assert bet["status"] == BetStatus.VOID.value
    wallet = await db.wallets.find_one({"_id": uid})
    assert wallet["available_balance"] == 500.0 and wallet["locked_balance"] == 0.0


async def test_event_still_listed_is_left_pending(db, monkeypatch):
    from datetime import timedelta

    from app.core.enums import BetStatus
    from app.modules.bets.service import BetService
    from app.utils.time import utcnow

    user = await make_user(db, "waiting", Role.USER)
    uid = str(user["_id"])
    await db.bets.insert_one(
        {
            "user_id": uid,
            "event_id": "cricket:2:1.2",
            "start_time": utcnow() - timedelta(hours=9),
            "outcome_name": "A",
            "stake": 100.0,
            "potential_payout": 200.0,
            "status": BetStatus.PENDING.value,
            "placed_at": utcnow(),
            "settled_at": None,
            "payout": None,
        }
    )
    service = BetService(db)

    class StillThere:
        async def get_live_data(self, event_id):
            return None

        async def get_event_detail(self, event_id):
            return {"id": event_id}

    monkeypatch.setattr(service, "provider", StillThere())
    assert await service.settle_pending() == 0
    assert (await db.bets.find_one({"user_id": uid}))["status"] == BetStatus.PENDING.value


async def _seed_ladder_event(db, *, start_offset):
    """An event whose match-odds carry the three back and three lay rungs."""
    from app.utils.time import utcnow

    doc = {
        "sport_id": "cricket",
        "name": "Ladder XI vs Depth CC",
        "participants": ["Ladder XI", "Depth CC"],
        "home_team": "Ladder XI",
        "away_team": "Depth CC",
        "start_time": utcnow() + start_offset,
        "status": "live",
        "score": {},
        "bookmakers": [
            {
                "key": "match_odds:1",
                "title": "MATCH_ODDS",
                "kind": "match_odds",
                "suspended": False,
                "markets": [
                    {
                        "key": "h2h",
                        "outcomes": [
                            {
                                "name": "Ladder XI",
                                "price": 2.0,
                                "lay": 2.1,
                                "back_ladder": [
                                    {"price": 2.0, "size": "100"},
                                    {"price": 1.95, "size": "50"},
                                    {"price": 1.9, "size": "20"},
                                ],
                                "lay_ladder": [
                                    {"price": 2.1, "size": "80"},
                                    {"price": 2.2, "size": "40"},
                                    {"price": 2.3, "size": "10"},
                                ],
                            }
                        ],
                    }
                ],
            }
        ],
    }
    result = await db.events.insert_one(doc)
    return str(result.inserted_id)


async def test_a_deeper_rung_can_be_backed_at_the_price_shown(client, db):
    user = await make_user(db, "depth1", Role.USER)
    await set_wallet(db, user["_id"], 1000)
    event_id = await _seed_ladder_event(db, start_offset=timedelta(hours=1))
    token = await login(client, "depth1")

    res = await client.post(
        "/bets",
        headers=auth_header(token),
        json={
            "event_id": event_id,
            "bookmaker_key": "match_odds:1",
            "outcome_name": "Ladder XI",
            "stake": 100,
            "side": "BACK",
            "price": 1.9,
        },
    )
    assert res.status_code == 201, res.text
    bet = res.json()["data"]
    assert bet["price"] == 1.9 and bet["potential_payout"] == 190


async def test_a_price_that_left_the_ladder_is_refused(client, db):
    user = await make_user(db, "depth2", Role.USER)
    await set_wallet(db, user["_id"], 1000)
    event_id = await _seed_ladder_event(db, start_offset=timedelta(hours=1))
    token = await login(client, "depth2")

    res = await client.post(
        "/bets",
        headers=auth_header(token),
        json={
            "event_id": event_id,
            "bookmaker_key": "match_odds:1",
            "outcome_name": "Ladder XI",
            "stake": 100,
            "price": 5.0,
        },
    )
    assert res.status_code == 422
    wallet = await db.wallets.find_one({"_id": str(user["_id"])})
    assert wallet["available_balance"] == 1000  # nothing held for a refused bet


async def test_lay_holds_liability_and_pays_when_the_runner_loses(client, db):
    user = await make_user(db, "layer1", Role.USER)
    await set_wallet(db, user["_id"], 1000)
    event_id = await _seed_ladder_event(db, start_offset=timedelta(hours=1))
    token = await login(client, "layer1")

    res = await client.post(
        "/bets",
        headers=auth_header(token),
        json={
            "event_id": event_id,
            "bookmaker_key": "match_odds:1",
            "outcome_name": "Ladder XI",
            "stake": 100,
            "side": "LAY",
            "price": 2.1,
        },
    )
    assert res.status_code == 201, res.text
    bet = res.json()["data"]
    assert bet["side"] == "LAY"
    assert bet["exposure"] == 110.0          # liability = 100 x (2.1 - 1)
    assert bet["potential_payout"] == 210.0  # liability back + the backer's stake

    wallet = await db.wallets.find_one({"_id": str(user["_id"])})
    assert wallet["available_balance"] == 890 and wallet["locked_balance"] == 110
