```json decision_meta
{
  "schema_version": 1,
  "decision_id": "decision_20260617_artifact_deliverable_reporting_rework_v1",
  "round_id": "round_20260617_artifact_deliverable_reporting_rework_v1",
  "based_on_state_build_id": "state_20260615_150220_24f61a9ac337",
  "based_on_state_digest": "24f61a9ac337b596ff7d56b3e29f01e5ab68342825fb2a32ba50b65a84512bae",
  "status": "APPROVED",
  "mainline": "engineering_branch",
  "skill_profiles": ["reverse-agent-iteration@v2"]
}
```

# DECISION_PACKET

## 1. Goal

Repair the audit/reporting chain for artifact-only rounds so core deliverables cannot be hidden as inherited baseline dirty files and omitted from `codex_report_summary.files_changed` / `generated_artifacts`.

This is a narrow engineering rework after the audit of `decision_20260617_training_dataset_cipher_static_evidence_profile_v1`. Do not redo the cipher static evidence profile content. The existing `project_state/local_reverse_cipher_static_evidence_profile.json` and `.md` are content deliverables to preserve, not regenerate.

Required end state:

- artifact-only deliverables required by `decision_packet.md` must appear in the synthesized and final `codex_report_summary.files_changed` and `generated_artifacts` when they are present in the final dirty set;
- `report-summary` / `final-check` must not silently treat required deliverables as harmless inherited dirty files when they are the core output of the round;
- add regression coverage for required deliverables that are created before baseline capture;
- keep source/test changes small and limited to project gate/report metadata logic;
- do not modify solver, harness, IDA/Ghidra/debugger, runtime probe, sample runner, GUI/frontend, or `.codex-skills/` code.

## 2. Current Evidence

Current execution authority is this `project_state/decision_packet.md`. `task_packet.json` remains non-authoritative state input and still may describe old `samplereverse` sample-state work.

The immediately preceding round:

- `decision_20260617_training_dataset_cipher_static_evidence_profile_v1`
- `round_20260617_training_dataset_cipher_static_evidence_profile_v1`
- `report_id=codex_report_20260617_training_dataset_cipher_static_evidence_profile_v1`
- `mainline=training_dataset`
- audit conclusion from GPT: `REWORK_REQUIRED` for audit metadata, not for profile content.

Observed audit defect:

- `project_state/pytest_result.txt` startup `git status --short` showed `A  project_state/local_reverse_cipher_static_evidence_profile.json` and `A  project_state/local_reverse_cipher_static_evidence_profile.md` before gate execution.
- `project_state/codex_execution_report.md` did not include those two profile deliverables in `codex_report_summary.files_changed` or `generated_artifacts`.
- `project_state/gates/report_summary_synthesis.json` also omitted those two deliverables from synthesized `files_changed` and `generated_artifacts`.
- `project_state/gates/final_gate_result.json` classified the two profile files as `inherited_dirty_files`, while `files_changed_covers_git_diff` still passed.
- This means a core required deliverable can be present in final dirty files but absent from the report summary because it existed before baseline capture.

Content status of previous profile:

- `project_state/local_reverse_cipher_static_evidence_profile.json` appears structurally complete and includes `decision_id`, `round_id`, DES/RC4 sample coverage, evidence contract, StructuredEvidence mapping plan, future static triage sequence, first bounded triage targets, non-goals, and stop conditions.
- `project_state/local_reverse_cipher_static_evidence_profile.md` is the companion human-readable artifact.
- Do not rewrite or reinterpret the DES/RC4 evidence profile unless a schema/check requires a minimal metadata-only change.

Artifact freshness:

- Historical `samplereverse` missing artifacts remain non-current evidence and must not drive this engineering rework.
- This round is about live project-state report/gate metadata consistency only.

Negative results:

- Do not return to old sample_solver blind search.
- Do not only increase guided-pool beam or budget.
- Do not use `compare_semantics_agree=false` candidates as primary frontier.
- Do not commit full `solve_reports/`.
- Do not repeat prior `samplereverse` failed candidate/runtime branches.

Existing relevant capabilities:

- `reverse_agent/project_gate.py` owns preflight, command-plan, report-summary, final-check, close-round, round baseline/delta, and files_changed/generated_artifacts checks.
- `reverse_agent/project_state.py` owns report parsing, lint-report, doctor, pytest result validation, artifact freshness, and status summary.
- Existing IDA / IDAPython, OllyDbg/debugger, solver, harness, sample metadata, and artifact-index capabilities must remain untouched.
- Mature reverse tools are not relevant to this rework except as prohibited scope.

Allowed tool execution:

- Read repository source/tests and `project_state/` metadata.
- Run the gate/status/test commands listed below.
- Do not run local reverse samples, IDA, Ghidra, debugger, emulator, runtime probes, harness campaigns, or solvers.

## 3. Do Not Do

Do not redo `project_state/local_reverse_cipher_static_evidence_profile.json` or `.md` content.

Do not solve DES/RC4 samples.

Do not run sample binaries.

Do not run IDA/Ghidra/debugger/emulator/runtime probe/harness/solver commands.

