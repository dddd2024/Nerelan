# QUEUED DECISION CANDIDATE

```json queue_meta
{
  "schema_version": 1,
  "queue_status": "QUEUED_NOT_ACTIVE",
  "candidate_path": "project_state/queued_decisions/decision_20260720_selective_capability_integration_v1/decision_packet.md",
  "target_active_path": "project_state/decision_packet.md",
  "supersedes_candidate": "decision_20260720_legacy_control_plane_transition_disposition_v1",
  "activation_policy": "Do not execute from this queued path or from PR #6. Before execution, fetch current main, create a fresh execution branch from current main, promote this packet to project_state/decision_packet.md, commit the Decision before implementation, generate and review the current command-plan, and confirm PR #5 and PR #7 remain read-only evidence.",
  "estimated_effort_class": "medium_engineering_integration_round",
  "effort_target_note": "Designed for approximately four to eight hours of bounded Codex work. Stop when packaging, narrow preflight compatibility, focused tests, and exact-head remote evidence are complete. Do not expand into framework installation or legacy closeout repair."
}
```

```json decision_meta
{
  "schema_version": 1,
  "decision_id": "decision_20260720_selective_capability_integration_v1",
  "round_id": "round_20260720_selective_capability_integration_v1",
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
  "follows_last_decision_id": "decision_20260720_legacy_control_plane_transition_disposition_v1",
  "follows_last_round_id": "round_20260720_legacy_control_plane_transition_disposition_v1",
  "previous_audit_outcome": "REWORK_REQUIRED",
  "transition_progression_authorized_by_user": true,
  "previous_round_artifacts_are_planning_input_only": true,
  "legacy_disposition_repair_prohibited": true,
  "workstream_id": "selective-capability-integration",
  "fresh_execution_branch_from_current_main_required": true,
  "queued_packet_must_be_promoted_before_execution": true,
  "decision_commit_must_precede_implementation": true,
  "command_plan_precedes_substantive_execution": true,
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
  "product_source_mutation_allowed": true,
  "product_source_mutation_scope": [
    "reverse_agent/project_gate.py"
  ],
  "test_mutation_scope": [
    "tests/test_packaging_metadata.py",
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
  "scope_policy": "one_mainline_selective_integration_only"
}
```

# DECISION_PACKET

## 1. Goal

Create the first clean selective-integration baseline on a fresh branch from activation-time `main`.

This round integrates only the minimum independent capabilities required to make the repository installable in a clean GitHub Actions checkout and to validate the consumed-Decision preflight compatibility boundary without importing PR #5 as a whole.

Required outcomes:

1. add minimal packaging metadata so `python -m pip install -e .` succeeds from a clean checkout;
2. add packaging/build ignore entries so editable-install metadata and build outputs cannot become tracked changes;
3. add focused packaging tests adapted to the current integration Decision rather than retaining historical v6 wording;
4. add the smallest possible `--allow-consumed` compatibility implementation to `reverse_agent.project_gate` because activation-time `main` does not expose that option;
5. keep strict local preflight behavior as the default;
6. make `--allow-consumed` relax only the `decision_not_consumed_by_report` check for a valid current Decision/report identity;
7. apply only two reviewed Workflow compatibility changes to State Gate and Decision Preflight:
   - full-history checkout with `fetch-depth: 0`;
   - explicit `--allow-consumed` on the Workflow preflight command;
8. leave `.github/workflows/ci.yml` unchanged;
9. verify installation, imports, packaging metadata, strict/consumed preflight behavior, and exact Workflow text;
10. publish one Draft PR from the fresh execution branch and collect exact-head GitHub evidence;
11. stop after this integration boundary; do not begin Trust Layer, BMAD, LangGraph, GitHub adapter, Web, User Solve, or runtime work.

The target sequence is:

```text
fresh current main
→ active Decision commit
→ current command-plan
→ minimal packaging metadata
→ focused packaging tests
→ minimal allow-consumed compatibility
→ two narrow Workflow hunks
→ local tests and clean install
→ exact diff audit
→ Draft PR
→ exact-head CI evidence
→ stop
```

This round does not accept PR #5 or PR #7 as merge units. They remain read-only evidence sources.

## 2. Current Evidence

