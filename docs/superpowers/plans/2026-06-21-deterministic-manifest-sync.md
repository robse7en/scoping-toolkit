# Deterministic Manifest Synchronization Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Replace model-generated manifest synchronization with a validated, dependency-free Python generator that produces stable Markdown and never overwrites a valid manifest from invalid inputs.

**Architecture:** A project-scoped Python module discovers task files, parses the toolkit's constrained frontmatter format into immutable task records, validates the complete dependency graph, and renders the existing manifest layout in stable order. A small CLI writes through a same-directory temporary file and atomically replaces the manifest only after successful validation; the Claude command becomes a thin launcher.

**Tech Stack:** Python 3.9+ standard library (`argparse`, `dataclasses`, `datetime`, `pathlib`, `re`, `tempfile`, `unittest`), Markdown command/templates, PowerShell contract validation.

---

## File Map

- Create `docs/project-scope/_scripts/sync_manifest.py`: parsing, validation, rendering, atomic writing, and CLI entry point.
- Create `tests/test_sync_manifest.py`: end-to-end unit tests using temporary project fixtures.
- Modify `.claude/commands/sync-manifest.md`: invoke the script and relay its exact result.
- Modify `README.md`: install `_scripts`, document Python prerequisite, and identify executable generation.
- Modify `CLAUDE.md`: document the runtime/test suite and script ownership.
- Reuse `tests/validate-agent-contracts.ps1`: existing full-suite static contract check.

### Task 1: Parse valid project state and render stable Markdown

**Files:**
- Create: `tests/test_sync_manifest.py`
- Create: `docs/project-scope/_scripts/sync_manifest.py`

- [ ] **Step 1: Write the valid-project and deterministic-order tests**

Create `tests/test_sync_manifest.py` with fixture helpers that write a temporary
`architecture.md` and task files. The first tests must import `generate_manifest`
and assert exact ordering, status counts, blocked-reason extraction, and identical
bytes for a fixed timestamp:

```python
import importlib.util
import sys
import tempfile
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
SCRIPT_PATH = REPO_ROOT / "docs/project-scope/_scripts/sync_manifest.py"


def load_sync_module():
    spec = importlib.util.spec_from_file_location("sync_manifest", SCRIPT_PATH)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def task_text(*, task_id, phase, title, status="pending", depends_on="[]",
              touches_files="[]", parallel_safe="false", architecture_version=3,
              conflict="-"):
    return f"""---
id: {task_id}
phase: {phase}
title: {title}
status: {status}
dependsOn: {depends_on}
touchesFiles: {touches_files}
parallelSafe: {parallel_safe}
architectureVersion: {architecture_version}
---

## Objective

Fixture task.

## Session Log

### Architecture Conflict (if any)
{conflict}

### Rejection History
-
"""


class ManifestFixture:
    def __init__(self, root):
        self.root = Path(root)
        scope = self.root / "docs/project-scope"
        scope.mkdir(parents=True)
        (scope / "architecture.md").write_text(
            "# Architecture\n\n**Version:** 3\n", encoding="utf-8"
        )

    def add_task(self, phase_folder, filename, **values):
        task_dir = self.root / "docs/project-scope/phases" / phase_folder / "tasks"
        task_dir.mkdir(parents=True, exist_ok=True)
        (task_dir / filename).write_text(task_text(**values), encoding="utf-8")


class GenerateManifestTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.sync = load_sync_module()

    def test_renders_counts_tasks_and_blocked_reason_in_stable_order(self):
        with tempfile.TemporaryDirectory() as directory:
            fixture = ManifestFixture(directory)
            fixture.add_task(
                "phase-2-reporting", "P2-002.md", task_id="P2-002", phase=2,
                title="Export report", status="blocked", depends_on="[P1-001]",
                conflict="- Architecture requires a report store that does not exist.",
            )
            fixture.add_task(
                "phase-1-foundation", "P1-001.md", task_id="P1-001", phase=1,
                title="Create foundation", status="done", parallel_safe="true",
            )

            output = self.sync.generate_manifest(
                Path(directory), timestamp="2026-06-21T01:02:03Z"
            )

            self.assertIn("**Last synced:** 2026-06-21T01:02:03Z", output)
            self.assertIn("**Architecture version:** 3", output)
            self.assertIn("| 1 — Foundation | 1 | 0 | 0 | 0 | 1 | 0 |", output)
            self.assertIn("| 2 — Reporting | 1 | 0 | 0 | 0 | 0 | 1 |", output)
            self.assertIn(
                "| P2-002 | 2 | Export report | Architecture requires a report store that does not exist. |",
                output,
            )
            self.assertLess(output.index("## Phase 1"), output.index("## Phase 2"))
            self.assertLess(output.index("P1-001"), output.index("P2-002"))

    def test_fixed_timestamp_produces_identical_bytes(self):
        with tempfile.TemporaryDirectory() as directory:
            fixture = ManifestFixture(directory)
            fixture.add_task(
                "phase-1-foundation", "P1-001.md", task_id="P1-001", phase=1,
                title="Create foundation",
            )
            first = self.sync.generate_manifest(Path(directory), "fixed")
            second = self.sync.generate_manifest(Path(directory), "fixed")
            self.assertEqual(first.encode("utf-8"), second.encode("utf-8"))


if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 2: Run the tests and verify RED**

Run:

```powershell
python -m unittest tests.test_sync_manifest -v
```

Expected: error loading `docs/project-scope/_scripts/sync_manifest.py` because the
generator does not exist.

- [ ] **Step 3: Implement parsing, normalization, and rendering**

Create `docs/project-scope/_scripts/sync_manifest.py`. Implement these public and
internal interfaces:

```python
#!/usr/bin/env python3
from __future__ import annotations

