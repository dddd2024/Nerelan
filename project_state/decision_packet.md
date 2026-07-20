```json decision_meta
{
  "schema_version": 1,
  "decision_id": "decision_20260720_transition_bootstrap_and_architecture_spine_v1",
  "round_id": "round_20260720_transition_bootstrap_and_architecture_spine_v1",
  "based_on_state_build_id": "state_20260618_134029_d6bd033d2532",
  "based_on_state_digest": "d6bd033d25324345cfd8ada0ac65db42bc86eb5017f3ffc92906fcd8b71cacb5",
  "status": "APPROVED",
  "mainline": "engineering_branch",
  "skill_profiles": [
    "reverse-agent-iteration@v2"
  ]
}
```

```json decision_contract
{
  "follows_last_decision_id": "decision_20260720_transition_workflow_cutover_and_ci_test_bootstrap_v1",
  "follows_last_round_id": "round_20260720_transition_workflow_cutover_and_ci_test_bootstrap_v1",
  "previous_remote_gate_status": "SUCCESS",
  "workstream_id": "transition-bootstrap-and-architecture-spine-v1",
  "required_branch": "codex/architecture-spine-v1",
  "activation_base_sha": "0dbdc3cb82c7935ae715d7f3092f16e2242c0948",
  "source_pull_request": 8,
  "source_branch": "codex/control-plane-transition-kernel-v1",
  "source_head_sha": "0dbdc3cb82c7935ae715d7f3092f16e2242c0948",
  "roadmap_path": "docs/roadmap/architecture_transition_next_24h.md",
  "unified_long_term_roadmap": "docs/roadmap/reverse_agent_unified_architecture_and_trust_roadmap.md",
  "decision_commit_must_precede_implementation": true,
  "transition_kernel_required": true,
  "architecture_migration_required": true,
  "legacy_state_maintenance_is_primary_goal": false,
  "legacy_final_check_is_acceptance_authority": false,
  "legacy_closeout_is_acceptance_authority": false,
  "legacy_state_manifest_is_acceptance_authority": false,
  "bootstrap_exception_authorized": true,
  "bootstrap_exception_reason": "The inherited transition-command-plan only validates and copies the previous round plan, while transition-preflight hard-codes the previous branch and path scope. A narrowly bounded gate bootstrap must run before the current Decision can generate its own command authority.",
  "bootstrap_exception_expires_when": "The current Decision command plan has been regenerated, transition-lint passes, and transition-preflight passes on codex/architecture-spine-v1.",
  "bootstrap_exception_files": [
    "reverse_agent/project_gate.py",
    "reverse_agent/control_plane/legacy_adapter.py",
    "reverse_agent/control_plane/models.py",
    "reverse_agent/control_plane/command_authority.py",
    "tests/test_project_gate.py",
    "tests/test_control_plane_transition.py",
    "project_state/decision_packet.md",
    "project_state/gates/command_plan.json",
    "project_state/gates/transition_command_plan_preview.json",
    "project_state/gates/transition_preflight_result.json"
  ],
  "bootstrap_exception_commands": [
    "python -m pytest tests/test_project_gate.py -q",
    "python -m pytest tests/test_project_gate.py tests/test_control_plane_transition.py -q",
    "python -m reverse_agent.project_gate transition-command-plan --state-dir project_state",
    "python -m reverse_agent.project_gate transition-lint --state-dir project_state",
    "python -m reverse_agent.project_gate transition-preflight --state-dir project_state",
    "git diff --check",
    "git status --short"
  ],
  "command_plan_precedes_architecture_implementation": true,
  "command_plan_is_local_command_authority_after_bootstrap": true,
  "allowed_packaging_files": [
    "pyproject.toml"
  ],
  "allowed_workflow_files": [
    ".github/workflows/ci.yml"
  ],
  "allowed_control_plane_files": [
    "reverse_agent/project_gate.py",
    "reverse_agent/control_plane/legacy_adapter.py",
    "reverse_agent/control_plane/models.py",
    "reverse_agent/control_plane/command_authority.py"
  ],
  "allowed_source_paths": [
    "reverse_agent/architecture/**",
    "reverse_agent/workflows/**",
    "reverse_agent/trust/**",
    "reverse_agent/adapters/**"
  ],
  "allowed_test_files": [
    "tests/test_project_gate.py",
    "tests/test_control_plane_transition.py",
    "tests/test_architecture_contracts.py",
    "tests/test_risk_classifier.py",
    "tests/test_development_graph.py",
    "tests/test_trust_authorization_adapter.py",
    "tests/test_planning_and_github_adapters.py"
  ],
  "allowed_documentation_files": [
    "docs/roadmap/architecture_transition_next_24h.md",
    "docs/architecture/architecture-spine-v1.md",
    "docs/architecture/transition-gate-bootstrap.md"
  ],
  "allowed_project_state_files": [
    "project_state/decision_packet.md",
    "project_state/gates/command_plan.json",
    "project_state/gates/execution_log.json",
    "project_state/gates/transition_preflight_result.json",
    "project_state/gates/transition_command_plan_preview.json",
    "project_state/pytest_result.txt",
    "project_state/codex_execution_report.md",
    "project_state/execution_report.md"
  ],
  "read_only_compatibility_paths": [
    ".github/workflows/state-gate.yml",
    ".github/workflows/decision-preflight.yml",
    "project_state/schemas/transition_authority.schema.json",
    "project_state/schemas/transition_command_plan.schema.json",
    "project_state/schemas/execution_envelope.schema.json",
    "project_state/schemas/transition_preflight_result.schema.json"
  ],
  "forbidden_mutated_paths": [
    "frontend/**",
    "solve_reports/**",
    "local_reverse_samples/**",
    "training_materials/**",
    "reverse_agent/user_solve_*.py",
    "reverse_agent/orchestrator_api.py",
    "reverse_agent/project_agent_runner.py",
    "reverse_agent/project_runner_contract.py",
    "project_state/current_state.json",
    "project_state/artifact_index.json",
    "project_state/state_manifest.json",
    "project_state/context/**",
    "project_state/rounds/**",
    ".codex-skills/**"
  ],
  "framework_installation_allowed": true,
  "allowed_frameworks": [
    "langgraph"
  ],
  "bmad_installation_allowed": false,
  "runner_dispatch_allowed": false,
  "model_api_invocation_allowed": false,
  "external_reverse_tool_invocation_allowed": false,
  "unknown_binary_execution_allowed": false,
  "destructive_operations_allowed": false,
  "network_access_allowed": false,
  "direct_push_to_main_allowed": false,
  "merge_allowed": false,
  "force_push_allowed": false,
  "rebase_during_execution_allowed": false,
  "draft_pull_request_allowed": true,
  "scope_policy": "single_round_gate_bootstrap_then_architecture_spine_only"
}
```

