```json decision_meta
{
  "schema_version": 1,
  "decision_id": "decision_20260720_architecture_spine_v1",
  "round_id": "round_20260720_architecture_spine_v1",
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
  "workstream_id": "architecture-spine-v1",
  "required_branch": "codex/architecture-spine-v1",
  "activation_base_sha": "0dbdc3cb82c7935ae715d7f3092f16e2242c0948",
  "source_pull_request": 8,
  "source_branch": "codex/control-plane-transition-kernel-v1",
  "source_head_sha": "0dbdc3cb82c7935ae715d7f3092f16e2242c0948",
  "roadmap_path": "docs/roadmap/architecture_transition_next_24h.md",
  "decision_commit_must_precede_implementation": true,
  "command_plan_precedes_substantive_execution": true,
  "command_plan_is_local_command_authority": true,
  "transition_kernel_required": true,
  "architecture_migration_required": true,
  "legacy_state_maintenance_is_primary_goal": false,
  "legacy_final_check_is_acceptance_authority": false,
  "legacy_closeout_is_acceptance_authority": false,
  "legacy_state_manifest_is_acceptance_authority": false,
  "allowed_packaging_files": [
    "pyproject.toml"
  ],
  "allowed_workflow_files": [
    ".github/workflows/ci.yml"
  ],
  "allowed_source_paths": [
    "reverse_agent/architecture/**",
    "reverse_agent/workflows/**",
    "reverse_agent/trust/**",
    "reverse_agent/adapters/**"
  ],
  "allowed_test_files": [
    "tests/test_architecture_contracts.py",
    "tests/test_risk_classifier.py",
    "tests/test_development_graph.py",
    "tests/test_trust_authorization_adapter.py",
    "tests/test_planning_and_github_adapters.py"
  ],
  "allowed_documentation_files": [
    "docs/roadmap/architecture_transition_next_24h.md",
    "docs/architecture/architecture-spine-v1.md"
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
    "reverse_agent/control_plane/**",
    "reverse_agent/project_gate.py",
    ".github/workflows/state-gate.yml",
    ".github/workflows/decision-preflight.yml",
    "project_state/schemas/transition_authority.schema.json",
    "project_state/schemas/transition_command_plan.schema.json",
    "project_state/schemas/execution_envelope.schema.json",
    "project_state/schemas/transition_preflight_result.schema.json"
  ],
  "forbidden_mutated_paths": [
    "reverse_agent/control_plane/**",
    "reverse_agent/project_gate.py",
    ".github/workflows/state-gate.yml",
    ".github/workflows/decision-preflight.yml",
    "frontend/**",
    "solve_reports/**",
    "training_materials/**",
    "local_reverse_samples/**",
    "reverse_agent/user_solve_*.py",
    "reverse_agent/project_state.py",
    "reverse_agent/project_state_manifest.py",
    "reverse_agent/project_jobs.py",
    "reverse_agent/project_agent_runner.py",
    "reverse_agent/orchestrator_api.py",
    "project_state/current_state.json",
    "project_state/state_manifest.json",
    "project_state/context/**",
    "project_state/roadmap/workstreams.json",
    "project_state/rounds/**"
  ],
  "allowed_new_primary_dependency": "langgraph",
  "bmad_package_installation_allowed": false,
  "microsoft_agent_framework_installation_allowed": false,
  "second_workflow_runtime_allowed": false,
  "runner_dispatch_allowed": false,
  "model_api_invocation_allowed": false,
  "external_reverse_tool_invocation_allowed": false,
  "unknown_binary_execution_allowed": false,
  "destructive_operations_allowed": false,
  "network_access_for_dependency_install_only": true,
  "commit_push_draft_pr_allowed": true,
  "direct_push_to_main_allowed": false,
  "merge_allowed": false,
  "force_push_allowed": false,
  "rebase_during_execution_allowed": false,
  "estimated_effort_hours_min": 20,
  "estimated_effort_hours_max": 26,
  "scope_policy": "single_mainline_architecture_spine_vertical_slice"
}
```

```json architecture_contract
{
  "schema_version": 1,
  "planning_authority": "BMAD_ARTIFACT_REFERENCE",
  "engineering_work_authority": "GITHUB_WORK_ITEM",
  "workflow_runtime_authority": "LANGGRAPH",
  "repository_and_ci_truth": "GITHUB",
  "high_risk_authority": "REVERSE_AGENT_TRUST_LAYER",
  "binary_evidence_authority": "REVERSE_AGENT_TRUST_LAYER",
  "risk_tiers": ["R0", "R1", "R2", "R3"],
  "standard_path_tiers": ["R0", "R1"],
  "trust_authorization_tiers": ["R2", "R3"],
  "unknown_or_incomplete_input_result": "BLOCKED",
  "runtime_mode": "SHADOW_NON_DISPATCHING",
  "final_merge_authority": "HUMAN_AND_GITHUB_PROTECTION"
}
```

