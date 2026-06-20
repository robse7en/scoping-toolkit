---
description: Regenerate manifest.md by reading frontmatter from every task file. Deterministic — do not hand-edit manifest.md, this command is the only writer.
allowed-tools: Bash, Read, Write, Glob
disable-model-invocation: true
---

Regenerate `docs/project-scope/manifest.md` from the actual frontmatter in every file under `docs/project-scope/phases/**/tasks/*.md`. This must be a faithful, mechanical transformation — do not editorialize, summarize subjectively, or omit any task.

1. Use Glob to find every task file under `docs/project-scope/phases/*/tasks/*.md`.
2. Read each file's YAML frontmatter: `id`, `phase`, `title`, `status`, `dependsOn`, `touchesFiles`, `parallelSafe`, `architectureVersion`.
3. Read the current `architecture.md` to get its `Version` field for the manifest header.
4. Build the manifest following the exact structure in `docs/project-scope/_templates/manifest.template.md`:
   - **Summary table**: one row per phase, with counts of pending/in-progress/review/done/blocked.
   - **Blocked Tasks table**: every task with `status: blocked`, across all phases, with its id, phase, title, and the most recent blocking reason (pull from the task's "Architecture Conflict" or relevant Session Log note — whichever is more recent/relevant).
   - **Per-phase tables**: one table per phase folder, listing every task with id, title, status, dependsOn, parallelSafe.
5. Set `Last synced` to the current date/time and `Architecture version` to the value read in step 3.
6. Write the result to `docs/project-scope/manifest.md`, overwriting the previous version entirely.
7. Report a one-line summary to the user: total tasks, how many done, how many blocked (call out blocked tasks specifically since they need attention).

This command should be run after any task status change — after `/implement` completes a task, after `/qa` reviews one, after `/amend-architecture` blocks/unblocks tasks. It can also be run any time the user just wants a fresh progress view.
