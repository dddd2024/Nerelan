```json decision_meta
{
  "schema_version": 1,
  "decision_id": "decision_20260619_affine_reverse_solving_ciphertext_handoff_v1",
  "round_id": "round_20260619_affine_reverse_solving_ciphertext_handoff_v1",
  "based_on_state_build_id": "state_20260618_134029_d6bd033d2532",
  "based_on_state_digest": "d6bd033d25324345cfd8ada0ac65db42bc86eb5017f3ffc92906fcd8b71cacb5",
  "status": "APPROVED",
  "mainline": "reverse_solving",
  "skill_profiles": ["reverse-agent-iteration@v2"]
}
```

# DECISION_PACKET

## 1. Goal

Advance `affine_8cfebe03` from static transform-material readiness into a bounded reverse-solving handoff.

This round must not rebuild the affine solver from scratch. The previous accepted tool-integration round recovered the affine transform material with static IDA provenance. The next step is to locate an auditable expected ciphertext, feed it through the existing affine inverse handoff path, and produce either a candidate with provenance or a precise blocker artifact if no trusted ciphertext is available.

Success criteria:

1. Confirm the round is running under this `decision_packet.md`, not the advisory `task_packet.json`.
2. Confirm existing affine static evidence and transform-material artifacts are readable and current.
3. Search only bounded, relevant metadata/problem-statement/static-evidence locations for expected ciphertext.
4. Use the existing `reverse_agent/local_reverse_affine_inverse_handoff.py` path rather than creating a duplicate affine solver.
5. Produce a current solve handoff/result artifact or a current blocker artifact.
6. Do not execute the target binary and do not claim a final answer unless candidate derivation has trusted ciphertext provenance.

## 2. Current Evidence

Current `task_packet.json` is advisory only. It still points at the older `samplereverse` state package and must not override this decision.

Known state limitation: `current_state.json` and `task_packet.json` are not fully aligned with the current affine round. Treat them as compact historical state references only. For this round, the controlling evidence is this decision packet plus current affine artifacts in `artifact_index.json` and the accepted previous report.

Previous audit status: `ACCEPTED_WITH_LIMITATIONS` for `decision_20260619_affine_static_material_artifact_enrichment_v1`. Limitations were non-blocking for the affine current round: final-check had WARN, mainly build-output-scope provenance and historical/backlog artifact warnings.

Current affine transform evidence:

1. `project_state/local_reverse_affine_8cfebe03_transform_material_static_extract.json`
   - `freshness=current`
   - `sample_id=affine_8cfebe03`
   - `source_run=round_20260619_affine_static_material_artifact_enrichment_v1`
   - static-only; no sample execution.
2. `project_state/local_reverse_affine_8cfebe03_transform_material_evidence.json`
   - contains `StaticConstantEvidence` from IDA.
   - affine constants: `a=5`, `b=5`, `modulus=26`, `a_inverse=21`.
3. `project_state/local_reverse_affine_8cfebe03_transform_material_dispatch_plan.json`
   - `readiness=transform_material_resolved`
   - `recommended_solver_profiles=["affine_inverse_solver"]`
   - `required_missing_evidence=[]`
   - `has_compare_site=false`.
4. `project_state/local_reverse_affine_8cfebe03_transform_material_provenance_report.json`
   - static-only provenance.
   - `runtime_validated=false`.
   - source targeted decompile available.
5. `project_state/local_reverse_affine_main0_targeted_ida_decompile.json`
   - targeted IDA static artifact with `_main_0` pseudocode.
   - confirms input range `a-z`, transform loop, and no compare/success branch.

Existing affine solving capability already exists and must be reused:

1. `reverse_agent/local_reverse_affine_inverse_handoff.py`
   - computes modular inverse and per-character mapping.
   - refuses to generate a candidate unless `expected_ciphertext` exists with trusted provenance.
   - trusted sources are `challenge_statement`, `allowed_static_evidence`, and `user_provided`.
2. `tests/test_local_reverse_affine_inverse_handoff.py`
   - covers inverse computation, provenance gate, unsupported domain, non-invertible multiplier, and static-only flags.
