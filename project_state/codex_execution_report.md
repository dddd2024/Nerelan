```json codex_report_summary
{
  "schema_version": 1,
  "report_id": "report_20260603_ida_summary_guided_solver_v1",
  "round_id": "round_20260603_ida_summary_guided_solver_v1",
  "based_on_decision_id": "decision_20260603_ida_summary_guided_solver_v1",
  "status": "SUCCESS",
  "acceptance_recommendation": "ACCEPTED",
  "files_changed": [
    "reverse_agent/local_reverse_ida_guided_solver.py",
    "tests/test_local_reverse_ida_guided_solver.py",
    "project_state/local_reverse_ida_solver_result.json",
    "project_state/artifact_index.json",
    "project_state/current_state.json",
    "project_state/task_packet.json",
    "project_state/codex_execution_report.md",
    "project_state/pytest_result.txt"
  ],
  "tests_ran": [
    "python -m py_compile reverse_agent\\local_reverse_ida_guided_solver.py",
    "python -m pytest -q tests\\test_local_reverse_ida_guided_solver.py",
    "python -m reverse_agent.local_reverse_ida_guided_solver --ida-summary project_state\\local_reverse_ida_summary.json --artifact-index project_state\\artifact_index.json --policy project_state\\local_reverse_runtime_policy.json --out project_state\\local_reverse_ida_solver_result.json",
    "python -m json.tool project_state\\current_state.json > NUL",
    "python -m json.tool project_state\\artifact_index.json > NUL",
    "python -m json.tool project_state\\task_packet.json > NUL",
    "python -m json.tool project_state\\local_reverse_ida_summary.json > NUL",
    "python -m json.tool project_state\\local_reverse_ida_solver_result.json > NUL",
    "python -c \"import json; d=json.load(open('project_state/local_reverse_ida_solver_result.json', encoding='utf-8')); assert d['target_count']==3; assert len(d['targets'])==3; assert all(t.get('classification') for t in d['targets']); assert all(t.get('selected_solver_profile') for t in d['targets'])\"",
    "python -m pytest -q tests\\test_local_reverse_string_solver.py tests\\test_local_reverse_ida_summary.py tests\\test_project_state.py tests\\test_local_reverse_ida_guided_solver.py",
    "python -m reverse_agent.project_state lint-decision --state-dir project_state",
    "python -m reverse_agent.project_state lint-report --state-dir project_state",
    "git diff --check"
  ],
  "generated_artifacts": [
    "project_state/local_reverse_ida_solver_result.json",
    "project_state/artifact_index.json",
    "project_state/current_state.json",
    "project_state/task_packet.json"
  ],
  "result_status": "PARTIAL",
  "next_suggested_task": "Refine local_reverse static constraints for sha_256/CPP2 and investigate Cpp1 rejected static candidate"
}
```

# Codex Execution Report

## Decision Alignment

This execution follows `project_state/decision_packet.md` for `decision_20260603_ida_summary_guided_solver_v1`.

The mainline for this round is `reverse_solving`. `project_state/task_packet.json` remains advisory/background only; the active decision packet was the execution authority. Existing `samplereverse` fields in `current_state.json` were treated as compatibility/background, not current evidence.

Current evidence entrypoints were:

```text
project_state/current_state.json -> local_reverse_training.current_ida_evidence
project_state/artifact_index.json -> local_reverse_ida_summary and local_reverse_ida_evidence_*
project_state/local_reverse_ida_summary.json
```

## Implementation

Added `reverse_agent/local_reverse_ida_guided_solver.py`, a thin IDA-summary-guided orchestrator rather than a hard-coded one-sample solver. It reads the registered IDA summary and raw IDA JSON files, classifies each sample, chooses a bounded solver profile, derives only evidence-backed candidates, and writes `project_state/local_reverse_ida_solver_result.json`.

Existing `reverse_agent/local_reverse_string_solver.py` was inspected and left unchanged because it solves from binary strings plus runtime probes, not from registered IDA evidence/provenance. `sample_solver.py` was inspected only as a legacy sample-specific path and was not used as the primary solver.

Read raw IDA JSON paths:

```text
solve_reports\tool_artifacts\local_reverse_ida_evidence_integration_v1\18019fca52b389fe\sha_256_ida_evidence.json
solve_reports\tool_artifacts\local_reverse_ida_evidence_integration_v1\4c69f173f2bd0211\CPP2_ida_evidence.json
solve_reports\tool_artifacts\local_reverse_ida_evidence_integration_v1\bcbd9979db015bfd\Cpp1_ida_evidence.json
```

No full `solve_reports/` scan was performed.

## Result Summary

Generated `project_state/local_reverse_ida_solver_result.json`:

```text
status=PARTIAL
target_count=3
solved_count=0
validated_count=0
runtime_validation_attempted_count=1
```

Per-sample outcomes:

```text
18019fca52b389fe / sha_256.exe
classification=sha256_hex_compare_with_post_hash_character_adjustment
profile=hash_hex_compare_static
candidate=<none>
validation_status=unverified
reason=64-byte hash compare target exists, but current evidence has no bounded preimage domain.

4c69f173f2bd0211 / CPP2.exe
classification=bounded_input_range_hash_output_increment_compare
profile=bounded_char_transform_inversion
candidate=<none>
validation_status=unverified
reason=input range and post-transform increment are visible, but upstream hash/transform routine remains uninverted.

bcbd9979db015bfd / Cpp1.exe
classification=api_assisted_password_write_and_compare
profile=direct_or_api_password_extraction
candidate=hookapi
validation_status=rejected
reason=static XOR candidate was tested by bounded runtime probe and output contained "try again!".
```

The `Cpp1` candidate was not promoted to validated. The recorded probe output was:

```text
Press any key to continue . . .
Please input your flag
File open success
try again!
```

`project_state/artifact_index.json`, `current_state.json`, and `task_packet.json` were minimally updated so the generated solver result is discoverable by the next compact-state pass.

## Scope Audit

- IDA was not rerun.
- Ghidra was not run.
- OllyDbg/x64dbg/Frida/debugger probes were not run.
- No samples outside the three registered targets were processed.
- The sample set was not expanded to 22.
- No sample binary was copied into the repo, committed, uploaded, or encoded.
- Full `solve_reports/` was not read.
- Full `PROJECT_PROGRESS_LOG.txt` was not read.
- `.codex-skills/` was not modified.
- Runtime validation was limited to one policy-bounded candidate probe for `Cpp1`.

## Validation

```text
python -m py_compile reverse_agent\local_reverse_ida_guided_solver.py -> passed
python -m pytest -q tests\test_local_reverse_ida_guided_solver.py -> 2 passed
solver CLI -> status=PARTIAL targets=3 solved=0 validated=0
python -m json.tool project_state\current_state.json > NUL -> passed
python -m json.tool project_state\artifact_index.json > NUL -> passed
python -m json.tool project_state\task_packet.json > NUL -> passed
python -m json.tool project_state\local_reverse_ida_summary.json > NUL -> passed
python -m json.tool project_state\local_reverse_ida_solver_result.json > NUL -> passed
result schema assertion -> passed
python -m pytest -q tests\test_local_reverse_string_solver.py tests\test_local_reverse_ida_summary.py tests\test_project_state.py tests\test_local_reverse_ida_guided_solver.py -> 171 passed
python -m reverse_agent.project_state lint-decision --state-dir project_state -> OK
python -m reverse_agent.project_state lint-report --state-dir project_state -> OK
git diff --check -> passed with line-ending warnings only
```
