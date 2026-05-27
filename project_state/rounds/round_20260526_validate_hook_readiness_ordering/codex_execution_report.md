```json codex_report_summary
{
  "schema_version": 1,
  "report_id": "report_20260526_validate_hook_readiness_ordering",
  "round_id": "round_20260526_validate_hook_readiness_ordering",
  "based_on_decision_id": "decision_20260526_validate_hook_readiness_ordering",
  "status": "BLOCKED",
  "acceptance_recommendation": "BLOCKED",
  "files_changed": [
    "reverse_agent/olly_scripts/compare_pre_compare_handoff_target_probe.py",
    "reverse_agent/sidecar_health.py",
    "reverse_agent/project_state.py",
    "tests/test_project_state.py",
    "project_state/current_state.json",
    "project_state/artifact_index.json",
    "project_state/model_gate.json",
    "project_state/task_packet.json",
    "project_state/codex_execution_report.md",
    "project_state/pytest_result.txt"
  ],
  "tests_ran": [
    "python -m py_compile reverse_agent/strategies/compare_aware_search.py reverse_agent/project_state.py reverse_agent/sidecar_health.py reverse_agent/olly_scripts/compare_pre_compare_handoff_target_probe.py",
    "python -m pytest -q tests/test_compare_aware_search_strategy.py -k \"arg0 or observation or sidecar or ui or trigger or timeout or lifecycle or classification or readiness\"",
    "python -m pytest -q tests/test_project_state.py -k \"sidecar or ui or trigger or timing or observation or blocker or report or runtime or projection or readiness\"",
    "python -m pytest -q tests/test_project_state.py",
    "bounded rerun: run_compare_real_lhs_provenance_audit(..., run_name=\"sr_arg0_hook_readiness_ordering_20260526_r1\")",
    "python -m reverse_agent.project_state build --reports-dir solve_reports --sample samplereverse --run-name sr_arg0_hook_readiness_ordering_20260526_r1",
    "python -m reverse_agent.project_state lint-decision --state-dir project_state",
    "python -m reverse_agent.project_state status --state-dir project_state",
    "python -m reverse_agent.project_state lint-report --state-dir project_state",
    "git diff --check"
  ],
  "generated_artifacts": [
    "solve_reports/harness_runs/sr_arg0_hook_readiness_ordering_20260526_r1/reports/tool_artifacts/samplereverse_patched/compare_real_lhs_provenance_audit/compare_real_lhs_provenance_audit.json",
    "solve_reports/harness_runs/sr_arg0_hook_readiness_ordering_20260526_r1/case_results/samplereverse-compare-producer-backtrace.json",
    "solve_reports/harness_runs/sr_arg0_hook_readiness_ordering_20260526_r1/summary.json",
    "solve_reports/harness_runs/sr_arg0_hook_readiness_ordering_20260526_r1/run_manifest.json",
    "project_state/current_state.json",
    "project_state/artifact_index.json",
    "project_state/model_gate.json",
    "project_state/task_packet.json",
    "project_state/codex_execution_report.md",
    "project_state/pytest_result.txt"
  ]
}
```

# CODEX_EXECUTION_REPORT

## 2026-05-27 Hook Readiness Ordering

Result: `BLOCKED` / `BLOCKED`.

This round executed `decision_20260526_validate_hook_readiness_ordering` on the reverse-solving mainline. The code fix and bounded rerun completed, and the blocker advanced from `hooks_not_ready_before_ui_trigger` to `ui_trigger_executed_but_compare_arg_observation_missing`. Final full acceptance is blocked only by a decision-packet metadata conflict: the required post-rerun `project_state build` changed `current_state.state_digest`, while the decision packet explicitly forbids rewriting `project_state/decision_packet.md`.

## Code Changes

- `reverse_agent/olly_scripts/compare_pre_compare_handoff_target_probe.py`: added an explicit `waiting_for_hooks_ready` stage before UI connection/trigger. If Python does not receive the JS `hooks_installed` stage within the existing readiness window, the sidecar now records `hooks_ready_barrier_timeout_before_ui_trigger`, sets `ui_trigger_status=not_triggered_hooks_ready_timeout`, and stops before clicking the UI.
- `reverse_agent/sidecar_health.py`: classifies the readiness-timeout stop as `sidecar_runtime_precondition_failed`, and classifies contradictory telemetry where hooks are ready but `ui_trigger_after_hooks_installed=false` as `compare_arg_payload_schema_gap`.
- `reverse_agent/project_state.py` and `tests/test_project_state.py`: project the new blockers into the existing sidecar observation task path and cover them with focused tests.

## Bounded Rerun

Command:

```text
run_compare_real_lhs_provenance_audit(
  target=Path("solve_reports/samplereverse_patched.exe"),
  artifacts_dir=Path("solve_reports/harness_runs/sr_arg0_hook_readiness_ordering_20260526_r1/reports/tool_artifacts/samplereverse_patched/compare_real_lhs_provenance_audit"),
  transform_model=SamplereverseTransformModel(),
  per_probe_timeout=2.2,
  post_handoff_exception_payload={"classification": "compare_reached_but_path_unresolved"},
  run_name="sr_arg0_hook_readiness_ordering_20260526_r1"
)
```

Run name:

```text
sr_arg0_hook_readiness_ordering_20260526_r1
```

Current artifact:

```text
solve_reports\harness_runs\sr_arg0_hook_readiness_ordering_20260526_r1\reports\tool_artifacts\samplereverse_patched\compare_real_lhs_provenance_audit\compare_real_lhs_provenance_audit.json
```

Candidate set used exactly:

```text
78d540b49c59077041414141414141
5a3e7f46ddd474d041414141414141
78d540b49c59076f41414141414141
```

Rerun telemetry:

```text
classification = instrumentation_incomplete
sidecar_observation_blocker = ui_trigger_executed_but_compare_arg_observation_missing
lhs_writer_classification_blocker = ui_trigger_executed_but_compare_arg_observation_missing
hook_install_status = installed for all 3 candidates
hook_count/requested_hook_count = 4/4 for all 3 candidates
hooks_ready_barrier_seen = true for all 3 candidates
hooks_ready_before_ui_trigger = true for all 3 candidates
ui_trigger_after_hooks_installed = true for all 3 candidates
ui_trigger_status = button_triggered for all 3 candidates
ui_trigger_timing_status = hooks_ready_before_ui_trigger for all 3 candidates
observation_count = 0 for all 3 candidates
post_ui_observation_count = 0 for all 3 candidates
actual_compare.entry_status = confirmed
actual_compare.arg0/arg1 maps = empty
```

`artifact_index.latest_artifacts_v2.compare_real_lhs_provenance_audit.freshness` is `current`, with `source_run=sr_arg0_hook_readiness_ordering_20260526_r1`.

## Scope Audit

- No Base64/RC4 breakpoint probe was run.
- No old `sample_solver` path was used.
- No candidate search, frontier expansion, beam/topN/budget expansion, or timeout expansion was performed.
- No final-writer chase was performed.
- No full `solve_reports/` scan was needed.
- `PROJECT_PROGRESS_LOG.txt` was not edited.
- `project_state/decision_packet.md` was not modified.
- The new artifact, not stale compare_probe or stale handoff artifacts, is the current compare-real-LHS evidence.
- CompareProbe fallback remains diagnostic-only and is not promoted to provenance.

## Verification

```text
python -m py_compile reverse_agent/strategies/compare_aware_search.py reverse_agent/project_state.py reverse_agent/sidecar_health.py reverse_agent/olly_scripts/compare_pre_compare_handoff_target_probe.py
passed

python -m pytest -q tests/test_compare_aware_search_strategy.py -k "arg0 or observation or sidecar or ui or trigger or timeout or lifecycle or classification or readiness"
passed: 48 passed, 148 deselected

python -m pytest -q tests/test_project_state.py -k "sidecar or ui or trigger or timing or observation or blocker or report or runtime or projection or readiness"
passed: 63 passed, 85 deselected

python -m pytest -q tests/test_project_state.py
passed: 148 passed

python -m reverse_agent.project_state build --reports-dir solve_reports --sample samplereverse --run-name sr_arg0_hook_readiness_ordering_20260526_r1
passed

python -m reverse_agent.project_state status --state-dir project_state
passed with missing: [] and latest_harness_run=solve_reports\harness_runs\sr_arg0_hook_readiness_ordering_20260526_r1

python -m reverse_agent.project_state lint-decision --state-dir project_state
failed as expected after rerun build: based_on_state_digest does not match current_state.state_digest

python -m reverse_agent.project_state lint-report --state-dir project_state
passed with warnings: report_status is BLOCKED and report round was not archived yet

git diff --check
passed; only CRLF working-copy warnings were emitted
```

## Blocker

The implemented work meets the runtime evidence objective: UI trigger now occurs after hooks are ready, and the blocker advanced to `ui_trigger_executed_but_compare_arg_observation_missing`. However, the closeout checklist cannot also make `lint-decision` pass without updating `project_state/decision_packet.md` to the new digest, and this decision explicitly forbids modifying that file. The correct final state is therefore blocked pending a refreshed decision packet for `state_20260527_084821_6904311ce1cc`.
