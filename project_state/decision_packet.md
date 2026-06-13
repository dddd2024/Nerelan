```json decision_meta
{
  "schema_version": 1,
  "decision_id": "decision_20260613_affineenc_static_triage_v1",
  "round_id": "round_20260613_affineenc_static_triage_v1",
  "based_on_state_build_id": "state_20260613_054156_2729a02c7407",
  "based_on_state_digest": "2729a02c7407808c057a8a3f3e1d414797d660957dbe80b6c0780ffe6ec6bac9",
  "status": "APPROVED",
  "mainline": "tool_integration",
  "skill_profiles": ["reverse-agent-iteration@v2"]
}
```

# DECISION_PACKET

## 1. Goal

对训练评估队列 rank 1 的新样本 `affineenc_333f8ca9` 做一次有界静态 triage，并把成熟工具输出登记成当前证据。本轮不求解、不生成 candidate、不做 runtime/debugger/harness，只验证现有 IDA/static triage 工具链能否对该 inventory-only 样本产生可审计的静态证据。

本轮明确不重复已经做过的训练任务：不再处理 `affine_8cfebe03` 的 static evidence classification，不再做 `affine_8cfebe03` static tool blocker/state closure，不再继续 gate closure framework fix，也不重复 `cpp1_bcbd9979` solved 样本、`cpp2_4c69f173` blocked 样本或 `sha_256_18019fca` blocked 样本的既有训练结论。

## 2. Current Evidence

当前主线为 `tool_integration`，原因是本轮目标是复用现有静态分析工具接口，导出并登记 `affineenc_333f8ca9` 的工具证据，而不是直接求解样本，也不是做训练集批量评估。

`project_state/decision_packet.md` 是当前轮执行权威。`project_state/task_packet.json` 和 `project_state/current_state.json` 仍是旧 `samplereverse` sample_state，只能作为背景，不能覆盖本 decision。不得根据 `task_packet.task=collect_missing_evidence` 回到旧 `samplereverse` 求解线。

最新已完成 round 是 `decision_20260613_gate_closure_framework_fix_v1`，该 round 修复了 report-summary/final-check/close-round/archive 闭环，302 个 project gate/state 测试通过，close-round 已创建 archive。该工作已经结束，本轮不得继续改 gate 框架，除非 gate 对本轮记录产生直接阻塞。

`artifact_index.json` 中 `local_reverse_affine_8cfebe03_static_triage` 和 `local_reverse_affine_8cfebe03_static_evidence_summary` 为 current；这只证明 `affine_8cfebe03` 已有 current IDA 静态证据，不能作为 `affineenc_333f8ca9` 的当前证据。

`project_state/local_reverse_training_status.json` 显示：总样本 65 个，solved 1，blocked 2，needs_triage 2，inventory_only 60。`affine_8cfebe03` 两个重复路径条目已是 `needs_triage`，有 IDA/static evidence summary；`affineenc_333f8ca9` 仍是 `inventory_only`，relative_path 为 `逆向课程2020秋04/affineenc.exe`，sha256 为 `333f8ca9f47e5e705b6dcdbcfbb6b24898dba01f6c518f51515d36618e7add9f`，next_action 为 `static triage and manual evaluation required`。

`project_state/local_reverse_evaluation_queue.json` 的 rank 1 是 `affineenc_333f8ca9`，proposed_next_mainline 为 `tool_integration`，allowed_actions 只有 `static_triage`，forbidden_actions 包括 `runtime_probe`、`bruteforce`、`upload_binary`。本轮必须严格遵守这个队列约束。

`negative_results.json` 中禁止回到旧 sample_solver 盲搜、只扩大 beam/budget、使用 compare_semantics_agree=false 作为主 frontier、提交完整 solve_reports、重复旧 samplereverse 失败方向。本轮不触碰这些方向。

已有相关能力必须优先复用：`reverse_agent/local_reverse_single_sample_static_triage.py`、`reverse_agent/local_reverse_forced_ida_extract.py`、`reverse_agent/local_reverse_xref_disassembly.py`、tool capability inventory、project_state artifact_index、training_status、evaluation_queue、project_gate preflight/command-plan/report-summary/final-check/close-round。不得新建重复 IDA/Ghidra/debugger/solver/harness 接口。

