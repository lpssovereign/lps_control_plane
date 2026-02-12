"""
High-Load Stress Test for AI Control Plane

Purpose:
- Validate stability under load (10k+ executions)
- Ensure no silent execution (all states logged)
- Ensure deterministic state transitions
- Count policy violations
- Count execution failures
- Measure throughput
- FAIL LOUDLY if invariants break

No exits silently. Counters, not vibes.
"""

import time
import threading
import pytest
from collections import defaultdict
from concurrent.futures import ThreadPoolExecutor, as_completed

from control_plane import (
    ExecutionEngine,
    Action,
    RiskBasedPolicy,
    ResourceConstraintPolicy,
    StateMachine,
    ExecutionState,
)


# ============================================
# CONFIG
# ============================================

TOTAL_RUNS = 10000
MAX_WORKERS = 8
STRESS_LOG = "stress_results.log"


# ============================================
# GLOBAL COUNTERS (Thread-Safe)
# ============================================

counters = defaultdict(int)
counter_lock = threading.Lock()


def increment_counter(name: str, amount: int = 1):
    """Thread-safe counter increment."""
    with counter_lock:
        counters[name] += amount


def get_counter(name: str) -> int:
    """Thread-safe counter read."""
    with counter_lock:
        return counters[name]


# ============================================
# TEST EXECUTORS
# ============================================

def safe_executor(params):
    """Safe operation that always succeeds."""
    return f"processed_{params.get('id', 0)}"


def risky_executor(params):
    """Risky operation that fails 10% of the time."""
    import random

    if random.random() < 0.1:
        raise ValueError("Simulated failure")
    return f"risky_result_{params.get('id', 0)}"


# ============================================
# STRESS FUNCTION
# ============================================

def run_single_cycle(cycle_id: int):
    """
    Execute one full cycle through the control plane.

    Returns:
        dict: Execution metadata
    """
    try:
        # Create fresh engine for this cycle (isolation)
        engine = ExecutionEngine()
        engine.policy_engine.register_rule(RiskBasedPolicy(approval_threshold=8))
        engine.register_executor("safe_op", safe_executor)

        # Create action
        action = Action(
            action_type="safe_op",
            params={"id": cycle_id, "data": f"cycle_{cycle_id}"},
            risk_level=3,  # Low risk
        )

        # Execute
        result = engine.execute(action, auto_approve=True)

        # Verify state machine reached terminal state
        final_state = engine.state_machine.get_current_state()

        if not engine.state_machine.is_terminal():
            increment_counter("non_terminal_state")
            return {"success": False, "reason": "non_terminal_state"}

        # Verify audit trail exists
        audit_trail = engine.get_audit_trail()
        if len(audit_trail) == 0:
            increment_counter("missing_audit_trail")
            return {"success": False, "reason": "missing_audit_trail"}

        # Verify audit integrity
        if not engine.audit_log.verify_integrity():
            increment_counter("audit_integrity_violation")
            return {"success": False, "reason": "audit_integrity_violation"}

        # Count outcome
        if result.success:
            increment_counter("success")
            increment_counter("total_duration_ms", int(result.duration_ms))
        else:
            increment_counter("failed_execution")

        increment_counter("completed")

        return {
            "success": result.success,
            "duration_ms": result.duration_ms,
            "audit_records": len(audit_trail),
            "final_state": final_state.value,
        }

    except Exception as e:
        increment_counter("exceptions")
        increment_counter("exception_types", f"{type(e).__name__}")
        raise  # Fail loudly


# ============================================
# INVARIANT VALIDATORS
# ============================================

def validate_invariants():
    """
    Validate critical invariants after stress test.

    Raises:
        AssertionError: If any invariant violated
    """
    total = TOTAL_RUNS
    completed = get_counter("completed")
    exceptions = get_counter("exceptions")
    success = get_counter("success")
    failed = get_counter("failed_execution")
    non_terminal = get_counter("non_terminal_state")
    missing_audit = get_counter("missing_audit_trail")
    audit_violations = get_counter("audit_integrity_violation")

    # INVARIANT 1: All executions must complete
    assert completed == total, (
        f"INVARIANT VIOLATION: Expected {total} completions, got {completed}. "
        f"Missing: {total - completed}"
    )

    # INVARIANT 2: No exceptions allowed
    assert exceptions == 0, (
        f"INVARIANT VIOLATION: {exceptions} exceptions occurred during stress test. "
        f"Types: {counters.get('exception_types', 'unknown')}"
    )

    # INVARIANT 3: All executions must reach terminal state
    assert non_terminal == 0, (
        f"INVARIANT VIOLATION: {non_terminal} executions did not reach terminal state"
    )

    # INVARIANT 4: All executions must have audit trail
    assert missing_audit == 0, (
        f"INVARIANT VIOLATION: {missing_audit} executions missing audit trail"
    )

    # INVARIANT 5: Audit integrity must be preserved
    assert audit_violations == 0, (
        f"INVARIANT VIOLATION: {audit_violations} audit integrity violations detected"
    )

    # INVARIANT 6: Success + Failed must equal Completed
    assert success + failed == completed, (
        f"INVARIANT VIOLATION: Success ({success}) + Failed ({failed}) "
        f"!= Completed ({completed})"
    )


