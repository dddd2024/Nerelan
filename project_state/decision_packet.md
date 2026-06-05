```json decision_meta
{
  "schema_version": 1,
  "decision_id": "decision_20260605_affine_inverse_handoff_static_only_v1",
  "round_id": "round_20260605_affine_inverse_handoff_static_only_v1",
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

上一轮 `decision_20260605_affine_main0_targeted_ida_decompile_v1` 审计结论为 `ACCEPTED_WITH_LIMITATIONS`。功能目标已经达成：IDA/Hex-Rays targeted export 成功补齐 `affine_8cfebe03` 的 `_main_0` 伪代码，并确认该程序是 **仿射密码编码器**，不是 password checker。限制项是：

```text
1. codex_report_summary.tests_ran 漏列 git diff --check 与 git status --short，虽然 pytest_result.txt 已记录。
2. git status --short 显示 solve_reports 下有 targeted IDA export JSON/log 未跟踪；下一轮提交前必须严格控制范围，不能提交 full solve_reports 或无必要 log/i64。
```

本轮目标：**基于 `project_state/local_reverse_affine_main0_targeted_ida_decompile.json` 中的 current IDA 静态证据，生成可复用的 affine inverse handoff / constraint artifact。**

必须明确：当前证据中没有 final compare、没有 success/failure branch、没有目标密文；因此本轮不得生成 flag，不得声称已解出 candidate。应输出一个结构化结果，说明：

```text
transform: c = (5 * p + 5) mod 26
alphabet: lowercase a-z
inverse_a: 21
inverse_formula: p = 21 * (c - 5) mod 26
status: BLOCKED 或 PARTIAL，原因是 MISSING_EXPECTED_CIPHERTEXT
recommended_next_action: provide expected ciphertext from challenge statement / captured output / allowed evidence source
```

本轮只允许静态 JSON 处理和单元测试；不得运行 `affine.exe`，不得 runtime probe，不得 debugger/emulator，不得盲跑 solver，不得发明目标密文。

---

## 2. Current Evidence

当前 `task_packet.json` 仍含旧 samplereverse/local_reverse advisory 信息，不控制本轮。本轮以本 `project_state/decision_packet.md` 为唯一执行权威。

当前 affine targeted artifact：

```text
project_state/local_reverse_affine_main0_targeted_ida_decompile.json
  sample_id: affine_8cfebe03
  relative_path: 逆向课程2024春补考03/affine.exe
  sha256: 8cfebe030f2d9fced106881e5aa6b2d81d162d31230dd3418b8fc3b15a5ef659
  executed_sample: false
  ida_static_only: true
  ida_status: success
  hexrays_available: true
  pseudocode_available: true
  confidence: high
  recommended_next_action: affine_constraint_recovery
```

关键静态事实：

```text
input_api: scanf
format_string: %s
buffer: Str[97]
input validation: every char must be 'a'..'z', otherwise return -1
transform_formula: Str[j] = (v10 + v11 * (Str[j] - 97)) % 26 + 97
affine_parameters: a=5, b=5, modulus=26
cipher_type: affine_cipher
output_api: printf("%s", Str)
candidate_compare_sites: []
success_failure_branch_candidates: []
notes: pure transform program / encoder, not password checker
```

`artifact_index.latest_artifacts_v2` 中以下 affine artifact 均应保持 `freshness=current`：

```text
local_reverse_affine_ida_summary
local_reverse_ida_evidence_affine_8cfebe03
local_reverse_affine_main_input_flow_reextract
local_reverse_affine_main0_targeted_ida_decompile
```

已有相关能力：

```text
reverse_agent/local_reverse_constraint_recovery.py exists.
It currently contains classification-specific constraint recovery for previous local_reverse profiles.
Before adding any new code, Codex must inspect it and decide whether affine support belongs there or should be a small generic adapter.

reverse_agent/local_reverse_targeted_static_reextract.py exists.
Do not duplicate its static extraction role.

