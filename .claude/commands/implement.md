---
description: Implement a single task by id. Intended to be run in a fresh Claude Code session so only the minimal task context is loaded.
argument-hint: <task-id>
disable-model-invocation: true
---

The user wants to implement task `$ARGUMENTS`. This command assumes a fresh or
near-fresh session. Do not assume prior conversation context about this project
beyond what you load here.

1. Locate the task file matching id `$ARGUMENTS` under
   `docs/project-scope/phases/**/tasks/`. If not found, stop and tell the user.
2. Read the task file and check `status`:
   - If `done`: tell the user this task is already complete and ask if they
     meant a different task.
   - If `in-progress` or `review`: tell the user its current status and ask
     whether to proceed anyway.
   - If `blocked`: stop. Tell the user this task is blocked and show the
     Architecture Conflict note. It needs `/amend-architecture`, not
     implementation.
   - If `pending`: proceed.
3. Check `dependsOn`. For each listed task id, confirm its status is `done`. If
   any dependency is incomplete, stop and tell the user which dependency is not
   done.
4. Check for
   `docs/project-scope/verification/artifact-consistency.md`:
   - If it exists and it reports critical findings, stop and tell the user the
     scope still has blocking verification issues.
   - If it exists but is stale relative to `architecture.md` or the task file,
     warn the user and recommend `/verify-scope artifacts` before proceeding.
   - If it does not exist, warn the user that implementation is starting
     without artifact verification and ask for explicit confirmation before
     continuing.
5. Load context, in this order: `constraints.md`, `architecture.md`,
   `decisions.md`, then the full task file. Do not load other task files or the
   manifest unless needed to resolve a specific blocker.
6. Set the task's `status: in-progress` immediately so the manifest reflects
   active work if synced.
7. Implement strictly within the task's Scope section. Follow `architecture.md`
   exactly: layering, naming/folder conventions, API conventions,
   multi-tenancy mechanism, and project-specific engineering principles.
   Explicitly respect named principles such as YAGNI, KISS, DRY, SOLID, and
   any one-line explainability preference captured in `constraints.md`.
8. If, during implementation, you discover `architecture.md` genuinely does not
   fit reality:
   - Stop implementing further on the conflicting part.
   - Set `status: blocked`.
   - Append to the task's `Architecture Conflict` section: what `architecture.md`
     specifies, what you are actually encountering, and any proposed
     resolution.
   - Tell the user clearly this needs `/amend-architecture $ARGUMENTS` before
     the task can continue.
9. Once implementation is genuinely complete against every Acceptance
   Criterion:
   - Set `status: review`.
   - Append a Session Log note summarizing what was implemented and which files
     changed.
   - Tell the user the task is ready for `/qa $ARGUMENTS`.

## Hard rules

- Never touch files outside this task's Scope, even if you notice something
  else that could use fixing. Note it in Session Log instead.
- Never set `status: done`.
- Never proceed past an unmet dependency without explicit user override.
- Never silently work around an architecture mismatch by improvising.
