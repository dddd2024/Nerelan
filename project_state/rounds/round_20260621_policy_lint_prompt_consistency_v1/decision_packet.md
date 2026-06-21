```json decision_meta
{
  "schema_version": 1,
  "decision_id": "decision_20260621_policy_lint_prompt_consistency_v1",
  "round_id": "round_20260621_policy_lint_prompt_consistency_v1",
  "based_on_state_build_id": "state_20260618_134029_d6bd033d2532",
  "based_on_state_digest": "d6bd033d25324345cfd8ada0ac65db42bc86eb5017f3ffc92906fcd8b71cacb5",
  "status": "APPROVED",
  "mainline": "engineering_branch",
  "skill_profiles": ["reverse-agent-iteration@v2"]
}
```

```json decision_contract
{
  "previous_decision_id": "decision_20260621_decision_command_plan_conflict_lint_v1",
  "previous_round_id": "round_20260621_decision_command_plan_conflict_lint_v1",
  "previous_acceptance": "ACCEPTED",
  "primary_goal": "Add policy-lint / prompt-consistency v1 to detect prompt-skill-documentation drift against current engineering rules.",
  "command_plan_authority_required": true,
  "accepted_requires_policy_lint_tests": true,
  "accepted_requires_final_check_passed": true,
  "allowed_source_files": [
    "reverse_agent/project_gate.py",
    "tests/test_project_gate.py"
  ],
  "allowed_state_artifacts": [
    "project_state/codex_execution_report.md",
    "project_state/pytest_result.txt",
    "project_state/gates/command_plan.json",
    "project_state/gates/gate_profile_plan.json",
    "project_state/gates/preflight_result.json",
    "project_state/gates/policy_lint_result.json",
    "project_state/gates/report_summary_synthesis.json",
    "project_state/gates/final_gate_result.json",
    "project_state/gates/round_baseline.json",
    "project_state/gates/round_delta_summary.json",
    "project_state/gates/round_close_snapshot.json",
    "project_state/gates/run_closeout_result.json",
    "project_state/rounds/round_20260621_policy_lint_prompt_consistency_v1/*"
  ],
  "forbidden_mutated_paths": [
    "project_state/current_state.json",
    "project_state/task_packet.json",
    "project_state/artifact_index.json",
    "project_state/negative_results.json",
    ".codex-skills/registry.json"
  ]
}
```

# DECISION_PACKET

## 1. Goal

Implement `policy-lint` / prompt-consistency v1 so the project can detect rule drift between current engineering behavior and long-lived text contracts such as skills, prompts, docs, and decision templates.

The previous accepted round added early decision/command-plan conflict detection. The next engineering gap is policy drift: the code can evolve to `fast/standard/full`, command-plan authority, supported report statuses, and no-default-heavy-artifact rules while prompts or skills continue to say `medium`, make Tests authoritative, allow `task_packet` to control execution, or write unsupported report statuses.

This round must add a small, bounded policy-lint capability. It should detect high-value drift patterns and produce a structured artifact without rewriting the whole policy system or generating prompts from a manifest.

## 2. Current Evidence

Mainline: `engineering_branch`.

`task_packet.json` is background only. It still describes stale `samplereverse` work and must not control this round.

The previous round `decision_20260621_decision_command_plan_conflict_lint_v1` is accepted. Its evidence showed:

- `codex_execution_report.md` had `status=SUCCESS` and `acceptance_recommendation=ACCEPTED`.
- `final_gate_result.json` had `gate_status=PASSED`, no blocking reasons, no warnings, and `recommended_next_action=no_action_required`.
- `command_plan_execution_authority` passed.
- `report_summary_fields_match_synthesis` passed.
- decision/command-plan conflict detection was added in preflight/decision-lint with tests.

Existing relevant capabilities to reuse:

- `reverse_agent.project_gate` CLI structure and artifact-writing conventions
- existing `decision-lint`, `preflight`, `command-plan`, `report-summary`, and `final-check`
- current profile constants and command kinds: `fast`, `standard`, `full`
- current supported report status values: `SUCCESS`, `PARTIAL`, `FAILED`, `BLOCKED`
- skill registry parsing from `.codex-skills/registry.json`
- tests in `tests/test_project_gate.py`

