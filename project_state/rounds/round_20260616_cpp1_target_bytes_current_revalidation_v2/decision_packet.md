```json decision_meta
{
  "schema_version": 1,
  "decision_id": "decision_20260616_cpp1_target_bytes_current_revalidation_v2",
  "round_id": "round_20260616_cpp1_target_bytes_current_revalidation_v2",
  "based_on_state_build_id": "state_20260615_150220_24f61a9ac337",
  "based_on_state_digest": "24f61a9ac337b596ff7d56b3e29f01e5ab68342825fb2a32ba50b65a84512bae",
  "status": "APPROVED",
  "mainline": "tool_integration",
  "skill_profiles": ["reverse-agent-iteration@v2"]
}
```

# DECISION_PACKET

## 1. Goal

本轮目标是对 `cpp1_2f6fcb63` 的 target compare bytes 做**当前证据重验证与 artifact_index 登记**。

上一轮 closeout 已收口；当前 `artifact_index.json` 中只有 `project_state/local_reverse_cpp1_2f6fcb63_static_triage.json` 明确为 current。仓库中虽然存在历史 `project_state/local_reverse_cpp1_2f6fcb63_target_bytes.json`，但它不能直接作为当前求解证据。本轮要复用现有 `reverse_agent/local_reverse_cpp1_target_byte_extract.py --current-revalidation` 能力，把历史 target bytes 与当前 static triage 做一致性校验，生成新的 current revalidation artifact，并登记到 `artifact_index.json`。

本轮不是求解轮，不生成 candidate/password/flag，不运行样本，不做 runtime probe，不启动 debugger/harness，不扩展到其他样本。

## 2. Current Evidence

当前执行权威是本 `project_state/decision_packet.md`，不是 `task_packet.json`。`task_packet.json/current_state.json` 仍包含历史 `samplereverse` 压缩状态，只能作为背景，不得覆盖本轮任务。

上一轮 `decision_20260616_cpp1_static_triage_closeout_rework_v1` 为 `engineering_branch` closeout，审计结论可接受：report/pytest/final gate/round archive 已对齐。本轮不继续 gate closeout 返工。

`artifact_index.json` 中 `local_reverse_cpp1_2f6fcb63_static_triage` 为 current，path 为 `project_state/local_reverse_cpp1_2f6fcb63_static_triage.json`，source_run 为 `round_20260615_cpp1_2f6fcb63_bounded_static_triage_v1`，tool_status 为 success。

当前 static triage artifact 显示：

- sample_id: `cpp1_2f6fcb63`
- relative_path: `逆向课程2023春01/CPP1.exe`
- sha256: `2f6fcb637151a413dae11ab981706ff1f46d2202abc1d60de8a3b534448baede`
- analysis_mode: `single_sample_static_triage`
- executed_sample=false
- static_only=true
- runtime_validated=false
- source_tool=IDA
- forbidden_actions 包含 `runtime_probe`, `bruteforce`, `upload_binary`
- `_main_0` 是最高分 validation function candidate
- `_main_0` 伪代码显示 `scanf("%s", Str)`, `strlen(Str) != 18`, `strncpy(Destination, Str, 0x10u)`, transform 公式，以及 `Destination[i] == byte_429A30[i]` 比较，`i == 16` 时输出成功

仓库存在历史 `project_state/local_reverse_cpp1_2f6fcb63_target_bytes.json`，包含 `byte_429A30`、target address `0x00429A30`、target length 16、target bytes、main pseudocode 和 transform 信息。但它当前没有在 `artifact_index.json` 中被证明为 current，因此本轮只能把它作为待重验证输入，不能直接当 solved evidence 或 current evidence。

现有能力必须复用：

- IDA / IDAPython runner、IDA script 和静态 triage 能力已存在；不得重写反汇编/反编译能力。
- `reverse_agent/local_reverse_cpp1_target_byte_extract.py` 已有 `--current-revalidation` 模式，可读取 current triage 与旧 target bytes，生成 `target_bytes_current_revalidation` artifact，并更新 artifact_index。
- solver templates、symbolic solver、harness 都已存在，但本轮不得使用它们做 candidate 搜索或 runtime validation。
- `negative_results.json` 当前包含旧 `samplereverse` 失败方向；本轮不得触碰这些方向，也不得回到旧 `sample_solver` 盲搜、只扩 budget/beam、或提交完整 `solve_reports/`。

## 3. Do Not Do

不得分析或求解 `samplereverse`。

不得把 `task_packet.task` 当本轮执行任务。

不得运行目标样本二进制；不得 runtime probe、dynamic debugger、hook、emulator、harness campaign、raw stdin validation、SMT、bruteforce 或 old `sample_solver` blind search。

