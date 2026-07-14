from __future__ import annotations

import tempfile
import unittest
import os
from datetime import datetime, timedelta, timezone
from pathlib import Path

from codex_multi_agent_workflow_kit.envelope import (
    EnvelopeError,
    OperationEnvelope,
    child_envelope,
)


class EnvelopeTests(unittest.TestCase):
    def valid_values(self, cwd: Path) -> dict[str, object]:
        return {
            "operation_id": "op-123",
            "idempotency_key": "idem-123",
            "parent_session_id": None,
            "delegation_owner": "visible_thread",
            "delegation_depth": 0,
            "cwd_realpath": str(cwd.resolve()),
            "deadline_at": (datetime.now(timezone.utc) + timedelta(minutes=5)).isoformat(),
        }

    def test_requires_exactly_the_seven_envelope_fields(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            values = self.valid_values(Path(tmp))
            for field in tuple(values):
                invalid = dict(values)
                invalid.pop(field)
                with self.subTest(field=field), self.assertRaises(EnvelopeError):
                    OperationEnvelope.from_mapping(invalid)

            extra = dict(values, prompt="must-not-be-durable")
            with self.assertRaises(EnvelopeError):
                OperationEnvelope.from_mapping(extra)

    def test_rejects_invalid_owner_depth_cwd_and_deadline(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            cwd = Path(tmp)
            cases = (
                {"delegation_owner": ""},
                {"delegation_owner": "unknown_owner"},
                {"delegation_depth": -1},
                {"delegation_depth": 9},
                {"delegation_depth": True},
                {"delegation_depth": 1},
                {"cwd_realpath": str(cwd / "missing")},
                {"deadline_at": (datetime.now(timezone.utc) - timedelta(seconds=1)).isoformat()},
                {"deadline_at": (datetime.now(timezone.utc) + timedelta(hours=25)).isoformat()},
                {"deadline_at": "2026-07-15T00:00:00"},
            )
            for override in cases:
                invalid = dict(self.valid_values(cwd), **override)
                with self.subTest(override=override), self.assertRaises(EnvelopeError):
                    OperationEnvelope.from_mapping(invalid)

    def test_child_preserves_identity_and_increments_depth(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            parent = OperationEnvelope.from_mapping(self.valid_values(Path(tmp)))
            child = child_envelope(
                parent,
                parent_session_id="session-123",
                delegation_owner="internal_subagent",
            )

            self.assertEqual(child.operation_id, parent.operation_id)
            self.assertEqual(child.idempotency_key, parent.idempotency_key)
            self.assertEqual(child.parent_session_id, "session-123")
            self.assertEqual(child.delegation_depth, parent.delegation_depth + 1)
            self.assertEqual(child.delegation_owner, "internal_subagent")
            self.assertEqual(child.cwd_realpath, parent.cwd_realpath)
            self.assertEqual(child.deadline_at, parent.deadline_at)

    def test_rejects_dot_alias_and_cwd_outside_fixture_boundary(self) -> None:
        with tempfile.TemporaryDirectory() as tmp, tempfile.TemporaryDirectory() as outside:
            root = Path(tmp)
            dot_alias = dict(self.valid_values(root), cwd_realpath=str(root) + os.sep + ".")
            with self.assertRaises(EnvelopeError):
                OperationEnvelope.from_mapping(dot_alias, fixture_root=root)

            escaped = dict(self.valid_values(root), cwd_realpath=str(Path(outside).resolve()))
            with self.assertRaises(EnvelopeError):
                OperationEnvelope.from_mapping(escaped, fixture_root=root)


if __name__ == "__main__":
    unittest.main()
