```json decision_meta
{
  "schema_version": 1,
  "decision_id": "decision_20260531_rename_local_samples_to_uploadable_corpus",
  "round_id": "round_20260531_rename_local_samples_to_uploadable_corpus",
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

本轮属于 **engineering_branch**。目标是按用户最新要求，将原本被忽略的本地样本目录 `local_reverse_samples/` **改名**为可提交的受控样本语料目录 `sample_corpus/reverse/`，并在该目录内完成样本规范化和上传准备。

本轮不是“额外复制一份新目录并保留原样本目录”。本轮要求是：

```text
local_reverse_samples/   ->   sample_corpus/reverse/
```

也就是把原目录改名/移动为新的可提交语料库目录，再整理内部结构后提交。`local_reverse_samples/` 以后仍可作为临时本地导入目录名称保留在 `.gitignore` 中，但本轮不应保留第二份同内容样本副本。

当前 Codex 实际执行权威是本文件 `project_state/decision_packet.md`。`project_state/task_packet.json` 中的 `task` / `derived_task` 仍是旧 reverse_solving 状态派生建议，不自动覆盖本 decision。

## 1. Goal

将当前本地目录：

```text
local_reverse_samples/
  cpp_6af7c7f1/
  cpp.exe
  desenc.exe
  rc4enc.exe
  SEH.exe
```

改名并整理为：

```text
sample_corpus/reverse/
  README.md
  manifest.json

  cpp_6af7c7f1/
    sample.exe
    metadata.json
    case.json
    notes.md
    codex_task.md
    analysis_notes.md      # 若已有且可提交，需脱敏后保留；否则可不提交
    solve_result.json      # 若已有且可提交，需脱敏后保留；否则可不提交

  desenc_<sha8>/
    sample.exe
    metadata.json
    case.json
    notes.md
    codex_task.md

  rc4enc_<sha8>/
    sample.exe
    metadata.json
    case.json
    notes.md
    codex_task.md

  SEH_<sha8>/
    sample.exe
    metadata.json
    case.json
    notes.md
    codex_task.md
```

核心目标：

```text
1. 将 local_reverse_samples/ 原目录改名/移动为 sample_corpus/reverse/。
2. 不额外保留第二份 local_reverse_samples/ 样本副本。
3. 保留 .gitignore 中的 local_reverse_samples/ 规则，用于未来临时导入目录防误提交。
4. 确保 sample_corpus/reverse/ 不被 .gitignore 忽略。
5. 整理 sample_corpus/reverse/ 根目录裸 .exe，使每个样本进入独立 case 目录。
6. 每个 case 必须有 sample.exe / metadata.json / case.json / notes.md / codex_task.md。
7. 每个 metadata.json 必须记录 sha256、size_bytes、upload_allowed=true、safe_to_run=false。
8. 生成 sample_corpus/reverse/manifest.json。
9. 新增或更新 README.txt，说明可提交样本语料库和临时本地导入目录的区别。
10. 新增 tests/test_sample_corpus.py，验证 corpus 结构、metadata 和 hash。
```

## 2. Current Evidence

用户明确修正了上传方案：不是复制到一个额外的新目录，而是把原来的 `F:\reverse-agent\local_reverse_samples` 改名后上传。

当前用户截图显示本地目录为：

```text
local_reverse_samples/
  cpp_6af7c7f1/
  cpp.exe
  desenc.exe
  rc4enc.exe
  SEH.exe
```

这说明：

```text
1. 当前目录混合了一个已规范 case 目录和多个根目录裸 .exe。
2. 原先 local-only 语义已经改变：用户明确允许这些本地训练样本上传。
3. 不能直接提交当前混合结构；需要在改名后的 sample_corpus/reverse/ 内完成规范化。
```

上一轮本地样本相关工作已产生：

```text
1. cpp_6af7c7f1 已有本地 solver 结果，candidate = higuys。
2. reverse_agent/simple_static_patterns.py 已新增轻量静态模式 helper。
3. 之前报告指出根目录裸 .exe 未规范化，这是本轮必须修正的核心问题。
```

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
1. 不把 local_reverse_samples/ 原样提交为混合结构。
2. 不同时保留两份相同样本副本：local_reverse_samples/ 和 sample_corpus/reverse/。
3. 不提交 sample_corpus/reverse/ 根目录裸 .exe。
4. 不提交没有 metadata.json 的 .exe。
5. 不提交没有 sha256 / size_bytes / upload_allowed / safe_to_run 字段的样本。
6. 不执行未知 sample.exe。
7. 不运行 IDA/Olly/Frida runtime probe。
8. 不运行 Base64/RC4 breakpoint probe。
9. 不运行 samplereverse harness。
10. 不修改 .codex-skills/。
11. 不读取完整 solve_reports/。
12. 不读取完整 PROJECT_PROGRESS_LOG.txt。
13. 不提交 solve_reports/。
14. 不把 sample_corpus/reverse/ 当作动态运行产物目录。
15. 不把未脱敏的本地绝对路径写入 corpus metadata。
```

