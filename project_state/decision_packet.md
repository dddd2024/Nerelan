```json decision_meta
{
  "schema_version": 1,
  "decision_id": "decision_20260619_prompt_contract_closeout_hardening_v1",
  "round_id": "round_20260619_prompt_contract_closeout_hardening_v1",
  "based_on_state_build_id": "state_20260618_134029_d6bd033d2532",
  "based_on_state_digest": "d6bd033d25324345cfd8ada0ac65db42bc86eb5017f3ffc92906fcd8b71cacb5",
  "status": "APPROVED",
  "mainline": "engineering_branch",
  "skill_profiles": ["reverse-agent-iteration@v2"]
}
```

# DECISION_PACKET

## 1. Goal

Completely harden the current round closeout/report/artifact workflow by converting prompt-only execution constraints into machine-checkable contract and gate invariants.

This round must not continue single-field report patching. The immediate observed defect is that `decision_20260619_staged_artifact_generated_artifacts_fix_v1` still allowed report prose to claim staged/apply-plan artifacts were in `files_changed`, while `codex_report_summary.files_changed` omitted them. The final gate incorrectly passed `report_body_consistency`.

The goal is to fix the underlying class of failure:

1. decision requirements must become machine-readable where possible;
2. report summary fields must be validated against decision contract, round delta, and report prose claims;
3. `SUCCESS / ACCEPTED` must not rely on Codex prose;
4. final-check must fail when required generated artifacts are misplaced, omitted, or contradicted by report prose.

## 2. Current Evidence

Current authoritative decision remains `project_state/decision_packet.md`; `task_packet.json` is advisory and still points to old `samplereverse` state.

The latest report for `decision_20260619_staged_artifact_generated_artifacts_fix_v1` claims `SUCCESS / ACCEPTED`.

The latest report correctly includes staged/apply-plan artifacts in `generated_artifacts`.

However, the same artifacts are absent from `files_changed`, despite the decision requiring them to be kept there.

The report body claims those artifacts are listed in `files_changed`, contradicting its own structured JSON summary.

Final-check passed `report_body_consistency`, so the gate currently fails to catch this class of mismatch.

## 3. Do Not Do

Do not continue affine solving.

Do not resume samplereverse candidate search.

Do not run binaries, runtime probes, debuggers, emulators, hooks, IDA, Ghidra, x64dbg, OllyDbg, or dynamic validation.

Do not run live `python -m reverse_agent.project_state build`.

Do not promote `project_state/proposed_state/*` to live root state.

Do not modify `.codex-skills/`.

Do not patch only `codex_execution_report.md` to add missing paths. This round must address the gate/report contract mechanism.

Do not introduce database, message queue, Kubernetes, web server, or heavy workflow engine.

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

Gate/report implementation:

1. `reverse_agent/project_gate.py`
2. `reverse_agent/project_state.py`
3. `tests/test_project_gate.py`
4. `tests/test_project_state.py`

Gate artifacts:

1. `project_state/gates/final_gate_result.json`
2. `project_state/gates/report_summary_synthesis.json`
3. `project_state/gates/round_delta_summary.json`
4. `project_state/gates/command_plan.json`
5. `project_state/gates/gate_profile_plan.json`

Current regression artifacts:

1. `project_state/state_rebuild_apply_plan.json`
2. `project_state/proposed_state/artifact_index.json`
3. `project_state/proposed_state/current_state.json`
4. `project_state/proposed_state/negative_results.json`
5. `project_state/proposed_state/model_gate.json`
6. `project_state/proposed_state/task_packet.json`

## 5. Required Audit

Before changing code, Codex must answer:

1. Which parts of the current closeout process are still prompt-only?
2. Why did final-check pass when report prose contradicted `codex_report_summary.files_changed`?
3. Does `report_body_consistency` currently parse enough artifact/file claim patterns?
4. Does `report_summary_fields_match_synthesis` validate `files_changed`, `generated_artifacts`, `referenced_artifacts`, and `required_closeout_artifacts` against a contract, or only against synthesized report fields?
5. Can current decision requirements be represented as a machine-readable `decision_contract` block without breaking existing decision packets?
6. What minimal backward-compatible schema should be accepted?
7. Should missing `decision_contract` default to current behavior?
8. Which tests should preserve existing accepted rounds while failing the new regression case?