不得生成 candidate/password/flag；不得把 `cpp1_2f6fcb63` 标记为 solved。

不得把历史 `target_bytes.json` 直接改成 current，或只改 `artifact_index.json` 来伪造 current。必须生成独立 revalidation artifact，并记录 source_artifact_freshness 与 revalidation_checks。

不得新建重复 IDA/Ghidra/debugger/radare2/objdump/solver/harness 接口。成熟工具和现有接口优先。

不得修改 `.codex-skills/`、raw samples、training materials、完整 `solve_reports/` 或无关模块。

不得读取完整 `PROJECT_PROGRESS_LOG.txt` 或完整 `solve_reports/`。

不得扩大到其他本地样本；本轮只允许 `cpp1_2f6fcb63`。

## 4. Files To Inspect

必须按顺序读取默认状态文件：

1. `project_state/task_packet.json`
2. `project_state/current_state.json`
3. `project_state/artifact_index.json`
4. `project_state/negative_results.json`
5. `project_state/codex_execution_report.md`
6. `project_state/decision_packet.md`
7. `project_state/pytest_result.txt`
8. `.codex-skills/registry.json`

必须有界读取：

- `project_state/local_reverse_cpp1_2f6fcb63_static_triage.json`
- `project_state/local_reverse_cpp1_2f6fcb63_target_bytes.json`
- `reverse_agent/local_reverse_cpp1_target_byte_extract.py`
- `reverse_agent/tool_capability_inventory.py`
- `reverse_agent/tool_runners.py`，只核验既有 IDA/tool runner 能力
- `reverse_agent/ida_scripts/extract_named_data.py`，只在 revalidation blocked 且需要确认现有 IDA extraction 能力时读取
- `tests/test_project_gate.py`
- `tests/test_project_state.py`

可选、有界读取：

- `project_state/rounds/round_20260616_cpp1_static_triage_closeout_rework_v1/round_manifest.json`
- `project_state/gates/final_gate_result.json`
- `project_state/gates/report_summary_synthesis.json`

## 5. Required Audit

开始修改前必须确认：

1. 当前工作目录是 `F:\reverse-agent`，且 `git rev-parse --show-toplevel` 指向该仓库。
2. `decision_meta` 可解析，`status=APPROVED`，`mainline=tool_integration`。
3. `reverse-agent-iteration@v2` 在 `.codex-skills/registry.json` 中为 active。
4. `task_packet.json/current_state.json` 的 `samplereverse` 状态不是本轮任务权威。
5. `artifact_index.json` 中 `local_reverse_cpp1_2f6fcb63_static_triage` 为 current，且 sample_id 为 `cpp1_2f6fcb63`。
6. 历史 `target_bytes.json` 只作为待重验证输入；在 revalidation 通过前不得当 current evidence。
7. `reverse_agent/local_reverse_cpp1_target_byte_extract.py` 已有相关能力；不得新建重复 extractor 或 runner。
8. 本轮不运行样本，不做 runtime validation，不生成 candidate。

本轮必须执行或如实报告：

- 运行现有 current revalidation：

```powershell
python -m reverse_agent.local_reverse_cpp1_target_byte_extract --current-revalidation --triage project_state/local_reverse_cpp1_2f6fcb63_static_triage.json --target-bytes project_state/local_reverse_cpp1_2f6fcb63_target_bytes.json --out project_state/local_reverse_cpp1_2f6fcb63_target_bytes_revalidation.json --artifact-index project_state/artifact_index.json
```

- 新 artifact 必须包含至少：
  - `schema_version`
  - `sample_id`
  - `relative_path`
  - `sha256`
  - `analysis_mode="target_bytes_current_revalidation"`
  - `mainline="tool_integration"`
  - `executed_sample=false`
  - `static_only=true`
  - `runtime_validated=false`
  - `candidate=null`
  - `known_candidate=""`
  - `source_artifacts`
  - `source_artifact_freshness`
  - `revalidation_checks`
  - `revalidation_status`
  - `blocked_reason`
  - `mismatched_fields`
  - `target_symbol`
  - `target_address`
  - `target_length`
  - `target_bytes_hex`
  - `target_bytes`
  - `forward_transform`
  - `recommended_next_action`

