# reverse-agent Larger Step Roadmap Plan

## 0. Document Position

This document is a larger-step roadmap plan for reverse-agent. It is not a `DECISION_PACKET`, does not control the current engineering round, and does not replace:

```text
project_state/decision_packet.md
project_state/gates/command_plan.json
project_state/context/current_context_packet.json
project_state/roadmap/workstreams.json
project_state/state_manifest.json
```

Execution authority remains:

```text
project_state/decision_packet.md
```

Command authority remains:

```text
project_state/gates/command_plan.json
```

This plan intentionally groups multiple related engineering capabilities into larger milestones. Each milestone is still expected to be split into formal `DECISION_PACKET` rounds before implementation.

---

## 1. Why This Plan Is Larger Than The Previous Next Step

The previous next-step proposal only repaired a few closeout/report consistency issues left by the latest audit. That was safe but too narrow for project direction.

This plan moves one level up. It treats the next stage as a coordinated platform push:

```text
Project State domain separation
+ User Solve result contract
+ Evidence / Replay schema
+ Fast static solving wrapper
+ Web workbench foundation
+ Tool profile readiness
```

The goal is not to implement all of these in one uncontrolled round. The goal is to make the next several rounds share one coherent product milestone instead of repeatedly making isolated gate fixes.

---

## 2. Larger-Step Target

The next major platform milestone should be:

```text
Evidence-Centered User Solve Platform Foundation
```

One-sentence target:

```text
Turn reverse-agent from an internal governance-and-solver project into a user-facing reverse-analysis platform where candidates, validation state, evidence timeline, reports, and future tool outputs all share one auditable contract.
```

This milestone should be treated as one large roadmap item, implemented through multiple bounded decisions.

---

## 3. Current Basis

The latest audit reached:

```text
ACCEPTED_WITH_LIMITATIONS
```

The accepted part:

```text
1. decision metadata was valid.
2. command-plan existed and selected full profile.
3. pytest ran and passed.
4. report-summary passed.
5. execution-log passed.
6. final-check passed.
7. run-closeout passed.
8. close-round generated round_manifest.
```

The limitations:

```text
1. pytest coverage text was not fully aligned with decision examples.
2. report prose had minor expected-exit wording drift.
3. state_manifest looked stale as a strong current evidence source.
```

These are not severe enough to require another tiny rework-only round before all product planning. They should be absorbed into the larger platform foundation milestone as governance hardening tasks.

---

## 4. Mainline Selection

This roadmap touches multiple future capabilities, but the next implementation sequence should still remain mainline-separated.

Recommended sequence:

```text
project_governance
→ engineering_branch
→ reverse_solving
→ user_solve_layer
→ evidence_replay
→ web_workbench
→ tool_integration
```

The next formal decision should still use only one mainline.

Recommended immediate mainline:

```text
project_governance
```

Reason:

```text
Before User Solve, Web, evidence replay, and tool providers can be cleanly implemented, project_state must stop mixing global governance state, reverse-solving sample state, artifact freshness, negative results, and current-round gate evidence.
```

---

## 5. Larger Milestone: Evidence-Centered User Solve Platform Foundation

### 5.1 Included Workstreams

This milestone combines six related tracks:

```text
A. Project State Domain Taxonomy
B. User Solve Contract
C. Evidence Event / Solve Trace Schema
D. Fast Static Solve Wrapper
E. Web Workbench Read Model
F. Tool Profile Readiness
```

These are related because they all need the same state and evidence boundaries.

### 5.2 Non-Goals

This milestone must not become a full automation system.

Do not include:

```text
1. automatic GitHub push / PR / merge.
2. full autonomous runner dispatch.
3. database replacement for project_state.
4. IDA MCP execution.
5. dynamic debugging.
6. sample runtime probing.
7. exploit or crash exploitation work.
8. cleanup apply or deletion.
9. complete Web product.
10. full CI orchestration rewrite.
```

