```json codex_report_summary
{
  "schema_version": 1,
  "report_id": "codex_report_20260617_training_dataset_cipher_static_evidence_profile_v1",
  "round_id": "round_20260617_training_dataset_cipher_static_evidence_profile_v1",
  "based_on_decision_id": "decision_20260617_training_dataset_cipher_static_evidence_profile_v1",
  "status": "SUCCESS",
  "acceptance_recommendation": "ACCEPTED_WITH_LIMITATIONS",
  "files_changed": [
    "project_state/codex_execution_report.md",
    "project_state/gates/command_plan.json",
    "project_state/gates/final_gate_result.json",
    "project_state/gates/preflight_result.json",
    "project_state/gates/report_summary_synthesis.json",
    "project_state/gates/round_baseline.json",
    "project_state/gates/round_close_snapshot.json",
    "project_state/gates/round_delta_summary.json",
    "project_state/gates/run_round_result.json",
    "project_state/pytest_result.txt",
    "project_state/rounds/round_20260617_training_dataset_cipher_static_evidence_profile_v1/codex_execution_report.md",
    "project_state/rounds/round_20260617_training_dataset_cipher_static_evidence_profile_v1/decision_packet.md",
    "project_state/rounds/round_20260617_training_dataset_cipher_static_evidence_profile_v1/pytest_result.txt",
    "project_state/rounds/round_20260617_training_dataset_cipher_static_evidence_profile_v1/round_manifest.json"
  ],
  "tests_ran": [
    "git status --short",
    "Set-Location F:\\reverse-agent",
    "Get-Location",
    "Test-Path F:\\reverse-agent",
    "git rev-parse --show-toplevel",
    "python -m reverse_agent.project_gate preflight --state-dir project_state",
    "python -m reverse_agent.project_gate command-plan --state-dir project_state",
    "python -m reverse_agent.project_gate command-plan --state-dir project_state --json",
    "python -m reverse_agent.project_gate run-round --state-dir project_state --dry-run --json",
    "python -m reverse_agent.project_state doctor --state-dir project_state",
    "python -m reverse_agent.project_state lint-report --state-dir project_state",
    "python -m pytest tests/test_local_reverse_training_status.py tests/test_project_state.py tests/test_project_gate.py -q",
    "python -m reverse_agent.project_gate report-summary --state-dir project_state",
    "python -m reverse_agent.project_gate final-check --state-dir project_state",
    "python -m reverse_agent.project_gate close-round --state-dir project_state --round-id round_20260617_training_dataset_cipher_static_evidence_profile_v1"
  ],
  "generated_artifacts": [
    "project_state/codex_execution_report.md",
    "project_state/gates/command_plan.json",
    "project_state/gates/final_gate_result.json",
    "project_state/gates/preflight_result.json",
    "project_state/gates/report_summary_synthesis.json",
    "project_state/gates/round_baseline.json",
    "project_state/gates/round_close_snapshot.json",
    "project_state/gates/round_delta_summary.json",
    "project_state/gates/run_round_result.json",
    "project_state/pytest_result.txt",
    "project_state/rounds/round_20260617_training_dataset_cipher_static_evidence_profile_v1/codex_execution_report.md",
    "project_state/rounds/round_20260617_training_dataset_cipher_static_evidence_profile_v1/decision_packet.md",
    "project_state/rounds/round_20260617_training_dataset_cipher_static_evidence_profile_v1/pytest_result.txt",
    "project_state/rounds/round_20260617_training_dataset_cipher_static_evidence_profile_v1/round_manifest.json"
  ]
}
```

## Goal

Create a cipher static evidence profile that defines the exact evidence fields future IDA/Ghidra static extraction must collect for DES and RC4 PE cipher samples. This profile unblocks the 6 cipher/cipher PE samples (0% coverage) by establishing a concrete evidence contract.

## Changes

### New Artifacts

1. **`project_state/local_reverse_cipher_static_evidence_profile.json`** — Structured evidence contract with:
   - Target sample IDs by cipher family (4 DES PE + 2 RC4 PE)
   - Reference material sample IDs (1 DES Python + 2 RC4 Python)
   - 10 required evidence fields: algorithm_marker, string, constant_table, import_api, input_source, key_source, iv_mode_padding, ciphertext_source, comparison_output_sink, candidate_input_domain
   - Validation preconditions and blocker conditions
   - StructuredEvidence mapping plan (4 steps)
   - Future static triage sequence (5 steps)
   - First bounded triage targets: desenc_0e0b5203 (DES) and rc4enc_3480917d (RC4)

2. **`project_state/local_reverse_cipher_static_evidence_profile.md`** — Human-readable version with tables

## Evidence

1. No source/test files modified
2. No samples executed
3. No IDA/Ghidra/debugger/harness/solver invoked
4. Existing tool capabilities (static_feature_extractor, tool_capability_inventory, local_reverse_inventory) not duplicated
5. Evidence contract covers all required fields for DES and RC4
6. First bounded triage targets specified
