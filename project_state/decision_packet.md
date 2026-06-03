```json decision_meta
{
  "schema_version": 1,
  "decision_id": "decision_20260603_simple_reverse_training_corpus_bootstrap",
  "round_id": "round_20260603_simple_reverse_training_corpus_bootstrap",
  "based_on_state_build_id": "state_20260602_053948_4e3984041cd7",
  "based_on_state_digest": "4e3984041cd78e5a412e28a53fa3441957ea87f43f62a9688c3e80ca4413678c",
  "status": "APPROVED",
  "mainline": "reverse_solving",
  "skill_profiles": [
    "reverse-agent-iteration@v2"
  ]
}
```

# DECISION_PACKET

本轮正式改变方向：从当前 `samplereverse` 单样本深挖，切换到 **simple reverse training corpus bootstrap**。

当前 Codex 实际执行权威是本文件 `project_state/decision_packet.md`。`project_state/task_packet.json` 中的旧 `task` / `derived_task` / `sample=samplereverse` 只作为旧状态背景，不能覆盖本 decision。

本轮目标不是继续解决 `samplereverse`，而是让项目开始基于本地样本目录：

```text
E:\reverse
```

建立简单逆向题训练集的可审计、可复现、可逐步扩展的解题能力。

---

## 1. Goal

本轮目标是新增一个“简单逆向题训练集”入口，使项目能够：

1. 扫描 `E:\reverse` 下的本地样本文件。
2. 为每个样本生成轻量 metadata。
3. 自动识别简单题类型的初步线索。
4. 建立训练集索引，不直接提交样本二进制。
5. 为后续每一道简单题生成可执行的 bounded solve plan。
6. 输出机器可读的训练集状态文件，供下一轮 GPT/Codex 审查。

本轮只做 **corpus bootstrap + triage + harness skeleton**，不要直接追求解出全部题目。

最低验收目标：

```text
1. 能从 E:\reverse 扫描出样本列表。
2. 能识别常见二进制/脚本文件类型。
3. 能为每个样本生成 sha256、size、extension、mtime、relative_path。
4. 能做初步分类：xor/shift/strcmp/array_compare/des/rc4/base64/unknown 等。
5. 能输出 project_state/local_reverse_corpus_index.json。
6. 能输出 project_state/local_reverse_training_state.json。
7. 能为前 N 个简单样本生成 bounded triage report，但不提交 solve_reports 全量。
8. 有 pytest 覆盖新增扫描、分类、状态输出逻辑。
```

---

## 2. Current Evidence

当前主线切换为：

```text
reverse_solving
```

但本轮不是继续旧 `samplereverse` 深挖，而是启动：

```text
local_reverse_simple_training
```

当前旧状态背景：

```text
task_packet.sample=samplereverse
task_packet.task=Review bounded window discovery diagnostics
task_packet.execution_scope=decision_packet_controls_current_round
```

这些旧字段只是上一轮状态派生建议，不是本轮执行权威。

上一轮 Codex report 状态：

```text
status=PARTIAL
acceptance_recommendation=NEEDS_REVIEW
current blocker=window_lifecycle_no_window_created
```

上一轮测试结果显示：

```text
py_compile passed
focused pytest passed
project_state build passed
lint-report OK
lint-decision expected failed after rebuild because state digest changed
```

因此本轮应避免在旧 decision 上继续堆叠窗口诊断，直接新建本地训练集方向。

Artifact freshness 判断：

```text
1. samplereverse 相关 latest_artifacts_v2 只作为旧样本背景。
2. 不得把旧 samplereverse stale/missing artifact 当成本地 E:\reverse 训练集证据。
3. E:\reverse 是本轮新的本地事实来源，只允许记录 metadata / sha256 / bounded triage，不提交二进制样本。
4. 如果 E:\reverse 不存在或不可访问，必须输出 BLOCKED 状态和明确缺失原因。
```

当前 skill profiles：

```text
reverse-agent-iteration@v2
```

本轮不使用 `samplereverse-frontier@v2`，因为当前任务不是 `samplereverse` frontier 深挖，而是本地简单题训练集 bootstrap。

---

## 3. Do Not Do

严禁：

```text
1. 不继续 samplereverse 的窗口发现、compare handoff、Base64/RC4 breakpoint probe。
2. 不回旧 sample_solver 盲搜。
3. 不扩大 beam / topN / budget / timeout / frontier limit。
4. 不运行 Base64/RC4 breakpoint probe。
5. 不默认读取完整 solve_reports/。
6. 不读取完整 PROJECT_PROGRESS_LOG.txt。
7. 不提交 E:\reverse 下的二进制样本。
8. 不把本地样本复制进 Git 仓库。
9. 不把样本路径、candidate、runtime metric 写进 .codex-skills/。
10. 不修改 .codex-skills/ registry 或新增 skill。
11. 不建设重型多 agent 平台。
12. 不引入数据库、Redis、Celery、Kubernetes、Airflow、Temporal、LangGraph。
13. 不一次性尝试解完所有样本。
14. 不对未知样本执行不受控 runtime probe。
15. 不把 triage heuristic 的结果宣称为最终解。
16. 不提交完整 solve_reports/。
```

