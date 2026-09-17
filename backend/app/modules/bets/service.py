"""Sports betting: place a bet at current provider odds, settle against provider results.

Design notes
------------
* Odds are read fresh from the sports provider at placement time and locked onto
  the bet document — the user cannot submit their own price.
* Stake is moved available -> locked via an atomic guarded update (same pattern as
  `WalletRepository.try_debit`), so concurrent bets can't overdraw a balance.
* Settlement is polled by a background worker (`app.workers.settlement`) calling
  `settle_pending()`; each bet is claimed with a status-guarded update so a bet is
  never paid out twice even if settlement runs concurrently.
"""
from __future__ import annotations

import logging
from datetime import datetime, timedelta, timezone
from typing import Any

from motor.motor_asyncio import AsyncIOMotorDatabase

from app.core.dependencies import CurrentUser
from app.core.enums import BetSide, BetStatus, Role
from app.core.exceptions import NotFoundError, ValidationError
from app.modules.audit.models import AuditAction
from app.modules.audit.service import record_audit
from app.modules.bets.repository import BetRepository
from app.modules.bets.schema import PlaceBetRequest
from app.modules.ledger.service import InsufficientFundsError
from app.modules.providers.provider_factory import get_sports_provider
from app.modules.wallet.repository import WalletRepository
from app.utils.ids import serialize, serialize_many
from app.utils.time import utcnow

logger = logging.getLogger(__name__)

MARKET = "h2h"

#: A market can close without the feed ever publishing a result (the event simply
#: disappears). Rather than sit on a player's stake forever, refund it once the
#: event is this old and no longer in the feed.
VOID_AFTER = timedelta(hours=6)


def _as_datetime(value: Any) -> datetime | None:
    if value is None:
        return None
    if isinstance(value, datetime):
        return value if value.tzinfo else value.replace(tzinfo=timezone.utc)
    return datetime.fromisoformat(str(value).replace("Z", "+00:00"))


def _determine_winner(bet: dict[str, Any], score: dict[str, Any]) -> str | None:
    home, away = bet.get("home_team"), bet.get("away_team")
    if home not in score or away not in score:
        return None
    try:
        home_score, away_score = float(score[home]), float(score[away])
    except (TypeError, ValueError):
        return None
    if home_score > away_score:
        return home
    if away_score > home_score:
        return away
    return "Draw"


