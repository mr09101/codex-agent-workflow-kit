from __future__ import annotations

import json
import unittest
from importlib.resources import files

from codex_multi_agent_workflow_kit.contracts import HarnessErrorCode


class ContractTests(unittest.TestCase):
    def test_error_codes_are_complete_and_match_machine_readable_schema(self) -> None:
        expected = {
            "UNAVAILABLE",
            "IDEMPOTENCY_CONFLICT",
            "STALE_RESUME",
            "SHADOW_CONFLICT",
            "INVALID_ENVELOPE",
        }
        self.assertEqual({item.value for item in HarnessErrorCode}, expected)

        schema = json.loads(
            files("codex_multi_agent_workflow_kit")
            .joinpath("harness-contract.schema.json")
            .read_text(encoding="utf-8")
        )
        self.assertEqual(set(schema["$defs"]["error_code"]["enum"]), expected)


if __name__ == "__main__":
    unittest.main()
