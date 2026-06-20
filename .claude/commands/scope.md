---
description: Entry point. Scope a new project or an additional module for an existing system, running discovery, interview, feature suggestion, architecture, planning, and task-writing in sequence with user checkpoints.
argument-hint: new|extend "<project or module description>"
disable-model-invocation: true
---

The user invoked `/scope $ARGUMENTS`. Parse the first word as the mode (`new` or `extend`) and the rest as the project/module description. If the mode is missing or invalid, ask the user to clarify before proceeding — do not guess.

Run the following pipeline. Each numbered step is a checkpoint: summarize what the subagent produced and confirm with the user before moving to the next step, except where noted as fully automatic.

## If mode = new

1. Invoke `research-agent` with the project description. Show the user the summary it reports.
2. Invoke `interviewer`, pointing it at `docs/project-scope/research-summary.md`. This step will involve back-and-forth via `AskUserQuestion` — let it run to completion.
3. Confirm `docs/project-scope/constraints.md` has no unresolved "Open Questions" before continuing. If it does, surface them to the user directly and ask how to resolve before proceeding.
4. Invoke `feature-suggester`. This also involves user interaction — let it complete.
5. Invoke `architect-agent` (Mode 1: Initial Architecture). Show the user the summary, including the layering and multi-tenancy approach chosen.
6. Invoke `planner`. Show the user the phase list for sanity-check. Ask explicitly: "Does this phase breakdown look right before I generate granular tasks?" Wait for confirmation or adjustment requests.
7. For each phase planner created, invoke `task-writer` (one invocation per phase, these can run in parallel as separate subagent calls since each phase folder is independent).
8. For each phase, invoke `scope-reviewer` (Mode 1) after its tasks are written. If it flags tasks needing rework, report this to the user and offer to re-invoke `task-writer` for just those tasks.
9. Invoke `/sync-manifest` to generate the manifest rollup.
10. Tell the user the plan is ready for manual review: point them to `docs/project-scope/architecture.md`, `decisions.md`, `manifest.md`, and the phase task folders. Explicitly state that implementation should only begin (via `/implement <task-id>` in a NEW session) after they've reviewed these files — do not offer to start implementing in this same session.

## If mode = extend

1. Invoke `codebase-analyst` with the module description and the current working directory as the repo to analyze. Show the user the summary.
2. Invoke `interviewer`, pointing it at `docs/project-scope/existing-system-context.md` instead of a research summary.
3. Continue with steps 3-10 exactly as in the `new` path above.

## Hard rules for this command

- Never skip a checkpoint to save time, even if the user seems eager to move fast — each checkpoint exists because a downstream agent depends on the upstream one being genuinely correct, not just complete.
- Never invoke `architect-agent` before `constraints.md` is fully resolved.
- Never invoke `planner` before `architecture.md` exists.
- Never invoke `task-writer` for a phase before `planner` has created that phase's folder.
- If any subagent reports a blocker (e.g. research-agent says the description is too vague, or architect-agent says constraints.md is insufficient), stop the pipeline and surface it to the user directly rather than trying to push through.
