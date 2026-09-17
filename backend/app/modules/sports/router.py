"""Sports & events endpoints. Public reads + admin management."""
from __future__ import annotations

from fastapi import APIRouter, Query

from app.core.database import get_database
from app.core.dependencies import AdminUserDep
from app.core.responses import ok
from app.modules.sports.schema import EventCreate, EventUpdate, SportCreate
from app.modules.sports.service import SportsService

router = APIRouter(tags=["sports"])


# --- Public ---
@router.get("/sports")
async def list_sports():
    service = SportsService(get_database())
    return ok(await service.sports())


@router.get("/events")
async def list_events(
    sport_id: str | None = Query(default=None),
    status: str | None = Query(default=None, pattern="^(live|upcoming|finished)$"),
):
    service = SportsService(get_database())
    return ok(await service.events(sport_id=sport_id, status=status))


@router.get("/events/{event_id}")
async def event_detail(event_id: str):
    service = SportsService(get_database())
    return ok(await service.event_detail(event_id))


@router.get("/events/{event_id}/live")
async def event_live(event_id: str):
    service = SportsService(get_database())
    return ok(await service.live_data(event_id))


# --- Admin ---
@router.post("/sports", status_code=201)
async def create_sport(payload: SportCreate, actor: AdminUserDep):
    service = SportsService(get_database())
    return ok(await service.create_sport(payload), message="Sport created")


@router.post("/events", status_code=201)
async def create_event(payload: EventCreate, actor: AdminUserDep):
    service = SportsService(get_database())
    return ok(await service.create_event(payload), message="Event created")


@router.patch("/events/{event_id}")
async def update_event(event_id: str, payload: EventUpdate, actor: AdminUserDep):
    service = SportsService(get_database())
    return ok(await service.update_event(event_id, payload), message="Event updated")
