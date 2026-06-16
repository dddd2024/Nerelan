```json decision_meta
{
  "schema_version": 1,
  "decision_id": "decision_20260616_cpp1_pause_aware_runtime_evidence_review_v1",
  "round_id": "round_20260616_cpp1_pause_aware_runtime_evidence_review_v1",
  "based_on_state_build_id": "state_20260615_150220_24f61a9ac337",
  "based_on_state_digest": "24f61a9ac337b596ff7d56b3e29f01e5ab68342825fb2a32ba50b65a84512bae",
  "status": "APPROVED",
  "mainline": "reverse_solving",
  "skill_profiles": ["reverse-agent-iteration@v2"]
}
```

# DECISION_PACKET

## 1. Goal

Use the current `cpp1_2f6fcb63` bounded runtime boundary probe artifact to perform a **pause-aware runtime evidence review**.

The previous runtime probe round did execute the local trusted sample, but all probes timed out because `CPP1.exe` enters a `system("pause")` loop. The captured stdout still contains program output, including failure markers. This round must classify that captured output without rerunning the sample.

The goal is to turn the current `INCONCLUSIVE_TIMEOUT_OR_IO` probe artifact into a more useful evidence artifact:

- identify whether each timed-out probe still produced decisive success/failure output before the pause loop;
- confirm whether the current all-byte inverse preview was rejected at runtime;
- avoid treating timeout alone as success/failure;
- preserve `runtime_validated=false` unless an exact success marker is present;
- produce a clear next action: either candidate-confirmation path, or static/debugger recheck of the success boundary.

This is a reverse-solving evidence interpretation round, not a new runtime campaign and not a frontend/backend round.

## 2. Current Evidence

The current execution authority is this `project_state/decision_packet.md`; `task_packet.json` and `current_state.json` remain historical `samplereverse` state inputs and must not override this decision.

Current mainline: `reverse_solving`.

Accepted previous closeout:

- `decision_20260616_cpp1_runtime_boundary_closeout_rework_v1`
- `round_20260616_cpp1_runtime_boundary_closeout_rework_v1`
- report/final gate/archive were accepted with limitations.

Current cpp1 artifacts:

- `local_reverse_cpp1_2f6fcb63_static_triage` is current in `artifact_index.json`.
- `local_reverse_cpp1_2f6fcb63_target_bytes_revalidation` is current in `artifact_index.json` and has `revalidation_status=PASSED`.
- `local_reverse_cpp1_2f6fcb63_runtime_boundary_probe` is current in `artifact_index.json`; it records three probes and `verdict=INCONCLUSIVE_TIMEOUT_OR_IO`.
- The runtime boundary probe artifact now has non-empty `decision_id` and `round_id`, `executed_sample=true`, and `runtime_validated=false`.
- The captured output contains repeated `Press any key to continue` plus visible failure text such as `Sorry, you are wrong!`; there is no accepted evidence of `Congratulations! You are right!` or equivalent success text.

Relevant negative results:

- Do not return to old `sample_solver` blind search.
- Do not only increase beam/budget.
- Do not commit full `solve_reports/`.
- Do not repeat the printable inverse path unless target bytes or transform semantics change.

Existing tool capability audit:

- IDA / IDAPython capability exists and was already used for static triage; do not duplicate it.
- OllyDbg/debugger capability exists in the project, but this round does not use debugger automation.
- Existing `local_reverse_cpp1_runtime_boundary_probe.py` generated the current runtime artifact; do not rerun it in this round.
- Existing generic runtime benchmark helpers exist; do not create a second runtime framework.
- Solver templates, symbolic solvers, and harness exist, but this round must not use them for search.
- Tool execution policy: no sample execution in this round; reading current runtime output artifact is allowed.
- Heavy artifacts: do not read full `solve_reports/` or `PROJECT_PROGRESS_LOG.txt`; only read explicitly listed current artifacts.

## 3. Do Not Do

Do not rerun `CPP1.exe`.

Do not run new runtime probes, debugger automation, emulator, hook, harness campaign, or console automation.

Do not patch the binary in this round.

Do not run old `sample_solver`, brute force, SMT, beam/topN/budget expansion, or candidate-pool exploration.

Do not analyze or solve `samplereverse`.

Do not mark CPP1 as solved.

