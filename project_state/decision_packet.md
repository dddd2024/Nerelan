```json decision_meta
{
  "schema_version": 1,
  "decision_id": "decision_20260619_reverse_solving_status_policy_rework_v1",
  "round_id": "round_20260619_reverse_solving_status_policy_rework_v1",
  "based_on_state_build_id": "state_20260618_134029_d6bd033d2532",
  "based_on_state_digest": "d6bd033d25324345cfd8ada0ac65db42bc86eb5017f3ffc92906fcd8b71cacb5",
  "status": "APPROVED",
  "mainline": "engineering_branch",
  "skill_profiles": ["reverse-agent-iteration@v2"]
}
```

# DECISION_PACKET

## 1. Goal

Fix the gate/status-policy failure that blocked `round_20260619_affine_reverse_solving_ciphertext_handoff_v1`.

This is an engineering rework round. Do not continue solving `affine_8cfebe03`. The previous reverse-solving work produced a valid blocker, but `final-check` failed because historical/backlog missing artifacts are treated as blocking under `reverse_solving`. The goal is to make the gate policy/state handling precise enough that a reverse-solving blocker-only report with complete current-round artifacts is not blocked by unrelated historical/backlog artifacts, or to produce a precise engineering blocker if that policy cannot be safely changed.

## 2. Current Evidence

`decision_packet.md` for the failed round was valid and mainline was `reverse_solving`.

`codex_execution_report.md` reported `status=FAILED` and `acceptance_recommendation=REWORK_REQUIRED`.

`pytest_result.txt` shows:

- startup path checks passed;
- decision-lint passed;
- preflight passed;
- pytest passed with 887 tests;
- final-check failed on `status_policy_valid`;
- close-round failed because `final_check_before_archive` was blocked by `status_policy_valid`.

`final_gate_result.json` shows:

- `gate_status=FAILED`;
- `status_policy_valid=FAIL`;
- lint error: `50 missing, 0 stale artifacts`;
- report status is `FAILED`;
- archive status is `not_archived`.

The affine-specific blocker artifacts are current and should not be discarded:

- `project_state/local_reverse_affine_8cfebe03_expected_ciphertext_evidence.json`
- `project_state/local_reverse_affine_8cfebe03_inverse_handoff_current.json`
- `project_state/local_reverse_affine_8cfebe03_solve_blocker.json`
- `project_state/local_reverse_affine_8cfebe03_solve_provenance_report.json`
- `project_state/local_reverse_affine_8cfebe03_solve_provenance_report.md`

The important semantic distinction:

- Current affine round evidence is complete for a blocker outcome.
- Historical/backlog artifacts are missing.
- The failed reverse-solving report does not claim a candidate or final answer.

## 3. Do Not Do

Do not continue solving `affine_8cfebe03`.

Do not invent or provide expected ciphertext.

Do not rerun blind search, dynamic execution, debugger, emulator, hook, or runtime probe.

Do not create fake historical artifacts just to satisfy the gate.

Do not add `reverse_solving` globally to a non-blocking whitelist without guard conditions.

Do not weaken gate policy for candidate/solution claims.

Do not modify `.codex-skills/`.

Do not read complete `solve_reports/` or `PROJECT_PROGRESS_LOG.txt`.

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

Likely implementation files:

1. `reverse_agent/project_gate.py`
2. `reverse_agent/project_state.py`
3. related gate/status-policy helper modules if split out
4. `tests/test_project_gate.py`
5. `tests/test_project_state.py`

Current affine blocker artifacts for regression context:

1. `project_state/local_reverse_affine_8cfebe03_expected_ciphertext_evidence.json`
2. `project_state/local_reverse_affine_8cfebe03_inverse_handoff_current.json`
3. `project_state/local_reverse_affine_8cfebe03_solve_blocker.json`
4. `project_state/local_reverse_affine_8cfebe03_solve_provenance_report.json`

## 5. Required Audit

Before changing code, answer:

1. Where is `status_policy_valid` implemented?
2. Where are historical/backlog artifact freshness issues classified as blocking or non-blocking?
3. Why are 50 missing historical artifacts blocking under `reverse_solving`?
4. Does the failed affine round claim a candidate, solution, flag, or runtime validation?
5. Are all current-round affine blocker artifacts present and covered?
6. Can the policy safely distinguish blocker-only reverse-solving reports from candidate/solution reverse-solving reports?

## 6. Implementation Scope

Preferred fix:

Introduce or adjust claim-aware gate policy so that, for `reverse_solving`, historical/backlog missing artifacts are non-blocking only when all of the following are true:

1. the report status is non-success / blocker / failed handoff;
2. no candidate, final answer, flag, or runtime-validated solution is claimed;
3. current-round claimed artifacts are present;
4. report/decision/pytest IDs match;
5. pytest passed;
6. current blocker artifact clearly records missing evidence and next action;
7. no stale/missing artifact is used as current evidence.

Historical/backlog artifacts must remain blocking for `reverse_solving` when the report claims a candidate, final answer, validation success, or solution.

Allowed source/test changes:

- `reverse_agent/project_gate.py`
- `reverse_agent/project_state.py`
- any existing small gate helper module if the relevant policy is already split out
- `tests/test_project_gate.py`
- `tests/test_project_state.py`

Allowed project_state outputs:

- `project_state/codex_execution_report.md`
- `project_state/pytest_result.txt`
- `project_state/gates/*.json`
- `project_state/rounds/round_20260619_reverse_solving_status_policy_rework_v1/*`

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
python -m pytest tests/test_project_gate.py tests/test_project_state.py -q
python -m reverse_agent.project_gate gate-profile --state-dir project_state
python -m reverse_agent.project_gate command-plan --state-dir project_state
python -m reverse_agent.project_gate report-summary --state-dir project_state
python -m reverse_agent.project_gate final-check --state-dir project_state
```

If source changes touch broader gate/project-state behavior, run the broader relevant suite.

## 8. Stop Conditions

Stop and report `BLOCKED` or `REWORK_REQUIRED` if:

1. repository root cannot be confirmed;
2. decision metadata is invalid;
3. mainline is not `engineering_branch`;
4. skill profile is not active;
5. the policy fix would globally weaken reverse-solving candidate/solution validation;
6. the fix requires creating fake historical artifacts;
7. source changes exceed allowed gate/project-state files;
8. pytest fails;
9. final-check has any FAIL;
10. report/decision/pytest IDs mismatch;
11. the report claims the affine sample is solved;
12. the implementation modifies solver logic or affine artifacts unnecessarily.
