# QUEUED DECISION CANDIDATE

```json queue_meta
{
  "schema_version": 1,
  "queue_status": "QUEUED_NOT_ACTIVE",
  "candidate_path": "project_state/queued_decisions/decision_20260720_transition_workflow_cutover_and_ci_test_bootstrap_v1/decision_packet.md",
  "target_active_path": "project_state/decision_packet.md",
  "supersedes_candidate": "decision_20260720_control_plane_transition_kernel_cutover_v1",
  "activation_policy": "Do not execute from PR #6. Continue on PR #8 only after confirming its exact starting head, promote this packet to project_state/decision_packet.md on the PR #8 branch, commit the Decision before any new implementation change, regenerate the current command-plan, and then execute the bounded workflow cutover.",
  "estimated_effort_class": "medium_large_workflow_cutover_round",
  "effort_target_note": "Designed for approximately six to ten hours of bounded Codex work. Preserve the accepted transition-kernel implementation, fix clean-runner test installation, add fail-closed control-plane mode routing, cut State Gate and Decision Preflight over conditionally, obtain three exact-head successful workflows, then stop."
}
```

```json decision_meta
{
  "schema_version": 1,
  "decision_id": "decision_20260720_transition_workflow_cutover_and_ci_test_bootstrap_v1",
  "round_id": "round_20260720_transition_workflow_cutover_and_ci_test_bootstrap_v1",
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
  "follows_last_decision_id": "decision_20260720_control_plane_transition_kernel_cutover_v1",
  "follows_last_round_id": "round_20260720_control_plane_transition_kernel_cutover_v1",
  "previous_audit_outcome": "REWORK_REQUIRED",
  "workstream_id": "workflow-transition-cutover",
  "continue_existing_execution_branch": true,
  "required_branch": "codex/control-plane-transition-kernel-v1",
  "required_starting_head": "783f3c68912d0fde46cd725d292f5fba1fcec916",
  "reuse_draft_pr_number": 8,
  "new_pull_request_allowed": false,
  "decision_commit_must_precede_new_implementation": true,
  "command_plan_precedes_substantive_execution": true,
  "command_plan_is_local_command_authority": true,
  "transition_kernel_required": true,
  "workflow_cutover_required": true,
  "legacy_behavior_preservation_required": true,
  "legacy_final_check_is_acceptance_authority": false,
  "legacy_closeout_is_acceptance_authority": false,
  "legacy_state_manifest_is_acceptance_authority": false,
  "workflow_mutation_allowed": true,
  "workflow_mutation_scope": [
    ".github/workflows/ci.yml",
    ".github/workflows/state-gate.yml",
    ".github/workflows/decision-preflight.yml"
  ],
  "product_source_mutation_allowed": true,
  "product_source_mutation_scope": [
    "reverse_agent/project_gate.py",
    "reverse_agent/control_plane/legacy_adapter.py"
  ],
  "test_mutation_scope": [
    "tests/test_project_gate.py"
  ],
  "documentation_mutation_scope": [
    "docs/architecture/control-plane-transition-kernel.md",
    "docs/architecture/legacy-control-plane-boundary.md",
    "docs/architecture/transition-command-authority.md",
    "docs/architecture/workflow-transition-cutover.md"
  ],
  "packaging_metadata_read_only": true,
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
  "scope_policy": "single_mainline_transition_workflow_cutover_only"
}
```

```json workflow_contract
{
  "schema_version": 1,
  "install_command": "python -m pip install -e \".[test]\"",
  "mode_detection_command": "python -m reverse_agent.project_gate control-plane-mode --state-dir project_state",
  "transition_commands": [
    "python -m reverse_agent.project_gate transition-lint --state-dir project_state",
    "python -m reverse_agent.project_gate transition-command-plan --state-dir project_state",
    "python -m reverse_agent.project_gate transition-preflight --state-dir project_state"
  ],
  "focused_test_command": "python -m pytest tests/test_project_gate.py tests/test_project_reports.py tests/test_project_jobs.py tests/test_post_final_evidence_sync.py tests/test_decision_preflight.py tests/test_project_state.py -q",
  "legacy_mode_value": "legacy",
  "transition_mode_value": "transition",
  "state_gate_full_history_required": true,
  "decision_preflight_full_history_required": true,
  "ci_full_history_required": false,
  "legacy_pipeline_preserved": true,
  "transition_pipeline_skips_legacy_acceptance_chain": true
}
```

