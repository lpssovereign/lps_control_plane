"""
Policy engine for execution control.

Evaluates actions against registered policies.
Some patterns here may remind observant readers of natural constraint systems.
"""

from typing import List, Dict, Optional
import logging

from .models import Action, PolicyRule, PolicyVerdict

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class PolicyEngine:
    """
    Policy evaluation engine.

    Enforces constraints on action execution through rule-based system.
    """

    def __init__(self):
        self.rules: List[PolicyRule] = []
        self._evaluation_count = 0

    def register_rule(self, rule: PolicyRule):
        """Register a policy rule."""
        self.rules.append(rule)
        # Sort by priority (higher priority first)
        self.rules.sort(key=lambda r: r.priority, reverse=True)
        logger.info(f"Registered rule: {rule.rule_type} (priority={rule.priority})")

    def evaluate(self, action: Action) -> PolicyVerdict:
        """
        Evaluate action against all active rules.

        Returns most restrictive verdict from all matching rules.

        Rule evaluation follows priority order:
        1. DENY (most restrictive)
        2. REQUIRE_APPROVAL
        3. ALLOW (least restrictive)
        """
        self._evaluation_count += 1

        if not self.rules:
            # No rules = default allow (permissive)
            return PolicyVerdict.ALLOW

        verdicts = []

        for rule in self.rules:
            if not rule.active:
                continue

            # Evaluate rule
            verdict = rule.evaluate(action)
            verdicts.append((rule, verdict))

            # Early exit on DENY (most restrictive)
            if verdict == PolicyVerdict.DENY:
                logger.warning(
                    f"Action {action.action_type} DENIED by rule {rule.rule_type}"
                )
                return PolicyVerdict.DENY

        # Aggregate verdicts (most restrictive wins)
        final_verdict = self._aggregate_verdicts([v for _, v in verdicts])

        logger.info(
            f"Action {action.action_type} evaluated: {final_verdict.value} "
            f"({len(verdicts)} rules checked)"
        )

        return final_verdict

    def _aggregate_verdicts(self, verdicts: List[PolicyVerdict]) -> PolicyVerdict:
        """
        Aggregate multiple verdicts into final verdict.

        Priority: DENY > REQUIRE_APPROVAL > ALLOW
        """
        if not verdicts:
            return PolicyVerdict.ALLOW

        if PolicyVerdict.DENY in verdicts:
            return PolicyVerdict.DENY
        elif PolicyVerdict.REQUIRE_APPROVAL in verdicts:
            return PolicyVerdict.REQUIRE_APPROVAL
        else:
            return PolicyVerdict.ALLOW

    def get_applicable_rules(self, action: Action) -> List[PolicyRule]:
        """Get all active rules that apply to this action."""
        return [
            rule
            for rule in self.rules
            if rule.active and self._rule_applies(rule, action)
        ]

    def _rule_applies(self, rule: PolicyRule, action: Action) -> bool:
        """
        Check if rule applies to action.

        Override this for more sophisticated matching.
        """
        # Simple scope matching
        if rule.scope == "global":
            return True

        if rule.scope == action.action_type:
            return True

        return False

    def get_statistics(self) -> Dict[str, int]:
        """Get policy engine statistics."""
        return {
            "total_rules": len(self.rules),
            "active_rules": sum(1 for r in self.rules if r.active),
            "evaluations": self._evaluation_count,
        }


class RiskBasedPolicy(PolicyRule):
    """
    Policy based on action risk level.

    High-risk actions require approval.
    This mirrors natural systems where dangerous operations
    require higher activation energy.
    """

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
        """Evaluate based on risk level."""
        if action.risk_level >= self.deny_threshold:
            return PolicyVerdict.DENY
        elif action.risk_level >= self.approval_threshold:
            return PolicyVerdict.REQUIRE_APPROVAL
        else:
            return PolicyVerdict.ALLOW


class ResourceConstraintPolicy(PolicyRule):
    """
    Policy based on resource availability.

    Rejects operations when resources are constrained.
    Those familiar with biological homeostasis may recognize this pattern.
    """

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
        """Evaluate based on resource availability."""
        usage = self.resource_check_fn()

        if usage >= self.threshold:
            # System under stress—reject new operations
            return PolicyVerdict.DENY
        elif usage >= (self.threshold * 0.8):
            # Approaching limits—require approval
            return PolicyVerdict.REQUIRE_APPROVAL
        else:
            return PolicyVerdict.ALLOW


class ActionTypePolicy(PolicyRule):
    """
    Policy based on action type.

    Allows/denies specific action types.
    """

    def __init__(
        self,
        allowed_types: List[str],
        denied_types: List[str] = None,
        priority: int = 50,
    ):
        super().__init__(
            rule_type="action_type",
            scope="global",
            constraint="type in allowed_list",
            priority=priority,
        )
        self.allowed_types = set(allowed_types)
        self.denied_types = set(denied_types or [])

    def evaluate(self, action: Action) -> PolicyVerdict:
        """Evaluate based on action type."""
        if action.action_type in self.denied_types:
            return PolicyVerdict.DENY
        elif action.action_type in self.allowed_types:
            return PolicyVerdict.ALLOW
        else:
            # Unknown action type—require approval
            return PolicyVerdict.REQUIRE_APPROVAL
