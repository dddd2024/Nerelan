```json decision_meta
{
  "schema_version": 1,
  "decision_id": "decision_20260531_rework_local_sample_normalization_and_batch_solver",
  "round_id": "round_20260531_rework_local_sample_normalization_and_batch_solver",
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

本轮属于 **engineering_branch**，是对上一轮 `decision_20260531_local_simple_batch_solver_capability_extraction` 的返工。

上一轮核心问题是：`local_reverse_samples/` 根目录中仍存在裸 `.exe` 样本，没有按 `local_samples add/solve` 规范整理成 `<case_id>/` 目录；同时只处理了 `cpp_6af7c7f1` 一个样本，并过早跳过 DES/RC4/SEH 相关样本。

当前 Codex 实际执行权威是本文件 `project_state/decision_packet.md`。`project_state/task_packet.json` 中的 `task` / `derived_task` 仍是旧 reverse_solving 状态派生建议，不自动覆盖本 decision。

## 1. Goal

修正本地样本目录规范，并重新执行受限批量解题：

```text
1. 扫描 local_reverse_samples/ 根目录下的裸 .exe 文件。
2. 对每个裸 .exe 使用现有 local_samples intake 流程登记成 case 目录。
3. 确保每个样本都有：
   - metadata.json
   - case.json
   - notes.md
   - codex_task.md
   - sample.exe
4. 对 3–5 个 case 做静态分析。
5. 能解则写本地 solver.py 和 solve_result.json。
6. 不能解则写 SKIPPED_STATIC_INSUFFICIENT，不允许无证据地写 runtime_required。
7. 项目级 simple_static_patterns.py 只保留有样本证据支撑的能力，或者把无样本证据的函数降级为未推广 helper。
8. 修复 codex_report_summary 字段完整性。
```

## 2. Current Evidence

用户截图显示本地目录当前为：

```text
local_reverse_samples/
  cpp_6af7c7f1/
  cpp.exe
  desenc.exe
  rc4enc.exe
  SEH.exe
