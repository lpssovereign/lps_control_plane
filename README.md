# AI Control Plane

A minimal, constraint-first runtime for safe LLM agent execution.

## Problem

LLM agents often execute tools without explicit state control, policy enforcement, or deterministic replay. This creates safety risks:

- **Silent Execution:** Actions execute without approval gates
- **No Audit Trail:** Cannot trace why actions occurred
- **Policy Bypass:** No enforcement layer between intent and execution
- **Non-Deterministic:** Cannot replay executions for debugging

## Approach

This repository implements a control plane with:

- **Explicit Execution State Machine:** All executions follow INIT → PLAN → APPROVE → EXECUTE → VERIFY → COMPLETE
- **Policy-as-Code Enforcement:** Actions evaluated against registered policies before execution
- **Append-Only Audit Logging:** Immutable, hash-chained audit trail with tamper detection
- **Deterministic Replay:** Reconstruct execution from audit logs

## Architecture

```
┌─────────────────────────────────────────────────────────┐
│ ExecutionEngine                                         │
│ ┌─────────────────────────────────────────────────────┐ │
│ │ StateMachine                                        │ │
│ │ • Enforces state transitions                        │ │
│ │ • Validates at each step                            │ │
│ │ • Immutable audit trail                             │ │
│ ├─────────────────────────────────────────────────────┤ │
│ │ PolicyEngine                                        │ │
│ │ • Evaluates actions against rules                   │ │
│ │ • Priority-based rule ordering                      │ │
│ │ • Most restrictive verdict wins                     │ │
│ ├─────────────────────────────────────────────────────┤ │
│ │ AuditLog                                            │ │
│ │ • Append-only immutable log                         │ │
│ │ • Hash-chained entries (tamper detection)           │ │
│ │ • Deterministic replay support                      │ │
│ └─────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────┘
```

## Installation

```bash
git clone https://github.com/[username]/ai-control-plane.git
cd ai-control-plane
pip install -e .
```

## Quick Start

```python
from control_plane import ExecutionEngine, Action, RiskBasedPolicy

# Initialize engine
engine = ExecutionEngine()

# Add policy
engine.policy_engine.register_rule(
    RiskBasedPolicy(approval_threshold=7, deny_threshold=10)
)

# Register action executor
engine.register_executor(
    "send_email",
    lambda params: f"Email sent to {params['to']}"
)

# Execute action
action = Action(
    action_type="send_email",
    params={"to": "user@example.com", "subject": "Test"},
    risk_level=5
)

result = engine.execute(action, auto_approve=True)

if result.success:
    print(f"Success: {result.output}")
    print(f"Duration: {result.duration_ms:.2f}ms")
else:
    print(f"Failed: {result.error}")

# Verify audit trail
print(f"Audit trail: {len(engine.get_audit_trail())} records")
print(f"Integrity: {engine.audit_log.verify_integrity()}")
```

## Key Features

### 1. State Machine Control

All executions follow deterministic state transitions:

```
INIT → PLAN → APPROVE → EXECUTE → VERIFY → COMPLETE
                  ↓
              REJECTED (if policy denies)
                  ↓
              FAILED (if execution errors)
```

Invalid transitions raise `ValueError`:

```python
sm = StateMachine()
sm.initialize()
sm.transition(ExecutionState.EXECUTE)  # ❌ ValueError: Cannot skip PLAN and APPROVE
```

### 2. Policy Enforcement

Actions evaluated against registered policies:

```python
from control_plane import ResourceConstraintPolicy

# Reject operations when memory usage > 90%
policy = ResourceConstraintPolicy(
    resource_check_fn=lambda: psutil.virtual_memory().percent / 100,
    threshold=0.9
)
engine.policy_engine.register_rule(policy)
```

Policy verdicts (in order of restrictiveness):
1. `DENY` - Action blocked
2. `REQUIRE_APPROVAL` - User approval required
3. `ALLOW` - Action proceeds

### 3. Immutable Audit Trail

All operations logged to append-only, hash-chained audit log:

```python
# Execute actions
for i in range(10):
    action = Action(action_type="compute", params={"x": i})
    engine.execute(action, auto_approve=True)

# Export audit log
exported_log = engine.audit_log.export(format="json")

# Verify integrity (detects tampering)
assert engine.audit_log.verify_integrity()

# Replay from exported log
from control_plane import AuditLog
replayed = AuditLog().replay(exported_log)
```

### 4. Deterministic Replay

Reconstruct execution from audit trail:

```python
# Original execution
sm1 = StateMachine()
sm1.initialize()
sm1.transition(ExecutionState.PLAN, reason="Planning")
sm1.transition(ExecutionState.APPROVE, reason="Approved")
sm1.transition(ExecutionState.EXECUTE, reason="Executing")
sm1.transition(ExecutionState.VERIFY, reason="Verifying")
sm1.transition(ExecutionState.COMPLETE, reason="Done")

# Get audit trail
trail = sm1.get_audit_trail()

# Replay in new state machine
sm2 = StateMachine()
final_context = sm2.replay(trail)

assert final_context.state == ExecutionState.COMPLETE  # ✅ Matches original
```

