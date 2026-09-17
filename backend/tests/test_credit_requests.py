"""Deposit/withdraw request flow: create, approve, reject, permissions, races."""
from __future__ import annotations

from app.core.enums import Role
from tests.conftest import auth_header, login, make_user
from tests.test_ledger import set_wallet


async def test_deposit_request_approved_moves_credits(client, db):
    agent = await make_user(db, "agent1", Role.AGENT)
    user = await make_user(db, "user1", Role.USER, parent=agent)
    await set_wallet(db, agent["_id"], 1000)

    user_token = await login(client, "user1")
    res = await client.post(
        "/credit-requests",
        headers=auth_header(user_token),
        json={"type": "DEPOSIT", "amount": 200},
    )
    assert res.status_code == 201, res.text
    request_id = res.json()["data"]["id"]

    agent_token = await login(client, "agent1")
    approve = await client.post(
        f"/credit-requests/{request_id}/approve", headers=auth_header(agent_token), json={}
    )
    assert approve.status_code == 200, approve.text
    assert approve.json()["data"]["status"] == "APPROVED"

    agent_wallet = await db.wallets.find_one({"_id": str(agent["_id"])})
    user_wallet = await db.wallets.find_one({"_id": str(user["_id"])})
    assert agent_wallet["available_balance"] == 800
    assert user_wallet["available_balance"] == 200


async def test_withdraw_request_approved_moves_credits_back(client, db):
    agent = await make_user(db, "agent2", Role.AGENT)
    user = await make_user(db, "user2", Role.USER, parent=agent)
    await set_wallet(db, user["_id"], 500)

    user_token = await login(client, "user2")
    res = await client.post(
        "/credit-requests", headers=auth_header(user_token), json={"type": "WITHDRAW", "amount": 300}
    )
    request_id = res.json()["data"]["id"]

    agent_token = await login(client, "agent2")
    approve = await client.post(
        f"/credit-requests/{request_id}/approve", headers=auth_header(agent_token), json={}
    )
    assert approve.status_code == 200, approve.text

    agent_wallet = await db.wallets.find_one({"_id": str(agent["_id"])})
    user_wallet = await db.wallets.find_one({"_id": str(user["_id"])})
    assert agent_wallet["available_balance"] == 300
    assert user_wallet["available_balance"] == 200


async def test_withdraw_insufficient_balance_auto_rejected(client, db):
    agent = await make_user(db, "agent3", Role.AGENT)
    user = await make_user(db, "user3", Role.USER, parent=agent)
    await set_wallet(db, user["_id"], 50)

    user_token = await login(client, "user3")
    res = await client.post(
        "/credit-requests", headers=auth_header(user_token), json={"type": "WITHDRAW", "amount": 300}
    )
    request_id = res.json()["data"]["id"]

    agent_token = await login(client, "agent3")
    approve = await client.post(
        f"/credit-requests/{request_id}/approve", headers=auth_header(agent_token), json={}
    )
    assert approve.status_code == 400
    assert approve.json()["error"]["code"] == "INSUFFICIENT_FUNDS"

    req = await db.credit_requests.find_one({"user_id": str(user["_id"])})
    assert req["status"] == "REJECTED"


async def test_reject_leaves_balances_unchanged(client, db):
    agent = await make_user(db, "agent4", Role.AGENT)
    user = await make_user(db, "user4", Role.USER, parent=agent)
    await set_wallet(db, agent["_id"], 1000)

    user_token = await login(client, "user4")
    res = await client.post(
        "/credit-requests", headers=auth_header(user_token), json={"type": "DEPOSIT", "amount": 100}
    )
    request_id = res.json()["data"]["id"]

    agent_token = await login(client, "agent4")
    reject = await client.post(
        f"/credit-requests/{request_id}/reject",
        headers=auth_header(agent_token),
        json={"note": "not enough info"},
    )
    assert reject.status_code == 200
    assert reject.json()["data"]["status"] == "REJECTED"

    agent_wallet = await db.wallets.find_one({"_id": str(agent["_id"])})
    assert agent_wallet["available_balance"] == 1000


async def test_only_direct_parent_can_decide(client, db):
    agent = await make_user(db, "agent5", Role.AGENT)
    other_agent = await make_user(db, "agent5b", Role.AGENT)
    user = await make_user(db, "user5", Role.USER, parent=agent)
    await set_wallet(db, agent["_id"], 1000)

    user_token = await login(client, "user5")
    res = await client.post(
        "/credit-requests", headers=auth_header(user_token), json={"type": "DEPOSIT", "amount": 100}
    )
    request_id = res.json()["data"]["id"]

    other_token = await login(client, "agent5b")
    approve = await client.post(
        f"/credit-requests/{request_id}/approve", headers=auth_header(other_token), json={}
    )
    assert approve.status_code == 403


async def test_cannot_decide_twice(client, db):
    agent = await make_user(db, "agent6", Role.AGENT)
    user = await make_user(db, "user6", Role.USER, parent=agent)
    await set_wallet(db, agent["_id"], 1000)

    user_token = await login(client, "user6")
    res = await client.post(
        "/credit-requests", headers=auth_header(user_token), json={"type": "DEPOSIT", "amount": 100}
    )
    request_id = res.json()["data"]["id"]

    agent_token = await login(client, "agent6")
    first = await client.post(
        f"/credit-requests/{request_id}/approve", headers=auth_header(agent_token), json={}
    )
    second = await client.post(
        f"/credit-requests/{request_id}/approve", headers=auth_header(agent_token), json={}
    )
    assert first.status_code == 200
    assert second.status_code == 409
