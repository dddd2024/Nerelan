```json decision_meta
{
  "schema_version": 1,
  "decision_id": "decision_20260629_startup_snapshot_and_control_plane_rework_v1",
  "round_id": "round_20260629_startup_snapshot_and_control_plane_rework_v1",
  "based_on_state_build_id": "state_20260618_134029_d6bd033d2532",
  "based_on_state_digest": "d6bd033d25324345cfd8ada0ac65db42bc86eb5017f3ffc92906fcd8b71cacb5",
  "status": "APPROVED",
  "mainline": "engineering_branch",
  "skill_profiles": ["reverse-agent-iteration@v2"]
}
```

```json decision_contract
{
  "previous_decision_id": "decision_20260629_control_plane_snapshot_gate_v1",
  "previous_round_id": "round_20260629_control_plane_snapshot_gate_v1",
  "previous_audit_outcome": "REWORK_REQUIRED",
  "supersedes_uploaded_decision_id": "decision_20260629_control_plane_snapshot_gate_v1",
  "phase_label": "phase_2_17_startup_snapshot_and_control_plane_rework",
  "primary_goal": "Fix startup baseline ordering with a hard startup snapshot gate, then rerun and finalize control-plane snapshot so it reflects post-closeout final state.",
  "subplans": [
    {
      "plan_id": "fix_plan_startup_snapshot_hard_gate_v1",
      "kind": "repair",
      "priority": 1,
      "goal": "Make startup evidence machine-captured, startup-first, and impossible to excuse through inherited dirty source/test allowlists."
    },
    {
      "plan_id": "engineering_plan_control_plane_final_state_sync_v1",
      "kind": "next_engineering",
      "priority": 2,
      "goal": "Refresh control_plane_snapshot after final-check/run-closeout so UI/runner consumers see final current state."
    }
  ],
  "command_plan_authority_required": true,
  "accepted_requires_clean_source_test_start": true,
  "accepted_requires_startup_snapshot_artifact": true,
  "accepted_requires_control_plane_snapshot_artifact": true,
  "accepted_requires_startup_snapshot_first": true,
  "accepted_requires_no_source_test_inherited_dirty_allowlist": true,
  "accepted_requires_final_state_snapshot_refresh": true,
  "accepted_requires_no_remote_mutation": true,
  "accepted_requires_report_summary_fields_match_synthesis": true,
  "accepted_requires_execute_decision_contract_passed": true,
  "accepted_requires_run_closeout_exit_zero": true,
  "accepted_requires_closeout_nested_failures_absent": true,
  "allowed_source_files": [
    "reverse_agent/project_gate.py",
    "reverse_agent/project_control_plane.py",
    "tests/test_project_gate.py",
    "tests/test_project_control_plane.py",
    "tests/test_project_gate_baseline_lifecycle.py",
    "docs/prompts/codex_execution_prompt.md"
  ],
  "preserve_only_files": [
    "reverse_agent/project_audits.py",
    "reverse_agent/project_jobs.py",
    "reverse_agent/project_rounds.py",
    "tests/test_project_audits.py",
    "tests/test_project_jobs.py",
    "tests/test_project_rounds.py",
    ".github/workflows/decision-preflight.yml",
    ".github/workflows/ci.yml",
    ".github/workflows/state-gate.yml"
  ],
  "preserve_only_audit_records": [
    "project_state/audits/audit_20260629_rework_required_audit_inventory_gate.md",
    "project_state/audits/audit_20260629_rework_required_clean_baseline_jobs_inventory_gate.md"
  ],
  "allowed_new_gate_artifacts": [
    "project_state/gates/startup_snapshot.json",
    "project_state/gates/control_plane_snapshot.json"
  ],
  "forbidden_mutated_paths": [
    "project_state/current_state.json",
    "project_state/task_packet.json",
    "project_state/artifact_index.json",
    "project_state/negative_results.json",
    ".codex-skills/registry.json",
    "docs/prompts/project_workspace_prompt.md",
    "docs/prompts/README.md",
    "project_state/audits/audit_20260629_rework_required_audit_inventory_gate.md",
    "project_state/audits/audit_20260629_rework_required_clean_baseline_jobs_inventory_gate.md"
  ]
}
```

