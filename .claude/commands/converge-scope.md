---
description: Compare current implementation state against the scoped intent and write a read-only convergence report.
argument-hint: all|<task-id>
disable-model-invocation: true
---

The user wants to run `/converge-scope $ARGUMENTS`.

1. If `$ARGUMENTS` is empty, default to `all`.
2. Confirm `docs/project-scope/constraints.md`, `architecture.md`, and
   `decisions.md` exist.
3. If a specific task id was supplied:
   - Locate the matching task file.
   - If not found, stop and tell the user.
   - Invoke `scope-verifier` in Mode 3 with that task id.
4. If the target is `all`:
   - Invoke `scope-verifier` in Mode 3 across the current scoped implementation.
5. Relay the report summary back to the user, including counts for `missing`,
   `partial`, `contradicts`, and `unrequested`.

Hard rules:
- This command writes a convergence report only. It does not reopen tasks, edit
  scope files, or generate remediation tasks automatically.
