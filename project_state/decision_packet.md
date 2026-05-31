```json decision_meta
{
  "schema_version": 1,
  "decision_id": "decision_20260531_local_reverse_samples_ignore",
  "round_id": "round_20260531_local_reverse_samples_ignore",
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

本轮属于 **engineering_branch**，目标是新增一个本地逆向例题目录约定，让用户可以在项目工作区内直接放置 `.exe`、`notes.md`、`case.json` 等本地训练材料，同时保证该目录不会上传到 GitHub。

当前 Codex 实际执行权威是本文件 `project_state/decision_packet.md`。`project_state/task_packet.json` 中的 `task` / `derived_task` 仍是旧 reverse_solving 状态派生建议，不自动覆盖本 decision。

## 1. Goal

新增并文档化一个本地目录：

```text
local_reverse_samples/
```

该目录用于用户本地存放真实逆向训练题目，例如：

```text
local_reverse_samples/
  crackme_sha256_001/
    sample.exe
    notes.md
    case.json
  crackme_rc4_001/
    sample.exe
    notes.md
    case.json
```

核心要求：

```text
1. local_reverse_samples/ 可以存在于项目工作区根目录。
2. 用户可以直接把 .exe、.dll、压缩包、notes、case.json 放进去。
3. local_reverse_samples/ 必须被 Git 忽略，不上传到 GitHub。
4. README.txt 必须说明该目录的用途、不会提交、以及 harness 如何引用其中的 case.json。
5. 不把 local_reverse_samples/ 设计成正式训练语料库，不引入 schema/lint/复杂样本管理系统。
6. 不修改 .codex-skills/。
7. 不推进 samplereverse 解题主线。
```

## 2. Current Evidence

当前主线判断：

```text
mainline = engineering_branch
reason = 用户明确要求新增本地样本目录，并保证不上传 GitHub；这是仓库使用方式和本地工作区约定，不是 samplereverse 解题推进。
```

当前 project_state：

```text
state_build_id = state_20260527_153028_1d6dd81ecbd6
state_digest = 1d6dd81ecbd615598f7b0fda09f1e859a4cba6a0d28b45711434e174ba6b5e02
active_strategy = CompareAwareSearchStrategy
task_packet.task = Diagnose bounded compare hook path reachability
task_packet.derived_task = Diagnose bounded compare hook path reachability
```

说明：

```text
1. task_packet.task / derived_task 是旧 reverse_solving 状态派生建议，不是本轮实际执行任务。
2. 本轮由本 decision_packet 控制。
3. 本轮不读取完整 solve_reports/，不读取完整 PROJECT_PROGRESS_LOG.txt。
4. 本轮不使用 stale/missing artifact 作为 runtime evidence。
5. 本轮不运行任何逆向 runtime probe。
```

当前上一轮 Codex 状态：

```text
previous_decision_id = decision_20260528_fix_material_hook_utf16_kind_protocol
previous_report_status = SUCCESS
previous_acceptance_recommendation = ACCEPTED
pytest_result.status = PASSED
```

当前 skill profiles：

```text
reverse-agent-iteration@v2
```

不使用：

```text
samplereverse-frontier@v2
```

原因：本轮不是 samplereverse 样本前沿推进，不涉及 candidate、frontier、artifact freshness、runtime evidence 推进。

## 3. Do Not Do

严禁：

```text
1. 不修改 .codex-skills/、registry、sync 脚本或 skill 内容。
2. 不运行 samplereverse harness。
3. 不运行 Base64/RC4 breakpoint probe。
4. 不运行任何真实逆向 runtime probe。
5. 不读取完整 solve_reports/。
6. 不读取完整 PROJECT_PROGRESS_LOG.txt。
7. 不提交任何 .exe、.dll、.bin、.zip、.7z、.rar 样本文件。
8. 不提交 local_reverse_samples/ 目录内的任何实际内容。
9. 不把 local_reverse_samples/ 放进 project_state/。
10. 不把 local_reverse_samples/ 放进 solve_reports/。
11. 不把 local_reverse_samples/ 设计成长期事实源。
12. 不引入数据库、消息队列、重型 workflow 平台。
13. 不新增复杂训练材料 schema/lint，除非当前最小需求无法满足。
```

特别注意：

```text
Git 不跟踪空目录。因此如果 local_reverse_samples/ 整个目录被 .gitignore 忽略，那么该目录本身不会出现在 GitHub 上。Codex 可以在本地创建该目录用于用户使用，但它不应出现在 git diff 中。
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

代码/文档必须检查：

```text
.gitignore
README.txt
reverse_agent/harness.py
tests/test_harness.py
```

可以有界检查：