This is not a reverse-solving round. Do not inspect or run sample binaries. Do not use IDA, Ghidra, debuggers, emulators, runtime probes, harnesses, or full `solve_reports/`.

## 3. Do Not Do

Do not redesign the policy system or introduce a database, message queue, or workflow engine.

Do not create a full `policy_manifest.json` yet unless a very small constant table inside `project_gate.py` is insufficient. This round is policy-lint v1, not a policy-generation system.

Do not create or rewrite long prompt documents in this round. Detect drift first; storing canonical prompts in the repo can be a later round.

Do not weaken `command_plan_execution_authority`, `decision_command_plan_conflict`, `report_summary_fields_match_synthesis`, or final-check.

Do not change profile names. The current profile names are `fast`, `standard`, and `full`; do not introduce `medium` as a profile.

Do not mutate `project_state/current_state.json`, `project_state/task_packet.json`, `project_state/artifact_index.json`, `project_state/negative_results.json`, or `.codex-skills/registry.json`.

Do not continue `samplereverse` solving. Do not run samples, solvers, harnesses, runtime probes, IDA/Ghidra, debuggers, emulators, GUI workflows, or full `solve_reports/` scans.

Do not push, commit, create PRs, switch branches, rebase, merge, or modify remote state unless the user explicitly requests it in the current message.

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

Then inspect only files relevant to this engineering check:

1. `reverse_agent/project_gate.py`
2. `tests/test_project_gate.py`
3. `.codex-skills/registry.json`
4. `.codex-skills/reverse-agent-iteration/SKILL.md`
5. `.codex-skills/samplereverse-frontier/SKILL.md` only for read-only drift scanning
6. `README.md` only if policy-lint v1 scans README text
7. `docs/prompts/*` only if such files already exist
8. `project_state/gates/command_plan.json`
9. `project_state/gates/final_gate_result.json`
10. `project_state/gates/report_summary_synthesis.json`

Historical files may be read only by exact path when needed for a focused regression fixture. Do not scan entire `project_state/rounds/`, full `solve_reports/`, or full `PROJECT_PROGRESS_LOG.txt`.

## 5. Required Audit

Answer all items in `project_state/codex_execution_report.md` before claiming success:

1. What policy drift patterns does policy-lint v1 detect?
2. Which files are scanned by default, and why are heavy paths such as full `solve_reports/` excluded?
3. How does policy-lint detect obsolete profile naming such as `medium` when the project supports `fast/standard/full`?
4. How does policy-lint detect text that contradicts command-plan authority, such as making Tests authoritative over command-plan?
5. How does policy-lint detect text that makes `task_packet` execution authority over `decision_packet`?
6. How does policy-lint detect unsupported report statuses such as using `COMPLETED_WITH_LIMITATIONS` as `codex_report_summary.status`?
7. How are findings classified as FAIL, WARN, or INFO so existing docs/skills do not produce noisy false failures?
8. What regression tests prove policy-lint catches real drift while allowing valid current project wording?

## 6. Implementation Scope

Implement one bounded feature: `policy-lint` / prompt-consistency v1.

Allowed source changes:

- `reverse_agent/project_gate.py`
- `tests/test_project_gate.py`

Allowed state/artifact updates:

- `project_state/codex_execution_report.md`
- `project_state/pytest_result.txt`
- `project_state/gates/command_plan.json`
- `project_state/gates/gate_profile_plan.json`
- `project_state/gates/preflight_result.json`
- `project_state/gates/policy_lint_result.json`
- `project_state/gates/report_summary_synthesis.json`
- `project_state/gates/final_gate_result.json`
- `project_state/gates/round_baseline.json`
- `project_state/gates/round_delta_summary.json`
- `project_state/gates/round_close_snapshot.json`
- `project_state/gates/run_closeout_result.json`
- `project_state/rounds/round_20260621_policy_lint_prompt_consistency_v1/*` only if command-plan authorizes closeout

