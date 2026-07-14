from __future__ import annotations

import unittest

from codex_multi_agent_workflow_kit.model_policy import (
    ModelSlugError,
    ResolutionStatus,
    compare_model_slugs,
    load_default_policy,
    resolve_role,
)


class ModelPolicyTests(unittest.TestCase):
    def test_semantic_version_and_tier_are_compared_separately(self) -> None:
        comparison = compare_model_slugs("gpt-5.10-sol", "gpt-5.9-sol")
        self.assertEqual(comparison.version, 1)
        self.assertEqual(comparison.tier, 0)

        reverse = compare_model_slugs("gpt-5.9-sol", "gpt-5.10-sol")
        self.assertEqual(reverse.version, -1)
        self.assertEqual(reverse.tier, 0)

        equal = compare_model_slugs("gpt-5.10.0-sol", "gpt-5.10-sol")
        self.assertEqual(equal.version, 0)
        self.assertEqual(equal.tier, 0)

        tier_only = compare_model_slugs("gpt-5.6-sol", "gpt-5.6-terra")
        self.assertEqual(tier_only.version, 0)
        self.assertEqual(tier_only.tier, 1)

        with self.assertRaises(ModelSlugError):
            compare_model_slugs("gpt-5.10-preview", "gpt-5.9-sol")

    def test_resolver_uses_only_capability_compatible_allowlisted_fallback(self) -> None:
        policy = load_default_policy()
        catalog = {
            "models": {
                "gpt-5.6-terra": {
                    "thinking": ["high", "xhigh"],
                    "capabilities": ["background", "cancel", "resume", "tools"],
                }
            },
            "tools": ["shell", "filesystem"],
        }

        result = resolve_role("project_lead", catalog, policy=policy)

        self.assertEqual(result.status, ResolutionStatus.AVAILABLE)
        self.assertEqual(result.model, "gpt-5.6-terra")
        self.assertTrue(result.used_fallback)
        self.assertEqual(result.thinking, "xhigh")
        self.assertEqual(result.ordered_fallbacks, ("gpt-5.6-terra",))
        self.assertEqual(result.decision_reason, "ALLOWLISTED_FALLBACK")
        self.assertEqual(
            set(result.required_capabilities), {"background", "cancel", "resume", "tools"}
        )
        self.assertEqual(result.policy_version, policy["policy_version"])
        self.assertRegex(result.policy_hash, r"^[0-9a-f]{64}$")

    def test_missing_model_or_tool_is_structured_unavailable(self) -> None:
        policy = load_default_policy()
        no_models = resolve_role(
            "project_lead", {"models": {}, "tools": ["shell", "filesystem"]}, policy=policy
        )
        self.assertEqual(no_models.status, ResolutionStatus.UNAVAILABLE)
        self.assertEqual(no_models.error_code, "UNAVAILABLE")
        self.assertIn("gpt-5.6-sol", no_models.missing_models)
        self.assertIsNone(no_models.model)

        missing_tool = resolve_role(
            "project_lead",
            {
                "models": {
                    "gpt-5.6-sol": {
                        "thinking": ["xhigh"],
                        "capabilities": ["background", "cancel", "resume", "tools"],
                    }
                },
                "tools": ["filesystem"],
            },
            policy=policy,
        )
        self.assertEqual(missing_tool.status, ResolutionStatus.UNAVAILABLE)
        self.assertEqual(missing_tool.error_code, "UNAVAILABLE")
        self.assertEqual(missing_tool.missing_tools, ("shell",))
        self.assertIsNone(missing_tool.model)

    def test_unknown_role_is_unavailable_and_high_risk_simple_work_is_promoted(self) -> None:
        policy = load_default_policy()
        catalog = {
            "models": {
                "gpt-5.6-sol": {
                    "thinking": ["xhigh"],
                    "capabilities": ["background", "cancel", "resume", "tools"],
                },
                "gpt-5.6-luna": {
                    "thinking": ["xhigh"],
                    "capabilities": ["tools"],
                },
            },
            "tools": ["filesystem"],
        }

        unknown = resolve_role("not-a-role", catalog, policy=policy)
        self.assertEqual(unknown.status, ResolutionStatus.UNAVAILABLE)
        self.assertEqual(unknown.error_code, "UNAVAILABLE")

        for capability in ("security", "design"):
            with self.subTest(capability=capability):
                promoted = resolve_role(
                    "simple_subagent",
                    catalog,
                    policy=policy,
                    requested_capabilities={capability},
                )
                self.assertEqual(promoted.status, ResolutionStatus.AVAILABLE)
                self.assertEqual(promoted.model, "gpt-5.6-sol")
                self.assertEqual(promoted.thinking, "xhigh")
                self.assertEqual(promoted.decision_reason, "HIGH_RISK_PROMOTION")

    def test_policy_exposes_exact_required_role_assignments(self) -> None:
        policy = load_default_policy()
        expected = {
            "root_manager": ("gpt-5.6-sol", "ultra"),
            "project_lead": ("gpt-5.6-sol", "xhigh"),
            "ux_qa": ("gpt-5.6-terra", "xhigh"),
            "simple_subagent": ("gpt-5.6-luna", "xhigh"),
            "security_design": ("gpt-5.6-sol", "xhigh"),
        }

        self.assertEqual(set(policy["roles"]), set(expected))
        for role, (model, thinking) in expected.items():
            with self.subTest(role=role):
                self.assertEqual(policy["roles"][role]["primary"], model)
                self.assertEqual(policy["roles"][role]["thinking"], thinking)

    def test_active_policy_has_no_historical_54_or_55_dependency(self) -> None:
        policy = load_default_policy()
        active_text = str(policy["roles"]) + str(policy["models"])
        self.assertNotIn("5.4", active_text)
        self.assertNotIn("5.5", active_text)
        self.assertIn("historical_models", policy)
        self.assertEqual(policy["historical_models"]["scope"], "history_only")


if __name__ == "__main__":
    unittest.main()
