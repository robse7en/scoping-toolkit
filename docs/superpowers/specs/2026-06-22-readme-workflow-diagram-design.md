# README Workflow Diagram Design

## Goal

Create a polished branded infographic that explains the toolkit workflow more
clearly than the current ASCII diagram in `README.md`, while remaining easy to
read when embedded in GitHub Markdown.

## Scope

This change produces a single README-ready workflow diagram asset and the
documentation update needed to embed it. It does not change the underlying
workflow, command semantics, or agent responsibilities.

## Audience

The diagram is for readers evaluating the toolkit from the repository landing
page. It needs to communicate the workflow quickly to someone who has not yet
read the full command and agent sections.

## Content Model

The diagram should show the flow in three visually distinct stages:

1. `Scoping`
2. `Manual Review`
3. `Implementation Loop`

Within `Scoping`, the flow should show:

- `/scope new|extend`
- `research-agent / codebase-analyst`
- `interviewer`
- `feature-suggester`
- `scope-verifier (features)`
- `architect-agent`
- `planner`
- `task-writer`
- `scope-reviewer`
- `scope-verifier (artifacts)`
- `/sync-manifest`

After that, the flow should show:

- `Manual review of architecture, decisions, manifest, verification reports, and tasks`
- `(new session) /implement P1-001 -> status: review`
- `(same or new session) /qa P1-001 -> status: done`
- `/sync-manifest`
- `/status`

Two gates need extra emphasis:

- `scope-verifier` as the pre-implementation verification layer
- `qa-reviewer` as the only path to `status: done`

## Visual Design

The image should be a wide landscape infographic suitable for GitHub README
usage. Favor a clear documentation-first composition over decorative
illustration.

Design constraints:

- light background
- strong typographic hierarchy
- clean connector arrows with minimal crossing
- distinct stage bands or panels
- subtle branded color system rather than monochrome boxes
- polished, modern infographic styling
- no fake browser chrome or device mockups
- text must remain readable when the image is scaled down in GitHub

## Layout

Use a left-to-right primary reading direction.

- Stage 1: `Scoping` occupies the left and largest region because it contains
  the most steps.
- Stage 2: `Manual Review` is a compact central checkpoint panel.
- Stage 3: `Implementation Loop` occupies the right region and visually shows
  the repeatable implement -> QA -> manifest -> status path.

The scoping stage may use a vertical sub-flow within its panel as long as the
overall diagram still reads left to right across the three stages.

## Output

Produce one final PNG asset sized for README use. The file should live in a
stable repo path that can be referenced from `README.md`.

## Non-Goals

- Replacing the detailed textual workflow description in the README
- Documenting every file artifact inside the diagram
- Showing low-level branching for architecture conflicts or amendment flows
- Creating an interactive or animated asset
