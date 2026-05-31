```json decision_meta
{
  "schema_version": 1,
  "decision_id": "decision_20260531_corpus_static_audit_route2",
  "round_id": "round_20260531_corpus_static_audit_route2",
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

本轮属于 **engineering_branch**，但目标服务于后续逆向解题能力提升。任务不是继续修 report schema，也不是推进 `samplereverse` 当前 runtime 主线，而是基于已经整理好的 `sample_corpus/reverse/` 建立一套 **静态优先的 corpus 画像、题型分类和能力缺口审计流程**。

本轮核心原则：**不执行任何 `sample.exe`，不运行 IDA / OllyDbg / Frida，不运行 runtime probe，不运行 Base64/RC4 breakpoint probe。**

当前 Codex 实际执行权威是本文件 `project_state/decision_packet.md`。`project_state/task_packet.json` 中的 `task` / `derived_task` 仍是旧 `samplereverse` 状态派生建议，不自动覆盖本 decision。

## 1. Goal

建立 `sample_corpus/reverse/` 的静态画像与分类 audit 基础设施，使 reverse-agent 后续可以系统性利用真实逆向样本提升解题能力。

本轮目标不是“自动解出所有题”，而是建立可复现的静态评测闭环：

```text
sample_corpus/reverse/
  -> corpus loader
  -> static feature extractor
  -> rule-based corpus classifier
  -> corpus_static_audit.json
  -> corpus_solver_gap_report.md
```

完成后，项目应能回答：

```text
1. corpus 中有哪些样本。
2. 每个样本的 metadata/case/notes/codex_task 是否可加载。
3. 每个 sample.exe 的 sha256/size 是否与 metadata 一致。
4. 每个样本有哪些静态字符串、关键词、加密/编码提示和比较提示。
5. 每个样本初步像哪类逆向题：affine/string_compare/hash/rc4/des/seh/unknown 等。
6. 当前项目已有能力覆盖哪些题型，哪些题型仍是能力缺口。
```

本轮必须新增一个可运行的静态 audit CLI：

```text
python -m reverse_agent.corpus_static_audit --corpus-dir sample_corpus/reverse --out project_state/corpus_static_audit.json --gap-report project_state/corpus_solver_gap_report.md
```

## 2. Current Evidence

当前事实来源：

```text
project_state/task_packet.json
project_state/current_state.json
project_state/artifact_index.json
project_state/negative_results.json
project_state/codex_execution_report.md
project_state/decision_packet.md
project_state/pytest_result.txt
sample_corpus/reverse/manifest.json
sample_corpus/reverse/*/metadata.json
sample_corpus/reverse/*/case.json
sample_corpus/reverse/*/notes.md
sample_corpus/reverse/*/codex_task.md
```

当前状态：

```text
1. sample_corpus/reverse/ 已经建立并通过上一轮审计。
2. case.json input_value 已经指向 sample_corpus/reverse/<case_id>/sample.exe。
3. tests/test_sample_corpus.py 已经能真实校验 sample.exe sha256 / size_bytes。
4. sample_corpus/reverse/README.md 已说明 safe_to_run=false 和 upload_allowed=true。
5. 根 README.txt 已说明 local_reverse_samples/ 与 sample_corpus/reverse/ 的区别。
6. 上一轮 solver.py 已删除或不再作为默认提交 artifact。
```

当前主线解释：

```text
mainline = engineering_branch
```

原因：本轮实现的是 corpus 静态画像和评测基础设施，不是求解某个具体样本，也不推进 `samplereverse` runtime candidate/frontier。

当前 skill profiles：

```text
reverse-agent-iteration@v2
```

不使用：

```text
samplereverse-frontier@v2
```

原因：本轮不读取或推进 `samplereverse` candidate、frontier、runtime metric、compare hook、artifact freshness 或 negative runtime evidence。

artifact freshness 约束：

```text
1. 本轮不依赖 solve_reports/ 中的 samplereverse runtime artifact。
2. artifact_index.latest_artifacts_v2 中的 stale/missing runtime artifact 不作为本轮证据。
3. 本轮输出的 project_state/corpus_static_audit.json 和 project_state/corpus_solver_gap_report.md 属于新的 corpus 静态 audit 产物。
```

## 3. Do Not Do

严禁：

```text
1. 不执行任何 sample.exe。
2. 不运行 IDA。
3. 不运行 OllyDbg。
4. 不运行 Frida。
5. 不运行 pywinauto / GUI runtime validation。
6. 不运行 Base64/RC4 breakpoint probe。
7. 不运行 samplereverse harness。
8. 不读取完整 solve_reports/。
9. 不读取完整 PROJECT_PROGRESS_LOG.txt。
10. 不修改 .codex-skills/。
11. 不修改 reverse_agent/strategies/compare_aware_search.py。
12. 不修改 reverse_agent/profiles/samplereverse.py。
13. 不修改 reverse_agent/sample_solver.py。
14. 不修改 sample_corpus/reverse/*/sample.exe。
15. 不重新提交 solver.py 到 sample_corpus/reverse/*/。
16. 不把 sample_corpus/reverse/ 当作动态运行产物目录。
17. 不把静态分类结果写成确定解题结论。
18. 不把 rc4/des/seh 分类结果当作已解出 flag。
```

特别限制：

```text
1. 所有样本 safe_to_run 必须保持 false。
2. 所有样本 upload_allowed 必须保持 true。
3. 只允许读取 sample.exe 字节用于 hash、字符串和静态特征抽取；不得执行。
4. 如果实现需要执行二进制样本，立即停止并报告 BLOCKED。
5. 如果实现需要引入重型逆向框架或动态调试器，立即停止并报告 BLOCKED。
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