# DECISION_PACKET

## 1. Goal

Complete one merged implementation round of approximately 24 hours:

```text
Phase A: Transition Gate Bootstrap Repair
→ regenerate current Decision command authority
→ pass current-branch transition lint and preflight
→ Phase B: Architecture Spine v1
```

The round exists because the prior Architecture Spine Decision could not start safely. The inherited transition kernel contains two self-bootstrap defects:

1. `transition-command-plan` reads and republishes the previous `command_plan.json` instead of generating a plan from the active Decision;
2. `transition-preflight` hard-codes the previous branch and path scope instead of reading the active Decision contract.

This Decision explicitly authorizes a narrow bootstrap exception to repair those defects. The exception is not a permanent bypass. It expires immediately after the current Decision generates its own command plan and the current branch passes transition lint and preflight.

After the exception expires, all Architecture Spine work must follow the regenerated command plan.

Estimated effort:

```text
Phase A: 4–6 hours
Phase B: 18–20 hours
Total target: approximately 24 hours
```

Do not expand scope merely to consume the estimate.

---

## 2. Phase A — Transition Gate Bootstrap Repair

### 2.1 Required behavior

Implement all of the following:

1. `transition-command-plan` loads the active Decision and deterministically writes a new `project_state/gates/command_plan.json` for that Decision;
2. generated plan identity exactly matches active `decision_id` and `round_id`;
3. generated plan derives allowed paths, forbidden paths, forbidden operations and allowed commands from the active Decision contract;
4. `transition-lint` validates the newly generated current plan rather than the previous round plan;
5. `transition-preflight` derives `expected_branch` from `required_branch` in the active Decision;
6. `transition-preflight` derives allowed and forbidden paths from the active Decision;
7. no previous branch or previous round path scope remains hard-coded as the authority;
8. missing, malformed or ambiguous Decision fields fail closed;
9. legacy mode behavior remains unchanged;
10. tests prove a second Decision on a different branch and scope can bootstrap successfully without editing constants.

