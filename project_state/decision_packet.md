```json decision_meta
{
  "schema_version": 1,
  "decision_id": "decision_20260629_round_manifest_inventory_gate_v1",
  "round_id": "round_20260629_round_manifest_inventory_gate_v1",
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
  "phase_label": "phase_2_16_round_manifest_inventory_gate",
  "primary_goal": "Expose project_state/rounds/*/round_manifest.json records through a bounded read-only project_gate round manifest inventory gate artifact.",
  "command_plan_authority_required": true,
  "accepted_requires_clean_source_test_start": true,
  "accepted_requires_round_manifest_inventory_gate_artifact": true,
  "accepted_requires_existing_round_archives_preserved": true,
  "accepted_requires_no_remote_mutation": true,
  "accepted_requires_report_summary_fields_match_synthesis": true,
  "accepted_requires_execute_decision_contract_passed": true,
  "accepted_requires_run_closeout_exit_zero": true,
  "accepted_requires_closeout_nested_failures_absent": true,
  "allowed_source_files": [
    "reverse_agent/project_rounds.py",
    "reverse_agent/project_gate.py",
    "tests/test_project_rounds.py",
    "tests/test_project_gate.py"
  ],
  "preserve_only_files": [
    "reverse_agent/project_audits.py",
    "reverse_agent/project_jobs.py",
    "tests/test_project_audits.py",
    "tests/test_project_jobs.py",
    ".github/workflows/decision-preflight.yml",
    ".github/workflows/ci.yml",
    ".github/workflows/state-gate.yml"
  ],
  "preserve_only_audit_records": [
    "project_state/audits/audit_20260629_rework_required_audit_inventory_gate.md",
    "project_state/audits/audit_20260629_rework_required_clean_baseline_jobs_inventory_gate.md"
  ],
  "allowed_new_gate_artifacts": [
    "project_state/gates/round_manifest_inventory_result.json"
  ],
  "allowed_round_manifest_reads": [
    "project_state/rounds/*/round_manifest.json"
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

Implement Round Manifest Inventory Gate v1.

The previous accepted round completed Audit Inventory Gate v1 and made `project_state/audits/*.md` visible as bounded gate evidence. The next small engineering step is to apply the same pattern to closed round manifests: keep archived round directories as immutable evidence, but expose their `round_manifest.json` files through a current, bounded, read-only gate artifact.

Goal:

1. Preserve existing round archives under `project_state/rounds/` as immutable evidence for this round.
2. Add a bounded read-only round manifest inventory validator for `project_state/rounds/*/round_manifest.json`.
3. Expose that validator through `project_gate` as a `round-manifest-inventory` CLI/gate command.
4. Generate `project_state/gates/round_manifest_inventory_result.json` as current evidence for this decision/round.
5. Add tests proving valid manifests are detected, missing/invalid manifest files are reported, duplicate round IDs are rejected, stale or mismatched decision/report IDs are counted but not silently accepted, and archived round files are not mutated.
6. Integrate round manifest inventory evidence into final-check or an equivalent gate evidence path.

Preferred final outcome:

- `status: SUCCESS`.
- `acceptance_recommendation: ACCEPTED`.
- `limitations` null or absent.
- startup source/test baseline is clean.
- `round_manifest_inventory_result.json` exists, is current, and records the current decision/round IDs.
- existing round archives and audit records remain unchanged.
- `execution_log.json.source` remains hybrid/direct, not derived-only.
- `report_summary_fields_match_synthesis`, `execute_decision_contract`, `run-closeout`, and `closeout_nested_failures_absent` all pass.

This is an engineering branch round. It must not implement Web UI, AgentRunner, API Planner/Auditor, database, queue, scheduler, self-hosted runner automation, automatic remote writes, GitHub Actions mutation, or reverse-solving.

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

Current state summary:

- `current_state.json` remains a sample-state snapshot for `samplereverse` with missing runtime/sample artifacts.
- This round does not claim sample-solving progress and must not use sample-state gaps as current solved evidence.
- `artifact_index.json` lists many sample artifacts as `missing`; those are non-blocking for this engineering branch because no reverse-solving evidence is being claimed.

Negative results:

- `negative_results.json` blocks old sample_solver blind search, only increasing beam/budget, using `compare_semantics_agree=false` candidates as primary frontier, committing full `solve_reports`, and repeating old bounded runtime branches.
- This round must not perform reverse-solving, runtime probing, dynamic debugging, sample execution, or full `solve_reports` scans.

Existing capability to build on:

- `project_gate` already exposes preflight, command-plan, jobs-inventory, audit-inventory, report-summary, execute-decision, execution-log, final-check, and run-closeout gate surfaces.
- `project_jobs` and `project_audits` provide precedents for small inventory validators plus project_gate wrappers and tests.
- final-check already inspects the active round manifest for report/archive consistency; this round must not duplicate that check blindly. It should add a bounded inventory view over all archived `round_manifest.json` files and aggregate their basic health.

Artifact freshness:

- Current gate artifacts must carry this decision ID and round ID.
- Older sample artifacts with `missing`, `stale`, or unknown freshness may be referenced only as backlog/context, not as current evidence.
- Existing round manifests are historical archive evidence. The new `round_manifest_inventory_result.json` must be generated fresh for this round and must clearly distinguish current decision/round IDs from historical archived round IDs.

Tool and artifact permissions:

- It is allowed to run bounded local project gate commands and pytest commands authorized by command-plan.
- It is allowed to read `project_state/rounds/*/round_manifest.json` only. Do not scan or parse full archived round report bodies, full archived pytest logs, or arbitrary files under `project_state/rounds/`.
- It is allowed to read normal bounded project_state gate artifacts required by command-plan/final-check.
- It is not allowed to read full `solve_reports/` or full `PROJECT_PROGRESS_LOG.txt`.
- It is not allowed to mutate GitHub or remote state unless the user separately instructs the executor to upload.
- Closeout is allowed because this is an engineering gate round and command-plan should use the appropriate `full` profile if source/gate code changes are made.

## 3. Do Not Do

Do not begin implementation if startup `git status --short` shows dirty source/test paths under `reverse_agent/` or `tests/`. Stop with `BLOCKED` instead.

Do not rewrite existing job inventory or audit inventory logic. Preserve `reverse_agent/project_jobs.py`, `reverse_agent/project_audits.py`, `tests/test_project_jobs.py`, and `tests/test_project_audits.py`.

Do not mutate existing audit records under `project_state/audits/`. Treat them as read-only evidence for this round.

Do not mutate archived round files under `project_state/rounds/` except the allowed current-round archive files generated by run-closeout for `round_20260629_round_manifest_inventory_gate_v1`.

Do not scan full `project_state/rounds/`; only read `project_state/rounds/*/round_manifest.json` and the current round archive files generated by closeout.

Do not use round manifests as active execution authority. `project_state/decision_packet.md` remains the task contract, and command-plan remains the command execution authority.

Do not allow round manifests to override `codex_execution_report.md`, `pytest_result.txt`, `execution_log.json`, or final-check.

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
3. `reverse_agent/project_audits.py`
4. `tests/test_project_audits.py`
5. `reverse_agent/project_jobs.py`
6. `tests/test_project_jobs.py`
7. `project_state/gates/audit_inventory_result.json`
8. `project_state/gates/final_gate_result.json`
9. `project_state/gates/run_closeout_result.json`
10. `project_state/gates/execution_log.json`
11. `project_state/gates/command_plan.json`
12. `project_state/gates/report_summary_synthesis.json`
13. `project_state/gates/round_baseline.json`
14. `project_state/gates/round_delta_summary.json`
15. `project_state/rounds/*/round_manifest.json`

If implementation creates a dedicated round helper module or tests, inspect:

1. `reverse_agent/project_rounds.py`
2. `tests/test_project_rounds.py`
3. `project_state/gates/round_manifest_inventory_result.json`

Do not scan full `project_state/rounds/`, full `solve_reports/`, or full `PROJECT_PROGRESS_LOG.txt`.

## 5. Required Audit

The report must answer all items with concrete evidence and status `PASS`, `FAIL`, `BLOCKED`, or `NOT_APPLICABLE`:

1. Was startup source/test baseline clean before implementation?
2. Was the previous accepted audit inventory gate preserved?
3. Was the previous accepted jobs inventory gate preserved?
4. What round manifest inventory validator was added, and where is it implemented?
5. What `project_gate` CLI/gate surface was added for round manifest inventory validation?
6. Does `round_manifest_inventory_result.json` exist, and does it carry current decision/round IDs?
7. Does round manifest inventory report manifest count, validated paths, duplicate round ID errors, invalid file errors, status counts, and archive path counts?
8. Does round manifest inventory read only `project_state/rounds/*/round_manifest.json`, not full archived reports or pytest logs?
9. Does the validator handle a missing `project_state/rounds` directory as valid zero-manifest evidence in isolated tests?
10. Are invalid or malformed manifest files reported without mutating archive files?
11. Are duplicate archived `round_id` values rejected or reported?
12. Are existing round archives preserved byte-for-byte or at least not modified in git diff outside the current round archive generated by closeout?
13. Is round manifest inventory evidence included in final-check or an equivalent gate evidence path?
14. Did required pytest commands exit 0, and what are their pass counts?
15. Did `report_summary_fields_match_synthesis` pass with no diffs?
16. Did `execute_decision_contract` pass?
17. Did `run-closeout` exit 0, with `closeout_status: PASSED` and `close_round_result.close_status: CLOSED`?
18. Did `closeout_nested_failures_absent` pass with no active nested FAILED/FAIL states?
19. Did hybrid execution-log provenance remain valid and non-derived-only?
20. Were forbidden paths, full solve_reports scans, reverse-solving, Web/AgentRunner/DB/queue/scheduler scope, and remote mutation avoided?

## 6. Implementation Scope

Allowed source/test changes:

- `reverse_agent/project_rounds.py`
- `reverse_agent/project_gate.py`
- `tests/test_project_rounds.py`
- `tests/test_project_gate.py`

Preserve-only source/test files:

- `reverse_agent/project_audits.py`
- `reverse_agent/project_jobs.py`
- `tests/test_project_audits.py`
- `tests/test_project_jobs.py`

Preserve-only audit records:

- `project_state/audits/audit_20260629_rework_required_audit_inventory_gate.md`
- `project_state/audits/audit_20260629_rework_required_clean_baseline_jobs_inventory_gate.md`

Allowed generated or updated state artifacts:

- `project_state/gates/round_manifest_inventory_result.json`
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
- `project_state/rounds/round_20260629_round_manifest_inventory_gate_v1/*`

Allowed read-only historical round inputs:

- `project_state/rounds/*/round_manifest.json`

Required behavior:

1. Add a bounded round manifest inventory validator for `project_state/rounds/*/round_manifest.json`.
2. Each valid manifest should expose, at minimum, `round_id`, `decision_id`, `report_id` if present, round status or close status if present, and archive paths if present.
3. Missing optional manifest fields may be reported as warnings, but required identity fields must not be silently accepted if absent.
4. Missing `project_state/rounds` directory must be valid in isolated tests with `manifest_count: 0` and `gate_status: PASSED`.
5. Invalid JSON or malformed manifests must be reported in `invalid_file_errors` without changing those files.
6. Duplicate archived `round_id` values must be rejected or reported in `duplicate_round_id_errors`.
7. The artifact must include schema version, artifact name, gate name, gate status, current decision ID, current round ID, manifest count, status/close-status counts, validated paths, duplicate round ID errors, invalid file errors, warnings, and generated artifact path.
8. Add `python -m reverse_agent.project_gate round-manifest-inventory --state-dir project_state` or an equivalent bounded CLI command.
9. Include round manifest inventory evidence in final-check or equivalent gate evidence.
10. Keep the implementation small, deterministic, and read-only with respect to historical round archives.
11. Do not create a database, queue, scheduler, Web UI, AgentRunner, API Planner/Auditor, or remote automation.

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
python -m reverse_agent.project_gate round-manifest-inventory --state-dir project_state
python -m reverse_agent.project_gate report-summary --state-dir project_state
python -m reverse_agent.project_gate execute-decision --state-dir project_state --round-id round_20260629_round_manifest_inventory_gate_v1 --mode execute
python -m pytest tests/test_project_rounds.py -q
python -m pytest tests/test_project_gate.py tests/test_project_state.py tests/test_project_rounds.py -q
python -m reverse_agent.project_gate execution-log --state-dir project_state
python -m reverse_agent.project_gate final-check --state-dir project_state
python -m reverse_agent.project_gate run-closeout --state-dir project_state --round-id round_20260629_round_manifest_inventory_gate_v1
python -m reverse_agent.project_gate final-check --state-dir project_state
```

The command-plan-authorized set is authoritative. If this Tests section conflicts with command-plan, command-plan controls, except it must not override startup-first ordering, clean source/test baseline, pytest summary consistency, round manifest inventory gate evidence, report-summary convergence, execute-decision contract, hybrid provenance preservation, or closeout consistency.

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
- implementation requires modifying preserve-only job or audit inventory files;
- implementation requires forbidden path mutation;
- implementation requires Web UI, AgentRunner, external dispatch, database, queue, scheduler, automatic remote writes, GitHub Actions mutation, or sample-solving work.

Stop with `REWORK_REQUIRED` if:

- any required pytest command exits nonzero;
- `pytest_result_summary.status` contradicts recorded command-block exit codes;
- startup source/test dirty baseline is ignored and implementation proceeds;
- round manifest inventory gate command or artifact is missing;
- round manifest inventory artifact is stale or missing current decision/round IDs;
- invalid manifests or duplicate round IDs are silently accepted;
- historical round archives are modified outside the current round archive generated by closeout;
- round manifest inventory evidence is not included in final-check or equivalent gate evidence;
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
