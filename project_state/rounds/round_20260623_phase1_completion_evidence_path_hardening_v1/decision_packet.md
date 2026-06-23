```json decision_meta
{
  "schema_version": 1,
  "decision_id": "decision_20260623_phase1_completion_evidence_path_hardening_v1",
  "round_id": "round_20260623_phase1_completion_evidence_path_hardening_v1",
  "based_on_state_build_id": "state_20260618_134029_d6bd033d2532",
  "based_on_state_digest": "d6bd033d25324345cfd8ada0ac65db42bc86eb5017f3ffc92906fcd8b71cacb5",
  "status": "APPROVED",
  "mainline": "engineering_branch",
  "skill_profiles": ["reverse-agent-iteration@v2"]
}
```

```json decision_contract
{
  "previous_decision_id": "decision_20260623_phase1_completion_execute_decision_closure_v1",
  "previous_round_id": "round_20260623_phase1_completion_execute_decision_closure_v1",
  "previous_audit_outcome": "REWORK_REQUIRED",
  "primary_goal": "Harden Phase 1 completion evidence-path validation so a PASS/SUCCESS report cannot cite missing or unreported evidence paths, with special focus on the missing execute_decision_result.json evidence path referenced by phase1_completion_result.json.",
  "command_plan_authority_required": true,
  "accepted_requires_phase1_completion_artifact": true,
  "accepted_requires_phase1_evidence_paths_exist": true,
  "accepted_requires_phase1_evidence_paths_reported": true,
  "accepted_requires_execute_decision_evidence_current": true,
  "accepted_requires_no_phase2_scope": true,
  "accepted_requires_final_check_passed": true,
  "accepted_requires_execution_log_consistency_passed": true,
  "accepted_requires_report_auto_summary_consistency_passed": true,
  "accepted_requires_report_summary_passed": true,
  "accepted_requires_run_closeout_passed": true,
  "accepted_requires_report_status_success": true,
  "accepted_requires_report_acceptance_accepted": true,
  "allowed_source_files": [
    "reverse_agent/project_gate.py",
    "tests/test_project_gate.py"
  ],
  "allowed_state_artifacts": [
    "project_state/codex_execution_report.md",
    "project_state/pytest_result.txt",
    "project_state/gates/codex_report_auto_summary.json",
    "project_state/gates/command_plan.json",
    "project_state/gates/execute_decision_result.json",
    "project_state/gates/execution_log.json",
    "project_state/gates/final_gate_result.json",
    "project_state/gates/gate_profile_plan.json",
    "project_state/gates/phase1_completion_result.json",
    "project_state/gates/preflight_result.json",
    "project_state/gates/policy_impact_audit.json",
    "project_state/gates/policy_lint_result.json",
    "project_state/gates/report_summary_synthesis.json",
    "project_state/gates/round_baseline.json",
    "project_state/gates/round_close_snapshot.json",
    "project_state/gates/round_delta_summary.json",
    "project_state/gates/run_closeout_execution_log.json",
    "project_state/gates/run_closeout_result.json",
    "project_state/gates/run_round_result.json",
    "project_state/rounds/round_20260623_phase1_completion_evidence_path_hardening_v1/*"
  ],
  "forbidden_mutated_paths": [
    "project_state/current_state.json",
    "project_state/task_packet.json",
    "project_state/artifact_index.json",
    "project_state/negative_results.json",
    ".codex-skills/registry.json",
    "docs/prompts/project_workspace_prompt.md",
    "docs/prompts/codex_execution_prompt.md",
    "docs/prompts/README.md"
  ]
}
```

# DECISION_PACKET

## 1. Goal

Implement Phase 1 Completion Evidence Path Hardening v1.

The previous round mostly completed the Phase 1 local hard-gate closure: `execute-decision` was added as a thin wrapper, command-plan authority remained active, `phase1_completion_result.json` was generated, tests passed, and final-check reported `PASSED`. However, audit found a blocker: `project_state/gates/phase1_completion_result.json` marked `execute_decision_entrypoint` as `PASS` while citing `project_state/gates/execute_decision_result.json` as its `evidence_path`, but that artifact did not exist in GitHub and was not included in `generated_artifacts`, `referenced_artifacts`, existing gate artifacts, or final-check live paths.