Do not modify solver logic, harness behavior, tool runners, IDA scripts, debugger scripts, GUI/frontend, raw samples, or `.codex-skills/`.

Do not read full `solve_reports/` or full `PROJECT_PROGRESS_LOG.txt`.

Do not weaken report/gate checks globally.

Do not allow arbitrary inherited dirty files to be reported as generated artifacts. The fix must be limited to deliverables required by the active decision scope and present in final dirty files.

Do not change sample training statuses.

Do not treat `task_packet.task` as current execution authority.

## 4. Files To Inspect

Read default project-state files in order:

1. `project_state/task_packet.json`
2. `project_state/current_state.json`
3. `project_state/artifact_index.json`
4. `project_state/negative_results.json`
5. `project_state/codex_execution_report.md`
6. `project_state/decision_packet.md`
7. `project_state/pytest_result.txt`
8. `.codex-skills/registry.json`

Also inspect:

- `project_state/gates/round_baseline.json`
- `project_state/gates/round_delta_summary.json`
- `project_state/gates/report_summary_synthesis.json`
- `project_state/gates/final_gate_result.json`
- `project_state/local_reverse_cipher_static_evidence_profile.json`
- `project_state/local_reverse_cipher_static_evidence_profile.md`
- `project_state/rounds/round_20260617_training_dataset_cipher_static_evidence_profile_v1/round_manifest.json`
- `reverse_agent/project_gate.py`
- `reverse_agent/project_state.py`
- `tests/test_project_gate.py`
- `tests/test_project_state.py`

Do not inspect unrelated solver/harness/tool-runner modules unless a failing test directly requires it.

## 5. Required Audit

Before implementation, confirm:

1. Startup path is `F:\reverse-agent`, `Test-Path F:\reverse-agent` is true, and `git rev-parse --show-toplevel` points to this repository.
2. Startup `git status --short` is recorded as baseline.
3. `decision_meta` is valid, `status=APPROVED`, `mainline=engineering_branch`, and `reverse-agent-iteration@v2` is active.
4. The previous cipher profile files exist and were omitted from report summary despite being required deliverables.
5. The defect is in audit/report metadata, not in DES/RC4 profile content.
6. Existing gate/report-summary code paths are reused; do not implement a second gate system.
7. No reverse sample execution is needed to complete the rework.

## 6. Implementation Scope

Allowed source files:

- `reverse_agent/project_gate.py`
- `reverse_agent/project_state.py` only if report parsing/lint-report support is strictly required

Allowed tests:

- `tests/test_project_gate.py`
- `tests/test_project_state.py` only if project_state support is changed

Allowed generated/project-state files:

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
- `project_state/rounds/round_20260617_artifact_deliverable_reporting_rework_v1/*`

Required implementation behavior:

- Detect deliverables explicitly required by the active decision's Implementation Scope / Allowed generated artifacts.
- If a required deliverable is present in the final dirty files, include it in synthesized `files_changed` even when it was present in `baseline_dirty_files` / `inherited_dirty_files`.
- Include those required deliverables in synthesized `generated_artifacts` when they are project-state artifacts produced for the current round.
- Keep inherited source/test dirty handling unchanged.
- Keep the guard against arbitrary inherited dirty files unchanged.
- Make the rule path-normalized and compatible with Windows and POSIX separators.
- Preserve old fields and backward compatibility.

Required test scenarios:

1. A required artifact-only deliverable listed in decision scope and present before baseline capture must appear in synthesized `files_changed` and `generated_artifacts`.
2. A non-required inherited dirty file must not be promoted to `generated_artifacts`.
3. Source/test inherited dirty files must not be silently promoted unless already allowed by existing source/test rules.
4. The previous cipher-profile pattern (`project_state/local_reverse_cipher_static_evidence_profile.json` and `.md`) should be represented by a regression fixture.
5. Existing report-summary/final-check tests must continue to pass.

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
python -m pytest tests/test_project_gate.py tests/test_project_state.py -q
python -m reverse_agent.project_state doctor --state-dir project_state
python -m reverse_agent.project_state lint-report --state-dir project_state
python -m reverse_agent.project_gate report-summary --state-dir project_state
python -m reverse_agent.project_gate final-check --state-dir project_state
python -m reverse_agent.project_gate close-round --state-dir project_state --round-id round_20260617_artifact_deliverable_reporting_rework_v1
```

The pytest result header must include:

- `decision_id=decision_20260617_artifact_deliverable_reporting_rework_v1`
- `round_id=round_20260617_artifact_deliverable_reporting_rework_v1`
- the final `report_id`
- all commands actually run

## 8. Stop Conditions

Stop and report `BLOCKED` without expanding scope if:

- current `decision_packet.md` is no longer this decision;
- `.codex-skills/registry.json` does not contain active `reverse-agent-iteration@v2`;
- the fix requires redesigning the gate system instead of a small report-summary/final-check adjustment;
- the fix requires running IDA/Ghidra/debugger/harness/solver/sample binaries;
- tests fail for reasons outside the narrow artifact deliverable reporting scope;
- implementing the fix would modify solver/harness/tool-runner/sample code;
- `report-summary` or `final-check` fails for a real blocking reason unrelated to this metadata rework.
