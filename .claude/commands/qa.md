---
description: Review a task that's in status:review, via qa-reviewer. The only path by which a task can become status:done.
argument-hint: <task-id>
disable-model-invocation: true
---

The user wants QA review for task `$ARGUMENTS`.

1. Locate the task file matching id `$ARGUMENTS`. If not found, stop and tell the user.
2. Confirm `status` is `review`. If it's anything else (`pending`, `in-progress`, `done`, `blocked`), tell the user the current status and that QA only applies to tasks in `review` — don't proceed.
3. Invoke the `qa-reviewer` subagent with the task id.
4. Relay its verdict to the user in full: pass (now done), reject (back to pending, with the specific rejection reason), or architecture conflict (now blocked, needs `/amend-architecture`).
5. If multiple tasks are ready for review, you may invoke `qa-reviewer` once per task — but always one task per invocation, never batch several tasks into a single qa-reviewer call, since each review needs its own focused verification pass against that task's specific acceptance criteria.
6. After QA completes (pass or reject), suggest running `/sync-manifest` to refresh the progress rollup.
