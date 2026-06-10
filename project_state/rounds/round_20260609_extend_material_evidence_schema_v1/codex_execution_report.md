```json codex_report_summary
{
  "schema_version": 1,
  "report_id": "report_20260609_extend_material_evidence_schema_v1",
  "round_id": "round_20260609_extend_material_evidence_schema_v1",
  "based_on_decision_id": "decision_20260609_extend_material_evidence_schema_v1",
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
    "reverse_agent/evidence.py",
    "reverse_agent/tool_runners.py",
    "tests/test_tool_runners.py",
    "project_state/codex_execution_report.md",
    "project_state/pytest_result.txt"
  ],
  "tests_ran": [
    "python -m reverse_agent.project_state status",
    "python -m reverse_agent.project_state lint-decision",
    "python -m reverse_agent.project_state lint-report",
    "python -m pytest tests/test_tool_runners.py -q",
    "python -m pytest tests/test_project_state.py tests/test_tool_runners.py tests/test_ollydbg_preflight.py tests/test_pipeline.py tests/test_harness_artifact_manifest.py -q"
  ],
  "generated_artifacts": [],
  "schema_changes": {
    "evidence_py": {
      "added_constants": ["EVIDENCE_KIND_BASE64_MATERIAL", "EVIDENCE_KIND_RC4_MATERIAL", "EVIDENCE_KIND_UTF16LE_MATERIAL"],
      "added_functions": ["base64_material_evidence()", "rc4_material_evidence()", "utf16le_material_evidence()"],
      "backward_compatible": true
    },
    "tool_runners_py": {
      "added_function": "_ingest_material_evidence()",
      "modified_function": "_structured_evidence_from_json()",
      "backward_compatible": true
    }
  }
}
```

# Codex Execution Report

## 1. Decision Authority Check

- [x] `project_state/decision_packet.md` is the execution authority for this round.
- [x] Active decision: `decision_20260609_extend_material_evidence_schema_v1`.
- [x] Active round: `round_20260609_extend_material_evidence_schema_v1`.
- [x] Mainline is `tool_integration`; this is a bounded schema-extension round.
- [x] No sample binary was executed.
- [x] No candidate, solver, search, runtime probe, debugger, emulator, hook, winpty, or sidecar work was run.
- [x] `.codex-skills/` was not modified.
- [x] `training_status`, status overlay, sample metadata, and source modules were not modified.
- [x] Changes are within allowed scope (evidence.py, tool_runners.py, test_tool_runners.py).
- [x] Full `solve_reports/` and full `PROJECT_PROGRESS_LOG.txt` were not read.

## 2. Scope

Implement the next step recommended by `tool_interface_gap_audit_material_evidence_v1`: extend `StructuredEvidence` with dedicated material evidence kinds and update the JSON evidence converter in `tool_runners.py` to support Base64/RC4/UTF-16LE material probe outputs from existing OllyDbg scripts.

This round:
1. Extended `reverse_agent/evidence.py`:
   - Added 3 evidence kind constants: `EVIDENCE_KIND_BASE64_MATERIAL`, `EVIDENCE_KIND_RC4_MATERIAL`, `EVIDENCE_KIND_UTF16LE_MATERIAL`
   - Added 3 helper constructors: `base64_material_evidence()`, `rc4_material_evidence()`, `utf16le_material_evidence()`
   - All constructors accept explicit material-probe fields and produce properly-structured `StructuredEvidence` records
2. Extended `reverse_agent/tool_runners.py`:
   - Added `_ingest_material_evidence()` helper that looks for explicit material-probe JSON keys and converts them to material evidence records
   - Modified `_structured_evidence_from_json()` to call `_ingest_material_evidence()` after existing evidence branches
   - Does NOT treat compare capture or candidate lists alone as material proof — only explicit material fields trigger ingestion
