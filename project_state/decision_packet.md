```json decision_meta
{
  "schema_version": 1,
  "decision_id": "decision_20260617_training_dataset_cipher_static_evidence_profile_v1",
  "round_id": "round_20260617_training_dataset_cipher_static_evidence_profile_v1",
  "based_on_state_build_id": "state_20260615_150220_24f61a9ac337",
  "based_on_state_digest": "24f61a9ac337b596ff7d56b3e29f01e5ab68342825fb2a32ba50b65a84512bae",
  "status": "APPROVED",
  "mainline": "training_dataset",
  "skill_profiles": ["reverse-agent-iteration@v2"]
}
```

# DECISION_PACKET

## 1. Goal

Build the next training-dataset step for local reverse samples by producing a bounded `cipher_static_evidence_profile` plan for PE cipher samples, especially DES and RC4.

This round must unblock the current type-level training gap without solving a single sample. The immediate purpose is to turn the `pending_cipher_static_evidence_profile` blocker into an explicit, reusable evidence contract that future static-triage rounds can apply to DES/RC4 PE samples.

Required end state:

- create a reviewable cipher static evidence profile artifact under `project_state/`;
- cover both DES and RC4 PE sample families listed in the local reverse training matrix;
- define exact evidence fields future IDA/Ghidra/static extraction should collect;
- define how the profile maps tool output into training metadata and later `StructuredEvidence`;
- select the first bounded DES and RC4 samples for later triage, but do not triage them in this round;
- do not run local reverse samples, debuggers, harness campaigns, runtime probes, or solver searches;
- do not modify solver logic, static tool runners, IDA/Ghidra/debugger adapters, or harness behavior.

## 2. Current Evidence

Current execution authority is this `project_state/decision_packet.md`. `task_packet.json` still reflects an old `samplereverse` sample-state task (`collect_missing_evidence`) and is non-authoritative for this round.

Current state digest and build id are retained from the available state package:

- `state_build_id`: `state_20260615_150220_24f61a9ac337`
- `state_digest`: `24f61a9ac337b596ff7d56b3e29f01e5ab68342825fb2a32ba50b65a84512bae`

The previous gate-policy repair round was accepted with limitations and archived:

- `decision_20260616_training_dataset_historical_artifact_policy_v1`
- `round_20260616_training_dataset_historical_artifact_policy_v1`
- `report_status=SUCCESS`
- `acceptance_recommendation=ACCEPTED`
- `final_gate_result.json` now treats historical sample artifact freshness as a non-blocking external-state notice for non-sample-solving closeout.

Training-dataset evidence to use:

- `project_state/local_reverse_training_resume_plan.json` reports 50 local samples: 1 solved, 2 blocked, 1 needs triage, 46 inventory-only.
- The resume plan lists `crypto/cipher` as a type coverage gap and states that `pending_cipher_static_evidence_profile` blocks cipher sample triage.
- The recommended resume sequence includes building a cipher static evidence profile for DES and RC4 samples.
- `project_state/local_reverse_type_coverage_matrix.json` reports 6 PE `crypto/cipher` samples, 0 solved, 0 blocked, 0 needs triage, 6 inventory-only.
- The cipher PE inventory-only sample ids are `desenc_0e0b5203`, `desenc_14c58fcd`, `desenc_40cba418`, `desenc_fd9d0af6`, `rc4enc_3480917d`, and `rc4enc_f93c785f`.
- The matrix also lists Python reference/support materials: `des_interactive_solver_256e1726`, `rc4_add1978d`, and `rc4_interactive_solver_773052ac`; these may be used as reference metadata only, not as target binaries.

Artifact freshness:

- `artifact_index.json` still has many old `samplereverse` artifacts marked missing/stale; these are historical sample artifacts and must not be treated as current evidence for this training-dataset planning round.
- Do not use stale/missing `samplereverse` artifacts as evidence.
- The current training artifacts are the local reverse resume plan and type coverage matrix from `project_state/`; verify they exist before relying on them.

Negative results:

- Do not return to old `sample_solver` blind search.
- Do not only increase guided-pool beam or budget.
- Do not use `compare_semantics_agree=false` candidates as a primary frontier.
- Do not commit full `solve_reports/`.
- Do not repeat previously failed `samplereverse` candidate-pool/runtime-validation branches.

Existing relevant capabilities that must be checked and reused instead of duplicated:

- IDA / IDAPython: existing runner, scripts, evidence parsing, and static triage consumers exist; do not create a duplicate IDA interface.
- Ghidra: currently no implemented headless runner/evidence adapter is recorded; mention as optional future evidence source only, do not implement it here.
- OllyDbg / debugger: existing runtime/debugger evidence path exists; do not run or modify it in this round.
- strings/static feature extraction: existing pure-Python static string extraction exists; reuse as a future evidence source, do not duplicate it.
- solver templates and symbolic/constraint solvers exist; this round must not run or modify solvers.
- harness and artifact freshness tracking exist; this round must not run harness campaigns.
- sample metadata and local reverse training inventory exist; use them as the source for sample ids and categories.

Allowed tool execution:

- Read repository source, tests, `project_state/` JSON/markdown, and `training_materials/local_reverse/` metadata.
- Run gate/status/test commands listed in the Tests section.
- Do not execute local reverse sample binaries.
- Do not run IDA/Ghidra/debugger/emulator/runtime probe/harness/solver commands in this round.

Heavy artifact policy:

- Do not read full `solve_reports/`.
- Do not read full `PROJECT_PROGRESS_LOG.txt`.
- Do not commit generated full runtime reports.

## 3. Do Not Do

Do not solve DES or RC4 samples in this round.

Do not run sample binaries.

Do not run runtime probes, OllyDbg, x64dbg, emulator, harness campaigns, or candidate validation.

Do not run IDA/Ghidra analysis in this round. This round only defines the evidence profile that later static-triage rounds will use.

Do not modify `reverse_agent/tool_runners.py`, IDA scripts, debugger scripts, solver modules, harness modules, GUI/frontend, or `.codex-skills/`.

Do not modify raw sample files.

Do not modify or commit full `solve_reports/`.

Do not mark any cipher sample as solved, blocked, or triaged merely because this profile exists.

Do not overwrite existing training status artifacts unless the change is a clearly named additive planning artifact.

Do not treat `task_packet.task` as the current execution authority.

## 4. Files To Inspect

Read the default project-state files in order:

1. `project_state/task_packet.json`
2. `project_state/current_state.json`
3. `project_state/artifact_index.json`
4. `project_state/negative_results.json`
5. `project_state/codex_execution_report.md`
6. `project_state/decision_packet.md`
7. `project_state/pytest_result.txt`
8. `.codex-skills/registry.json`

Also inspect:

- `project_state/local_reverse_training_resume_plan.json`
- `project_state/local_reverse_type_coverage_matrix.json`
- `project_state/local_reverse_training_status.json`, if present
- `project_state/local_reverse_training_review_queue.json`, if present
- `project_state/local_reverse_training_next_queue.json`, if present
- `training_materials/local_reverse/queue.json`, if present
- `training_materials/local_reverse/github_safe_status_overlay.json`, if present
- `reverse_agent/tool_capability_inventory.py`
- `reverse_agent/local_reverse_training_status.py`
- `reverse_agent/local_samples.py`
- `reverse_agent/local_reverse_inventory.py`
- `reverse_agent/static_feature_extractor.py`
- existing DES/RC4 solver or reference modules, read-only only
- tests related to local reverse training status and project gates

Do not read full `solve_reports/` or full `PROJECT_PROGRESS_LOG.txt`.

## 5. Required Audit

Before implementation, confirm:

1. Startup path is `F:\reverse-agent`, `Test-Path F:\reverse-agent` is true, and `git rev-parse --show-toplevel` points to this repository.
2. Startup `git status --short` is recorded as baseline.
3. `decision_meta` is valid, `status=APPROVED`, `mainline=training_dataset`, and `reverse-agent-iteration@v2` is active.
4. `task_packet.json` is non-authoritative and still reflects old sample-state information.
5. `project_state/local_reverse_training_resume_plan.json` exists and lists `pending_cipher_static_evidence_profile` as a cipher gap.
6. `project_state/local_reverse_type_coverage_matrix.json` exists and lists the 6 PE cipher samples.
7. Existing IDA, debugger, solver, harness, sample metadata, and artifact-index capabilities are identified so this round does not duplicate them.
8. Historical `samplereverse` missing/stale artifacts are not used as current evidence.
9. No local sample execution is required to complete this round.

## 6. Implementation Scope

Allowed generated artifacts:

- `project_state/local_reverse_cipher_static_evidence_profile.json`
- `project_state/local_reverse_cipher_static_evidence_profile.md`
- `project_state/codex_execution_report.md`
- `project_state/pytest_result.txt`
- `project_state/gates/preflight_result.json`
- `project_state/gates/command_plan.json`
- `project_state/gates/run_round_result.json`
- `project_state/gates/report_summary_synthesis.json`
- `project_state/gates/final_gate_result.json`
- `project_state/gates/round_baseline.json`
- `project_state/gates/round_delta_summary.json`
- `project_state/gates/round_close_snapshot.json`
- `project_state/rounds/round_20260617_training_dataset_cipher_static_evidence_profile_v1/*`

Allowed source/test changes:

- Prefer no source/test changes.
- If and only if an existing test requires a small schema accommodation for the new additive profile artifact, modify only narrowly related tests and explain why.
- Do not modify production code unless a gate/test failure proves that existing code cannot record the additive artifact; in that case stop and report `BLOCKED` instead of expanding scope.

The JSON profile must include at least:

- `schema_version`
- `decision_id`
- `round_id`
- `generated_at`
- `source_artifacts`
- `scope`: PE cipher samples only
- `cipher_families`: at least `DES` and `RC4`
- `target_sample_ids_by_family`
- `reference_material_sample_ids_by_family`
- `evidence_contract` with required future evidence fields:
  - algorithm marker evidence
  - string evidence
  - constant/table evidence
  - import/API evidence
  - input source evidence
  - key/source evidence
  - IV/mode/padding evidence when applicable
  - ciphertext/source evidence
  - comparison/output sink evidence
  - candidate input domain evidence
  - validation preconditions
  - confidence and blocker fields
- `structured_evidence_mapping_plan`
- `future_static_triage_sequence`
- `first_bounded_triage_targets`: one DES sample and one RC4 sample
- `non_goals`
- `stop_conditions`

The markdown profile must be a concise human-readable companion explaining:

- why this profile is needed;
- how DES and RC4 should be distinguished statically;
- what evidence future IDA/static-triage runs must extract;
- why no sample is solved in this round;
- which future round should run first after this artifact is accepted.

Recommended first bounded triage targets for later rounds:

- DES: `desenc_0e0b5203`
- RC4: `rc4enc_3480917d`

Do not update `local_reverse_training_status.json` to claim progress unless the new artifact is explicitly designed as a planning artifact and does not alter sample statuses.

## 7. Tests

Run and record the following commands in `project_state/pytest_result.txt`:

```powershell
Set-Location F:\reverse-agent
Get-Location
Test-Path F:\reverse-agent
git rev-parse --show-toplevel
git status --short
python -m reverse_agent.project_gate preflight --state-dir project_state
python -m reverse_agent.project_gate command-plan --state-dir project_state
python -m reverse_agent.project_gate command-plan --state-dir project_state --json
python -m reverse_agent.project_gate run-round --state-dir project_state --dry-run --json
python -m reverse_agent.project_state doctor --state-dir project_state
python -m reverse_agent.project_state lint-report --state-dir project_state
python -m pytest tests/test_local_reverse_training_status.py tests/test_project_state.py tests/test_project_gate.py -q
python -m reverse_agent.project_gate report-summary --state-dir project_state
python -m reverse_agent.project_gate final-check --state-dir project_state
python -m reverse_agent.project_gate close-round --state-dir project_state --round-id round_20260617_training_dataset_cipher_static_evidence_profile_v1
```

The pytest result header must include:

- `decision_id=decision_20260617_training_dataset_cipher_static_evidence_profile_v1`
- `round_id=round_20260617_training_dataset_cipher_static_evidence_profile_v1`
- the final `report_id`
- all commands actually run

## 8. Stop Conditions

Stop and report `BLOCKED` without modifying additional files if:

- required training artifacts are missing and cannot be read;
- `.codex-skills/registry.json` does not contain active `reverse-agent-iteration@v2`;
- current `decision_packet.md` is no longer this decision;
- Codex would need to run IDA/Ghidra/debugger/harness/solver/sample binaries to complete the profile;
- resolving the task would require changing production tool runners, solver logic, harness behavior, or raw samples;
- existing artifacts show a newer accepted decision superseding this one;
- `report-summary` or `final-check` fails for reasons other than known historical sample artifact external-state notices;
- tests fail and the cause is outside this narrow additive planning-artifact scope.
