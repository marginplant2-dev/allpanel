"""MongoDB connection lifecycle and index management (Motor)."""
from __future__ import annotations

import logging

from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase
from pymongo import ASCENDING, DESCENDING

from app.core.config import settings

logger = logging.getLogger(__name__)


class _Database:
    client: AsyncIOMotorClient | None = None
    db: AsyncIOMotorDatabase | None = None


mongo = _Database()


def get_database() -> AsyncIOMotorDatabase:
    """Return the active database. Raises if not connected."""
    if mongo.db is None:
        raise RuntimeError("Database is not initialised. Call connect_to_mongo first.")
    return mongo.db


async def connect_to_mongo() -> None:
    mongo.client = AsyncIOMotorClient(settings.mongo_uri, uuidRepresentation="standard")
    mongo.db = mongo.client[settings.mongo_db_name]
    logger.info("Connected to MongoDB at %s / %s", settings.mongo_uri, settings.mongo_db_name)


async def close_mongo_connection() -> None:
    if mongo.client is not None:
        mongo.client.close()
        logger.info("Closed MongoDB connection")


async def ensure_indexes() -> None:
    """Create all intentional indexes. Safe to call repeatedly (idempotent)."""
    db = get_database()

    await db.users.create_index([("username", ASCENDING)], unique=True)
    await db.users.create_index([("parent_id", ASCENDING)])
    await db.users.create_index([("role", ASCENDING)])
    await db.users.create_index([("hierarchy_path", ASCENDING)])
    await db.users.create_index([("status", ASCENDING)])

    await db.transactions.create_index([("transaction_id", ASCENDING)], unique=True)
    await db.transactions.create_index(
        [("idempotency_key", ASCENDING)],
        unique=True,
        partialFilterExpression={"idempotency_key": {"$type": "string"}},
    )
    await db.transactions.create_index([("from_user_id", ASCENDING)])
    await db.transactions.create_index([("to_user_id", ASCENDING)])
    await db.transactions.create_index([("created_at", DESCENDING)])

    # one wallet movement per provider transaction, however often it is retried
    await db.casino_rounds.create_index(
        [("txn_id", ASCENDING)], unique=True, partialFilterExpression={"txn_id": {"$type": "string"}}
    )
    await db.casino_rounds.create_index([("user_id", ASCENDING), ("created_at", DESCENDING)])
    await db.casino_sessions.create_index([("user_id", ASCENDING)])
    await db.casino_bets.create_index([("user_id", ASCENDING), ("placed_at", DESCENDING)])
    await db.casino_bets.create_index([("status", ASCENDING), ("code", ASCENDING)])

    await db.games.create_index([("slug", ASCENDING)], unique=True)
    await db.games.create_index([("category", ASCENDING)])
    await db.games.create_index([("status", ASCENDING)])
    await db.games.create_index([("featured", ASCENDING)])
    await db.games.create_index([("sort_order", ASCENDING)])

    await db.game_categories.create_index([("key", ASCENDING)], unique=True)
    await db.sports.create_index([("key", ASCENDING)], unique=True)
    await db.providers.create_index([("key", ASCENDING)], unique=True)

    await db.events.create_index([("sport_id", ASCENDING)])
    await db.events.create_index([("status", ASCENDING)])
    await db.events.create_index([("start_time", ASCENDING)])

    await db.notifications.create_index([("user_id", ASCENDING)])
    await db.notifications.create_index([("created_at", DESCENDING)])

    await db.sessions.create_index([("token_id", ASCENDING)], unique=True)
    await db.sessions.create_index([("user_id", ASCENDING)])

    await db.audit_logs.create_index([("actor_id", ASCENDING)])
    await db.audit_logs.create_index([("action", ASCENDING)])
    await db.audit_logs.create_index([("created_at", DESCENDING)])

    await db.credit_requests.create_index([("user_id", ASCENDING)])
    await db.credit_requests.create_index([("parent_id", ASCENDING)])
    await db.credit_requests.create_index([("status", ASCENDING)])
    await db.credit_requests.create_index([("created_at", DESCENDING)])

    await db.bets.create_index([("user_id", ASCENDING)])
    await db.bets.create_index([("event_id", ASCENDING)])
    await db.bets.create_index([("status", ASCENDING)])
    await db.bets.create_index([("placed_at", DESCENDING)])

    logger.info("MongoDB indexes ensured")
