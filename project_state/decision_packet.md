```json decision_meta
{
  "schema_version": 1,
  "decision_id": "decision_20260613_report_metadata_hygiene_v1",
  "round_id": "round_20260613_report_metadata_hygiene_v1",
  "based_on_state_build_id": "state_20260613_054156_2729a02c7407",
  "based_on_state_digest": "2729a02c7407808c057a8a3f3e1d414797d660957dbe80b6c0780ffe6ec6bac9",
  "status": "APPROVED",
  "mainline": "engineering_branch",
  "skill_profiles": ["reverse-agent-iteration@v2"]
}
```

# DECISION_PACKET

## 1. Goal

对上一轮 `decision_20260613_training_queue_static_triage_hygiene_v1` 的审计限制做小范围收口：修复当前轮报告、pytest 记录、gate/round 归档之间的 metadata 一致性问题，确保 `codex_report_summary.tests_ran`、`generated_artifacts`、`verified_artifacts`、`project_state/pytest_result.txt`、`project_state/gates/*.json`、`project_state/rounds/<round_id>/*` 互相匹配，并且所有验证命令都在 `close-round` 之前完成。

本轮不推进任何逆向样本，不运行 static triage，不运行 IDA/Ghidra/debugger/emulator/harness/runtime validation，不生成 candidate，不改 solver，不改训练集状态生成逻辑。目标只是消除上一轮 `ACCEPTED_WITH_LIMITATIONS` 中的报告元数据不完整问题，为后续再推进 `cpp1_2f6fcb63` 的静态 triage 决策清理状态。

## 2. Current Evidence

当前主线为 `engineering_branch`。本轮处理的是 project_state 报告、pytest、gate、round archive 的审计一致性，不是 `training_dataset` 的样本队列策略继续修改，也不是 `tool_integration` 的 IDA/Ghidra 工具接入，更不是 `reverse_solving` 的样本求解。

`project_state/decision_packet.md` 是当前轮执行权威。`project_state/task_packet.json` 与 `project_state/current_state.json` 仍包含旧 `samplereverse` sample_state 背景，只能作为历史背景，不能覆盖本 decision。不得根据 `task_packet.task=collect_missing_evidence` 回到旧 `samplereverse` 求解线。

上一轮审计结论为 `ACCEPTED_WITH_LIMITATIONS`：训练队列卫生修复本身有效，`affineenc_333f8ca9` 已经从 static triage 队列移除，PDF 支持文档未进入队列，`cpp1_2f6fcb63` 成为 rank 1 PE 候选；但是上一轮 `codex_report_summary.tests_ran` 没有完整列入补充执行的 `tests/test_local_reverse_training_status.py`、训练状态重建命令和 queue/status schema verification，`generated_artifacts` 也没有完整列入 `project_state/local_reverse_training_status.json` 与 `project_state/local_reverse_evaluation_queue.json`。这些是 report metadata hygiene 问题，不是训练队列实现失败。

上一轮 `project_state/pytest_result.txt` 已经记录过：`tests/test_project_state.py tests/test_project_gate.py` 通过，`tests/test_local_reverse_training_status.py` 通过，训练状态生成命令退出码为 0，queue/status verification 显示 `affineenc_333f8ca9` 为 `needs_triage` 且 queue_rank=None，`ascii_table_chinese_46efc7ea` queue_rank=None，`cpp1_2f6fcb63` queue_rank=1。该证据只能作为上一轮审计背景；本轮必须重新记录本轮自己的 command/test/gate 结果。

`project_state/artifact_index.json` 仍有旧 `samplereverse` 历史 artifact missing 项。这些 missing/stale 历史样本 artifact 对本轮 engineering metadata 收口是非阻塞背景，不能被当作 current sample-solving evidence，也不能作为推进旧 `samplereverse` 的理由。

`negative_results.json` 中禁止回到旧 sample_solver 盲搜、只扩大 beam/budget、使用 compare_semantics_agree=false 作为主 frontier、提交完整 solve_reports、重复旧 `samplereverse` 失败方向。本轮不触碰这些方向。

现有相关能力必须优先复用：`reverse_agent.project_gate` 的 `preflight`、`command-plan`、`report-summary`、`final-check`、`close-round`，以及 `reverse_agent.project_state` 的 `doctor`、`lint-report`、pytest/result 校验和 round archive 机制。不得新建一套 report/gate/round 系统。

工具能力边界：本轮不需要 IDA/Ghidra/debugger/emulator/harness/solver。若为了报告元数据一致性需要改代码，应只限于现有 project_gate/project_state 机制的小修正和测试；不得新增逆向工具接口或触碰 sample-solving pipeline。

允许读取重型 artifact：不允许读取完整 `solve_reports/` 或完整 `PROJECT_PROGRESS_LOG.txt`。只允许读取本轮直接相关的 project_state 文件、上一轮 round archive、gate JSON、report/pytest、project_gate/project_state 相关源码和测试。

## 3. Do Not Do

