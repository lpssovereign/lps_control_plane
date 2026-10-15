from control_plane import Action, PolicyVerdict
from control_plane.delegation import (
    StandingDelegationPolicy,
    default_lps_standing_delegation,
)
from control_plane.tesseract import TesseractExecutionEngine


def gov(**overrides):
    base = {
        "scope": "internal",
        "reversible": True,
        "external_consequence": False,
        "protected_data_release": False,
    }
    base.update(overrides)
    return {"_governance": base}


def test_reversible_internal_commit_is_standing_authorized():
    policy = StandingDelegationPolicy(default_lps_standing_delegation())
    action = Action(action_type="commit", params=gov(), risk_level=2)
    assert policy.evaluate(action) == PolicyVerdict.ALLOW


def test_external_send_is_not_standing_authorized():
    policy = StandingDelegationPolicy(default_lps_standing_delegation())
    action = Action(
        action_type="send_email",
        params=gov(scope="external", external_consequence=True),
        risk_level=4,
    )
    assert policy.evaluate(action) == PolicyVerdict.REQUIRE_APPROVAL


def test_destructive_consequential_action_is_denied():
    policy = StandingDelegationPolicy(default_lps_standing_delegation())
    action = Action(
        action_type="delete_evidence",
        params=gov(reversible=False, destructive=True),
        risk_level=10,
    )
    assert policy.evaluate(action) == PolicyVerdict.DENY


def test_revoked_delegation_no_longer_covers_internal_work():
    delegation = default_lps_standing_delegation()
    revoked = type(delegation)(
        delegation_id=delegation.delegation_id,
        principal=delegation.principal,
        delegate_class=delegation.delegate_class,
        allowed_action_types=delegation.allowed_action_types,
        repository_scope=delegation.repository_scope,
        require_internal=delegation.require_internal,
        require_reversible=delegation.require_reversible,
        active=False,
    )
    policy = StandingDelegationPolicy(revoked)
    action = Action(action_type="commit", params=gov(), risk_level=2)
    assert policy.evaluate(action) == PolicyVerdict.REQUIRE_APPROVAL


def test_engine_executes_internal_document_action_without_callback():
    engine = TesseractExecutionEngine()
    engine.register_executor("document", lambda params: "documented")
    result = engine.execute(
        Action(action_type="document", params=gov(), risk_level=2)
    )
    assert result.success is True
    assert result.output == "documented"


def test_engine_requires_approval_for_external_send():
    engine = TesseractExecutionEngine()
    engine.register_executor("send_email", lambda params: "sent")
    result = engine.execute(
        Action(
            action_type="send_email",
            params=gov(scope="external", external_consequence=True),
            risk_level=4,
        )
    )
    assert result.success is False
    assert "requires approval" in (result.error or "").lower()
