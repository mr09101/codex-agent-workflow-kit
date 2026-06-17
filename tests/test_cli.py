from __future__ import annotations

import io
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path

from codex_multi_agent_workflow_kit.cli import main


class CliTests(unittest.TestCase):
    def run_cli(self, *args: str) -> tuple[int, str]:
        output = io.StringIO()
        with redirect_stdout(output):
            code = main(list(args))
        return code, output.getvalue()

    def test_init_creates_templates_and_check_passes(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            target = Path(tmp)
            code, output = self.run_cli("init", str(target))
            self.assertEqual(code, 0)
            self.assertIn("Initialized workflow templates", output)

            self.assertTrue((target / "AGENTS.md").is_file())
            self.assertTrue((target / "WORKFLOW.md").is_file())
            self.assertTrue((target / "HANDOFF.md").is_file())
            self.assertTrue((target / "FINAL_KEEP" / "README.md").is_file())

            check_code, check_output = self.run_cli("check", str(target))
            self.assertEqual(check_code, 0)
            self.assertIn("Workflow check passed", check_output)

    def test_check_fails_for_missing_files(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            code, output = self.run_cli("check", tmp)
            self.assertEqual(code, 1)
            self.assertIn("Missing required file: AGENTS.md", output)

    def test_check_fails_for_missing_section(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            target = Path(tmp)
            self.run_cli("init", str(target))
            workflow = target / "WORKFLOW.md"
            workflow.write_text("# Workflow\n", encoding="utf-8")

            code, output = self.run_cli("check", str(target))
            self.assertEqual(code, 1)
            self.assertIn("Missing section in WORKFLOW.md: ## Roles", output)

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


if __name__ == "__main__":
    unittest.main()