- The prior transition-disposition round on PR #7 produced useful planning artifacts but is formally `REWORK_REQUIRED` because its execution log omitted required commands, its baseline was captured after implementation files existed, its state manifest remained stale, its final-check failed, and its report status was `FAILED`.
- The prior round nevertheless established a usable planning conclusion: select `SELECTIVE_INTEGRATION_BASELINE` rather than current-main-only or PR-#5-as-a-whole.
- PR #5 remains frozen migration evidence at exact head `6a2867467c90cf37929787be3ba6061fcbb81312`.
- PR #7 remains read-only transition evidence at exact head `7cd75fcaa60cb6ecd7730c98bc5bf693716e45ec`.
- Activation-time `main` must be fetched again. The prior planning base `5884cf2abb37945652ef166cf0e78fa24593b0d5` is historical context, not an assumption that current main has not advanced.
- Current `main` has no `pyproject.toml`, while CI, State Gate, and Decision Preflight all run `python -m pip install -e .`; this causes clean-checkout installation failure before tests.
- PR #5 contains a small `pyproject.toml`, focused packaging tests, and editable-install ignore entries. These are independent from its legacy round archive and report/closeout chain.
- Current main `.gitignore` lacks `*.egg-info/`, `*.egg-link`, `build/`, and `dist/` ignores.
- Current main State Gate and Decision Preflight use shallow default checkout and strict preflight without `--allow-consumed`.
- PR #5 demonstrates `fetch-depth: 0` plus explicit `--allow-consumed` in those two Workflows.
- Current main `reverse_agent/project_gate.py` does not expose `--allow-consumed`; therefore changing only Workflow YAML would create an invalid command. The prior transition plan omitted this dependency.
- The minimal source change must not transplant PR #5 `project_gate.py` wholesale. It must implement only the consumed-Decision compatibility surface and focused tests.
- Strict preflight remains the default local execution guard. The new flag is a Workflow validation mode, not a universal bypass.
- `task_packet.json` remains background-only. The active promoted `project_state/decision_packet.md` controls the round.
- `current_state.json`, `current_context_packet.json`, and old state manifests may be stale and must not override live Git and current Decision evidence.
- Workstream registry entries are planning data, not command authority.
- Existing command-plan and execution-log foundations are compatibility mechanisms for this round. They must not be expanded or repaired beyond what is necessary to record the actual commands.
- No BMAD, LangGraph, Microsoft Agent Framework, MetaGPT, ChatDev, database, queue, scheduler, model API, reverse tool, debugger, emulator, or unknown binary is needed or allowed.
- No full `solve_reports/**` or historical round scan is required.
- Legacy final-check, run-closeout, final seal, and remote-attestation mirrors are not acceptance authorities for this integration round and must not trigger a new repair Decision.
- GitHub exact-head workflow/job results are the remote execution facts for this round.
- This round does not duplicate a framework capability. It selectively integrates packaging and a narrow compatibility guard discovered in existing work.

## 3. Do Not Do

Do not:

- execute this packet from `project_state/queued_decisions/**`;
- execute on PR #6, PR #7, PR #5, or their branches;
- start from PR #5 or PR #7 rather than fresh activation-time `main`;
- modify, merge, close, rebase, force-push, or mark PR #5 or PR #7 ready for review;
- copy PR #5 wholesale;
- copy any PR #5 `project_state/rounds/**`, reports, seals, remote observations, mutable aliases, or state manifests;
- copy `reverse_agent/project_gate.py` wholesale from PR #5;
- add any source behavior unrelated to the `--allow-consumed` compatibility boundary;
- make `--allow-consumed` the default;
- remove `decision_not_consumed_by_report`;
- allow `--allow-consumed` to bypass wrong Decision ID, wrong round ID, wrong report identity, failed report, non-APPROVED Decision, inactive skill, invalid mainline, forbidden scope, dirty startup, or other preflight checks;
- modify `.github/workflows/ci.yml`;
- modify any State Gate or Decision Preflight line other than checkout history and the project-gate preflight command;
- add, remove, reorder, or rename other Workflow steps;
- add BMAD, LangGraph, Microsoft Agent Framework, MetaGPT, ChatDev, `requests`, database clients, Web frameworks, or speculative dependencies;
- place unrelated test or development tools into runtime dependencies without an explicit compatibility rationale;
- commit `*.egg-info`, `build/`, `dist/`, caches, or virtual environments;
- modify User Solve, frontend, solver, harness, sample, tool-adapter, Trust Layer, GitHub adapter, job runtime, Runner, or orchestration code;
- run reverse tools, runtime probes, unknown binaries, debuggers, emulators, hooks, or model APIs;
- modify roadmap/workstreams in this round;
- repair legacy report-summary, execution-log synthesis, final-check, closeout, seal, state-manifest, context, or remote-attestation systems;
- require a legacy final-check or closeout pass as acceptance evidence;
- create another legacy cleanup/rework round if downstream old State Gate steps fail after the integration-specific steps pass;
- use `git add -A`;
- push directly to `main`;
- merge, tag, rebase during execution, force-push, amend published history, delete branches, or alter secrets;
- commit any remote workflow receipt after the final integration commit;
- execute a command absent from the current command-plan;
- continue after a Stop Condition.

