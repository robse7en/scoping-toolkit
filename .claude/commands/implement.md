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
2. Confirm the git worktree is clean before changing files. This clean worktree
   preflight supports implementation drift detection:
   - Run `git status --porcelain`.
   - If any output exists, stop and tell the user `/implement` requires a clean
     worktree so final drift detection can attribute changed files to this task.
   - Ask the user to commit, stash, or otherwise resolve existing worktree
     changes before running `/implement $ARGUMENTS` again.
3. Read the task file and check `status`:
   - If `done`: tell the user this task is already complete and ask if they
     meant a different task.
   - If `in-progress` or `review`: tell the user its current status and ask
     whether to proceed anyway.
   - If `blocked`: stop. Tell the user this task is blocked and show the
     Architecture Conflict note. It needs `/amend-architecture`, not
     implementation.
   - If `pending`: proceed.
4. Check `dependsOn`. For each listed task id, confirm its status is `done`. If
   any dependency is incomplete, stop and tell the user which dependency is not
   done.
5. Check for `docs/project-scope/verification/artifact-consistency.md`:
   - Read the verification report frontmatter, not just the prose body.
   - If `criticalFindings` is greater than zero, stop and tell the user the
     scope still has blocking verification issues.
   - Treat the report as stale if any of these are true:
     - `architectureVersionChecked` does not match the current
       `architecture.md` version
     - the current task file is missing from `taskPathsChecked`
     - `generatedAt` predates the last modification time of `architecture.md`
       or the current task file
   - If the report is stale, warn the user and recommend
     `/verify-scope artifacts` before proceeding.
   - If the report does not exist, warn the user that implementation is
     starting without artifact verification and ask for explicit confirmation
     before continuing.
6. Load context, in this order: `constraints.md`, `architecture.md`,
   `decisions.md`, then the full task file. Do not load other task files or the
   manifest unless needed to resolve a specific blocker.
7. Set the task's `status: in-progress` immediately so the manifest reflects
   active work if synced.
8. Implement strictly within the task's Scope section. Follow `architecture.md`
   exactly: layering, naming/folder conventions, API conventions,
   multi-tenancy mechanism, and project-specific engineering principles.
   Explicitly respect named principles such as YAGNI, KISS, DRY, SOLID, and
   any one-line explainability preference captured in `constraints.md`.
9. If, during implementation, you discover `architecture.md` genuinely does not
   fit reality:
   - Stop implementing further on the conflicting part.
   - Set `status: blocked`.
   - Append to the task's `Architecture Conflict` section: what `architecture.md`
     specifies, what you are actually encountering, and any proposed
     resolution.
   - Tell the user clearly this needs `/amend-architecture $ARGUMENTS` before
     the task can continue.
10. Once implementation is genuinely complete against every Acceptance
   Criterion, run every test/build/check named or implied by the Acceptance
   Criteria before any review transition.
11. Run final implementation drift detection:
   - Run `git diff --name-only HEAD` and keep the changed file list.
   - Invoke `scope-verifier` in `implementation-drift-gate` mode for
     `$ARGUMENTS`, passing the changed file list.
   - The verifier writes a timestamped
     `docs/project-scope/verification/implementation-drift-$ARGUMENTS-<timestamp>.md`
     report with machine-readable frontmatter.
   - Read the report frontmatter, not just the prose body.
   - If `blockingFindings` is greater than zero, leave the task `in-progress`,
     append a Session Log note naming the drift report and summarizing the
     blocking count, tell the user review is blocked by implementation drift,
     and stop.
   - If `warningFindings` is greater than zero and `blockingFindings` is zero,
     report the warning count and continue to review.
12. If implementation is genuinely complete, all required checks pass, and the
   implementation drift gate has zero blocking findings:
   - Set the task's `status: review`.
   - Append a Session Log note summarizing what was implemented and which files
     changed, and name the implementation drift report that was checked.
   - Tell the user the task is ready for `/qa $ARGUMENTS`.

## Hard rules

- Never touch files outside this task's Scope, even if you notice something
  else that could use fixing. Note it in Session Log instead.
- Never set `status: done`.
- Never proceed past an unmet dependency without explicit user override.
- Never silently work around an architecture mismatch by improvising.
- Never move a task to `review` when the implementation drift gate reports
  blocking findings.
