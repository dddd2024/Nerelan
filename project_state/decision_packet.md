```json decision_meta
{
  "schema_version": 1,
  "decision_id": "decision_20260603_local_reverse_ida_path_rerun_v1",
  "round_id": "round_20260603_local_reverse_ida_path_rerun_v1",
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

## 1. Goal

本轮目标是用用户新提供的 IDA 安装目录：

```text
E:\Program Files\ida_pro
```

重新执行本地逆向训练线的 IDA evidence integration。

只处理上一轮被 IDA 不可用阻塞的 3 个目标：

```text
18019fca52b389fe -> 逆向课程2024春01/sha_256.exe
4c69f173f2bd0211 -> 逆向课程2022春02/CPP2.exe
bcbd9979db015bfd -> 逆向课程2022春补考01/Cpp1.exe
```

本轮输出：

```text
project_state/local_reverse_ida_summary.json
```

如果 IDA 能正常运行，则 summary 中应出现真实 `strings_summary`、`compare_contexts_summary`、`local_check_contexts_summary`、`string_xrefs_summary`、`validation_function_candidates`、`decompiler_snippets` 或 `solver_hints`。

如果 IDA 路径仍不可用，必须继续记录 `BLOCKED_BY_IDA_UNAVAILABLE`，不得伪造 IDA/Hex-Rays 结果。

本轮不是进入 solver，不是扩大样本，不是 GUI 整合。

---

## 2. Current Evidence

当前主线是：

```text
reverse_solving / local_reverse_simple_training
```

当前可用 skill profile 为：

```text
reverse-agent-iteration@v2
```

`.codex-skills/registry.json` 中 `reverse-agent-iteration` 状态为 active，version=2。

上一轮 `project_state/local_reverse_ida_summary.json` 状态：

```text
status=BLOCKED
target_count=3
ida_available=false
hexrays_available_any=false
success_count=0
```

三个目标全部因为 `BLOCKED_BY_IDA_UNAVAILABLE` 被阻塞。

上一轮 blocker 是环境配置问题，不是工程逻辑必须继续重构。用户本轮已经提供 IDA 目录：

```text
E:\Program Files\ida_pro
```

现有代码能力：

```text
1. reverse_agent/local_reverse_ida_summary.py 已支持 --ida-path。
2. run_local_reverse_ida_summary() 会把 ida_executable 传给 run_ida_evidence。
3. reverse_agent/tool_runners.py 的 _resolve_ida_executable() 支持用户传入目录。
4. 目录模式下会依次查找 idat64.exe / idat.exe / ida64.exe / ida.exe。
5. reverse_agent/ida_scripts/collect_evidence.py 是现有 IDA evidence 脚本，本轮必须复用。
```

runtime policy 当前限定：

```text
root=E:\reverse
runtime_allowed=true
allowed_extensions=.exe
path_scope=indexed_files_under_root_only
network_allowed=false
copy_binary_into_repo=false
default_timeout_seconds=5
max_timeout_seconds=15
```

旧 `task_packet.json` / `current_state.json` 中仍可能存在 `samplereverse` 背景字段，只能作为旧状态背景，不能覆盖本 decision。

---

## 3. Do Not Do

严禁：

```text
1. 不修改 .codex-skills/。
2. 不扩大到 22 个样本。
3. 不处理这 3 个目标之外的 challenge binary。
4. 不复制、上传、提交、base64/hex 编码 E:\reverse 下的样本二进制。
5. 不读取完整 solve_reports/。
6. 不读取完整 PROJECT_PROGRESS_LOG.txt。
7. 不新建另一套 IDA runner。
8. 不复制 _run_ida 逻辑。
9. 不重写 collect_evidence.py。
10. 不继续 samplereverse 的窗口发现、compare handoff、Base64/RC4 breakpoint probe。
11. 不回旧 sample_solver 盲搜。
12. 不做无界 brute force。
13. 不在 IDA evidence 成功前进入 solver。
14. 不伪造 IDA/Hex-Rays 输出。
15. 不因为 Hex-Rays 不可用就判定 IDA 失败；Hex-Rays 只能作为可选增强。
16. 不把本轮扩展为 GUI 前端整合。
17. 不引入数据库、Redis、Celery、Kubernetes、Airflow、Temporal、LangGraph。
```

允许：

```text
1. 使用 --ida-path "E:\Program Files\ida_pro" 重新运行 local_reverse_ida_summary。
2. 必要时只做最小修复：如果路径包含空格导致命令构造问题，可以修正引用/参数传递。
3. 必要时只做最小修复：如果 ida_pro 目录下实际可执行文件名不在现有查找列表中，可添加该文件名。
4. 读取 project_state/local_reverse_corpus_index.json。
5. 读取 project_state/local_reverse_semantic_rule_result.json。
6. 读取 project_state/local_reverse_runtime_policy.json。
7. 读取 reverse_agent/tool_runners.py。
8. 读取 reverse_agent/local_reverse_ida_summary.py。
9. 读取 reverse_agent/ida_scripts/collect_evidence.py。
10. 重新生成 project_state/local_reverse_ida_summary.json。
11. 运行必要测试并写入 project_state/pytest_result.txt。
12. 写入 project_state/codex_execution_report.md。
```

---

## 4. Files To Inspect

必须读取：

```text
project_state/task_packet.json
project_state/current_state.json
project_state/artifact_index.json
project_state/negative_results.json
project_state/decision_packet.md
project_state/codex_execution_report.md
project_state/pytest_result.txt
project_state/local_reverse_ida_summary.json
project_state/local_reverse_corpus_index.json
project_state/local_reverse_semantic_rule_result.json
project_state/local_reverse_runtime_policy.json
reverse_agent/tool_runners.py
reverse_agent/local_reverse_ida_summary.py
reverse_agent/ida_scripts/collect_evidence.py
tests/test_local_reverse_ida_summary.py
tests/test_tool_runners.py
```

不要默认读取：

```text
solve_reports/
PROJECT_PROGRESS_LOG.txt
```

---

## 5. Required Audit

Codex 必须在 `project_state/codex_execution_report.md` 中写明：

```text
1. 当前 decision_packet 是执行权威。
2. 用户本轮新增 IDA 路径：E:\Program Files\ida_pro。
3. 本轮只重新运行 local_reverse_ida_summary，不进入 solver。
4. 只处理 3 个 previous_missing_evidence=needs_symbolic_execution 目标。
5. 未处理 3 个目标之外的 challenge binary。
6. 未复制、提交、上传或编码任何样本二进制。
7. 未修改 .codex-skills/。
8. 未读取完整 solve_reports/ 或 PROJECT_PROGRESS_LOG.txt。
9. 是否成功解析到 IDA 可执行文件。
10. 实际解析到的 IDA 可执行文件路径，例如 idat64.exe / ida64.exe。
11. 每个目标的 ida_status。
12. 每个目标是否产生真实 IDA JSON output。
13. Hex-Rays 是否可用；不可用时必须记录 hexrays_available=false。
14. 是否产生 strings / compare_contexts / string_xrefs / validation_function_candidates / solver_hints。
15. 测试真实运行并写入 project_state/pytest_result.txt。
```

报告顶部必须包含：

```json codex_report_summary
{
  "schema_version": 1,
  "report_id": "report_20260603_local_reverse_ida_path_rerun_v1",
  "round_id": "round_20260603_local_reverse_ida_path_rerun_v1",
  "based_on_decision_id": "decision_20260603_local_reverse_ida_path_rerun_v1",
  "status": "SUCCESS_OR_PARTIAL_OR_BLOCKED",
  "acceptance_recommendation": "ACCEPT_OR_NEEDS_REVIEW_OR_REWORK",
  "files_changed": [],
  "tests_ran": [],
  "generated_artifacts": []
}
```

---

## 6. Implementation Scope

### 6.1 首先直接运行，不改代码

优先直接执行：

```bash
python -m reverse_agent.local_reverse_ida_summary --corpus-index project_state\local_reverse_corpus_index.json --semantic-result project_state\local_reverse_semantic_rule_result.json --policy project_state\local_reverse_runtime_policy.json --ida-path "E:\Program Files\ida_pro" --out project_state\local_reverse_ida_summary.json
```

预期变化：

```text
ida_available=true
至少部分 target 的 ida_status=success
成功 target 的 ida_output_path 非空
```

如果三个目标都成功，则本轮不要继续求解，只记录 evidence summary。

### 6.2 如果 IDA 仍不可用，做有界诊断

只允许检查：

```text
E:\Program Files\ida_pro\idat64.exe
E:\Program Files\ida_pro\idat.exe
E:\Program Files\ida_pro\ida64.exe
E:\Program Files\ida_pro\ida.exe
```

如果实际文件名不同，只做最小兼容修复 `_resolve_ida_executable()` 的候选列表。

不得写新的 IDA 启动器。

### 6.3 如果 IDA 成功但输出解析失败

只允许检查：

```text
reverse_agent/ida_scripts/collect_evidence.py
reverse_agent/tool_runners.py
reverse_agent/local_reverse_ida_summary.py
```

处理方式：

```text
1. 保留旧字段兼容。
2. 不删除 strings / functions / compare_contexts / local_check_contexts / control_id_contexts。
3. 只修复 JSON 输出、路径、编码、空字段容错。
4. 不把 IDA 输出伪造成 success。
```

### 6.4 如果只有部分目标成功

输出 `PARTIAL`，并保留每个目标的具体 blocked/failed reason。

不要因为一个样本成功就进入 solver。

---

## 7. Tests

必须运行：

```bash
python -m py_compile reverse_agent\tool_runners.py reverse_agent\local_reverse_ida_summary.py reverse_agent\ida_scripts\collect_evidence.py
```

```bash
python -m pytest -q tests\test_local_reverse_ida_summary.py tests\test_tool_runners.py
```

```bash
python -m reverse_agent.local_reverse_ida_summary --corpus-index project_state\local_reverse_corpus_index.json --semantic-result project_state\local_reverse_semantic_rule_result.json --policy project_state\local_reverse_runtime_policy.json --ida-path "E:\Program Files\ida_pro" --out project_state\local_reverse_ida_summary.json
```

如果修改了公共 runner，再运行：

```bash
python -m pytest -q
```

最后运行：

```bash
python -m reverse_agent.project_state lint-decision --state-dir project_state
python -m reverse_agent.project_state lint-report --state-dir project_state
git diff --check
```

测试结果必须写入：

```text
project_state/pytest_result.txt
```

---

## 8. Stop Conditions

出现以下任一情况立即停止并报告：

```text
1. IDA 路径不存在。
2. ida_pro 目录存在，但找不到 idat64.exe / idat.exe / ida64.exe / ida.exe。
3. 样本路径不在 E:\reverse 下。
4. 样本 sha256 与 corpus index 不一致。
5. IDA 启动后没有生成 JSON evidence。
6. collect_evidence.py 抛出异常且无法在本轮最小修复。
7. 任意二进制样本被复制进仓库。
8. 需要读取完整 solve_reports/ 或 PROJECT_PROGRESS_LOG.txt 才能继续。
9. 需要扩大到 3 个目标之外。
10. 需要进入 solver 才能继续。
```

本轮完成标准：

```text
project_state/local_reverse_ida_summary.json 已重新生成；
project_state/codex_execution_report.md 已记录本轮真实状态；
project_state/pytest_result.txt 已记录测试；
没有伪造 IDA/Hex-Rays evidence；
没有扩大 scope。
```
