```json codex_report_summary
{
  "schema_version": 1,
  "report_id": "report_20260603_local_reverse_ida_evidence_integration_v1",
  "round_id": "round_20260603_local_reverse_ida_evidence_integration_v1",
  "based_on_decision_id": "decision_20260603_local_reverse_ida_evidence_integration_v1",
  "status": "BLOCKED",
  "acceptance_recommendation": "NEEDS_REVIEW",
  "files_changed": [
    "reverse_agent/tool_runners.py",
    "reverse_agent/ida_scripts/collect_evidence.py",
    "reverse_agent/local_reverse_ida_summary.py",
    "tests/test_local_reverse_ida_summary.py",
    "tests/test_tool_runners.py",
    "project_state/local_reverse_ida_summary.json",
    "project_state/codex_execution_report.md",
    "project_state/pytest_result.txt"
  ],
  "tests_ran": [
    "python -m py_compile reverse_agent\\tool_runners.py reverse_agent\\local_reverse_ida_summary.py reverse_agent\\ida_scripts\\collect_evidence.py",
    "python -m pytest -q tests\\test_local_reverse_ida_summary.py tests\\test_local_reverse_semantic_rules.py tests\\test_tool_runners.py",
    "python -m pytest -q",
    "python -m reverse_agent.local_reverse_ida_summary --corpus-index project_state\\local_reverse_corpus_index.json --semantic-result project_state\\local_reverse_semantic_rule_result.json --policy project_state\\local_reverse_runtime_policy.json --out project_state\\local_reverse_ida_summary.json",
    "python -m reverse_agent.project_state lint-decision --state-dir project_state",
    "python -m reverse_agent.project_state lint-report --state-dir project_state",
    "git diff --check"
  ],
  "generated_artifacts": [
    "project_state/local_reverse_ida_summary.json"
  ],
  "next_suggested_task": "Run local_reverse_ida_summary again with a valid IDA/idat path, then use ida_summary_guided_solver_v1 if evidence is produced"
}
```

# Codex Execution Report

## Decision Alignment

This execution follows `project_state/decision_packet.md` for `decision_20260603_local_reverse_ida_evidence_integration_v1`.

The stale `samplereverse` fields in `project_state/task_packet.json` and `project_state/current_state.json` were treated as background only. The active decision packet controls this round.

This round replaces the previous `bounded_symbolic_execution_v1` direction because the repository already has IDA integration that should be reused.

## Scope

This round only processed the three local reverse targets from `project_state/local_reverse_semantic_rule_result.json` with `solved=false` and `missing_evidence=needs_symbolic_execution`:

```text
4c69f173f2bd0211 -> 逆向课程2022春02/CPP2.exe
bcbd9979db015bfd -> 逆向课程2022春补考01/Cpp1.exe
18019fca52b389fe -> 逆向课程2024春01/sha_256.exe
```

No other challenge binary entered IDA evidence integration. No executable outside indexed `E:\reverse` paths was run. No binary sample was copied into the repository, uploaded, committed, relocated, or encoded as hex/base64.

No `.codex-skills/` files were modified. Full `solve_reports/` and full `PROJECT_PROGRESS_LOG.txt` were not read. This round did not continue `samplereverse` window discovery, compare handoff work, Base64/RC4 breakpoint probing, old `sample_solver`, GUI integration, Redis, databases, or a new agent platform.

## Implementation

Added `run_ida_evidence(...)` in `reverse_agent/tool_runners.py` as a public wrapper over the existing IDA automation path. It constructs `ToolAutomationConfig` and reuses `_run_ida`, `_resolve_ida_executable`, `_resolve_ida_script`, the existing headless IDA command shape, and `REVERSE_AGENT_IDA_OUT`. `run_tool_automation()` now calls that wrapper, preserving existing GUI/pipeline behavior.

Extended `reverse_agent/ida_scripts/collect_evidence.py` additively. The existing fields remain compatible:

```text
strings
functions
compare_contexts
local_check_contexts
control_id_contexts
```

New bounded fields:

```text
string_xrefs
validation_function_candidates
hexrays_available
decompiler_snippets
solver_hints
```

Hex-Rays is treated as optional. If the API/plugin is unavailable, the script reports `hexrays_available=false` and `decompiler_snippets=[]`.

Added `reverse_agent/local_reverse_ida_summary.py`, a bounded CLI and library module:

```text
python -m reverse_agent.local_reverse_ida_summary --corpus-index project_state\local_reverse_corpus_index.json --semantic-result project_state\local_reverse_semantic_rule_result.json --policy project_state\local_reverse_runtime_policy.json --out project_state\local_reverse_ida_summary.json
```

The orchestrator validates root/path/sha256 before invoking IDA. Raw IDA output is directed to ignored `solve_reports/tool_artifacts/local_reverse_ida_evidence_integration_v1/`; tracked `project_state/local_reverse_ida_summary.json` keeps only a lightweight summary and output paths.

## Result

Generated:

```text
project_state/local_reverse_ida_summary.json
```

Summary:

```text
status=BLOCKED
target_count=3
success_count=0
ida_available=false
hexrays_available_any=false
```

Per-target result:

```text
18019fca52b389fe -> ida_status=blocked, blocked_reasons=[BLOCKED_BY_IDA_UNAVAILABLE]
4c69f173f2bd0211 -> ida_status=blocked, blocked_reasons=[BLOCKED_BY_IDA_UNAVAILABLE]
bcbd9979db015bfd -> ida_status=blocked, blocked_reasons=[BLOCKED_BY_IDA_UNAVAILABLE]
```

The local machine did not expose an IDA/idat executable through the configured path or PATH lookup, so no real IDA evidence or Hex-Rays snippets were produced. The result is intentionally `BLOCKED`; mock/fake IDA output was used only for tests and was not presented as real evidence.

## Required Audit

- Current `decision_packet.md` was the execution authority.
- This round replaced the previous symbolic-execution direction by reusing existing IDA integration.
- Mainline is `reverse_solving`; concrete direction is `local_reverse_ida_evidence_integration_v1`.
- Only the three specified `needs_symbolic_execution` local reverse targets were processed.
- No challenge binary outside those three entered IDA evidence integration.
- No executable outside indexed `E:\reverse` paths was run.
- No binary sample was copied, committed, uploaded, relocated, or encoded.
- `.codex-skills/` was not modified.
- Full `solve_reports/` and full `PROJECT_PROGRESS_LOG.txt` were not read.
- Existing `tool_runners.py` / `collect_evidence.py` were reused; no separate IDA startup framework was created.
- `collect_evidence.py` preserved old fields while adding bounded new fields.
- IDA unavailable was recorded as `BLOCKED_BY_IDA_UNAVAILABLE`; no IDA success was fabricated.
- Hex-Rays snippets were not fabricated.
- Tests were run and recorded in `project_state/pytest_result.txt`.
