"""Mock live-event worker.

Periodically nudges the scores of live events and broadcasts the change over the
`live_events` channel. In production this would be replaced by a real data feed
behind the same provider/event interface.
"""
from __future__ import annotations

import asyncio
import logging
import random

from app.core.database import get_database
from app.utils.time import utcnow
from app.websocket.events import publish_live_event
from app.websocket.manager import manager

logger = logging.getLogger(__name__)

_INTERVAL_SECONDS = 12


async def run_live_ticker(stop: asyncio.Event) -> None:
    logger.info("Live ticker worker started")
    while not stop.is_set():
        try:
            await asyncio.sleep(_INTERVAL_SECONDS)
            if manager.connection_count == 0:
                continue
            await _tick_once()
        except asyncio.CancelledError:
            break
        except Exception as exc:  # noqa: BLE001
            logger.warning("Live ticker error: %s", exc)
    logger.info("Live ticker worker stopped")


async def _tick_once() -> None:
    db = get_database()
    cursor = db.events.find({"status": "live"}).limit(20)
    async for event in cursor:
        score = dict(event.get("score") or {})
        participants = event.get("participants") or list(score.keys())
        if not participants:
            continue
        # Randomly advance one participant's score.
        who = random.choice(participants)
        score[who] = int(score.get(who, 0)) + random.choice([0, 0, 1, 1, 2])
        await db.events.update_one(
            {"_id": event["_id"]}, {"$set": {"score": score, "updated_at": utcnow()}}
        )
        await publish_live_event({"event_id": str(event["_id"]), "score": score, "status": "live"})
