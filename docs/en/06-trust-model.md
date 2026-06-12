# Trust Model

`rso-keel` does not prove model outputs are true. It proves the workflow chain of custody.

## Trust Boundary

`rso-keel` does not trust:

- free-form prompts
- model-generated plans
- client-provided template hashes
- handler-specific private output shapes
- claims without sources
- resume requests without ownership checks

It trusts objects that passed host authorization and `rso-keel` contracts:

- authorized domain payloads
- server-side adapters
- `WorkflowIR`
- validation and gates
- server-side template registry records
- `HandlerOutput`
- `PlanProvenance`
- HumanGate decisions

## Chain of Custody

```text
authenticated actor
  -> authorized domain payload
  -> server-side adapter
  -> WorkflowIR
  -> validator
  -> deterministic/rules gates
  -> compiled runtime graph
  -> registered node handlers
  -> HandlerOutput
  -> PlanProvenance
  -> generated artifacts
  -> metrics
  -> TemplateSpec or rollback
```

## What It Proves

`rso-keel` proves:

- which workflow version ran
- which policies were active
- which nodes ran
- which handler outputs were produced
- which model usage was recorded
- which artifacts were generated
- which human decisions occurred
- which template/version/hash was used
- whether fallback or rollback happened

It does not prove the scientific, medical, legal, or financial conclusion is correct. That remains a domain validation problem.