reverse_agent/ida_scripts/collect_evidence.py already supports forced _main_0 decompile from the previous round.
Do not rerun IDA unless this round becomes BLOCKED due to missing targeted artifact; normal path should consume the existing project_state JSON.
```

`negative_results.json` 仍禁止 old sample_solver blind search、only increase beam/budget、commit full solve_reports、重复旧 runtime/probe 失败方向。本轮不得进入这些方向。

---

## 3. Do Not Do

严禁：

```text
1. 不运行 affine.exe。
2. 不运行 runtime probe、debugger、Frida、OllyDbg、x64dbg、emulator。
3. 不生成 flag、validated_candidate 或最终答案。
4. 不发明 expected ciphertext。
5. 不把 printf 输出路径误判成 password checker 的 success path。
6. 不把 candidate_compare_sites=[] 的程序硬塞进 compare solver。
7. 不回到 old sample_solver blind search。
8. 不扩大 beam/budget/bruteforce。
9. 不新建 affine_8cfebe03 单样本硬编码 solver。
10. 不把 affine 单题结论写入 .codex-skills。
11. 不修改 .codex-skills。
12. 不上传或复制 E:\reverse 原始样本。
13. 不提交 full solve_reports 目录。
14. 不提交 IDA .i64 数据库或无必要 log。
15. 不把 IDA 静态证据说成 runtime validation。
16. 不读取完整 solve_reports 或 PROJECT_PROGRESS_LOG.txt。
17. 不改变上一轮已接受 artifact 的语义事实。
18. 不删除 current affine artifact。
```

允许：

```text
1. 读取默认 project_state 事实源。
2. 读取 project_state/local_reverse_affine_main0_targeted_ida_decompile.json。
3. 检查 existing local_reverse constraint/static modules，避免重复造轮子。
4. 新增或最小扩展一个通用 affine inverse handoff 能力，输入为结构化 affine static artifact。
5. 输出 project_state/local_reverse_affine_inverse_handoff.json。
6. 更新 artifact_index.json，将新 handoff 登记为 freshness=current。
7. 更新 codex_execution_report.md 和 pytest_result.txt。
8. 添加或修改轻量单元测试，覆盖 affine 参数解析、模逆元、无目标密文阻断。
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
project_state/local_reverse_affine_main0_targeted_ida_decompile.json
reverse_agent/local_reverse_constraint_recovery.py
reverse_agent/local_reverse_targeted_static_reextract.py
reverse_agent/local_reverse_training_status.py
project_state/local_reverse_training_status.json
```

必要时检查：

```text
tests/test_local_reverse_constraint_recovery.py
tests/test_local_reverse_inventory.py
tests/test_local_reverse_training_status.py
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
3. 是否确认本轮主线为 reverse_solving，且没有扩大到工程重构或训练集批量跑。
4. 是否确认目标样本是 affine_8cfebe03。
5. 是否确认 targeted IDA artifact 为 freshness=current。
6. 是否确认 targeted artifact 中 executed_sample=false、ida_static_only=true。
7. 是否确认程序为 affine encoder / pure transform，而不是 password checker。
8. 是否确认 candidate_compare_sites=[]、success_failure_branch_candidates=[]。
9. 是否检查并复用/评估已有 local_reverse_constraint_recovery.py，避免重复造轮子。
10. 如果新增 affine handoff 模块，是否为通用 affine profile adapter，而非 affine_8cfebe03 硬编码。
11. 是否计算并记录 gcd(a, modulus)=1 与 inverse_a=21。
12. 是否在没有 expected ciphertext 时输出 BLOCKED/PARTIAL，而不是生成 candidate。
13. 是否没有运行 affine.exe。
14. 是否没有运行 runtime probe、debugger、emulator。
15. 是否没有运行 old sample_solver blind search。
16. 是否没有提交 full solve_reports、IDA .i64 或无必要 log。
17. 是否没有修改 .codex-skills。
18. 是否生成 project_state/local_reverse_affine_inverse_handoff.json。
19. 是否更新 artifact_index.latest_artifacts 与 latest_artifacts_v2，freshness=current，source_run=round_20260605_affine_inverse_handoff_static_only_v1。
20. 是否更新 codex_execution_report.md 与 pytest_result.txt。
21. codex_report_summary.based_on_decision_id 是否等于 decision_20260605_affine_inverse_handoff_static_only_v1。
22. codex_report_summary.tests_ran 是否完整列出 py_compile、pytest、lint-decision、lint-report、git diff --check、git status --short。
23. pytest_result.txt 是否记录每条命令、Exit code 和输出摘要。
```

---

## 6. Implementation Scope

优先方案：在现有 local_reverse 约束恢复体系中增加 **通用 affine encoder handoff**，不要写单题 solver。

允许修改：

```text
reverse_agent/local_reverse_constraint_recovery.py
project_state/artifact_index.json
project_state/codex_execution_report.md
project_state/pytest_result.txt
```

如现有 `local_reverse_constraint_recovery.py` 的输入结构不适合消费 `local_reverse_affine_main0_targeted_ida_decompile.json`，允许新增一个小型通用 adapter：

```text
reverse_agent/local_reverse_affine_inverse_handoff.py
```

允许新增输出：

```text
project_state/local_reverse_affine_inverse_handoff.json
```

允许新增或修改测试：

```text
tests/test_local_reverse_affine_inverse_handoff.py
tests/test_local_reverse_constraint_recovery.py
```

实现约束：

```text
1. 输入必须来自 project_state/local_reverse_affine_main0_targeted_ida_decompile.json 或等价结构化 JSON。
2. 不从原始 binary 重新提取，不运行 IDA，除非输入 artifact 缺失或不可解析，此时应 BLOCKED。
3. 从 artifact 中读取 affine_parameters: a, b, modulus。
4. 校验 alphabet/input domain 为 lowercase a-z；如果不满足，输出 BLOCKED/UNSUPPORTED_DOMAIN。
5. 计算 gcd(a, modulus)。若 gcd != 1，输出 BLOCKED/NON_INVERTIBLE_AFFINE_MULTIPLIER。
6. 对 a=5, modulus=26，计算 inverse_a=21。
7. 输出 inverse_formula 与 per-character mapping 规则。
8. 如果 artifact 未提供 expected_ciphertext，则 status=BLOCKED 或 PARTIAL，blocked_reason=MISSING_EXPECTED_CIPHERTEXT。
9. 不生成 candidate，除非输入中明确存在 expected_ciphertext 且来源字段可审计；本轮当前 artifact 没有该字段，因此正常结果应不含 validated_candidate。
10. 输出必须明确 static_only=true、runtime_validated=false、executed_sample=false。
11. 保持旧字段兼容，不破坏已有 local_reverse_constraint_recovery tests。
12. 不把本轮逻辑写入 .codex-skills。
```

建议输出结构：

```json
{
  "schema_version": 1,
  "sample_id": "affine_8cfebe03",
  "source_artifact": "project_state/local_reverse_affine_main0_targeted_ida_decompile.json",
  "analysis_mode": "affine_inverse_handoff_static_only",
  "executed_sample": false,
  "static_only": true,
  "runtime_validated": false,
  "cipher_type": "affine_cipher",
  "domain": {
    "alphabet": "lowercase_ascii",
    "min_char": "a",
    "max_char": "z",
    "modulus": 26
  },
  "forward_transform": {
    "a": 5,
    "b": 5,
    "formula": "c = (a * p + b) mod 26"
  },
  "inverse_transform": {
    "gcd_a_modulus": 1,
    "inverse_a": 21,
    "formula": "p = inverse_a * (c - b) mod 26"
  },
  "expected_ciphertext": null,
  "candidate": null,
  "status": "BLOCKED",
  "blocked_reason": "MISSING_EXPECTED_CIPHERTEXT",
  "recommended_next_action": "Provide expected ciphertext from challenge statement or another allowed evidence source before candidate generation."
}
```

---

## 7. Tests

必须运行并记录：

```bash
python -m py_compile reverse_agent/local_reverse_constraint_recovery.py
python -m pytest -q tests/test_project_state.py
python -m reverse_agent.project_state lint-decision --state-dir project_state
python -m reverse_agent.project_state lint-report --state-dir project_state
git diff --check
git status --short
```

如果新增 `reverse_agent/local_reverse_affine_inverse_handoff.py`，必须额外运行：

```bash
python -m py_compile reverse_agent/local_reverse_affine_inverse_handoff.py
python -m pytest -q tests/test_local_reverse_affine_inverse_handoff.py
```

如果修改 `tests/test_local_reverse_constraint_recovery.py`，必须额外运行：

```bash
python -m pytest -q tests/test_local_reverse_constraint_recovery.py
```

如果运行 handoff CLI，必须记录命令、Exit code、输出路径和摘要，例如：

```bash
python -m reverse_agent.local_reverse_affine_inverse_handoff \
  --input project_state/local_reverse_affine_main0_targeted_ida_decompile.json \
  --out project_state/local_reverse_affine_inverse_handoff.json
