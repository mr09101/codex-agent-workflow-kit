from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from codex_multi_agent_workflow_kit.skill_sync import (
    ShadowConflict,
    SkillSyncError,
    build_tree_manifest,
    sync_skill_roots,
    validate_skill_name,
    verify_skill_roots,
)


class SkillSyncTests(unittest.TestCase):
    def write_skill(self, root: Path, directory: str, name: str, body: str = "body") -> None:
        skill = root / directory
        skill.mkdir(parents=True, exist_ok=True)
        (skill / "SKILL.md").write_text(
            f"---\nname: {name}\ndescription: fixture\n---\n\n{body}\n", encoding="utf-8"
        )
        (skill / "agents" / "openai.yaml").parent.mkdir(parents=True, exist_ok=True)
        (skill / "agents" / "openai.yaml").write_text("interface: fixture\n", encoding="utf-8")
        (skill / "scripts").mkdir(exist_ok=True)
        (skill / "scripts" / "check.py").write_text("print('fixture')\n", encoding="utf-8")
        (skill / "references").mkdir(exist_ok=True)
        (skill / "references" / "guide.md").write_text("guide\n", encoding="utf-8")
        (skill / "assets").mkdir(exist_ok=True)
        (skill / "assets" / "data.bin").write_bytes(b"fixture")

    def roots(self, base: Path) -> tuple[Path, dict[str, Path]]:
        source = base / "vault"
        outputs = {
            "claude": base / "outputs" / ".claude" / "skills",
            "codex": base / "outputs" / ".codex" / "skills",
            "agents": base / "outputs" / ".agents" / "skills",
        }
        return source, outputs

    def test_copy_hash_and_swap_failures_preserve_original_targets(self) -> None:
        for fault in ("copy", "stage", "hash", "swap", "post-verify"):
            with self.subTest(fault=fault), tempfile.TemporaryDirectory() as tmp:
                base = Path(tmp)
                source, outputs = self.roots(base)
                self.write_skill(source, "new-skill", "new-skill", "new")
                for target in outputs.values():
                    self.write_skill(target, "old-skill", "old-skill", "old")
                before = {name: build_tree_manifest(path) for name, path in outputs.items()}

                with self.assertRaises(SkillSyncError):
                    sync_skill_roots(
                        source, outputs, fixture_root=base, apply=True, fault_step=fault
                    )

                after = {name: build_tree_manifest(path) for name, path in outputs.items()}
                self.assertEqual(after, before)
                self.assertFalse((base / ".skill-sync.lock").exists())

    def test_full_tree_verify_detects_missing_mismatch_and_extra(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            source, outputs = self.roots(base)
            self.write_skill(source, "one", "one")
            for target in outputs.values():
                self.write_skill(target, "one", "one")
                (target / "one" / "SKILL.md").unlink()

            (outputs["claude"] / "one" / "assets" / "data.bin").unlink()
            (outputs["codex"] / "one" / "references" / "guide.md").write_text(
                "changed\n", encoding="utf-8"
            )
            (outputs["agents"] / "extra.txt").write_text("extra\n", encoding="utf-8")

            result = verify_skill_roots(source, outputs, fixture_root=base)

            self.assertFalse(result.ok)
            self.assertTrue(result.targets["claude"].missing)
            self.assertTrue(result.targets["codex"].mismatched)
            self.assertTrue(result.targets["agents"].extra)

    def test_shadow_name_with_different_hash_fails_closed(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            source, outputs = self.roots(base)
            self.write_skill(source, "canonical", "same-name", "canonical")
            for target in outputs.values():
                self.write_skill(target, "shadow", "same-name", "different")

            with self.assertRaises(ShadowConflict):
                verify_skill_roots(source, outputs, fixture_root=base)

            reversed_outputs = dict(reversed(tuple(outputs.items())))
            with self.assertRaises(ShadowConflict):
                verify_skill_roots(source, reversed_outputs, fixture_root=base)

    def test_shadow_directory_with_different_hash_fails_independent_of_order(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            source, outputs = self.roots(base)
            self.write_skill(source, "shared-directory", "source-name", "canonical")
            for target in outputs.values():
                self.write_skill(target, "shared-directory", "target-name", "different")

            for ordered in (outputs, dict(reversed(tuple(outputs.items())))):
                with self.subTest(order=tuple(ordered)), self.assertRaises(ShadowConflict):
                    verify_skill_roots(source, ordered, fixture_root=base)

    def test_validates_names_and_rejects_path_or_reparse_escape(self) -> None:
        self.assertEqual(validate_skill_name("safe-skill-1"), "safe-skill-1")
        for name in ("../escape", "two/parts", "two\\parts", "C:drive", "CON", "", "."):
            with self.subTest(name=name), self.assertRaises(SkillSyncError):
                validate_skill_name(name)

        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            outside = base.parent / f"{base.name}-outside"
            outside.mkdir(exist_ok=False)
            try:
                source, outputs = self.roots(base)
                self.write_skill(source, "one", "one")
                with self.assertRaises(SkillSyncError):
                    sync_skill_roots(source, {**outputs, "agents": outside}, fixture_root=base)
            finally:
                outside.rmdir()

    def test_process_lock_contention_is_nonzero_and_target_unchanged(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            source, outputs = self.roots(base)
            self.write_skill(source, "one", "one")
            for target in outputs.values():
                self.write_skill(target, "old", "old")
            before = {name: build_tree_manifest(path) for name, path in outputs.items()}
            lock = base / ".skill-sync.lock"
            lock.write_text(json.dumps({"pid": os.getpid()}), encoding="utf-8")

            with self.assertRaises(SkillSyncError):
                sync_skill_roots(source, outputs, fixture_root=base, apply=True)

            self.assertEqual(
                {name: build_tree_manifest(path) for name, path in outputs.items()}, before
            )

    def test_separate_os_process_holds_sync_lock(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            source, outputs = self.roots(base)
            self.write_skill(source, "one", "one")
            helper = (
                "import os,time,pathlib; "
                "p=pathlib.Path(os.environ['LOCK_PATH']); "
                "fd=os.open(p,os.O_CREAT|os.O_EXCL|os.O_WRONLY); "
                "os.write(fd,str(os.getpid()).encode()); "
                "print('LOCKED',flush=True); time.sleep(10)"
            )
            process = subprocess.Popen(
                [sys.executable, "-c", helper],
                env={**os.environ, "LOCK_PATH": str(base / ".skill-sync.lock")},
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
            )
            try:
                self.assertEqual(process.stdout.readline().strip(), "LOCKED")
                with self.assertRaises(SkillSyncError):
                    sync_skill_roots(source, outputs, fixture_root=base, apply=True)
            finally:
                process.terminate()
                process.wait(timeout=5)
                if process.stdout is not None:
                    process.stdout.close()
                if process.stderr is not None:
                    process.stderr.close()

    def test_agents_is_a_required_output_root(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            source, outputs = self.roots(base)
            self.write_skill(source, "one", "one")
            outputs.pop("agents")

            with self.assertRaises(SkillSyncError):
                sync_skill_roots(source, outputs, fixture_root=base)
            with self.assertRaises(SkillSyncError):
                verify_skill_roots(source, outputs, fixture_root=base)

    def test_duplicate_or_overlapping_target_paths_fail_closed(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            source, outputs = self.roots(base)
            self.write_skill(source, "one", "one")

            duplicate = dict(outputs, agents=outputs["codex"])
            with self.assertRaises(SkillSyncError):
                sync_skill_roots(source, duplicate, fixture_root=base)

            overlapping = dict(outputs, agents=outputs["codex"] / "nested")
            with self.assertRaises(SkillSyncError):
                verify_skill_roots(source, overlapping, fixture_root=base)


if __name__ == "__main__":
    unittest.main()