特别限制：

```text
1. 所有上传样本 safe_to_run 必须是 false。
2. 所有上传样本 upload_allowed 必须是 true。
3. 本轮只做目录改名、样本结构规范化、metadata 补齐和 corpus 测试；不执行样本二进制。
4. 如果 sample_corpus/reverse/ 已存在且非空，必须先审计是否为旧 corpus；不能盲目覆盖。
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
local_reverse_samples/*/notes.md
local_reverse_samples/*/codex_task.md
local_reverse_samples/*/solve_result.json
local_reverse_samples/*/analysis_notes.md
sample_corpus/reverse/        # 若已存在，必须检查是否可安全合并或应 BLOCKED
.gitignore
README.txt
```

允许新增并提交：

```text
sample_corpus/reverse/README.md
sample_corpus/reverse/manifest.json
sample_corpus/reverse/<case_id>/sample.exe
sample_corpus/reverse/<case_id>/metadata.json
sample_corpus/reverse/<case_id>/case.json
sample_corpus/reverse/<case_id>/notes.md
sample_corpus/reverse/<case_id>/codex_task.md
tests/test_sample_corpus.py
```

允许有条件提交：

```text
sample_corpus/reverse/<case_id>/analysis_notes.md
sample_corpus/reverse/<case_id>/solve_result.json
```

条件：内容必须不包含本地绝对敏感路径、不包含完整反汇编 dump、不包含不适合提交的临时数据。

允许修改：

```text
.gitignore
README.txt
project_state/codex_execution_report.md
project_state/pytest_result.txt
```

不应修改：

```text
.codex-skills/
reverse_agent/strategies/compare_aware_search.py
reverse_agent/profiles/samplereverse.py
reverse_agent/harness.py
reverse_agent/local_samples.py
```

如果必须修改 `local_samples.py` 或 `harness.py` 才能完成，停止并报告 `BLOCKED`，不要扩大范围。

## 5. Required Audit

Codex 报告必须回答：

```text
1. 是否将 local_reverse_samples/ 改名/移动为 sample_corpus/reverse/，而不是复制后保留两份样本。
2. 如果仍存在 local_reverse_samples/，它是否为空或仅作为未来临时导入目录；是否不包含旧样本副本。
3. sample_corpus/reverse/ 根目录是否还存在裸 .exe。
4. 本轮发现了哪些本地样本。
5. 每个样本对应的 case_id 是什么。
6. 每个样本的 sha256 / size_bytes 是什么。
7. 每个样本是否有 metadata.json / case.json / notes.md / codex_task.md。
8. 每个样本 metadata.json 是否包含 upload_allowed=true。
9. 每个样本 metadata.json 是否包含 safe_to_run=false。
10. 是否生成 sample_corpus/reverse/manifest.json。
11. 是否生成 sample_corpus/reverse/README.md。
12. 是否新增 tests/test_sample_corpus.py。
13. tests/test_sample_corpus.py 是否校验实际 sample.exe 的 sha256。
14. .gitignore 是否仍然忽略 local_reverse_samples/。
15. .gitignore 是否没有忽略 sample_corpus/reverse/。
16. 是否没有执行任何 sample.exe。
17. 是否没有运行 runtime probe。
18. 是否没有提交 solve_reports/。
19. 是否没有修改 .codex-skills/。
20. 是否没有修改 samplereverse 主线。
21. codex_report_summary 是否包含 files_changed / tests_ran / generated_artifacts。
22. 是否确认这些二进制文件是用户明确允许上传的本地训练样本。
```

## 6. Implementation Scope

### 6.1 Precheck

必须先执行并记录：

```powershell
Test-Path .\local_reverse_samples
Test-Path .\sample_corpus\reverse
git check-ignore -v local_reverse_samples/
git check-ignore -v sample_corpus/reverse/
```