Do not generate a password/flag.

Do not treat timeout alone as failure or success. A timeout can be classified only through captured success/failure markers.

Do not call nonprintable bytes a normal text password; if bytes must be recorded, use hex fields.

Do not modify `.codex-skills/`, raw samples, training materials, GUI/frontend, complete `solve_reports/`, IDA runner semantics, debugger runner semantics, or harness runtime behavior.

Do not remove historical missing artifact entries just to pass gates.

## 4. Files To Inspect

Read default state files in order:

1. `project_state/task_packet.json`
2. `project_state/current_state.json`
3. `project_state/artifact_index.json`
4. `project_state/negative_results.json`
5. `project_state/codex_execution_report.md`
6. `project_state/decision_packet.md`
7. `project_state/pytest_result.txt`
8. `.codex-skills/registry.json`

Also inspect:

- `project_state/local_reverse_cpp1_2f6fcb63_runtime_boundary_probe.json`
- `project_state/local_reverse_cpp1_2f6fcb63_target_bytes_revalidation.json`
- `project_state/local_reverse_cpp1_2f6fcb63_success_boundary_static_recheck.json`
- `project_state/local_reverse_cpp1_2f6fcb63_input_delivery_review.json`
- `reverse_agent/local_reverse_cpp1_runtime_boundary_probe.py`
- `reverse_agent/tool_capability_inventory.py`
- `reverse_agent/tool_runners.py`, only to confirm existing mature tool interfaces if needed
- directly relevant tests if any source is touched

Do not read full `PROJECT_PROGRESS_LOG.txt` or full `solve_reports/`.

## 5. Required Audit

Before changing files, confirm:

1. Startup path is `F:\reverse-agent` and `git rev-parse --show-toplevel` points to this repository.
2. `decision_meta` is valid, `status=APPROVED`, `mainline=reverse_solving`, and `reverse-agent-iteration@v2` is active.
3. `task_packet.json/current_state.json` are historical `samplereverse` state, not this round's execution authority.
4. `local_reverse_cpp1_2f6fcb63_runtime_boundary_probe` is current in `artifact_index.json` and its artifact exists.
5. The runtime artifact records exactly the prior bounded probes and `runtime_validated=false`.
6. No success marker has been observed in the current artifact unless exact captured output proves otherwise.
7. Current target revalidation remains current and is not downgraded.
8. This round does not require re-executing the sample.

Output artifact:

- `project_state/local_reverse_cpp1_2f6fcb63_pause_aware_runtime_review.json`

The artifact must include at least:

- `schema_version`
- `decision_id`
- `round_id`
- `sample_id`
- `relative_path`
- `sha256`
- `analysis_mode="pause_aware_runtime_evidence_review"`
- `mainline="reverse_solving"`
- `source_artifacts`
- `source_artifact_freshness`
- `executed_sample=false` for this review round
- `reviewed_prior_runtime_execution=true`
- `runtime_validated=false` unless an exact success marker appears and baseline does not
- `success_markers`
- `failure_markers`
- `pause_markers`
- `per_probe_classification`, with each probe classified as one of `SUCCESS_MARKER_SEEN`, `FAILURE_MARKER_SEEN`, `PAUSE_ONLY_TIMEOUT`, `NO_DECISIVE_MARKER`, `MIXED_MARKERS`
- `candidate_bytes_hex=null` unless success is exact and baseline fails
- `candidate_text=null` unless candidate bytes are printable ASCII
- `current_preview_status`, one of `REJECTED_BY_RUNTIME_OUTPUT`, `SUCCESS_CONFIRMED`, `INCONCLUSIVE_NO_DECISIVE_MARKER`, `MIXED_OUTPUT_NEEDS_TOOL_RECHECK`
- `static_boundary_contradicted=false` unless success is observed
- `recommended_next_action`
- `stop_conditions_for_next_round`

Expected classification unless the artifact content contradicts it:

- `baseline_18_A`: `FAILURE_MARKER_SEEN`
- `raw_inverse_AA`: `FAILURE_MARKER_SEEN`
- `raw_inverse_BB`: `FAILURE_MARKER_SEEN`
- `current_preview_status`: `REJECTED_BY_RUNTIME_OUTPUT`
- `runtime_validated=false`
- recommended next action: use a separate tool-integration/static-debugger decision to inspect why the first 16 transformed bytes or success boundary fail; do not rerun the same payloads.

