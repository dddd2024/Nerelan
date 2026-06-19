```json decision_meta
{
  "schema_version": 1,
  "decision_id": "decision_20260619_run_closeout_automation_v1",
  "round_id": "round_20260619_run_closeout_automation_v1",
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
    "project_state/rounds/round_20260619_run_closeout_automation_v1/round_manifest.json"
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
    "python -m reverse_agent.project_gate run-closeout --state-dir project_state --round-id round_20260619_run_closeout_automation_v1"
  ],
  "close_round_required": true,
  "accepted_requires_final_check_passed": true
}
```

# DECISION_PACKET

## 1. Goal

Implement a minimal `run-closeout` automation path so the round closeout flow no longer depends on Codex manually following `command-plan` and manually assembling `pytest_result.txt` command evidence.

The previous hardening round added `decision_contract` parsing and gate invariants, and was accepted with limitations. The remaining limitation is that `command-plan` still says `record_and_follow_command_plan_manually`, so the critical closeout sequence is still mostly prompt-driven. This round must turn that manual closeout sequence into a controlled CLI workflow.

Target command:

```powershell
python -m reverse_agent.project_gate run-closeout --state-dir project_state --round-id round_20260619_run_closeout_automation_v1
```

The command should execute or orchestrate the closeout pipeline, capture command evidence, write/update gate artifacts, and close the round when policy permits. It must remain small, local, and deterministic. Do not introduce a workflow engine.

## 2. Current Evidence

Current `task_packet.json` still points to an old `samplereverse` advisory state, but it explicitly declares `project_state/decision_packet.md` as the active decision packet and `decision_packet_controls_current_round` as execution scope. Therefore this decision controls the current round.

The previous accepted-with-limitations round implemented:

- optional `decision_contract` parsing;
- decision-lint validation for invalid contract JSON and unknown fields;
- final-check artifact placement checks;
- final-check status hardening checks;
- report body consistency checks for prose/summary contradictions;
- regression tests for the prior staged artifact mismatch class.

Remaining limitation:

- `command-plan` still requires manual execution and recording;
- `pytest_result.txt` is still manually assembled from command blocks;
- `codex_report_summary.tests_ran` can still be narrower than the full command evidence;
- `SUCCESS / ACCEPTED` is closer to gate-derived than before, but execution evidence is still produced by a prompt-following agent rather than by a single deterministic closeout command.

This is an `engineering_branch` round. It must not continue reverse solving.

## 3. Do Not Do

Do not continue affine solving.

Do not resume `samplereverse` candidate search.

Do not run binaries, runtime probes, debuggers, emulators, hooks, IDA, Ghidra, x64dbg, OllyDbg, or dynamic validation.

Do not run live `python -m reverse_agent.project_state build`.

Do not promote `project_state/proposed_state/*` to live root state.

Do not modify `.codex-skills/`.

Do not introduce a database, message queue, Kubernetes, daemon, web server, scheduler, or heavy workflow engine.

Do not make `run-closeout` execute arbitrary shell commands from a decision file. It must use a bounded allowlist or structured command model.

Do not remove existing manual commands until the new command is covered by tests and remains backward-compatible.

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

Current contract/gate regression context:

1. `project_state/state_rebuild_apply_plan.json`
2. `project_state/proposed_state/artifact_index.json`
3. `project_state/proposed_state/current_state.json`
4. `project_state/proposed_state/negative_results.json`
5. `project_state/proposed_state/model_gate.json`
6. `project_state/proposed_state/task_packet.json`

## 5. Required Audit

Before implementing, Codex must answer in `codex_execution_report.md`:

1. Which current command-plan steps are safe to automate?
2. Which commands must remain manually controlled or explicitly blocked?
3. How should `run-closeout` represent startup checks without relying on PowerShell-only commands?
4. How should `run-closeout` record stdout, stderr, exit codes, and expected exit codes in `pytest_result.txt`?
5. How should `run-closeout` avoid recursive self-execution if command-plan itself mentions `run-closeout`?
6. How should the command handle archive-pending final-check warnings before close-round?
7. Should report-summary run before or after final-check, and how should status fields be refreshed after close-round?
8. How will tests monkeypatch subprocess execution so they do not run nested full pytest or mutate real project_state?
9. Does the current `decision_contract` correctly require the new `run-closeout` command to appear in the recorded command evidence?

## 6. Implementation Scope

Implement a minimal, backward-compatible local closeout executor.

Required feature A: new CLI subcommand