涉及逆向工具边界：允许有界运行现有静态 triage/IDA 静态提取工具，但只针对 `affineenc_333f8ca9`。不允许运行 runtime probe、debugger、emulator、hook、harness campaign、solver、bruteforce 或 candidate validation。

允许读取重型 artifact：不允许读取完整 `solve_reports/` 或完整 `PROJECT_PROGRESS_LOG.txt`。只允许读取本轮直接相关的 project_state 文件、工具能力文件、现有静态 triage/IDA 代码、相关测试和本轮生成的 `affineenc_333f8ca9` 静态 artifact。

## 3. Do Not Do

不得重复 `affine_8cfebe03` 的 static evidence classification、static tool validation/state closure、audit closure 或 gate closure framework fix。

不得运行 solver、bruteforce、guided_pool、sample_solver、SMT、runtime validation、debugger、emulator、hook、harness campaign。

不得生成 candidate、flag、password；不得把 `affineenc_333f8ca9` 标成 solved。

不得把 `affine_8cfebe03` 的 current artifact 当作 `affineenc_333f8ca9` 的 current evidence。

不得读取完整 `solve_reports/` 或完整 `PROJECT_PROGRESS_LOG.txt`，不得提交完整 solve_reports，不得修改 `.codex-skills/`、training materials、raw sample 文件。

不得处理 evaluation queue rank 2 及以后样本，不得批量跑 60 个 inventory_only 样本。

不得新建重复 IDA/Ghidra/debugger/solver/harness 接口；成熟工具已有能力必须复用。

不得修改 gate 框架、project_state 框架或 skill，除非本轮 gate 记录出现直接阻塞且有最小修复理由。

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
- `project_state/local_reverse_inventory.json` 中 `affineenc_333f8ca9` 对应条目
- `project_state/local_reverse_affine_8cfebe03_static_evidence_summary.json` 仅用于确认不重复旧任务，不得作为本样本证据
- `reverse_agent/tool_capability_inventory.py`
- `reverse_agent/local_reverse_single_sample_static_triage.py`
- `reverse_agent/local_reverse_forced_ida_extract.py`
- `reverse_agent/local_reverse_xref_disassembly.py`
- 与上述工具和 project_state/project_gate 直接相关的测试
- 本轮生成的 `project_state/local_reverse_affineenc_333f8ca9_*` artifact（生成后读取核验）

## 5. Required Audit

Codex 必须先确认：

- 当前 decision_meta 合法，`status=APPROVED`，`mainline=tool_integration`，`skill_profiles` 来自 active registry。
- `task_packet.json/current_state.json` 是旧 `samplereverse` 背景；当前执行权威是本 decision。
- `affineenc_333f8ca9` 在 training_status 中仍是 `inventory_only`，evaluation_queue rank 1，allowed_actions 只有 `static_triage`。
- `affine_8cfebe03` 已有 current static triage 和 static evidence summary；本轮不得重复该样本工作。
- 现有 IDA/static triage/tool capability 接口存在；不得新建重复接口。

必须完成或如实报告：

- 对 `affineenc_333f8ca9` 运行现有静态 triage 或 IDA static extraction 的最小命令；若 IDA 不可用或工具失败，生成 blocker diagnostic，不得伪造成功。
- 若工具成功，生成 `project_state/local_reverse_affineenc_333f8ca9_static_triage.json` 或项目既有命名约定下的等价 artifact，并记录 tool、source_run、sha256、size、strings/functions/compare contexts 等关键摘要。
- 将新 artifact 登记到 `artifact_index.json`，freshness 必须为 current，source_run 必须为 `round_20260613_affineenc_static_triage_v1`。
- 仅在有 current 静态证据时，允许把 `local_reverse_training_status.json` 中 `affineenc_333f8ca9` 从 `inventory_only` 更新为 `needs_triage`，classification 只能写静态 triage 支持的保守分类，known_candidate 必须保持空。
- 若工具失败，不得更新为 `needs_triage`；应保留或设置 blocked/diagnostic，写明 blocker，例如 IDA unavailable、sample path missing、static tool no output。
- 不得修改 `affine_8cfebe03`、`cpp1_bcbd9979`、`cpp2_4c69f173`、`sha_256_18019fca` 的既有训练结论。

