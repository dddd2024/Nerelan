```json codex_report_summary
{
  "schema_version": 1,
  "report_id": "report_20260531_fix_material_hook_utf16_kind_protocol",
  "round_id": "round_20260528_fix_material_hook_utf16_kind_protocol",
  "based_on_decision_id": "decision_20260528_fix_material_hook_utf16_kind_protocol",
  "status": "SUCCESS",
  "acceptance_recommendation": "ACCEPTED",
  "files_changed": [
    "reverse_agent/strategies/compare_aware_search.py",
    "tests/test_compare_aware_search_strategy.py",
    "project_state/codex_execution_report.md",
    "project_state/pytest_result.txt"
  ],
  "tests_ran": [
    "python -m py_compile reverse_agent/strategies/compare_aware_search.py reverse_agent/olly_scripts/base64_rc4_breakpoint_probe.py",
    "python -m pytest -q tests/test_compare_aware_search_strategy.py -k \"material_hook or base64_rc4 or breakpoint or utf16\"",
    "python -m pytest -q tests/test_project_state.py -k \"material_hook or report or lint\"",
    "python -m reverse_agent.project_state lint-decision --state-dir project_state",
    "python -m reverse_agent.project_state lint-report --state-dir project_state",
    "git diff --check"
  ],
  "generated_artifacts": [
    "project_state/codex_execution_report.md",
    "project_state/pytest_result.txt"
  ]
}
```

# CODEX_EXECUTION_REPORT

## 2026-05-31 UTF-16 Material Hook Protocol Fix

Result: `SUCCESS` / `ACCEPTED`.

This round executed `decision_20260528_fix_material_hook_utf16_kind_protocol`.
It was a narrow protocol repair only: no reverse runtime probe, no real
samplereverse harness rerun, no Base64/RC4 breakpoint probe, and no candidate,
beam, topN, budget, timeout, frontier, or search expansion.

## Audit Answers

1. Before this fix, `_breakpoint_static_points_from_material_hook_runtime_validation_payload()` copied the validated semantic material kind into downstream static point `kind`, so `utf16le_payload` could be passed as a probe protocol kind.
2. `reverse_agent/olly_scripts/base64_rc4_breakpoint_probe.py` still only infers `hook_results["utf16le_payload"]` when a hook event has `point_kind == "utf16le"`.
3. After this fix, ACCEPT material-hook validation static points keep their semantic grouping as `utf16le_payload`, but the downstream point field is `kind="utf16le"`.
4. The upstream semantic identity is preserved as `material_kind="utf16le_payload"` and `semantic_kind="utf16le_payload"`.
5. `BLOCKED`, `REJECTED`, and `breakpoint_probe_allowed=false` payloads still do not produce Base64/RC4 static points.
6. The fix did not run Base64/RC4 probing, runtime probing, stale artifact promotion, or any search expansion.
7. Negative-results constraints were respected: no old `sample_solver`, no full `solve_reports` commit/read, no Base64/RC4 breakpoint probe, and no candidate/frontier/budget expansion.

## Code Changes

- Updated material-hook semantic normalization in `reverse_agent/strategies/compare_aware_search.py` so material hook records can derive semantics from `material_kind`, `semantic_kind`, or `kind`.
- Updated material-hook ACCEPT static point conversion so `utf16le_payload` is preserved semantically while the downstream probe protocol receives `kind="utf16le"`.
- Added focused tests covering the UTF-16 material kind mapping, downstream hook-result normalization, and blocked-path gating.

## Verification

```text
python -m py_compile reverse_agent/strategies/compare_aware_search.py reverse_agent/olly_scripts/base64_rc4_breakpoint_probe.py
passed

python -m pytest -q tests/test_compare_aware_search_strategy.py -k "material_hook or base64_rc4 or breakpoint or utf16"
passed: 20 passed, 179 deselected

python -m pytest -q tests/test_project_state.py -k "material_hook or report or lint"
passed: 72 passed, 77 deselected

python -m reverse_agent.project_state lint-decision --state-dir project_state
passed

python -m reverse_agent.project_state lint-report --state-dir project_state
passed

git diff --check
passed
```

## Next Bottleneck

This round only fixes the ACCEPT handoff protocol bug. The active sample-state
bottleneck remains the previously recorded runtime path issue:

```text
decrypt_handler_entered_but_candidate_path_exits_before_handoff
```

The next reverse-solving decision should continue from that blocker only after
this protocol repair is accepted, still without widening candidate search by
default.
