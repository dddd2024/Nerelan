```json decision_meta
{"schema_version":1,"decision_id":"decision_20260610_rework_project_state_command_log_exactness_v1","round_id":"round_20260610_rework_project_state_command_log_exactness_v1","based_on_state_build_id":"state_20260610_131714_88c14099a13a","based_on_state_digest":"88c14099a13a2bf2999e4a61b2c53d8edd9568217bb5ee36f0cfd4462e8cbbd2","status":"APPROVED","mainline":"engineering_branch","skill_profiles":["reverse-agent-iteration@v2","samplereverse-frontier@v2"]}
```

# DECISION_PACKET

## 1. Goal

Repair the remaining command-log exactness defects from `decision_20260610_rework_project_state_evidence_manifest_consistency_v1`.

The previous round improved the evidence manifest, added `doctor_result_final.json` to `files_changed`, and aligned much of the metadata. It still failed audit because `pytest_result_summary.tests_ran` omitted required commands, `pytest_result.txt` recorded a placeholder sha256 for `doctor_result_final.json`, and the new `git index corruption` / `difflib fallback` explanation was not supported by complete command evidence.

This is an `engineering_branch` command-log/evidence bookkeeping repair. It must not change doctor behavior and must not run samples, solvers, debuggers, IDA, Ghidra, or other reverse tools.

## 2. Current Evidence

- Previous audit conclusion: `REWORK_REQUIRED`.
- Previous decision: `decision_20260610_rework_project_state_evidence_manifest_consistency_v1`.
- Previous report: `report_20260610_rework_project_state_evidence_manifest_consistency_v1`, status `SUCCESS`, bound to the previous decision.
- Previous pytest result: `167 passed in 73.73s`, bound to the previous decision/report/round.
- Previous `files_changed` now includes `doctor_result_final.json`.
- Previous `evidence_metadata.json` contains the correct `doctor_result_final.json` sha256: `4bcbf6183d7900d4e931004ee64ede858e4edf24d5ef3886d28a98ea282dba05`.
- Blocking defect: `pytest_result_summary.tests_ran` omits required commands including `pwd`, `git rev-parse --show-toplevel`, `git status --short`, `git diff -- ...`, and `git diff --cached -- ...`.
- Blocking defect: `pytest_result.txt` final doctor JSON section uses a placeholder sha256 instead of the exact sha256 for `doctor_result_final.json`.
- Blocking defect: the report introduced `git index corruption` and `git fsck --full` as key explanation, but those commands and outputs are not present in `pytest_result_summary.tests_ran` or recorded as evidence artifacts.
- `task_packet.json` remains advisory. This `decision_packet.md` controls the current round.
- `model_gate.json` and sample-state evidence are context only and must not drive reverse solving.
- Negative results still block blind search, candidate expansion, repeated stale runtime probes, and full `solve_reports/` scans.

## 3. Do Not Do

- Do not modify `.codex-skills/`.
- Do not start or run any sample-solving workflow.
- Do not run sample binaries.
- Do not generate, mutate, rank, validate, or emit candidates or flags.
- Do not run solver/search expansion.
- Do not run runtime probes, debuggers, emulators, hooks, sidecars, IDA, Ghidra, OllyDbg, x64dbg, Frida, or pywinauto.
- Do not inspect full `solve_reports/` or full `PROJECT_PROGRESS_LOG.txt`.
- Do not change doctor behavior.
- Do not rewrite `reverse_agent/project_state.py` or `tests/test_project_state.py` merely to make status clean.
- Do not mutate previous archived rounds.
- Do not introduce placeholder hashes, abbreviated JSON, or unrecorded key claims.
- Do not rely on `git index corruption` / `git fsck --full` claims unless the exact command output is recorded in `pytest_result.txt` or as an evidence artifact with sha256.

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
- `project_state/evidence/round_20260610_rework_project_state_full_evidence_outputs_v1/evidence_metadata.json`
- `project_state/evidence/round_20260610_rework_project_state_full_evidence_outputs_v1/doctor_result_final.json`
- `project_state/evidence/round_20260610_rework_project_state_full_evidence_outputs_v1/git_diff_scoped.patch`
- `project_state/evidence/round_20260610_rework_project_state_full_evidence_outputs_v1/git_diff_cached.patch`
- `reverse_agent/project_state.py`
- `tests/test_project_state.py`

