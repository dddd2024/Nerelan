```json decision_meta
{"schema_version":1,"decision_id":"decision_20260611_refresh_training_inventory_and_queue_v1","round_id":"round_20260611_refresh_training_inventory_and_queue_v1","based_on_state_build_id":"state_20260610_131714_88c14099a13a","based_on_state_digest":"88c14099a13a2bf2999e4a61b2c53d8edd9568217bb5ee36f0cfd4462e8cbbd2","status":"APPROVED","mainline":"training_dataset","skill_profiles":["reverse-agent-iteration@v2","samplereverse-frontier@v2"]}
```

# DECISION_PACKET

## 1. Goal

Close the engineering-branch cleanup loop and begin the `training_dataset` mainline by refreshing the local reverse sample inventory, metadata-only GitHub inventory, harness case JSONs, training status overlay, and evaluation queue.

This round is **not** a sample-solving round. It must only establish the training dataset control plane: what samples exist, how they are identified, what metadata is safe to commit, what cases can later be evaluated, and which unsolved samples should enter a bounded future evaluation queue.

Use the existing inventory and training-status tools. Do not create a second scanner, a new database, or a new workflow engine.

## 2. Current Evidence

- The previous engineering round `decision_20260611_classify_doctor_artifact_freshness_v1` was accepted. Final `doctor` is `PASS`, while historical sample artifact counts remain visible as non-blocking INFO.
- `project_state/decision_packet.md` now controls the active round. `task_packet.json` remains advisory only and still contains stale sample-solving context derived from older `samplereverse` artifacts.
- `current_state.json` and `artifact_index.json` still primarily describe an old `samplereverse` reverse-solving state. They must not be treated as the current training-dataset source of truth.
- `negative_results.json` blocks old blind sample search, beam/budget expansion, stale runtime probes, and full `solve_reports/` commits. This training round must not repeat those directions.
- `.codex-skills/registry.json` currently has only two active skill profiles available: `reverse-agent-iteration@v2` and `samplereverse-frontier@v2`. Do not invent a training skill profile.
- Existing training inventory capability exists in `reverse_agent/local_reverse_inventory.py`:
  - default local root: `E:/reverse`;
  - output: `project_state/local_reverse_inventory.json`;
  - GitHub-safe metadata output: `training_materials/local_reverse/inventory.json`;
  - harness-compatible cases: `training_materials/local_reverse/cases/*.json`;
  - `LOCAL_REVERSE_ROOT` placeholder is used instead of committing absolute local paths.
- Existing training status capability exists in `reverse_agent/local_reverse_training_status.py`:
  - reads metadata inventory and existing validated/blocked evidence;
  - writes `project_state/local_reverse_training_status.json`;
  - writes `project_state/local_reverse_evaluation_queue.json`;
  - writes GitHub-safe `training_materials/local_reverse/status_overlay.json`;
  - does not upload original samples, run solvers, run dynamic analysis, generate candidates, or create another scanner.
- `training_materials/local_reverse/README.md` states the repository stores metadata only, not original sample binaries; actual samples are local under `E:\reverse` or `LOCAL_REVERSE_ROOT`.
- Existing tests cover inventory scanning, GitHub-safe output with no absolute local path leakage, generated harness case payloads with `${LOCAL_REVERSE_ROOT}`, and training-status overlay logic.
- Existing mature tools/interfaces in the project include harness, project_state, sample inventory/status overlay, solver/runtime/debugger/tool-interface evidence paths. This round must inspect those capabilities but not execute IDA/Ghidra/debugger/runtime tooling.

## 3. Do Not Do

- Do not modify `.codex-skills/`.
- Do not commit original sample binaries, archives, extracted sample contents, local executable samples, or full local dataset contents.
- Do not commit full `solve_reports/`.
- Do not read full `solve_reports/` or full `PROJECT_PROGRESS_LOG.txt`.
- Do not run solvers, candidate search, candidate validation, model calls, runtime probes, debuggers, emulators, hooks, sidecars, IDA, Ghidra, OllyDbg, x64dbg, Frida, pywinauto, or sample binaries.
- Do not batch-run harness against real samples.
- Do not infer solved/blocked status from stale sample artifacts as if they were current evidence.
- Do not mark stale/missing artifacts as current.
- Do not hardcode a single sample result into long-term training logic.
- Do not broaden into reverse solving or tool integration.
- Do not create a new scanner when `reverse_agent/local_reverse_inventory.py` already exists.
- Do not create a database, queue service, Kubernetes job, or heavy workflow engine.

