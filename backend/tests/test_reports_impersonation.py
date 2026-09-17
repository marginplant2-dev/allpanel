"""Tests for reporting aggregation and impersonation flow."""
from __future__ import annotations

from app.core.enums import Role
from tests.conftest import auth_header, login, make_user


async def test_dashboard_scoped_counts(client, db):
    admin = await make_user(db, "repadmin", Role.ADMIN)
    await make_user(db, "repuser1", Role.USER, parent=admin)
    await make_user(db, "repuser2", Role.USER, parent=admin)

    token = await login(client, "repadmin")
    res = await client.get("/reports/dashboard", headers=auth_header(token))
    assert res.status_code == 200
    data = res.json()["data"]
    # admin + 2 users = 3 within scope
    assert data["total_users"] == 3
    assert data["active_users"] == 3


async def test_user_cannot_access_reports(client, db):
    await make_user(db, "repplain", Role.USER)
    token = await login(client, "repplain")
    res = await client.get("/reports/dashboard", headers=auth_header(token))
    assert res.status_code == 403


async def test_impersonation_start_and_end(client, db):
    admin = await make_user(db, "impadmin", Role.ADMIN)
    target = await make_user(db, "imptarget", Role.USER, parent=admin)

    token = await login(client, "impadmin")
    start = await client.post(
        "/impersonation/start",
        headers=auth_header(token),
        json={"target_id": str(target["_id"])},
    )
    assert start.status_code == 200, start.text
    imp_token = start.json()["data"]["access_token"]
    assert start.json()["data"]["user"]["username"] == "imptarget"

    # The impersonation token acts as the target
    me = await client.get("/auth/me", headers=auth_header(imp_token))
    assert me.json()["data"]["username"] == "imptarget"

    # End returns to the admin
    end = await client.post("/impersonation/end", headers=auth_header(imp_token))
    assert end.status_code == 200
    assert end.json()["data"]["user"]["username"] == "impadmin"


async def test_cannot_impersonate_outside_hierarchy(client, db):
    await make_user(db, "impadmin2", Role.ADMIN)
    other_admin = await make_user(db, "impadmin3", Role.ADMIN)
    foreign = await make_user(db, "impforeign", Role.USER, parent=other_admin)

    token = await login(client, "impadmin2")
    res = await client.post(
        "/impersonation/start",
        headers=auth_header(token),
        json={"target_id": str(foreign["_id"])},
    )
    assert res.status_code == 403
