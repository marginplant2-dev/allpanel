"""Live casino tables: normalisation, bet validation and round settlement."""
import pytest

from app.core.enums import BetStatus, Role
from app.modules.casino import live_service as live
from app.modules.providers.proexch_casino import map_table, parse_cards, unwrap
from tests.conftest import make_user

TEEN20 = {
    "mid": 102260921134126,
    "lt": 14,
    "ft": 1,
    "card": "KCC,6DD,QDD,1,1,1",
    "gtype": "teen20",
    "remark": "",
    "sub": [
        {"sid": 1, "nat": "Player A", "b": 1.98, "bs": 600000.0, "sr": 1, "gstatus": "OPEN",
         "min": 100.0, "max": 500000.0, "subtype": "Player", "etype": "fancy"},
        {"sid": 3, "nat": "Pair Plus A", "b": 2.0, "bs": 600000.0, "sr": 3, "gstatus": "SUSPENDED",
         "min": 100.0, "max": 25000.0, "subtype": "Pair", "etype": "fancy"},
    ],
}


def test_the_feeds_nested_envelope_is_unwrapped():
    assert unwrap({"statusCode": 200, "data": {"data": {"data": {"mid": 7}}}}) == {"mid": 7}


def test_face_down_cards_are_not_shown():
    assert parse_cards("KCC,6DD,1,1") == ["KCC", "6DD"]
    assert parse_cards("1,1,1") == []
    assert parse_cards(None) == []


def test_table_maps_round_countdown_and_selections():
    t = map_table("TEEN_20", TEEN20)
    assert t["name"] == "20-20 Teen Patti" and t["category"] == "teenpatti"
    assert t["round_id"] == "102260921134126"
    assert t["timer"] == 14 and t["betting_open"] is True
    assert t["cards"] == ["KCC", "6DD", "QDD"]
    assert [o["name"] for o in t["options"]] == ["Player A", "Pair Plus A"]
    assert t["options"][0]["open"] is True
    assert t["options"][1]["open"] is False  # suspended selection cannot be backed


def test_a_table_that_is_not_running_has_no_options():
    t = map_table("POKER_20", {})
    assert t["live"] is False and t["options"] == [] and t["betting_open"] is False


async def _table(db, monkeypatch, *, timer=14):
    payload = {**TEEN20, "lt": timer}
    monkeypatch.setattr(live, "fetch_table", lambda code: _async(map_table(code, payload)))
    monkeypatch.setattr(live, "fetch_results", lambda code: _async([]))
    return live.CasinoLiveService(db)


async def _async(value):
    return value


async def test_bet_is_refused_once_the_round_moves_on(db, monkeypatch):
    user = await make_user(db, "casino1", Role.USER)
    await db.wallets.update_one({"_id": str(user["_id"])}, {"$set": {"available_balance": 5000.0}}, upsert=True)
    service = await _table(db, monkeypatch)
    from app.core.dependencies import CurrentUser

    actor = CurrentUser(user)
    with pytest.raises(Exception) as err:
        await service.place_bet(actor, code="TEEN_20", round_id="999", sid="1", stake=500)
    assert "closed" in str(err.value).lower()


async def test_bet_debits_the_stake_and_settles_on_the_result(db, monkeypatch):
    from app.core.dependencies import CurrentUser

    user = await make_user(db, "casino2", Role.USER)
    uid = str(user["_id"])
    await db.wallets.update_one({"_id": uid}, {"$set": {"available_balance": 5000.0, "locked_balance": 0.0}}, upsert=True)
    service = await _table(db, monkeypatch)

    bet = await service.place_bet(CurrentUser(user), code="TEEN_20", round_id="102260921134126", sid="1", stake=500)
    assert bet["price"] == 1.98 and bet["potential_payout"] == 990.0
    wallet = await db.wallets.find_one({"_id": uid})
    assert wallet["available_balance"] == 4500.0

    monkeypatch.setattr(
        live, "fetch_results", lambda code: _async([{"round_id": "102260921134126", "winners": ["1"]}])
    )
    assert await service.settle_pending() == 1

    settled = await db.casino_bets.find_one({"user_id": uid})
    assert settled["status"] == BetStatus.WON.value and settled["payout"] == 990.0
    wallet = await db.wallets.find_one({"_id": uid})
    assert wallet["available_balance"] == 5490.0


async def test_a_losing_round_keeps_the_stake(db, monkeypatch):
    from app.core.dependencies import CurrentUser

    user = await make_user(db, "casino3", Role.USER)
    uid = str(user["_id"])
    await db.wallets.update_one({"_id": uid}, {"$set": {"available_balance": 1000.0}}, upsert=True)
    service = await _table(db, monkeypatch)
    await service.place_bet(CurrentUser(user), code="TEEN_20", round_id="102260921134126", sid="1", stake=200)

    monkeypatch.setattr(
        live, "fetch_results", lambda code: _async([{"round_id": "102260921134126", "winners": ["2"]}])
    )
    assert await service.settle_pending() == 1
    assert (await db.casino_bets.find_one({"user_id": uid}))["status"] == BetStatus.LOST.value
    assert (await db.wallets.find_one({"_id": uid}))["available_balance"] == 800.0


async def test_results_are_named_from_the_live_tables_own_options(db, monkeypatch):
    """A result is a bare sid. While the table is live its options name every sid,
    and those names are remembered so a closed table still reads "Player A"."""
    service = await _table(db, monkeypatch)
    monkeypatch.setattr(
        live, "fetch_results", lambda code: _async([{"round_id": "1", "winners": ["1"]}])
    )

    t = await service.table("TEEN_20")
    assert t["results"][0]["winner_names"] == ["Player A"]

    # the table goes dark: no options, but the learned labels survive
    monkeypatch.setattr(live, "fetch_table", lambda code: _async(map_table(code, {})))
    closed = await service.table("TEEN_20")
    assert closed["live"] is False
    assert closed["results"][0]["winner_names"] == ["Player A"]


async def test_a_table_never_seen_live_still_names_its_winners(db, monkeypatch):
    """Dragon Tiger 1 Day runs once a day; its results should not read "1" and "2"
    just because we have not caught it dealing yet."""
    monkeypatch.setattr(live, "fetch_table", lambda code: _async(map_table(code, {})))
    monkeypatch.setattr(
        live, "fetch_results", lambda code: _async([{"round_id": "9", "winners": ["2"]}])
    )
    service = live.CasinoLiveService(db)
    t = await service.table("DRAGON_TIGER_6")
    assert t["results"][0]["winner_names"] == ["Tiger"]
