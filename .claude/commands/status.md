---
description: Print a human-friendly progress summary by reading the current manifest.md plus any available scope verification reports.
allowed-tools: Read, Bash
disable-model-invocation: true
---

Read `docs/project-scope/manifest.md` and present a concise, human-friendly
progress summary. Do not regenerate the manifest yourself. If it looks stale
(check `Last synced` against recent git activity), tell the user to run
`/sync-manifest` first rather than silently trusting outdated data.

Also check for these reports if they exist:
- `docs/project-scope/verification/feature-necessity.md`
- `docs/project-scope/verification/artifact-consistency.md`
- latest `docs/project-scope/verification/convergence-*.md`

Present:
1. Overall progress: total tasks, done count, percentage.
2. Per-phase breakdown, one line each: phase name, done/total, and whether it
   is fully complete.
3. Blocked tasks, called out prominently if any exist.
4. Verification status, if reports exist:
   - latest feature verification result summary
   - latest artifact verification critical findings count
   - latest convergence report summary
5. A suggested next action:
   - if artifact verification has critical findings, recommend `/verify-scope artifacts`
     or task/architecture rework first
   - otherwise, if there are pending tasks with all dependencies met and
     `parallelSafe: true`, name a few candidates the user could run
     `/implement` on next
   - if everything in the current phase is done, suggest moving to the next
     phase
   - if everything is blocked, say so plainly and point at
     `/amend-architecture` or `/verify-scope`

Keep this conversational and brief. It is meant to be glanced at, not read like
a report.