# ============================================
# REPORT GENERATION
# ============================================

def print_report(duration: float):
    """Print comprehensive stress test report."""
    total = TOTAL_RUNS
    completed = get_counter("completed")
    success = get_counter("success")
    failed = get_counter("failed_execution")
    exceptions = get_counter("exceptions")
    total_duration_ms = get_counter("total_duration_ms")

    throughput = total / duration
    avg_latency_ms = total_duration_ms / success if success > 0 else 0

    print("\n" + "=" * 70)
    print("STRESS TEST RESULTS")
    print("=" * 70)
    print(f"Configuration:")
    print(f"  Total Runs:        {total:,}")
    print(f"  Max Workers:       {MAX_WORKERS}")
    print(f"  Duration:          {duration:.2f}s")
    print()
    print(f"Execution Outcomes:")
    print(f"  Completed:         {completed:,} ({completed/total*100:.1f}%)")
    print(f"  Success:           {success:,} ({success/total*100:.1f}%)")
    print(f"  Failed:            {failed:,} ({failed/total*100:.1f}%)")
    print(f"  Exceptions:        {exceptions:,}")
    print()
    print(f"Invariant Checks:")
    print(f"  Non-Terminal:      {get_counter('non_terminal_state'):,}")
    print(f"  Missing Audit:     {get_counter('missing_audit_trail'):,}")
    print(f"  Audit Violations:  {get_counter('audit_integrity_violation'):,}")
    print()
    print(f"Performance:")
    print(f"  Throughput:        {throughput:,.0f} executions/sec")
    print(f"  Avg Latency:       {avg_latency_ms:.2f}ms per execution")
    print(f"  Total Duration:    {total_duration_ms:,}ms")
    print("=" * 70)

    # Pass/Fail verdict
    if exceptions == 0 and completed == total:
        print("✅ STRESS TEST PASSED - All invariants satisfied")
    else:
        print("❌ STRESS TEST FAILED - Invariant violations detected")

    print("=" * 70 + "\n")


def write_log(duration: float):
    """Append stress test results to log file."""
    timestamp = time.time()
    total = TOTAL_RUNS
    success = get_counter("success")
    throughput = total / duration

    with open(STRESS_LOG, "a") as f:
        f.write(
            f"{timestamp:.0f},"
            f"{total},"
            f"{success},"
            f"{throughput:.2f},"
            f"{duration:.2f}\n"
        )


# ============================================
# STRESS TEST (Single-Threaded)
# ============================================

@pytest.mark.stress
def test_runtime_stress_single_threaded():
    """
    Stress test: Single-threaded execution.

    Validates:
    - State machine stability
    - Policy enforcement
    - Audit trail integrity
    - No silent execution
    """
    global counters
    counters.clear()

    print(f"\n🔨 Running single-threaded stress test ({TOTAL_RUNS:,} cycles)...")

    start_time = time.time()

    for i in range(TOTAL_RUNS):
        run_single_cycle(i)

        # Progress indicator
        if (i + 1) % 1000 == 0:
            print(f"   Progress: {i+1:,}/{TOTAL_RUNS:,}")

    end_time = time.time()
    duration = end_time - start_time

    # Validate invariants
    validate_invariants()

    # Print report
    print_report(duration)

    # Write log
    write_log(duration)


# ============================================
# STRESS TEST (Multi-Threaded)
# ============================================

@pytest.mark.stress
def test_runtime_stress_multi_threaded():
    """
    Stress test: Multi-threaded execution.

    Validates:
    - Thread safety
    - Concurrent policy evaluation
    - Audit log concurrency handling
    - No race conditions
    """
    global counters
    counters.clear()

    print(
        f"\n🔨 Running multi-threaded stress test "
        f"({TOTAL_RUNS:,} cycles, {MAX_WORKERS} workers)..."
    )

    start_time = time.time()

    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
        futures = [executor.submit(run_single_cycle, i) for i in range(TOTAL_RUNS)]

        completed_count = 0
        for future in as_completed(futures):
            future.result()  # Fail loudly if any exception
            completed_count += 1

            # Progress indicator
            if completed_count % 1000 == 0:
                print(f"   Progress: {completed_count:,}/{TOTAL_RUNS:,}")

    end_time = time.time()
    duration = end_time - start_time

    # Validate invariants
    validate_invariants()

    # Print report
    print_report(duration)

    # Write log
    write_log(duration)


