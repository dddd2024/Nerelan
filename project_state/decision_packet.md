```json decision_meta
{
  "schema_version": 1,
  "decision_id": "decision_20260603_forced_ida_sub401005_extraction_v1",
  "round_id": "round_20260603_forced_ida_sub401005_extraction_v1",
  "based_on_state_build_id": "state_20260602_053948_4e3984041cd7",
  "based_on_state_digest": "4e3984041cd78e5a412e28a53fa3441957ea87f43f62a9688c3e80ca4413678c",
  "status": "APPROVED",
  "mainline": "tool_integration",
  "skill_profiles": [
    "reverse-agent-iteration@v2"
  ]
}
```

# DECISION_PACKET

## 1. Goal

本轮合并两个小任务，但主任务是 IDA 工具接入增强：

```text
1. 补齐上一轮 targeted_static_reextraction 的测试记录缺口：pytest_result.txt 必须记录 lint-decision、lint-report、git diff --check。
2. 增强现有 IDA/IDAPython 静态提取能力，对两个 unresolved 样本中的 sub_401005 做 forced extraction。
```

当前状态：

```text
Cpp1.exe / bcbd9979db015bfd 已解决：validated candidate = hookapi。
sha_256.exe 仍 blocked：NO_BOUNDED_HASH_PREIMAGE_DOMAIN。
CPP2.exe 仍 blocked：MISSING_UPSTREAM_TRANSFORM_FUNCTION:sub_401005。
上一轮 local_reverse_targeted_static_reextraction_result.json 只从 raw IDA JSON 复述了缺口，没有真正强制导出 sub_401005。
```

本轮目标不是直接求解，不生成新 candidate；目标是补出 `sub_401005` 的可信静态证据，让下一轮 reverse_solving 可以基于函数真实语义继续。

必须输出：

```text
project_state/local_reverse_forced_ida_sub401005_result.json
```

该结果必须覆盖且仅覆盖：

```text
18019fca52b389fe -> 逆向课程2024春01/sha_256.exe
4c69f173f2bd0211 -> 逆向课程2022春02/CPP2.exe
```

必须尝试导出：

```text
1. sub_401005 函数边界、入口地址、名称、大小。
2. Hex-Rays pseudocode；如果失败，记录失败原因和错误类型。
3. disassembly 基本块或指令列表。
4. constants/immediates。
5. calls/callees/callers。
6. xrefs to/from sub_401005。
7. function string refs。
8. stack/local variable summary if available。
9. 与 _main_0 的调用点关系：参数、输出 buffer、输入 prefix buffer、长度参数。
10. transform hypothesis：hash / hex encoding / char transform / table lookup / unknown。
```

如果 IDA/Hex-Rays 能导出 sub_401005 伪代码或反汇编，则下一轮可以进入 `sub401005_semantic_solver_v1`；如果不能，则必须输出 `BLOCKED_NEEDS_IDA_HEXRAYS_OR_DISASM_FIX`，不要伪造证据。

---

## 2. Current Evidence

当前主线：

```text
tool_integration
```

理由：本轮核心是增强 IDA/IDAPython 静态证据导出接口，不进行候选求解或动态验证。

当前执行权威是本 `decision_packet.md`，不是 `task_packet.task`。`task_packet.json` 里的旧 `samplereverse` 字段仍是背景兼容字段。

当前可信证据入口：

```text
project_state/local_reverse_validated_candidate_handoff.json
project_state/local_reverse_targeted_static_reextraction_result.json
project_state/local_reverse_constraint_recovery_result.json
project_state/local_reverse_ida_summary.json
project_state/artifact_index.json latest_artifacts_v2.local_reverse_* freshness=current
project_state/current_state.json local_reverse_training
```

已接受事实：

```text
1. Cpp1.exe hookapi 已 validated，handoff=current。
2. sha_256.exe 没有 bounded input domain，不能做无界 hash preimage。
3. CPP2.exe 的 input range 65..122 是 warning_only，不是 hard exit。
4. 两个 unresolved 样本都调用 sub_401005(Str1, &Destination, len)。
5. 当前 raw IDA JSON 缺 sub_401005 pseudocode/disasm/constants/callgraph。
6. 上一轮 pytest_result.txt 缺 lint-decision/lint-report/git diff --check 记录。
```

已有工具能力必须先检查并复用：

```text
reverse_agent/tool_runners.py
reverse_agent/local_reverse_ida_summary.py
reverse_agent/ida_scripts/collect_evidence.py
reverse_agent/local_reverse_targeted_static_reextract.py
reverse_agent/local_reverse_ida_guided_solver.py
```

原则：成熟工具优先。IDA/Hex-Rays 负责反汇编、反编译、XREF、函数、常量和调用图；reverse-agent 只负责编排、强制指定函数、结构化输出和 project_state 登记。

