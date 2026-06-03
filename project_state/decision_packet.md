```json decision_meta
{
  "schema_version": 1,
  "decision_id": "decision_20260603_local_reverse_targeted_static_reextraction_v1",
  "round_id": "round_20260603_local_reverse_targeted_static_reextraction_v1",
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

本轮目标是对两个 unresolved local reverse 样本做 targeted static re-extraction，为下一轮继续求解提供更精确的静态证据。

当前已经完成并接受：

```text
Cpp1.exe / bcbd9979db015bfd 已有 validated candidate: hookapi
handoff artifact: project_state\local_reverse_validated_candidate_handoff.json
```

本轮不再处理 Cpp1 的求解，只把它作为已解决样本保留在状态中。

只处理以下两个未解决样本：

```text
18019fca52b389fe -> 逆向课程2024春01/sha_256.exe
4c69f173f2bd0211 -> 逆向课程2022春02/CPP2.exe
```

本轮必须输出：

```text
project_state/local_reverse_targeted_static_reextraction_result.json
```

目标证据：

```text
1. sha_256.exe:
   - 输入长度、prefix、scanf/gets/fgets/cin 等输入 API 上下文。
   - hash 前的 input buffer 数据流。
   - sub_401005 的调用参数、返回值、写入 buffer、格式化输出关系。
   - 是否存在题目提示、内置字典、固定 prefix、长度上界或可枚举输入域。
   - 若没有 bounded input domain，必须保持 NO_BOUNDED_HASH_PREIMAGE_DOMAIN，不得做 hash preimage 盲搜。

2. CPP2.exe:
   - sub_401005 的伪代码/反汇编/常量/局部变量/调用图。
   - sub_401005 是否为 hash、逐字符变换、查表、XOR/add/sub/shift/rotate/affine 或其它可逆变换。
   - main 中 post-increment 前后的 target、长度、输入范围 65..122、compare 关系。
   - 若 sub_401005 不能恢复，必须给出精确缺口：缺伪代码、缺调用图、缺常量、缺 buffer xref 或缺 transform relation。
```

允许有界使用现有 IDA runner/IDAPython 能力做 targeted static re-extraction。禁止重新跑 22 个样本，禁止 debugger/dynamic probe，禁止无界 brute force。

---

## 2. Current Evidence

当前主线：

```text
reverse_solving
```

理由：本轮围绕两个具体未解样本补充求解所需静态证据，而不是做通用工程重构。

当前执行权威是本 `decision_packet.md`，不是 `task_packet.task`。

当前可信证据入口：

```text
project_state/local_reverse_validated_candidate_handoff.json
project_state/local_reverse_constraint_recovery_result.json
project_state/local_reverse_ida_summary.json
project_state/local_reverse_ida_solver_result.json
project_state/artifact_index.json latest_artifacts_v2.local_reverse_* freshness=current
project_state/current_state.json local_reverse_training
```

当前已解决样本：

```text
bcbd9979db015bfd / Cpp1.exe
candidate=hookapi
validation_status=validated
source_artifact=project_state\local_reverse_validated_candidate_handoff.json
```

当前未解决样本：

```text
sha_256.exe:
  blocked_reason=NO_BOUNDED_HASH_PREIMAGE_DOMAIN
  next_action=targeted static re-extraction of input length/domain or request problem statement hint

CPP2.exe:
  blocked_reason=MISSING_UPSTREAM_TRANSFORM_FUNCTION:sub_401005
  next_action=recover sub_401005 transform or bounded dictionary before inversion
