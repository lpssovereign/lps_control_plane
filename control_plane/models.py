"""
Core data models for AI Control Plane.

Defines immutable execution states, actions, and audit records.
"""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional
import uuid


class ExecutionState(Enum):
    """Execution state machine stages."""
    INIT = "init"
    PLAN = "plan"
    APPROVE = "approve"
    EXECUTE = "execute"
    VERIFY = "verify"
    COMPLETE = "complete"
    FAILED = "failed"
    REJECTED = "rejected"


class PolicyVerdict(Enum):
    """Policy evaluation results."""
    ALLOW = "allow"
    DENY = "deny"
    REQUIRE_APPROVAL = "require_approval"


@dataclass(frozen=True)  # Immutable by design
class Action:
    """
    Represents a single executable action.

    Immutability ensures audit integrity—actions cannot be
    retroactively modified after execution.
    """
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    action_type: str = ""
    params: Dict[str, Any] = field(default_factory=dict)
    risk_level: int = 0  # 0-10 scale
    timestamp: datetime = field(default_factory=datetime.utcnow)

    def __post_init__(self):
        """Validate action on creation."""
        if not self.action_type:
            raise ValueError("Action must have a type")
        if not 0 <= self.risk_level <= 10:
            raise ValueError("Risk level must be 0-10")


@dataclass(frozen=True)
class ExecutionContext:
    """
    Execution context tracks state transitions.

    Immutable snapshots enable deterministic replay.
    """
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    state: ExecutionState = ExecutionState.INIT
    actions: tuple = field(default_factory=tuple)  # Immutable list
    approval_required: bool = False
    approved_by: Optional[str] = None
    timestamp: datetime = field(default_factory=datetime.utcnow)
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class AuditRecord:
    """
    Immutable audit record.

    Once created, cannot be modified—ensures forensic integrity.
    """
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    timestamp: datetime = field(default_factory=datetime.utcnow)
    state_from: ExecutionState = ExecutionState.INIT
    state_to: ExecutionState = ExecutionState.INIT
    action: Optional[Action] = None
    verdict: Optional[PolicyVerdict] = None
    reason: str = ""
    context: Dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class PolicyRule:
    """
    Policy rule for execution control.

    Rules define constraints on what actions are permissible.
    """
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    rule_type: str = ""
    scope: str = "global"
    constraint: str = ""
    priority: int = 0
    active: bool = True

    def evaluate(self, action: Action) -> PolicyVerdict:
        """
        Evaluate action against rule.

        Default implementation—override in subclasses.
        """
        # Simple risk-based evaluation
        if action.risk_level >= 8:
            return PolicyVerdict.REQUIRE_APPROVAL
        elif action.risk_level >= 5:
            return PolicyVerdict.ALLOW
        else:
            return PolicyVerdict.ALLOW


@dataclass
class ExecutionResult:
    """
    Result of execution (mutable for practical use).

    Contains outcome, errors, and metrics.
    """
    success: bool = False
    output: Any = None
    error: Optional[str] = None
    duration_ms: float = 0.0
    timestamp: datetime = field(default_factory=datetime.utcnow)