## Benchmarks

On Python 3.11, AMD Ryzen (16GB RAM):

| Operation | Throughput | Latency |
|-----------|------------|---------|
| **State transitions** | 12,300 ops/sec | 0.081ms |
| **Policy evaluations** | 185,000 ops/sec | 0.005ms |
| **End-to-end execution** | 950 ops/sec | 1.05ms |
| **Audit integrity checks** | 42,000 ops/sec | 0.024ms |

Run benchmarks:

```bash
python benchmarks/simple_run_benchmark.py
```

## Security Considerations

### No Silent Execution

Actions cannot execute without passing through state machine:

```python
# ❌ This would raise ValueError
sm.transition(ExecutionState.EXECUTE)  # Must go through PLAN and APPROVE first
```

### Immutable Audit Records

Audit records are frozen dataclasses:

```python
record = engine.get_audit_trail()[0]
record.reason = "tampered"  # ❌ Raises FrozenInstanceError
```

### Hash Chain Integrity

Tampering breaks hash chain:

```python
# Audit log uses SHA-256 hash chain
# Each entry's previous_hash must match previous entry's entry_hash
assert engine.audit_log.verify_integrity()  # ✅ True

# If log tampered:
# verify_integrity() → False
```

### Policy Priority

Higher priority policies evaluated first, most restrictive verdict wins:

```python
# High priority: deny dangerous actions
engine.policy_engine.register_rule(
    ActionTypePolicy(denied_types=["delete_all"], priority=100)
)

# Low priority: allow most actions
engine.policy_engine.register_rule(
    ActionTypePolicy(allowed_types=["read", "write", "delete_all"], priority=10)
)

# delete_all is DENIED (high priority wins)
```

## Limitations

- **Single-Node Only:** No distributed execution support yet
- **No Cryptographic Signing:** Hash chains detect tampering but not who tampered
- **No Persistence Backend:** Audit logs stored in memory (export to disk manually)
- **Simple Policy Language:** No DSL for complex rules yet

## Roadmap

- [ ] Distributed mode (multi-node state machine)
- [ ] Policy DSL (declarative rule language)
- [ ] Persistence backend (PostgreSQL, SQLite)
- [ ] Cryptographic signing (EdDSA for audit entries)
- [ ] Performance optimizations (async execution, caching)
- [ ] Web dashboard (visualize state transitions)

## Testing

Run tests:

```bash
pytest tests/ -v
```

Test coverage:

```bash
pytest tests/ --cov=control_plane --cov-report=html
```

## Contributing

Contributions welcome! Please:

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/my-feature`)
3. Add tests for new functionality
4. Ensure all tests pass (`pytest tests/`)
5. Submit a pull request

## License

MIT License

## References

This architecture draws inspiration from:

- **State Machines:** Harel, D. (1987). "Statecharts: A visual formalism for complex systems."
- **Event Sourcing:** Fowler, M. (2005). "Event Sourcing."
- **Policy Enforcement:** Sandhu, R. & Samarati, P. (1994). "Access control: principle and practice."
- **Immutability:** Okasaki, C. (1998). "Purely Functional Data Structures."
- **Audit Logging:** NIST SP 800-92 (2006). "Guide to Computer Security Log Management."

## Citation

```bibtex
@software{ai_control_plane,
  title = {AI Control Plane: Constraint-Based Runtime for Safe AI Agent Execution},
  author = {[Author]},
  year = {2026},
  url = {https://github.com/[username]/ai-control-plane}
}
```

---

**Status:** Production-ready for single-node AI agent execution with constraint enforcement and full audit trail.

## Stress Testing

Production-grade stress testing validates stability under load.

### Test Results

**40,000 executions across 4 scenarios:**

| Test | Throughput | Invariant Violations | Status |
|------|------------|---------------------|---------|
| **Single-Threaded** | 5,517 exec/sec | 0 | ✅ PASSED |
| **Multi-Threaded (8 workers)** | 3,818 exec/sec | 0 | ✅ PASSED |
| **Adversarial (mixed risk)** | 7,174 exec/sec | 0 | ✅ PASSED |
| **Memory Stability** | 0% growth | 0 | ✅ PASSED |

**Invariants Verified:**
- ✅ No silent execution (100% logged)
- ✅ No exceptions (0/40,000)
- ✅ Terminal states reached (40,000/40,000)
- ✅ Audit integrity (100% hash chain valid)
- ✅ Memory stable (0% growth over 5k iterations)

See [STRESS_TEST_REPORT.md](STRESS_TEST_REPORT.md) for full details.

### Running Stress Tests

```bash
# Run all stress tests
python3 tests/test_runtime_stress.py

# Or with pytest
pytest tests/test_runtime_stress.py -v -m stress

# Run specific test
pytest tests/test_runtime_stress.py::test_runtime_stress_multi_threaded -v
```
