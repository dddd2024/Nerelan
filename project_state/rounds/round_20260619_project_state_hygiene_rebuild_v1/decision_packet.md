```json decision_meta
{
  "schema_version": 1,
  "decision_id": "decision_20260619_project_state_hygiene_rebuild_v1",
  "round_id": "round_20260619_project_state_hygiene_rebuild_v1",
  "based_on_state_build_id": "state_20260618_134029_d6bd033d2532",
  "based_on_state_digest": "d6bd033d25324345cfd8ada0ac65db42bc86eb5017f3ffc92906fcd8b71cacb5",
  "status": "APPROVED",
  "mainline": "engineering_branch",
  "skill_profiles": ["reverse-agent-iteration@v2"]
}
```

# DECISION_PACKET

## 1. Goal

Clean up and rebuild the compact `project_state` package after the accepted status-policy closeout.

The previous round was accepted with limitations: the full gate sequence now passes under fast profile, but `task_packet.json` and `current_state.json` still point to the older `samplereverse` state package, while `artifact_index.json` still carries many historical/backlog missing artifacts. This round must reduce state confusion and make the next execution handoff unambiguous.

This is an engineering state-hygiene round. Do not solve `affine_8cfebe03` and do not resume `samplereverse` candidate search.

Success criteria:

1. Rebuild or normalize the compact project state so `decision_packet.md` remains the execution authority.
2. Record whether `task_packet.json`, `current_state.json`, and `artifact_index.json` still represent stale `samplereverse` sample state or a valid compact advisory cache.
3. Preserve the accepted blocker-only reverse-solving policy behavior; do not weaken solution/candidate gates.
4. Leave a current, auditable state-hygiene report and pytest/gate evidence.
5. Do not create fake historical artifacts and do not read full heavy-history directories.

## 2. Current Evidence

Current accepted audit result: `ACCEPTED_WITH_LIMITATIONS` for `decision_20260619_status_policy_rework_closeout_v1`.

The accepted closeout round established:

- `final-check` passed for `decision_20260619_status_policy_rework_closeout_v1`.
- `final_gate_result.json` carried current matching decision/report/round IDs.
- `status_policy_valid` was `WARN`, not `FAIL`.
- Historical/backlog artifacts were classified as non-blocking external state notices.
- Fast profile intentionally omitted close-round; this was accepted as a limitation.

Known remaining limitations:

1. `task_packet.json` still describes the older `samplereverse` package and says the task is `collect_missing_evidence`.
2. `current_state.json` still describes `samplereverse`, `L15(prefix8)`, and older compare-aware state.
3. `artifact_index.json` still has many `latest_artifacts_v2` entries with `freshness=missing` and null paths.
4. Historical/backlog artifact warnings are now non-blocking for the accepted fast validation round, but they can still confuse future decisions if left unexplained.
5. `pytest_result_summary.status` in the previous accepted round was `PARTIAL` although command bodies and final-check passed; this is not blocking but should be observed during the hygiene audit.

`task_packet.json` remains advisory only. It must not override this `decision_packet.md`.

Negative-results still apply:

- Do not return to old sample_solver blind search.
- Do not only increase beam/budget.
- Do not use compare_semantics_agree=false candidates as a primary frontier.
- Do not commit full `solve_reports/`.
- Do not repeat current 5-candidate transform-trace audit without new runtime evidence.

## 3. Do Not Do

Do not continue affine solving.

Do not invent or provide expected ciphertext for `affine_8cfebe03`.

Do not resume `samplereverse` reverse-solving or candidate generation.

Do not run target binaries, runtime probes, debuggers, emulators, hooks, or dynamic validation.

Do not read complete `solve_reports/` or `PROJECT_PROGRESS_LOG.txt`.

Do not create placeholder/fake historical artifacts to silence warnings.

Do not modify `.codex-skills/`.

Do not weaken status-policy handling for reverse-solving candidate, final answer, flag, or runtime validation claims.

Do not change solver logic.

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

Gate/status files:

1. `project_state/gates/final_gate_result.json`
2. `project_state/gates/preflight_result.json`
3. `project_state/gates/command_plan.json`
4. `project_state/gates/report_summary_synthesis.json`
5. `project_state/gates/round_delta_summary.json`
6. `project_state/gates/gate_profile_plan.json`

