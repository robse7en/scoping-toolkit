---
id: P0-000
phase: 0
title: ""
status: pending          # pending | in-progress | review | done | blocked
dependsOn: []             # list of task ids, e.g. [P1-001, P1-002]
touchesFiles: []          # best-effort glob/path list, used for parallel-safety checks
parallelSafe: false       # set by scope-reviewer after overlap check, not task-writer
architectureVersion: 1    # version of architecture.md this task was written against
scenarioRefs: []          # optional list of scenario ids, e.g. [US1, US2]
---

## Objective

> One paragraph: what this task accomplishes and why, in plain language.
> A coding agent with NO other context besides constraints.md, architecture.md,
> decisions.md, and this file should be able to start immediately.

## Scope

> Explicit boundaries. What this task DOES include and, just as importantly,
> what it does NOT include (to prevent scope creep into adjacent tasks).

## Relevant Architecture References

> Pointers into architecture.md sections this task must conform to
> (e.g. "Multi-Tenancy Implementation", "API Conventions").

## Relevant Scenario References

> Scenario ids from constraints.md that this task directly advances
> (e.g. US1, US2). Keep this aligned with frontmatter `scenarioRefs`.
- 

## Acceptance Criteria

> Mechanically checkable by qa-reviewer. Avoid subjective criteria.
- [ ]
- [ ]
- [ ]

## Implementation Notes

> Optional: hints, gotchas, things task-writer or architect flagged in advance.

---

## Session Log

> Appended to by implement sessions and qa-reviewer. Never edited retroactively,
> only appended.

### Architecture Conflict (if any)
> If a coding session hits a mismatch between architecture.md and reality,
> it appends here, sets status: blocked, and stops. Resolved only via
> /amend-architecture.
-

### Rejection History
> qa-reviewer appends here on reject, with reason. Status resets to pending.
-
