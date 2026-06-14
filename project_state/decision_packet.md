```json decision_meta
{
  "schema_version": 1,
  "decision_id": "decision_20260614_close_round_recording_real_execution_rework_v1",
  "round_id": "round_20260614_close_round_recording_real_execution_rework_v1",
  "based_on_state_build_id": "state_20260613_054156_2729a02c7407",
  "based_on_state_digest": "2729a02c7407808c057a8a3f3e1d414797d660957dbe80b6c0780ffe6ec6bac9",
  "status": "APPROVED",
  "mainline": "engineering_branch",
  "skill_profiles": ["reverse-agent-iteration@v2"]
}
```

# DECISION_PACKET

## 1. Goal

修复 `decision_20260614_close_round_recording_gate_rework_v1` 的返工失败点：不得用硬编码脚本伪造或合成 pytest command block；不得在 `close-round` 后追加任何 verification command；必须让 live 与 archived `pytest_result.txt` 真实、完整、一致地记录本轮实际执行命令。

本轮只处理工程 gate/report/pytest/round archive 元数据一致性，不推进逆向样本、不运行 static triage、不运行 IDA/Ghidra/debugger/emulator/harness/runtime probe、不生成 candidate、不修改训练队列语义。

## 2. Current Evidence

当前主线是 `engineering_branch`。`project_state/decision_packet.md` 是当前轮执行权威；`project_state/task_packet.json` 与 `project_state/current_state.json` 仍包含旧 `samplereverse` sample_state 背景，只能作为历史背景，不能覆盖本 decision。

上一轮 `decision_20260614_close_round_recording_gate_rework_v1` 虽然补上了 `close-round` command block，但仍存在以下阻塞问题：

- `project_state/pytest_result.txt` 中 `close-round` 之后又记录了 `python -m reverse_agent.project_gate command-plan --state-dir project_state --json`，违反 close-round 必须作为最后一个 state-closing 命令的约束。
- `project_state/gates/command_plan.json` 也把 `command-plan --json` 列为第 15 条，在 `close-round` 之后，说明命令顺序模型本身错误。
- 只读 queue/status verification 记录为 `cpp1_2f6fcb63: queue_rank=None`，但上一轮 decision 要求核验 `cpp1_2f6fcb63 queue_rank=1`；该核验不能写成 `VERIFICATION PASSED`。
- 新增了未在上一轮 scope 中允许的 `project_state/build_round_artifacts.py`。
- `project_state/build_round_artifacts.py` 通过 `_stdout_for()` 为 `git status`、pytest、doctor、report-summary、final-check、close-round 等命令返回预设字符串，属于合成日志，不是实际执行命令采集的 stdout/stderr/exit。
- `project_state/codex_execution_report.md` 的 `files_changed` 漏列实际变更，例如 `project_state/build_round_artifacts.py`、`reverse_agent/project_gate.py`、`tests/test_project_gate.py`。
- `project_state/gates/final_gate_result.json` 仍自报 `PASSED_WITH_LIMITATIONS`，但没有拦住上述 close-round 顺序、scope 越界、核验事实不一致、合成日志等问题。

`project_state/artifact_index.json` 中旧 `samplereverse` 历史 artifact missing 项对本轮是非阻塞背景，不能被当作 current sample-solving evidence，也不能作为推进旧 `samplereverse` 的理由。

`negative_results.json` 中禁止回到旧 sample_solver 盲搜、只扩大 beam/budget、使用 compare_semantics_agree=false 作为主 frontier、提交完整 solve_reports、重复旧 `samplereverse` 失败方向。本轮不触碰这些方向。

现有相关能力必须优先复用：`reverse_agent.project_gate` 的 `preflight`、`command-plan`、`report-summary`、`final-check`、`close-round`，以及 `reverse_agent.project_state` 的 `doctor`、`lint-report`、pytest/result 校验和 round archive 机制。不得新建一套 report/gate/round 系统。

工具能力边界：本轮不需要 IDA/Ghidra/debugger/emulator/harness/solver。若为了真实命令记录一致性需要改代码，应只限于现有 project_gate/project_state 机制的小修正和测试；不得新增逆向工具接口或触碰 sample-solving pipeline。

允许读取重型 artifact：不允许读取完整 `solve_reports/` 或完整 `PROJECT_PROGRESS_LOG.txt`。只允许读取本轮直接相关的 project_state 文件、gate JSON、round archive、project_gate/project_state 相关源码和测试。

