# Infrastructure

Deployment configuration for the platform.

## Current state

Nothing is provisioned yet — hosting is still being chosen. What exists
today:

| Piece | Where | Status |
|---|---|---|
| API container image | [`../backend/Dockerfile`](../backend/Dockerfile) | Works; reads `$PORT`, so it runs on Cloud Run / Render / Fly as-is |
| Local dev stack | [`../backend/docker-compose.yml`](../backend/docker-compose.yml) | Postgres + Mongo + API |
| CI | [`../.github/workflows/ci.yml`](../.github/workflows/ci.yml) | Tests and build on every PR |
| A worked deployment | [`../docs/deployment.md`](../docs/deployment.md) | Verified zero-cost option, usable as a reference |

## What a deployment needs

Four things, whatever the provider:

1. **PostgreSQL** — accounts, profiles, case metadata. Connection string
   must use the `postgresql+psycopg2://` scheme; most providers hand you
   `postgresql://`, which SQLAlchemy will reject.
2. **MongoDB** — optional until Module 1 ships. The API starts fine
   without it.
3. **A container host** for `backend/Dockerfile`. It binds `$PORT` if set,
   else 8000, and exposes `/health` for health checks — deliberately
   outside the `/api/v1` prefix so a future `/api/v2` doesn't break probes.
4. **Static hosting** for the frontend build (`npm run build` → `dist/`).

### Environment variables

Full list in [`../backend/.env.example`](../backend/.env.example). The ones
that must not keep their defaults:

| Variable | Why |
|---|---|
| `DATABASE_URL` | SQLite default is for local smoke tests only |
| `JWT_SECRET_KEY` | The default is public in this repo — anyone with it can mint valid tokens |
| `STORAGE_BACKEND` | `local` loses every uploaded PDF on redeploy (see below) |
| `CORS_ALLOW_ORIGINS` | Must list the deployed frontend's origin, or every API call is blocked |

### Two things that fail quietly

**Uploaded PDFs on local disk.** `STORAGE_BACKEND=local` writes to the
container filesystem, which nearly every platform wipes on redeploy or
restart. Uploads appear to work and then vanish, with nothing in the logs.
Use `database` (bytes in Postgres — no extra vendor) or `s3` (AWS S3 or
S3-compatible; the right answer at real volume). See ADR-07.

**Frontend API URL.** `VITE_API_BASE_URL` is baked into the static bundle
at **build time**, not read at runtime. It has to be set before the build;
changing it afterwards does nothing until you rebuild.

### Migrations

Run `alembic upgrade head` against the target database as a deploy step —
never automatically on container start, so a bad migration can't be
half-applied by a restart loop. If the host has no shell, run it from any
machine that can reach the database:

```bash
cd backend
DATABASE_URL='postgresql+psycopg2://...' alembic upgrade head
```

## When you pick a provider

Add its configuration here (Terraform, `render.yaml`, Cloud Run YAML,
whatever it is) and replace this section with the real runbook: how to
deploy, how to roll back, and where the logs are. Keep
`docs/deployment.md` as the worked example it is, or delete it once this
directory has the real thing.
