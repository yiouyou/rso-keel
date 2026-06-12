# AGENTS.md

Instructions for AI coding agents working in this repository.

## Project Boundary

`rso-keel` is a platform-independent Python package for accountable AI workflows.

It must stay independent from any host product:

- Do not import `app.*`, `backend.*`, frontend code, database models, billing code, user systems, deployment scripts, or private RSO platform modules.
- Host products provide auth, tenancy, storage, queues, UI, model credentials, and deployment.
- `rso-keel` provides workflow contracts: `WorkflowIR`, validation, gates, `HandlerOutput`, `PlanProvenance`, `HumanGate`, `TemplateSpec`, metrics, and rollback semantics.

The import boundary is intentional. Do not weaken it to make a test pass.

## Architecture Rules

1. Keep `src/keel/` pure and reusable.
2. `WorkflowIR v1` has exactly six node kinds:
   - `workspace_read`
   - `literature_search`
   - `independent_critic`
   - `synthesis`
   - `human_approval`
   - `report_write`
3. Treat those six node kinds as the v1 minimal safety core for accountable knowledge workflows, not as a universal workflow ontology.
4. Do not add a node kind unless the change bumps `schema_version` and updates schema, validator, compiler, provenance, tests, and docs.
5. Do not embed arbitrary Python, JavaScript, shell, prompt code, or free-form executable conditions in `WorkflowIR`.
6. New executable behavior should enter through registered skills, node handlers, or host-provided adapters, not through dynamic code in the IR.
7. Handler results must use `HandlerOutput`; do not invent per-handler output shapes.
8. Provenance, HumanGate, and template version/hash are core contracts, not optional logging.

## Tests

Run:

```bash
uv run --extra dev python -m pytest
```

Before submitting changes, make sure:

- All tests pass.
- Import-boundary tests still pass.
- New behavior has focused tests.
- Validation failures are fail-closed.
- Markdown links still resolve if docs changed.

## Documentation

The docs are bilingual:

- English docs live in `docs/en/`.
- Chinese docs live in `docs/zh/`.
- Root `README.md` is the English entrypoint.
- `docs/zh/README.md` is the Chinese entrypoint.

When changing public concepts, keep English and Chinese documentation structurally aligned. The wording can differ naturally, but the navigation and major claims should not drift.

Do not add internal RSO platform details to this public repository:

- No production hostnames, IPs, deployment paths, credentials, test accounts, private emails, or cloud configuration.
- No private backend/frontend file maps.
- No internal migration runbooks unless they have been explicitly rewritten as public architecture guidance.

## Style

- Prefer small, explicit changes.
- Preserve type safety.
- Do not suppress errors with `# type: ignore` or equivalent unless there is a narrow, documented reason.
- Do not add dependencies without a clear need.
- Keep comments useful and sparse.
- Keep public language precise: `rso-keel` is an accountability layer, not a replacement for workflow runtimes or agent frameworks.