## 4. Files To Inspect

Required current authority and live state after activation:

```text
project_state/decision_packet.md
project_state/task_packet.json
project_state/current_state.json
project_state/artifact_index.json
project_state/negative_results.json
project_state/pytest_result.txt
project_state/codex_execution_report.md
project_state/gates/command_plan.json
project_state/gates/execution_log.json
.codex-skills/registry.json
```

Required activation-time source files:

```text
.gitignore
.github/workflows/ci.yml
.github/workflows/state-gate.yml
.github/workflows/decision-preflight.yml
reverse_agent/project_gate.py
tests/test_project_gate.py
```

Required read-only source evidence:

```text
PR #5 exact head 6a2867467c90cf37929787be3ba6061fcbb81312:
  .gitignore
  pyproject.toml
  tests/test_packaging_metadata.py
  .github/workflows/state-gate.yml
  .github/workflows/decision-preflight.yml
  reverse_agent/project_gate.py
  tests/test_project_gate.py

PR #7 exact head 7cd75fcaa60cb6ecd7730c98bc5bf693716e45ec:
  project_state/gates/transition_baseline_recommendation.json
  project_state/gates/selective_migration_manifest.json
  project_state/context/framework_transition_packet.json
  docs/architecture/legacy-control-plane-disposition.md
```

Targeted code checks:

```text
search current main for allow-consumed
search current main reverse_agent/** for external imports
confirm no current reverse_agent/** import requires requests
confirm project_gate CLI parser and preflight call sites
confirm existing consumed-report status fields and report identity checks
confirm Workflow install and preflight commands
```

Do not inspect unrelated source trees after the integration dependency is understood.

## 5. Required Audit

The final report must answer every item separately with exact file/artifact path, observed value, and conclusion:

1. Was this queued packet promoted to `project_state/decision_packet.md` before implementation?
2. Was execution started from a fresh branch whose base is activation-time `main`?
3. Does the active Decision ID, round ID, mainline, and skill exactly match this packet?
4. Was the current command-plan generated before packaging, source, test, or Workflow changes?
5. Did PR #5 remain frozen at `6a2867467c90cf37929787be3ba6061fcbb81312`?
6. Did PR #7 remain frozen at `7cd75fcaa60cb6ecd7730c98bc5bf693716e45ec`?
7. Does the final Git diff contain only the explicitly allowed implementation, test, Workflow, Decision, and evidence paths?
8. Were only editable-install/build ignore entries added to `.gitignore`?
9. Does `pyproject.toml` provide a minimal setuptools build system and package discovery for `reverse_agent*`?
10. Does packaging exclude tests, docs, and project-state data from the installed package?
11. Is every dependency justified by current code or current CI execution needs?
12. Was no unused `requests` or framework dependency copied from PR #5?
13. Does `python -m pip install -e .` succeed in a clean environment or clean checkout?
14. Do required reverse-agent modules import successfully after editable installation?
15. Does `tests/test_packaging_metadata.py` describe the current integration contract rather than historical v6 requirements?
16. Does strict preflight without `--allow-consumed` retain its existing default semantics?
17. Does strict preflight still block a Decision already consumed by its current successful report?
18. Does `--allow-consumed` relax only `decision_not_consumed_by_report` for a valid current Decision/report identity?
19. Does `--allow-consumed` still fail for wrong Decision ID, wrong round ID, wrong report ID, failed report, non-APPROVED Decision, inactive skill, invalid mainline, invalid scope, and dirty startup conditions?
20. Was the source change to `reverse_agent/project_gate.py` limited to the new parameter/CLI plumbing and narrow consumed-check semantics?
21. Were focused tests added to `tests/test_project_gate.py` for strict and allow-consumed modes?
22. Does State Gate checkout use `fetch-depth: 0`?
23. Does Decision Preflight checkout use `fetch-depth: 0`?
24. Do both Workflows call preflight with explicit `--allow-consumed`?
25. Is `.github/workflows/ci.yml` byte-for-byte unchanged?
26. Were no Workflow steps added, removed, reordered, or renamed beyond the two allowed hunks?
27. Does the command-plan authorize every executed local command and both CI-only Workflow commands?
28. Does `pytest_result.txt` contain actual stdout, stderr, and exit codes for every required local command rather than only a summary list?
29. Does `execution_log.json` cover every required command with the correct exit code?
30. Did focused packaging/project-gate tests pass?
31. Did `git diff --check` pass?
32. Are `*.egg-info`, `build/`, and `dist/` absent from the committed diff?
33. On the exact final head, did CI complete successfully?
34. On the exact final head, did State Gate complete `Install package` and `Project gate preflight` successfully?
35. On the exact final head, did Decision Preflight complete `Install package` and `Project gate preflight` successfully?
36. If later legacy State Gate/Decision Preflight steps failed, were those failures recorded without creating a legacy repair round?
37. Was no post-remote-evidence commit added after the exact head was published?
38. Did the final report avoid claiming that BMAD, LangGraph, Trust Layer, or GitHub adapter integration was implemented?
39. Did the round stop before the `trust-layer-schema-foundation` workstream?
40. Is the next action the already registered `trust-layer-schema-foundation` planning/Decision step rather than an open-ended cleanup instruction?

