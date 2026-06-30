```json decision_meta
{
  "schema_version": 1,
  "decision_id": "decision_20260630_required_audit_alignment_rework_v1",
  "round_id": "round_20260630_required_audit_alignment_rework_v1",
  "based_on_state_build_id": "state_20260618_134029_d6bd033d2532",
  "based_on_state_digest": "d6bd033d25324345cfd8ada0ac65db42bc86eb5017f3ffc92906fcd8b71cacb5",
  "status": "APPROVED",
  "mainline": "engineering_branch",
  "skill_profiles": ["reverse-agent-iteration@v2"]
}
```

```json decision_contract
{
  "previous_decision_id": "decision_20260630_hygiene_handoff_rework_v1",
  "previous_round_id": "round_20260630_hygiene_handoff_rework_v1",
  "previous_audit_outcome": "REWORK_REQUIRED",
  "phase_label": "phase_2_23_required_audit_alignment_rework",
  "primary_goal": "Repair Required Audit answer alignment, enforce report tests coverage, and clarify final-check exit semantics without expanding runner, handoff, artifact, or control-plane capabilities.",
  "command_plan_authority_required": true,
  "accepted_requires_required_audit_answer_alignment": true,
  "accepted_requires_tests_project_reports_py": true,
  "accepted_requires_required_audit_alignment_negative_test": true,
  "accepted_requires_final_check_exit_semantics_clean": true,
  "accepted_requires_startup_snapshot_immediate_after_startup_status": true,
  "accepted_requires_source_test_clean_start_hard_block_preserved": true,
  "accepted_requires_artifact_role_taxonomy_preserved": true,
  "accepted_requires_no_new_runner_capability": true,
  "accepted_requires_report_summary_fields_match_synthesis": true,
  "accepted_requires_execute_decision_contract_passed": true,
  "accepted_requires_run_closeout_exit_zero": true,
  "accepted_requires_closeout_nested_failures_absent": true,
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
    "docs/prompts/codex_execution_prompt.md",
    "docs/prompts/project_workspace_prompt.md",
    "docs/prompts/README.md",
    ".github/workflows/decision-preflight.yml",
    ".github/workflows/ci.yml",
    ".github/workflows/state-gate.yml"
  ],
  "allowed_generated_or_updated_artifacts": [
    "project_state/codex_execution_report.md",
    "project_state/execution_report.md",
    "project_state/pytest_result.txt",
    "project_state/gates/agent_runner_dry_run_result.json",
    "project_state/gates/agent_runner_handoff_bundle.json",
    "project_state/gates/agent_runner_handoff_validation.json",
    "project_state/gates/codex_report_auto_summary.json",
    "project_state/gates/command_plan.json",
    "project_state/gates/control_plane_snapshot.json",
    "project_state/gates/execution_report_auto_summary.json",
    "project_state/gates/execute_decision_result.json",
    "project_state/gates/execution_log.json",
    "project_state/gates/final_gate_result.json",
    "project_state/gates/gate_profile_plan.json",
    "project_state/gates/job_orchestration_result.json",
    "project_state/gates/jobs_inventory_result.json",
    "project_state/gates/preflight_result.json",
    "project_state/gates/report_summary_synthesis.json",
    "project_state/gates/round_baseline.json",
    "project_state/gates/round_close_snapshot.json",
    "project_state/gates/round_delta_summary.json",
    "project_state/gates/run_closeout_execution_log.json",
    "project_state/gates/run_closeout_result.json",
    "project_state/gates/run_round_result.json",
    "project_state/gates/runner_contract_result.json",
    "project_state/gates/startup_snapshot.json",
    "project_state/jobs/job_20260630_required_audit_alignment_rework_v1.json",
    "project_state/rounds/round_20260630_required_audit_alignment_rework_v1/*"
  ],
  "historical_artifacts_must_not_be_generated_unless_current_round_rebuilt": [
    "project_state/gates/phase1_completion_result.json",
    "project_state/gates/policy_impact_audit.json",
    "project_state/gates/policy_lint_result.json",
    "project_state/gates/state_hygiene_inventory.json",
    "project_state/gates/audit_inventory_result.json",
    "project_state/gates/naming_migration_plan.json"
  ],
  "forbidden_mutated_paths": [
    "project_state/current_state.json",
    "project_state/task_packet.json",
    "project_state/artifact_index.json",
    "project_state/negative_results.json",
    ".codex-skills/registry.json",
    "docs/prompts/codex_execution_prompt.md",
    "docs/prompts/project_workspace_prompt.md",
    "docs/prompts/README.md",
    ".github/workflows/decision-preflight.yml",
    ".github/workflows/ci.yml",
    ".github/workflows/state-gate.yml",
    "solve_reports/*"
  ]
}
```

