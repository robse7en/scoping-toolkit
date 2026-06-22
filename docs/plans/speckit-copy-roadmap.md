# Incremental Spec Kit Adaptation Plan

## Summary

Create this handoff file first, then incrementally adopt Spec Kit ideas that
improve scoping quality without replacing this toolkit's single-task execution
model. Keep the toolkit Claude-first and Markdown/YAML-only.

Adopt: project-specific engineering principles, user-scenario traceability,
feature necessity verification, cross-artifact consistency analysis,
implementation-to-scope convergence reporting, and template overrides.

Defer: a Python CLI, installer/upgrader flows, multi-agent integration catalogs,
presets/extensions/bundles, GitHub issue generation, and batch implementation.

## Implementation Changes

- Add `Engineering Principles` and `User Scenarios & Success Criteria` to
  `constraints.md`, and treat both as binding scope inputs.
- Add optional `scenarioRefs` to task frontmatter and task body so work can be
  traced back to user scenarios.
- Add a new `scope-verifier` agent with three read-only reporting modes:
  `features`, `artifacts`, and `convergence`.
- Add `/verify-scope` and `/converge-scope` commands.
- Update `/scope` to verify optional features before architecture and verify
  artifact consistency after task generation.
- Update `/implement` to respect artifact verification reports before coding.
- Update `/status` to surface verification state alongside task progress.
- Support project-local template overrides via
  `docs/project-scope/_templates/overrides/`.

## Verification Rules

- Feature verification classifies approved optional features as `Keep`,
  `Reconfirm`, or `Drop`.
- Artifact verification reports unresolved questions, placeholders, missing
  coverage, stale architecture versions, unverifiable criteria, and task graph
  issues.
- Convergence reports classify implementation findings as `missing`, `partial`,
  `contradicts`, or `unrequested`.

## Assumptions

- Verification reports are committed project artifacts, not ephemeral logs.
- Existing task files without `scenarioRefs` remain valid.
- Scope reports do not directly rewrite core scope files; they inform the
  existing single-writer agents and user checkpoints.