3. `project_state/local_reverse_affine_inverse_handoff.json`
   - existing older handoff is `BLOCKED` because `expected_ciphertext` is missing.
   - it is a useful prior artifact but not sufficient as current solve evidence.

Negative-results policy remains active:

- Do not return to old blind search.
- Do not only increase beam/budget.
- Do not use compare-semantics-disagreed candidates.
- Do not commit full `solve_reports/`.
- Do not repeat unrelated `samplereverse` failed directions.

Tool capability policy:

- IDA has already provided static evidence for this sample; do not rerun IDA unless the required source artifact is missing or unreadable.
- Existing affine inverse handoff must be used before any implementation change.
- Mature/static tool evidence is sufficient for candidate derivation only after expected ciphertext provenance is established.
- Static candidate derivation is not runtime validation.

Allowed heavy artifact access:

- Do not read complete `solve_reports/` or `PROJECT_PROGRESS_LOG.txt`.
- You may read only explicitly referenced affine static evidence paths already named by current artifacts.
- You may inspect bounded local sample metadata/problem-statement files if they are directly tied to `affine_8cfebe03` or `逆向课程2024春补考03/affine.exe`.

## 3. Do Not Do

Do not implement a new affine solver when `reverse_agent/local_reverse_affine_inverse_handoff.py` already exists.

Do not run the target binary.

Do not perform dynamic debugging, emulator execution, runtime probe, hook, or validation unless a later decision explicitly permits it.

Do not scan complete `solve_reports/` or `PROJECT_PROGRESS_LOG.txt`.

Do not change `.codex-skills/`.

Do not modify unrelated source modules.

Do not broaden to other samples or training-set batch evaluation.

Do not treat the old `project_state/local_reverse_affine_inverse_handoff.json` as current candidate evidence.

Do not invent expected ciphertext. If expected ciphertext is not found with trusted provenance, produce a blocker artifact.

Do not claim a final flag/password/answer unless the handoff result has `status=READY`, a non-null `candidate`, and trusted ciphertext provenance.

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

Current affine artifacts:

1. `project_state/local_reverse_affine_8cfebe03_transform_material_static_extract.json`
2. `project_state/local_reverse_affine_8cfebe03_transform_material_evidence.json`
3. `project_state/local_reverse_affine_8cfebe03_transform_material_dispatch_plan.json`
4. `project_state/local_reverse_affine_8cfebe03_transform_material_provenance_report.json`
5. `project_state/local_reverse_affine_main0_targeted_ida_decompile.json`
6. `project_state/local_reverse_affine_inverse_handoff.json`

Existing implementation and tests:

1. `reverse_agent/local_reverse_affine_inverse_handoff.py`
2. `tests/test_local_reverse_affine_inverse_handoff.py`
3. `reverse_agent/solver_dispatch_plan.py`
4. `reverse_agent/static_evidence_bridge.py`
5. `reverse_agent/evidence.py`
6. `reverse_agent/tool_capability_inventory.py`

Bounded possible ciphertext sources:

1. Local sample metadata files that directly reference `affine_8cfebe03`, `affine.exe`, or `逆向课程2024春补考03`.
2. Challenge statement / README / notes files in the local sample directory, if present.
3. Existing current static evidence artifacts that explicitly contain an expected output or ciphertext field.
4. A user-provided ciphertext artifact only if it is explicitly written with provenance `user_provided`.

## 5. Required Audit

Before implementation, confirm:

1. repository root is `F:\reverse-agent`;
2. startup `git status --short` is recorded;
3. decision status is `APPROVED`;
4. mainline is `reverse_solving`;
5. skill profile is active;
6. this round is not controlled by `task_packet.json`;
7. current affine transform artifacts are readable;
8. existing affine inverse handoff interface and tests were inspected before any implementation change;
9. `negative_results.json` was checked and no forbidden search direction is repeated.

Implementation audit must answer:

1. Where was expected ciphertext searched for?
2. Was expected ciphertext found?
3. If found, what trusted provenance category was used: `challenge_statement`, `allowed_static_evidence`, or `user_provided`?
4. Was `reverse_agent/local_reverse_affine_inverse_handoff.py` used unchanged? If not, why was a code change necessary?
5. What candidate or blocker artifact was produced?
6. Is the output a final answer, a candidate requiring validation, or a blocker?
7. What evidence remains missing?
8. Whether the next safe mainline stays `reverse_solving` or should return to `tool_integration` / `training_dataset`.

