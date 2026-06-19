```json decision_meta
{
  "schema_version": 1,
  "decision_id": "decision_20260619_affine_static_material_artifact_enrichment_v1",
  "round_id": "round_20260619_affine_static_material_artifact_enrichment_v1",
  "based_on_state_build_id": "state_20260618_134029_d6bd033d2532",
  "based_on_state_digest": "d6bd033d25324345cfd8ada0ac65db42bc86eb5017f3ffc92906fcd8b71cacb5",
  "status": "APPROVED",
  "mainline": "tool_integration",
  "skill_profiles": ["reverse-agent-iteration@v2"]
}
```

# DECISION_PACKET

## 1. Goal

Enrich the current static material record for `affine_8cfebe03` as a tool-integration step.

The project gate/report closeout work is accepted. Return to the static artifact chain and close the remaining evidence gap identified by the current dispatch record: transform material is still missing. This round must stay static-only and produce either a current transform-material artifact or a precise blocker artifact.

Success criteria:

1. Current affine static records are read as referenced artifacts.
2. Existing extraction and bridge interfaces are inspected before any implementation change.
3. A bounded transform-material artifact is produced, or a blocker explains the exact missing current input.
4. The report states whether transform material is resolved, partially resolved, or still missing.
5. No final solve output is produced.

## 2. Current Evidence

Current `task_packet.json` is advisory only because `project_state/decision_packet.md` controls the current round.

Accepted input records:

1. `project_state/local_reverse_affine_8cfebe03_current_static_triage.json`
2. `project_state/local_reverse_affine_8cfebe03_current_static_bridge_result.json`
3. `project_state/local_reverse_affine_8cfebe03_current_solver_dispatch_plan.json`
4. `project_state/local_reverse_affine_8cfebe03_current_static_provenance_report.json`
5. `project_state/local_reverse_affine_8cfebe03_current_static_provenance_report.md`

The current dispatch record still lists `transform_constant_evidence` as missing. The current bridge record has input, compare, transform-hint, and anti-debug evidence, but no concrete transform material.

Required referenced records for closeout coverage:

```json closeout_artifacts_contract
{
  "required_closeout_artifacts": [
    "project_state/artifact_index.json",
    "project_state/local_reverse_affine_8cfebe03_current_static_triage.json",
    "project_state/local_reverse_affine_8cfebe03_current_static_bridge_result.json",
    "project_state/local_reverse_affine_8cfebe03_current_solver_dispatch_plan.json",
    "project_state/local_reverse_affine_8cfebe03_current_static_provenance_report.json",
    "project_state/local_reverse_affine_8cfebe03_current_static_provenance_report.md"
  ]
}
```

Existing interfaces to inspect and reuse:

1. `reverse_agent/local_reverse_targeted_static_reextract.py`
2. `reverse_agent/local_reverse_single_sample_static_triage.py`
3. `reverse_agent/static_evidence_bridge.py`
4. `reverse_agent/solver_dispatch_plan.py`
5. `reverse_agent/evidence.py`
6. `reverse_agent/tool_runners.py`
7. `reverse_agent/tool_capability_inventory.py`

`negative_results.json` remains valid. Avoid old blind-search directions, budget-only expansion, and full heavy-history submission.

## 3. Do Not Do

Do not enter a solving round.

Do not produce final solve output.

Do not use dynamic validation.

Do not modify unrelated source modules.

Do not read complete heavy-history directories.

Do not modify `.codex-skills/`.

Do not replace existing extraction, bridge, or dispatch interfaces with duplicates.

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

Affine static records:

1. `project_state/local_reverse_affine_8cfebe03_current_static_triage.json`
2. `project_state/local_reverse_affine_8cfebe03_current_static_bridge_result.json`
3. `project_state/local_reverse_affine_8cfebe03_current_solver_dispatch_plan.json`
4. `project_state/local_reverse_affine_8cfebe03_current_static_provenance_report.json`
5. `project_state/local_reverse_affine_8cfebe03_current_static_provenance_report.md`