import argparse
import os
import re
import sys
import tempfile
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterable, Optional

VALID_STATUSES = ("pending", "in-progress", "review", "done", "blocked")
REQUIRED_FIELDS = (
    "id", "phase", "title", "status", "dependsOn", "touchesFiles",
    "parallelSafe", "architectureVersion",
)


class ManifestError(ValueError):
    pass


@dataclass(frozen=True)
class Task:
    path: Path
    task_id: str
    phase: int
    phase_name: str
    title: str
    status: str
    depends_on: tuple[str, ...]
    touches_files: tuple[str, ...]
    parallel_safe: bool
    architecture_version: int
    blocked_reason: str


def strip_inline_comment(value: str) -> str:
    quote = None
    escaped = False
    for index, character in enumerate(value):
        if escaped:
            escaped = False
            continue
        if character == "\\" and quote:
            escaped = True
            continue
        if character in ("'", '"'):
            quote = None if quote == character else character if quote is None else quote
            continue
        if character == "#" and quote is None and (index == 0 or value[index - 1].isspace()):
            return value[:index].rstrip()
    return value.strip()


def parse_scalar(value: str) -> str:
    value = strip_inline_comment(value)
    if len(value) >= 2 and value[0] == value[-1] and value[0] in ("'", '"'):
        return value[1:-1]
    return value


def parse_list(value: str, field: str, path: Path) -> tuple[str, ...]:
    value = strip_inline_comment(value)
    if not (value.startswith("[") and value.endswith("]")):
        raise ManifestError(f"{path}: {field} must be an inline list")
    body = value[1:-1].strip()
    if not body:
        return ()
    return tuple(parse_scalar(item.strip()) for item in body.split(","))


