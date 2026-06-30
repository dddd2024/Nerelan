```json decision_meta
{
  "schema_version": 1,
  "decision_id": "decision_20260630_final_check_exit_and_audit_readiness_v1",
  "round_id": "round_20260630_final_check_exit_and_audit_readiness_v1",
  "based_on_state_build_id": "state_20260618_134029_d6bd033d2532",
  "based_on_state_digest": "d6bd033d25324345cfd8ada0ac65db42bc86eb5017f3ffc92906fcd8b71cacb5",
  "status": "APPROVED",
  "mainline": "engineering_branch",
  "skill_profiles": ["reverse-agent-iteration@v2"]
}
```

```json decision_contract
{
  "previous_decision_id": "decision_20260630_required_audit_alignment_rework_v1",
  "previous_round_id": "round_20260630_required_audit_alignment_rework_v1",
  "previous_audit_outcome": "ACCEPTED_WITH_LIMITATIONS",
  "phase_label": "phase_2_24_final_check_exit_and_audit_readiness",
  "primary_goal": "Fix final-check accepted exit semantics and Required Audit item 6 evidence, then add a local audit readiness packet.",
  "command_plan_authority_required": true,
  "accepted_requires_final_check_exit_zero": true,
  "accepted_requires_required_audit_item_6_negative_evidence": true,
  "accepted_requires_tests_project_reports_py": true,
  "accepted_requires_audit_readiness_packet": true,
  "accepted_requires_startup_and_artifact_taxonomy_regression_free": true,
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
    "project_state/jobs/job_20260630_final_check_exit_and_audit_readiness_v1.json",
    "project_state/gates/*.json",
    "project_state/rounds/round_20260630_final_check_exit_and_audit_readiness_v1/*"
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

Implement **Final-Check Exit Policy and Audit Readiness Packet v1**.

This round combines a repair task and a small engineering advance.

Repair tasks:

1. Accepted `final-check` evidence must use CLI exit `0`. A passed final gate artifact paired with exit `1` is no longer enough for final accepted evidence.
2. Required Audit item 6 must prove that final-check rejects dirty startup source/test evidence. It must not only state that the real startup was clean.
3. Preserve existing startup order, startup cleanliness, Required Audit alignment, and artifact taxonomy fixes.

Engineering advance:

4. Add `project_state/gates/audit_readiness_packet.json`. This is a compact local evidence packet for later UI/API handoff. It summarizes the current decision, report, pytest, final-check, closeout, artifact taxonomy, Required Audit coverage, limitations, and next action.

Target outcome: report `SUCCESS`, recommendation `ACCEPTED`, pytest `PASSED`, closeout `PASSED`, close-round `CLOSED`, final accepted checks exit `0`, and audit readiness packet is current and valid.

## 2. Current Evidence

Mainline: `engineering_branch`.

`project_state/decision_packet.md` controls this round. `project_state/task_packet.json` is background only.

Previous round: `decision_20260630_required_audit_alignment_rework_v1` / `round_20260630_required_audit_alignment_rework_v1`.

Previous audit outcome: `ACCEPTED_WITH_LIMITATIONS`.

Accepted evidence from the previous round:

- decision digest matched `current_state.state_digest`;
- Required Audit alignment was repaired;
- `tests/test_project_reports.py` was added and run;
- startup order was correct;
- startup source/test state was clean;
- artifact taxonomy separated current generated artifacts from historical references.

Remaining limitations:

- Required Audit item 6 should cite final-check negative evidence directly;
- accepted final-check command blocks should exit `0` to avoid automation ambiguity.

Artifact freshness:

- New artifacts must carry this decision ID and round ID.
- Historical artifacts may only be referenced unless rebuilt in this round.
- Missing sample artifacts remain nonblocking background.

Command-plan policy:

- `command-plan` is the command authority.
- Codex may only run command-plan authorized commands.
- Command-plan must preserve startup order, final-check exit-zero acceptance, audit readiness packet validation, and artifact taxonomy.

## 3. Do Not Do

Do not expand runner, handoff, control-plane, job, round, or state modules.

Do not add UI, service, database, scheduler, external integration, or new execution channel.

Do not modify workflows, prompt docs, skills, task/current/artifact/negative state files, or solve report output.

Do not perform sample solving or heavy historical scanning.

Do not accept final-check exit `1` as final accepted evidence.

Do not accept Required Audit item 6 without direct negative evidence from final-check behavior.

Do not make the audit readiness packet executable or capable of changing state. It is evidence only.

Do not commit, push, create PRs, switch branches, rebase, merge, or modify remote state unless the user explicitly asks the executor to upload results.

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

Read-only context if needed:

1. `reverse_agent/project_agent_runner.py`
2. `reverse_agent/project_control_plane.py`
3. `tests/test_project_agent_runner.py`
4. `tests/test_project_control_plane.py`
5. `tests/test_project_state.py`

Inspect bounded artifacts only:

1. `project_state/gates/startup_snapshot.json`
2. `project_state/gates/command_plan.json`
3. `project_state/gates/report_summary_synthesis.json`
4. `project_state/gates/final_gate_result.json`
5. `project_state/gates/run_closeout_result.json`
6. `project_state/gates/execution_log.json`
7. `project_state/gates/round_delta_summary.json`
8. `project_state/gates/audit_readiness_packet.json` if present

Do not scan full `solve_reports/`, full `PROJECT_PROGRESS_LOG.txt`, or full historical round directories.

## 5. Required Audit

The execution report must answer these items with direct evidence:

1. Startup commands confirmed `F:\reverse-agent`, repo root, and `git status --short`.
2. Startup-snapshot was the immediate sixth command and first project gate.
3. No preflight ran before startup-snapshot.
4. Startup had no dirty `reverse_agent/` or `tests/` files.
5. `source_test_clean_start` matched actual startup state.
6. Final-check blocks dirty startup source/test evidence and the report cites that negative evidence directly.
7. Final-check blocks gate-order regression before startup-snapshot.
8. Decision metadata and active skill are valid.
9. Decision packet was authority and task packet was background.
10. Required Audit alignment remains fixed.
11. Artifact taxonomy separates generated, referenced, historical, and archived artifacts.
12. Historical-only artifacts are excluded from generated/current lists unless rebuilt this round.
13. Report-summary synthesis passes with no diffs.
14. `tests/test_project_reports.py` ran and pytest exited 0.
15. Accepted final-check command blocks exit 0.
16. Closeout internal final-checks have unambiguous success semantics.
17. `audit_readiness_packet.json` exists with current IDs.
18. Audit readiness packet is evidence-only and cannot execute or mutate state.
19. Final-check validates audit readiness packet freshness and policy fields.
20. Implementation stayed within allowed files.
21. Preserve-only and forbidden files were not modified.
22. Required command-plan commands were recorded with expected exits.
23. Execute-decision passed.
24. Execution-log provenance is current-round aligned.
25. Run-closeout exited 0 and close-round is CLOSED.
26. Post-closeout final-check passed with exit 0.
27. Closeout nested failure scan passed.
28. Report summary matches pytest, artifacts, changed files, decision ID, round ID, and audit readiness packet status.

## 6. Implementation Scope

Allowed source/test changes:

- `reverse_agent/project_gate.py`
- `tests/test_project_gate.py`
- `tests/test_project_reports.py`

Allowed generated or updated artifacts:

- `project_state/codex_execution_report.md`
- `project_state/execution_report.md`
- `project_state/pytest_result.txt`
- `project_state/jobs/job_20260630_final_check_exit_and_audit_readiness_v1.json`
- `project_state/gates/*.json`
- `project_state/rounds/round_20260630_final_check_exit_and_audit_readiness_v1/*`

Required behavior:

1. Accepted final-check and post-closeout final-check exit 0.
2. Tests fail if final accepted evidence still depends on exit 1.
3. Required Audit item 6 uses final-check dirty-startup negative evidence.
4. Tests fail if item 6 only cites clean startup evidence.
5. Add an `audit-readiness-packet` gate or equivalent function that writes `project_state/gates/audit_readiness_packet.json`.
6. Packet fields include IDs, readiness status, recommendation, startup hygiene, Required Audit coverage, pytest coverage, final-check policy, closeout status, artifact taxonomy, limitations, and next action.
7. Final-check validates packet freshness and evidence-only semantics.
8. Existing startup and artifact taxonomy fixes do not regress.

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

Required coverage:

- accepted final-check exits 0;
- post-closeout final-check exits 0;
- Required Audit item 6 rejects clean-startup-only evidence;
- Required Audit item 6 accepts dirty-startup negative evidence;
- audit readiness packet is current, evidence-only, and complete;
- final-check validates audit readiness packet;
- artifact taxonomy remains clean.

Then run only command-plan authorized validation commands. At minimum the command-plan must cover startup-snapshot, command-plan, preflight, report-summary, focused pytest, final-check, execute-decision, execution-log, run-closeout, post-closeout final-check, audit-readiness-packet, and final-check after audit-readiness.

Write all top-level commands, exit codes, and pytest pass/fail counts to `project_state/pytest_result.txt`.

## 8. Stop Conditions

Stop with `BLOCKED` if:

- startup path or repo root is wrong;
- startup `git status --short` has dirty source/test files;
- startup-snapshot is not immediate after startup status commands;
- any gate runs before startup-snapshot;
- decision metadata or skill profile is invalid;
- command-plan is missing or unsafe;
- implementation requires preserve-only or forbidden paths.

Stop with `REWORK_REQUIRED` if:

- accepted final-check or post-closeout final-check exits 1;
- Required Audit item 6 lacks direct dirty-startup negative evidence;
- Required Audit alignment regresses;
- `tests/test_project_reports.py` is missing from pytest;
- audit readiness packet is missing, stale, mutable, incomplete, or not validated by final-check;
- startup or artifact taxonomy fixes regress;
- generated/current artifacts include historical-only artifacts;
- any forbidden path is modified;
- pytest, report-summary, execute-decision, execution-log, final-check, audit-readiness, or run-closeout fails;
- close-round is not CLOSED;
- nested failure scan finds active failures.
