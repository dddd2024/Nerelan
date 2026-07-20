# QUEUED DECISION CANDIDATE

```json queue_meta
{
  "schema_version": 1,
  "queue_status": "QUEUED_NOT_ACTIVE",
  "candidate_path": "project_state/queued_decisions/decision_20260720_control_plane_transition_kernel_cutover_v1/decision_packet.md",
  "target_active_path": "project_state/decision_packet.md",
  "supersedes_candidate": "decision_20260720_selective_capability_integration_v2",
  "activation_policy": "Do not execute from this queued path or from PR #6. Fetch activation-time main, create a fresh execution branch, promote this packet to project_state/decision_packet.md, commit the Decision before implementation, generate and inspect the current full command-plan, and execute only commands present in that plan.",
  "estimated_effort_class": "large_engineering_cutover_round",
  "effort_target_note": "Designed for approximately ten to fourteen hours of bounded Codex work. Stop when the transition kernel, packaging baseline, schemas, tests, documentation, and exact-head CI evidence are complete. Do not pad the round or enter Workflow cutover, BMAD, LangGraph, Trust Layer, Web, Runner, or reverse-solving work."
}
```

```json decision_meta
{
  "schema_version": 1,
  "decision_id": "decision_20260720_control_plane_transition_kernel_cutover_v1",
  "round_id": "round_20260720_control_plane_transition_kernel_cutover_v1",
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
  "follows_last_decision_id": "decision_20260720_selective_capability_integration_v2",
  "follows_last_round_id": "round_20260720_selective_capability_integration_v2",
  "previous_audit_outcome": "BLOCKED",
  "workstream_id": "control-plane-transition-kernel",
  "large_structural_change_authorized": true,
  "fresh_execution_branch_from_current_main_required": true,
  "queued_packet_must_be_promoted_before_execution": true,
  "decision_commit_must_precede_implementation": true,
  "command_plan_precedes_substantive_execution": true,
  "command_plan_is_command_authority": true,
  "legacy_preflight_required_before_implementation": false,
  "legacy_final_check_is_acceptance_authority": false,
  "legacy_closeout_is_acceptance_authority": false,
  "legacy_state_manifest_is_acceptance_authority": false,
  "transition_kernel_required": true,
  "product_source_mutation_allowed": true,
  "workflow_mutation_allowed": false,
  "framework_installation_allowed": false,
  "runner_dispatch_allowed": false,
  "model_api_invocation_allowed": false,
  "external_reverse_tool_invocation_allowed": false,
  "destructive_operations_allowed": false,
  "direct_push_to_main_allowed": false,
  "merge_allowed": false,
  "force_push_allowed": false,
  "rebase_during_execution_allowed": false,
  "post_remote_evidence_commit_allowed": false,
  "scope_policy": "single_mainline_control_plane_transition_kernel"
}
```

# DECISION_PACKET

## 1. Goal

Build an independent Control Plane Transition Kernel that can authorize and validate architecture-migration rounds without depending on the legacy closeout, startup-snapshot, state-manifest, report-summary, final-check, final-seal, or remote-observation chain.

This round replaces repeated selective-integration bootstrap attempts with one bounded structural cutover foundation.

Required outcomes:

1. extract transition-specific authority, models, command authorization, scope validation, and preflight logic from the legacy monolithic project gate;
2. add a transition preflight that does not require current legacy startup, baseline, closeout, final-check, state-manifest, report-summary, or final-seal artifacts;
3. keep Decision identity, round identity, APPROVED status, active skill, legal mainline, branch/base ancestry, command-plan identity, path scope, and forbidden-operation checks fail-closed;
4. add explicit command contracts for transition Decisions while retaining the legacy command-plan path for legacy Decisions;
5. preserve all legacy commands and behavior unless a compatibility adapter is explicitly required;
6. add minimal Python packaging so existing GitHub Actions editable-install steps can run in clean checkouts;
7. add schemas, focused tests, and architecture documentation;
8. create a Draft implementation PR from a fresh activation-time main branch and collect exact-head CI evidence;
9. stop before Workflow cutover, BMAD, LangGraph, Trust Layer, GitHub adapter, Runner, Web, User Solve, or reverse-solving implementation.

Target sequence:

```text
fresh activation-time main
→ promote and commit Decision
→ generate and inspect full command-plan
→ do not run legacy preflight as an implementation prerequisite
→ add packaging baseline
→ implement transition kernel modules
→ route transition CLI commands through project_gate
→ add schemas and focused tests
→ run only command-plan-authorized tests and Git checks
→ create Draft PR
→ collect exact-head CI evidence
→ stop
```