## 6. Implementation Scope

Allowed

- `project_state/local_reverse_affineenc_333f8ca9_static_triage.json`
- `project_state/static_tool_blocker_diagnostic_affineenc_333f8ca9.json`
- `project_state/artifact_index.json`
- `project_state/local_reverse_training_status.json`（仅限 `affineenc_333f8ca9` 条目，且不得写 candidate/solved）
- `project_state/local_reverse_evaluation_queue.json`（仅限把 `affineenc_333f8ca9` 的 rank/next_action 状态同步为已静态 triage 或保留待处理；不得批量重排）
- `project_state/codex_execution_report.md`
- `project_state/pytest_result.txt`
- `project_state/gates/*.json`
- `project_state/rounds/round_20260613_affineenc_static_triage_v1/*`

Allowed only if strictly necessary for existing tool compatibility, with focused tests:

- `reverse_agent/local_reverse_single_sample_static_triage.py`
- `reverse_agent/local_reverse_forced_ida_extract.py`
- `reverse_agent/local_reverse_xref_disassembly.py`
- tests directly covering the touched static triage/tool integration path

Forbidden

- solver、harness、debugger、emulator、runtime probe、candidate validation 相关代码
- `reverse_agent/strategies/`、`reverse_agent/transforms/`、IDA/Ghidra/debugger 新接口
- `.codex-skills/`
- `training_materials/`
- `solve_reports/`
- raw sample 文件
- `project_state/local_reverse_affine_8cfebe03_static_evidence_summary.json` 的语义字段
- 任何已 solved/blocked 样本的 known_candidate、classification、blocked_reason 结论

## 7. Tests

必须运行并记录：

- `Get-Location`
- `Test-Path F:\reverse-agent`
- `git status --short`
- `python -m reverse_agent.project_gate preflight --state-dir project_state`
- `python -m reverse_agent.project_gate command-plan --state-dir project_state`
- 现有 static triage / forced IDA / xref 相关定向 pytest；若不存在精确测试，运行最小相关测试并说明覆盖边界
- `python -m pytest tests/test_project_state.py tests/test_project_gate.py -q`
- 对 `affineenc_333f8ca9` 的有界 static triage/IDA static extraction 命令，必须记录 stdout/stderr/exit code
- artifact schema/存在性核验：path 存在、sha256/size 已登记、freshness=current、source_run 正确
- training_status 核验：`affineenc_333f8ca9` 未 solved、known_candidate 为空；已完成样本和 blocked 样本结论未变
- `python -m reverse_agent.project_state doctor --state-dir project_state`
- `python -m reverse_agent.project_state lint-report --state-dir project_state`
- `python -m reverse_agent.project_gate report-summary --state-dir project_state`
- `python -m reverse_agent.project_gate final-check --state-dir project_state`
- `python -m reverse_agent.project_gate close-round --state-dir project_state --round-id round_20260613_affineenc_static_triage_v1`

`project_state/pytest_result.txt` 必须包含本轮 `decision_20260613_affineenc_static_triage_v1`、`round_20260613_affineenc_static_triage_v1`、真实命令、退出码和最终结果。

`project_state/codex_execution_report.md` 顶部必须包含合法 `codex_report_summary`，其中 `based_on_decision_id=decision_20260613_affineenc_static_triage_v1`，`round_id=round_20260613_affineenc_static_triage_v1`，并列出实际 files_changed、tests_ran、generated_artifacts。

## 8. Stop Conditions

如果 static triage/IDA 工具不可用、样本路径不可访问、或工具输出为空，停止样本推进并写 blocker diagnostic；不得伪造 current evidence。

如果需要 solver、runtime validation、debugger、emulator、hook、harness campaign，停止。

如果需要修改 `.codex-skills/`、training materials、solve_reports 历史目录或 raw sample 文件，停止。

如果需要处理 `affine_8cfebe03`、`samplereverse` 或 queue rank 2 及以后样本，停止。

如果需要把 `affineenc_333f8ca9` 标成 solved 或写入 candidate，停止；本轮只允许 static triage 证据。

如果 gate/report/archive 再次出现框架级 FAIL，报告应为 REWORK_REQUIRED 或 BLOCKED，不能写 SUCCESS。