`artifact_index.json` must register `local_reverse_cpp1_2f6fcb63_pause_aware_runtime_review` as current only if the artifact is generated successfully.

## 6. Implementation Scope

Prefer no source changes if Codex can produce the review artifact directly from current JSON evidence.

Allowed project_state updates:

- `project_state/local_reverse_cpp1_2f6fcb63_pause_aware_runtime_review.json`
- `project_state/artifact_index.json`, only to register the new review artifact
- `project_state/codex_execution_report.md`
- `project_state/pytest_result.txt`
- `project_state/gates/command_plan.json`
- `project_state/gates/final_gate_result.json`
- `project_state/gates/preflight_result.json`
- `project_state/gates/report_summary_synthesis.json`
- `project_state/gates/round_baseline.json`
- `project_state/gates/round_close_snapshot.json`
- `project_state/gates/round_delta_summary.json`
- `project_state/gates/run_round_result.json`
- `project_state/rounds/round_20260616_cpp1_pause_aware_runtime_evidence_review_v1/*`

Allowed source change only if needed for reproducibility:

- `reverse_agent/local_reverse_cpp1_pause_aware_runtime_review.py`, as a thin parser/classifier for the existing runtime boundary artifact.
- Directly related focused tests.

Do not modify `reverse_agent/project_gate.py` in this round.

Do not modify runtime runner behavior, debugger integration, solver logic, harness behavior, GUI/frontend, `.codex-skills/`, or raw samples.

## 7. Tests

Record commands, stdout, stderr, and exit code in `project_state/pytest_result.txt`.

Required commands:

```powershell
Set-Location F:\reverse-agent
Get-Location
Test-Path F:\reverse-agent
git rev-parse --show-toplevel
git status --short
python -m reverse_agent.project_gate preflight --state-dir project_state
python -m reverse_agent.project_gate command-plan --state-dir project_state
python -m reverse_agent.project_gate command-plan --state-dir project_state --json
python -m reverse_agent.project_gate run-round --state-dir project_state --dry-run --json
python -m reverse_agent.project_state doctor --state-dir project_state
python -m reverse_agent.project_state lint-report --state-dir project_state
python -m reverse_agent.project_state active-execution-view --state-dir project_state --json
```

If a new parser CLI is added, use this shape:

```powershell
python -m reverse_agent.local_reverse_cpp1_pause_aware_runtime_review --runtime-boundary project_state/local_reverse_cpp1_2f6fcb63_runtime_boundary_probe.json --target-revalidation project_state/local_reverse_cpp1_2f6fcb63_target_bytes_revalidation.json --success-boundary project_state/local_reverse_cpp1_2f6fcb63_success_boundary_static_recheck.json --artifact-index project_state/artifact_index.json --out project_state/local_reverse_cpp1_2f6fcb63_pause_aware_runtime_review.json
```

If no source code is changed, run:

```powershell
python -m pytest tests/test_project_state.py tests/test_project_gate.py -q
```

If source code is changed, run focused tests plus:

```powershell
python -m pytest tests/test_project_state.py tests/test_project_gate.py -q
```

Finish with:

```powershell
python -m reverse_agent.project_gate report-summary --state-dir project_state
python -m reverse_agent.project_gate final-check --state-dir project_state
python -m reverse_agent.project_gate close-round --state-dir project_state --round-id round_20260616_cpp1_pause_aware_runtime_evidence_review_v1
```

## 8. Stop Conditions

Stop with `BLOCKED` if the current runtime boundary probe artifact is missing or not current.

Stop with `BLOCKED` if current target revalidation is missing or not current.

Stop with `REWORK_REQUIRED` if the review artifact omits probe classifications or cannot justify its verdict from captured stdout/stderr.

Stop with `REWORK_REQUIRED` if any sample execution occurs in this round.

Stop with `REWORK_REQUIRED` if `project_gate.py` is modified.

Stop with `REWORK_REQUIRED` if report-summary and live report disagree.

Stop with `REWORK_REQUIRED` if close-round exits nonzero.

Do not write SUCCESS or ACCEPTED if final gate fails or close-round fails.
