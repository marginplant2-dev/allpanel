# Deploying AllPanel next to an existing site (same server)

> **Live status (17 Sep 2026)** — deployed on `13.204.121.174` beside marginplant:
> backend `sportx-api` on 127.0.0.1:8010, frontends in `/var/www/sportx/{user,admin}`,
> nginx file `allpanel55.conf` (mirrored in `deploy/nginx/`). Serving on HTTP and
> verified by Host header. **Waiting on DNS** before TLS — see the table below.
>
> | Host | A record needed | Serves |
> |---|---|---|
> | `allpanel55.com`, `www` | 13.204.121.174 (currently 2.57.91.91, Hostinger parked) | player site |
> | `admin.allpanel55.com` | 13.204.121.174 (missing) | admin console |
> | `api.allpanel55.com` | 13.204.121.174 (missing) | API + WebSocket |
>
> Once those resolve: `sudo certbot --nginx -d allpanel55.com -d www.allpanel55.com -d admin.allpanel55.com -d api.allpanel55.com`

Written for: whoever runs the server — assumes root/sudo and an existing production
site on the same box that must keep running untouched.

The goal is a **test deployment that cannot disturb the neighbour app**. Everything
SportX uses is its own: its own Linux user, its own directory, its own port on
loopback, its own database name, its own nginx file, its own subdomains, and hard
memory/CPU caps. No existing file is edited; files are only added.

> Why this server at all: the proexch odds feed whitelists by **server IP**, and this
> box's IP is the one that was submitted. The outbound calls have to leave from here.

---

## 0. Target server — surveyed 2026-09-17 (read-only)

AWS box `13.204.121.174` (ubuntu), already running the **marginplant** stack. Checked
before writing these steps; re-run the commands below if anything has moved since.

| | Found | Verdict |
|---|---|---|
| CPU / RAM | 8 vCPU · 15.7 GB (8.1 GB available, 4 GB swap) | plenty of headroom |
| Disk | 484 GB, 7% used | fine |
| Python / Node | 3.12.3 · v20.20.2 · npm 10.8.2 · venv ok | nothing to install |
| Port 8010 / 8011 | free (neighbour uses 8000, 8001, 8002, 3000-3002, 6379, 27017) | use **8010** |
| MongoDB | running, `cacheSizeGB: 4`, loopback only, DB `marginplant` (7.4 GB) | reuse it, new DB name |
| nginx | config valid, per-domain files in `sites-enabled/` | add one more file |
| certbot | installed | TLS ready |
| Outbound | works, egress IP = 13.204.121.174 | matches the whitelist request |
| Neighbour services | `marginplant-backend`, `-celery-worker`, `-celery-beat`, `-feed`, `-feed-global`, `pm2-ubuntu`, `redis-server` | no name clash with `sportx-api` |

Re-check command:

```bash
ss -ltn 'sport = :8010'; free -m; df -h /; nginx -t; python3 --version; node --version
```

**Two things to know before going further:**

1. **The proexch whitelist is not active yet.** From this exact server the feed still
   answers 403 (`/api/cricket/matches`, `/api/soccer/matches`, `/api/score-fixture`).
   Deployment can proceed — the app runs on seeded demo data until the feed opens —
   but confirm with the vendor that `13.204.121.174` is the IP they added.
2. **mongod has no authentication** (`security:` is not configured, bound to
   127.0.0.1). That is the neighbour app's existing setup, not something this
   deployment changes; it does mean any local process can read the 7.4 GB
   `marginplant` database. Worth enabling auth on that server at some point —
   separately, and with the marginplant team, since it needs their connection
   strings updated too.

## 1. Dedicated user and directory

```bash
sudo useradd --system --home /opt/sportx --shell /usr/sbin/nologin sportx
sudo mkdir -p /opt/sportx /var/www/sportx
sudo chown -R sportx:sportx /opt/sportx
```

Copy the repo to `/opt/sportx` (git clone, scp or rsync — whatever you already use).

---

## 2. MongoDB — nothing to install, just a new database name

mongod is already running on this server (loopback only, cache capped at 4 GB). A
different database name gives full collection-level isolation; the `marginplant`
data is never read or written by this app.

```ini
# backend/.env
MONGO_URI=mongodb://localhost:27017
MONGO_DB_NAME=sportx
```

Do **not** edit `/etc/mongod.conf` — the neighbour app depends on it.

## 3. Backend

```bash
cd /opt/sportx/backend
sudo -u sportx python3 -m venv .venv
sudo -u sportx .venv/bin/pip install -r requirements.txt
sudo -u sportx cp .env.example .env
sudo -u sportx nano .env
```