# DECISION_PACKET

## 1. Goal

Implement a merged repair-and-next-engineering round:

1. **Fix Plan: Startup Snapshot Hard Gate v1**
   - Convert startup evidence from a mutable text convention in `pytest_result.txt` into a first-class gate artifact: `project_state/gates/startup_snapshot.json`.
   - Make startup capture the first executable phase before implementation, pytest, command-plan execution, preflight, report generation, and closeout.
   - Treat any startup dirty source/test file under `reverse_agent/` or `tests/` as `BLOCKED` with no inherited dirty allowlist exception.
   - Make `round_baseline.json` derive from startup snapshot, not from a later git status capture.
   - Promote source/test baseline capture-order violations from WARN to FAIL/REWORK_REQUIRED.

2. **Next Engineering Plan: Control Plane Snapshot Final-State Sync v1**
   - Preserve the control-plane snapshot builder from the previous round if correct.
   - Refresh or regenerate `project_state/gates/control_plane_snapshot.json` after final-check and run-closeout so it reflects the final accepted state, not an intermediate pre-closeout state.
   - Ensure the snapshot exposes accurate final `final_gate_status`, `closeout_status`, `close_round_status`, warnings, blocking reasons, runner readiness, and UI summary.

This is a single `engineering_branch` round. The repair phase must complete first. The control-plane final-state phase must not proceed unless the startup snapshot hard gate is functioning and passes from a clean source/test baseline.

Preferred final outcome:

- `codex_report_summary.status: SUCCESS`.
- `acceptance_recommendation: ACCEPTED`.
- `limitations` absent or empty.
- startup source/test baseline is clean and captured by `startup_snapshot.json`.
- `command_plan.json` lists startup commands first before any pytest, implementation gate, report-summary, execute-decision, final-check, or run-closeout command.
- `preflight_result.json` reads startup cleanliness from `startup_snapshot.json` and cannot excuse source/test dirty files through inherited allowlists.
- `round_baseline.json` matches `startup_snapshot.json` for startup dirty state.
- `baseline_capture_order` is PASS or absent, not WARN.
- `final_gate_result.json.gate_status` is `PASSED`, not `PASSED_WITH_LIMITATIONS`.
- `control_plane_snapshot.json` is current after closeout and reports `final_gate_status: PASSED`, `closeout_status: PASSED`, and `close_round_status: CLOSED`.
- runner readiness remains non-dispatching by default unless explicit safe dispatch evidence exists.
- no forbidden path, remote mutation, Web UI, AgentRunner, database, queue, scheduler, GitHub Actions mutation, or reverse-solving work is introduced.

## 2. Current Evidence

Mainline: `engineering_branch`.

The current task is controlled by `project_state/decision_packet.md` as the task contract. `project_state/task_packet.json` remains background only and still refers to older `samplereverse` missing evidence; it must not drive this engineering round.

Command execution authority remains `command-plan`: Codex may only execute commands authorized in `command-plan.commands`, and must not execute commands listed in `command-plan.omitted_commands`. If Tests and command-plan conflict, command-plan controls the concrete command list, but command-plan may not override startup-first ordering, clean source/test baseline requirements, startup snapshot hard gating, artifact freshness, report-summary convergence, final-check, or closeout requirements.

The previous `decision_20260629_control_plane_snapshot_gate_v1` execution was audited as `REWORK_REQUIRED` for two reasons:

1. The recorded startup `git status --short` contained dirty source/test files under `reverse_agent/` and `tests/`, yet execution continued.
2. `control_plane_snapshot.json` existed but reflected an intermediate state with failed final/closeout statuses even though later final-check and run-closeout passed.

Observed process defects to fix:

- `command_plan.json` allowed non-startup commands before startup commands in a previous run.
- `pytest_result.txt` is mutable final text and cannot prove startup commands happened before file edits.
- `preflight_result.json` allowed source/test dirty files to pass as `allowed_inherited_dirty_baseline_files`.
- `round_baseline.json` was able to contain untracked implementation files, indicating late baseline capture.
- final-check downgraded source/test baseline capture-order overlap to WARN, causing `PASSED_WITH_LIMITATIONS` instead of hard failure.
- control-plane snapshot was generated before closeout/final-check convergence and was not refreshed afterward.

