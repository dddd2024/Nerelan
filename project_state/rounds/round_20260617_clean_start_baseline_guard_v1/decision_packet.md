```json decision_meta
{
  "schema_version": 1,
  "decision_id": "decision_20260617_clean_start_baseline_guard_v1",
  "round_id": "round_20260617_clean_start_baseline_guard_v1",
  "based_on_state_build_id": "state_20260615_150220_24f61a9ac337",
  "based_on_state_digest": "24f61a9ac337b596ff7d56b3e29f01e5ab68342825fb2a32ba50b65a84512bae",
  "status": "APPROVED",
  "mainline": "engineering_branch",
  "skill_profiles": ["reverse-agent-iteration@v2"]
}
```

# DECISION_PACKET

## 1. Goal

Harden the round startup/baseline lifecycle so Codex cannot modify source/test files before recording the startup baseline and then have those modifications treated as harmless inherited dirty files.

This is a narrow engineering guardrail task. The purpose is to make repeated `ACCEPTED_WITH_LIMITATIONS` outcomes caused by pre-baseline source/test modifications become an early `BLOCKED` condition, not a warning that can be explained away after implementation.

Required end state:

- source/test files dirty at startup must be treated as blocking for source/test implementation rounds unless they are explicitly declared in a dedicated pre-existing inherited baseline allowlist before the round starts;
- project_state generated files dirty at startup may remain non-blocking when they are normal gate/report/round artifacts;
- command-plan/final-check/close-round behavior must remain backward-compatible except for stricter source/test clean-start enforcement;
- add tests proving that source/test startup dirty causes a hard block, while generated project_state artifacts do not;
- do not change solver, harness, IDA/Ghidra/debugger/tool-runner, sample runner, GUI/frontend, raw samples, or `.codex-skills/` behavior.

## 2. Current Evidence

Current execution authority is this `project_state/decision_packet.md`. `task_packet.json` and `current_state.json` are state inputs only and must not override this decision.

Previous accepted-with-limitations round:

- `decision_20260617_tiered_gate_profile_plan_v1`
- `round_20260617_tiered_gate_profile_plan_v1`
- mainline: `engineering_branch`
- result: gate profile classifier accepted with limitations
- limitation: startup `git status --short` already showed `reverse_agent/project_gate.py` and `tests/test_project_gate.py` dirty before implementation evidence was captured, and final gate accepted them as inherited source/test dirty with warnings.

Observed recurring defect:

- Multiple recent engineering rounds have had source/test files modified before startup/baseline evidence was recorded.
- Existing gate can classify these files as `inherited_dirty_files` and permit closeout with warnings.
- This weakens audit provenance because it becomes unclear whether Codex respected the required startup sequence or retroactively explained already-modified files.

Desired policy shift:

- For source/test files, clean-start should be strict by default.
- If source/test files are dirty at startup, Codex must stop before implementation and report `BLOCKED` unless the decision explicitly contains an `Allowed Inherited Dirty Baseline Files` section naming those exact source/test paths with a reason.
- The explicit allowlist should be rare and should not be inferred from ordinary `Allowed source files` / `Allowed tests` implementation scope.

Existing relevant capabilities to reuse:

- `reverse_agent/project_gate.py` already tracks startup command coverage, baseline lifecycle checks, baseline dirty files, inherited dirty files, startup_baseline_consistency, and close snapshot state.
- `project_state/gates/round_baseline.json` and `project_state/gates/round_delta_summary.json` already contain enough information to identify baseline dirty and inherited dirty files.
- `pytest_result.txt` command blocks already record startup path confirmation and `git status --short`.
- Do not add a second gate system.

Artifact freshness:

- Historical `samplereverse` missing/stale artifacts are not current evidence for this engineering guardrail round.
- This round does not depend on reverse sample artifacts.

Negative results:

- Do not return to old `sample_solver` blind search.
- Do not only increase beam/budget.
- Do not use `compare_semantics_agree=false` candidates as primary frontier.
- Do not commit full `solve_reports/`.
- Do not repeat old `samplereverse` failed candidate/runtime branches.

Allowed tool execution:

- Read repository source/tests and compact `project_state/` metadata.
- Run gate/status/test commands listed in the Tests section.
- Do not run local reverse samples, IDA, Ghidra, debugger, emulator, runtime probe, harness campaigns, or solver commands.

Heavy artifact policy:

- Do not read full `solve_reports/`.
- Do not read full `PROJECT_PROGRESS_LOG.txt`.

## 3. Do Not Do

Do not weaken existing gate, report-summary, final-check, or close-round checks.

Do not treat files listed under ordinary `Allowed source files` or `Allowed tests` as automatically allowed inherited dirty baseline files.

Do not hide source/test dirty-at-startup behind `ACCEPTED_WITH_LIMITATIONS` when no explicit inherited baseline allowlist exists.

