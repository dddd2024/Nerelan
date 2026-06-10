```json decision_meta
{"schema_version":1,"decision_id":"decision_20260610_rework_project_state_full_evidence_outputs_v1","round_id":"round_20260610_rework_project_state_full_evidence_outputs_v1","based_on_state_build_id":"state_20260610_131714_88c14099a13a","based_on_state_digest":"88c14099a13a2bf2999e4a61b2c53d8edd9568217bb5ee36f0cfd4462e8cbbd2","status":"APPROVED","mainline":"engineering_branch","skill_profiles":["reverse-agent-iteration@v2","samplereverse-frontier@v2"]}
```

# DECISION_PACKET

## 1. Goal

Repair the remaining evidence-recording defect from the workspace diff audit round by recording complete, machine-checkable outputs for `doctor --json` and real `git diff` evidence.

The previous round correctly identified provenance for source/test modifications, but its evidence was still summarized instead of recorded as command output. In particular, `doctor --json` was recorded as `{status: WARN, checks: [...]}`, which is not valid JSON, and `git diff` was summarized as `+~200 lines` / `Same as initial diff`, which is not a real patch output.

This is an `engineering_branch` evidence-output repair round. Do not change doctor behavior, do not start solving, and do not run samples or reverse tools.

## 2. Current Evidence

- Previous audit conclusion: `REWORK_REQUIRED`.
- Previous decision: `decision_20260610_rework_project_state_workspace_diff_audit_v1`.
- Previous report: `report_20260610_rework_project_state_workspace_diff_audit_v1`, status `SUCCESS`, bound to the previous decision.
- Previous pytest record: `167 passed in 64.53s`.
- Previous final `doctor` output: `doctor: WARN`, with only artifact freshness warning.
- Blocking defect: previous `doctor --json` was not complete parseable JSON because it used unquoted keys and abbreviated `checks` as `[...]`.
- Blocking defect: previous `git diff -- ...` output was not a real patch. It was an English summary of file changes.
- Blocking defect: previous final `git diff -- ...` was also summarized, so provenance claims cannot be independently audited from command output.
- Existing source/test modifications may remain prior uncommitted changes from `decision_20260610_add_project_state_doctor_v1`; this round must not alter them unless a genuine command failure requires it.
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
- Do not change doctor behavior unless a required command genuinely fails because of a code defect.
- Do not rewrite `reverse_agent/project_state.py` or `tests/test_project_state.py` merely to make status clean.
- Do not mutate previous archived rounds.
- Do not record abbreviated JSON such as `{status: WARN, checks: [...]}`.
- Do not replace real `git diff` output with English summaries such as `+~200 lines` or `Same as initial diff`.
- Do not claim evidence is complete unless the full output is in `pytest_result.txt` or in a referenced artifact with sha256.

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

Optional only to compare previous evidence:

- `project_state/rounds/round_20260610_rework_project_state_workspace_diff_audit_v1/round_manifest.json`
- `project_state/rounds/round_20260610_rework_project_state_workspace_diff_audit_v1/pytest_result.txt`

Do not inspect unrelated harness runs. Do not inspect full `solve_reports/`.

## 5. Required Audit

Codex must:

1. Confirm this decision packet is the active execution authority and `task_packet.json` is advisory only.
2. Confirm both skill profiles are active in `.codex-skills/registry.json`.
3. Run `python -m reverse_agent.project_state doctor --state-dir project_state --json` and save the exact complete stdout as valid JSON evidence.
4. If the JSON output is stored in `pytest_result.txt`, it must be full JSON with quoted keys and complete `checks` list.
5. If the JSON output is stored as an artifact, write it to `project_state/evidence/round_20260610_rework_project_state_full_evidence_outputs_v1/doctor_result.json` and record the path and sha256 in `pytest_result.txt` and `codex_execution_report.md`.
6. Run scoped `git diff -- ...` over all relevant paths and record the real patch output.
7. If scoped `git diff` is too long for `pytest_result.txt`, save it to `project_state/evidence/round_20260610_rework_project_state_full_evidence_outputs_v1/git_diff_scoped.patch` and record the path, byte size, line count, and sha256.
8. Run scoped `git diff --cached -- ...` over the same paths and record the real output. If empty, record exact empty-output evidence; if non-empty and too long, save it to `project_state/evidence/round_20260610_rework_project_state_full_evidence_outputs_v1/git_diff_cached.patch` with path, byte size, line count, and sha256.
9. Run and record `git status --short` before and after report/pytest/artifact updates.
10. Ensure `codex_report_summary.files_changed` includes all files intentionally changed by this round, including any new evidence artifact files.
11. Ensure `pytest_result_summary.tests_ran` covers every command claimed in `codex_report_summary.tests_ran`.
12. Archive this round into `project_state/rounds/round_20260610_rework_project_state_full_evidence_outputs_v1/`.
13. After archive, run final `lint-report`, `status`, `doctor`, and `doctor --json`.
14. Do not run any sample, solver, candidate validation, runtime probe, debugger, emulator, IDA, Ghidra, hook, or sidecar.

