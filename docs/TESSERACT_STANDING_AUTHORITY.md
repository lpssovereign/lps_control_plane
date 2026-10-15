# Tesseract Standing Authority for the Control Plane

The existing INIT -> PLAN -> APPROVE -> EXECUTE -> VERIFY -> COMPLETE machine should distinguish explicit one-off approval from a pre-existing standing delegation.

## Requirement

APPROVE must be satisfiable by one of:
1. explicit human approval for this action;
2. valid standing delegation covering action class/scope;
3. deterministic policy ALLOW where no human authority is required.

No approval state may be skipped. Standing authorization satisfies the state; it does not remove it.

## Standing low-risk internal delegation

Allowed without another prompt when all are true:
- internal scope;
- version-controlled or otherwise reversible;
- no protected secret/private-data publication;
- no external communication;
- no money/contract/legal filing;
- no destructive evidence loss;
- no material safety/privacy/reputation consequence;
- action is covered by registered delegation.

Examples: repository reads, docs, schemas, tests, fixtures, branch/commit work, issue/work-order creation, static analysis, local simulations, reconciliation.

## Required model extensions

Action:
- consequence_class
- reversibility
- data_class
- externality
- jurisdiction
- delegation_id

Delegation:
- principal
- delegate / delegate_class
- allowed_action_types
- repository/domain scope
- constraints
- issued_at
- revocable
- expires_at optional
- evidence/receipt requirements

Approval receipt must state whether approval came from explicit seal, standing delegation, or policy.

## Tesseract state objects

The control plane should be capable of carrying:
Entity, Observation, Source, Claim, State, Context, Discrepancy, Hypothesis, Confidence, Unknown, Intervention; Action, Prediction, Outcome, Revision.

Do not force all of these into Action itself; preserve typed objects/events.

## Tests

Add tests proving:
- standing delegation allows a reversible internal commit flow without interactive approval;
- same delegate is blocked from external send or destructive deletion;
- revocation immediately removes standing authority;
- receipt records delegation provenance;
- unknown/missing delegation fails closed;
- verification still occurs after automatically authorized execution.
