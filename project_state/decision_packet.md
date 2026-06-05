```json decision_meta
{
  "schema_version": 1,
  "decision_id": "decision_20260605_cpp1_transform_semantics_recheck_v1",
  "round_id": "round_20260605_cpp1_transform_semantics_recheck_v1",
  "based_on_state_build_id": "state_20260602_053948_4e3984041cd7",
  "based_on_state_digest": "4e3984041cd78e5a412e28a53fa3441957ea87f43f62a9688c3e80ca4413678c3e80ca4413678c",
  "status": "APPROVED",
  "mainline": "reverse_solving",
  "skill_profiles": [
    "reverse-agent-iteration@v2"
  ]
}
```

# DECISION_PACKET

## 1. Goal

本轮主线是 **reverse_solving**。

目标：对 `cpp1_2f6fcb63` 的 static transform / compare semantics 做一次有界复核，解释为什么上一轮 inverse handoff 得到不可打印候选，并产出可审计 artifact。

上一轮清理结论已接受，当前不再围绕 report/pytest 记录返工。

当前证据链：

```text
1. static triage artifact freshness=current：project_state/local_reverse_cpp1_2f6fcb63_static_triage.json
2. target bytes artifact freshness=current：project_state/local_reverse_cpp1_2f6fcb63_target_bytes.json
3. inverse handoff artifact freshness=current：project_state/local_reverse_cpp1_2f6fcb63_inverse_handoff.json
4. inverse handoff 当前状态：BLOCKED / STATIC_CANDIDATE_NONPRINTABLE
```

本轮只做静态语义复核，不动态执行样本，不运行 runtime validation，不把样本标记 solved。

预期产物：

```text
reverse_agent/local_reverse_cpp1_transform_recheck.py
tests/test_local_reverse_cpp1_transform_recheck.py
project_state/local_reverse_cpp1_2f6fcb63_transform_recheck.json
```

并将新 artifact 登记进 `project_state/artifact_index.json`，`freshness=current`，`source_run=round_20260605_cpp1_transform_semantics_recheck_v1`。

---

## 2. Current Evidence

当前 `task_packet.json` 仍是旧 samplereverse advisory，不控制本轮。本轮以本 `project_state/decision_packet.md` 为唯一执行权威。

`artifact_index.json` 显示：

```text
local_reverse_cpp1_2f6fcb63_static_triage: freshness=current
local_reverse_cpp1_2f6fcb63_target_bytes: freshness=current
local_reverse_cpp1_2f6fcb63_inverse_handoff: freshness=current
```

`target_bytes` artifact 中的关键事实：

```text
sample_id=cpp1_2f6fcb63
source_tool=IDA
target_symbol=byte_429A30
target_address=0x00429A30
target_length=16
target_bytes_hex=d596c4f60745577776e5f64847f74817
main_function=_main_0
executed_sample=false
static_only=true
runtime_validated=false
candidate=null
known_candidate=""
```

`main_pseudocode` 中的关键逻辑：

```c
v4 = strlen(Str);
if ( v4 != 18 ) {
  printf("Sorry,you are wrong!\n");
  system("pause");
}
strncpy(Destination, Str, 0x10u);
v6 = v9 / v8;
for ( i = 0; i < v4; ++i )
  Destination[i] = Destination[i] & 3 | (16 * (Destination[i] & 0xC)) | ((Destination[i] & 0xF0) >> 2);
for ( i = 0; i < v4 && Destination[i] == byte_429A30[i]; ++i )
  ;
if ( i == 16 )
  printf("Congratulations! You are right!\n");
```

`inverse_handoff` artifact 中的关键事实：

```text
forward formula: y = (x & 0x03) | ((x & 0x0C) << 4) | ((x & 0xF0) >> 2)
inverse formula: x = (y & 0x03) | ((y & 0xC0) >> 4) | ((y & 0x3C) << 2)
static_candidate_bytes_hex=5d5a1cde131557d7d69dde2417df2453
printable_ascii=false
candidate=null
known_candidate=""
status=BLOCKED
blocked_reason=STATIC_CANDIDATE_NONPRINTABLE
notes=[length discrepancy: input must be 18 chars but compare loop checks 16 bytes, division operation detected in path]
recommended_next_action=static re-check of transform semantics or allowed dynamic validation; do not mark solved
```

当前 negative_results 仍禁止：

```text
1. old sample_solver blind search
2. only increase guided_pool beam or budget
3. compare_semantics_agree=false candidates as primary frontier
4. commit full solve_reports directory
5. repeat dynamic-probe directions without new evidence
```

已有能力检查：

