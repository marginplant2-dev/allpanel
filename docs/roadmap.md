# Implementation Roadmap

The project is delivered phase by phase; each phase stays runnable.

## Phase 1 — Foundation
Root structure, `.gitignore`, README, docs. Backend app factory, config, MongoDB
connection + index creation, health endpoint. Scaffold both frontends (Vite + React +
TS + Tailwind + shadcn/ui, routing, API client, env). Verify all three boot.

## Phase 2 — Auth & Hierarchy
Password hashing, JWT access/refresh, session tracking, RBAC dependencies, user CRUD
with hierarchy scoping, downline tree, Create User flow, audit logging, seed super admin.

## Phase 3 — Wallet & Ledger
Wallet model, ledger transactions, idempotent concurrency-safe transfer engine, history
+ filters, admin ledger view.

## Phase 4 — User Frontend
Layout, Home sections, Sports/Events/Event Detail, Casino/Categories/Game Detail,
Wallet + history + activity, Profile/Security/Notifications/Help — API-driven.

## Phase 5 — Admin Frontend
Dashboard + charts, user management, hierarchy management, game/sports/category/provider
management, reports, impersonation, system + security screens.

## Phase 6 — Realtime
WebSocket manager + channels, notifications, wallet-update push, mock live-event ticker.

## Phase 7 — Hardening
Index review, cursor pagination, code splitting/lazy routes, caching-ready patterns,
rate-limit-ready middleware, CORS, security review, docs finalization.
