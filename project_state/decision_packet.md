```json decision_meta
{
  "schema_version": 1,
  "decision_id": "decision_20260605_cpp1_target_byte_extraction_v1",
  "round_id": "round_20260605_cpp1_target_byte_extraction_v1",
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

本轮主线是 **tool_integration**。

上一轮 `decision_20260605_cpp1_static_triage_metadata_rework_v1` 审计结论为 `ACCEPTED`。`cpp1_2f6fcb63` 的 single-sample static triage 已经生成并登记为 current artifact，且保持：

```text
executed_sample=false
static_only=true
runtime_validated=false
candidate=null
known_candidate=""
```

当前 static triage 的关键发现是：`_main_0` 伪代码显示程序读取 `scanf("%s", Str)`，要求长度相关条件，复制前 16 字节到 `Destination`，对 `Destination[i]` 执行 nibble/bit-level 变换，然后与 `byte_429A30[i]` 比较。现在缺失的是 `byte_429A30` 的 current 静态字节证据。

本轮目标：**只补齐 `cpp1_2f6fcb63` 的 targeted compare-byte static evidence**，也就是从现有静态工具能力中提取：

```text
1. _main_0 targeted pseudocode / compare loop evidence。
2. byte_429A30 的地址、长度和字节值。
3. forward transform 结构摘要。
4. 是否足以进入下一轮 inverse-transform solver handoff。
```

本轮不得直接求解，不得生成 candidate/flag/known_candidate，不得把训练状态改为 solved。

目标输出：

```text
project_state/local_reverse_cpp1_2f6fcb63_target_bytes.json
```

---

## 2. Current Evidence

当前 `task_packet.json` 仍是旧 samplereverse advisory，不控制本轮。本轮以本 `project_state/decision_packet.md` 为唯一执行权威。

当前 accepted artifact：

```text
project_state/local_reverse_cpp1_2f6fcb63_static_triage.json
  sample_id=cpp1_2f6fcb63
  analysis_mode=single_sample_static_triage
  source_tool=IDA
  tool_status=success
  executed_sample=false
  static_only=true
  runtime_validated=false
  candidate=null
  known_candidate=""
  triage.compare_contexts count=1
  triage.decompiler_snippets includes _main_0
```

关键 `_main_0` 伪代码事实：

```text
printf("Please input the password : ");
scanf("%s", Str);
v4 = strlen(Str);
if (v4 != 18) wrong path is printed.
strncpy(Destination, Str, 0x10u);
for each i < v4:
  Destination[i] = Destination[i] & 3 | (16 * (Destination[i] & 0xC)) | ((Destination[i] & 0xF0) >> 2);
for i < v4 && Destination[i] == byte_429A30[i]: continue;
if (i == 16) print success string.
```

Important interpretation boundary:

```text
1. 上述是静态反编译证据，不是运行验证。
2. `v6 = v9 / v8` 出现在路径中，当前不要解释为已验证反调试或可执行路径结论，只记录为 static anomaly / potential trap。
3. `v4 != 18` 与 `i == 16` 存在长度/比较范围差异，本轮只记录证据，不做 candidate。
4. 没有 current `byte_429A30` bytes 之前，不允许 reverse solver 产出答案。
```

已存在工具能力，必须优先复用：

```text
reverse_agent/tool_runners.py
reverse_agent/ida_scripts/collect_evidence.py
reverse_agent/local_reverse_single_sample_static_triage.py
reverse_agent/local_reverse_forced_ida_extract.py
reverse_agent/local_reverse_targeted_static_reextract.py
```

可新增小型 targeted adapter，但不得新建第二套通用 IDA runner，也不得重复实现 IDA 的反汇编、反编译、XREF、字符串提取能力。

`negative_results.json` 仍禁止旧盲搜、单纯扩大搜索预算、提交 full solve_reports、重复旧动态探测方向。本轮必须避开这些方向。

---

## 3. Do Not Do

严禁：

```text
1. 不动态执行本地样本。
2. 不做动态探测或交互式调试。
3. 不运行旧盲搜 solver。
4. 不运行 brute force 或扩大搜索预算。
5. 不生成 candidate、flag、known_candidate。
6. 不把 cpp1_2f6fcb63 标记 solved。
7. 不提交原始样本文件。
8. 不提交 full solve_reports、IDA 数据库副产物或无必要日志。
9. 不读取完整 solve_reports 或 PROJECT_PROGRESS_LOG.txt。
10. 不修改 .codex-skills。
11. 不新建第二套 IDA runner。
12. 不把静态字节提取结果说成 runtime validation。
13. 不把 `byte_429A30` 缺失时的推测字节写入 artifact。
```

允许：

```text
1. 读取默认 project_state 事实源。
2. 读取 current cpp1 static triage artifact。
3. 读取并复用现有 IDA/static tool interfaces。
4. 新增一个小型 targeted compare-byte extraction adapter 或 IDAPython script，前提是它只服务本轮提取目标字节和比较上下文，不替代现有通用 runner。
5. 在静态工具可用时提取 `_main_0`、`byte_429A30` 数据和相关 XREF/bytes。
6. 如果工具或样本路径不可用，输出明确 BLOCKED artifact。
7. 更新 artifact_index.json、codex_execution_report.md、pytest_result.txt。
8. 添加轻量测试，覆盖 schema、byte extraction parser、blocked artifact、no-candidate invariant。
```

---

## 4. Files To Inspect

默认必须读取：

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
project_state/local_reverse_cpp1_2f6fcb63_static_triage.json
project_state/local_reverse_evaluation_queue.json
project_state/local_reverse_inventory.json
reverse_agent/tool_runners.py
reverse_agent/ida_scripts/collect_evidence.py
reverse_agent/local_reverse_single_sample_static_triage.py
reverse_agent/local_reverse_forced_ida_extract.py
reverse_agent/local_reverse_targeted_static_reextract.py
```

