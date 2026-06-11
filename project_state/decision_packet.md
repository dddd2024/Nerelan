```json decision_meta
{
  "schema_version": 1,
  "decision_id": "decision_20260611_engineering_gate_final_check_v1",
  "round_id": "round_20260611_engineering_gate_final_check_v1",
  "based_on_state_build_id": "state_20260610_131714_88c14099a13a",
  "based_on_state_digest": "88c14099a13a2bf2999e4a61b2c53d8edd9568217bb5ee36f0cfd4462e8cbbd2",
  "status": "APPROVED",
  "mainline": "engineering_branch",
  "skill_profiles": [
    "reverse-agent-iteration@v2",
    "samplereverse-frontier@v2"
  ]
}
```

# DECISION_PACKET

## 1. Goal

建设门禁系统第一阶段：新增一个只读 final-check 门禁，用于降低 Codex 执行后的人工审计成本和返工率。

本轮只做门禁骨架，不做自动执行命令、不做 close-round、不推进样本求解。

必须完成：

1. 新增只读门禁命令：
   ```bash
   python -m reverse_agent.project_gate final-check --state-dir project_state
   ```
2. 输出结构化结果：
   ```text
   project_state/gates/final_gate_result.json
   ```
3. 门禁复用现有 `project_state` 能力，不重复实现 decision/report/pytest/archive 解析。
4. 门禁能自动检查：
   - decision/report/pytest_result ID 一致性；
   - report.tests_ran 与 pytest_result.tests_ran 覆盖关系；
   - report.files_changed 与实际 Git diff 文件一致性；
   - report.generated_artifacts 与 round archive 文件一致性；
   - archived report 与 live report 一致性；
   - forbidden paths；
   - SUCCESS/BLOCKED/FAILED 状态是否合理。
5. 添加测试覆盖这些门禁规则。

## 2. Current Evidence

- 当前上一轮归档一致性已完成，结论为 `ACCEPTED_WITH_LIMITATIONS`；项目仍因 `affine_8cfebe03` 的 IDA static triage 没有 evidence JSON 而处于业务 BLOCKED。
- 现在返工率高的主要原因不是 solver 或样本分析，而是 report、pytest_result、archive、git diff 之间的一致性长期依赖人工审计。
- `reverse_agent/project_state.py` 已有：
  - `DECISION_META_BLOCK_NAME`
  - `CODEX_REPORT_SUMMARY_BLOCK_NAME`
  - `PYTEST_RESULT_SUMMARY_BLOCK_NAME`
  - report/decision/pytest_result 状态枚举
  - `lint_report`
  - `doctor`
  - `archive-round`
- 因此本轮应复用这些能力，新增门禁聚合层，而不是重写现有解析和诊断逻辑。
- 当前主线切换为 `engineering_branch`，不得继续推进 `affine` 样本求解，也不得改 IDA runner。

## 3. Do Not Do

- 不运行样本二进制。
- 不运行 solver、candidate search、runtime probe、debugger、hook、emulator、sidecar。
- 不修 `affine_8cfebe03` 的 IDA evidence 输出问题。
- 不改训练集状态文件，除非测试 fixture 需要。
- 不读取完整 `solve_reports/`。
- 不修改 `.codex-skills/`。
- 不创建重型 workflow engine、数据库、消息队列、Kubernetes。
- 不实现自动执行命令的 close-round。
- 不替代现有 `lint-report/status/doctor/archive-round`，只做门禁聚合层。
- 不把 `doctor WARN` 简单等同于 gate failure；必须按规则区分 BLOCKED 报告、历史 stale artifacts、真实失败。

## 4. Files To Inspect

必须检查：

- `reverse_agent/project_state.py`
- `tests/test_project_state.py`
- `project_state/decision_packet.md`
- `project_state/codex_execution_report.md`
- `project_state/pytest_result.txt`
- `project_state/rounds/*/round_manifest.json`
- `.codex-skills/registry.json`

必要时检查：

- `pyproject.toml`
- `README.md`

## 5. Required Audit

Codex must:

1. Confirm repository root is `F:\reverse-agent`.
2. Confirm active decision is this packet and `status` is `APPROVED`.
3. Confirm `skill_profiles` are active.
4. Inspect existing `project_state.py` helpers before adding new code.
5. Decide whether to implement the CLI as:
   - preferred: `reverse_agent/project_gate.py`
   - acceptable: `reverse_agent/project_state.py gate-check`
6. Reuse existing parsing helpers where possible:
   - decision meta parser
   - codex report parser
   - pytest_result parser
   - round consistency builder
   - lint_report / doctor output
7. Add a structured result schema:
   ```json
   {
     "schema_version": 1,
     "gate_name": "final-check",
     "gate_status": "PASSED | FAILED | BLOCKED | WARN",
     "decision_id": "",
     "report_id": "",
     "round_id": "",
     "checks": [],
     "blocking_reasons": [],
     "warnings": [],
     "recommended_next_action": ""
   }
   ```
8. Gate rules must include:
   - `decision_report_match`
   - `pytest_result_match`
   - `pytest_result_covers_report_tests`
   - `round_manifest_present`
   - `archived_report_matches_live_report`
   - `archived_pytest_result_matches_live_pytest_result`
   - `files_changed_covers_git_diff`
   - `generated_artifacts_cover_round_archive`
   - `forbidden_paths_absent`
   - `status_policy_valid`
9. Add tests proving the exact regressions from recent rounds are caught:
   - missing `codex_report_summary`;
   - pytest_result lacks required command outputs;
   - report files_changed omits archive files;
   - generated_artifacts omits archive files;
   - archived report differs from live report;
   - SUCCESS with doctor/lint failures is rejected;
   - BLOCKED report with consistent archive is accepted as `BLOCKED`, not failure.

## 6. Implementation Scope

Allowed source files:

- `reverse_agent/project_gate.py`
- `reverse_agent/project_state.py` only if helper exposure or CLI integration is necessary

Allowed tests:

- `tests/test_project_gate.py`
- `tests/test_project_state.py` only if existing helper tests must be extended

Allowed generated files:

- `project_state/gates/final_gate_result.json`
- `project_state/pytest_result.txt`
- `project_state/codex_execution_report.md`
- `project_state/rounds/round_20260611_engineering_gate_final_check_v1/*`

Disallowed:

- `reverse_agent/local_reverse_training_status.py`
- `reverse_agent/local_reverse_single_sample_static_triage.py`
- solver modules
- IDA/Ghidra/debugger/runtime modules
- sample binaries
- `solve_reports/`
- `.codex-skills/`
- training inventory/status/queue files

## 7. Tests

Run and record exact outputs:

```bash
pwd
git rev-parse --show-toplevel
git status --short
python -m pytest tests/test_project_gate.py tests/test_project_state.py -q
python -m reverse_agent.project_gate final-check --state-dir project_state
python -m reverse_agent.project_gate final-check --state-dir project_state --json
python -m reverse_agent.project_state lint-report --state-dir project_state
python -m reverse_agent.project_state status --state-dir project_state
python -m reverse_agent.project_state doctor --state-dir project_state
python -m reverse_agent.project_state doctor --state-dir project_state --json
python -m reverse_agent.project_state archive-round --state-dir project_state --round-id round_20260611_engineering_gate_final_check_v1
python -m reverse_agent.project_state lint-report --state-dir project_state
python -m reverse_agent.project_state status --state-dir project_state
python -m reverse_agent.project_state doctor --state-dir project_state
python -m reverse_agent.project_state doctor --state-dir project_state --json
git status --short
```

`pytest_result.txt` 必须使用正式 `pytest_result_summary`，并记录所有命令 stdout/stderr。

## 8. Stop Conditions

Stop and report `BLOCKED` or `FAILED` if:

- 需要重写现有 `project_state` 解析器才能完成；
- final-check 会修改 live state 文件；
- gate 不能区分 `BLOCKED but consistent` 与 `FAILED evidence mismatch`；
- gate 无法检测 archive report 与 live report 不一致；
- gate 无法检查 files_changed/generated_artifacts 与实际 Git diff/round archive 的关系；
- tests 无法复现最近几轮返工问题；
- 实现会触碰 sample solving、IDA runner、training status 或 solver 逻辑；
- final git status 出现 scope 外文件。
