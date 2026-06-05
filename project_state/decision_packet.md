```json decision_meta
{
  "schema_version": 1,
  "decision_id": "decision_20260605_cpp1_inverse_transform_handoff_v1",
  "round_id": "round_20260605_cpp1_inverse_transform_handoff_v1",
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

本轮主线是 **reverse_solving**。

上一轮 `decision_20260605_cpp1_target_bytes_test_record_rework_v1` 审计结论为 `ACCEPTED`。`cpp1_2f6fcb63` 当前已经具备 current 静态证据：

```text
project_state/local_reverse_cpp1_2f6fcb63_static_triage.json
project_state/local_reverse_cpp1_2f6fcb63_target_bytes.json
```

其中 target bytes artifact 已满足：

```text
expected_target_length=16
target_length=16
target_bytes_hex=d596c4f60745577776e5f64847f74817
executed_sample=false
static_only=true
runtime_validated=false
candidate=null
known_candidate=""
```

本轮目标：**基于 current 的 16 字节 target bytes 和静态 forward transform，生成 cpp1_2f6fcb63 的 inverse-transform handoff artifact。**

本轮允许做静态逆变换推导，但不得运行样本，不得 runtime validation，不得把训练状态改为 solved，不得写入 known_candidate。

目标输出：

```text
project_state/local_reverse_cpp1_2f6fcb63_inverse_handoff.json
```

该 artifact 应回答：

```text
1. forward transform 的位映射。
2. inverse transform 的位映射和公式。
3. target bytes 逐字节逆算后的 static_candidate_bytes_hex。
4. static_candidate_bytes 是否全部 printable ASCII。
5. 如果结果含不可打印字节，应标记 BLOCKED / STATIC_CANDIDATE_NONPRINTABLE，而不是 solved。
6. 如果结果 printable，也只能标记 STATIC_CANDIDATE_DERIVED，不得 runtime_validated，不得写 training_status solved。
7. 记录 length discrepancy：strlen == 18，但 compare success uses i == 16；本轮不得擅自补齐后 2 字节。
8. 记录 division anomaly：v6 = v9 / v8；本轮不得把它解释成已验证路径。
```

---

## 2. Current Evidence

当前 `task_packet.json` 仍是旧 samplereverse advisory，不控制本轮。本轮以本 `project_state/decision_packet.md` 为唯一执行权威。

当前 accepted evidence：

```text
artifact_index.latest_artifacts_v2.local_reverse_cpp1_2f6fcb63_static_triage:
  freshness=current
  source_run=round_20260605_cpp1_static_triage_metadata_rework_v1
  path=project_state\\local_reverse_cpp1_2f6fcb63_static_triage.json

artifact_index.latest_artifacts_v2.local_reverse_cpp1_2f6fcb63_target_bytes:
  freshness=current
  source_run=round_20260605_cpp1_target_bytes_test_record_rework_v1
  path=project_state\\local_reverse_cpp1_2f6fcb63_target_bytes.json
```

Static transform evidence from `_main_0`:

```text
scanf("%s", Str)
v4 = strlen(Str)
if (v4 != 18) wrong path is printed
strncpy(Destination, Str, 0x10u)
Destination[i] = Destination[i] & 3 | (16 * (Destination[i] & 0xC)) | ((Destination[i] & 0xF0) >> 2)
for (i = 0; i < v4 && Destination[i] == byte_429A30[i]; ++i)
if (i == 16) success string is printed
```

Forward transform interpretation:

```text
Let x be input byte and y be transformed byte.
y = (x & 0x03) | ((x & 0x0C) << 4) | ((x & 0xF0) >> 2)

Bit mapping:
y0=x0
y1=x1
y2=x4
y3=x5
y4=x6
y5=x7
y6=x2
y7=x3
```

Inverse transform to derive:

```text
x0=y0
x1=y1
x2=y6
x3=y7
x4=y2
x5=y3
x6=y4
x7=y5

