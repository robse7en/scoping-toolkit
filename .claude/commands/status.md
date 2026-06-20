---
description: Print a human-friendly progress summary by reading the current manifest.md. The fast way to orient at the start of any new session.
allowed-tools: Read, Bash
disable-model-invocation: true
---

Read `docs/project-scope/manifest.md` and present a concise, human-friendly progress summary. Do not regenerate the manifest yourself — if it looks stale (check `Last synced` against recent git activity, e.g. `git log -1 --format=%cd`), tell the user to run `/sync-manifest` first rather than silently trusting possibly-outdated data.

Present:
1. Overall progress: total tasks, done count, percentage.
2. Per-phase breakdown, one line each: phase name, done/total, and whether it's fully complete.
3. Blocked tasks, called out prominently if any exist — these need user attention before more work can proceed on them.
4. A suggested next action: if there are pending tasks with all dependencies met and `parallelSafe: true`, name a few candidates the user could run `/implement` on next. If everything in the current phase is done, suggest moving to the next phase. If everything is blocked, say so plainly and point at `/amend-architecture`.

Keep this conversational and brief — this is meant to be glanced at, not read like a report.
