# Example AI Project Layout

```text
example-agent-project/
├── AGENTS.md
├── WORKFLOW.md
├── HANDOFF.md
├── FINAL_KEEP/
│   └── README.md
├── src/
├── tests/
└── docs/
```

## Operating Pattern

1. The manager records the request and chooses the project.
2. The project lead inspects `AGENTS.md` and `WORKFLOW.md`.
3. The lead makes scoped changes.
4. The reviewer checks user-facing outputs and release risks.
5. The lead updates `HANDOFF.md`.
6. Final exports go in `FINAL_KEEP`.

## Why This Helps

- Future agents can find operating rules quickly.
- Handoffs survive context resets.
- Review gates are explicit.
- Final artifacts are separated from temporary work.