This round must harden the Phase 1 completion gate so a completion artifact cannot claim a PASS using missing or unreported evidence paths. The fix must either generate and report `project_state/gates/execute_decision_result.json` as current evidence, or change the Phase 1 completion evidence path to real current artifacts such as `execution_log.json`, `command_plan.json`, and `run_round_result.json`. In either case, final-check must verify that every `phase1_completion_result.json.capabilities[*].evidence_path` exists and is represented in the report evidence chain.

This is a narrow evidence-path hardening round. Do not start naming-neutralization, state hygiene cleanup, file deletion, Phase 2 CI, Web UI, AgentRunner, database, queue, scheduler, or multi-executor architecture.

## 2. Current Evidence

Mainline: `engineering_branch`.

`task_packet.json` remains background-only `samplereverse` sample state and is not authoritative. The current task is controlled by this `decision_packet.md`.

Previous audit outcome: `REWORK_REQUIRED` for `decision_20260623_phase1_completion_execute_decision_closure_v1`.

Accepted prior-round facts:

- `codex_execution_report.md` reached `SUCCESS / ACCEPTED` for `round_20260623_phase1_completion_execute_decision_closure_v1`.
- `pytest_result.txt` reached `PASSED`, with `tests/test_project_gate.py` and `tests/test_project_gate.py tests/test_project_state.py` passing.
- `execute-decision` appeared in `command_plan.json` and in `execution_log.json` as an authorized command kind.
- `pytest_result.txt` recorded `execute-decision --dry-run --json` with `entrypoint: execute-decision` and `delegates_to: run-round`.
- `execution_log.json`, `codex_report_auto_summary.json`, `report_summary_synthesis.json`, `final_gate_result.json`, and `run_closeout_result.json` all reached `PASSED` for the previous round.
- `phase1_completion_result.json` existed and enumerated 10 Phase 1 capabilities.

Blocking facts from audit:

- `phase1_completion_result.json` listed capability `execute_decision_entrypoint` with `evidence_path: project_state/gates/execute_decision_result.json` and `status: PASS`.
- `project_state/gates/execute_decision_result.json` did not exist when fetched from GitHub.
- `execute_decision_result.json` was absent from `codex_execution_report.md.generated_artifacts`.
- `execute_decision_result.json` was absent from `codex_report_auto_summary.json.generated_artifacts`.
- `execute_decision_result.json` was absent from final-check `generated_artifact_live_paths_exist` and `generated_artifacts_cover_gate_artifacts` evidence.
- final-check had `phase1_completion_status: PASS`, but did not validate individual capability `evidence_path` existence or report coverage.
- `execute-decision` non-dry-run stdout reported `mode: dry-run` and `executed_count: 0`; this may be acceptable as self-invocation recursion prevention, but the report must describe the semantics precisely.

Artifact freshness:

- All proof for this rework must be regenerated under `decision_20260623_phase1_completion_evidence_path_hardening_v1` and `round_20260623_phase1_completion_evidence_path_hardening_v1`.
- Prior-round artifacts are diagnostic context only.
- Historical/backlog `samplereverse` artifacts remain external notices only and must not be claimed as current evidence.

Existing capabilities to reuse:

- `preflight` and decision metadata validation.
- `command-plan`, omitted-command authority, and `execute-decision` command kind handling.
- `run-round --dry-run --json` and `run-round --execute`.
- `execution-log` current-round derivation.
- `report-auto-summary`, `report-summary`, and final-check consistency checks.
- `phase1_completion_result.json` generation.
- `run-closeout`, `close-round`, round manifest, and archive consistency checks.
- `policy-lint` and `policy-impact`.

Gate/command-plan strategy:

- Use only valid profiles: `fast`, `standard`, `full`.
- Because this round changes final-check and Phase 1 completion evidence validation, command-plan should select or require `full` validation.
- Tests are subordinate to command-plan. If this Tests section conflicts with command-plan, command-plan is authoritative.
- Closeout may run only if command-plan authorizes it and the selected profile allows closeout.

Tool policy:

- This is not a reverse-solving round.
- Do not inspect, execute, debug, emulate, or solve sample binaries.
- Do not use IDA, Ghidra, OllyDbg, x64dbg, radare2, runtime probes, solver expansion, harness sample execution, or full `solve_reports/` scans.

## 3. Do Not Do

Do not broaden this round into naming-neutralization, `execution_report.md` migration, Codex-name cleanup, state hygiene deletion, orphan artifact deletion, Phase 2 GitHub CI, `ci.yml`, `state-gate.yml`, PR automation, branch protection, Web UI, AgentRunner, Codex adapter, Trae adapter, Job Manager, database, queue, scheduler, daemon, API Planner, API Auditor, self-hosted runner, or background worker work.

