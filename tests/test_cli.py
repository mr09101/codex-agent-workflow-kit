from __future__ import annotations

import io
import os
import subprocess
import tempfile
import unittest
from contextlib import redirect_stderr, redirect_stdout
from pathlib import Path

from codex_multi_agent_workflow_kit.cli import main


class CliTests(unittest.TestCase):
    def run_cli(self, *args: str) -> tuple[int, str, str]:
        stdout = io.StringIO()
        stderr = io.StringIO()
        with redirect_stdout(stdout), redirect_stderr(stderr):
            code = main(list(args))
        return code, stdout.getvalue(), stderr.getvalue()

    def create_symlink(self, link: Path, target: Path, *, directory: bool = False) -> None:
        try:
            link.symlink_to(target, target_is_directory=directory)
        except OSError as error:
            if os.name == "nt" and getattr(error, "winerror", None) == 1314:
                self.skipTest(
                    "Windows symlink creation requires Developer Mode or "
                    "SeCreateSymbolicLinkPrivilege"
                )
            raise

    def create_directory_link(self, link: Path, target: Path) -> None:
        try:
            self.create_symlink(link, target, directory=True)
        except unittest.SkipTest:
            result = subprocess.run(
                ["cmd", "/c", "mklink", "/J", str(link), str(target)],
                capture_output=True,
                text=True,
                check=False,
            )
            if result.returncode != 0:
                self.skipTest(
                    "Windows symlink privilege is unavailable and junction creation failed"
                )

    def test_init_creates_templates_and_check_passes(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            target = Path(tmp)
            code, output, error = self.run_cli("init", str(target))
            self.assertEqual(code, 0)
            self.assertIn("Initialized workflow templates", output)
            self.assertEqual(error, "")

            self.assertTrue((target / "AGENTS.md").is_file())
            self.assertTrue((target / "WORKFLOW.md").is_file())
            self.assertTrue((target / "HANDOFF.md").is_file())
            self.assertTrue((target / "FINAL_KEEP" / "README.md").is_file())

            check_code, check_output, check_error = self.run_cli("check", str(target))
            self.assertEqual(check_code, 0)
            self.assertIn("Workflow check passed", check_output)
            self.assertEqual(check_error, "")

    def test_check_fails_for_missing_files(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            code, output, error = self.run_cli("check", tmp)
            self.assertEqual(code, 1)
            self.assertIn("Missing required file: AGENTS.md", output)
            self.assertEqual(error, "")

    def test_check_fails_for_missing_section(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            target = Path(tmp)
            self.run_cli("init", str(target))
            workflow = target / "WORKFLOW.md"
            workflow.write_text("# Workflow\n", encoding="utf-8")

            code, output, error = self.run_cli("check", str(target))
            self.assertEqual(code, 1)
            self.assertIn("Missing section in WORKFLOW.md: ## Roles", output)
            self.assertEqual(error, "")

    def test_init_does_not_overwrite_without_force(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            target = Path(tmp)
            target.mkdir(parents=True, exist_ok=True)
            agents = target / "AGENTS.md"
            agents.write_text("custom", encoding="utf-8")

            self.run_cli("init", str(target))
            self.assertEqual(agents.read_text(encoding="utf-8"), "custom")

            self.run_cli("init", str(target), "--force")
            self.assertIn("# Agent Operating Guide", agents.read_text(encoding="utf-8"))

    def test_init_force_rejects_file_symlink_without_overwriting_target(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            target = base / "project"
            target.mkdir()
            outside = base / "outside.md"
            outside.write_text("sentinel", encoding="utf-8")
            self.create_symlink(target / "AGENTS.md", outside)

            code, output, error = self.run_cli("init", str(target), "--force")

            self.assertEqual(code, 2)
            self.assertEqual(outside.read_text(encoding="utf-8"), "sentinel")
            self.assertEqual(output, "")
            self.assertIn("unsafe filesystem link", error.lower())
            self.assertNotIn("Traceback", error)

    def test_init_force_rejects_directory_symlink_without_writing_outside(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            target = base / "project"
            target.mkdir()
            outside = base / "outside"
            outside.mkdir()
            self.create_directory_link(target / "FINAL_KEEP", outside)

            code, output, error = self.run_cli("init", str(target), "--force")

            self.assertEqual(code, 2)
            self.assertFalse((outside / "README.md").exists())
            self.assertEqual(output, "")
            self.assertIn("unsafe filesystem link", error.lower())
            self.assertNotIn("Traceback", error)

    def test_init_rejects_symlink_as_target_root(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            outside = base / "outside"
            outside.mkdir()
            linked_target = base / "project"
            self.create_directory_link(linked_target, outside)

            code, output, error = self.run_cli("init", str(linked_target), "--force")

            self.assertEqual(code, 2)
            self.assertFalse((outside / "AGENTS.md").exists())
            self.assertEqual(output, "")
            self.assertIn("unsafe filesystem link", error.lower())
            self.assertNotIn("Traceback", error)

    def test_init_reports_path_conflict_without_traceback(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            target = Path(tmp) / "project"
            target.write_text("not a directory", encoding="utf-8")

            code, output, error = self.run_cli("init", str(target))

            self.assertEqual(code, 2)
            self.assertEqual(output, "")
            self.assertRegex(error, r"^ERROR: .+\n$")
            self.assertNotIn("Traceback", error)

    def test_check_reports_invalid_utf8_without_traceback(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            target = Path(tmp)
            (target / "AGENTS.md").write_bytes(b"\xff")

            code, output, error = self.run_cli("check", str(target))

            self.assertEqual(code, 2)
            self.assertEqual(output, "")
            self.assertRegex(error, r"^ERROR: .+\n$")
            self.assertNotIn("Traceback", error)


if __name__ == "__main__":
    unittest.main()