必须检查：

```text
sample_corpus/reverse/manifest.json
sample_corpus/reverse/README.md
sample_corpus/reverse/*/metadata.json
sample_corpus/reverse/*/case.json
sample_corpus/reverse/*/notes.md
sample_corpus/reverse/*/codex_task.md
tests/test_sample_corpus.py
reverse_agent/simple_static_patterns.py
README.txt
.gitignore
```

允许新增：

```text
reverse_agent/corpus_loader.py
reverse_agent/static_feature_extractor.py
reverse_agent/corpus_classifier.py
reverse_agent/corpus_static_audit.py
tests/test_corpus_loader.py
tests/test_static_feature_extractor.py
tests/test_corpus_classifier.py
tests/test_corpus_static_audit.py
project_state/corpus_static_audit.json
project_state/corpus_solver_gap_report.md
```

允许修改：

```text
README.txt                         # 仅在需要补充 corpus static audit 使用说明时
project_state/codex_execution_report.md
project_state/pytest_result.txt
```

原则上不修改：

```text
sample_corpus/reverse/*/metadata.json
sample_corpus/reverse/*/case.json
sample_corpus/reverse/*/codex_task.md
sample_corpus/reverse/manifest.json
sample_corpus/reverse/README.md
```

如果发现 corpus 文件本身不一致，应优先报告 `BLOCKED` 或最小修复并在 report 中明确说明；不要顺手扩大整理范围。

不得修改：

```text
.codex-skills/
reverse_agent/strategies/compare_aware_search.py
reverse_agent/profiles/samplereverse.py
reverse_agent/sample_solver.py
sample_corpus/reverse/*/sample.exe
solve_reports/
```

## 5. Required Audit

Codex 执行报告必须逐项回答：

