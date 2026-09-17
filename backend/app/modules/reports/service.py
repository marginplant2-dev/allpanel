"""Reporting service: hierarchy-scoped aggregations for the admin dashboard."""
from __future__ import annotations

from datetime import timedelta
from typing import Any

from motor.motor_asyncio import AsyncIOMotorDatabase

from app.core.dependencies import CurrentUser
from app.core.enums import Role
from app.utils.time import utcnow


class ReportService:
    def __init__(self, db: AsyncIOMotorDatabase):
        self.db = db

    async def _scoped_user_ids(self, actor: CurrentUser) -> list[str]:
        """Ids that count towards this account's own dashboard.

        Same rule as the user list: the actor plus its direct children (and, for a
        master, its agents' players). Deeper accounts belong to someone else's
        panel — you see them by logging in as that account, not from up here.
        """
        from app.modules.users.repository import UserRepository

        scope = await UserRepository(self.db).visible_query(actor.role.value, actor.id)
        cursor = self.db.users.find(scope, {"_id": 1})
        ids = [str(d["_id"]) async for d in cursor]
        ids.append(actor.id)
        return ids

    async def dashboard(self, actor: CurrentUser) -> dict[str, Any]:
        ids = await self._scoped_user_ids(actor)
        user_filter: dict[str, Any] = {"_id": {"$in": _oids(ids)}}
        scoped_ids = ids

        now = utcnow()
        start_today = now.replace(hour=0, minute=0, second=0, microsecond=0)

        total_users = await self.db.users.count_documents(user_filter)
        active_users = await self.db.users.count_documents({**user_filter, "status": "active"})
        new_today = await self.db.users.count_documents({**user_filter, "created_at": {"$gte": start_today}})
        active_agents = await self.db.users.count_documents({**user_filter, "role": Role.AGENT.value, "status": "active"})

        # Credits
        credit_match: dict[str, Any] = {
            "status": "COMPLETED",
            "$or": [
                {"from_user_id": {"$in": scoped_ids}},
                {"to_user_id": {"$in": scoped_ids}},
            ],
        }
        transferred_today_match = {**credit_match, "created_at": {"$gte": start_today}}
        transferred_today = await self._sum_amount(transferred_today_match)

        total_credits = await self._sum_balances(scoped_ids)

        team_pipeline = [
            {"$match": {"parent_id": actor.id}},
            {"$group": {"_id": "$role", "count": {"$sum": 1}}},
        ]
        team = {r["_id"]: r["count"] async for r in self.db.users.aggregate(team_pipeline)}

        active_events = await self.db.events.count_documents({"status": "live"})
        active_games = await self.db.games.count_documents({"status": "active"})

        return {
            "total_users": total_users,
            "active_users": active_users,
            "new_users_today": new_today,
            "active_agents": active_agents,
            "total_virtual_credits": total_credits,
            "credits_transferred_today": transferred_today,
            "team_by_role": team,
            "active_events": active_events,
            "active_games": active_games,
        }

    async def user_growth(self, actor: CurrentUser, days: int = 14) -> list[dict[str, Any]]:
        ids = await self._scoped_user_ids(actor)
        now = utcnow()
        start = (now - timedelta(days=days - 1)).replace(hour=0, minute=0, second=0, microsecond=0)
        match: dict[str, Any] = {"created_at": {"$gte": start}, "_id": {"$in": _oids(ids)}}
        pipeline = [
            {"$match": match},
            {"$group": {"_id": {"$dateToString": {"format": "%Y-%m-%d", "date": "$created_at"}}, "count": {"$sum": 1}}},
            {"$sort": {"_id": 1}},
        ]
        rows = {r["_id"]: r["count"] async for r in self.db.users.aggregate(pipeline)}
        out = []
        for i in range(days):
            day = (start + timedelta(days=i)).strftime("%Y-%m-%d")
            out.append({"date": day, "users": rows.get(day, 0)})
        return out

    async def credit_movement(self, actor: CurrentUser, days: int = 14) -> list[dict[str, Any]]:
        ids = await self._scoped_user_ids(actor)
        now = utcnow()
        start = (now - timedelta(days=days - 1)).replace(hour=0, minute=0, second=0, microsecond=0)
        match: dict[str, Any] = {
            "status": "COMPLETED",
            "created_at": {"$gte": start},
            "$or": [{"from_user_id": {"$in": ids}}, {"to_user_id": {"$in": ids}}],
        }
        pipeline = [
            {"$match": match},
            {"$group": {"_id": {"$dateToString": {"format": "%Y-%m-%d", "date": "$created_at"}}, "amount": {"$sum": "$amount"}}},
            {"$sort": {"_id": 1}},
        ]
        rows = {r["_id"]: r["amount"] async for r in self.db.transactions.aggregate(pipeline)}
        out = []
        for i in range(days):
            day = (start + timedelta(days=i)).strftime("%Y-%m-%d")
            out.append({"date": day, "amount": rows.get(day, 0)})
        return out

    async def _sum_amount(self, match: dict[str, Any]) -> float:
        pipeline = [{"$match": match}, {"$group": {"_id": None, "total": {"$sum": "$amount"}}}]
        async for row in self.db.transactions.aggregate(pipeline):
            return float(row.get("total", 0))
        return 0.0

    async def _sum_balances(self, ids: list[str] | None) -> float:
        match: dict[str, Any] = {} if ids is None else {"_id": {"$in": ids}}
        pipeline = [{"$match": match}, {"$group": {"_id": None, "total": {"$sum": "$available_balance"}}}]
        async for row in self.db.wallets.aggregate(pipeline):
            return float(row.get("total", 0))
        return 0.0


def _oids(ids: list[str]):
    from app.utils.ids import to_object_id

    return [to_object_id(i) for i in ids]
