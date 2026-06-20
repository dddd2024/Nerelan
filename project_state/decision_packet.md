```json decision_meta
{
  "schema_version": 1,
  "decision_id": "decision_20260620_training_capability_gap_matrix_v1",
  "round_id": "round_20260620_training_capability_gap_matrix_v1",
  "based_on_state_build_id": "state_20260618_134029_d6bd033d2532",
  "based_on_state_digest": "d6bd033d25324345cfd8ada0ac65db42bc86eb5017f3ffc92906fcd8b71cacb5",
  "status": "APPROVED",
  "mainline": "training_dataset",
  "skill_profiles": ["reverse-agent-iteration@v2"]
}
```

```json decision_contract
{
  "required_generated_artifacts": [
    "project_state/local_reverse_training_capability_gap_matrix.json",
    "project_state/local_reverse_training_capability_gap_matrix_report.md",
    "project_state/local_reverse_next_static_triage_plan.json",
    "project_state/local_reverse_next_static_triage_plan_report.md",
    "project_state/pytest_result.txt",
    "project_state/codex_execution_report.md",
    "project_state/gates/command_plan.json",
    "project_state/gates/report_summary_synthesis.json",
    "project_state/gates/final_gate_result.json",
    "project_state/rounds/round_20260620_training_capability_gap_matrix_v1/round_manifest.json"
  ],
  "required_files_changed": [
    "project_state/local_reverse_training_capability_gap_matrix.json",
    "project_state/local_reverse_training_capability_gap_matrix_report.md",
    "project_state/local_reverse_next_static_triage_plan.json",
    "project_state/local_reverse_next_static_triage_plan_report.md"
  ],
  "forbidden_mutated_paths": [
    "project_state/current_state.json",
    "project_state/task_packet.json",
    "project_state/artifact_index.json",
    "project_state/model_gate.json",
    "project_state/negative_results.json",
    ".codex-skills/registry.json"
  ],
  "required_command_fragments": [
    "python -m reverse_agent.project_gate run-closeout --state-dir project_state --round-id round_20260620_training_capability_gap_matrix_v1"
  ],
  "close_round_required": true,
  "accepted_requires_final_check_passed": true
}
```

# DECISION_PACKET

## 1. Goal

Switch from the completed engineering closeout hardening line back to the training-dataset objective: build a current, evidence-aware capability gap matrix for the local reverse training set, and produce the next bounded static-triage plan.

This round must not solve any sample. Its purpose is to convert the existing metadata-level queue into a concrete planning artifact that answers, for each supported type, what evidence is missing, which existing tool route should be used next, whether solver work is currently allowed, and which one-to-three samples should be triaged first in a later explicitly authorized round.

## 2. Current Evidence

The recent engineering hardening plan is complete: `run-closeout`, `decision_contract`, Required Audit answer validation, report-summary consistency, and command-plan run-closeout recommendation have passed final-check in the previous round.

The current project state still shows the reverse-solving sample state is not complete: `task_packet.json` remains advisory and points to `project_state/decision_packet.md` as execution authority, while listing missing `case_results`, `frontier_summary`, `runtime_validation`, `strata_summary`, and `summary` evidence. `current_state.json` remains tied to `samplereverse` with `review_status: PENDING_REVIEW`; this round must not treat that as solved or current training-set completion.

The training-dataset artifacts already contain a first metadata-level static triage queue:

- `project_state/local_reverse_first_static_triage_queue.json`
- `project_state/local_reverse_first_static_triage_queue_report.md`

That queue contains one representative item for `string_comparison`, `xor`, `shift_affine`, `lookup_table`, `rc4`, `des`, `hash_md5_sha`, `simple_antidebug`, and `mixed_unknown`. It explicitly states these are metadata-only queue seeds and not static-verified or solved samples.

The same queue records blocked categories:

- `tea_xtea`: blocked because no current sample exists;
- `base64`: blocked because no current sample exists;
- `gui_validation`: blocked because no current sample exists.

The queue also records tool-route hints such as `reverse_agent.local_reverse_single_sample_static_triage`, solver profiles, IDA evidence collection, and evidence classes. These must be inspected before inventing new interfaces.

## 3. Do Not Do

Do not continue the `samplereverse` solving branch.

Do not run samples, binaries, harnesses, runtime probes, debuggers, emulators, hooks, GUI workflows, IDA, Ghidra, x64dbg, OllyDbg, or dynamic validation in this round.