```text
1. 是否新增 reverse_agent/corpus_loader.py。
2. corpus_loader 是否能读取 manifest.json 并加载所有 case。
3. corpus_loader 是否真实校验 sample.exe sha256 / size_bytes。
4. corpus_loader 是否强制 safe_to_run=false / upload_allowed=true。
5. 是否新增 reverse_agent/static_feature_extractor.py。
6. static_feature_extractor 是否只做静态字节读取，不执行样本。
7. static_feature_extractor 是否能提取 ASCII 字符串。
8. static_feature_extractor 是否能提取 UTF-16LE 字符串。
9. static_feature_extractor 是否能识别 PE/MZ 基础格式。
10. static_feature_extractor 是否能提取 crypto/encoding/compare 关键词提示。
11. 是否新增 reverse_agent/corpus_classifier.py。
12. corpus_classifier 是否输出 predicted_category / confidence / evidence。
13. 分类是否是 rule-based static hint，而非确定解题结论。
14. 是否新增 reverse_agent/corpus_static_audit.py CLI。
15. CLI 是否能生成 project_state/corpus_static_audit.json。
16. CLI 是否能生成 project_state/corpus_solver_gap_report.md。
17. 生成的 project_state/corpus_static_audit.json 是否不包含大块二进制 dump 或完整字符串 dump。
18. 生成的 project_state/corpus_solver_gap_report.md 是否说明当前能力覆盖和缺口。
19. 是否没有执行任何 sample.exe。
20. 是否没有运行 IDA / OllyDbg / Frida / runtime probe。
21. 是否没有修改 .codex-skills/。
22. 是否没有修改 samplereverse 主线。
23. 是否没有读取完整 solve_reports/。
24. 是否没有读取完整 PROJECT_PROGRESS_LOG.txt。
```

## 6. Implementation Scope

### 6.1 新增 corpus loader

新增：

```text
reverse_agent/corpus_loader.py
```

建议实现：

```text
1. CorpusCase dataclass。
2. load_manifest(corpus_dir)。
3. load_corpus_cases(corpus_dir)。
4. verify_case_files(case)。
5. compute_sha256(path)。
6. validate_corpus(corpus_dir)。
```

建议 `CorpusCase` 字段：

```text
case_id: str
sample_path: Path
sha256: str
size_bytes: int
category: str
tags: list[str]
safe_to_run: bool
upload_allowed: bool
metadata_path: Path
case_json_path: Path
notes_path: Path
codex_task_path: Path
notes: str
```

要求：

```text
1. 只读取文件，不执行 sample.exe。
2. sample_path 必须在 corpus_dir 下。
3. sample_path 不允许绝对外部路径。
4. sha256 必须与真实文件一致。
5. size_bytes 必须与真实文件一致。
6. safe_to_run 必须是 false。
7. upload_allowed 必须是 true。
```

### 6.2 新增静态特征抽取器

新增：

```text
reverse_agent/static_feature_extractor.py
```

第一版只做轻量、无外部动态工具的静态提取：

```text
1. 检测 MZ / PE header。
2. 提取 ASCII 字符串。
3. 提取 UTF-16LE 字符串。
4. 提取常见输入/成功/失败关键词。
5. 提取 crypto/encoding 关键词：md5, sha, sha1, sha256, rc4, des, aes, base64。
6. 提取 compare 关键词：strcmp, strncmp, memcmp, compare, input, password, key, flag。
7. 提取 hex-like 常量。
8. 提取 base64-like 字符串候选。
9. 输出摘要时限制字符串数量和长度，避免 project_state 膨胀。
```

建议输出结构：

```json
{
  "format": "pe|mz|unknown",
  "file_size": 0,
  "ascii_strings_sample": [],
  "utf16_strings_sample": [],
  "keyword_hits": [],
  "crypto_hints": [],
  "compare_hints": [],
  "interesting_constants": [],
  "entropy_hint": "low|medium|high|unknown"
}
```

注意：

```text
1. 不输出完整字符串列表。
2. 不输出大块二进制内容。
3. 不做反汇编。
4. 不调用 IDA/angr/pefile，除非项目已有依赖且实现极小；第一版优先纯 Python。
```

