# Handover — Module 2 (Account Management & Case Repository)

Written 2026-10-22 by Team 2 (Siddhesh). Last code activity on this
module: **2026-07-29**.

> **Read the dates.** Roughly three months passed between the last commit
> and this handover. Everything about the *code* below is verified against
> git. Everything about the *hosted services* is not — free tiers suspend
> or reclaim idle resources, so assume Neon, Render and Vercel all need
> re-checking before you trust them. See
> [Outstanding work](#outstanding-work).

---

## 1. Where everything is

| | |
|---|---|
| **Platform repo (current, use this)** | https://github.com/susanthl1998/AI-Case-Preparation-Platform |
| Local clone | `C:\Users\Asus\Downloads\AI-Case-Preparation-Platform` |
| **Standalone Team 2 repo (superseded)** | https://github.com/siddheshnevagi/casearena-account-case-repository |
| Local clone | `C:\Users\Asus\Downloads\Case Arena` |

Module 2 was first built in the standalone repo, then relaid out onto the
architect's structure and merged into the platform repo. **The standalone
repo is history only** — it stops at commit `6d4a7fd` and has none of the
three-module shell, the `/api/v1` prefix, or the deploy pipeline. Don't
develop there. It is worth keeping because `docs/source-materials/` holds
the original PRDs, and its `docs/INTEGRATION.md` records how the migration
was planned.

## 2. What is merged and working

All three of Team 2's pull requests are merged into `main`:

| PR | Branch | What it delivered |
|---|---|---|
| #1 | `team2/module-2-account-case-repository` | Module 2, relaid out onto the platform structure |
| #2 | `team2/three-module-shell-and-tests` | Three-module shell, frontend test suite, CI gate |
| #3 | `team2/deployment-config` | Continuous deployment pipeline, CORS for previews |

`main` also carries one commit that is **not** ours:

- `d1772e9 added master docker compose file` — Sushanth, 2026-07-29. Adds a
  root `docker-compose.yml`, `frontend/Dockerfile`, and
  `frontend/docker-compose.yml`. See
  [known issues](#4-loose-ends-in-the-current-main) — it overlaps with
  `backend/docker-compose.yml` and has a couple of gaps.

### Module 2 feature scope (implemented and tested)

- **Accounts** — signup with bcrypt-hashed passwords, login issuing JWT
  access + refresh tokens, session timeout, account lockout after 5
  consecutive failed logins, token-based verification stub (ADR-04)
- **Onboarding and profile** — mandatory target firm type
  (Consulting / Product Management), optional case preferences, editable
  afterwards
- **Dashboard** — personalised ordering driven by case preferences (FR-04,
  and ADR-06 for why it is preferences rather than firm type)
- **Case repository** — browse, keyword search (3+ chars), filter by
  type/difficulty/industry, sort by newest or most practised, empty state
  with filter reset
- **Uploads** — PDF up to 10 MB, private by default, share to community,
  withdraw, owner-only edit/delete
- **Moderation** — admin soft-removal with a reason; admin granted by CLI
  only, deliberately no API (ADR-05)
- **Account deletion** — shared cases retained and anonymised, private
  cases hard-deleted (ADR-03)

### The three-module shell

After login, users land on a launcher (`frontend/src/pages/Home.jsx`) with
three cards:

| Module | Name in app | Team | Route | State |
|---|---|---|---|---|
| 1 | CasePrep with AI | Team 1 | `/case-prep` | Placeholder, fully wired |
| 2 | CaseRepository | Team 2 | `/repository` | Implemented |
| 3 | Peer2Peer Group | Team 3 | `/peer2peer` | Placeholder, fully wired |

Modules 1 and 3 have a working route, navigation entry, authentication, a
placeholder screen carrying build instructions, and a live backend
`/status` endpoint. Their teams only need to drop code in.

## 3. How the code is organised

Two registries are the integration points. Neither requires another team
to edit shared files:

- **Backend** — `backend/app/api/v1/__init__.py` aggregates routers.
  `app/main.py` mounts that one router at `/api/v1` and never needs
  changing.
- **Frontend** — `frontend/src/modules/registry.js` declares the three
  modules and drives the launcher, the router, and the navbar.

Full conventions: [`../CONTRIBUTING.md`](../CONTRIBUTING.md).

### Things not to undo by accident

Each of these is a decision with reasoning recorded in
[`Architecture/architecture.md`](Architecture/architecture.md). If one looks
wrong, read the ADR before changing it.

| | |
|---|---|
| ADR-01 | FastAPI + Postgres, not Supabase (the PRD assumed Supabase) |
| ADR-02 | **Case metadata is in Postgres, not MongoDB** — still needs Sushanth's explicit sign-off, see §5 |
| ADR-03 | Account deletion keeps shared cases, anonymised |
| ADR-04 | Signup verification is a stub; login is not gated on it |
| ADR-05 | No content review queue in v1.0; admin removal only |
| ADR-06 | Dashboard ordering uses case preferences, not firm type |
| ADR-07 | PDF storage is pluggable: `local` / `database` / `s3` |

Two specific traps:

- **`STORAGE_BACKEND` must never be `local` on a hosted deployment.** Most
  platforms wipe the container filesystem on deploy, which silently
  destroys every uploaded PDF. An unrecognised value now raises at
  startup rather than falling back to `local`, precisely so a typo cannot
  cause this quietly.
- **All three teams share one Alembic migration history.** Two migrations
  branched from the same parent produce "multiple heads" and
  `alembic upgrade head` then fails in *every* environment. CI fails the
  PR when there is more than one head.

## 4. Loose ends in the current `main`

Found while writing this handover, all in or caused by Sushanth's
`d1772e9`. None is urgent; none is ours to fix unilaterally.

1. **Two docker-compose files.** Root `docker-compose.yml` (his, full
   stack) and `backend/docker-compose.yml` (ours, backend + databases).
   They overlap and will drift. One should be deleted — probably ours,
   since his covers more, but it needs a conversation first.
2. **No migration step in either compose file.** A fresh
   `docker compose up` gives you an API against empty tables; every
   request fails until someone runs `alembic upgrade head`. This is
   deliberate for *production* (ADR reasoning: a restart loop must not
   half-apply a migration) but is a bad first-run experience locally. A
   documented one-liner in the README would fix it.
3. **`STORAGE_BACKEND` is unset in his `api` service**, so it defaults to
   `local`. It happens to work there because `./backend:/app` is bind-
   mounted, so uploads land on the host — but it is one removed volume
   away from silent data loss, and the setting should be explicit.
4. **`frontend/Dockerfile` bakes `VITE_API_BASE_URL` at build time** with
   no build arg, so the image is pinned to `http://localhost:8000`. Fine
   for local Docker; wrong for any other environment.

## 5. Outstanding work

### Needs doing by a person, in rough priority order

- [ ] **Rotate the credentials.** The Neon PostgreSQL connection string
      and the MongoDB Atlas username/password were pasted into a chat
      transcript during development. They should be treated as exposed.
      Neon: Dashboard → Roles → Reset password. Atlas: Database Access →
      Edit user. Then update Render's env vars and the `DATABASE_URL`
      GitHub secret. **This is the one item I would not defer.**
- [ ] **Verify the hosted services still exist.** After ~3 months idle,
      check Neon (free compute suspends, and idle projects can be
      reclaimed), Render (free instances sleep and the monthly hour budget
      resets), and Vercel. Re-provision as needed from
      [`../infra/README.md`](../infra/README.md).
- [ ] **Confirm whether deployment setup was ever completed.** The
      pipeline is committed but I never saw it run end to end. It needs:
      the Render Blueprint created, the Vercel project imported with
      `VITE_API_BASE_URL` set *before* its first build, `CORS_ALLOW_ORIGINS`
      and `VERCEL_PROJECT_SLUG` set on Render, and two GitHub Actions
      secrets (`DATABASE_URL`, `RENDER_DEPLOY_HOOK`). Without the secrets
      the deploy workflow fails loudly rather than half-deploying — check
      the Actions tab to see whether it has ever succeeded.
- [ ] **Fill the live URLs into `infra/README.md`.** It has placeholders
      where the Render and Vercel URLs should be.
- [ ] **Get ADR-02 signed off.** Case metadata lives in Postgres, while
      the architecture document originally assigned it to MongoDB, and the
      skeleton carries both `postgres.py` and `mongodb.py`. Team 1 reads
      case data, so Sushanth should confirm or overrule this explicitly
      rather than discovering it later.
- [ ] **Commit `frontend/package-lock.json`.** Not committed, so CI runs
      `npm install` instead of `npm ci` — slower, and not reproducible.
      Run `npm install` locally and commit the lockfile.

### Known gaps, deliberately not done

- **Email verification is a stub** (ADR-04). Signup returns the token in
  the response instead of emailing it; there is no transactional email
  provider. The seam for one is marked in the code.
- **The 25 curated launch cases** called for in PRD §9 do not exist.
  `backend/seed-data/` holds exactly one sample case, written for testing
  the upload flow. Curating real content is a content task, not a code
  task.
- **Mongo has no collections.** The connection helper works and is
  optional at runtime; Module 1 owns what goes in it.
- **React Router v7 future-flag warnings** appear in test output. Cosmetic
  noise, not failures. Silencing them changes routing behaviour slightly,
  so it was left alone.

## 6. Running it locally

```bash
# Backend
cd backend
cp .env.example .env
docker compose up -d db mongo
pip install -r requirements.txt
alembic upgrade head
uvicorn app.main:app --reload       # http://localhost:8000/docs
```

```bash
# Frontend
cd frontend
cp .env.example .env.local
npm install
npm run dev                         # http://localhost:5173
```

Tests — both must pass before a PR can merge:

```bash
cd backend  && pytest
cd frontend && npm test
```

## 7. How a change reaches production

```
merge to main
   ├─ CI: backend tests, frontend tests, production build,
   │      single-migration-head check
   │     └─ Deploy: alembic upgrade head → POST Render deploy hook
   └─ Vercel builds and deploys the frontend
```

Render's own auto-deploy is **off** (`autoDeploy: false` in
`render.yaml`). The deploy workflow owns the ordering, because deploying
straight off a push races the migration job and new code can reach the
database before the columns it expects exist.

Rollback: Render → service → Events → redeploy a previous one; Vercel →
Deployments → Promote to Production. Neither reverses a migration, so
write migrations such that the previous release still works against the
new schema.

## 8. If you are a new maintainer, read in this order

1. [`../README.md`](../README.md) — what the platform is, the three modules
2. [`../CONTRIBUTING.md`](../CONTRIBUTING.md) — where code goes, the
   migration rule, what to test
3. [`API/api-spec.md`](API/api-spec.md) — the contract between modules
4. [`Architecture/architecture.md`](Architecture/architecture.md) — why
   things are the way they are
5. [`Database/database-design.md`](Database/database-design.md) — schema
6. [`../infra/README.md`](../infra/README.md) — deployment and the failures
   that are silent

The test suite is the best documentation of intended behaviour.
`backend/tests/test_app_wiring.py` in particular encodes the cross-module
contract: all three modules mounted, routes under `/api/v1`, no duplicate
paths, protected routes rejecting anonymous callers. Don't delete an
assertion there to make a change pass — if it fails, either the change is
wrong or the contract genuinely moved and
[`API/api-spec.md`](API/api-spec.md) needs updating in the same commit.
