# Evaluation

An `rso-keel` harness should be evaluated as a workflow system, not only as a model output.

## Four Layers

```text
Layer 1: Structural correctness
Layer 2: Execution reliability
Layer 3: Output accountability
Layer 4: Production adoption
```

## Structural Correctness

Check:

- schema parse
- validator rules
- DAG correctness
- allowed skills
- cost ceiling
- network policy
- required HumanGate
- no free-code conditional edges

## Execution Reliability

Check:

- handler registry
- checkpoint/resume
- owner/project resume checks
- generated files
- model usage
- runtime cost guard
- fallback provenance

## Output Accountability

Check:

- artifact -> job -> plan id
- plan id -> IR hash
- template id/version/content hash
- node traces
- source ids
- warnings and limitations
- HumanGate decision

## Production Adoption

Check:

- template lifecycle
- template-level rollback
- domain-level rollback
- rollout metrics
- auto-bind gate
- success rate vs baseline
- cost delta vs baseline

## Release Gate

Before default rollout:

- structural tests pass
- integration tests pass
- at least one live e2e pass
- provenance completeness is high
- resume success rate is acceptable
- fallback tested
- rollback tested
- owner signs off

Do not use “CI is green” as a substitute for production rollout metrics.