```

测试期望：

```text
1. 无 expected_ciphertext 时，artifact status 为 BLOCKED 或 PARTIAL，blocked_reason=MISSING_EXPECTED_CIPHERTEXT。
2. inverse_a=21。
3. executed_sample=false、static_only=true、runtime_validated=false。
4. 不产生 validated_candidate。
5. 旧 project_state tests 不回退。
6. git status --short 不出现 full solve_reports 批量新增；不得出现 .i64。
```

---

## 8. Stop Conditions

立即停止并报告 `BLOCKED`：

```text
1. project_state/local_reverse_affine_main0_targeted_ida_decompile.json 缺失或 JSON 不可解析。
2. artifact_index 中 local_reverse_affine_main0_targeted_ida_decompile 不是 freshness=current。
3. targeted artifact 未明确 executed_sample=false 或 ida_static_only=true。
4. targeted artifact 不含 affine_parameters，且不能从结构化字段可靠恢复 a/b/modulus。
5. affine multiplier 与 modulus 不互素，无法求逆。
6. 输入域不是 lowercase a-z，且当前实现不支持该域。
7. 需要运行 affine.exe 才能完成本轮。
8. 需要 runtime probe/debugger/emulator 才能完成本轮。
9. 需要读取完整 solve_reports 或 PROJECT_PROGRESS_LOG 才能完成本轮。
10. 需要提交 full solve_reports、IDA .i64 或原始样本才能完成本轮。
11. 需要把单题结论写入 .codex-skills 才能完成本轮。
```

完成条件：

```text
1. 生成 project_state/local_reverse_affine_inverse_handoff.json。
2. artifact 明确记录 forward affine transform、inverse transform、inverse_a=21。
3. artifact 在缺少 expected ciphertext 时明确 BLOCKED/PARTIAL，不生成 candidate。
4. artifact 明确 executed_sample=false、static_only=true、runtime_validated=false。
5. artifact_index.latest_artifacts 和 latest_artifacts_v2 已登记 handoff，freshness=current，source_run=round_20260605_affine_inverse_handoff_static_only_v1。
6. codex_execution_report.md 和 pytest_result.txt 与当前 decision_id/round_id 对齐。
7. codex_report_summary.tests_ran 完整列出 required commands，包括 git diff --check 和 git status --short。
8. 必要测试全部 Exit code 0。
9. 未运行样本、solver blind search、runtime probe、debugger、emulator。
10. 未提交 full solve_reports、IDA .i64、原始样本或 .codex-skills 修改。
```