不得运行 IDA、Ghidra、static triage、forced IDA、xref extraction、decompiler extraction、debugger、emulator、hook、runtime probe、harness campaign、solver、SMT、bruteforce 或 sample_solver。

不得推进 `cpp1_2f6fcb63` 的实际 static triage；本轮只能确认它仍是下一候选，不能分析它、不能生成证据、不能求解。

不得生成 candidate、flag、password；不得把任何新样本标成 solved。

不得修改 `reverse_agent/local_reverse_training_status.py`、训练队列筛选语义、solver、harness、debugger/emulator、IDA/Ghidra 接口、`reverse_agent/strategies/`、`reverse_agent/transforms/`。

不得修改 `.codex-skills/`、training materials、raw sample 文件、`solve_reports/` 历史目录，不得提交完整 solve_reports。

不得手工改写 `project_state/local_reverse_training_status.json` 或 `project_state/local_reverse_evaluation_queue.json` 来掩盖生成器问题。本轮如果需要验证这些文件，只做只读 schema/status 检查，除非明确发现它们已经与上一轮 accepted evidence 不一致；若不一致，停止并报告 REWORK_REQUIRED，不要私自修复训练语义。

不得在 `close-round` 之后追加新的测试或 verification 命令记录。所有本轮 verification 必须先完成，再 final-check，再 close-round。

## 4. Files To Inspect

必须按顺序读取：

1. `project_state/task_packet.json`
2. `project_state/current_state.json`
3. `project_state/artifact_index.json`
4. `project_state/negative_results.json`
5. `project_state/codex_execution_report.md`
6. `project_state/decision_packet.md`
7. `project_state/pytest_result.txt`
8. `.codex-skills/registry.json`

还必须有界读取：

- `project_state/gates/command_plan.json`
- `project_state/gates/report_summary_synthesis.json`
- `project_state/gates/final_gate_result.json`，若存在
- `project_state/gates/round_baseline.json`
- `project_state/gates/round_delta_summary.json`
- `project_state/rounds/round_20260613_training_queue_static_triage_hygiene_v1/round_manifest.json`
- `project_state/rounds/round_20260613_training_queue_static_triage_hygiene_v1/codex_execution_report.md`
- `project_state/rounds/round_20260613_training_queue_static_triage_hygiene_v1/pytest_result.txt`
- `project_state/local_reverse_training_status.json`，只读核验
- `project_state/local_reverse_evaluation_queue.json`，只读核验
- `reverse_agent/project_gate.py`
- `reverse_agent/project_state.py`
- `tests/test_project_gate.py`
- `tests/test_project_state.py`
- `tests/test_local_reverse_training_status.py`，只用于验证上一轮行为仍被测试覆盖，不允许改训练语义

## 5. Required Audit

Codex 必须先确认：

- 当前 decision_meta 合法，`status=APPROVED`，`mainline=engineering_branch`，`skill_profiles` 来自 active registry。
- `task_packet.json/current_state.json` 是旧 `samplereverse` 背景；当前执行权威是本 decision。
- 上一轮训练队列实现本身已经审计通过但带 metadata 限制；本轮只处理 metadata/command ordering，不处理训练逻辑。
- 当前 `codex_execution_report.md`、`pytest_result.txt`、`gates/*.json`、上一轮 round archive 是否存在 report/test/generated_artifacts 不一致，特别是：report summary 是否遗漏实际执行命令，pytest header 是否遗漏实际执行命令，generated_artifacts/verified_artifacts 是否遗漏本轮实际生成或验证文件。
- `project_state/local_reverse_training_status.json` 与 `project_state/local_reverse_evaluation_queue.json` 当前仍满足：`affineenc_333f8ca9` 为 `needs_triage` 且 queue_rank=None，`ascii_table_chinese_46efc7ea` queue_rank=None，`cpp1_2f6fcb63` queue_rank=1。此核验必须只读，不得重跑 static triage。

必须完成或如实报告：

- 生成本轮新的 `project_state/codex_execution_report.md`，顶部包含合法 `codex_report_summary`，`based_on_decision_id=decision_20260613_report_metadata_hygiene_v1`，`round_id=round_20260613_report_metadata_hygiene_v1`。
- `codex_report_summary.tests_ran` 必须完整列出本轮实际执行的所有命令，包含 targeted pytest、只读 queue/status verification、doctor、lint-report、report-summary、final-check、close-round。不得遗漏 close-round 前的任何验证命令。
- `codex_report_summary.generated_artifacts` 必须只列出本轮真实生成/更新的文件；如果没有更新训练状态/队列，就不得把它们列为 generated_artifacts。
- `codex_report_summary.verified_artifacts` 应列出本轮只读验证过的状态文件和 gate/round 文件。
- `project_state/pytest_result.txt` 顶部 `pytest_result_summary.tests_ran` 必须与本轮实际命令一致，并包含每条命令的 stdout/stderr 摘要和退出码。
- 所有本轮测试、只读核验、doctor/lint/report-summary/final-check 必须发生在 close-round 之前；close-round 应是本轮最后一个 state-closing 命令。
- close-round 后不得追加测试记录。如需补充测试，必须重新生成 report/pytest/gates 并重新 close-round。