3. Added 6 unit tests to `tests/test_tool_runners.py`:
   - `test_structured_evidence_from_json_ingests_base64_material`
   - `test_structured_evidence_from_json_ingests_rc4_material`
   - `test_structured_evidence_from_json_ingests_utf16le_material`
   - `test_structured_evidence_from_json_mixed_preserves_existing_evidence`
   - `test_structured_evidence_from_json_unknown_material_fields_no_crash`
   - `test_structured_evidence_from_json_partial_material_fields_no_crash`
4. Updated this report and `pytest_result.txt`.

No new tool runners added. No sample execution. No debugger attached.

## 3. Schema Changes Summary

### evidence.py

| Addition | Description |
|----------|-------------|
| `EVIDENCE_KIND_BASE64_MATERIAL` | Constant `"Base64MaterialEvidence"` |
| `EVIDENCE_KIND_RC4_MATERIAL` | Constant `"RC4MaterialEvidence"` |
| `EVIDENCE_KIND_UTF16LE_MATERIAL` | Constant `"UTF16LEMaterialEvidence"` |
| `base64_material_evidence()` | Constructor with construction_point, input_bytes_hex, output_chars, chunk_boundary_info, instruction_address |
| `rc4_material_evidence()` | Constructor with ksa_point, prga_point, key_material_hex, input_bytes_hex, output_bytes_hex, instruction_address |
| `utf16le_material_evidence()` | Constructor with expansion_point, source_bytes_hex, wide_chars, instruction_address |

### tool_runners.py

| Addition | Description |
|----------|-------------|
| `_ingest_material_evidence()` | Helper that inspects JSON for `base64_*`, `rc4_*`, `utf16le_*` keys and creates material evidence records |
| `_structured_evidence_from_json()` | Extended to call `_ingest_material_evidence()` after existing branches |

### Backward Compatibility

- All existing evidence kinds (`CandidateEvidence`, `RuntimeCompareEvidence`, `StaticStringEvidence`, `ConstraintEvidence`) are unchanged
- `_structured_evidence_from_json()` still produces the same output for JSON without material fields
- No breaking changes to any public API

## 4. Tests

### Test Suite

`tests/test_tool_runners.py` — **17/17 passed** (including 6 new material evidence tests)

`tests/test_project_state.py tests/test_tool_runners.py tests/test_ollydbg_preflight.py tests/test_pipeline.py tests/test_harness_artifact_manifest.py` — **230/230 passed**

## 5. negative_results.json Cross-Check

This schema-extension round does not repeat any blocked solver/probe direction:
- No compare-aware search executed
- No candidate validation performed
- No runtime probe launched
- No full solve_reports commit attempted
- All negative-result prohibitions respected

## 6. Required Audit Checklist

| # | Check | Result |
|---|-------|--------|
| 1 | decision_packet.md has fenced JSON decision_meta block | PASS |
| 2 | decision_meta.status == APPROVED | PASS |
| 3 | decision_meta.mainline == tool_integration | PASS |
| 4 | Both skill profiles active in registry | PASS |
| 5 | decision_packet.md is execution authority; task_packet.json advisory | PASS |
| 6 | decision based_on_state_digest matches current state | PASS |
| 7 | Stale artifacts remain stale | PASS |
| 8 | No negative-result direction repeated | PASS |
| 9 | Report updated to this decision/round | PASS |
| 10 | pytest_result.txt records this round's real outputs | PASS |
| 11 | Final lint-decision passes | PASS |
| 12 | Final lint-report passes | PASS |
| 13 | No sample/tool/debugger/solver/runtime probe | PASS |
| 14 | No `.codex-skills/` changes | PASS |
| 15 | Schema changes are backward compatible | PASS |
| 16 | New tests cover Base64, RC4, UTF-16LE ingestion | PASS |
| 17 | Mixed evidence test confirms existing kinds still work | PASS |

## 7. Stop Conditions

No stop condition triggered. This schema-extension round is complete and accepted.
