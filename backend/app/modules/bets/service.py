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

from datetime import datetime, timezone
from typing import Any

from motor.motor_asyncio import AsyncIOMotorDatabase

from app.core.dependencies import CurrentUser
from app.core.enums import BetStatus, Role
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

MARKET = "h2h"


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

        start_time = _as_datetime(event.get("start_time"))
        if start_time is not None and start_time <= utcnow():
            raise ValidationError("Betting is closed for this event")

        bookmaker = next(
            (b for b in event.get("bookmakers", []) if b.get("key") == payload.bookmaker_key), None
        )
        if bookmaker is None:
            raise ValidationError("Selected bookmaker odds are no longer available")
        market = next((m for m in bookmaker.get("markets", []) if m.get("key") == MARKET), None)
        if market is None:
            raise ValidationError("Selected market is no longer available")
        outcome = next(
            (o for o in market.get("outcomes", []) if o.get("name") == payload.outcome_name), None
        )
        if outcome is None:
            raise ValidationError("Selected odds are no longer available")

        try:
            price = float(outcome["price"])
        except (TypeError, ValueError, KeyError):
            raise ValidationError("Invalid odds")
        if price <= 1:
            raise ValidationError("Invalid odds")

        stake = float(payload.stake)
        potential_payout = round(stake * price, 2)

        locked = await self.wallets.try_lock(user.id, stake)
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
            "price": price,
            "stake": stake,
            "potential_payout": potential_payout,
            "status": BetStatus.PENDING.value,
            "placed_at": now,
            "settled_at": None,
            "payout": None,
        }
        try:
            await self.repo.insert(doc)
        except Exception:
            await self.wallets.unlock(user.id, stake)
            raise

        await record_audit(
            self.db,
            actor_id=user.id,
            action=AuditAction.BET_PLACED,
            target_id=str(doc["_id"]),
            metadata={"event_id": payload.event_id, "stake": stake, "price": price},
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
                continue
            bets = await self.repo.pending_for_event(event_id)
            if not bets:
                continue
            winner = _determine_winner(bets[0], live.get("score") or {})
            if winner is None:
                continue

            for bet in bets:
                won = bet["outcome_name"] == winner
                payout = bet["potential_payout"] if won else 0.0
                claimed = await self.repo.claim_settlement(
                    bet["_id"],
                    status=BetStatus.WON.value if won else BetStatus.LOST.value,
                    payout=payout,
                    settled_at=utcnow(),
                )
                if claimed is None:
                    continue
                if won:
                    await self.wallets.settle_win(bet["user_id"], stake=bet["stake"], payout=payout)
                else:
                    await self.wallets.settle_loss(bet["user_id"], stake=bet["stake"])
                await self._notify_settlement(bet, won)
                settled += 1
        return settled

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