Add a `project_gate` CLI subcommand:

```powershell
python -m reverse_agent.project_gate run-closeout --state-dir project_state --round-id <round_id>
```

Required behavior:

1. Validate decision metadata and requested round_id.
2. Generate or refresh command-plan before execution.
3. Execute a bounded closeout sequence:
   - startup diagnostics using Python/cross-platform equivalents;
   - decision-lint;
   - preflight;
   - pytest command selected from command-plan or a safe default for changed gate/project_state files;
   - gate-profile;
   - command-plan;
   - report-summary;
   - final-check;
   - close-round if allowed;
   - final-check after close-round.
4. Capture each executed step into `project_state/pytest_result.txt` using the existing command-block style plus a `pytest_result_summary` JSON header.
5. Preserve command stdout/stderr and exit code evidence.
6. Treat expected nonzero exits only when command-plan explicitly allows them.
7. Refuse arbitrary shell commands not in an allowlist.
8. Never run target binaries, dynamic probes, debuggers, or external reverse tooling.
9. Exit nonzero if final-check or close-round fails.
10. Keep the existing manual path working.

Required feature B: command evidence consistency

`run-closeout` must ensure that:

1. `pytest_result.txt` contains startup evidence;
2. `pytest_result.txt` contains the `run-closeout` command itself or a clear self-invocation marker;
3. `codex_report_summary.tests_ran` is covered by `pytest_result.txt`;
4. command-plan checks can verify the automated evidence;
5. close-round is last or followed only by the final after-close `final-check`, according to the gate policy chosen and tested.

Required feature C: tests

Add tests for at least:

1. `run-closeout` executes expected steps in order with a monkeypatched command runner;
2. `run-closeout` writes `pytest_result.txt` summary and command blocks;
3. `run-closeout` refuses disallowed shell/runtime commands;
4. `run-closeout` handles expected exit `[0, 1]` for report-summary/final-check when archive is pending;
5. `run-closeout` closes the round only after pre-close final-check is acceptable;
6. after-close final-check is recorded;
7. command evidence includes the `run-closeout` invocation or explicit self-invocation marker;
8. existing manual command-plan/final-check behavior remains backward-compatible.

Allowed source/test files:

- `reverse_agent/project_gate.py`
- `reverse_agent/project_state.py`
- `tests/test_project_gate.py`
- `tests/test_project_state.py`

Allowed project_state outputs:

- `project_state/codex_execution_report.md`
- `project_state/pytest_result.txt`
- `project_state/gates/*.json`
- `project_state/rounds/round_20260619_run_closeout_automation_v1/*`

## 7. Tests

Before using the new command, run and record the bootstrap checks manually if needed:

```powershell
Set-Location F:\reverse-agent
Get-Location
Test-Path F:\reverse-agent
git rev-parse --show-toplevel
git status --short

python -m reverse_agent.project_gate decision-lint --state-dir project_state
python -m reverse_agent.project_gate preflight --state-dir project_state
python -m pytest tests/test_project_gate.py tests/test_project_state.py -q
```

After implementing `run-closeout`, the primary acceptance command is:

```powershell
python -m reverse_agent.project_gate run-closeout --state-dir project_state --round-id round_20260619_run_closeout_automation_v1
```

Then verify, if not already done by `run-closeout`:

```powershell
python -m reverse_agent.project_gate final-check --state-dir project_state
```

The final `project_state/pytest_result.txt` must include the `run-closeout` command or an explicit self-invocation marker. The final `codex_execution_report.md` must list `run-closeout` in `tests_ran`.

## 8. Stop Conditions

Stop and report `REWORK_REQUIRED` if:

1. `run-closeout` is not implemented;
2. `run-closeout` exists but does not write `pytest_result.txt` command evidence;
3. `run-closeout` can execute arbitrary shell commands from decision/report text;
4. `run-closeout` omits startup diagnostics;
5. `run-closeout` omits final-check or close-round when policy requires it;
6. `run-closeout` cannot archive the round;
7. after-close final-check is missing or fails;
8. `pytest_result.txt` does not include `run-closeout` or a self-invocation marker;
9. `codex_report_summary.tests_ran` omits `run-closeout`;
10. decision_contract checks fail;
11. pytest fails;
12. final-check has any FAIL;
13. report/decision/pytest/final-gate IDs mismatch;
14. live root state files are promoted or mutated;
15. source changes exceed allowed gate/project_state files;
16. any reverse-solving progress is claimed.
