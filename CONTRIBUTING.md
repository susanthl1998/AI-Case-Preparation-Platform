# Contributing

Three teams share this repository. These conventions exist so that adding
your module doesn't require editing another team's files — which is what
turns a shared repo into a merge-conflict machine.

## Who owns what

| Area | Owner |
|---|---|
| `api/v1/auth.py`, `users.py`, `cases.py`, `models/`, `schemas/`, `alembic/` | Team 2 — Account Management & Case Repository |
| `api/v1/chat.py`, `interview.py`, `services/ai_service.py`, `rag_service.py`, `evaluation_service.py`, `database/mongodb.py` collections, `database/vector_db.py` | Team 1 — AI Trainer |
| Multiplayer / group prep (no files yet — create them) | Team 3 |
| `main.py`, `core/config.py`, `docs/`, CI | Shared — coordinate before changing |

Touching another team's files is fine when you need to; telling them is the
part that matters.

## Adding endpoints

**Do not edit `app/main.py`.** It mounts one router and never needs to
change. Instead:

1. Create your file in `backend/app/api/v1/`, e.g. `groups.py`:

   ```python
   from fastapi import APIRouter

   router = APIRouter(prefix="/groups", tags=["groups"])

   @router.get("/")
   def list_groups():
       ...
   ```

2. Register it in `backend/app/api/v1/__init__.py` — one import, one
   `include_router` line, in your team's marked section.

That file is the only shared merge point for routes, and conflicts there
are one-line and trivial to resolve.

Everything lands under `/api/v1` automatically. Don't hardcode the prefix
in your routers — it comes from `API_V1_PREFIX` and is applied once in
`main.py`.

## Where logic goes

Keep routers thin: parse the request, call a service, return a response.
Business logic belongs in `backend/app/services/`, named `<area>_service.py`.

The reason is practical rather than aesthetic: logic in a service can be
called by scripts, background jobs, and other modules; logic in a route
handler can only be reached over HTTP.

## Databases

**PostgreSQL** is the relational source of truth — accounts, profiles, case
metadata. **MongoDB** holds schemaless per-session documents (chat
transcripts, AI evaluation results).

Mongo is optional at runtime: with `MONGODB_URI` unset the service still
starts and serves everything Module 2 provides. Keep it that way — a
missing Mongo should never take down login.

```python
from app.database.postgres import get_db        # SQLAlchemy session
from app.database.mongodb import get_mongo_db    # Mongo database handle
```

### ⚠️ Migrations: the one rule that bites everyone

All modules share one Alembic history. Before writing a migration:

```bash
git pull
cd backend && alembic heads     # must show exactly one head
```

Set your new revision's `down_revision` to that head. If two teams branch
migrations from the same parent, `alembic upgrade head` fails with
"multiple heads" and **every** environment breaks until it's merged — not
just the team that caused it.

Migrations are never run automatically on container start, so a bad one
can't be half-applied by a restart loop. Run `alembic upgrade head`
explicitly.

## Shared constants

Import the case taxonomy from `app.core.constants`, not from Module 2's
ORM models:

```python
from app.core.constants import CaseType, Difficulty
```

That module is a deliberate contract; `app/models/` is Module 2's internal
storage detail and may be reorganized.

The case taxonomy is **frozen** per PRD §9 because Module 1 depends on it.
Adding a value needs a migration (the Postgres ENUM type must be altered
too) and cross-team sign-off.

## Configuration

Every setting lives in `backend/app/core/config.py` and is documented in
`backend/.env.example`. If you add one, add it to both in the same commit —
otherwise it works on your machine and nowhere else.

Never commit a real `.env`. `.gitignore` covers it; don't use `git add -f`
to get around that.

## Tests

```bash
cd backend && pytest
```

Tests run against in-memory SQLite, one database per test, no external
services needed. CI runs the same suite plus migrations against real
Postgres on every pull request.

Add tests for your module under `backend/tests/`. When you change shared
code (`main.py`, `core/`, `database/`), run the whole suite — that's what
catches breakage in another team's module before they find it.

## Documentation

Update these in the **same commit** as the code, not afterwards:

- New or changed endpoints → [`docs/API/api-spec.md`](docs/API/api-spec.md)
- Schema changes → [`docs/Database/database-design.md`](docs/Database/database-design.md)
- A decision someone might otherwise reverse by accident →
  a new ADR in [`docs/Architecture/architecture.md`](docs/Architecture/architecture.md)

The ADR log is the most valuable thing here. If you chose something
non-obvious, write down *why* — a future teammate reading only the code
cannot tell a deliberate constraint from an accident.

## Pull requests

Branch from `main`, named `team<N>/<short-description>`
(e.g. `team1/chat-endpoints`). Open a PR; CI must be green before merge.

If your change affects another module's contract — an endpoint shape, a
shared constant, the schema — say so in the PR description and tell that
team directly. CI catches broken code, not broken assumptions.
