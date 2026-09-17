"""Shared enumerations used across modules."""
from __future__ import annotations

from enum import Enum


class Role(str, Enum):
    MOTHER_ADMIN = "MOTHER_ADMIN"
    SUPER_ADMIN = "SUPER_ADMIN"
    ADMIN = "ADMIN"
    MASTER = "MASTER"
    AGENT = "AGENT"
    USER = "USER"

    @property
    def level(self) -> int:
        """Lower number = higher authority."""
        return _ROLE_LEVELS[self]

    @property
    def child_role(self) -> "Role | None":
        """The one admin role this role may create directly below itself."""
        return _CHILD_ROLE.get(self)

    def can_create(self, other: "Role") -> bool:
        """Every level creates its own players, plus the next admin level down.

        Skipping a level is not allowed: an ADMIN cannot mint an AGENT directly,
        it has to go through a MASTER, so the coin chain and the dashboards line
        up with the real reporting line.
        """
        if other is Role.USER:
            return self is not Role.USER
        return self.child_role is other


_ROLE_LEVELS: dict[Role, int] = {
    Role.MOTHER_ADMIN: 0,
    Role.SUPER_ADMIN: 1,
    Role.ADMIN: 2,
    Role.MASTER: 3,
    Role.AGENT: 4,
    Role.USER: 5,
}

_CHILD_ROLE: dict[Role, Role] = {
    Role.MOTHER_ADMIN: Role.SUPER_ADMIN,
    Role.SUPER_ADMIN: Role.ADMIN,
    Role.ADMIN: Role.MASTER,
    Role.MASTER: Role.AGENT,
}

ADMIN_ROLES = {Role.MOTHER_ADMIN, Role.SUPER_ADMIN, Role.ADMIN, Role.MASTER, Role.AGENT}

#: Roles whose dashboard also shows the players of their direct children.
#: A master runs the agents' books, so their players roll up; nobody else's do.
SEES_GRANDCHILD_PLAYERS = {Role.MASTER}


class UserStatus(str, Enum):
    ACTIVE = "active"
    SUSPENDED = "suspended"
    INACTIVE = "inactive"


class TransactionType(str, Enum):
    CREDIT_TRANSFER = "CREDIT_TRANSFER"
    CREDIT_ALLOCATION = "CREDIT_ALLOCATION"
    ADJUSTMENT = "ADJUSTMENT"


class TransactionStatus(str, Enum):
    PENDING = "PENDING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
    REVERSED = "REVERSED"


class RequestType(str, Enum):
    DEPOSIT = "DEPOSIT"
    WITHDRAW = "WITHDRAW"


class RequestStatus(str, Enum):
    PENDING = "PENDING"
    PROCESSING = "PROCESSING"
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"


class BetStatus(str, Enum):
    PENDING = "PENDING"
    WON = "WON"
    LOST = "LOST"


class GameRoundStatus(str, Enum):
    WON = "WON"
    LOST = "LOST"
