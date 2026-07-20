# QUEUED DECISION CANDIDATE

```json queue_meta
{
  "schema_version": 1,
  "queue_status": "QUEUED_NOT_ACTIVE",
  "candidate_path": "project_state/queued_decisions/decision_20260720_selective_capability_integration_v2/decision_packet.md",
  "target_active_path": "project_state/decision_packet.md",
  "supersedes_candidate": "decision_20260720_selective_capability_integration_v1",
  "supersede_reason": "The v1 activation attempt correctly stopped before implementation. Its Current Evidence incorrectly claimed activation-time main lacked --allow-consumed even though the live CLI already exposed it, and its Tests required exact local packaging/pytest commands that the generated command-plan did not authorize. v2 treats the existing consumed mode as read-only capability, removes duplicate source implementation, reuses a command-plan-authorized standard pytest surface, and uses exact-head GitHub Install package evidence for editable-install acceptance.",
  "activation_policy": "Do not execute from this queued path or from PR #6. Fetch activation-time main, create a fresh execution branch, promote this packet to project_state/decision_packet.md, commit the Decision before implementation, generate and inspect the current full command-plan, and execute only commands present in that plan.",
  "estimated_effort_class": "medium_engineering_integration_round",
  "effort_target_note": "Designed for approximately four to seven hours of bounded Codex work. Stop after packaging metadata, two narrow Workflow compatibility hunks, standard authorized tests, and exact-head remote evidence. Do not pad the round or enter framework/Trust Layer work."
}
```

```json decision_meta
{
  "schema_version": 1,
  "decision_id": "decision_20260720_selective_capability_integration_v2",
  "round_id": "round_20260720_selective_capability_integration_v2",
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
  "follows_last_decision_id": "decision_20260720_selective_capability_integration_v1",
  "follows_last_round_id": "round_20260720_selective_capability_integration_v1",
  "previous_audit_outcome": "BLOCKED",
  "previous_attempt_remote_publication": false,
  "previous_attempt_implementation_changes": false,
  "workstream_id": "selective-capability-integration",
  "fresh_execution_branch_from_current_main_required": true,
  "queued_packet_must_be_promoted_before_execution": true,
  "decision_commit_must_precede_implementation": true,
  "command_plan_precedes_substantive_execution": true,
  "command_plan_is_command_authority": true,
  "decision_tests_must_not_override_command_plan": true,
  "execution_log_required": true,
  "pytest_result_required": true,
  "codex_execution_report_required": true,
  "remote_exact_head_evidence_required": true,
  "legacy_final_check_is_not_acceptance_authority": true,
  "legacy_closeout_is_not_acceptance_authority": true,
  "framework_installation_allowed": false,
  "workflow_mutation_allowed": true,
  "workflow_mutation_scope": [
    ".github/workflows/state-gate.yml",
    ".github/workflows/decision-preflight.yml"
  ],
  "product_source_mutation_allowed": false,
  "test_mutation_scope": [
    "tests/test_project_gate.py"
  ],
  "packaging_mutation_scope": [
    ".gitignore",
    "pyproject.toml"
  ],
  "runner_dispatch_allowed": false,
  "model_api_invocation_allowed": false,
  "external_reverse_tool_invocation_allowed": false,
  "destructive_operations_allowed": false,
  "merge_allowed": false,
  "direct_push_to_main_allowed": false,
  "force_push_allowed": false,
  "rebase_during_execution_allowed": false,
  "post_remote_evidence_commit_allowed": false,
  "scope_policy": "one_mainline_selective_packaging_and_workflow_integration_only"
}
```

# DECISION_PACKET

## 1. Goal

Create the first clean selective-integration baseline on a fresh branch from activation-time `main` without repeating the blocked v1 assumptions.

This round integrates only two independent capability groups:

1. minimal Python packaging metadata required by the repository's existing GitHub Actions `python -m pip install -e .` step;
2. the two already-reviewed Workflow compatibility hunks: full Git history checkout and explicit use of the already-existing `--allow-consumed` preflight mode.

Required outcomes:

1. add minimal packaging metadata so clean-checkout editable installation succeeds;
2. prevent editable-install and build outputs from becoming tracked files;
3. add packaging and Workflow contract assertions to the existing command-plan-covered `tests/test_project_gate.py` test surface;
4. verify, but do not reimplement or modify, the existing `--allow-consumed` CLI behavior;
5. preserve strict preflight as the default when the flag is absent;
6. change only State Gate and Decision Preflight checkout history/preflight command lines;
7. leave `.github/workflows/ci.yml` and all `reverse_agent/**` files unchanged;
8. execute only commands present in the generated current command-plan;
9. use remote exact-head `Install package` results as the editable-install execution evidence instead of requiring an unauthorized custom local pip command;
10. use the standard command-plan-authorized pytest command that already includes `tests/test_project_gate.py`, rather than requiring a new custom pytest command;
11. create one new Draft implementation PR and collect exact-head CI/job-step evidence;
12. stop before Trust Layer, BMAD, LangGraph, GitHub adapter, Web, User Solve, or runtime implementation.

