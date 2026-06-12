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

If an AI workflow produces a research review, patent analysis, compliance finding, lab experiment card, investment memo, or safety assessment, the system must answer:

- What inputs did it use?
- Which sources support each claim?
- Which workflow version ran?
- Which model and tools were used?
- Which steps required human approval?
- What files were generated?
- What did it cost?
- Can this workflow be reused?
- Can it be rolled back by template version?

## Documentation

- [00 Overview](docs/en/00-overview.md)
- [01 Why rso-keel](docs/en/01-why-rso-keel.md)
- [02 When to Use](docs/en/02-when-to-use.md)
- [03 Comparison](docs/en/03-comparison.md)
- [04 Quickstart](docs/en/04-quickstart.md)
- [05 Architecture](docs/en/05-architecture.md)
- [06 Trust Model](docs/en/06-trust-model.md)
- [07 Building Harnesses](docs/en/07-building-harnesses.md)
- [08 Integrations](docs/en/08-integrations.md)
- [09 Evaluation](docs/en/09-evaluation.md)
- [10 FAQ](docs/en/10-faq.md)
- [11 RSO Case Study](docs/en/11-case-study-rso.md)
- [12 Deep Rationale](docs/en/12-deep-rationale.md)

## Core Primitives

- `WorkflowIR`
- fail-closed validation
- deterministic/rules gates
- runtime compilation
- `HandlerOutput`
- `PlanProvenance`
- `HumanGate`
- `TemplateSpec`

The package has zero platform dependencies: no `app.*`, no backend models, no user database, no billing system. Host products provide auth, tenancy, storage, queues, UI, and model credentials; `rso-keel` provides the accountable workflow contract.
