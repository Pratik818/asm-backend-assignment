# ASM Asset Discovery Service

Backend microservice for the Attack Surface Management (ASM) platform. Manages a list of
monitored domains and performs passive DNS asset discovery (A, AAAA, NS, MX records) against
them, in the background, with full scan history and role-based access control.

## Requirements

- Docker & Docker Compose (everything else runs inside containers)
- Python 3.12+ (only needed if you want to run the API directly on your host, or run the test
  suite from your host)

## Quick start (Docker)

```bash
git clone <this-repo>
cd asm-backend-assignment
docker compose up --build
```

That's it — no `.env` file is required. `Settings` (`app/core/config.py`) ships with working
defaults for every value, and `docker-compose.yml` supplies the two values (`POSTGRES_HOST`,
`REDIS_HOST`) that only make sense inside the Docker network.

This single command:

- Builds and starts `db` (Postgres), `redis`, `api`, and `worker`
- Runs Alembic migrations automatically before the API starts (see the `Dockerfile`'s `CMD`)
- Serves the API at `http://localhost:8000`, with interactive docs at `http://localhost:8000/docs`

If you want to override any credential or setting, copy `.env.example` to `.env` and fill in
only the values you want to change — every line is optional and blank lines fall back to
`Settings`' built-in defaults.

```bash
cp .env.example .env
```

### Creating your first user

`POST /auth/register` is Admin-only, which means there's no way to create the *first* user
through the API — that's what the `asm` CLI is for:

```bash
From Docker :
step 1 : docker exec -it <docker_id> or <docker_name> /bin/bash ( to get into docker terminal )
step 2 :  asm create-admin --email admin@example.com --password 'Str0ngPass!23' --full-name "Admin User"
```

- All three flags are required; `--password value` and `--password=value` both work.
- The password must satisfy the same policy enforced everywhere else (min 8 / max 72 bytes, at
  least one letter and one digit) — a weak password prints `Invalid password: <reason>` and
  exits with a non-zero status instead of creating the user.
- If the email is already registered, it prints a message and exits cleanly without creating a
  duplicate.
- On success: `Created admin user: <email>`.

From there, log in to get a token and use it to register further users (Admin/Analyst/Viewer)
through `POST /auth/register`:

```bash
curl -X POST http://localhost:8000/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email": "admin@example.com", "password": "Str0ngPass!23"}'
```

## Running without Docker

Only useful for local development/debugging outside a container:
``` bash
# Linux/macOS
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
pip install -e . --no-deps   # registers the `asm` console script

docker compose up -d db redis   # still need Postgres/Redis running somewhere
alembic upgrade head
uvicorn app.main:app --reload


# Windows (PowerShell)
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
pip install -e . --no-deps   # registers the `asm` console script

docker compose up -d db redis   # still need Postgres/Redis running somewhere
alembic upgrade head
uvicorn app.main:app --reload
```

`Settings.POSTGRES_HOST`/`REDIS_HOST` default to `"localhost"` (correct for this scenario,
since Docker publishes `db`'s and `redis`'s ports to your host) — no environment variables
needed unless you've changed the published ports.

## Running the test suite

```bash
docker compose up -d db      # only the database is needed — Celery runs in-process during tests
pip install -r requirements.txt
pytest
```

No environment variables are required. A few things happen automatically, the first time you
run it:

- `app/tests/conftest.py` connects to Postgres and creates a dedicated `asm_db_test` database
  (via `Settings.POSTGRES_TEST_DB`) if it doesn't already exist — this is a completely separate
  database from `asm_db`, so tests can never touch real data.
- It then creates every table directly from the SQLAlchemy models (`Base.metadata.create_all`).
- Celery is configured to run tasks synchronously in-process (`task_always_eager`), so `redis`
  and the `worker` container aren't needed to run the suite at all.

Useful flags: `pytest -k test_login` to run a subset by name, `pytest -x` to stop at the first
failure, `pytest -v` for per-test output.

The suite covers: authentication (login success/failure/inactive user), RBAC enforcement across
all three roles, domain CRUD including duplicate rejection and FQDN validation, DNS discovery
logic (fully mocked — no real network calls in the test suite itself), scan lifecycle and the
one-running-scan-per-domain conflict, asset listing/filtering, audit logging, and password
policy.

## Architecture overview

```
app/
  api/v1/        route handlers only — parse request, call a service, return response_model
  core/          config, security (JWT/bcrypt), RBAC dependency, audit dependency, logging, exceptions
  models/        SQLAlchemy models (one class per file, relationships via string targets)
  schemas/       Pydantic request/response models
  services/      business logic — the only layer that enforces rules like "no duplicate domains"
  repositories/  one class per table, plain SQLAlchemy queries, no business logic
  workers/       Celery app + the discover_domain task + DNS resolver
  db/            engine/session/Base
  tests/         pytest suite (mirrors this same layout)
migrations/      Alembic
```

Request flow: **route → service → repository → model**. Routes never touch the database
directly; services never import FastAPI; repositories never contain business rules. Each layer
only knows about the one below it.

**Auth & RBAC** — JWT bearer tokens (`app/core/security.py`), decoded by
`get_current_user` (`app/core/dependencies.py`). `require_role(*roles)` is a dependency
*factory* — each route declares exactly which roles it accepts, matching the RBAC matrix in the
assignment spec one-to-one.

**Background discovery** — `POST /domains` and `POST /domains/{id}/scan` create a `Scan` row
(`PENDING`) and dispatch `discover_domain.delay(scan_id)` to Celery. The worker (separate
container, same codebase) picks it up, flips the `Scan`/`Domain` status to `RUNNING`, resolves
A/AAAA/NS/MX records, persists `Asset` rows, and finishes as `COMPLETED` or `FAILED` (with
`error_message` populated) — never left stuck in `RUNNING`.

**Audit logging** — a bonus feature, not part of the core spec. `POST /domains` and
`DELETE /domains/{id}` are wired with a `log_event(...)` dependency
(`app/core/audit.py`) that captures the request's path/query/body params *before* the route
runs. The shared request-logging middleware in `app/main.py` writes the actual `EventLog` row
*after* the response comes back, and only if the request succeeded (status code < 400) — so a
409 duplicate-domain attempt or a 403 doesn't produce a false audit entry.

## Environment variables

All optional — every field in `Settings` has a working default. `.env.example` documents each
one with blank values (copy it to `.env` and fill in only what you want to override).

| Variable | Default | Notes |
|---|---|---|
| `POSTGRES_USER` | `postgres` | |
| `POSTGRES_PASSWORD` | `asm@postgres` | Change this for anything beyond local dev |
| `POSTGRES_DB` | `asm_db` | |
| `POSTGRES_HOST` | `localhost` | `docker-compose.yml` sets this to `db` for the `api`/`worker` containers |
| `POSTGRES_PORT` | `5432` | Also used as the host-side port mapping in `docker-compose.yml` |
| `REDIS_HOST` | `localhost` | `docker-compose.yml` sets this to `redis` for the `api`/`worker` containers |
| `REDIS_PORT` | `6379` | Also used as the host-side port mapping |
| `APP_PORT` | `8000` | Host-side port mapping only (docker-compose) |
| `APP_NAME` | `ASM Asset Discovery Service` | Shown in `/docs` |
| `APP_VERSION` | `0.1.0` | |
| `ENVIRONMENT` | `development` | One of `development` / `staging` / `production` |
| `LOG_LEVEL` | `INFO` | One of `DEBUG` / `INFO` / `WARNING` / `ERROR` / `CRITICAL` |
| `JWT_SECRET_KEY` | dev-only placeholder | **Change this in any real deployment** |
| `JWT_ALGORITHM` | `HS256` | |
| `JWT_EXPIRE_SECONDS` | `3600` | |
| `DNS_RESOLVE_TIMEOUT` | `3.0` | Seconds, per DNS lookup attempt |
| `DNS_RESOLVE_RETRIES` | `3` | Retries on transient failure (timeout/no nameservers) before the scan fails; `NXDOMAIN`/no-record responses are not retried, since they're a definitive answer |

`POSTGRES_TEST_DB` (default `asm_db_test`) also exists but isn't meant to be set via `.env` —
it's a fixed, separate database name the test suite always uses, so tests can never collide
with real data regardless of what `POSTGRES_DB` is set to.

## Key design decisions & trade-offs

- **Repository/Service/Route split, not a generic "manager" layer.** Repositories take a
  `Session` and do plain `select()`/`scalar()` calls; services construct their own repositories
  internally rather than receiving them via nested `Depends()` chains. This keeps each route
  function to a single `Depends(get_db)` + one `Depends(require_role(...))`, no provider
  pyramids.
- **String-based `relationship()` targets** (e.g. `relationship("Domain", ...)`) instead of
  importing model classes across files. SQLAlchemy resolves these at runtime via its own class
  registry, so `app/models/*.py` files never import each other — avoids circular imports without
  needing `TYPE_CHECKING` gymnastics.
- **Sync SQLAlchemy + Celery, not async.** The assignment lists async SQLAlchemy as optional
  bonus stack; the scan-then-DNS-then-persist workflow is I/O-bound but low-concurrency (one
  worker process, one scan at a time per domain by design), so the simplicity of a sync stack
  outweighs the throughput benefit async would bring here.
- **`tests/` nested under `app/`**, matching the assignment's suggested project structure
  exactly, rather than at the repo root.
- **Settings-as-single-source-of-truth.** `app/core/config.py`'s `Settings` class holds real,
  working defaults for every value (matching `docker-compose.yml`'s internal service names/
  ports); `.env`/`.env.example` are optional overrides layered on top, not a requirement — a
  fresh clone works with zero configuration.
- **DNS retry policy distinguishes "no such record" from "transient failure."** `NXDOMAIN`/
  `NoAnswer` return an empty list immediately (retrying won't produce a record that doesn't
  exist); `Timeout`/`NoNameservers` retry up to `DNS_RESOLVE_RETRIES` times before the whole scan
  is marked `FAILED` — a partial failure never leaves partially-discovered assets persisted,
  since `AssetRepository.bulk_create()` only runs after every record type for a domain has been
  attempted.
- **Audit logging is deliberately lightweight**, not a generic event-sourcing system: one
  dependency + one shared middleware, covering the two sensitive actions the spec calls out
  (domain create/delete) rather than a framework meant to cover every future endpoint
  automatically.

## Ideas for future improvement

- Rate limiting on `/auth/login` and `/auth/register` (listed as bonus in the spec)
- A read endpoint over `event_logs` for actually reviewing the audit trail
- CI pipeline (lint + test on every push)
- Metrics endpoint (Prometheus-style)
- Soft delete for domains instead of a hard `DELETE`
- Fully async SQLAlchemy if discovery throughput ever needs to scale past one worker
