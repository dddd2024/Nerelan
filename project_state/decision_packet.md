```json decision_meta
{
  "schema_version": 1,
  "decision_id": "decision_20260531_local_simple_batch_solver_capability_extraction",
  "round_id": "round_20260531_local_simple_batch_solver_capability_extraction",
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

本轮属于 **engineering_branch**。目标是把 `local_reverse_samples/` 中多个简单本地逆向题的解题过程，与项目级通用能力提炼合并成一轮小步可审计任务。

本轮不是继续推进旧 `samplereverse` 主线。当前 `task_packet.task` / `derived_task` 仍然是旧 `samplereverse` 状态派生建议，不能作为本轮执行权威；本轮以本文件 `project_state/decision_packet.md` 为准。

## 1. Goal

本轮做两件事，但必须合并在同一个受限闭环内：

```text
A. 批量解 3–5 个简单 local_reverse_samples 样本；
B. 从这些解题过程里提炼 1 个轻量通用能力。
```

目标结构：

```text
local_reverse_samples/<case_id>/
  sample.exe 或 sample.<ext>
  case.json
  metadata.json
  notes.md
  codex_task.md
  analysis_notes.md       # 本轮可更新，但不得提交 Git
  solver.py               # 本轮可生成，但不得提交 Git
  solve_result.json       # 本轮可生成，但不得提交 Git
```

项目级允许新增一个轻量能力文件，例如：

```text
reverse_agent/simple_static_patterns.py
tests/test_simple_static_patterns.py
```

该能力只服务于简单题型，不要接入复杂 agent runtime。

本轮优先提炼的 pattern：

```text
1. simple string compare
2. lowercase affine alphabet transform + literal compare
3. xor single-byte / repeating-key transform
4. Caesar / ROT / add-sub constant transform
5. MD5 / SHA1 / SHA256 literal hash check
6. Base64 literal decode / compare
```

其中 `lowercase affine alphabet transform + literal compare` 已有上一轮样本证据：目标字符串 `qvldxt`、小写输入约束、affine alphabet transform，solver 输出 `higuys`。

## 2. Current Evidence

上一轮完成：

```text
decision_id = decision_20260531_local_sample_single_solver_round
report_id = report_20260531_local_sample_single_solver_round
status = SUCCESS
acceptance_recommendation = ACCEPTED
```

上一轮报告记录：

```text
case_id = cpp_6af7c7f1
classification = string_compare
solver output = higuys
sample.exe executed = no
runtime probe used = no
local_reverse_samples content submitted = no
```

上一轮测试记录：

```text
python .\local_reverse_samples\cpp_6af7c7f1\solver.py
git status --short
git check-ignore -v local_reverse_samples/
python -m reverse_agent.project_state lint-decision --state-dir project_state
python -m reverse_agent.project_state lint-report --state-dir project_state
git diff --check
```

当前 `local_reverse_samples/` 已被 `.gitignore` 忽略，因此本轮可以在其中生成 solver 和分析记录，但不得提交这些文件。

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
2. 不提交 sample.exe / .dll / .bin / .zip / .7z / .rar。
3. 不提交每题 solver.py。
4. 不提交 solve_result.json。
5. 不执行未知 sample.exe。
6. 不运行 IDA/Olly/Frida runtime probe。
7. 不运行 Base64/RC4 breakpoint probe。
8. 不运行 samplereverse harness。
9. 不修改 CompareAwareSearchStrategy。
10. 不修改 reverse_agent/profiles/samplereverse.py。
11. 不修改 .codex-skills/。
12. 不读取完整 solve_reports/。
13. 不读取完整 PROJECT_PROGRESS_LOG.txt。
14. 不把本地样本内容写入 project_state。
15. 不把本轮做成自动训练平台、数据库、队列、多 worker 或后台任务系统。
16. 不一次性处理全部 local_reverse_samples。
17. 不把没有样本证据支撑的猜测 pattern 写成项目能力。
```

特别限制：

