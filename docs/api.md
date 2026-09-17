# API Reference (overview)

All responses use a consistent envelope.

**Success**
```json
{ "success": true, "data": {}, "message": "" }
```

**Error**
```json
{ "success": false, "error": { "code": "ERROR_CODE", "message": "Human readable" } }
```

Base path: `/api/v1`. Interactive docs at `/docs` (Swagger) when the backend runs.

## Auth
- `POST /auth/register` — self-register a USER account
- `POST /auth/login` — returns access + refresh tokens
- `POST /auth/refresh` — exchange refresh token for a new access token
- `POST /auth/logout` — revoke the current session
- `GET  /auth/me` — current authenticated principal

## Users
- `GET  /users` — hierarchy-scoped list (filter, sort, paginate)
- `POST /users` — create child user (role/hierarchy validated)
- `GET  /users/{id}` — details (must be in downline or self)
- `PATCH /users/{id}` — update
- `POST /users/{id}/suspend` · `POST /users/{id}/activate`
- `GET  /users/{id}/activity`

## Hierarchy
- `GET /hierarchy/tree` · `GET /hierarchy/downline`

## Wallet & Credits
- `GET  /wallet` — balances for current user
- `GET  /wallet/transactions` — filtered, paginated history
- `POST /credits/transfer` — idempotent transfer (Idempotency-Key header)
- `GET  /credits/history` · `GET /credits/ledger` (admin)
- `POST /credit-requests` — user requests a virtual deposit/withdraw from their direct parent
- `GET  /credit-requests/mine` — requester's own request history
- `GET  /credit-requests/inbox` (admin) — pending requests awaiting the actor's decision
- `POST /credit-requests/{id}/approve` · `POST /credit-requests/{id}/reject` (direct parent only)

## Games / Sports
- `GET /games` · `GET /games/{slug}` (public catalogue)
- Admin: `POST/PATCH/DELETE /games`, categories, providers
- `GET /sports` · `GET /events?status=` · `GET /events/{id}` (via provider layer)

## Reports
- `GET /reports/user|agent|credit|activity|general`

## Notifications
- `GET /notifications` · `POST /notifications/{id}/read`

## Impersonation
- `POST /impersonation/start` · `POST /impersonation/end`

## Settings
- `GET/PATCH /settings` · feature flags

## WebSocket
- `GET /ws` — authenticated channels: live events, wallet, notifications, admin alerts
