"""Shared test fixtures. Uses mongomock-motor for an in-memory MongoDB."""
from __future__ import annotations

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from mongomock_motor import AsyncMongoMockClient

import app.core.database as database_module
from app.core.enums import Role, UserStatus
from app.core.security import hash_password
from app.main import app
from app.utils.time import utcnow


@pytest_asyncio.fixture
async def db():
    client = AsyncMongoMockClient()
    test_db = client["sportx_test"]
    database_module.mongo.client = client
    database_module.mongo.db = test_db
    yield test_db
    database_module.mongo.db = None
    database_module.mongo.client = None


@pytest_asyncio.fixture
async def client(db):
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test/api/v1") as c:
        yield c


async def make_user(
    db,
    username: str,
    role: Role,
    *,
    parent: dict | None = None,
    password: str = "secret123",
    status: UserStatus = UserStatus.ACTIVE,
) -> dict:
    now = utcnow()
    hierarchy_path = []
    parent_id = None
    if parent is not None:
        parent_id = str(parent["_id"])
        hierarchy_path = [*parent.get("hierarchy_path", []), parent_id]
    doc = {
        "username": username,
        "password_hash": hash_password(password),
        "full_name": username.title(),
        "role": role.value,
        "parent_id": parent_id,
        "hierarchy_path": hierarchy_path,
        "status": status.value,
        "credit_limit": 0.0,
        "notes": None,
        "two_factor_enabled": False,
        "created_at": now,
        "updated_at": now,
        "last_login": None,
    }
    result = await db.users.insert_one(doc)
    doc["_id"] = result.inserted_id
    return doc


async def login(client: AsyncClient, username: str, password: str = "secret123") -> str:
    res = await client.post("/auth/login", json={"username": username, "password": password})
    assert res.status_code == 200, res.text
    return res.json()["data"]["access_token"]


def auth_header(token: str) -> dict:
    return {"Authorization": f"Bearer {token}"}
