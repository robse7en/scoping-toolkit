---
description: Resolve a blocked task's architecture conflict by invoking architect-agent to review and (if approved) amend architecture.md
argument-hint: <task-id>
disable-model-invocation: true
---

The user wants to resolve a blocked task via architecture amendment. Task id: $ARGUMENTS

Steps:
1. Locate the task file matching id `$ARGUMENTS` under `docs/project-scope/phases/**/tasks/`.
2. Confirm its `status` is `blocked` and it has a non-empty "Architecture Conflict" section. If not blocked for architecture reasons, stop and tell the user this command is only for architecture conflicts — other blocks should be handled directly.
3. Invoke the `architect-agent` subagent in Mode 2 (Amend Architecture), passing the task id.
4. Relay the architect's proposed diff (or "no amendment needed" verdict) to the user and wait for explicit approval before any file is written. The subagent itself will hold for approval — do not approve on the user's behalf.
5. After the architect-agent completes, remind the user to run the scope-reviewer sweep (you can offer to invoke it) to check whether other tasks are invalidated by this change.
6. Once the sweep is complete, suggest `/verify-scope artifacts` because any architecture change can stale the previous artifact verification report.
