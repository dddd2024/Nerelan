```json codex_report_summary
{
  "schema_version": 1,
  "report_id": "report_20260601_branch_operand_runtime_sidecar_audit",
  "round_id": "round_20260601_branch_operand_runtime_sidecar_audit",
  "based_on_decision_id": "decision_20260601_branch_operand_runtime_sidecar_audit",
  "status": "PARTIAL",
  "acceptance_recommendation": "NEEDS_REVIEW",
  "files_changed": [
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
    "python -m py_compile reverse_agent\\strategies\\compare_aware_search.py reverse_agent\\project_state.py",
    "python -m pytest -q tests\\test_compare_aware_search_strategy.py -k \"branch_operand_runtime or handoff_edge_operand or handoff_path_divergence or handoff_exit_classifier\"",
    "python -m pytest -q tests\\test_project_state.py -k \"branch_operand_runtime or handoff_edge_operand or handoff_path_divergence or handoff_exit_classifier\"",
    "python -m reverse_agent.project_state build --reports-dir solve_reports --sample samplereverse --run-name sr_arg0_hook_readiness_ordering_20260526_r1",
    "python -m reverse_agent.project_state status --state-dir project_state",
    "python -m reverse_agent.project_state lint-decision --state-dir project_state",
    "python -m reverse_agent.project_state lint-report --state-dir project_state",
    "git diff --check"
  ],
  "generated_artifacts": [
    "solve_reports\\harness_runs\\sr_arg0_hook_readiness_ordering_20260526_r1\\reports\\tool_artifacts\\samplereverse_patched\\compare_handoff_branch_operand_runtime_audit\\compare_handoff_branch_operand_runtime_audit.json"
  ],
  "next_suggested_task": "Repair bounded handoff branch hook surface"
}
```

# Codex Execution Report

## Decision Alignment

This execution follows `project_state/decision_packet.md` for `decision_20260601_branch_operand_runtime_sidecar_audit`.

The active `task_packet.task` / `derived_task` was state-derived guidance. The current decision packet controlled this round.

Skill profiles:

```text
reverse-agent-iteration@v2
samplereverse-frontier@v2
```

Mainline:

```text
reverse_solving
```

This round did not seek the final flag, did not add candidates, and did not expand beam, topN, budget, timeout, or frontier limits.

## Implementation Summary

- Added `compare_handoff_branch_operand_runtime_audit` as a new artifact kind with file name `compare_handoff_branch_operand_runtime_audit.json`.
- Added a bounded offline instruction-boundary projection that consumes the current `compare_handoff_edge_operand_provenance_audit` payload and emits per-candidate entry context, branch operand evidence, exception evidence, post-entry outcome, and return-target trust.
- Added project_state indexing and current-state summary projection for the new artifact.
- Added focused strategy and project_state regression tests.
- Rebuilt project_state for `sr_arg0_hook_readiness_ordering_20260526_r1`; current bottleneck now points at `compare_handoff_branch_operand_runtime_audit`.

## Generated Artifact

```text
solve_reports\harness_runs\sr_arg0_hook_readiness_ordering_20260526_r1\reports\tool_artifacts\samplereverse_patched\compare_handoff_branch_operand_runtime_audit\compare_handoff_branch_operand_runtime_audit.json
```

Artifact index entry:

| Field | Value |
|---|---|
| freshness | current |
| kind | compare_handoff_branch_operand_runtime_audit |
| modified_at | 2026-06-01T05:32:40Z |
| sha256 | 22d2e3dabea0b53d60d5a77e71391c3eae5152ddf1fe564ed80ada4ae443b654 |
| size_bytes | 6329 |
| source_run | sr_arg0_hook_readiness_ordering_20260526_r1 |

## Audit Result

Fixed candidates were unchanged:

```text
78d540b49c59077041414141414141
5a3e7f46ddd474d041414141414141
78d540b49c59076f41414141414141
```

Cross-candidate result:

```text
root_cause_classification=instruction_boundary_gap
branch_guard_explained=false
return_context_candidate_dependent=true
return_context_values=0xc5052f, 0x2ae052f, 0xfff4052f
return_target_trust=suspicious
exception_edge_shared_for_subset=true
exception_edge_candidate_dependent_memory=true
branch_operand_gap_count=1
exception_candidate_count=2
next_bounded_action=hook_surface_repair
```

Per-candidate result:

| Candidate | Prior role | Exception evidence | Branch evidence | Post-entry outcome |
|---|---|---|---|---|
| `78d540b49c59077041414141414141` | exception_edge_after_handoff | observed at `0x1913`, memory `0x5305154b` | not_observed | exception_edge |
| `5a3e7f46ddd474d041414141414141` | exception_edge_after_handoff | observed at `0x1913`, memory `0x820004` | not_observed | exception_edge |
| `78d540b49c59076f41414141414141` | branch_guard_silent_after_handoff | not_observed | instruction_boundary_gap | instruction_boundary_gap |

The branch_guard candidate still has no captured branch instruction, flags, condition outcome, operand source, or next basic block. The bounded instruction-boundary audit therefore stops at `instruction_boundary_gap` instead of widening runtime budget or adding unrelated probes.

## Scope Audit

- `.codex-skills/registry.json` was not modified.
- Fixed 3 candidates were preserved.
- No candidate/frontier/beam/topN/budget/timeout expansion was performed.
- No Base64/RC4 breakpoint probe was run.
- No material capture, crypto hook, or Base64/RC4 hook was run.
- The old `sample_solver` path was not used.
- Full `solve_reports/` and full `PROJECT_PROGRESS_LOG.txt` were not read.
- `.codex-skills/`, `sample_corpus/reverse/`, `reverse_agent/harness.py`, and `reverse_agent/sample_solver.py` were not modified.
- The current source artifact `compare_handoff_edge_operand_provenance_audit` was consumed from current project_state refs.

## Validation

- `python -m py_compile reverse_agent\strategies\compare_aware_search.py reverse_agent\project_state.py` -> PASSED
- `python -m pytest -q tests\test_compare_aware_search_strategy.py -k "branch_operand_runtime or handoff_edge_operand or handoff_path_divergence or handoff_exit_classifier"` -> PASSED, 6 passed / 199 deselected
- `python -m pytest -q tests\test_project_state.py -k "branch_operand_runtime or handoff_edge_operand or handoff_path_divergence or handoff_exit_classifier"` -> PASSED, 4 passed / 149 deselected
- `python -m reverse_agent.project_state build --reports-dir solve_reports --sample samplereverse --run-name sr_arg0_hook_readiness_ordering_20260526_r1` -> PASSED
- `python -m reverse_agent.project_state status --state-dir project_state` -> PASSED; current bottleneck is `compare_handoff_branch_operand_runtime_audit / instruction_boundary_gap`
- `python -m reverse_agent.project_state lint-decision --state-dir project_state` -> FAILED after rebuild because the new artifact intentionally changed `current_state.state_digest`
- `python -m reverse_agent.project_state lint-report --state-dir project_state` -> initial pre-refresh report FAILED because it still referenced the previous decision
- `git diff --check` -> PASSED with line-ending warnings only

## Stop Condition

Status is `PARTIAL / NEEDS_REVIEW` because the requested branch operand / flags / next-block evidence was not available from the bounded source artifact. The round produced the required explicit gap classification and stopped without scope expansion.
