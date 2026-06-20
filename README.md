# Claude Code Scoping Toolkit

A workflow for scoping and implementing software projects with Claude Code, designed so that
implementation work can happen across many independent, context-limited sessions without losing
the thread. Discovery, architecture, and planning happen once, up front, with explicit human
checkpoints. Implementation happens task-by-task, each task self-contained enough that a brand-new
session can pick it up with no memory of anything that came before.

## Why this exists

Long-running AI coding sessions degrade: context fills up, earlier decisions get forgotten,
architecture drifts task to task. This toolkit separates **deciding what to build and how** (once,
reviewable, version-controlled) from **building it** (many short, focused sessions, each scoped to
one task). Progress is tracked entirely in markdown files committed to the repo — no external
database, no hidden state.

## Install

Copy `.claude/` and `docs/project-scope/_templates/` into the root of your project repository.
That's it — no dependencies beyond Claude Code itself.

```
your-project/
  .claude/
    agents/        # 9 subagent definitions
    commands/       # 6 slash commands
  docs/
    project-scope/
      _templates/   # schema every generated file conforms to
```

Commit `.claude/` and the templates to version control so your whole team uses the same agents.

## The workflow, end to end

```
/scope new "Visitor Management System"
        │
        ├─ research-agent / codebase-analyst   (research-summary.md / existing-system-context.md)
        ├─ interviewer                          (constraints.md)
        ├─ feature-suggester                    (adds to constraints.md, with your approval)
        ├─ architect-agent                      (architecture.md, decisions.md)
        ├─ planner                              (phase folders, manifest.md skeleton)
        ├─ task-writer  (per phase)              (task files)
        └─ scope-reviewer (per phase)            (validates sizing, sets parallelSafe)
        │
        ▼
   /sync-manifest
        │
        ▼
   *** YOU manually review architecture.md, decisions.md, manifest.md, and the task files ***
        │
        ▼
   (new session) /implement P1-001   →  status: review
        │
   (same or new session) /qa P1-001  →  status: done  (or rejected back to pending)
        │
        ▼
   /sync-manifest   (repeat for every task)
        │
        ▼
   /status   (check progress any time, from any session)
```

If a coding or QA session hits a real architecture mismatch mid-project, the task is set to
`blocked` rather than worked around. You resolve it with:

```
/amend-architecture P3-007
```

which invokes `architect-agent` to propose a diff to `architecture.md` — nothing is written without
your explicit approval — and then prompts a `scope-reviewer` sweep to catch any other tasks
(including already-`done` ones) that the change might invalidate.

## Commands

| Command | Purpose |
|---|---|
| `/scope new "<description>"` | Start scoping a brand-new project |
| `/scope extend "<description>"` | Start scoping an additional module for an existing system |
| `/implement <task-id>` | Run in a fresh session to implement one task |
| `/qa <task-id>` | The only path by which a task can reach `status: done` |
| `/amend-architecture <task-id>` | Resolve a blocked task by amending `architecture.md` |
| `/sync-manifest` | Regenerate `manifest.md` from task file frontmatter (deterministic, no model judgment) |
| `/status` | Quick human-readable progress summary |

## Agents

| Agent | Role |
|---|---|
| `research-agent` | Domain research for new projects (web search) |
| `codebase-analyst` | Read-only analysis of an existing codebase, for extension projects |
| `interviewer` | Asks clarifying questions, writes `constraints.md` |
| `feature-suggester` | Proposes optional features, with user approval required for each |
| `architect-agent` | **Only** writer of `architecture.md`. Initial design, or amendments via `/amend-architecture` |
| `planner` | Breaks the project into phases, seeds the manifest |
| `task-writer` | Writes granular, session-sized task files per phase |
| `scope-reviewer` | Validates task sizing, checks file-overlap conflicts, sets `parallelSafe`, sweeps for invalidated tasks after architecture amendments |
| `qa-reviewer` | **Only** agent allowed to set `status: done`. Runs builds/tests, checks acceptance criteria, rejects with specific reasons or blocks on architecture conflicts |

## Generated files (per project)

| File | Written by | Notes |
|---|---|---|
| `docs/project-scope/research-summary.md` | `research-agent` | New projects only |
| `docs/project-scope/existing-system-context.md` | `codebase-analyst` | Extension projects only |
| `docs/project-scope/constraints.md` | `interviewer`, `feature-suggester` | Binding answers: stack, multi-tenancy, security, out-of-scope |
| `docs/project-scope/architecture.md` | `architect-agent` only | Binding technical blueprint. Versioned. |
| `docs/project-scope/decisions.md` | `architect-agent` only | Append-only ADR log |
| `docs/project-scope/manifest.md` | `/sync-manifest` only | Generated rollup — never hand-edit |
| `docs/project-scope/phases/phase-N-<slug>/tasks/*.md` | `task-writer`, edited by `/implement`, `/qa`, `scope-reviewer` | One file per task |

## Task status lifecycle

```
pending ──(/implement)──▶ in-progress ──(criteria met)──▶ review ──(/qa pass)──▶ done
   ▲                                          │                      │
   │                                    (architecture                │
   │                                     mismatch found)              (/qa reject,
   │                                          │                       with reason)
   │                                          ▼                       │
   └──────────────────────────────────  blocked ◀─────────────────────┘
              (/amend-architecture resolves, resets to pending)
```

Only `qa-reviewer` sets `status: done`. Only `architect-agent` (via `/amend-architecture`) resolves
a `blocked` architecture conflict. No other agent is permitted to write either of those things,
by design — this is what keeps the audit trail trustworthy across dozens of independent sessions.

## Design principles this toolkit follows

- **Single writer per file.** `architecture.md` ← `architect-agent` only. `status: done` ←
  `qa-reviewer` only. `manifest.md` ← `/sync-manifest` only. No two agents fight over the same
  fact.
- **Explicit over implicit.** Dependencies (`dependsOn`), file conflicts (`touchesFiles`), and
  architecture conformance (`architectureVersion`) are all explicit frontmatter fields, not
  inferred at read time.
- **Block, don't improvise.** When a coding session hits something architecture.md doesn't cover,
  it stops and surfaces the conflict rather than making a judgment call that the next session won't
  know about.
- **Human checkpoints at every irreversible step.** Architecture, phase breakdown, and feature
  additions all require explicit approval before downstream agents build on them.
