from __future__ import annotations

import json
import subprocess
import tempfile
import unittest
from pathlib import Path

from codex_multi_agent_workflow_kit.skill_sync import (
    SkillSyncError,
    build_tree_manifest,
    sync_approved_skill_roots,
)
from codex_multi_agent_workflow_kit.watcher_adapter import collect_watcher_result


class SourceAdapterTests(unittest.TestCase):
    def write_skill(self, root: Path, body: str) -> None:
        skill = root / "fixture"
        skill.mkdir(parents=True, exist_ok=True)
        (skill / "SKILL.md").write_text(
            f"---\nname: fixture\ndescription: fixture\n---\n\n{body}\n",
            encoding="utf-8",
        )

    def roots(self, base: Path) -> tuple[Path, dict[str, Path], dict[str, Path], Path]:
        source = base / "vault"
        targets = {
            "claude": base / "runtime" / ".claude" / "skills",
            "codex": base / "runtime" / ".codex" / "skills",
            "agents": base / "runtime" / ".agents" / "skills",
        }
        approved = {"source": source, **targets}
        return source, targets, approved, base / "skill-sync.lock"

    def test_approved_real_root_adapter_is_dry_run_by_default_and_exact_allowlist(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            source, targets, approved, lock = self.roots(Path(tmp))
            self.write_skill(source, "new")
            for target in targets.values():
                self.write_skill(target, "old")
            before = {name: build_tree_manifest(root) for name, root in targets.items()}

            result = sync_approved_skill_roots(
                source, targets, approved_roots=approved, lock_path=lock
            )
            self.assertEqual(result.mode, "dry-run")
            self.assertEqual(
                before, {name: build_tree_manifest(root) for name, root in targets.items()}
            )

            wrong = {**approved, "agents": Path(tmp) / "different"}
            with self.assertRaises(SkillSyncError) as raised:
                sync_approved_skill_roots(
                    source, targets, approved_roots=wrong, lock_path=lock
                )

    def test_approved_adapter_cleanup_failure_occurs_after_verified_commit(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            source, targets, approved, lock = self.roots(Path(tmp))
            self.write_skill(source, "new")
            for target in targets.values():
                self.write_skill(target, "old")
            expected = build_tree_manifest(source)

            with self.assertRaises(SkillSyncError) as raised:
                sync_approved_skill_roots(
                    source,
                    targets,
                    approved_roots=approved,
                    lock_path=lock,
                    apply=True,
                    fault_step="cleanup",
                )
            self.assertIn(
                "Verified sync commit is preserved",
                str(raised.exception),
                repr(raised.exception.__cause__),
            )
            actual = {name: build_tree_manifest(root) for name, root in targets.items()}
            self.assertTrue(
                all(manifest == expected for manifest in actual.values()),
                {
                    "expected": expected.sha256,
                    "actual": {
                        name: manifest.sha256 for name, manifest in actual.items()
                    },
                },
            )

    def test_approved_adapter_intermediate_failures_preserve_original_targets(self) -> None:
        for fault in ("copy", "hash", "swap", "post-verify"):
            with self.subTest(fault=fault), tempfile.TemporaryDirectory() as tmp:
                source, targets, approved, lock = self.roots(Path(tmp))
                self.write_skill(source, "new")
                for target in targets.values():
                    self.write_skill(target, "old")
                before = {
                    name: build_tree_manifest(root) for name, root in targets.items()
                }
                with self.assertRaises(SkillSyncError):
                    sync_approved_skill_roots(
                        source,
                        targets,
                        approved_roots=approved,
                        lock_path=lock,
                        apply=True,
                        fault_step=fault,
                    )
                self.assertEqual(
                    before,
                    {name: build_tree_manifest(root) for name, root in targets.items()},
                )

    def test_watcher_adapter_never_reports_success_for_nonzero_or_failed_target(self) -> None:
        heartbeat = {
            "status": "SUCCESS",
            "policy_version": "2026-07-15.p0",
            "source_manifest": "a" * 64,
            "target_manifests": {name: "a" * 64 for name in ("claude", "codex", "agents")},
            "failed_targets": [],
        }

        def nonzero(*_args: object, **_kwargs: object) -> subprocess.CompletedProcess[str]:
            return subprocess.CompletedProcess(["fixture"], 9, json.dumps(heartbeat), "failed")

        result = collect_watcher_result(["fixture"], runner=nonzero)
        self.assertEqual(result.status, "FAILURE")
        self.assertEqual(result.child_exit_code, 9)
        self.assertNotIn('"stderr": "failed"', json.dumps(result.to_mapping()))

        def failed_target(*_args: object, **_kwargs: object) -> subprocess.CompletedProcess[str]:
            payload = {**heartbeat, "failed_targets": ["agents"]}
            return subprocess.CompletedProcess(["fixture"], 0, json.dumps(payload), "")

        result = collect_watcher_result(["fixture"], runner=failed_target)
        self.assertEqual(result.status, "FAILURE")
        self.assertEqual(result.failed_targets, ("agents",))
        self.assertEqual(result.root_precedence, ("vault", "claude", "codex", "agents"))

    def test_watcher_adapter_fails_closed_on_malformed_or_timed_out_child(self) -> None:
        def malformed(*_args: object, **_kwargs: object) -> subprocess.CompletedProcess[str]:
            return subprocess.CompletedProcess(["fixture"], 0, "not-json", "private stderr")

        malformed_result = collect_watcher_result(["fixture"], runner=malformed)
        self.assertEqual(malformed_result.status, "FAILURE")
        self.assertEqual(malformed_result.error_code, "WATCHER_INVALID_HEARTBEAT")
        self.assertNotIn("private stderr", json.dumps(malformed_result.to_mapping()))

        def timed_out(*_args: object, **_kwargs: object) -> subprocess.CompletedProcess[str]:
            raise subprocess.TimeoutExpired(["fixture"], 1, output="partial", stderr="private")

        timeout_result = collect_watcher_result(["fixture"], runner=timed_out)
        self.assertEqual(timeout_result.status, "FAILURE")
        self.assertEqual(timeout_result.error_code, "WATCHER_CHILD_TIMEOUT")


if __name__ == "__main__":
    unittest.main()
