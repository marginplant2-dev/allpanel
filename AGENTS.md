# AGENTS.md — SportX project guide

Modular-monolith virtual sports & games platform. **Virtual/demo credits only** — no
real-money features. No Docker. Three apps: `backend/` (FastAPI + MongoDB),
`frontend-user/`, `frontend-admin/` (React + TS + Vite + Tailwind + shadcn/ui).

## Prerequisites
- Python 3.12+, Node 20+ (repo built with Node 24), MongoDB running locally at
  `mongodb://localhost:27017`.

## Backend (`backend/`)
```powershell
python -m venv .venv; .\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
Copy-Item .env.example .env
python -m scripts.seed_data       # bootstrap MOTHER_ADMIN (superadmin / ChangeMe123!) + role migration
python -m scripts.seed_content    # demo games/sports/events
uvicorn app.main:app --reload --port 8000
pytest                            # run tests (mongomock, no DB needed)
```
- Docs/Swagger: http://localhost:8000/docs · Health: `/health` · Meta: `/api/v1/meta`
- Module layout: `app/modules/<name>/{router,service,repository,schema,models}.py`
- Response envelope: success `{success,data,message}`, error `{success:false,error:{code,message}}`
- Never expose `password_hash` (use `public_user`); all RBAC/hierarchy checks are server-side.

## Frontends
```powershell
# frontend-user (port 5173) and frontend-admin (port 5174)
npm install
npm run dev         # dev server (proxies /api and /ws to :8000)
npm run build       # tsc -b && vite build  (use this to typecheck + verify)
npm run typecheck
```
- API base URL via `VITE_API_BASE_URL` (falls back to `/api/v1` + Vite proxy in dev).
- WebSocket base via `VITE_WS_BASE_URL` (falls back to same-origin `/ws` proxy in dev).

## Verification checklist
- Backend: `pytest` (all green) and app imports.
- Frontends: `npm run build` in each app (type-checks + bundles).

## Conventions
- TypeScript strict; avoid `any`. Reusable components in `components/`, pages in `features/`.
- Centralized API clients in `src/api/`; TanStack Query for server state; Zustand for auth/UI.
- Backend: async endpoints, Motor for Mongo, Pydantic v2 schemas, idempotent ledger transfers.

## Seeded login
- Admin console (5174): `superadmin` / `ChangeMe123!` (change after first login).
- Hierarchy: `MOTHER_ADMIN → SUPER_ADMIN → ADMIN → MASTER → AGENT → USER`. Each level
  creates its own players plus the next level down; coins move one step at a time; a
  panel lists direct children only (see `docs/rbac.md`).
