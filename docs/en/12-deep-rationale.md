# Deep Rationale

## Core Argument

AI for Science and agentic R&D are moving from model demonstrations to production platforms. Systems such as Microsoft Discovery, FutureHouse Robin, Google DeepMind Co-Scientist, AI Scientist-v2, AgentRxiv, and AlphaFold-style domain models show that AI can increasingly generate hypotheses, search literature, analyze evidence, and coordinate experiments.

But research is not coding.

Coding has cheap executable verifiers: compilers, tests, CI, containers, and benchmarks such as SWE-bench. Scientific and other high-responsibility workflows often have expensive, delayed, noisy, or institutionally mediated verification.

That means high-responsibility AI systems need a stronger external structure:

- source binding
- evidence trails
- hypothesis status
- human review
- experiment or action cards
- provenance
- rollback
- workflow hardening
- cross-project memory with authorization

## Why rso-keel

As models improve, prompt tricks and shallow orchestration become less defensible. The durable value is the accountability layer:

- typed workflow IR
- fail-closed validation
- HumanGate
- provenance
- template lifecycle
- metrics and rollback

`rso-keel` is designed to be that layer.

It does not compete with frontier models or automated scientist systems. It lets their outputs enter formal work safely.
