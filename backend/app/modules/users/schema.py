"""Pydantic schemas for the users module."""
from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from app.core.enums import Role, UserStatus


class UserCreate(BaseModel):
    username: str = Field(min_length=3, max_length=32, pattern=r"^[a-zA-Z0-9_.-]+$")
    password: str = Field(min_length=6, max_length=128)
    full_name: str = Field(min_length=1, max_length=120)
    role: Role
    parent_id: str | None = None
    status: UserStatus = UserStatus.ACTIVE
    credit_limit: float = Field(default=0, ge=0)
    notes: str | None = Field(default=None, max_length=1000)


class UserUpdate(BaseModel):
    full_name: str | None = Field(default=None, min_length=1, max_length=120)
    password: str | None = Field(default=None, min_length=6, max_length=128)
    credit_limit: float | None = Field(default=None, ge=0)
    notes: str | None = Field(default=None, max_length=1000)
    status: UserStatus | None = None


class UserPublic(BaseModel):
    model_config = ConfigDict(extra="ignore")

    id: str
    username: str
    full_name: str
    role: Role
    parent_id: str | None = None
    hierarchy_path: list[str] = []
    status: str
    credit_limit: float = 0
    notes: str | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None
    last_login: datetime | None = None
