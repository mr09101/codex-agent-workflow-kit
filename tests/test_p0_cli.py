from __future__ import annotations

import io
import json
import tempfile
import unittest
from contextlib import redirect_stderr, redirect_stdout
from datetime import datetime, timedelta, timezone
from pathlib import Path

from codex_multi_agent_workflow_kit.cli import main


class P0CliTests(unittest.TestCase):
    def run_cli(self, *args: str) -> tuple[int, str, str]:
        stdout = io.StringIO()
        stderr = io.StringIO()
        with redirect_stdout(stdout), redirect_stderr(stderr):
            code = main(list(args))
        return code, stdout.getvalue(), stderr.getvalue()

    def write_skill(self, root: Path, directory: str, name: str, body: str = "body") -> None:
        skill = root / directory
        skill.mkdir(parents=True, exist_ok=True)
        (skill / "SKILL.md").write_text(
            f"---\nname: {name}\ndescription: fixture\n---\n\n{body}\n", encoding="utf-8"
        )
        (skill / "assets").mkdir()
        (skill / "assets" / "data.bin").write_bytes(b"fixture")

    def skill_roots(self, base: Path) -> tuple[Path, dict[str, Path]]:
        source = base / "vault"
        targets = {
            name: base / "outputs" / f".{name}" / "skills"
            for name in ("claude", "codex", "agents")
        }
        return source, targets

    def sync_arguments(
        self, base: Path, source: Path, targets: dict[str, Path]
    ) -> list[str]:
        return [
            "--fixture-root",
            str(base),
            "--source",
            str(source),
            *sum(
                (["--target", f"{name}={path}"] for name, path in targets.items()),
                [],
            ),
        ]

    def test_validate_envelope_routes_through_production_module(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            envelope = base / "envelope.json"
            envelope.write_text(
                json.dumps(
                    {
                        "operation_id": "op-cli",
                        "idempotency_key": "idem-cli",
                        "parent_session_id": None,
                        "delegation_owner": "visible_thread",
                        "delegation_depth": 0,
                        "cwd_realpath": str(base.resolve()),
                        "deadline_at": (
                            datetime.now(timezone.utc) + timedelta(minutes=5)
                        ).isoformat(),
                    }
                ),
                encoding="utf-8",
            )

            code, output, error = self.run_cli("validate-envelope", str(envelope))

            self.assertEqual(code, 0)
            self.assertIn('"status": "VALID"', output)
            self.assertEqual(error, "")

    def test_resolve_role_returns_nonzero_structured_unavailable(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            catalog = Path(tmp) / "catalog.json"
            catalog.write_text(json.dumps({"models": {}, "tools": []}), encoding="utf-8")

            code, output, error = self.run_cli(
                "harness-resolve", "project_lead", "--catalog", str(catalog)
            )

            self.assertEqual(code, 3)
            payload = json.loads(output)
            self.assertEqual(payload["status"], "UNAVAILABLE")
            self.assertEqual(error, "")

    def test_skill_sync_defaults_to_dry_run_with_all_three_roots(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            source = base / "vault"
            skill = source / "fixture"
            skill.mkdir(parents=True)
            (skill / "SKILL.md").write_text(
                "---\nname: fixture\ndescription: test\n---\n", encoding="utf-8"
            )
            targets = {
                name: base / "outputs" / f".{name}" / "skills"
                for name in ("claude", "codex", "agents")
            }

            code, output, error = self.run_cli(
                "skill-sync",
                "--dry-run",
                "--fixture-root",
                str(base),
                "--source",
                str(source),
                *sum((["--target", f"{name}={path}"] for name, path in targets.items()), []),
            )

            self.assertEqual(code, 0)
            payload = json.loads(output)
            self.assertEqual(payload["mode"], "dry-run")
            self.assertEqual(set(payload["target_manifests"]), {"claude", "codex", "agents"})
            self.assertEqual(payload["failed_targets"], [])
            self.assertEqual(payload["runtime_status"]["windows"], "SUCCESS")
            self.assertEqual(payload["runtime_status"]["wsl"], "WSL_UNAVAILABLE")
            self.assertRegex(payload["completed_at"], r"^\d{4}-\d{2}-\d{2}T")
            self.assertTrue(payload["process_instance_id"])
            self.assertTrue(payload["policy_version"])
            self.assertTrue(all(not target.exists() for target in targets.values()))
            self.assertEqual(error, "")

    def test_skill_sync_failure_is_nonzero_without_success_message(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            source = base / "vault"
            source.mkdir()
            targets = {
                name: base / "outputs" / f".{name}" / "skills"
                for name in ("claude", "codex")
            }

            code, output, error = self.run_cli(
                "skill-sync",
                "--dry-run",
                "--fixture-root",
                str(base),
                "--source",
                str(source),
                *sum((["--target", f"{name}={path}"] for name, path in targets.items()), []),
            )

            self.assertNotEqual(code, 0)
            self.assertNotIn("success", (output + error).lower())
            payload = json.loads(output)
            self.assertEqual(payload["status"], "FAILURE")
            self.assertTrue(payload["failed_targets"])
            self.assertEqual(set(payload["target_manifests"]), {"claude", "codex", "agents"})
            self.assertEqual(payload["runtime_status"]["windows"], "FAILURE")
            self.assertEqual(payload["runtime_status"]["wsl"], "WSL_UNAVAILABLE")
            self.assertEqual(error, "")

    def test_skill_verify_success_has_complete_heartbeat(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            source, targets = self.skill_roots(base)
            self.write_skill(source, "fixture", "fixture")
            for target in targets.values():
                self.write_skill(target, "fixture", "fixture")

            code, output, error = self.run_cli(
                "skill-verify", *self.sync_arguments(base, source, targets)
            )

            self.assertEqual(code, 0)
            payload = json.loads(output)
            self.assertEqual(payload["status"], "SUCCESS")
            self.assertEqual(payload["failed_targets"], [])
            self.assertEqual(set(payload["target_manifests"]), set(targets))
            self.assertEqual(
                len(set(payload["target_manifests"].values()) | {payload["source_manifest"]}),
                1,
            )
            self.assertEqual(payload["runtime_status"]["wsl"], "WSL_UNAVAILABLE")
            self.assertEqual(error, "")

    def test_skill_verify_diff_is_structured_nonzero(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            source, targets = self.skill_roots(base)
            self.write_skill(source, "fixture", "fixture")
            for target in targets.values():
                self.write_skill(target, "fixture", "fixture")
                (target / "fixture" / "SKILL.md").unlink()
            (targets["agents"] / "fixture" / "assets" / "data.bin").unlink()

            code, output, error = self.run_cli(
                "skill-verify", *self.sync_arguments(base, source, targets)
            )

            self.assertNotEqual(code, 0)
            payload = json.loads(output)
            self.assertEqual(payload["status"], "FAILURE")
            self.assertIn("agents", payload["failed_targets"])
            self.assertTrue(payload["targets"]["agents"]["missing"])
            self.assertEqual(set(payload["target_manifests"]), set(targets))
            self.assertEqual(payload["runtime_status"]["windows"], "FAILURE")
            self.assertEqual(payload["runtime_status"]["wsl"], "WSL_UNAVAILABLE")
            self.assertEqual(error, "")

    def test_skill_verify_shadow_conflict_is_structured_nonzero(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            source, targets = self.skill_roots(base)
            self.write_skill(source, "canonical", "same-name", "source")
            for target in targets.values():
                self.write_skill(target, "shadow", "same-name", "target")

            code, output, error = self.run_cli(
                "skill-verify", *self.sync_arguments(base, source, targets)
            )

            self.assertNotEqual(code, 0)
            payload = json.loads(output)
            self.assertEqual(payload["error_code"], "SHADOW_CONFLICT")
            self.assertTrue(payload["failed_targets"])
            self.assertEqual(set(payload["target_manifests"]), set(targets))
            self.assertEqual(payload["runtime_status"]["wsl"], "WSL_UNAVAILABLE")
            self.assertEqual(error, "")


if __name__ == "__main__":
    unittest.main()