# DECISION_PACKET

## 1. Goal

Complete the first real Workflow transition cutover on the existing PR #8 branch without rebuilding the transition kernel and without reopening the legacy closeout chain.

The prior round produced a usable transition kernel and passed 1540 local tests, but exact-head CI failed because the clean runner installed only the base package while `pytest` was declared in the optional `test` extra. State Gate and Decision Preflight also still invoked the legacy preflight path, which was intentionally deferred to this round.

This round must deliver all of the following:

1. preserve the transition-kernel implementation already committed at `783f3c68912d0fde46cd725d292f5fba1fcec916`;
2. keep `pytest` out of runtime dependencies and install the existing `test` extra in all workflows that execute tests;
3. add a deterministic, fail-closed `control-plane-mode` CLI that outputs exactly `legacy` or `transition`;
4. route State Gate and Decision Preflight conditionally:
   - transition Decisions run only transition lint, transition command-plan validation, transition preflight, focused tests, and evidence upload;
   - legacy Decisions retain the existing legacy pipeline;
5. use full Git history in the two governance workflows so branch/base and Decision ancestry can be checked;
6. keep CI focused on installation, import, and tests, but install the test extra;
7. obtain exact-head success for CI, State Gate, and Decision Preflight on the same final commit;
8. stop after remote success and independent-audit readiness;
9. do not begin BMAD, LangGraph, Trust Layer, GitHub adapter, Runner, Web, User Solve, or reverse-analysis implementation.

Target sequence:

```text
PR #8 exact head 783f3c68...
→ promote and commit this Decision on the same branch
→ regenerate and inspect the current command-plan
→ verify the existing transition kernel remains intact
→ add fail-closed control-plane mode detection
→ install .[test] in all test-running workflows
→ conditionally route transition and legacy workflow paths
→ add deterministic tests for mode detection and workflow contracts
→ run command-plan-authorized local tests
→ create one final validation commit on PR #8
→ wait for CI + State Gate + Decision Preflight on that exact head
→ stop
```

Estimated effort: approximately 6–10 hours of Codex Goal-mode work. Do not expand scope to consume the estimate.

## 2. Current Evidence

- PR #8 is Draft, open, mergeable, and based on `main`.
- The audited exact head is `783f3c68912d0fde46cd725d292f5fba1fcec916`.
- The Decision commit `5c3363b7827b371061390af875ff2f462024dd04` precedes the implementation commit.
- The transition kernel exists under `reverse_agent/control_plane/` and is separated from the legacy acceptance chain.
- `legacy_adapter.dispatch_preflight` already preserves legacy behavior unless `transition_kernel_required` is true.
- `pyproject.toml` already declares `test = ["pytest>=8,<9"]` and correctly keeps runtime dependencies empty.
- Current CI, State Gate, and Decision Preflight install only `python -m pip install -e .`.
- Current CI then invokes `python -m pytest`, so a clean runner lacks the pytest module.
- Exact-head remote results for the prior round were:
  - CI: Install package passed; Import check passed; Focused tests failed;
  - State Gate: Install package passed; legacy Project gate preflight failed;
  - Decision Preflight: Install package passed; legacy Project gate preflight failed.
- The prior Decision explicitly required exact-head CI install/import/tests success, so the prior round is formally `REWORK_REQUIRED`.
- The prior Decision also explicitly deferred Workflow cutover to the next bounded round.
- Local evidence records two timeout attempts, one intermediate failing pytest run, then successful 1539-pass and 1540-pass runs; this history must remain intact.
- `execution_log.json` truthfully preserves failed and successful commands and must not be rewritten as an all-green history.
- Legacy startup snapshot, baseline, report-summary, final-check, closeout, state-manifest, final seal, and remote-observation mirrors are not acceptance authorities for this round.
- PR #5 and PR #7 remain read-only migration evidence.
- PR #6 remains plan storage only.
- No framework installation, reverse tool, model API, database, queue, scheduler, or Web runtime is required.

## 3. Do Not Do

Do not:

- execute this packet while it remains under `project_state/queued_decisions/**`;
- execute from PR #6 or its branch;
- create a new implementation branch or a new PR;
- start from any PR #8 head other than `783f3c68912d0fde46cd725d292f5fba1fcec916` unless a new audit is supplied;
- revert, rewrite, or wholesale replace the existing transition-kernel modules;
- move `pytest` into `[project].dependencies`;
- add `requests`, BMAD, LangGraph, Agent Framework, database clients, Web frameworks, or speculative dependencies;
- modify `pyproject.toml` unless an independently demonstrated metadata defect exists;
- change `.gitignore` unless a newly generated packaging artifact is not already covered;
- make transition mode the default when the Decision contract does not explicitly request it;
- route malformed or unreadable Decision contracts to transition or legacy silently;
- let mode detection print logs, warnings, JSON, or multiple lines to stdout;
- run both transition and legacy pipelines for the same workflow execution;
- remove any legacy workflow step; legacy steps may only receive explicit mode conditions and otherwise retain their commands and order;
- alter legacy command semantics;
- repair legacy report-summary, final-check, closeout, seal, state-manifest, context-sync, or remote-observation systems;
- require those legacy artifacts for transition acceptance;
- modify User Solve, Runner, frontend, solver, harness, sample, tool adapter, reverse-analysis, or CI observation business logic;
- install BMAD, LangGraph, Microsoft Agent Framework, MetaGPT, ChatDev, or another agent framework;
- run unknown binaries, reverse tools, debuggers, emulators, runtime probes, hooks, or model APIs;
- manually edit or fabricate `project_state/gates/command_plan.json`;
- execute a local command absent from the generated command-plan;
- use `git add -A`;
- push directly to `main`;
- merge, rebase, force-push, amend published history, delete branches, change secrets, or tag a release;
- commit remote workflow receipts after the final validation head;
- automatically begin the next workstream.

## 4. Files To Inspect

Required current authority and evidence on PR #8:

```text
project_state/decision_packet.md
project_state/codex_execution_report.md
project_state/pytest_result.txt
project_state/gates/command_plan.json
project_state/gates/execution_log.json
project_state/gates/transition_preflight_result.json
project_state/gates/transition_command_plan_preview.json
.codex-skills/registry.json
```

Required implementation files:

```text
pyproject.toml
reverse_agent/project_gate.py
reverse_agent/control_plane/legacy_adapter.py
reverse_agent/control_plane/models.py
reverse_agent/control_plane/transition.py
reverse_agent/control_plane/command_authority.py
tests/test_project_gate.py
.github/workflows/ci.yml
.github/workflows/state-gate.yml
.github/workflows/decision-preflight.yml
docs/architecture/control-plane-transition-kernel.md
docs/architecture/legacy-control-plane-boundary.md
docs/architecture/transition-command-authority.md
```

Required remote evidence:

```text
PR #8
starting head: 783f3c68912d0fde46cd725d292f5fba1fcec916
prior CI run: 29736618760
prior State Gate run: 29736618745
prior Decision Preflight run: 29736618765
```

Required searches:

```text
control-plane-mode
transition_kernel_required
dispatch_preflight
transition-lint
transition-command-plan
transition-preflight
python -m pip install -e .
python -m pytest
fetch-depth
```

Do not inspect complete `solve_reports/`, `PROJECT_PROGRESS_LOG.txt`, unrelated historical rounds, or unrelated sample artifacts.

## 5. Required Audit

The final report must answer every item separately with exact path/value evidence:

1. Did execution continue from PR #8 exact starting head `783f3c68912d0fde46cd725d292f5fba1fcec916`?
2. Was this Decision promoted and committed before every new source, test, documentation, or Workflow change?
3. Was the new Decision commit an ancestor of the final validation commit?
4. Was the current command-plan regenerated before substantive work?
5. Was the command-plan left machine-generated and unedited?
6. Was the existing transition-kernel implementation preserved rather than rebuilt?
7. Did `pyproject.toml` keep `pytest` in the optional `test` extra?
8. Did runtime dependencies remain empty or otherwise unchanged?
9. Do all workflows that invoke pytest install `.[test]` first?
10. Is the exact install command quoted safely as `python -m pip install -e ".[test]"`?
11. Does `control-plane-mode` output exactly one token: `legacy` or `transition`?
12. Does an explicit `transition_kernel_required=true` contract select transition mode?
13. Does an absent or false flag select legacy mode?
14. Does malformed Decision metadata or contract fail closed with a nonzero exit?
15. Is mode detection covered by unit tests?
16. Do State Gate and Decision Preflight use `fetch-depth: 0`?
17. Does CI retain its existing checkout depth unless independently required?
18. Does CI otherwise preserve its install/import/test structure?
19. Do State Gate and Decision Preflight run exactly one authority path per execution?
20. In transition mode, are legacy preflight, post-final sync, closeout-related, report-summary, final-check, state-manifest, and remote-observation steps skipped?
21. In transition mode, do `transition-lint`, `transition-command-plan`, and `transition-preflight` run?
22. In legacy mode, do all existing legacy steps remain present, ordered, and runnable?
23. Were no legacy step commands silently changed?
24. Are transition and legacy conditions explicit and readable in the Workflow YAML?
25. Does the focused pytest step run after the selected authority path succeeds?
26. Does evidence upload still run with `if: always()`?
27. Is `project_gate.py` limited to the new mode-routing CLI and thin dispatch changes?
28. Does `legacy_adapter.py` remain the compatibility boundary?
29. Are wrong or ambiguous mode values rejected?
30. Does transition preflight still fail closed for wrong Decision, round, status, skill, mainline, branch, ancestry, command, scope, and forbidden operation?
31. Do legacy Decision tests still pass?
32. Do new Workflow contract tests verify install extras, full history, conditions, and commands?
33. Were only Decision-allowed local commands executed?
34. Does `pytest_result.txt` preserve stdout, stderr, exit code, and any failed attempts?
35. Does `execution_log.json` cover every executed command in observed order?
36. Did `git diff --check` pass?
37. Is the final Git diff limited to allowed paths?
38. Was no `egg-info`, build, dist, cache, or virtual environment committed?
39. Did exact-head CI complete with Install package, Import check, Focused tests, and overall success?
40. Did exact-head State Gate complete with overall success in transition mode?
41. Did exact-head Decision Preflight complete with overall success in transition mode?
42. Did all three successful workflows evaluate the same final head?
43. Was no post-evidence commit added?
44. Was PR #8 kept Draft and unmerged?
45. Were PR #5, PR #6, and PR #7 left unchanged?
46. Was no legacy cleanup Decision created?
47. Did the round stop before BMAD, LangGraph, Trust Layer, GitHub adapter, Runner, Web, User Solve, or reverse-solving work?
48. Is the next workstream clearly identified without being started automatically?

## 6. Implementation Scope

### 6.1 Activation and branch boundary

On the existing PR #8 branch:

1. fetch remote state;
2. switch to `codex/control-plane-transition-kernel-v1`;
3. require `git rev-parse HEAD` to equal `783f3c68912d0fde46cd725d292f5fba1fcec916`;
4. require PR #8 Head to equal the same SHA;
5. promote this packet to `project_state/decision_packet.md`;
6. commit the Decision alone;
7. regenerate and inspect `project_state/gates/command_plan.json`;
8. do not manually edit the plan;
9. run transition lint/preflight only when authorized by the generated plan or through tests that exercise the same API;
10. stop as `BLOCKED` if the branch or PR Head has moved unexpectedly.

### 6.2 Packaging and CI test bootstrap

`pyproject.toml` is read-only by default.

Its required state is:

```toml
[project]
dependencies = []

[project.optional-dependencies]
test = ["pytest>=8,<9"]
```

Modify only Workflow installation commands:

```text
python -m pip install -e ".[test]"
```

Required files:

```text
.github/workflows/ci.yml
.github/workflows/state-gate.yml
.github/workflows/decision-preflight.yml
```

Requirements:

- every workflow that invokes `python -m pytest` must first install the `test` extra;
- do not add a second pytest installation step;
- do not move test tools into runtime dependencies;
- do not add unrelated dependency caching or matrix expansion;
- preserve Python 3.13.

### 6.3 Control-plane mode detection

Allowed source changes:

```text
reverse_agent/project_gate.py
reverse_agent/control_plane/legacy_adapter.py
```

Add a CLI command:

```text
python -m reverse_agent.project_gate control-plane-mode --state-dir project_state
```

Output contract:

```text
transition
```

or:

```text
legacy
```

Requirements:

- stdout contains exactly one newline-terminated token;
- stderr may contain an error only on failure;
- exit code 0 only for a valid deterministic mode;
- `decision_contract.transition_kernel_required is true` selects `transition`;
- absent or explicit false selects `legacy`;
- malformed JSON, missing Decision metadata, invalid flag types, or unreadable authority files fail nonzero;
- no startup snapshot, baseline, closeout, state manifest, report-summary, final-check, seal, or remote-observation artifact is consulted;
- legacy behavior remains the fallback only for valid non-transition Decisions, not for malformed input.

