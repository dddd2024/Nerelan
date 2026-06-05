```json decision_meta
{
  "schema_version": 1,
  "decision_id": "decision_20260605_affine_inverse_handoff_test_and_provenance_rework_v1",
  "round_id": "round_20260605_affine_inverse_handoff_test_and_provenance_rework_v1",
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

上一轮 `decision_20260605_affine_inverse_handoff_static_only_v1` 审计结论为 `REWORK_REQUIRED`。方向正确，但存在三个验收缺口：

```text
1. pytest_result.txt 缺少 required command：python -m py_compile reverse_agent/local_reverse_constraint_recovery.py。
2. 新增 reverse_agent/local_reverse_affine_inverse_handoff.py 后，未新增并运行 tests/test_local_reverse_affine_inverse_handoff.py。
3. expected_ciphertext 存在时，代码只检查 expected_ciphertext，不检查 expected_ciphertext provenance/source；不满足“来源字段可审计才允许生成 candidate”的约束。
```

本轮目标：**只做 affine inverse handoff 的测试与 provenance gate 返工**。

必须完成：

```text
1. 补齐 required test 记录。
2. 新增 tests/test_local_reverse_affine_inverse_handoff.py，覆盖 affine handoff 核心逻辑。
3. 修复 expected_ciphertext 的 provenance gate：没有可审计来源字段时，不得生成 candidate。
4. 保持当前无密文 artifact 的结果为 BLOCKED / MISSING_EXPECTED_CIPHERTEXT。
5. 更新 codex_execution_report.md 与 pytest_result.txt。
```

本轮不得扩大到运行样本、runtime probe、debugger、solver blind search、训练集批量跑或工程重构。

---

## 2. Current Evidence

当前 `task_packet.json` 仍含旧 samplereverse/local_reverse advisory 信息，不控制本轮。本轮以本 `project_state/decision_packet.md` 为唯一执行权威。

当前 handoff artifact：

```text
project_state/local_reverse_affine_inverse_handoff.json
  sample_id: affine_8cfebe03
  source_artifact: project_state/local_reverse_affine_main0_targeted_ida_decompile.json
  analysis_mode: affine_inverse_handoff_static_only
  executed_sample: false
  static_only: true
  runtime_validated: false
  cipher_type: affine_cipher
  forward_transform: a=5, b=5, modulus=26
  inverse_transform: gcd_a_modulus=1, inverse_a=21
  expected_ciphertext: null
  candidate: null
  status: BLOCKED
  blocked_reason: MISSING_EXPECTED_CIPHERTEXT
```

当前代码问题：

```text
reverse_agent/local_reverse_affine_inverse_handoff.py 当前逻辑：
  expected_ciphertext = artifact.get("expected_ciphertext")
  if expected_ciphertext is None:
      status = "BLOCKED"
      blocked_reason = "MISSING_EXPECTED_CIPHERTEXT"
      candidate = None
  else:
      status = "READY"
      candidate = _decrypt_affine(expected_ciphertext, inverse_a, b, modulus)