---

## 6. Workstream A: Project State Domain Taxonomy

### Goal

Separate global project state from domain-specific state.

Current problem:

```text
project_state/current_state.json currently behaves like reverse-solving sample state, but its name suggests global current state.
project_state/negative_results.json mixes reverse-solving failures with global policy restrictions.
artifact_index and state_manifest do not yet fully express domain, scope, role, and freshness in a way that prevents stale evidence from being reused.
```

### Scope

Implement a compatibility-first state taxonomy:

```text
project_state/domains/reverse_solving/
project_state/domains/project_governance/
project_state/domains/user_solve_layer/
project_state/domains/evidence_replay/
project_state/domains/web_workbench/
project_state/domains/tool_integration/
project_state/domains/automation_runner/
```

First implementation should add metadata and skeletons before moving files.

### Deliverables

```text
1. Domain README skeletons.
2. state_manifest role/scope/domain/freshness fields.
3. artifact_index scope/domain/mainline/freshness fields.
4. negative_results global_policy vs domain-specific classification.
5. final-check warning for missing legacy scope metadata.
6. context packet consuming domain metadata.
```

### Acceptance

```text
1. Engineering rounds are not blocked by stale reverse-solving sample artifacts.
2. Reverse-solving rounds still read reverse-solving negative results.
3. Global hard blocks such as not committing full solve_reports remain global.
4. state_manifest can say which file supports which domain.
5. artifact_index can distinguish current evidence from historical artifact.
```

---

## 7. Workstream B: User Solve Contract

### Goal

Define the user-facing result object before building more Web or solver code.

### Required Model

```text
UserSolveResult
UserSolveTask
UserSolveStatus
ValidationStatus
CandidateEvidenceRef
UserFacingMessage
```

Suggested status values:

```text
uploaded
fast_analyzing
candidate_found
static_verified
runtime_validation_pending
runtime_validated
failed
blocked
```

Suggested validation values:

```text
not_started
pending
passed
failed
unavailable
```

### Rules

```text
candidate_found != verified
static_verified != runtime_validated
runtime_validated requires explicit validation evidence
failed requires a user-readable reason
blocked requires a policy/tool/environment reason
user output must not expose internal decision_packet or command-plan details
```

### Deliverables

```text
reverse_agent/user_solve_contract.py
reverse_agent/user_solve_state.py
tests/test_user_solve_contract.py
tests/test_user_solve_state.py
docs/user_solve_contract.md
```

### Acceptance

```text
1. UserSolveResult serializes to stable JSON.
2. Illegal transitions are rejected.
3. verified states require evidence references.
4. candidate-only states remain allowed.
5. internal governance state is not leaked to user-facing payloads.
```

---

## 8. Workstream C: Evidence Event / Solve Trace Schema

### Goal

Make every candidate and report traceable.

### Event Types

```text
upload
hash
extract_strings
type_detect
solver_attempt
candidate_generated
validation_attempt
validation_result
fallback_step
report_generated
error
blocked
```

### Trace Model

```text
SolveTrace
EvidenceEvent
CandidateEvidence
ValidationEvidence
ReportEvidenceSummary
ReplayTimeline
```

### Deliverables

```text
reverse_agent/evidence/events.py
reverse_agent/evidence/trace.py
reverse_agent/evidence/replay_model.py
tests/test_evidence_events.py
tests/test_solve_trace.py
docs/evidence_trace_schema.md
```

### Acceptance

```text
1. Every candidate can point to at least one evidence event.
2. Every validation result can point to a validation event.
3. A report can summarize evidence without embedding bulky artifacts.
4. Replay timeline can be generated deterministically from trace JSON.
5. Missing evidence is explicit, not hidden.
```

---

## 9. Workstream D: Fast Static Solve Wrapper

### Goal

Expose a safe static solve path for user-facing mode.

