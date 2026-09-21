"""Bet settlement worker: periodically settles pending bets against provider results."""
from __future__ import annotations

import asyncio
import logging

from app.core.database import get_database
from app.modules.bets.service import BetService
from app.modules.casino.live_service import CasinoLiveService

logger = logging.getLogger(__name__)

# ponytail: 5 min, not seconds — each poll costs 2 usage credits per distinct pending
# event against the real odds API's quota (daysFrom=3 on /scores). Bet settlement isn't
# latency-sensitive; live score display already polls a free endpoint on its own.
_INTERVAL_SECONDS = 300

#: A casino round lasts about half a minute, so its bets settle on their own clock.
#: The results endpoint is cheap (no usage quota, unlike the sports scores feed).
_CASINO_INTERVAL_SECONDS = 15


async def run_bet_settlement(stop: asyncio.Event) -> None:
    logger.info("Bet settlement worker started")
    while not stop.is_set():
        try:
            await asyncio.sleep(_INTERVAL_SECONDS)
            settled = await BetService(get_database()).settle_pending()
            if settled:
                logger.info("Settled %d bet(s)", settled)
        except asyncio.CancelledError:
            break
        except Exception as exc:  # noqa: BLE001
            logger.warning("Bet settlement error: %s", exc)
    logger.info("Bet settlement worker stopped")


async def run_casino_settlement(stop: asyncio.Event) -> None:
    """Casino rounds finish every half minute; their bets cannot wait on the
    five-minute sports pass."""
    logger.info("Casino settlement worker started")
    while not stop.is_set():
        try:
            await asyncio.sleep(_CASINO_INTERVAL_SECONDS)
            settled = await CasinoLiveService(get_database()).settle_pending()
            if settled:
                logger.info("Settled %d casino bet(s)", settled)
        except asyncio.CancelledError:
            break
        except Exception as exc:  # noqa: BLE001
            logger.warning("Casino settlement error: %s", exc)
    logger.info("Casino settlement worker stopped")
