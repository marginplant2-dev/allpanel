"""The bootstrap account has to be the MOTHER_ADMIN.

If it is seeded one rung down, self-registered players find no root to attach to
and land parentless: invisible in every panel and impossible to fund. That only
shows up on a live server, so it is pinned here.
"""
from app.core.enums import Role
from scripts import seed_data


async def test_bootstrap_account_is_mother_admin(db, monkeypatch):
    monkeypatch.setattr(seed_data, "connect_to_mongo", _noop)
    monkeypatch.setattr(seed_data, "ensure_indexes", _noop)
    monkeypatch.setattr(seed_data, "close_mongo_connection", _noop)

    await seed_data.seed()

    root = await db.users.find_one({"parent_id": None})
    assert root is not None
    assert root["role"] == Role.MOTHER_ADMIN.value


async def test_existing_root_is_promoted_and_orphans_adopted(db, monkeypatch):
    monkeypatch.setattr(seed_data, "connect_to_mongo", _noop)
    monkeypatch.setattr(seed_data, "ensure_indexes", _noop)
    monkeypatch.setattr(seed_data, "close_mongo_connection", _noop)

    await db.users.insert_one(
        {"username": "superadmin", "role": Role.SUPER_ADMIN.value, "parent_id": None, "hierarchy_path": []}
    )
    orphan = await db.users.insert_one(
        {"username": "walkin", "role": Role.USER.value, "parent_id": None, "hierarchy_path": []}
    )

    await seed_data.seed()

    root = await db.users.find_one({"username": "superadmin"})
    assert root["role"] == Role.MOTHER_ADMIN.value

    player = await db.users.find_one({"_id": orphan.inserted_id})
    assert player["parent_id"] == str(root["_id"])
    assert player["hierarchy_path"] == [str(root["_id"])]


async def _noop(*args, **kwargs):
    return None
