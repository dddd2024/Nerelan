```json decision_meta
{
  "schema_version": 1,
  "decision_id": "decision_20260620_run_closeout_usage_solidification_v1",
  "round_id": "round_20260620_run_closeout_usage_solidification_v1",
  "based_on_state_build_id": "state_20260618_134029_d6bd033d2532",
  "based_on_state_digest": "d6bd033d25324345cfd8ada0ac65db42bc86eb5017f3ffc92906fcd8b71cacb5",
  "status": "APPROVED",
  "mainline": "engineering_branch",
  "skill_profiles": ["reverse-agent-iteration@v2"]
}
```

```json decision_contract
{
  "required_generated_artifacts": [
    "project_state/pytest_result.txt",
    "project_state/codex_execution_report.md",
    "project_state/gates/command_plan.json",
    "project_state/gates/report_summary_synthesis.json",
    "project_state/gates/final_gate_result.json",
    "project_state/rounds/round_20260620_run_closeout_usage_solidification_v1/round_manifest.json"
  ],
  "required_files_changed": [
    "reverse_agent/project_gate.py",
    "tests/test_project_gate.py",
    "README.md",
    "docs/run_closeout.md"
  ],
  "forbidden_mutated_paths": [
    "project_state/current_state.json",
    "project_state/task_packet.json",
    "project_state/artifact_index.json",
    "project_state/model_gate.json",
    "project_state/negative_results.json",
    ".codex-skills/registry.json"
  ],
  "required_command_fragments": [
    "python -m reverse_agent.project_gate run-closeout --state-dir project_state --round-id round_20260620_run_closeout_usage_solidification_v1"
  ],
  "close_round_required": true,
  "accepted_requires_final_check_passed": true
}
```

# DECISION_PACKET

## 1. Goal

Solidify the now-accepted `run-closeout`, `decision_contract`, and Required Audit checks as the default engineering-round closeout path.

The previous accepted rounds fixed the automated closeout loop and Required Audit answer validation. The remaining usage-level problem is that `command-plan` can still present a manual next action such as `record_and_follow_command_plan_manually`, and project-facing documentation does not yet make `run-closeout` the obvious default for Codex execution rounds.

This round must make the recommended workflow explicit and testable: when a decision is approved and closeout is allowed, `command-plan` should prefer the single `run-closeout` invocation over a manual command-plan handoff. Documentation should describe the default path, its evidence artifacts, and the cases where manual fallback remains appropriate.

## 2. Current Evidence

The current `task_packet.json` still points to `project_state/decision_packet.md` as the active decision packet and states that execution is controlled by the decision packet.

The previous accepted round `decision_20260620_required_audit_answer_validation_v1` completed successfully:

- `codex_execution_report.md` was `SUCCESS / ACCEPTED`.
- `pytest_result.txt` recorded startup checks, `run-closeout`, nested gate commands, close-round, and after-close final-check.
- pytest passed with `922 passed`.
- final-check passed with current decision/report/round IDs.
- `required_audit_coverage` passed with substantive answers and no placeholders.

Remaining usage issue:

- The workflow still risks drifting back to manual command-plan execution because the preferred Codex action is not documented and not enforced as the primary recommendation.
- Older command-plan outputs have used `recommended_next_action: record_and_follow_command_plan_manually` even after `run-closeout` existed.
- Some command-plan outputs may still include live `python -m reverse_agent.project_state build` status commands even when the active decision's Do Not Do section forbids live state build.

This is an engineering branch documentation and command-plan guidance round. It must not continue reverse solving.

## 3. Do Not Do

Do not run live `python -m reverse_agent.project_state build`.

Do not promote `project_state/proposed_state/*` to live root state.

Do not continue affine solving.

Do not resume samplereverse candidate search.

Do not run binaries, runtime probes, debuggers, emulators, hooks, IDA, Ghidra, x64dbg, OllyDbg, or dynamic validation.

Do not modify `.codex-skills/`.

Do not replace `run-closeout` with a workflow engine.

Do not add a daemon, scheduler, database, message queue, Kubernetes workflow, or web server.

Do not remove the manual command-plan path; keep it as a fallback for blocked or unsupported cases.

Do not claim `SUCCESS` unless command-plan recommendation, documentation, tests, run-closeout, report-summary, final-check, close-round, after-close final-check, and Required Audit checks pass.

## 4. Files To Inspect

Default context:

1. `project_state/task_packet.json`
2. `project_state/current_state.json`
3. `project_state/artifact_index.json`
4. `project_state/negative_results.json`
5. `project_state/codex_execution_report.md`
6. `project_state/decision_packet.md`
7. `project_state/pytest_result.txt`
8. `.codex-skills/registry.json`

Implementation and tests:

1. `reverse_agent/project_gate.py`
2. `reverse_agent/project_state.py`
3. `tests/test_project_gate.py`
4. `tests/test_project_state.py`
5. `README.md`
6. `docs/run_closeout.md` if present; create it if absent.

Gate artifacts:

1. `project_state/gates/command_plan.json`
2. `project_state/gates/gate_profile_plan.json`
3. `project_state/gates/report_summary_synthesis.json`
4. `project_state/gates/final_gate_result.json`
5. `project_state/gates/round_delta_summary.json`
6. `project_state/gates/round_close_snapshot.json`

Previous successful-round context:

1. `project_state/rounds/round_20260620_required_audit_answer_validation_v1/codex_execution_report.md`
2. `project_state/rounds/round_20260620_required_audit_answer_validation_v1/pytest_result.txt`
3. `project_state/rounds/round_20260620_required_audit_answer_validation_v1/round_manifest.json`

## 5. Required Audit

Before editing code, answer in `codex_execution_report.md`:

1. Where does `command-plan` currently decide `recommended_next_action`?
2. Under what conditions should `run-closeout` be the recommended next action?
3. Under what conditions should manual command-plan execution remain the recommended fallback?
4. Does command-plan currently include `python -m reverse_agent.project_state build` when the active decision forbids live build?
5. How will the implementation avoid executing or recommending forbidden live build commands?
6. Which documentation location is best for user-facing closeout workflow instructions: README, docs page, or both?
7. How will tests prove that `run-closeout` is now the preferred default without breaking manual fallback?
8. How will the report prove that Required Audit answer validation from the previous round remains active?

## 6. Implementation Scope

Implement a small usage-layer hardening change. Do not rewrite the gate architecture.

Required feature A: command-plan recommendation.

Update `command-plan` so that when all of the following are true:

- the active decision is APPROVED;
- closeout is allowed by gate-profile;
- the mainline is an engineering/tooling/state round where `run-closeout` is supported;
- the decision does not explicitly prohibit `run-closeout`;

then `recommended_next_action` should prefer the exact command:

```powershell
python -m reverse_agent.project_gate run-closeout --state-dir project_state --round-id <active_round_id>
```

Manual command-plan execution must remain as fallback when `run-closeout` is not supported, closeout is not allowed, decision metadata is invalid, or the decision explicitly requires manual steps.

Required feature B: forbidden live build recommendation guard.

When the active decision's Do Not Do section forbids live `python -m reverse_agent.project_state build`, command-plan must not list that command as a required or recommended command. If a status/build-like command is needed, it must be represented as a non-mutating status/read command or omitted with an explicit reason.

Required feature C: documentation.

Add or update a concise documentation page, preferably `docs/run_closeout.md`, explaining:

1. `decision_packet.md` remains the execution authority.
2. `task_packet.json` is advisory only.
3. `run-closeout` is the default engineering-round closeout command after implementation work.
4. Evidence written by `run-closeout`: `pytest_result.txt`, `codex_execution_report.md`, `project_state/gates/*.json`, and round archive files.
5. Required Audit answers must be substantive for `SUCCESS / ACCEPTED`.
6. Manual command-plan execution is fallback only.
7. Live `project_state build` must not be run when the active decision forbids it.

Add a short README pointer to the new documentation.

Required feature D: tests.

Add tests for at least:

1. command-plan recommends `run-closeout` for an approved engineering decision with closeout allowed;
2. command-plan keeps manual fallback when decision metadata is invalid or closeout is not allowed;
3. command-plan does not require/recommend live `project_state build` when the decision forbids it;
4. documentation file contains the canonical `run-closeout` command and Required Audit warning;
5. previous Required Audit answer validation remains active for SUCCESS reports.

Allowed source/test/doc files:

- `reverse_agent/project_gate.py`
- `reverse_agent/project_state.py`
- `tests/test_project_gate.py`
- `tests/test_project_state.py`
- `README.md`
- `docs/run_closeout.md`

Allowed project_state outputs:

- `project_state/codex_execution_report.md`
- `project_state/pytest_result.txt`
- `project_state/gates/*.json`
- `project_state/rounds/round_20260620_run_closeout_usage_solidification_v1/*`

## 7. Tests

Run and record:

```powershell
Set-Location F:\reverse-agent
Get-Location
Test-Path F:\reverse-agent
git rev-parse --show-toplevel
git status --short

python -m reverse_agent.project_gate decision-lint --state-dir project_state
python -m reverse_agent.project_gate preflight --state-dir project_state
python -m pytest tests/test_project_gate.py tests/test_project_state.py -q
python -m reverse_agent.project_gate command-plan --state-dir project_state --json
python -m reverse_agent.project_gate run-closeout --state-dir project_state --round-id round_20260620_run_closeout_usage_solidification_v1
python -m reverse_agent.project_gate final-check --state-dir project_state
```

The final `command_plan.json` must recommend `run-closeout` for this round, not `record_and_follow_command_plan_manually`. The final `codex_execution_report.md` must include substantive Required Audit answers. The final `final_gate_result.json` must be `PASSED`.

## 8. Stop Conditions

Stop and report `REWORK_REQUIRED` or `BLOCKED` if:

1. command-plan still recommends manual command-plan execution as primary action for this supported engineering closeout round;
2. command-plan recommends or requires live `project_state build` despite the decision forbidding it;
3. documentation is missing or omits the canonical run-closeout command;
4. documentation presents task_packet as execution authority;
5. Required Audit answer validation regresses;
6. old manual fallback behavior breaks;
7. pytest fails;
8. run-closeout cannot archive the round;
9. close-round fails;
10. after-close final-check fails;
11. final-check has any FAIL;
12. report-summary synthesis differs from `codex_report_summary`;
13. final gate contains stale IDs from another round;
14. live root state files are promoted or mutated;
15. source/doc changes exceed allowed files;
16. any reverse-solving progress is claimed.
