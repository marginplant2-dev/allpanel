# MongoDB Schema

Database: `sportx` (configurable via `MONGO_DB_NAME`).

## Collections & key indexes

### users
`_id, username, password_hash, full_name, role, parent_id, hierarchy_path[], status,
credit_limit, notes, two_factor_enabled, created_at, updated_at, last_login`
- `username` unique
- `parent_id`, `role`, `hierarchy_path`, `status`

### wallets
`_id(user_id), available_balance, locked_balance, updated_at`
- `_id` is the user id (1:1)

### transactions (ledger)
`transaction_id, from_user_id, to_user_id, amount, transaction_type, status,
idempotency_key, metadata, created_at`
- `transaction_id` unique
- `idempotency_key` unique (partial, when present)
- `from_user_id`, `to_user_id`, `created_at`

### games
`name, slug, provider, category, thumbnail_url, banner_url, status, featured,
sort_order, tags[], created_at, updated_at`
- `slug` unique
- `category`, `status`, `featured`, `sort_order`

### game_categories
`key(unique), name, sort_order, status`

### sports
`key(unique), name, icon, sort_order, status`

### events
`sport_id, name, participants[], league, start_time, status, score, markets[]`
- `sport_id`, `status`, `start_time`

### providers
`key(unique), type, name, config, enabled`

### credit_requests
`user_id, username, parent_id, type(DEPOSIT|WITHDRAW), amount, status(PENDING|PROCESSING|APPROVED|REJECTED),
note, decision_note, transaction_id, created_at, decided_at`
- `user_id`, `parent_id`, `status`, `created_at`
- Approval moves virtual credits via the same `LedgerService` primitive as `/credits/transfer`
  (parent -> user for DEPOSIT, user -> parent for WITHDRAW); no real payment gateway involved.

### notifications
`user_id, type, title, body, read, created_at`
- `user_id`, `created_at`

### sessions
`token_id(unique), user_id, ip, user_agent, created_at, expires_at, revoked`
- `user_id`

### audit_logs
`actor_id, action, target_id, metadata, ip_address, created_at`
- `actor_id`, `action`, `created_at`

### impersonation_sessions
`admin_id, target_id, token_id, started_at, ended_at`

### system_settings
Singleton document holding config + feature flags.

## Transfer concurrency

Credit transfers use an atomic guarded `find_one_and_update`
(`available_balance >= amount`) to debit the sender, credit the receiver, and write a
ledger transaction. A unique `idempotency_key` prevents duplicate processing.
