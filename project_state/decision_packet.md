```json decision_meta
{
  "schema_version": 1,
  "decision_id": "decision_20260618_static_triage_type_tag_contract_v1",
  "round_id": "round_20260618_static_triage_type_tag_contract_v1",
  "based_on_state_build_id": "state_20260618_114539_14d4ec94f06b",
  "based_on_state_digest": "14d4ec94f06bab113eb55fdf774e82b449b2851672e927f2b0df7a6052a95cc2",
  "status": "APPROVED",
  "mainline": "training_dataset",
  "skill_profiles": ["reverse-agent-iteration@v2"]
}
```

# DECISION_PACKET

## 1. Goal

把上一轮训练覆盖矩阵中的“metadata-level planning gaps”推进到可复用的静态分类契约：为本地逆向训练集建立 static triage type-tag contract，并用单元测试验证分类逻辑，但不运行任何样本和逆向工具。

上一轮已经完成训练覆盖矩阵，确认短期缺口集中在：type tag enrichment、simple transform recipes、cipher static evidence profile、hash bounded-domain policy、GUI/anti-debug metadata fields。本轮只做第一步：定义并落地静态证据到题型标签的契约，使后续每次 static triage 能把观察到的 evidence 映射为可审计 type tags。

目标产物：

1. `project_state/local_reverse_static_type_tag_contract.json`
2. `project_state/local_reverse_static_type_tag_contract_report.md`
3. 必要的只读/纯函数分类逻辑和测试，优先复用现有 `StructuredEvidence`、`tool_runners`、`local_reverse_single_sample_static_triage` 能力。

本轮不求解样本，不运行样本，不运行 IDA/Ghidra/debugger/emulator/runtime probe，也不批量处理 inventory。

## 2. Current Evidence

主线是 `training_dataset`。

上一轮 `training_coverage_matrix_gap_report_v1` 给出的事实：

- local project_state inventory 有 65 个 metadata-only entries；GitHub-safe mirror 为 50 个 entries。
- 当前 read-only builder status：solved=1、blocked=2、needs_triage=0、inventory_only=62。
- queue 有 52 items，策略为 `simple_static_first_unsolved_only`。
- coverage matrix 覆盖字符串比较、XOR、移位/仿射、位运算、查表、RC4、DES、TEA、Base64、hash/MD5/SHA、GUI、简单反调试、mixed/unknown。
- 除字符串比较有一个已解样本外，大多数类别仍是 metadata/source-audit level，缺少 current static-triage evidence。
- gap report 明确下一步应先做 type tag enrichment，并为 RC4/DES、simple transforms、hash/GUI/anti-debug 定义静态证据要求。

上一轮 gate 工程清理已 ACCEPTED：`fast_profile_non_closeout_success_policy_v1` final-check PASSED，archive_status=archived，report_status=SUCCESS，acceptance_recommendation=ACCEPTED。

`task_packet.json` 仍保留旧 `samplereverse` sample_state/reverse-solving 内容；它不是本轮执行权威。本轮执行以 `project_state/decision_packet.md` 为准。

`negative_results.json` 禁止旧 sample_solver blind search、budget-only expansion、compare_semantics_agree=false candidate frontier、提交完整 solve_reports。本轮不触碰这些方向。

进入 training_dataset 前必须检查已有能力：sample metadata、inventory/status overlay、evaluation queue、solver templates、static triage、IDA/Ghidra/debugger/tool runner/harness/StructuredEvidence 接口。成熟工具优先，不重复实现已有工具能力。

## 3. Do Not Do

不要运行 reverse-solving。

不要运行任何样本可执行文件。

不要运行 IDA、Ghidra、OllyDbg、x64dbg、debugger hook、emulator、runtime probe、sidecar、sample runner 或 GUI/frontend workflow。

不要调用旧 `sample_solver`，不要扩大 beam/topN/budget/timeout。

不要读取或提交完整 `solve_reports/`。

不要修改 `.codex-skills/`。

