```json codex_report_summary
{
  "schema_version": 1,
  "report_id": "report_phase2d_harness_resource_budget_20260520",
  "round_id": "round_20260520_phase2d_harness_resource_budget",
  "based_on_decision_id": "decision_phase2d_harness_resource_budget_20260520",
  "status": "SUCCESS",
  "acceptance_recommendation": "ACCEPTED",
  "files_changed": [
    "reverse_agent/harness.py",
    "tests/test_harness_resource_budget.py",
    "project_state/codex_execution_report.md",
    "project_state/pytest_result.txt"
  ],
  "tests_ran": [
    "python -m py_compile reverse_agent\\harness.py",
    "python -m pytest -q tests\\test_harness_resource_budget.py",
    "python -m pytest -q tests\\test_harness.py",
    "python -m pytest -q tests\\test_harness_resume.py",
    "python -m pytest -q tests\\test_harness_artifact_manifest.py",
    "python -m pytest -q tests\\test_harness_compare.py",
    "python -m pytest -q",
    "python -m reverse_agent.project_state status --state-dir project_state",
    "python -m reverse_agent.project_state lint-decision --state-dir project_state",
    "python -m reverse_agent.project_state lint-report --state-dir project_state",
    "python -m reverse_agent.project_state lint-handoff --state-dir project_state",
    "python -m reverse_agent.project_state archive-round --state-dir project_state --round-id round_20260520_phase2d_harness_resource_budget"
  ],
  "generated_artifacts": [
    "project_state/rounds/round_20260520_phase2d_harness_resource_budget/round_manifest.json",
    "project_state/rounds/round_20260520_phase2d_harness_resource_budget/artifact_index.json",
    "project_state/rounds/round_20260520_phase2d_harness_resource_budget/current_state.json",
    "project_state/rounds/round_20260520_phase2d_harness_resource_budget/negative_results.json",
    "project_state/rounds/round_20260520_phase2d_harness_resource_budget/model_gate.json",
    "project_state/rounds/round_20260520_phase2d_harness_resource_budget/task_packet.json",
    "project_state/rounds/round_20260520_phase2d_harness_resource_budget/decision_packet.md",
    "project_state/rounds/round_20260520_phase2d_harness_resource_budget/codex_execution_report.md",
    "project_state/rounds/round_20260520_phase2d_harness_resource_budget/pytest_result.txt",
    "project_state/rounds/round_20260520_phase2d_harness_resource_budget/git_diff.patch"
  ],
  "next_suggested_task": "Have GPT audit Phase 2D resource_budget manifest semantics before authorizing Phase 2E compare strict/path/round commit cleanup or returning to samplereverse runtime work."
}
```

# CODEX_EXECUTION_REPORT

## 2026-05-20 Phase 2D harness resource budget

This pass implements the approved Phase 2D engineering branch from `project_state/decision_packet.md`. It adds a local `resource_budget` record to harness configuration and `run_manifest.json` for reproducibility auditing. It does not advance the `samplereverse` reverse-engineering mainline, run runtime probes, modify `compare_aware_search.py`, modify `olly_scripts`, modify `project_state.py`, change GPT/Codex handoff schemas, enforce process kills, delete artifacts, crop candidates, or implement queue/backpressure/worker scheduling.

## Required Audit