### 2.2 Bootstrap execution order

The Agent is explicitly authorized to perform the following sequence before a valid current command plan exists:

```text
read active Decision and transition implementation
→ modify only bootstrap_exception_files
→ run focused bootstrap tests
→ run transition-command-plan
→ inspect generated command_plan.json
→ run transition-lint
→ run transition-preflight
```

No Architecture Spine source file may be created before all three conditions are true:

```text
current plan identity matches this Decision
transition-lint = PASSED
transition-preflight = PASSED
```

### 2.3 Phase A acceptance

Phase A passes only if:

1. `command_plan.json` was generated, not manually fabricated;
2. its Decision and round identity match this packet;
3. current branch `codex/architecture-spine-v1` is accepted from the Decision contract;
4. current allowed paths come from the Decision contract;
5. old branch `codex/control-plane-transition-kernel-v1` is no longer a hard-coded requirement;
6. focused tests pass;
7. `git diff --check` passes.

If Phase A fails, stop. Do not begin Phase B.

---

## 3. Phase B — Architecture Spine v1

### 3.1 Target architecture slice

Build the first executable vertical slice of the new architecture:

```text
Planning Reference
→ GitHub Work Item
→ Workflow Identity
→ deterministic R0–R3 Risk Classification
→ LangGraph Shadow Workflow
   ├─ R0/R1 → STANDARD_PATH
   └─ R2/R3 → Trust Authorization Adapter
→ Deterministic Acceptance Gate
```

This is a shadow architecture slice. It must not dispatch coding Agents, run shell tools, invoke model APIs, execute binaries, push automatically or merge.

### 3.2 Architecture contracts

Add typed, serializable models for at least:

```text
PlanningReference
GitHubWorkItem
WorkflowIdentity
RiskTier
ExecutionEnvelope
AuthorizationRequirement
AuthorizationRequest
AuthorizationResult
AcceptanceResult
DevelopmentWorkflowState
```

Required semantics:

1. BMAD planning artifacts are context only and never command authority;
2. GitHub Work Item is the ordinary engineering task entry;
3. R0/R1 do not require a full Decision;
4. R2/R3 route to the Trust Authorization Port;
5. unknown or incomplete risk inputs fail closed;
6. GitHub branch/PR/CI facts are observations with repository, SHA and observed time;
7. runtime state belongs to LangGraph, not to the legacy closeout chain.

### 3.3 Deterministic risk classifier

Implement R0–R3 without an LLM.

Minimum routing:

```text
R0/R1 → STANDARD_PATH
R2/R3 → TRUST_AUTHORIZATION_REQUIRED
unknown / malformed → BLOCKED
```

Representative classifications:

- R0: research, planning, read-only audit;
- R1: scoped code edits, unit tests, local static checks, no network or push;
- R2: workflow changes, dependency changes, network, commit/push/Draft PR, permission policy;
- R3: unknown binary execution, debugger/emulator/hook, secrets, destructive or privileged actions.

### 3.4 LangGraph Shadow Runtime

Add a minimal graph:

```text
START
→ load_work_item
→ load_planning_context
→ classify_risk
→ conditional route
   ├─ standard_path
   └─ request_trust_authorization
→ acceptance_gate
→ END
```

Constraints:

1. use LangGraph as the single Python workflow runtime;
2. use an in-memory or test checkpointer;
3. nodes are ordinary Python functions;
4. same input can be replayed deterministically;
5. no source mutation, shell execution, network, model API or external reverse tool action occurs inside the graph;
6. graph state is not copied into multiple legacy gate artifacts.

### 3.5 Trust Authorization Adapter

Wrap the transition kernel behind a narrow port:

```python
class TrustAuthorizationPort(Protocol):
    def authorize(self, request: AuthorizationRequest) -> AuthorizationResult:
        ...
```

The adapter returns only:

```text
AUTHORIZED
APPROVAL_REQUIRED
BLOCKED
```

