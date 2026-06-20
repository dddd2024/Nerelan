```json decision_meta
{
  "schema_version": 1,
  "decision_id": "decision_20260620_required_audit_answer_validation_v1",
  "round_id": "round_20260620_required_audit_answer_validation_v1",
  "based_on_state_build_id": "state_20260618_134029_d6bd033d2532",
  "based_on_state_digest": "d6bd033d25324345cfd8ada0ac65db42bc86eb5017f3ffc92906fcd8b71cacb5",
  "status": "APPROVED",
  "mainline": "engineering_branch",
  "skill_profiles": ["reverse-agent-iteration@v2"]
}
```

```json decision_contract
{
  "required_generated_artifacts": [
    "project_state/pytest_result.txt",
    "project_state/codex_execution_report.md",
    "project_state/gates/command_plan.json",
    "project_state/gates/report_summary_synthesis.json",
    "project_state/gates/final_gate_result.json",
    "project_state/rounds/round_20260620_required_audit_answer_validation_v1/round_manifest.json"
  ],
  "required_files_changed": [
    "reverse_agent/project_gate.py",
    "tests/test_project_gate.py"
  ],
  "forbidden_mutated_paths": [
    "project_state/current_state.json",
    "project_state/task_packet.json",
    "project_state/artifact_index.json",
    "project_state/model_gate.json",
    "project_state/negative_results.json"
  ],
  "required_command_fragments": [
    "python -m reverse_agent.project_gate run-closeout --state-dir project_state --round-id round_20260620_required_audit_answer_validation_v1"
  ],
  "close_round_required": true,
  "accepted_requires_final_check_passed": true
}
```

# DECISION_PACKET

## 1. Goal

Fix Required Audit validation so a `SUCCESS / ACCEPTED` report cannot pass with placeholder Required Audit answers such as `(to be filled)`, `PENDING`, empty `Answer:`, or equivalent unresolved markers.

The previous round implemented Required Audit extraction and coverage checking, but final-check accepted a report where all Required Audit answers were only scaffolds. This round must convert that into a hard validation rule.

## 2. Current Evidence

The previous round `decision_20260620_required_audit_report_generation_v1` produced a `SUCCESS / ACCEPTED` report and final-check passed.

However, the report's `## Required Audit` section contained all 8 required questions but each answer was still a placeholder:

- `Evidence: (to be filled)`
- `Status: PENDING`
- `Answer: (to be filled)`

The current `required_audit_coverage` gate only checks item coverage, not answer validity. It passed despite unresolved placeholders.

This is an engineering branch task. Do not continue reverse solving.

## 3. Do Not Do

Do not run live `python -m reverse_agent.project_state build`.

Do not promote `project_state/proposed_state/*` to live root state.

Do not continue affine solving.

Do not resume samplereverse candidate search.

Do not run binaries, runtime probes, debuggers, emulators, hooks, IDA, Ghidra, x64dbg, OllyDbg, or dynamic validation.

Do not modify `.codex-skills/`.

Do not make report generation depend on an LLM call.

Do not simply replace `(to be filled)` with generic fake text.

Do not claim `SUCCESS` unless Required Audit answers are substantive or explicitly supported by evidence.

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

Implementation and tests:

1. `reverse_agent/project_gate.py`
2. `reverse_agent/project_state.py`
3. `tests/test_project_gate.py`
4. `tests/test_project_state.py`

Gate artifacts:

1. `project_state/gates/command_plan.json`
2. `project_state/gates/gate_profile_plan.json`
3. `project_state/gates/report_summary_synthesis.json`
4. `project_state/gates/final_gate_result.json`
5. `project_state/gates/round_delta_summary.json`
6. `project_state/gates/round_close_snapshot.json`

Regression context:

1. `project_state/rounds/round_20260620_required_audit_report_generation_v1/codex_execution_report.md`
2. `project_state/rounds/round_20260620_required_audit_report_generation_v1/pytest_result.txt`
3. `project_state/rounds/round_20260620_required_audit_report_generation_v1/round_manifest.json`

