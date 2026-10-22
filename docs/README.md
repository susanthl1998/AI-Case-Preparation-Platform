# Documentation

| Document | What it covers |
|---|---|
| [`HANDOVER.md`](HANDOVER.md) | Module 2 state, outstanding work, and what not to undo — start here if you are picking this up |
| [`API/api-spec.md`](API/api-spec.md) | Endpoint contract between modules — read this before integrating |
| [`Architecture/architecture.md`](Architecture/architecture.md) | Decision records (ADR-01…07): what was decided and *why* |
| [`Architecture/prd-gap-log.md`](Architecture/prd-gap-log.md) | Gaps and conflicts found in the source requirements, and how each was resolved |
| [`Database/database-design.md`](Database/database-design.md) | Schema, tables, and which store owns what |
| [`../infra/README.md`](../infra/README.md) | The live environment: how deploys work, first-time setup, rollback |
| [`Sprints/sprint-plan.md`](Sprints/sprint-plan.md) | *(empty)* |
| [`UML/system-design.md`](UML/system-design.md) | *(empty)* |
| [`source-materials/`](source-materials/) | Original PRD, requirements-gathering doc, agile plan, architecture spec |

## Which document is authoritative

1. **The running code** — FastAPI's `/docs` is generated from it. When
   `/docs` and `api-spec.md` disagree, `/docs` is right and the spec needs
   fixing.
2. **`architecture.md`** for *why* something is the way it is. If the code
   contradicts an ADR, either the code is a bug or the ADR is stale — find
   out which rather than assuming.
3. **`source-materials/`** for original intent. These are the inputs, not
   the current state; where they conflict with each other,
   `prd-gap-log.md` records which way it was resolved and why.

## Keeping these current

Update docs in the **same commit** as the code:

- Endpoint added or changed → `API/api-spec.md`
- Schema changed → `Database/database-design.md`
- A non-obvious decision someone could reverse by accident → a new ADR in
  `Architecture/architecture.md`

Stale documentation is worse than none: it costs a teammate an hour before
they discover it's wrong. The ADR log especially — code shows *what*, only
the ADR shows *why*, and "why" is what stops a future teammate from undoing
a deliberate constraint.
