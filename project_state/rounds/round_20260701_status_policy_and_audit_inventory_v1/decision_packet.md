```json decision_meta
{
  "schema_version": 1,
  "decision_id": "decision_20260701_status_policy_and_audit_inventory_v1",
  "round_id": "round_20260701_status_policy_and_audit_inventory_v1",
  "based_on_state_build_id": "state_20260618_134029_d6bd033d2532",
  "based_on_state_digest": "d6bd033d25324345cfd8ada0ac65db42bc86eb5017f3ffc92906fcd8b71cacb5",
  "status": "APPROVED",
  "mainline": "engineering_branch",
  "skill_profiles": ["reverse-agent-iteration@v2"]
}
```

```json decision_contract
{
  "previous_decision_id": "decision_20260630_final_check_exit_and_audit_readiness_v1",
  "previous_round_id": "round_20260630_final_check_exit_and_audit_readiness_v1",
  "previous_audit_outcome": "ACCEPTED_WITH_LIMITATIONS",
  "phase_label": "phase_2_25_status_policy_and_audit_inventory",
  "primary_goal": "Fix status-policy warning/source inconsistency and advance audit inventory into a current gate artifact.",
  "command_plan_authority_required": true,
  "accepted_requires_status_policy_no_false_failed_report_warning": true,
  "accepted_requires_current_audit_inventory": true,
  "accepted_requires_existing_audit_readiness_packet_not_regressed": true,
  "accepted_requires_command_plan_order_policy_preserved": true,
  "allowed_source_files": [
    "reverse_agent/project_gate.py",
    "tests/test_project_gate.py",
    "tests/test_project_reports.py"
  ],
  "preserve_only_files": [
    "reverse_agent/project_agent_runner.py",
    "reverse_agent/project_control_plane.py",
    "reverse_agent/project_jobs.py",
    "reverse_agent/project_runner_contract.py",
    "reverse_agent/project_audits.py",
    "reverse_agent/project_rounds.py",
    "reverse_agent/project_state.py",
    "tests/test_project_agent_runner.py",
    "tests/test_project_control_plane.py",
    "tests/test_project_state.py",
    "docs/prompts/*",
    ".github/workflows/*"
  ],
  "allowed_generated_or_updated_artifacts": [
    "project_state/codex_execution_report.md",
    "project_state/execution_report.md",
    "project_state/pytest_result.txt",
    "project_state/gates/*.json",
    "project_state/rounds/round_20260701_status_policy_and_audit_inventory_v1/*"
  ],
  "forbidden_mutated_paths": [
    "project_state/current_state.json",
    "project_state/task_packet.json",
    "project_state/artifact_index.json",
    "project_state/negative_results.json",
    ".codex-skills/registry.json",
    "docs/prompts/*",
    ".github/workflows/*",
    "solve_reports/*"
  ]
}
```

# DECISION_PACKET

## 1. Goal

Implement **Status Policy Cleanup and Current Audit Inventory v1**.

This round deliberately combines one repair and one bounded engineering advance.

Repair task:

1. Fix the `status_policy_valid` false/inconsistent warning where final-check can report current-round artifacts complete while still embedding `report_status is FAILED` or `doctor status is WARN` even though the live report summary is `SUCCESS` and `ACCEPTED`.

Engineering advance:

2. Promote audit inventory from historical/nonblocking context into a current, bounded gate artifact for this round.
3. The current audit inventory must validate `project_state/audits/*.md` files, including the latest uploaded audit result, and report outcome counts without using stale historical IDs as current evidence.

Target outcome:

- `codex_execution_report.md` status: `SUCCESS`.
- acceptance recommendation: `ACCEPTED`.
- `pytest_result.txt` status: `PASSED`.
- `final-check`: `PASSED`.
- `run-closeout`: `PASSED`.
- `close-round`: `CLOSED`.
- `audit_readiness_packet.json`: remains `READY`, `PASSED`, `no_action_required`, evidence-only.
- `status_policy_valid`: no false `report_status is FAILED` warning when the canonical report summary is `SUCCESS`.
- `audit_inventory_result.json`: current decision ID, current round ID, valid audit count, valid outcome counts, no duplicate audit IDs.