This is not full automatic reversing. It is a controlled wrapper over known low-risk capabilities.

### First Supported Types

```text
plain string comparison
Base64
single-byte XOR
simple repeated-key XOR
simple shift
hash string detection
RC4 signature hint
lookup-table hint
```

### Deliverables

```text
reverse_agent/user_solve_fast.py
reverse_agent/static_extract.py
reverse_agent/static_candidate.py
tests/test_user_solve_fast.py
tests/test_static_candidate.py
```

### Rules

```text
Do not execute samples.
Do not invoke debugger.
Do not call IDA/Ghidra/MCP.
Do not brute-force by expanding budgets blindly.
Do not claim runtime validation from static checks.
```

### Acceptance

```text
1. No candidate returns failed/no_candidate with reason.
2. Candidate returns candidate_found with evidence refs.
3. Static verification is explicitly labeled static_verified.
4. Unsupported sample types return blocked or unsupported, not fake success.
5. All attempts write a solve trace.
```

---

## 10. Workstream E: Web Workbench Read Model

### Goal

Prepare the Web backend data model without building the full Web UI first.

### First Read Models

```text
TaskListItem
TaskDetailView
CandidateView
ValidationView
EvidenceTimelineView
ReportView
CapabilityMatrixView
```

### Deliverables

```text
reverse_agent/web_read_models.py
reverse_agent/user_solve_views.py
tests/test_web_read_models.py
docs/web_workbench_read_model.md
```

### Rules

```text
Web read models are read-only.
Web does not create evidence.
Web does not execute tools.
Web does not bypass command-plan.
Web receives user-facing summaries, not raw internal governance state.
```

### Acceptance

```text
1. UserSolveResult can be converted to TaskDetailView.
2. SolveTrace can be converted to EvidenceTimelineView.
3. Report summary can be shown without exposing bulky artifacts.
4. Candidate and validation states are visually distinguishable.
5. Web read models remain deterministic.
```

---

## 11. Workstream F: Tool Profile Readiness

### Goal

Prepare future IDA/Ghidra/OllyDbg integration without invoking tools yet.

### Deliverables

```text
reverse_agent/tool_profiles.py
reverse_agent/tool_capabilities.py
reverse_agent/tool_provider_contract.py
tests/test_tool_profiles.py
tests/test_tool_capabilities.py
docs/tool_provider_contract.md
```

### Rules

```text
Tool profile describes availability, command, path, risk level, timeout, and allowed operations.
Provider output must become evidence schema.
Provider output is not final truth.
Missing tool means blocked/tool_unavailable.
```

### Acceptance

```text
1. Local tool availability can be represented without executing tools.
2. IDA/Ghidra/OllyDbg provider contracts exist as schemas.
3. No real tool invocation occurs.
4. Future command-plan can authorize provider calls precisely.
5. Web/API does not hardcode local tool paths.
```

---

## 12. Recommended Larger-Step Implementation Sequence

### Round 1: Project State Domain Taxonomy Foundation

Mainline:

```text
project_governance
```

Implement:

```text
1. domain taxonomy metadata schema.
2. state_manifest scoped role fields.
3. artifact_index scoped artifact fields.
4. negative_results scope classification.
5. final-check warnings for legacy missing scope.
```

Do not move files yet.

### Round 2: Domain Skeleton + Context Builder Alignment

Mainline:

```text
project_governance
```

Implement:

```text
1. project_state/domains/* README skeletons.
2. context packet reads scoped state metadata.
3. workstream registry records platform foundation milestone.
4. final-check confirms domain skeleton does not claim current evidence.
```

### Round 3: User Solve Contract + State Machine

Mainline:

```text
engineering_branch or user_solve_layer
```

Implement:

```text
1. UserSolveResult.
2. UserSolveTask.
3. ValidationStatus.
4. State transition checks.
5. User-facing error model.
```

### Round 4: Evidence Event + Solve Trace Schema