Do not make generated project_state gate artifacts blocking merely because they are dirty at startup.

Do not modify solver, harness, IDA/Ghidra/debugger/tool-runner, runtime probe, GUI/frontend, sample runner, raw sample, or `.codex-skills/` files.

Do not run sample binaries.

Do not run IDA/Ghidra/debugger/harness/solver/runtime probe commands.

Do not change training sample statuses.

Do not add a database, queue system, workflow engine, or new external dependency.

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
- `project_state/gates/final_gate_result.json`
- `project_state/gates/report_summary_synthesis.json`
- `reverse_agent/project_gate.py`
- `reverse_agent/project_state.py`
- `tests/test_project_gate.py`
- `tests/test_project_state.py`

Do not inspect unrelated solver/harness/tool-runner modules unless a failing test directly requires it.

## 5. Required Audit

Before implementation, confirm:

1. Startup path is `F:\reverse-agent`, `Test-Path F:\reverse-agent` is true, and `git rev-parse --show-toplevel` points to this repository.
2. Startup `git status --short` is recorded before any file modification.
3. If startup `git status --short` already shows source/test dirty files, stop immediately and write `codex_execution_report.md` with `status=BLOCKED`; do not implement changes.
4. `decision_meta` is valid, `status=APPROVED`, `mainline=engineering_branch`, and `reverse-agent-iteration@v2` is active.
5. Current decision controls execution; `task_packet.json` is not authoritative.
6. Existing baseline lifecycle and final-check behavior is understood before changing code.
7. No mature reverse-engineering tool integration needs to be modified.

## 6. Implementation Scope

Allowed source files:

- `reverse_agent/project_gate.py`
- `reverse_agent/project_state.py` only if report/status plumbing strictly requires it

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
- `project_state/rounds/round_20260617_clean_start_baseline_guard_v1/*`

Required implementation behavior:

- Add or harden a clean-start source/test dirty policy in the existing gate path.
- Source/test paths dirty in the round baseline must produce a blocking result unless all such paths are explicitly listed in a dedicated `Allowed Inherited Dirty Baseline Files` section.
- The dedicated allowlist must be separate from ordinary `Allowed source files` / `Allowed tests` and must be parsed narrowly.
- The block should occur as early as practical, preferably in preflight or final-check with a clear blocking reason. Prefer preflight if this can be done without broad refactoring.
- Generated project_state gate artifacts, report files, round archives, and other build outputs should not be treated as source/test clean-start violations.
- Preserve existing report-summary/final-check/close-round compatibility.
- Preserve path normalization across Windows and POSIX separators.
- Keep the already added gate-profile classifier behavior intact.

Required tests:

1. Startup/baseline dirty `reverse_agent/project_gate.py` without explicit inherited allowlist causes a blocking preflight or final-check result.
2. Startup/baseline dirty `tests/test_project_gate.py` without explicit inherited allowlist causes a blocking preflight or final-check result.
3. The same source/test dirty file is allowed only when listed under `Allowed Inherited Dirty Baseline Files`.
4. Ordinary `Allowed source files` / `Allowed tests` does not authorize inherited dirty baseline files.
5. Dirty generated project_state files do not trigger the source/test clean-start block.
6. Existing report-summary/final-check/close-round tests continue to pass.
7. Existing gate-profile tests continue to pass.

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
python -m reverse_agent.project_gate gate-profile --state-dir project_state --json
python -m reverse_agent.project_gate run-round --state-dir project_state --dry-run --json
python -m pytest tests/test_project_gate.py tests/test_project_state.py -q
python -m reverse_agent.project_state doctor --state-dir project_state
python -m reverse_agent.project_state lint-report --state-dir project_state
python -m reverse_agent.project_gate report-summary --state-dir project_state
python -m reverse_agent.project_gate final-check --state-dir project_state
python -m reverse_agent.project_gate close-round --state-dir project_state --round-id round_20260617_clean_start_baseline_guard_v1
```

The pytest result header must include:

- `decision_id=decision_20260617_clean_start_baseline_guard_v1`
- `round_id=round_20260617_clean_start_baseline_guard_v1`
- the final `report_id`
- all commands actually run

## 8. Stop Conditions

Stop and report `BLOCKED` without expanding scope if:

- current `decision_packet.md` is no longer this decision;
- `.codex-skills/registry.json` does not contain active `reverse-agent-iteration@v2`;
- startup `git status --short` already shows source/test dirty files before implementation begins;
- implementing this requires rewriting close-round or replacing the existing gate system;
- the change would require modifying solver/harness/tool-runner/debugger/sample code;
- tests fail for reasons outside the narrow clean-start baseline guard scope;
- the guard cannot distinguish source/test files from generated project_state artifacts without broad refactoring.
