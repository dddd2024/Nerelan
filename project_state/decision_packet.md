```json decision_meta
{
  "schema_version": 1,
  "decision_id": "decision_20260603_local_reverse_string_compare_solver_v1",
  "round_id": "round_20260603_local_reverse_string_compare_solver_v1",
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

本轮继续 `local_reverse_simple_training`，但从上一轮的 **bounded runtime solve benchmark** 推进到第一类 solver 能力建设：**bounded string-compare solver family v1**。

当前 Codex 实际执行权威是本文件 `project_state/decision_packet.md`。旧 `project_state/task_packet.json` 中的 `samplereverse` 字段仍只作为旧状态背景，不能覆盖本 decision。

本轮只处理上一轮 benchmark 推荐的 3 个 `ready_static_string_compare` challenge binary，不扩展到全量样本，不做无界 brute force。

---

## 1. Goal

本轮目标是实现第一个可复用的本地简单题 solver family：`string_compare_static_solver_v1`。

核心目标：

```text
1. 只针对上一轮 benchmark 推荐的 3 个 ready_static_string_compare challenge binary。
2. 对每个目标样本做 bounded static string/constant extraction。
3. 从静态字符串和 runtime prompt/failure 输出中生成有限候选输入。
4. 使用上一轮已有 runtime harness 验证候选。
5. 若验证成功，记录 solved=true、candidate、evidence。
6. 若验证失败，记录 bounded negative result 和下一步缺失证据。
7. 输出机器可读的 project_state/local_reverse_string_solver_result.json。
```

本轮目标不是通吃所有样本，不是构建通用反编译器，也不是做全量密码学 solver。它只建立第一版可审计、可复现、可验证的 string-compare solver family。

---

## 2. Current Evidence

上一轮 runtime benchmark 已完成：

```text
project_state/local_reverse_runtime_policy.json
project_state/local_reverse_solve_benchmark.json
```

上一轮 runtime summary：

```text
root=E:\reverse
status=READY
challenge_count=22
executed_count=22
skipped_count=0
timeout_count=3
solved_count=0
```

上一轮 solve readiness distribution：

```text
needs_disassembly=12
needs_gui_interaction=3
ready_crypto_known_family=4
ready_static_string_compare=3
```

本轮只处理 benchmark 推荐的 3 个目标：

```text
1. sample_id=4c69f173f2bd0211
   relative_path=逆向课程2022春02/CPP2.exe
   solve_readiness=ready_static_string_compare

2. sample_id=bcbd9979db015bfd
   relative_path=逆向课程2022春补考01/Cpp1.exe
   solve_readiness=ready_static_string_compare

3. sample_id=18019fca52b389fe
   relative_path=逆向课程2024春01/sha_256.exe
   solve_readiness=ready_static_string_compare
