# Backend

FastAPI + SQLAlchemy + PostgreSQL, with MongoDB alongside for Module 1's
document data.

- Endpoint contract: [`../docs/API/api-spec.md`](../docs/API/api-spec.md)
  (also live at `/docs` when the server is running)
- Why the stack looks like this:
  [`../docs/Architecture/architecture.md`](../docs/Architecture/architecture.md)
- Schema: [`../docs/Database/database-design.md`](../docs/Database/database-design.md)
- Conventions for adding code: [`../CONTRIBUTING.md`](../CONTRIBUTING.md)

## Requirements

- Python 3.12+
- PostgreSQL — via the included `docker-compose.yml` or your own instance
- MongoDB — optional; only Module 1's features need it

## Setup

```bash
cp .env.example .env          # edit if not using the docker-compose defaults
docker compose up -d db mongo
pip install -r requirements.txt
alembic upgrade head          # creates users/profiles/cases/case_files
uvicorn app.main:app --reload
```

The API is then at `http://localhost:8000`:

| | |
|---|---|
| Interactive docs | `/docs` |
| Versioned API | `/api/v1/...` |
| Health check | `/health` |

### Without Docker

SQLite works for a zero-dependency smoke test — set in `.env`:

```
DATABASE_URL=sqlite:///./dev.db
```

Fine for manual testing (the test suite uses SQLite too), but CI runs
migrations against real Postgres to catch what SQLite papers over: native
enums, JSON column semantics, stricter type checking.

### Full stack in Docker

```bash
docker compose up --build
```

Run `alembic upgrade head` once against the Dockerized Postgres before the
API can serve real requests. Migrations deliberately do not run on
container boot, so a bad migration can't be half-applied by a restart loop.

## Tests

```bash
pytest
```

In-memory SQLite, one database per test, no external services. Coverage
maps to the PRD acceptance criteria: `test_auth.py` (US-03 signup/login/
lockout), `test_profile.py` (onboarding, dashboard ordering), `test_cases.py`
(US-04 browse/search/filter, US-04B upload/share, ownership, admin
moderation), `test_storage.py` (storage backends).

`test_app_wiring.py` is different in kind: it asserts the *shape* of the
API rather than any feature — that all three modules are mounted, that
routes stay under `/api/v1`, that no two modules claim the same path, that
the documented endpoints still exist, and that protected routes still
reject anonymous callers. Those are the failures another team's change can
cause without breaking any of their own tests. Don't delete an assertion
there to make a change pass; if it fails, either the change is wrong or the
contract moved and `docs/API/api-spec.md` needs updating too.

Note that `tests/conftest.py` prefixes every request with `/api/v1`, so
tests name endpoints the way the API spec documents them (`/auth/login`).

## Configuration

`.env.example` documents every variable. Nothing in the codebase reads an
environment variable that isn't listed there — if you add one, add it to
both `.env.example` and `app/core/config.py` in the same commit.

Three that matter in any deployment:

- `DATABASE_URL` — never SQLite outside local smoke tests. Managed Postgres
  connection strings usually need `postgresql+psycopg2://`, not the
  `postgresql://` they hand you.
- `STORAGE_BACKEND` — never `local` on a hosted deployment. Most platforms
  wipe local disk on redeploy, silently destroying every uploaded PDF. Use
  `database` or `s3` (ADR-07).
- `JWT_SECRET_KEY` — the default is public in this repo; anyone with it can
  mint valid tokens.

## Migrations

```bash
alembic upgrade head                                   # apply
alembic revision --autogenerate -m "describe change"   # create (review it!)
```

All modules share one migration history — see the migrations section of
[`../CONTRIBUTING.md`](../CONTRIBUTING.md) before adding one.

Existing migrations were hand-written to mirror `app/models/*.py`, so
autogenerate output needs review: renamed columns show up as drop+add, and
`SAEnum` `name=` changes aren't detected. Every `SAEnum` pins `name=`
explicitly so the Python enum and the Postgres native ENUM can't drift.

## Admin access

Admin rights are granted by CLI only — deliberately no API endpoint, since
an HTTP privilege-escalation path is a liability nobody needed (ADR-05):

```bash
python scripts/promote_admin.py user@example.com
```

## Layout

```
app/
  main.py            App instance, CORS, mounts the v1 router
  api/v1/            HTTP layer — see CONTRIBUTING.md to add endpoints
  core/              config, constants, security, dependencies
  database/          postgres.py, mongodb.py, vector_db.py
  models/            SQLAlchemy ORM models
  schemas/           Pydantic request/response models
  services/          Business logic, callable outside HTTP
alembic/             Migrations
tests/               Pytest suite
scripts/             Operational CLIs
seed-data/           Sample case PDF for exercising uploads
```
