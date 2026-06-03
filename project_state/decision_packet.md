```json decision_meta
{
  "schema_version": 1,
  "decision_id": "decision_20260603_local_reverse_runtime_solve_benchmark",
  "round_id": "round_20260603_local_reverse_runtime_solve_benchmark",
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

本轮继续 `local_reverse_simple_training`，但从上一轮的 **static-only corpus bootstrap** 推进到 **bounded runtime solve benchmark**。

用户已经明确确认：

```text
E:\reverse 内的 .exe 样本都已经手动试过，可以直接运行，不认为有病毒。
```

因此本轮允许对 `E:\reverse` 内已索引的 `.exe` 样本进行**有界运行**，但仍然必须保留工程安全边界：不复制二进制、不上传样本、不无界执行、不联网、不做全盘扫描、不改 `.codex-skills/`。

当前 Codex 实际执行权威是本文件 `project_state/decision_packet.md`。旧 `task_packet.json` 中的 `samplereverse` 字段仍只作为旧状态背景，不能覆盖本 decision。

---

## 1. Goal

本轮目标是让项目开始真正基于 `E:\reverse` 的全部题目提升解题能力。

具体目标：

```text
1. 在上一轮 corpus index 基础上，区分“题目样本”和“已有 solver/笔记/辅助脚本”。
2. 对所有题目 .exe 建立 bounded runtime baseline。
3. 捕获每个 .exe 的运行行为：exit_code、stdout、stderr、timeout、是否等待输入、是否 GUI、是否崩溃。
4. 结合静态 triage + runtime baseline，生成每个题目的 solve readiness。
5. 按题型输出可执行的下一步 solver plan，而不是只做泛泛分类。
6. 为简单题优先建立通用 solver family：strcmp、xor/array、shift、DES、RC4、Base64/hash。
7. 输出机器可读的 benchmark 状态，供下一轮选择具体题目或批量改进 solver。
```

本轮不是要求一次性解完全部 flag；本轮要求建立**可复现的全样本解题能力基线**，并把每道题归入可训练队列。

---

## 2. Current Evidence

上一轮已经生成：

```text
project_state/local_reverse_corpus_index.json
project_state/local_reverse_training_state.json
```

当前训练状态：

```text
root=E:\reverse
status=READY
sample_count=28
recommended_next_samples=5
```

上一轮 triage summary：

```text
xor=3
shift=3
strcmp=7
base64=1
rc4=2
des=6
hash=1
packed_or_obfuscated=22
unknown=1
```

上一轮限制：

```text
1. 只做 static-only。
2. 所有 sample safe_to_run=false。
3. recommended_next_samples 中混入了 solver 脚本，不够适合作为下一题目标。
```

本轮新增事实：

```text
用户确认 E:\reverse 内 .exe 已手动运行过，可以作为本地训练样本直接运行。
```

该事实只能写入 `project_state/` 动态状态，不得写入 `.codex-skills/`。

---

## 3. Do Not Do

严禁：

```text
1. 不继续 samplereverse 的窗口发现、compare handoff、Base64/RC4 breakpoint probe。
2. 不回旧 sample_solver 盲搜。
3. 不扩大 beam / topN / frontier search。
4. 不读取完整 solve_reports/。
5. 不读取完整 PROJECT_PROGRESS_LOG.txt。
6. 不提交 E:\reverse 下的二进制样本。
7. 不把 E:\reverse 样本复制进 Git 仓库。
8. 不把样本二进制转成 base64 或 hex 提交。
9. 不修改 .codex-skills/。
10. 不建设重型 agent 平台。
11. 不引入数据库、Redis、Celery、Kubernetes、Airflow、Temporal、LangGraph。
12. 不一次性做无限制 brute force。
13. 不对 E:\reverse 之外的 exe 执行 runtime。
14. 不伪造运行结果。
15. 不把 heuristic triage 当成最终 flag。
16. 不提交完整 solve_reports/。
```

允许：

```text
1. 对 E:\reverse 内已索引 .exe 做 bounded runtime。
2. 每个 exe 设置 timeout。
3. 捕获 stdout/stderr/exit_code。
4. 对等待输入的 console 程序喂入少量固定 probe input。
5. 对 GUI 程序只记录 GUI classification，不做复杂自动化。
6. 根据用户确认，把 E:\reverse 内 exe 标记为 user_runtime_allowed。
7. 新增 local reverse runtime benchmark 模块。
8. 新增 project_state/local_reverse_runtime_policy.json。
9. 新增 project_state/local_reverse_solve_benchmark.json。
10. 新增 tests。
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
```

必须检查：

```text
reverse_agent/local_reverse_corpus.py
tests/test_local_reverse_corpus.py
```

允许新增：

```text
reverse_agent/local_reverse_runtime.py
tests/test_local_reverse_runtime.py
project_state/local_reverse_runtime_policy.json
project_state/local_reverse_solve_benchmark.json
```

不要默认读取：

```text
solve_reports/
PROJECT_PROGRESS_LOG.txt
```

---

## 5. Required Audit

Codex 必须审计：

```text
1. 当前 decision_packet 是执行权威。
2. 旧 samplereverse task 只是背景。
3. 本轮 mainline=reverse_solving，具体方向=local_reverse_runtime_solve_benchmark。
4. 用户确认 E:\reverse exe 可以运行，但该事实只写入 project_state，不写入 skill。
5. 没有运行 E:\reverse 之外的 exe。
6. 没有复制或提交样本二进制。
7. 没有改 .codex-skills/。
8. 没有提交完整 solve_reports/。
9. 所有 runtime 都有 timeout。
10. 所有 runtime 结果都来自真实执行或明确标记为 skipped/blocked。
11. 测试真实运行并写入 project_state/pytest_result.txt。
```

报告顶部必须包含：

```json codex_report_summary
{
  "schema_version": 1,
  "report_id": "report_20260603_local_reverse_runtime_solve_benchmark",
  "round_id": "round_20260603_local_reverse_runtime_solve_benchmark",
  "based_on_decision_id": "decision_20260603_local_reverse_runtime_solve_benchmark",
  "status": "SUCCESS_OR_PARTIAL_OR_BLOCKED",
  "acceptance_recommendation": "ACCEPT_OR_NEEDS_REVIEW_OR_REWORK",
  "files_changed": [],
  "tests_ran": [],
  "generated_artifacts": []
}
```

---

## 6. Implementation Scope

### 6.1 修正样本角色分类

在 `local_reverse_corpus.py` 或新增模块中增加：

```text
artifact_role
```

建议取值：

```text
challenge_binary
solver_script
notes_or_source
support_file
unknown
```

规则：

```text
1. .exe/.dll 默认 challenge_binary。
2. 文件名包含 solver、interactive_solver、decrypt、encrypt、script 等，优先 solver_script。
3. .py 如果是已有解题脚本，不应进入 recommended_next_samples 的优先队列。
4. .txt/.md/.c/.cpp 可标为 notes_or_source 或 source_challenge。
```

修正 `recommended_next_samples`：

```text
1. 优先推荐 challenge_binary。
2. 其次推荐 source_challenge。
3. 不优先推荐 solver_script。
4. 每个推荐项给出 reason、triage_tags、runtime_allowed、next_action。
```

---

### 6.2 新增 runtime policy

新增：

```text
project_state/local_reverse_runtime_policy.json
```

建议结构：

```json
{
  "schema_version": 1,
  "generated_at": "ISO-8601",
  "root": "E:\\reverse",
  "runtime_allowed": true,
  "allowance_source": "user_asserted_pretested_no_virus",
  "allowed_extensions": [".exe"],
  "path_scope": "indexed_files_under_root_only",
  "network_allowed": false,
  "copy_binary_into_repo": false,
  "default_timeout_seconds": 5,
  "max_timeout_seconds": 15,
  "stdin_probe_limit": 8
}
```

---

### 6.3 新增 bounded runtime benchmark

新增模块：

```text
reverse_agent/local_reverse_runtime.py
```

职责：

```text
1. 读取 project_state/local_reverse_corpus_index.json。
2. 只选择 artifact_role=challenge_binary 且 extension=.exe 的样本。
3. 运行前验证路径仍在 E:\reverse 下。
4. 运行前验证 sha256 与 index 一致。
5. 每个样本设置 timeout。
6. 捕获 stdout/stderr/exit_code/timeout。
7. 不联网。
8. 不修改样本。
9. 不把二进制复制进仓库。
10. 输出 project_state/local_reverse_solve_benchmark.json。
```

推荐 CLI：

```bash
python -m reverse_agent.local_reverse_runtime ^
  --corpus-index project_state\local_reverse_corpus_index.json ^
  --policy project_state\local_reverse_runtime_policy.json ^
  --out project_state\local_reverse_solve_benchmark.json