---

## 3. Do Not Do

严禁：

```text
1. 不扩大到 22 个样本。
2. 不处理这两个 unresolved 样本之外的 binary。
3. 不重新验证或改写 Cpp1 hookapi handoff。
4. 不生成新 candidate。
5. 不运行 solver。
6. 不运行 debugger/dynamic probe/Frida/OllyDbg/x64dbg。
7. 不运行 Ghidra。
8. 不做无界 brute force。
9. 不把 SHA-256/hash 当作可逆解密。
10. 不伪造 Hex-Rays pseudocode 或 disassembly。
11. 不新建第二套 IDA runner；必须复用现有 IDA runner 能力，只做 targeted wrapper/script。
12. 不复制、上传、提交、base64/hex 编码 E:\reverse 下的样本二进制。
13. 不提交完整 solve_reports/。
14. 不读取完整 solve_reports/。
15. 不读取完整 PROJECT_PROGRESS_LOG.txt。
16. 不修改 .codex-skills/。
17. 不把 hookapi 写入长期 skill 或硬编码成通用规则。
18. 不引入数据库、消息队列、Redis、Celery、Kubernetes、Airflow、Temporal、LangGraph。
```

允许：

```text
1. 复用现有 IDA runner，对两个 unresolved 样本做 targeted static extraction。
2. 新增最小 IDAPython 脚本 reverse_agent/ida_scripts/forced_function_extract.py。
3. 新增最小 Python wrapper reverse_agent/local_reverse_forced_ida_extract.py。
4. 只对 sub_401005 和必要的 _main_0 调用点导出证据。
5. 生成 project_state/local_reverse_forced_ida_sub401005_result.json。
6. 更新 artifact_index/current_state/task_packet 的 local_reverse advisory 字段。
7. 更新 codex_execution_report.md 和 pytest_result.txt。
8. 只读取 artifact_index/current_state 指向的两个 unresolved raw IDA JSON 作为输入线索。
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
project_state/local_reverse_validated_candidate_handoff.json
project_state/local_reverse_targeted_static_reextraction_result.json
project_state/local_reverse_ida_summary.json
project_state/local_reverse_runtime_policy.json
reverse_agent/tool_runners.py
reverse_agent/local_reverse_ida_summary.py
reverse_agent/ida_scripts/collect_evidence.py
reverse_agent/local_reverse_targeted_static_reextract.py
```

有界读取，仅限两个 unresolved 样本的 current raw IDA JSON：

```text
solve_reports\tool_artifacts\local_reverse_ida_evidence_integration_v1\18019fca52b389fe\sha_256_ida_evidence.json
solve_reports\tool_artifacts\local_reverse_ida_evidence_integration_v1\4c69f173f2bd0211\CPP2_ida_evidence.json
```

必要时读取：

```text
tests/test_tool_runners.py
tests/test_local_reverse_ida_summary.py
tests/test_local_reverse_targeted_static_reextract.py
tests/test_project_state.py
```

不要默认读取：

```text
solve_reports/ 全目录
PROJECT_PROGRESS_LOG.txt
```

---

## 5. Required Audit

Codex 必须在 `project_state/codex_execution_report.md` 中写明：

```text
1. 当前 decision_packet 是执行权威。
2. 本轮 mainline=tool_integration，不是 solver 轮。
3. 本轮只处理 sha_256.exe 和 CPP2.exe 的 sub_401005 forced static extraction。
4. Cpp1 hookapi handoff 保持 current，未重新验证、未覆盖。
5. 是否复用现有 IDA runner；如果新增 wrapper/script，说明边界。
6. 实际运行的 IDA/IDAPython 命令、目标、输出路径。
7. 每个样本 sub_401005 的 pseudocode/disasm/constants/calls/xrefs 导出状态。
8. sha_256 的 NO_BOUNDED_HASH_PREIMAGE_DOMAIN 是否仍保持。
9. CPP2 的 MISSING_UPSTREAM_TRANSFORM_FUNCTION:sub_401005 是否解除。
10. 新 result artifact path、status、target_count。
11. artifact_index/current_state/task_packet 更新内容。
12. 是否补齐上一轮缺失的 lint-decision/lint-report/git diff --check 测试记录。
13. 未扩大样本。
14. 未复制、提交、上传或编码样本二进制。
15. 未读取完整 solve_reports/ 或 PROJECT_PROGRESS_LOG.txt。
16. 未修改 .codex-skills/。
17. 未运行 debugger/dynamic probe/Ghidra。
18. 测试真实运行并写入 project_state/pytest_result.txt。
```

报告顶部必须包含：

