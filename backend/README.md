# SportX Backend

FastAPI + MongoDB (Motor) modular monolith. Virtual credits only.

## Prerequisites

- Python 3.12+
- MongoDB Community Server running locally (default `mongodb://localhost:27017`)

### Install MongoDB locally (Windows)

1. Download **MongoDB Community Server** from
   <https://www.mongodb.com/try/download/community> (MSI installer).
2. Install as a **Windows Service** (default) so `mongod` runs automatically.
3. Verify it is listening on port `27017` (e.g. `Get-Service MongoDB`).

Alternatively install via Chocolatey: `choco install mongodb`.

## Setup

```powershell
cd backend
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
Copy-Item .env.example .env   # then edit secrets
```

## Run

```powershell
uvicorn app.main:app --reload --port 8000
```

- Health: <http://localhost:8000/health>
- API meta: <http://localhost:8000/api/v1/meta>
- Swagger docs: <http://localhost:8000/docs>

## Seed the bootstrap super admin (Phase 2+)

```powershell
python -m scripts.seed_data
```

## Tests

```powershell
pytest
```

## Project layout

```
app/
├── core/         config, database, security, dependencies, enums, responses, exceptions
├── modules/      domain modules (auth, users, hierarchy, wallet, ledger, games, ...)
│   └── <module>/ router.py · service.py · repository.py · schema.py · models.py
├── middleware/   request context, error handlers
├── websocket/    connection manager, channels, events
├── workers/      background tasks
├── utils/        shared helpers
├── api.py        aggregates versioned routers
└── main.py       app factory + lifespan
```