```

上一轮已知限制：

```text
1. network_allowed=false 只是 policy 声明，未做 OS 级网络隔离。
2. local_reverse_runtime.py 中 sample result 的 runtime_allowed 字段当前硬编码为 true。
```

本轮不要把上述两个限制扩大成框架改造，只允许做与 solver 验证直接相关的最小修正：让 runtime_allowed 字段真实反映 policy / sample runtime status，并在 report 中说明 network_allowed 仍是 local trusted sample policy，不是 OS sandbox。

Artifact freshness 判断：

```text
1. project_state/local_reverse_solve_benchmark.json 是本轮 string solver 的直接输入证据。
2. project_state/local_reverse_corpus_index.json 提供样本 sha256、relative_path、artifact_role 和 triage_tags。
3. samplereverse latest_artifacts_v2 只能作为旧背景，不得用于本轮 solver evidence。
4. 不得把 stale/missing samplereverse artifact 当成本轮证据。
```

---

## 3. Do Not Do

严禁：

```text
1. 不继续 samplereverse 的窗口发现、compare handoff、Base64/RC4 breakpoint probe。
2. 不回旧 sample_solver 盲搜。
3. 不对 22 个样本全量求解。
4. 不处理本 decision 指定 3 个样本之外的 challenge binary。
5. 不扩大到 DES/RC4/Base64/hash solver family。
6. 不做无界 brute force。
7. 不扩大 beam / topN / frontier search。
8. 不读取完整 solve_reports/。
9. 不读取完整 PROJECT_PROGRESS_LOG.txt。
10. 不提交 E:\reverse 下的二进制样本。
11. 不把 E:\reverse 样本复制进 Git 仓库。
12. 不把样本二进制转成 base64 或 hex 提交。
13. 不修改 .codex-skills/。
14. 不建设重型 agent 平台。
15. 不引入数据库、Redis、Celery、Kubernetes、Airflow、Temporal、LangGraph。
16. 不把 heuristic candidate 当成 solved。
17. 不伪造 runtime 验证结果。
18. 不提交完整 solve_reports/。
```

允许：

```text
1. 读取 project_state/local_reverse_corpus_index.json。
2. 读取 project_state/local_reverse_solve_benchmark.json。
3. 有界读取 3 个目标 exe 的 bytes 用于 strings/constant extraction。
4. 使用 existing static_feature_extractor 提取 ASCII / UTF-16LE 字符串。
5. 生成有限候选输入，默认每个样本最多 50 个。
6. 使用 local_reverse_runtime.run_probe 对候选做 bounded runtime validation。
7. 新增 reverse_agent/local_reverse_string_solver.py。
8. 新增 tests/test_local_reverse_string_solver.py。
9. 输出 project_state/local_reverse_string_solver_result.json。
10. 对 runtime_allowed 字段硬编码问题做最小修复并测试。
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
project_state/local_reverse_corpus_index.json
project_state/local_reverse_training_state.json
project_state/local_reverse_runtime_policy.json
project_state/local_reverse_solve_benchmark.json
```

必须检查：

```text
reverse_agent/local_reverse_corpus.py
reverse_agent/local_reverse_runtime.py
reverse_agent/static_feature_extractor.py
tests/test_local_reverse_corpus.py
tests/test_local_reverse_runtime.py
```

允许新增：

```text
reverse_agent/local_reverse_string_solver.py
tests/test_local_reverse_string_solver.py
project_state/local_reverse_string_solver_result.json
```

不要默认读取：

```text
solve_reports/
PROJECT_PROGRESS_LOG.txt
```

---

## 5. Required Audit

Codex 必须审计并写入 `project_state/codex_execution_report.md`：

```text
1. 当前 decision_packet 是执行权威。
2. 旧 samplereverse task 只是背景。
3. 本轮 mainline=reverse_solving，具体方向=local_reverse_string_compare_solver_v1。
4. 只处理 3 个指定 ready_static_string_compare 样本。
5. 未处理 3 个指定样本之外的 challenge binary。
6. 未运行 E:\reverse 之外的 exe。
7. 未复制、提交、上传或编码任何样本二进制。
8. 未修改 .codex-skills/。
9. 未读取完整 solve_reports/ 或 PROJECT_PROGRESS_LOG.txt。
10. 每个候选验证都有 timeout。
11. 每个 solved=true 都必须有 runtime success evidence。
12. 未 solved 的样本必须有 negative_result / missing_evidence 说明。
13. 测试真实运行并写入 project_state/pytest_result.txt。
```

报告顶部必须包含：

```json codex_report_summary
{
  "schema_version": 1,
  "report_id": "report_20260603_local_reverse_string_compare_solver_v1",
  "round_id": "round_20260603_local_reverse_string_compare_solver_v1",
  "based_on_decision_id": "decision_20260603_local_reverse_string_compare_solver_v1",
  "status": "SUCCESS_OR_PARTIAL_OR_BLOCKED",
  "acceptance_recommendation": "ACCEPT_OR_NEEDS_REVIEW_OR_REWORK",
  "files_changed": [],
  "tests_ran": [],
  "generated_artifacts": []
}
```

---

## 6. Implementation Scope

### 6.1 新增 string solver 模块

新增：

```text
reverse_agent/local_reverse_string_solver.py
```

建议 CLI：

```bash
python -m reverse_agent.local_reverse_string_solver ^
  --corpus-index project_state\local_reverse_corpus_index.json ^
  --benchmark project_state\local_reverse_solve_benchmark.json ^
  --policy project_state\local_reverse_runtime_policy.json ^
  --out project_state\local_reverse_string_solver_result.json