## 6. Implementation Scope

### 6.1 Activation and authority

On a fresh branch from activation-time `main`:

1. promote this packet to `project_state/decision_packet.md`;
2. commit the Decision before implementation;
3. confirm the Decision commit is an ancestor of all later implementation commits;
4. generate and inspect `project_state/gates/command_plan.json`;
5. do not manually fabricate or edit the command-plan;
6. record the branch name, activation-time main SHA, Decision commit SHA, PR #5 evidence SHA, and PR #7 evidence SHA in the final report.

### 6.2 Packaging baseline

Allowed packaging changes:

```text
.gitignore
pyproject.toml
tests/test_packaging_metadata.py
```

Requirements:

- add only:
  - `*.egg-info/`
  - `*.egg-link`
  - `build/`
  - `dist/`
- use setuptools as the build backend;
- define package name `reverse-agent` and a bounded version;
- require Python 3.13 or the actual supported current baseline confirmed by tests;
- include `reverse_agent*` packages;
- exclude tests, project_state, and docs from package discovery;
- keep dependency metadata minimal;
- do not copy the PR #5 optional `requests` group unless a current source import proves it necessary;
- adapt test prose and assertions to this integration Decision;
- ensure editable installation does not create tracked changes.

### 6.3 Minimal consumed-Decision compatibility

Allowed source/test changes:

```text
reverse_agent/project_gate.py
tests/test_project_gate.py
```

The implementation must:

- add an `allow_consumed: bool = False` parameter or equivalent explicit mode to preflight;
- preserve strict behavior when the parameter is false;
- expose `--allow-consumed` only on the preflight CLI;
- when true, permit the consumed-report condition only if the report belongs to the current Decision and current round and otherwise satisfies existing report/status checks;
- leave every other preflight check unchanged;
- avoid importing unrelated PR #5 control-plane code;
- avoid adding new state mirrors, remote observations, locks, seals, or report machinery.

Focused tests must prove strict default, valid consumed mode, and fail-closed behavior for invalid identities and unrelated preflight failures.

### 6.4 Workflow compatibility

Allowed Workflow changes:

```text
.github/workflows/state-gate.yml
.github/workflows/decision-preflight.yml
```

In each file only:

1. add:

```yaml
with:
  fetch-depth: 0
```

under the existing `actions/checkout@v4` step;

2. change the existing project-gate preflight command to:

```text
python -m reverse_agent.project_gate preflight --state-dir project_state --allow-consumed
```

No other Workflow text may change. `.github/workflows/ci.yml` is read-only.

### 6.5 Evidence files

Allowed current-round evidence updates:

```text
project_state/decision_packet.md
project_state/pytest_result.txt
project_state/codex_execution_report.md
project_state/execution_report.md
project_state/gates/command_plan.json
project_state/gates/execution_log.json
```