不要把单次样本 candidate、flag、本地绝对路径或 runtime metric 写进 skill。

不要把 metadata-level 标签声称为 solved 或 static-verified。

不要批量 backfill inventory type tags；本轮只定义 contract 和 synthetic/unit-level tests。

不要重复实现 IDA/Ghidra/debugger 已有能力；只做现有 evidence 输出的结构化映射。

## 4. Files To Inspect

默认先读取：

1. `project_state/task_packet.json`
2. `project_state/current_state.json`
3. `project_state/artifact_index.json`
4. `project_state/negative_results.json`
5. `project_state/codex_execution_report.md`
6. `project_state/decision_packet.md`
7. `project_state/pytest_result.txt`
8. `.codex-skills/registry.json`

训练/静态证据重点检查：

1. `project_state/local_reverse_training_coverage_matrix.json`
2. `project_state/local_reverse_training_gap_report.md`
3. `project_state/local_reverse_solver_tool_capability_map.json`
4. `project_state/local_reverse_training_inventory_refresh.json`
5. `reverse_agent/local_reverse_single_sample_static_triage.py`
6. `reverse_agent/evidence.py`
7. `reverse_agent/tool_runners.py`
8. `reverse_agent/local_reverse_training_status.py`
9. `tests/test_local_reverse_training_status.py`
10. 现有 static/solver/tool capability 相关测试，例如 `tests/test_tool_runners.py`、`tests/test_tool_capability_inventory.py`、`tests/test_simple_static_patterns.py`、`tests/test_static_feature_extractor.py`，只在直接相关时有界读取。

不要读取完整 `PROJECT_PROGRESS_LOG.txt` 或完整 `solve_reports/`。

## 5. Required Audit

执行前必须确认：

1. 当前工作目录是 `F:\reverse-agent`。
2. `Test-Path F:\reverse-agent` 为 `True`。
3. `git rev-parse --show-toplevel` 指向当前仓库。
4. 启动 `git status --short` 已记录。
5. `decision_meta.status=APPROVED`。
6. `mainline=training_dataset`。
7. `reverse-agent-iteration@v2` 是 active skill。
8. 本轮是训练集 type-tag contract 工作，不是逆向样本求解。

必须审计并记录：

1. 现有 `StructuredEvidence` 或 tool output 中已经有哪些可用于题型判断的字段。
2. `local_reverse_single_sample_static_triage` 当前是否已有 tags/category 输出；如果已有，不得重复造一套平行 schema。
3. 现有 IDA/Ghidra/debugger/tool runner 接口是否能提供 strings、functions、constants、compare contexts、crypto/material evidence；本轮只登记能力，不执行工具。
4. 每个目标题型的最低静态证据要求，特别是 string comparison、XOR、shift/affine、lookup table、RC4、DES、hash、GUI、anti-debug。
5. 哪些标签只能 metadata-level planning，哪些可以由 synthetic static evidence 单元测试验证。

## 6. Implementation Scope

优先生成/更新 project_state training artifacts：

- `project_state/local_reverse_static_type_tag_contract.json`
- `project_state/local_reverse_static_type_tag_contract_report.md`
- `project_state/artifact_index.json`
- `project_state/current_state.json`
- `project_state/codex_execution_report.md`
- `project_state/pytest_result.txt`
- `project_state/gates/preflight_result.json`
- `project_state/gates/gate_profile_plan.json`
- `project_state/gates/command_plan.json`
- `project_state/gates/report_summary_synthesis.json`
- `project_state/gates/final_gate_result.json`
- `project_state/gates/round_baseline.json`
- `project_state/gates/round_delta_summary.json`
- `project_state/gates/round_close_snapshot.json`
- `project_state/rounds/round_20260618_static_triage_type_tag_contract_v1/*`

仅当现有代码缺少静态标签契约入口时，允许小范围新增或修改：

