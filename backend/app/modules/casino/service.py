"""Gamblly casino integration (V1 seamless wallet).

The player's balance stays here: the provider calls our callback for every bet
and win, we apply it to the wallet and answer with the new balance. That matches
this platform's ledger model — no funds are parked with the provider.

Contract (Gamblly V1):
  launch   POST {base}/v1/gameLaunch.php  form-encoded, returns {success, game_url}
  callback POST <our callback_url>        JSON  {player_uid, bet_amount, win_amount,
           action, game_uid, game_name, txn_id, game_round, currency_code, api_key}
           -> we answer {"balance": <number>, "status": true}

Every callback is keyed by `txn_id`: the provider retries, and a replay must not
move money twice.
"""
from __future__ import annotations

import logging
from typing import Any

import httpx
from motor.motor_asyncio import AsyncIOMotorDatabase
from pymongo.errors import DuplicateKeyError

from app.core.config import settings
from app.core.dependencies import CurrentUser
from app.core.exceptions import AppError, NotFoundError, ValidationError
from app.modules.wallet.repository import WalletRepository
from app.utils.ids import to_object_id
from app.utils.time import utcnow

logger = logging.getLogger(__name__)

#: Informational notice from the provider — not a wallet movement.
NOTICE_ACTIONS = {"deposit_required"}


class ProviderUnavailableError(AppError):
    status_code = 503
    code = "PROVIDER_UNAVAILABLE"


def _amount(value: Any) -> float:
    try:
        out = float(value)
    except (TypeError, ValueError):
        return 0.0
    return out if out > 0 else 0.0


class CasinoService:
    def __init__(self, db: AsyncIOMotorDatabase):
        self.db = db
        self.wallets = WalletRepository(db)

    # ---- launch ----
    async def launch(self, user: CurrentUser, game_slug: str) -> dict[str, Any]:
        if not settings.gamblly_api_key:
            raise ProviderUnavailableError(
                "Casino provider is not configured yet — add GAMBLLY_API_KEY to enable real games"
            )

        game = await self.db.games.find_one({"slug": game_slug, "status": "active"})
        if game is None:
            raise NotFoundError("Game not found")
        game_uid = game.get("game_uid")
        if not game_uid:
            raise ValidationError("This game has no provider id yet")

        wallet = await self.wallets.ensure(user.id)
        payload = {
            "api_key": settings.gamblly_api_key,
            "member_account": user.id,
            "game_uid": game_uid,
            "credit_amount": f"{wallet.get('available_balance', 0.0):.2f}",
            "currency_code": settings.gamblly_currency,
            "language": settings.gamblly_language,
            "platform": settings.gamblly_platform,
            "home_url": settings.gamblly_home_url,
        }
        try:
            async with httpx.AsyncClient(timeout=20.0) as client:
                r = await client.post(
                    f"{settings.gamblly_base_url.rstrip('/')}/v1/gameLaunch.php", data=payload
                )
                r.raise_for_status()
                body = r.json()
        except Exception as exc:  # noqa: BLE001 — upstream outage is not our 500
            logger.warning("gamblly launch failed for %s: %s", game_slug, exc)
            raise ProviderUnavailableError("Could not reach the game provider") from exc

        if not body.get("success") or not body.get("game_url"):
            raise ProviderUnavailableError(body.get("msg") or "Game could not be started")

        await self.db.casino_sessions.insert_one(
            {
                "user_id": user.id,
                "game_uid": game_uid,
                "game_slug": game_slug,
                "transfer_id": body.get("transfer_id"),
                "created_at": utcnow(),
            }
        )
        return {"game_url": body["game_url"], "transfer_id": body.get("transfer_id")}

    # ---- seamless callback ----
    async def handle_callback(self, data: dict[str, Any]) -> dict[str, Any]:
        """Apply one wallet event and answer with the resulting balance.

        Errors are deliberate here: an unknown player or a bad key must not be
        answered with a balance, or the provider will let the round run.
        """
        if str(data.get("api_key") or "") != settings.gamblly_api_key:
            raise ValidationError("Unauthorized callback")

        player_uid = str(data.get("player_uid") or "")
        if not player_uid:
            raise ValidationError("player_uid is required")

        try:
            user = await self.db.users.find_one({"_id": to_object_id(player_uid)})
        except Exception:  # noqa: BLE001 — a malformed id is simply not a player
            user = None
        if user is None:
            raise NotFoundError("Player not found")

        action = str(data.get("action") or "").lower()
        wallet = await self.wallets.ensure(player_uid)
        if action in NOTICE_ACTIONS:
            return {"balance": round(wallet.get("available_balance", 0.0), 2), "status": True}

        bet = _amount(data.get("bet_amount"))
        win = _amount(data.get("win_amount"))
        txn_id = str(data.get("txn_id") or "")

        if bet or win:
            applied = await self._record_round(player_uid, txn_id, data, bet, win)
            if applied:
                if bet and not await self.wallets.try_debit(player_uid, bet):
                    await self.db.casino_rounds.update_one(
                        {"txn_id": txn_id}, {"$set": {"status": "REJECTED", "reason": "insufficient"}}
                    )
                    raise ValidationError("Insufficient balance")
                if win:
                    await self.wallets.credit(player_uid, win)

        wallet = await self.wallets.ensure(player_uid)
        return {"balance": round(wallet.get("available_balance", 0.0), 2), "status": True}

    async def _record_round(
        self, user_id: str, txn_id: str, data: dict[str, Any], bet: float, win: float
    ) -> bool:
        """Write the round first; a duplicate txn_id means this is a replay.

        Returns True when the caller should move money, False for a replay.
        """
        doc = {
            "txn_id": txn_id or None,
            "user_id": user_id,
            "game_uid": data.get("game_uid"),
            "game_name": data.get("game_name"),
            "game_round": data.get("game_round"),
            "action": data.get("action"),
            "bet": bet,
            "win": win,
            "currency": data.get("currency_code"),
            "status": "APPLIED",
            "raw": data,
            "created_at": utcnow(),
        }
        if not txn_id:
            # No id to dedupe on: apply it, but say so in the record.
            doc["status"] = "APPLIED_NO_TXN_ID"
            await self.db.casino_rounds.insert_one(doc)
            return True
        if await self.db.casino_rounds.find_one({"txn_id": txn_id}, {"_id": 1}) is not None:
            logger.info("gamblly callback replay ignored: %s", txn_id)
            return False
        try:
            await self.db.casino_rounds.insert_one(doc)
        except DuplicateKeyError:
            # two retries landed together; the unique index settled it
            logger.info("gamblly callback replay ignored (race): %s", txn_id)
            return False
        return True

    async def history(self, user_id: str, *, skip: int, limit: int) -> tuple[list[dict[str, Any]], int]:
        query = {"user_id": user_id}
        total = await self.db.casino_rounds.count_documents(query)
        cursor = self.db.casino_rounds.find(query, {"raw": 0}).sort("created_at", -1).skip(skip).limit(limit)
        rows = await cursor.to_list(length=limit)
        for row in rows:
            row["id"] = str(row.pop("_id"))
        return rows, total
