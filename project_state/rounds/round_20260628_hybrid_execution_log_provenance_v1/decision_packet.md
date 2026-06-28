```json decision_meta
{
  "schema_version": 1,
  "decision_id": "decision_20260628_hybrid_execution_log_provenance_v1",
  "round_id": "round_20260628_hybrid_execution_log_provenance_v1",
  "based_on_state_build_id": "state_20260618_134029_d6bd033d2532",
  "based_on_state_digest": "d6bd033d25324345cfd8ada0ac65db42bc86eb5017f3ffc92906fcd8b71cacb5",
  "status": "APPROVED",
  "mainline": "engineering_branch",
  "skill_profiles": ["reverse-agent-iteration@v2"]
}
```

```json decision_contract
{
  "previous_decision_id": "decision_20260628_pytest_summary_and_closeout_consistency_rework_v1",
  "previous_round_id": "round_20260628_pytest_summary_and_closeout_consistency_rework_v1",
  "previous_audit_outcome": "ACCEPTED_WITH_LIMITATIONS",
  "phase_label": "phase_2_10_hybrid_execution_log_provenance",
  "primary_goal": "Remove the remaining derived-only execution_log limitation by upgrading execution_log provenance to a mechanically checked hybrid/direct model without introducing AgentRunner or external dispatch.",
  "command_plan_authority_required": true,
  "accepted_requires_execution_log_not_derived_only": true,
  "accepted_requires_no_derived_log_limitation_for_pure_accepted": true,
  "accepted_requires_pytest_summary_matches_command_blocks": true,
  "accepted_requires_closeout_passed": true,
  "allowed_source_files": ["reverse_agent/project_gate.py", "tests/test_project_gate.py"],
  "preserve_only_files": [
    ".github/workflows/decision-preflight.yml",
    "reverse_agent/project_jobs.py",
    "tests/test_project_jobs.py",
    ".github/workflows/ci.yml",
    ".github/workflows/state-gate.yml"
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

Implement Hybrid Execution Log Provenance v1.

The previous round was accepted with limitations. The only active limitation was that `project_state/gates/execution_log.json` still had `source: derived_from_pytest_result_and_command_plan`. This round should remove that limitation by upgrading execution-log provenance to a bounded, mechanically checked hybrid or direct model.

This is an engineering round. It must not add AgentRunner, external agent dispatch, web UI, database, queue, scheduler, automatic remote writes, or sample-solving. The goal is provenance hardening inside the existing `project_gate` chain.

Final preferred outcome:

1. `execution_log.json.source` is no longer `derived_from_pytest_result_and_command_plan`.
2. `execution_log.json` includes explicit provenance metadata sufficient for final-check to classify it as `hybrid` or `direct`.
3. If classified as `hybrid`, the artifact must state what evidence was combined, such as pytest transcript command blocks, command-plan artifact/stdout parity, run-closeout execution log, command exit codes, current decision/report IDs, and content hashes.
4. final-check must verify that the hybrid/direct provenance is current, internally consistent, and tied to the current round.
5. If hybrid/direct provenance is valid, `status` may be `SUCCESS`, `acceptance_recommendation` may be pure `ACCEPTED`, and `limitations` may be null.
6. If hybrid/direct provenance cannot be implemented safely, keep `ACCEPTED_WITH_LIMITATIONS` with the derived-log limitation and report why; do not fake direct capture.
7. Preserve the existing correct startup order, `startup_command_position_order`, pytest-summary consistency, reverse_solving strict freshness semantics, report-summary synthesis consistency, and run-closeout convergence.

## 2. Current Evidence

Mainline: `engineering_branch`.

The previous accepted round was `decision_20260628_pytest_summary_and_closeout_consistency_rework_v1`, with audit outcome `ACCEPTED_WITH_LIMITATIONS`.

Accepted evidence from that round:

- `codex_report_summary.status` was `SUCCESS`.
- `acceptance_recommendation` was `ACCEPTED_WITH_LIMITATIONS`.
- The only active limitation was `execution_log.json is derived_from_pytest_result_and_command_plan; not direct or hybrid capture`.
- Both required pytest commands exited 0.
- `pytest_result_summary.status` matched command-block exits.
- final-check completed as `PASSED_WITH_LIMITATIONS` with no blocking reasons or warnings.
- run-closeout completed as `PASSED`.
- `startup_command_position_order` remained PASS.
- `baseline_capture_order` was PASS.
- report-summary synthesis matched the live reports.
- reverse_solving strict freshness regression was fixed.

`task_packet.json` remains non-authoritative background state and states that `decision_packet` controls the current round. Do not execute `task_packet.task` as authority.

`current_state.json` and `artifact_index.json` still describe sample-state and missing historical sample artifacts. They are non-blocking for this engineering round because no sample-solving evidence is claimed.

`negative_results.json` contains reverse-solving prohibitions. This round must not repeat old sample_solver blind search, beam/budget expansion, compare_semantics_agree=false primary frontier usage, full solve_reports commits, or repeated runtime evidence directions.

Existing accepted work to preserve:

- `decision-preflight.yml` bounded read-only workflow;
- `project_jobs.py` minimal non-dispatching job schema validator;
- `tests/test_project_jobs.py` coverage;
- neutral-primary report semantics and legacy aliases;
- command-plan, pytest_result, execution-log, report-summary, final-check, and run-closeout chain;
- startup-position order validation;
- limited-acceptance policy when provenance remains derived-only.

## 3. Do Not Do

Do not claim direct capture unless there is actual direct or hybrid provenance evidence and final-check verifies it.

Do not remove the derived-log limitation by only editing report prose.

Do not weaken status-policy checks that block pure `ACCEPTED` for derived-only execution logs.

Do not break reverse_solving strict freshness semantics.

Do not regress startup ordering, pytest summary consistency, report-summary synthesis, final-check, or run-closeout.

Do not redesign `decision-preflight.yml`, `project_jobs.py`, or `tests/test_project_jobs.py`.

Do not add Web UI, AgentRunner, external runner dispatch, database, queue, scheduler, automatic remote writes, GitHub Actions mutation, or sample-solving work.

Do not scan full `solve_reports/` or execute reverse samples.

Do not modify forbidden paths listed in `decision_contract`.

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

Then inspect only bounded implementation and gate evidence:

1. `reverse_agent/project_gate.py`
2. `tests/test_project_gate.py`
3. `project_state/gates/execution_log.json`
4. `project_state/gates/run_closeout_execution_log.json`
5. `project_state/gates/run_closeout_result.json`
6. `project_state/gates/command_plan.json`
7. `project_state/gates/report_summary_synthesis.json`
8. `project_state/gates/final_gate_result.json`
9. `project_state/gates/execute_decision_result.json`
10. `project_state/gates/round_baseline.json`
11. `project_state/gates/round_delta_summary.json`
12. preservation-only files named in `decision_contract.preserve_only_files` only to confirm they were not redesigned.

Do not scan full `project_state/rounds/`, full `solve_reports/`, or full `PROJECT_PROGRESS_LOG.txt`.

## 5. Required Audit

The report must answer all items with concrete evidence and status `PASS`, `FAIL`, `BLOCKED`, or `NOT_APPLICABLE`:

1. What is the final `execution_log.json.source` value?
2. Is the execution log direct, hybrid, or still derived-only?
3. If hybrid, what evidence sources are combined, and where are their content hashes or IDs recorded?
4. Which final-check rule verifies that hybrid/direct provenance is current and consistent with pytest_result, command_plan, run_closeout_execution_log, decision_id, round_id, and report_id?
5. Does status policy still block pure `ACCEPTED` when execution_log is derived-only?
6. If the limitation is removed, do `codex_report_summary`, `execution_report_summary`, auto summaries, synthesis, and final-check all agree on `SUCCESS / ACCEPTED` with null or absent limitations?
7. If the limitation remains, do all reports consistently use `SUCCESS / ACCEPTED_WITH_LIMITATIONS` with explicit limitation text?
8. Did both required pytest commands exit 0, and what are their pass counts?
9. Did final-check and run-closeout pass?
10. Were startup order, `startup_command_position_order`, pytest-summary consistency, reverse_solving strict freshness semantics, and preservation-only files kept intact?

## 6. Implementation Scope

Allowed source changes:

- `reverse_agent/project_gate.py`
- `tests/test_project_gate.py`

Allowed generated or updated state artifacts:

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
- `project_state/rounds/round_20260628_hybrid_execution_log_provenance_v1/*`

Required behavior:

1. Add or refine execution-log provenance classification so final-check distinguishes `derived`, `hybrid`, and `direct`.
2. A hybrid classification must be mechanically supported by current artifacts, not report prose.
3. Include enough provenance metadata in `execution_log.json` for final-check to validate current decision/round/report IDs, command-plan parity, pytest transcript command blocks and exit codes, run-closeout execution evidence where applicable, and content hashes or equivalent stable checks.
4. Keep derived-only execution logs limited. Pure `ACCEPTED` is allowed only for verified hybrid/direct provenance.
5. Preserve existing status-policy behavior for `ACCEPTED_WITH_LIMITATIONS` when provenance remains derived-only.
6. Preserve all previous passing gate behavior and avoid broad refactors.

## 7. Tests

Record startup checks first:

```powershell
Set-Location F:\reverse-agent
Get-Location
Test-Path F:\reverse-agent
git rev-parse --show-toplevel
git status --short
```

Then run command-plan-authorized validation. At minimum include:

```powershell
python -m reverse_agent.project_gate command-plan --state-dir project_state
python -m reverse_agent.project_gate command-plan --state-dir project_state --json
python -m reverse_agent.project_gate preflight --state-dir project_state --allow-consumed
python -m reverse_agent.project_gate report-summary --state-dir project_state
python -m reverse_agent.project_gate final-check --state-dir project_state
python -m reverse_agent.project_gate execute-decision --state-dir project_state --round-id round_20260628_hybrid_execution_log_provenance_v1 --mode execute
python -m pytest tests/test_project_gate.py tests/test_project_state.py -q
python -m pytest tests/test_project_gate.py tests/test_project_state.py tests/test_project_jobs.py -q
python -m reverse_agent.project_gate execution-log --state-dir project_state
python -m reverse_agent.project_gate run-closeout --state-dir project_state --round-id round_20260628_hybrid_execution_log_provenance_v1
python -m reverse_agent.project_gate final-check --state-dir project_state
```

The command-plan-authorized set is authoritative, but it must not override startup-first ordering, pytest summary consistency, provenance classification, or closeout consistency requirements.

Write all top-level commands and exit codes to `project_state/pytest_result.txt`.

## 8. Stop Conditions

Stop immediately and report `BLOCKED` if:

- startup checks do not confirm `F:\reverse-agent` and repository root;
- decision_meta is invalid;
- status is not APPROVED;
- mainline is invalid;
- skill profiles do not match active registry entries;
- command-plan is missing, failed, or unsafe;
- implementing hybrid/direct provenance requires forbidden path mutation;
- implementation requires Web UI, AgentRunner, external runner dispatch, database, queue, scheduler, automatic remote writes, GitHub Actions mutation, or sample-solving work.

Stop with `REWORK_REQUIRED` if:

- execution_log remains derived-only while report/final-check claims pure `ACCEPTED`;
- execution_log claims hybrid/direct without final-check-verifiable evidence;
- report summaries, auto summaries, synthesis, and final-check disagree on acceptance recommendation or limitations;
- any required pytest command exits nonzero;
- `pytest_result_summary.status` contradicts recorded command-block exit codes;
- final-check fails unexpectedly;
- run-closeout fails;
- startup transcript order regresses;
- `startup_command_position_order` disappears or fails;
- reverse_solving strict freshness semantics regress;
- baseline_capture_order regresses to WARN without explicit limited acceptance;
- preservation-only files are redesigned;
- neutral-primary report semantics regress;
- legacy alias parity breaks;
- forbidden paths are modified;
- tests fail.
