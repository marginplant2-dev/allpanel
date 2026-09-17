"""Shared FastAPI dependencies: authentication context and RBAC guards."""
from __future__ import annotations

from typing import Annotated, Callable

import jwt
from fastapi import Depends, Request
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from app.core.database import get_database
from app.core.enums import Role
from app.core.exceptions import AuthenticationError, PermissionDeniedError

_bearer = HTTPBearer(auto_error=False)


class CurrentUser:
    """Lightweight authenticated principal loaded from the database."""

    def __init__(self, doc: dict):
        self.id: str = str(doc["_id"])
        self.username: str = doc["username"]
        self.role: Role = Role(doc["role"])
        self.parent_id: str | None = doc.get("parent_id")
        self.hierarchy_path: list[str] = doc.get("hierarchy_path", [])
        self.status: str = doc.get("status", "active")
        self.impersonator_id: str | None = None
        self.raw = doc

    def is_downline_of(self, actor: "CurrentUser") -> bool:
        return actor.role is Role.MOTHER_ADMIN or actor.id in self.hierarchy_path

    def can_manage(self, target: "CurrentUser") -> bool:
        if self.id == target.id:
            return True
        return target.is_downline_of(self)


async def get_current_user(
    request: Request,
    credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(_bearer)],
) -> CurrentUser:
    if credentials is None:
        raise AuthenticationError("Missing authentication credentials")
    try:
        payload = jwt.decode(
            credentials.credentials,
            _secret(),
            algorithms=[_algorithm()],
        )
    except jwt.PyJWTError as exc:  # noqa: BLE001
        raise AuthenticationError("Invalid or expired token") from exc

    if payload.get("type") != "access":
        raise AuthenticationError("Invalid token type")

    user_id = payload.get("sub")
    db = get_database()
    from bson import ObjectId  # local import to keep module import light

    try:
        doc = await db.users.find_one({"_id": ObjectId(user_id)})
    except Exception:  # noqa: BLE001
        doc = None
    if doc is None:
        raise AuthenticationError("User no longer exists")
    if doc.get("status") == "suspended":
        raise PermissionDeniedError("Account is suspended")

    user = CurrentUser(doc)
    user.impersonator_id = payload.get("impersonator_id")
    request.state.user = user
    return user


CurrentUserDep = Annotated[CurrentUser, Depends(get_current_user)]


def require_roles(*roles: Role) -> Callable[..., CurrentUser]:
    allowed = set(roles)

    async def _guard(user: CurrentUserDep) -> CurrentUser:
        if user.role not in allowed:
            raise PermissionDeniedError("Insufficient role for this action")
        return user

    return _guard


async def require_admin(user: CurrentUserDep) -> CurrentUser:
    if user.role is Role.USER:
        raise PermissionDeniedError("Admin access required")
    return user


AdminUserDep = Annotated[CurrentUser, Depends(require_admin)]


def _secret() -> str:
    from app.core.config import settings

    return settings.jwt_secret_key


def _algorithm() -> str:
    from app.core.config import settings

    return settings.jwt_algorithm
