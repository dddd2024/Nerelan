```json codex_report_summary
{
  "schema_version": 1,
  "report_id": "report_20260601_handoff_edge_operand_provenance_audit",
  "round_id": "round_20260601_handoff_edge_operand_provenance_audit",
  "based_on_decision_id": "decision_20260601_handoff_edge_operand_provenance_audit",
  "status": "PARTIAL",
  "acceptance_recommendation": "NEEDS_REVIEW",
  "files_changed": [
    "reverse_agent/strategies/compare_aware_search.py",
    "reverse_agent/project_state.py",
    "tests/test_compare_aware_search_strategy.py",
    "tests/test_project_state.py",
    "project_state/decision_packet.md",
    "project_state/artifact_index.json",
    "project_state/current_state.json",
    "project_state/model_gate.json",
    "project_state/task_packet.json",
    "project_state/codex_execution_report.md",
    "project_state/pytest_result.txt",
    "project_state/rounds/round_20260601_handoff_edge_operand_provenance_audit"
  ],
  "tests_ran": [
    "python -m py_compile reverse_agent\\strategies\\compare_aware_search.py reverse_agent\\project_state.py",
    "python -m pytest -q tests\\test_compare_aware_search_strategy.py -k \"handoff_edge_operand or handoff_path_divergence or handoff_exit_classifier\"",
    "python -m pytest -q tests\\test_project_state.py -k \"handoff_edge_operand or handoff_path_divergence or handoff_exit_classifier\"",
    "python -m reverse_agent.project_state build --reports-dir solve_reports --sample samplereverse --run-name sr_arg0_hook_readiness_ordering_20260526_r1",
    "python -m reverse_agent.project_state lint-decision --state-dir project_state",
    "python -m reverse_agent.project_state lint-report --state-dir project_state",
    "python -m reverse_agent.project_state status --state-dir project_state",
    "git diff --check",
    "python -m reverse_agent.project_state archive-round --state-dir project_state --round-id round_20260601_handoff_edge_operand_provenance_audit",
    "python -m reverse_agent.project_state status --state-dir project_state",
    "python -m reverse_agent.project_state lint-report --state-dir project_state"
  ],
  "generated_artifacts": [
    "solve_reports\\harness_runs\\sr_arg0_hook_readiness_ordering_20260526_r1\\reports\\tool_artifacts\\samplereverse_patched\\compare_handoff_edge_operand_provenance_audit\\compare_handoff_edge_operand_provenance_audit.json",
    "project_state\\rounds\\round_20260601_handoff_edge_operand_provenance_audit"
  ],
  "next_suggested_task": "Trace bounded branch operand runtime sidecar or instruction boundary"
}
```

# Codex Execution Report

## Decision Alignment

This execution follows `project_state/decision_packet.md` for `decision_20260601_handoff_edge_operand_provenance_audit`.

The active `task_packet.task` / `derived_task` is state-derived guidance. The current decision packet controls this round.

Skill profiles:

```text
reverse-agent-iteration@v2
samplereverse-frontier@v2
```

Mainline:

```text
reverse_solving
```

This round did not seek the final flag. It generated a bounded offline projection from the current handoff path divergence artifact.

## Implementation Summary

- Added `compare_handoff_edge_operand_provenance_audit` as a new artifact kind with file name `compare_handoff_edge_operand_provenance_audit.json`.
- Added an offline projection builder/runner that consumes the current `compare_handoff_path_divergence_audit` payload and writes the edge/operand provenance artifact without executing the sample or any runtime sidecar.
- Added `project_state` indexing and current-state summary projection for the new artifact.
- Added strategy and project_state regression tests for the new projection and state indexing.
- Rebuilt project_state for `sr_arg0_hook_readiness_ordering_20260526_r1`; current bottleneck now points at `compare_handoff_edge_operand_provenance_audit`.

## Generated Artifact

```text
solve_reports\harness_runs\sr_arg0_hook_readiness_ordering_20260526_r1\reports\tool_artifacts\samplereverse_patched\compare_handoff_edge_operand_provenance_audit\compare_handoff_edge_operand_provenance_audit.json
```

Artifact index entry:

| Field | Value |
|---|---|
| freshness | current |
| kind | compare_handoff_edge_operand_provenance_audit |
| modified_at | 2026-06-01T04:36:16Z |
| sha256 | 6e5408b45f49e0013b5edd6008cac2bca22fee6876c27bcd2eb78172edb4c167 |
| size_bytes | 7800 |
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
common_prefix_events=predecessor_handoff_call -> handoff_helper_entry
first_divergence_after=handoff_helper_entry
return_context_candidate_dependent=true
return_context_values=0xc5052f, 0x2ae052f, 0xfff4052f
exception_edge_shared_for_subset=true
exception_edge_candidate_dependent_memory=true
branch_guard_candidate_count=1
exception_candidate_count=2
root_cause_classification=candidate_dependent_handoff_exit_edge_unresolved
schema_gap_fields=branch_operand_summary
next_bounded_action=bounded_branch_operand_runtime_sidecar_or_instruction_boundary_audit
```

Per-candidate result:

| Candidate | Prior role | Exception edge | Branch operand | Classification |
|---|---|---|---|---|
| `78d540b49c59077041414141414141` | exception_path | `0xf41913` / `0x5305154b`, previous `handoff_helper_entry` | not observed before exception | exception_edge_after_handoff |
| `5a3e7f46ddd474d041414141414141` | exception_path | `0xf41913` / `0x820004`, previous `handoff_helper_entry` | not observed before exception | exception_edge_after_handoff |
| `78d540b49c59076f41414141414141` | branch_guard_or_silent_non_reaching_path | not observed | schema_gap: no branch operand or flags in prior artifact | branch_guard_silent_after_handoff |

The result is `PARTIAL` because the offline projection preserved the required exception and return-context evidence, but the branch/silent candidate still lacks a captured branch operand or flags. The bounded next step is a branch-operand runtime sidecar or instruction-boundary audit, not search expansion.

## Scope Audit

| Requirement | Status | Evidence |
|---|---|---|
| Current mainline is `reverse_solving` | PASS | active decision packet |
| `task_packet.task` is derived guidance | PASS | active decision packet controls this round |
| Skill profiles preserved | PASS | `reverse-agent-iteration@v2`, `samplereverse-frontier@v2` |
| Same 3 fixed candidates | PASS | artifact `fixed_candidates` and `candidate_count=3` |
| No candidate/beam/topN/budget/timeout/frontier expansion | PASS | offline projection only |
| No Base64/RC4 breakpoint probe | PASS | no probe command run; artifact blocks it |
| No material capture or crypto hook | PASS | no material hook/runtime command run |
| No old `sample_solver` | PASS | not used |
| Did not read full `solve_reports/` | PASS | only indexed artifact paths were used |
| Did not read full `PROJECT_PROGRESS_LOG.txt` | PASS | not used |
| `.codex-skills/` unchanged | PASS | not modified |
| `sample_corpus/reverse/` unchanged | PASS | not modified |
| Did not treat stale/missing artifact as current | PASS | source divergence artifact freshness was current |
| New artifact contains per-candidate handoff edge summary | PASS | `candidates[*]` |
| New artifact preserves exception address/memory/previous_event | PASS | `exception_edge_summary` |
| New artifact preserves branch/silent explanation | PASS | `branch_operand_summary.classification=schema_gap` |
| New artifact gives cross-candidate root cause | PASS | `cross_candidate.root_cause_classification` |
| Negative results not repeated | PASS | no blocked direction was executed |

## Verification

- `python -m py_compile reverse_agent\strategies\compare_aware_search.py reverse_agent\project_state.py` -> PASSED
- `python -m pytest -q tests\test_compare_aware_search_strategy.py -k "handoff_edge_operand or handoff_path_divergence or handoff_exit_classifier"` -> PASSED, 5 passed / 199 deselected
- `python -m pytest -q tests\test_project_state.py -k "handoff_edge_operand or handoff_path_divergence or handoff_exit_classifier"` -> PASSED, 3 passed / 149 deselected
- `python -m reverse_agent.project_state build --reports-dir solve_reports --sample samplereverse --run-name sr_arg0_hook_readiness_ordering_20260526_r1` -> PASSED
- `python -m reverse_agent.project_state lint-decision --state-dir project_state` -> PASSED
- `python -m reverse_agent.project_state lint-report --state-dir project_state` -> PASSED with expected warnings: `report_status is PARTIAL`, `report round not archived yet`
- `python -m reverse_agent.project_state status --state-dir project_state` -> PASSED
- `git diff --check` -> PASSED
- `python -m reverse_agent.project_state archive-round --state-dir project_state --round-id round_20260601_handoff_edge_operand_provenance_audit` -> pending after report update