It must not read final-check, closeout, final seal, report-summary or publication mirrors. It must not make a full Decision mandatory for R0/R1.

### 3.6 BMAD and GitHub adapter boundaries

Implement fixtures and parsing boundaries only:

- BMAD adapter loads artifact references, summaries and digests;
- GitHub Work Item adapter loads repository, issue/story identity, title, acceptance criteria and immutable source references;
- GitHub truth adapter models branch, head SHA, PR and CI observations without making remote mutations.

Do not install BMAD in this round and do not call GitHub remotely from the graph.

---

## 4. Required tests

Add focused tests covering:

### Gate bootstrap

1. active Decision generates a new plan;
2. plan identity changes when Decision identity changes;
3. branch comes from Decision, not a constant;
4. allowed paths come from Decision, not a constant;
5. missing branch/scope fields fail closed;
6. manually edited or malformed plan is blocked;
7. legacy path remains compatible.

### Architecture contracts

1. stable serialization;
2. invalid enums and missing identity rejected;
3. planning input cannot authorize commands;
4. GitHub observation requires repository and SHA provenance.

### Risk classifier

1. representative R0/R1/R2/R3 cases;
2. conflicting features select the higher risk;
3. unknown inputs block.

### LangGraph

1. R0/R1 take standard path;
2. R2/R3 call Trust Authorization Port;
3. blocked authorization reaches blocked acceptance;
4. checkpoint replay produces the same terminal result;
5. no side-effect tool is invoked.

### Trust adapter

1. R2/R3 Decision/plan identity mismatch blocks;
2. authorized request returns expected status;
3. R0/R1 do not depend on legacy closeout files.

---

## 5. Required validation sequence

After Phase A passes:

```text
python -m pytest tests/test_project_gate.py tests/test_control_plane_transition.py -q
python -m reverse_agent.project_gate transition-command-plan --state-dir project_state
python -m reverse_agent.project_gate transition-lint --state-dir project_state
python -m reverse_agent.project_gate transition-preflight --state-dir project_state
```

After Phase B implementation:

```text
python -m pytest tests/test_architecture_contracts.py tests/test_risk_classifier.py tests/test_development_graph.py tests/test_trust_authorization_adapter.py tests/test_planning_and_github_adapters.py -q
python -m pytest tests/test_project_gate.py tests/test_control_plane_transition.py -q
git diff --check
```

Then run the repository test suite within the available execution window. If the full suite exceeds the environment time limit, preserve the timeout truthfully and run the largest deterministic covered subset; do not report an uncompleted full suite as passed.

---

## 6. Do Not Do

Do not:

- begin Phase B before Phase A lint and preflight pass;
- manually fabricate `command_plan.json`;
- preserve the old hard-coded branch or path scope as a fallback;
- broaden the bootstrap exception beyond the exact files and commands listed;
- repair legacy closeout, final seal, publication truth, context sync or state manifest;
- install BMAD in this round;
- add Microsoft Agent Framework, MetaGPT or ChatDev;
- use two workflow runtimes;
- modify User Solve, frontend, solver, harness or reverse-analysis business logic;
- run unknown binaries, IDA, Ghidra, debugger, emulator, hook or runtime probe;
- call a model API;
- access secrets;
- push directly to main;
- merge, rebase, force-push, tag or release;
- create a second implementation branch for this round;
- automatically start the next Trust Layer phase.

---

## 7. Completion criteria

The round is complete only if all are true:

1. gate bootstrap is data-driven by the active Decision;
2. current Decision generated the current command plan;
3. current transition lint and preflight pass;
4. Architecture Spine contracts exist and serialize stably;
5. R0–R3 classification is deterministic and fail-closed;
6. LangGraph Shadow Workflow runs and replays;
7. R2/R3 use the Trust Authorization Adapter;
8. R0/R1 do not require legacy closeout artifacts;
9. focused tests and diff check pass;
10. reports distinguish completed validation from timeout or unrun validation;
11. changes are pushed only to `codex/architecture-spine-v1`;
12. at most one Draft PR is created and no merge occurs.

After completion, stop and wait for independent audit. Do not begin BMAD installation, Trust Schema Foundation, Binary Evidence Firewall, tool integration or Web work automatically.
