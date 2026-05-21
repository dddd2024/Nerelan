# Phase 2 Harness Reproducibility Completion Report

## Scope

Phase 2 is closed as an A-D engineering branch for harness reproducibility, resumability, and comparison:

- Phase 2A: harness resume semantics.
- Phase 2B: case result `artifact_manifest` and project_state ingestion.
- Phase 2C: read-only harness compare.
- Phase 2D: resource budget recording in run manifests.

Phase 2E is not an official phase. The correct next label is Phase 3A or post-Phase-2 hardening.

This completion audit does not advance the `samplereverse` runtime mainline, run reverse probes, run pipeline/model calls, or modify harness functionality.

## Acceptance Matrix

| phase | decision_id | report_id | round_id | status | tests | Codex acceptance_recommendation | GPT review result |
|---|---|---|---|---|---|---|---|
| Phase 2A | `decision_phase2a_harness_resume_policy_20260520` | `report_phase2a_harness_resume_policy_20260520` | `round_20260520_phase2a_harness_resume_policy` | `SUCCESS` | `tests/test_harness_resume.py`: 6 passed; full pytest: 360 passed | `ACCEPTED` | `ACCEPTED_WITH_LIMITATIONS` |
| Phase 2B | `decision_phase2b_case_artifact_manifest_20260520` | `report_phase2b_case_artifact_manifest_20260520` | `round_20260520_phase2b_case_artifact_manifest` | `SUCCESS` | `tests/test_harness_artifact_manifest.py`: 3 passed; `tests/test_project_state.py`: 104 passed; full pytest: 366 passed | `ACCEPTED` | `ACCEPTED_WITH_LIMITATIONS` |
| Phase 2C | `decision_phase2c_harness_compare_20260520` | `report_phase2c_harness_compare_20260520` | `round_20260520_phase2c_harness_compare` | `SUCCESS` | `tests/test_harness_compare.py`: 9 passed; full pytest: 375 passed | `ACCEPTED` | `ACCEPTED_WITH_LIMITATIONS` |
| Phase 2D | `decision_phase2d_harness_resource_budget_20260520` | `report_phase2d_harness_resource_budget_20260520` | `round_20260520_phase2d_harness_resource_budget` | `SUCCESS` | `tests/test_harness_resource_budget.py`: 9 passed; full pytest: 384 passed | `ACCEPTED` | `ACCEPTED_WITH_LIMITATIONS` |

## Completed Capabilities

- Phase 2A added explicit resume policy behavior: default terminal-only resume, legacy all-existing compatibility, and rerun status overrides including `--rerun-error`.
- Phase 2B added additive per-case artifact manifests and project_state ingestion that prefers case-level provenance when present while retaining legacy scan fallback.
- Phase 2C added a read-only harness compare command for base/head harness run case results and lightweight artifact deltas.
- Phase 2D added local resource budget recording to harness configuration and `run_manifest.json` without enforcing process termination, artifact cleanup, truncation, or queue behavior.

## Evidence

- `project_state/rounds/round_20260520_phase2a_harness_resume_policy/decision_packet.md`
- `project_state/rounds/round_20260520_phase2a_harness_resume_policy/codex_execution_report.md`
- `project_state/rounds/round_20260520_phase2a_harness_resume_policy/pytest_result.txt`
- `project_state/rounds/round_20260520_phase2a_harness_resume_policy/round_manifest.json`
- `project_state/rounds/round_20260520_phase2b_case_artifact_manifest/decision_packet.md`
- `project_state/rounds/round_20260520_phase2b_case_artifact_manifest/codex_execution_report.md`
- `project_state/rounds/round_20260520_phase2b_case_artifact_manifest/pytest_result.txt`
- `project_state/rounds/round_20260520_phase2b_case_artifact_manifest/round_manifest.json`
- `project_state/rounds/round_20260520_phase2c_harness_compare/decision_packet.md`
- `project_state/rounds/round_20260520_phase2c_harness_compare/codex_execution_report.md`
- `project_state/rounds/round_20260520_phase2c_harness_compare/pytest_result.txt`
- `project_state/rounds/round_20260520_phase2c_harness_compare/round_manifest.json`
- `project_state/rounds/round_20260520_phase2d_harness_resource_budget/decision_packet.md`
- `project_state/rounds/round_20260520_phase2d_harness_resource_budget/codex_execution_report.md`
- `project_state/rounds/round_20260520_phase2d_harness_resource_budget/pytest_result.txt`
- `project_state/rounds/round_20260520_phase2d_harness_resource_budget/round_manifest.json`

Current completion-audit verification on 2026-05-21:

- `python -m pytest -q tests\test_harness_resume.py`: 6 passed.
- `python -m pytest -q tests\test_harness_artifact_manifest.py`: 3 passed.
- `python -m pytest -q tests\test_harness_compare.py`: 9 passed.
- `python -m pytest -q tests\test_harness_resource_budget.py`: 9 passed.
- `python -m pytest -q`: 384 passed.
- `python -m reverse_agent.project_state lint-decision --state-dir project_state`: OK.
- Pre-report `python -m reverse_agent.project_state lint-handoff --state-dir project_state`: OK as `READY_FOR_CODEX`, with the expected old Phase 2D report mismatch.

## Audit Findings

- Phase 2A-D archived decision, report, pytest result, and round manifest files are present and readable.
- Each archived report has `status=SUCCESS`, Codex `acceptance_recommendation=ACCEPTED`, and a `based_on_decision_id` matching the archived decision for that phase.
- GPT review results for Phase 2A-D are `ACCEPTED_WITH_LIMITATIONS`; the `ACCEPTED` value is retained only as Codex's `acceptance_recommendation`.
- Each archived phase records real pytest evidence in its archived `pytest_result.txt`.
- Phase 2A-D did not modify `reverse_agent/strategies/compare_aware_search.py` or `reverse_agent/olly_scripts/*`.
- Phase 2B modified `reverse_agent/project_state.py` for artifact manifest ingestion, but Phase 2A-D did not change the GPT/Codex decision/report/handoff schema.
- Phase 2A-D did not run reverse runtime probes or advance the `samplereverse` solving mainline.
- Phase 2D mentioned a possible "Phase 2E" cleanup in its next suggested task; this report corrects that naming. Those items are Phase 3 or post-Phase-2 hardening work.

## Known Limitations

- Harness compare does not yet enforce strict behavior for missing runs or missing comparison inputs.
- Artifact manifest path handling remains tolerant rather than normalized under a formal path schema.
- `round_manifest` still does not distinguish all desired source-state commit and archive commit semantics.
- Archive diffs are not yet a complete replay format for untracked or generated-file recovery.

## Phase 3 Backlog

- Compare strict behavior for missing runs and missing required compare inputs.
- Formal artifact manifest path normalization and validation.
- Clear `round_manifest` semantics for source state git commit versus archive git commit.
- Archive diff replayability for untracked files and generated handoff artifacts.

## Closure

Phase 2 A-D is complete and closed. There is no Phase 2E. Future work should start as Phase 3A or as explicitly named post-Phase-2 hardening.