Mainline:

```text
evidence_replay or engineering_branch
```

Implement:

```text
1. EvidenceEvent.
2. SolveTrace.
3. CandidateEvidenceRef.
4. ValidationEvidence.
5. ReplayTimeline read model.
```

### Round 5: Fast Static Solve Wrapper

Mainline:

```text
reverse_solving
```

Implement:

```text
1. static extraction wrapper.
2. safe candidate generation.
3. UserSolveResult mapping.
4. solve trace emission.
5. no runtime execution.
```

### Round 6: Web Workbench Read Model

Mainline:

```text
engineering_branch or web_workbench
```

Implement:

```text
1. Task list view model.
2. Task detail view model.
3. Candidate/validation/evidence timeline view models.
4. report summary view model.
5. no frontend runtime yet if backend contracts are not stable.
```

### Round 7: Minimal Web UI

Mainline:

```text
web_workbench
```

Implement:

```text
1. task list page.
2. task detail page.
3. candidate and validation display.
4. evidence timeline display.
5. markdown report display.
```

### Round 8: Tool Profile Readiness

Mainline:

```text
tool_integration
```

Implement:

```text
1. tool profile schema.
2. tool capability detection contract.
3. provider result schema.
4. no IDA/Ghidra/OllyDbg invocation yet.
```

---

## 13. Larger Acceptance Target

The whole milestone is acceptable when reverse-agent can do the following:

```text
1. Keep project governance facts separated from reverse-solving facts.
2. Produce a user-facing solve result without exposing internal governance files.
3. Distinguish candidate, static verified, runtime validated, failed, and blocked.
4. Attach every candidate to evidence events.
5. Generate a deterministic timeline/replay model.
6. Prepare Web read models from the same evidence contract.
7. Represent tool availability and provider contracts without unsafe invocation.
8. Keep command-plan, execution_log, final-check, run-closeout, and round archive intact.
```

---

## 14. What Not To Do Even In The Larger Plan

Do not use the larger plan as permission to make uncontrolled large changes.

Forbidden until separately authorized:

```text
1. moving or deleting existing project_state files.
2. cleanup apply.
3. database replacement.
4. runtime probing.
5. debugger invocation.
6. IDA MCP invocation.
7. sample execution.
8. automatic runner dispatch.
9. GitHub Action dispatch.
10. full Web rewrite.
11. exploit/crash exploitation direction.
12. changing .codex-skills.
```

---

## 15. Recommended Workstream Entry

If this roadmap is registered in `project_state/roadmap/workstreams.json`, use a non-authoritative roadmap entry:

```json
{
  "workstream_id": "evidence_centered_user_solve_platform_foundation",
  "family": "project_governance",
  "status": "CANDIDATE",
  "is_execution_authority": false,
  "execution_authority": "project_state/decision_packet.md",
  "notes": "Larger platform milestone covering project_state domain taxonomy, User Solve contract, evidence/replay schema, fast static solve wrapper, Web read models, and tool profile readiness. This roadmap entry is not execution authority; each implementation step must be selected by a future decision_packet and authorized by command-plan.",
  "active_decision_id": "",
  "active_round_id": "",
  "baseline_round_id": ""
}
```

Do not mark it `ACTIVE_ROUND` until a future `decision_packet.md` explicitly selects one bounded part of it.

---

## 16. Final Direction

The larger next step should not be another tiny gate-only patch, and it should not be a chaotic jump into Web or IDA.

The correct larger direction is:

```text
State ownership foundation
→ User-facing solve contract
→ Evidence trace and replay model
→ Safe static solve wrapper
→ Web read model
→ Minimal Web workbench
→ Tool profile readiness
```

This gives the project a visible product direction while preserving the core reverse-agent rule:

```text
No current conclusion without current evidence.
No execution without decision_packet and command-plan.
No acceptance without pytest, report-summary, final-check, run-closeout, and audit.
```
