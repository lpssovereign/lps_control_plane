"""
Tests for policy enforcement.
"""

import pytest
from control_plane import (
    PolicyEngine,
    RiskBasedPolicy,
    ResourceConstraintPolicy,
    ActionTypePolicy,
    Action,
    PolicyVerdict,
)


def test_empty_policy_engine():
    """Test policy engine with no rules (default allow)."""
    engine = PolicyEngine()
    action = Action(action_type="test", risk_level=5)

    verdict = engine.evaluate(action)
    assert verdict == PolicyVerdict.ALLOW


def test_risk_based_policy():
    """Test risk-based policy evaluation."""
    engine = PolicyEngine()
    policy = RiskBasedPolicy(approval_threshold=7, deny_threshold=10)
    engine.register_rule(policy)

    # Low risk → ALLOW
    low_risk = Action(action_type="read", risk_level=3)
    assert engine.evaluate(low_risk) == PolicyVerdict.ALLOW

    # Medium risk → ALLOW
    medium_risk = Action(action_type="write", risk_level=6)
    assert engine.evaluate(medium_risk) == PolicyVerdict.ALLOW

    # High risk → REQUIRE_APPROVAL
    high_risk = Action(action_type="delete", risk_level=8)
    assert engine.evaluate(high_risk) == PolicyVerdict.REQUIRE_APPROVAL

    # Extreme risk → DENY
    extreme_risk = Action(action_type="delete_all", risk_level=10)
    assert engine.evaluate(extreme_risk) == PolicyVerdict.DENY


def test_resource_constraint_policy():
    """Test resource constraint policy."""
    engine = PolicyEngine()

    # Mock resource check function
    class ResourceMonitor:
        def __init__(self):
            self.usage = 0.5

        def check(self):
            return self.usage

    monitor = ResourceMonitor()
    policy = ResourceConstraintPolicy(
        resource_check_fn=monitor.check, threshold=0.9
    )
    engine.register_rule(policy)

    # Normal usage → ALLOW
    action = Action(action_type="compute", risk_level=5)
    assert engine.evaluate(action) == PolicyVerdict.ALLOW

    # High usage (approaching threshold) → REQUIRE_APPROVAL
    monitor.usage = 0.75
    assert engine.evaluate(action) == PolicyVerdict.REQUIRE_APPROVAL

    # Critical usage (above threshold) → DENY
    monitor.usage = 0.95
    assert engine.evaluate(action) == PolicyVerdict.DENY


def test_action_type_policy():
    """Test action type whitelisting/blacklisting."""
    engine = PolicyEngine()
    policy = ActionTypePolicy(
        allowed_types=["read", "write"], denied_types=["delete", "execute"]
    )
    engine.register_rule(policy)

    # Allowed action
    allowed = Action(action_type="read")
    assert engine.evaluate(allowed) == PolicyVerdict.ALLOW

    # Denied action
    denied = Action(action_type="delete")
    assert engine.evaluate(denied) == PolicyVerdict.DENY

    # Unknown action → REQUIRE_APPROVAL
    unknown = Action(action_type="unknown_operation")
    assert engine.evaluate(unknown) == PolicyVerdict.REQUIRE_APPROVAL


def test_policy_priority():
    """Test that higher priority policies are evaluated first."""
    engine = PolicyEngine()

    # Add low priority permissive policy
    permissive = ActionTypePolicy(
        allowed_types=["read", "write", "delete"], priority=10
    )
    engine.register_rule(permissive)

    # Add high priority restrictive policy
    restrictive = ActionTypePolicy(denied_types=["delete"], priority=100)
    engine.register_rule(restrictive)

    # Delete should be DENIED (high priority policy wins)
    delete_action = Action(action_type="delete")
    assert engine.evaluate(delete_action) == PolicyVerdict.DENY


def test_most_restrictive_verdict_wins():
    """Test that most restrictive verdict from multiple policies wins."""
    engine = PolicyEngine()

    # Policy 1: Allow based on type
    engine.register_rule(
        ActionTypePolicy(allowed_types=["sensitive_operation"], priority=50)
    )

    # Policy 2: Require approval based on risk
    engine.register_rule(RiskBasedPolicy(approval_threshold=5, priority=60))

    # Action matches both policies
    action = Action(action_type="sensitive_operation", risk_level=7)

    # REQUIRE_APPROVAL should win over ALLOW
    assert engine.evaluate(action) == PolicyVerdict.REQUIRE_APPROVAL


def test_policy_statistics():
    """Test policy engine statistics."""
    engine = PolicyEngine()

    assert engine.get_statistics()["total_rules"] == 0
    assert engine.get_statistics()["evaluations"] == 0

    engine.register_rule(RiskBasedPolicy())
    engine.register_rule(ActionTypePolicy(allowed_types=["test"]))

    assert engine.get_statistics()["total_rules"] == 2
    assert engine.get_statistics()["active_rules"] == 2

    # Evaluate an action
    action = Action(action_type="test")
    engine.evaluate(action)

    assert engine.get_statistics()["evaluations"] == 1


def test_get_applicable_rules():
    """Test getting applicable rules for an action."""
    engine = PolicyEngine()

    global_rule = RiskBasedPolicy()
    specific_rule = ActionTypePolicy(allowed_types=["specific"], priority=100)

    engine.register_rule(global_rule)
    engine.register_rule(specific_rule)

    action = Action(action_type="test")
    applicable = engine.get_applicable_rules(action)

    # Global rule should always apply
    assert any(r.rule_type == "risk_based" for r in applicable)
