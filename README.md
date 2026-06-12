# rso-keel

[English] | [中文](https://github.com/yiouyou/rso-keel/blob/main/docs/zh/README.md)

Governance / provenance / orchestration for high-responsibility AI workflows.

`rso-keel` is not another agent framework, and it is not tied to one runtime. It is the accountability layer above workflow runtimes and agent frameworks:

```text
domain payload
  -> WorkflowIR
  -> validation and gates
  -> compiled graph
  -> node handlers
  -> HandlerOutput
  -> PlanProvenance
  -> WorkflowTemplate
  -> metrics and rollback
```

Use `rso-keel` when an AI workflow produces accountable work: research reviews, patent analysis, compliance findings, lab experiment cards, investment diligence, safety evaluations, or any workflow that needs provenance, human approval, reproducibility, rollback, and template hardening.

Start here:

- [Documentation index](docs/README.md)
- [Overview](docs/en/00-overview.md)
- [Why rso-keel](docs/en/01-why-rso-keel.md)
- [Quickstart](docs/en/04-quickstart.md)
- [Comparison with adjacent open-source projects](docs/en/03-comparison.md)
- [Trust Model](docs/en/06-trust-model.md)

Core primitives:

- `WorkflowIR`
- fail-closed validation
- deterministic/rules gates
- runtime compilation, currently LangGraph in RSO
- `HandlerOutput`
- `PlanProvenance`
- `HumanGate`
- `TemplateSpec`

The package has zero platform dependencies: no `app.*`, no backend models, no user database, no billing system. Host products provide auth, tenancy, storage, queues, UI, and model credentials; `rso-keel` provides the accountable workflow contract.