Implementation files to inspect before any change:

1. `reverse_agent/project_state.py`
2. `reverse_agent/project_gate.py`
3. `tests/test_project_state.py`
4. `tests/test_project_gate.py`

Relevant current affine blocker artifacts only as regression context:

1. `project_state/local_reverse_affine_8cfebe03_expected_ciphertext_evidence.json`
2. `project_state/local_reverse_affine_8cfebe03_inverse_handoff_current.json`
3. `project_state/local_reverse_affine_8cfebe03_solve_blocker.json`
4. `project_state/local_reverse_affine_8cfebe03_solve_provenance_report.json`
5. `project_state/local_reverse_affine_8cfebe03_solve_provenance_report.md`

## 5. Required Audit

Before implementation, answer:

1. Does `task_packet.json` still point to stale `samplereverse` state?
2. Does `current_state.json` still point to stale `samplereverse` state?
3. Which `artifact_index.json` entries are historical/backlog missing artifacts rather than current evidence?
4. Is there an existing state build or doctor command that can rebuild compact state without reading heavy history?
5. Does the existing gate policy already classify historical/backlog artifacts as non-blocking external notices for accepted engineering rounds?
6. Are any source/test changes actually necessary, or is this an artifact-only state rebuild/normalization round?

## 6. Implementation Scope

Preferred implementation is artifact-only.

Allowed actions:

1. Run the compact state build/doctor/lint commands already provided by `reverse_agent.project_state` and `reverse_agent.project_gate`.
2. If supported by existing CLI, run:
   - `python -m reverse_agent.project_state build`
   - `python -m reverse_agent.project_gate decision-lint --state-dir project_state`
   - `python -m reverse_agent.project_gate preflight --state-dir project_state`
   - `python -m reverse_agent.project_gate gate-profile --state-dir project_state`
   - `python -m reverse_agent.project_gate command-plan --state-dir project_state`
   - `python -m reverse_agent.project_gate report-summary --state-dir project_state`
   - `python -m reverse_agent.project_gate final-check --state-dir project_state`
3. Update `project_state/task_packet.json`, `project_state/current_state.json`, and `project_state/artifact_index.json` only if the existing build/normalization command does so legitimately.
4. Produce a state-hygiene summary artifact if helpful, for example `project_state/project_state_hygiene_report.json` or `.md`.
5. Update `project_state/codex_execution_report.md` and `project_state/pytest_result.txt` with this round's evidence.
6. Update `project_state/gates/*.json` through the gate commands.

Allowed source/test changes only if a real bug is found in existing state build or classification behavior:

- `reverse_agent/project_state.py`
- `reverse_agent/project_gate.py`
- `tests/test_project_state.py`
- `tests/test_project_gate.py`

Allowed project_state outputs:

- `project_state/task_packet.json`
- `project_state/current_state.json`
- `project_state/artifact_index.json`
- `project_state/project_state_hygiene_report.json`
- `project_state/project_state_hygiene_report.md`
- `project_state/codex_execution_report.md`
- `project_state/pytest_result.txt`
- `project_state/gates/*.json`
- `project_state/rounds/round_20260619_project_state_hygiene_rebuild_v1/*`

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

If source files are changed, also run the broader project-state/gate test subset required by the command plan.

If the command plan requires a build command, record it explicitly in `pytest_result.txt` before the gate sequence.

## 8. Stop Conditions

Stop and report `BLOCKED` or `REWORK_REQUIRED` if:

1. repository root cannot be confirmed;
2. decision metadata is invalid;
3. mainline is not `engineering_branch`;
4. skill profile is not active;
5. existing build/normalization would require reading complete `solve_reports/` or `PROJECT_PROGRESS_LOG.txt`;
6. implementation would need fake historical artifacts;
7. implementation would change solver logic;
8. implementation would weaken reverse-solving candidate/solution gates;
9. source changes exceed allowed project-state/gate files;
10. pytest fails;
11. final-check has any FAIL;
12. report/decision/pytest/final-gate IDs mismatch;
13. report claims affine or samplereverse solving progress.