Do not modify the transition validator's substantive security checks unless a focused failing test demonstrates a defect.

### 6.4 Workflow routing

#### CI

Only change the install command from base editable install to test-extra editable install.

Keep:

- checkout;
- Python setup;
- Import check;
- Focused tests;
- existing step order and names.

#### State Gate and Decision Preflight

In each workflow:

1. configure checkout with:

```yaml
with:
  fetch-depth: 0
```

2. install `.[test]`;
3. add one mode-detection step with stable ID, for example:

```yaml
- name: Detect control-plane mode
  id: control_plane
  shell: bash
  run: echo "mode=$(python -m reverse_agent.project_gate control-plane-mode --state-dir project_state)" >> "$GITHUB_OUTPUT"
```

4. for transition mode, add exactly these authority steps:

```text
python -m reverse_agent.project_gate transition-lint --state-dir project_state
python -m reverse_agent.project_gate transition-command-plan --state-dir project_state
python -m reverse_agent.project_gate transition-preflight --state-dir project_state
```

5. every legacy-only Gate step must receive an explicit condition equivalent to:

```yaml
if: steps.control_plane.outputs.mode == 'legacy'
```

6. every transition-only step must receive:

```yaml
if: steps.control_plane.outputs.mode == 'transition'
```

7. the focused pytest step runs after the selected authority path and is not duplicated;
8. artifact upload remains `if: always()`;
9. no Decision may run both transition and legacy authority chains;
10. no legacy command may be deleted or changed except adding its mode condition.

### 6.5 Transition command and Workflow contract verification

The immutable `workflow_contract` block in this Decision is the reviewed remote-command contract for this cutover round.

Tests must verify exact parity between the block and the three Workflow files for:

- install command;
- mode detection command;
- transition commands;
- focused test command;
- full-history requirements;
- legacy/transition conditions.

Do not scrape arbitrary Markdown command examples as executable authority. Read only the named JSON block.

The local generated command-plan remains the sole authority for commands Codex executes locally. GitHub Actions commands are reviewed CI-only commands governed by this immutable Workflow contract and the GitHub Workflow diff.

### 6.6 Tests

Allowed test modification:

```text
tests/test_project_gate.py
```

Required tests:

- mode CLI returns transition for explicit transition Decision;
- mode CLI returns legacy for valid legacy Decision;
- malformed contract fails closed;
- invalid non-boolean flag fails closed;
- mode output is exactly one token;
- legacy dispatch remains legacy;
- transition dispatch remains transition;
- CI installs `.[test]` and otherwise preserves structure;
- State Gate and Decision Preflight use fetch-depth 0;
- both governance workflows contain mode detection;
- transition-only steps have transition conditions;
- legacy-only steps have legacy conditions;
- no legacy command is deleted or changed;
- focused tests and evidence upload remain present;
- runtime dependencies remain empty;
- test extra remains bounded to pytest;
- existing transition fail-closed tests continue to pass.

### 6.7 Documentation

Allowed documentation changes:

```text
docs/architecture/control-plane-transition-kernel.md
docs/architecture/legacy-control-plane-boundary.md
docs/architecture/transition-command-authority.md
docs/architecture/workflow-transition-cutover.md
```

Document:

- mode detection contract;
- transition versus legacy Workflow paths;
- why pytest remains an optional test dependency;
- why CI installs the extra explicitly;
- fail-closed behavior for malformed Decisions;
- exact rollback: restore Workflow routing while leaving kernel modules intact;
- the next workstream boundary.

### 6.8 Current-round evidence

Allowed updates:

```text
project_state/decision_packet.md
project_state/pytest_result.txt
project_state/codex_execution_report.md
project_state/execution_report.md
project_state/gates/command_plan.json
project_state/gates/execution_log.json
project_state/gates/transition_preflight_result.json
project_state/gates/transition_command_plan_preview.json
```

Read-only legacy evidence:

```text
project_state/state_manifest.json
project_state/context/current_context_packet.json
project_state/gates/run_closeout_result.json
project_state/gates/final_gate_result.json
project_state/gates/final_evidence_seal.json
project_state/rounds/**
```

Do not regenerate or repair the legacy read-only evidence.

### 6.9 Publication boundary

After local validation:

- create one final validation commit on the existing PR #8 branch;
- push to the existing branch;
- do not create another PR;
- keep PR #8 Draft;
- freeze the branch after the push;
- wait for CI, State Gate, and Decision Preflight to complete on the exact final head;
- require all three workflow conclusions to be success;
- do not commit remote receipts;
- do not merge;
- do not begin the next workstream.

## 7. Tests

Initial commands:

```powershell
Set-Location F:\reverse-agent
Get-Location
Test-Path F:\reverse-agent
git rev-parse --show-toplevel
git status --short
git rev-parse HEAD
git fetch origin
git rev-parse origin/codex/control-plane-transition-kernel-v1
python -m reverse_agent.project_gate decision-lint --state-dir project_state
python -m reverse_agent.project_gate command-plan --state-dir project_state
python -m reverse_agent.project_gate command-plan --state-dir project_state --json
```

Do not execute legacy closeout/finalization commands:

```text
run-closeout
close-round
final-check
final-evidence-seal
state-manifest refresh
post-final-evidence-sync
report-summary repair
```

After implementation, execute only local commands present in the generated command-plan.

Preferred existing test surface when authorized:

```powershell
python -m pytest `
  tests/test_project_gate.py `
  tests/test_project_reports.py `
  tests/test_project_jobs.py `
  tests/test_post_final_evidence_sync.py `
  tests/test_decision_preflight.py `
  tests/test_project_state.py -q
```

Required Git checks when authorized:

```powershell
git diff --check
git status --short
```

Transition CLI checks may be executed directly only when authorized:

```powershell
python -m reverse_agent.project_gate control-plane-mode --state-dir project_state
python -m reverse_agent.project_gate transition-lint --state-dir project_state
python -m reverse_agent.project_gate transition-command-plan --state-dir project_state
python -m reverse_agent.project_gate transition-preflight --state-dir project_state
```

If a precise CLI command is absent from the local command-plan, pytest must exercise the equivalent Python API; do not manually add the command.

`pytest_result.txt` must preserve stdout, stderr, exit codes, timeouts, and intermediate failures for every executed required command. `execution_log.json` must preserve actual order.

Remote exact-head acceptance:

```text
CI:
  Install package = success
  Import check = success
  Focused tests = success
  workflow conclusion = success

State Gate:
  Install package = success
  Detect control-plane mode = success
  transition-lint = success
  transition-command-plan = success
  transition-preflight = success
  Focused gate tests = success
  legacy-only steps = skipped
  workflow conclusion = success

Decision Preflight:
  Install package = success
  Detect control-plane mode = success
  transition-lint = success
  transition-command-plan = success
  transition-preflight = success
  Focused preflight tests = success
  legacy-only steps = skipped
  workflow conclusion = success
```

All three workflows must refer to the same exact final Head SHA.

## 8. Stop Conditions

Stop and report `BLOCKED` without expanding scope if:

- PR #8 no longer starts at `783f3c68912d0fde46cd725d292f5fba1fcec916` and no new audit is supplied;
- PR #8 is closed, merged, non-Draft, or unexpectedly moved;
- this Decision is not committed before new implementation;
- the command-plan cannot be regenerated;
- local work requires manually modifying the command-plan;
- the transition kernel must be rebuilt rather than extended through the bounded routing surface;
- mode detection cannot be deterministic and fail closed;
- preserving legacy behavior requires deleting or semantically changing legacy commands;
- a workflow would execute both transition and legacy paths;
- `pytest` must be moved into runtime dependencies;
- an unrelated dependency or framework becomes necessary;
- completing the round requires modifying files outside the allowlist;
- transition validation accepts a wrong Decision, round, status, skill, mainline, branch, ancestry, command, scope, or forbidden operation;
- legacy Decision tests fail and the repair requires redesigning the legacy control plane;
- generated egg-info, build, dist, cache, or virtual-environment files enter the diff;
- tests fail and repair requires User Solve, Runner, frontend, solver, harness, sample, tool-adapter, or reverse-analysis changes;
- completing the round requires repairing legacy report-summary, final-check, closeout, state-manifest, seal, or remote-observation systems;
- direct-main, merge, rebase, force-push, destructive, or secret-changing operations are attempted;
- any exact-head workflow fails after the final validation commit;
- a post-remote-evidence commit would be required;
- the round attempts to start BMAD, LangGraph, Trust Layer, GitHub adapter, Runner, Web, User Solve, or reverse-solving work automatically.

On successful completion, stop after all three exact-head workflows are successful and PR #8 is ready for independent audit. Do not merge and do not begin the next workstream.
