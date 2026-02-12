"""
Tests for state machine transitions.
"""

import pytest
from control_plane import StateMachine, ExecutionState, Action, PolicyVerdict


def test_initialization():
    """Test state machine initialization."""
    sm = StateMachine()
    context = sm.initialize()

    assert context.state == ExecutionState.INIT
    assert len(sm.get_audit_trail()) == 1


def test_valid_transitions():
    """Test all valid state transitions."""
    sm = StateMachine()
    sm.initialize()

    # INIT → PLAN
    sm.transition(ExecutionState.PLAN, reason="Planning")
    assert sm.get_current_state() == ExecutionState.PLAN

    # PLAN → APPROVE
    sm.transition(ExecutionState.APPROVE, reason="Approved")
    assert sm.get_current_state() == ExecutionState.APPROVE

    # APPROVE → EXECUTE
    sm.transition(ExecutionState.EXECUTE, reason="Executing")
    assert sm.get_current_state() == ExecutionState.EXECUTE

    # EXECUTE → VERIFY
    sm.transition(ExecutionState.VERIFY, reason="Verifying")
    assert sm.get_current_state() == ExecutionState.VERIFY

    # VERIFY → COMPLETE
    sm.transition(ExecutionState.COMPLETE, reason="Completed")
    assert sm.get_current_state() == ExecutionState.COMPLETE
    assert sm.is_terminal()


def test_invalid_transition():
    """Test that invalid transitions raise ValueError."""
    sm = StateMachine()
    sm.initialize()

    # Cannot go directly from INIT to EXECUTE
    with pytest.raises(ValueError, match="Invalid transition"):
        sm.transition(ExecutionState.EXECUTE)


def test_rejection_path():
    """Test rejection path (PLAN → REJECTED)."""
    sm = StateMachine()
    sm.initialize()

    sm.transition(ExecutionState.PLAN, reason="Planning")
    sm.transition(ExecutionState.REJECTED, reason="Policy denied")

    assert sm.get_current_state() == ExecutionState.REJECTED
    assert sm.is_terminal()


def test_failure_path():
    """Test failure paths."""
    sm = StateMachine()
    sm.initialize()

    # INIT → PLAN → APPROVE → EXECUTE → FAILED
    sm.transition(ExecutionState.PLAN)
    sm.transition(ExecutionState.APPROVE)
    sm.transition(ExecutionState.EXECUTE)
    sm.transition(ExecutionState.FAILED, reason="Execution error")

    assert sm.get_current_state() == ExecutionState.FAILED
    assert sm.is_terminal()


def test_audit_trail_immutability():
    """Test that audit trail records are immutable."""
    sm = StateMachine()
    sm.initialize()

    sm.transition(ExecutionState.PLAN)
    trail = sm.get_audit_trail()

    # Try to modify (should fail due to frozen dataclass)
    with pytest.raises(Exception):  # FrozenInstanceError or AttributeError
        trail[0].reason = "modified"


def test_action_tracking():
    """Test that actions are tracked in context."""
    sm = StateMachine()
    sm.initialize()

    action1 = Action(action_type="read", params={"file": "test.txt"})
    action2 = Action(action_type="write", params={"file": "output.txt"})

    sm.transition(ExecutionState.PLAN, action=action1)
    sm.transition(ExecutionState.APPROVE, action=action2)

    context = sm.current_context
    assert len(context.actions) == 2
    assert context.actions[0].action_type == "read"
    assert context.actions[1].action_type == "write"


def test_replay():
    """Test deterministic replay from audit trail."""
    sm1 = StateMachine()
    sm1.initialize()

    sm1.transition(ExecutionState.PLAN, reason="Plan action")
    sm1.transition(ExecutionState.APPROVE, reason="Approve action")
    sm1.transition(ExecutionState.EXECUTE, reason="Execute action")
    sm1.transition(ExecutionState.VERIFY, reason="Verify result")
    sm1.transition(ExecutionState.COMPLETE, reason="Complete")

    # Get audit trail
    trail = sm1.get_audit_trail()

    # Replay in new state machine
    sm2 = StateMachine()
    final_context = sm2.replay(trail)

    # Should end in same state
    assert final_context.state == ExecutionState.COMPLETE
    assert sm2.get_current_state() == ExecutionState.COMPLETE


def test_can_transition():
    """Test can_transition method."""
    sm = StateMachine()
    sm.initialize()

    # From INIT, can only go to PLAN
    assert sm.can_transition(ExecutionState.PLAN)
    assert not sm.can_transition(ExecutionState.EXECUTE)

    sm.transition(ExecutionState.PLAN)

    # From PLAN, can go to APPROVE or REJECTED
    assert sm.can_transition(ExecutionState.APPROVE)
    assert sm.can_transition(ExecutionState.REJECTED)
    assert not sm.can_transition(ExecutionState.EXECUTE)


def test_validator_registration():
    """Test custom validator registration."""
    sm = StateMachine()

    # Register validator that rejects high-risk actions
    def validate_execute(context, action):
        if action and action.risk_level > 5:
            return False
        return True

    sm.register_validator(ExecutionState.EXECUTE, validate_execute)

    sm.initialize()
    sm.transition(ExecutionState.PLAN)
    sm.transition(ExecutionState.APPROVE)

    # High-risk action should fail validation
    high_risk_action = Action(action_type="delete", risk_level=9)
    with pytest.raises(RuntimeError, match="Validation failed"):
        sm.transition(ExecutionState.EXECUTE, action=high_risk_action)