允许：

```text
1. 有界扫描 E:\reverse。
2. 读取文件 metadata 和 sha256。
3. 对小文件做 bounded strings 提取。
4. 对 PE 文件做轻量 header 检测。
5. 对 Python/C/文本脚本做轻量内容分类。
6. 为前 3~5 个明显简单样本生成 triage summary。
7. 新增 tests。
8. 新增 project_state 输出文件。
```

---

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

需要检查现有项目结构，优先找是否已有类似模块，避免重复实现：

```text
reverse_agent/
tests/
project_state/
README.txt
```

重点搜索关键词：

```text
sample_corpus
corpus
reverse sample
sample_solver
project_state build
artifact_index
```

不要默认读取：

```text
solve_reports/
PROJECT_PROGRESS_LOG.txt
```

除非 `project_state` 明确缺失关键上下文。

---

## 5. Required Audit

Codex 必须完成以下审计并写入 `project_state/codex_execution_report.md`：

```text
1. 确认本轮 decision_packet 是执行权威。
2. 确认 task_packet 中旧 samplereverse task 只是旧状态背景。
3. 确认本轮 mainline=reverse_solving，但具体方向为 local_reverse_simple_training。
4. 确认没有继续 samplereverse window/compare/Base64/RC4 probe。
5. 确认没有修改 .codex-skills/。
6. 确认没有提交 E:\reverse 样本二进制。
7. 确认没有提交完整 solve_reports/。
8. 确认新增文件是 additive，兼容旧 project_state。
9. 确认所有输出文件均可机器读取。
10. 确认测试真实运行，并同步写入 project_state/pytest_result.txt。
```

报告顶部必须包含：

```json codex_report_summary
{
  "schema_version": 1,
  "report_id": "report_20260603_simple_reverse_training_corpus_bootstrap",
  "round_id": "round_20260603_simple_reverse_training_corpus_bootstrap",
  "based_on_decision_id": "decision_20260603_simple_reverse_training_corpus_bootstrap",
  "status": "SUCCESS_OR_PARTIAL_OR_BLOCKED",
  "acceptance_recommendation": "ACCEPT_OR_NEEDS_REVIEW_OR_REWORK",
  "files_changed": [],
  "tests_ran": [],
  "generated_artifacts": []
}
```

---

## 6. Implementation Scope

### 6.1 新增本地样本扫描模块

优先新增轻量模块，例如：

```text
reverse_agent/local_reverse_corpus.py
```

职责：

```text
1. 接收 root path，默认不硬编码 E:\reverse。
2. 支持 CLI 参数传入 --root E:\reverse。
3. 递归扫描文件，但跳过明显无关或过大文件。
4. 输出 normalized metadata。
5. 不复制样本。
6. 不上传样本。
7. 不把绝对路径写入长期 skill。
```

建议数据结构：

```json
{
  "schema_version": 1,
  "generated_at": "ISO-8601",
  "root": "E:\\reverse",
  "root_exists": true,
  "sample_count": 0,
  "samples": [
    {
      "sample_id": "sha256_prefix_or_stable_id",
      "relative_path": "xxx.exe",
      "extension": ".exe",
      "size_bytes": 12345,
      "sha256": "...",
      "mtime": "...",
      "file_kind": "pe32|pe64|python|text|unknown",
      "triage_tags": ["xor", "array_compare"],
      "triage_confidence": "low|medium|high",
      "safe_to_run": false,
      "notes": []
    }
  ]
}
```

输出到：

```text
project_state/local_reverse_corpus_index.json
```

### 6.2 新增简单题 triage heuristic

允许做静态轻量识别，不做重型反编译。

建议识别规则：

```text
1. 文件扩展名：
   - .exe/.dll -> possible_pe
   - .py -> python_solver_or_script
   - .c/.cpp/.txt/.md -> source_or_notes
2. PE magic:
   - MZ header -> pe_candidate
3. strings 线索：
   - flag, input, password, wrong, correct, success
   - xor, rc4, des, base64
   - 明显十六进制数组
4. 字节模式：
   - 高频 XOR 常量
   - 小数组 compare
   - ASCII shift 线索
5. 文件名线索：
   - xor, shift, rc4, des, base64, crackme
```

输出 tag 只代表初判：