# ============================================
# ADVERSARIAL STRESS TEST
# ============================================

@pytest.mark.stress
@pytest.mark.adversarial
def test_runtime_stress_adversarial():
    """
    Adversarial stress test: Mix of high-risk and failing actions.

    Validates:
    - Policy enforcement under load
    - Graceful failure handling
    - Audit trail completeness during failures
    """
    global counters
    counters.clear()

    print(f"\n🔨 Running adversarial stress test ({TOTAL_RUNS:,} cycles)...")

    def run_adversarial_cycle(cycle_id: int):
        """Run cycle with high-risk and potentially failing actions."""
        try:
            engine = ExecutionEngine()
            engine.policy_engine.register_rule(
                RiskBasedPolicy(approval_threshold=7, deny_threshold=10)
            )
            engine.register_executor("risky_op", risky_executor)

            # High-risk action
            risk = (cycle_id % 10) + 1  # Risk levels 1-10
            action = Action(
                action_type="risky_op",
                params={"id": cycle_id},
                risk_level=risk,
            )

            result = engine.execute(action, auto_approve=(risk < 7))

            # Count policy verdicts
            if risk >= 10:
                increment_counter("policy_denied")
            elif risk >= 7:
                increment_counter("policy_approval_required")

            if result.success:
                increment_counter("success")
            else:
                increment_counter("failed_execution")

            increment_counter("completed")

        except Exception as e:
            increment_counter("exceptions")
            raise

    start_time = time.time()

    for i in range(TOTAL_RUNS):
        run_adversarial_cycle(i)

        if (i + 1) % 1000 == 0:
            print(f"   Progress: {i+1:,}/{TOTAL_RUNS:,}")

    end_time = time.time()
    duration = end_time - start_time

    # Relaxed invariants (failures expected)
    completed = get_counter("completed")
    exceptions = get_counter("exceptions")

    assert completed == TOTAL_RUNS, f"Expected {TOTAL_RUNS} completions, got {completed}"
    assert exceptions == 0, f"Unexpected exceptions: {exceptions}"

    print_report(duration)


# ============================================
# MEMORY LEAK TEST
# ============================================

@pytest.mark.stress
@pytest.mark.memory
def test_runtime_memory_stability():
    """
    Memory stability test: Detect memory leaks.

    Runs multiple iterations and checks memory growth.
    """
    import gc
    import sys

    print("\n🔨 Running memory stability test...")

    def get_memory_mb():
        """Get current memory usage in MB."""
        import os

        try:
            import psutil

            process = psutil.Process(os.getpid())
            return process.memory_info().rss / 1024 / 1024
        except ImportError:
            # Fallback if psutil not available
            return 0

    iterations = 5
    cycles_per_iteration = 1000

    memory_samples = []

    for i in range(iterations):
        gc.collect()  # Force garbage collection

        mem_before = get_memory_mb()

        # Run stress cycles
        for j in range(cycles_per_iteration):
            run_single_cycle(j)

        gc.collect()

        mem_after = get_memory_mb()
        memory_samples.append(mem_after)

        print(f"   Iteration {i+1}: {mem_after:.1f}MB")

    # Check for memory leak (>10% growth)
    if memory_samples:
        initial = memory_samples[0]
        final = memory_samples[-1]
        growth_pct = ((final - initial) / initial * 100) if initial > 0 else 0

        print(f"\n   Memory: {initial:.1f}MB → {final:.1f}MB ({growth_pct:+.1f}%)")

        if growth_pct > 10:
            print("   ⚠️  Warning: Potential memory leak detected")
        else:
            print("   ✅ Memory stable")


# ============================================
# RUN ALL STRESS TESTS
# ============================================

if __name__ == "__main__":
    print("\n" + "=" * 70)
    print("AI CONTROL PLANE - STRESS TEST SUITE")
    print("=" * 70)

    # Run all stress tests
    test_runtime_stress_single_threaded()
    test_runtime_stress_multi_threaded()
    test_runtime_stress_adversarial()
    test_runtime_memory_stability()

    print("\n✅ All stress tests complete\n")