## 6. Implementation Scope

Preferred implementation is artifact-only.

Allowed project_state outputs:

- `project_state/local_reverse_affine_8cfebe03_expected_ciphertext_evidence.json`
- `project_state/local_reverse_affine_8cfebe03_inverse_handoff_current.json`
- `project_state/local_reverse_affine_8cfebe03_solve_result.json`
- `project_state/local_reverse_affine_8cfebe03_solve_blocker.json`
- `project_state/local_reverse_affine_8cfebe03_solve_provenance_report.json`
- `project_state/local_reverse_affine_8cfebe03_solve_provenance_report.md`
- `project_state/artifact_index.json`
- `project_state/codex_execution_report.md`
- `project_state/pytest_result.txt`
- `project_state/gates/*.json`
- `project_state/rounds/round_20260619_affine_reverse_solving_ciphertext_handoff_v1/*`

Allowed source files only if a small reusable compatibility adapter is unavoidable:

- `reverse_agent/local_reverse_affine_inverse_handoff.py`
- `tests/test_local_reverse_affine_inverse_handoff.py`
- `reverse_agent/solver_dispatch_plan.py`

Expected execution shape:

1. Read current affine transform-material artifacts.
2. Perform a bounded search for expected ciphertext in directly related metadata/problem-statement/static-evidence files.
3. If expected ciphertext is found, create a small current input artifact that includes:
   - affine parameters or reference to current transform-material evidence;
   - `expected_ciphertext`;
   - one trusted provenance field accepted by the handoff gate.
4. Run or call the existing affine inverse handoff to produce `local_reverse_affine_8cfebe03_inverse_handoff_current.json`.
5. If handoff status is `READY`, write a solve result artifact with candidate, formula, provenance, and validation limitation.
6. If no trusted ciphertext is found, write a blocker artifact with exact searched locations and missing evidence.
7. Update `artifact_index.json` with current provenance/freshness for new solve handoff/result/blocker artifacts.
8. Write `codex_execution_report.md` with `codex_report_summary` for this decision.

Candidate policy:

- A candidate may be derived only by inverse affine over trusted ciphertext.
- Candidate derivation formula must be recorded: `p = 21 * (c - 5) mod 26`, lowercase `a-z` domain.
- If the candidate is not runtime-validated, label it as `static_candidate`, not `runtime_validated_solution`.

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
python -m pytest tests/test_local_reverse_affine_inverse_handoff.py tests/test_static_evidence_bridge.py tests/test_solver_dispatch_plan.py tests/test_project_gate.py tests/test_project_state.py -q
python -m reverse_agent.project_gate gate-profile --state-dir project_state
python -m reverse_agent.project_gate command-plan --state-dir project_state
python -m reverse_agent.project_gate report-summary --state-dir project_state
python -m reverse_agent.project_gate final-check --state-dir project_state
```

If no source file changes are made, the pytest set may still include the full listed set because the round crosses solver handoff, artifact index, and gate checks.

If final-check passes or only has non-blocking warnings:

```powershell
python -m reverse_agent.project_gate close-round --state-dir project_state --round-id round_20260619_affine_reverse_solving_ciphertext_handoff_v1
python -m reverse_agent.project_gate final-check --state-dir project_state
```

## 8. Stop Conditions

Stop and report `BLOCKED` or `REWORK_REQUIRED` if:

1. repository root cannot be confirmed;
2. decision metadata is invalid;
3. mainline is not `reverse_solving`;
4. skill profile is not active;
5. current affine transform-material artifacts are missing or unreadable;
6. existing affine inverse handoff is missing or ignored;
7. expected ciphertext cannot be found with trusted provenance;
8. expected ciphertext contains characters outside the supported lowercase `a-z` domain and no documented normalization rule exists;
9. implementation would require dynamic execution or target binary execution;
10. implementation would require reading complete heavy-history directories;
11. source changes would exceed the allowed files;
12. pytest fails;
13. final-check has any FAIL;
14. report/decision/pytest IDs mismatch;
15. report claims a final answer without trusted ciphertext provenance and a current handoff/result artifact.
