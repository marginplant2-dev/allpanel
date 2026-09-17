"""Credit transfer engine tests: success, overdraft, idempotency, permissions."""
from __future__ import annotations

from app.core.enums import Role
from tests.conftest import auth_header, login, make_user


async def set_wallet(db, user_id, available: float):
    await db.wallets.update_one(
        {"_id": str(user_id)},
        {"$set": {"available_balance": available, "locked_balance": 0.0}},
        upsert=True,
    )


async def test_transfer_success_moves_credits(client, db):
    admin = await make_user(db, "adm", Role.ADMIN)
    user = await make_user(db, "usr", Role.USER, parent=admin)
    await set_wallet(db, admin["_id"], 1000)

    token = await login(client, "adm")
    res = await client.post(
        "/credits/transfer",
        headers=auth_header(token),
        json={"to_user_id": str(user["_id"]), "amount": 250},
    )
    assert res.status_code == 201, res.text
    assert res.json()["data"]["status"] == "COMPLETED"

    admin_wallet = await db.wallets.find_one({"_id": str(admin["_id"])})
    user_wallet = await db.wallets.find_one({"_id": str(user["_id"])})
    assert admin_wallet["available_balance"] == 750
    assert user_wallet["available_balance"] == 250


async def test_insufficient_funds_rejected(client, db):
    admin = await make_user(db, "adm2", Role.ADMIN)
    user = await make_user(db, "usr2", Role.USER, parent=admin)
    await set_wallet(db, admin["_id"], 100)

    token = await login(client, "adm2")
    res = await client.post(
        "/credits/transfer",
        headers=auth_header(token),
        json={"to_user_id": str(user["_id"]), "amount": 500},
    )
    assert res.status_code == 400
    assert res.json()["error"]["code"] == "INSUFFICIENT_FUNDS"
    # Balance unchanged
    admin_wallet = await db.wallets.find_one({"_id": str(admin["_id"])})
    assert admin_wallet["available_balance"] == 100


async def test_idempotent_replay_transfers_once(client, db):
    admin = await make_user(db, "adm3", Role.ADMIN)
    user = await make_user(db, "usr3", Role.USER, parent=admin)
    await set_wallet(db, admin["_id"], 1000)
    token = await login(client, "adm3")

    body = {"to_user_id": str(user["_id"]), "amount": 300}
    headers = {**auth_header(token), "Idempotency-Key": "abc-123"}

    first = await client.post("/credits/transfer", headers=headers, json=body)
    second = await client.post("/credits/transfer", headers=headers, json=body)
    assert first.status_code == 201
    assert second.status_code == 201
    assert first.json()["data"]["transaction_id"] == second.json()["data"]["transaction_id"]

    admin_wallet = await db.wallets.find_one({"_id": str(admin["_id"])})
    assert admin_wallet["available_balance"] == 700  # debited only once


async def test_cannot_transfer_outside_hierarchy(client, db):
    admin_a = await make_user(db, "adm_a", Role.ADMIN)
    admin_b = await make_user(db, "adm_b", Role.ADMIN)
    foreign_user = await make_user(db, "u_b", Role.USER, parent=admin_b)
    await set_wallet(db, admin_a["_id"], 1000)

    token = await login(client, "adm_a")
    res = await client.post(
        "/credits/transfer",
        headers=auth_header(token),
        json={"to_user_id": str(foreign_user["_id"]), "amount": 100},
    )
    assert res.status_code == 403


async def test_cannot_transfer_to_self(client, db):
    admin = await make_user(db, "adm4", Role.ADMIN)
    await set_wallet(db, admin["_id"], 1000)
    token = await login(client, "adm4")
    res = await client.post(
        "/credits/transfer",
        headers=auth_header(token),
        json={"to_user_id": str(admin["_id"]), "amount": 100},
    )
    assert res.status_code == 422


async def test_plain_user_cannot_transfer(client, db):
    user = await make_user(db, "plain2", Role.USER)
    await set_wallet(db, user["_id"], 1000)
    token = await login(client, "plain2")
    res = await client.post(
        "/credits/transfer",
        headers=auth_header(token),
        json={"to_user_id": "000000000000000000000000", "amount": 10},
    )
    assert res.status_code == 403


async def test_wallet_and_history_endpoints(client, db):
    admin = await make_user(db, "adm5", Role.ADMIN)
    user = await make_user(db, "usr5", Role.USER, parent=admin)
    await set_wallet(db, admin["_id"], 1000)
    token_admin = await login(client, "adm5")
    await client.post(
        "/credits/transfer",
        headers=auth_header(token_admin),
        json={"to_user_id": str(user["_id"]), "amount": 400},
    )

    token_user = await login(client, "usr5")
    wallet = await client.get("/wallet", headers=auth_header(token_user))
    assert wallet.json()["data"]["available_balance"] == 400

    history = await client.get("/wallet/transactions", headers=auth_header(token_user))
    assert history.json()["data"]["meta"]["total"] == 1


async def test_coins_cannot_skip_a_level(client, db):
    """An admin tops up its master, and the master tops up the agent — the admin
    cannot reach past the master to fund the agent itself."""
    admin = await make_user(db, "adm_chain", Role.ADMIN)
    master = await make_user(db, "mst_chain", Role.MASTER, parent=admin)
    agent = await make_user(db, "agt_chain", Role.AGENT, parent=master)
    await set_wallet(db, admin["_id"], 1000)

    admin_token = await login(client, "adm_chain")
    res = await client.post(
        "/credits/transfer",
        headers=auth_header(admin_token),
        json={"to_user_id": str(agent["_id"]), "amount": 100},
    )
    assert res.status_code == 403, "grandchild top-up must be refused"

    res = await client.post(
        "/credits/transfer",
        headers=auth_header(admin_token),
        json={"to_user_id": str(master["_id"]), "amount": 400},
    )
    assert res.status_code == 201, res.text

    master_token = await login(client, "mst_chain")
    res = await client.post(
        "/credits/transfer",
        headers=auth_header(master_token),
        json={"to_user_id": str(agent["_id"]), "amount": 400},
    )
    assert res.status_code == 201, res.text

    assert (await db.wallets.find_one({"_id": str(master["_id"])}))["available_balance"] == 0
    assert (await db.wallets.find_one({"_id": str(agent["_id"])}))["available_balance"] == 400
