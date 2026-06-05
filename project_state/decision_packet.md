```json decision_meta
{
  "schema_version": 1,
  "decision_id": "decision_20260605_affine_inverse_handoff_artifact_consistency_rework_v1",
  "round_id": "round_20260605_affine_inverse_handoff_artifact_consistency_rework_v1",
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

上一轮 `decision_20260605_affine_inverse_handoff_test_and_provenance_rework_v1` 审计结论为 `REWORK_REQUIRED`。核心代码与测试方向已经基本合格，但存在 **artifact 内容、artifact_index 与 report 声明不一致** 的记录一致性问题：

```text
1. artifact_index 声称 project_state/local_reverse_affine_inverse_handoff.json 已由 round_20260605_affine_inverse_handoff_test_and_provenance_rework_v1 更新。
2. codex_execution_report.md 声称当前 artifact 包含 ciphertext_provenance: null。
3. 但仓库中的 project_state/local_reverse_affine_inverse_handoff.json 仍像上一轮旧文件：
   - generated_at 仍为 2026-06-05T04:16:47Z
   - 缺少 ciphertext_provenance 字段
```

本轮目标：**只做 artifact 一致性返工**，确保 `project_state/local_reverse_affine_inverse_handoff.json` 的实际提交内容、`artifact_index.json` 登记、`codex_execution_report.md` 与 `pytest_result.txt` 完全一致。

本轮不需要修改核心算法逻辑，除非重新运行 CLI 后仍不能输出 `ciphertext_provenance` 字段。

---

## 2. Current Evidence

当前 `task_packet.json` 仍含旧 samplereverse/local_reverse advisory 信息，不控制本轮。本轮以本 `project_state/decision_packet.md` 为唯一执行权威。

上一轮已完成的有效部分：

```text
reverse_agent/local_reverse_affine_inverse_handoff.py 已增加 provenance gate。
TRUSTED_CIPHERTEXT_SOURCES = {challenge_statement, allowed_static_evidence, user_provided}。
_check_ciphertext_provenance() 会检查 expected_ciphertext_source / expected_ciphertext_provenance / expected_ciphertext_origin。
expected_ciphertext 无可信来源时应 BLOCKED / UNTRUSTED_EXPECTED_CIPHERTEXT_SOURCE / candidate=null。
tests/test_local_reverse_affine_inverse_handoff.py 已新增并覆盖 35 个测试用例。
```

当前需要修复的一致性缺口：

```text
project_state/local_reverse_affine_inverse_handoff.json 必须由当前代码重新生成，并包含：
  "ciphertext_provenance": null

同时该 artifact 应保持：
  "sample_id": "affine_8cfebe03"
  "analysis_mode": "affine_inverse_handoff_static_only"
  "executed_sample": false
  "static_only": true
  "runtime_validated": false
  "expected_ciphertext": null
  "candidate": null
  "status": "BLOCKED"
  "blocked_reason": "MISSING_EXPECTED_CIPHERTEXT"
  "inverse_transform.inverse_a": 21
