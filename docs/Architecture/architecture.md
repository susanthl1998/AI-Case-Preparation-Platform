# Architecture decisions

Status: Living document — update whenever a decision below is revisited.

Every entry is a decision record: the conflict or gap, the decision, and
the reasoning, so anyone picking the code up later understands *why*, not
just *what*. Add new ADRs here rather than burying rationale in commit
messages, and take the next number in sequence.

**ADR-01 to ADR-07 came out of Module 2** (Account Management & Case
Repository, EPIC-02, Team 2), which was built first and had to resolve
conflicts between its own PRD and the product-wide Technical Requirements &
Architecture Document before code could be written. They live here rather
than in a module-local file because they constrain the whole platform: the
auth model, the case schema, and which store owns which data all cross
module boundaries. Module 1 and Module 3 should append their own.

## Data stores at a glance

The platform runs **both PostgreSQL and MongoDB**, split by data shape
rather than by owning team:

- **PostgreSQL** — accounts, profiles, sessions, case metadata, case files.
  Relational, heavily filtered, transactional.
- **MongoDB** — chat transcripts, AI evaluation results (Module 1).
  Schemaless, append-heavy, per-session.

ADR-02 explains why case metadata stayed relational even though the
architecture document originally listed it under MongoDB. The concrete
schema is in
[`../Database/database-design.md`](../Database/database-design.md).

## ADR-01: Backend framework and datastore — Supabase vs. FastAPI + Cloud SQL

**Conflict.** The Module 2 PRD
(`docs/source-materials/CaseArena_PRD_AccountMgmt_CaseRepository.docx`,
§9 Assumptions) states: *"Backend assumed to be Supabase (Postgres) with
insert-only row-level security, consistent with the team's prior sprint
work."* The product-wide
`docs/source-materials/Technical Requirements & Architecture Document.pdf`
— which applies to all three teams — specifies **Python + FastAPI** as the
primary backend framework, **Google Cloud SQL (PostgreSQL)** for accounts,
auth and sessions, deployed on **Google Cloud Run**, with GitHub Actions +
Docker for CI/CD. It does not mention Supabase anywhere.

**Decision.** Build this module on **FastAPI + SQLAlchemy + PostgreSQL**,
matching the product-wide architecture, not Supabase.

**Why.** The architecture document is the cross-team contract: Team 1 (AI
Trainer) and Team 3 (Multiplayer) are told to integrate against "the auth
interface" and "the case schema" from this module, and they were scoped
assuming the product-wide stack. Standardizing on one backend framework and
one hosting model across all three teams avoids duplicated auth
implementations and three different deployment pipelines. Supabase's
row-level security is a nice property, but it is a single-team assumption
written before the cross-team architecture doc existed; nothing in the PRD's
actual requirements (FR-01–FR-11, NFR-01–NFR-05) depends on Supabase
specifically — they depend on hashed passwords, session handling, and
per-user data isolation, all of which FastAPI + Postgres deliver directly.
Ownership checks (a user can only read/write their own profile and private
cases) are enforced in the FastAPI dependency/service layer rather than via
Postgres RLS policies — functionally equivalent for this MVP's needs, and it
keeps authorization logic in one place (Python) instead of split across the
app and the database.

**Consequence.** `backend/` is a FastAPI project with Alembic migrations
against Postgres (see `backend/README.md`). Local dev can point
`DATABASE_URL` at a Dockerized Postgres (via `docker-compose.yml`) or at
SQLite for a zero-dependency smoke test; Postgres is the target for
staging/production, matching Cloud SQL.

## ADR-02: Case repository metadata — Postgres vs. MongoDB

**Conflict.** The architecture document lists "Case repository metadata" as
a MongoDB Atlas responsibility, alongside chat history and AI evaluation
results. But the PRD's acceptance criteria for the repository (US-04)
require compound filtering (case type + difficulty + industry), keyword
search across title and tags, sorting, and a hard 2-second response target
over up to 500 cases (NFR-02) — all things a relational store with indexes
does well and a document store makes harder to guarantee.

