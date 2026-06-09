```json codex_report_summary
{
  "schema_version": 1,
  "report_id": "report_20260609_ollydbg_user_path_preflight_validation_v1",
  "round_id": "round_20260609_ollydbg_user_path_preflight_validation_v1",
  "based_on_decision_id": "decision_20260609_ollydbg_user_path_preflight_validation_v1",
  "status": "SUCCESS",
  "acceptance_recommendation": "ACCEPTED",
  "mainline": "tool_integration",
  "sample_id": "samplereverse",
  "candidate_generated": false,
  "candidate_validation_attempted": false,
  "runtime_validation_attempted": false,
  "debugger_attached": false,
  "emulator_used": false,
  "ida_ghidra_static_extraction_attempted": false,
  "full_solve_reports_read": false,
  "training_status_modified": false,
  "status_overlay_modified": false,
  "files_changed": [
    "reverse_agent/ollydbg_preflight.py",
    "tests/test_ollydbg_preflight.py",
    "project_state/ollydbg_preflight_result.json",
    "project_state/codex_execution_report.md",
    "project_state/pytest_result.txt"
  ],
  "tests_ran": [
    "python -m reverse_agent.project_state status",
    "python -m reverse_agent.project_state lint-decision",
    "python -m reverse_agent.project_state lint-report",
    "python -m pytest tests/test_project_state.py tests/test_ollydbg_preflight.py",
    "$env:REVERSE_AGENT_OLLYDBG_PATH = 'E:\\Program Files\\ollydbg'; python -m reverse_agent.ollydbg_preflight --out project_state/ollydbg_preflight_result.json",
    "python -m json.tool project_state/ollydbg_preflight_result.json > NUL"
  ],
  "generated_artifacts": [
    "project_state/ollydbg_preflight_result.json"
  ],
  "preflight_result": {
    "ready": false,
    "backend_ready": false,
    "runtime_ready": false,
    "ollydbg_executable_found": true,
    "ollydbg_executable_path": "E:\\Program Files\\ollydbg\\ollydbg.exe",
    "olly_script_module_importable": false,
    "sample_path_resolvable": false,
    "preflight_recommendation": "preflight_not_configured_user_env_needed",
    "next_decision_recommendation": "blocked_waiting_for_user_sample_or_ollyscript_config"
  }
}
```

# Codex Execution Report

## 1. Decision Authority Check

- [x] `project_state/decision_packet.md` is the execution authority for this round.
- [x] Active decision: `decision_20260609_ollydbg_user_path_preflight_validation_v1`.
- [x] Active round: `round_20260609_ollydbg_user_path_preflight_validation_v1`.
- [x] Mainline is `tool_integration`; this is a bounded path-validation preflight round.
- [x] No sample binary was executed.
- [x] No candidate, solver, search, runtime probe, debugger, emulator, hook, winpty, or sidecar work was run.
- [x] `.codex-skills/` was not modified.
- [x] `training_status`, status overlay, sample metadata, and archive directories were not modified.
- [x] No changes outside allowed scope (preflight path validation, tests, preflight JSON, report, pytest_result).
- [x] Full `solve_reports/` and full `PROJECT_PROGRESS_LOG.txt` were not read.

## 2. Scope

Validate the user-provided OllyDbg tool location (`E:\Program Files\ollydbg`) in the existing non-invasive preflight path. Two changes were made:

1. **Repaired `reverse_agent/ollydbg_preflight.py`** — added `_resolve_ollydbg_exe()` helper that:
   - Accepts a direct file path to `ollydbg.exe`
   - Accepts a directory path and resolves it to `ollydbg.exe` inside that directory
   - Rejects a directory that does not contain `ollydbg.exe`
   - Rejects non-existent paths
   - Rejects files that do not end with `.exe`
   - Never misclassifies a directory as an executable

2. **Added hermetic tests in `tests/test_ollydbg_preflight.py`** — 5 new `_resolve_ollydbg_exe` tests:
   - `test_resolve_ollydbg_exe_direct_file` — env var points directly to executable
   - `test_resolve_ollydbg_exe_directory_with_exe` — env var points to directory containing `ollydbg.exe`
   - `test_resolve_ollydbg_exe_directory_without_exe` — env var points to directory without `ollydbg.exe`
   - `test_resolve_ollydbg_exe_nonexistent_path` — env var points to non-existent path
   - `test_resolve_ollydbg_exe_directory_not_marked_executable` — directory must not be misclassified as executable

3. **Ran preflight with user-provided path** — `REVERSE_AGENT_OLLYDBG_PATH=E:\Program Files\ollydbg`

## 3. Preflight Result with User Path

