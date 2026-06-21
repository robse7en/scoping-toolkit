# Scoping Toolkit

A workflow for scoping and implementing software projects with Claude Code,
designed so that implementation work can happen across many independent,
context-limited sessions without losing the thread. Discovery, architecture,
verification, and planning happen up front with explicit human checkpoints.
Implementation happens task-by-task, each task self-contained enough that a
brand-new session can pick it up with no memory of anything that came before.

## Why this exists

Long-running AI coding sessions degrade: context fills up, earlier decisions get
forgotten, and architecture drifts task to task. This toolkit separates
deciding what to build and how from building it. Progress is tracked entirely in
markdown files committed to the repo. There is no external database and no
hidden state.

## Install

This toolkit has two parts that install differently:

- `.claude/agents/` and `.claude/commands/`: the agent and command definitions.
  Install either personally (`~/.claude/`) or per-project (`<project>/.claude/`).
- `docs/project-scope/_templates/`: the schema for generated files. This is
  always per-project because the generated files live in the target repo.
  Project-local template overrides can be placed under
  `docs/project-scope/_templates/overrides/`.

### Personal install

```bash
mkdir -p ~/.claude/agents ~/.claude/commands
cp .claude/agents/*.md ~/.claude/agents/
cp .claude/commands/*.md ~/.claude/commands/
```

Then, for each target project:

```bash
cd ~/path/to/your-project
mkdir -p docs/project-scope
cp -r ~/path/to/this-toolkit/docs/project-scope/_templates docs/project-scope/
```

Restart any open Claude Code session afterward so the new agents and commands
load.

### Project install

```text
your-project/
  .claude/
    agents/        # 10 subagent definitions
    commands/      # 8 slash commands
  docs/
    project-scope/
      _templates/  # schema every generated file conforms to
```

Copy `.claude/` and `docs/project-scope/_templates/` into the project repo root
and commit them so the team uses the same workflow definitions.

## Workflow

```text
/scope new "Visitor Management System"
        |
        |- research-agent / codebase-analyst      (research-summary.md / existing-system-context.md)
        |- interviewer                             (constraints.md)
        |- feature-suggester                       (adds approved optional features)
        |- scope-verifier (features)               (feature-necessity.md)
        |- architect-agent                         (architecture.md, decisions.md)
        |- planner                                 (phase folders, manifest.md skeleton)
        |- task-writer (per phase)                 (task files)
        |- scope-reviewer (per phase)              (parallelSafe, rework findings)
        |- scope-verifier (artifacts)              (artifact-consistency.md)
        |
        v
   /sync-manifest
        |
        v
   Manual review of architecture, decisions, manifest, verification reports, and tasks
        |
        v
   (new session) /implement P1-001   -> status: review
        |
   (same or new session) /qa P1-001  -> status: done
        |
        v
   /sync-manifest
        |
        v
   /status
```

If a coding or QA session hits a real architecture mismatch mid-project, the
task is set to `blocked` rather than worked around. You resolve it with
`/amend-architecture <task-id>`, then re-run the post-amendment review and any
needed scope verification.

## Commands

| Command | Purpose |
|---|---|
| `/scope new "<description>"` | Start scoping a brand-new project |
| `/scope extend "<description>"` | Start scoping an additional module for an existing system |
| `/implement <task-id>` | Run in a fresh session to implement one task |
| `/qa <task-id>` | The only path by which a task can reach `status: done` |
| `/amend-architecture <task-id>` | Resolve a blocked task by amending `architecture.md` |
| `/verify-scope features|artifacts|all` | Write read-only scope verification reports before implementation |
| `/converge-scope all|<task-id>` | Compare current implementation state against scoped intent |
| `/sync-manifest` | Regenerate `manifest.md` from task file frontmatter |
| `/status` | Quick human-readable progress and verification summary |

## Agents

| Agent | Role |
|---|---|
| `research-agent` | Domain research for new projects |
| `codebase-analyst` | Read-only analysis of an existing codebase for extension projects |
| `interviewer` | Asks clarifying questions and writes `constraints.md` |
| `feature-suggester` | Proposes optional features and reconciles them after verification |
| `scope-verifier` | Produces read-only reports for feature necessity, artifact consistency, and convergence |
| `architect-agent` | Only writer of `architecture.md` |
| `planner` | Breaks the project into phases and seeds the manifest |
| `task-writer` | Writes granular, session-sized task files per phase |
| `scope-reviewer` | Validates task sizing, file overlap, and parallel safety |
| `qa-reviewer` | Only agent allowed to set `status: done` |

## Generated files

| File | Written by | Notes |
|---|---|---|
| `docs/project-scope/research-summary.md` | `research-agent` | New projects only |
| `docs/project-scope/existing-system-context.md` | `codebase-analyst` | Extension projects only |
| `docs/project-scope/constraints.md` | `interviewer`, `feature-suggester` | Binding answers, including engineering principles such as YAGNI, KISS, DRY, SOLID, user scenarios, and out-of-scope |
| `docs/project-scope/architecture.md` | `architect-agent` only | Binding technical blueprint |
| `docs/project-scope/decisions.md` | `architect-agent` only | Append-only ADR log |
| `docs/project-scope/manifest.md` | `/sync-manifest` only | Generated rollup |
| `docs/project-scope/phases/phase-N-<slug>/tasks/*.md` | `task-writer`, `/implement`, `/qa`, `scope-reviewer` | One file per task |
| `docs/project-scope/verification/*.md` | `scope-verifier` only | Read-only reports for feature review, artifact consistency, and convergence |

## Task status lifecycle

```text
pending --(/implement)--> in-progress --(criteria met)--> review --(/qa pass)--> done
   ^                                               |                      |
   |                                      (architecture                   |
   |                                       mismatch found)                |
   |                                               |                      |
   +-----------------------------------------------+-------> blocked <----+
                    (/amend-architecture resolves, resets to pending)
```

Only `qa-reviewer` sets `status: done`. Only `architect-agent` resolves a
blocked architecture conflict.

## Design principles

- Single writer per file. `architecture.md` is owned by `architect-agent`,
  `manifest.md` by `/sync-manifest`, and `status: done` by `qa-reviewer`.
- Explicit over implicit. Dependencies (`dependsOn`), file conflicts
  (`touchesFiles`), architecture conformance (`architectureVersion`), and
  scenario traceability (`scenarioRefs`) are recorded instead of inferred.
- Verify before you build. Optional features are rechecked before architecture,
  and scope artifacts are rechecked before implementation starts.
- Block, do not improvise. If architecture does not fit reality, surface the
  conflict instead of silently changing course.
