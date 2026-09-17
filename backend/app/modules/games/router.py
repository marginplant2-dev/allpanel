"""Game catalogue endpoints. Public reads + admin management."""
from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, Query, Request

from app.core.database import get_database
from app.core.dependencies import AdminUserDep
from app.core.responses import ok
from app.modules.games.schema import CategoryCreate, GameCreate, GameImportRequest, GameUpdate
from app.modules.games.service import GameService
from app.utils.pagination import PageParams, build_page, pagination_params

router = APIRouter(prefix="/games", tags=["games"])


def _ip(request: Request) -> str | None:
    return getattr(request.state, "client_ip", None)


# --- Public reads (declared before /{slug} so the static paths win) ---
@router.get("/categories")
async def list_categories():
    service = GameService(get_database())
    return ok(await service.categories())


@router.get("")
async def list_games(
    category: str | None = Query(default=None),
    featured: bool | None = Query(default=None),
    search: str | None = Query(default=None),
):
    service = GameService(get_database())
    return ok(await service.catalogue(category=category, featured=featured, search=search))


@router.get("/{slug}")
async def game_detail(slug: str):
    service = GameService(get_database())
    return ok(await service.game_by_slug(slug))


# --- Admin management ---
@router.post("", status_code=201)
async def create_game(payload: GameCreate, request: Request, actor: AdminUserDep):
    service = GameService(get_database())
    return ok(await service.create_game(actor, payload, ip=_ip(request)), message="Game created")


@router.get("/admin/list")
async def list_games_admin(
    actor: AdminUserDep,
    params: Annotated[PageParams, Depends(pagination_params)],
    category: str | None = Query(default=None),
    status: str | None = Query(default=None),
    search: str | None = Query(default=None),
):
    service = GameService(get_database())
    query: dict = {}
    if category:
        query["category"] = category
    if status:
        query["status"] = status
    if search:
        query["name"] = {"$regex": search, "$options": "i"}
    docs, total = await service.list_admin(query=query, skip=params.skip, limit=params.limit)
    return ok(build_page(docs, total, params))


@router.post("/import")
async def import_games(payload: GameImportRequest, request: Request, actor: AdminUserDep):
    """Load a provider catalogue (names, artwork and game_uid) in one call."""
    service = GameService(get_database())
    return ok(await service.import_games(actor, payload, ip=_ip(request)), message="Catalogue imported")


@router.patch("/{game_id}")
async def update_game(game_id: str, payload: GameUpdate, request: Request, actor: AdminUserDep):
    service = GameService(get_database())
    return ok(await service.update_game(actor, game_id, payload, ip=_ip(request)), message="Game updated")


@router.delete("/{game_id}")
async def delete_game(game_id: str, request: Request, actor: AdminUserDep):
    service = GameService(get_database())
    await service.delete_game(actor, game_id, ip=_ip(request))
    return ok(message="Game deleted")


@router.post("/categories", status_code=201)
async def create_category(payload: CategoryCreate, actor: AdminUserDep):
    service = GameService(get_database())
    return ok(await service.create_category(payload), message="Category created")
