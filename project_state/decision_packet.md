```json decision_meta
{
  "schema_version": 1,
  "decision_id": "decision_20260531_local_sample_intake_solve_bootstrap",
  "round_id": "round_20260531_local_sample_intake_solve_bootstrap",
  "based_on_state_build_id": "state_20260527_153028_1d6dd81ecbd6",
  "based_on_state_digest": "1d6dd81ecbd615598f7b0fda09f1e859a4cba6a0d28b45711434e174ba6b5e02",
  "status": "APPROVED",
  "mainline": "engineering_branch",
  "skill_profiles": [
    "reverse-agent-iteration@v2"
  ]
}
```

# DECISION_PACKET

本轮属于 **engineering_branch**。上一轮已经完成 `local_reverse_samples/` 本地逆向样本目录约定：`.gitignore` 已忽略该目录，README 已说明用途、不会上传 GitHub，并给出 harness `case.json` 示例和运行命令。

当前用户进一步澄清目标：不希望长期手写每个 `case.json`，而是希望“提供一个逆向题目后，项目自动登记样本，自动生成 `case.json` / `metadata.json` / `notes.md`，并生成 Codex 可以继续写本题 solver 的本地任务入口”。因此本轮计划替代上一版单纯 `local_samples list/run` 方案，改为 **local sample intake + solve bootstrap**。

当前 Codex 实际执行权威是本文件 `project_state/decision_packet.md`。`project_state/task_packet.json` 中的 `task` / `derived_task` 仍是旧 reverse_solving 状态派生建议，不自动覆盖本 decision。

## 1. Goal

新增一个最小本地样本导入与解题引导入口：

```text
python -m reverse_agent.local_samples add <path-to-exe-or-attachment> [--case-id <case_id>]
python -m reverse_agent.local_samples solve <case_id>
```

目标不是实现完整自动训练平台，而是建立如下本地工作流：

```text
用户提供一个逆向题目文件
        ↓
local_samples add 自动复制/登记样本
        ↓
自动生成 case.json / metadata.json / notes.md
        ↓
local_samples solve 运行最小静态 harness 或生成解题 bootstrap
        ↓
生成 local_reverse_samples/<case_id>/codex_task.md
        ↓
本地 Codex 可依据 codex_task.md 和本地样本继续写 local solver.py
```

本轮必须实现的最小能力：

```text
1. 新增 reverse_agent/local_samples.py。
2. add 命令接受一个本地题目文件路径，自动创建 local_reverse_samples/<case_id>/。
3. add 命令自动复制题目文件到样本目录，推荐命名为 sample<原扩展名>，例如 sample.exe。
4. add 命令自动生成 case.json，不再要求用户手写。
5. add 命令自动生成 metadata.json，至少包含 case_id、original_path、stored_sample_path、sha256、size_bytes、created_at、category、tags。
6. add 命令自动生成 notes.md 模板。
7. solve 命令读取 metadata.json / case.json，生成 codex_task.md，说明本地 Codex 下一步应如何分析该题和写 solver.py。
8. solve 命令默认先走静态、安全、可审计路径；不要自动运行 IDA/Olly/Frida runtime probe。
9. 允许 solve 命令可选调用现有 harness 的 Static Analysis 路径，但必须可在测试中 monkeypatch，不依赖真实 .exe。
10. README.txt 更新为“用户只需提供样本文件，不必手写 case.json”的流程说明。
```

本轮不要求 Codex 真的对某个真实 `.exe` 写出 solver；本轮只建设本地样本 intake 和 solver bootstrap 机制。真实 solver.py 应在本地样本目录下由后续本地 Codex/人工迭代生成，不提交 GitHub。

## 2. Current Evidence

当前主线判断：

```text
mainline = engineering_branch
reason = 用户明确要求把 local_reverse_samples 从“本地文件夹约定”推进到“提供题目后自动登记并生成 solver 工作入口”；这是本地工作流建设，不是 samplereverse 当前解题推进。
```

上一轮已完成并接受：

```text
previous_decision_id = decision_20260531_local_reverse_samples_ignore
previous_report_id = report_20260531_local_reverse_samples_ignore
previous_status = SUCCESS / ACCEPTED
```

上一轮事实：

```text
1. .gitignore 已忽略 local_reverse_samples/。
2. README.txt 已说明 local_reverse_samples\ 是本地逆向训练样本目录。
3. README.txt 已给出手写 case.json 的 harness 示例。
4. 未提交真实 .exe/.dll/.bin/.zip/.7z/.rar 样本。
5. 未运行 reverse runtime probe。
```

当前 `task_packet.task` / `derived_task` 仍然是旧 samplereverse 状态派生建议：

```text
task = Diagnose bounded compare hook path reachability
derived_task = Diagnose bounded compare hook path reachability
```

这些不是本轮执行任务。本轮由本 `decision_packet.md` 控制。

当前 skill profiles：

```text
reverse-agent-iteration@v2
```

不使用：

```text
samplereverse-frontier@v2
```