必要时检查：

```text
tests/test_local_reverse_single_sample_static_triage.py
tests/test_project_state.py
```

不要默认读取：

```text
solve_reports/ 全量
PROJECT_PROGRESS_LOG.txt 全量
project_state/rounds/ 全量历史
```

---

## 5. Required Audit

Codex 报告必须回答：

```text
1. 是否确认当前 decision_packet 是本轮唯一执行权威。
2. 是否确认 task_packet.task 只是 advisory。
3. 是否确认本轮主线为 tool_integration。
4. 是否确认目标样本只限 cpp1_2f6fcb63。
5. 是否确认本轮只做 targeted compare-byte static extraction。
6. 是否确认复用现有 IDA/static tooling，未新建重复通用 runner。
7. 是否确认没有动态执行本地样本。
8. 是否确认没有运行 solver / brute force。
9. 是否确认没有生成 candidate / flag / known_candidate。
10. 是否确认没有把样本标记 solved。
11. 是否生成 project_state/local_reverse_cpp1_2f6fcb63_target_bytes.json。
12. 是否提取并记录 byte_429A30 的地址、长度和字节值；若无法提取，是否输出 BLOCKED reason。
13. 是否记录 `_main_0` 中 forward transform 的静态公式摘要。
14. 是否记录 `v4 != 18` 与 `i == 16` 的长度/比较范围差异为 evidence note，而不是求解结论。
15. 是否 artifact_index 登记 local_reverse_cpp1_2f6fcb63_target_bytes，freshness=current，source_run=round_20260605_cpp1_target_byte_extraction_v1。
16. 是否没有提交 full solve_reports、IDA 数据库副产物、原始样本或 .codex-skills 修改。
17. 是否更新 codex_execution_report.md 与 pytest_result.txt。
18. based_on_decision_id 是否匹配当前 decision_id。
19. tests_ran 是否完整列出 required commands，且无省略号。
20. pytest_result.txt 是否记录每条命令、Exit Code 和输出摘要。
```

---

## 6. Implementation Scope

首选实现：新增一个薄 adapter，复用现有 static evidence 路径并仅补齐目标字节：

```text
reverse_agent/local_reverse_cpp1_target_byte_extract.py
```

允许新增：

```text
reverse_agent/local_reverse_cpp1_target_byte_extract.py
tests/test_local_reverse_cpp1_target_byte_extract.py
project_state/local_reverse_cpp1_2f6fcb63_target_bytes.json
```

允许修改：

```text
project_state/artifact_index.json
project_state/codex_execution_report.md
project_state/pytest_result.txt
```

如果需要 IDAPython 支持，可以新增一个小型脚本：

```text
reverse_agent/ida_scripts/extract_named_data.py
```

该脚本只允许做 named data / bytes / xref / selected function pseudocode extraction，不得变成第二套 collect_evidence。

建议 artifact schema：