### 6.3 新增 corpus classifier

新增：

```text
reverse_agent/corpus_classifier.py
```

第一版分类为 rule-based static hint：

```text
affine_lowercase
caesar_or_shift
xor_or_bytewise
hash_check
rc4_like
des_like
aes_like
base64_or_encoding
seh_or_exception
string_compare
unknown
```

输出必须包含：

```text
predicted_category
confidence
evidence
recommended_next_step
```

分类约束：

```text
1. 证据必须来自 static_feature_extractor 输出或 notes/codex_task 中的可提交文本。
2. 不得因为文件名叫 rc4enc/desenc 就直接给 high confidence；文件名只能作为 weak evidence。
3. 如果只来自文件名或 notes，confidence 最高 medium。
4. 如果来自二进制字符串/常量等静态特征，可提升 confidence。
5. 对 rc4/des/seh 输出必须是 “like / hint”，不能写成已解出。
```

### 6.4 新增 corpus static audit CLI

新增：

```text
reverse_agent/corpus_static_audit.py
```

支持命令：

```text
python -m reverse_agent.corpus_static_audit --corpus-dir sample_corpus/reverse --out project_state/corpus_static_audit.json --gap-report project_state/corpus_solver_gap_report.md
```

CLI 行为：

```text
1. 加载 corpus。
2. 对每个 case 运行静态特征抽取。
3. 对每个 case 运行题型分类。
4. 生成 project_state/corpus_static_audit.json。
5. 生成 project_state/corpus_solver_gap_report.md。
6. 不执行 sample.exe。
7. 不调用 runtime probe。
```

`project_state/corpus_static_audit.json` 建议结构：

```json
{
  "schema_version": 1,
  "generated_at": "...",
  "corpus_dir": "sample_corpus/reverse",
  "execution_policy": {
    "executed_samples": false,
    "runtime_probe_used": false,
    "static_only": true
  },
  "cases": [
    {
      "case_id": "cpp_6af7c7f1",
      "sha256": "...",
      "size_bytes": 0,
      "static_features": {},
      "classification": {},
      "status": "static_profiled"
    }
  ],
  "summary": {
    "total_cases": 0,
    "classified_cases": 0,
    "unknown_cases": 0,
    "category_counts": {}
  }
}
```

`project_state/corpus_solver_gap_report.md` 必须说明：

```text
1. corpus 总样本数。
2. 每个样本的 predicted_category / confidence / evidence 摘要。
3. 当前已有能力覆盖哪些题型，例如 simple_static_patterns.py 覆盖 affine/caesar/xor/hash digest helper。
4. 当前缺口：DES 静态 key/ciphertext 识别、RC4 KSA/PRGA 静态识别、SEH 静态控制流提示等。
5. 下一轮建议按一个题型一个小步推进，不要一次性写 DES/RC4/SEH solver。
```

### 6.5 测试

新增测试：

```text
tests/test_corpus_loader.py
tests/test_static_feature_extractor.py
tests/test_corpus_classifier.py
tests/test_corpus_static_audit.py
```

测试要求：

```text
1. corpus_loader 能加载 sample_corpus/reverse/ 的所有 case。
2. corpus_loader 能校验 sha256/size_bytes。
3. corpus_loader 会拒绝 safe_to_run=true 的 metadata fixture。
4. static_feature_extractor 对小型 synthetic bytes 能提取 ASCII/UTF-16LE 字符串。
5. static_feature_extractor 能识别 MZ header。
6. static_feature_extractor 能识别 crypto/compare 关键词。
7. corpus_classifier 对 synthetic features 能输出 rc4_like/des_like/hash_check/string_compare/unknown。
8. corpus_static_audit CLI 能在临时 corpus fixture 上生成 json 和 md。
9. 所有测试不得执行真实 sample.exe。
```

### 6.6 报告更新

更新：