```text
1. 已有 IDA 相关能力：local_reverse_single_sample_static_triage.py、local_reverse_cpp1_target_byte_extract.py、local_reverse_ida_summary.py、local_reverse_forced_ida_extract.py。
2. 已有 cpp1 target byte extraction 脚本和测试。
3. 已有 cpp1 inverse handoff 脚本和测试。
4. 本轮不新建重复 IDA runner，不重新运行 IDA。
5. 本轮只使用 current JSON artifacts 做 transform/compare consistency audit。
6. 若静态 artifact 不足以判断控制流或 SEH/division trap，输出 BLOCKED，并建议下一轮显式批准 bounded IDA instruction-level re-extraction。
```

---

## 3. Do Not Do

严禁：

```text
1. 不动态执行样本。
2. 不做 runtime validation。
3. 不运行 old blind solver / brute force。
4. 不扩大 beam、topN、budget、timeout。
5. 不把不可打印 static_candidate 当作 candidate。
6. 不写 known_candidate。
7. 不把 cpp1_2f6fcb63 标记 solved。
8. 不修改 local_reverse_training_status.json 为 solved。
9. 不提交原始样本、IDA .i64、IDA log、full solve_reports 或本地临时目录。
10. 不修改 .codex-skills。
11. 不新建重复 IDA runner。
12. 不重新运行 IDA，除非本 decision 明确允许；本轮不允许。
13. 不改动无关样本、GUI、harness、pipeline 或 samplereverse profile。
14. 不把 task_packet.task 当执行权威。
15. 不用一次 cpp1 结论改长期 skill。
```

允许：

```text
1. 新增一个小的 deterministic static recheck 脚本。
2. 新增对应单元测试。
3. 读取 current static_triage / target_bytes / inverse_handoff artifacts。
4. 枚举 0..255 的 transform mapping，验证 forward/inverse 是否双射。
5. 枚举 printable ASCII 输入域，判断每个 target byte 是否存在 printable preimage。
6. 分析 v4==18、strncpy copy_length=16、compare loop 和 success condition i==16 的关系。
7. 生成 transform_recheck JSON artifact。
8. 更新 artifact_index、codex_execution_report.md、pytest_result.txt。
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
project_state/local_reverse_cpp1_2f6fcb63_static_triage.json
project_state/local_reverse_cpp1_2f6fcb63_target_bytes.json
project_state/local_reverse_cpp1_2f6fcb63_inverse_handoff.json
reverse_agent/local_reverse_cpp1_inverse_handoff.py
reverse_agent/local_reverse_cpp1_target_byte_extract.py
tests/test_local_reverse_cpp1_inverse_handoff.py
tests/test_local_reverse_cpp1_target_byte_extract.py
.codex-skills/registry.json
```

可检查但不得默认重型读取：

```text
reverse_agent/local_reverse_single_sample_static_triage.py
reverse_agent/local_reverse_ida_summary.py
reverse_agent/local_reverse_forced_ida_extract.py
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
3. 是否确认本轮主线为 reverse_solving。
4. 是否确认本轮只处理 cpp1_2f6fcb63。
5. 是否确认 static_triage / target_bytes / inverse_handoff 均为 freshness=current。
6. 是否确认没有动态执行样本。
7. 是否确认没有 runtime validation。
8. 是否确认没有重新运行 IDA。
9. 是否确认没有恢复或提交 IDA .i64 / IDA log。
10. 是否确认没有运行 old blind solver / brute force。
11. 是否验证 forward transform 在 0..255 上是否为 bijection。
12. 是否验证 inverse formula 与 forward formula roundtrip 全覆盖。
13. 是否枚举 printable ASCII 域并给出每个 target byte 的 printable preimage 状态。
14. 是否解释 static_candidate_bytes_hex 为什么不可打印。
15. 是否分析 length check v4==18、strncpy copy_length=16、compare loop i<v4、success condition i==16 之间的关系。
16. 是否明确说明当前证据是否足以产出 candidate。
17. 是否保持 candidate=null、known_candidate=""。
18. 是否保持样本 unsolved / BLOCKED。
19. 是否生成 transform_recheck artifact 并登记 artifact_index。
20. 是否 tests_ran 完整列出 required commands。
21. 是否 pytest_result.txt 记录每条命令、Exit Code 和输出摘要。
```

---

## 6. Implementation Scope

允许新增：

```text
reverse_agent/local_reverse_cpp1_transform_recheck.py
tests/test_local_reverse_cpp1_transform_recheck.py
project_state/local_reverse_cpp1_2f6fcb63_transform_recheck.json
```

允许修改：

```text
project_state/artifact_index.json
project_state/codex_execution_report.md
project_state/pytest_result.txt
```

不得修改，除非测试暴露确定错误且报告中说明：

