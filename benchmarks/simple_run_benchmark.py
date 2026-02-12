#!/usr/bin/env python3
"""
Simple benchmark for AI Control Plane.

Measures:
- State transitions per second
- Policy evaluations per second
- End-to-end execution throughput
"""

import time
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from control_plane import (
    ExecutionEngine,
    Action,
    RiskBasedPolicy,
    StateMachine,
    ExecutionState,
)


def benchmark_state_transitions(iterations=10000):
    """Benchmark state machine transitions."""
    print(f"\n📊 Benchmarking {iterations:,} state transitions...")

    sm = StateMachine()
    start = time.time()

    for _ in range(iterations):
        sm.initialize()
        sm.transition(ExecutionState.PLAN)
        sm.transition(ExecutionState.APPROVE)
        sm.transition(ExecutionState.EXECUTE)
        sm.transition(ExecutionState.VERIFY)
        sm.transition(ExecutionState.COMPLETE)

        # Reset for next iteration
        sm = StateMachine()

    elapsed = time.time() - start
    ops_per_sec = iterations / elapsed

    print(f"✅ {ops_per_sec:,.0f} transitions/sec")
    print(f"   ({elapsed:.2f}s total, {elapsed/iterations*1000:.3f}ms per transition)")

    return ops_per_sec


def benchmark_policy_evaluation(iterations=50000):
    """Benchmark policy engine evaluation."""
    print(f"\n📊 Benchmarking {iterations:,} policy evaluations...")

    engine = ExecutionEngine()
    engine.policy_engine.register_rule(RiskBasedPolicy())

    actions = [
        Action(action_type=f"action_{i % 10}", risk_level=i % 10)
        for i in range(100)
    ]

    start = time.time()

    for i in range(iterations):
        action = actions[i % len(actions)]
        engine.policy_engine.evaluate(action)

    elapsed = time.time() - start
    ops_per_sec = iterations / elapsed

    print(f"✅ {ops_per_sec:,.0f} evaluations/sec")
    print(f"   ({elapsed:.2f}s total, {elapsed/iterations*1000:.3f}ms per evaluation)")

    return ops_per_sec


def benchmark_end_to_end_execution(iterations=1000):
    """Benchmark complete execution pipeline."""
    print(f"\n📊 Benchmarking {iterations:,} end-to-end executions...")

    engine = ExecutionEngine()
    engine.policy_engine.register_rule(RiskBasedPolicy())

    # Simple executor
    engine.register_executor("compute", lambda params: params.get("x", 0) * 2)

    actions = [
        Action(action_type="compute", params={"x": i}, risk_level=3)
        for i in range(100)
    ]

    start = time.time()

    for i in range(iterations):
        action = actions[i % len(actions)]
        result = engine.execute(action, auto_approve=True)

        # Reset state machine for next execution
        engine.state_machine = StateMachine()

    elapsed = time.time() - start
    ops_per_sec = iterations / elapsed

    print(f"✅ {ops_per_sec:,.0f} executions/sec")
    print(f"   ({elapsed:.2f}s total, {elapsed/iterations*1000:.3f}ms per execution)")

    return ops_per_sec


def benchmark_audit_log_integrity(iterations=10000):
    """Benchmark audit log integrity verification."""
    print(f"\n📊 Benchmarking audit log integrity checks...")

    engine = ExecutionEngine()
    engine.register_executor("test", lambda params: "result")

    # Generate audit trail
    for i in range(100):
        action = Action(action_type="test", params={"i": i}, risk_level=3)
        engine.execute(action, auto_approve=True)
        engine.state_machine = StateMachine()

    # Benchmark verification
    start = time.time()

    for _ in range(iterations):
        is_valid = engine.audit_log.verify_integrity()
        assert is_valid

    elapsed = time.time() - start
    ops_per_sec = iterations / elapsed

    print(f"✅ {ops_per_sec:,.0f} verifications/sec")
    print(f"   ({elapsed:.2f}s total, {elapsed/iterations*1000:.3f}ms per verification)")
    print(f"   (100 entries per verification)")

    return ops_per_sec


def main():
    """Run all benchmarks."""
    print("=" * 70)
    print("AI CONTROL PLANE - BENCHMARK SUITE")
    print("=" * 70)

    results = {}

    results["state_transitions"] = benchmark_state_transitions(10000)
    results["policy_evaluations"] = benchmark_policy_evaluation(50000)
    results["end_to_end"] = benchmark_end_to_end_execution(1000)
    results["audit_integrity"] = benchmark_audit_log_integrity(10000)

    print("\n" + "=" * 70)
    print("SUMMARY")
    print("=" * 70)

    for name, ops_per_sec in results.items():
        print(f"{name:25s}: {ops_per_sec:>15,.0f} ops/sec")

    print("\n✅ Benchmarks complete")


if __name__ == "__main__":
    main()