# DECISION_PACKET

## 1. Goal

Implement the first runnable vertical slice of the target reverse-agent architecture in approximately 24 hours of bounded engineering work.

The target path is:

```text
BMAD Planning Reference
→ GitHub Work Item
→ LangGraph Workflow Instance
→ Deterministic R0-R3 Risk Classification
→ R0/R1 Standard Path
→ R2/R3 Trust Authorization Adapter
→ Deterministic Acceptance Result
```

This round is an architecture migration round. It is not a legacy state-file repair round and it is not a binary-analysis feature round.

The completed transition kernel from PR #8 remains intact and is reused only as the compatibility authorization mechanism behind the new Trust Authorization Port for R2/R3 work.

## 2. Required Outcomes

The round must deliver all of the following:

1. A small typed architecture contract layer for planning references, GitHub work items, workflow identity, risk tiers, authorization requirements, execution envelopes, and acceptance results.
2. A deterministic risk classifier with fail-closed behavior.
3. LangGraph as the single Python workflow runtime.
4. A non-dispatching development graph that can be invoked against fixtures and replayed deterministically.
5. A Trust Authorization Port that adapts the existing transition kernel without importing the full legacy project-gate lifecycle.
6. BMAD planning and GitHub work-item adapters that consume structured fixtures only.
7. A GitHub truth observation model that records repository facts with source and observation time but does not override GitHub.
8. Tests for low-risk routing, high-risk routing, malformed input blocking, deterministic replay, checkpoint/resume, adapter boundaries, and transition-kernel compatibility.
9. CI coverage for the new focused architecture tests.
10. A Draft PR against `main`; no merge.

## 3. Authority Boundaries

The implementation must encode these boundaries in code and tests:

| Fact class | Primary authority | Required behavior |
|---|---|---|
| Product Brief, PRD, architecture, story | BMAD planning artifacts | Read-only planning references; never command authority |
| Current engineering unit | GitHub Work Item | Creates workflow input identity |
| Workflow state and checkpoint | LangGraph | Do not mirror node state into the legacy closeout chain |
| Branch, commit, PR, checks | GitHub | Store only sourced observations |
| R0/R1 engineering work | Work Item plus execution envelope | No full Decision required in the target design |
| R2/R3 high-risk work | reverse-agent Trust Layer | Explicit authorization required |
| Binary evidence and claims | reverse-agent Trust Layer | Not asserted by BMAD, GitHub, or LangGraph |
| Merge | Human plus GitHub protection | Never automatic in this round |

## 4. Implementation Packages

### Package A — Architecture contracts

Create:

```text
reverse_agent/architecture/__init__.py
reverse_agent/architecture/contracts.py
reverse_agent/architecture/authority.py
reverse_agent/architecture/risk.py
```

Required models:

```text
PlanningReference
GitHubWorkItem
WorkflowIdentity
RiskTier
ExecutionEnvelope
AuthorizationRequirement
ArchitectureDecision
AcceptanceResult
```

Requirements:

- Stable JSON serialization.
- Explicit schema version.
- No dependency on legacy report, closeout, seal, context, or state-manifest artifacts.
- Planning reference contains artifact type, path or URI, digest, and summary only.
- GitHub work item contains repository, item number, immutable observation reference, acceptance criteria, requested operations, and requested paths.

### Package B — Risk classification and routing

Create:

```text
reverse_agent/architecture/risk_classifier.py
reverse_agent/architecture/authorization_router.py
```

First version must be deterministic and rule-based.

Risk policy:

```text
R0: read-only research, planning, code reading, review
R1: bounded source/test edits, formatting, local tests, no network, no push, no binary execution
R2: workflow changes, dependency changes, network access, commit/push/Draft PR, permission policy, migration
R3: unknown binary execution, debugger/emulator/hook, dynamic probing, sample mutation, secrets, privileged remote execution, destructive deletion
```

Routing result:

```text
R0/R1 → STANDARD_PATH
R2/R3 → TRUST_AUTHORIZATION_REQUIRED
missing/unknown/conflicting facts → BLOCKED
```

### Package C — LangGraph shadow runtime

Add `langgraph` as the only primary workflow runtime dependency.

Create:

```text
reverse_agent/workflows/__init__.py
reverse_agent/workflows/state.py
reverse_agent/workflows/development_graph.py
reverse_agent/workflows/nodes/__init__.py
reverse_agent/workflows/nodes/load_work_item.py
reverse_agent/workflows/nodes/load_planning_context.py
reverse_agent/workflows/nodes/classify_risk.py
reverse_agent/workflows/nodes/request_authorization.py
reverse_agent/workflows/nodes/acceptance_gate.py
```

Required graph:

```text
START
→ load_work_item
→ load_planning_context
→ classify_risk
→ conditional route
   ├─ R0/R1 → acceptance_gate
   └─ R2/R3 → request_authorization → acceptance_gate
→ END
```

Constraints:

- Shadow mode only.
- No shell execution.
- No source mutation by graph nodes.
- No push or PR creation by graph nodes.
- Use an in-memory or test checkpointer.
- Same input must produce equivalent final state.
- Checkpoint/resume must be demonstrated by tests.

### Package D — Trust authorization adapter

Create:

```text
reverse_agent/trust/__init__.py
reverse_agent/trust/authorization.py
```

Expose a narrow protocol:

```python
class TrustAuthorizationPort(Protocol):
    def authorize(self, request: AuthorizationRequest) -> AuthorizationResult:
        ...
```

The compatibility implementation may reuse:

```text
TransitionDecision
TransitionCommandPlan
ExecutionEnvelope
validate_transition
```

It must not:

- import the full legacy closeout lifecycle;
- read final-check, report-summary, final seal, context sync, or state manifest;
- make Decision mandatory for R0/R1 target behavior;
- modify the transition-kernel modules;
- return ambiguous success.

Allowed results:

```text
AUTHORIZED
APPROVAL_REQUIRED
BLOCKED
```

### Package E — Planning and GitHub adapters

Create:

```text
reverse_agent/adapters/__init__.py
reverse_agent/adapters/bmad_planning.py
reverse_agent/adapters/github_work_item.py
reverse_agent/adapters/github_truth.py
```

BMAD adapter scope:

- Parse structured fixture metadata for Product Brief, PRD, architecture, and story references.
- Validate digest and required fields.
- Never emit command authorization.
- Do not install BMAD in this round.

GitHub work-item adapter scope:

- Convert structured fixture data to `GitHubWorkItem`.
- Require repository, item number, acceptance criteria, requested operations, and requested paths.
- Fail closed on incomplete identity.

GitHub truth scope:

- Represent branch, commit, PR, and check observations.
- Require repository, exact SHA or item identity, source, and observed-at time.
- Mark observations as caches, not primary truth.
- No live remote mutation from workflow nodes.

### Package F — Tests, CI, and documentation

Create:

```text
tests/test_architecture_contracts.py
tests/test_risk_classifier.py
tests/test_development_graph.py
tests/test_trust_authorization_adapter.py
tests/test_planning_and_github_adapters.py
docs/architecture/architecture-spine-v1.md
```

Update `.github/workflows/ci.yml` only as needed to run the new focused tests after the existing installation/import checks.

## 5. Required Tests

At minimum, tests must cover:

1. Stable model serialization and round trip.
2. PlanningReference cannot authorize commands.
3. Complete GitHub Work Item loads successfully.
4. Missing repository or work-item identity blocks.
5. Read-only review classifies R0.
6. Bounded local edit and tests classify R1.
7. Workflow or dependency change classifies R2.
8. Unknown binary execution classifies R3.
9. Conflicting or unknown operations block.
10. R0/R1 bypass the Trust Authorization Port.
11. R2/R3 invoke the Trust Authorization Port.
12. A blocked Trust result blocks acceptance.
13. An approval-required result remains non-executable.
14. Transition-kernel adapter preserves fail-closed behavior.
15. Graph nodes perform no shell or repository mutation.
16. Equivalent fixture input produces equivalent final state.
17. Checkpoint/resume reaches the same terminal state.
18. GitHub observations include provenance and cannot become repository truth.
19. Existing transition-kernel focused tests remain green.
20. Full repository tests remain green, or any unrelated pre-existing failure is recorded truthfully.

## 6. Commands and Execution Order

The inherited PR #8 command plan is stale and is not authority for this round.

Before substantive work, execute in this order:

```bash
git branch --show-current
```

```bash
git rev-parse HEAD
```

```bash
git status --short
```

```bash
python -m reverse_agent.project_gate transition-lint --state-dir project_state
```

```bash
python -m reverse_agent.project_gate transition-command-plan --state-dir project_state
```