def parse_frontmatter(text: str, path: Path) -> dict[str, str]:
    lines = text.splitlines()
    if not lines or lines[0].strip() != "---":
        raise ManifestError(f"{path}: missing opening frontmatter delimiter")
    try:
        closing = next(index for index, line in enumerate(lines[1:], 1) if line.strip() == "---")
    except StopIteration as error:
        raise ManifestError(f"{path}: missing closing frontmatter delimiter") from error
    values = {}
    for line in lines[1:closing]:
        if not line.strip() or line.lstrip().startswith("#"):
            continue
        if ":" not in line:
            raise ManifestError(f"{path}: malformed frontmatter line: {line}")
        key, value = line.split(":", 1)
        key = key.strip()
        if key in values:
            raise ManifestError(f"{path}: duplicate frontmatter field {key}")
        values[key] = value.strip()
    missing = [field for field in REQUIRED_FIELDS if field not in values]
    if missing:
        raise ManifestError(f"{path}: missing fields: {', '.join(missing)}")
    return values


def positive_int(value: str, field: str, path: Path) -> int:
    try:
        number = int(strip_inline_comment(value))
    except ValueError as error:
        raise ManifestError(f"{path}: {field} must be a positive integer") from error
    if number < 1:
        raise ManifestError(f"{path}: {field} must be a positive integer")
    return number


def conflict_reason(text: str) -> str:
    match = re.search(
        r"(?ms)^### Architecture Conflict[^\n]*\n(?P<body>.*?)(?=^#{2,3} |\Z)", text
    )
    if not match:
        return "Not documented"
    for line in match.group("body").splitlines():
        candidate = line.strip()
        if not candidate or candidate.startswith(">") or candidate == "-":
            continue
        return candidate.removeprefix("- ").strip()
    return "Not documented"


def parse_task(path: Path) -> Task:
    text = path.read_text(encoding="utf-8")
    values = parse_frontmatter(text, path)
    folder_match = re.fullmatch(r"phase-(\d+)-(.+)", path.parent.parent.name)
    if not folder_match:
        raise ManifestError(f"{path}: parent folder must match phase-N-slug")
    phase = positive_int(values["phase"], "phase", path)
    folder_phase = int(folder_match.group(1))
    if phase != folder_phase:
        raise ManifestError(f"{path}: phase {phase} does not match folder phase {folder_phase}")
    status = parse_scalar(values["status"])
    if status not in VALID_STATUSES:
        raise ManifestError(f"{path}: invalid status {status}")
    boolean = strip_inline_comment(values["parallelSafe"]).lower()
    if boolean not in ("true", "false"):
        raise ManifestError(f"{path}: parallelSafe must be true or false")
    return Task(
        path=path,
        task_id=parse_scalar(values["id"]),
        phase=phase,
        phase_name=folder_match.group(2).replace("-", " ").title(),
        title=parse_scalar(values["title"]),
        status=status,
        depends_on=parse_list(values["dependsOn"], "dependsOn", path),
        touches_files=parse_list(values["touchesFiles"], "touchesFiles", path),
        parallel_safe=boolean == "true",
        architecture_version=positive_int(values["architectureVersion"], "architectureVersion", path),
        blocked_reason=conflict_reason(text),
    )


def architecture_version(root: Path) -> int:
    path = root / "docs/project-scope/architecture.md"
    if not path.is_file():
        raise ManifestError(f"{path}: file not found")
    match = re.search(r"(?m)^\*\*Version:\*\*\s*(\d+)\s*$", path.read_text(encoding="utf-8"))
    if not match or int(match.group(1)) < 1:
        raise ManifestError(f"{path}: missing positive integer Version")
    return int(match.group(1))


def escape_cell(value: object) -> str:
    return str(value).replace("|", "\\|").replace("\r", " ").replace("\n", " ")


