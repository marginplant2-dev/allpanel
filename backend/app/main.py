"""FastAPI application factory and entrypoint."""
from __future__ import annotations

import asyncio
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api import api_router
from app.core.config import settings
from app.core.database import (
    close_mongo_connection,
    connect_to_mongo,
    ensure_indexes,
)
from app.middleware.context import RequestContextMiddleware
from app.middleware.errors import register_exception_handlers
from app.middleware.rate_limit import RateLimitMiddleware

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(_: FastAPI):
    await connect_to_mongo()
    try:
        await ensure_indexes()
    except Exception as exc:  # noqa: BLE001
        logger.warning("Could not ensure indexes (is MongoDB running?): %s", exc)

    # Start background workers.
    stop_event = asyncio.Event()
    from app.workers.settlement import run_bet_settlement, run_casino_settlement
    from app.workers.sync import run_live_ticker

    ticker_task = asyncio.create_task(run_live_ticker(stop_event))
    settlement_task = asyncio.create_task(run_bet_settlement(stop_event))
    casino_task = asyncio.create_task(run_casino_settlement(stop_event))

    yield

    stop_event.set()
    for task in (ticker_task, settlement_task, casino_task):
        task.cancel()
    for task in (ticker_task, settlement_task, casino_task):
        try:
            await task
        except asyncio.CancelledError:
            pass
    await close_mongo_connection()


def create_app() -> FastAPI:
    app = FastAPI(
        title=settings.app_name,
        version="0.1.0",
        debug=settings.debug,
        lifespan=lifespan,
        docs_url="/docs",
        redoc_url="/redoc",
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    if settings.rate_limit_enabled:
        app.add_middleware(
            RateLimitMiddleware,
            limit=settings.rate_limit_requests,
            window_seconds=settings.rate_limit_window_seconds,
            path_prefix=settings.api_v1_prefix,
        )
    # Outermost so request.state.client_ip is available to the limiter and routes.
    app.add_middleware(RequestContextMiddleware)

    register_exception_handlers(app)

    @app.get("/health", tags=["meta"])
    async def health() -> dict:
        return {"success": True, "data": {"status": "ok"}, "message": ""}

    app.include_router(api_router, prefix=settings.api_v1_prefix)

    # WebSocket routes (registered if present)
    try:
        from app.websocket.routes import register_ws_routes

        register_ws_routes(app)
    except ImportError:
        pass

    return app


app = create_app()
