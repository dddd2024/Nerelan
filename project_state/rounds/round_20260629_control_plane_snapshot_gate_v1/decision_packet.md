```json decision_meta
{
  "schema_version": 1,
  "decision_id": "decision_20260629_control_plane_snapshot_gate_v1",
  "round_id": "round_20260629_control_plane_snapshot_gate_v1",
  "based_on_state_build_id": "state_20260618_134029_d6bd033d2532",
  "based_on_state_digest": "d6bd033d25324345cfd8ada0ac65db42bc86eb5017f3ffc92906fcd8b71cacb5",
  "status": "APPROVED",
  "mainline": "engineering_branch",
  "skill_profiles": ["reverse-agent-iteration@v2"]
}
```

```json decision_contract
{
  "previous_decision_id": "decision_20260629_audit_inventory_gate_v1",
  "previous_round_id": "round_20260629_audit_inventory_gate_v1",
  "previous_audit_outcome": "ACCEPTED",
  "supersedes_uploaded_decision_id": "decision_20260629_round_manifest_inventory_gate_v1",
  "supersedes_reason": "The round manifest inventory task was too small; this round rolls the same state-readiness direction into a broader control-plane snapshot artifact.",
  "phase_label": "phase_2_16_control_plane_snapshot_gate",
  "primary_goal": "Generate a bounded control-plane snapshot that summarizes active decision/report/test/gate/inventory/runner-readiness state for Web UI or runner consumption.",
  "command_plan_authority_required": true,
  "accepted_requires_clean_source_test_start": true,
  "accepted_requires_control_plane_snapshot_artifact": true,
  "accepted_requires_no_remote_mutation": true,
  "accepted_requires_report_summary_fields_match_synthesis": true,
  "accepted_requires_execute_decision_contract_passed": true,
  "accepted_requires_run_closeout_exit_zero": true,
  "accepted_requires_closeout_nested_failures_absent": true,
  "allowed_source_files": [
    "reverse_agent/project_control_plane.py",
    "reverse_agent/project_gate.py",
    "tests/test_project_control_plane.py",
    "tests/test_project_gate.py"
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
    "project_state/gates/control_plane_snapshot.json"
  ],
  "forbidden_mutated_paths": [
    "project_state/current_state.json",
    "project_state/task_packet.json",
    "project_state/artifact_index.json",
    "project_state/negative_results.json",
    ".codex-skills/registry.json",
    "docs/prompts/project_workspace_prompt.md",
    "docs/prompts/codex_execution_prompt.md",
    "docs/prompts/README.md",
    "project_state/audits/audit_20260629_rework_required_audit_inventory_gate.md",
    "project_state/audits/audit_20260629_rework_required_clean_baseline_jobs_inventory_gate.md"
  ]
}
```

# DECISION_PACKET

## 1. Goal

Implement Control Plane Snapshot Gate v1.

The previous accepted round completed Audit Inventory Gate v1 and made `project_state/audits/*.md` visible as bounded gate evidence. A smaller `Round Manifest Inventory Gate v1` decision was uploaded afterward, but that task is too narrow to materially improve the system. This decision supersedes it with a broader but still bounded control-plane step.

Goal:

1. Add a unified read-only control-plane snapshot builder.
2. Expose it through `project_gate` as `control-plane-snapshot`.
3. Generate `project_state/gates/control_plane_snapshot.json` as current machine-readable state for Web UI / runner / planner consumption.
4. Summarize active decision state, report state, pytest state, final-check state, closeout state, inventory state, command-plan state, runner readiness, and UI-facing summary.
5. Treat missing optional inventory artifacts as warnings or historical/nonblocking states, not as current evidence.
6. Add tests proving the snapshot is stable, rejects hard mismatches, preserves no-dispatch defaults, and does not mutate project evidence.
7. Integrate control-plane snapshot evidence into final-check or an equivalent gate evidence path.

Preferred final outcome:

- `status: SUCCESS`.
- `acceptance_recommendation: ACCEPTED`.
- `limitations` null or absent.
- startup source/test baseline is clean.
- `control_plane_snapshot.json` exists, is current, and records the current decision/round IDs.
- report, pytest, final-check, closeout, and command-plan states are summarized in one artifact.
- runner readiness defaults to non-dispatching unless an explicit safe READY/RUNNING job policy exists.
- UI summary provides a short stable headline, next action, blocking reasons, and warnings.
- `execution_log.json.source` remains hybrid/direct, not derived-only.
- `report_summary_fields_match_synthesis`, `execute_decision_contract`, `run-closeout`, and `closeout_nested_failures_absent` all pass.

This is an engineering branch round. It must not implement Web UI, AgentRunner, API Planner/Auditor, database, queue, scheduler, self-hosted runner automation, automatic remote writes, GitHub Actions mutation, or reverse-solving. It only creates the bounded state artifact that those later surfaces can consume.