```

`artifact_index.latest_artifacts_v2.local_reverse_affine_inverse_handoff` 必须与实际提交的 `project_state/local_reverse_affine_inverse_handoff.json` 对应：

```text
freshness: current
source_run: round_20260605_affine_inverse_handoff_artifact_consistency_rework_v1
sha256: 重新计算后的实际文件 sha256
size_bytes: 实际文件大小
modified_at: 本轮重新生成时间
sample_id: affine_8cfebe03
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
9. 不扩大到训练集批量执行。
10. 不重构无关 solver、IDA/Ghidra runner、训练集管理模块。
11. 不只更新 artifact_index 而不提交对应 artifact 内容。
12. 不让 report 声明与实际 artifact 内容不一致。
```

允许：

```text
1. 重新运行 affine inverse handoff CLI。
2. 重新生成 project_state/local_reverse_affine_inverse_handoff.json。
3. 更新 artifact_index.json 中 handoff artifact 的 sha256、size_bytes、modified_at、source_run。
4. 更新 codex_execution_report.md 与 pytest_result.txt。
5. 如重新生成后仍缺少 ciphertext_provenance，最小修复 reverse_agent/local_reverse_affine_inverse_handoff.py。
6. 运行 required tests。
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
tests/test_local_reverse_affine_inverse_handoff.py
```

允许修改：

```text
project_state/local_reverse_affine_inverse_handoff.json
project_state/artifact_index.json
project_state/codex_execution_report.md
project_state/pytest_result.txt
```

仅在重新生成后仍缺少 `ciphertext_provenance` 字段时，才允许修改：

```text
reverse_agent/local_reverse_affine_inverse_handoff.py
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
3. 是否确认本轮只是 artifact consistency 返工，没有扩大主线。
4. 是否重新运行 affine inverse handoff CLI。
5. 是否确认 project_state/local_reverse_affine_inverse_handoff.json 的 generated_at 已更新为本轮时间。
6. 是否确认 project_state/local_reverse_affine_inverse_handoff.json 包含 ciphertext_provenance: null。
7. 是否确认 current artifact 仍为 BLOCKED / MISSING_EXPECTED_CIPHERTEXT / candidate=null。
8. 是否重新计算并更新 artifact_index 中 local_reverse_affine_inverse_handoff 的 sha256、size_bytes、modified_at、source_run。
9. 是否确认 artifact_index sha256 与实际文件 sha256 一致。
10. 是否没有运行 affine.exe。
11. 是否没有运行 runtime probe、debugger、emulator。
12. 是否没有运行 old sample_solver blind search。
13. 是否没有提交 solve_reports、IDA .i64、log、原始样本。
14. 是否没有修改 .codex-skills。
15. 是否更新 codex_execution_report.md 和 pytest_result.txt。
16. codex_report_summary.based_on_decision_id 是否等于 decision_20260605_affine_inverse_handoff_artifact_consistency_rework_v1。
17. codex_report_summary.tests_ran 是否完整列出所有 required commands。
18. pytest_result.txt 是否记录每条命令、Exit code 和输出摘要。
```

---

## 6. Implementation Scope

本轮首选路径：**不改核心代码，只重新生成并同步记录**。

必须执行：

```bash
python -m reverse_agent.local_reverse_affine_inverse_handoff \
  --input project_state/local_reverse_affine_main0_targeted_ida_decompile.json \
  --out project_state/local_reverse_affine_inverse_handoff.json
```

生成后必须检查：

```text
1. project_state/local_reverse_affine_inverse_handoff.json 包含 ciphertext_provenance 字段。
2. ciphertext_provenance 为 null。
3. generated_at 不再是旧时间 2026-06-05T04:16:47Z。
4. expected_ciphertext=null。
5. candidate=null。
6. status=BLOCKED。
7. blocked_reason=MISSING_EXPECTED_CIPHERTEXT。
8. runtime_validated=false。
```

如果 CLI 重新生成后仍缺少 `ciphertext_provenance`，允许最小修复 `reverse_agent/local_reverse_affine_inverse_handoff.py`，但不得改变当前无密文 artifact 的 BLOCKED 语义。

更新 `artifact_index.json` 时必须保证：

```text
latest_artifacts.local_reverse_affine_inverse_handoff 指向 project_state\local_reverse_affine_inverse_handoff.json。
latest_artifacts_v2.local_reverse_affine_inverse_handoff.freshness=current。
latest_artifacts_v2.local_reverse_affine_inverse_handoff.source_run=round_20260605_affine_inverse_handoff_artifact_consistency_rework_v1。
latest_artifacts_v2.local_reverse_affine_inverse_handoff.sha256 与实际文件一致。
latest_artifacts_v2.local_reverse_affine_inverse_handoff.size_bytes 与实际文件一致。
latest_artifacts_v2.local_reverse_affine_inverse_handoff.sample_id=affine_8cfebe03。
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
2. 当前 handoff artifact 包含 ciphertext_provenance: null。
3. 当前 handoff artifact 为 BLOCKED / MISSING_EXPECTED_CIPHERTEXT / candidate=null。
4. artifact_index sha256 与实际 handoff artifact 一致。
5. git status --short 不出现 solve_reports、IDA .i64、log、原始样本、.codex-skills。
```

---

## 8. Stop Conditions

立即停止并报告 `BLOCKED`：

```text
1. 重新生成 handoff artifact 后仍缺少 ciphertext_provenance，且无法小步修复。
2. artifact_index 无法与实际 artifact sha256 对齐。
3. 需要运行 affine.exe 才能完成。
4. 需要 runtime probe/debugger/emulator 才能完成。
5. 需要提交 solve_reports、IDA .i64、log 或原始样本才能完成。
6. 需要修改 .codex-skills 才能完成。
7. 重新生成导致当前无密文 artifact 生成 candidate。
```

完成条件：

```text
1. project_state/local_reverse_affine_inverse_handoff.json 实际内容包含 ciphertext_provenance: null。
2. generated_at 为本轮重新生成时间。
3. artifact 仍为 BLOCKED / MISSING_EXPECTED_CIPHERTEXT / candidate=null。
4. artifact_index 与实际 artifact 文件一致。
5. codex_execution_report.md 与 pytest_result.txt 对齐当前 decision。
6. required tests 全部通过。
7. git status --short 不出现 solve_reports、IDA .i64、log、原始样本、.codex-skills。
```
