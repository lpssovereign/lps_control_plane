"""Standing delegation for reversible internal agent work.

This module turns the founder's standing authorization into deterministic policy.
It does not remove the APPROVE state. Covered actions receive PolicyVerdict.ALLOW;
actions outside the delegation remain approval-gated or denied.
"""

from dataclasses import dataclass, field
from typing import FrozenSet, Mapping, Any

from .models import Action, PolicyRule, PolicyVerdict


DEFAULT_INTERNAL_ACTIONS = frozenset({
    "read",
    "search",
    "analyze",
    "document",
    "update_docs",
    "create_schema",
    "update_schema",
    "create_test",
    "run_test",
    "create_fixture",
    "static_analysis",
    "simulate",
    "create_branch",
    "commit",
    "create_issue",
    "create_work_order",
    "draft_ptr",
    "reconcile_state",
    "stage_change",
})

CONSEQUENTIAL_ACTIONS = frozenset({
    "send_email",
    "send_sms",
    "publish",
    "deploy_external",
    "move_money",
    "spend_money",
    "sign_contract",
    "file_legal",
    "change_secret",
    "rotate_secret",
    "delete_evidence",
    "destructive_migration",
    "release_private_data",
    "release_protected_ip",
})


@dataclass(frozen=True)
class StandingDelegation:
    """Versionable standing grant from a principal to an agent class."""

    delegation_id: str
    principal: str
    delegate_class: str = "lps_internal_agent"
    allowed_action_types: FrozenSet[str] = field(
        default_factory=lambda: DEFAULT_INTERNAL_ACTIONS
    )
    repository_scope: str = "lpssovereign/*"
    require_internal: bool = True
    require_reversible: bool = True
    active: bool = True

    def covers(self, action: Action) -> bool:
        if not self.active:
            return False
        if action.action_type not in self.allowed_action_types:
            return False

        meta: Mapping[str, Any] = action.params.get("_governance", {})
        if self.require_internal and meta.get("scope", "internal") != "internal":
            return False
        if self.require_reversible and meta.get("reversible", True) is not True:
            return False
        if meta.get("protected_data_release", False):
            return False
        if meta.get("external_consequence", False):
            return False
        return True


class StandingDelegationPolicy(PolicyRule):
    """Allow covered low-risk internal work; gate or deny everything else."""

    def __init__(
        self,
        delegation: StandingDelegation,
        deny_action_types=CONSEQUENTIAL_ACTIONS,
        priority: int = 1000,
    ):
        super().__init__(
            rule_type="standing_delegation",
            scope="global",
            constraint=f"delegation:{delegation.delegation_id}",
            priority=priority,
        )
        self.delegation = delegation
        self.deny_action_types = frozenset(deny_action_types)

    def evaluate(self, action: Action) -> PolicyVerdict:
        if self.delegation.covers(action):
            return PolicyVerdict.ALLOW

        meta = action.params.get("_governance", {})
        if (
            action.action_type in self.deny_action_types
            and meta.get("destructive", False)
        ):
            return PolicyVerdict.DENY

        # Consequential or unrecognized work is not silently authorized.
        return PolicyVerdict.REQUIRE_APPROVAL


def default_lps_standing_delegation() -> StandingDelegation:
    """Founder standing delegation for routine reversible repository work."""
    return StandingDelegation(
        delegation_id="lps-founder-standing-internal-v1",
        principal="Lalo Pacheco Sánchez",
    )