## 4. Files To Inspect

Required:

- `project_state/decision_packet.md`
- `project_state/codex_execution_report.md`
- `project_state/pytest_result.txt`
- `project_state/current_state.json`
- `project_state/artifact_index.json`
- `project_state/task_packet.json`
- `project_state/negative_results.json`
- `.codex-skills/registry.json`
- `reverse_agent/local_reverse_inventory.py`
- `reverse_agent/local_reverse_training_status.py`
- `training_materials/local_reverse/README.md`
- `tests/test_local_reverse_inventory.py`
- `tests/test_local_reverse_training_status.py`
- `tests/test_project_state.py`
- `reverse_agent/harness.py` only to confirm generated case files remain compatible with `load_harness_cases`

Optional, bounded:

- `project_state/local_reverse_inventory.json` if present.
- `training_materials/local_reverse/inventory.json` if present.
- `training_materials/local_reverse/status_overlay.json` if present.
- `project_state/local_reverse_training_status.json` if present.
- `project_state/local_reverse_evaluation_queue.json` if present.
- Prior training-related project_state JSONs only if directly needed to understand status overlay merge inputs.

Do not inspect unrelated harness runs. Do not inspect full `solve_reports/`.

## 5. Required Audit

Codex must:

1. Confirm this decision packet is the active execution authority and `task_packet.json` is advisory only.
2. Confirm both declared skill profiles are active in `.codex-skills/registry.json`; do not invent a training-specific skill profile.
3. Confirm repository root is `F:\reverse-agent` before making changes.
4. Inspect `local_reverse_inventory.py`, `local_reverse_training_status.py`, and existing tests before modifying any code.
5. Check whether `LOCAL_REVERSE_ROOT` is set. If unset, check whether `E:\reverse` exists. If neither exists, stop with `BLOCKED` and write a report explaining the missing local sample root; do not fabricate inventory data.
6. If a local sample root exists, run the existing inventory scanner only for metadata:
   - `project_state/local_reverse_inventory.json`
   - `training_materials/local_reverse/inventory.json`
   - `training_materials/local_reverse/cases/*.json`
7. Ensure GitHub-safe inventory and case files contain no absolute local paths and no binary payload bytes.
8. Ensure every generated case uses `${LOCAL_REVERSE_ROOT}/relative/path` rather than a real local drive path.
9. Run existing training-status builder to refresh:
   - `project_state/local_reverse_training_status.json`
   - `project_state/local_reverse_evaluation_queue.json`
   - `training_materials/local_reverse/status_overlay.json`
10. Ensure the training status distinguishes `solved`, `blocked`, `needs_triage`, and `inventory_only` without promoting stale evidence to current.
11. Ensure the evaluation queue only contains unsolved / inventory-only / needs-triage items and does not include solved entries as targets.
12. Add or update focused tests only if the existing inventory/status tools fail to enforce metadata-only behavior, placeholder paths, or queue filtering.
13. Update `codex_execution_report.md` using `generated_artifacts` for current-round outputs and `verified_artifacts` only for pre-existing checked artifacts, if any.
14. Archive this round into `project_state/rounds/round_20260611_refresh_training_inventory_and_queue_v1/`.
15. After archive, run final `lint-report`, `status`, `doctor`, and `doctor --json`.
16. Record final `git status --short`.
17. Do not run any reverse-solving, solver, candidate validation, runtime probe, debugger, emulator, IDA, Ghidra, hook, sidecar, or model.

## 6. Implementation Scope

Allowed without further justification:

- `project_state/local_reverse_inventory.json`
- `project_state/local_reverse_training_status.json`
- `project_state/local_reverse_evaluation_queue.json`
- `training_materials/local_reverse/inventory.json`
- `training_materials/local_reverse/status_overlay.json`
- `training_materials/local_reverse/cases/*.json`
- `project_state/codex_execution_report.md`
- `project_state/pytest_result.txt`
- `project_state/rounds/round_20260611_refresh_training_inventory_and_queue_v1/*`