Do not continue `samplereverse` solving or any sample-solving task.

Do not read the full `solve_reports/` directory or full `PROJECT_PROGRESS_LOG.txt`.

Do not treat old sample artifacts or prior-round gate artifacts as current evidence.

Do not create a second execution engine. `execute-decision` must remain a thin command-plan-controlled wrapper around the existing run-round execution path or an explicitly guarded no-recursion wrapper.

Do not bypass command-plan. `execute-decision` must not execute omitted or unauthorized commands.

Do not weaken existing command-plan authority, execution-log consistency, report-auto-summary consistency, report-summary consistency, final-check strictness, archive strictness, run-closeout evidence scoping, generated_artifacts coverage, or Required Audit coverage.

Do not allow `phase1_completion_result.json` to mark a capability `PASS` with a missing evidence path.

Do not allow a `project_state/gates/*` evidence path to be omitted from both `generated_artifacts` and `referenced_artifacts` unless it is explicitly documented as a non-file logical evidence reference and final-check understands it.

Do not relabel missing evidence as accepted merely to close Phase 1.

Do not inject closeout-internal commands into the top-level `pytest_result.txt` command stream. Closeout-internal commands must remain scoped in closeout evidence.

Do not modify forbidden paths:

- `project_state/current_state.json`
- `project_state/task_packet.json`
- `project_state/artifact_index.json`
- `project_state/negative_results.json`
- `.codex-skills/registry.json`
- `docs/prompts/project_workspace_prompt.md`
- `docs/prompts/codex_execution_prompt.md`
- `docs/prompts/README.md`

Do not introduce a `medium` profile.

Do not commit, push, create PRs, switch branches, rebase, merge, or modify remote state unless the user explicitly requests it in the current message given to the executor.

## 4. Files To Inspect

Read default state files first:

1. `project_state/task_packet.json`
2. `project_state/current_state.json`
3. `project_state/artifact_index.json`
4. `project_state/negative_results.json`
5. `project_state/codex_execution_report.md`
6. `project_state/decision_packet.md`
7. `project_state/pytest_result.txt`
8. `.codex-skills/registry.json`

Then inspect only relevant implementation and gate evidence files:

1. `reverse_agent/project_gate.py`
2. `tests/test_project_gate.py`
3. `project_state/gates/phase1_completion_result.json`
4. `project_state/gates/execute_decision_result.json` if present
5. `project_state/gates/command_plan.json`
6. `project_state/gates/execution_log.json`
7. `project_state/gates/codex_report_auto_summary.json`
8. `project_state/gates/report_summary_synthesis.json`
9. `project_state/gates/final_gate_result.json`
10. `project_state/gates/preflight_result.json`
11. `project_state/gates/policy_lint_result.json`
12. `project_state/gates/policy_impact_audit.json`
13. `project_state/gates/run_round_result.json`
14. `project_state/gates/run_closeout_result.json`
15. `project_state/gates/run_closeout_execution_log.json`
16. `project_state/gates/round_delta_summary.json`
17. `project_state/gates/round_close_snapshot.json` if present
18. `project_state/rounds/round_20260623_phase1_completion_execute_decision_closure_v1/round_manifest.json` only as bounded prior-round diagnostic evidence
19. `project_state/rounds/round_20260623_phase1_completion_execute_decision_closure_v1/codex_execution_report.md` only as bounded prior-round diagnostic evidence

Do not scan the full `project_state/rounds/`, full `solve_reports/`, or full `PROJECT_PROGRESS_LOG.txt`.

## 5. Required Audit

Before claiming success, `project_state/codex_execution_report.md` must answer all eight items below. Each answer must include concrete evidence and one status value: `PASS`, `FAIL`, `BLOCKED`, or `NOT_APPLICABLE`.

