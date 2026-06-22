---
description: Run read-only scope verification over optional features, scope artifacts, or both, and write the resulting reports under docs/project-scope/verification.
argument-hint: features|artifacts|all
disable-model-invocation: true
---

The user wants to run `/verify-scope $ARGUMENTS`.

1. Parse `$ARGUMENTS` as one of `features`, `artifacts`, or `all`. If omitted,
   default to `all`.
2. For `features`:
   - Confirm `docs/project-scope/constraints.md` exists.
   - Confirm either `research-summary.md` or `existing-system-context.md` exists.
   - Invoke `scope-verifier` in Mode 1.
3. For `artifacts`:
   - Confirm `constraints.md`, `architecture.md`, and `decisions.md` exist.
   - Confirm at least one task file exists under `docs/project-scope/phases/**/tasks/`.
   - Invoke `scope-verifier` in Mode 2.
4. For `all`, run the applicable modes in that order: features, then artifacts.
5. Relay the report summaries back to the user, including any critical findings
   and whether implementation should pause.

Hard rules:
- This command writes verification reports only. It does not change core scope
  artifacts.
- If a required input document is missing, stop and tell the user which earlier
  workflow step is missing instead of guessing.
