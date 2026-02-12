"""
Controlled execution engine.

Coordinates state machine, policy engine, and audit logging
for safe AI agent execution.
"""

import time
import logging
from typing import Any, Callable, Optional

from .models import (
    Action,
    ExecutionState,
    ExecutionContext,
    ExecutionResult,
    PolicyVerdict,
)
from .state_machine import StateMachine
from .policy_engine import PolicyEngine
from .audit_log import AuditLog

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class ExecutionEngine:
    """
    Controlled execution engine.

    Orchestrates:
    - State transitions
    - Policy enforcement
    - Action execution
    - Audit logging

    No action executes without passing through:
    INIT → PLAN → APPROVE → EXECUTE → VERIFY → COMPLETE
    """

    def __init__(self, audit_log: Optional[AuditLog] = None):
        self.state_machine = StateMachine()
        self.policy_engine = PolicyEngine()
        self.audit_log = audit_log or AuditLog()
        self._action_executors: dict[str, Callable] = {}

    def register_executor(self, action_type: str, executor: Callable[[dict], Any]):
        """
        Register executor function for action type.

        executor: function(params) -> result
        """
        self._action_executors[action_type] = executor
        logger.info(f"Registered executor for: {action_type}")

    def execute(
        self,
        action: Action,
        auto_approve: bool = False,
        approval_callback: Optional[Callable[[Action], bool]] = None,
    ) -> ExecutionResult:
        """
        Execute action through controlled pipeline.

        Process:
        1. INIT: Initialize execution context
        2. PLAN: Validate action structure
        3. APPROVE: Check policies, get approval if needed
        4. EXECUTE: Run action executor
        5. VERIFY: Validate execution result
        6. COMPLETE: Finalize and log

        Args:
            action: Action to execute
            auto_approve: Skip approval for low-risk actions
            approval_callback: Function to request approval

        Returns:
            ExecutionResult with outcome
        """
        start_time = time.time()

        try:
            # INIT
            context = self.state_machine.initialize()
            self.audit_log.log(context, action, "Execution started")

            # PLAN
            context = self.state_machine.transition(
                ExecutionState.PLAN, action, reason="Planning action"
            )
            self.audit_log.log(context, action, "Action planned")

            # Evaluate policy
            verdict = self.policy_engine.evaluate(action)

            # APPROVE
            if verdict == PolicyVerdict.DENY:
                context = self.state_machine.transition(
                    ExecutionState.REJECTED,
                    action,
                    verdict,
                    "Action denied by policy",
                )
                self.audit_log.log(context, action, "Action rejected")

                return ExecutionResult(
                    success=False,
                    error="Action denied by policy",
                    duration_ms=(time.time() - start_time) * 1000,
                )

            elif verdict == PolicyVerdict.REQUIRE_APPROVAL:
                if auto_approve:
                    logger.warning("Auto-approval enabled for high-risk action")
                    approved = True
                elif approval_callback:
                    approved = approval_callback(action)
                else:
                    raise RuntimeError(
                        "Action requires approval but no approval mechanism provided"
                    )

                if not approved:
                    context = self.state_machine.transition(
                        ExecutionState.REJECTED,
                        action,
                        verdict,
                        "Approval denied",
                    )
                    self.audit_log.log(context, action, "Approval denied")

                    return ExecutionResult(
                        success=False,
                        error="Approval denied",
                        duration_ms=(time.time() - start_time) * 1000,
                    )

            context = self.state_machine.transition(
                ExecutionState.APPROVE, action, verdict, "Action approved"
            )
            self.audit_log.log(context, action, "Action approved")

            # EXECUTE
            context = self.state_machine.transition(
                ExecutionState.EXECUTE, action, reason="Executing action"
            )

            executor = self._action_executors.get(action.action_type)
            if not executor:
                raise RuntimeError(f"No executor registered for: {action.action_type}")

            try:
                output = executor(action.params)
                execution_success = True
                execution_error = None
            except Exception as e:
                output = None
                execution_success = False
                execution_error = str(e)
                logger.error(f"Execution failed: {e}")

            self.audit_log.log(
                context,
                action,
                f"Execution {'succeeded' if execution_success else 'failed'}",
            )

            # VERIFY
            if execution_success:
                context = self.state_machine.transition(
                    ExecutionState.VERIFY, action, reason="Verifying result"
                )
                # TODO: Add result verification logic
                context = self.state_machine.transition(
                    ExecutionState.COMPLETE, action, reason="Execution completed"
                )
                self.audit_log.log(context, action, "Execution completed")
            else:
                context = self.state_machine.transition(
                    ExecutionState.FAILED,
                    action,
                    reason=f"Execution failed: {execution_error}",
                )
                self.audit_log.log(context, action, "Execution failed")

            duration_ms = (time.time() - start_time) * 1000

            return ExecutionResult(
                success=execution_success,
                output=output,
                error=execution_error,
                duration_ms=duration_ms,
            )

        except Exception as e:
            logger.error(f"Execution engine error: {e}")
            duration_ms = (time.time() - start_time) * 1000

            return ExecutionResult(
                success=False, error=str(e), duration_ms=duration_ms
            )

    def get_audit_trail(self):
        """Get complete audit trail."""
        return self.state_machine.get_audit_trail()

    def get_statistics(self):
        """Get execution statistics."""
        return {
            "state_machine": {
                "current_state": self.state_machine.get_current_state(),
                "is_terminal": self.state_machine.is_terminal(),
                "audit_records": len(self.state_machine.audit_trail),
            },
            "policy_engine": self.policy_engine.get_statistics(),
            "audit_log": {
                "total_entries": len(self.audit_log.entries),
            },
        }
