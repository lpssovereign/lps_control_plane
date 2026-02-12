"""
State machine for controlled AI execution.

Implements deterministic state transitions with validation.
Observant readers may notice patterns inspired by natural systems.
"""

from typing import Dict, List, Optional, Callable
from datetime import datetime
import logging

from .models import (
    ExecutionState,
    ExecutionContext,
    Action,
    AuditRecord,
    PolicyVerdict,
)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class StateMachine:
    """
    Finite state machine for execution control.

    Key properties:
    - Deterministic transitions
    - Validation at each step
    - Immutable audit trail
    - No silent execution
    """

    # Valid state transitions (directed graph)
    TRANSITIONS = {
        ExecutionState.INIT: [ExecutionState.PLAN],
        ExecutionState.PLAN: [ExecutionState.APPROVE, ExecutionState.REJECTED],
        ExecutionState.APPROVE: [ExecutionState.EXECUTE],
        ExecutionState.EXECUTE: [ExecutionState.VERIFY, ExecutionState.FAILED],
        ExecutionState.VERIFY: [ExecutionState.COMPLETE, ExecutionState.FAILED],
        ExecutionState.COMPLETE: [],  # Terminal state
        ExecutionState.FAILED: [],  # Terminal state
        ExecutionState.REJECTED: [],  # Terminal state
    }

    def __init__(self):
        self.current_context: Optional[ExecutionContext] = None
        self.audit_trail: List[AuditRecord] = []
        self._validators: Dict[ExecutionState, Callable] = {}

    def initialize(self) -> ExecutionContext:
        """Initialize new execution context."""
        self.current_context = ExecutionContext(
            state=ExecutionState.INIT,
            timestamp=datetime.utcnow(),
        )
        self._log_transition(None, ExecutionState.INIT, "Execution initialized")
        return self.current_context

    def transition(
        self,
        target_state: ExecutionState,
        action: Optional[Action] = None,
        verdict: Optional[PolicyVerdict] = None,
        reason: str = "",
    ) -> ExecutionContext:
        """
        Transition to target state with validation.

        Raises:
            ValueError: If transition is invalid
            RuntimeError: If validation fails
        """
        if not self.current_context:
            raise RuntimeError("No active context. Call initialize() first.")

        current_state = self.current_context.state

        # Validate transition is allowed
        if target_state not in self.TRANSITIONS.get(current_state, []):
            raise ValueError(
                f"Invalid transition: {current_state.value} → {target_state.value}"
            )

        # Run state-specific validator if registered
        if target_state in self._validators:
            validator = self._validators[target_state]
            if not validator(self.current_context, action):
                raise RuntimeError(f"Validation failed for {target_state.value}")

        # Create new context (immutable pattern)
        new_actions = list(self.current_context.actions)
        if action:
            new_actions.append(action)

        new_context = ExecutionContext(
            id=self.current_context.id,  # Same execution
            state=target_state,
            actions=tuple(new_actions),  # Convert back to immutable tuple
            approval_required=(verdict == PolicyVerdict.REQUIRE_APPROVAL),
            approved_by=self.current_context.approved_by,
            timestamp=datetime.utcnow(),
            metadata=self.current_context.metadata.copy(),
        )

        # Log transition
        self._log_transition(current_state, target_state, reason, action, verdict)

        # Update state
        self.current_context = new_context
        logger.info(f"State transition: {current_state.value} → {target_state.value}")

        return new_context

    def register_validator(
        self, state: ExecutionState, validator: Callable[[ExecutionContext, Optional[Action]], bool]
    ):
        """
        Register validation function for a state.

        Validator receives (context, action) and returns True if valid.
        """
        self._validators[state] = validator

    def _log_transition(
        self,
        state_from: Optional[ExecutionState],
        state_to: ExecutionState,
        reason: str,
        action: Optional[Action] = None,
        verdict: Optional[PolicyVerdict] = None,
    ):
        """Log state transition to immutable audit trail."""
        record = AuditRecord(
            timestamp=datetime.utcnow(),
            state_from=state_from or ExecutionState.INIT,
            state_to=state_to,
            action=action,
            verdict=verdict,
            reason=reason,
        )
        self.audit_trail.append(record)

    def get_audit_trail(self) -> List[AuditRecord]:
        """
        Return immutable audit trail.

        Note: Records are frozen dataclasses—cannot be modified.
        """
        return self.audit_trail.copy()

    def can_transition(self, target_state: ExecutionState) -> bool:
        """Check if transition to target state is valid."""
        if not self.current_context:
            return target_state == ExecutionState.INIT

        current_state = self.current_context.state
        return target_state in self.TRANSITIONS.get(current_state, [])

    def get_current_state(self) -> Optional[ExecutionState]:
        """Get current execution state."""
        return self.current_context.state if self.current_context else None

    def is_terminal(self) -> bool:
        """Check if execution reached terminal state."""
        if not self.current_context:
            return False

        current_state = self.current_context.state
        return current_state in [
            ExecutionState.COMPLETE,
            ExecutionState.FAILED,
            ExecutionState.REJECTED,
        ]

    def replay(self, audit_trail: List[AuditRecord]) -> ExecutionContext:
        """
        Replay execution from audit trail.

        Enables deterministic reconstruction of execution history.
        This is critical for debugging and verification.
        """
        self.initialize()

        for record in audit_trail:
            if record.state_to == ExecutionState.INIT:
                continue  # Skip initialization record

            self.transition(
                target_state=record.state_to,
                action=record.action,
                verdict=record.verdict,
                reason=record.reason,
            )

        return self.current_context