def render_manifest(tasks: list[Task], version: int, timestamp: str) -> str:
    lines = [
        "# Manifest", "",
        "> AUTO-GENERATED by `/sync-manifest`. Do not hand-edit — changes will be",
        "> overwritten. Source of truth is the frontmatter in `phases/**/tasks/*.md`.",
        "", f"**Last synced:** {timestamp}", f"**Architecture version:** {version}", "",
        "## Summary", "",
        "| Phase | Total | Pending | In Progress | Review | Done | Blocked |",
        "|---|---|---|---|---|---|---|",
    ]
    phases = sorted({task.phase for task in tasks})
    for phase in phases:
        phase_tasks = [task for task in tasks if task.phase == phase]
        name = phase_tasks[0].phase_name
        counts = {status: sum(task.status == status for task in phase_tasks) for status in VALID_STATUSES}
        lines.append(
            f"| {phase} — {escape_cell(name)} | {len(phase_tasks)} | {counts['pending']} | "
            f"{counts['in-progress']} | {counts['review']} | {counts['done']} | {counts['blocked']} |"
        )
    lines.extend(["", "## Blocked Tasks (needs attention)", "", "| Task ID | Phase | Title | Reason |", "|---|---|---|---|"])
    for task in tasks:
        if task.status == "blocked":
            lines.append(
                f"| {escape_cell(task.task_id)} | {task.phase} | {escape_cell(task.title)} | "
                f"{escape_cell(task.blocked_reason)} |"
            )
    for phase in phases:
        phase_tasks = [task for task in tasks if task.phase == phase]
        lines.extend([
            "", f"## Phase {phase} — {phase_tasks[0].phase_name}", "",
            "| Task ID | Title | Status | Depends On | Parallel Safe |",
            "|---|---|---|---|---|",
        ])
        for task in phase_tasks:
            dependencies = ", ".join(task.depends_on) if task.depends_on else "—"
            lines.append(
                f"| {escape_cell(task.task_id)} | {escape_cell(task.title)} | {task.status} | "
                f"{escape_cell(dependencies)} | {str(task.parallel_safe).lower()} |"
            )
    return "\n".join(lines) + "\n"
```

Add `generate_manifest` after these helpers:

```python
def load_tasks(root: Path) -> list[Task]:
    root = root.resolve()
    task_paths = sorted(root.glob("docs/project-scope/phases/phase-*/tasks/*.md"))
    if not task_paths:
        raise ManifestError("no task files found under docs/project-scope/phases")
    tasks = sorted((parse_task(path) for path in task_paths), key=lambda task: (task.phase, task.task_id))
    validate_tasks(tasks)
    return tasks


def generate_manifest(root: Path, timestamp: Optional[str] = None) -> str:
    root = root.resolve()
    tasks = load_tasks(root)
    effective_timestamp = timestamp or datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z")
    return render_manifest(tasks, architecture_version(root), effective_timestamp)
```

Define this initial `validate_tasks`; Task 2 extends it with cycle detection:

```python
def validate_tasks(tasks: list[Task]) -> None:
    by_id = {}
    for task in tasks:
        if not task.task_id:
            raise ManifestError(f"{task.path}: id must not be empty")
        if task.task_id in by_id:
            raise ManifestError(f"duplicate task id {task.task_id}")
        by_id[task.task_id] = task
    for task in tasks:
        for dependency in task.depends_on:
            if dependency == task.task_id:
                raise ManifestError(f"{task.task_id} depends on itself")
            if dependency not in by_id:
                raise ManifestError(f"{task.task_id} depends on unknown task {dependency}")
