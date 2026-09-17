"""ObjectId helpers and document serialization."""
from __future__ import annotations

from typing import Any

from bson import ObjectId
from bson.errors import InvalidId

from app.core.exceptions import ValidationError


def to_object_id(value: str) -> ObjectId:
    try:
        return ObjectId(value)
    except (InvalidId, TypeError) as exc:
        raise ValidationError(f"Invalid id: {value}") from exc


def is_object_id(value: str) -> bool:
    return ObjectId.is_valid(value)


def serialize(doc: dict[str, Any] | None) -> dict[str, Any] | None:
    """Convert a Mongo document into a JSON-friendly dict.

    `_id` becomes `id` (string); nested ObjectIds are stringified.
    """
    if doc is None:
        return None
    out: dict[str, Any] = {}
    for key, value in doc.items():
        if key == "_id":
            out["id"] = str(value)
        elif isinstance(value, ObjectId):
            out[key] = str(value)
        else:
            out[key] = value
    return out


def serialize_many(docs: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [serialize(d) for d in docs]  # type: ignore[misc]