## 5. Required Audit

Before editing code, answer in `codex_execution_report.md`:

1. Why did `required_audit_coverage` pass when all answers were placeholders?
2. Which placeholder patterns should be invalid for `SUCCESS / ACCEPTED` reports?
3. Should `PENDING` be allowed only for `BLOCKED`, `PARTIAL`, or `REWORK_REQUIRED` reports?
4. What counts as a substantive Required Audit answer?
5. How can the check avoid requiring long prose while still rejecting scaffolds?
6. Should the generated scaffold default to `PENDING` and force Codex or report-summary to fill evidence before success?
7. Which regression test should encode the previous all-placeholder Required Audit report?
8. How will backward compatibility be preserved for decisions without Required Audit items?

## 6. Implementation Scope

Implement a narrow Required Audit answer-validity layer.

Required feature A: placeholder detection.

Detect unresolved Required Audit answer markers, including at least:

- `(to be filled)`
- `TODO`
- `TBD`
- empty `Answer:`
- empty `Evidence:`
- `Status: PENDING`
- equivalent unresolved markers already used by generated scaffolds.

Required feature B: status-sensitive validation.

Rules:

1. For `SUCCESS / ACCEPTED` reports, every Required Audit item must have a non-placeholder answer or evidence-backed explicit answer.
2. For `BLOCKED`, `PARTIAL`, `FAILED`, or `REWORK_REQUIRED` reports, placeholder or PENDING items may be allowed only if the report status explains why the audit item remains unresolved.
3. If Required Audit extraction finds items but answers are missing or placeholder-only, final-check must fail for `SUCCESS / ACCEPTED`.

Required feature C: report generation behavior.

The scaffold generator may still create `PENDING` placeholders, but `run-closeout` / report-summary must not promote the report to `SUCCESS` while those placeholders remain.

Required feature D: regression tests.

Add tests for at least:

1. SUCCESS report with all Required Audit items present but placeholder answers fails.
2. SUCCESS report with `Status: PENDING` fails.
3. PARTIAL or BLOCKED report with explicit unresolved markers can pass or warn according to chosen policy.
4. SUCCESS report with concise non-placeholder answers passes.
5. Old decisions without Required Audit remain backward-compatible.
6. Previous `round_20260620_required_audit_report_generation_v1` report shape is represented as a regression fixture and fails.

Allowed source/test files:

- `reverse_agent/project_gate.py`
- `reverse_agent/project_state.py`
- `tests/test_project_gate.py`
- `tests/test_project_state.py`

Allowed project_state outputs:

- `project_state/codex_execution_report.md`
- `project_state/pytest_result.txt`
- `project_state/gates/*.json`
- `project_state/rounds/round_20260620_required_audit_answer_validation_v1/*`

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
python -m reverse_agent.project_gate run-closeout --state-dir project_state --round-id round_20260620_required_audit_answer_validation_v1
python -m reverse_agent.project_gate final-check --state-dir project_state
```

The final `codex_execution_report.md` must include a `## Required Audit` section with non-placeholder answers. The final `final_gate_result.json` must be `PASSED`.

## 8. Stop Conditions

Stop and report `REWORK_REQUIRED` or `BLOCKED` if:

1. Required Audit answer validation is not implemented;
2. SUCCESS reports with `(to be filled)` still pass;
3. SUCCESS reports with `Status: PENDING` still pass;
4. generated scaffolds can be promoted to SUCCESS without substantive answers;
5. old decisions without Required Audit break;
6. pytest fails;
7. run-closeout cannot archive the round;
8. close-round fails;
9. after-close final-check fails;
10. final-check has any FAIL;
11. report-summary synthesis differs from `codex_report_summary`;
12. final gate contains stale IDs from another round;
13. live root state files are promoted or mutated;
14. source changes exceed allowed files;
15. any reverse-solving progress is claimed.