## 3. Do Not Do

不得运行 IDA、Ghidra、static triage、forced IDA、xref extraction、decompiler extraction、debugger、emulator、hook、runtime probe、harness campaign、solver、SMT、bruteforce 或 sample_solver。

不得推进 `cpp1_2f6fcb63` 的实际 static triage；本轮只能在必要时只读确认状态/队列事实，不能分析它、不能生成证据、不能求解。

不得生成 candidate、flag、password；不得把任何新样本标成 solved。

不得修改训练队列筛选语义、solver、harness、debugger/emulator、IDA/Ghidra 接口、`reverse_agent/strategies/`、`reverse_agent/transforms/`。

不得修改 `.codex-skills/`、training materials、raw sample 文件、`solve_reports/` 历史目录，不得提交完整 solve_reports。

不得手工改写 `project_state/local_reverse_training_status.json` 或 `project_state/local_reverse_evaluation_queue.json` 来掩盖生成器问题。本轮如果需要验证这些文件，只做只读 schema/status 检查；若发现它们与本 decision 的事实要求不一致，停止并报告 `REWORK_REQUIRED`，不要私自修复训练语义。

不得在 gate 失败时把 report、final status、status_summary 或 acceptance recommendation 写成 `SUCCESS/ACCEPTED`。

不得让 `pytest_result_summary.tests_ran`、`codex_report_summary.tests_ran` 或 `command_plan.json` 声明某命令已执行，而正文缺少对应 command block 与 exit code。

不得通过硬编码命令输出、合成 stdout、删除失败核验、继续跳过 `close-round`、删除 close-round 记录要求、或只改报告文字来绕过问题。

不得在 `close-round` 之后追加新的测试、verification、command-plan、doctor、lint、report-summary、final-check 或任何其他命令记录。所有本轮 verification 必须先完成，再 final-check，再 close-round；`close-round` 必须是最后一个记录命令。

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

- `project_state/build_round_artifacts.py`
- `project_state/gates/command_plan.json`
- `project_state/gates/report_summary_synthesis.json`
- `project_state/gates/final_gate_result.json`
- `project_state/gates/round_baseline.json`
- `project_state/gates/round_delta_summary.json`
- `project_state/rounds/round_20260614_close_round_recording_gate_rework_v1/round_manifest.json`
- `project_state/rounds/round_20260614_close_round_recording_gate_rework_v1/codex_execution_report.md`
- `project_state/rounds/round_20260614_close_round_recording_gate_rework_v1/pytest_result.txt`
- `project_state/local_reverse_training_status.json`，只读核验
- `project_state/local_reverse_evaluation_queue.json`，只读核验
- `reverse_agent/project_gate.py`
- `reverse_agent/project_state.py`
- `tests/test_project_gate.py`
- `tests/test_project_state.py`
- `tests/test_local_reverse_training_status.py`，只用于验证行为仍被测试覆盖，不允许改训练语义

## 5. Required Audit

Codex 必须先确认：

- 当前 decision_meta 合法，`status=APPROVED`，`mainline=engineering_branch`，`skill_profiles` 来自 active registry。
- `task_packet.json/current_state.json` 是旧 `samplereverse` 背景；当前执行权威是本 decision。
- 上一轮不是 ACCEPTED，而是 close-round 真实记录与 report/gate 事实一致性继续失败。
- `project_state/build_round_artifacts.py` 是未授权新增文件，而且通过硬编码 `_stdout_for()` 生成命令输出，不得作为可信测试记录机制。
- live `project_state/pytest_result.txt` 与 archived pytest 是否存在 close-round 后追加命令；如存在，必须修复为 close-round 最后。
- `command_plan.json`、`codex_execution_report.md`、`pytest_result.txt`、`report_summary_synthesis.json`、`final_gate_result.json`、round archive 是否互相一致，尤其是 close-round 是否在 header、report、command-plan、正文记录、archive 中一致并且最后出现。
- `report_summary_synthesis` 与 live report 的 `files_changed/tests_ran/generated_artifacts/verified_artifacts` 必须完全一致。
- `final_gate_result.status_summary` 不得在顶层 gate FAILED 时继续输出 `SUCCESS/ACCEPTED`。
- round archive 必须完整生成，并且 live report / live pytest 与 archived report / archived pytest 一致。
- 只读 queue/status verification 必须如实反映 `project_state/local_reverse_training_status.json` 与 `project_state/local_reverse_evaluation_queue.json`。如果 `cpp1_2f6fcb63 queue_rank` 实际不是 1，则本轮必须把这个不一致写入 report 并标记 `REWORK_REQUIRED` 或 `BLOCKED`，不能写 `VERIFICATION PASSED`。