Allowed only if tests reveal a metadata/inventory bug:

- `reverse_agent/local_reverse_inventory.py`
- `reverse_agent/local_reverse_training_status.py`
- `tests/test_local_reverse_inventory.py`
- `tests/test_local_reverse_training_status.py`
- `tests/test_project_state.py`
- `training_materials/local_reverse/README.md`

Disallowed:

- `.codex-skills/`
- sample binaries or archive payloads
- full `solve_reports/`
- full `PROJECT_PROGRESS_LOG.txt`
- solver/search/runtime/debugger/probe code
- IDA/Ghidra/debugger interface code
- candidate files
- unrelated harness behavior
- previous archived round mutation

## 7. Tests

Run and record exact outputs in `project_state/pytest_result.txt`.

```bash
pwd
git rev-parse --show-toplevel
git status --short
python -m pytest tests/test_local_reverse_inventory.py tests/test_local_reverse_training_status.py tests/test_project_state.py -q
python -m reverse_agent.local_reverse_inventory scan --samples-root %LOCAL_REVERSE_ROOT% --out project_state\local_reverse_inventory.json --github-out training_materials\local_reverse\inventory.json --cases-dir training_materials\local_reverse\cases
python -m reverse_agent.local_reverse_training_status --inventory project_state\local_reverse_inventory.json --out project_state\local_reverse_training_status.json --queue-out project_state\local_reverse_evaluation_queue.json --github-status-out training_materials\local_reverse\status_overlay.json
python -m reverse_agent.project_state lint-report --state-dir project_state
python -m reverse_agent.project_state status --state-dir project_state
python -m reverse_agent.project_state doctor --state-dir project_state
python -m reverse_agent.project_state doctor --state-dir project_state --json
python -m reverse_agent.project_state archive-round --state-dir project_state --round-id round_20260611_refresh_training_inventory_and_queue_v1
python -m reverse_agent.project_state lint-report --state-dir project_state
python -m reverse_agent.project_state status --state-dir project_state
python -m reverse_agent.project_state doctor --state-dir project_state
python -m reverse_agent.project_state doctor --state-dir project_state --json
git status --short
```

If `%LOCAL_REVERSE_ROOT%` is unset, use `E:\reverse` only if it exists. Record which root was used. If no root exists, do not run scan/status generation; mark the round `BLOCKED` with a precise reason.

Acceptance requirements:

- Repository root is confirmed as `F:\reverse-agent`.
- Inventory scan uses an existing local sample root and does not fabricate entries.
- GitHub-safe outputs contain no absolute local paths and no sample binary payloads.
- Generated case JSONs use `${LOCAL_REVERSE_ROOT}` placeholders.
- Training status and evaluation queue are refreshed from metadata only.
- Evaluation queue does not target samples already marked solved.
- Existing inventory/status/project_state tests pass.
- `lint-report` is OK after report and pytest are written.
- Final status shows `decision_report_id_match: True`, `decision_consumed_by_report: True`, `decision_execution_state: CONSUMED_BY_SUCCESS_REPORT`, `round_manifest_present: True`, and `archive_status: archived`.
- Final `doctor` is `PASS`, or `WARN` only for a real active-round issue, not historical artifact freshness alone.
- `codex_report_summary.tests_ran` and `pytest_result_summary.tests_ran` match command-for-command.
- No `.codex-skills/` changes.
- No solver/search/runtime/debugger/probe/IDA/Ghidra/model/sample execution.

## 8. Stop Conditions

Stop and report `BLOCKED` or `FAILED` if:

- Repository root is not `F:\reverse-agent`.
- `LOCAL_REVERSE_ROOT` is unset and `E:\reverse` does not exist.
- Inventory scan would require committing sample binaries or absolute local paths.
- The existing inventory/status tools cannot produce metadata-only outputs.
- Tests fail.
- Final `lint-report` fails.
- Final status cannot reach consumed/archived state.
- Final doctor is `FAIL`.
- The round requires running solvers, sample binaries, candidate validation, runtime probes, debuggers, emulators, hooks, sidecars, IDA, or Ghidra.
- The round would change `.codex-skills/`.
- The round drifts back into single-sample reverse solving instead of training dataset inventory/status work.