| check | result |
|---|---|
| Current timeout or budget fields | Existing harness config had `copilot_timeout_seconds`; `ToolAutomationConfig` had `ida_timeout_seconds` and `ollydbg_timeout_seconds`. No existing local resource budget structure was present. |
| Existing timeout manifest recording | `copilot_timeout_seconds` is written directly into `pipeline_defaults`; IDA/Olly timeouts are written under `pipeline_defaults.tool_config`. |
| Manifest config structure | `_build_manifest()` builds `config_payload`, hashes it as `config_digest`, writes it as `pipeline_defaults`, and keeps top-level manifest fields such as `schema_version`, `status`, `run_name`, `run_dir`, `started_at`, `dataset_digest`, `git_commit`, and `case_ids`. |
| Resource budget placement | `resource_budget` is written at top level for direct audit visibility and inside `pipeline_defaults` so it is part of the preserved config payload. |
| Config digest decision | `resource_budget` is included in `config_digest`; changing a budget for the same `run_name` is rejected as a different harness config, preserving resume compatibility. |
| CLI naming | Added `--max-case-seconds`, `--max-tool-seconds`, `--max-artifact-bytes`, `--max-recent-artifacts`, `--max-context-pack-bytes`, `--max-candidate-count`, and `--max-probe-candidates`. These names do not conflict with existing operational timeout arguments. |
| Defaults | Defaults match the decision packet: `21600`, `300`, `52428800`, `20`, `1048576`, `5000`, and `50`. |
| Legal values | Each budget value must be a positive integer or `None` / JSON `null`. CLI accepts `null` and `none` case-insensitively. |
| Rejected values | Negative, zero, non-integer, and boolean-like programmatic values are rejected before a run is accepted. |
| Enforcement behavior | Phase 2D only records the budget. It does not override Copilot, IDA, or Olly timeouts, does not terminate processes, does not delete artifacts, and does not modify candidate/probe counts. |
| Equivalent existing feature | No equivalent local `resource_budget` structure was present, so a small harness-owned dataclass was added. |
| Runtime/probe/solve_reports risk | Implementation and tests use temporary harness runs and mocked `run_pipeline`; no runtime probe, model call, reverse-engineering sidecar, or full `solve_reports` scan is introduced. |
| Phase 2C limitations | Compare strictness for missing runs, artifact manifest path schema, and round manifest commit semantics were not changed or expanded; they remain follow-up items. |

## Implementation

- Added `ResourceBudget` to `reverse_agent.harness` and attached it to `HarnessConfig` with decision-packet defaults.
- Added positive-integer-or-null CLI parsing for the seven local budget arguments.
- Wrote budget values into `run_manifest.json` both as top-level `resource_budget` and `pipeline_defaults.resource_budget`.
- Kept existing manifest fields and timeout fields compatible; `resource_budget` is not passed into `run_pipeline`.
- Added focused resource budget regression tests for defaults, digest mismatch, nullable CLI values, invalid CLI values, programmatic validation, and runtime kwargs isolation.

## Verification

| command | result |
|---|---|
| `python -m py_compile reverse_agent\harness.py` | passed |
| `python -m pytest -q tests\test_harness_resource_budget.py` | `9 passed in 0.37s` |
| `python -m pytest -q tests\test_harness.py` | `5 passed in 0.34s` |
| `python -m pytest -q tests\test_harness_resume.py` | `6 passed in 0.42s` |
| `python -m pytest -q tests\test_harness_artifact_manifest.py` | `3 passed in 0.27s` |
| `python -m pytest -q tests\test_harness_compare.py` | `9 passed in 0.30s` |
| `python -m pytest -q` | `384 passed in 48.71s` |
| `python -m reverse_agent.project_state status --state-dir project_state` | passed; active decision is Phase 2D and report is consumed |
| `python -m reverse_agent.project_state lint-decision --state-dir project_state` | passed |
| `python -m reverse_agent.project_state lint-report --state-dir project_state` | passed with expected `round_id` warning against current sample state |
| `python -m reverse_agent.project_state lint-handoff --state-dir project_state` | passed as `REVIEW_COMPLETE` with expected `round_id` warning |
| `python -m reverse_agent.project_state archive-round --state-dir project_state --round-id round_20260520_phase2d_harness_resource_budget` | passed; command returned exit code 0 with no console output |

## State Notes

- The active state still references the sample-derived task and `sr_lhs_thread_follow_timing_20260520_r4`; this pass intentionally followed `execution_scope=decision_packet_controls_current_round` and treated `project_state/decision_packet.md` as authoritative.
- No `samplereverse` artifacts were rebuilt and no harness runtime probe was run.
- Phase 2D project_state lint and archive-round verification passed.

## Next Suggested Task

Have GPT audit the Phase 2D `resource_budget` manifest contract and archive. Do not start Phase 2E compare strict/path/round commit cleanup or return to `samplereverse` runtime work until a fresh decision packet explicitly authorizes it.
