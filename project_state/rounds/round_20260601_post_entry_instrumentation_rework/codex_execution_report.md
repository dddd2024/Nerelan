```json codex_report_summary
{
  "schema_version": 1,
  "report_id": "report_20260601_post_entry_instrumentation_rework",
  "round_id": "round_20260601_post_entry_instrumentation_rework",
  "based_on_decision_id": "decision_20260601_post_entry_instrumentation_rework",
  "status": "PARTIAL",
  "acceptance_recommendation": "NEEDS_REVIEW",
  "files_changed": [
    "reverse_agent/olly_scripts/compare_handoff_post_entry_step_audit.py",
    "reverse_agent/strategies/compare_aware_search.py",
    "reverse_agent/project_state.py",
    "tests/test_compare_aware_search_strategy.py",
    "tests/test_project_state.py",
    "project_state/artifact_index.json",
    "project_state/current_state.json",
    "project_state/model_gate.json",
    "project_state/task_packet.json",
    "project_state/codex_execution_report.md",
    "project_state/pytest_result.txt"
  ],
  "tests_ran": [
    "python -m py_compile reverse_agent\\strategies\\compare_aware_search.py reverse_agent\\project_state.py reverse_agent\\olly_scripts\\compare_handoff_post_entry_step_audit.py",
    "python -m pytest -q tests\\test_compare_aware_search_strategy.py -k \"post_entry_step or instrumentation or hook_surface_repair\"",
    "python -m pytest -q tests\\test_project_state.py -k \"post_entry_step or instrumentation or artifact_index\"",
    "python -m reverse_agent.project_state build --reports-dir solve_reports --sample samplereverse --run-name sr_arg0_hook_readiness_ordering_20260526_r1",
    "python -m reverse_agent.project_state lint-decision --state-dir project_state",
    "python -m reverse_agent.project_state lint-report --state-dir project_state",
    "python -m reverse_agent.project_state status --state-dir project_state",
    "git diff --check"
  ],
  "generated_artifacts": [
    "solve_reports/harness_runs/sr_arg0_hook_readiness_ordering_20260526_r1/reports/tool_artifacts/samplereverse_patched/compare_handoff_post_entry_step_runtime_audit/compare_handoff_post_entry_step_runtime_audit.json"
  ],
  "next_suggested_task": "Implement a narrower post-entry breakpoint path or wire a real single-step backend"
}
```

# Codex Execution Report

## Decision Alignment

This execution follows `project_state/decision_packet.md` for `decision_20260601_post_entry_instrumentation_rework`.

`project_state/task_packet.json` / `derived_task` were treated as state-derived guidance only. Mainline is `reverse_solving`; skill profiles remain `reverse-agent-iteration@v2` and `samplereverse-frontier@v2`; `.codex-skills/registry.json` still registers only those two active skills.

## Scope

This round stayed inside bounded `compare_handoff_post_entry_step_runtime_audit` instrumentation repair.

The fixed candidates stayed unchanged:

```text
78d540b49c59077041414141414141
5a3e7f46ddd474d041414141414141
78d540b49c59076f41414141414141
```

No candidate generation, ranking, beam, topN, budget, timeout, or frontier limit changed. No Base64/RC4 breakpoint probe, material capture, crypto hook, old `sample_solver`, full `solve_reports/` traversal, or full `PROJECT_PROGRESS_LOG.txt` read was performed. No `.codex-skills/`, `sample_corpus/reverse/`, `reverse_agent/harness.py`, or `reverse_agent/sample_solver.py` changes were made.

## Implementation

`compare_handoff_post_entry_step_audit.py` now emits structured diagnostics for environment, breakpoint installation, single-step availability, and artifact parsing.

`CompareAwareSearchStrategy` now preserves the exact 3-candidate set and aggregates per-candidate diagnostics into a specific post-entry classification instead of collapsing all non-executed cases to `runtime_unavailable`.

`project_state.py` now carries the additive diagnostic summaries into `current_state.latest_compare_handoff_post_entry_step_runtime_audit` and maps the new post-entry blocker classes back to the same bounded repair task.

## Artifact

Generated bounded artifact:

```text
solve_reports/harness_runs/sr_arg0_hook_readiness_ordering_20260526_r1/reports/tool_artifacts/samplereverse_patched/compare_handoff_post_entry_step_runtime_audit/compare_handoff_post_entry_step_runtime_audit.json
```

Result:

```text
classification=step_api_unavailable
runtime_sidecar_executed=false
candidate_count=3
debugger_backend=frida
backend_import_ok=true
target_executable_exists=true
breakpoint_probe_allowed=false
material_capture_allowed=false
crypto_hook_allowed=false
next_bounded_action=narrower_post_entry_breakpoint
```

The direct cause is no local Olly/Frida single-step implementation wired for this sidecar. The artifact does not fabricate `post_entry_events`, branch EFLAGS, conditions, or next-EIP.

## Project State

`project_state` was rebuilt from `sr_arg0_hook_readiness_ordering_20260526_r1`.

Updated state indexes:

```text
artifact_index.latest_artifacts.compare_handoff_post_entry_step_runtime_audit
artifact_index.latest_artifacts_v2.compare_handoff_post_entry_step_runtime_audit
current_state.latest_compare_handoff_post_entry_step_runtime_audit
current_state.current_bottleneck.stage=compare_handoff_post_entry_step_runtime_audit
current_state.current_bottleneck.reason=step_api_unavailable
```

Because the rebuild advanced `current_state.state_digest` beyond the decision's original digest, `lint-decision` correctly fails with a digest mismatch. Per the decision packet, this closeout is `PARTIAL` / `NEEDS_REVIEW`, not `SUCCESS` / `ACCEPTED`.

## Validation

- `python -m py_compile reverse_agent\strategies\compare_aware_search.py reverse_agent\project_state.py reverse_agent\olly_scripts\compare_handoff_post_entry_step_audit.py` -> passed
- `python -m pytest -q tests\test_compare_aware_search_strategy.py -k "post_entry_step or instrumentation or hook_surface_repair"` -> 6 passed, 201 deselected
- `python -m pytest -q tests\test_project_state.py -k "post_entry_step or instrumentation or artifact_index"` -> 7 passed, 148 deselected
- `python -m reverse_agent.project_state build --reports-dir solve_reports --sample samplereverse --run-name sr_arg0_hook_readiness_ordering_20260526_r1` -> passed
- `python -m reverse_agent.project_state lint-decision --state-dir project_state` -> failed as expected: decision digest mismatch after state rebuild
- `python -m reverse_agent.project_state lint-report --state-dir project_state` -> OK, warning: report_status is PARTIAL
- `python -m reverse_agent.project_state status --state-dir project_state` -> passed; current bottleneck is `compare_handoff_post_entry_step_runtime_audit/step_api_unavailable`
- `git diff --check` -> passed with line-ending warnings only

## Required Audit

1. Current mainline is `reverse_solving`.
2. `task_packet.task` / `derived_task` are derived tasks only.
3. `project_state/decision_packet.md` controlled this round.
4. Skill profiles are `reverse-agent-iteration@v2` and `samplereverse-frontier@v2`.
5. `.codex-skills/registry.json` still has only those two active skills.
6. `compare_handoff_post_entry_step_runtime_audit` freshness is current after rebuild.
7. The same 3 fixed candidates were preserved.
8. No candidate, beam, topN, budget, timeout, or frontier limit was expanded.
9. No Base64/RC4 breakpoint probe was run.
10. No material capture or crypto hook was run.
11. Full `solve_reports/` and full `PROJECT_PROGRESS_LOG.txt` were not read.
12. Forbidden files and directories were not modified.
13. `runtime_sidecar_executed=false` is now explained as `step_api_unavailable`.
14. The artifact distinguishes backend, target launch, breakpoint installation, step API, and artifact parse diagnostics.
15. `0x2338` and `0x1b50` are recorded as the bounded breakpoint surfaces; install was not attempted because no step backend is wired.
16. Runtime capture remained limited to control-flow surface.
17. Runtime unavailable is no longer repeated without diagnostics.
18. Artifact contains `environment_diagnostics`.
19. Artifact contains `breakpoint_installation_diagnostics`.
20. Artifact contains `sidecar_invocation` evidence via candidate logs and per-candidate diagnostics.
21. `breakpoint_probe_allowed=false`.
22. Artifact index update was additive.
23. Current state updates stayed in `project_state`, not skills.
24. Negative-result constraints were not violated.
25. `lint-decision` failed only because the state digest changed after rebuild; report is PARTIAL.
26. `lint-report` passed with the expected PARTIAL warning.
27. Focused pytest passed.
28. `git diff --check` passed with line-ending warnings only.
29. `pytest_result.txt` records the real command results.
30. `codex_report_summary` matches `decision_20260601_post_entry_instrumentation_rework`.
31. Round archived as `round_20260601_post_entry_instrumentation_rework`.