```

---

### 6.4 Runtime probe 策略

对每个 exe 允许以下 bounded probe：

```text
1. run_no_input
2. run_with_empty_line
3. run_with_test
4. run_with_123456
5. run_with_password
6. run_with_flag_test
7. run_with_AAAA
8. run_with_16_A
```

每次运行记录：

```json
{
  "probe_name": "run_with_test",
  "stdin": "test\\n",
  "exit_code": 0,
  "timeout": false,
  "stdout_preview": "...",
  "stderr_preview": "...",
  "duration_ms": 123,
  "classification": "asks_for_input|prints_success_failure|silent_exit|timeout|gui_or_no_console|crash"
}
```

stdout/stderr preview 必须限制长度，例如 4096 字符。

---

### 6.5 Solve readiness 分类

每个题目输出：

```text
solve_readiness
```

取值：

```text
ready_static_string_compare
ready_xor_array_static
ready_shift_static
ready_crypto_known_family
needs_disassembly
needs_gui_interaction
needs_manual_review
blocked_runtime_error
unknown
```

不要直接声称已经 solved，除非真的输出了 flag 或正确输入，并且有 runtime 验证。

---

### 6.6 输出 benchmark 状态

新增：

```text
project_state/local_reverse_solve_benchmark.json
```

建议结构：

```json
{
  "schema_version": 1,
  "generated_at": "ISO-8601",
  "root": "E:\\reverse",
  "status": "READY|PARTIAL|BLOCKED",
  "challenge_count": 0,
  "executed_count": 0,
  "skipped_count": 0,
  "timeout_count": 0,
  "solved_count": 0,
  "samples": [
    {
      "sample_id": "...",
      "relative_path": "...",
      "sha256": "...",
      "artifact_role": "challenge_binary",
      "triage_tags": ["xor"],
      "runtime_allowed": true,
      "runtime_results": [],
      "solve_readiness": "ready_xor_array_static",
      "next_action": "extract compare constants and build per-sample solver"
    }
  ]
}
```

---

## 7. Tests

必须新增：

```text
tests/test_local_reverse_runtime.py
```

最低测试：

```text
1. policy 只允许 root 内 indexed exe。
2. sha256 mismatch 时不执行。
3. 非 .exe 不执行。
4. solver_script 不进入 challenge runtime 队列。
5. timeout 能被记录。
6. stdout/stderr preview 会截断。
7. benchmark JSON schema 正确。
8. missing root 或 missing sample 输出 BLOCKED/PARTIAL，不崩溃。
```

必须运行：

```bash
python -m py_compile reverse_agent\local_reverse_corpus.py reverse_agent\local_reverse_runtime.py
python -m pytest -q tests\test_local_reverse_corpus.py tests\test_local_reverse_runtime.py
python -m reverse_agent.local_reverse_corpus --root E:\reverse --out project_state\local_reverse_corpus_index.json --training-state project_state\local_reverse_training_state.json
python -m reverse_agent.local_reverse_runtime --corpus-index project_state\local_reverse_corpus_index.json --policy project_state\local_reverse_runtime_policy.json --out project_state\local_reverse_solve_benchmark.json
python -m reverse_agent.project_state lint-decision --state-dir project_state
python -m reverse_agent.project_state lint-report --state-dir project_state
git diff --check
```

---

## 8. Stop Conditions

出现以下情况必须停止：

```text
1. E:\reverse 不存在。
2. index 中 sha256 与当前文件不匹配。
3. 样本路径逃逸出 E:\reverse。
4. 运行 exe 超过 timeout。
5. 运行需要管理员权限。
6. 运行产生异常大量输出。
7. 运行结果需要复杂 GUI 自动化。
8. 需要复制二进制进仓库。
9. 需要无界 brute force。
10. 测试失败。
```

停止时输出：

```text
1. 哪些样本完成 runtime baseline。
2. 哪些样本 skipped/blocked。
3. 哪些题型最适合下一轮优先实现通用 solver。
4. 下一轮建议选择的 3 个具体 challenge_binary。
```
