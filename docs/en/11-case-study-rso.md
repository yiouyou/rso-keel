# Case Study: RSO Migration to rso-keel

This case study summarizes how RSO moved from parallel legacy runners and opt-in Keel paths to a single `rso-keel` orchestration architecture.

This public case study keeps the reusable architecture lessons. Internal PR history, production configuration, and deployment details are intentionally omitted from the initial open-source repository.

## Starting Point

RSO had multiple background task paths:

- legacy review runner
- opt-in Keel review path
- reference import path
- patent workflow path
- lab experiment proposal path

The long-term risk was not whether each path could run. The risk was split lifecycle semantics:

- separate provenance
- separate progress/generated file handling
- inconsistent billing/model usage
- inconsistent resume ownership checks
- scattered fallback behavior
- no unified template lifecycle

## Migration Strategy

The target architecture:

```text
TaskJob
  -> WorkflowTemplate or WorkflowIR
  -> rso-keel graph
  -> registered handlers
  -> unified provenance / billing / progress / generated_files
```

The strategy:

- fix ownership and resume safety first
- make legacy runners handlers
- unify handler output
- introduce plan records and template hashes
- switch review/reference/patent/lab to default `rso-keel`
- add metrics, rollback, and CI gates

## Production Result

As of 2026-06-11:

- review/reference/patent/lab default to `rso-keel`
- legacy runners are handlers or fallback paths
- HumanGate resume is ownership-safe
- generated files, billing, and provenance use one contract
- jobs can bind immutable WorkflowTemplate versions/hashes
- rollout metrics and admin diagnostics exist
- full backend DB CI, `rso-keel` package tests, and frontend checks are green

## Lesson

`rso-keel` is not a toy abstraction. It was shaped by production migration pressure: ownership, resume, provenance, billing, generated files, fallback, rollback, template reuse, and CI coverage.
