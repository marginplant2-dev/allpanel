"""Aggregate versioned API router. Module routers are registered here as they are built."""
from __future__ import annotations

from fastapi import APIRouter

api_router = APIRouter()


@api_router.get("/meta", tags=["meta"])
async def meta() -> dict:
    from app.core.config import settings
    from app.modules.providers.provider_factory import sports_data_source

    return {
        "success": True,
        "data": {
            "app": settings.app_name,
            "environment": settings.environment,
            "version": "0.1.0",
            "sports_provider": settings.sports_provider,
            "sports_data_source": sports_data_source(),
        },
        "message": "",
    }


# --- Module routers (registered incrementally across phases) ---
# Phase 2+
try:
    from app.modules.auth.router import router as auth_router

    api_router.include_router(auth_router)
except ImportError:
    pass

try:
    from app.modules.users.router import router as users_router

    api_router.include_router(users_router)
except ImportError:
    pass

try:
    from app.modules.hierarchy.router import router as hierarchy_router

    api_router.include_router(hierarchy_router)
except ImportError:
    pass

try:
    from app.modules.audit.router import router as audit_router

    api_router.include_router(audit_router)
except ImportError:
    pass

try:
    from app.modules.wallet.router import router as wallet_router

    api_router.include_router(wallet_router)
except ImportError:
    pass

try:
    from app.modules.ledger.router import router as ledger_router

    api_router.include_router(ledger_router)
except ImportError:
    pass

try:
    from app.modules.games.router import router as games_router

    api_router.include_router(games_router)
except ImportError:
    pass

try:
    from app.modules.sports.router import router as sports_router

    api_router.include_router(sports_router)
except ImportError:
    pass

try:
    from app.modules.reports.router import router as reports_router

    api_router.include_router(reports_router)
except ImportError:
    pass

try:
    from app.modules.notifications.router import router as notifications_router

    api_router.include_router(notifications_router)
except ImportError:
    pass

try:
    from app.modules.impersonation.router import router as impersonation_router

    api_router.include_router(impersonation_router)
except ImportError:
    pass

try:
    from app.modules.settings.router import router as settings_router

    api_router.include_router(settings_router)
except ImportError:
    pass

try:
    from app.modules.credit_requests.router import router as credit_requests_router

    api_router.include_router(credit_requests_router)
except ImportError:
    pass

try:
    from app.modules.bets.router import router as bets_router

    api_router.include_router(bets_router)
except ImportError:
    pass

try:
    from app.modules.casino.router import router as casino_router

    api_router.include_router(casino_router)
except ImportError:
    pass