```

- [ ] **Step 4: Run the focused tests and verify GREEN**

Run:

```powershell
python -m unittest tests.test_sync_manifest.GenerateManifestTests -v
```

Expected: 2 tests pass.

- [ ] **Step 5: Commit parser and renderer**

```powershell
git add -- tests/test_sync_manifest.py docs/project-scope/_scripts/sync_manifest.py
git commit -m "Add deterministic manifest renderer"
```

### Task 2: Reject invalid task graphs and preserve existing output

**Files:**
- Modify: `tests/test_sync_manifest.py`
- Modify: `docs/project-scope/_scripts/sync_manifest.py`

- [ ] **Step 1: Add failing validation and atomic-write tests**

Add tests that create duplicate IDs, unknown dependencies, self-dependencies,
cycles, invalid status, and mismatched phase folders. Add this preservation test:

```python
    def test_validation_failure_does_not_replace_existing_manifest(self):
        with tempfile.TemporaryDirectory() as directory:
            fixture = ManifestFixture(directory)
            fixture.add_task(
                "phase-1-foundation", "P1-001.md", task_id="P1-001", phase=1,
                title="Broken task", status="invalid",
            )
            manifest = Path(directory) / "docs/project-scope/manifest.md"
            manifest.write_text("existing manifest\n", encoding="utf-8")

            with self.assertRaises(self.sync.ManifestError):
                self.sync.synchronize(Path(directory), timestamp="fixed")

            self.assertEqual("existing manifest\n", manifest.read_text(encoding="utf-8"))
```

Use `subTest` over explicit fixture configurations and expected message fragments
so each invalid case checks a specific diagnostic.

- [ ] **Step 2: Run tests and verify RED**

Run:

```powershell
python -m unittest tests.test_sync_manifest -v
```

Expected: failures for missing cycle detection and missing `synchronize`.

- [ ] **Step 3: Complete graph validation**

Implement `validate_tasks` with stable duplicate/dependency diagnostics and a
three-state depth-first traversal:

```python
def validate_tasks(tasks: list[Task]) -> None:
    by_id = {}
    for task in tasks:
        if not task.task_id:
            raise ManifestError(f"{task.path}: id must not be empty")
        if task.task_id in by_id:
            raise ManifestError(f"duplicate task id {task.task_id}")
        by_id[task.task_id] = task
    for task in tasks:
        for dependency in task.depends_on:
            if dependency == task.task_id:
                raise ManifestError(f"{task.task_id} depends on itself")
            if dependency not in by_id:
                raise ManifestError(f"{task.task_id} depends on unknown task {dependency}")

    state = {}
    stack = []

    def visit(task_id: str) -> None:
        if state.get(task_id) == "done":
            return
        if state.get(task_id) == "visiting":
            start = stack.index(task_id)
            cycle = stack[start:] + [task_id]
            raise ManifestError(f"dependency cycle: {' -> '.join(cycle)}")
        state[task_id] = "visiting"
        stack.append(task_id)
        for dependency in by_id[task_id].depends_on:
            visit(dependency)
        stack.pop()
        state[task_id] = "done"

    for task_id in sorted(by_id):
        visit(task_id)
```

- [ ] **Step 4: Add atomic synchronization**

Implement `synchronize` so the temporary file lives beside the destination and
is deleted on failure:

```python
def synchronize(root: Path, timestamp: Optional[str] = None) -> tuple[int, int, int]:
    root = root.resolve()
    tasks = load_tasks(root)
    effective_timestamp = timestamp or datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z")
    content = render_manifest(tasks, architecture_version(root), effective_timestamp)
    destination = root / "docs/project-scope/manifest.md"
    destination.parent.mkdir(parents=True, exist_ok=True)
    temporary_name = None
    try:
        with tempfile.NamedTemporaryFile(
            mode="w", encoding="utf-8", newline="\n", delete=False,
            dir=destination.parent, prefix=".manifest.", suffix=".tmp",
        ) as temporary:
            temporary.write(content)
            temporary_name = temporary.name
        os.replace(temporary_name, destination)
        temporary_name = None
    finally:
        if temporary_name:
            Path(temporary_name).unlink(missing_ok=True)
    return len(tasks), sum(task.status == "done" for task in tasks), sum(task.status == "blocked" for task in tasks)