Set at least:

```ini
ENVIRONMENT=production
DEBUG=false
JWT_SECRET_KEY=<python3 -c "import secrets;print(secrets.token_urlsafe(64))">
MONGO_URI=mongodb://localhost:27017
MONGO_DB_NAME=sportx
CORS_ORIGINS=https://game.example.com,https://admin.example.com

# odds feed (this server's IP + these domains are the whitelisted ones)
SPORTS_PROVIDER=proexch
PROEXCH_BASE_URL=https://apidata.proexch.in
PROEXCH_ORIGIN=https://game.example.com

SUPERADMIN_PASSWORD=<something long>
```

Seed and check the feed:

```bash
sudo -u sportx .venv/bin/python -m scripts.seed_data        # mother admin + role migration
sudo -u sportx .venv/bin/python -m scripts.seed_content     # demo board (fallback data)
sudo -u sportx .venv/bin/python -m scripts.probe_proexch --out /tmp/feed.json
```

The probe is the whitelist test: 403 means the IP/domain is not active yet.
`/tmp/feed.json` is what the provider mapping is written from — send it over.

---

## 4. Service

```bash
sudo cp /opt/sportx/deploy/systemd/sportx-api.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable --now sportx-api
curl -s localhost:8010/health          # {"success":true,...}
journalctl -u sportx-api -n 50 --no-pager
```

The unit binds to `127.0.0.1` and is capped at `MemoryMax=600M`, `CPUQuota=50%`,
`Nice=5` — under load the kernel prioritises the neighbour app, and SportX gets
OOM-killed (and restarted) long before the server runs out of memory.

---

## 5. Frontends

Build on the server, or build locally and upload the `dist/` folders.

```bash
cd /opt/sportx/frontend-user
printf 'VITE_API_BASE_URL=https://game.example.com/api/v1\nVITE_WS_BASE_URL=wss://game.example.com\n' > .env
npm ci && npm run build
sudo rsync -a --delete dist/ /var/www/sportx/user/

cd ../frontend-admin
printf 'VITE_API_BASE_URL=https://admin.example.com/api/v1\nVITE_WS_BASE_URL=wss://admin.example.com\n' > .env
npm ci && npm run build
sudo rsync -a --delete dist/ /var/www/sportx/admin/

sudo chown -R www-data:www-data /var/www/sportx
```

> `npm ci` is memory-hungry. On a small box run the builds one at a time, or build
> on your laptop and upload the `dist/` folders instead.

---

## 6. nginx — add a file, reload (never restart)

```bash
sudo cp /opt/sportx/deploy/nginx/sportx.conf.sample /etc/nginx/sites-available/sportx.conf
sudo sed -i 's/game.example.com/game.YOURDOMAIN.com/; s/admin.example.com/admin.YOURDOMAIN.com/' \
  /etc/nginx/sites-available/sportx.conf
sudo ln -s /etc/nginx/sites-available/sportx.conf /etc/nginx/sites-enabled/
sudo nginx -t                      # MUST pass before the next line
sudo systemctl reload nginx        # reload keeps the existing site serving
```

`reload` re-reads config without dropping connections. If `nginx -t` fails, remove
the symlink and reload again — the other site is unaffected either way.

DNS: point `game` and `admin` A records at this server's IP. Then TLS:

```bash
sudo certbot --nginx -d game.YOURDOMAIN.com -d admin.YOURDOMAIN.com
```

Certbot only rewrites the blocks for those names.

---

## 7. Verify, then watch the neighbour

```bash
curl -I https://game.YOURDOMAIN.com          # 200, SPA
curl -s https://game.YOURDOMAIN.com/api/v1/meta   # sports_data_source: live | seeded
systemctl status sportx-api --no-pager
systemd-cgtop -1 -n1 | head                  # SportX must stay inside its caps
```

Check the existing site once after the reload — it should be exactly as before.

---

## Rollback (one minute, no effect on the other site)

```bash
sudo rm /etc/nginx/sites-enabled/sportx.conf && sudo nginx -t && sudo systemctl reload nginx
sudo systemctl disable --now sportx-api
# optional: drop the data
mongosh --eval 'db.getSiblingDB("sportx").dropDatabase()'
sudo rm -rf /opt/sportx /var/www/sportx
sudo userdel sportx
```

---

## What this deployment deliberately does NOT do

- No Docker, no changes to the neighbour app's nginx blocks, services or database.
- No new public port (the API is loopback-only, reachable through nginx).
- Single backend worker: realtime and rate limiting are in-process. Scaling out needs
  Redis first — see `deploy/README.md`.
- No backups/monitoring: this is a test deployment. Add both before real users.
