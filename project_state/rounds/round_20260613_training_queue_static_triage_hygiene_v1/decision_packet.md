```json decision_meta
{
  "schema_version": 1,
  "decision_id": "decision_20260613_training_queue_static_triage_hygiene_v1",
  "round_id": "round_20260613_training_queue_static_triage_hygiene_v1",
  "based_on_state_build_id": "state_20260613_054156_2729a02c7407",
  "based_on_state_digest": "2729a02c7407808c057a8a3f3e1d414797d660957dbe80b6c0780ffe6ec6bac9",
  "status": "APPROVED",
  "mainline": "training_dataset",
  "skill_profiles": ["reverse-agent-iteration@v2"]
}
```

# DECISION_PACKET

## 1. Goal

修复本地训练集 evaluation queue 的状态卫生问题：已经完成 static triage 的样本不应继续排在 `static_triage` 队列前列，非逆向题样本/支持文档不应被排入可执行样本 triage 队列。目标是让训练状态和队列可重复生成，并把下一个真正可执行 PE 样本选出来，但本轮不运行任何新的 static triage、IDA、solver、runtime 或 harness。

本轮明确不重复之前已经做过的训练任务：不重跑 `affine_8cfebe03` static evidence classification，不重跑 `affineenc_333f8ca9` static triage，不继续 gate closeout，不处理 solved/blocked 样本结论，不批量跑 inventory_only 样本。

## 2. Current Evidence

当前主线为 `training_dataset`，因为本轮目标是训练集 metadata、training_status、evaluation_queue 的可重复生成与队列筛选规则，不是 reverse_solving、tool_integration 内容推进或 gate 框架返工。

`project_state/decision_packet.md` 是当前轮执行权威。`project_state/task_packet.json` 和 `project_state/current_state.json` 仍是旧 `samplereverse` sample_state，只能作为背景，不能覆盖本 decision。不得根据 `task_packet.task=collect_missing_evidence` 回到旧 `samplereverse` 求解线。

最近完成的 `decision_20260613_tool_integration_artifact_policy_closeout_v1` 已 ACCEPTED_WITH_LIMITATIONS：gate/status policy closeout 完成，report-summary PASSED，final-check PASSED_WITH_LIMITATIONS，close-round 已归档。该线已经结束，本轮不得继续修改 gate，除非训练队列 gate 记录直接阻塞。

`project_state/local_reverse_training_status.json` 当前显示总样本 65：solved 1，blocked 2，needs_triage 2，inventory_only 60。已完成或已有状态的样本包括：`cpp1_bcbd9979` solved，`cpp2_4c69f173` blocked，`sha_256_18019fca` blocked，两个 `affine_8cfebe03` 为 needs_triage，`affineenc_333f8ca9` 为 needs_triage 且 known_candidate 为空。

`project_state/artifact_index.json` 中 `local_reverse_affineenc_333f8ca9_static_triage` freshness 为 current，kind 为 `local_reverse_single_sample_static_triage`，source_run 为 `round_20260613_affineenc_static_triage_v1`。这说明 `affineenc_333f8ca9` 已经有 current static triage 证据，不能再次排入 static_triage 执行队列。

`project_state/local_reverse_evaluation_queue.json` 当前存在两个明显卫生问题：rank 1 仍是 `affineenc_333f8ca9`，但该条已经 `static_triage_completed=true`；rank 2 是 `ascii_table_chinese_46efc7ea`，relative_path 为 `ascii_table_chinese.pdf`，这不是 PE 可执行逆向题，不应作为当前 static triage 的优先样本。rank 3 是 `cpp1_2f6fcb63`，relative_path 为 `逆向课程2023春01/CPP1.exe`，是下一个更合理的 PE static_triage 候选。

`reverse_agent/local_reverse_training_status.py` 当前 `_build_evaluation_queue()` 注释称队列来自 unsolved inventory_only samples，但实际队列文件仍包含已 static_triage_completed 的 `affineenc_333f8ca9`；同时筛选只跳过 solver/script/decrypt/encrypt/interactive 等关键词，没有明确排除 PDF/文档/非 PE 非源码挑战。该逻辑需要最小修正并配套测试。

现有相关能力必须优先复用：`reverse_agent/local_reverse_training_status.py` 的 `build_training_status()` 和 `_build_evaluation_queue()`，现有 inventory/status/queue JSON，project_gate/report/round 机制。不得新建重复 inventory/queue 系统。

