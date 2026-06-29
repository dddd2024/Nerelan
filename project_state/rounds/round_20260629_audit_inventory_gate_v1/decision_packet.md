```json decision_meta
{
  "schema_version": 1,
  "decision_id": "decision_20260629_audit_inventory_gate_v1",
  "round_id": "round_20260629_audit_inventory_gate_v1",
  "based_on_state_build_id": "state_20260618_134029_d6bd033d2532",
  "based_on_state_digest": "d6bd033d25324345cfd8ada0ac65db42bc86eb5017f3ffc92906fcd8b71cacb5",
  "status": "APPROVED",
  "mainline": "engineering_branch",
  "skill_profiles": ["reverse-agent-iteration@v2"]
}
```

```json decision_contract
{
  "previous_decision_id": "decision_20260628_clean_baseline_jobs_inventory_gate_v1",
  "previous_round_id": "round_20260628_clean_baseline_jobs_inventory_gate_v1",
  "previous_audit_outcome": "ACCEPTED",
  "phase_label": "phase_2_15_audit_inventory_gate",
  "primary_goal": "Expose project_state/audits audit records through a bounded read-only project_gate audit inventory gate artifact.",
  "command_plan_authority_required": true,
  "accepted_requires_clean_source_test_start": true,
  "accepted_requires_audit_inventory_gate_artifact": true,
  "accepted_requires_existing_audit_records_preserved": true,
  "accepted_requires_no_remote_mutation": true,
  "accepted_requires_report_summary_fields_match_synthesis": true,
  "accepted_requires_execute_decision_contract_passed": true,
  "accepted_requires_run_closeout_exit_zero": true,
  "accepted_requires_closeout_nested_failures_absent": true,
  "allowed_source_files": [
    "reverse_agent/project_audits.py",
    "reverse_agent/project_gate.py",
    "tests/test_project_audits.py",
    "tests/test_project_gate.py"
  ],
  "preserve_only_files": [
    "reverse_agent/project_jobs.py",
    "tests/test_project_jobs.py",
    ".github/workflows/decision-preflight.yml",
    ".github/workflows/ci.yml",
    ".github/workflows/state-gate.yml"
  ],
  "preserve_only_audit_records": [
    "project_state/audits/audit_20260629_rework_required_clean_baseline_jobs_inventory_gate.md"
  ],
  "allowed_new_gate_artifacts": [
    "project_state/gates/audit_inventory_result.json"
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
    "project_state/audits/audit_20260629_rework_required_clean_baseline_jobs_inventory_gate.md"
  ]
}
```

# DECISION_PACKET

## 1. Goal

Implement Audit Inventory Gate v1.

The previous accepted round completed Clean Baseline Jobs Inventory Gate v1 and eliminated the `baseline_capture_order` limitation. The current repository now also contains at least one human/LLM audit record under `project_state/audits/`, but those records are not yet first-class gate evidence. This round makes audit records discoverable and auditable without changing the active task authority model.

Goal:

1. Preserve existing audit records under `project_state/audits/` as immutable evidence for this round.
2. Add a bounded read-only audit inventory validator for `project_state/audits/*.md`.
3. Expose that validator through `project_gate` as an `audit-inventory` CLI/gate command.
4. Generate `project_state/gates/audit_inventory_result.json` as current evidence for this decision/round.
5. Add tests proving valid audit records are detected, invalid summaries are reported, duplicate audit IDs are rejected, a missing audits directory is handled safely, and no audit record is mutated.
6. Integrate audit inventory evidence into final-check or an equivalent gate evidence path.

Preferred final outcome:

- `status: SUCCESS`.
- `acceptance_recommendation: ACCEPTED`.
- `limitations` null or absent.
- startup source/test baseline is clean.
- `audit_inventory_result.json` exists, is current, and records the current decision/round IDs.
- existing audit records remain unchanged.
- `execution_log.json.source` remains hybrid/direct, not derived-only.
- `report_summary_fields_match_synthesis`, `execute_decision_contract`, `run-closeout`, and `closeout_nested_failures_absent` all pass.

This is an engineering round. It must not implement Web UI, AgentRunner, API Planner/Auditor, database, queue, scheduler, self-hosted runner automation, automatic remote writes, GitHub Actions mutation, or reverse-solving.

## 2. Current Evidence

Mainline: `engineering_branch`.

The current task is controlled by `project_state/decision_packet.md`; `project_state/task_packet.json` remains non-authoritative background only. The task packet still describes older `samplereverse` missing evidence and must not drive this engineering round.

Accepted previous round:

- `decision_20260628_clean_baseline_jobs_inventory_gate_v1` / `round_20260628_clean_baseline_jobs_inventory_gate_v1` is accepted.
- `codex_execution_report.md` reports `status: SUCCESS` and `acceptance_recommendation: ACCEPTED`.
- `final_gate_result.json` reports `gate_status: PASSED`, no warnings, and no blocking reasons.
- `baseline_capture_order` is `PASS` with `capture_order_status: clean`.
- startup `git status --short` had no dirty `reverse_agent/` or `tests/` source/test paths.
- focused job tests passed with 19 tests.
- combined gate/state/jobs tests passed with 1269 tests.
- `jobs_inventory_result.json` is current, non-dispatching, and validates one DRAFT job.
- `execution_log.json.source` remained `hybrid_from_pytest_result_command_plan_and_run_closeout_execution_log`.
- `run-closeout` passed and close-round status was `CLOSED`.

Current state summary:

- `current_state.json` remains a sample-state snapshot for `samplereverse` with many missing runtime/sample artifacts.
- This round does not claim sample-solving progress and must not use sample-state gaps as current solved evidence.
- `artifact_index.json` lists many sample artifacts as `missing`; those are non-blocking for this engineering branch because no reverse-solving evidence is being claimed.

Negative results:

- `negative_results.json` blocks old sample_solver blind search, only increasing beam/budget, using `compare_semantics_agree=false` candidates as primary frontier, committing full `solve_reports`, and repeating old bounded runtime branches.
- This round must not perform reverse-solving, runtime probing, dynamic debugging, sample execution, or full `solve_reports` scans.

Existing capability to build on:

- `project_gate` already exposes preflight, command-plan, jobs-inventory, report-summary, execute-decision, execution-log, final-check, and run-closeout gate surfaces.
- `project_jobs` already provides a precedent for a small inventory validator plus a project_gate wrapper and tests.
- No existing audit-inventory gate was found in the current repository context; do not duplicate unrelated job inventory behavior, but reuse its bounded read-only pattern.

Artifact freshness:

- Current gate artifacts must carry this decision ID and round ID.
- Existing older sample artifacts with `missing`, `stale`, or unknown freshness may be referenced only as backlog/context, not as current evidence.
- The audit inventory artifact must be generated fresh for this round.

Tool and artifact permissions:

- It is allowed to run bounded local project gate commands and pytest commands authorized by command-plan.
- It is allowed to read `project_state/audits/*.md` and normal bounded project_state gate artifacts.
- It is not allowed to read full `solve_reports/` or full `PROJECT_PROGRESS_LOG.txt`.
- It is not allowed to mutate GitHub or remote state unless the user separately instructs the executor to upload.
- Closeout is allowed because this is an engineering gate round and command-plan should use the appropriate `full` profile if source/gate code changes are made.

## 3. Do Not Do

Do not begin implementation if startup `git status --short` shows dirty source/test paths under `reverse_agent/` or `tests/`. Stop with `BLOCKED` instead.

Do not rewrite existing job inventory logic. Preserve `reverse_agent/project_jobs.py`, `tests/test_project_jobs.py`, and the existing DRAFT job contract behavior.

Do not mutate existing audit record files under `project_state/audits/`. Treat them as read-only evidence for this round.

Do not use audit records as active execution authority. `project_state/decision_packet.md` remains the task authority.

Do not allow audit records to override `codex_execution_report.md`, `pytest_result.txt`, `execution_log.json`, or final-check.

Do not introduce Web UI, AgentRunner, API Planner/Auditor, database, queue, scheduler, self-hosted runner automation, GitHub Actions mutation, automatic push, or reverse-solving.

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
3. `reverse_agent/project_jobs.py`
4. `tests/test_project_jobs.py`
5. `project_state/audits/audit_20260629_rework_required_clean_baseline_jobs_inventory_gate.md`
6. `project_state/gates/final_gate_result.json`
7. `project_state/gates/run_closeout_result.json`
8. `project_state/gates/execution_log.json`
9. `project_state/gates/command_plan.json`
10. `project_state/gates/report_summary_synthesis.json`
11. `project_state/gates/round_baseline.json`
12. `project_state/gates/round_delta_summary.json`

If implementation creates a dedicated audit helper module or tests, inspect:

1. `reverse_agent/project_audits.py`
2. `tests/test_project_audits.py`
3. `project_state/gates/audit_inventory_result.json`

Do not scan full `project_state/rounds/`, full `solve_reports/`, or full `PROJECT_PROGRESS_LOG.txt`.

## 5. Required Audit

The report must answer all items with concrete evidence and status `PASS`, `FAIL`, `BLOCKED`, or `NOT_APPLICABLE`:

1. Was startup source/test baseline clean before implementation?
2. Was the previous accepted jobs inventory gate preserved?
3. What audit inventory validator was added, and where is it implemented?
4. What `project_gate` CLI/gate surface was added for audit inventory validation?
5. Does `audit_inventory_result.json` exist, and does it carry current decision/round IDs?
6. Does audit inventory report audit count, validated paths, duplicate audit ID errors, invalid file errors, and allowed outcome counts?
7. Does audit inventory handle a missing `project_state/audits` directory as valid zero-audit evidence?
8. Are invalid `audit_summary` blocks reported without mutating audit files?
9. Are duplicate audit IDs rejected?
10. Are existing audit record files preserved byte-for-byte or at least not modified in git diff?
11. Is audit inventory evidence included in final-check or an equivalent gate evidence path?
12. Did required pytest commands exit 0, and what are their pass counts?
13. Did `report_summary_fields_match_synthesis` pass with no diffs?
14. Did `execute_decision_contract` pass?
15. Did `run-closeout` exit 0, with `closeout_status: PASSED` and `close_round_result.close_status: CLOSED`?
16. Did `closeout_nested_failures_absent` pass with no active nested FAILED/FAIL states?
17. Did hybrid execution-log provenance remain valid and non-derived-only?
18. Were forbidden paths, full solve_reports scans, reverse-solving, Web/AgentRunner/DB/queue/scheduler scope, and remote mutation avoided?

## 6. Implementation Scope

Allowed source/test changes:

- `reverse_agent/project_audits.py`
- `reverse_agent/project_gate.py`
- `tests/test_project_audits.py`
- `tests/test_project_gate.py`

Preserve-only source/test files:

- `reverse_agent/project_jobs.py`
- `tests/test_project_jobs.py`

Preserve-only existing audit record:

- `project_state/audits/audit_20260629_rework_required_clean_baseline_jobs_inventory_gate.md`

Allowed generated or updated state artifacts:

- `project_state/gates/audit_inventory_result.json`
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
- `project_state/rounds/round_20260629_audit_inventory_gate_v1/*`

Required behavior:

1. Add a bounded audit inventory validator for Markdown files under `project_state/audits/`.
2. Each valid audit record should contain a fenced JSON block named `audit_summary`.
3. Required audit summary fields: `schema_version`, `audit_id`, `audited_decision_id`, `audited_round_id`, `outcome`, and `mainline`.
4. Optional but recognized fields should include `audited_report_id`, `created_by`, `created_at_local`, and `remote_mutation_scope`.
5. Allowed audit outcomes: `ACCEPTED`, `ACCEPTED_WITH_LIMITATIONS`, `REWORK_REQUIRED`, `BLOCKED`.
6. Missing audits directory must be valid with `audit_count: 0` and `gate_status: PASSED`.
7. Invalid Markdown files must be reported in `invalid_file_errors` without changing those files.
8. Duplicate `audit_id` values must be rejected.
9. The gate artifact must include schema version, artifact name, gate name, gate status, current decision ID, current round ID, audit count, outcome counts, validated paths, duplicate audit ID errors, invalid file errors, warnings, and generated artifact path.
10. Add `python -m reverse_agent.project_gate audit-inventory --state-dir project_state` or an equivalent bounded CLI command.
11. Include audit inventory evidence in final-check or equivalent gate evidence.
12. Keep the implementation small, deterministic, and read-only with respect to audit records.
13. Do not create a database, queue, scheduler, Web UI, AgentRunner, API Planner/Auditor, or remote automation.

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
python -m reverse_agent.project_gate audit-inventory --state-dir project_state
python -m reverse_agent.project_gate report-summary --state-dir project_state
python -m reverse_agent.project_gate execute-decision --state-dir project_state --round-id round_20260629_audit_inventory_gate_v1 --mode execute
python -m pytest tests/test_project_audits.py -q
python -m pytest tests/test_project_gate.py tests/test_project_state.py tests/test_project_audits.py -q
python -m reverse_agent.project_gate execution-log --state-dir project_state
python -m reverse_agent.project_gate final-check --state-dir project_state
python -m reverse_agent.project_gate run-closeout --state-dir project_state --round-id round_20260629_audit_inventory_gate_v1
python -m reverse_agent.project_gate final-check --state-dir project_state
```

The command-plan-authorized set is authoritative. If this Tests section conflicts with command-plan, command-plan controls, except it must not override startup-first ordering, clean source/test baseline, pytest summary consistency, audit inventory gate evidence, report-summary convergence, execute-decision contract, hybrid provenance preservation, or closeout consistency.

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
- implementation requires modifying preserve-only job files;
- implementation requires forbidden path mutation;
- implementation requires Web UI, AgentRunner, external dispatch, database, queue, scheduler, automatic remote writes, GitHub Actions mutation, or sample-solving work.

Stop with `REWORK_REQUIRED` if:

- any required pytest command exits nonzero;
- `pytest_result_summary.status` contradicts recorded command-block exit codes;
- startup source/test dirty baseline is ignored and implementation proceeds;
- audit inventory gate command or artifact is missing;
- audit inventory artifact is stale or missing current decision/round IDs;
- invalid audit files or duplicate audit IDs are silently accepted;
- existing audit records are modified;
- audit inventory evidence is not included in final-check or equivalent gate evidence;
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