```text
reverse_agent/local_reverse_cpp1_inverse_handoff.py
reverse_agent/local_reverse_cpp1_target_byte_extract.py
tests/test_local_reverse_cpp1_inverse_handoff.py
tests/test_local_reverse_cpp1_target_byte_extract.py
```

`local_reverse_cpp1_transform_recheck.py` 至少应提供：

```text
1. load_artifacts(target_bytes_path, inverse_handoff_path, static_triage_path optional)
2. forward_transform(x)
3. inverse_transform(y)
4. analyze_mapping()  # 0..255 bijection / roundtrip
5. analyze_printable_preimages(target_bytes, printable_range=0x20..0x7e)
6. analyze_length_compare_semantics(main_pseudocode or artifact fields)
7. build_recheck_report(...)
8. CLI: python -m reverse_agent.local_reverse_cpp1_transform_recheck --target-bytes ... --inverse-handoff ... --triage ... --out ...
```

`project_state/local_reverse_cpp1_2f6fcb63_transform_recheck.json` 至少包含：

```text
schema_version
sample_id
analysis_mode=static_transform_semantics_recheck
mainline=reverse_solving
executed_sample=false
static_only=true
runtime_validated=false
source_artifacts
forward_formula
inverse_formula
mapping_bijective
roundtrip_all_256
static_candidate_bytes_hex
static_candidate_printable_ascii
per_byte_printable_preimage
length_compare_semantics
candidate=null
known_candidate=""
status=BLOCKED 或 NEEDS_STATIC_CONTROL_FLOW_RECHECK
blocked_reason
recommended_next_action
```

如果当前 transform 在 printable ASCII 域下无法生成 target bytes，artifact 应明确写：

```text
current_static_transform_has_no_printable_solution=true
candidate=null
known_candidate=""
status=BLOCKED
blocked_reason=NO_PRINTABLE_PREIMAGE_UNDER_CURRENT_STATIC_TRANSFORM
recommended_next_action=bounded IDA instruction-level / control-flow / SEH recheck, not brute force
```

---

## 7. Tests

必须运行并记录：

```bash
python -m py_compile reverse_agent/local_reverse_cpp1_transform_recheck.py
python -m pytest -q tests/test_local_reverse_cpp1_transform_recheck.py
python -m pytest -q tests/test_local_reverse_cpp1_inverse_handoff.py
python -m pytest -q tests/test_project_state.py
python -m reverse_agent.local_reverse_cpp1_transform_recheck --target-bytes project_state/local_reverse_cpp1_2f6fcb63_target_bytes.json --inverse-handoff project_state/local_reverse_cpp1_2f6fcb63_inverse_handoff.json --triage project_state/local_reverse_cpp1_2f6fcb63_static_triage.json --out project_state/local_reverse_cpp1_2f6fcb63_transform_recheck.json
python -m reverse_agent.project_state lint-decision --state-dir project_state
python -m reverse_agent.project_state lint-report --state-dir project_state
git diff --check
git status --short
git diff --name-status
```

可选但允许：

```bash
python -m pytest -q tests/test_local_reverse_cpp1_target_byte_extract.py
```

Expected results：

```text
1. All required commands Exit Code 0。
2. transform_recheck CLI 生成 JSON artifact。
3. artifact_index 登记新 artifact，freshness=current。
4. candidate=null，known_candidate=""。
5. runtime_validated=false。
6. 不产生 IDA .i64、IDA log、solve_reports、原始样本提交。
7. git diff --name-status 只包含本轮允许范围内的新增/修改文件。
```

---

## 8. Stop Conditions

立即停止并报告 `BLOCKED`：

```text
1. target_bytes artifact 缺失或 freshness 非 current。
2. inverse_handoff artifact 缺失或 freshness 非 current。
3. artifact_index 无法登记 transform_recheck artifact。
4. transform_recheck 需要动态执行样本才能继续。
5. transform_recheck 需要 runtime validation 才能继续。
6. transform_recheck 需要重新运行 IDA 才能继续。
7. 发现当前 static artifacts 内部字段矛盾，无法安全判定 transform semantics。
8. 出现 candidate 非 null 或 known_candidate 非空的写入倾向。
9. git status 出现 IDA .i64、IDA log、原始样本、full solve_reports 或无关文件。
```

完成条件：

```text
1. transform_recheck artifact 生成并登记 current。
2. 明确解释 current static transform 下候选不可打印的原因。
3. 明确说明是否存在 printable ASCII preimage。
4. 明确说明 length/compare semantics 对 first 16 bytes 和 18-byte input 的影响。
5. 不标记 solved，不写 candidate，不写 known_candidate。
6. 给出下一轮建议：若仍 blocked，下一轮应是 bounded IDA instruction-level/control-flow/SEH recheck，而不是 brute force 或扩大预算。
```