```

- [ ] **Step 5: Run tests and verify GREEN**

Run `python -m unittest tests.test_sync_manifest -v`.

Expected: all manifest tests pass, including preservation after failure.

- [ ] **Step 6: Commit validation and atomic writing**

```powershell
git add -- tests/test_sync_manifest.py docs/project-scope/_scripts/sync_manifest.py
git commit -m "Validate task graph before manifest replacement"
```

### Task 3: Add the CLI and convert `/sync-manifest` to a thin wrapper

**Files:**
- Modify: `tests/test_sync_manifest.py`
- Modify: `docs/project-scope/_scripts/sync_manifest.py`
- Modify: `.claude/commands/sync-manifest.md`

- [ ] **Step 1: Write failing CLI and command-contract tests**

Add subprocess tests asserting exit code 0, the exact summary
`Manifest synced: 2 tasks, 1 done, 1 blocked.`, exit code 1 with an `error:`
diagnostic, and no traceback for invalid input. Add a static test that reads
`.claude/commands/sync-manifest.md`, requires `_scripts/sync_manifest.py`, and
rejects instructions for the model to parse frontmatter or write the manifest.

Add `import subprocess` to the test module and use these concrete tests:

```python
    def test_cli_writes_manifest_and_reports_counts(self):
        with tempfile.TemporaryDirectory() as directory:
            fixture = ManifestFixture(directory)
            fixture.add_task(
                "phase-1-foundation", "P1-001.md", task_id="P1-001", phase=1,
                title="Create foundation", status="done",
            )
            result = subprocess.run(
                [sys.executable, str(SCRIPT_PATH), "--root", directory, "--timestamp", "fixed"],
                capture_output=True, text=True, check=False,
            )
            self.assertEqual(0, result.returncode, result.stderr)
            self.assertEqual("Manifest synced: 1 tasks, 1 done, 0 blocked.\n", result.stdout)
            self.assertTrue((Path(directory) / "docs/project-scope/manifest.md").is_file())

    def test_cli_reports_validation_error_without_traceback(self):
        with tempfile.TemporaryDirectory() as directory:
            ManifestFixture(directory)
            result = subprocess.run(
                [sys.executable, str(SCRIPT_PATH), "--root", directory, "--timestamp", "fixed"],
                capture_output=True, text=True, check=False,
            )
            self.assertEqual(1, result.returncode)
            self.assertIn("error: no task files found", result.stderr)
            self.assertNotIn("Traceback", result.stderr)

    def test_sync_command_delegates_transformation_to_script(self):
        command = (REPO_ROOT / ".claude/commands/sync-manifest.md").read_text(encoding="utf-8")
        self.assertIn("docs/project-scope/_scripts/sync_manifest.py", command)
        self.assertNotIn("Read each file's YAML frontmatter", command)
        self.assertNotIn("Write the result to `docs/project-scope/manifest.md`", command)
```

- [ ] **Step 2: Run tests and verify RED**

Run `python -m unittest tests.test_sync_manifest -v`.

Expected: CLI tests fail because `main` and command-wrapper changes are absent.

- [ ] **Step 3: Implement CLI error and summary behavior**

Append:

```python
def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Regenerate project-scope manifest deterministically.")
    parser.add_argument("--root", type=Path, default=Path.cwd(), help="Target repository root")
    parser.add_argument("--timestamp", help=argparse.SUPPRESS)
    return parser