涉及逆向工具边界：本轮不运行 IDA/Ghidra/static triage，不运行 solver、runtime probe、debugger、emulator、hook、harness campaign，不生成 candidate。只允许读取已有 static triage artifact 来确保队列排除规则正确。

允许读取重型 artifact：不允许读取完整 `solve_reports/` 或完整 `PROJECT_PROGRESS_LOG.txt`。只允许读取本轮直接相关的 project_state 文件、local_reverse_training_status 源码、相关测试和已有 `affineenc/affine` 静态 artifact 摘要。

`negative_results.json` 中禁止回到旧 sample_solver 盲搜、只扩大 beam/budget、使用 compare_semantics_agree=false 作为主 frontier、提交完整 solve_reports、重复旧 samplereverse 失败方向。本轮不触碰这些方向。

## 3. Do Not Do

不得运行或重跑 `affineenc_333f8ca9` static triage、IDA static extraction、forced IDA、xref extraction。

不得重复 `affine_8cfebe03` 的 static evidence classification、static tool blocker/state closure、audit closure 或任何旧训练任务。

不得运行 solver、bruteforce、guided_pool、sample_solver、SMT、runtime validation、debugger、emulator、hook、harness campaign。

不得生成 candidate、flag、password；不得把任何新样本标成 solved。

不得处理 evaluation queue rank 3 `cpp1_2f6fcb63` 的实际 static triage。本轮最多只能把它作为下一候选写入队列，不能分析它。

不得批量跑 60 个 inventory_only 样本，不得读取完整 `solve_reports/` 或完整 `PROJECT_PROGRESS_LOG.txt`，不得提交完整 solve_reports。

不得修改 `.codex-skills/`、training materials、raw sample 文件。

不得改写 `project_state/local_reverse_affineenc_333f8ca9_static_triage.json`、`project_state/local_reverse_affine_8cfebe03_static_evidence_summary.json` 的语义字段。

不得修改 `cpp1_bcbd9979` solved、`cpp2_4c69f173` blocked、`sha_256_18019fca` blocked、`affine_8cfebe03` needs_triage、`affineenc_333f8ca9` needs_triage 的既有结论，除非只是由可重复 queue/status 生成器重写等价字段且语义不变。

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

- `project_state/local_reverse_training_status.json`
- `project_state/local_reverse_evaluation_queue.json`
- `project_state/local_reverse_inventory.json`
- `project_state/local_reverse_affineenc_333f8ca9_static_triage.json`，仅用于确认已经 static triage，不得重跑
- `project_state/local_reverse_affine_8cfebe03_static_evidence_summary.json`，仅用于确认不重复旧任务
- `reverse_agent/local_reverse_training_status.py`
- 与 local_reverse_training_status、project_state/project_gate 直接相关的测试；若缺少训练队列测试，允许新增最小单元测试

## 5. Required Audit

Codex 必须先确认：

- 当前 decision_meta 合法，`status=APPROVED`，`mainline=training_dataset`，`skill_profiles` 来自 active registry。
- `task_packet.json/current_state.json` 是旧 `samplereverse` 背景；当前执行权威是本 decision。
- `affineenc_333f8ca9` 已有 current static triage artifact，且 training_status 为 needs_triage，known_candidate 为空，未 solved。
- 当前 queue rank 1 已 static_triage_completed，不应继续作为 static_triage 待执行项。
- 当前 queue rank 2 是 PDF 文档，不应优先作为 PE/static triage 训练样本。
- `cpp1_2f6fcb63` 是下一个合理 PE 候选，但本轮只允许调整队列，不允许 triage 它。

必须完成或如实报告：

- 最小修改 `reverse_agent/local_reverse_training_status.py`，使 successful current `local_reverse_single_sample_static_triage` artifact 可稳定映射为 training_status `needs_triage`，不会在重新生成状态时回退为 `inventory_only`。
- `_build_evaluation_queue()` 必须排除已 solved、blocked、needs_triage、static_triage_completed 或已有 current static triage evidence 的样本；也必须排除 PDF、文档、支持文件、solver/helper 脚本等非目标训练样本。
- 重新生成 `project_state/local_reverse_training_status.json` 与 `project_state/local_reverse_evaluation_queue.json`。结果应保留 `affineenc_333f8ca9` 为 needs_triage、known_candidate 为空、not solved，并从 static_triage 队列中移除。
- 队列下一候选应优先选择未处理的 PE 样本；若 `cpp1_2f6fcb63` 因规则成为 rank 1，需要在 report 中记录它只是下一候选，未执行 static triage。
- 若发现队列生成逻辑需要更大重构，停止并报告 REWORK_REQUIRED，不要临时手写 queue JSON 掩盖生成器问题。