Do not run live `python -m reverse_agent.project_state build`.

Do not promote `project_state/proposed_state/*` to live root state.

Do not scan the full `solve_reports/` directory.

Do not mark any sample as solved, static_verified, runtime_validated, or solver_ready from filename, sample id, category, inventory metadata, coverage row membership, or solver script name alone.

Do not implement new solver logic or duplicate existing IDA/Ghidra/tool-runner/solver/harness interfaces.

Do not modify `.codex-skills/`.

Do not modify reverse-agent source unless a narrow blocker is discovered and reported; this round should be artifact/report generation over existing state, not source development.

Do not claim SUCCESS unless the matrix, next plan, Required Audit, pytest record, run-closeout, close-round, and final-check all pass.

## 4. Files To Inspect

Default context:

1. `project_state/task_packet.json`
2. `project_state/current_state.json`
3. `project_state/artifact_index.json`
4. `project_state/negative_results.json`
5. `project_state/codex_execution_report.md`
6. `project_state/decision_packet.md`
7. `project_state/pytest_result.txt`
8. `.codex-skills/registry.json`

Training-dataset inputs:

1. `project_state/local_reverse_inventory.json`
2. `project_state/local_reverse_training_status.json`
3. `project_state/local_reverse_training_coverage_matrix.json`
4. `project_state/local_reverse_training_gap_report.md`
5. `project_state/local_reverse_solver_tool_capability_map.json`
6. `project_state/local_reverse_evaluation_queue.json`
7. `project_state/local_reverse_static_type_tag_contract.json`
8. `project_state/local_reverse_static_type_tag_contract_report.md`
9. `project_state/local_reverse_first_static_triage_queue.json`
10. `project_state/local_reverse_first_static_triage_queue_report.md`

Existing capability/interface files to inspect only as needed:

1. `reverse_agent/local_reverse_single_sample_static_triage.py`
2. `reverse_agent/tool_runners/`
3. `reverse_agent/evidence.py`
4. `reverse_agent/local_reverse_solver_profiles.py`
5. `reverse_agent/local_reverse_affine_inverse_handoff.py`
6. `reverse_agent/local_reverse_string_solver.py`
7. `reverse_agent/local_reverse_constraint_recovery.py`
8. `tests/test_project_state.py`
9. `tests/test_project_gate.py`

Output artifacts for this round:

1. `project_state/local_reverse_training_capability_gap_matrix.json`
2. `project_state/local_reverse_training_capability_gap_matrix_report.md`
3. `project_state/local_reverse_next_static_triage_plan.json`
4. `project_state/local_reverse_next_static_triage_plan_report.md`

## 5. Required Audit

Before editing artifacts, answer in `codex_execution_report.md`:

1. Which previous engineering closeout artifacts prove that the gate/closeout hardening line is complete enough to leave it?
2. Which training-dataset artifacts are current inputs for this round, and which are only historical or advisory?
3. Which local reverse categories already have queue representatives, and which are blocked because no current sample exists?
4. Which queued items are metadata-only and must not be promoted without static evidence?
5. Which existing tool or solver interfaces are already present and must be reused rather than recreated?
6. What criteria will the capability gap matrix use to label a type as `ready_for_static_triage`, `blocked_missing_sample`, `blocked_missing_evidence_fields`, `blocked_bounded_domain`, or `metadata_only`?
7. How will the next static-triage plan stay bounded and avoid batch-blind execution?
8. How will this round prove it did not run samples, tools, debuggers, dynamic validation, or solvers?

## 6. Implementation Scope

Implement a metadata-only training-dataset planning step. Do not solve samples.

Required feature A: capability gap matrix artifact.

Create `project_state/local_reverse_training_capability_gap_matrix.json` with one row per relevant local reverse type. Each row must include at least:

- `type_id`;
- `representative_sample_id` or `null`;
- `coverage_status_before`;
- `current_evidence_status` using a controlled value such as `metadata_only`, `blocked_missing_sample`, `blocked_missing_evidence_fields`, `blocked_bounded_domain`, or `ready_for_static_triage`;
- `required_static_evidence`;
- `existing_routes_to_reuse`;
- `solver_readiness` with reason;
- `blocked_reason` if blocked;
- `promotion_rule`;
- `next_authorized_action`;
- provenance fields referencing the queue, inventory, coverage matrix, or status artifacts used.

