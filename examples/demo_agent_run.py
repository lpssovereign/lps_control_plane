#!/usr/bin/env python3
"""
Demo: AI agent execution with control plane.

Shows how to safely execute AI agent actions with:
- State machine control
- Policy enforcement
- Audit logging
- Approval gates
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from control_plane import ExecutionEngine, Action, RiskBasedPolicy


def demo_simple_execution():
    """Demo: Simple action execution."""
    print("\n" + "=" * 70)
    print("DEMO 1: Simple Execution")
    print("=" * 70)

    engine = ExecutionEngine()

    # Register executor
    def read_file(params):
        filename = params.get("file", "unknown")
        return f"Contents of {filename}"

    engine.register_executor("read_file", read_file)

    # Execute action
    action = Action(
        action_type="read_file", params={"file": "data.txt"}, risk_level=2
    )

    result = engine.execute(action, auto_approve=True)

    print(f"✅ Execution {'succeeded' if result.success else 'failed'}")
    print(f"   Output: {result.output}")
    print(f"   Duration: {result.duration_ms:.2f}ms")
    print(f"   Audit trail: {len(engine.get_audit_trail())} records")


def demo_policy_enforcement():
    """Demo: Policy-based action control."""
    print("\n" + "=" * 70)
    print("DEMO 2: Policy Enforcement")
    print("=" * 70)

    engine = ExecutionEngine()

    # Add risk-based policy
    engine.policy_engine.register_rule(
        RiskBasedPolicy(approval_threshold=7, deny_threshold=10)
    )

    # Register executor
    engine.register_executor("delete_file", lambda params: f"Deleted {params['file']}")

    # Low risk action (should auto-approve)
    low_risk = Action(action_type="delete_file", params={"file": "temp.txt"}, risk_level=3)

    result = engine.execute(low_risk, auto_approve=True)
    print(f"📝 Low risk action: {'✅ succeeded' if result.success else '❌ failed'}")

    # High risk action (requires approval)
    high_risk = Action(
        action_type="delete_file", params={"file": "critical_data.db"}, risk_level=8
    )

    def approval_callback(action):
        print(f"⚠️  Approval requested for: {action.action_type}")
        print(f"   Risk level: {action.risk_level}/10")
        print(f"   Params: {action.params}")
        # Simulate user denial
        return False

    engine.state_machine = type(engine.state_machine)()  # Reset
    result = engine.execute(high_risk, approval_callback=approval_callback)

    print(f"🛡️  High risk action: {'✅ succeeded' if result.success else '❌ blocked'}")
    if not result.success:
        print(f"   Reason: {result.error}")


def demo_audit_trail():
    """Demo: Audit trail and replay."""
    print("\n" + "=" * 70)
    print("DEMO 3: Audit Trail & Replay")
    print("=" * 70)

    engine = ExecutionEngine()
    engine.register_executor("compute", lambda params: params["x"] * params["y"])

    # Execute several actions
    actions = [
        Action(action_type="compute", params={"x": 2, "y": 3}, risk_level=1),
        Action(action_type="compute", params={"x": 5, "y": 7}, risk_level=1),
        Action(action_type="compute", params={"x": 10, "y": 12}, risk_level=1),
    ]

    for action in actions:
        result = engine.execute(action, auto_approve=True)
        print(f"   Computed: {result.output}")
        engine.state_machine = type(engine.state_machine)()  # Reset

    # Verify audit log integrity
    is_valid = engine.audit_log.verify_integrity()
    print(f"\n🔍 Audit trail integrity: {'✅ Valid' if is_valid else '❌ Corrupted'}")
    print(f"   Total entries: {len(engine.audit_log)}")

    # Export audit log
    exported = engine.audit_log.export()
    print(f"   Exported size: {len(exported)} bytes")

    # Demonstrate replay
    from control_plane import AuditLog

    replayed = AuditLog().replay(exported)
    print(f"✅ Replayed audit log: {len(replayed)} entries")


def demo_statistics():
    """Demo: Execution statistics."""
    print("\n" + "=" * 70)
    print("DEMO 4: Execution Statistics")
    print("=" * 70)

    engine = ExecutionEngine()
    engine.policy_engine.register_rule(RiskBasedPolicy())
    engine.register_executor("test", lambda params: "result")

    # Execute multiple actions
    for i in range(10):
        action = Action(action_type="test", params={"i": i}, risk_level=i % 8)
        engine.execute(action, auto_approve=True)
        engine.state_machine = type(engine.state_machine)()

    # Get statistics
    stats = engine.get_statistics()

    print("📊 Execution Statistics:")
    print(f"   State machine:")
    print(f"      - Audit records: {stats['state_machine']['audit_records']}")
    print(f"   Policy engine:")
    print(f"      - Total rules: {stats['policy_engine']['total_rules']}")
    print(f"      - Evaluations: {stats['policy_engine']['evaluations']}")
    print(f"   Audit log:")
    print(f"      - Total entries: {stats['audit_log']['total_entries']}")


def main():
    """Run all demos."""
    print("\n" + "=" * 70)
    print("AI CONTROL PLANE - DEMO SUITE")
    print("=" * 70)

    demo_simple_execution()
    demo_policy_enforcement()
    demo_audit_trail()
    demo_statistics()

    print("\n" + "=" * 70)
    print("✅ All demos complete")
    print("=" * 70 + "\n")


if __name__ == "__main__":
    main()