Existing capability to build on:

- `project_gate` already exposes preflight, command-plan, report-summary, execute-decision, execution-log, final-check, run-closeout, audit-inventory, jobs-inventory, and control-plane-snapshot gate surfaces.
- `project_control_plane.py` and its tests from the previous round may be preserved if correct, but must be adjusted for final-state refresh semantics.
- `tests/test_project_gate_baseline_lifecycle.py` already contains lifecycle tests that should be extended to cover startup snapshot hard failure and command-plan startup ordering.
- `docs/prompts/codex_execution_prompt.md` currently permits an inherited dirty baseline exception for source/test files. This must be tightened so `reverse_agent/` and `tests/` dirty startup state is always blocking.

Artifact freshness:

- `startup_snapshot.json` and `control_plane_snapshot.json` must carry this decision ID and round ID.
- Older sample artifacts with `missing`, `stale`, or unknown freshness may be referenced only as backlog/context, not current evidence.
- Existing audit and job inventory artifacts may be historical/nonblocking if their decision/round IDs are stale; they must not be mislabeled as current.

Negative results:

- `negative_results.json` blocks old sample_solver blind search, only increasing beam/budget, using compare_semantics_agree=false candidates as primary frontier, committing full solve_reports, and repeating old bounded runtime branches.
- This round must not perform reverse-solving, runtime probing, dynamic debugging, sample execution, or full solve_reports scans.

Allowed tool scope:

- It is allowed to run bounded local project gate commands and pytest commands authorized by command-plan.
- It is allowed to update prompt docs only for the startup dirty baseline rule in `docs/prompts/codex_execution_prompt.md`.
- It is not allowed to read full `solve_reports/`, full `PROJECT_PROGRESS_LOG.txt`, or full `project_state/rounds/`.
- It is not allowed to mutate GitHub or remote state unless the user separately instructs the executor to upload.

## 3. Do Not Do

Do not treat `pytest_result.txt` as the sole startup proof. It may record the transcript, but `startup_snapshot.json` must be the authoritative startup evidence artifact.

Do not let report prose, `files_changed`, or an inherited-dirty allowlist excuse dirty source/test files under `reverse_agent/` or `tests/` at startup.

Do not allow `allowed_inherited_dirty_baseline_files` to include source/test implementation files. For this round, source/test startup dirty state must be hard blocking.

Do not generate `round_baseline.json` from a later git status after implementation. It must derive from `startup_snapshot.json` or match it exactly.

Do not generate `command_plan.json` with pytest, implementation gates, report-summary, execute-decision, final-check, run-closeout, or closeout before startup commands.

Do not accept `baseline_capture_order` as WARN if source/test files overlap between baseline dirty and files_changed. That case must fail or force REWORK_REQUIRED.

Do not leave `control_plane_snapshot.json` in a pre-closeout or intermediate state while claiming acceptance. The final accepted snapshot must be post-closeout/current.

Do not implement Web UI, AgentRunner adapters, API Planner/Auditor, database, queue, scheduler, self-hosted runner automation, GitHub Actions mutation, automatic push, or reverse-solving.

Do not rewrite existing job/audit/round inventory modules except where `project_gate.py` needs to reference them. Preserve `reverse_agent/project_audits.py`, `reverse_agent/project_jobs.py`, `reverse_agent/project_rounds.py`, and their tests.

Do not mutate existing audit records under `project_state/audits/`.

Do not modify `current_state.json`, `task_packet.json`, `artifact_index.json`, `negative_results.json`, `.codex-skills/registry.json`, or unrelated prompt docs.

Do not scan full `solve_reports/`, run samples, execute runtime probes, or perform dynamic debugging.

Do not claim `SUCCESS` or `ACCEPTED` unless final-check and run-closeout converge without active warnings or nested failures.

Do not commit, push, create PRs, switch branches, rebase, merge, or modify remote state unless the user explicitly instructs the executor to do so.

## 4. Files To Inspect

Read first:

1. `project_state/task_packet.json`
2. `project_state/current_state.json`
3. `project_state/artifact_index.json`
4. `project_state/negative_results.json`
5. `project_state/codex_execution_report.md`
6. `project_state/execution_report.md` if present
7. `project_state/decision_packet.md`
8. `project_state/pytest_result.txt`
9. `.codex-skills/registry.json`

Then inspect implementation and gate evidence:

1. `reverse_agent/project_gate.py`
2. `reverse_agent/project_control_plane.py`
3. `tests/test_project_gate.py`
4. `tests/test_project_control_plane.py`
5. `tests/test_project_gate_baseline_lifecycle.py`
6. `docs/prompts/codex_execution_prompt.md`
7. `project_state/gates/command_plan.json`
8. `project_state/gates/preflight_result.json`
9. `project_state/gates/round_baseline.json`
10. `project_state/gates/round_delta_summary.json`
11. `project_state/gates/control_plane_snapshot.json`
12. `project_state/gates/final_gate_result.json`
13. `project_state/gates/run_closeout_result.json`
14. `project_state/gates/execution_log.json`
15. `project_state/gates/report_summary_synthesis.json`

Inspect preserve-only files only enough to avoid duplicate implementation:

1. `reverse_agent/project_audits.py`
2. `reverse_agent/project_jobs.py`
3. `reverse_agent/project_rounds.py`
4. `tests/test_project_audits.py`
5. `tests/test_project_jobs.py`
6. `tests/test_project_rounds.py`

Do not scan full `project_state/rounds/`, full `solve_reports/`, or full `PROJECT_PROGRESS_LOG.txt`.

## 5. Required Audit

The report must answer all items with concrete evidence and status `PASS`, `FAIL`, `BLOCKED`, or `NOT_APPLICABLE`:

1. Was startup source/test baseline clean before implementation?
2. Was `startup_snapshot.json` generated before any pytest, implementation gate, report-summary, execute-decision, final-check, or run-closeout command?
3. Does `startup_snapshot.json` carry current decision ID, round ID, head commit, startup command sequence, raw git status output, source/test dirty list, generated state dirty list, and clean-source-test boolean?
4. Does startup source/test dirty under `reverse_agent/` or `tests/` produce BLOCKED/failed preflight with no inherited dirty exception?
5. Does command-plan place startup commands before all non-startup commands?
6. Does command-plan fail or block if startup commands are missing or not first?
7. Does preflight derive `source_test_clean_start` from `startup_snapshot.json` rather than report prose or files_changed?
8. Does `round_baseline.json` derive from or exactly match `startup_snapshot.json` for startup dirty state?
9. Does final-check treat source/test baseline dirty overlap with files_changed as FAIL/REWORK_REQUIRED, not WARN?
10. Was the existing control-plane snapshot implementation preserved where correct?
11. Does `control_plane_snapshot.json` carry current decision/round IDs and post-closeout final statuses?
12. Does final accepted snapshot report `final_gate_status: PASSED`, `closeout_status: PASSED`, and `close_round_status: CLOSED`?
13. Does runner readiness remain non-dispatching by default unless explicit safe dispatch evidence exists?
14. Does UI summary expose stable headline, next action, blocking reasons, and warnings based on final state?
15. Are stale optional inventory artifacts labeled historical/nonblocking rather than current?
16. Did required pytest commands exit 0, and what are their pass counts?
17. Did `report_summary_fields_match_synthesis` pass with no diffs?
18. Did `execute_decision_contract` pass?
19. Did `run-closeout` exit 0, with `closeout_status: PASSED` and `close_round_result.close_status: CLOSED`?
20. Did `closeout_nested_failures_absent` pass with no active nested FAILED/FAIL states?
21. Did hybrid execution-log provenance remain valid and non-derived-only?
22. Were forbidden paths, preserve-only files, full solve_reports scans, Web/AgentRunner/DB/queue/scheduler scope, GitHub Actions mutation, and remote mutation avoided?

## 6. Implementation Scope

Allowed source/test/doc changes:

- `reverse_agent/project_gate.py`
- `reverse_agent/project_control_plane.py`
- `tests/test_project_gate.py`
- `tests/test_project_control_plane.py`
- `tests/test_project_gate_baseline_lifecycle.py`
- `docs/prompts/codex_execution_prompt.md`