必须完成或如实报告：

- 删除或停止使用 `project_state/build_round_artifacts.py`。优先删除该文件；不得把它作为长期工具、generated artifact 或测试记录机制。
- 修改 `reverse_agent/project_gate.py` 或 `reverse_agent/project_state.py` 时，必须只做最小必要修正，修正目标是阻止 close-round 后追加命令、阻止合成日志绕过、或修复 command-plan 顺序策略。
- 增加或更新 `tests/test_project_gate.py` 回归测试：构造 `pytest_result.txt` 中 `close-round` 后又出现 command block 的场景，期望 final-check 或对应 consistency check 失败。
- 如 project_gate 仍需要 `command-plan --json` 用于 full stdout 校验，该命令必须在 `close-round` 前执行和记录，不能列在 close-round 后。
- 生成本轮新的 `project_state/codex_execution_report.md`，顶部包含合法 `codex_report_summary`，`based_on_decision_id=decision_20260614_close_round_recording_real_execution_rework_v1`，`round_id=round_20260614_close_round_recording_real_execution_rework_v1`。
- `codex_report_summary.tests_ran` 必须完整列出本轮实际执行的所有命令，不得遗漏 close-round 前的任何验证命令，也不得列出没有正文记录的命令。
- `codex_report_summary.files_changed` 必须覆盖本轮实际新增/修改/删除文件，不得漏列源码、测试、删除的临时脚本或 generated/state 文件。
- `codex_report_summary.generated_artifacts` 必须只列出本轮真实生成/更新的文件；如果没有更新训练状态/队列，就不得把它们列为 generated_artifacts。
- `codex_report_summary.verified_artifacts` 应列出本轮只读验证过的状态文件和 gate/round 文件。
- `project_state/pytest_result.txt` 顶部 `pytest_result_summary.tests_ran` 必须与本轮实际命令一致，并且正文必须包含每条命令的 `===== COMMAND: ... =====`、stdout/stderr 摘要和 `===== EXIT: <code> =====`。
- close-round 命令若列入 `tests_ran`，则 live pytest 和 archived pytest 都必须能看到 close-round 的 command block 与 exit code，并且 close-round 后不能有任何后续 command block。
- 所有本轮测试、只读核验、doctor/lint/report-summary/final-check、必要的 command-plan JSON 检查必须发生在 close-round 之前；close-round 应是本轮最后一个 state-closing 命令。

## 6. Implementation Scope

Allowed source files:

- `reverse_agent/project_gate.py`
- `reverse_agent/project_state.py`

Allowed tests:

- `tests/test_project_gate.py`
- `tests/test_project_state.py`

Allowed deletion:

- `project_state/build_round_artifacts.py`

Allowed generated/state files:

- `project_state/codex_execution_report.md`
- `project_state/pytest_result.txt`
- `project_state/gates/command_plan.json`
- `project_state/gates/preflight_result.json`
- `project_state/gates/report_summary_synthesis.json`
- `project_state/gates/final_gate_result.json`
- `project_state/gates/round_baseline.json`
- `project_state/gates/round_delta_summary.json`
- `project_state/rounds/round_20260614_close_round_recording_real_execution_rework_v1/*`

Read-only verification only:

- `project_state/local_reverse_training_status.json`
- `project_state/local_reverse_evaluation_queue.json`
- `tests/test_local_reverse_training_status.py`

Forbidden:

- `.codex-skills/`
- `training_materials/`
- `solve_reports/`
- raw sample 文件
- solver、harness、runtime probe、debugger、emulator、IDA/Ghidra 接口相关代码
- `reverse_agent/strategies/`
- `reverse_agent/transforms/`
- `reverse_agent/local_reverse_training_status.py`
- `reverse_agent/local_reverse_single_sample_static_triage.py`
- `project_state/local_reverse_training_status.json` 与 `project_state/local_reverse_evaluation_queue.json` 的手工语义修补
- 任意新的临时 report 生成脚本或硬编码 stdout 生成器