```

其中只有 `cpp_6af7c7f1/` 是规范 case 目录；其余 `.exe` 仍裸放在根目录。

上一轮报告只处理了 `cpp_6af7c7f1`，并跳过 `SEH.exe`、`desenc.exe`、`rc4enc.exe`。上一轮报告还把它们直接归为 DES/RC4/SEH 相关并标记为需要动态分析，但缺少足够静态证据。

当前项目级能力文件 `reverse_agent/simple_static_patterns.py` 已新增，但其支持范围包含 affine、Caesar、XOR、hash digest detection。当前明确有样本证据支撑的是 `affine_lowercase_transform`；其他 helper 若保留，报告中必须明确它们是 generic helper，不是本轮样本沉淀出的能力。

当前 skill profiles：

```text
reverse-agent-iteration@v2
```

不使用：

```text
samplereverse-frontier@v2
```

原因：本轮不推进 `samplereverse` 样本，不涉及 candidate、frontier、runtime evidence 或 artifact freshness 推进。

## 3. Do Not Do

严禁：

```text
1. 不提交 local_reverse_samples/ 下任何内容。
2. 不提交 .exe/.dll/.bin/.zip/.7z/.rar。
3. 不执行未知 sample.exe。
4. 不运行 IDA/Olly/Frida runtime probe。
5. 不运行 Base64/RC4 breakpoint probe。
6. 不运行 samplereverse harness。
7. 不修改 .codex-skills/。
8. 不修改 CompareAwareSearchStrategy。
9. 不修改 reverse_agent/profiles/samplereverse.py。
10. 不读取完整 solve_reports/。
11. 不读取完整 PROJECT_PROGRESS_LOG.txt。
12. 不把无样本证据支撑的 pattern 作为“已沉淀能力”宣传。
13. 不把本轮扩展成自动训练平台、数据库、队列、多 worker 或后台任务系统。
```

## 4. Files To Inspect

默认读取：

```text
project_state/task_packet.json
project_state/current_state.json
project_state/artifact_index.json
project_state/negative_results.json
project_state/codex_execution_report.md
project_state/decision_packet.md
project_state/pytest_result.txt
```

必须本地检查：

```text
local_reverse_samples/
local_reverse_samples/*.exe
local_reverse_samples/*/metadata.json
local_reverse_samples/*/case.json
local_reverse_samples/*/codex_task.md
local_reverse_samples/*/notes.md
```

允许修改并提交：

```text
reverse_agent/simple_static_patterns.py
tests/test_simple_static_patterns.py
project_state/codex_execution_report.md
project_state/pytest_result.txt
```

允许本地新增或修改但不得提交：

```text
local_reverse_samples/<case_id>/analysis_notes.md
local_reverse_samples/<case_id>/solver.py
local_reverse_samples/<case_id>/solve_result.json
```

不应修改：

```text
reverse_agent/local_samples.py
reverse_agent/harness.py
reverse_agent/strategies/compare_aware_search.py
reverse_agent/profiles/samplereverse.py
.codex-skills/
```

如果发现必须修改 `local_samples.py` 或 `harness.py` 才能完成本轮目标，停止并报告 `BLOCKED`，不要扩大范围。

## 5. Required Audit

Codex 报告必须回答：

```text
1. 根目录下发现了哪些裸 .exe。
2. 每个裸 .exe 是否已经登记成 case 目录。
3. 每个 case_id 是什么。
4. 每个 case 是否有 metadata.json / case.json / notes.md / codex_task.md。
5. 根目录裸 .exe 是否被删除、移动或保留；如果保留，理由是什么。
6. 每个样本是否只做静态分析。
7. 每个样本的初步分类是什么。
8. 每个样本是否生成 solver.py。
9. 每个 solver.py 是否运行。
10. 每个样本 solve_result.json 的 status 是什么。
11. 对 DES/RC4/SEH 样本，如果跳过，必须给出静态证据，而不是只按文件名判断。
12. simple_static_patterns.py 中哪些能力有样本证据。
13. 哪些能力只是 helper，不能声明为本轮样本沉淀能力。
14. codex_report_summary 是否包含 files_changed / tests_ran / generated_artifacts。
15. 是否没有提交 local_reverse_samples/ 内容。
16. 是否没有执行 sample.exe。
17. 是否没有运行 runtime probe。
18. 是否没有修改 .codex-skills/。
19. 是否没有修改 samplereverse 主线。
20. 是否没有读取完整 solve_reports/ 或 PROJECT_PROGRESS_LOG.txt。
```

## 6. Implementation Scope

### 6.1 规范化本地样本目录

对根目录裸 `.exe` 执行规范化登记。

推荐命令：

```powershell
python -m reverse_agent.local_samples add .\local_reverse_samples\desenc.exe
python -m reverse_agent.local_samples add .\local_reverse_samples\rc4enc.exe
python -m reverse_agent.local_samples add .\local_reverse_samples\SEH.exe
```

如果 `cpp.exe` 已经对应 `cpp_6af7c7f1/`，则：

```text
1. 校验 cpp.exe 与 cpp_6af7c7f1/sample.exe 的 sha256 是否一致。
2. 如果一致，记录为 duplicate_root_sample。
3. 不要重复创建 case。
```

对每个新登记的样本继续执行：

```powershell
python -m reverse_agent.local_samples solve <case_id>
```

以生成 `codex_task.md`。

注意：如果 `local_samples add` 默认复制而不是移动裸 `.exe`，Codex 不应自行删除原始裸 `.exe`。应在报告里明确记录：root sample retained as local source attachment and ignored by Git。若要删除或移动根目录原始附件，必须等待用户确认。

### 6.2 静态 triage

对每个 case 做静态 triage：

```text
1. 提取 ASCII / UTF-16LE 字符串。
2. 查看 PE imports。
3. 搜索 key/password/flag/input/correct/wrong/success/fail。
4. 搜索 DES/RC4/Base64/hash/XOR/rotate/SEH 特征。
5. 判断能否纯静态写 solver。
```

如果不能解，状态必须是：

```text
SKIPPED_STATIC_INSUFFICIENT
```

只有在确有静态证据说明必须运行样本才能继续时，才允许写：

```text
SKIPPED_RUNTIME_REQUIRED
```

不允许只根据文件名 `desenc` / `rc4enc` / `SEH` 判定 runtime_required。

### 6.3 修正 simple_static_patterns.py 范围

二选一：

```text
A. 只保留 affine_lowercase_transform 作为本轮沉淀能力；
B. 保留 Caesar/XOR/hash helper，但报告必须明确它们是 generic helper，不是本轮样本证据沉淀能力。
```

如果保留 helper，测试可以保留；但 `codex_execution_report.md` 不能写成这些能力都来自本轮样本。

### 6.4 修正报告 meta

`codex_report_summary` 顶部必须包含：

```json
{
  "schema_version": 1,
  "report_id": "report_20260531_rework_local_sample_normalization_and_batch_solver",
  "round_id": "round_20260531_rework_local_sample_normalization_and_batch_solver",
  "based_on_decision_id": "decision_20260531_rework_local_sample_normalization_and_batch_solver",
  "status": "SUCCESS | PARTIAL | BLOCKED",
  "acceptance_recommendation": "ACCEPTED | ACCEPTED_WITH_LIMITATIONS | REWORK_REQUIRED | BLOCKED",
  "files_changed": [],
  "tests_ran": [],
  "generated_artifacts": []
}
```

`generated_artifacts` 可以列出 ignored local artifacts，但必须明确它们没有提交 Git。

## 7. Tests

必须运行：

```text
python -m py_compile reverse_agent/simple_static_patterns.py
python -m pytest -q tests/test_simple_static_patterns.py
git status --short
git check-ignore -v local_reverse_samples/
python -m reverse_agent.project_state lint-decision --state-dir project_state
python -m reverse_agent.project_state lint-report --state-dir project_state
git diff --check
```

如果生成了多个 solver.py，则逐个运行：

```powershell
python .\local_reverse_samples\<case_id>\solver.py
```

不要求运行：

```text
python -m pytest -q
真实 sample.exe
IDA/Olly/Frida runtime probe
samplereverse harness
Base64/RC4 runtime probe
```

## 8. Stop Conditions

立即停止并报告 `BLOCKED`：

```text
1. local_samples add 无法登记根目录裸 .exe。
2. local_samples solve 无法生成 codex_task.md。
3. 必须执行 sample.exe 才能继续。
4. 必须运行 IDA/Olly/Frida runtime probe。
5. 必须提交 local_reverse_samples/ 内容。
6. 必须修改 local_samples.py 或 harness.py。
7. lint-report 无法通过且不是本轮可安全修复的问题。
```

完成条件：

```text
1. 根目录裸 .exe 已被登记为规范 case，或明确记录为 duplicate_root_sample / retained_source_attachment。
2. 每个登记 case 都有 metadata.json / case.json / notes.md / codex_task.md。
3. 至少重新 triage 3 个本地样本；如果不足 3 个，报告实际原因。
4. 能静态解的样本生成 solver.py / solve_result.json。
5. 不能静态解的样本给出 SKIPPED_STATIC_INSUFFICIENT 及静态证据。
6. simple_static_patterns.py 的能力边界与样本证据一致。
7. codex_report_summary 字段完整。
8. local_reverse_samples/ 内容没有进入 Git。
9. 未执行未知样本。
10. 未运行 runtime probe。
```

这轮返工的重点不是继续加新能力，而是先把本地样本目录治理回规范状态，再做有证据的静态 triage。