预期：

```text
1. local_reverse_samples/ 存在。
2. sample_corpus/reverse/ 不存在，或存在但为空/可安全合并。
3. local_reverse_samples/ 被 .gitignore 忽略。
4. sample_corpus/reverse/ 不应被 .gitignore 忽略。
```

如果 `sample_corpus/reverse/` 已存在且非空，必须停止并报告 `BLOCKED`，除非能证明它是同一批样本的未完成迁移结果且可安全继续。

### 6.2 Rename / Move 原目录

推荐 Windows PowerShell 操作：

```powershell
New-Item -ItemType Directory -Force .\sample_corpus | Out-Null
Move-Item .\local_reverse_samples .\sample_corpus\reverse
```

移动后目录应为：

```text
sample_corpus/reverse/
  cpp_6af7c7f1/
  cpp.exe
  desenc.exe
  rc4enc.exe
  SEH.exe
```

然后在 `sample_corpus/reverse/` 内部规范化。

### 6.3 Normalize root-level exe files

对改名后的根目录裸 `.exe` 做整理：

```text
sample_corpus/reverse/cpp.exe
sample_corpus/reverse/desenc.exe
sample_corpus/reverse/rc4enc.exe
sample_corpus/reverse/SEH.exe
```

规则：

```text
1. 对每个根目录裸 .exe 计算 sha256 和 size_bytes。
2. case_id 使用 <stem>_<sha256前8位>。
3. 如果已存在同 sha256 的 case 目录，例如 cpp_6af7c7f1/sample.exe：
   - 记录 duplicate_root_sample。
   - 不创建重复 case。
   - 从可提交 corpus 中移除根目录重复 .exe，避免同一样本提交两份。
4. 对非重复裸 .exe：
   - 创建 sample_corpus/reverse/<case_id>/。
   - 移动该 .exe 到 <case_id>/sample.exe。
   - 生成 metadata.json / case.json / notes.md / codex_task.md。
5. 完成后 sample_corpus/reverse/ 根目录不得再有裸 .exe。
```

如果 Codex 不确定是否可以删除重复根目录附件，应优先把重复项移入 `_duplicates/` 吗？不允许。本轮要求最终可提交 corpus 不能包含根目录裸 `.exe`，重复项应不进入提交；如果无法安全移除，停止并报告 `BLOCKED`。

### 6.4 metadata.json 格式

每个样本写：

```json
{
  "schema_version": 1,
  "case_id": "<case_id>",
  "sample_filename": "sample.exe",
  "sample_path": "sample_corpus/reverse/<case_id>/sample.exe",
  "sha256": "<sha256>",
  "size_bytes": 0,
  "source": "renamed_from_local_reverse_samples",
  "upload_allowed": true,
  "safe_to_run": false,
  "analysis_mode": "Static Analysis",
  "category": "unknown",
  "tags": [
    "reverse",
    "local-sample",
    "curated"
  ],
  "created_at": "<iso8601>"
}
```

不得写入 `F:\...` 这类本地绝对路径。

### 6.5 case.json 格式

每个样本写：

```json
{
  "cases": [
    {
      "case_id": "<case_id>",
      "input_value": "sample_corpus/reverse/<case_id>/sample.exe",
      "expected_flag": "",
      "category": "unknown",
      "tags": [
        "reverse",
        "local-sample",
        "curated"
      ],
      "notes": "Curated reverse training sample. Static analysis first. Do not execute by default."
    }
  ]
}
```

### 6.6 codex_task.md 格式

每个样本都应有 `codex_task.md`，至少说明：

```text
1. case_id
2. sample path
3. sha256 / size_bytes
4. static-first analysis requirement
5. do not execute sample.exe by default
6. do not run runtime probe unless explicitly authorized
7. expected local solver path if user later asks to solve this case
```

### 6.7 manifest.json 格式

写入：

```json
{
  "schema_version": 1,
  "generated_at": "<iso8601>",
  "source_directory": "local_reverse_samples renamed to sample_corpus/reverse",
  "samples": [
    {
      "case_id": "<case_id>",
      "path": "sample_corpus/reverse/<case_id>/sample.exe",
      "sha256": "<sha256>",
      "size_bytes": 0,
      "category": "unknown",
      "safe_to_run": false,
      "upload_allowed": true
    }
  ]
}
```

### 6.8 README updates

新增：

