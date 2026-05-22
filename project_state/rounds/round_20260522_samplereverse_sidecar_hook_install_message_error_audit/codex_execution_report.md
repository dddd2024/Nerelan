```json codex_report_summary
{
  "schema_version": 1,
  "report_id": "report_samplereverse_sidecar_hook_install_message_error_audit_20260522",
  "round_id": "round_20260522_samplereverse_sidecar_hook_install_message_error_audit",
  "based_on_decision_id": "decision_samplereverse_sidecar_hook_install_message_error_audit_20260522",
  "status": "BLOCKED",
  "acceptance_recommendation": "REWORK_REQUIRED",
  "files_changed": [
    "reverse_agent/olly_scripts/compare_pre_compare_handoff_target_probe.py",
    "reverse_agent/strategies/compare_aware_search.py",
    "tests/test_compare_aware_search_strategy.py",
    "project_state/codex_execution_report.md",
    "project_state/pytest_result.txt"
  ],
  "tests_ran": [
    "python -m py_compile reverse_agent\\olly_scripts\\compare_pre_compare_handoff_target_probe.py reverse_agent\\strategies\\compare_aware_search.py",
    "python -m pytest -q tests\\test_compare_aware_search_strategy.py -k \"compare_lhs_last_writer or compare_real_lhs_last_writer or pre_compare_handoff\"",
    "python -m pytest -q tests\\test_compare_aware_search_strategy.py",
    "bounded runtime sidecar sr_lhs_last_writer_hook_install_message_error_audit_20260522_r1",
    "python -m reverse_agent.project_state status --state-dir project_state",
    "python -m reverse_agent.project_state lint-decision --state-dir project_state",
    "python -m reverse_agent.project_state lint-report --state-dir project_state",
    "python -m reverse_agent.project_state lint-handoff --state-dir project_state",
    "python -m reverse_agent.project_state archive-round --state-dir project_state --round-id round_20260522_samplereverse_sidecar_hook_install_message_error_audit"
  ],
  "generated_artifacts": [
    "solve_reports/harness_runs/sr_lhs_last_writer_hook_install_message_error_audit_20260522_r1/reports/tool_artifacts/samplereverse_patched/compare_lhs_last_writer_provenance_audit/compare_lhs_last_writer_provenance_audit.json",
    "project_state/rounds/round_20260522_samplereverse_sidecar_hook_install_message_error_audit/round_manifest.json",
    "project_state/rounds/round_20260522_samplereverse_sidecar_hook_install_message_error_audit/codex_execution_report.md",
    "project_state/rounds/round_20260522_samplereverse_sidecar_hook_install_message_error_audit/pytest_result.txt",
    "project_state/rounds/round_20260522_samplereverse_sidecar_hook_install_message_error_audit/git_diff.patch"
  ]
}
```

# CODEX_EXECUTION_REPORT

## 2026-05-22 Samplereverse sidecar hook-install message-error audit

This pass executes `decision_samplereverse_sidecar_hook_install_message_error_audit_20260522` against state build `state_20260520_052928_8a77e6637c6c` / digest `8a77e6637c6cf7578750af01b447ccf7c39541df00661e8c882bc89cd826339d`.

Result: `BLOCKED`. The code now separates Frida message errors, Python/runtime exceptions, script load errors, hook-install errors, `hooks_installed` stage visibility, and per-hook install results. The bounded runtime rerun still could not confirm hook install: the sidecar process timed out before lifecycle fields advanced past the initial `not_started` payload, while CompareProbe fallback captured diagnostic compare args. Because `hooks_installed_stage_seen=false`, this is not a success and no provenance is claimed.

## Required Audit

| check | result |
|---|---|
| Why previous report was `REWORK_REQUIRED` | `report_samplereverse_sidecar_hook_install_vs_compareprobe_divergence_20260521` correctly avoided success, but it still left `frida_message_error_count` semantically suspect and did not output per-hook install results for `0x258c`, `0x2559`, `0x1b50`. |
| `on_message` error flow | Frida `message.type == "error"` now enters `frida_message_errors`; JS `compare_pre_compare_handoff_target_error` remains a structured send payload and is counted as hook-install error, not Frida message error. |
| `errors` vs `script_errors` risk | The old `frida_message_error_count = len(script_errors)` conflated Python/load exceptions with Frida message errors. This is fixed by separate `frida_message_errors`, `python_exceptions`, and `hook_install_errors`. |
| Hook-install result schema | JS now emits `compare_pre_compare_handoff_target_hook_install_result` per point with `name`, `module_offset`, `install_status`, `address`, `error`. |
| Required hook points | The bounded hook set remains exactly `0x258c` static compare, `0x2559` post-handoff LHS reload, and `0x1b50` handoff helper candidate. |
| `hooks_installed` stage semantics | Payload now records `hooks_installed_stage_seen` and `hooks_installed_stage_hook_count`; stage seen with `hook_count=0` maps to `hook_loop_completed_zero_installed`. |
| Stage not seen after load | If `script_load_status=loaded` but stage is absent, root cause maps to `hooks_installed_stage_missing_after_script_load`, not generic timeout. |
| Current runtime root cause | Current bounded rerun produced only initial sidecar payloads: `script_load_status=not_started`, `hooks_installed_stage_seen=false`, and `instrumentation_failure_stage=timeout_before_script_lifecycle_observation`. |
| CompareProbe fallback | Fallback captured diagnostic compare args, but `compare_probe_fallback_is_provenance=false`; no fallback arg0 address was linked to write events or runtime-backed writer identity. |
| Project state rebuild | Not rebuilt. This direct bounded sidecar artifact is reported explicitly and is not treated as live indexed current artifact. |
| `PROJECT_PROGRESS_LOG.txt` handling | Untouched. |

