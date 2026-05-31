```json codex_report_summary
{
  "schema_version": 1,
  "report_id": "report_20260531_resume_samplereverse_handoff_exit_diagnosis",
  "round_id": "round_20260531_resume_samplereverse_handoff_exit_diagnosis",
  "based_on_decision_id": "decision_20260531_resume_samplereverse_handoff_exit_diagnosis",
  "status": "SUCCESS",
  "acceptance_recommendation": "ACCEPTED",
  "files_changed": [
    "project_state/samplereverse_handoff_exit_diagnosis.md (added)",
    "project_state/codex_execution_report.md (updated)",
    "project_state/pytest_result.txt (updated)"
  ],
  "tests_ran": [
    "python -m reverse_agent.project_state lint-decision --state-dir project_state",
    "python -m reverse_agent.project_state lint-report --state-dir project_state",
    "git diff --check"
  ],
  "generated_artifacts": [
    "project_state/samplereverse_handoff_exit_diagnosis.md"
  ]
}
```

# Codex Execution Report

## Decision Alignment

This execution follows `project_state/decision_packet.md` for `decision_20260531_resume_samplereverse_handoff_exit_diagnosis`.

The round is a bounded no-runtime diagnosis for the samplereverse reverse-solving mainline. It did not continue the corpus/static-audit branch, did not modify solver code, and did not run a new runtime probe.

## Evidence Used

Current artifacts read:

- `solve_reports/harness_runs/sr_arg0_hook_readiness_ordering_20260526_r1/run_manifest.json`
- `solve_reports/harness_runs/sr_arg0_hook_readiness_ordering_20260526_r1/summary.json`
- `solve_reports/harness_runs/sr_arg0_hook_readiness_ordering_20260526_r1/reports/tool_artifacts/samplereverse_patched/compare_hook_path_reachability_audit/compare_hook_path_reachability_audit.json`
- `solve_reports/harness_runs/sr_arg0_hook_readiness_ordering_20260526_r1/reports/tool_artifacts/samplereverse_patched/compare_real_lhs_provenance_audit/compare_real_lhs_provenance_audit.json`

No full `solve_reports/` scan was performed. Stale and missing artifacts were not used as current evidence.

## Required Audit Checklist

| # | Requirement | Status | Evidence |
|---:|---|---|---|
| 1 | mainline switched back to `reverse_solving` | PASS | decision meta |
| 2 | `task_packet.task` is derived, not current authority | PASS | decision controls current round |
| 3 | `decision_packet.md` controls this round | PASS | active decision packet present |
| 4 | skill profiles match expected profiles | PASS | `reverse-agent-iteration@v2`, `samplereverse-frontier@v2` |
| 5 | `compare_hook_path_reachability_audit` is current | PASS | artifact_index freshness current |
| 6 | `compare_real_lhs_provenance_audit` is current | PASS | artifact_index freshness current |
| 7 | `run_manifest` and `summary` are current | PASS | artifact_index freshness current |
| 8 | stale/missing artifacts not used as current evidence | PASS | freshness table in diagnosis |
| 9 | hook path audit conclusion recorded | PASS | `decrypt_handler_entered_but_candidate_path_exits_before_handoff` |
| 10 | real-LHS provenance conclusion recorded | PASS | `instrumentation_incomplete`; fallback not provenance |
| 11 | handoff-exit minimum explanation recorded | PASS | candidate-dependent exit or exception before compare |
| 12 | next bounded runtime probe design feasibility answered | PASS | targeted handoff/exception classifier recommended |
| 13 | project_state rebuild requirement answered | PASS | not required while current artifacts are readable |
| 14 | no sample.exe executed | PASS | no runtime command run |
| 15 | no runtime probe executed | PASS | no probe command run |
| 16 | no Base64/RC4 breakpoint probe executed | PASS | no breakpoint probe run |
| 17 | full `solve_reports/` not read | PASS | bounded files only |
| 18 | full `PROJECT_PROGRESS_LOG.txt` not read | PASS | not used in this execution |
| 19 | `.codex-skills/` not modified | PASS | no changes |
| 20 | `sample_corpus/reverse/` not modified | PASS | no changes |
| 21 | old `sample_solver` / search expansion not used | PASS | no solver/search commands run |
| 22 | negative_results failed directions not repeated | PASS | no blocked direction rerun |

## Diagnosis Summary

The selected/current run is `sr_arg0_hook_readiness_ordering_20260526_r1`.

The current `compare_hook_path_reachability_audit` shows all 3 fixed candidates are runtime-backed and hit `predecessor_handoff_call=1`, `handoff_helper_entry=1`, and `process_exception=1`, but actual compare observation remains zero. Its classification is `decrypt_handler_entered_but_candidate_path_exits_before_handoff`.

The current `compare_real_lhs_provenance_audit` remains `instrumentation_incomplete`. Its compare-probe fallback captured compare args, but `compare_probe_fallback_is_provenance=false`, so the fallback is not a provenance source and the old `[ebp-0x1170]` slot must not be reused as real LHS evidence.

The minimum explanation is candidate-dependent exit or exception before the handoff/compare connection. Branch guard and wrong hook site remain secondary hypotheses because current branch-outcome and exception-unwind artifacts are missing.

## Next Recommendation

The next executable decision should be a bounded runtime probe that keeps the same 3 fixed candidates and classifies control-flow outcome between predecessor handoff, helper entry, process exception, and the first possible compare successor. It should not expand search, rerun Base64/RC4 breakpoint probing, or revive old `sample_solver` paths.

## Test Results

Required checks were run:

- `python -m reverse_agent.project_state lint-decision --state-dir project_state` -> PASSED
- `python -m reverse_agent.project_state lint-report --state-dir project_state` -> PASSED
- `git diff --check` -> PASSED

No pytest was required because this round changed only documentation/project_state diagnosis files and no code.