x = (y & 0x03) | ((y & 0xC0) >> 4) | ((y & 0x3C) << 2)
```

Important boundaries:

```text
1. This is static evidence only.
2. No sample execution is allowed.
3. No runtime validation is allowed.
4. The inverse bytes may be non-printable; if so, this is a blocker, not a solved password.
5. The length discrepancy 18 vs 16 must remain an evidence note, not a guessed suffix.
6. `v6 = v9 / v8` must remain a static anomaly note, not a proven anti-debug/runtime conclusion.
```

Existing related implementation must be inspected to avoid duplicate patterns:

```text
reverse_agent/local_reverse_affine_inverse_handoff.py
reverse_agent/local_reverse_constraint_recovery.py
reverse_agent/local_reverse_cpp1_target_byte_extract.py
reverse_agent/local_reverse_single_sample_static_triage.py
```

`negative_results.json` still forbids old blind search, only increasing search budget, committing full solve_reports, and repeating old dynamic-probe directions. This round must not enter those directions.

---

## 3. Do Not Do

严禁：

```text
1. 不动态执行本地样本。
2. 不做动态探测或交互式调试。
3. 不运行旧盲搜 solver。
4. 不运行 brute force 或扩大搜索预算。
5. 不执行 runtime validation。
6. 不把 static candidate 写入 known_candidate。
7. 不把 cpp1_2f6fcb63 标记 solved。
8. 不更新 local_reverse_training_status.json 为 solved。
9. 不猜测 strlen==18 中缺失的后 2 字节。
10. 不把不可打印 static bytes 当作可提交密码。
11. 不提交原始样本文件。
12. 不提交 full solve_reports、IDA 数据库副产物或无必要日志。
13. 不读取完整 solve_reports 或 PROJECT_PROGRESS_LOG.txt。
14. 不修改 .codex-skills。
15. 不新建第二套 IDA runner。
16. 不把静态推导说成 runtime validation。
```

允许：

```text
1. 读取默认 project_state 事实源。
2. 读取 current static triage artifact 与 target bytes artifact。
3. 复用或参考 existing inverse handoff / constraint recovery patterns。
4. 新增一个小型 inverse-transform handoff adapter，优先做通用 bit-permutation inverse，而不是单样本硬编码 solver。
5. 生成 project_state/local_reverse_cpp1_2f6fcb63_inverse_handoff.json。
6. 更新 artifact_index.json、codex_execution_report.md、pytest_result.txt。
7. 新增轻量测试，覆盖 forward/inverse roundtrip、target bytes inverse、non-printable blocker、no-candidate-known invariant。
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
project_state/local_reverse_cpp1_2f6fcb63_target_bytes.json
reverse_agent/local_reverse_affine_inverse_handoff.py
reverse_agent/local_reverse_constraint_recovery.py
reverse_agent/local_reverse_cpp1_target_byte_extract.py
reverse_agent/local_reverse_single_sample_static_triage.py
```

允许新增：

```text
reverse_agent/local_reverse_cpp1_inverse_handoff.py
tests/test_local_reverse_cpp1_inverse_handoff.py
project_state/local_reverse_cpp1_2f6fcb63_inverse_handoff.json
```

允许修改：

```text
project_state/artifact_index.json
project_state/codex_execution_report.md
project_state/pytest_result.txt
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
4. 是否确认目标样本只限 cpp1_2f6fcb63。
5. 是否确认本轮只做 static inverse-transform handoff。
6. 是否确认使用的 static triage 和 target bytes artifact 均为 freshness=current。
7. 是否确认 target bytes 为 16 字节。
8. 是否推导并记录 forward bit mapping 与 inverse bit mapping。
9. 是否生成 static_candidate_bytes_hex。
10. 是否检测 static_candidate_bytes 是否 printable ASCII。
11. 如果 non-printable，是否输出 BLOCKED / STATIC_CANDIDATE_NONPRINTABLE。
12. 是否没有猜测 strlen==18 的后 2 字节。
13. 是否没有动态执行样本。
14. 是否没有运行 runtime validation。
15. 是否没有运行 old blind solver / brute force。
16. 是否没有写 known_candidate。
17. 是否没有把 cpp1_2f6fcb63 标记 solved。
18. 是否没有提交原始样本、full solve_reports、IDA 数据库副产物或 .codex-skills 修改。
19. 是否生成 project_state/local_reverse_cpp1_2f6fcb63_inverse_handoff.json。
20. 是否 artifact_index 登记 local_reverse_cpp1_2f6fcb63_inverse_handoff，freshness=current，source_run=round_20260605_cpp1_inverse_transform_handoff_v1。
21. 是否 codex_execution_report.md 与 pytest_result.txt 对齐当前 decision_id/round_id。
22. tests_ran 是否完整列出 required commands，且无省略号。
23. pytest_result.txt 是否记录每条命令、Exit Code 和输出摘要。
```

---

## 6. Implementation Scope

首选实现：新增 `reverse_agent/local_reverse_cpp1_inverse_handoff.py`，但保持逻辑可复用：将 `forward_transform.formula_c` 识别为 bit permutation，并对 target bytes 执行明确的 inverse formula。

建议实现约束：

```text
1. 输入必须来自 project_state/local_reverse_cpp1_2f6fcb63_target_bytes.json。
2. 校验 expected_target_length=16、target_length=16、len(target_bytes)=16。
3. 校验 executed_sample=false、static_only=true、runtime_validated=false。
4. 校验 candidate=null、known_candidate=""。
5. 使用 inverse formula：x = (y & 0x03) | ((y & 0xC0) >> 4) | ((y & 0x3C) << 2)。
6. 输出 static_candidate_bytes_hex 与 static_candidate_bytes。
7. 如果所有字节都在 printable ASCII 范围 0x20..0x7e，可输出 static_candidate_text，但 runtime_validated=false。
8. 如果任意字节不可打印，则 status=BLOCKED，blocked_reason=STATIC_CANDIDATE_NONPRINTABLE，static_candidate_text=null。
9. 始终不写 candidate，不写 known_candidate。
10. 始终不更新 training status。
```

建议 output schema：

```json
{
  "schema_version": 1,
  "sample_id": "cpp1_2f6fcb63",
  "analysis_mode": "static_inverse_transform_handoff",
  "mainline": "reverse_solving",
  "executed_sample": false,
  "static_only": true,
  "runtime_validated": false,
  "source_artifact": "project_state/local_reverse_cpp1_2f6fcb63_target_bytes.json",
  "target_bytes_hex": "d596c4f60745577776e5f64847f74817",
  "expected_target_length": 16,
  "forward_transform": {
    "formula": "y = (x & 0x03) | ((x & 0x0C) << 4) | ((x & 0xF0) >> 2)",
    "bit_mapping": ["y0=x0", "y1=x1", "y2=x4", "y3=x5", "y4=x6", "y5=x7", "y6=x2", "y7=x3"]
  },
  "inverse_transform": {
    "formula": "x = (y & 0x03) | ((y & 0xC0) >> 4) | ((y & 0x3C) << 2)",
    "bit_mapping": ["x0=y0", "x1=y1", "x2=y6", "x3=y7", "x4=y2", "x5=y3", "x6=y4", "x7=y5"]
  },
  "static_candidate_bytes_hex": "",
  "static_candidate_bytes": [],
  "static_candidate_text": null,
  "printable_ascii": false,
  "candidate": null,
  "known_candidate": "",
  "status": "BLOCKED_or_STATIC_CANDIDATE_DERIVED",
  "blocked_reason": "STATIC_CANDIDATE_NONPRINTABLE_or_empty",
  "evidence_notes": [
    "length discrepancy: input must be 18 chars but compare loop checks 16 bytes",
    "division operation detected in path; potential anti-debug trap or dead code"
  ],
  "recommended_next_action": "If candidate is non-printable, require static re-check of transform semantics or allowed dynamic validation; do not mark solved."
}
```

---

## 7. Tests

必须运行并记录：

```bash
python -m py_compile reverse_agent/local_reverse_cpp1_inverse_handoff.py
python -m pytest -q tests/test_local_reverse_cpp1_inverse_handoff.py
python -m pytest -q tests/test_project_state.py
python -m reverse_agent.project_state lint-decision --state-dir project_state
python -m reverse_agent.project_state lint-report --state-dir project_state
python -m reverse_agent.local_reverse_cpp1_inverse_handoff --input project_state/local_reverse_cpp1_2f6fcb63_target_bytes.json --out project_state/local_reverse_cpp1_2f6fcb63_inverse_handoff.json
git diff --check
git status --short
```

Tests must cover：

```text
1. forward_transform_byte and inverse_transform_byte roundtrip for 0..255。
2. inverse formula on target bytes produces deterministic static_candidate_bytes_hex。
3. non-printable static candidate -> BLOCKED / STATIC_CANDIDATE_NONPRINTABLE。
4. printable synthetic target -> STATIC_CANDIDATE_DERIVED, runtime_validated=false。
5. invalid target length -> BLOCKED / INVALID_TARGET_LENGTH。
6. source artifact with candidate or known_candidate already set -> BLOCKED / UNEXPECTED_PRIOR_CANDIDATE。
7. output artifact always has candidate=null and known_candidate=""。
```

Expected results：

```text
1. All required commands Exit Code 0.
2. Inverse handoff artifact exists.
3. Artifact includes static_candidate_bytes_hex but not known_candidate.
4. If static_candidate bytes are non-printable, artifact status is BLOCKED / STATIC_CANDIDATE_NONPRINTABLE.
5. artifact_index registers local_reverse_cpp1_2f6fcb63_inverse_handoff with freshness=current and source_run=round_20260605_cpp1_inverse_transform_handoff_v1.
6. git status --short does not include original samples, full solve_reports, IDA database side products, or .codex-skills.
```

---

## 8. Stop Conditions

立即停止并报告 `BLOCKED`：

```text
1. target bytes artifact 缺失或不是 freshness=current。
2. target bytes artifact 不是 expected_target_length=16 / target_length=16。
3. target bytes artifact 含 candidate 或 known_candidate 非空。
4. 无法实现 forward/inverse roundtrip 测试。
5. 需要动态执行样本才能完成。
6. 需要 runtime validation 才能完成。
7. 需要运行 brute force 或旧盲搜 solver 才能完成。
8. 需要提交原始样本、full solve_reports、IDA 数据库副产物或 .codex-skills 才能完成。
9. 修复过程中出现 known_candidate/solved 写入倾向。
```

完成条件：

```text
1. project_state/local_reverse_cpp1_2f6fcb63_inverse_handoff.json 存在。
2. Artifact 包含 forward/inverse bit mapping 与 static_candidate_bytes_hex。
3. Artifact 不含 candidate/flag/known_candidate。
4. Artifact 明确 runtime_validated=false。
5. 若 static candidate 不可打印，artifact 必须 BLOCKED / STATIC_CANDIDATE_NONPRINTABLE。
6. artifact_index source_run=round_20260605_cpp1_inverse_transform_handoff_v1。
7. codex_execution_report.md 与 pytest_result.txt 对齐当前 decision_id/round_id。
8. required tests 全部记录。
9. 未动态执行样本，未运行 runtime validation，未修改 .codex-skills，未提交大型副产物或原始样本。
```
