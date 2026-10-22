"""
Policy engine for execution control.

Evaluates actions against registered policies.
Some patterns here may remind observant readers of natural constraint systems.
"""

import logging
from typing import Dict, List, Optional

from .models import Action, PolicyRule, PolicyVerdict

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class PolicyEngine:
    """Policy evaluation engine for action constraints."""

    def __init__(self):
        self.rules: List[PolicyRule] = []
        self._evaluation_count = 0

    def register_rule(self, rule: PolicyRule):
        """Register a policy rule."""
        self.rules.append(rule)
        self.rules.sort(key=lambda r: r.priority, reverse=True)
        logger.info("Registered rule: %s (priority=%s)", rule.rule_type, rule.priority)

    def evaluate(self, action: Action) -> PolicyVerdict:
        """Evaluate an action and return the most restrictive verdict."""
        self._evaluation_count += 1

        if not self.rules:
            return PolicyVerdict.ALLOW

        verdicts = []

        for rule in self.rules:
            if not rule.active:
                continue

            verdict = rule.evaluate(action)
            verdicts.append((rule, verdict))

            if verdict == PolicyVerdict.DENY:
                logger.warning(
                    "Action %s DENIED by rule %s",
                    action.action_type,
                    rule.rule_type,
                )
                return PolicyVerdict.DENY

        final_verdict = self._aggregate_verdicts([v for _, v in verdicts])

        logger.info(
            "Action %s evaluated: %s (%s rules checked)",
            action.action_type,
            final_verdict.value,
            len(verdicts),
        )
        return final_verdict

    def _aggregate_verdicts(self, verdicts: List[PolicyVerdict]) -> PolicyVerdict:
        """Aggregate verdicts using DENY > REQUIRE_APPROVAL > ALLOW."""
        if not verdicts:
            return PolicyVerdict.ALLOW
        if PolicyVerdict.DENY in verdicts:
            return PolicyVerdict.DENY
        if PolicyVerdict.REQUIRE_APPROVAL in verdicts:
            return PolicyVerdict.REQUIRE_APPROVAL
        return PolicyVerdict.ALLOW

    def get_applicable_rules(self, action: Action) -> List[PolicyRule]:
        """Get all active rules that apply to an action."""
        return [
            rule
            for rule in self.rules
            if rule.active and self._rule_applies(rule, action)
        ]

    def _rule_applies(self, rule: PolicyRule, action: Action) -> bool:
        """Check whether a rule's scope applies to an action."""
        return rule.scope in ("global", action.action_type)

    def get_statistics(self) -> Dict[str, int]:
        """Get policy-engine statistics."""
        return {
            "total_rules": len(self.rules),
            "active_rules": sum(1 for r in self.rules if r.active),
            "evaluations": self._evaluation_count,
        }


class RiskBasedPolicy(PolicyRule):
    """Require approval or deny execution based on action risk."""

    def __init__(
        self,
        approval_threshold: int = 7,
        deny_threshold: int = 10,
        priority: int = 100,
    ):
        super().__init__(
            rule_type="risk_based",
            scope="global",
            constraint=f"risk < {deny_threshold}",
            priority=priority,
        )
        self.approval_threshold = approval_threshold
        self.deny_threshold = deny_threshold

    def evaluate(self, action: Action) -> PolicyVerdict:
        """Evaluate an action's risk level."""
        if action.risk_level >= self.deny_threshold:
            return PolicyVerdict.DENY
        if action.risk_level >= self.approval_threshold:
            return PolicyVerdict.REQUIRE_APPROVAL
        return PolicyVerdict.ALLOW


class ResourceConstraintPolicy(PolicyRule):
    """Deny or gate operations as resource usage approaches a limit."""

    def __init__(
        self,
        resource_check_fn,
        threshold: float = 0.9,
        priority: int = 90,
    ):
        super().__init__(
            rule_type="resource_constraint",
            scope="global",
            constraint=f"resource_usage < {threshold}",
            priority=priority,
        )
        self.resource_check_fn = resource_check_fn
        self.threshold = threshold

    def evaluate(self, action: Action) -> PolicyVerdict:
        """Evaluate current resource usage."""
        usage = self.resource_check_fn()

        if usage >= self.threshold:
            return PolicyVerdict.DENY
        if usage >= (self.threshold * 0.8):
            return PolicyVerdict.REQUIRE_APPROVAL
        return PolicyVerdict.ALLOW


class ActionTypePolicy(PolicyRule):
    """Allow, deny, or gate execution based on action type."""

    def __init__(
        self,
        allowed_types: Optional[List[str]] = None,
        denied_types: Optional[List[str]] = None,
        priority: int = 50,
    ):
        super().__init__(
            rule_type="action_type",
            scope="global",
            constraint="type in allowed_list and not in denied_list",
            priority=priority,
        )
        self.allowed_types = set(allowed_types or [])
        self.denied_types = set(denied_types or [])

    def evaluate(self, action: Action) -> PolicyVerdict:
        """Evaluate an action type against deny and allow sets."""
        if action.action_type in self.denied_types:
            return PolicyVerdict.DENY
        if action.action_type in self.allowed_types:
            return PolicyVerdict.ALLOW
        return PolicyVerdict.REQUIRE_APPROVAL
