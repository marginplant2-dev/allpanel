"""Reporting endpoints (admin roles, hierarchy-scoped)."""
from __future__ import annotations

from fastapi import APIRouter, Query

from app.core.database import get_database
from app.core.dependencies import AdminUserDep
from app.core.responses import ok
from app.modules.reports.service import ReportService

router = APIRouter(prefix="/reports", tags=["reports"])


@router.get("/dashboard")
async def dashboard(actor: AdminUserDep):
    service = ReportService(get_database())
    return ok(await service.dashboard(actor))


@router.get("/user-growth")
async def user_growth(actor: AdminUserDep, days: int = Query(default=14, ge=1, le=90)):
    service = ReportService(get_database())
    return ok(await service.user_growth(actor, days))


@router.get("/credit-movement")
async def credit_movement(actor: AdminUserDep, days: int = Query(default=14, ge=1, le=90)):
    service = ReportService(get_database())
    return ok(await service.credit_movement(actor, days))