缺口：expected_ciphertext 非空时，没有检查 expected_ciphertext_source / expected_ciphertext_provenance / expected_ciphertext_origin 等可审计来源字段。
```

`negative_results.json` 仍禁止 old sample_solver blind search、only increase beam/budget、commit full solve_reports、重复旧 runtime/probe 失败方向。本轮不得进入这些方向。

---

## 3. Do Not Do

严禁：

```text
1. 不运行 affine.exe。
2. 不运行 runtime probe、debugger、Frida、OllyDbg、x64dbg、emulator。
3. 不运行 old sample_solver blind search。
4. 不生成 flag 或最终 candidate。
5. 不发明 expected ciphertext。
6. 不读取完整 solve_reports 或 PROJECT_PROGRESS_LOG.txt。
7. 不提交 full solve_reports、IDA .i64、log 或原始样本。
8. 不修改 .codex-skills。
9. 不改动无关 solver、训练集、IDA runner、Ghidra runner。
10. 不把本轮返工扩大成训练集批量执行。
```

允许：

```text
1. 修改 reverse_agent/local_reverse_affine_inverse_handoff.py，加入 expected_ciphertext provenance gate。
2. 新增 tests/test_local_reverse_affine_inverse_handoff.py。
3. 重新生成 project_state/local_reverse_affine_inverse_handoff.json，保持当前无密文状态为 BLOCKED。
4. 更新 codex_execution_report.md 和 pytest_result.txt。
5. 必要时更新 artifact_index.json 中 handoff artifact 的 sha256、size_bytes、modified_at，但不得改变 freshness/source_run 语义。
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
project_state/local_reverse_affine_inverse_handoff.json
project_state/local_reverse_affine_main0_targeted_ida_decompile.json
reverse_agent/local_reverse_affine_inverse_handoff.py
reverse_agent/local_reverse_constraint_recovery.py
tests/test_project_state.py
```

允许新增或修改：

```text
reverse_agent/local_reverse_affine_inverse_handoff.py
tests/test_local_reverse_affine_inverse_handoff.py
project_state/local_reverse_affine_inverse_handoff.json
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
3. 是否确认本轮只是 affine inverse handoff 返工，未扩大主线。
4. 是否补跑 python -m py_compile reverse_agent/local_reverse_constraint_recovery.py。
5. 是否补跑 python -m py_compile reverse_agent/local_reverse_affine_inverse_handoff.py。
6. 是否新增并运行 tests/test_local_reverse_affine_inverse_handoff.py。
7. 是否测试 inverse_a=21。
8. 是否测试无 expected_ciphertext 时 status=BLOCKED、blocked_reason=MISSING_EXPECTED_CIPHERTEXT。
9. 是否测试 expected_ciphertext 无 provenance/source 时仍 BLOCKED，不生成 candidate。
10. 是否测试 expected_ciphertext 有可审计 provenance/source 时才允许 READY/candidate。
11. 是否测试 unsupported domain 阻断。
12. 是否测试 non-invertible affine multiplier 阻断。
13. 是否确认当前 project_state/local_reverse_affine_inverse_handoff.json 没有 candidate。
14. 是否没有运行 affine.exe。
15. 是否没有运行 runtime probe、debugger、emulator。
16. 是否没有运行 old sample_solver blind search。
17. 是否没有提交 solve_reports、IDA .i64、log、原始样本。
18. 是否没有修改 .codex-skills。
19. 是否更新 codex_execution_report.md 和 pytest_result.txt。
20. codex_report_summary.based_on_decision_id 是否等于 decision_20260605_affine_inverse_handoff_test_and_provenance_rework_v1。
21. codex_report_summary.tests_ran 是否完整列出所有 required commands。
22. pytest_result.txt 是否记录每条命令、Exit code 和输出摘要。
```

---

## 6. Implementation Scope

实现约束：

```text
1. 在 reverse_agent/local_reverse_affine_inverse_handoff.py 中增加 expected_ciphertext provenance gate。
2. 可接受字段示例：
   - expected_ciphertext_source
   - expected_ciphertext_provenance
   - expected_ciphertext_origin
3. provenance/source 必须非空，且取值属于可审计来源白名单，例如：
   - challenge_statement
   - allowed_static_evidence
   - user_provided
4. 如果 expected_ciphertext 存在但 provenance/source 缺失或不在白名单中，输出：
   status=BLOCKED
   blocked_reason=UNTRUSTED_EXPECTED_CIPHERTEXT_SOURCE
   candidate=null
5. 如果 expected_ciphertext 存在且 provenance/source 可审计，才允许：
   status=READY
   candidate=<inverse affine plaintext>
   runtime_validated=false
6. 当前 project_state/local_reverse_affine_inverse_handoff.json 的输入 artifact 没有 expected_ciphertext，因此正常输出仍应为：
   status=BLOCKED
   blocked_reason=MISSING_EXPECTED_CIPHERTEXT
   candidate=null