Estimated effort: approximately 10–14 hours of Codex Goal-mode work. Stop when acceptance criteria are met; do not expand scope to consume the time estimate.

## 2. Current Evidence

- The selective-capability-integration v2 activation attempt correctly stopped before implementation and publication.
- Its blocker demonstrates that the legacy control plane cannot reliably authorize its own migration: the new Decision and generated command-plan can still be judged through stale startup/legacy-closeout assumptions.
- Current main contains a large project-gate module that combines legacy preflight, command planning, reporting, closeout, CI evidence, Runner, and User Solve concerns.
- Existing `--allow-consumed` support is already present and must not be reimplemented.
- Existing command-plan, execution-log, policy-lint, report-summary, final-check, closeout, CI gates, Runner contracts, and User Solve foundations must not be described as absent or rebuilt from zero.
- The new work is a separate transition path, not another exception inside the legacy closeout chain.
- Current `task_packet.json` is background-only and cannot control this engineering round.
- Current sample-derived state and old context packets may be stale and must not override the promoted Decision, live Git state, or current command-plan.
- PR #5 and PR #7 remain read-only migration evidence.
- PR #6 is plan storage only and must not be used as the execution branch.
- Running Python unit tests, Git read/check commands, and existing CI is allowed.
- Running unknown binaries, reverse tools, debuggers, emulators, hooks, runtime probes, or model APIs is prohibited.
- Full `solve_reports/`, `PROJECT_PROGRESS_LOG.txt`, and unrelated historical rounds are not required.
- Legacy final-check, closeout, state-manifest freshness, report-summary, final-seal, and remote-observation mirrors are not acceptance authorities for this round.
- This round is large by authorization, but it advances only the `engineering_branch` control-plane-transition mainline.

## 3. Do Not Do

Do not:

- execute this packet while it remains under `project_state/queued_decisions/**`;
- execute from PR #6 or its branch;
- continue either blocked local selective-integration branch;
- modify, merge, close, rebase, force-push, or mark PR #5 or PR #7 ready for review;
- copy PR #5 or PR #7 wholesale;
- repair legacy report-summary, final-check, run-closeout, close-round, final-seal, state-manifest, context-sync, or remote-observation chains;
- add another selective-integration v3/v4 exception round;
- delete or rewrite legacy artifacts or historical rounds;
- repeat implementation of `--allow-consumed`;
- move the full legacy `project_gate.py` implementation into new modules;
- make transition behavior the default for legacy Decisions;
- weaken Decision identity, round identity, skill, mainline, branch, ancestry, command, scope, or forbidden-operation checks;
- manually fabricate or edit `command_plan.json`;
- execute a command absent from the generated command-plan;
- modify `.github/workflows/**` in this round;
- install BMAD, LangGraph, Microsoft Agent Framework, MetaGPT, ChatDev, or any other agent framework;
- implement real Agent dispatch, checkpointing, scheduling, database, queue, or Web orchestration;
- modify frontend, User Solve, solver, harness, sample, tool-adapter, or reverse-analysis code;
- run reverse tools, runtime probes, unknown binaries, debuggers, emulators, hooks, or model APIs;
- add speculative runtime dependencies;
- commit `*.egg-info`, `*.egg-link`, `build/`, `dist/`, caches, or virtual environments;
- modify roadmap/workstreams in this engineering round;
- use `git add -A`;
- push directly to `main`;
- merge, tag, rebase during execution, force-push, amend published history, delete branches, or alter secrets;
- commit remote workflow receipts after the final implementation head is published;
- automatically begin Workflow cutover or any later workstream.

## 4. Files To Inspect

Required current authority and state after activation:

```text
project_state/decision_packet.md
project_state/task_packet.json
project_state/current_state.json
project_state/artifact_index.json
project_state/negative_results.json
project_state/codex_execution_report.md
project_state/pytest_result.txt
project_state/gates/command_plan.json
project_state/gates/execution_log.json
project_state/gates/preflight_result.json
project_state/gates/startup_snapshot.json
project_state/gates/round_baseline.json
project_state/context/current_context_packet.json
project_state/state_manifest.json
.codex-skills/registry.json
```

Required source and test inspection:

```text
reverse_agent/project_gate.py
reverse_agent/project_state.py
reverse_agent/decision_preflight.py
reverse_agent/project_runner_contract.py

tests/test_project_gate.py
tests/test_project_reports.py
tests/test_project_control_plane.py
tests/test_decision_preflight.py
tests/test_project_state.py

.github/workflows/ci.yml
.github/workflows/state-gate.yml
.github/workflows/decision-preflight.yml
.gitignore
```