Target sequence:

```text
fresh activation-time main
→ promote and commit v2 Decision
→ generate and inspect full command-plan
→ verify allow-consumed already exists
→ add minimal packaging metadata and ignores
→ add packaging/workflow assertions to existing test_project_gate surface
→ apply two narrow Workflow hunks
→ run only command-plan-authorized tests/checks
→ publish one exact final head
→ collect GitHub workflow/job-step evidence
→ stop
```

## 2. Current Evidence

- The v1 attempt created a fresh local branch, promoted the Decision, committed it, and generated a full command-plan, then correctly stopped before implementation or remote push.
- The v1 attempt is `BLOCKED`, not `REWORK_REQUIRED`: no packaging, source, test, or Workflow implementation was performed and no Draft implementation PR was created.
- The v1 Stop Condition identified two factual/contract defects:
  - the Decision claimed current main lacked `--allow-consumed`, while the live `project_gate.py` CLI already exposed that parameter;
  - the generated command-plan did not authorize two exact custom packaging/pytest commands required by v1.
- No v1 implementation result exists on GitHub. The local v1 Decision commit and branch are not remote execution authorities.
- The current GitHub `main` task packet is old sample-derived background data and cannot control this engineering round.
- The current GitHub `main` Decision/report/pytest artifacts still describe older governance rounds; they are historical compatibility inputs until this queued packet is promoted on a fresh branch.
- PR #5 remains frozen migration evidence at exact head `6a2867467c90cf37929787be3ba6061fcbb81312`.
- PR #7 remains read-only transition-planning evidence at exact head `7cd75fcaa60cb6ecd7730c98bc5bf693716e45ec`.
- PR #6 is plan storage only. It is not execution authority and must not be used as the implementation branch.
- Existing CI, State Gate, and Decision Preflight workflows run `python -m pip install -e .` before imports/tests.
- Activation-time main has no committed `pyproject.toml`, so clean-checkout workflow installation cannot succeed until packaging metadata is added.
- Current `.gitignore` lacks editable-install/build output exclusions such as `*.egg-info/`, `*.egg-link`, `build/`, and `dist/`.
- Live local evidence shows current `project_gate.py` already supports `--allow-consumed`. This round must confirm that fact against activation-time main and treat the source as read-only.
- The full command-plan generated during v1 did not authorize bespoke local `pip install -e .` and bespoke packaging pytest commands. v2 does not require those exact local commands.
- The existing standard focused test surface includes `tests/test_project_gate.py`; v2 places packaging/Workflow assertions there so the existing command-plan-authorized pytest command exercises them.
- Exact-head GitHub job-step evidence is the authoritative proof that editable installation succeeds in a clean checkout.
- Strict local preflight remains the default guard. Explicit consumed mode is a CI validation mode, not a universal bypass.
- `task_packet.json` is background only. After promotion, `project_state/decision_packet.md` is the sole task authority.
- `project_state/gates/command_plan.json` is the sole command authority. A command listed in this Decision but absent from the generated plan must not be executed.
- Existing command-plan and execution-log mechanisms are temporary compatibility foundations for this round; they must not be expanded or repaired.
- Legacy final-check, report-summary, run-closeout, seal, state-manifest, context-sync, and remote-observation mirrors are not acceptance authorities for this integration round.
- This round does not install or emulate BMAD, LangGraph, Microsoft Agent Framework, MetaGPT, ChatDev, a database, queue, scheduler, model API, reverse tool, debugger, emulator, or sandbox.
- Full `solve_reports/**`, `PROJECT_PROGRESS_LOG.txt`, and unrelated historical rounds remain excluded.
- This round reuses existing capabilities and does not rebuild consumed preflight, command-plan, execution-log, report-summary, closeout, policy-lint, prompt-consistency, Runner, User Solve, or CI from scratch.

## 3. Do Not Do

Do not:

- execute this packet while it remains under `project_state/queued_decisions/**`;
- execute from PR #6 or its branch;
- reuse the local v1 branch or local v1 Decision commit as authority;
- execute on PR #5 or PR #7 branches;
- start from anything other than freshly fetched activation-time `origin/main`;
- modify, merge, close, rebase, force-push, or mark PR #5 or PR #7 ready for review;
- copy PR #5 or PR #7 wholesale;
- copy their round archives, reports, seals, state manifests, remote observations, or mutable report aliases;
- modify `reverse_agent/project_gate.py` or any file under `reverse_agent/**`;
- reimplement, refactor, rename, broaden, or weaken `--allow-consumed`;
- make consumed mode the default;
- remove or weaken `decision_not_consumed_by_report` or any other preflight check;
- create `tests/test_packaging_metadata.py`; packaging assertions belong in the existing command-plan-covered `tests/test_project_gate.py` surface for this round;
- require or execute a bespoke local `python -m pip install -e .` command when it is absent from the generated command-plan;
- require or execute a bespoke pytest command when it is absent from the generated command-plan;
- manually add commands to `command_plan.json`;
- edit, fabricate, or post-hoc rewrite command-plan or execution-log evidence;
- modify `.github/workflows/ci.yml`;
- modify any State Gate or Decision Preflight line other than checkout history and the project-gate preflight command;
- add, remove, reorder, or rename Workflow steps;
- add `requests`, BMAD, LangGraph, Agent Framework, Web frameworks, database clients, or speculative dependencies;
- commit `*.egg-info`, `*.egg-link`, `build/`, `dist/`, caches, or virtual environments;
- modify roadmap/workstreams in this round;
- modify User Solve, frontend, solver, harness, sample, tool-adapter, Trust Layer, GitHub adapter, job runtime, Runner, or orchestration code;
- run reverse tools, runtime probes, unknown binaries, debuggers, emulators, hooks, or model APIs;
- repair legacy report-summary, final-check, closeout, seal, state-manifest, context, or remote-attestation systems;
- require legacy closeout/final-check success as acceptance evidence;
- create another legacy repair round because later old State Gate steps fail;
- execute any command absent from the generated command-plan;
- use `git add -A`;
- push directly to `main`;
- merge, tag, rebase during execution, force-push, amend published history, delete branches, or alter secrets;
- add a post-remote-evidence commit;
- continue after a Stop Condition;
- begin the next workstream automatically.

## 4. Files To Inspect

Required authority and current evidence after activation:

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
.codex-skills/registry.json
```

Required activation-time implementation files:

```text
.gitignore
.github/workflows/ci.yml
.github/workflows/state-gate.yml
.github/workflows/decision-preflight.yml
reverse_agent/project_gate.py
tests/test_project_gate.py
```

Required read-only evidence:

```text
PR #5 exact head 6a2867467c90cf37929787be3ba6061fcbb81312:
  .gitignore
  pyproject.toml
  tests/test_packaging_metadata.py
  .github/workflows/state-gate.yml
  .github/workflows/decision-preflight.yml

PR #7 exact head 7cd75fcaa60cb6ecd7730c98bc5bf693716e45ec:
  project_state/gates/transition_baseline_recommendation.json
  project_state/gates/selective_migration_manifest.json
  project_state/context/framework_transition_packet.json