Do not refresh or repair legacy state manifests, context packets, closeout artifacts, round archives, final seals, remote mirrors, or report-summary chains in this round.

The final report must derive `files_changed` from the final Git diff and must list untracked ignored build outputs separately if they exist locally.

### 6.6 Publication boundary

After local validation:

- create a Draft PR from the new execution branch to `main`;
- do not reuse PR #5, #6, or #7;
- push one final integration head;
- do not mutate the branch after remote evidence collection begins;
- inspect exact-head CI, State Gate, and Decision Preflight step results externally;
- do not commit remote receipts.

## 7. Tests

The command-plan must include and execution evidence must record the real output of the following local commands:

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
python -m pip install -e .
python -c "import reverse_agent.project_gate; import reverse_agent.project_state; import reverse_agent.post_final_evidence_sync; import reverse_agent.decision_preflight"
python -m pytest tests/test_packaging_metadata.py tests/test_project_gate.py -q
python -m pytest tests/test_packaging_metadata.py tests/test_project_gate.py tests/test_project_reports.py tests/test_decision_preflight.py -q
python -m reverse_agent.project_gate preflight --state-dir project_state
git diff -- .gitignore pyproject.toml tests/test_packaging_metadata.py reverse_agent/project_gate.py tests/test_project_gate.py .github/workflows/state-gate.yml .github/workflows/decision-preflight.yml
git diff --check
git status --short
```

Testing requirements:

- `pytest_result.txt` must contain a command block for every required command with stdout, stderr, and exit code;
- the focused tests must include valid and invalid consumed-report identity fixtures;
- the tests must confirm strict mode remains default;
- packaging tests must inspect the actual `pyproject.toml`;
- Workflow tests or deterministic assertions must verify exactly two permitted hunks per Workflow;
- no full legacy 1500-test suite is required unless a changed file directly demands it;
- legacy `final-check`, `run-closeout`, `close-round`, final seal, report-summary, and state-manifest refresh are not required tests for this round.

Remote evidence requirements for the exact final head:

```text
CI:
  workflow conclusion = success

State Gate:
  Install package step = success
  Project gate preflight step = success
  later legacy-step failures may be recorded as nonblocking migration debt

Decision Preflight:
  Install package step = success
  Project gate preflight step = success
  later legacy-step failures may be recorded as nonblocking migration debt
```

## 8. Stop Conditions

Stop and report `BLOCKED` without expanding scope if:

- PR #5 no longer matches `6a2867467c90cf37929787be3ba6061fcbb81312` and no new audit is supplied;
- PR #7 no longer matches `7cd75fcaa60cb6ecd7730c98bc5bf693716e45ec` and no new audit is supplied;
- activation-time `main` cannot be fetched or a fresh branch cannot be created;
- the promoted Decision is not the sole active task authority;
- `reverse-agent-iteration@v2` is inactive;
- packaging requires a new external runtime dependency not already justified by current source or CI;
- clean editable installation cannot be achieved without modifying files outside the allowlist;
- `--allow-consumed` cannot be implemented without importing substantial PR #5 control-plane code;
- strict local preflight must be weakened to make Workflow validation pass;
- a wrong Decision, round, report, status, skill, mainline, scope, or dirty-start fixture passes with `--allow-consumed`;
- `.github/workflows/ci.yml` would need modification;
- either Workflow requires changes beyond full-history checkout and explicit consumed mode;
- a framework installation, runtime dispatch, Trust Layer implementation, GitHub adapter, Web change, User Solve change, database, queue, or scheduler becomes necessary;
- tests fail and repair requires leaving the allowed paths;
- required commands cannot be fully recorded in `pytest_result.txt` and `execution_log.json`;
- build outputs or egg-info enter the committed diff;
- CI fails after clean packaging installation for a reason inside the allowed scope that cannot be fixed without scope expansion;
- State Gate or Decision Preflight fails at `Install package` or `Project gate preflight` after the integration changes;
- the work begins repairing downstream legacy report-summary, closeout, state-manifest, seal, or remote-attestation steps;
- a post-remote-evidence commit would be needed;
- the round attempts to begin the next workstream automatically.

On successful completion, stop after exact-head evidence is collected and the Draft PR is ready for independent audit. Do not merge and do not begin Trust Layer work.
