---
description: Regenerate manifest.md through the deterministic project-scoped helper script. Do not hand-edit manifest.md; this command is the only writer.
allowed-tools: Bash
disable-model-invocation: true
---

Regenerate `docs/project-scope/manifest.md` by delegating all parsing,
validation, rendering, and writes to:

`docs/project-scope/_scripts/sync_manifest.py`

The helper reads the repo's constrained frontmatter format for task files. It
does not implement general YAML parsing.

1. Confirm `docs/project-scope/_scripts/sync_manifest.py` exists. If it does
   not, stop and tell the user the project-scoped helper script is missing.
2. Run:

   `python docs/project-scope/_scripts/sync_manifest.py --root .`

3. If the script exits non-zero, relay stderr verbatim and stop.
4. If the script succeeds, relay stdout verbatim.

This command must never parse constrained frontmatter itself, choose blocked reasons,
or write `manifest.md` directly.