def main(argv: Optional[Iterable[str]] = None) -> int:
    arguments = build_parser().parse_args(argv)
    try:
        total, done, blocked = synchronize(arguments.root, arguments.timestamp)
    except (ManifestError, OSError) as error:
        print(f"error: {error}", file=sys.stderr)
        return 1
    print(f"Manifest synced: {total} tasks, {done} done, {blocked} blocked.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
```

- [ ] **Step 4: Replace the command body**

Keep `allowed-tools: Bash` only. Instruct the command to locate
`docs/project-scope/_scripts/sync_manifest.py`, run:

```text
python docs/project-scope/_scripts/sync_manifest.py --root .
```

It must stop and relay stderr verbatim on non-zero exit, relay stdout verbatim on
success, and never parse or write scope artifacts itself.

- [ ] **Step 5: Run tests and verify GREEN**

Run `python -m unittest tests.test_sync_manifest -v`.

Expected: all parser, validation, atomic-write, CLI, and command-contract tests
pass.

- [ ] **Step 6: Commit CLI integration**

```powershell
git add -- tests/test_sync_manifest.py docs/project-scope/_scripts/sync_manifest.py .claude/commands/sync-manifest.md
git commit -m "Run manifest synchronization through deterministic script"
```

### Task 4: Update installation and contributor documentation

**Files:**
- Modify: `README.md:17-62`
- Modify: `README.md:108-118`
- Modify: `CLAUDE.md:5-22`
- Modify: `CLAUDE.md:99-106`

- [ ] **Step 1: Add a failing documentation contract test**

Extend `tests/test_sync_manifest.py` to assert that README installation text
contains both `docs/project-scope/_templates` and
`docs/project-scope/_scripts`, and that `CLAUDE.md` no longer claims the repo has
no runtime or test suite.

```python
    def test_documentation_covers_script_installation_and_tests(self):
        readme = (REPO_ROOT / "README.md").read_text(encoding="utf-8")
        guidance = (REPO_ROOT / "CLAUDE.md").read_text(encoding="utf-8")
        self.assertIn("docs/project-scope/_templates", readme)
        self.assertIn("docs/project-scope/_scripts", readme)
        self.assertIn("Python 3.9", readme)
        self.assertNotIn("There is no build step, no test suite, and no runtime", guidance)
        self.assertIn("python -m unittest", guidance)
        self.assertIn("validate-agent-contracts.ps1", guidance)
```

- [ ] **Step 2: Run the documentation test and verify RED**

Run `python -m unittest tests.test_sync_manifest -v`.

Expected: documentation-contract assertions fail.

- [ ] **Step 3: Update README installation and command documentation**

Document Python 3.9+ as a prerequisite for deterministic helper scripts. Change
personal installation to copy both project-scoped directories and change the
project layout/example copy instructions accordingly. Describe `/sync-manifest`
as an executable validated transformation rather than model judgment.

- [ ] **Step 4: Update CLAUDE.md contributor guidance**

Document `_scripts`, `tests/test_sync_manifest.py`, and these commands:

```powershell
python -m unittest tests.test_sync_manifest -v
& '.\tests\validate-agent-contracts.ps1'
```

State that Markdown remains the primary product surface while Python provides
deterministic project-scoped helpers.

- [ ] **Step 5: Run all tests and verify GREEN**

Run:

```powershell
python -m unittest discover -s tests -p 'test_*.py' -v
& '.\tests\validate-agent-contracts.ps1'
git diff --check
```

Expected: all Python tests pass, `Agent contracts valid.` is printed, and
`git diff --check` exits 0.

- [ ] **Step 6: Commit documentation**

```powershell
git add -- README.md CLAUDE.md tests/test_sync_manifest.py
git commit -m "Document deterministic manifest tooling"
```

### Task 5: Final end-to-end verification

**Files:**
- Verify only; no planned modifications.

- [ ] **Step 1: Run the complete verification suite from repository root**

```powershell
python -m unittest discover -s tests -p 'test_*.py' -v
& '.\tests\validate-agent-contracts.ps1'
git diff --check
git status --short
```

Expected: all tests pass, agent contracts are valid, no whitespace errors are
reported, and only intentional plan-tracking changes remain uncommitted.

- [ ] **Step 2: Inspect commit history and generated-file ownership**

```powershell
git log -6 --oneline
rg -n "sync_manifest.py|parse frontmatter|write.*manifest" .claude README.md CLAUDE.md
```

Expected: commits are separated by renderer, validation, command integration,
and documentation; `/sync-manifest` delegates all transformation and writes to
the Python script.