## 2. Current Evidence

Mainline: `engineering_branch`.

`project_state/decision_packet.md` controls the current round. `project_state/task_packet.json` remains background only.

Previous accepted-with-limitations evidence:

- `audit_readiness_packet.json` was repaired to `readiness_status: READY`.
- `audit_readiness_packet.closeout_status.status` is now `PASSED`.
- `audit_readiness_packet.limitations` is empty.
- `audit_readiness_packet.next_action` is `no_action_required`.
- final-check validates `audit_readiness_packet_valid`.
- pytest passed with expanded counts.
- run-closeout passed and close-round is closed.
- command-plan now explicitly documents `execution_order_policy.mode = coverage_expected_exit_not_strict_wall_clock`.

Remaining limitation:

- `final_gate_result.json` still contains a `status_policy_valid` warning with stale/inconsistent text such as `report_status is FAILED` even though report summary synthesis and final status summary show `SUCCESS` / `ACCEPTED`.
- `audit_inventory_result.json` is still treated as stale/historical in final-check and does not provide a current-round inventory of `project_state/audits/*.md`.

Artifact freshness policy:

- Current-round gate artifacts must carry `decision_20260701_status_policy_and_audit_inventory_v1` and `round_20260701_status_policy_and_audit_inventory_v1`.
- Historical artifacts may be referenced but not listed as generated/current unless rebuilt in this round.
- Missing historical sample artifacts remain nonblocking background.
- The uploaded audit result under `project_state/audits/` should be treated as input evidence for audit inventory, not as a generated artifact of this new round unless Codex modifies it.

Command-plan policy:

- `command-plan` is the execution authority.
- Codex may only run command-plan authorized commands.
- Existing execution order policy may remain coverage/expected-exit based, but it must be explicit and final-check validated.
- Startup order and closeout order checks must remain strict.

## 3. Do Not Do

Do not expand runner, handoff, control-plane, job, round, Web, API, CI, scheduler, database, or external integration modules.

Do not perform reverse solving, sample solving, runtime probing, dynamic debugging, emulator work, IDA/Ghidra/OllyDbg execution, or heavy historical scanning.

Do not read full `solve_reports/` or full `PROJECT_PROGRESS_LOG.txt`.

Do not modify:

- `project_state/current_state.json`
- `project_state/task_packet.json`
- `project_state/artifact_index.json`
- `project_state/negative_results.json`
- `.codex-skills/registry.json`
- `.github/workflows/*`
- `docs/prompts/*`

Do not create a new audit verdict file unless explicitly required by a generated artifact policy. This round should validate audit inventory, not write a new human audit.

Do not weaken final-check merely to silence warnings. The fix must make status-policy sources consistent.

Do not change report status schema values or introduce unsupported status names.

Do not commit, push, create PRs, switch branches, rebase, merge, or modify remote state unless the user explicitly asks the executor to upload results.

## 4. Files To Inspect

Read first:

1. `project_state/task_packet.json`
2. `project_state/current_state.json`
3. `project_state/artifact_index.json`
4. `project_state/negative_results.json`
5. `project_state/decision_packet.md`
6. `project_state/codex_execution_report.md`
7. `project_state/execution_report.md`
8. `project_state/pytest_result.txt`
9. `.codex-skills/registry.json`

Inspect bounded gate artifacts:

1. `project_state/gates/final_gate_result.json`
2. `project_state/gates/report_summary_synthesis.json`
3. `project_state/gates/audit_readiness_packet.json`
4. `project_state/gates/audit_inventory_result.json` if present
5. `project_state/gates/command_plan.json`
6. `project_state/gates/execution_log.json`
7. `project_state/gates/run_closeout_result.json`
8. `project_state/gates/round_delta_summary.json`

