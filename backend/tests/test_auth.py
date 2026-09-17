"""Auth flow tests: register, login, me, refresh, suspended login."""
from __future__ import annotations

from app.core.enums import Role, UserStatus
from tests.conftest import auth_header, login, make_user


async def test_register_and_me(client):
    res = await client.post(
        "/auth/register",
        json={"username": "alice", "password": "secret123", "full_name": "Alice"},
    )
    assert res.status_code == 201, res.text
    body = res.json()
    assert body["success"] is True
    token = body["data"]["access_token"]
    assert body["data"]["user"]["role"] == "USER"

    me = await client.get("/auth/me", headers=auth_header(token))
    assert me.status_code == 200
    assert me.json()["data"]["username"] == "alice"


async def test_duplicate_registration_conflict(client):
    payload = {"username": "bob", "password": "secret123", "full_name": "Bob"}
    assert (await client.post("/auth/register", json=payload)).status_code == 201
    dup = await client.post("/auth/register", json=payload)
    assert dup.status_code == 409
    assert dup.json()["error"]["code"] == "CONFLICT"


async def test_login_and_refresh(client, db):
    await make_user(db, "carol", Role.USER)
    res = await client.post("/auth/login", json={"username": "carol", "password": "secret123"})
    assert res.status_code == 200
    data = res.json()["data"]
    refresh = data["refresh_token"]

    r = await client.post("/auth/refresh", json={"refresh_token": refresh})
    assert r.status_code == 200
    assert r.json()["data"]["access_token"]


async def test_bad_password_rejected(client, db):
    await make_user(db, "dave", Role.USER)
    res = await client.post("/auth/login", json={"username": "dave", "password": "wrong"})
    assert res.status_code == 401
    assert res.json()["error"]["code"] == "UNAUTHENTICATED"


async def test_suspended_user_cannot_login(client, db):
    await make_user(db, "eve", Role.USER, status=UserStatus.SUSPENDED)
    res = await client.post("/auth/login", json={"username": "eve", "password": "secret123"})
    assert res.status_code == 401


async def test_me_requires_auth(client):
    res = await client.get("/auth/me")
    assert res.status_code == 401
