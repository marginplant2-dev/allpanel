"""Live casino rounds: take a bet on a table, settle it from the round result.

Unlike the sports book there is no lay side and no exposure — a casino bet is a
flat stake on one selection of one round, settled the moment the feed publishes
that round's winner.
"""
from __future__ import annotations

import logging
from typing import Any

from motor.motor_asyncio import AsyncIOMotorDatabase
from pymongo.errors import DuplicateKeyError

from app.core.dependencies import CurrentUser
from app.core.enums import BetStatus
from app.modules.ledger.service import InsufficientFundsError
from app.modules.providers.proexch_casino import CASINO_GAMES, fetch_results, fetch_table
from app.modules.wallet.repository import WalletRepository
from app.core.exceptions import NotFoundError, ValidationError
from app.utils.ids import to_object_id
from app.utils.time import utcnow

logger = logging.getLogger(__name__)

#: A round's result can take a few polls to appear; give up long after that and
#: refund rather than sit on the stake.
ROUNDS_BEFORE_VOID = 40


class CasinoLiveService:
    def __init__(self, db: AsyncIOMotorDatabase):
        self.db = db
        self.wallets = WalletRepository(db)

    # ---- reads ----
    def games(self) -> list[dict[str, Any]]:
        return [
            {"code": code, "name": name, "category": category}
            for code, (name, category) in CASINO_GAMES.items()
        ]

    async def table(self, code: str) -> dict[str, Any]:
        if code not in CASINO_GAMES:
            raise NotFoundError("Unknown casino game")
        table = await fetch_table(code)
        table["results"] = await fetch_results(code)
        return table

    async def my_bets(
        self, user_id: str, *, code: str | None = None, skip: int = 0, limit: int = 20
    ) -> tuple[list[dict[str, Any]], int]:
        query: dict[str, Any] = {"user_id": user_id}
        if code:
            query["code"] = code
        total = await self.db.casino_bets.count_documents(query)
        cursor = self.db.casino_bets.find(query).sort("placed_at", -1).skip(skip).limit(limit)
        rows = await cursor.to_list(length=limit)
        for row in rows:
            row["id"] = str(row.pop("_id"))
        return rows, total

    # ---- writes ----
    async def place_bet(
        self, user: CurrentUser, *, code: str, round_id: str, sid: Any, stake: float
    ) -> dict[str, Any]:
        table = await self.table(code)
        if not table["live"]:
            raise ValidationError("This table is not running right now")
        if table["round_id"] != str(round_id):
            raise ValidationError("That round has closed — the next one is already up")
        if not table["betting_open"]:
            raise ValidationError("Betting for this round is closed")

        option = next((o for o in table["options"] if str(o["sid"]) == str(sid)), None)
        if option is None:
            raise ValidationError("Unknown selection")
        if not option["open"]:
            raise ValidationError(f"{option['name']} is {option['status'].lower()}")
        if stake < option["min_stake"]:
            raise ValidationError(f"Minimum stake is {option['min_stake']:.0f}")
        if option["max_stake"] and stake > option["max_stake"]:
            raise ValidationError(f"Maximum stake is {option['max_stake']:.0f}")

        # the price is read here, not sent by the client
        price = option["price"]
        doc = {
            "user_id": user.id,
            "code": code,
            "game_name": table["name"],
            "round_id": table["round_id"],
            "sid": str(sid),
            "selection": option["name"],
            "price": price,
            "stake": float(stake),
            "potential_payout": round(float(stake) * price, 2),
            "status": BetStatus.PENDING.value,
            "placed_at": utcnow(),
            "settled_at": None,
            "payout": None,
            "polls": 0,
        }
        try:
            result = await self.db.casino_bets.insert_one(doc)
        except DuplicateKeyError as exc:
            raise ValidationError("Duplicate bet") from exc

        if not await self.wallets.try_debit(user.id, float(stake)):
            await self.db.casino_bets.delete_one({"_id": result.inserted_id})
            raise InsufficientFundsError("Insufficient available balance")

        doc["id"] = str(result.inserted_id)
        doc.pop("_id", None)
        await self._publish_wallet(user.id)
        return doc

    # ---- settlement ----
    async def settle_pending(self) -> int:
        """Pay out every pending bet whose round has a published result."""
        codes = await self.db.casino_bets.distinct("code", {"status": BetStatus.PENDING.value})
        settled = 0
        for code in codes:
            results = {r["round_id"]: r["winners"] for r in await fetch_results(code)}
            if not results:
                continue
            cursor = self.db.casino_bets.find(
                {"code": code, "status": BetStatus.PENDING.value}
            )
            async for bet in cursor:
                winners = results.get(bet["round_id"])
                if winners is None:
                    settled += await self._void_if_stale(bet)
                    continue
                won = bet["sid"] in winners
                payout = bet["potential_payout"] if won else 0.0
                claimed = await self.db.casino_bets.find_one_and_update(
                    {"_id": bet["_id"], "status": BetStatus.PENDING.value},
                    {
                        "$set": {
                            "status": BetStatus.WON.value if won else BetStatus.LOST.value,
                            "payout": payout,
                            "settled_at": utcnow(),
                        }
                    },
                )
                if claimed is None:
                    continue  # another pass got there first
                if won:
                    await self.wallets.credit(bet["user_id"], payout)
                await self._publish_wallet(bet["user_id"])
                settled += 1
        return settled

    async def _void_if_stale(self, bet: dict[str, Any]) -> int:
        """Refund a bet whose round never showed up in the results."""
        polls = int(bet.get("polls") or 0) + 1
        if polls < ROUNDS_BEFORE_VOID:
            await self.db.casino_bets.update_one({"_id": bet["_id"]}, {"$set": {"polls": polls}})
            return 0
        claimed = await self.db.casino_bets.find_one_and_update(
            {"_id": bet["_id"], "status": BetStatus.PENDING.value},
            {
                "$set": {
                    "status": BetStatus.VOID.value,
                    "payout": bet["stake"],
                    "settled_at": utcnow(),
                }
            },
        )
        if claimed is None:
            return 0
        await self.wallets.credit(bet["user_id"], bet["stake"])
        await self._publish_wallet(bet["user_id"])
        logger.info("voided stale casino bet %s on %s", bet["_id"], bet["code"])
        return 1

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


def _oid(value: str):
    return to_object_id(value)