Inspect implementation and tests:

1. `reverse_agent/project_gate.py`
2. `tests/test_project_gate.py`
3. `tests/test_project_reports.py`

Inspect audit inputs only:

1. `project_state/audits/*.md`

Read-only context if needed:

1. `reverse_agent/project_audits.py`
2. `reverse_agent/project_rounds.py`

Do not scan full `solve_reports/`, full historical round directories, or full `PROJECT_PROGRESS_LOG.txt`.

## 5. Required Audit

The execution report must answer these items with direct evidence:

1. Did startup commands confirm `F:\reverse-agent`, repo root, and clean `git status --short` before any project gate?
2. Was `startup-snapshot` still the immediate sixth command and first project gate?
3. Did `decision_meta` remain valid and APPROVED on `engineering_branch`?
4. Did `reverse-agent-iteration@v2` remain active in `.codex-skills/registry.json`?
5. Did Codex treat `decision_packet.md` as authority and `task_packet.json` as background only?
6. Did the implementation stay within allowed source/test files?
7. Were preserve-only and forbidden files not modified?
8. Did the status-policy repair remove false `report_status is FAILED` warning when canonical report summary is `SUCCESS`?
9. Does final-check now use one canonical status source, or explicitly reconcile report summary, report body, report-summary synthesis, and final status summary?
10. Is there a regression test where stale `FAILED` status-policy data would have produced the old warning and now fails or normalizes correctly?
11. Did `audit_inventory_result.json` get regenerated with the current decision ID and round ID?
12. Does audit inventory validate all `project_state/audits/*.md` files in bounded form?
13. Does audit inventory include the latest uploaded `audit_20260701_rework_required_audit_readiness_packet.md` file or otherwise explain why it is excluded?
14. Does audit inventory report outcome counts and duplicate audit ID errors?
15. Does final-check distinguish stale historical audit inventory from current audit inventory?
16. Does final-check reject current audit inventory with stale decision/round IDs if this round requires current inventory?
17. Did audit inventory remain evidence-only and non-dispatching?
18. Did `audit_readiness_packet.json` remain `READY`, `PASSED`, evidence-only, and `no_action_required`?
19. Did command-plan retain explicit `execution_order_policy`?
20. Did final-check continue validating command-plan coverage, expected exits, and startup/closeout ordering?
21. Did report-summary synthesis pass with no diffs?
22. Did focused pytest include `tests/test_project_reports.py` and exit 0?
23. Did `execution-log` provenance remain current-round aligned?
24. Did `run-closeout` exit 0?
25. Did close-round become `CLOSED`?
26. Did post-closeout final-check pass with exit 0?
27. Did closeout nested failure scan pass?
28. Did final report summary match pytest, changed files, generated artifacts, decision ID, round ID, audit inventory status, and audit readiness packet status?

## 6. Implementation Scope

Allowed source/test changes:

- `reverse_agent/project_gate.py`
- `tests/test_project_gate.py`
- `tests/test_project_reports.py`

Allowed generated or updated artifacts:

- `project_state/codex_execution_report.md`
- `project_state/execution_report.md`
- `project_state/pytest_result.txt`
- `project_state/gates/*.json`
- `project_state/rounds/round_20260701_status_policy_and_audit_inventory_v1/*`

Required behavior:

1. `status_policy_valid` must not report `report_status is FAILED` when canonical report summary and final status summary are `SUCCESS` / `ACCEPTED`.
2. If multiple report status sources disagree, final-check must either:
   - fail with explicit source mismatch; or
   - normalize through a documented canonical source and record the noncanonical source as stale/nonblocking only.