```bash
python -m reverse_agent.project_gate transition-preflight --state-dir project_state
```

After the command plan is regenerated and inspected, implementation may proceed.

Authorized validation commands:

```bash
python -m pip install -e ".[test]"
```

```bash
python -m pytest tests/test_architecture_contracts.py tests/test_risk_classifier.py tests/test_development_graph.py tests/test_trust_authorization_adapter.py tests/test_planning_and_github_adapters.py -q
```

```bash
python -m pytest tests/test_project_gate.py -q
```

```bash
python -m pytest -q
```

```bash
git diff --check
```

```bash
git status --short
```

```bash
git diff --stat
```

Remote publication is allowed only after local acceptance. Stage explicit paths; do not use `git add -A`.

Expected publication commands:

```bash
git add pyproject.toml .github/workflows/ci.yml reverse_agent/architecture reverse_agent/workflows reverse_agent/trust reverse_agent/adapters tests/test_architecture_contracts.py tests/test_risk_classifier.py tests/test_development_graph.py tests/test_trust_authorization_adapter.py tests/test_planning_and_github_adapters.py docs/architecture/architecture-spine-v1.md project_state/pytest_result.txt project_state/codex_execution_report.md project_state/execution_report.md project_state/gates/command_plan.json project_state/gates/execution_log.json project_state/gates/transition_preflight_result.json project_state/gates/transition_command_plan_preview.json
```

```bash
git commit -m "architecture: add architecture spine v1"
```

```bash
git push -u origin codex/architecture-spine-v1
```

Create a Draft PR against `main`. Do not merge it.

## 7. Do Not Do

Do not:

- repair or extend closeout, report-summary, final seal, publication truth, state manifest, context sync, or round archive systems;
- modify `reverse_agent/project_gate.py` or `reverse_agent/control_plane/**`;
- modify State Gate or Decision Preflight workflows;
- implement a second workflow runtime;
- install BMAD, Microsoft Agent Framework, MetaGPT, or ChatDev;
- invoke model APIs;
- implement free-form multi-agent coding;
- enable runner dispatch;
- run unknown binaries or reverse-engineering tools;
- modify User Solve, frontend, solvers, harnesses, or sample profiles;
- create a database, queue, scheduler, or Web service;
- mirror every LangGraph node into legacy `project_state/gates` files;
- treat GitHub observations as authoritative over GitHub;
- make a Decision mandatory for the target R0/R1 path;
- weaken R2/R3 authorization to make tests pass;
- edit the generated command plan manually;
- use `git add -A`;
- push to `main`;
- merge, rebase, force-push, amend published history, delete branches, or create a release.

## 8. Acceptance Criteria

The round is successful only when all of the following are true:

1. The Decision commit is an ancestor of every implementation commit.
2. The current command plan was regenerated before substantive implementation.
3. The implementation branch descends from `0dbdc3cb82c7935ae715d7f3092f16e2242c0948`.
4. LangGraph is the only primary workflow runtime.
5. A fixture-backed development graph runs end to end in shadow mode.
6. R0/R1 use the standard path without full Decision authorization.
7. R2/R3 route through the Trust Authorization Port.
8. Unknown or incomplete input blocks.
9. The adapter reuses the transition kernel without modifying it.
10. BMAD references cannot authorize commands.
11. GitHub observations preserve provenance and remain non-authoritative caches.
12. Checkpoint/resume is tested.
13. No node executes shell commands or mutates the repository.
14. Focused architecture tests pass.
15. Existing transition-kernel tests pass.
16. `git diff --check` passes.
17. CI succeeds on the Draft PR exact head.
18. State Gate and Decision Preflight succeed on the same exact head.
19. The final report truthfully records tests, failures, limitations, branch, commit, PR, and remote checks.
20. The PR remains Draft and unmerged.

## 9. Required Final Report

Update `project_state/codex_execution_report.md` and the neutral report alias with:

- exact Decision and round identity;
- activation base SHA and final SHA;
- changed paths grouped by architecture package;
- dependency changes;
- graph topology;
- risk classification rules;
- Trust adapter boundary;
- all test commands and exact outcomes;
- checkpoint/resume evidence;
- confirmation that no shell or repository mutation occurred inside graph nodes;
- Draft PR number and exact-head CI results;
- known limitations and the next recommended bounded workstream.

## 10. Stop Condition

Stop after one Draft PR has exact-head CI, State Gate, and Decision Preflight success and the independent-audit handoff is ready.

Do not automatically begin Binary Evidence Firewall, Claim Ledger, real Agent dispatch, BMAD installation, User Solve migration, Web migration, or external tool integration.
