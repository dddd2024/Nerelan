```json decision_meta
{
  "schema_version": 1,
  "decision_id": "decision_20260620_required_audit_report_generation_v1",
  "round_id": "round_20260620_required_audit_report_generation_v1",
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
    "project_state/rounds/round_20260620_required_audit_report_generation_v1/round_manifest.json"
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
    "python -m reverse_agent.project_gate run-closeout --state-dir project_state --round-id round_20260620_required_audit_report_generation_v1"
  ],
  "close_round_required": true,
  "accepted_requires_final_check_passed": true
}
```

# DECISION_PACKET

## 1. Goal

Close the remaining limitation from the accepted-with-limitations `run-closeout` re-entry round by making `codex_execution_report.md` include a machine-generated, human-readable Required Audit summary.

The previous round successfully fixed the `run-closeout` re-entry and closeout evidence loop. However, the live `codex_execution_report.md` was too thin: it contained the structured `codex_report_summary` and `## Status SUCCESS`, but did not answer the decision's Required Audit questions in prose. This round must make that class of omission mechanically harder to repeat.

The target outcome is: report-summary or run-closeout should generate or validate a `## Required Audit` section that covers the decision's Required Audit questions, while preserving the existing structured summary and final gate checks.

## 2. Current Evidence

The previous round `decision_20260620_run_closeout_reentry_unblock_v1` is accepted with limitations.

Evidence from that round:

- `pytest_result.txt` recorded startup checks, `run-closeout`, nested decision-lint, preflight, pytest, gate-profile, command-plan, command-plan `--json`, report-summary, final-check, close-round, and after-close final-check.
- pytest passed with `901 passed`.
- final gate was `PASSED` and archived report/pytest matched live report/pytest.
- report-summary synthesis matched `codex_report_summary`.
- command-plan JSON stdout and exit code checks passed.

Remaining limitation:

- `codex_execution_report.md` did not include a substantive `## Required Audit` section answering the decision's Required Audit questions.
- The gate accepted this because existing checks focus on structured fields and command evidence, not human-readable audit coverage.

This is an engineering branch task. It must not continue reverse solving.

## 3. Do Not Do

Do not run live `python -m reverse_agent.project_state build`.

Do not promote `project_state/proposed_state/*` to live root state.

Do not continue affine solving.

Do not resume samplereverse candidate search.

Do not run binaries, runtime probes, debuggers, emulators, hooks, IDA, Ghidra, x64dbg, OllyDbg, or dynamic validation.

Do not modify `.codex-skills/`.

Do not replace `run-closeout` with a workflow engine.

Do not make report generation depend on an LLM call.

Do not generate fake Required Audit answers. If evidence is absent, the generated section must say so and the gate should fail or warn according to the chosen policy.

Do not claim `SUCCESS` unless pytest, run-closeout, report-summary, final-check, close-round, after-close final-check, and the new Required Audit coverage check pass.

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

Previous limitation context:

1. `project_state/rounds/round_20260620_run_closeout_reentry_unblock_v1/codex_execution_report.md`
2. `project_state/rounds/round_20260620_run_closeout_reentry_unblock_v1/pytest_result.txt`
3. `project_state/rounds/round_20260620_run_closeout_reentry_unblock_v1/round_manifest.json`

## 5. Required Audit

Before changing code, Codex must answer in the report:

1. How is the decision's Required Audit section currently parsed, if at all?
2. Which Required Audit questions from the decision can be answered mechanically from project_state artifacts?
3. Which questions require Codex-authored explanation, and how should missing answers be handled?
4. Should final-check fail when `## Required Audit` is missing for an engineering decision that declares Required Audit items?
5. Should the check require exact question text, numbered answers, or only coverage markers?
6. How can this remain backward-compatible for old decisions without a Required Audit section?
7. How should report-summary/run-closeout avoid overwriting useful human-written report text?
8. Which regression test should represent the previous accepted-with-limitations report that had structured SUCCESS but no Required Audit body?

## 6. Implementation Scope

Implement a small, backward-compatible Required Audit report coverage layer.

Required feature A: parse Required Audit questions from decision packets.

- Extract the `## 5. Required Audit` section from `project_state/decision_packet.md`.
- Recognize numbered questions or bullet items.
- If no Required Audit section exists, preserve current behavior.

Required feature B: report coverage validation.

Add report-summary/final-check validation so that when Required Audit items exist:

1. `codex_execution_report.md` must include a `## Required Audit` section;
2. the section must contain an answer or explicit evidence status for each Required Audit item;
3. missing answers must be reported as a gate failure, or as a clearly justified warning only when the report status is not `SUCCESS`;
4. `SUCCESS / ACCEPTED` reports must not omit Required Audit coverage.

Required feature C: report generation helper.

Add a helper that can generate a deterministic Required Audit scaffold from the current decision. It may include placeholder answer markers such as `Evidence:` / `Status:` / `Answer:` but must not fabricate facts. The helper may be invoked by `run-closeout` or documented as a CLI/report-summary function.

Required feature D: preserve existing workflow.

Do not break old reports without Required Audit sections when the active decision has no Required Audit items. Do not change reverse-solving logic or sample state.

Required feature E: tests.

Add tests for at least:

1. Required Audit extraction from numbered questions;
2. old decisions without Required Audit remain backward-compatible;
3. SUCCESS report without `## Required Audit` fails when decision has Required Audit items;
4. BLOCKED/PARTIAL report may include explicit unanswered evidence markers without claiming success;
5. generated scaffold includes every Required Audit item;
6. previous thin SUCCESS report shape is represented as a regression fixture and fails the new coverage check;
7. run-closeout/report-summary path produces or preserves Required Audit coverage.

Allowed source/test files:

- `reverse_agent/project_gate.py`
- `reverse_agent/project_state.py`
- `tests/test_project_gate.py`
- `tests/test_project_state.py`

Allowed project_state outputs:

- `project_state/codex_execution_report.md`
- `project_state/pytest_result.txt`
- `project_state/gates/*.json`
- `project_state/rounds/round_20260620_required_audit_report_generation_v1/*`

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
python -m reverse_agent.project_gate run-closeout --state-dir project_state --round-id round_20260620_required_audit_report_generation_v1
python -m reverse_agent.project_gate final-check --state-dir project_state
```

The final `codex_execution_report.md` must include a substantive `## Required Audit` section. The final `pytest_result.txt` must include `run-closeout` and nested command evidence. The final `final_gate_result.json` must be `PASSED`.

## 8. Stop Conditions

Stop and report `REWORK_REQUIRED` or `BLOCKED` if:

1. Required Audit extraction is not implemented;
2. SUCCESS reports can still omit `## Required Audit` when the decision declares Required Audit items;
3. generated Required Audit scaffolds omit any decision audit item;
4. the implementation fabricates audit answers instead of marking missing evidence;
5. old decisions without Required Audit break;
6. run-closeout overwrites useful report prose unexpectedly;
7. pytest fails;
8. run-closeout cannot archive the round;
9. close-round fails;
10. after-close final-check fails;
11. final-check has any FAIL;
12. report-summary synthesis differs from `codex_report_summary`;
13. final gate contains stale IDs from another round;
14. live root state files are promoted or mutated;
15. source changes exceed allowed files;
16. any reverse-solving progress is claimed.
