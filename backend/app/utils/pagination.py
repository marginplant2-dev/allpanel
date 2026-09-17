"""Pagination helpers for list endpoints."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Annotated, Any

from fastapi import Query


@dataclass
class PageParams:
    page: int
    page_size: int

    @property
    def skip(self) -> int:
        return (self.page - 1) * self.page_size

    @property
    def limit(self) -> int:
        return self.page_size


def pagination_params(
    page: Annotated[int, Query(ge=1)] = 1,
    page_size: Annotated[int, Query(ge=1, le=100)] = 20,
) -> PageParams:
    return PageParams(page=page, page_size=page_size)


def build_page(items: list[Any], total: int, params: PageParams) -> dict[str, Any]:
    pages = (total + params.page_size - 1) // params.page_size if params.page_size else 0
    return {
        "items": items,
        "meta": {
            "total": total,
            "page": params.page,
            "page_size": params.page_size,
            "pages": pages,
        },
    }
