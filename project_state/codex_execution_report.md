```json codex_report_summary
{
  "schema_version": 1,
  "report_id": "report_20260603_ida_guided_solver_trust_gate_v1",
  "round_id": "round_20260603_ida_guided_solver_trust_gate_v1",
  "based_on_decision_id": "decision_20260603_ida_guided_solver_trust_gate_v1",
  "status": "SUCCESS",
  "acceptance_recommendation": "ACCEPTED",
  "files_changed": [
    "reverse_agent/local_reverse_ida_guided_solver.py",
    "tests/test_local_reverse_ida_guided_solver.py",
    "project_state/local_reverse_ida_solver_result.json",
    "project_state/artifact_index.json",
    "project_state/codex_execution_report.md",
    "project_state/pytest_result.txt"
  ],
  "tests_ran": [
    "python -m py_compile reverse_agent\\local_reverse_ida_guided_solver.py",
    "python -m pytest -q tests\\test_local_reverse_ida_guided_solver.py",
    "python -m reverse_agent.local_reverse_ida_guided_solver --ida-summary project_state\\local_reverse_ida_summary.json --artifact-index project_state\\artifact_index.json --policy project_state\\local_reverse_runtime_policy.json --out project_state\\local_reverse_ida_solver_result.json",
    "python -m json.tool project_state\\current_state.json > NUL",
    "python -m json.tool project_state\\artifact_index.json > NUL",
    "python -m json.tool project_state\\local_reverse_ida_summary.json > NUL",
    "python -m json.tool project_state\\local_reverse_ida_solver_result.json > NUL",
    "python -m pytest -q tests\\test_local_reverse_string_solver.py tests\\test_local_reverse_ida_summary.py tests\\test_project_state.py tests\\test_local_reverse_ida_guided_solver.py",
    "python -m reverse_agent.project_state lint-decision --state-dir project_state",
    "python -m reverse_agent.project_state lint-report --state-dir project_state",
    "git diff --check"
  ],
  "generated_artifacts": [
    "project_state/local_reverse_ida_solver_result.json"
  ],
  "result_status": "PARTIAL"
}
```

# Codex Execution Report

## Decision Alignment

This execution follows `project_state/decision_packet.md` for `decision_20260603_ida_guided_solver_trust_gate_v1`.

The mainline for this round is `engineering_branch`. The current `samplereverse` task packet fields remain compatibility/background; the active decision packet was the execution authority.

This round implements the trust gate for `reverse_agent/local_reverse_ida_guided_solver.py`: artifact freshness/provenance and classification evidence gating only. It does not continue local_reverse solving and does not advance the three targets to validated.

## Implementation

`local_reverse_ida_guided_solver` now resolves raw IDA evidence through `latest_artifacts_v2` only. A raw evidence artifact must have `freshness=current`, a non-empty path, an existing file, and parseable JSON before it can influence classification or candidate derivation.

Legacy `latest_artifacts` is no longer used as a current-evidence fallback for raw IDA JSON. Stale, missing, unknown, pathless, missing-file, or invalid-JSON artifacts cause the affected target to be blocked with an explicit artifact-key reason.

Classification was tightened so `relative_path` and filename are weak hints only. `sha_256` filename alone no longer selects `hash_hex_compare_static`; the hash profile requires 64-byte compare evidence, `%08x/%08X` format evidence, a 64-hex target, and hash/data-flow evidence. `CPP2` no longer selects a transform profile by filename alone. The API/password profile requires pwd-like string evidence, compare/API evidence, and decompiler/data-flow evidence.

`solved_count` is now conservative and counts only validated targets. Rejected or blocked candidates do not increase solved or validated counts. Validation still treats output containing both success and failure markers as rejected.

## Result Summary

The official solver result was regenerated:

```text
project_state/local_reverse_ida_solver_result.json
status=PARTIAL
target_count=3
solved_count=0
validated_count=0
runtime_validation_attempted_count=1
```

The three local_reverse targets remain unvalidated:

```text
18019fca52b389fe / sha_256.exe -> unverified, no bounded preimage domain
4c69f173f2bd0211 / CPP2.exe -> unverified, upstream hash/transform remains uninverted
bcbd9979db015bfd / Cpp1.exe -> rejected, hookapi still prints try again
```

`project_state/artifact_index.json` was updated only to keep `local_reverse_ida_solver_result` metadata current for the regenerated official result.

## Scope Audit

- IDA was not rerun.
- Ghidra was not run.
- OllyDbg/x64dbg/Frida/debugger probes were not run.
- No samples outside the three registered local_reverse targets were processed.
- The sample set was not expanded.
- No sample binary was copied into the repo, committed, uploaded, or encoded.
- Full `solve_reports/` was not read.
- Full `PROJECT_PROGRESS_LOG.txt` was not read.
- `.codex-skills/` was not modified.
- Runtime validation was limited to the existing policy-bounded `Cpp1` candidate probe performed by the solver CLI.

## Validation

```text
python -m py_compile reverse_agent\local_reverse_ida_guided_solver.py -> passed
python -m pytest -q tests\test_local_reverse_ida_guided_solver.py -> 7 passed
solver CLI -> status=PARTIAL targets=3 solved=0 validated=0
python -m json.tool project_state\current_state.json > NUL -> passed
python -m json.tool project_state\artifact_index.json > NUL -> passed
python -m json.tool project_state\local_reverse_ida_summary.json > NUL -> passed
python -m json.tool project_state\local_reverse_ida_solver_result.json > NUL -> passed
python -m pytest -q tests\test_local_reverse_string_solver.py tests\test_local_reverse_ida_summary.py tests\test_project_state.py tests\test_local_reverse_ida_guided_solver.py -> 176 passed
python -m reverse_agent.project_state lint-decision --state-dir project_state -> OK
python -m reverse_agent.project_state lint-report --state-dir project_state -> OK, with report round not archived warning
git diff --check -> passed with line-ending warnings only
```