Required searches:

```text
decision_command_plan_conflict
decision_not_consumed_by_report
startup_snapshot
round_baseline
run_closeout
final-check
command-plan
allow_consumed
allowed_source_files
forbidden_mutated_paths
```

Read-only evidence:

```text
PR #5 head: 6a2867467c90cf37929787be3ba6061fcbb81312
PR #7 head: 7cd75fcaa60cb6ecd7730c98bc5bf693716e45ec
```

Do not inspect complete `solve_reports/`, `PROJECT_PROGRESS_LOG.txt`, unrelated historical rounds, or unrelated sample artifacts.

## 5. Required Audit

The final report must answer every item separately with exact path/value evidence:

1. Was execution started from a fresh branch based on activation-time `origin/main`?
2. Was this packet promoted to `project_state/decision_packet.md` before implementation?
3. Was the Decision committed before every source/test/packaging/documentation change?
4. Was the current command-plan generated before substantive implementation?
5. Was the command-plan left machine-generated and unedited?
6. Was legacy preflight deliberately not used as the implementation prerequisite?
7. Was `--allow-consumed` reused without reimplementation?
8. Was the transition kernel implemented as separate modules rather than more legacy special cases?
9. Does transition preflight avoid `startup_snapshot.json`?
10. Does it avoid `round_baseline.json`?
11. Does it avoid legacy closeout/final-check/final-seal artifacts?
12. Does it avoid state-manifest freshness as a transition prerequisite?
13. Does it avoid report-summary and remote-observation mirrors?
14. Does it require exact Decision ID and round ID?
15. Does it require `status=APPROVED`?
16. Does it require an active registered skill?
17. Does it validate legal mainline?
18. Does it validate branch/base and Decision ancestry?
19. Does it validate command-plan Decision/round identity?
20. Does it validate allowed and forbidden paths?
21. Does it fail closed for undeclared commands?
22. Does it distinguish local and `ci_only` execution surfaces?
23. Does it block direct-main, force-push, merge, destructive, and out-of-scope operations?
24. Do legacy Decisions retain legacy behavior?
25. Were no legacy artifacts deleted or rewritten?
26. Is packaging metadata minimal and installable?
27. Are tests/docs/project_state excluded from package discovery?
28. Are test tools absent from runtime dependencies unless explicitly justified?
29. Are editable-install/build outputs ignored and absent from the committed diff?
30. Is transition logic modularized outside the legacy monolith?
31. Is `project_gate.py` limited to CLI routing/compatibility changes for the new path?
32. Do new schemas validate independently?
33. Were focused tests added for valid and invalid transition authority cases?
34. Were only command-plan-authorized commands executed?
35. Does `pytest_result.txt` contain actual command stdout/stderr/exit codes?
36. Does `execution_log.json` cover every executed command?
37. Did `git diff --check` pass?
38. Is the final diff limited to allowed paths?
39. Are all `.github/workflows/**` files unchanged?
40. Did exact-head CI complete install/import/tests successfully?
41. Were legacy State Gate/Decision Preflight failures recorded only as migration debt?
42. Was no new legacy repair Decision created?
43. Was no post-evidence commit created?
44. Is the next round explicitly bounded to Workflow transition cutover?
45. Did the round stop before BMAD, LangGraph, Trust Layer, Runner, Web, or reverse-solving work?

## 6. Implementation Scope

### 6.1 Activation and authority

On a fresh branch from activation-time `origin/main`:

1. create `codex/control-plane-transition-kernel-v1`;
2. promote this packet to `project_state/decision_packet.md`;
3. commit the Decision before implementation;
4. confirm the Decision commit is an ancestor of all implementation commits;
5. generate and inspect the current full `project_state/gates/command_plan.json`;
6. do not manually edit or fabricate the plan;
7. confirm the plan authorizes standard startup checks, at least one existing full/focused pytest surface covering the allowed tests, `git diff --check`, and `git status --short`;
8. do not execute legacy preflight as an implementation prerequisite;
9. if the plan cannot authorize standard tests/Git checks without manual editing, stop as `BLOCKED`.

### 6.2 Packaging baseline

Allowed files:

```text
.gitignore
pyproject.toml
```

Requirements:

- use a minimal setuptools build backend;
- include only `reverse_agent*` packages;
- exclude `tests*`, `project_state*`, and `docs*`;
- require the actual supported Python baseline confirmed by current CI/tests;
- place test/development tooling in an optional development/test group, not runtime dependencies;
- add no unused runtime dependency;
- add ignores for `*.egg-info/`, `*.egg-link`, `build/`, and `dist/`;
- do not commit generated packaging outputs.

### 6.3 Transition kernel modules

Allowed new files:

```text
reverse_agent/control_plane/__init__.py
reverse_agent/control_plane/models.py
reverse_agent/control_plane/transition.py
reverse_agent/control_plane/command_authority.py
reverse_agent/control_plane/legacy_adapter.py
```

`models.py` must define stable typed structures for:

- `TransitionAuthority`;
- `TransitionDecision`;
- `TransitionCommandPlan`;
- `TransitionPreflightResult`;
- `ExecutionEnvelope`.

`transition.py` must validate:

```text
Decision identity
→ APPROVED status
→ active skill
→ legal mainline
→ branch/base
→ Decision ancestry
→ command-plan identity
→ allowed/forbidden scope
→ forbidden operations
→ deterministic result
```

It must not require or read as authority:

```text
startup_snapshot.json
round_baseline.json
run_closeout_result.json
final_gate_result.json
state_manifest.json
report_summary_synthesis.json
final_evidence_seal.json
remote_check_observation.json
```

`command_authority.py` must support explicit command entries with at least:

```json
{
  "command": "...",
  "phase": "test",
  "required": true,
  "expected_exit_codes": [0],
  "execution_surface": "local"
}
```

Requirements:

- canonical command identity;
- undeclared commands denied by default;
- local and `ci_only` separated;
- no ambiguous Markdown-only command inference for transition Decisions;
- deterministic serialization and validation;
- legacy command-plan behavior preserved through the adapter.

`legacy_adapter.py` may:

- identify legacy Decisions;
- invoke existing legacy readers/validators;
- preserve existing legacy command/preflight behavior;
- label legacy artifacts as compatibility evidence.

It must not copy the entire legacy project-gate implementation.

### 6.4 Project-gate routing

Allowed modification:

```text
reverse_agent/project_gate.py
```

Required additions:

```text
transition-lint
transition-command-plan
transition-preflight
```

Requirements:

- route transition operations to the new modules;
- retain all legacy CLI names and behavior;
- do not make transition mode the legacy default;
- do not add transition checks as more branches inside legacy closeout/final-check logic;
- do not modify User Solve, Runner, CI observation, or reverse-solving behavior.

### 6.5 Schemas

Allowed new files:

```text
project_state/schemas/transition_authority.schema.json
project_state/schemas/transition_command_plan.schema.json
project_state/schemas/execution_envelope.schema.json
project_state/schemas/transition_preflight_result.schema.json
```

Requirements:

- explicit required fields;
- explicit `additionalProperties` policy;
- machine-verifiable Decision/round/command/scope data;
- no legacy closeout/state-manifest/final-seal fields required.

### 6.6 Tests

Allowed modifications:

```text
tests/test_project_gate.py
tests/test_project_control_plane.py
tests/test_decision_preflight.py
tests/test_project_reports.py
tests/test_project_state.py
```

Allowed new file when needed:

```text
tests/test_control_plane_transition.py
```

If the new test file is not already executed by existing CI, core transition assertions must also be placed in an existing CI-covered test surface.

Required cases:

- valid transition Decision passes;
- stale startup snapshot does not block;
- stale baseline does not block;
- missing/failed legacy closeout does not block;
- failed legacy final-check does not block;
- stale legacy state manifest does not block;
- wrong Decision ID blocks;
- wrong round ID blocks;
- non-APPROVED status blocks;
- inactive skill blocks;
- illegal mainline blocks;
- wrong branch/base or missing ancestry blocks;
- command-plan identity mismatch blocks;
- undeclared command blocks;
- path scope violation blocks;
- forbidden operation blocks;
- local/ci-only confusion blocks;
- legacy Decision still follows legacy behavior;
- explicit command contract serializes deterministically;
- packaging metadata and ignores are correct.

### 6.7 Documentation

Allowed new files:

```text
docs/architecture/control-plane-transition-kernel.md
docs/architecture/legacy-control-plane-boundary.md
docs/architecture/transition-command-authority.md
```

Documentation must explain:

- legacy versus transition authority boundaries;
- why transition rounds do not depend on legacy closeout/state mirrors;
- how command authority remains fail-closed;
- compatibility and rollback behavior;
- the exact next Workflow cutover round.

### 6.8 Current-round evidence

Allowed updates:

```text
project_state/decision_packet.md
project_state/pytest_result.txt
project_state/codex_execution_report.md
project_state/execution_report.md
project_state/gates/command_plan.json
project_state/gates/execution_log.json
```

Allowed new artifacts:

```text
project_state/gates/transition_preflight_result.json
project_state/gates/transition_command_plan_preview.json
```

Read-only legacy artifacts:

```text
project_state/state_manifest.json
project_state/context/current_context_packet.json
project_state/gates/run_closeout_result.json
project_state/gates/final_gate_result.json
project_state/gates/final_evidence_seal.json
project_state/rounds/**
```

### 6.9 Publication boundary

After local validation:

- create a new Draft PR to `main`;
- do not reuse PR #5, #6, or #7;
- push one final implementation head;
- do not mutate the branch after remote evidence collection starts;
- require exact-head CI install/import/test success;
- record State Gate/Decision Preflight legacy failures without repairing them;
- do not commit remote receipts;
- do not merge or start the next workstream.

## 7. Tests

Initial commands:

```powershell
Set-Location F:\reverse-agent
Get-Location
Test-Path F:\reverse-agent
git rev-parse --show-toplevel
git status --short
git rev-parse HEAD
git merge-base HEAD origin/main
python -m reverse_agent.project_gate decision-lint --state-dir project_state
python -m reverse_agent.project_gate command-plan --state-dir project_state
python -m reverse_agent.project_gate command-plan --state-dir project_state --json
```

Do not execute before implementation:

```text
legacy preflight
run-closeout
close-round
final-check
final-evidence-seal
state-manifest refresh
post-final-evidence-sync
```

After implementation, execute only commands present in the generated command-plan.

Preferred existing test surface when authorized:

```powershell
python -m pytest `
  tests/test_project_gate.py `
  tests/test_project_reports.py `
  tests/test_project_control_plane.py `
  tests/test_decision_preflight.py `
  tests/test_project_state.py -q
```

The exact test command may differ if the generated plan uses an existing broader command. Do not execute a plan-external command.

Required Git checks when authorized:

```powershell
git diff --check
git status --short
```

Transition CLI checks may be executed only when authorized:

```powershell
python -m reverse_agent.project_gate transition-lint --state-dir project_state
python -m reverse_agent.project_gate transition-preflight --state-dir project_state
```

If not authorized, pytest must exercise equivalent Python APIs.

`pytest_result.txt` must retain stdout, stderr, and exit code for every executed required command. `execution_log.json` must cover every executed command.

Remote exact-head acceptance:

```text
CI:
  Install package = success
  Import check = success
  Focused tests = success
  workflow conclusion = success

State Gate and Decision Preflight:
  record exact-head conclusions and failed steps;
  legacy-chain failures are migration debt, not acceptance blockers;
  do not create a legacy repair round.
```

## 8. Stop Conditions

Stop and report `BLOCKED` without expanding scope if:

- activation-time main cannot be fetched or a fresh branch cannot be created;
- this packet is not promoted and committed before implementation;
- the active skill is unavailable;
- the command-plan cannot be generated;
- standard tests and Git checks cannot be authorized without editing the plan;
- continuing requires manual command-plan modification;
- continuing requires legacy preflight as an implementation prerequisite;
- continuing requires repairing startup snapshot, baseline, closeout, final-check, state-manifest, report-summary, seal, or remote-observation chains;
- transition preflight must depend on any legacy acceptance artifact;
- transition validation accepts wrong Decision, round, status, skill, mainline, branch, ancestry, command, scope, or forbidden operation;
- legacy Decision behavior is unintentionally changed;
- completing the round requires modifying `.github/workflows/**`;
- completing the round requires modifying frontend, User Solve, Runner, solver, harness, sample, tool-adapter, or reverse-analysis code;
- completing the round requires installing BMAD, LangGraph, another agent framework, a database, queue, scheduler, or Web runtime;
- deleting or rewriting historical state becomes necessary;
- packaging requires an unjustified runtime dependency;
- generated egg-info/build/dist files enter the committed diff;
- tests fail and repair requires leaving the allowed paths;
- exact-head CI install/import/tests fail for a reason outside the allowed paths;
- Codex attempts to repair downstream legacy State Gate/Decision Preflight steps;
- direct-main, merge, rebase, force-push, destructive, or secret-changing operations are attempted;
- a post-remote-evidence commit would be required;
- the round attempts to start Workflow cutover or any later workstream automatically.

On successful completion, stop after the Draft PR and exact-head evidence are ready for independent audit.