```json codex_report_summary
{
  "schema_version": 1,
  "report_id": "report_20260603_forced_ida_sub401005_extraction_v1",
  "round_id": "round_20260603_forced_ida_sub401005_extraction_v1",
  "based_on_decision_id": "decision_20260603_forced_ida_sub401005_extraction_v1",
  "status": "SUCCESS_OR_PARTIAL_OR_BLOCKED",
  "acceptance_recommendation": "ACCEPT_OR_NEEDS_REVIEW_OR_REWORK",
  "files_changed": [],
  "tests_ran": [],
  "generated_artifacts": []
}
```

---

## 6. Implementation Scope

### 6.1 First inspect existing IDA runner

先确认现有 IDA runner 可否接受指定 script / target / output：

```bash
python -m reverse_agent.local_reverse_ida_summary --help
```

并检查：

```text
reverse_agent/tool_runners.py
reverse_agent/local_reverse_ida_summary.py
reverse_agent/ida_scripts/collect_evidence.py
```

如果已有 runner 能直接运行自定义 IDAPython，复用它；否则做最小 wrapper，不复制 runner。

### 6.2 IDAPython targeted script

如需新增脚本，推荐：

```text
reverse_agent/ida_scripts/forced_function_extract.py
```

输入参数应包含：

```text
--functions sub_401005,_main_0
--out <json>
```

导出字段：

```json
{
  "schema_version": 1,
  "ida_script": "forced_function_extract",
  "functions": [
    {
      "name": "sub_401005",
      "ea": "0x401005",
      "exists": true,
      "size": 0,
      "pseudocode_available": false,
      "pseudocode": "",
      "pseudocode_error": "",
      "disasm_available": true,
      "disasm": [],
      "constants": [],
      "calls": [],
      "callers": [],
      "xrefs_to": [],
      "xrefs_from": [],
      "string_refs": [],
      "local_vars": []
    }
  ],
  "main_callsite_relation": []
}
```

必须调用 IDA/Hex-Rays API；不要自己写反汇编器。

### 6.3 Python wrapper

推荐新增：

```text
reverse_agent/local_reverse_forced_ida_extract.py
```

CLI：

```bash
python -m reverse_agent.local_reverse_forced_ida_extract --artifact-index project_state\artifact_index.json --ida-summary project_state\local_reverse_ida_summary.json --handoff project_state\local_reverse_validated_candidate_handoff.json --targeted-result project_state\local_reverse_targeted_static_reextraction_result.json --policy project_state\local_reverse_runtime_policy.json --ida-path "E:\Program Files\ida_pro" --out project_state\local_reverse_forced_ida_sub401005_result.json
```

职责：

```text
1. 强制 latest_artifacts_v2 freshness=current。
2. 只选择 sha_256 和 CPP2 两个 unresolved target。
3. 保留 Cpp1 handoff，不重新验证。
4. 通过现有 IDA runner 对两个样本运行 forced_function_extract.py。
5. 汇总每个样本的 sub_401005 extraction result。
6. 输出 project_state/local_reverse_forced_ida_sub401005_result.json。
```

### 6.4 Output schema

`project_state/local_reverse_forced_ida_sub401005_result.json` 必须包含：

```json
{
  "schema_version": 1,
  "stage": "forced_ida_sub401005_extraction_v1",
  "status": "SUCCESS_OR_PARTIAL_OR_BLOCKED",
  "target_count": 2,
  "source_targeted_static_reextraction": "project_state\\local_reverse_targeted_static_reextraction_result.json",
  "preserved_validated_handoff": "project_state\\local_reverse_validated_candidate_handoff.json",
  "targets": [
    {
      "sample_id": "18019fca52b389fe",
      "relative_path": "逆向课程2024春01/sha_256.exe",
      "target_function": "sub_401005",
      "extraction_status": "success|partial|blocked",
      "ida_output_path": "...",
      "pseudocode_available": false,
      "disasm_available": false,
      "constants": [],
      "calls": [],
      "callers": [],
      "xrefs_to": [],
      "xrefs_from": [],
      "string_refs": [],
      "transform_hypothesis": "",
      "blocker_resolved": false,
      "next_action": "..."
    },
    {
      "sample_id": "4c69f173f2bd0211",
      "relative_path": "逆向课程2022春02/CPP2.exe",
      "target_function": "sub_401005",
      "extraction_status": "success|partial|blocked",
      "ida_output_path": "...",
      "pseudocode_available": false,
      "disasm_available": false,
      "constants": [],
      "calls": [],
      "callers": [],
      "xrefs_to": [],
      "xrefs_from": [],
      "string_refs": [],
      "transform_hypothesis": "",
      "blocker_resolved": false,
      "next_action": "..."
    }
  ]
}
```

If IDA is unavailable, missing, or the script cannot be run, output status=`BLOCKED` and explain; do not fabricate extraction.