Preserve-only source/test files:

- `reverse_agent/project_audits.py`
- `reverse_agent/project_jobs.py`
- `reverse_agent/project_rounds.py`
- `tests/test_project_audits.py`
- `tests/test_project_jobs.py`
- `tests/test_project_rounds.py`

Preserve-only audit records:

- `project_state/audits/audit_20260629_rework_required_audit_inventory_gate.md`
- `project_state/audits/audit_20260629_rework_required_clean_baseline_jobs_inventory_gate.md`

Allowed generated or updated state artifacts:

- `project_state/gates/startup_snapshot.json`
- `project_state/gates/control_plane_snapshot.json`
- `project_state/execution_report.md`
- `project_state/codex_execution_report.md`
- `project_state/pytest_result.txt`
- `project_state/gates/command_plan.json`
- `project_state/gates/execute_decision_result.json`
- `project_state/gates/execution_log.json`
- `project_state/gates/execution_report_auto_summary.json`
- `project_state/gates/codex_report_auto_summary.json`
- `project_state/gates/final_gate_result.json`
- `project_state/gates/gate_profile_plan.json`
- `project_state/gates/preflight_result.json`
- `project_state/gates/report_summary_synthesis.json`
- `project_state/gates/round_baseline.json`
- `project_state/gates/round_close_snapshot.json`
- `project_state/gates/round_delta_summary.json`
- `project_state/gates/run_closeout_execution_log.json`
- `project_state/gates/run_closeout_result.json`
- `project_state/gates/run_round_result.json`
- `project_state/gates/state_hygiene_inventory.json`
- `project_state/rounds/round_20260629_startup_snapshot_and_control_plane_rework_v1/*`

Required behavior for Fix Plan:

1. Add `python -m reverse_agent.project_gate startup-snapshot --state-dir project_state` or equivalent.
2. The startup-snapshot command must record the startup sequence and current git status into `project_state/gates/startup_snapshot.json`.
3. It must classify dirty paths into source/test dirty and generated/state dirty.
4. Dirty source/test files under `reverse_agent/` or `tests/` must make the snapshot status failed/blocking, not allowed inherited.
5. `preflight` must consume the snapshot and fail if source/test dirty is present.
6. `command-plan` must include startup commands first and must fail if it cannot guarantee startup-first ordering.
7. `final-check` must reject source/test baseline dirty overlap with files_changed as FAIL/REWORK_REQUIRED.
8. `round_baseline.json` must be derived from or checked against `startup_snapshot.json`.
9. Tests must include an attack case where implementation files appear before baseline capture and confirm it cannot be accepted.
10. Update `docs/prompts/codex_execution_prompt.md` to remove the source/test inherited dirty exception.

Required behavior for Next Engineering Plan:

1. Preserve or minimally fix `project_control_plane.py`.
2. Ensure `control-plane-snapshot` can run in a final-state mode after closeout/final-check convergence.
3. The final accepted snapshot must reflect post-closeout statuses, not earlier failed or unknown statuses.
4. If the snapshot is produced before closeout, it must be marked pre-closeout and cannot satisfy accepted final-state requirements.
5. final-check or an equivalent gate must validate that the accepted snapshot is post-closeout/current.
6. Runner readiness must default to `can_dispatch_next_decision: false`.
7. Stale inventory artifacts must be historical/nonblocking, not current.

## 7. Tests

Record startup checks first:

```powershell
Set-Location F:\reverse-agent
Get-Location
Test-Path F:\reverse-agent
git rev-parse --show-toplevel
git status --short
python -m reverse_agent.project_gate startup-snapshot --state-dir project_state
```

Hard startup rule:

- If `git status --short` or `startup_snapshot.json` contains dirty source/test paths under `reverse_agent/` or `tests/`, stop with `BLOCKED` before modifying any source/test file.
- Existing dirty generated state artifacts may be recorded but must not excuse source/test dirty files.

Then run command-plan-authorized validation. At minimum include:

```powershell
python -m reverse_agent.project_gate command-plan --state-dir project_state
python -m reverse_agent.project_gate command-plan --state-dir project_state --json
python -m reverse_agent.project_gate preflight --state-dir project_state --allow-consumed
python -m reverse_agent.project_gate control-plane-snapshot --state-dir project_state
python -m reverse_agent.project_gate report-summary --state-dir project_state
python -m reverse_agent.project_gate execute-decision --state-dir project_state --round-id round_20260629_startup_snapshot_and_control_plane_rework_v1 --mode execute
python -m pytest tests/test_project_gate_baseline_lifecycle.py -q
python -m pytest tests/test_project_control_plane.py -q
python -m pytest tests/test_project_gate.py tests/test_project_state.py tests/test_project_gate_baseline_lifecycle.py tests/test_project_control_plane.py -q
python -m reverse_agent.project_gate execution-log --state-dir project_state
python -m reverse_agent.project_gate final-check --state-dir project_state
python -m reverse_agent.project_gate run-closeout --state-dir project_state --round-id round_20260629_startup_snapshot_and_control_plane_rework_v1
python -m reverse_agent.project_gate control-plane-snapshot --state-dir project_state --final-state
python -m reverse_agent.project_gate final-check --state-dir project_state
```

The command-plan-authorized set is authoritative. If this Tests section conflicts with command-plan, command-plan controls the concrete command list, except it must not override startup-first ordering, startup-snapshot generation, clean source/test baseline, pytest summary consistency, control-plane final-state evidence, report-summary convergence, execute-decision contract, hybrid provenance preservation, or closeout consistency.

Write all top-level commands and exit codes to `project_state/pytest_result.txt`.

## 8. Stop Conditions

Stop immediately and report `BLOCKED` if:

- startup checks do not confirm `F:\reverse-agent` and repository root;
- startup `git status --short` shows dirty source/test files under `reverse_agent/` or `tests/`;
- `startup_snapshot.json` cannot be created as the first gate artifact;
- `startup_snapshot.json` reports source/test dirty files;
- decision_meta is invalid;
- status is not APPROVED;
- mainline is invalid;
- skill profiles do not match active registry entries;
- command-plan is missing, failed, unsafe, or places startup commands after non-startup commands;
- implementation requires mutating existing audit records;
- implementation requires mutating historical round archives outside the current round archive generated by closeout;
- implementation requires modifying preserve-only job, audit inventory, or round inventory files;
- implementation requires forbidden path mutation;
- implementation requires Web UI, AgentRunner, external dispatch, database, queue, scheduler, automatic remote writes, GitHub Actions mutation, or sample-solving work.

Stop with `REWORK_REQUIRED` if:

- any required pytest command exits nonzero;
- `pytest_result_summary.status` contradicts recorded command-block exit codes;
- startup source/test dirty baseline is ignored and implementation proceeds;
- `startup_snapshot.json` is missing, stale, overwritten after implementation, or not referenced by preflight/final-check;
- preflight uses inherited dirty allowlists to pass source/test dirty files;
- `round_baseline.json` differs from `startup_snapshot.json` for startup dirty state;
- `baseline_capture_order` reports WARN for source/test dirty overlap instead of FAIL/REWORK_REQUIRED;
- command-plan lists pytest or non-startup gates before startup commands;
- control-plane snapshot gate command or artifact is missing;
- control-plane snapshot artifact is stale or missing current decision/round IDs;
- final accepted snapshot does not reflect post-closeout statuses;
- final accepted snapshot reports final-check, closeout, or close-round status as failed/unknown while report claims accepted;
- stale optional artifacts are mislabeled as current evidence;
- runner readiness defaults to dispatching without explicit safe dispatch evidence;
- existing audit records or historical round archives are modified outside current closeout archive;
- control-plane snapshot evidence is not included in final-check or equivalent gate evidence;
- `report_summary_fields_match_synthesis` fails;
- `execute_decision_contract` fails;
- `run-closeout` exits nonzero;
- `close_round_result.close_status` is not `CLOSED`;
- `closeout_nested_failures_absent` fails;
- `execution_log.json` regresses to derived-only while report/final-check claims `ACCEPTED`;
- startup transcript order regresses;
- reverse_solving strict freshness semantics regress;
- forbidden paths are modified;
- tests fail.
