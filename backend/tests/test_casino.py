"""Casino catalogue import and the provider's seamless wallet callback."""
from app.core.config import settings
from app.core.enums import Role
from app.modules.casino.service import CasinoService
from tests.conftest import auth_header, login, make_user


async def test_import_upserts_by_game_uid_and_can_deactivate(client, db):
    await make_user(db, "boss", Role.MOTHER_ADMIN)
    token = await login(client, "boss")

    res = await client.post(
        "/games/import",
        headers=auth_header(token),
        json={
            "games": [
                {"name": "Aviator", "game_uid": "uid-1", "category": "crash", "thumbnail_url": "http://x/a.png"},
                {"name": "Andar Bahar", "game_uid": "uid-2", "category": "live"},
            ]
        },
    )
    assert res.status_code == 200, res.text
    assert res.json()["data"]["created"] == 2

    game = await db.games.find_one({"game_uid": "uid-1"})
    assert game["slug"] == "aviator" and game["thumbnail_url"] == "http://x/a.png"

    # re-import with replace: uid-2 is gone from the provider, so it is switched off
    res = await client.post(
        "/games/import",
        headers=auth_header(token),
        json={
            "games": [{"name": "Aviator", "game_uid": "uid-1", "category": "crash"}],
            "replace": True,
        },
    )
    assert res.json()["data"]["deactivated"] == 1
    assert (await db.games.find_one({"game_uid": "uid-2"}))["status"] == "inactive"


async def test_callback_applies_bet_and_win_once(db, monkeypatch):
    monkeypatch.setattr(settings, "gamblly_api_key", "secret-key")
    player = await make_user(db, "player", Role.USER)
    pid = str(player["_id"])
    await db.wallets.update_one(
        {"_id": pid}, {"$set": {"available_balance": 1000.0, "locked_balance": 0.0}}, upsert=True
    )
    service = CasinoService(db)

    bet = {"api_key": "secret-key", "player_uid": pid, "bet_amount": 100, "win_amount": 0, "txn_id": "t1"}
    assert (await service.handle_callback(bet))["balance"] == 900

    # the provider retries the same txn: money must not move twice
    assert (await service.handle_callback(bet))["balance"] == 900

    win = {"api_key": "secret-key", "player_uid": pid, "bet_amount": 0, "win_amount": 250, "txn_id": "t2"}
    assert (await service.handle_callback(win))["balance"] == 1150


async def test_callback_rejects_a_bad_key(db, monkeypatch):
    monkeypatch.setattr(settings, "gamblly_api_key", "secret-key")
    player = await make_user(db, "p2", Role.USER)
    service = CasinoService(db)
    try:
        await service.handle_callback({"api_key": "wrong", "player_uid": str(player["_id"])})
    except Exception as exc:
        assert "Unauthorized" in str(exc)
    else:
        raise AssertionError("a bad api_key must be refused")


async def test_notice_action_does_not_move_money(db, monkeypatch):
    monkeypatch.setattr(settings, "gamblly_api_key", "secret-key")
    player = await make_user(db, "p3", Role.USER)
    pid = str(player["_id"])
    await db.wallets.update_one({"_id": pid}, {"$set": {"available_balance": 500.0}}, upsert=True)
    service = CasinoService(db)
    out = await service.handle_callback(
        {"api_key": "secret-key", "player_uid": pid, "action": "deposit_required", "bet_amount": 99}
    )
    assert out["balance"] == 500