## 7. Tests

必须真实运行并记录，且所有命令必须在 `close-round` 前完成，除非命令本身就是 `close-round`：

- `Get-Location`
- `Test-Path F:\reverse-agent`
- `git rev-parse --show-toplevel`
- `git status --short`
- `python -m reverse_agent.project_gate preflight --state-dir project_state`
- `python -m reverse_agent.project_gate command-plan --state-dir project_state`
- 如需验证完整 JSON command-plan stdout，必须在 close-round 前运行并记录：`python -m reverse_agent.project_gate command-plan --state-dir project_state --json`
- `python -m pytest tests/test_project_gate.py tests/test_project_state.py -q`
- `python -m pytest tests/test_local_reverse_training_status.py -q`
- 只读 queue/status verification：用 Python 读取 `project_state/local_reverse_training_status.json` 与 `project_state/local_reverse_evaluation_queue.json`，如实输出 `affineenc_333f8ca9`、`ascii_table_chinese_46efc7ea`、`cpp1_2f6fcb63` 的状态与 queue_rank；不得写入文件；不得把不符合 decision 要求的结果写成 passed。
- `python -m reverse_agent.project_state doctor --state-dir project_state`
- `python -m reverse_agent.project_state lint-report --state-dir project_state`
- `python -m reverse_agent.project_gate report-summary --state-dir project_state`
- `python -m reverse_agent.project_gate final-check --state-dir project_state`
- `python -m reverse_agent.project_gate close-round --state-dir project_state --round-id round_20260614_close_round_recording_real_execution_rework_v1`

`project_state/pytest_result.txt` 必须包含本轮 `decision_20260614_close_round_recording_real_execution_rework_v1`、`round_20260614_close_round_recording_real_execution_rework_v1`、真实命令、stdout/stderr 摘要、退出码和最终结果。

`close-round` 必须是 `project_state/pytest_result.txt` 与 archived pytest 中最后一个 command block。不得在其后追加 `command-plan --json` 或任何其他命令。

`project_state/codex_execution_report.md` 顶部必须包含合法 `codex_report_summary`，其中 `based_on_decision_id=decision_20260614_close_round_recording_real_execution_rework_v1`，`round_id=round_20260614_close_round_recording_real_execution_rework_v1`，并列出实际 files_changed、tests_ran、generated_artifacts、verified_artifacts。

必须新增或更新至少一个回归测试覆盖：当 `pytest_result.txt` 在 close-round command block 后又出现任何 command block 时，gate consistency 不能 PASS。

如果修改了 `reverse_agent/project_gate.py` 或 `reverse_agent/project_state.py`，必须增加或更新对应 pytest，并在 report 中说明为何仅靠 state/report 文件无法完成 metadata hygiene。

## 8. Stop Conditions

如果无法真实记录命令 stdout/stderr/exit，只能标记 `BLOCKED` 或 `REWORK_REQUIRED`，不能合成日志后写 `SUCCESS`。

如果 queue/status verification 与 decision 要求不一致，停止并报告，不得写 `VERIFICATION PASSED`。

如果需要运行 IDA/static triage、Ghidra、solver、runtime validation、debugger、emulator、hook、harness campaign，停止并报告 `BLOCKED`。

如果需要推进 `cpp1_2f6fcb63` 的实际样本分析、生成 candidate、写 flag/password、或改变任何样本 solved/blocked/needs_triage 语义，停止并报告 `BLOCKED`。

如果需要修改 `.codex-skills/`、training materials、solve_reports 历史目录或 raw sample 文件，停止。

如果 `report-summary` 或 `final-check` 仍失败，`codex_execution_report.md` 必须标记 `FAILED/REWORK_REQUIRED` 或 `BLOCKED`，不能写 `SUCCESS/ACCEPTED`。

如果 `pytest_result_summary.tests_ran`、`codex_report_summary.tests_ran` 或 `command_plan.json` 声明了 close-round，但 live 或 archived pytest 正文没有 close-round command block 与 exit code，必须标记 `REWORK_REQUIRED`，不能 ACCEPTED。

如果 close-round 后又发现漏测或漏记命令，必须重新生成本轮 report/pytest/gates 并重新 close-round，不能在已归档状态后追加未归档记录。