```text
tests/
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
1. 当前 .gitignore 是否已经忽略 local_reverse_samples/。
2. 当前 README.txt 是否已经说明 local_reverse_samples/ 的用途。
3. README.txt 是否明确说明 local_reverse_samples/ 不上传 GitHub。
4. README.txt 是否给出 harness 使用 local_reverse_samples/**/case.json 的示例。
5. 是否没有提交任何真实 .exe/.dll/.bin/.zip/.7z/.rar 样本。
6. 是否没有修改 .codex-skills/。
7. 是否没有运行 reverse runtime probe。
8. 是否没有读取完整 solve_reports/。
9. 是否没有改变 samplereverse 当前解题主线。
10. codex_execution_report.md 顶部必须包含 codex_report_summary。
11. codex_report_summary.based_on_decision_id 必须等于 decision_20260531_local_reverse_samples_ignore。
12. pytest_result.txt 必须记录本轮实际检查命令。
```

## 6. Implementation Scope

允许修改：

```text
.gitignore
README.txt
project_state/codex_execution_report.md
project_state/pytest_result.txt
```

允许本地创建但不提交：

```text
local_reverse_samples/
local_reverse_samples/.local_README.txt
```

如果创建 `local_reverse_samples/.local_README.txt`，必须确认它被 `.gitignore` 忽略，不应出现在 `git diff --name-only` 中。

推荐 `.gitignore` 修改：

```gitignore
local_reverse_samples/
```

推荐 README.txt 新增内容位置：

```text
放在“项目结构”部分，紧接 solve_reports/project_state 说明附近；
或者放在“批量 Harness”部分，说明本地 dataset 可以位于 local_reverse_samples/ 下。
```

推荐 README.txt 新增说明：

```text
- `local_reverse_samples\`：本地逆向训练样本目录，用于放置用户自己的 `.exe`、`.dll`、题目附件、notes 和 harness `case.json`。该目录被 `.gitignore` 忽略，不提交 GitHub；适合保存版权不明确、体积较大、可能包含恶意逻辑或仅限本地使用的逆向例题。
```

推荐 README.txt 中给出示例：

```json
{
  "cases": [
    {
      "case_id": "crackme-sha256-001",
      "input_value": "local_reverse_samples/crackme_sha256_001/sample.exe",
      "expected_flag": "",
      "category": "hash_check",
      "tags": ["sha256", "static", "crackme"],
      "notes": "本地 SHA-256 判断类逆向练习样本"
    }
  ]
}
```

推荐 README.txt 中给出运行命令：

```powershell
python -m reverse_agent.harness --dataset .\local_reverse_samples\crackme_sha256_001\case.json --run-name crackme_sha256_001
```

可选本地初始化动作：

```powershell
mkdir local_reverse_samples
```

注意：这个目录被忽略后不会上传 GitHub，这是预期行为。

## 7. Tests

必须运行：

```text
git diff --check
git status --short
git check-ignore -v local_reverse_samples/
python -m py_compile reverse_agent/harness.py
python -m pytest -q tests/test_harness.py
python -m reverse_agent.project_state lint-decision --state-dir project_state
```

如果修改了 `project_state/codex_execution_report.md`，还必须运行：

```text
python -m reverse_agent.project_state lint-report --state-dir project_state
```

不要求运行：

```text
python -m pytest -q
真实 samplereverse harness
Base64/RC4 runtime breakpoint probe
任何 IDA/Olly/Frida runtime probe
```

如果 `git check-ignore -v local_reverse_samples/` 在目录不存在时无法验证，Codex 应先本地创建空目录：

```powershell
mkdir local_reverse_samples
```

然后重新运行：

```text
git check-ignore -v local_reverse_samples/
```

该目录仍不得进入 git diff。

## 8. Stop Conditions

立即停止并报告 `BLOCKED`：

```text
1. .gitignore 规则无法忽略 local_reverse_samples/。
2. README.txt 与现有项目结构冲突，无法安全插入本地样本目录说明。
3. Codex 发现仓库已有同名目录且已被跟踪，需要用户决定是否迁移。
4. lint-decision 因当前 decision_meta 与 project_state 状态不兼容而失败，且无法在本轮安全修正。
5. 任何测试要求必须运行真实逆向样本或 runtime probe 才能验证本轮变更。
```

完成条件：

```text
1. .gitignore 包含 local_reverse_samples/。
2. README.txt 说明 local_reverse_samples/ 是本地逆向例题目录。
3. README.txt 明确说明该目录不上传 GitHub。
4. README.txt 给出 harness dataset 示例和运行命令。
5. git check-ignore 能确认 local_reverse_samples/ 被忽略。
6. git diff 中不包含 local_reverse_samples/ 下任何文件。
7. 未修改 .codex-skills/。
8. 未运行逆向 runtime probe。
9. codex_execution_report.md、pytest_result.txt 与 decision_20260531_local_reverse_samples_ignore 对齐。
```