7. 不修改 artifact 语义为 solved。
8. 保持 CLI 兼容：python -m reverse_agent.local_reverse_affine_inverse_handoff --input ... --out ...
9. 保持旧字段兼容，不破坏 tests/test_project_state.py。
10. 不修改 .codex-skills。
```

测试文件 `tests/test_local_reverse_affine_inverse_handoff.py` 至少覆盖：

```text
1. 从结构化 artifact 读取 a=5、b=5、modulus=26。
2. 计算 gcd=1、inverse_a=21。
3. 生成 26 个 per_char_mapping。
4. 无 expected_ciphertext -> BLOCKED / MISSING_EXPECTED_CIPHERTEXT / candidate=null。
5. expected_ciphertext 非空但无 source/provenance -> BLOCKED / UNTRUSTED_EXPECTED_CIPHERTEXT_SOURCE / candidate=null。
6. expected_ciphertext 非空且 source=challenge_statement -> READY 且生成 candidate。
7. input domain 不是 lowercase a-z -> BLOCKED / UNSUPPORTED_DOMAIN。
8. a 与 modulus 不互素 -> BLOCKED / NON_INVERTIBLE_AFFINE_MULTIPLIER。
```

---

## 7. Tests

必须运行并记录：

```bash
python -m py_compile reverse_agent/local_reverse_constraint_recovery.py
python -m py_compile reverse_agent/local_reverse_affine_inverse_handoff.py
python -m pytest -q tests/test_local_reverse_affine_inverse_handoff.py
python -m pytest -q tests/test_project_state.py
python -m reverse_agent.project_state lint-decision --state-dir project_state
python -m reverse_agent.project_state lint-report --state-dir project_state
python -m reverse_agent.local_reverse_affine_inverse_handoff --input project_state/local_reverse_affine_main0_targeted_ida_decompile.json --out project_state/local_reverse_affine_inverse_handoff.json
git diff --check
git status --short
```

测试期望：

```text
1. 所有命令 Exit code 0。
2. 当前 handoff artifact 仍为 BLOCKED / MISSING_EXPECTED_CIPHERTEXT。
3. current artifact 不生成 candidate。
4. expected_ciphertext 无 provenance/source 的测试样例不会生成 candidate。
5. expected_ciphertext 有 challenge_statement provenance/source 的测试样例可以生成 candidate，但 runtime_validated=false。
6. git status --short 不出现 solve_reports、IDA .i64、log、原始样本、.codex-skills。
```

---

## 8. Stop Conditions

立即停止并报告 `BLOCKED`：

```text
1. local_reverse_affine_inverse_handoff.py 无法保持旧 CLI 兼容。
2. 无法新增 tests/test_local_reverse_affine_inverse_handoff.py。
3. 无法补齐 python -m py_compile reverse_agent/local_reverse_constraint_recovery.py。
4. 需要运行 affine.exe 才能完成。
5. 需要 runtime probe/debugger/emulator 才能完成。
6. 需要提交 solve_reports、IDA .i64、log 或原始样本才能完成。
7. 需要修改 .codex-skills 才能完成。
8. provenance gate 会导致当前无密文 artifact 生成 candidate。
```

完成条件：

```text
1. tests/test_local_reverse_affine_inverse_handoff.py 存在并通过。
2. local_reverse_constraint_recovery.py 与 local_reverse_affine_inverse_handoff.py 均 py_compile 通过。
3. 当前无密文 artifact 仍为 BLOCKED / MISSING_EXPECTED_CIPHERTEXT / candidate=null。
4. expected_ciphertext 无 provenance/source 时不会生成 candidate。
5. expected_ciphertext 有可审计 provenance/source 时才允许生成 candidate。
6. codex_execution_report.md 与 pytest_result.txt 对齐当前 decision。
7. codex_report_summary.tests_ran 完整列出 required commands。
8. git status --short 不出现 solve_reports、IDA .i64、log、原始样本、.codex-skills。
```
