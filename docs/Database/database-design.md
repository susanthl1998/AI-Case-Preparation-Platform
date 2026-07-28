# Database design

The platform uses two stores, split by data shape rather than by module:

| Store | Holds | Owner |
|---|---|---|
| **PostgreSQL** | Accounts, profiles, sessions, case metadata, case files | Module 2 (Team 2) |
| **MongoDB** | Chat transcripts, AI evaluation results | Module 1 (Team 1) |
| **Vector DB** | Embeddings for retrieval | Module 1 (Team 1) |

The source of truth for the PostgreSQL schema is
`backend/app/models/*.py` plus the Alembic migrations in
`backend/alembic/versions/`. This document explains the shape and the
reasoning; when the two disagree, the code is right and this file needs
updating.

**Why case metadata is relational, not in Mongo.** The platform
architecture document originally listed case repository metadata under
MongoDB. It is stored in PostgreSQL instead — see **ADR-02** in
[`../Architecture/architecture.md`](../Architecture/architecture.md). In
short: case rows are queried almost entirely by filter and sort
(`case_type`, `difficulty`, `industry`, keyword, "most practised"), they
join to `users` for ownership, and ownership rules are enforced
transactionally alongside account state. Splitting them into a second store
would create two sources of truth for one entity with no offsetting
benefit. Mongo remains the right home for the schemaless, append-heavy
documents Module 1 produces.

---

## PostgreSQL schema

### `users`

Authentication state only. Deliberately separate from `profiles` so "can
this user log in" stays independent of "has this user finished onboarding".

| Column | Type | Notes |
|---|---|---|
| `id` | integer PK | |
| `email` | varchar(255) | unique, indexed |
| `hashed_password` | varchar(255) | bcrypt; never plaintext (NFR-01) |
| `is_admin` | boolean | grantable only via `scripts/promote_admin.py`, no API (ADR-05) |
| `is_verified` | boolean | tracked, not enforced as a login gate in v1.0 (ADR-04) |
| `verification_token` | varchar(64), null | cleared once used |
| `failed_login_attempts` | integer | reset on successful login |
| `locked_until` | timestamptz, null | set after N consecutive failures |
| `is_deleted` | boolean | soft delete; see account deletion below |
| `created_at` / `updated_at` | timestamptz | |

### `profiles`

One row per user, created empty at signup so onboarding has something to
update.

| Column | Type | Notes |
|---|---|---|
| `id` | integer PK | |
| `user_id` | integer FK → `users.id` | unique, `ON DELETE CASCADE` |
| `target_firm_type` | enum `targetfirmtype`, null | `CONSULTING` \| `PRODUCT_MANAGEMENT`; mandatory at onboarding (FR-03) |
| `case_preferences` | JSON | list of strings, optional |
| `onboarding_completed` | boolean | |
| `created_at` / `updated_at` | timestamptz | |

### `cases`

Case metadata. **Frozen per PRD §9** — Module 1 depends on this shape, so
changes need a migration and cross-team sign-off.

| Column | Type | Notes |
|---|---|---|
| `id` | integer PK | |
| `owner_id` | integer FK → `users.id`, null | nullable so a case can outlive its owner (ADR-03) |
| `owner_deleted` | boolean | drives the "Anonymous" contributor label |
| `title` | varchar(255) | |
| `case_type` | enum `casetype` | `PROFITABILITY` \| `MARKET_ENTRY` \| `MERGERS_ACQUISITIONS` \| `PRICING` \| `OPERATIONS` \| `OTHER`; indexed |
| `difficulty` | enum `difficulty` | `EASY` \| `MEDIUM` \| `HARD`; indexed |
| `industry` | varchar(100), null | free text; indexed |
| `tags` | JSON | list of strings |
| `storage_key` | varchar(512) | opaque; meaning depends on `STORAGE_BACKEND` |
| `original_filename` | varchar(255) | |
| `file_size_bytes` | integer | |
| `is_shared` | boolean | private by default (US-04B) |
| `shared_at` | timestamptz, null | |
| `is_removed` | boolean | admin soft-delete, keeps content auditable (FR-11) |
| `removal_reason` | text, null | |
| `practice_count` | integer | incremented by Module 1 via `POST /cases/{id}/practice` |
| `created_at` / `updated_at` | timestamptz | `created_at` indexed for newest-first sort |

### `case_files`

Uploaded PDF bytes, used only when `STORAGE_BACKEND=database`.

| Column | Type | Notes |
|---|---|---|
| `id` | integer PK | |
| `storage_key` | varchar(512) | unique, indexed; matches `cases.storage_key` |
| `content` | bytea | the PDF |
| `created_at` | timestamptz | |

Kept as a **separate table**, not a column on `cases`, so that browse,
search, and filter queries never drag multi-megabyte payloads along. The
link is by `storage_key` rather than a foreign key, which keeps this table
an implementation detail of the storage layer: `cases.storage_key` means
the same opaque thing whether bytes live here, on local disk, or in S3.

---

## Cross-cutting behaviors worth knowing

**Enum type names are pinned.** Every `SAEnum` passes an explicit `name=`
(`casetype`, `difficulty`, `targetfirmtype`) so the Python enum and the
PostgreSQL native ENUM type can never drift. The migrations are
hand-written, so nothing reconciles this automatically. Adding a value
means altering the ENUM type in a migration, not just editing the Python
class.

**Account deletion keeps shared content (ADR-03).** Deleting an account
does not cascade to shared cases: the row is retained with `owner_id` set
to `NULL` and `owner_deleted = true`, so a case another student is using
does not vanish. Private cases are hard-deleted along with their bytes. The
`users` row itself is soft-deleted with credentials scrubbed, so it can
never authenticate again while foreign keys stay intact.

**Admin removal is a soft delete.** `is_removed = true` plus a
`removal_reason`, so moderation decisions stay auditable.

## MongoDB

No collections are defined yet — Module 1 owns this store. The connection
helper is `backend/app/database/mongodb.py`, configured with `MONGODB_URI`
and `MONGODB_DATABASE`.

It is **optional at runtime**: with `MONGODB_URI` unset the service still
starts and serves everything Module 2 provides, and only raises if
something actually asks for a Mongo handle. That is deliberate — an
unreachable Mongo should not be able to take down login and the case
repository.

When Module 1 defines collections, document them here alongside the
PostgreSQL tables so there is one place to look for "where does this data
live".

## Migrations

Alembic, in `backend/alembic/versions/`:

- `0001_initial_schema` — `users`, `profiles`, `cases`
- `0002_case_files` — `case_files`

```bash
cd backend
alembic upgrade head
```

Migrations are **not** run automatically when the API container boots, so a
bad migration can't be half-applied by a restart loop. Run them explicitly.

⚠️ **Shared database, three teams.** If all modules point at one PostgreSQL
instance they share one Alembic history. Before adding a migration, pull
`main` and confirm your `down_revision` points at the current head —
otherwise two teams create sibling revisions and `alembic upgrade head`
fails with "multiple heads". Agree on who applies migrations to shared
environments before the first time it matters.

The existing migrations were hand-written rather than autogenerated. Once
you have a working Alembic CLI against a real database, `alembic revision
--autogenerate` works, but always review the output: renamed columns appear
as drop+add, and `SAEnum` `name=` changes aren't detected.
