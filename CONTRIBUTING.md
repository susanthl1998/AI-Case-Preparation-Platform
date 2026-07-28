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

## Adding your module's UI

The frontend has the same shape as the backend: one registry, and you
never touch the router.

`frontend/src/modules/registry.js` declares all three modules. The
post-login launcher, the routes, and the navbar are all generated from it.

1. Build your screens under `frontend/src/modules/<yourModule>/`.
   Placeholder landing components are already there —
   `casePrep/CasePrepHome.jsx` and `peer2peer/Peer2PeerHome.jsx`. Replace
   the body of yours.
2. In `registry.js`, point your entry's `Component` at your landing screen
   and change `status` from `"planned"` to `"live"`.
3. Extra screens go in that entry's `routes` array:

   ```js
   routes: [
     { path: "/case-prep/session/:id", Component: SessionScreen },
   ]
   ```

That's the whole integration. Do not edit `App.jsx`, `Home.jsx`, or
`Navbar.jsx` — they read the registry, so editing them means your changes
and another team's conflict for no reason.

Every module route is already behind authentication, so your components
can assume a logged-in user via `useAuth()`.

**Always call the API through `src/api/client.js`:**

```js
import api from "../../api/client.js";
const { data } = await api.get("/case-prep/status");
```

It attaches the bearer token, refreshes it transparently on a 401, and
adds the `/api/v1` prefix. A bare `fetch` gets none of that, and the bug
shows up as random logouts.

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

**Every pull request runs the full suite. It must be green to merge.**
That is the only thing standing between three teams working in parallel
and a broken `main` on demo day.

```bash
cd backend && pytest        # in-memory SQLite, no services needed
cd frontend && npm test     # Vitest + React Testing Library
```

CI additionally applies the migrations to a real PostgreSQL service,
checks there is exactly one Alembic head, and runs a production frontend
build — all things a passing local suite can still get wrong.

### What to test

Put backend tests in `backend/tests/`, and frontend tests next to the code
they cover as `*.test.js` / `*.test.jsx`.

Cover at minimum:

- **Every endpoint you add** — the success path, the auth failure (401),
  and the "not yours" failure (403/404) where ownership applies.
- **Any component with a condition in it** — both branches. A component
  that only ever renders one way is not worth a test.
- **The bug you just fixed** — a test that fails before your fix and
  passes after is the only proof it is actually fixed, and the only thing
  stopping it coming back.

### Tests that protect other teams

Some existing tests are deliberately about the *shape* of the app rather
than any one feature. Do not delete them to make a change pass — if one
fails, either your change broke another team's contract, or the contract
genuinely moved and the test plus `docs/API/api-spec.md` need updating in
the same commit.

| Test | Catches |
|---|---|
| `backend/tests/test_app_wiring.py` | A module's router silently unregistered; a moved URL prefix; two teams claiming one path; a protected endpoint losing its auth dependency |
| `frontend/src/modules/registry.test.js` | A module dropped from the launcher, duplicate routes, a malformed registry entry |
| CI's single-head check | Two teams branching migrations from the same parent |

### When you change shared code

`main.py`, `core/`, `database/`, `api/v1/__init__.py`, `registry.js`,
`App.jsx`, and `client.js` are shared. Run **both** suites in full before
opening the PR, and say in the description which shared file you touched
so the other teams know to pull.

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