```text
本轮最多处理 5 个样本。
如果可用样本超过 5 个，只选择最简单、最适合静态分析的 3–5 个。
如果某个样本需要动态运行才能继续，跳过该样本并记录为 skipped_runtime_required。
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
local_reverse_samples/*/metadata.json
local_reverse_samples/*/case.json
local_reverse_samples/*/codex_task.md
local_reverse_samples/*/notes.md
```

允许读取样本字节：

```text
local_reverse_samples/<case_id>/sample.*
```

允许新增或修改但不得提交：

```text
local_reverse_samples/<case_id>/analysis_notes.md
local_reverse_samples/<case_id>/solver.py
local_reverse_samples/<case_id>/solve_result.json
```

允许提交的项目级文件：

```text
reverse_agent/simple_static_patterns.py
tests/test_simple_static_patterns.py
project_state/codex_execution_report.md
project_state/pytest_result.txt
```

不应修改：

```text
reverse_agent/local_samples.py
reverse_agent/harness.py
reverse_agent/strategies/compare_aware_search.py
reverse_agent/profiles/samplereverse.py
.codex-skills/
```

如果发现必须修改 `local_samples.py` 或 `harness.py` 才能继续，停止并报告 `BLOCKED`，不要扩大范围。

## 5. Required Audit

Codex 报告必须回答：

```text
1. 本轮选择了哪些 case_id。
2. 每个 case 的选择依据是什么。
3. 每个样本的 sha256 / size_bytes 是多少。
4. 每个样本是否只做静态分析。
5. 每个样本是否生成 solver.py。
6. 每个 solver.py 是否运行。
7. 每个 solver.py 输出了什么 candidate。
8. 每个 solve_result.json 的 status 是 SOLVED / PARTIAL / SKIPPED / BLOCKED 中哪一种。
9. 有哪些样本被跳过，跳过原因是什么。
10. 本轮归纳出了哪些 pattern。
11. 哪一个 pattern 被提升为项目级通用能力。
12. 该通用能力是否有至少一个本地样本证据支撑。
13. 是否新增 reverse_agent/simple_static_patterns.py。
14. 是否新增 tests/test_simple_static_patterns.py。
15. 是否没有提交 local_reverse_samples/ 内容。
16. 是否没有执行 sample.exe。
17. 是否没有运行 runtime probe。
18. 是否没有修改 .codex-skills/。
19. 是否没有修改 samplereverse 主线。
20. 是否没有读取完整 solve_reports/ 或 PROJECT_PROGRESS_LOG.txt。
```

## 6. Implementation Scope

### 6.1 选择样本

优先选择用户指定列表：

```powershell
$env:LOCAL_REVERSE_CASE_IDS
```

格式：

```text
case1,case2,case3
```

如果没有指定，则自动选择：

```text
1. 包含 metadata.json / case.json / codex_task.md 的 case；
2. 未存在 solve_result.json，或 solve_result.json.status != SOLVED；
3. 样本体积较小；
4. notes.md / codex_task.md 看起来是简单题；
5. 最多 5 个。
```

如果没有足够样本，也可以处理 1–2 个，不要强行造样本。

### 6.2 每题静态解题流程

对每个 case 执行：

```text
1. 读取 metadata.json / case.json / codex_task.md。
2. 读取 sample bytes。
3. 提取 ASCII / UTF-16LE 字符串。
4. 检查 imports。
5. 搜索常见提示字符串：
   - flag
   - password
   - serial
   - key
   - input
   - correct
   - wrong
   - success
   - fail
6. 搜索简单变换特征：
   - literal compare string
   - lowercase guard
   - XOR constant
   - add/sub constant
   - ROT/Caesar
   - MD5/SHA constants or 32/40/64 hex digest
   - Base64 alphabet
7. 写 analysis_notes.md。
8. 写 solver.py。
9. 运行 solver.py。
10. 写 solve_result.json。
```

### 6.3 pattern 归纳规则

对每题写一个本地 pattern summary：