3. Add a regression test for the stale status-policy warning case.
4. Add or update an `audit-inventory` gate function if already present in `project_gate.py`, or repair its current-round integration if the function already exists.
5. `audit_inventory_result.json` must include:
   - schema_version;
   - artifact_name;
   - gate_name;
   - gate_status;
   - decision_id;
   - round_id;
   - generated_at;
   - audit_count;
   - outcome_counts;
   - validated_paths;
   - duplicate_audit_id_errors;
   - invalid_file_errors;
   - evidence_only or equivalent non-dispatching marker.
6. final-check must validate current audit inventory when this decision contract requires it.
7. Existing audit readiness packet behavior must not regress.
8. Existing command-plan execution order policy must not regress.
9. Existing artifact taxonomy separation must not regress.

## 7. Tests

Startup sequence must be recorded first:

```powershell
Set-Location F:\reverse-agent
Get-Location
Test-Path F:\reverse-agent
git rev-parse --show-toplevel
git status --short
python -m reverse_agent.project_gate startup-snapshot --state-dir project_state
```

Required focused pytest command:

```powershell
python -m pytest tests/test_project_gate.py tests/test_project_reports.py tests/test_project_state.py -q
```

Required gate commands must be authorized by command-plan. At minimum command-plan should cover:

```powershell
python -m reverse_agent.project_gate command-plan --state-dir project_state
python -m reverse_agent.project_gate command-plan --state-dir project_state --json
python -m reverse_agent.project_gate preflight --state-dir project_state --allow-consumed
python -m reverse_agent.project_gate audit-inventory --state-dir project_state
python -m reverse_agent.project_gate report-summary --state-dir project_state
python -m reverse_agent.project_gate execution-log --state-dir project_state
python -m reverse_agent.project_gate audit-readiness-packet --state-dir project_state
python -m reverse_agent.project_gate final-check --state-dir project_state
python -m reverse_agent.project_gate run-closeout --state-dir project_state --round-id round_20260701_status_policy_and_audit_inventory_v1
python -m reverse_agent.project_gate final-check --state-dir project_state
```

If the exact CLI name for audit inventory differs, use the existing project_gate subcommand and record the actual command in `pytest_result.txt`.

Required regression coverage:

- stale `report_status is FAILED` warning is removed or becomes a blocking source mismatch;
- current audit inventory carries current decision/round IDs;
- audit inventory validates every bounded audit file;
- duplicate audit IDs fail;
- invalid audit summary blocks fail;
- stale audit inventory is not accepted as current when current inventory is required;
- audit readiness packet remains READY/PASSED/no_action_required;
- command-plan execution_order_policy remains explicit;
- final-check and closeout exit 0.

Write all top-level commands, exit codes, and pytest pass/fail counts to `project_state/pytest_result.txt`.

## 8. Stop Conditions

Stop with `BLOCKED` if:

- startup path or repo root is wrong;
- startup `git status --short` has dirty source/test files outside allowed baseline;
- startup-snapshot is not immediate after startup status commands;
- any project gate runs before startup-snapshot;
- decision metadata or skill profile is invalid;
- command-plan is missing or unsafe;
- implementation requires preserve-only or forbidden paths;
- repair requires changing workflow, runner, Web/API, database, project state builder, or remote state.

Stop with `REWORK_REQUIRED` if:

- `status_policy_valid` still reports false `report_status is FAILED` while canonical report status is `SUCCESS`;
- status sources disagree and final-check neither fails nor documents a safe canonical source;
- `audit_inventory_result.json` is missing, stale, malformed, or not current-round aligned;
- audit inventory omits the uploaded audit result without explanation;
- duplicate audit IDs or invalid audit summaries are not detected;
- audit readiness packet regresses from READY/PASSED/no_action_required;
- command-plan execution order policy disappears or becomes implicit again;
- focused pytest omits `tests/test_project_reports.py`;
- pytest, report-summary, execution-log, audit-inventory, final-check, audit-readiness, run-closeout, or post-closeout final-check fails;
- close-round is not CLOSED;
- closeout nested failure scan finds active failures;
- forbidden files are modified.