1. Why did the previous `phase1_completion_result.json` cite `project_state/gates/execute_decision_result.json` as PASS evidence while that file was missing from GitHub and absent from generated_artifacts?
2. What rule now ensures every `phase1_completion_result.json.capabilities[*].evidence_path` exists or is explicitly represented as a valid non-file evidence reference?
3. What rule now ensures every `project_state/gates/*` evidence path in Phase 1 completion is included in `generated_artifacts` or `referenced_artifacts` before a SUCCESS report is accepted?
4. How is `execute-decision` currently evidenced: by a real `execute_decision_result.json`, or by existing artifacts such as `execution_log.json`, `command_plan.json`, and `run_round_result.json`? Why is that evidence current and sufficient?
5. How does final-check prove `phase1_completion_status`, `phase1_completion_evidence_paths_exist`, and `phase1_completion_evidence_paths_reported` all pass?
6. Which regression tests prove missing Phase 1 evidence paths block SUCCESS, unreported gate evidence paths block SUCCESS, real execute-decision evidence passes, and alternate existing-artifact execute-decision evidence passes if no separate result artifact is generated?
7. If `execute-decision` non-dry-run uses a self-invocation guard and reports `mode: dry-run` / `executed_count: 0`, why is that safe, and how is the report wording corrected to avoid implying that it executed a second independent run?
8. How does this round preserve no sample-solving behavior, no prompt/skill mutation, no forbidden path mutation, no heavy artifact scan, no evidence weakening, and no Phase 2 expansion?

Do not write TODO, TBD, PENDING, “should pass”, “expected to pass”, or speculative answers.

## 6. Implementation Scope

Primary scope: harden Phase 1 completion evidence-path validation and correct execute-decision evidence semantics.

Allowed source changes:

- `reverse_agent/project_gate.py`
- `tests/test_project_gate.py`

Allowed generated or updated state artifacts:

- `project_state/codex_execution_report.md`
- `project_state/pytest_result.txt`
- `project_state/gates/codex_report_auto_summary.json`
- `project_state/gates/command_plan.json`
- `project_state/gates/execute_decision_result.json`
- `project_state/gates/execution_log.json`
- `project_state/gates/final_gate_result.json`
- `project_state/gates/gate_profile_plan.json`
- `project_state/gates/phase1_completion_result.json`
- `project_state/gates/preflight_result.json`
- `project_state/gates/policy_impact_audit.json`
- `project_state/gates/policy_lint_result.json`
- `project_state/gates/report_summary_synthesis.json`
- `project_state/gates/round_baseline.json`
- `project_state/gates/round_close_snapshot.json`
- `project_state/gates/round_delta_summary.json`
- `project_state/gates/run_closeout_execution_log.json`
- `project_state/gates/run_closeout_result.json`
- `project_state/gates/run_round_result.json`
- `project_state/rounds/round_20260623_phase1_completion_evidence_path_hardening_v1/*`

Required behavior:

1. Establish a current-round baseline before modifications.
2. Inspect existing `phase1_completion_result.json` generation and final-check handling.
3. Add or harden validation so every capability `evidence_path` is checked for existence when it is a file path.
4. Add or harden validation so every `project_state/gates/*` capability `evidence_path` is covered by live report `generated_artifacts` or `referenced_artifacts`.
5. Ensure missing evidence paths block `SUCCESS / ACCEPTED` reports.
6. Decide one of two valid execute-decision evidence strategies:
   - Strategy A: generate `project_state/gates/execute_decision_result.json`, include it in generated_artifacts, include it in gate artifact coverage, and make it current; or
   - Strategy B: change `execute_decision_entrypoint.evidence_path` to a real current artifact or list of artifacts that already exist and are reported, such as `project_state/gates/execution_log.json`, `project_state/gates/command_plan.json`, and `project_state/gates/run_round_result.json`.
7. If multiple evidence paths are needed for a capability, use a schema that final-check validates, such as `evidence_paths: [...]`, while preserving backward compatibility with singular `evidence_path`.
8. Correct report wording around `execute-decision` non-dry-run/no-recursion behavior. Do not claim it performed an independent second execution if it intentionally guarded into dry-run/no-op mode.
9. Preserve prior fixes: execution-log must remain current-round-only, report-auto-summary must remain current-round-only, report-summary must match live report, final-check must pass, closeout log must remain current, generated_artifacts must remain complete.
10. Add focused regression tests for Phase 1 missing evidence paths, evidence path report coverage, execute-decision evidence strategy, and final-check blocking behavior.
11. Regenerate current-round `pytest_result.txt`, `execution_log.json`, `codex_report_auto_summary.json`, `report_summary_synthesis.json`, `final_gate_result.json`, `phase1_completion_result.json`, and `codex_execution_report.md`.
12. Run closeout if and only if command-plan authorizes it.
13. Final accepted report must be `SUCCESS / ACCEPTED` with final-check `PASSED`, phase1 completion `PASSED`, evidence-path checks `PASSED`, execution-log `PASSED`, report-auto-summary `PASSED`, report-summary `PASSED`, run-closeout `PASSED`, and no blocking reasons.