```json
{
  "case_id": "<case_id>",
  "status": "SOLVED",
  "classification": "xor_or_bitshift | string_compare | hash_check | affine_lowercase | base64_or_encoding | unknown",
  "candidate": "<candidate>",
  "evidence": [
    "static string ...",
    "literal compare ...",
    "transform ..."
  ],
  "reusable_pattern": "<pattern name>"
}
```

然后在 `project_state/codex_execution_report.md` 里只写摘要，不写样本内容。

### 6.4 通用能力实现

本轮只允许实现一个轻量通用能力文件：

```text
reverse_agent/simple_static_patterns.py
```

建议提供纯函数，不接入 GUI / harness / runtime：

```python
def solve_affine_lowercase_literal(target: str, a: int, b: int) -> str | None:
    ...

def solve_caesar_lowercase_literal(target: str, shift: int) -> str:
    ...

def xor_bytes(data: bytes, key: bytes) -> bytes:
    ...

def detect_hex_digest_kind(s: str) -> str | None:
    ...
```

但本轮不要贪多。优先实现已有证据最强的：

```text
affine lowercase transform inverse
```

原因：上一轮已有样本 `cpp_6af7c7f1` 支撑该 pattern。

测试文件：

```text
tests/test_simple_static_patterns.py
```

最低测试：

```text
1. affine lowercase inverse 能从 qvldxt 还原 higuys。
2. 非小写输入返回 None 或抛出清晰错误。
3. Caesar/ROT helper 如果实现，必须有 round-trip 测试。
4. hex digest detector 如果实现，必须区分 md5/sha1/sha256 长度。
```

### 6.5 不接入策略主线

本轮不要把 `simple_static_patterns.py` 接入：

```text
CompareAwareSearchStrategy
samplereverse profile
GUI pipeline
harness runtime
```

原因：先把能力做成可测试库函数，下一轮再决定如何接入项目主流程。

## 7. Tests

必须运行：

```text
python .\local_reverse_samples\<case_id_1>\solver.py
python .\local_reverse_samples\<case_id_2>\solver.py
...
python -m py_compile reverse_agent/simple_static_patterns.py
python -m pytest -q tests/test_simple_static_patterns.py
git status --short
git check-ignore -v local_reverse_samples/
python -m reverse_agent.project_state lint-decision --state-dir project_state
python -m reverse_agent.project_state lint-report --state-dir project_state
git diff --check
```

如果本轮只实现本地 solver，没有新增项目级能力，则必须说明原因：

```text
No project-level pattern promoted because fewer than one reusable pattern had sufficient evidence.
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
1. local_reverse_samples/ 不存在。
2. 找不到任何包含 metadata.json / case.json / codex_task.md 的 case。
3. 所有样本都必须动态运行才能继续。
4. 必须修改 local_samples.py 或 harness.py 才能继续。
5. 必须提交 local_reverse_samples/ 内容才能完成。
6. 必须运行 IDA/Olly/Frida runtime probe。
7. 必须联网或下载外部资源。
8. lint-decision 或 lint-report 无法通过，且不是本轮可安全修复的问题。
```

完成条件：

```text
1. 解出或部分解出 3–5 个简单本地样本；如果不足 3 个，报告实际可用数量。
2. 每个处理过的样本都有 analysis_notes.md / solver.py / solve_result.json。
3. 所有 solver.py 都已运行，结果写入 pytest_result.txt。
4. 至少归纳出一个 reusable pattern。
5. 至少一个 pattern 被实现为 reverse_agent/simple_static_patterns.py 中的可测试纯函数；如果没有实现，必须给出明确证据不足原因。
6. tests/test_simple_static_patterns.py 通过。
7. local_reverse_samples/ 内容仍未进入 Git。
8. 未执行未知 sample.exe。
9. 未运行 runtime probe。
10. project_state/codex_execution_report.md 只记录摘要，不包含样本内容或完整 solver。
```

这个合并计划的核心是：本地 solver 作为训练材料，项目级 pattern 作为沉淀结果。每轮不是单纯“多解几题”，而是至少产出一个可测试、可复用的小能力。