# DECISION_PACKET

## 1. Goal

Implement **Required Audit Alignment Rework v1**.

This is a narrow rework round after the audit of `decision_20260630_hygiene_handoff_rework_v1` returned `REWORK_REQUIRED`. Do not advance new runner, handoff, artifact, control-plane, Web, API, database, queue, scheduler, CI, or reverse-solving capability.

Primary goals:

1. Rewrite `project_state/codex_execution_report.md` and `project_state/execution_report.md` Required Audit answers so every item directly answers its own question with item-specific evidence.
2. Harden final-check or report-summary validation so it rejects the exact failure pattern seen in the previous round: cyclic/template answers where a startup question is answered with artifact taxonomy evidence, a taxonomy question is answered with decision metadata evidence, or a Required Audit alignment question is answered with generic closeout evidence.
3. Ensure `tests/test_project_reports.py` is actually included in the focused pytest command and recorded in `project_state/pytest_result.txt`.
4. Add or update negative tests for Required Audit answer alignment so mismatched evidence/template-cycled answers fail.
5. Clarify final-check CLI exit semantics. If `final-check` or `final-check-after-close` writes a PASSED artifact but exits `1`, the accepted report must explain why the exit code is expected and non-blocking, or final-check must exit `0` in accepted state. Silent exit-code ambiguity is not acceptable.
6. Preserve the prior improvements:
   - startup source/test baseline is clean and hard-blocked if dirty;
   - startup-snapshot is immediate after the five startup commands;
   - artifact taxonomy excludes historical-only artifacts from generated/current lists;
   - handoff bundle and replay validation remain local, non-executing, and non-dispatching.

Preferred final outcome:

- `codex_report_summary.status: SUCCESS`.
- `acceptance_recommendation: ACCEPTED`.
- `pytest_result_summary.status: PASSED`.
- Focused pytest includes `tests/test_project_reports.py`.
- Required Audit answers are item-specific and no longer template-cycled.
- `required_audit_coverage` or equivalent reports no missing, placeholder, or alignment failures and is credible under manual review.
- `report_summary_fields_match_synthesis: PASS`.
- `execute_decision_contract: PASS`.
- `run-closeout: PASSED`, close-round `CLOSED`, no nested active FAIL/FAILED states.
- final-check after archive/closeout is unambiguous: either CLI exit `0`, or exit `1` is explicitly expected and accompanied by a PASS artifact plus a documented non-blocking reason.

## 2. Current Evidence

Mainline: `engineering_branch`.

The current task is controlled by this `project_state/decision_packet.md`. `project_state/task_packet.json` remains background only and still refers to an older `samplereverse` sample state. It must not drive this engineering rework.

The latest audited execution was `decision_20260630_hygiene_handoff_rework_v1` / `round_20260630_hygiene_handoff_rework_v1`. Its audit conclusion was `REWORK_REQUIRED` for these reasons:

1. Startup baseline and startup ordering were improved. `git status --short` was empty, startup-snapshot was immediate after the five startup commands, and `source_test_clean_start` matched the clean state.
2. Artifact taxonomy was improved. Historical-only artifacts such as `phase1_completion_result.json`, `policy_impact_audit.json`, `policy_lint_result.json`, and `state_hygiene_inventory.json` were moved out of generated/current lists.
3. However, Required Audit answers remained misaligned. Examples from the failed round:
   - the item asking whether startup `git status --short` showed no dirty `reverse_agent/` or `tests/` files was answered with artifact taxonomy evidence;
   - the item asking whether `startup_snapshot.source_test_clean_start` matched actual source/test dirtiness was answered with Required Audit validator evidence;
   - the item asking whether final-check blocks dirty source/test startup was answered with handoff bundle evidence;
   - the item asking whether report taxonomy exists was answered with decision/task/skill metadata;
   - the item asking whether Required Audit answers are aligned was answered with generic closeout/pytest/final-check status.
4. `tests/test_project_reports.py` was required by the decision but was missing from the focused pytest command actually recorded in `pytest_result.txt`.
5. `run_closeout_result.json` showed internal `final-check` and `final-check-after-close` commands exiting `1` while being marked `PASSED`. This may be a known diagnostic convention, but the accepted report did not explain the semantics sufficiently.