## Implementation

- Updated `compare_pre_compare_handoff_target_probe.py` to emit per-hook install results, separate Frida/Python/hook-install error counts, and expose `hooks_installed_stage_seen` plus hook-count evidence.
- Updated `compare_aware_search.py` to aggregate the new fields at candidate and top-level `compare_lhs_last_writer_provenance_audit` scope, including precise root causes for stage-missing and zero-installed cases.
- Added regression coverage for error separation, hook-install counting, stage missing after script load, zero-installed stage handling, fixed two-candidate scope, and fallback non-provenance.

## Runtime Artifact

| field | value |
|---|---|
| run_name | `sr_lhs_last_writer_hook_install_message_error_audit_20260522_r1` |
| artifact | `solve_reports/harness_runs/sr_lhs_last_writer_hook_install_message_error_audit_20260522_r1/reports/tool_artifacts/samplereverse_patched/compare_lhs_last_writer_provenance_audit/compare_lhs_last_writer_provenance_audit.json` |
| classification | `instrumentation_incomplete` |
| instrumentation_failure_stage | `timeout_before_script_lifecycle_observation` |
| root_cause_hypothesis | `timeout_before_script_lifecycle_observation` |
| hook_install_status / hook_count / requested_hook_count | `not_confirmed_stage_missing` / `0` / `3` |
| hooks_installed_stage_seen / hooks_installed_stage_hook_count | `false` / `0` |
| hook_install_error_count / frida_message_error_count / python_exception_count | `0` / `0` / `0` |
| script_load_status / script_load_error | `not_started` / empty |
| spawn_attach_resume_status / ui_trigger_status | `not_started` / `not_started` |
| same_process_compare_args_captured | `false` |
| diagnostic_compare_args_captured | `true` |
| compare_probe_fallback_used | `true` |
| compare_probe_fallback_is_provenance | `false` |
| candidate_generation_changed | `false` |
| beam_budget_topn_timeout_frontier_limit_expanded | `false` |
| base64_rc4_breakpoint_probe_run | `false` |
| project_progress_log_handling | `untouched` |

## Verification

| command | result |
|---|---|
| `python -m py_compile reverse_agent\olly_scripts\compare_pre_compare_handoff_target_probe.py reverse_agent\strategies\compare_aware_search.py` | passed |
| `python -m pytest -q tests\test_compare_aware_search_strategy.py -k "compare_lhs_last_writer or compare_real_lhs_last_writer or pre_compare_handoff"` | `25 passed, 164 deselected` |
| `python -m pytest -q tests\test_compare_aware_search_strategy.py` | `189 passed` |
| bounded runtime sidecar | completed with `instrumentation_incomplete`; current blocker is `timeout_before_script_lifecycle_observation` |
| `python -m reverse_agent.project_state status --state-dir project_state` | passed before report rewrite; `missing: []`; decision ready for execution |
| `python -m reverse_agent.project_state lint-decision --state-dir project_state` | passed |
| `python -m reverse_agent.project_state lint-report --state-dir project_state` | passed; `BLOCKED` / `REWORK_REQUIRED`; `decision_report_id_match=True` |
| `python -m reverse_agent.project_state lint-handoff --state-dir project_state` | passed; `REPORT_NEEDS_REVIEW`; `CONSUMED_BY_NON_SUCCESS_REPORT` |
| `python -m reverse_agent.project_state archive-round --state-dir project_state --round-id round_20260522_samplereverse_sidecar_hook_install_message_error_audit` | passed; archive generated under `project_state\rounds\round_20260522_samplereverse_sidecar_hook_install_message_error_audit` |

## Next Suggested Task

Stay on this bounded two-candidate sidecar. The next blocker is why the sidecar subprocess times out before persisting script lifecycle progress in this environment; do not move to Base64/RC4 breakpoint probing, old `sample_solver`, stale sidecar artifacts, or candidate search expansion.
