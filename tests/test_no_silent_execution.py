"""
Tests ensuring no silent execution.

Critical safety property: Actions must pass through full pipeline.
No shortcuts, no silent execution.
"""

import pytest
from control_plane import ExecutionEngine, Action, PolicyVerdict, RiskBasedPolicy


def test_execution_requires_approval_path():
    """Test that high-risk actions cannot execute without approval."""
    engine = ExecutionEngine()

    # Register policy
    engine.policy_engine.register_rule(RiskBasedPolicy(approval_threshold=7))

    # Register dummy executor
    engine.register_executor("risky_action", lambda params: "executed")

    # High-risk action without approval mechanism should fail
    high_risk = Action(action_type="risky_action", risk_level=8)

    with pytest.raises(RuntimeError, match="requires approval"):
        engine.execute(high_risk, auto_approve=False, approval_callback=None)


def test_all_executions_logged():
    """Test that all executions are logged to audit trail."""
    engine = ExecutionEngine()

    engine.register_executor("test_action", lambda params: "result")

    action = Action(action_type="test_action", risk_level=3)
    result = engine.execute(action, auto_approve=True)

    # Check audit trail exists
    audit_trail = engine.get_audit_trail()
    assert len(audit_trail) > 0

    # Check audit log
    assert len(engine.audit_log) > 0


def test_denied_actions_do_not_execute():
    """Test that denied actions never reach execution."""
    engine = ExecutionEngine()

    # Policy that denies everything
    class DenyAllPolicy:
        rule_type = "deny_all"
        scope = "global"
        constraint = "deny"
        priority = 100
        active = True

        def evaluate(self, action):
            return PolicyVerdict.DENY

    engine.policy_engine.register_rule(DenyAllPolicy())

    # Track if executor was called
    executed = {"called": False}

    def executor(params):
        executed["called"] = True
        return "should_not_happen"

    engine.register_executor("test", executor)

    # Execute denied action
    action = Action(action_type="test", risk_level=5)
    result = engine.execute(action)

    # Should not succeed
    assert not result.success
    assert "denied" in result.error.lower()

    # Executor should never be called
    assert not executed["called"]


def test_approval_denial_prevents_execution():
    """Test that denied approvals prevent execution."""
    engine = ExecutionEngine()

    engine.policy_engine.register_rule(RiskBasedPolicy(approval_threshold=5))

    # Track execution
    executed = {"called": False}

    def executor(params):
        executed["called"] = True
        return "result"

    engine.register_executor("test", executor)

    # Approval callback that denies
    def deny_approval(action):
        return False

    action = Action(action_type="test", risk_level=7)
    result = engine.execute(action, approval_callback=deny_approval)

    # Should not succeed
    assert not result.success
    assert "denied" in result.error.lower()

    # Executor should not be called
    assert not executed["called"]


def test_state_machine_enforces_ordering():
    """Test that state machine enforces correct ordering."""
    engine = ExecutionEngine()

    # Try to manually manipulate state (should fail)
    engine.state_machine.initialize()

    # Cannot skip states
    with pytest.raises(ValueError):
        engine.state_machine.transition(
            engine.state_machine.ExecutionState.EXECUTE  # Skip PLAN and APPROVE
        )


def test_audit_trail_integrity():
    """Test audit trail hash chain integrity."""
    engine = ExecutionEngine()

    engine.register_executor("test", lambda params: "result")

    # Execute several actions
    for i in range(5):
        action = Action(action_type="test", params={"i": i}, risk_level=3)
        engine.execute(action, auto_approve=True)

        # Reset state machine for next execution
        engine.state_machine = type(engine.state_machine)()

    # Verify audit log integrity
    assert engine.audit_log.verify_integrity()


def test_immutable_audit_records():
    """Test that audit records cannot be modified."""
    engine = ExecutionEngine()

    engine.register_executor("test", lambda params: "result")

    action = Action(action_type="test", risk_level=3)
    engine.execute(action, auto_approve=True)

    # Get audit entries
    entries = engine.audit_log.get_entries()
    assert len(entries) > 0

    # Try to modify (should fail)
    with pytest.raises(Exception):  # FrozenInstanceError
        entries[0].message = "tampered"


def test_execution_statistics_tracking():
    """Test that execution statistics are tracked."""
    engine = ExecutionEngine()

    engine.register_executor("test", lambda params: "result")

    # Execute action
    action = Action(action_type="test", risk_level=3)
    result = engine.execute(action, auto_approve=True)

    # Get statistics
    stats = engine.get_statistics()

    assert "state_machine" in stats
    assert "policy_engine" in stats
    assert "audit_log" in stats
    assert stats["policy_engine"]["evaluations"] > 0