- 如果 revalidation_status 为 `PASSED`，`artifact_index.json` 必须登记 `local_reverse_cpp1_2f6fcb63_target_bytes_revalidation` 为 current，path 指向 `project_state/local_reverse_cpp1_2f6fcb63_target_bytes_revalidation.json`，source_run 为本轮 round_id，sample_id 为 `cpp1_2f6fcb63`。
- 如果 revalidation_status 为 `BLOCKED` 或 `FAILED`，不得继续求解；报告 blocker，下一轮再决定是否使用既有 IDA extraction 有界重建。
- `codex_execution_report.md` 必须明确说明：是否运行了 revalidation、是否更新 artifact_index、是否没有运行样本、是否没有生成 candidate、是否没有新建工具接口。
- `pytest_result.txt` 必须记录真实命令、stdout/stderr 和 exit code。

## 6. Implementation Scope

默认不改源码。

允许更新/生成：

- `project_state/local_reverse_cpp1_2f6fcb63_target_bytes_revalidation.json`
- `project_state/artifact_index.json`
- `project_state/codex_execution_report.md`
- `project_state/pytest_result.txt`
- `project_state/gates/command_plan.json`
- `project_state/gates/preflight_result.json`
- `project_state/gates/report_summary_synthesis.json`
- `project_state/gates/final_gate_result.json`
- `project_state/gates/round_baseline.json`
- `project_state/gates/round_delta_summary.json`
- `project_state/gates/run_round_result.json`
- `project_state/rounds/round_20260616_cpp1_target_bytes_current_revalidation_v2/*`

仅当现有 revalidation CLI 无法运行且必须做最小兼容修复时，允许修改：

- `reverse_agent/local_reverse_cpp1_target_byte_extract.py`
- `reverse_agent/project_state.py`
- `reverse_agent/project_gate.py`
- 直接相关 tests

不得修改 solver logic、harness runtime behavior、IDA runner semantics、GUI/frontend、training materials 或 `.codex-skills/`。

不得提交完整 `solve_reports/`。

## 7. Tests

必须把命令、stdout、stderr、exit code 记录到 `project_state/pytest_result.txt`。

启动检查必须先执行：

```powershell
Set-Location F:\reverse-agent
Get-Location
Test-Path F:\reverse-agent
git rev-parse --show-toplevel
git status --short
```

必跑 gate/status 命令：

```powershell
python -m reverse_agent.project_gate preflight --state-dir project_state
python -m reverse_agent.project_gate command-plan --state-dir project_state
python -m reverse_agent.project_gate command-plan --state-dir project_state --json
python -m reverse_agent.project_gate run-round --state-dir project_state --dry-run --json
python -m reverse_agent.project_state doctor --state-dir project_state
python -m reverse_agent.project_state lint-report --state-dir project_state
python -m reverse_agent.project_state active-execution-view --state-dir project_state --json
```

必跑本轮 revalidation 命令：

```powershell
python -m reverse_agent.local_reverse_cpp1_target_byte_extract --current-revalidation --triage project_state/local_reverse_cpp1_2f6fcb63_static_triage.json --target-bytes project_state/local_reverse_cpp1_2f6fcb63_target_bytes.json --out project_state/local_reverse_cpp1_2f6fcb63_target_bytes_revalidation.json --artifact-index project_state/artifact_index.json
```

如果无源码修改，运行：

```powershell
python -m pytest tests/test_project_state.py tests/test_project_gate.py -q
```

如果源码被修改，必须增加直接相关测试；至少运行：

```powershell
python -m pytest tests/test_project_state.py tests/test_project_gate.py -q
```

收尾必须运行：

```powershell
python -m reverse_agent.project_gate report-summary --state-dir project_state
python -m reverse_agent.project_gate final-check --state-dir project_state
python -m reverse_agent.project_gate close-round --state-dir project_state --round-id round_20260616_cpp1_target_bytes_current_revalidation_v2
```

## 8. Stop Conditions

如果无法进入 `F:\reverse-agent` 或不是该 Git 仓库，立即停止。

如果 `decision_meta` 不合法、status 不是 APPROVED、mainline 不是 tool_integration、skill profile 不 active，立即停止。

如果 current static triage artifact 缺失、不是 current、sample_id 不是 `cpp1_2f6fcb63`，停止并报告 state mismatch。

如果历史 `target_bytes.json` 缺失或 revalidation 发现关键字段冲突，停止在 BLOCKED/FAILED，不继续 solver，不运行 IDA，除非本 decision 明确允许的 current-revalidation 已完成并给出 blocker。

如果 revalidation 成功，也不要继续求解；本轮 stop after artifact registration and gate closeout。

如果任何命令失败、pytest_result 缺失/不匹配、report/decision/round id mismatch、final-check 或 close-round 失败，不得写 SUCCESS/ACCEPTED。

如果需要 runtime validation、raw stdin delivery、candidate confirmation 或 solver 推进，停止并请求下一轮独立 `reverse_solving` decision。
