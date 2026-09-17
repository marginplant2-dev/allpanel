"""Consistent API response envelope helpers."""
from __future__ import annotations

from typing import Any, Generic, TypeVar

from pydantic import BaseModel

T = TypeVar("T")


class ErrorDetail(BaseModel):
    code: str
    message: str


class SuccessResponse(BaseModel, Generic[T]):
    success: bool = True
    data: T | None = None
    message: str = ""


class ErrorResponse(BaseModel):
    success: bool = False
    error: ErrorDetail


def ok(data: Any = None, message: str = "") -> dict[str, Any]:
    return {"success": True, "data": data, "message": message}


def err(code: str, message: str) -> dict[str, Any]:
    return {"success": False, "error": {"code": code, "message": message}}


class PageMeta(BaseModel):
    total: int
    page: int
    page_size: int
    pages: int


class Paginated(BaseModel, Generic[T]):
    items: list[T]
    meta: PageMeta
