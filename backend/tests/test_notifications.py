"""Notification creation on transfer + notification endpoints."""
from __future__ import annotations

from app.core.enums import Role
from tests.conftest import auth_header, login, make_user


async def set_wallet(db, user_id, available: float):
    await db.wallets.update_one(
        {"_id": str(user_id)},
        {"$set": {"available_balance": available, "locked_balance": 0.0}},
        upsert=True,
    )


async def test_transfer_creates_recipient_notification(client, db):
    admin = await make_user(db, "notadmin", Role.ADMIN)
    user = await make_user(db, "notuser", Role.USER, parent=admin)
    await set_wallet(db, admin["_id"], 1000)

    token_admin = await login(client, "notadmin")
    res = await client.post(
        "/credits/transfer",
        headers=auth_header(token_admin),
        json={"to_user_id": str(user["_id"]), "amount": 150},
    )
    assert res.status_code == 201, res.text

    token_user = await login(client, "notuser")
    notifs = await client.get("/notifications", headers=auth_header(token_user))
    assert notifs.status_code == 200
    body = notifs.json()["data"]
    assert body["meta"]["total"] == 1
    assert body["unread"] == 1
    assert body["items"][0]["type"] == "CREDIT_RECEIVED"


async def test_mark_notification_read(client, db):
    admin = await make_user(db, "notadmin2", Role.ADMIN)
    user = await make_user(db, "notuser2", Role.USER, parent=admin)
    await set_wallet(db, admin["_id"], 1000)
    token_admin = await login(client, "notadmin2")
    await client.post(
        "/credits/transfer",
        headers=auth_header(token_admin),
        json={"to_user_id": str(user["_id"]), "amount": 50},
    )

    token_user = await login(client, "notuser2")
    listing = await client.get("/notifications", headers=auth_header(token_user))
    notif_id = listing.json()["data"]["items"][0]["id"]

    read = await client.post(f"/notifications/{notif_id}/read", headers=auth_header(token_user))
    assert read.status_code == 200

    after = await client.get("/notifications", headers=auth_header(token_user))
    assert after.json()["data"]["unread"] == 0
