# Deployment (no Docker)

> Sharing a server with another live site? Follow [`CO-HOSTING.md`](CO-HOSTING.md)
> instead — same steps, but isolated (own user, loopback port, own DB name, own nginx
> file, memory/CPU caps) so the existing site is untouched.

SportX is a modular monolith. For now it runs as three processes plus MongoDB:

1. **MongoDB** (Windows service or managed instance)
2. **Backend** — Uvicorn serving the FastAPI app
3. **Frontends** — static builds of `frontend-user` and `frontend-admin` served by a
   web server (nginx, IIS, or any static host)

There is intentionally **no Docker** and **no microservices** at this stage. The code
is structured so modules (and the realtime layer) can be extracted into separate
services later.

## 1. MongoDB

Install MongoDB Community Server and run it (default `mongodb://localhost:27017`).
See `backend/README.md` for Windows install notes.

## 2. Backend (production)

```powershell
cd backend
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
Copy-Item .env.example .env   # set JWT_SECRET_KEY, MONGO_URI, CORS_ORIGINS, etc.
python -m scripts.seed_data          # bootstrap super admin
python -m scripts.seed_content       # optional demo content

# Run with multiple workers behind a process manager
uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 4
```

> **Note on scaling:** the in-memory WebSocket manager and rate limiter are
> single-process. When running multiple workers/instances, move these to a shared
> backend (e.g. Redis pub/sub for realtime, Redis for rate limiting) before scaling
> out. The interfaces are isolated to make this swap localized.

## 3. Frontends (production build)

```powershell
cd frontend-user
npm ci
# Point the app at your public API/WS URLs
"VITE_API_BASE_URL=https://api.example.com/api/v1`nVITE_WS_BASE_URL=wss://api.example.com" | Set-Content .env
npm run build      # outputs dist/

cd ..\frontend-admin
npm ci
"VITE_API_BASE_URL=https://api.example.com/api/v1`nVITE_WS_BASE_URL=wss://api.example.com" | Set-Content .env
npm run build      # outputs dist/
```

Serve each `dist/` as a static SPA (fallback all routes to `index.html`).

## 4. Reverse proxy

See `nginx.conf.sample` for an example that serves both frontends and proxies
`/api` and `/ws` to the backend.

## Environment variables

| Variable | Purpose |
|----------|---------|
| `JWT_SECRET_KEY` | **Required in production** — strong random secret |
| `MONGO_URI`, `MONGO_DB_NAME` | Database connection |
| `CORS_ORIGINS` | Comma-separated allowed origins (the two frontends) |
| `ACCESS_TOKEN_EXPIRE_MINUTES`, `REFRESH_TOKEN_EXPIRE_DAYS` | Token lifetimes |
| `RATE_LIMIT_*` | Rate limiter tuning (or disable with `RATE_LIMIT_ENABLED=false`) |
| `SPORTS_PROVIDER`, `GAMES_PROVIDER` | Provider selection (currently `mock`) |