```

Targeted inspection only:

```text
confirm activation-time main project_gate preflight parser exposes --allow-consumed
confirm strict mode remains default
confirm existing tests cover consumed identity/status fail-closed behavior
confirm current reverse_agent imports do not require requests or a framework dependency
confirm all three GitHub workflows use python -m pip install -e .
confirm the standard generated pytest command includes tests/test_project_gate.py
confirm State Gate and Decision Preflight current checkout/preflight text
```

Do not inspect unrelated trees after sufficient evidence exists.

## 5. Required Audit

The final report must answer each item separately with exact file/artifact path, observed value, and conclusion:

1. Was v2 promoted to `project_state/decision_packet.md` before implementation?
2. Was the execution branch freshly created from activation-time `origin/main`?
3. Were the v1 local branch and unpushed Decision excluded from authority?
4. Does active Decision metadata match v2 exactly?
5. Is `reverse-agent-iteration@v2` active?
6. Was the full command-plan generated before implementation?
7. Were all executed commands present in that plan?
8. Did PR #5 remain frozen at its audited SHA?
9. Did PR #7 remain frozen at its audited SHA?
10. Did activation-time main already expose `--allow-consumed`?
11. Did all `reverse_agent/**` files remain byte-for-byte unchanged?
12. Does strict preflight remain the default when no flag is provided?
13. Were existing consumed-mode fail-closed tests preserved and executed?
14. Were only the four specified build/install ignore entries added to `.gitignore`?
15. Does `pyproject.toml use a minimal setuptools build backend?
16. Does package discovery include `reverse_agent*` and exclude tests, docs, and project state?
17. Is every declared dependency justified by the current GitHub workflow execution model?
18. Was no `requests` or framework dependency added?
19. Are packaging assertions implemented in `tests/test_project_gate.py` rather than a new custom test file?
20. Did the executed command-plan-authorized standard pytest command include and pass `tests/test_project_gate.py`?
21. Was no unapproved bespoke local install or pytest command executed?
22. Does State Gate checkout use `fetch-depth: 0`?
23. Does Decision Preflight checkout use `fetch-depth: 0`?
24. Do both Workflows explicitly call preflight with `--allow-consumed`?
25. Is `.github/workflows/ci.yml` byte-for-byte unchanged?
26. Were no other Workflow lines or step order changed?
27. Does final Git diff contain only allowed packaging, test, Workflow, Decision, report, and execution-evidence paths?
28. Are build outputs and egg-info absent from the committed diff?
29. Does `pytest_result.txt` contain real command blocks for all executed required local commands?
30. Does `execution_log.json` match those executed commands and exit codes?
31. Did `git diff --check` pass if authorized by the plan?
32. Was one new Draft implementation PR created from the fresh branch?
33. On its exact final head, did CI `Install package` succeed?
34. On its exact final head, did CI complete successfully?
35. On its exact final head, did State Gate `Install package` succeed?
36. On its exact final head, did State Gate `Project gate preflight` succeed?
37. On its exact final head, did Decision Preflight `Install package` succeed?
38. On its exact final head, did Decision Preflight `Project gate preflight` succeed?
39. If later legacy steps failed, were they recorded as migration debt without opening a legacy repair round?
40. Was no post-evidence commit added?
41. Did the final report avoid claiming framework, Trust Layer, GitHub adapter, Runner, or User Solve implementation?
42. Did execution stop before the next workstream?
43. Is the next action the `trust-layer-schema-foundation` Decision/planning step, not open-ended cleanup?

## 6. Implementation Scope

### 6.1 Activation and authority

On a fresh branch from activation-time main:

1. promote this packet to `project_state/decision_packet.md`;
2. commit the Decision before implementation;
3. confirm its commit is an ancestor of all later commits;
4. generate and inspect the full current command-plan;
5. do not edit or fabricate the plan;
6. verify the plan contains an existing standard pytest command that runs `tests/test_project_gate.py`;
7. if no such authorized pytest command exists, stop `BLOCKED` before implementation;
8. record activation main SHA, branch, Decision commit SHA, PR #5 evidence SHA, and PR #7 evidence SHA.

### 6.2 Existing consumed-mode verification

`reverse_agent/project_gate.py` and all `reverse_agent/**` files are read-only.

Before implementation, verify:

- preflight CLI already accepts `--allow-consumed`;
- strict mode remains default;
- existing focused tests cover valid consumed mode and invalid identity/status cases sufficiently for this integration boundary.

If the CLI does not exist on activation-time main, stop `BLOCKED`. Do not implement it in this round.

### 6.3 Packaging baseline

Allowed packaging changes:

```text
.gitignore
pyproject.toml
```

`.gitignore` may add only:

```text
*.egg-info/
*.egg-link
build/
dist/
```

`pyproject.toml` must:

- use setuptools as the build backend;
- define project name `reverse-agent` and a bounded version;
- set the tested supported Python baseline;
- include `reverse_agent*` packages;
- exclude tests, `project_state*`, and `docs*` from installed packages;
- declare only dependencies required by existing clean-checkout workflow execution;
- not include `requests` or any framework/runtime dependency;
- document any temporary pytest-as-install dependency as CI compatibility debt if existing workflows require it after only `pip install -e .`.

### 6.4 Existing-test-surface integration

Allowed test change:

```text
tests/test_project_gate.py
```

Add focused assertions that:

- parse the actual `pyproject.toml` with `tomllib`;
- verify build backend, project identity, Python baseline, package inclusion/exclusion, and bounded dependencies;
- reject speculative dependencies;
- verify `.gitignore` contains the four exact ignore entries;
- verify State Gate and Decision Preflight contain only the required checkout/preflight compatibility text;
- verify `.github/workflows/ci.yml` remains unchanged relative to activation-time main, using a deterministic fixture or captured baseline digest if practical without new generated state machinery;
- retain existing strict/consumed preflight tests unchanged unless a test-only assertion is necessary.

Do not create a new packaging test file. Run these assertions through the standard command-plan-authorized pytest command that already includes `tests/test_project_gate.py`.

### 6.5 Workflow compatibility

Allowed Workflow changes:

```text
.github/workflows/state-gate.yml
.github/workflows/decision-preflight.yml
```

In each file only:

1. add under `actions/checkout@v4`:

```yaml
with:
  fetch-depth: 0
```

2. change the existing project-gate preflight command to:

```text
python -m reverse_agent.project_gate preflight --state-dir project_state --allow-consumed
```

No other Workflow text may change. `.github/workflows/ci.yml` remains read-only.

### 6.6 Current-round evidence

Allowed current-round evidence updates:

```text
project_state/decision_packet.md
project_state/pytest_result.txt
project_state/codex_execution_report.md
project_state/execution_report.md
project_state/gates/command_plan.json
project_state/gates/execution_log.json
```

Do not refresh, repair, or regenerate legacy state manifests, context packets, report summaries, closeout artifacts, round archives, seals, or remote mirrors.

The report must derive `files_changed` from final Git diff and separately note ignored local build outputs if any.

### 6.7 Publication and remote evidence

After command-plan-authorized local validation:

- create a new Draft PR to `main` from the fresh execution branch;
- do not reuse PR #5, #6, or #7;
- publish one final integration head;
- stop branch mutation when remote evidence begins;
- inspect exact-head workflow and job-step results externally;
- do not commit remote receipts.

Acceptance is based on the exact Git head and GitHub workflow/job-step facts, not legacy closeout artifacts.

## 7. Tests

Command authority rule:

> The generated `project_state/gates/command_plan.json` is authoritative. This section defines required coverage and expected evidence, but does not authorize a command absent from the plan.

Required local evidence categories:

1. standard startup/location/Git status checks already present in the full plan;
2. Decision lint and full command-plan generation already present in the full plan;
3. the standard focused pytest command already present in the full plan and including `tests/test_project_gate.py`;
4. plan-authorized Git diff/status validation;
5. no bespoke local editable-install command;
6. no bespoke pytest command added solely for this Decision.

Before implementation, Codex must list the exact plan commands that will satisfy categories 1–4. If any category has no authorized command, stop `BLOCKED`.

`pytest_result.txt` must preserve the actual stdout, stderr, and exit code for every executed required command. `execution_log.json` must cover the same execution chronology.

Remote exact-head requirements:

```text
CI:
  Install package = success
  Import check = success
  Focused tests = success
  workflow conclusion = success

State Gate:
  Install package = success
  Project gate preflight = success
  later legacy-step failures may be nonblocking migration debt

Decision Preflight:
  Install package = success
  Project gate preflight = success
  later legacy-step failures may be nonblocking migration debt
```

Legacy `report-summary`, `final-check`, `run-closeout`, `close-round`, state-manifest refresh, final seal, and remote observation mirror generation are not required tests and are not acceptance authorities.

## 8. Stop Conditions

Stop and report `BLOCKED` without expanding scope if:

- activation-time main cannot be fetched or a fresh branch cannot be created;
- the promoted v2 Decision is not the sole active task authority;
- `reverse-agent-iteration@v2` is inactive;
- PR #5 or PR #7 no longer matches the audited SHA and no newer independent audit exists;
- the full command-plan is unavailable or invalid;
- the plan does not contain a standard authorized pytest command that includes `tests/test_project_gate.py`;
- satisfying required local evidence would require any command absent from the plan;
- activation-time main does not already expose `--allow-consumed`;
- consumed-mode verification requires modifying `reverse_agent/**`;
- packaging requires a dependency not justified by current clean-checkout workflow execution;
- clean packaging requires modifying files outside `.gitignore` and `pyproject.toml`;
- test coverage requires a new test file or modifying a test outside `tests/test_project_gate.py`;
- `.github/workflows/ci.yml` would need modification;
- either allowed Workflow requires changes beyond `fetch-depth: 0` and explicit consumed mode;
- any other Workflow step changes;
- tests fail and repair requires leaving the allowlist;
- a build output or egg-info file enters the committed diff;
- execution evidence cannot truthfully record every executed required command;
- CI `Install package`, Import check, Focused tests, or overall workflow fails on the exact head;
- State Gate or Decision Preflight fails at `Install package` or `Project gate preflight` on the exact head;
- the round begins repairing downstream legacy report-summary, closeout, manifest, seal, or remote-attestation behavior;
- a framework, Trust Layer, GitHub adapter, Runner, Web, User Solve, database, queue, scheduler, reverse tool, or model API becomes necessary;
- a post-remote-evidence commit would be required;
- the round attempts to begin the next workstream automatically.

On successful completion, stop with the new Draft implementation PR ready for independent audit. Do not merge and do not begin Trust Layer work.