Current capability to preserve, not expand:

- `project_gate.py` now contains stricter startup ordering, startup dirty baseline, artifact taxonomy, and Required Audit coverage logic.
- `project_agent_runner.py`, `project_runner_contract.py`, and `project_control_plane.py` contain local non-executing runner/dry-run/handoff evidence support from earlier rounds. This round must not expand them.
- `report_summary_synthesis.json` and final-check already enforce many report consistency checks, but Required Audit alignment remains too permissive.

Artifact freshness:

- Current-round artifacts must carry `decision_20260630_required_audit_alignment_rework_v1` and `round_20260630_required_audit_alignment_rework_v1`.
- Historical gate artifacts may be referenced only as historical/nonblocking unless regenerated in this round with current IDs and current provenance.
- Existing missing sample artifacts in `artifact_index.json` remain nonblocking historical backlog for this engineering rework.

Negative results:

- `negative_results.json` blocks old sample_solver blind search, only increasing beam/budget, compare_semantics_agree=false candidate frontier reuse, full solve_reports commits, and repeated old runtime candidate branches.
- This round must not run samples, solve a reverse challenge, read full solve_reports, run runtime probes, or modify negative_results.

Command-plan policy:

- `command-plan` is the command execution authority.
- Codex may only execute commands authorized by command-plan.
- Command-plan must not weaken these hard requirements: focused pytest must include `tests/test_project_reports.py`; Required Audit alignment must be fixed; startup-snapshot immediacy and clean startup baseline must be preserved; artifact taxonomy must remain fixed; final-check/closeout exit semantics must be explicit; no real execution or dispatch is allowed.

## 3. Do Not Do

Do not implement new runner, handoff, control-plane, job orchestration, Web, API, database, queue, scheduler, CI, or reverse-solving capability.

Do not modify `reverse_agent/project_agent_runner.py`, `reverse_agent/project_control_plane.py`, `reverse_agent/project_jobs.py`, `reverse_agent/project_runner_contract.py`, `reverse_agent/project_audits.py`, `reverse_agent/project_rounds.py`, or `reverse_agent/project_state.py` unless this decision is explicitly revised.

Do not execute handoff bundle commands.

Do not call Codex CLI, Trae, Claude Code, Aider, model APIs, browser automation, GitHub Actions, remote services, or external runners.

Do not enable dispatch. `dispatch_enabled`, `can_dispatch`, `allow_agent_dispatch`, `executable`, `external_invocation`, `remote_mutation`, and equivalent flags must remain false.

Do not create a Web UI, API Planner, API Auditor, database, queue daemon, scheduler, worker process, message bus, Kubernetes workflow, or long-running service.

Do not modify GitHub workflows, prompt docs, `.codex-skills/`, `current_state.json`, `task_packet.json`, `artifact_index.json`, or `negative_results.json`.

Do not read full `solve_reports/`, full `PROJECT_PROGRESS_LOG.txt`, or full historical round directories.

Do not perform reverse-solving, sample execution, runtime probe, dynamic debugging, emulator execution, hook execution, or binary analysis.

Do not accept Required Audit answers that are generic, template-cycled, mismatched with their question, or supported by unrelated evidence.

Do not omit `tests/test_project_reports.py` from the focused pytest run.

Do not silently accept `final-check` exit code `1` in an accepted closeout without a documented non-blocking semantics check.

Do not commit, push, create PRs, switch branches, rebase, merge, or modify remote state unless the user explicitly instructs the executor to upload execution results.

## 4. Files To Inspect

Read first:

1. `project_state/task_packet.json`
2. `project_state/current_state.json`
3. `project_state/artifact_index.json`
4. `project_state/negative_results.json`
5. `project_state/decision_packet.md`
6. `project_state/codex_execution_report.md`
7. `project_state/execution_report.md` if present
8. `project_state/pytest_result.txt`
9. `.codex-skills/registry.json`

Inspect implementation and tests:

1. `reverse_agent/project_gate.py`
2. `tests/test_project_gate.py`
3. `tests/test_project_reports.py`

Inspect only as preserve/read-only context if needed:

1. `reverse_agent/project_agent_runner.py`
2. `reverse_agent/project_control_plane.py`
3. `tests/test_project_agent_runner.py`
4. `tests/test_project_control_plane.py`
5. `tests/test_project_state.py`

Inspect bounded gate artifacts:

1. `project_state/gates/startup_snapshot.json`
2. `project_state/gates/command_plan.json`
3. `project_state/gates/report_summary_synthesis.json`
4. `project_state/gates/final_gate_result.json`
5. `project_state/gates/run_closeout_result.json`
6. `project_state/gates/execution_log.json`
7. `project_state/gates/round_baseline.json`
8. `project_state/gates/round_delta_summary.json`
9. `project_state/gates/agent_runner_dry_run_result.json`
10. `project_state/gates/agent_runner_handoff_bundle.json`
11. `project_state/gates/agent_runner_handoff_validation.json`
12. `project_state/gates/control_plane_snapshot.json`

Create/update if needed:

1. `project_state/jobs/job_20260630_required_audit_alignment_rework_v1.json`
2. `project_state/rounds/round_20260630_required_audit_alignment_rework_v1/*`

Do not scan full `solve_reports/`, full `PROJECT_PROGRESS_LOG.txt`, or full historical round directories.

## 5. Required Audit

The execution report must answer every item below with `PASS`, `FAIL`, `BLOCKED`, or `NOT_APPLICABLE`, with direct evidence for that exact item. The answer text must be specific to the question and must not be copied from another item.

1. Did the first five recorded commands exactly confirm `F:\reverse-agent`, repository root, and `git status --short`?
2. Was `startup-snapshot` the immediate sixth recorded command and the first project gate command?
3. Was `preflight` absent before startup-snapshot?
4. Did startup `git status --short` show no dirty `reverse_agent/` or `tests/` files?
5. Did `startup_snapshot.source_test_clean_start` match the actual startup source/test dirtiness?
6. Does final-check block SUCCESS/ACCEPTED when startup source/test is dirty?
7. Does final-check block SUCCESS/ACCEPTED when preflight or any gate appears before startup-snapshot?
8. Is decision metadata valid: APPROVED, engineering_branch, active `reverse-agent-iteration@v2`?
9. Did Codex treat `decision_packet.md` as authority and `task_packet.json` as background only?
10. Did this round repair the previous Required Audit answer misalignment rather than only reporting generic pass status?
11. Does report taxonomy include generated/updated, referenced, historical_nonblocking, and archived artifacts or equivalent fields?
12. Are `phase1_completion_result.json`, `policy_impact_audit.json`, `policy_lint_result.json`, `state_hygiene_inventory.json`, `audit_inventory_result.json`, and `naming_migration_plan.json` excluded from generated/generated_or_updated unless actually regenerated in this round with current IDs?
13. Does report-summary synthesis validate taxonomy and report no diffs?
14. Does final-check detect stale/historical-only artifacts being placed in generated/current artifact lists?
15. Does final-check or report-summary detect Required Audit placeholder/template/misaligned answers?
16. Are Required Audit answers in `codex_execution_report.md` directly aligned with their question and evidence?
17. Was `tests/test_project_reports.py` included in the focused pytest command recorded in `pytest_result.txt`?
18. Did focused pytest exit 0 and include report/alignment tests?
19. Are existing dry-run, handoff bundle, and replay validation artifacts still current, local, non-executing, and non-dispatching if regenerated this round?
20. Did the rework avoid adding any new real runner, dispatch, external invocation, model API, Web/API/DB/queue/scheduler, GitHub Actions mutation, runtime probe, or reverse-solving capability?
21. Did the implementation stay within allowed source/test files?
22. Were preserve-only and forbidden files not modified?
23. Did required top-level commands exit with expected codes, with pass/fail counts recorded in `pytest_result.txt`?
24. Did `report_summary_fields_match_synthesis` pass with no diffs?
25. Did `execute_decision_contract` pass?
26. Did `execution_log` provenance remain current-round aligned?
27. Did `run-closeout` exit 0 with `closeout_status: PASSED` and close-round `CLOSED`?
28. Did final-check pass after archive/closeout, not only before archive?
29. If any internal final-check command exits `1` while status is treated as PASSED, is the expected-exit and non-blocking semantics explicitly documented and validated?
30. Did `closeout_nested_failures_absent` pass?
31. Does `codex_report_summary` match `pytest_result.txt`, artifact taxonomy, generated/updated artifacts, changed files, decision ID, and round ID?

## 6. Implementation Scope

Allowed source/test changes:

- `reverse_agent/project_gate.py`
- `tests/test_project_gate.py`
- `tests/test_project_reports.py`

Preserve-only files:

- `reverse_agent/project_agent_runner.py`
- `reverse_agent/project_control_plane.py`
- `reverse_agent/project_jobs.py`
- `reverse_agent/project_runner_contract.py`
- `reverse_agent/project_audits.py`
- `reverse_agent/project_rounds.py`
- `reverse_agent/project_state.py`
- `tests/test_project_agent_runner.py`
- `tests/test_project_control_plane.py`
- `tests/test_project_state.py`
- `docs/prompts/codex_execution_prompt.md`
- `docs/prompts/project_workspace_prompt.md`
- `docs/prompts/README.md`
- `.github/workflows/decision-preflight.yml`
- `.github/workflows/ci.yml`
- `.github/workflows/state-gate.yml`

Allowed generated or updated artifacts:

- `project_state/codex_execution_report.md`
- `project_state/execution_report.md`
- `project_state/pytest_result.txt`
- `project_state/jobs/job_20260630_required_audit_alignment_rework_v1.json`
- `project_state/gates/agent_runner_dry_run_result.json`
- `project_state/gates/agent_runner_handoff_bundle.json`
- `project_state/gates/agent_runner_handoff_validation.json`
- `project_state/gates/codex_report_auto_summary.json`
- `project_state/gates/command_plan.json`
- `project_state/gates/control_plane_snapshot.json`
- `project_state/gates/execution_report_auto_summary.json`
- `project_state/gates/execute_decision_result.json`
- `project_state/gates/execution_log.json`
- `project_state/gates/final_gate_result.json`
- `project_state/gates/gate_profile_plan.json`
- `project_state/gates/job_orchestration_result.json`
- `project_state/gates/jobs_inventory_result.json`
- `project_state/gates/preflight_result.json`
- `project_state/gates/report_summary_synthesis.json`
- `project_state/gates/round_baseline.json`
- `project_state/gates/round_close_snapshot.json`
- `project_state/gates/round_delta_summary.json`
- `project_state/gates/run_closeout_execution_log.json`
- `project_state/gates/run_closeout_result.json`
- `project_state/gates/run_round_result.json`
- `project_state/gates/runner_contract_result.json`
- `project_state/gates/startup_snapshot.json`
- `project_state/rounds/round_20260630_required_audit_alignment_rework_v1/*`

Required implementation behavior:

1. Improve `_required_audit_alignment_failures()` or equivalent logic so it catches cross-topic/template-cycled answers.
2. Add explicit mapping from each Required Audit question to required evidence terms or artifact classes.
3. Reject answers that use evidence from an unrelated category. For example:
   - startup dirty questions must cite startup transcript or startup snapshot fields;
   - taxonomy questions must cite report summary taxonomy or synthesis fields;
   - decision authority questions must cite decision/task/registry evidence;
   - handoff questions must cite dry-run/handoff validation artifacts;
   - closeout questions must cite run-closeout/final-check artifacts.
4. Rewrite all Required Audit answers in the execution report to be item-specific.
5. Ensure focused pytest includes `tests/test_project_reports.py` and that this is recorded in both `codex_report_summary.tests_ran` and `pytest_result_summary.tests_ran`.
6. Add a test that fails on the previous report pattern where Required Audit answers rotate among unrelated evidence templates.
7. Add or update tests for final-check exit semantics so accepted closeout cannot silently treat unexplained final-check exit `1` as fully passed.
8. Preserve startup baseline and artifact taxonomy fixes from the prior round.
9. Preserve existing local non-executing handoff evidence without expanding functionality.

## 7. Tests

Startup sequence must be recorded first in `project_state/pytest_result.txt`:

```powershell
Set-Location F:\reverse-agent
Get-Location
Test-Path F:\reverse-agent
git rev-parse --show-toplevel
git status --short
python -m reverse_agent.project_gate startup-snapshot --state-dir project_state
```

Hard startup rules:

- No `python -m reverse_agent.project_gate preflight ...` may be recorded before startup-snapshot.
- No `command-plan`, `final-check`, `jobs-inventory`, `job-orchestration`, `runner-contract`, `agent-runner-dry-run`, `agent-runner-handoff-*`, `control-plane-snapshot`, `report-summary`, `execution-log`, or `run-closeout` command may appear before startup-snapshot.
- If startup `git status --short` shows any dirty `reverse_agent/` or `tests/` path, stop with `BLOCKED` before implementation and do not write `SUCCESS`.

Required focused pytest command must include `tests/test_project_reports.py`:

```powershell
python -m pytest tests/test_project_gate.py tests/test_project_reports.py tests/test_project_agent_runner.py tests/test_project_control_plane.py tests/test_project_state.py -q
```

Focused tests must cover at least:

- Required Audit item-to-evidence alignment;
- rejection of template-cycled Required Audit answers;
- rejection of startup questions answered with taxonomy or handoff evidence;
- rejection of taxonomy questions answered with decision metadata evidence;
- rejection of Required Audit alignment questions answered only with generic closeout evidence;
- inclusion of `tests/test_project_reports.py` in the recorded pytest command;
- final-check exit semantics for accepted closeout.

Then run command-plan-authorized validation. At minimum include the equivalent of:

```powershell
python -m reverse_agent.project_gate command-plan --state-dir project_state
python -m reverse_agent.project_gate command-plan --state-dir project_state --json
python -m reverse_agent.project_gate preflight --state-dir project_state --allow-consumed
python -m reverse_agent.project_gate jobs-inventory --state-dir project_state
python -m reverse_agent.project_gate job-orchestration --state-dir project_state
python -m reverse_agent.project_gate runner-contract --state-dir project_state
python -m reverse_agent.project_gate agent-runner-dry-run --state-dir project_state
python -m reverse_agent.project_gate agent-runner-handoff-bundle --state-dir project_state
python -m reverse_agent.project_gate agent-runner-handoff-validate --state-dir project_state
python -m reverse_agent.project_gate control-plane-snapshot --state-dir project_state
python -m reverse_agent.project_gate report-summary --state-dir project_state
python -m reverse_agent.project_gate execute-decision --state-dir project_state --round-id round_20260630_required_audit_alignment_rework_v1 --mode execute
python -m reverse_agent.project_gate execution-log --state-dir project_state
python -m reverse_agent.project_gate final-check --state-dir project_state
python -m reverse_agent.project_gate run-closeout --state-dir project_state --round-id round_20260630_required_audit_alignment_rework_v1
python -m reverse_agent.project_gate final-check --state-dir project_state
```

The concrete command list must come from command-plan. Do not run commands outside command-plan. Write all top-level commands, exit codes, and pytest pass/fail counts to `project_state/pytest_result.txt`.

## 8. Stop Conditions

Stop immediately with `BLOCKED` if:

- startup cannot confirm `F:\reverse-agent` and repository root;
- startup `git status --short` shows any dirty `reverse_agent/` or `tests/` path;
- startup-snapshot cannot be generated immediately after the five startup status commands;
- preflight or any other project gate runs before startup-snapshot;
- decision metadata is invalid;
- skill profile is not active;
- command-plan is missing or unsafe;
- the task requires real runner dispatch, external model calls, GitHub Actions triggers, remote mutation, Web/API/DB/queue/scheduler work, reverse-solving, runtime probes, or full solve_reports scanning;
- implementation requires mutating forbidden paths or preserve-only files.

Stop with `REWORK_REQUIRED` if:

- Required Audit answers are generic, placeholder, repeated from a template, copied from another item, or mismatched with their questions;
- final-check cannot detect the previous round's Required Audit template-cycling pattern;
- `tests/test_project_reports.py` is missing from the focused pytest command or from `pytest_result.txt`;
- required pytest commands fail;
- final-check CLI exit semantics remain ambiguous in accepted closeout;
- startup source/test dirty files are reclassified as authorized rather than blocking;
- `startup_snapshot.source_test_clean_start` does not match actual startup source/test dirtiness;
- final-check accepts dirty startup source/test evidence;
- startup ordering regresses;
- `generated_artifacts` or `generated_or_updated_artifacts` includes stale/historical-only artifacts as current generated artifacts;
- artifact taxonomy fields are missing from summaries or not checked by report-summary synthesis;
- existing handoff bundle or validation artifacts regress if regenerated;
- any runner/handoff code executes commands, spawns subprocesses, calls external services, or mutates remote state;
- stale sample or historical gate artifacts are treated as current accepted evidence;
- `codex_execution_report.md` omits Required Audit answers;
- `pytest_result.txt` does not match actual commands or exit codes;
- `report_summary_fields_match_synthesis` fails;
- `execute_decision_contract` fails;
- `execution_log` provenance regresses;
- `run-closeout` exits nonzero or close status is not CLOSED;
- final-check after archive/closeout does not pass or has unexplained expected exit behavior;
- nested failure scan finds active FAILED/FAIL states;
- Codex modifies workflows, prompts, skills, task/current/artifact/negative state, solve_reports, or remote state.
