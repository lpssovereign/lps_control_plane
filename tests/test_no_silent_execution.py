"""
Tests ensuring no silent execution.

Critical safety property: actions must pass through the governed pipeline.
"""

import pytest

from control_plane import (
    Action,
    ExecutionEngine,
    ExecutionState,
    PolicyVerdict,
    RiskBasedPolicy,
)


def test_execution_requires_approval_path():
    """High-risk actions fail closed when no approval mechanism is provided."""
    engine = ExecutionEngine()
    engine.policy_engine.register_rule(RiskBasedPolicy(approval_threshold=7))

    executed = {"called": False}

    def executor(params):
        executed["called"] = True
        return "executed"

    engine.register_executor("risky_action", executor)
    high_risk = Action(action_type="risky_action", risk_level=8)

    result = engine.execute(
        high_risk,
        auto_approve=False,
        approval_callback=None,
    )

    assert not result.success
    assert "requires approval" in result.error.lower()
    assert not executed["called"]


def test_all_executions_logged():
    """All executions are represented in the audit trail."""
    engine = ExecutionEngine()
    engine.register_executor("test_action", lambda params: "result")

    action = Action(action_type="test_action", risk_level=3)
    result = engine.execute(action, auto_approve=True)

    assert result.success
    assert len(engine.get_audit_trail()) > 0
    assert len(engine.audit_log) > 0


def test_denied_actions_do_not_execute():
    """Denied actions never reach the executor."""
    engine = ExecutionEngine()

    class DenyAllPolicy:
        rule_type = "deny_all"
        scope = "global"
        constraint = "deny"
        priority = 100
        active = True

        def evaluate(self, action):
            return PolicyVerdict.DENY

    engine.policy_engine.register_rule(DenyAllPolicy())
    executed = {"called": False}

    def executor(params):
        executed["called"] = True
        return "should_not_happen"

    engine.register_executor("test", executor)
    result = engine.execute(Action(action_type="test", risk_level=5))

    assert not result.success
    assert "denied" in result.error.lower()
    assert not executed["called"]


def test_approval_denial_prevents_execution():
    """A rejected approval prevents executor invocation."""
    engine = ExecutionEngine()
    engine.policy_engine.register_rule(RiskBasedPolicy(approval_threshold=5))
    executed = {"called": False}

    def executor(params):
        executed["called"] = True
        return "result"

    engine.register_executor("test", executor)
    action = Action(action_type="test", risk_level=7)
    result = engine.execute(action, approval_callback=lambda _: False)

    assert not result.success
    assert "denied" in result.error.lower()
    assert not executed["called"]


def test_state_machine_enforces_ordering():
    """The state machine rejects attempts to skip required states."""
    engine = ExecutionEngine()
    engine.state_machine.initialize()

    with pytest.raises(ValueError):
        engine.state_machine.transition(ExecutionState.EXECUTE)


def test_audit_trail_integrity():
    """The audit-log hash chain remains valid across executions."""
    engine = ExecutionEngine()
    engine.register_executor("test", lambda params: "result")

    for i in range(5):
        action = Action(action_type="test", params={"i": i}, risk_level=3)
        engine.execute(action, auto_approve=True)
        engine.state_machine = type(engine.state_machine)()

    assert engine.audit_log.verify_integrity()


def test_immutable_audit_records():
    """Audit entries cannot be modified."""
    engine = ExecutionEngine()
    engine.register_executor("test", lambda params: "result")

    engine.execute(Action(action_type="test", risk_level=3), auto_approve=True)
    entries = engine.audit_log.get_entries()

    assert entries
    with pytest.raises(Exception):
        entries[0].message = "tampered"


def test_execution_statistics_tracking():
    """Execution statistics report state, policy, and audit activity."""
    engine = ExecutionEngine()
    engine.register_executor("test", lambda params: "result")

    engine.execute(Action(action_type="test", risk_level=3), auto_approve=True)
    stats = engine.get_statistics()

    assert "state_machine" in stats
    assert "policy_engine" in stats
    assert "audit_log" in stats
    assert stats["policy_engine"]["evaluations"] > 0
