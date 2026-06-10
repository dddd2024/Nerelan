```json decision_meta
{
  "schema_version": 1,
  "decision_id": "decision_20260610_add_project_state_doctor_v1",
  "round_id": "round_20260610_add_project_state_doctor_v1",
  "based_on_state_build_id": "state_20260610_105707_1114a74dbc48",
  "based_on_state_digest": "1114a74dbc482a6cdcef792426ec10b895a15da031744a6e295ca39d770800fb",
  "status": "APPROVED",
  "mainline": "engineering_branch",
  "skill_profiles": ["reverse-agent-iteration@v2", "samplereverse-frontier@v2"]
}
```

# DECISION_PACKET

## 1. Goal

Add the first `project_state doctor` command under the existing `reverse_agent.project_state` CLI.

The purpose is to automate the status checks that are currently repeated manually: decision/report matching, pytest-result matching, archive state, skill profile validity, and stale/missing artifact warnings. This is an `engineering_branch` round only. Do not start any solving workflow.

Before changing files, Codex must confirm it is working in the real local repository:

```powershell
cd F:\reverse-agent
pwd
git status --short
git rev-parse --show-toplevel
```

If the repository root is not `F:\reverse-agent`, stop and report `BLOCKED`.

## 2. Current Evidence

- Previous round `decision_20260610_rework_run_missing_harness_compare_test_v1` completed the missing-test rework.
- Previous audit result was `ACCEPTED_WITH_LIMITATIONS` because local path confirmation and final diff self-check were not recorded.
- Existing project-state CLI already has `build`, `status`, `lint-decision`, `lint-report`, `lint-handoff`, `archive-round`, and `pack`.
- Search did not find an existing `doctor` command.
- Existing `status_summary()`, `lint_decision()`, `lint_report()`, and `lint_handoff()` should be reused.
- Current `model_gate.json` still reports `next_local_action: repair_harness_case_result_materialization`; this is state context, not the target of this round.
- `artifact_index.json` still has stale/missing artifacts. Doctor may warn about them, but must not promote them.
- `task_packet.json` is advisory. This `decision_packet.md` controls the round.

## 3. Do Not Do

- Do not start a solving run or validate any candidate.
- Do not run external analysis tools.
- Do not read full `solve_reports/` or full `PROJECT_PROGRESS_LOG.txt`.
- Do not modify `.codex-skills/`.
- Do not create a parallel state-management module.
- Do not implement `solve`, `solve --dry-run`, or a workflow engine.
- Do not change sample data, candidate files, training metadata, or historical reports.
- Do not make doctor auto-fix files. First version is diagnostic only.

## 4. Files To Inspect

Required:

- `project_state/decision_packet.md`
- `project_state/codex_execution_report.md`
- `project_state/pytest_result.txt`
- `project_state/current_state.json`
- `project_state/artifact_index.json`
- `project_state/model_gate.json`
- `project_state/task_packet.json`
- `project_state/negative_results.json`
- `.codex-skills/registry.json`
- `reverse_agent/project_state.py`
- `tests/test_project_state.py`

Optional, only if needed for archive assertions:

- `project_state/rounds/round_20260610_rework_run_missing_harness_compare_test_v1/round_manifest.json`
- `tests/test_harness_artifact_manifest.py`

## 5. Required Audit

Codex must confirm:

1. Working tree root is `F:\reverse-agent`, and the report records this check.
2. Current decision packet is the execution authority.
3. `decision_meta.status == APPROVED` and `mainline == engineering_branch`.
4. Both listed skill profiles are active in `.codex-skills/registry.json`.
5. Existing project-state helpers are reused instead of reimplemented.
6. Doctor does not mutate live state files.
7. Doctor reports status as `PASS`, `WARN`, or `FAIL`.
8. Doctor returns exit code `0` for `PASS` and `WARN`, and `1` for `FAIL`.
9. Doctor gives a concrete `next_action` when status is `FAIL`.
10. Final report and pytest result are bound to this decision and round.

Doctor must check at least:

- decision packet parse status;
- decision approval status;
- allowed mainline value;
- active skill profiles;
- report parse status;
- report-to-decision ID match;
- pytest-result parse status;
- pytest-result-to-report match;
- pytest-result test coverage for report `tests_ran`;
- round manifest presence;
- archive status;
- stale/missing artifact counts as warnings.

## 6. Implementation Scope

Allowed changes:

- `reverse_agent/project_state.py`
- `tests/test_project_state.py`
- `project_state/codex_execution_report.md`
- `project_state/pytest_result.txt`
- `project_state/rounds/round_20260610_add_project_state_doctor_v1/*`

Optional only if directly required by tests:

- `tests/test_harness_artifact_manifest.py`

Disallowed changes:

- `.codex-skills/`
- unrelated source files
- sample/candidate/training files
- historical report payloads

## 7. Tests

Run and record exact output:

```bash
python -m pytest tests/test_project_state.py -q
python -m reverse_agent.project_state doctor --state-dir project_state
python -m reverse_agent.project_state lint-decision --state-dir project_state
python -m reverse_agent.project_state lint-report --state-dir project_state
python -m reverse_agent.project_state status --state-dir project_state
python -m reverse_agent.project_state archive-round --state-dir project_state --round-id round_20260610_add_project_state_doctor_v1
python -m reverse_agent.project_state lint-report --state-dir project_state
python -m reverse_agent.project_state status --state-dir project_state
```

If `--json` is implemented, also run:

```bash
python -m reverse_agent.project_state doctor --state-dir project_state --json
```

Record final self-check:

```bash
pwd
git rev-parse --show-toplevel
git status --short
git diff -- reverse_agent/project_state.py tests/test_project_state.py project_state/codex_execution_report.md project_state/pytest_result.txt project_state/rounds/round_20260610_add_project_state_doctor_v1
```

Acceptance requirements:

- `python -m reverse_agent.project_state doctor --state-dir project_state` runs successfully.
- Doctor does not modify live state files.
- Current consumed/archived state is reported as `PASS` or `WARN`, not `FAIL`.
- Tests cover one healthy state and at least two failure states: report/decision mismatch, pytest/report mismatch or missing pytest result, and optionally missing archive.
- `python -m pytest tests/test_project_state.py -q` passes.
- Final `lint-report: OK`.
- Final status shows consumed and archived.
- No `.codex-skills/` changes.

## 8. Stop Conditions

Stop and report `BLOCKED` or `FAILED` if:

- Repository root is not `F:\reverse-agent`.
- Adding doctor cannot be done inside existing `reverse_agent.project_state` CLI.
- The change requires a parallel state system.
- The task requires starting a solving workflow.
- Tests fail and cannot be repaired in the allowed scope.
- Final `lint-report` fails.
- Final status cannot reach consumed and archived.

## 9. Notes For Later

After this round is accepted, a later round may consider stricter JSON schema for doctor output or `solve --dry-run`. Do not implement those in this round.
