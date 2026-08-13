# Domain Docs

Before exploring the codebase, engineering skills should read:

- `CONTEXT.md` at the repository root
- Relevant ADRs under `docs/adr/`

If these files do not exist, proceed silently. Domain-modeling skills create them lazily when terminology or architectural decisions are resolved.

## File structure

This repository uses the single-context layout:

```
/
├── CONTEXT.md
├── docs/adr/
└── src/
```

Use terminology defined in `CONTEXT.md`. If proposed work contradicts an existing ADR, identify the conflict explicitly rather than silently overriding the decision.