Optional only if Codex continues to claim git/index corruption:

- A new evidence artifact under `project_state/evidence/round_20260610_rework_project_state_command_log_exactness_v1/` containing exact `git fsck --full` output.
- A new evidence artifact under the same directory containing exact scoped `git diff -- ...` output if the command output is too long for `pytest_result.txt`.

Do not inspect unrelated harness runs. Do not inspect full `solve_reports/`.

## 5. Required Audit

Codex must:

1. Confirm this decision packet is the active execution authority and `task_packet.json` is advisory only.
2. Confirm both skill profiles are active in `.codex-skills/registry.json`.
3. Update `pytest_result_summary.tests_ran` to include every required command actually run in this round.
4. Record exact output for `pwd` and `git rev-parse --show-toplevel`, proving `F:\reverse-agent`.
5. Record exact output for `git status --short`.
6. Run and record `git diff -- ...` over the scoped paths from this decision. If output is too long, save it as an artifact and record path, sha256, byte size, line count, and exact command.
7. Run and record `git diff --cached -- ...` over the same scoped paths. If empty, record exact empty output; if non-empty and too long, save it as an artifact with path, sha256, byte size, line count, and exact command.
8. Replace the placeholder `doctor_result_final.json` sha256 in `pytest_result.txt` with the exact value: `4bcbf6183d7900d4e931004ee64ede858e4edf24d5ef3886d28a98ea282dba05`.
9. If report or pytest mentions `git index corruption`, `short read while indexing`, or `git fsck --full`, record exact evidence for those commands. If Codex cannot record that evidence, remove the unsupported claim and limit the report to recorded facts.
10. Ensure `codex_report_summary.tests_ran` and `pytest_result_summary.tests_ran` match command-for-command, except duplicate commands may be listed in the same order actually run.
11. Ensure `codex_report_summary.files_changed`, `pytest_result.txt`, and `evidence_metadata.json` are mutually consistent.
12. Archive this repair round into `project_state/rounds/round_20260610_rework_project_state_command_log_exactness_v1/`.
13. After archive, run final `lint-report`, `status`, `doctor`, and `doctor --json`.
14. Record final `git status --short`.
15. Do not run any sample, solver, candidate validation, runtime probe, debugger, emulator, IDA, Ghidra, hook, or sidecar.

## 6. Implementation Scope

Allowed without further justification:

- `project_state/codex_execution_report.md`
- `project_state/pytest_result.txt`
- `project_state/rounds/round_20260610_rework_project_state_command_log_exactness_v1/*`
- `project_state/evidence/round_20260610_rework_project_state_full_evidence_outputs_v1/evidence_metadata.json`
- `project_state/evidence/round_20260610_rework_project_state_full_evidence_outputs_v1/git_diff_scoped.patch`
- `project_state/evidence/round_20260610_rework_project_state_full_evidence_outputs_v1/git_diff_cached.patch`
- `project_state/evidence/round_20260610_rework_project_state_command_log_exactness_v1/*`

Allowed only if already present and provenance is documented; do not intentionally modify:

- `project_state/evidence/round_20260610_rework_project_state_full_evidence_outputs_v1/doctor_result_final.json`
- `reverse_agent/project_state.py`
- `tests/test_project_state.py`
- `project_state/model_gate.json`
- `project_state/task_packet.json`

Disallowed:

- `.codex-skills/`
- solver/search/runtime/debugger/probe code
- IDA/Ghidra/debugger interface code
- sample binaries
- candidate files
- training dataset/sample metadata
- status overlay
- full `solve_reports/`
- full `PROJECT_PROGRESS_LOG.txt`
- previous archived round mutation

## 7. Tests

Run and record exact outputs in `project_state/pytest_result.txt`. If an output is saved as an artifact, record path, sha256, byte size, line count, and exact command.

