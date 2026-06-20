---
description: Implement a single task by id. Intended to be run in a fresh Claude Code session — loads only the minimal context needed (constraints, architecture, decisions, the one task file) rather than full project history.
argument-hint: <task-id>
disable-model-invocation: true
---

The user wants to implement task `$ARGUMENTS`. This command assumes a fresh or near-fresh session — do not assume prior conversation context about this project beyond what you load here.

1. Locate the task file matching id `$ARGUMENTS` under `docs/project-scope/phases/**/tasks/`. If not found, stop and tell the user.
2. Read the task file. Check `status`:
   - If `done`: tell the user this task is already complete and ask if they meant a different task.
   - If `in-progress` or `review`: tell the user its current status and ask whether to proceed anyway (it may be a resume).
   - If `blocked`: stop. Tell the user this task is blocked and show the Architecture Conflict note — it needs `/amend-architecture`, not implementation.
   - If `pending`: proceed.
3. Check `dependsOn`. For each listed task id, confirm its status is `done`. If any dependency isn't done, stop and tell the user which dependency is incomplete — do not proceed with an unmet dependency even if the user asks you to, since that's exactly the kind of silent ordering violation this system exists to prevent. If they want to override, that's their call to make explicitly, but surface the risk clearly first.
4. Load context, in this order: `docs/project-scope/constraints.md`, `docs/project-scope/architecture.md`, `docs/project-scope/decisions.md`, then the full task file. Do not load other task files or the manifest — keep this session's context minimal and focused, per the task's own self-containment design.
5. Set the task's `status: in-progress` immediately (Edit the frontmatter) so the manifest reflects active work if synced.
6. Implement strictly within the task's Scope section. Follow `architecture.md` exactly — layering, naming/folder conventions, API conventions, multi-tenancy mechanism, all of it. Apply the user's standing preferences: SOLID, DRY, readability over cleverness.
7. If, during implementation, you discover architecture.md genuinely doesn't fit the reality of the codebase (not just "I'd prefer to do it differently," but an actual structural mismatch):
   - Stop implementing further on the conflicting part.
   - Set `status: blocked`.
   - Append to the task's "Architecture Conflict" section: what architecture.md specifies, what you're actually encountering, and (if you have one) a proposed resolution.
   - Tell the user clearly this needs `/amend-architecture $ARGUMENTS` before this task can continue. Do not work around the conflict yourself.
8. Once implementation is genuinely complete against every Acceptance Criterion:
   - Set `status: review`.
   - Append a Session Log note summarizing what was implemented and which files changed.
   - Tell the user the task is ready for `/qa $ARGUMENTS`. Do NOT set `status: done` yourself under any circumstance — that's qa-reviewer's exclusive authority, not yours, even if you're confident the work is correct.

## Hard rules

- Never touch files outside this task's Scope, even if you notice something else that "could use fixing" — note it in Session Log as an observation instead, don't act on it unprompted.
- Never set `status: done`.
- Never proceed past an unmet dependency without explicit user override.
- Never silently work around an architecture mismatch by improvising — block and escalate instead.