## 2. Current Evidence

Mainline: `engineering_branch`.

The current task is controlled by `project_state/decision_packet.md` as the task contract. `project_state/task_packet.json` remains non-authoritative background only and still refers to older `samplereverse` missing evidence. It must not drive this engineering round.

Command execution authority remains `command-plan`: Codex may only execute commands authorized in `command-plan.commands`, and must not execute commands listed in `command-plan.omitted_commands`. If Tests and command-plan conflict, command-plan controls the concrete command list, but it may not override startup-first ordering, clean source/test baseline requirements, artifact freshness, report-summary convergence, final-check, or closeout requirements.

Accepted previous round:

- `decision_20260629_audit_inventory_gate_v1` / `round_20260629_audit_inventory_gate_v1` is accepted.
- `codex_execution_report.md` reports `status: SUCCESS` and `acceptance_recommendation: ACCEPTED`.
- `final_gate_result.json` reports `gate_status: PASSED`, no warnings, and no blocking reasons.
- `baseline_capture_order` is `PASS` with `capture_order_status: clean`.
- startup `git status --short` had no dirty `reverse_agent/` or `tests/` source/test paths.
- `audit_inventory_result.json` is current, passed, and validates two audit records.
- focused audit tests passed with 9 tests.
- combined gate/state/audits tests passed with 1266 tests.
- `execution_log.json.source` remained `hybrid_from_pytest_result_command_plan_and_run_closeout_execution_log`.
- `run-closeout` passed and close-round status was `CLOSED`.

Superseded uploaded decision:

- `decision_20260629_round_manifest_inventory_gate_v1` was uploaded after the accepted audit inventory round.
- It is superseded by this decision before execution because the task was too small. Do not execute that superseded task unless a future decision explicitly restores it.

Current state summary:

- `current_state.json` remains a sample-state snapshot for `samplereverse` with missing runtime/sample artifacts.
- This round does not claim sample-solving progress and must not use sample-state gaps as current solved evidence.
- `artifact_index.json` lists many sample artifacts as `missing`; those are non-blocking for this engineering branch because no reverse-solving evidence is being claimed.

Negative results:

- `negative_results.json` blocks old sample_solver blind search, only increasing beam/budget, using `compare_semantics_agree=false` candidates as primary frontier, committing full `solve_reports`, and repeating old bounded runtime branches.
- This round must not perform reverse-solving, runtime probing, dynamic debugging, sample execution, or full `solve_reports` scans.

Existing capability to build on:

- `project_gate` already exposes preflight, command-plan, jobs-inventory, audit-inventory, report-summary, execute-decision, execution-log, final-check, and run-closeout gate surfaces.
- `project_jobs` and `project_audits` provide inventory validator precedents.
- final-check already synthesizes many important checks. This round should not duplicate final-check wholesale; it should produce a compact, stable, consumer-facing snapshot derived from existing bounded artifacts.

Artifact freshness:

- Current gate artifacts must carry this decision ID and round ID.
- Older sample artifacts with `missing`, `stale`, or unknown freshness may be referenced only as backlog/context, not as current evidence.
- Missing optional inventories may be reported as warnings/nonblocking status, but must not be mislabeled as current PASSED evidence.
- `control_plane_snapshot.json` must be generated fresh for this round.

Tool and artifact permissions:

- It is allowed to run bounded local project gate commands and pytest commands authorized by command-plan.
- It is allowed to read normal bounded project_state gate artifacts needed for snapshot synthesis.
- It is allowed to read `project_state/audits/*.md` only through existing audit inventory artifacts or bounded audit inventory command output.
- It is allowed to read `project_state/jobs/*.json` only through existing jobs inventory artifacts or bounded jobs inventory command output.
- It is not allowed to read full `project_state/rounds/`, full `solve_reports/`, or full `PROJECT_PROGRESS_LOG.txt`.
- It is not allowed to mutate GitHub or remote state unless the user separately instructs the executor to upload.
- Closeout is allowed because this is an engineering gate round and command-plan should use the appropriate `full` profile if source/gate code changes are made.

## 3. Do Not Do

Do not begin implementation if startup `git status --short` shows dirty source/test paths under `reverse_agent/` or `tests/`. Stop with `BLOCKED` instead.

Do not implement Web UI, AgentRunner, API Planner/Auditor, database, queue, scheduler, self-hosted runner automation, GitHub Actions mutation, automatic push, or reverse-solving.

Do not rewrite existing job inventory or audit inventory logic. Preserve `reverse_agent/project_jobs.py`, `reverse_agent/project_audits.py`, `tests/test_project_jobs.py`, and `tests/test_project_audits.py`.