```bash
pwd
git rev-parse --show-toplevel
git status --short
git diff -- reverse_agent/project_state.py tests/test_project_state.py project_state/decision_packet.md project_state/codex_execution_report.md project_state/pytest_result.txt project_state/model_gate.json project_state/task_packet.json project_state/evidence/round_20260610_rework_project_state_full_evidence_outputs_v1 project_state/evidence/round_20260610_rework_project_state_command_log_exactness_v1 project_state/rounds/round_20260610_rework_project_state_evidence_manifest_consistency_v1 project_state/rounds/round_20260610_rework_project_state_command_log_exactness_v1
git diff --cached -- reverse_agent/project_state.py tests/test_project_state.py project_state/decision_packet.md project_state/codex_execution_report.md project_state/pytest_result.txt project_state/model_gate.json project_state/task_packet.json project_state/evidence/round_20260610_rework_project_state_full_evidence_outputs_v1 project_state/evidence/round_20260610_rework_project_state_command_log_exactness_v1 project_state/rounds/round_20260610_rework_project_state_evidence_manifest_consistency_v1 project_state/rounds/round_20260610_rework_project_state_command_log_exactness_v1
python -m pytest tests/test_project_state.py -q
python -m reverse_agent.project_state lint-report --state-dir project_state
python -m reverse_agent.project_state status --state-dir project_state
python -m reverse_agent.project_state doctor --state-dir project_state
python -m reverse_agent.project_state doctor --state-dir project_state --json
python -m reverse_agent.project_state archive-round --state-dir project_state --round-id round_20260610_rework_project_state_command_log_exactness_v1
python -m reverse_agent.project_state lint-report --state-dir project_state
python -m reverse_agent.project_state status --state-dir project_state
python -m reverse_agent.project_state doctor --state-dir project_state
python -m reverse_agent.project_state doctor --state-dir project_state --json
git status --short
```

Only if using the git-corruption explanation, also run and record:

```bash
git fsck --full
```

Acceptance requirements:

- `pwd` and `git rev-parse --show-toplevel` prove the local repository root is `F:\reverse-agent`.
- `pytest_result_summary.tests_ran` includes every command above that was required and run.
- `codex_report_summary.tests_ran` matches `pytest_result_summary.tests_ran`.
- `doctor_result_final.json` sha256 in `pytest_result.txt` is exact and is not a placeholder.
- `git diff -- ...` evidence is recorded exactly inline or saved as an artifact with path, sha256, byte size, line count, and exact command.
- `git diff --cached -- ...` evidence is recorded exactly inline or saved as an artifact with path, sha256, byte size, line count, and exact command; empty output is acceptable if explicit.
- Any `git fsck --full` / index-corruption claim is backed by exact command output or an artifact with path and sha256.
- `python -m pytest tests/test_project_state.py -q` passes.
- Final `lint-report` is OK.
- Final status shows `decision_report_id_match: True`, `decision_consumed_by_report: True`, `decision_execution_state: CONSUMED_BY_SUCCESS_REPORT`, `round_manifest_present: True`, and `archive_status: archived`.
- Final `doctor` output is `PASS` or `WARN`, not `FAIL`.
- Final `doctor --json` output is complete valid JSON or saved as an artifact with path and sha256.
- `codex_report_summary.files_changed`, `pytest_result.txt`, and `evidence_metadata.json` are mutually consistent.
- No `.codex-skills/` changes.
- No sample/tool/debugger/solver/probe/IDA/Ghidra execution.

## 8. Stop Conditions

Stop and report `BLOCKED` or `FAILED` if:

- Repository root is not `F:\reverse-agent`.
- Exact `doctor_result_final.json` sha256 cannot be recorded in `pytest_result.txt`.
- Required `git diff` / `git diff --cached` evidence cannot be recorded inline or as artifacts.
- `git index corruption` is claimed but `git fsck --full` evidence cannot be recorded.
- `pytest_result_summary.tests_ran` cannot be made to cover the required commands.
- `codex_report_summary.tests_ran` cannot match `pytest_result_summary.tests_ran`.
- Final `lint-report` fails.
- Final status cannot reach consumed/archived state.
- Final doctor remains `FAIL`.
- The repair requires sample execution, solver execution, candidate validation, runtime probe, debugger, emulator, IDA, or Ghidra.
- `.codex-skills/` changes are required.
- The round shifts from `engineering_branch` into reverse solving or tool execution.
