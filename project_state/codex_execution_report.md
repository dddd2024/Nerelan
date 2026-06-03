```json codex_report_summary
{
  "schema_version": 1,
  "report_id": "report_20260603_local_reverse_semantic_rule_extraction_v1",
  "round_id": "round_20260603_local_reverse_semantic_rule_extraction_v1",
  "based_on_decision_id": "decision_20260603_local_reverse_semantic_rule_extraction_v1",
  "status": "PARTIAL",
  "acceptance_recommendation": "NEEDS_REVIEW",
  "files_changed": [
    "reverse_agent/local_reverse_semantic_rules.py",
    "tests/test_local_reverse_semantic_rules.py",
    "project_state/local_reverse_semantic_rule_result.json",
    "project_state/codex_execution_report.md",
    "project_state/pytest_result.txt"
  ],
  "tests_ran": [
    "python -m reverse_agent.project_state lint-decision --state-dir project_state",
    "python -m py_compile reverse_agent\\local_reverse_semantic_rules.py",
    "python -m pytest -q tests\\test_local_reverse_semantic_rules.py",
    "python -m pytest -q tests\\test_local_reverse_runtime.py tests\\test_local_reverse_compare_site.py tests\\test_local_reverse_xref_disassembly.py tests\\test_local_reverse_semantic_rules.py",
    "python -m reverse_agent.local_reverse_semantic_rules --corpus-index project_state\\local_reverse_corpus_index.json --xref-result project_state\\local_reverse_xref_disassembly_result.json --policy project_state\\local_reverse_runtime_policy.json --out project_state\\local_reverse_semantic_rule_result.json",
    "python -m reverse_agent.project_state lint-report --state-dir project_state",
    "python -m reverse_agent.project_state status --state-dir project_state",
    "git diff --check"
  ],
  "generated_artifacts": [
    "project_state/local_reverse_semantic_rule_result.json"
  ],
  "next_suggested_task": "Use bounded symbolic execution or IDA decompiler summaries over the extracted semantic windows"
}
```

# Codex Execution Report

## Decision Alignment

This execution follows `project_state/decision_packet.md` for `decision_20260603_local_reverse_semantic_rule_extraction_v1`.

The stale `samplereverse` fields in `project_state/task_packet.json` and `project_state/current_state.json` were treated as background only. The active decision packet controls this round.

## Scope

This round only processed the three unsolved local reverse targets from `project_state/local_reverse_xref_disassembly_result.json` whose previous blocker was `new_xref_candidates_failed_runtime_validation`:

```text
4c69f173f2bd0211
bcbd9979db015bfd
18019fca52b389fe
```

No other challenge binary entered semantic extraction or runtime validation. No previous 90 compare-site candidates were re-run. No previous xref-derived candidates were re-run except when a candidate was explicitly regenerated from a semantic rule with `revalidated_reason=semantic_rule_derived`.

No `samplereverse` window discovery, compare handoff, Base64/RC4 probe, old `sample_solver`, GUI integration, full `solve_reports/` traversal, or full `PROJECT_PROGRESS_LOG.txt` read was performed.

No binary sample was copied into the repository, uploaded, committed, relocated, or encoded as hex/base64. `.codex-skills/` was not modified.

## Implementation

Added `reverse_agent/local_reverse_semantic_rules.py`, a bounded CLI and library module:

```text
python -m reverse_agent.local_reverse_semantic_rules --corpus-index project_state\local_reverse_corpus_index.json --xref-result project_state\local_reverse_xref_disassembly_result.json --policy project_state\local_reverse_runtime_policy.json --out project_state\local_reverse_semantic_rule_result.json
```

The module:

- Selects only the three in-scope unsolved xref targets with `missing_evidence=new_xref_candidates_failed_runtime_validation`.
- Extracts conservative semantic rules from existing `disassembly_windows`; it does not expand xrefs or disassembly windows.
- Recognizes bounded first-pass rule types: `length_check`, `loop_bound`, `stack_buffer`, `byte_load`, `byte_store`, `byte_add_const`, `byte_sub_const`, `byte_xor_const`, `byte_cmp_const`, and `replacement_rule`.
- Emits each rule with `rule_type`, `confidence`, `source_window`, `source_instructions`, `inferred_constraint`, and `candidate_generation_enabled`.
- Generates candidates only from semantic rules, with `max_rules_per_sample=20`, `max_candidates_per_sample=20`, and `max_runtime_validations_per_sample=20`.
- Uses the existing `run_probe` runtime path and `validation_succeeded` success/failure semantics.

Added `tests/test_local_reverse_semantic_rules.py` to cover target selection, synthetic rule extraction, bounds, semantic revalidation reasons, blocked runtime/path/hash preconditions, and success/failure marker conflict handling.

## Result

Generated:

```text
project_state/local_reverse_semantic_rule_result.json
```

Summary:

```text
status=PARTIAL
target_count=3
solved_count=0
blocked_reasons=[]
max_rules_per_sample=20
max_candidates_per_sample=20
max_runtime_validations_per_sample=20
```

Per-target result:

```text
18019fca52b389fe -> semantic_rule_count=20, generated_candidate_count=20, validated_candidate_count=20, solved=false, missing_evidence=needs_symbolic_execution
4c69f173f2bd0211 -> semantic_rule_count=20, generated_candidate_count=13, validated_candidate_count=13, solved=false, missing_evidence=needs_symbolic_execution
bcbd9979db015bfd -> semantic_rule_count=20, generated_candidate_count=12, validated_candidate_count=12, solved=false, missing_evidence=needs_symbolic_execution
```

No `solved=true` result was emitted because no semantic-rule candidate produced runtime success output without failure semantics.

## Required Audit

- Current `decision_packet.md` was the execution authority.
- Previous xref/disassembly result was complete but had `solved_count=0`; this round did not rerun xref extraction or ordinary candidate generation.
- Mainline is `reverse_solving`; concrete direction is `local_reverse_semantic_rule_extraction_v1`.
- Only the three specified unsolved local reverse targets were processed.
- No challenge binary outside the specified three entered extraction.
- No executable outside indexed `E:\reverse` paths was run.
- No binary sample was copied, committed, uploaded, relocated, or encoded.
- `.codex-skills/` was not modified.
- Full `solve_reports/` and full `PROJECT_PROGRESS_LOG.txt` were not read.
- Semantic extraction was bounded by max rules, candidates, and validations.
- Runtime evidence was recorded for semantic-rule-derived candidates, but no candidate satisfied the conservative success rule.
- All unsolved targets now have a sharper next blocker: `needs_symbolic_execution`.
- Tests were run for this decision and recorded in `project_state/pytest_result.txt`.

## Validation

- `python -m reverse_agent.project_state lint-decision --state-dir project_state` -> OK.
- `python -m py_compile reverse_agent\local_reverse_semantic_rules.py` -> passed.
- `python -m pytest -q tests\test_local_reverse_semantic_rules.py` -> `7 passed`.
- `python -m pytest -q tests\test_local_reverse_runtime.py tests\test_local_reverse_compare_site.py tests\test_local_reverse_xref_disassembly.py tests\test_local_reverse_semantic_rules.py` -> `30 passed`.
- `python -m reverse_agent.local_reverse_semantic_rules --corpus-index project_state\local_reverse_corpus_index.json --xref-result project_state\local_reverse_xref_disassembly_result.json --policy project_state\local_reverse_runtime_policy.json --out project_state\local_reverse_semantic_rule_result.json` -> `local reverse semantic rule extraction: status=PARTIAL targets=3 solved=0`.
- `python -m reverse_agent.project_state lint-report --state-dir project_state` -> OK with expected `PARTIAL` and not-archived warnings.
- `python -m reverse_agent.project_state status --state-dir project_state` -> `decision_execution_state=CONSUMED_BY_NON_SUCCESS_REPORT`.
- `git diff --check` -> passed with line-ending warnings for report files only.
