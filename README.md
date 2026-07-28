# AI Case Preparation Platform

An AI-powered case-interview preparation platform for MBA students, built
as a 30-day MVP by three parallel teams in one shared repository.

| Module | Epic | Team | Status |
|---|---|---|---|
| AI Trainer | EPIC-01 | Team 1 | Scaffolded, not implemented |
| **Account Management & Case Repository** | EPIC-02 | **Team 2** | **Implemented and tested** |
| Multiplayer Group Preparation | EPIC-03 | Team 3 | Not started |

Module 2 is the foundation the other two build on: both assume a logged-in
user with a prep profile, and the AI Trainer draws its practice cases from
the repository Module 2 owns. See
[`docs/API/api-spec.md`](docs/API/api-spec.md) for exactly what it exposes.

## Tech stack

- **Backend** — Python 3.12, FastAPI, SQLAlchemy, Alembic
- **Databases** — PostgreSQL (relational: accounts, profiles, cases),
  MongoDB (documents: chat transcripts, AI evaluations)
- **Frontend** — React 18, Vite, Tailwind CSS
- **CI** — GitHub Actions (backend tests against Postgres, frontend build)

## Repository layout

```
backend/
  app/
    main.py              FastAPI app: CORS, mounts the v1 router
    api/v1/              HTTP endpoints — one file per feature area
      __init__.py          Router aggregation; where new modules register
      auth.py              Signup, login, refresh, verify        [Module 2]
      users.py             Onboarding, profile, dashboard, deletion [Module 2]
      cases.py             Case browse/search/upload/share/moderate [Module 2]
      health.py            Liveness check
      chat.py              (empty — Module 1)
      interview.py         (empty — Module 1)
    core/
      config.py            Settings, env-driven — see backend/.env.example
      constants.py         Shared enums; import the case taxonomy from here
      security.py          Password hashing, JWT issue/verify
      deps.py              get_current_user / get_current_admin
    database/
      postgres.py          SQLAlchemy engine, session, declarative Base
      mongodb.py           Mongo client (optional at runtime)
      vector_db.py         (empty — Module 1)
    models/                SQLAlchemy ORM models
    schemas/               Pydantic request/response models
    services/              Business logic, kept out of the HTTP layer
  alembic/                 Database migrations
  tests/                   Pytest suite
  scripts/                 Operational CLIs (e.g. promote_admin.py)
  seed-data/               A sample case PDF for exercising uploads
frontend/                  React SPA (see frontend/README.md)
docs/                      Architecture, API spec, database design
infra/                     Deployment configuration
```

## Quickstart

Prerequisites: Python 3.12+, Node 20+, Docker (for local Postgres/Mongo).

```bash
# Backend
cd backend
cp .env.example .env
docker compose up -d db mongo
pip install -r requirements.txt
alembic upgrade head
uvicorn app.main:app --reload     # http://localhost:8000/docs
```

```bash
# Frontend (separate terminal)
cd frontend
cp .env.example .env.local
npm install
npm run dev                       # http://localhost:5173
```

Run the backend tests with `cd backend && pytest` — they use an in-memory
SQLite database and need no running services.

## Working in this repo

Three teams share this codebase. Read
[`CONTRIBUTING.md`](CONTRIBUTING.md) before your first change — it covers
where your module's code goes, how to add endpoints without creating merge
conflicts, and the one rule about migrations that will otherwise bite
everyone at once.

## Documentation

| Document | What it covers |
|---|---|
| [`docs/API/api-spec.md`](docs/API/api-spec.md) | Endpoint contract between modules |
| [`docs/Architecture/architecture.md`](docs/Architecture/architecture.md) | Decision records (ADR-01…07) and the reasoning behind them |
| [`docs/Database/database-design.md`](docs/Database/database-design.md) | Schema, tables, and which store owns what |
| [`docs/Architecture/prd-gap-log.md`](docs/Architecture/prd-gap-log.md) | Gaps and conflicts found in the source requirements |
| [`docs/deployment.md`](docs/deployment.md) | A worked reference deployment |
| [`docs/source-materials/`](docs/source-materials/) | Original PRD, requirements doc, agile plan, architecture spec |

The FastAPI `/docs` UI is generated from the running code, so when it and
the API spec disagree, `/docs` is right and the spec needs updating.
