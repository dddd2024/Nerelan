```json codex_report_summary
{
  "schema_version": 1,
  "report_id": "report_20260601_post_entry_step_runtime_audit",
  "round_id": "round_20260601_post_entry_step_runtime_audit",
  "based_on_decision_id": "decision_20260601_post_entry_step_runtime_audit",
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
    "python -m pytest -q tests\\test_compare_aware_search_strategy.py -k \"post_entry_step or hook_surface_repair or branch_operand_runtime or handoff_edge_operand\"",
    "python -m pytest -q tests\\test_project_state.py -k \"post_entry_step or hook_surface_repair or branch_operand_runtime or artifact_index\"",
    "python -m reverse_agent.project_state build --reports-dir solve_reports --sample samplereverse --run-name sr_arg0_hook_readiness_ordering_20260526_r1",
    "python -m reverse_agent.project_state lint-decision --state-dir project_state",
    "python -m reverse_agent.project_state lint-report --state-dir project_state",
    "python -m reverse_agent.project_state status --state-dir project_state",
    "git diff --check"
  ],
  "generated_artifacts": [
    "solve_reports/harness_runs/sr_arg0_hook_readiness_ordering_20260526_r1/reports/tool_artifacts/samplereverse_patched/compare_handoff_post_entry_step_runtime_audit/compare_handoff_post_entry_step_runtime_audit.json"
  ],
  "next_suggested_task": "Repair bounded post-entry step instrumentation"
}
```

# Codex Execution Report

## Decision Alignment

This execution follows `project_state/decision_packet.md` for `decision_20260601_post_entry_step_runtime_audit`.

The current decision packet controlled this round. `project_state/task_packet.json` / `derived_task` were treated as state-derived guidance only.

Mainline:

```text
reverse_solving
```

Skill profiles:

```text
reverse-agent-iteration@v2
samplereverse-frontier@v2
```

`.codex-skills/registry.json` still registers only those two active skills.

## Scope

This round stayed inside bounded `compare_handoff_post_entry_step_runtime_audit`.

It preserved the fixed 3 candidates:

```text
78d540b49c59077041414141414141
5a3e7f46ddd474d041414141414141
78d540b49c59076f41414141414141
```

No candidate generation, ranking, beam, topN, budget, timeout, or frontier limit changed.

No Base64/RC4 breakpoint probe, material capture, crypto hook, old `sample_solver`, full `solve_reports/` traversal, or full `PROJECT_PROGRESS_LOG.txt` read was performed.

No `.codex-skills/`, `sample_corpus/reverse/`, `reverse_agent/harness.py`, or `reverse_agent/sample_solver.py` changes were made.

## Implementation

Added bounded sidecar:

```text
reverse_agent/olly_scripts/compare_handoff_post_entry_step_audit.py
```

Added strategy support:

```text
compare_handoff_post_entry_step_runtime_audit
```

The new strategy path prepares only the fixed candidates, calls the sidecar, and writes `compare_handoff_post_entry_step_runtime_audit.json`. The artifact schema includes `post_entry_events`, `branch_observation`, `return_target_observation`, per-candidate `post_entry_outcome`, cross-candidate `first_divergence_point`, `branch_guard_explained`, and `breakpoint_probe_allowed=false`.

## Artifact

Generated bounded artifact:

```text
compare_handoff_post_entry_step_runtime_audit.json
```

Path:

```text
solve_reports/harness_runs/sr_arg0_hook_readiness_ordering_20260526_r1/reports/tool_artifacts/samplereverse_patched/compare_handoff_post_entry_step_runtime_audit/compare_handoff_post_entry_step_runtime_audit.json
```

Result:

```text
classification=runtime_unavailable
runtime_sidecar_executed=false
candidate_count=3
breakpoint_probe_allowed=false
next_bounded_action=narrower_post_entry_breakpoint
```

The sidecar did not capture post-entry branch instruction, EFLAGS, condition, or next-EIP events in this local environment. It did not fabricate `post_entry_events`.