Required implementation behavior:

1. Add a CLI entrypoint such as `python -m reverse_agent.project_gate policy-lint --state-dir project_state`.
2. Write a structured artifact at `project_state/gates/policy_lint_result.json` with schema_version, gate_name, gate_status, decision_id, round_id, scanned_files, findings, warnings, blocking_reasons, and recommended_next_action.
3. Scan only bounded text files: active skill files, current decision packet, README/docs prompt files if present, and any explicit small prompt/template files already in repo. Do not scan full `solve_reports/`, full `project_state/rounds/`, or large runtime outputs.
4. Detect at least these drift classes:
   - obsolete profile name `medium` used as a project profile instead of `standard`;
   - Tests or prompt text making Tests authoritative over command-plan;
   - text making `task_packet` current execution authority over `decision_packet`;
   - default full `solve_reports/` or full `PROJECT_PROGRESS_LOG.txt` reads;
   - unsupported `codex_report_summary.status` values such as `COMPLETED_WITH_LIMITATIONS`;
   - `.codex-skills/` text containing dynamic one-run facts such as candidate values, run names, artifact paths, local machine paths, or runtime metrics.
5. Classify findings conservatively: current-decision hard contradictions may be FAIL; long-lived prompt/skill drift may start as WARN unless it directly violates `.codex-skills/` hygiene.
6. Add `policy-lint` to command-plan only if this round implements the CLI and tests can prove it does not break existing fast/standard/full behavior. Otherwise document it as a manually runnable diagnostic and do not execute it outside command-plan authorization.
7. Add focused regression tests for all required drift classes and for valid current wording.
8. Preserve existing decision-lint, preflight, command-plan, report-summary, final-check, closeout, and command-plan authority behavior.

Do not add prompt generation, a full policy manifest, or `execution_log.json` in this round.

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

If preflight passes, run command-plan and follow only command-plan-authorized commands:

```powershell
python -m reverse_agent.project_gate command-plan --state-dir project_state --json
```

Targeted tests:

```powershell
python -m pytest tests/test_project_gate.py -q
```

Run policy-lint only if the newly generated command-plan explicitly includes or authorizes it after implementation:

```powershell
python -m reverse_agent.project_gate policy-lint --state-dir project_state
```

Final validation commands, only when authorized by command-plan:

```powershell
python -m reverse_agent.project_gate decision-lint --state-dir project_state
python -m pytest tests/test_project_gate.py tests/test_project_state.py -q
python -m reverse_agent.project_gate report-summary --state-dir project_state
python -m reverse_agent.project_gate final-check --state-dir project_state
```

Run closeout only if command-plan explicitly includes or authorizes the closeout command for this round:

```powershell
python -m reverse_agent.project_gate run-closeout --state-dir project_state --round-id round_20260621_policy_lint_prompt_consistency_v1
```

If closeout runs, rerun report-summary and final-check afterward.

Record all executed commands, stdout/stderr, exit codes, and final conclusion in `project_state/pytest_result.txt`. The structured summary must match this decision_id and round_id.

## 8. Stop Conditions

Stop and report `BLOCKED` or `REWORK_REQUIRED` if:

1. preflight fails before implementation for unrelated reasons;
2. implementing policy-lint requires broad redesign of project_gate, command-plan, report-summary, final-check, closeout, skill registry, or execution-log storage;
3. source changes outside `reverse_agent/project_gate.py` and `tests/test_project_gate.py` are needed;
4. the fix requires running samples, solvers, harnesses, IDA/Ghidra, debuggers, emulators, runtime probes, or full `solve_reports/` scans;
5. policy-lint scans heavy runtime outputs or full historical directories by default;
6. policy-lint produces blocking failures on valid current project wording without a precise drift reason;
7. command-plan authority, decision-command-plan conflict detection, report-summary, final-check, or closeout regresses;
8. `codex_execution_report.md`, `pytest_result.txt`, or gate artifacts use stale decision_id/round_id;
9. tests fail or any required command exit code is nonzero;
10. closeout archive files are created but not listed in `files_changed` and `generated_artifacts`.