Do not implement Phase 2 or naming cleanup in this round.

## 7. Tests

Run startup checks first:

```powershell
Set-Location F:\reverse-agent
Get-Location
Test-Path F:\reverse-agent
git rev-parse --show-toplevel
git status --short
```

Run preflight before implementation:

```powershell
python -m reverse_agent.project_gate preflight --state-dir project_state
```

Generate and obey command-plan:

```powershell
python -m reverse_agent.project_gate command-plan --state-dir project_state --json
```

After implementation, run only command-plan-authorized commands. If authorized, expected validation includes:

```powershell
python -m reverse_agent.project_gate command-plan --state-dir project_state
python -m reverse_agent.project_gate command-plan --state-dir project_state --json
python -m reverse_agent.project_gate preflight --state-dir project_state
python -m reverse_agent.project_gate run-round --state-dir project_state --round-id round_20260623_phase1_completion_evidence_path_hardening_v1 --dry-run --json
python -m reverse_agent.project_gate run-round --state-dir project_state --round-id round_20260623_phase1_completion_evidence_path_hardening_v1 --execute
python -m reverse_agent.project_gate execute-decision --state-dir project_state --round-id round_20260623_phase1_completion_evidence_path_hardening_v1 --dry-run --json
python -m reverse_agent.project_gate execute-decision --state-dir project_state --round-id round_20260623_phase1_completion_evidence_path_hardening_v1
python -m pytest tests/test_project_gate.py -q
python -m pytest tests/test_project_gate.py tests/test_project_state.py -q
python -m reverse_agent.project_gate policy-lint --state-dir project_state
python -m reverse_agent.project_gate policy-impact --state-dir project_state
python -m reverse_agent.project_gate execution-log --state-dir project_state
python -m reverse_agent.project_gate report-auto-summary --state-dir project_state
python -m reverse_agent.project_gate report-summary --state-dir project_state
python -m reverse_agent.project_gate final-check --state-dir project_state
python -m reverse_agent.project_gate run-closeout --state-dir project_state --round-id round_20260623_phase1_completion_evidence_path_hardening_v1
python -m reverse_agent.project_gate execution-log --state-dir project_state
python -m reverse_agent.project_gate report-auto-summary --state-dir project_state
python -m reverse_agent.project_gate report-summary --state-dir project_state
python -m reverse_agent.project_gate final-check --state-dir project_state
```

The exact command set is whatever current command-plan authorizes. Command-plan overrides this Tests section if there is any conflict.

Record all top-level commands in `project_state/pytest_result.txt`. Do not include nested closeout-internal command blocks in the top-level command stream. Record nested closeout command evidence in `project_state/gates/run_closeout_execution_log.json` or the existing scoped closeout evidence artifact.

## 8. Stop Conditions

Stop immediately and report `BLOCKED` if:

- startup checks do not confirm `F:\reverse-agent` and repository root;
- `decision_meta` is missing or invalid;
- `status` is not `APPROVED`;
- `mainline` is invalid;
- skill profiles do not match active registry entries;
- command-plan is missing, failed, or conflicts with safe execution;
- a needed command is not authorized by command-plan;
- the fix requires modifying files outside allowed source scope;
- state updates require forbidden paths;
- implementation requires weakening command-plan authority, execution-log consistency, archive strictness, report-summary consistency, report-auto-summary consistency, final-check strictness, generated_artifacts coverage, or Required Audit coverage;
- implementing evidence validation would require deleting or rewriting unrelated history;
- execute-decision evidence cannot be represented by current structured evidence;
- run-closeout cannot keep nested command evidence scoped outside the top-level command stream;
- Required Audit remains incomplete or placeholder-like.

Stop with `REWORK_REQUIRED` if tests fail, command-plan authority regresses, execution-log regresses, report-auto-summary regresses, report-summary regresses, policy-lint fails, policy-impact fails, Phase 1 completion artifact is missing or not PASSED, any capability evidence path is missing, any gate evidence path is absent from generated_artifacts/referenced_artifacts without explicit valid treatment, execute-decision evidence remains missing or misleading, run-closeout fails, final-check has warnings or blocking reasons, `generated_artifacts` misses current gate artifacts, or the final report remains `PARTIAL / NEEDS_REVIEW` for reasons other than a clearly documented real blocker.