```

默认只处理 benchmark 中 `recommended_next_challenges` 的 3 个样本，并且必须校验它们的 `solve_readiness == ready_static_string_compare`。

### 6.2 静态候选提取

对每个目标样本：

```text
1. 通过 corpus_index 找到 relative_path、sha256。
2. 验证实际文件仍在 root 下。
3. 验证 sha256 匹配。
4. 有界读取 bytes。
5. 提取 ASCII / UTF-16LE strings。
6. 过滤 prompt/failure/noise 字符串。
7. 生成候选输入集合。
```

候选来源允许：

```text
1. 可见 flag-like 字符串：flag{...}、ctf{...} 等。
2. 长度 4~64 的 printable token。
3. runtime 输出附近疑似 success/secret/check 字符串。
4. 路径/文件名提示派生的极小候选，例如 CPP2、sha_256，但不得爆破。
5. UTF-16LE 字符串。
```

必须过滤：

```text
wrong
sorry
try again
please input
input your flag
press any key
success/failure prompt itself
通用库名、路径、PE 节名、编译器残留
```

默认每个样本最多验证：

```text
max_candidates_per_sample=50
```

### 6.3 runtime 验证规则

使用 `reverse_agent.local_reverse_runtime.run_probe` 或等价有界函数验证：

```text
stdin = candidate + "\n"
timeout <= policy.max_timeout_seconds
preview_limit <= 4096
```

成功判定必须保守：

```text
1. stdout/stderr 出现 success/correct/right/congratulations/you win 等成功语义；
2. 且没有 wrong/sorry/fail/invalid/try again 等失败语义；
3. 或样本输出明确包含 flag/candidate accepted 语义；
4. 否则不得标记 solved=true。
```

如果所有候选都失败：

```text
solved=false
status=NO_CANDIDATE_VALIDATED
missing_evidence=needs_compare_constant_or_disassembly
```

### 6.4 输出 result artifact

新增：

```text
project_state/local_reverse_string_solver_result.json
```

建议结构：

```json
{
  "schema_version": 1,
  "generated_at": "ISO-8601",
  "solver_family": "string_compare_static_solver_v1",
  "status": "SUCCESS|PARTIAL|BLOCKED",
  "target_count": 3,
  "solved_count": 0,
  "targets": [
    {
      "sample_id": "...",
      "relative_path": "...",
      "sha256": "...",
      "solve_readiness": "ready_static_string_compare",
      "candidate_count": 0,
      "validated_candidate_count": 0,
      "solved": false,
      "solution": null,
      "candidate_sources": [],
      "validation_results_preview": [],
      "negative_result": "NO_CANDIDATE_VALIDATED",
      "missing_evidence": "needs_compare_constant_or_disassembly",
      "next_action": "bounded compare-site static extraction"
    }
  ]
}
```

如果有 solved=true，必须记录：

```text
solution
probe_name
stdout_success_preview
validation_duration_ms
```

但不得记录大体积 runtime output。

### 6.5 最小修复 runtime_allowed 字段

允许修复 `local_reverse_runtime.py` 的 `_sample_result()`：

```text
1. 不再硬编码 runtime_allowed=true。
2. runtime_allowed 应反映 policy runtime_allowed 且 runtime_status 是否可执行。
3. 加测试覆盖 runtime_allowed=false 时 JSON 不显示 true。
```

不要在本轮实现 OS 级网络隔离；只在 report 中明确 `network_allowed=false` 是 trusted local policy 声明，不是 sandbox enforcement。

---

## 7. Tests

必须新增或更新：

```text
tests/test_local_reverse_string_solver.py
tests/test_local_reverse_runtime.py
```

最低测试：

```text
1. 只选择 benchmark recommended_next_challenges 中的 ready_static_string_compare 样本。
2. 非目标样本不进入 solver。
3. sha256 mismatch 不验证候选。
4. path escape 不验证候选。
5. prompt/failure/noise 字符串不会成为优先候选。
6. 每个样本候选数受 max_candidates_per_sample 限制。
7. success marker 且无 failure marker 才能 solved=true。
8. wrong/sorry/fail/try again 输出不能 solved=true。
9. 无候选验证成功时输出 negative_result。
10. runtime_allowed=false 时 result 不应显示 runtime_allowed=true。
11. result JSON schema 正确。
```

必须运行：

```bash
python -m py_compile reverse_agent\local_reverse_runtime.py reverse_agent\local_reverse_string_solver.py
python -m pytest -q tests\test_local_reverse_runtime.py tests\test_local_reverse_string_solver.py
python -m reverse_agent.local_reverse_string_solver --corpus-index project_state\local_reverse_corpus_index.json --benchmark project_state\local_reverse_solve_benchmark.json --policy project_state\local_reverse_runtime_policy.json --out project_state\local_reverse_string_solver_result.json
python -m reverse_agent.project_state lint-decision --state-dir project_state
python -m reverse_agent.project_state lint-report --state-dir project_state
git diff --check
```

如果本轮没有任何样本 solved，只要输出了完整 negative evidence 和下一步 compare-site 缺失证据，也可以是 `PARTIAL / NEEDS_REVIEW`，不得伪报 SUCCESS solved。

---

## 8. Stop Conditions

出现以下情况必须停止：

```text
1. 三个指定样本任一文件缺失或 sha256 mismatch。
2. 样本路径逃逸出 E:\reverse。
3. runtime policy 不允许执行。
4. 候选验证超过 per-sample 上限。
5. 运行超过 timeout。
6. 需要无界 brute force 才能继续。
7. 需要复杂反编译器或 GUI 自动化。
8. 需要复制样本二进制进仓库。
9. 需要读取完整 solve_reports/ 或 PROJECT_PROGRESS_LOG.txt。
10. 测试失败。
```

停止时输出：

```text
1. 每个目标样本候选数量。
2. 每个目标样本是否 solved。
3. 未 solved 的 negative_result。
4. 下一轮是否需要 compare-site static extraction、IDA script、或更小范围 disassembly helper。
```