### 6.5 State updates

若 result 生成成功，登记：

```text
artifact_index.latest_artifacts_v2.local_reverse_forced_ida_sub401005_result
```

字段必须包括：

```text
kind=local_reverse_forced_ida_sub401005_result
path=project_state\local_reverse_forced_ida_sub401005_result.json
freshness=current
source_run=round_20260603_forced_ida_sub401005_extraction_v1
sha256
size_bytes
modified_at
```

更新或确认：

```text
current_state.json local_reverse_training.latest_forced_ida_sub401005
current_state.json local_reverse_training.latest_forced_ida_sub401005_status
task_packet.json local_reverse_current_artifact / local_reverse_next_suggested_task
```

不要删除旧 samplereverse 字段。

---

## 7. Tests

必须运行并写入 `project_state/pytest_result.txt`：

```bash
python -m py_compile reverse_agent\local_reverse_forced_ida_extract.py reverse_agent\ida_scripts\forced_function_extract.py
```

必须运行 CLI；如果 IDA 路径可用，显式传入：

```bash
python -m reverse_agent.local_reverse_forced_ida_extract --artifact-index project_state\artifact_index.json --ida-summary project_state\local_reverse_ida_summary.json --handoff project_state\local_reverse_validated_candidate_handoff.json --targeted-result project_state\local_reverse_targeted_static_reextraction_result.json --policy project_state\local_reverse_runtime_policy.json --ida-path "E:\Program Files\ida_pro" --out project_state\local_reverse_forced_ida_sub401005_result.json
```

必须校验输出：

```bash
python -m json.tool project_state\local_reverse_forced_ida_sub401005_result.json > NUL
python -c "import json; d=json.load(open('project_state/local_reverse_forced_ida_sub401005_result.json', encoding='utf-8')); assert d['target_count']==2; assert len(d['targets'])==2; assert {t['sample_id'] for t in d['targets']} == {'18019fca52b389fe','4c69f173f2bd0211'}"
```

必须新增或扩展测试：

```text
tests/test_local_reverse_forced_ida_extract.py
```

测试至少覆盖：

```text
1. 只选择 sha_256 和 CPP2，不选择 Cpp1。
2. stale/missing latest_artifacts_v2 raw evidence -> blocked。
3. handoff 缺 hookapi validated -> blocked。
4. IDA unavailable -> result status BLOCKED，不伪造 pseudocode/disasm。
5. forced_function_extract.py 输出被 wrapper 正确归一化。
6. output target_count=2。
7. Cpp1 hookapi handoff 不被覆盖或重写。
```

必须运行相关回归：

```bash
python -m pytest -q tests\test_local_reverse_forced_ida_extract.py tests\test_local_reverse_targeted_static_reextract.py tests\test_local_reverse_ida_summary.py tests\test_project_state.py
```

必须补齐上一轮缺失记录并运行：

```bash
python -m reverse_agent.project_state lint-decision --state-dir project_state
python -m reverse_agent.project_state lint-report --state-dir project_state
git diff --check
```

如果修改 tool_runners.py 或公共 IDA runner，必须额外运行：

```bash
python -m pytest -q tests\test_tool_runners.py
```

---

## 8. Stop Conditions

出现以下任一情况立即停止并报告：

```text
1. current handoff artifact 缺失或 hookapi 不再 validated。
2. current raw IDA evidence 缺失或 freshness 不是 current。
3. IDA 路径缺失且无法通过 PATH 解析；此时输出 BLOCKED_IDA_UNAVAILABLE。
4. forced_function_extract.py 无法被 IDA 执行；此时输出 BLOCKED_IDA_SCRIPT_FAILURE。
5. 需要读取完整 solve_reports/ 才能继续。
6. 需要读取完整 PROJECT_PROGRESS_LOG.txt 才能继续。
7. 需要扩大到两个 unresolved 样本之外才能继续。
8. 需要运行 debugger/dynamic probe/Ghidra 才能继续。
9. 需要无界 brute force 才能继续。
10. 需要复制、上传、提交或编码样本二进制才能继续。
```

本轮完成标准：

```text
project_state/local_reverse_forced_ida_sub401005_result.json 已生成；
只包含 sha_256.exe 和 CPP2.exe 两个 target；
Cpp1 hookapi handoff 保持 current，不被覆盖；
每个 target 都有 sub_401005 pseudocode/disasm/constants/calls/xrefs 的导出状态；
若无法导出，给出明确 IDA/Hex-Rays/script failure 原因；
artifact_index/current_state/task_packet 已同步；
codex_execution_report.md 和 pytest_result.txt 对应本 decision；
pytest_result.txt 记录 lint-decision/lint-report/git diff --check；
没有扩大样本、没有运行 debugger/Ghidra、没有提交二进制。
```
