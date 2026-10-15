"""Tesseract control-plane configuration."""

from .delegation import (
    StandingDelegation,
    StandingDelegationPolicy,
    default_lps_standing_delegation,
)
from .executor import ExecutionEngine


class TesseractExecutionEngine(ExecutionEngine):
    """Execution engine configured with a standing internal delegation."""

    def __init__(self, audit_log=None, delegation: StandingDelegation | None = None):
        super().__init__(audit_log=audit_log)
        self.standing_delegation = delegation or default_lps_standing_delegation()
        self.policy_engine.register_rule(
            StandingDelegationPolicy(self.standing_delegation)
        )
