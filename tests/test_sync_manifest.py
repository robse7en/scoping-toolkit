import importlib.util
import subprocess
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


def task_text(
    *,
    task_id,
    phase,
    title,
    status="pending",
    depends_on="[]",
    touches_files="[]",
    parallel_safe="false",
    architecture_version=3,
    conflict="-",
):
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
                "phase-2-reporting",
                "P2-002.md",
                task_id="P2-002",
                phase=2,
                title="Export report",
                status="blocked",
                depends_on="[P1-001]",
                conflict="- Architecture requires a report store that does not exist.",
            )
            fixture.add_task(
                "phase-1-foundation",
                "P1-001.md",
                task_id="P1-001",
                phase=1,
                title="Create foundation",
                status="done",
                parallel_safe="true",
            )

            output = self.sync.generate_manifest(
                Path(directory), timestamp="2026-06-21T01:02:03Z"
            )

            self.assertIn("**Last synced:** 2026-06-21T01:02:03Z", output)
            self.assertIn("**Architecture version:** 3", output)
            self.assertIn("| 1 - Foundation | 1 | 0 | 0 | 0 | 1 | 0 |", output)
            self.assertIn("| 2 - Reporting | 1 | 0 | 0 | 0 | 0 | 1 |", output)
            self.assertIn(
                "| P2-002 | 2 | Export report | Architecture requires a report store that does not exist. |",
                output,
            )
            self.assertLess(output.index("## Phase 1"), output.index("## Phase 2"))

    def test_fixed_timestamp_produces_identical_bytes(self):
        with tempfile.TemporaryDirectory() as directory:
            fixture = ManifestFixture(directory)
            fixture.add_task(
                "phase-1-foundation",
                "P1-001.md",
                task_id="P1-001",
                phase=1,
                title="Create foundation",
            )
            first = self.sync.generate_manifest(Path(directory), "fixed")
            second = self.sync.generate_manifest(Path(directory), "fixed")
            self.assertEqual(first.encode("utf-8"), second.encode("utf-8"))

    def test_manifest_escapes_markdown_table_cells(self):
        with tempfile.TemporaryDirectory() as directory:
            fixture = ManifestFixture(directory)
            fixture.add_task(
                "phase-1-foundation",
                "P1-001.md",
                task_id="P1-001",
                phase=1,
                title="Create | foundation",
                status="blocked",
                conflict="- Needs | separation\n- and a second line",
            )

            output = self.sync.generate_manifest(Path(directory), timestamp="fixed")

            self.assertIn(
                "| P1-001 | 1 | Create \\| foundation | Needs \\| separation |",
                output,
            )
            self.assertNotIn("| P1-001 | 1 | Create | foundation", output)

    def test_validation_cases_raise_specific_errors(self):
        cases = [
            (
                "duplicate task ids",
                [
                    (
                        "phase-1-foundation",
                        "P1-001.md",
                        dict(task_id="P1-001", phase=1, title="One"),
                    ),
                    (
                        "phase-1-foundation",
                        "P1-002.md",
                        dict(task_id="P1-001", phase=1, title="Two"),
                    ),
                ],
                "duplicate task id P1-001",
            ),
            (
                "unknown dependency",
                [
                    (
                        "phase-1-foundation",
                        "P1-001.md",
                        dict(
                            task_id="P1-001",
                            phase=1,
                            title="One",
                            depends_on="[P9-999]",
                        ),
                    )
                ],
                "P1-001 depends on unknown task P9-999",
            ),
            (
                "self dependency",
                [
                    (
                        "phase-1-foundation",
                        "P1-001.md",
                        dict(
                            task_id="P1-001",
                            phase=1,
                            title="One",
                            depends_on="[P1-001]",
                        ),
                    )
                ],
                "P1-001 depends on itself",
            ),
            (
                "dependency cycle",
                [
                    (
                        "phase-1-foundation",
                        "P1-001.md",
                        dict(
                            task_id="P1-001",
                            phase=1,
                            title="One",
                            depends_on="[P1-002]",
                        ),
                    ),
                    (
                        "phase-1-foundation",
                        "P1-002.md",
                        dict(
                            task_id="P1-002",
                            phase=1,
                            title="Two",
                            depends_on="[P1-001]",
                        ),
                    ),
                ],
                "dependency cycle: P1-001 -> P1-002 -> P1-001",
            ),
            (
                "invalid status",
                [
                    (
                        "phase-1-foundation",
                        "P1-001.md",
                        dict(task_id="P1-001", phase=1, title="One", status="invalid"),
                    )
                ],
                "invalid status invalid",
            ),
            (
                "mismatched phase folder",
                [
                    (
                        "phase-2-foundation",
                        "P1-001.md",
                        dict(task_id="P1-001", phase=1, title="One"),
                    )
                ],
                "phase 1 does not match folder phase 2",
            ),
        ]
        for label, tasks, message in cases:
            with self.subTest(label=label):
                with tempfile.TemporaryDirectory() as directory:
                    fixture = ManifestFixture(directory)
                    for phase_folder, filename, values in tasks:
                        fixture.add_task(phase_folder, filename, **values)
                    with self.assertRaisesRegex(self.sync.ManifestError, message):
                        self.sync.generate_manifest(Path(directory), timestamp="fixed")

    def test_validation_failure_does_not_replace_existing_manifest(self):
        with tempfile.TemporaryDirectory() as directory:
            fixture = ManifestFixture(directory)
            fixture.add_task(
                "phase-1-foundation",
                "P1-001.md",
                task_id="P1-001",
                phase=1,
                title="Broken task",
                status="invalid",
            )
            manifest = Path(directory) / "docs/project-scope/manifest.md"
            manifest.write_text("existing manifest\n", encoding="utf-8")

            with self.assertRaises(self.sync.ManifestError):
                self.sync.synchronize(Path(directory), timestamp="fixed")

            self.assertEqual("existing manifest\n", manifest.read_text(encoding="utf-8"))

    def test_cli_writes_manifest_and_reports_counts(self):
        with tempfile.TemporaryDirectory() as directory:
            fixture = ManifestFixture(directory)
            fixture.add_task(
                "phase-1-foundation",
                "P1-001.md",
                task_id="P1-001",
                phase=1,
                title="Create foundation",
                status="done",
            )
            result = subprocess.run(
                [sys.executable, str(SCRIPT_PATH), "--root", directory, "--timestamp", "fixed"],
                capture_output=True,
                text=True,
                check=False,
            )
            self.assertEqual(0, result.returncode, result.stderr)
            self.assertEqual("Manifest synced: 1 tasks, 1 done, 0 blocked.\n", result.stdout)
            self.assertTrue((Path(directory) / "docs/project-scope/manifest.md").is_file())

    def test_cli_reports_validation_error_without_traceback(self):
        with tempfile.TemporaryDirectory() as directory:
            ManifestFixture(directory)
            result = subprocess.run(
                [sys.executable, str(SCRIPT_PATH), "--root", directory, "--timestamp", "fixed"],
                capture_output=True,
                text=True,
                check=False,
            )
            self.assertEqual(1, result.returncode)
            self.assertIn("error: no task files found", result.stderr)
            self.assertNotIn("Traceback", result.stderr)

    def test_sync_command_delegates_transformation_to_script(self):
        command = (REPO_ROOT / ".claude/commands/sync-manifest.md").read_text(
            encoding="utf-8"
        )
        self.assertIn("docs/project-scope/_scripts/sync_manifest.py", command)
        self.assertNotIn("Read each file's YAML frontmatter", command)
        self.assertNotIn("Write the result to `docs/project-scope/manifest.md`", command)

    def test_sync_command_and_docs_describe_constrained_frontmatter(self):
        command = (REPO_ROOT / ".claude/commands/sync-manifest.md").read_text(
            encoding="utf-8"
        )
        guidance = (REPO_ROOT / "CLAUDE.md").read_text(encoding="utf-8")

        self.assertIn("constrained frontmatter", command)
        self.assertIn("constrained frontmatter", guidance)
        self.assertNotIn("YAML frontmatter", command)

    def test_documentation_covers_script_installation_and_tests(self):
        readme = (REPO_ROOT / "README.md").read_text(encoding="utf-8")
        guidance = (REPO_ROOT / "CLAUDE.md").read_text(encoding="utf-8")
        self.assertIn("docs/project-scope/_templates", readme)
        self.assertIn("docs/project-scope/_scripts", readme)
        self.assertIn("Python 3.9", readme)
        self.assertNotIn(
            "There is no build step, no test suite, and no runtime", guidance
        )
        self.assertIn("python -m unittest", guidance)
        self.assertIn("validate-agent-contracts.ps1", guidance)

    def test_artifact_report_template_has_machine_readable_frontmatter(self):
        template = (
            REPO_ROOT / "docs/project-scope/_templates/artifact-analysis.template.md"
        ).read_text(encoding="utf-8")
        command = (REPO_ROOT / ".claude/commands/implement.md").read_text(
            encoding="utf-8"
        )

        self.assertTrue(template.startswith("---\n"))
        self.assertIn("criticalFindings:", template)
        self.assertIn("generatedAt:", template)
        self.assertIn("architectureVersionChecked:", template)
        self.assertIn("taskPathsChecked:", template)
        self.assertIn("Read the verification report frontmatter", command)
        self.assertIn("`criticalFindings`", command)
        self.assertIn("`generatedAt`", command)
        self.assertIn("`architectureVersionChecked`", command)

    def test_qa_reviewer_has_explicit_stale_architecture_failure_path(self):
        qa_reviewer = (REPO_ROOT / ".claude/agents/qa-reviewer.md").read_text(
            encoding="utf-8"
        )

        self.assertIn("If the task's `architectureVersion` does not match", qa_reviewer)
        self.assertIn("Set `status: blocked`", qa_reviewer)
        self.assertIn("Do not mark the task done", qa_reviewer)


if __name__ == "__main__":
    unittest.main()
