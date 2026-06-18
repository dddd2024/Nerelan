```json codex_report_summary
{
  "schema_version": 1,
  "report_id": "codex_report_20260619_static_triage_type_evidence_schema_v1",
  "round_id": "round_20260619_static_triage_type_evidence_schema_v1",
  "based_on_decision_id": "decision_20260619_static_triage_type_evidence_schema_v1",
  "status": "FAILED",
  "acceptance_recommendation": "REWORK_REQUIRED",
  "files_changed": [
    "project_state/codex_execution_report.md",
    "project_state/gates/command_plan.json",
    "project_state/gates/final_gate_result.json",
    "project_state/gates/gate_profile_plan.json",
    "project_state/gates/preflight_result.json",
    "project_state/gates/report_summary_synthesis.json",
    "project_state/gates/round_baseline.json",
    "project_state/gates/round_delta_summary.json",
    "project_state/local_reverse_static_triage_type_evidence_schema.json",
    "project_state/local_reverse_static_triage_type_evidence_schema_report.md",
    "project_state/pytest_result.txt",
    "project_state/rounds/round_20260619_static_triage_type_evidence_schema_v1/codex_execution_report.md",
    "project_state/rounds/round_20260619_static_triage_type_evidence_schema_v1/decision_packet.md",
    "project_state/rounds/round_20260619_static_triage_type_evidence_schema_v1/pytest_result.txt",
    "project_state/rounds/round_20260619_static_triage_type_evidence_schema_v1/round_manifest.json",
    "reverse_agent/local_reverse_single_sample_static_triage.py",
    "tests/test_local_reverse_static_triage_type_evidence_schema.py"
  ],
  "tests_ran": [
    "python -m pytest tests/test_local_reverse_static_triage_type_evidence_schema.py tests/test_local_reverse_first_static_triage_queue.py tests/test_tool_runners.py tests/test_tool_capability_inventory.py tests/test_project_gate.py tests/test_project_state.py -q",
    "python -m reverse_agent.local_reverse_training_status --json",
    "python -m reverse_agent.project_gate preflight --state-dir project_state",
    "python -m reverse_agent.project_gate gate-profile --state-dir project_state",
    "python -m reverse_agent.project_gate gate-profile --state-dir project_state --json",
    "python -m reverse_agent.project_gate command-plan --state-dir project_state",
    "python -m reverse_agent.project_gate command-plan --state-dir project_state --json",
    "python -m reverse_agent.project_gate report-summary --state-dir project_state",
    "python -m reverse_agent.project_gate final-check --state-dir project_state",
    "python -m reverse_agent.project_gate close-round --state-dir project_state --round-id round_20260619_static_triage_type_evidence_schema_v1"
  ],
  "generated_artifacts": [
    "project_state/codex_execution_report.md",
    "project_state/gates/command_plan.json",
    "project_state/gates/final_gate_result.json",
    "project_state/gates/gate_profile_plan.json",
    "project_state/gates/preflight_result.json",
    "project_state/gates/report_summary_synthesis.json",
    "project_state/gates/round_baseline.json",
    "project_state/gates/round_delta_summary.json",
    "project_state/pytest_result.txt",
    "project_state/rounds/round_20260619_static_triage_type_evidence_schema_v1/codex_execution_report.md",
    "project_state/rounds/round_20260619_static_triage_type_evidence_schema_v1/decision_packet.md",
    "project_state/rounds/round_20260619_static_triage_type_evidence_schema_v1/pytest_result.txt",
    "project_state/rounds/round_20260619_static_triage_type_evidence_schema_v1/round_manifest.json"
  ],
  "limitations": [
    "Implementation and tests passed, but final closeout gate remains REWORK_REQUIRED because tool_integration enforces strict historical sample artifact freshness with 50 missing artifacts."
  ]
}
```

# Codex Execution Report - Static Triage Type Evidence Schema V1

## Decision

Decision `decision_20260619_static_triage_type_evidence_schema_v1` (round `round_20260619_static_triage_type_evidence_schema_v1`) on mainline `tool_integration`.

## Status: FAILED

### Completed Work

1. Reused `reverse_agent/local_reverse_single_sample_static_triage.py` and added pure adapter-side type evidence normalization; no new IDA/Ghidra/debugger/tool-runner interface was created.
2. Added `triage.type_evidence` to success artifacts and the same default structure to `_blocked_artifact` results.
3. Added schema fields `schema_version`, `source`, `type_tag_observations`, `profiles`, and `promotion_safety`.
4. Added stable profiles for `string_comparison`, `xor`, `shift_affine`, `bit_operations`, `lookup_table`, `rc4`, `des`, `hash_md5_sha`, `simple_antidebug`, and `mixed_unknown`.
5. Added schema/report artifacts under `project_state/` documenting status vocabulary, hash bounded-domain policy, lookup table evidence fields, and promotion safety.
6. Added synthetic unit tests only; they feed constructed evidence dictionaries and do not run samples or external static/runtime tools.

### Status Vocabulary

Profiles emit only `not_observed`, `candidate_static_signal`, `observed_static_signal`, or `blocked_missing_required_evidence`. The helper does not emit `static_verified`; promotion safety records that keyword hits, metadata, filenames, sample ids, solver module names, and queue membership are insufficient for static verification.

### Profile Coverage

Synthetic tests cover string comparison, XOR, shift/affine, bit operations, lookup-table missing base/size/contents, RC4, DES, hash with and without bounded-domain evidence, simple anti-debug signals, and default type evidence on the blocked artifact path.

### Safety Audit

`reverse_agent/ida_scripts/collect_evidence.py`, `reverse_agent/tool_runners.py`, `reverse_agent/evidence.py`, solver modules, harness modules, GUI/frontend, inventory/status builders, and project gate logic were not modified. This round did not run IDA, Ghidra, sample binaries, runtime probes, solvers, harnesses, debuggers, emulators, sidecars, or GUI workflows.

### Tests And Gates

The focused synthetic test passed with `10 passed`. The full command-plan pytest passed with `869 passed`. Read-only training status reported `writes_files=false`. Preflight, gate-profile, command-plan, report-summary, final-check, and conditional close-round were run or are recorded in `project_state/pytest_result.txt` as required by the command plan.

### Limitations

This round changes adapter schema and synthetic coverage only. It does not claim real sample static verification, candidate validation, or solved-sample progress.

### Closeout Result

Implementation and test validation passed, and the round archive was created. Final closeout remains `REWORK_REQUIRED` because `tool_integration` status policy treats the historical artifact freshness warning (`50 missing, 0 stale artifacts`) as blocking.