## 6. Implementation Scope

Allowed without further justification:

- `project_state/codex_execution_report.md`
- `project_state/pytest_result.txt`
- `project_state/rounds/round_20260610_rework_project_state_full_evidence_outputs_v1/*`
- `project_state/evidence/round_20260610_rework_project_state_full_evidence_outputs_v1/doctor_result.json`
- `project_state/evidence/round_20260610_rework_project_state_full_evidence_outputs_v1/git_diff_scoped.patch`
- `project_state/evidence/round_20260610_rework_project_state_full_evidence_outputs_v1/git_diff_cached.patch`

Allowed only if already modified as prior uncommitted work and provenance is documented:

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

Run and record exact outputs in `project_state/pytest_result.txt`. For outputs saved as artifacts, record artifact path, sha256, byte size, line count, and the exact command used to generate them.

```bash
pwd
git rev-parse --show-toplevel
git status --short
python -m pytest tests/test_project_state.py -q
python -m reverse_agent.project_state lint-report --state-dir project_state
python -m reverse_agent.project_state status --state-dir project_state
python -m reverse_agent.project_state doctor --state-dir project_state
python -m reverse_agent.project_state doctor --state-dir project_state --json
git diff -- reverse_agent/project_state.py tests/test_project_state.py project_state/decision_packet.md project_state/codex_execution_report.md project_state/pytest_result.txt project_state/model_gate.json project_state/task_packet.json project_state/rounds/round_20260610_rework_project_state_workspace_diff_audit_v1 project_state/rounds/round_20260610_rework_project_state_full_evidence_outputs_v1 project_state/evidence/round_20260610_rework_project_state_full_evidence_outputs_v1
git diff --cached -- reverse_agent/project_state.py tests/test_project_state.py project_state/decision_packet.md project_state/codex_execution_report.md project_state/pytest_result.txt project_state/model_gate.json project_state/task_packet.json project_state/rounds/round_20260610_rework_project_state_workspace_diff_audit_v1 project_state/rounds/round_20260610_rework_project_state_full_evidence_outputs_v1 project_state/evidence/round_20260610_rework_project_state_full_evidence_outputs_v1
python -m reverse_agent.project_state archive-round --state-dir project_state --round-id round_20260610_rework_project_state_full_evidence_outputs_v1
python -m reverse_agent.project_state lint-report --state-dir project_state
python -m reverse_agent.project_state status --state-dir project_state
python -m reverse_agent.project_state doctor --state-dir project_state
python -m reverse_agent.project_state doctor --state-dir project_state --json
git status --short
```

Acceptance requirements:

- `pwd` and `git rev-parse --show-toplevel` prove the local repository root is `F:\reverse-agent`.
- `python -m pytest tests/test_project_state.py -q` passes.
- Final `lint-report` is OK.
- Final status shows `decision_report_id_match: True`.
- Final status shows `decision_consumed_by_report: True`.
- Final status shows `decision_execution_state: CONSUMED_BY_SUCCESS_REPORT`.
- Final status shows `round_manifest_present: True` and `archive_status: archived`.
- Final `doctor` output is `PASS` or `WARN`, not `FAIL`.
- Final `doctor --json` output is complete valid JSON with quoted keys, complete `checks`, and status `PASS` or `WARN`.
- `git diff -- ...` evidence is real patch output, either inline or saved as a patch artifact with sha256.
- `git diff --cached -- ...` evidence is real output, either inline or saved as a patch artifact with sha256; empty output is acceptable if explicitly recorded.
- `codex_report_summary.files_changed` matches all files intentionally changed by this round, including evidence artifacts if created.
- No `.codex-skills/` changes.
- No sample/tool/debugger/solver/probe/IDA/Ghidra execution.

## 8. Stop Conditions

Stop and report `BLOCKED` or `FAILED` if:

- Repository root is not `F:\reverse-agent`.
- Final `doctor --json` cannot be captured as complete valid JSON.
- Real scoped `git diff` output cannot be recorded inline or as an artifact with sha256.
- Final `lint-report` fails.
- Final status cannot reach consumed/archived state.
- Final doctor remains `FAIL`.
- The repair requires sample execution, solver execution, candidate validation, runtime probe, debugger, emulator, IDA, or Ghidra.
- `.codex-skills/` changes are required.
- The round shifts from `engineering_branch` into reverse solving or tool execution.
