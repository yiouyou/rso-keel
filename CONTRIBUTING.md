# Contributing to rso-keel

Thanks for helping improve `rso-keel`.

This project is an accountability layer for high-responsibility AI workflows. It is intentionally small, platform-independent, and strict about provenance, validation, human approval, template versioning, and rollback semantics.

## Ways to Contribute

Good first contributions include:

- Documentation fixes.
- Examples that show how to embed `rso-keel` in a host product.
- Tests for validation, provenance, HumanGate, or template behavior.
- Small improvements to existing schemas, validators, compiler behavior, or gates.
- Bug reports with minimal reproducible examples.

Please open an issue first for larger changes, especially anything that changes public schemas, node kinds, policy semantics, or package dependencies.

## Development Setup

Install dependencies and run tests with:

```bash
uv run --extra dev python -m pytest
```

The expected result is that all tests pass.

## Pull Request Checklist

Before opening a PR:

- Run `uv run --extra dev python -m pytest`.
- Keep the import boundary intact: `src/keel/` must not import host platform code.
- Add or update tests for behavior changes.
- Keep validation fail-closed.
- Update docs when changing public concepts.
- Keep English and Chinese documentation structurally aligned when navigation or core claims change.
- Do not include secrets, private deployment details, internal hostnames, IP addresses, private emails, test accounts, or RSO platform runbooks.

## Architecture Boundaries

`rso-keel` is not a host application. It does not own:

- authentication
- tenancy
- billing
- UI
- deployment
- model credentials
- product-specific storage
- backend/frontend platform code

Host products provide those pieces. `rso-keel` provides reusable workflow contracts:

- `WorkflowIR`
- fail-closed validation
- deterministic/rules gates
- runtime compilation
- `HandlerOutput`
- `PlanProvenance`
- `HumanGate`
- `TemplateSpec`

## Node Kinds and Schema Changes

`WorkflowIR v1` currently has exactly six node kinds:

- `workspace_read`
- `literature_search`
- `independent_critic`
- `synthesis`
- `human_approval`
- `report_write`

These are the v1 minimal safety core for accountable knowledge workflows. They are not meant to be a universal workflow ontology.

Do not add a new node kind casually. A new node kind requires:

- a schema version decision
- schema updates
- validator updates
- compiler updates
- provenance updates
- tests
- docs
- a clear explanation of why existing node kinds cannot safely express the use case

Most domain-specific behavior should be implemented as registered skills, host adapters, node handlers, or handler payloads.

## Documentation

The public docs are bilingual:

- English: `docs/en/`
- Chinese: `docs/zh/`
- English entrypoint: `README.md`
- Chinese entrypoint: `docs/zh/README.md`

The wording does not need to be line-for-line identical, but structure and claims should stay aligned. If a new public concept is added in one language, add the corresponding entry in the other language.

## AI Coding Agents

If you are using Codex, Claude Code, Cursor, Copilot, or another coding agent, make sure it reads `AGENTS.md` before editing. That file contains stricter machine-oriented rules for repository boundaries and forbidden changes.