```text
sample_corpus/reverse/README.md
```

必须说明：

```text
1. 该目录是可提交的 curated reverse sample corpus。
2. 样本由用户明确允许上传。
3. 样本默认只用于静态分析训练。
4. safe_to_run=false，禁止默认在宿主机直接执行。
5. 每个样本必须有 metadata.json / case.json / notes.md / codex_task.md。
```

更新根 `README.txt`：

```text
1. local_reverse_samples/：未来临时本地导入目录，仍然被 .gitignore 忽略。
2. sample_corpus/reverse/：可提交、可审计、可复现的精选逆向样本库。
3. 不要把临时 solver.py 或运行产物提交到 sample_corpus/reverse/，除非经过专门脱敏和审查。
```

### 6.9 .gitignore update

保留：

```gitignore
local_reverse_samples/
```

确保没有：

```gitignore
sample_corpus/
sample_corpus/reverse/
```

如果存在 broader ignore 导致 `sample_corpus/reverse/` 被忽略，必须修正或报告 `BLOCKED`。

## 7. Tests

新增：

```text
tests/test_sample_corpus.py
```

测试必须检查：

```text
1. sample_corpus/reverse/manifest.json 存在。
2. manifest 中每个 sample path 存在。
3. sample_corpus/reverse/ 根目录不存在裸 .exe。
4. 每个 sample case 有 metadata.json / case.json / notes.md / codex_task.md。
5. 每个 metadata.json 有 sha256 / size_bytes / safe_to_run / upload_allowed。
6. 每个 sample.exe 的实际 sha256 与 metadata.json 一致。
7. 每个 safe_to_run 必须是 false。
8. 每个 upload_allowed 必须是 true。
9. case.json 的 input_value 指向 sample_corpus/reverse/<case_id>/sample.exe。
10. metadata.json 不包含本地绝对路径。
```

必须运行：

```text
python -m pytest -q tests/test_sample_corpus.py
git status --short
git check-ignore -v local_reverse_samples/
git check-ignore -v sample_corpus/reverse/
python -m reverse_agent.project_state lint-decision --state-dir project_state
python -m reverse_agent.project_state lint-report --state-dir project_state
git diff --check
```

如果保留或修改 `simple_static_patterns.py`，还必须运行：

```text
python -m py_compile reverse_agent/simple_static_patterns.py
python -m pytest -q tests/test_simple_static_patterns.py
```

不要求运行：

```text
python -m pytest -q
任何 sample.exe
IDA/Olly/Frida runtime probe
samplereverse harness
Base64/RC4 runtime probe
```

## 8. Stop Conditions

立即停止并报告 `BLOCKED`：

```text
1. 用户没有明确允许上传样本。
2. local_reverse_samples/ 不存在。
3. sample_corpus/reverse/ 已存在且非空，无法确认是否可安全合并。
4. 样本文件不存在或无法读取。
5. 样本疑似超过 GitHub 普通文件大小限制或不适合普通 Git 存储。
6. 无法计算 sha256。
7. 无法生成 metadata.json / case.json / manifest.json。
8. tests/test_sample_corpus.py 无法通过。
9. 必须执行 sample.exe 才能完成。
10. 必须修改 local_samples.py 或 harness.py 才能完成。
11. 必须上传 solve_reports/ 或 project_state 动态运行产物才能完成。
```

完成条件：

```text
1. local_reverse_samples/ 已改名/移动为 sample_corpus/reverse/，未保留第二份同内容样本副本。
2. local_reverse_samples/ 如仍存在，应为空或仅作为未来临时导入目录，且仍被 .gitignore 忽略。
3. sample_corpus/reverse/ 已创建并可被 Git 跟踪。
4. sample_corpus/reverse/ 根目录没有裸 .exe。
5. 用户允许上传的样本都位于 sample_corpus/reverse/<case_id>/sample.exe。
6. 每个样本有 metadata.json / case.json / notes.md / codex_task.md。
7. manifest.json 完整记录所有样本。
8. tests/test_sample_corpus.py 通过。
9. 未执行任何 sample.exe。
10. 未运行 runtime probe。
11. codex_execution_report.md 和 pytest_result.txt 与本 decision 对齐。
```

本轮核心是目录语义迁移：`local_reverse_samples/` 不再承载这批要上传的样本；这批样本改名迁移为 `sample_corpus/reverse/`，作为可审计、可复现、可提交的逆向样本语料库。