**Decision.** Case records (title, type, difficulty, industry, tags, owner,
sharing state, file reference) live in **Postgres**, alongside users and
profiles, as the system of record for this module's CRUD and search.

**Why.** MongoDB in the architecture doc is grouped with genuinely
document-shaped, high-write, schema-flexible data (chat transcripts, AI
evaluation blobs) — not with the tightly-tagged, relationally-filtered case
records this module owns. Keeping cases in Postgres also means Team 1's
"case schema must be frozen by end of Week 2" dependency (PRD §9) is a
single, unambiguous SQL schema to freeze, not a schema split across two
databases. If Team 1's AI Trainer later needs case content in a document or
vector form (for embeddings/RAG per the architecture doc's §6), that is a
downstream projection this module's API can feed — not a reason to move the
source of truth. This module does not implement that projection; it is
Team 1's concern, and the API contract (`docs/API/api-spec.md`) exposes what
Team 1 needs to build it.

## ADR-03: Account deletion and shared cases

**Gap.** Both the PRD (§11 Risks) and the Requirements Gathering Document
(§8) flag this as an open question, with a proposed-but-unconfirmed
resolution: *"shared cases remain with an 'anonymous' contributor label."*

**Decision.** Adopted as specified, made concrete: on account deletion,
cases the user had shared to the community are retained with
`owner_deleted = true` and the API reports the contributor as `"Anonymous"`
instead of the (now-gone) user's identity. Cases that were never shared
(private-only) are hard-deleted along with the account, since no other user
has a claim on them. This is enforced in one place: the account-deletion
service function, not scattered across endpoints.

**Why.** This matches the proposal already on record in both source
documents and closes the gap rather than leaving deletion behavior
undefined, which the requirements-traceability principle in the RGD (§7 —
"no orphan requirements") argues against leaving unresolved.

## ADR-04: Signup "verification step" — mechanism

**Gap.** FR/AC for US-03 says *"an account is created and a verification
step is triggered"* but never specifies the channel (email, OTP, SMS) or
whether an unverified account can log in. The PRD's non-goals list rules out
password reset via SMS but says nothing about signup verification, and no
email-sending infrastructure appears anywhere in the architecture document.

**Decision.** Implement token-based email verification as a stub: signup
generates a verification token and a `POST /auth/verify` endpoint accepts
it; the response to signup includes the token directly (clearly marked
`dev_only`) instead of emailing it, since no transactional email service is
provisioned for the MVP. An unverified account **can** log in — verification
is tracked but not enforced as a login gate.

**Why.** Blocking login on email verification with no email service to
deliver the token would make signup a dead end, contradicting the "onboarding
completable in under 2 minutes" NFR-03 target. Returning the token directly
keeps the feature demonstrably working end-to-end for the MVP demo and
leaves a single, clearly-labeled seam (`app/services/notifications.py`) where
a real email provider drops in later without changing the auth flow.

## ADR-05: Content review queue for uploads

**Gap.** RGD §8 leaves open "whether a content review queue is needed
before v1.1." The PRD resolves this for v1.0: upload guidelines plus Admin
removal rights (FR-11) are the only controls; no pre-publication review
queue.

**Decision.** No review queue in v1.0. `is_shared` cases are visible
immediately on sharing. Admin removal (soft-delete, `is_removed = true`,
with a `removal_reason`) is the only moderation control, exactly as scoped.

**Why.** This isn't a gap this module needed to resolve — the PRD already
decided it. Recorded here only so the "no review queue" behavior reads as a
deliberate MVP scope choice if someone finds it while testing, not a missing
feature.

## ADR-06: Dashboard ordering when the case taxonomy has no Product Management types

**Gap.** FR-04 requires the dashboard to be "ordered by the user's
firm-type preference," and the one concrete example given (US-03 AC) is
*"Given a user who selected Consulting … consulting-type cases appear first."*
But the case taxonomy (`case_type`), derived in the Requirements Gathering
Document from document analysis of existing casebooks, is entirely
consulting-flavored: `PROFITABILITY`, `MARKET_ENTRY`,
`MERGERS_ACQUISITIONS`, `PRICING`, `OPERATIONS`. There is no PM-specific
case type, so "order by firm-type preference" has no direct mapping for a
user who selected Product Management.

**Decision.** Dashboard ordering is driven primarily by the optional
`case_preferences` a user picks at onboarding (e.g. `["M&A", "Pricing"]`),
matched against `case_type` — this satisfies the Consulting example
directly, since a Consulting user's preferences are naturally drawn from
the (consulting-only) taxonomy. For a Product Management user with no
matching preferences, the dashboard falls back to newest-first, and this
fallback is surfaced as a known v1.0 limitation rather than hidden behind
an invented case-type mapping.

**Why.** Inventing a "PM maps to Operations" rule (an earlier draft of this
code did exactly that) would quietly misrepresent unrelated cases as
PM-relevant with no basis in the requirements documents. Making the gap
visible is more useful to whoever picks up v1.1: the real fix is extending
the case taxonomy with PM-specific types (product sense, metrics,
guesstimates, RCA), which is a taxonomy change requiring Team 1
sign-off (schema freeze), not something this module should do unilaterally
mid-MVP.

## ADR-07: Uploaded PDFs are stored via a pluggable backend, not a fixed one

**Context.** The architecture document specifies object storage (Google
Cloud Storage) for uploaded case PDFs. In practice the storage target
changed three times in a fortnight — local disk while developing, then
bytes-in-Postgres for a zero-budget demo where every S3-compatible free
tier still wanted a card on file, and eventually managed object storage
once the platform has a hosting budget.

**Decision.** Storage is an abstraction (`Storage` ABC in
`backend/app/services/storage_service.py`) with three implementations,
chosen at runtime by `STORAGE_BACKEND`:

| Value | Backend | Use |
|---|---|---|
| `local` | Local disk | Development only |
| `database` | Bytes in Postgres (`case_files`) | Demos, no extra vendor |
| `s3` | AWS S3 or S3-compatible (R2, MinIO, GCS interop) | Production |

Nothing outside that one file knows where bytes live; the rest of the app
handles an opaque `storage_key`. Switching backends is an environment
variable plus a one-time copy of existing objects — never a schema or code
change, since `cases.storage_key` is backend-agnostic.

**Why not just pick one.** Committing to GCS would have blocked the demo
on provisioning nobody owned yet; committing to bytes-in-Postgres would
have shipped a design that does not survive real usage. The ABC costs
about thirty lines and removes the need to choose under time pressure.

**Tradeoff of `database`, stated plainly.** It is fine at demo volumes and
wrong at scale: bytes inflate the database and its backups, every download
flows through the application process, and there is no CDN. The
`DatabaseStorage` docstring says so, so nobody mistakes its convenience for
an endorsement. Move to `s3` before real traffic.

**Consequence.** Whoever provisions production sets `STORAGE_BACKEND=s3`
and migrates any `case_files` rows into the bucket. `local` must never be
used on a hosted deployment: most platforms wipe local disk on redeploy,
which silently destroys every uploaded PDF with nothing in the logs. An
unrecognized value raises at startup rather than falling back to `local`,
specifically so a typo cannot cause that failure quietly.

## Summary for integrators (Team 1 / Team 3)

- Auth: JWT bearer tokens issued by this module's `/auth/login`; see
  `docs/API/api-spec.md` for the token shape and the dependency you can
  reuse to validate them in your own FastAPI services.
- Case schema: frozen relational shape in `backend/app/models/case.py`,
  exposed read-only (for shared cases) via `GET /cases`; source of truth is
  Postgres, not MongoDB, per ADR-02 above.
- User profile: `target_firm_type` and `case_preferences` are readable via
  `GET /profile/me` once a bearer token is presented.