## 6. Implementation Scope

Implement a small, backward-compatible hardening layer.

### Required feature A: decision_contract parsing

Support an optional fenced block in `decision_packet.md`:

```json decision_contract
{
  "required_generated_artifacts": [],
  "required_files_changed": [],
  "forbidden_mutated_paths": [],
  "required_command_fragments": [],
  "close_round_required": true,
  "accepted_requires_final_check_passed": true
}
```

Rules:

1. If absent, existing decisions must still work.
2. If present, final-check must enforce it.
3. Invalid contract JSON must fail decision-lint.
4. Unknown fields should warn or fail consistently; choose one behavior and test it.

### Required feature B: artifact placement checks

Add final-check invariants:

1. Every `required_generated_artifacts` path must appear in `codex_report_summary.generated_artifacts`.
2. Every `required_files_changed` path must appear in `codex_report_summary.files_changed`.
3. If a required generated artifact appears only in `referenced_artifacts`, final-check must FAIL.
4. If report prose claims a path is in `files_changed` or `generated_artifacts`, but JSON summary omits it, final-check must FAIL.
5. If a path is intentionally only referenced, the report must not claim it was generated or changed.

### Required feature C: status hardening

Add final-check invariants:

1. `SUCCESS / ACCEPTED` requires current final gate IDs to match current decision/report/round.
2. `ACCEPTED` requires close-round archive when `close_round_required=true`.
3. pytest-only success reports must fail if command-plan requires gate commands.
4. `acceptance_recommendation` must be derived from gate status or report-summary synthesis, not only prose.

### Required feature D: regression tests

Add tests for at least:

1. required generated artifact missing from `generated_artifacts` fails;
2. required changed file missing from `files_changed` fails;
3. artifact in `referenced_artifacts` only, while required generated, fails;
4. report body claims artifact in `files_changed` but JSON omits it, fails;
5. pytest-only SUCCESS report fails when contract requires final-check/close-round;
6. existing decision without `decision_contract` remains backward-compatible;
7. latest observed staged/apply-plan regression is represented as a fixture/test.

Allowed source/test files:

- `reverse_agent/project_gate.py`
- `reverse_agent/project_state.py`
- `tests/test_project_gate.py`
- `tests/test_project_state.py`

Allowed project_state outputs:

- `project_state/codex_execution_report.md`
- `project_state/pytest_result.txt`
- `project_state/gates/*.json`
- `project_state/rounds/round_20260619_prompt_contract_closeout_hardening_v1/*`

## 7. Tests

Run and record all commands in `project_state/pytest_result.txt`:

```powershell
Set-Location F:\reverse-agent
Get-Location
Test-Path F:\reverse-agent
git rev-parse --show-toplevel
git status --short

python -m reverse_agent.project_gate decision-lint --state-dir project_state
python -m reverse_agent.project_gate preflight --state-dir project_state
python -m pytest tests/test_project_state.py tests/test_project_gate.py -q
python -m reverse_agent.project_gate gate-profile --state-dir project_state
python -m reverse_agent.project_gate command-plan --state-dir project_state
python -m reverse_agent.project_gate report-summary --state-dir project_state
python -m reverse_agent.project_gate final-check --state-dir project_state
```

If final-check passes:

```powershell
python -m reverse_agent.project_gate close-round --state-dir project_state --round-id round_20260619_prompt_contract_closeout_hardening_v1
python -m reverse_agent.project_gate final-check --state-dir project_state
```

## 8. Stop Conditions

Stop and report `REWORK_REQUIRED` if:

1. backward compatibility breaks for decisions without `decision_contract`;
2. decision-lint fails on valid existing decision packets;
3. final-check still passes the staged artifact prose/summary contradiction regression;
4. required generated artifacts can still be satisfied only by `referenced_artifacts`;
5. required changed files can still be omitted from `files_changed`;
6. pytest fails;
7. final-check has any FAIL;
8. close-round fails;
9. report/decision/pytest/final-gate IDs mismatch;
10. live root state files are promoted or mutated;
11. source changes exceed the allowed gate/project-state files;
12. any reverse-solving progress is claimed.