```json
{
  "preflight_name": "ollydbg_backend_preflight",
  "preflight_version": 2,
  "ready": false,
  "backend_ready": false,
  "runtime_ready": false,
  "checks": {
    "ollydbg_executable_found": true,
    "ollydbg_executable_path": "E:\\Program Files\\ollydbg\\ollydbg.exe",
    "olly_script_module_importable": false,
    "olly_scripts_directory_exists": true,
    "step_audit_script_exists": true,
    "sample_path_resolvable": false,
    "sample_path": null
  },
  "recommendation": "preflight_not_configured_user_env_needed"
}
```

**Interpretation:**
- ✅ OllyDbg executable found at `E:\Program Files\ollydbg\ollydbg.exe` (directory correctly resolved to executable)
- ❌ OllyDbg Python module (`olly.ollyscript`) not importable
- ❌ Sample path not resolvable
- ❌ `backend_ready` is false (module missing)
- ❌ `runtime_ready` is false (module + sample missing)

## 4. Path Validation Behavior

### Before (Defective)

```python
p = Path(env)
if p.exists():
    return p  # Would return a directory as "executable"
```

### After (Repaired)

```python
def _resolve_ollydbg_exe(p: Path) -> Path | None:
    if not p.exists():
        return None
    if p.is_file():
        if p.suffix.lower() == ".exe":
            return p
        return None
    if p.is_dir():
        candidate = p / "ollydbg.exe"
        if candidate.exists() and candidate.is_file():
            return candidate
    return None
```

A directory path is now safely resolved to `ollydbg.exe` inside it, or rejected if the executable is missing.

## 5. Tests

### 5.1 Focused Preflight Tests

`tests/test_ollydbg_preflight.py` — 13 tests, all hermetic:

| Test | Category |
|------|----------|
| `test_step_audit_script_exists` | Script presence |
| `test_olly_script_module_not_available_when_spec_missing` | Module mock |
| `test_resolve_ollydbg_exe_direct_file` | **NEW** — direct executable path |
| `test_resolve_ollydbg_exe_directory_with_exe` | **NEW** — directory with exe |
| `test_resolve_ollydbg_exe_directory_without_exe` | **NEW** — directory without exe |
| `test_resolve_ollydbg_exe_nonexistent_path` | **NEW** — non-existent path |
| `test_resolve_ollydbg_exe_directory_not_marked_executable` | **NEW** — directory safety |
| `test_preflight_all_false_when_nothing_configured` | Default state |
| `test_preflight_backend_ready_but_sample_missing` | Backend ready, sample missing |
| `test_preflight_fully_ready_when_all_mocked` | Fully ready |
| `test_preflight_respects_explicit_paths` | Explicit paths |
| `test_preflight_main_cli_exit_code_when_not_ready` | CLI not ready |
| `test_preflight_main_cli_exit_code_when_ready` | CLI ready |

**Result: 13/13 passed**

### 5.2 Full Test Suite

`tests/test_project_state.py` + `tests/test_ollydbg_preflight.py` — **171/171 passed** (158 existing + 13 preflight)

## 6. JSON Validation

Command: `python -m json.tool project_state/ollydbg_preflight_result.json > NUL`

Result: PASSED (exit code 0) — JSON is well-formed and valid.

## 7. negative_results.json Cross-Check

This path-validation work does not repeat any blocked solver/probe direction:
- No compare-aware search executed
- No candidate validation performed
- No runtime probe launched
- No full solve_reports commit attempted
- All negative-result prohibitions respected

## 8. Required Audit Checklist

| # | Check | Result |
|---|-------|--------|
| 1 | decision_packet.md has fenced JSON decision_meta block | PASS |
| 2 | decision_meta.status == APPROVED | PASS |
| 3 | decision_meta.mainline == tool_integration | PASS |
| 4 | Both skill profiles active in registry | PASS |
| 5 | decision_packet.md is execution authority; task_packet.json advisory | PASS |
| 6 | `_ollydbg_exe_path()` behavior inspected for directory misclassification | PASS |
| 7 | Directory path safely resolved to `ollydbg.exe` inside it | PASS |
| 8 | Directory without `ollydbg.exe` rejected | PASS |
| 9 | Non-existent path rejected | PASS |
| 10 | File path without `.exe` suffix rejected | PASS |
| 11 | Tests hermetic (mocked, no real OllyDbg dependency) | PASS |
| 12 | Tests cover: direct file, directory with exe, directory without exe, non-existent, directory safety | PASS |
| 13 | Runtime readiness remains false when sample missing, even if executable found | PASS |
| 14 | Preflight run with user-provided path recorded | PASS |
| 15 | `preflight_recommendation` and `next_decision_recommendation` preserved as separate fields | PASS |
| 16 | Generated JSON, report summary, pytest_result summary agree on actual preflight recommendation | PASS |
| 17 | Next-step recommendation is one of 3 allowed values | PASS |
| 18 | no stale old IDs in pytest_result.txt | PASS |
| 19 | codex_execution_report.md matches this decision/round ID | PASS |

## 9. Stop Conditions

No stop condition triggered. This path-validation preflight round is complete and accepted.