Relevant implementation files:

1. `reverse_agent/local_reverse_targeted_static_reextract.py`
2. `reverse_agent/local_reverse_single_sample_static_triage.py`
3. `reverse_agent/static_evidence_bridge.py`
4. `reverse_agent/solver_dispatch_plan.py`
5. `reverse_agent/evidence.py`
6. `reverse_agent/tool_runners.py`
7. `reverse_agent/tool_capability_inventory.py`

## 5. Required Audit

Before implementation, confirm:

1. repository root is `F:\reverse-agent`;
2. startup `git status --short` is recorded;
3. decision status is `APPROVED`;
4. mainline is `tool_integration`;
5. skill profile is active;
6. current affine static records are readable;
7. existing interfaces were inspected before changing code.

Implementation audit must answer:

1. Which existing interface was used or why it was insufficient?
2. Which transform-material facts were recovered?
3. Which evidence remains missing?
4. Whether the next safe mainline is still `tool_integration` or can become `reverse_solving`.

## 6. Implementation Scope

Preferred implementation is artifact-only. Source changes are allowed only for a small reusable adapter if existing output cannot be represented cleanly.

Allowed source files if necessary:

- `reverse_agent/local_reverse_targeted_static_reextract.py`
- `reverse_agent/static_evidence_bridge.py`
- `reverse_agent/solver_dispatch_plan.py`
- `reverse_agent/evidence.py`

Allowed project_state outputs:

- `project_state/local_reverse_affine_8cfebe03_transform_material_static_extract.json`
- `project_state/local_reverse_affine_8cfebe03_transform_material_evidence.json`
- `project_state/local_reverse_affine_8cfebe03_transform_material_dispatch_plan.json`
- `project_state/local_reverse_affine_8cfebe03_transform_material_provenance_report.json`
- `project_state/local_reverse_affine_8cfebe03_transform_material_provenance_report.md`
- `project_state/artifact_index.json`
- `project_state/codex_execution_report.md`
- `project_state/pytest_result.txt`
- `project_state/gates/*.json`
- `project_state/rounds/round_20260619_affine_static_material_artifact_enrichment_v1/*`

## 7. Tests

Run and write results to `project_state/pytest_result.txt`:

```powershell
Set-Location F:\reverse-agent
Get-Location
Test-Path F:\reverse-agent
git rev-parse --show-toplevel
git status --short

python -m reverse_agent.project_gate decision-lint --state-dir project_state
python -m reverse_agent.project_gate preflight --state-dir project_state
python -m pytest tests/test_static_evidence_bridge.py tests/test_solver_dispatch_plan.py tests/test_project_gate.py tests/test_project_state.py -q
python -m reverse_agent.project_gate gate-profile --state-dir project_state
python -m reverse_agent.project_gate command-plan --state-dir project_state
python -m reverse_agent.project_gate report-summary --state-dir project_state
python -m reverse_agent.project_gate final-check --state-dir project_state
```

If source files are not changed, the pytest set may be reduced with a recorded reason.

If final-check passes or only has non-blocking warnings:

```powershell
python -m reverse_agent.project_gate close-round --state-dir project_state --round-id round_20260619_affine_static_material_artifact_enrichment_v1
python -m reverse_agent.project_gate final-check --state-dir project_state
```

## 8. Stop Conditions

Stop and report `BLOCKED` or `REWORK_REQUIRED` if:

1. repository root cannot be confirmed;
2. decision metadata is invalid;
3. mainline is not `tool_integration`;
4. required referenced records are missing;
5. existing interfaces were not inspected;
6. source changes would exceed the allowed files;
7. pytest fails;
8. final-check has any FAIL;
9. report/decision/pytest IDs mismatch;
10. the report claims transform material is resolved without concrete current evidence and provenance.
