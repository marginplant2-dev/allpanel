# Architecture

SportX is a **modular monolith**: a single backend deployable composed of independent
domain modules, plus two independent React frontends.

## Components

- **backend/** — FastAPI async app. Domain modules under `app/modules/*` each follow a
  clean layering: `router.py` (HTTP) → `service.py` (business logic) → `repository.py`
  (data access) → `schema.py` (Pydantic DTOs) / `models.py` (domain/DB shapes).
  Cross-cutting concerns live in `app/core`, `app/middleware`, `app/websocket`,
  `app/workers`, `app/utils`.
- **frontend-user/** — end-user premium dark UI.
- **frontend-admin/** — admin SaaS dashboard.

## Layering rules

- Routers never contain business logic; they validate input and delegate to services.
- Services orchestrate business rules and call repositories.
- Repositories are the only layer that talks to MongoDB (via Motor).
- Schemas are Pydantic models for request/response; models describe stored documents.

## Cross-cutting

- **core/config.py** — settings from environment (`pydantic-settings`).
- **core/database.py** — Motor client lifecycle + index creation.
- **core/security.py** — password hashing, JWT encode/decode.
- **core/dependencies.py** — FastAPI dependencies (current user, RBAC guards).
- **middleware/** — request id, error handling, CORS, rate-limit-ready hooks.
- **websocket/** — connection manager, channels, event dispatch.
- **workers/** — background tasks (notifications, reports, mock live sync).

## Realtime

WebSocket channels push live event updates, wallet updates, notifications and admin
alerts. The manager is designed so realtime can later be extracted into a dedicated
service backed by Redis pub/sub.

## Provider abstraction

`app/modules/providers` defines `BaseSportsProvider` and `BaseGameProvider` interfaces.
A `MockProvider` supplies deterministic development data. A `provider_factory` selects
the active provider from settings, so external APIs can be added without touching the
frontend or route contracts.