原因：本轮不推进 samplereverse 样本，不涉及 candidate、frontier、runtime evidence 或 artifact freshness 推进。

## 3. Do Not Do

严禁：

```text
1. 不修改 .codex-skills/、registry、sync 脚本或 skill 内容。
2. 不运行 samplereverse harness。
3. 不运行 Base64/RC4 breakpoint probe。
4. 不运行 IDA/Olly/Frida runtime probe。
5. 不读取完整 solve_reports/。
6. 不读取完整 PROJECT_PROGRESS_LOG.txt。
7. 不提交 local_reverse_samples/ 下任何内容。
8. 不提交任何 .exe、.dll、.bin、.zip、.7z、.rar。
9. 不新增数据库、消息队列、Web 服务或复杂训练平台。
10. 不新增样本 schema/lint 系统。
11. 不改动 CompareAwareSearchStrategy、samplereverse profile 或任何当前解题策略。
12. 不把 local_reverse_samples/ 当成 project_state 动态事实源。
13. 不把单题 solver.py 提交到 GitHub；solver.py 应位于被忽略的 local_reverse_samples/<case_id>/ 下。
14. 不实现自动分类、自动训练、自动通用 solver 提升。
```

特别限制：

```text
本轮只提供 local sample intake 和 solve bootstrap。不要把它扩展成完整解题 agent、后台任务系统、多 worker 平台或训练材料数据库。
```

## 4. Files To Inspect

默认必须读取：

```text
project_state/task_packet.json
project_state/current_state.json
project_state/artifact_index.json
project_state/negative_results.json
project_state/codex_execution_report.md
project_state/decision_packet.md
project_state/pytest_result.txt
```

必须检查：

```text
.gitignore
README.txt
reverse_agent/harness.py
tests/test_harness.py
```

允许新增：

```text
reverse_agent/local_samples.py
tests/test_local_samples.py
```

可以有界检查：

```text
reverse_agent/__init__.py
pyproject.toml
requirements.txt
```

不要默认检查：

```text
solve_reports/
PROJECT_PROGRESS_LOG.txt
project_state/rounds/ 全量历史
```

## 5. Required Audit

Codex 报告必须回答：

```text
1. local_samples add 是否能在不手写 case.json 的情况下自动创建样本目录。
2. add 是否自动复制输入文件到 local_reverse_samples/<case_id>/sample<ext>。
3. add 是否自动生成 case.json，且格式兼容 reverse_agent.harness.load_harness_cases。
4. add 是否自动生成 metadata.json，且包含 sha256、size_bytes、original_path、stored_sample_path。
5. add 是否自动生成 notes.md 模板。
6. add 是否能在未指定 --case-id 时生成稳定、安全的 case_id，例如 stem + sha256 前缀。
7. add 是否拒绝覆盖已有 case_id，除非显式提供安全选项；如果不实现覆盖选项，应清晰报错。
8. solve 是否能根据 case_id 定位本地样本目录和 case.json。
9. solve 是否生成 codex_task.md，说明后续本地 Codex 写 solver.py 的输入、输出、约束和禁止行为。
10. solve 是否默认不运行 IDA/Olly/Frida runtime probe。
11. 是否没有提交 local_reverse_samples/ 内任何文件。
12. 是否没有提交 .exe/.dll/.bin/.zip/.7z/.rar。
13. 是否没有修改 .codex-skills/。
14. 是否没有修改 samplereverse 解题主线。
15. codex_execution_report.md 顶部必须包含 codex_report_summary。
16. codex_report_summary.based_on_decision_id 必须等于 decision_20260531_local_sample_intake_solve_bootstrap。
17. pytest_result.txt 必须记录本轮实际测试结果。
```

## 6. Implementation Scope

允许修改：

```text
reverse_agent/local_samples.py
tests/test_local_samples.py
README.txt
project_state/codex_execution_report.md
project_state/pytest_result.txt
```

必要时允许修改：

```text
reverse_agent/__init__.py
```

不应修改：

```text
.gitignore
reverse_agent/harness.py
reverse_agent/strategies/compare_aware_search.py
reverse_agent/profiles/samplereverse.py
.codex-skills/
project_state/task_packet.json
project_state/current_state.json
project_state/artifact_index.json
project_state/negative_results.json
```

如果发现必须修改 `reverse_agent/harness.py` 才能复用 dataset 格式或 Static Analysis 调用，Codex 应优先停止并报告 `BLOCKED`，不要扩大范围。

推荐实现方式：