Do not implement `round-manifest-inventory` in this round unless it is a minimal internal read path needed for the snapshot. The superseded `decision_20260629_round_manifest_inventory_gate_v1` is not the active task.

Do not mutate existing audit records under `project_state/audits/`. Treat them as read-only evidence.

Do not mutate archived round files under `project_state/rounds/` except the allowed current-round archive files generated by run-closeout for `round_20260629_control_plane_snapshot_gate_v1`.

Do not scan full `project_state/rounds/`; this round is a control-plane summary, not a historical archive crawler.

Do not use the snapshot as active execution authority. `project_state/decision_packet.md` remains the task contract, and command-plan remains the command execution authority.

Do not allow `control_plane_snapshot.json` to override `codex_execution_report.md`, `pytest_result.txt`, `execution_log.json`, or final-check.

Do not modify `current_state.json`, `task_packet.json`, `artifact_index.json`, `negative_results.json`, `.codex-skills/registry.json`, or docs prompts.

Do not scan full `solve_reports/`, run samples, execute runtime probes, or perform dynamic debugging.

Do not manually edit `pytest_result.txt` to hide failed command blocks.

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

Then inspect bounded implementation and gate evidence:

1. `reverse_agent/project_gate.py`
2. `tests/test_project_gate.py`
3. `reverse_agent/project_audits.py`
4. `tests/test_project_audits.py`
5. `reverse_agent/project_jobs.py`
6. `tests/test_project_jobs.py`
7. `project_state/gates/audit_inventory_result.json`
8. `project_state/gates/jobs_inventory_result.json` if present
9. `project_state/gates/final_gate_result.json`
10. `project_state/gates/run_closeout_result.json`
11. `project_state/gates/execution_log.json`
12. `project_state/gates/command_plan.json`
13. `project_state/gates/report_summary_synthesis.json`
14. `project_state/gates/round_baseline.json`
15. `project_state/gates/round_delta_summary.json`

If implementation creates a dedicated control-plane helper module or tests, inspect:

1. `reverse_agent/project_control_plane.py`
2. `tests/test_project_control_plane.py`
3. `project_state/gates/control_plane_snapshot.json`

Do not scan full `project_state/rounds/`, full `solve_reports/`, or full `PROJECT_PROGRESS_LOG.txt`.

## 5. Required Audit

The report must answer all items with concrete evidence and status `PASS`, `FAIL`, `BLOCKED`, or `NOT_APPLICABLE`:

1. Was startup source/test baseline clean before implementation?
2. Was the previous accepted audit inventory gate preserved?
3. Was the previous accepted jobs inventory gate preserved or safely treated as historical/nonblocking when stale?
4. What control-plane snapshot builder was added, and where is it implemented?
5. What `project_gate` CLI/gate surface was added for control-plane snapshot generation?
6. Does `control_plane_snapshot.json` exist, and does it carry current decision/round IDs?
7. Does the snapshot summarize active decision metadata, including decision ID, status, mainline, skill profiles, and consumed-by-report status?
8. Does the snapshot summarize execution status: report status, acceptance recommendation, pytest status, final gate status, closeout status, and close-round status?
9. Does the snapshot summarize inventory status for audit inventory, jobs inventory, and any optional round/archive inventory without mislabeling stale artifacts as current?
10. Does the snapshot expose runner readiness with default non-dispatch behavior unless explicit safe dispatch evidence exists?
11. Does the snapshot expose a stable UI summary with headline, next action, blocking reasons, and warnings?
12. Does the snapshot preserve task authority separation: decision is task contract, command-plan is command execution authority, snapshot is read-only status output?
13. Does the implementation avoid full `solve_reports/`, full `PROJECT_PROGRESS_LOG.txt`, full `project_state/rounds/`, Web/AgentRunner/DB/queue/scheduler, and remote mutation?
14. Did required pytest commands exit 0, and what are their pass counts?
15. Did `report_summary_fields_match_synthesis` pass with no diffs?
16. Did `execute_decision_contract` pass?
17. Did `run-closeout` exit 0, with `closeout_status: PASSED` and `close_round_result.close_status: CLOSED`?
18. Did `closeout_nested_failures_absent` pass with no active nested FAILED/FAIL states?
19. Did hybrid execution-log provenance remain valid and non-derived-only?
20. Were forbidden paths and preserve-only files avoided?

## 6. Implementation Scope

Allowed source/test changes:

- `reverse_agent/project_control_plane.py`
- `reverse_agent/project_gate.py`
- `tests/test_project_control_plane.py`
- `tests/test_project_gate.py`

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
- `project_state/rounds/round_20260629_control_plane_snapshot_gate_v1/*`

Required behavior:

1. Add a bounded control-plane snapshot builder.
2. The snapshot must include `schema_version`, `artifact_name`, `gate_name`, `gate_status`, current decision ID, current round ID, mainline, generated timestamp, and generated artifact path.
3. The snapshot must include `active_decision` fields: decision ID, round ID, status, mainline, skill profiles, and whether it is consumed by a matching report.
4. The snapshot must include `execution_status` fields: report ID, report status, acceptance recommendation, pytest status, final gate status, closeout status, close-round status, warnings, and blocking reasons.
5. The snapshot must include `inventory_status` fields for audit inventory and jobs inventory. If jobs inventory is stale for the current decision, report it as stale/historical/nonblocking rather than current PASSED evidence.
6. The snapshot may include optional round/archive inventory status if already available, but must not implement a full archive crawler.
7. The snapshot must include `runner_readiness` with default `can_dispatch_next_decision: false` unless explicit safe dispatch evidence exists.
8. The snapshot must include `ui_summary` with stable keys: `headline`, `next_action`, `blocking_reasons`, `warnings`.
9. Hard mismatches between decision/report/pytest/final gate IDs must produce a failing snapshot status or explicit blocking reason.
10. Missing optional inventory artifacts may produce warnings, but missing required report/pytest/final gate artifacts must fail or block.
11. Add `python -m reverse_agent.project_gate control-plane-snapshot --state-dir project_state` or an equivalent bounded CLI command.
12. Include control-plane snapshot evidence in final-check or equivalent gate evidence.
13. Keep the implementation small, deterministic, and read-only with respect to source evidence.
14. Do not create a database, queue, scheduler, Web UI, AgentRunner, API Planner/Auditor, or remote automation.

## 7. Tests

Record startup checks first:

```powershell
Set-Location F:\reverse-agent
Get-Location
Test-Path F:\reverse-agent
git rev-parse --show-toplevel
git status --short
```

Hard startup rule:

- If `git status --short` contains dirty source/test paths under `reverse_agent/` or `tests/`, stop with `BLOCKED` before modifying any source/test file.
- Existing dirty generated state artifacts are not sufficient to block, but they must be recorded in startup evidence.

Then run command-plan-authorized validation. At minimum include:

```powershell
python -m reverse_agent.project_gate command-plan --state-dir project_state
python -m reverse_agent.project_gate command-plan --state-dir project_state --json
python -m reverse_agent.project_gate preflight --state-dir project_state --allow-consumed
python -m reverse_agent.project_gate control-plane-snapshot --state-dir project_state
python -m reverse_agent.project_gate report-summary --state-dir project_state
python -m reverse_agent.project_gate execute-decision --state-dir project_state --round-id round_20260629_control_plane_snapshot_gate_v1 --mode execute
python -m pytest tests/test_project_control_plane.py -q
python -m pytest tests/test_project_gate.py tests/test_project_state.py tests/test_project_control_plane.py -q
python -m reverse_agent.project_gate execution-log --state-dir project_state
python -m reverse_agent.project_gate final-check --state-dir project_state
python -m reverse_agent.project_gate run-closeout --state-dir project_state --round-id round_20260629_control_plane_snapshot_gate_v1
python -m reverse_agent.project_gate final-check --state-dir project_state
```

The command-plan-authorized set is authoritative. If this Tests section conflicts with command-plan, command-plan controls, except it must not override startup-first ordering, clean source/test baseline, pytest summary consistency, control-plane snapshot evidence, report-summary convergence, execute-decision contract, hybrid provenance preservation, or closeout consistency.

Write all top-level commands and exit codes to `project_state/pytest_result.txt`.

## 8. Stop Conditions

Stop immediately and report `BLOCKED` if:

- startup checks do not confirm `F:\reverse-agent` and repository root;
- startup `git status --short` shows dirty source/test files under `reverse_agent/` or `tests/`;
- decision_meta is invalid;
- status is not APPROVED;
- mainline is invalid;
- skill profiles do not match active registry entries;
- command-plan is missing, failed, or unsafe;
- implementation requires mutating existing audit records;
- implementation requires mutating historical round archives outside the current round archive generated by closeout;
- implementation requires modifying preserve-only job, audit inventory, or round inventory files;
- implementation requires forbidden path mutation;
- implementation requires Web UI, AgentRunner, external dispatch, database, queue, scheduler, automatic remote writes, GitHub Actions mutation, or sample-solving work.

Stop with `REWORK_REQUIRED` if:

- any required pytest command exits nonzero;
- `pytest_result_summary.status` contradicts recorded command-block exit codes;
- startup source/test dirty baseline is ignored and implementation proceeds;
- control-plane snapshot gate command or artifact is missing;
- control-plane snapshot artifact is stale or missing current decision/round IDs;
- hard ID mismatches are silently accepted;
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
