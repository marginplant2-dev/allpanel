"""RBAC & hierarchy scoping tests for user management."""
from __future__ import annotations

from app.core.enums import Role
from tests.conftest import auth_header, login, make_user


async def test_admin_creates_master_and_players_but_cannot_skip_a_level(client, db):
    await make_user(db, "admin1", Role.ADMIN)
    token = await login(client, "admin1")

    # ADMIN creates the next level down: MASTER
    res = await client.post(
        "/users",
        headers=auth_header(token),
        json={"username": "master1", "password": "secret123", "full_name": "Master One", "role": "MASTER"},
    )
    assert res.status_code == 201, res.text
    assert res.json()["data"]["parent_id"] is not None

    # ...and its own players
    res = await client.post(
        "/users",
        headers=auth_header(token),
        json={"username": "player1", "password": "secret123", "full_name": "P", "role": "USER"},
    )
    assert res.status_code == 201, res.text

    # but not an AGENT directly (that belongs under a MASTER)
    res = await client.post(
        "/users",
        headers=auth_header(token),
        json={"username": "agent1", "password": "secret123", "full_name": "A", "role": "AGENT"},
    )
    assert res.status_code == 403

    # nor anything above itself
    res = await client.post(
        "/users",
        headers=auth_header(token),
        json={"username": "sa1", "password": "secret123", "full_name": "S", "role": "SUPER_ADMIN"},
    )
    assert res.status_code == 403


async def test_hierarchy_scoping_isolates_admins(client, db):
    # Two independent admins
    admin_a = await make_user(db, "admin_a", Role.ADMIN)
    await make_user(db, "admin_b", Role.ADMIN)
    # A user under admin_a
    await make_user(db, "user_a", Role.USER, parent=admin_a)

    token_b = await login(client, "admin_b")
    res = await client.get("/users", headers=auth_header(token_b))
    assert res.status_code == 200
    usernames = {u["username"] for u in res.json()["data"]["items"]}
    assert "user_a" not in usernames  # admin_b must not see admin_a's downline


async def test_admin_cannot_read_foreign_user(client, db):
    admin_a = await make_user(db, "ad_a", Role.ADMIN)
    await make_user(db, "ad_b", Role.ADMIN)
    foreign = await make_user(db, "u_a", Role.USER, parent=admin_a)

    token_b = await login(client, "ad_b")
    res = await client.get(f"/users/{foreign['_id']}", headers=auth_header(token_b))
    assert res.status_code == 403


async def test_plain_user_cannot_list_users(client, db):
    await make_user(db, "plain", Role.USER)
    token = await login(client, "plain")
    res = await client.get("/users", headers=auth_header(token))
    assert res.status_code == 403


async def test_upline_does_not_see_downline_players(client, db):
    """A parent sees its direct children only — a child's players are the child's
    business (the parent has to log in as them to look)."""
    mother = await make_user(db, "mother", Role.MOTHER_ADMIN)
    sa = await make_user(db, "sa", Role.SUPER_ADMIN, parent=mother)
    await make_user(db, "sa_player", Role.USER, parent=sa)
    await make_user(db, "mother_player", Role.USER, parent=mother)

    token = await login(client, "mother")
    res = await client.get("/users?page_size=100", headers=auth_header(token))
    assert res.status_code == 200
    usernames = {u["username"] for u in res.json()["data"]["items"]}
    assert {"sa", "mother_player"}.issubset(usernames)
    assert "sa_player" not in usernames


async def test_master_sees_its_agents_players(client, db):
    master = await make_user(db, "master_x", Role.MASTER)
    agent = await make_user(db, "agent_x", Role.AGENT, parent=master)
    await make_user(db, "agent_player", Role.USER, parent=agent)

    token = await login(client, "master_x")
    res = await client.get("/users?page_size=100", headers=auth_header(token))
    usernames = {u["username"] for u in res.json()["data"]["items"]}
    assert {"agent_x", "agent_player"}.issubset(usernames)