At minimum cover:

- `string_comparison`
- `xor`
- `shift_affine`
- `lookup_table`
- `rc4`
- `des`
- `hash_md5_sha`
- `simple_antidebug`
- `mixed_unknown`
- `tea_xtea`
- `base64`
- `gui_validation`

Required feature B: human-readable gap report.

Create `project_state/local_reverse_training_capability_gap_matrix_report.md` summarizing:

- which types are ready for a later static triage round;
- which types are blocked and why;
- which items are metadata-only and must not be promoted;
- which existing routes should be reused;
- which categories are highest priority for the next evidence-producing round.

Required feature C: next static-triage plan.

Create `project_state/local_reverse_next_static_triage_plan.json` selecting at most three queue items for the next evidence-producing round. Selection must be justified by current metadata and must not include blocked-no-sample categories.

The plan must specify for each selected item:

- `queue_id`;
- `type_id`;
- `sample_id`;
- `why_selected`;
- `required_static_evidence`;
- `existing_route_to_attempt_first`;
- `expected_output_artifacts`;
- `forbidden_actions`;
- `stop_condition`.

Recommended starting priorities unless evidence says otherwise:

1. one string comparison or shift/affine sample, because these can validate the simple static-triage path;
2. one cipher sample such as RC4 or DES, because it exercises cipher evidence fields;
3. one blocked/special case such as hash bounded-domain or lookup-table field support, but only as a planning row, not as solver work.

Required feature D: next plan report.

Create `project_state/local_reverse_next_static_triage_plan_report.md` explaining the selected bounded batch and what the next `tool_integration` or `training_dataset` decision should authorize.

Required feature E: provenance and non-promotion safeguards.

Every artifact must explicitly state that this round did not execute samples, solvers, IDA, Ghidra, runtime probes, debuggers, or harnesses. The artifacts must not mark any sample as solved, static_verified, or runtime_validated.

Allowed changed files:

- `project_state/local_reverse_training_capability_gap_matrix.json`
- `project_state/local_reverse_training_capability_gap_matrix_report.md`
- `project_state/local_reverse_next_static_triage_plan.json`
- `project_state/local_reverse_next_static_triage_plan_report.md`
- `project_state/codex_execution_report.md`
- `project_state/pytest_result.txt`
- `project_state/gates/*.json`
- `project_state/rounds/round_20260620_training_capability_gap_matrix_v1/*`

If Codex determines source changes are necessary, it must stop and report a blocker instead of modifying source files.

## 7. Tests

Run and record:

```powershell
Set-Location F:\reverse-agent
Get-Location
Test-Path F:\reverse-agent
git rev-parse --show-toplevel
git status --short

python -m reverse_agent.project_gate decision-lint --state-dir project_state
python -m reverse_agent.project_gate preflight --state-dir project_state
python -m pytest tests/test_project_gate.py tests/test_project_state.py -q
python -m reverse_agent.project_gate command-plan --state-dir project_state --json
python -m reverse_agent.project_gate run-closeout --state-dir project_state --round-id round_20260620_training_capability_gap_matrix_v1
python -m reverse_agent.project_gate final-check --state-dir project_state
```

The final `codex_execution_report.md` must include substantive Required Audit answers. The final `command_plan.json` must recommend the canonical `run-closeout` command for this round. The final `final_gate_result.json` must be `PASSED`.

## 8. Stop Conditions

Stop and report `REWORK_REQUIRED` or `BLOCKED` if:

1. the capability gap matrix is not generated;
2. the next static-triage plan is not generated;
3. any artifact claims solved/static_verified/runtime_validated without current static evidence;
4. any sample, solver, IDA/Ghidra, debugger, harness, runtime probe, or GUI workflow is executed;
5. full `solve_reports/` is scanned;
6. blocked-no-sample categories are selected for static triage execution;
7. existing tool/solver interfaces are ignored and duplicate interfaces are created;
8. source files are modified instead of reporting a blocker;
9. live root state files listed in forbidden paths are mutated;
10. Required Audit answers are missing or placeholder-only;
11. pytest fails;
12. run-closeout cannot archive the round;
13. after-close final-check fails;
14. final-check has any FAIL;
15. report-summary synthesis differs from `codex_report_summary`;
16. final gate contains stale IDs from another round;
17. any reverse-solving progress is claimed.