## 6. Implementation Scope

Allowed

- `reverse_agent/local_reverse_training_status.py`
- 与 local_reverse_training_status 直接相关的测试文件；若无现有文件，允许新增 `tests/test_local_reverse_training_status.py`
- `project_state/local_reverse_training_status.json`
- `project_state/local_reverse_evaluation_queue.json`
- `project_state/codex_execution_report.md`
- `project_state/pytest_result.txt`
- `project_state/gates/*.json`
- `project_state/rounds/round_20260613_training_queue_static_triage_hygiene_v1/*`

Allowed only if required for gate/report consistency, without changing sample evidence semantics:

- `project_state/artifact_index.json`
- `reverse_agent/project_gate.py`
- `tests/test_project_gate.py`

禁止

- `project_state/local_reverse_affineenc_333f8ca9_static_triage.json` semantic fields
- `project_state/local_reverse_affine_8cfebe03_static_evidence_summary.json` semantic fields
- solver、harness、debugger、emulator、runtime probe、candidate validation 相关代码
- `reverse_agent/strategies/`、`reverse_agent/transforms/`、IDA/Ghidra/debugger 新接口
- `.codex-skills/`
- `training_materials/`
- `solve_reports/`
- raw sample 文件
- queue rank 1/2/3 的实际 static triage 或任何样本求解动作

## 7. Tests

必须运行并记录：

- `Get-Location`
- `Test-Path F:\reverse-agent`
- `git status --short`
- `python -m reverse_agent.project_gate preflight --state-dir project_state`
- `python -m reverse_agent.project_gate command-plan --state-dir project_state`
- targeted pytest for local_reverse_training_status queue hygiene：至少覆盖 successful static triage artifact keeps sample needs_triage、static_triage_completed/current evidence 不进入 queue、PDF/support docs 不进入 queue、next PE candidate appears before non-target samples
- `python -m pytest tests/test_project_state.py tests/test_project_gate.py -q`
- 运行训练状态生成命令：`python -m reverse_agent.local_reverse_training_status --inventory project_state/local_reverse_inventory.json --artifact-index project_state/artifact_index.json --out project_state/local_reverse_training_status.json --queue-out project_state/local_reverse_evaluation_queue.json`，若实际 CLI 参数不同，使用项目实际等价命令并记录
- queue/status 核验：`affineenc_333f8ca9` remains needs_triage, known_candidate empty, not solved；`ascii_table_chinese_46efc7ea` 不在可执行 PE static triage 队列前列；下一个 PE 候选被明确记录
- `python -m reverse_agent.project_state doctor --state-dir project_state`
- `python -m reverse_agent.project_state lint-report --state-dir project_state`
- `python -m reverse_agent.project_gate report-summary --state-dir project_state`
- `python -m reverse_agent.project_gate final-check --state-dir project_state`
- `python -m reverse_agent.project_gate close-round --state-dir project_state --round-id round_20260613_training_queue_static_triage_hygiene_v1`

`project_state/pytest_result.txt` 必须包含本轮 `decision_20260613_training_queue_static_triage_hygiene_v1`、`round_20260613_training_queue_static_triage_hygiene_v1`、真实命令、退出码和最终结果。

`project_state/codex_execution_report.md` 顶部必须包含合法 `codex_report_summary`，其中 `based_on_decision_id=decision_20260613_training_queue_static_triage_hygiene_v1`，`round_id=round_20260613_training_queue_static_triage_hygiene_v1`，并列出实际 files_changed、tests_ran、generated_artifacts。

## 8. Stop Conditions

如果需要运行 IDA/static triage、solver、runtime validation、debugger、emulator、hook、harness campaign，停止并报告 BLOCKED。

如果需要修改 `.codex-skills/`、training materials、solve_reports 历史目录或 raw sample 文件，停止。

如果需要把任何新样本标成 solved、写入 candidate、或继续做约束恢复/运行时验证，停止。

如果无法通过生成器稳定重建 training_status/evaluation_queue，只能手工 patch JSON，停止并报告 REWORK_REQUIRED。

如果 queue hygiene 修复会改变已 solved/blocked/needs_triage 样本语义，停止并报告 REWORK_REQUIRED。

如果 gate/report/archive 出现 FAIL，`codex_execution_report.md` 必须标记 FAILED/REWORK_REQUIRED 或 BLOCKED，不能写 SUCCESS/ACCEPTED。
