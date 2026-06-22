#!/usr/bin/env python3
from __future__ import annotations
"""Regenerate manifest.md from constrained task frontmatter.

This helper intentionally supports the repo's constrained frontmatter format:
- one scalar field per line
- inline lists only, such as [P1-001, P1-002]
- no multiline scalars or block-list YAML features
"""

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
    "id",
    "phase",
    "title",
    "status",
    "dependsOn",
    "touchesFiles",
    "parallelSafe",
    "architectureVersion",
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


def markdown_table_cell(value: str) -> str:
    normalized = re.sub(r"\s+", " ", value).strip()
    return normalized.replace("|", r"\|")


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
            if quote == character:
                quote = None
            elif quote is None:
                quote = character
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
    closing = next((index for index, line in enumerate(lines[1:], 1) if line.strip() == "---"), None)
    if closing is None:
        raise ManifestError(f"{path}: missing closing frontmatter delimiter")

    values: dict[str, str] = {}
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
        r"(?ms)^### Architecture Conflict[^\n]*\n(?P<body>.*?)(?=^#{2,3} |\Z)",
        text,
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

    parallel_safe = strip_inline_comment(values["parallelSafe"]).lower()
    if parallel_safe not in ("true", "false"):
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
        parallel_safe=parallel_safe == "true",
        architecture_version=positive_int(values["architectureVersion"], "architectureVersion", path),
        blocked_reason=conflict_reason(text),
    )


def architecture_version(root: Path) -> int:
    path = root / "docs/project-scope/architecture.md"
    if not path.is_file():
        raise ManifestError(f"{path}: file not found")
    match = re.search(r"(?m)^\*\*Version:\*\*\s*(\d+)\s*$", path.read_text(encoding="utf-8"))
    if not match:
        raise ManifestError(f"{path}: missing positive integer Version")
    version = int(match.group(1))
    if version < 1:
        raise ManifestError(f"{path}: missing positive integer Version")
    return version


def validate_tasks(tasks: list[Task]) -> None:
    by_id: dict[str, Task] = {}
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

    state: dict[str, str] = {}
    stack: list[str] = []

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


def load_tasks(root: Path) -> list[Task]:
    root = root.resolve()
    task_paths = sorted(root.glob("docs/project-scope/phases/phase-*/tasks/*.md"))
    if not task_paths:
        raise ManifestError("no task files found under docs/project-scope/phases")
    tasks = sorted((parse_task(path) for path in task_paths), key=lambda task: (task.phase, task.task_id))
    validate_tasks(tasks)
    return tasks


def render_manifest(tasks: list[Task], version: int, timestamp: str) -> str:
    lines = [
        "# Manifest",
        "",
        "> AUTO-GENERATED by `/sync-manifest`. Do not hand-edit - changes will be",
        "> overwritten. Source of truth is the frontmatter in `phases/**/tasks/*.md`.",
        "",
        f"**Last synced:** {timestamp}",
        f"**Architecture version:** {version}",
        "",
        "## Summary",
        "",
        "| Phase | Total | Pending | In Progress | Review | Done | Blocked |",
        "|---|---|---|---|---|---|---|",
    ]

    phases = sorted({task.phase for task in tasks})
    for phase in phases:
        phase_tasks = [task for task in tasks if task.phase == phase]
        name = markdown_table_cell(phase_tasks[0].phase_name)
        counts = {status: sum(task.status == status for task in phase_tasks) for status in VALID_STATUSES}
        lines.append(
            f"| {phase} - {name} | {len(phase_tasks)} | {counts['pending']} | "
            f"{counts['in-progress']} | {counts['review']} | {counts['done']} | {counts['blocked']} |"
        )

    lines.extend(
        [
            "",
            "## Blocked Tasks (needs attention)",
            "",
            "| Task ID | Phase | Title | Reason |",
            "|---|---|---|---|",
        ]
    )
    for task in tasks:
        if task.status == "blocked":
            lines.append(
                f"| {markdown_table_cell(task.task_id)} | {task.phase} | "
                f"{markdown_table_cell(task.title)} | {markdown_table_cell(task.blocked_reason)} |"
            )

    for phase in phases:
        phase_tasks = [task for task in tasks if task.phase == phase]
        lines.extend(
            [
                "",
                f"## Phase {phase} - {phase_tasks[0].phase_name}",
                "",
                "| Task ID | Title | Status | Depends On | Parallel Safe |",
                "|---|---|---|---|---|",
            ]
        )
        for task in phase_tasks:
            dependencies = ", ".join(markdown_table_cell(item) for item in task.depends_on) if task.depends_on else "-"
            parallel_safe = "true" if task.parallel_safe else "false"
            lines.append(
                f"| {markdown_table_cell(task.task_id)} | {markdown_table_cell(task.title)} | "
                f"{markdown_table_cell(task.status)} | {dependencies} | {parallel_safe} |"
            )

    return "\n".join(lines) + "\n"


def generate_manifest(root: Path, timestamp: Optional[str] = None) -> str:
    root = root.resolve()
    tasks = load_tasks(root)
    effective_timestamp = timestamp or datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z")
    return render_manifest(tasks, architecture_version(root), effective_timestamp)


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
            mode="w",
            encoding="utf-8",
            newline="\n",
            delete=False,
            dir=destination.parent,
            prefix=".manifest.",
            suffix=".tmp",
        ) as temporary:
            temporary.write(content)
            temporary_name = temporary.name
        os.replace(temporary_name, destination)
        temporary_name = None
    finally:
        if temporary_name:
            Path(temporary_name).unlink(missing_ok=True)
    total = len(tasks)
    done = sum(task.status == "done" for task in tasks)
    blocked = sum(task.status == "blocked" for task in tasks)
    return total, done, blocked


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