```text
xor
shift
array_compare
strcmp
serial_check
base64
rc4
des
aes
hash
packed_or_obfuscated
unknown
```

### 6.3 新增训练状态文件

新增：

```text
project_state/local_reverse_training_state.json
```

建议结构：

```json
{
  "schema_version": 1,
  "generated_at": "ISO-8601",
  "training_profile": "local_reverse_simple_training",
  "root": "E:\\reverse",
  "status": "READY|PARTIAL|BLOCKED",
  "sample_count": 0,
  "triage_summary": {
    "xor": 0,
    "shift": 0,
    "array_compare": 0,
    "strcmp": 0,
    "base64": 0,
    "rc4": 0,
    "des": 0,
    "unknown": 0
  },
  "recommended_next_samples": [
    {
      "sample_id": "...",
      "relative_path": "...",
      "reason": "small PE with strings and xor-like constants",
      "proposed_solver_family": "xor_array_solver"
    }
  ],
  "blocked_reason": ""
}
```

### 6.4 新增 CLI 入口

优先使用现有项目风格。如果已有 CLI，接入现有 CLI；否则新增最小命令：

```bash
python -m reverse_agent.local_reverse_corpus --root E:\reverse --out project_state/local_reverse_corpus_index.json --training-state project_state/local_reverse_training_state.json
```

CLI 要求：

```text
1. root 不存在时不要崩溃，要输出 BLOCKED 状态。
2. 默认 max file size 设置为保守值，例如 50MB。
3. 默认只对前若干 KB/MB 做 strings/heuristic，不全量加载大文件。
4. stdout 打印简短 summary。
5. 退出码：
   - 0: 成功或 PARTIAL
   - 2: root 不存在 / 无可读样本
```

### 6.5 不要直接求解全部样本

本轮只允许为推荐样本生成“下一步计划”，例如：

```text
sample_id=...
classification=xor/shift/array_compare
recommended_action=static_extract_constants_then_symbolic_or_bruteforce_small_domain
reason=...
```

不得把 heuristic 误报当作最终 flag。

---

## 7. Tests

必须新增或更新测试。

建议测试文件：

```text
tests/test_local_reverse_corpus.py
```

最低测试：

```text
1. root 不存在 -> 输出 BLOCKED training_state。
2. 空目录 -> sample_count=0，status=PARTIAL 或 BLOCKED，不能崩溃。
3. 临时目录含 .exe mock MZ 文件 -> file_kind=pe_candidate。
4. 临时目录含 xor/shift/base64 命名文件 -> triage_tags 正确包含对应 tag。
5. sha256、size、relative_path 稳定。
6. 大文件不会被完整读入进行 strings。
7. 输出 JSON schema 包含 schema_version/generated_at/sample_count/samples。
```

必须运行：

```bash
python -m py_compile reverse_agent\local_reverse_corpus.py
python -m pytest -q tests\test_local_reverse_corpus.py
python -m reverse_agent.local_reverse_corpus --root E:\reverse --out project_state\local_reverse_corpus_index.json --training-state project_state\local_reverse_training_state.json
python -m reverse_agent.project_state lint-decision --state-dir project_state
python -m reverse_agent.project_state lint-report --state-dir project_state
git diff --check
```

如果 `lint-decision` 因本轮重新写 state digest 失败，必须解释具体原因，不得报告 SUCCESS。

如果 `E:\reverse` 在 Codex 环境不可访问，必须：

```text
1. 不伪造扫描结果。
2. 让 CLI 对不存在 root 输出 BLOCKED。
3. 仍然用 pytest 临时目录验证扫描逻辑。
4. 在 codex_execution_report.md 中把 runtime corpus scan 标记为 BLOCKED_BY_LOCAL_PATH_UNAVAILABLE。
```

---

## 8. Stop Conditions

出现以下情况必须停止，不要继续扩展：

```text
1. E:\reverse 不存在或 Codex 无法访问。
2. 扫描发现样本数量巨大，超过默认限制。
3. 文件疑似恶意或 packed，需要动态执行才能判断。
4. 需要复制或提交二进制样本才能继续。
5. 需要运行未知 exe 才能分类。
6. 需要改 .codex-skills/。
7. 需要引入重型平台或数据库。
8. 测试无法稳定复现。
```

停止时输出：

```text
1. 已完成的扫描/测试。
2. BLOCKED 原因。
3. 下一轮最小可执行任务。
```

额外给 Codex 的一句话指令：

```text
本轮不要再碰 samplereverse 的窗口/compare/RC4/Base64 支线。先把 E:\reverse 作为本地简单题训练集建立索引、分类、推荐下一题，目标是让项目开始积累“简单逆向题可复现训练样本”的能力，而不是一次性解完所有题。
```
