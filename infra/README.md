# Infrastructure

The live environment, and how to deploy to it.

| Piece | Service | Plan | Deploys on |
|---|---|---|---|
| API | Render (Docker) | Free | CI success on `main`, via `.github/workflows/deploy.yml` |
| Frontend | Vercel | Hobby | Push, via Vercel's GitHub integration |
| PostgreSQL | Neon | Free | — |
| MongoDB | Atlas | Free | — |
| PDF storage | The PostgreSQL database (`STORAGE_BACKEND=database`) | — | — |

Fill in the URLs once the services exist:

- **App:** _(Vercel production URL)_
- **API:** _(Render URL)_ · docs at `/docs` · health at `/health`

## How a change reaches production

```
merge to main
   └─ CI (tests, build, single-migration-head check)
        └─ Deploy workflow  ── alembic upgrade head
                            └─ POST Render deploy hook
   └─ Vercel builds and deploys the frontend
```

Render's own auto-deploy is **off** (`autoDeploy: false` in `render.yaml`).
That's deliberate: deploying straight off a push races the migration job,
and new code can reach the database before the columns it expects exist.
The workflow owns the order — migrate, then release — and neither happens
if CI failed.

## First-time setup

Do these in order; each step needs a value the previous one produced.

### 1. Database

Use the existing Neon database. The connection string Neon shows you starts
`postgresql://`; SQLAlchemy needs the driver named explicitly, so change it
to **`postgresql+psycopg2://`** and keep everything else, including
`?sslmode=require`.

### 2. Backend — Render

1. **render.com** → **New +** → **Blueprint** → this repository. It reads
   `render.yaml` and prompts for the values marked `sync: false`.
2. Set:
   | Variable | Value |
   |---|---|
   | `DATABASE_URL` | the Neon string from step 1 |
   | `JWT_SECRET_KEY` | `python3 -c "import secrets; print(secrets.token_urlsafe(48))"` |
   | `CORS_ALLOW_ORIGINS` | `["https://<your-vercel-app>.vercel.app"]` — placeholder until step 3 |
   | `VERCEL_PROJECT_SLUG` | your Vercel project name, e.g. `ai-case-prep` |
   | `MONGODB_URI` | leave blank until Module 1 needs it |
3. Deploy, then check `<render-url>/health` returns `{"status":"ok"}`.

### 3. Frontend — Vercel

1. **vercel.com/new** → import this repository.
2. **Root Directory:** `frontend`. Framework preset auto-detects as Vite;
   the default build command and output directory are correct.
3. Environment variable, set **before** the first build:
   ```
   VITE_API_BASE_URL = https://<your-render-url>
   ```
   Host only, no path — `/api/v1` is appended in `src/api/client.js`.

   Vite bakes `VITE_*` values into the bundle at build time. Changing this
   later does nothing until you redeploy.
4. Deploy, then go back to Render and set `CORS_ALLOW_ORIGINS` to the real
   Vercel URL.

### 4. GitHub secrets

**Settings → Secrets and variables → Actions:**

| Secret | Where to find it |
|---|---|
| `DATABASE_URL` | Same Neon string as Render (with `+psycopg2`) |
| `RENDER_DEPLOY_HOOK` | Render → your service → Settings → Deploy Hook |

Without both, the deploy workflow fails loudly rather than half-deploying.

### 5. Verify the pipeline

Merge a trivial change to `main` and watch **Actions**: CI runs, then
Deploy runs, then Render shows a new deploy. That's the whole loop working.

## Operating notes

**Cold starts.** Render's free tier sleeps after 15 minutes idle and takes
about a minute to wake. For casual testing that's just a wait; before a
demo, open `<render-url>/health` five minutes ahead. A free pinger
(cron-job.org) every 10 minutes keeps it awake, but a permanently-awake
service uses ~730 of the 750 free instance-hours per month — enough for
this one service, with no headroom for a second. Ping during working hours
rather than around the clock.

**PR previews.** Vercel builds a preview for every pull request at its own
hostname. `VERCEL_PROJECT_SLUG` is what lets those previews call the API:
the backend matches the project's whole hostname family via
`allow_origin_regex`, so nobody has to add each branch URL to CORS by hand.
The regex is anchored and scoped to the project slug — see
`backend/tests/test_cors.py` for what it deliberately rejects.

Previews share the production database. Treat them as a way to see a UI
change, not as an isolated environment.

**Rollback.**
- API: Render → service → **Events** → redeploy the last good deploy.
- Frontend: Vercel → **Deployments** → pick a previous one → **Promote to
  Production**.

Both take under a minute. Neither reverses a migration — write migrations
so the previous release still works against the new schema (add columns,
don't rename or drop in the same release as the code change).

**Secrets.** Nothing real belongs in this repository; it is public. Render
and GitHub Actions secrets are the only homes for credentials. If one
leaks, rotate it in Neon/Render rather than editing history.

## Things that fail quietly

| Symptom | Cause |
|---|---|
| Uploads work, then PDFs vanish after a deploy | `STORAGE_BACKEND=local` — Render wipes the filesystem on deploy. Must be `database` (or `s3`). |
| Frontend loads, every API call fails | `CORS_ALLOW_ORIGINS` doesn't list the frontend's origin, or `VERCEL_PROJECT_SLUG` is unset for previews |
| Frontend still calls the old API URL | `VITE_API_BASE_URL` changed without a rebuild — it is baked in at build time |
| `alembic upgrade head` fails with "multiple heads" | Two teams branched migrations from the same parent. CI catches this on the PR; see CONTRIBUTING.md. |
| API returns 500s right after a deploy | Code released before its migration — check the Deploy workflow actually ran |

## Moving to Google Cloud later

The product architecture document targets Cloud SQL, Cloud Storage and
Cloud Run. Nothing here blocks that: the API is a plain Docker container
reading `$PORT`, the database is standard PostgreSQL, and object storage is
one environment variable away (`STORAGE_BACKEND=s3`, which GCS supports via
its S3 interoperability mode). Replace this document with the GCP runbook
when that happens rather than keeping both.
