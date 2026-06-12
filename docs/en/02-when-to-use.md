# When to Use rso-keel

Use `rso-keel` when an AI workflow output becomes formal work.

Do not use it for every prompt.

## Use It When

Use `rso-keel` when the workflow needs any of these:

- formal decision support
- source and evidence traceability
- reproducibility
- human approval
- durable resume
- generated artifact tracking
- template reuse
- production rollout metrics
- fallback and rollback

Typical domains:

- research review
- patent analysis
- compliance review
- medical quality control
- investment diligence
- engineering change review
- safety assessment
- lab experiment recommendation

## Do Not Use It When

Do not use `rso-keel` for:

- one-off low-risk chat
- creative drafting
- simple summarization
- internal throwaway utilities
- deterministic code paths that do not need AI
- cases where plain schema validation is enough

## Scoring Rule

Score each item from 0 to 2:

| Question | 0 | 1 | 2 |
|---|---|---|---|
| Does the output affect formal decisions? | no | indirectly | directly |
| Does it need evidence traceability? | no | partly | always |
| Does it need human approval? | no | sometimes | required |
| Does it need reproducibility? | no | on failure | always |
| Will it be repeated? | one-off | low frequency | recurring |
| Should it become a template? | no | project-level | cross-project |
| Does it need rollback? | no | manual | built-in |
| What is the error cost? | low | medium | high |

Suggested interpretation:

- 0-4: do not use `rso-keel`
- 5-8: prototype first, migrate later if the workflow becomes formal
- 9-12: use `rso-keel` for a narrow workflow
- 13+: use `rso-keel` from the beginning

## Decision Rule

The question is not “is this task complex?”

The question is:

> Does this AI workflow need to be accountable?

If yes, use `rso-keel`.
