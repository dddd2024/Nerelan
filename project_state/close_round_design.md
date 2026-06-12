# close-round Design

## Goal

`close-round` is a thin closeout gate for an already executed project round. It should close a round only when the active decision, Codex report, pytest result, command plan, final gate, and archive contract already agree.

This design is intentionally read-mostly and composition-oriented. A future implementation should reuse existing `project_gate` and `project_state` capabilities instead of adding a parallel parser, a new state machine, or a workflow runner.

## Responsibility Boundary

`close-round` may:

- Validate that the current round is ready to close.
- Reuse existing `final-check` logic.
- Reuse existing `archive-round` logic.
- Write or update `project_state/gates/final_gate_result.json`.
- Return a structured result for humans and automation.

`close-round` must not:

- Generate the next decision packet.
- Modify `project_state/decision_packet.md`.
- Execute the command plan.
- Run pytest.
- Run solvers, samples, tool automation, runtime probes, debuggers, hooks, emulators, or sidecars.
- Read full `solve_reports/` or full `PROJECT_PROGRESS_LOG.txt`.
- Delete, merge, compact, or migrate existing `project_state/rounds/` archives.
- Change the formal schemas for `decision_packet.md`, `codex_execution_report.md`, or `pytest_result.txt`.

The command is a closeout coordinator, not an executor.

## Proposed CLI Contract

Primary command:

```bash
python -m reverse_agent.project_gate close-round --state-dir project_state --round-id <round_id>
```

JSON mode:

```bash
python -m reverse_agent.project_gate close-round --state-dir project_state --round-id <round_id> --json
```

Default text output should be a compact status summary:

- `close-round: CLOSED|BLOCKED|FAILED`
- `decision_id`
- `report_id`
- `round_id`
- check lines with `PASS`, `WARN`, or `FAIL`
- `archive_status`
- `recommended_next_action`

`--json` should print the full structured payload and should still write the same gate artifact(s) as non-JSON mode when the command reaches a write step.

## Exit Codes

- `0`: round closed, or already closed with identical archive and passing final gate.
- `1`: close was blocked by unmet preconditions or failed validation.
- `2`: CLI usage error, invalid `--state-dir`, invalid `--round-id`, unreadable required files, or malformed JSON/Markdown metadata that prevents checks from running.

The implementation should keep `WARN` nonzero only if the warning prevents a safe close. A warning-only final gate that existing policy treats as closable should remain compatible with current behavior.

## JSON Output Draft

```json
{
  "schema_version": 1,
  "gate_name": "close-round",
  "close_status": "CLOSED",
  "decision_id": "decision_example",
  "report_id": "report_example",
  "round_id": "round_example",
  "state_dir": "project_state",
  "generated_at": "2026-06-12T00:00:00Z",
  "checks": [
    {
      "name": "decision_approved",
      "status": "PASS",
      "detail": "decision_meta exists and status is APPROVED"
    }
  ],
  "actions": [
    {
      "name": "final_check_before_archive",
      "status": "PASS",
      "artifact": "project_state/gates/final_gate_result.json"
    },
    {
      "name": "archive_round",
      "status": "created",
      "artifact": "project_state/rounds/round_example/round_manifest.json"
    },
    {
      "name": "final_check_after_archive",
      "status": "PASS",
      "artifact": "project_state/gates/final_gate_result.json"
    }
  ],
  "archive": {
    "status": "archived",
    "round_manifest_path": "project_state/rounds/round_example/round_manifest.json",
    "files": [
      "codex_execution_report.md",
      "decision_packet.md",
      "pytest_result.txt",
      "round_manifest.json"
    ]
  },
  "blocking_reasons": [],
  "warnings": [],
  "recommended_next_action": "no_action_required"
}
```

## Required Preconditions

`close-round` must stop before archiving unless all required preconditions pass:

- `decision_meta` exists and `status == APPROVED`.
- `decision.round_id == --round-id`.
- `codex_report_summary` exists.
- `report.based_on_decision_id == decision.decision_id`.
- `report.round_id == decision.round_id == --round-id`.
- `pytest_result_summary` exists and matches the report.
- `pytest_result_summary.tests_ran` covers `codex_report_summary.tests_ran`.
- If the report records `command-plan`, `project_state/gates/command_plan.json` exists, has `plan_status == PASSED`, matches the decision/report ids, covers report and pytest commands, and recorded command exit codes match `expected_exit_codes`.
- Existing `final-check` can pass under the current project policy before closure.
- `codex_report_summary.files_changed` covers current `git status --short` paths that are in scope for this round.
- `codex_report_summary.generated_artifacts` covers the closeout gate artifacts and expected round archive files.
- Forbidden paths are absent from reported and actual changed files.
- `project_state` package classification remains compact: `gates/*.json` are `derived_cache`, `rounds/<round_id>/*` are `archive`, and historical archive entries are not expanded into default context.
- Stale or missing sample artifacts are not claimed as current evidence for an engineering round.

## Execution Actions

The future implementation should perform only these actions, in order:

1. Load active metadata with existing `project_state` parsers.
2. Validate the preconditions above.
3. Run or call existing `final_check(state_dir=..., repo_root=...)` and write `project_state/gates/final_gate_result.json`.
4. If the round is not archived, call existing `archive_round(state_dir=..., round_id=...)` without `include_state_snapshot` and without `include_diff`.
5. If the round is already archived, accept only an idempotent identical archive; otherwise stop with `FAILED`.
6. Re-run or reuse existing `final_check` after archive creation so archive consistency is proven.
7. Return the structured result.

No command-plan command should be executed by `close-round`. The command plan is evidence to validate, not work to run.

## Failure Modes and Stop Conditions

`close-round` must not close when:

- The active decision is missing, malformed, not `APPROVED`, stale, or already consumed by a different report.
- The requested `--round-id` does not match the decision and report.
- Report or pytest summary metadata is missing or mismatched.
- Required command-plan consistency checks fail.
- `final-check` fails under current policy.
- `files_changed` omits in-scope git diff paths.
- Forbidden files or directories are present.
- Archive creation would overwrite a different existing manifest.
- A credible close requires running tests, executing commands, modifying schemas, changing state-machine behavior, or generating a next decision.
- A credible close requires reading full `solve_reports/` or `PROJECT_PROGRESS_LOG.txt`.
- Stale/missing sample artifacts are reinterpreted as current sample evidence.

Blocked and failed results should preserve exact check names and reasons so the next round can fix the missing prerequisite rather than rerunning broad exploration.

## Test Matrix for Minimal Implementation

Success path:

- Closes a healthy engineering round with matching decision/report/pytest ids.
- Creates a minimal archive containing `decision_packet.md`, `codex_execution_report.md`, `pytest_result.txt`, and `round_manifest.json`.
- Writes `project_state/gates/final_gate_result.json`.
- Returns `0` and `close_status == CLOSED`.
- Accepts an already archived identical round as idempotent.

Failure path:

- Fails when `decision_meta` is missing or not `APPROVED`.
- Fails when `--round-id` mismatches decision or report.
- Fails when `codex_report_summary` is missing.
- Fails when `pytest_result_summary` does not match the report.
- Fails when `command_plan.json` is required but missing or mismatched.
- Fails when recorded command exits do not match `command_plan.expected_exit_codes`.
- Fails when `command-plan --json` output recorded in `pytest_result.txt` is abbreviated.
- Fails when `files_changed` does not cover git diff.
- Fails when generated artifacts omit archive files.
- Fails when forbidden paths appear.
- Fails when an existing archive manifest differs.

Compatibility path:

- Preserves existing `preflight`, `command-plan`, `final-check`, `lint-report`, `status`, `doctor`, and `archive-round` behavior.
- Keeps historical sample artifact freshness non-blocking for healthy engineering rounds.
- Keeps `task_packet.json` advisory-only and unable to override `decision_packet.md`.
- Keeps `gates/*.json` classified as `derived_cache`.
- Keeps `rounds/<round_id>/*` classified as archive, not current execution authority.
- Keeps compact state package output from expanding historical archives by default.

## Next Minimal Implementation Round

The next round can implement `project_gate close-round` as a small wrapper around existing functions:

- Add the CLI subcommand in `reverse_agent/project_gate.py`.
- Add a `close_round(...)` function that composes existing parsers, `final_check`, and `archive_round`.
- Add focused tests in `tests/test_project_gate.py` for the matrix above.
- Keep source changes limited to `project_gate.py` unless a missing reusable helper in `project_state.py` is proven necessary.

Do not implement this in the design-only round.