```

已有工具能力必须优先检查和复用：

```text
reverse_agent/tool_runners.py
reverse_agent/local_reverse_ida_summary.py
reverse_agent/ida_scripts/collect_evidence.py
reverse_agent/local_reverse_ida_guided_solver.py
reverse_agent/local_reverse_constraint_recovery.py
reverse_agent/local_reverse_runtime.py
```

原则：成熟工具优先。IDA/Hex-Rays 能给出的伪代码、XREF、函数、常量、字符串和调用图，不要在项目里重复实现反编译器。若需要新增代码，只写薄 wrapper / targeted extractor / result normalizer。

---

## 3. Do Not Do

严禁：

```text
1. 不扩大到 22 个样本。
2. 不处理这两个 unresolved 样本之外的 binary。
3. 不重新求解或重复验证 Cpp1.exe；Cpp1 hookapi 已作为 accepted handoff。
4. 不复制、上传、提交、base64/hex 编码 E:\reverse 下的样本二进制。
5. 不提交完整 solve_reports/。
6. 不读取完整 solve_reports/。
7. 不读取完整 PROJECT_PROGRESS_LOG.txt。
8. 不修改 .codex-skills/。
9. 不回旧 sample_solver 盲搜。
10. 不做无界 brute force。
11. 不把 SHA-256/hash 当作可逆解密。
12. 不伪造 bounded input domain。
13. 不伪造 Hex-Rays/IDA evidence。
14. 不运行 OllyDbg/x64dbg/Frida/debugger/dynamic probe。
15. 不运行 Ghidra，除非本轮明确 BLOCKED 并在下一轮单独申请。
16. 不新建第二套 IDA runner；必须复用现有 tool_runners/local_reverse_ida_summary 相关能力或做最小扩展。
17. 不把 `hookapi` 写入长期 skill 或硬编码成通用 solver。
18. 不引入数据库、消息队列、Redis、Celery、Kubernetes、Airflow、Temporal、LangGraph。
```

允许：

```text
1. 有界读取当前 artifact_index/current_state 指向的 raw IDA JSON。
2. 有界运行现有 IDA runner 对两个 unresolved 样本做 targeted static re-extraction。
3. 新增或扩展一个最小 targeted static re-extraction CLI，例如 reverse_agent/local_reverse_targeted_static_reextract.py。
4. 新增或扩展 IDAPython 脚本，但必须是 targeted extraction，不得复制已有 collect_evidence.py 的通用逻辑。
5. 读取/导出指定函数 sub_401005、_main_0、相关 XREF、字符串、常量、伪代码和反汇编片段。
6. 生成 project_state/local_reverse_targeted_static_reextraction_result.json。
7. 必要时更新 artifact_index/current_state/task_packet 的 local_reverse advisory 字段。
8. 更新 codex_execution_report.md 和 pytest_result.txt。
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
project_state/local_reverse_constraint_recovery_result.json
project_state/local_reverse_ida_summary.json
project_state/local_reverse_ida_solver_result.json
project_state/local_reverse_runtime_policy.json
reverse_agent/tool_runners.py
reverse_agent/local_reverse_ida_summary.py
reverse_agent/ida_scripts/collect_evidence.py
reverse_agent/local_reverse_ida_guided_solver.py
reverse_agent/local_reverse_constraint_recovery.py
```

有界读取，仅限两个 unresolved 样本的 raw IDA JSON：

```text
solve_reports\tool_artifacts\local_reverse_ida_evidence_integration_v1\18019fca52b389fe\sha_256_ida_evidence.json
solve_reports\tool_artifacts\local_reverse_ida_evidence_integration_v1\4c69f173f2bd0211\CPP2_ida_evidence.json
```

必要时读取：

```text
tests/test_local_reverse_ida_guided_solver.py
tests/test_local_reverse_constraint_recovery.py
tests/test_local_reverse_ida_summary.py
tests/test_tool_runners.py
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
2. mainline=reverse_solving。
3. 本轮只处理 sha_256.exe 和 CPP2.exe，Cpp1 hookapi 只作为已解决 handoff 保留。
4. 是否复用现有 IDA runner / IDAPython 能力；如新增 wrapper，说明为什么需要。
5. 是否运行 targeted IDA re-extraction；如果运行，列出命令、目标、输出路径。
6. 是否只读取两个 unresolved 样本的 raw IDA JSON。
7. sha_256.exe 发现了哪些 input-domain / length / prefix / API / buffer-flow 证据。
8. CPP2.exe sub_401005 恢复了哪些 pseudo/disasm/constants/callgraph/xref 证据。
9. 是否足以解除 NO_BOUNDED_HASH_PREIMAGE_DOMAIN 或 MISSING_UPSTREAM_TRANSFORM_FUNCTION:sub_401005。
10. 新 artifact path、status、target_count。
11. artifact_index/current_state/task_packet 更新内容。
12. 未扩大样本。
13. 未复制、提交、上传或编码样本二进制。
14. 未读取完整 solve_reports/ 或 PROJECT_PROGRESS_LOG.txt。
15. 未修改 .codex-skills/。
16. 未运行 debugger/dynamic probe/Ghidra。
17. 测试真实运行并写入 project_state/pytest_result.txt。
```

报告顶部必须包含：

```json codex_report_summary
{
  "schema_version": 1,
  "report_id": "report_20260603_local_reverse_targeted_static_reextraction_v1",
  "round_id": "round_20260603_local_reverse_targeted_static_reextraction_v1",
  "based_on_decision_id": "decision_20260603_local_reverse_targeted_static_reextraction_v1",
  "status": "SUCCESS_OR_PARTIAL_OR_BLOCKED",
  "acceptance_recommendation": "ACCEPT_OR_NEEDS_REVIEW_OR_REWORK",
  "files_changed": [],
  "tests_ran": [],
  "generated_artifacts": []
}
```

---

## 6. Implementation Scope

### 6.1 First inspect existing capability

先检查现有入口能否完成 targeted extraction：

```bash
python -m reverse_agent.local_reverse_ida_summary --help
```

以及现有代码：

```text
reverse_agent/tool_runners.py
reverse_agent/local_reverse_ida_summary.py
reverse_agent/ida_scripts/collect_evidence.py
```

如果现有 `collect_evidence.py` 已包含所需字段，不要新增 IDAPython，只从 raw JSON 里提取并整理。

如果 raw JSON 缺字段，才允许新增最小 targeted extractor。

### 6.2 Optional targeted extractor

若需要新增，推荐：

```text
reverse_agent/local_reverse_targeted_static_reextract.py
```

CLI：

```bash
python -m reverse_agent.local_reverse_targeted_static_reextract --artifact-index project_state\artifact_index.json --ida-summary project_state\local_reverse_ida_summary.json --handoff project_state\local_reverse_validated_candidate_handoff.json --out project_state\local_reverse_targeted_static_reextraction_result.json
```

职责：

```text
1. 读取 current artifact metadata，强制 latest_artifacts_v2.freshness=current。
2. 只加载两个 unresolved raw IDA JSON。
3. 提取 sha_256 的 input-domain evidence。
4. 提取 CPP2 的 sub_401005 evidence。
5. 必要时通过现有 IDA runner 执行 targeted IDAPython extraction。
6. 输出结构化 JSON。
```

如果新增 IDAPython 脚本，推荐：

```text
reverse_agent/ida_scripts/targeted_static_extract.py
```

只允许输出：

```text
function pseudocode/disasm for _main_0 and sub_401005
function call graph around sub_401005
xrefs to input buffer / compare target / format string
constants and string refs in selected functions
input API context
```

不要重新实现反编译/反汇编算法，调用 IDA/Hex-Rays API 即可。

### 6.3 Output schema

`project_state/local_reverse_targeted_static_reextraction_result.json` 必须包含：

```json
{
  "schema_version": 1,
  "stage": "local_reverse_targeted_static_reextraction_v1",
  "status": "SUCCESS_OR_PARTIAL_OR_BLOCKED",
  "target_count": 2,
  "source_handoff": "project_state\\local_reverse_validated_candidate_handoff.json",
  "targets": [
    {
      "sample_id": "18019fca52b389fe",
      "relative_path": "逆向课程2024春01/sha_256.exe",
      "previous_blocker": "NO_BOUNDED_HASH_PREIMAGE_DOMAIN",
      "extraction_status": "success|partial|blocked",
      "recovered_evidence": [],
      "bounded_input_domain": {
        "status": "found|not_found|partial",
        "constraints": [],
        "candidate_source": ""
      },
      "next_action": "..."
    },
    {
      "sample_id": "4c69f173f2bd0211",
      "relative_path": "逆向课程2022春02/CPP2.exe",
      "previous_blocker": "MISSING_UPSTREAM_TRANSFORM_FUNCTION:sub_401005",
      "extraction_status": "success|partial|blocked",
      "sub_401005_evidence": {
        "pseudocode_available": false,
        "disasm_available": false,
        "constants": [],
        "callgraph": [],
        "string_refs": [],
        "transform_hypothesis": ""
      },
      "blocker_resolved": false,
      "next_action": "..."
    }
  ]
}
```

### 6.4 State updates

若 result 生成成功，必须登记：

```text
artifact_index.latest_artifacts_v2.local_reverse_targeted_static_reextraction_result
```

字段必须包括：

```text
kind=local_reverse_targeted_static_reextraction_result
path=project_state\local_reverse_targeted_static_reextraction_result.json
freshness=current
source_run=round_20260603_local_reverse_targeted_static_reextraction_v1
sha256
size_bytes
modified_at
```

必须更新或确认：

```text
current_state.json local_reverse_training.latest_targeted_static_reextraction
task_packet.json local_reverse_current_artifact / local_reverse_next_suggested_task
```

不要删除旧 samplereverse 字段。

---

## 7. Tests

必须运行：

```bash
python -m py_compile reverse_agent\local_reverse_targeted_static_reextract.py
```

如果新增 IDAPython script，至少运行语法检查或 AST parse：

```bash
python -m py_compile reverse_agent\ida_scripts\targeted_static_extract.py
```

必须运行 CLI：

```bash
python -m reverse_agent.local_reverse_targeted_static_reextract --artifact-index project_state\artifact_index.json --ida-summary project_state\local_reverse_ida_summary.json --handoff project_state\local_reverse_validated_candidate_handoff.json --out project_state\local_reverse_targeted_static_reextraction_result.json
```

必须校验输出：

```bash
python -m json.tool project_state\local_reverse_targeted_static_reextraction_result.json > NUL
python -c "import json; d=json.load(open('project_state/local_reverse_targeted_static_reextraction_result.json', encoding='utf-8')); assert d['target_count']==2; assert len(d['targets'])==2; assert {t['sample_id'] for t in d['targets']} == {'18019fca52b389fe','4c69f173f2bd0211'}"
```

必须新增或扩展测试：

```text
tests/test_local_reverse_targeted_static_reextract.py
```

测试至少覆盖：

```text
1. 只选择 sha_256 和 CPP2，不选择 Cpp1。
2. stale/missing latest_artifacts_v2 raw evidence -> blocked。
3. sha_256 没有 bounded input domain 时不得生成 preimage candidate。
4. CPP2 target 包含 sub_401005 blocker 时必须输出 sub_401005_evidence 或 exact missing evidence。
5. output target_count=2。
6. handoff 中 hookapi 不会被覆盖或重新验证。
```

必须运行相关回归：

```bash
python -m pytest -q tests\test_local_reverse_targeted_static_reextract.py tests\test_local_reverse_constraint_recovery.py tests\test_local_reverse_ida_guided_solver.py tests\test_local_reverse_ida_summary.py tests\test_project_state.py
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
1. current handoff artifact 缺失或 hookapi 不再 validated。
2. current raw IDA evidence 缺失或 freshness 不是 current。
3. 需要读取完整 solve_reports/ 才能继续。
4. 需要读取完整 PROJECT_PROGRESS_LOG.txt 才能继续。
5. 需要扩大到两个 unresolved 样本之外才能继续。
6. 需要无界 brute force 才能继续。
7. 需要运行 debugger/dynamic probe 才能继续。
8. 需要运行 Ghidra 才能继续。
9. 需要重新实现反编译/反汇编逻辑才能继续。
10. 需要复制、上传、提交或编码样本二进制才能继续。
11. IDA targeted extraction 无法在本轮最小扩展内完成；此时输出 BLOCKED_NEEDS_TARGETED_IDA_SCRIPT_FIX。
```

本轮完成标准：

```text
project_state/local_reverse_targeted_static_reextraction_result.json 已生成；
只包含 sha_256.exe 和 CPP2.exe 两个 target；
Cpp1 hookapi handoff 保持 current，不被覆盖；
sha_256 给出输入域证据或明确保持 NO_BOUNDED_HASH_PREIMAGE_DOMAIN；
CPP2 给出 sub_401005 的伪代码/反汇编/常量/调用图证据或精确缺口；
artifact_index/current_state/task_packet 已同步；
codex_execution_report.md 和 pytest_result.txt 对应本 decision；
没有扩大样本、没有重跑 Ghidra/debugger、没有提交二进制。
```