```text
1. 新增 reverse_agent/local_samples.py。
2. 使用 argparse 实现子命令：
   - add <path>
   - solve <case_id>
   - list   # 可选，但不是核心目标；若实现必须保持轻量。
3. 默认 samples root = local_reverse_samples。
4. 支持 --samples-dir 覆盖本地样本目录，便于测试。
5. add 流程：
   a. 校验输入文件存在且是文件。
   b. 计算 sha256、size_bytes。
   c. case_id 规则：
      - 如果用户提供 --case-id，则 sanitize 后使用。
      - 否则使用 <stem>_<sha256前8位>。
   d. 创建 local_reverse_samples/<case_id>/。
   e. 复制输入文件为 sample<原扩展名>。
   f. 写 case.json：object with cases list。
   g. 写 metadata.json。
   h. 写 notes.md。
6. case.json 默认字段：
   case_id = <case_id>
   input_value = local_reverse_samples/<case_id>/sample<ext>
   expected_flag = ""
   category = "unknown"
   tags = ["local", "reverse", "auto_imported"]
   notes = "Auto-generated from local sample intake."
7. solve 流程：
   a. 读取 local_reverse_samples/<case_id>/metadata.json 和 case.json。
   b. 生成 codex_task.md。
   c. codex_task.md 应要求本地 Codex 写 local_reverse_samples/<case_id>/solver.py。
   d. codex_task.md 应说明 solver.py 不提交 GitHub。
   e. codex_task.md 应默认先做静态分析，不运行 runtime probe，除非用户后续显式授权。
8. solve 可选参数：
   --run-static-harness
   如果实现该选项，必须调用现有 reverse_agent.harness.main([...]) 或等价公开入口，并且测试中 monkeypatch，不运行真实样本。
9. README.txt 更新：
   从“手写 case.json”改为“add 自动生成 case.json；solve 生成 Codex 解题任务”。保留手写 case.json 作为高级用法即可。
```

推荐命令示例：

```powershell
python -m reverse_agent.local_samples add .\crackme.exe --case-id crackme_sha256_001
python -m reverse_agent.local_samples solve crackme_sha256_001
```

推荐生成结构：

```text
local_reverse_samples/
  crackme_sha256_001/
    sample.exe
    case.json
    metadata.json
    notes.md
    codex_task.md        # solve 命令生成
    solver.py            # 后续本地 Codex/人工生成，不由本轮提交
```

`codex_task.md` 至少包含：

```text
1. case_id
2. sample path
3. sha256 / size
4. harness command
5. expected solver output path: local_reverse_samples/<case_id>/solver.py
6. first-pass analysis requirements: strings/imports/constants/compare points/hash or encoding indicators
7. do not run runtime probe unless user explicitly authorizes
8. do not commit local_reverse_samples/ contents
9. if a reusable pattern is found, propose a future project strategy instead of modifying strategy immediately
```

## 7. Tests

必须运行：

```text
python -m py_compile reverse_agent/local_samples.py
python -m pytest -q tests/test_local_samples.py
python -m pytest -q tests/test_harness.py
python -m reverse_agent.project_state lint-decision --state-dir project_state
python -m reverse_agent.project_state lint-report --state-dir project_state
git diff --check
git status --short
git check-ignore -v local_reverse_samples/
```

不要求运行：

```text
python -m pytest -q
真实 samplereverse harness
真实 local_reverse_samples 样本
IDA/Olly/Frida runtime probe
Base64/RC4 runtime probe
```

测试最低覆盖：

```text
1. add 在 tmp_path 下复制 fake binary，并自动生成 case.json / metadata.json / notes.md。
2. add 未指定 --case-id 时能生成稳定、安全的 case_id。
3. add 指定 --case-id 时使用该 case_id 并 sanitize。
4. add 不覆盖已有 case_id，返回清晰错误。
5. case.json 能被 reverse_agent.harness.load_harness_cases 读取。
6. metadata.json 包含 sha256、size_bytes、original_path、stored_sample_path。
7. solve 对存在 case_id 生成 codex_task.md。
8. solve 对不存在 case_id 返回非零或抛出 SystemExit，并有清晰错误。
9. 所有测试使用 tmp_path 和 fake file，不依赖真实 .exe。
10. 不需要创建或提交真实 local_reverse_samples/ 内容。
```

## 8. Stop Conditions

立即停止并报告 `BLOCKED`：

```text
1. 当前分支不是 feature/training-materials-corpus。
2. 当前 decision_id 不是 decision_20260531_local_sample_intake_solve_bootstrap。
3. 无法安全新增 reverse_agent/local_samples.py。
4. 无法在不提交 local_reverse_samples/ 内容的情况下测试 add/solve。
5. 必须修改 reverse_agent/harness.py 才能完成本轮目标。
6. 必须运行真实 .exe 或 runtime probe 才能验证本轮目标。
7. lint-decision 或 lint-report 因当前 project_state 元信息不兼容而失败，且无法在本轮安全修复。
```

完成条件：

```text
1. python -m reverse_agent.local_samples add <file> 可自动生成本地样本目录、case.json、metadata.json、notes.md。
2. 用户不再需要手写 case.json 才能登记单个本地样本。
3. python -m reverse_agent.local_samples solve <case_id> 可生成 codex_task.md。
4. README.txt 记录 add/solve 使用方式。
5. 测试覆盖 tmp_path fake samples，不依赖真实 .exe。
6. 未提交 local_reverse_samples/ 内容。
7. 未修改 .codex-skills/。
8. 未运行逆向 runtime probe。
9. codex_execution_report.md、pytest_result.txt 与 decision_20260531_local_sample_intake_solve_bootstrap 对齐。
```