若发现当前 project_gate 无法表达或校验完整命令记录，允许对 `reverse_agent/project_gate.py` 做最小修正，并为该修正添加 `tests/test_project_gate.py` 回归测试。除此之外，不得改工程源码。

## 6. Implementation Scope

Allowed source changes only if required for metadata consistency gate behavior:

- `reverse_agent/project_gate.py`
- `reverse_agent/project_state.py`
- `tests/test_project_gate.py`
- `tests/test_project_state.py`

Allowed generated/state files:

- `project_state/codex_execution_report.md`
- `project_state/pytest_result.txt`
- `project_state/gates/command_plan.json`
- `project_state/gates/preflight_result.json`
- `project_state/gates/report_summary_synthesis.json`
- `project_state/gates/final_gate_result.json`
- `project_state/gates/round_baseline.json`
- `project_state/gates/round_delta_summary.json`
- `project_state/rounds/round_20260613_report_metadata_hygiene_v1/*`

Read-only verification only:

- `project_state/local_reverse_training_status.json`
- `project_state/local_reverse_evaluation_queue.json`
- `tests/test_local_reverse_training_status.py`

Forbidden:

- `reverse_agent/local_reverse_training_status.py`
- `reverse_agent/local_reverse_single_sample_static_triage.py`
- solver、harness、runtime probe、debugger、emulator、IDA/Ghidra 接口相关代码
- `reverse_agent/strategies/`
- `reverse_agent/transforms/`
- `.codex-skills/`
- `training_materials/`
- `solve_reports/`
- raw sample 文件
- `project_state/local_reverse_affineenc_333f8ca9_static_triage.json` 语义字段
- `project_state/local_reverse_affine_8cfebe03_static_evidence_summary.json` 语义字段
- `project_state/local_reverse_training_status.json` 与 `project_state/local_reverse_evaluation_queue.json` 的手工语义修补

## 7. Tests

必须运行并记录，且所有命令必须在 `close-round` 前完成，除非命令本身就是 `close-round`：

- `Get-Location`
- `Test-Path F:\reverse-agent`
- `git status --short`
- `python -m reverse_agent.project_gate preflight --state-dir project_state`
- `python -m reverse_agent.project_gate command-plan --state-dir project_state`
- `python -m pytest tests/test_project_state.py tests/test_project_gate.py -q`
- `python -m pytest tests/test_local_reverse_training_status.py -q`
- 只读 queue/status verification：用 Python 读取 `project_state/local_reverse_training_status.json` 与 `project_state/local_reverse_evaluation_queue.json`，确认 `affineenc_333f8ca9 needs_triage known_candidate='' queue_rank=None`、`ascii_table_chinese_46efc7ea queue_rank=None`、`cpp1_2f6fcb63 queue_rank=1`，不得写入文件
- `python -m reverse_agent.project_state doctor --state-dir project_state`
- `python -m reverse_agent.project_state lint-report --state-dir project_state`
- `python -m reverse_agent.project_gate report-summary --state-dir project_state`
- `python -m reverse_agent.project_gate final-check --state-dir project_state`
- `python -m reverse_agent.project_gate close-round --state-dir project_state --round-id round_20260613_report_metadata_hygiene_v1`

`project_state/pytest_result.txt` 必须包含本轮 `decision_20260613_report_metadata_hygiene_v1`、`round_20260613_report_metadata_hygiene_v1`、真实命令、退出码和最终结果。

`project_state/codex_execution_report.md` 顶部必须包含合法 `codex_report_summary`，其中 `based_on_decision_id=decision_20260613_report_metadata_hygiene_v1`，`round_id=round_20260613_report_metadata_hygiene_v1`，并列出实际 files_changed、tests_ran、generated_artifacts、verified_artifacts。

如果修改了 `reverse_agent/project_gate.py` 或 `reverse_agent/project_state.py`，必须增加或更新对应 pytest，并在 report 中说明为何仅靠 state/report 文件无法完成 metadata hygiene。

## 8. Stop Conditions

如果需要运行 IDA/static triage、Ghidra、solver、runtime validation、debugger、emulator、hook、harness campaign，停止并报告 BLOCKED。

如果需要推进 `cpp1_2f6fcb63` 的实际样本分析、生成 candidate、写 flag/password、或改变任何样本 solved/blocked/needs_triage 语义，停止并报告 BLOCKED。

如果需要修改 `.codex-skills/`、training materials、solve_reports 历史目录或 raw sample 文件，停止。

如果发现上一轮训练状态/队列已经不满足审计通过条件，停止并报告 REWORK_REQUIRED，不要在本轮手工修补训练队列。

如果 gate/report/archive 出现 FAIL，`codex_execution_report.md` 必须标记 FAILED/REWORK_REQUIRED 或 BLOCKED，不能写 SUCCESS/ACCEPTED。

如果 close-round 后又发现漏测或漏记命令，必须重新生成本轮 report/pytest/gates 并重新 close-round，不能在已归档状态后追加未归档记录。