## Project State

`project_state` was rebuilt from `sr_arg0_hook_readiness_ordering_20260526_r1`.

Updated state now indexes:

```text
artifact_index.latest_artifacts.compare_handoff_post_entry_step_runtime_audit
artifact_index.latest_artifacts_v2.compare_handoff_post_entry_step_runtime_audit
current_state.latest_compare_handoff_post_entry_step_runtime_audit
current_state.current_bottleneck.stage=compare_handoff_post_entry_step_runtime_audit
current_state.current_bottleneck.reason=runtime_unavailable
```

Because the rebuild advanced `current_state.state_digest` from the decision's original digest, `lint-decision` correctly fails with a digest mismatch. Per the decision packet, this closeout is `PARTIAL` / `NEEDS_REVIEW`, not `SUCCESS` / `ACCEPTED`.

## Validation

- `python -m py_compile reverse_agent\strategies\compare_aware_search.py reverse_agent\project_state.py reverse_agent\olly_scripts\compare_handoff_post_entry_step_audit.py` -> passed
- `python -m pytest -q tests\test_compare_aware_search_strategy.py -k "post_entry_step or hook_surface_repair or branch_operand_runtime or handoff_edge_operand"` -> 4 passed, 203 deselected
- `python -m pytest -q tests\test_project_state.py -k "post_entry_step or hook_surface_repair or branch_operand_runtime or artifact_index"` -> 9 passed, 146 deselected
- `python -m reverse_agent.project_state build --reports-dir solve_reports --sample samplereverse --run-name sr_arg0_hook_readiness_ordering_20260526_r1` -> passed
- `python -m reverse_agent.project_state lint-decision --state-dir project_state` -> failed: expected digest mismatch after state rebuild
- `python -m reverse_agent.project_state lint-report --state-dir project_state` -> OK, warning: report_status is PARTIAL
- `python -m reverse_agent.project_state status --state-dir project_state` -> passed; current bottleneck is `compare_handoff_post_entry_step_runtime_audit/runtime_unavailable`
- `git diff --check` -> passed with line-ending warnings only

## Required Audit

1. Current mainline is `reverse_solving`.
2. `task_packet.task` / `derived_task` are derived tasks only.
3. This decision packet controlled the current round.
4. `skill_profiles` are `reverse-agent-iteration@v2` and `samplereverse-frontier@v2`.
5. `.codex-skills/registry.json` still has only those two active skills.
6. `compare_handoff_hook_surface_repair_audit` was current before execution.
7. The same 3 fixed candidates were preserved.
8. No candidate, beam, topN, budget, timeout, or frontier limit was expanded.
9. No Base64/RC4 breakpoint probe was run.
10. No material capture or crypto hook was run.
11. Full `solve_reports/` and full `PROJECT_PROGRESS_LOG.txt` were not read.
12. Forbidden files and directories were not modified.
13. `compare_handoff_post_entry_step_audit.py` was added and invoked.
14. Runtime sidecar scope was limited to control-flow surface.
15. Artifact contains `post_entry_events` for each fixed candidate, currently empty because runtime was unavailable.
16. Artifact contains `branch_observation`.
17. Artifact contains `return_target_observation`.
18. Artifact records no first divergence point because no post-entry events were captured.
19. Branch-guard gap remains unexplained due runtime unavailability.
20. `breakpoint_probe_allowed=false`.
21. Artifact index update was additive.
22. Current state updates stayed in `project_state`, not skills.
23. Negative-result constraints were not violated.
24. `lint-decision` failed because the state digest changed after the rebuild; report is PARTIAL.
25. `lint-report` passed with PARTIAL/not-archived warnings.
26. Focused pytest passed.
27. `git diff --check` passed with line-ending warnings only.
28. `pytest_result.txt` records the real command results.
29. `codex_report_summary` matches the current decision id.
30. Round archived as `round_20260601_post_entry_step_runtime_audit`.