class BetService:
    def __init__(self, db: AsyncIOMotorDatabase):
        self.db = db
        self.repo = BetRepository(db)
        self.wallets = WalletRepository(db)
        self.provider = get_sports_provider(db)

    async def place_bet(
        self, user: CurrentUser, payload: PlaceBetRequest, *, ip: str | None = None
    ) -> dict[str, Any]:
        event = await self.provider.get_event_detail(payload.event_id)
        if event is None:
            raise NotFoundError("Event not found")

        bookmaker = next(
            (b for b in event.get("bookmakers", []) if b.get("key") == payload.bookmaker_key), None
        )
        if bookmaker is None:
            raise ValidationError("Selected bookmaker odds are no longer available")
        if bookmaker.get("suspended"):
            raise ValidationError("This market is suspended")
        market = next((m for m in bookmaker.get("markets", []) if m.get("key") == MARKET), None)
        if market is None:
            raise ValidationError("Selected market is no longer available")
        outcome = next(
            (o for o in market.get("outcomes", []) if o.get("name") == payload.outcome_name), None
        )
        if outcome is None:
            raise ValidationError("Selected odds are no longer available")
        status = str(outcome.get("status") or "ACTIVE").upper()
        if status not in ("ACTIVE", "OPEN", ""):
            raise ValidationError(f"Selection is {outcome.get('status')}")

        side = BetSide(payload.side)
        price = _pick_price(outcome, side, payload.price)

        stake = float(payload.stake)
        if side is BetSide.BACK:
            # risk the stake, win stake x price back
            exposure = stake
            potential_payout = round(stake * price, 2)
        else:
            # lay: risk the liability, win the backer's stake (plus the liability back)
            exposure = round(stake * (price - 1), 2)
            if exposure <= 0:
                raise ValidationError("Invalid odds")
            potential_payout = round(exposure + stake, 2)

        locked = await self.wallets.try_lock(user.id, exposure)
        if not locked:
            raise InsufficientFundsError("Insufficient available balance")

        now = utcnow()
        doc: dict[str, Any] = {
            "user_id": user.id,
            "event_id": payload.event_id,
            "sport_id": event.get("sport_id"),
            "event_name": event.get("name") or f"{event.get('home_team')} vs {event.get('away_team')}",
            "home_team": event.get("home_team"),
            "away_team": event.get("away_team"),
            "start_time": event.get("start_time"),
            "bookmaker_key": bookmaker.get("key"),
            "bookmaker_title": bookmaker.get("title"),
            "market": MARKET,
            "outcome_name": payload.outcome_name,
            "side": side.value,
            "price": price,
            "stake": stake,
            #: what is actually held from the wallet (stake for a back, liability for a lay)
            "exposure": exposure,
            "potential_payout": potential_payout,
            "status": BetStatus.PENDING.value,
            "placed_at": now,
            "settled_at": None,
            "payout": None,
        }
        try:
            await self.repo.insert(doc)
        except Exception:
            await self.wallets.unlock(user.id, exposure)
            raise

        await record_audit(
            self.db,
            actor_id=user.id,
            action=AuditAction.BET_PLACED,
            target_id=str(doc["_id"]),
            metadata={
                "event_id": payload.event_id,
                "stake": stake,
                "price": price,
                "side": side.value,
            },
            ip_address=ip,
        )
        await self._publish_wallet(user.id)
        return serialize(doc)  # type: ignore[return-value]

    async def my_bets(
        self, user_id: str, *, status: str | None, skip: int, limit: int
    ) -> tuple[list[dict[str, Any]], int]:
        docs, total = await self.repo.list_for_user(user_id, status=status, skip=skip, limit=limit)
        return serialize_many(docs), total

    async def get_bet(self, user: CurrentUser, bet_id: str) -> dict[str, Any]:
        doc = await self.repo.get(bet_id)
        if doc is None:
            raise NotFoundError("Bet not found")
        if user.role is Role.USER and doc["user_id"] != user.id:
            raise NotFoundError("Bet not found")
        return serialize(doc)  # type: ignore[return-value]

    async def settle_pending(self) -> int:
        """Poll the provider for finished events and pay out / close matching bets.

        ponytail: h2h only, and an event that never reports `completed` scores stays
        PENDING forever (locked stake, no auto-void). Add a manual admin void action
        if postponed/cancelled events become common.
        """
        settled = 0
        for event_id in await self.repo.pending_event_ids():
            live = await self.provider.get_live_data(event_id)
            if live is None or live.get("status") != "finished":
                settled += await self._void_if_abandoned(event_id)
                continue
            bets = await self.repo.pending_for_event(event_id)
            if not bets:
                continue
            winner = _determine_winner(bets[0], live.get("score") or {})
            if winner is None:
                continue

            for bet in bets:
                runner_won = bet["outcome_name"] == winner
                # a lay bet is the other side of the same question
                won = runner_won if bet.get("side", BetSide.BACK.value) == BetSide.BACK.value else not runner_won
                payout = bet["potential_payout"] if won else 0.0
                claimed = await self.repo.claim_settlement(
                    bet["_id"],
                    status=BetStatus.WON.value if won else BetStatus.LOST.value,
                    payout=payout,
                    settled_at=utcnow(),
                )
                if claimed is None:
                    continue
                held = float(bet.get("exposure") or bet["stake"])
                if won:
                    await self.wallets.settle_win(bet["user_id"], stake=held, payout=payout)
                else:
                    await self.wallets.settle_loss(bet["user_id"], stake=held)
                await self._notify_settlement(bet, won)
                settled += 1
        return settled

    async def _void_if_abandoned(self, event_id: str) -> int:
        """Refund bets on an event the feed has dropped without a result."""
        bets = await self.repo.pending_for_event(event_id)
        if not bets:
            return 0
        start = _as_datetime(bets[0].get("start_time"))
        if start is None or utcnow() - start < VOID_AFTER:
            return 0
        if await self.provider.get_event_detail(event_id) is not None:
            return 0  # still listed: it just has not finished yet

        voided = 0
        for bet in bets:
            held = float(bet.get("exposure") or bet["stake"])
            claimed = await self.repo.claim_settlement(
                bet["_id"], status=BetStatus.VOID.value, payout=held, settled_at=utcnow()
            )
            if claimed is None:
                continue
            await self.wallets.unlock(bet["user_id"], held)
            await self._publish_wallet(bet["user_id"])
            voided += 1
        if voided:
            logger.info("voided %s abandoned bet(s) on %s", voided, event_id)
        return voided

    async def _publish_wallet(self, user_id: str) -> None:
        from app.websocket.events import publish_wallet_update

        wallet = await self.wallets.get(user_id)
        if wallet is not None:
            await publish_wallet_update(
                user_id,
                {
                    "user_id": user_id,
                    "available_balance": wallet.get("available_balance", 0.0),
                    "locked_balance": wallet.get("locked_balance", 0.0),
                },
            )

    async def _notify_settlement(self, bet: dict[str, Any], won: bool) -> None:
        from app.modules.notifications.service import NotificationService

        await self._publish_wallet(bet["user_id"])
        try:
            await NotificationService(self.db).create(
                bet["user_id"],
                type_="BET_SETTLED",
                title="Bet won!" if won else "Bet lost",
                body=(
                    f"Your bet on {bet['outcome_name']} ({bet['event_name']}) won "
                    f"{bet['potential_payout']:g} credits."
                    if won
                    else f"Your bet on {bet['outcome_name']} ({bet['event_name']}) did not win."
                ),
                metadata={"bet_id": str(bet["_id"]), "status": "WON" if won else "LOST"},
            )
        except Exception:  # noqa: BLE001
            pass


def _pick_price(outcome: dict[str, Any], side: BetSide, requested: float | None) -> float:
    """Resolve the price a bet is struck at.

    The board shows three rungs per side and every one of them is clickable, so a
    requested price is honoured only while it is still on the ladder — if the
    market has moved off it, the bet is refused rather than filled at a price the
    player did not choose.
    """
    key = "back_ladder" if side is BetSide.BACK else "lay_ladder"
    ladder = [
        float(level["price"])
        for level in (outcome.get(key) or [])
        if level.get("price") and float(level["price"]) > 1
    ]
    if not ladder:
        fallback = outcome.get("price") if side is BetSide.BACK else outcome.get("lay")
        try:
            value = float(fallback)
        except (TypeError, ValueError):
            value = 0.0
        ladder = [value] if value > 1 else []
    if not ladder:
        raise ValidationError("No price available on this side")

    if requested is None:
        return ladder[0]
    match = next((p for p in ladder if abs(p - requested) < 1e-9), None)
    if match is None:
        raise ValidationError("Odds have changed — please try again")
    return match
