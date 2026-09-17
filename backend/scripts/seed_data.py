"""Seed the bootstrap MOTHER_ADMIN account and its wallet.

Run with:  python -m scripts.seed_data
Idempotent: safe to run multiple times.
"""
from __future__ import annotations

import asyncio

from app.core.config import settings
from app.core.database import (
    connect_to_mongo,
    close_mongo_connection,
    ensure_indexes,
    get_database,
)
from app.core.enums import Role, UserStatus
from app.core.security import hash_password
from app.utils.time import utcnow


async def seed() -> None:
    await connect_to_mongo()
    await ensure_indexes()
    db = get_database()

    # Role rename migration (old tree: SUPER_ADMIN > MASTER_ADMIN > ADMIN > AGENT).
    # The root account becomes the MOTHER_ADMIN; MASTER_ADMIN accounts become MASTERs.
    renamed = await db.users.update_many({"role": "MASTER_ADMIN"}, {"$set": {"role": Role.MASTER.value}})
    promoted = await db.users.update_many(
        {"role": Role.SUPER_ADMIN.value, "parent_id": None}, {"$set": {"role": Role.MOTHER_ADMIN.value}}
    )
    if renamed.modified_count or promoted.modified_count:
        print(f"[seed] migrated roles: {renamed.modified_count} -> MASTER, {promoted.modified_count} -> MOTHER_ADMIN")

    # Self-registered players used to land with no parent, which leaves them in
    # nobody's panel and unfundable — adopt them into the root account.
    root = await db.users.find_one({"role": Role.MOTHER_ADMIN.value, "parent_id": None})
    if root is not None:
        adopted = await db.users.update_many(
            {"role": Role.USER.value, "parent_id": None},
            {"$set": {"parent_id": str(root["_id"]), "hierarchy_path": [str(root["_id"])]}},
        )
        if adopted.modified_count:
            print(f"[seed] adopted {adopted.modified_count} orphan player(s) into the root account")

    existing = await db.users.find_one({"username": settings.superadmin_username})
    if existing:
        print(f"[seed] Root admin '{settings.superadmin_username}' already exists ({existing['_id']}).")
        await close_mongo_connection()
        return

    now = utcnow()
    doc = {
        "username": settings.superadmin_username,
        "password_hash": hash_password(settings.superadmin_password),
        "full_name": settings.superadmin_fullname,
        "role": Role.SUPER_ADMIN.value,
        "parent_id": None,
        "hierarchy_path": [],
        "status": UserStatus.ACTIVE.value,
        "credit_limit": 0.0,
        "notes": "Bootstrap mother administrator",
        "two_factor_enabled": False,
        "created_at": now,
        "updated_at": now,
        "last_login": None,
    }
    result = await db.users.insert_one(doc)
    user_id = str(result.inserted_id)

    await db.wallets.update_one(
        {"_id": user_id},
        {
            "$set": {
                "available_balance": float(settings.superadmin_initial_credits),
                "locked_balance": 0.0,
                "updated_at": now,
            }
        },
        upsert=True,
    )

    print(f"[seed] Created MOTHER_ADMIN '{settings.superadmin_username}' ({user_id})")
    print(f"[seed] Allocated {settings.superadmin_initial_credits} virtual credits.")
    print("[seed] Remember to change the password after first login.")
    await close_mongo_connection()


if __name__ == "__main__":
    asyncio.run(seed())
