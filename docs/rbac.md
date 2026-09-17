# Roles & Permissions (RBAC)

## Hierarchy

```
MOTHER_ADMIN → SUPER_ADMIN → ADMIN → MASTER → AGENT → USER
```

Every account stores `parent_id` and `hierarchy_path` (ancestors, top down). A target
is in an actor's downline iff the actor's id appears in the target's `hierarchy_path`
(the MOTHER_ADMIN, being the root, is upline of everyone).

Each level signs up **its own players** as well as the one admin level below it.
Levels cannot be skipped: an ADMIN creates MASTERs, not AGENTs.

## Visibility

An account's own panel shows **its direct children only** — the players your downline
signed up belong to *their* panel, not yours. To look at them, use "Login as" on that
account (impersonation, fully audited).

| Logged in as | Sees in its own panel |
|--------------|------------------------|
| MOTHER_ADMIN | own players + its super admins |
| SUPER_ADMIN  | own players + its admins |
| ADMIN        | own players + its masters |
| MASTER       | own players + its agents **+ those agents' players** |
| AGENT        | own players |

## Coins

Coins only move one step down the chain: MOTHER_ADMIN → SUPER_ADMIN → ADMIN → MASTER
→ AGENT → USER. An account with no coins cannot fund anyone below it, and nobody can
reach past a level to fund a grandchild. The MOTHER_ADMIN is the only source (seeded).

## Permission matrix

| Capability                | MOTHER | SUPER | ADMIN | MASTER | AGENT | USER |
|---------------------------|--------|-------|-------|--------|-------|------|
| Create next level down    | SUPER  | ADMIN | MASTER| AGENT  | –     | –    |
| Create own players        | ✓      | ✓     | ✓     | ✓      | ✓     | –    |
| Give coins to own children| ✓      | ✓     | ✓     | ✓      | ✓     | –    |
| Deposit/withdraw for own players | ✓ | ✓    | ✓     | ✓      | ✓     | –    |
| Impersonate own downline  | ✓      | ✓     | ✓     | ✓      | –     | –    |
| Global reports / settings / audit | ✓ | –  | –     | –      | –     | –    |

## Enforcement

- `require_roles(...)` dependency restricts endpoints to specific roles.
- `require_downline(target_id)` verifies the target is within the actor's subtree.
- A role may only create a child role strictly one (or more) levels below itself,
  bounded by the matrix above.
- All checks run server-side. Frontend hiding of actions is cosmetic only.