```json
{
  "schema_version": 1,
  "sample_id": "cpp1_2f6fcb63",
  "analysis_mode": "target_compare_byte_extraction",
  "mainline": "tool_integration",
  "executed_sample": false,
  "static_only": true,
  "runtime_validated": false,
  "source_tool": "IDA",
  "tool_status": "success_or_blocked",
  "blocked_reason": "",
  "target_symbol": "byte_429A30",
  "target_address": "0x429A30",
  "target_length": 16,
  "target_bytes_hex": "",
  "target_bytes": [],
  "main_function": "_main_0",
  "forward_transform": {
    "input_buffer": "Str",
    "work_buffer": "Destination",
    "copy_length": 16,
    "formula_c": "(x & 3) | (16 * (x & 0x0C)) | ((x & 0xF0) >> 2)",
    "compare_expression": "Destination[i] == byte_429A30[i]"
  },
  "evidence_notes": [],
  "candidate": null,
  "known_candidate": "",
  "recommended_next_action": "If target bytes are current, create inverse-transform handoff in next round."
}
```

Implementation constraints：

```text
1. Do not infer target bytes from memory or from guesses.
2. If byte_429A30 cannot be read from static evidence, output BLOCKED / TARGET_BYTES_NOT_FOUND.
3. If IDA/static tool is unavailable, output BLOCKED / STATIC_TOOL_UNAVAILABLE.
4. If target bytes are extracted, do not invert them in this round.
5. Do not update training_status as solved/blocked.
6. Keep raw/static output compact; do not commit bulky side artifacts.
```

---

## 7. Tests

必须运行并记录：

```bash
python -m py_compile reverse_agent/tool_runners.py
python -m py_compile reverse_agent/local_reverse_cpp1_target_byte_extract.py
python -m pytest -q tests/test_local_reverse_cpp1_target_byte_extract.py
python -m pytest -q tests/test_project_state.py
python -m reverse_agent.project_state lint-decision --state-dir project_state
python -m reverse_agent.project_state lint-report --state-dir project_state
python -m reverse_agent.local_reverse_cpp1_target_byte_extract --sample-id cpp1_2f6fcb63 --triage project_state/local_reverse_cpp1_2f6fcb63_static_triage.json --inventory project_state/local_reverse_inventory.json --out project_state/local_reverse_cpp1_2f6fcb63_target_bytes.json
git diff --check
git status --short
```

如果 Codex chooses not to add a new adapter, it must run equivalent py_compile/pytest commands for the reused module and record the full reproducible extraction command. However, it must still generate `project_state/local_reverse_cpp1_2f6fcb63_target_bytes.json`.

Expected results：

```text
1. All required commands Exit Code 0, unless static tool/sample path is unavailable; in that case the CLI itself should Exit Code 0 and produce a BLOCKED artifact.
2. Artifact includes executed_sample=false, static_only=true, runtime_validated=false.
3. Artifact contains target bytes or a precise BLOCKED reason.
4. Artifact does not contain candidate/flag/known_candidate.
5. artifact_index registers local_reverse_cpp1_2f6fcb63_target_bytes with freshness=current.
6. git status --short does not include original samples, full solve_reports, IDA database side products, or .codex-skills.
```

---

## 8. Stop Conditions

立即停止并报告 `BLOCKED`：

```text
1. 当前 cpp1 static triage artifact 缺失或不是 freshness=current。
2. 无法定位 `byte_429A30`，且无法生成明确 BLOCKED artifact。
3. 需要动态执行样本才能完成。
4. 需要运行 solver / brute force 才能完成。
5. 需要提交原始样本、full solve_reports、IDA 数据库副产物或 .codex-skills 才能完成。
6. 重新提取过程中出现 candidate/known_candidate/flag 生成倾向。
```

完成条件：

```text
1. project_state/local_reverse_cpp1_2f6fcb63_target_bytes.json 存在。
2. Artifact 是 success target-byte evidence 或明确 BLOCKED。
3. Artifact includes executed_sample=false, static_only=true, runtime_validated=false。
4. Artifact 不含 candidate/flag/known_candidate。
5. artifact_index 登记新 artifact，freshness=current，source_run=round_20260605_cpp1_target_byte_extraction_v1。
6. codex_execution_report.md 与 pytest_result.txt 对齐当前 decision_id/round_id。
7. required tests 已记录。
8. 未动态执行样本，未运行 solver，未修改 .codex-skills，未提交大型副产物或原始样本。
```