```text
project_state/codex_execution_report.md
project_state/pytest_result.txt
```

`codex_execution_report.md` 顶部必须包含 fenced JSON block：

```json
{
  "schema_version": 1,
  "report_id": "report_20260531_corpus_static_audit_route2",
  "round_id": "round_20260531_corpus_static_audit_route2",
  "based_on_decision_id": "decision_20260531_corpus_static_audit_route2",
  "status": "SUCCESS",
  "acceptance_recommendation": "ACCEPTED",
  "files_changed": [],
  "tests_ran": [],
  "generated_artifacts": []
}
```

要求：

```text
1. files_changed 必须完整列出新增/修改/删除文件。
2. generated_artifacts 必须包含 project_state/corpus_static_audit.json 和 project_state/corpus_solver_gap_report.md。
3. tests_ran 必须包含本轮真实运行命令。
4. 报告正文必须回答 Required Audit 全部问题。
```

`pytest_result.txt` 必须与本轮 decision/report/round 对齐。

## 7. Tests

必须运行：

```text
python -m pytest -q tests/test_sample_corpus.py
python -m pytest -q tests/test_corpus_loader.py
python -m pytest -q tests/test_static_feature_extractor.py
python -m pytest -q tests/test_corpus_classifier.py
python -m pytest -q tests/test_corpus_static_audit.py
python -m reverse_agent.corpus_static_audit --corpus-dir sample_corpus/reverse --out project_state/corpus_static_audit.json --gap-report project_state/corpus_solver_gap_report.md
python -m reverse_agent.project_state lint-decision --state-dir project_state
python -m reverse_agent.project_state lint-report --state-dir project_state
git diff --check
```

建议补充运行：

```text
python -m py_compile reverse_agent/corpus_loader.py reverse_agent/static_feature_extractor.py reverse_agent/corpus_classifier.py reverse_agent/corpus_static_audit.py
```

不得运行：

```text
python -m pytest -q                 # 不要求全量，除非 Codex 自愿且耗时可控
任何 sample.exe
IDA / OllyDbg / Frida / pywinauto
samplereverse harness
Base64/RC4 breakpoint probe
```

## 8. Stop Conditions

立即停止并报告 `BLOCKED`：

```text
1. sample_corpus/reverse/manifest.json 缺失。
2. 任一样本 sample.exe 缺失。
3. 任一样本 sha256 与 metadata 不一致。
4. 任一样本 size_bytes 与 metadata 不一致。
5. 任一样本 metadata.safe_to_run 不是 false。
6. 任一样本 metadata.upload_allowed 不是 true。
7. 必须执行 sample.exe 才能完成。
8. 必须运行 IDA / OllyDbg / Frida / runtime probe 才能完成。
9. 必须读取完整 solve_reports/ 才能完成。
10. 必须修改 .codex-skills/ 才能完成。
11. 必须修改 samplereverse 主线才能完成。
12. 生成的 corpus_static_audit.json 过大或包含完整二进制/完整字符串 dump。
13. 新增测试无法通过。
14. lint-decision 或 lint-report 无法通过。
```

完成条件：

```text
1. 新增 corpus_loader。
2. 新增 static_feature_extractor。
3. 新增 corpus_classifier。
4. 新增 corpus_static_audit CLI。
5. 新增对应 pytest。
6. 生成 project_state/corpus_static_audit.json。
7. 生成 project_state/corpus_solver_gap_report.md。
8. corpus_static_audit.json 明确 static_only=true / executed_samples=false / runtime_probe_used=false。
9. solver_gap_report.md 给出每个样本的分类、证据和能力缺口。
10. 未执行任何 sample.exe。
11. 未运行 runtime probe。
12. 未修改 .codex-skills/。
13. 未修改 samplereverse 主线。
14. 所有规定测试通过并记录在 pytest_result.txt。
15. codex_execution_report.md 与本 decision_id / round_id 对齐。
```