- `reverse_agent/local_reverse_single_sample_static_triage.py`
- `reverse_agent/local_reverse_training_status.py`
- `reverse_agent/evidence.py`
- `tests/test_local_reverse_training_status.py`
- `tests/test_local_reverse_static_type_tags.py` 或现有等价测试文件

要求：

1. Contract 至少覆盖这些 tag ids：`string_comparison`、`xor`、`shift_affine`、`bit_operations`、`lookup_table`、`rc4`、`des`、`tea_xtea`、`base64`、`hash_md5_sha`、`gui_validation`、`simple_antidebug`、`mixed_unknown`。
2. 每个 tag 需包含：`evidence_requirements`、`allowed_evidence_sources`、`confidence_rules`、`solver_or_tool_route`、`not_sufficient_conditions`、`next_minimal_task`。
3. 如果新增代码，必须是纯函数或只读 schema helper；不得执行样本或工具。
4. 测试必须使用 synthetic evidence fixtures，验证至少 string comparison、XOR、shift/affine、lookup table、RC4、DES、hash、anti-debug 的分类输出与不充分证据场景。
5. 不得把文件名启发式当成 static-verified evidence；文件名只能用于 metadata-level hints。

## 7. Tests

必须运行并写入 `project_state/pytest_result.txt`：

```powershell
Set-Location F:\reverse-agent
Get-Location
Test-Path F:\reverse-agent
git rev-parse --show-toplevel
git status --short

python -m pytest tests/test_local_reverse_training_status.py tests/test_project_gate.py tests/test_project_state.py -q
```

如果新增了独立 type tag 测试文件，还必须运行：

```powershell
python -m pytest tests/test_local_reverse_static_type_tags.py tests/test_local_reverse_training_status.py tests/test_project_gate.py tests/test_project_state.py -q
```

必须运行只读 CLI 或等价检查：

```powershell
python -m reverse_agent.local_reverse_training_status --json
```

随后运行 gate：

```powershell
python -m reverse_agent.project_gate preflight --state-dir project_state
python -m reverse_agent.project_gate gate-profile --state-dir project_state
python -m reverse_agent.project_gate gate-profile --state-dir project_state --json
python -m reverse_agent.project_gate command-plan --state-dir project_state
python -m reverse_agent.project_gate command-plan --state-dir project_state --json
python -m reverse_agent.project_gate report-summary --state-dir project_state
python -m reverse_agent.project_gate final-check --state-dir project_state
```

如果 `final-check` 无 FAIL 且 `gate_profile_plan.closeout_allowed=true`，运行：

```powershell
python -m reverse_agent.project_gate close-round --state-dir project_state --round-id round_20260618_static_triage_type_tag_contract_v1
python -m reverse_agent.project_gate final-check --state-dir project_state
```

报告必须列出：profile、closeout_allowed、是否运行 close-round、type-tag contract 产物路径、测试覆盖的 tag、哪些类别仍为 metadata-level only、final-check 状态。

## 8. Stop Conditions

立即停止并报告 `REWORK_REQUIRED` 或 `BLOCKED`，如果：

1. 目录或仓库不正确。
2. `decision_meta` 缺失或不是 APPROVED。
3. `mainline` 不是 `training_dataset`。
4. `reverse-agent-iteration@v2` 不是 active。
5. 需要运行样本、debugger、IDA/Ghidra、emulator、runtime probe 或 sidecar。
6. 需要读取完整 `solve_reports/` 或 `PROJECT_PROGRESS_LOG.txt`。
7. 需要修改允许范围之外的文件。
8. 发现现有静态标签 schema 已存在但本轮准备重复实现。
9. 合约把 metadata/file-name hints 声称为 current static evidence。
10. 合约或测试把某类题声称为 solved/static-verified 但没有 evidence 规则支持。
11. 修改会影响 solver、harness、tool runner 主逻辑。
12. `report-summary` 或 `final-check` 最终出现 FAIL。
13. 报告声称完成 type tag contract，但没有 project_state artifact 或没有 synthetic/unit tests。
