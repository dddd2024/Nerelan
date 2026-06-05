```json decision_meta
{
  "schema_version": 1,
  "decision_id": "decision_20260605_cpp1_target_bytes_test_record_rework_v1",
  "round_id": "round_20260605_cpp1_target_bytes_test_record_rework_v1",
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

上一轮 `decision_20260605_cpp1_target_bytes_length_rework_v1` 审计结论为 `REWORK_REQUIRED`。功能目标已经基本完成：`project_state/local_reverse_cpp1_2f6fcb63_target_bytes.json` 已经包含 16 字节 target bytes，且保持 static-only 与 no-candidate 语义。但仍存在一个测试记录阻断：

```text
required command 缺失：python -m py_compile reverse_agent/tool_runners.py
```

本轮目标：**只修复 cpp1_2f6fcb63 target-bytes length rework 的测试记录缺口**。

不得修改核心提取逻辑，除非补跑 required tests 暴露真实错误。

必须保持当前 target bytes artifact 语义：

```text
sample_id=cpp1_2f6fcb63
analysis_mode=target_compare_byte_extraction
expected_target_length=16
target_length=16
len(target_bytes)=16
target_bytes_hex=d596c4f60745577776e5f64847f74817
executed_sample=false
static_only=true
runtime_validated=false
candidate=null
known_candidate=""
```

本轮仍不进入 inverse transform，不求解，不更新 solved 状态。

---

## 2. Current Evidence

当前 `task_packet.json` 仍是旧 samplereverse advisory，不控制本轮。本轮以本 `project_state/decision_packet.md` 为唯一执行权威。

上一轮已修复的有效事实：

```text
project_state/local_reverse_cpp1_2f6fcb63_target_bytes.json:
  tool_status=success
  expected_target_length=16
  target_length=16
  target_bytes_hex=d596c4f60745577776e5f64847f74817
  target_bytes=[213,150,196,246,7,69,87,119,118,229,246,72,71,247,72,23]
  executed_sample=false
  static_only=true
  runtime_validated=false
  candidate=null
  known_candidate=""

artifact_index.latest_artifacts_v2.local_reverse_cpp1_2f6fcb63_target_bytes:
  freshness=current
  source_run=round_20260605_cpp1_target_bytes_length_rework_v1
```

上一轮测试记录缺口：

```text
codex_execution_report.md tests_ran did not include:
  python -m py_compile reverse_agent/tool_runners.py

pytest_result.txt did not include:
  python -m py_compile reverse_agent/tool_runners.py
```

This rework must create a new aligned round:

```text
decision_id=decision_20260605_cpp1_target_bytes_test_record_rework_v1
round_id=round_20260605_cpp1_target_bytes_test_record_rework_v1
report_id=report_20260605_cpp1_target_bytes_test_record_rework_v1
artifact_index.latest_artifacts_v2.local_reverse_cpp1_2f6fcb63_target_bytes.source_run=round_20260605_cpp1_target_bytes_test_record_rework_v1
```

`negative_results.json` still forbids old blind search, only increasing search budget, committing full solve_reports, and repeating old dynamic-probe directions. This rework must not enter those directions.

---

## 3. Do Not Do

严禁：

```text
1. 不动态执行本地样本。
2. 不做动态探测或交互式调试。
3. 不运行旧盲搜 solver。
4. 不运行 brute force 或扩大搜索预算。
5. 不执行 inverse transform。
6. 不生成 candidate、flag、known_candidate。
7. 不把 cpp1_2f6fcb63 标记 solved。
8. 不提交原始样本文件。
9. 不提交 full solve_reports、IDA 数据库副产物或无必要日志。
10. 不读取完整 solve_reports 或 PROJECT_PROGRESS_LOG.txt。
11. 不修改 .codex-skills。
12. 不新建第二套 IDA runner。
13. 不重构 target-byte extraction 逻辑。
14. 不把静态字节提取结果说成 runtime validation。
```

允许：

```text
1. 补跑 required tests。
2. 重新运行 target byte extraction CLI，确保 artifact 仍为 16 字节 success。
3. 更新 artifact_index.json 的 source_run、sha256、size_bytes、modified_at。
4. 更新 codex_execution_report.md 与 pytest_result.txt。
5. 仅当补跑测试暴露真实错误时，才允许最小修复相关代码或测试。
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
project_state/local_reverse_cpp1_2f6fcb63_target_bytes.json
reverse_agent/tool_runners.py
reverse_agent/ida_scripts/extract_named_data.py
reverse_agent/local_reverse_cpp1_target_byte_extract.py
tests/test_local_reverse_cpp1_target_byte_extract.py
```

允许修改：

```text
project_state/local_reverse_cpp1_2f6fcb63_target_bytes.json
project_state/artifact_index.json
project_state/codex_execution_report.md
project_state/pytest_result.txt
```

仅当 required tests 暴露真实错误时，才允许最小修改：

```text
reverse_agent/tool_runners.py
reverse_agent/ida_scripts/extract_named_data.py
reverse_agent/local_reverse_cpp1_target_byte_extract.py
tests/test_local_reverse_cpp1_target_byte_extract.py
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
4. 是否确认本轮只是 target-bytes test-record rework。
5. 是否确认目标样本只限 cpp1_2f6fcb63。
6. 是否补跑 python -m py_compile reverse_agent/tool_runners.py。
7. 是否补跑 python -m py_compile reverse_agent/ida_scripts/extract_named_data.py。
8. 是否补跑 python -m py_compile reverse_agent/local_reverse_cpp1_target_byte_extract.py。
9. 是否运行 tests/test_local_reverse_cpp1_target_byte_extract.py。
10. 是否运行 tests/test_project_state.py。
11. 是否运行 lint-decision 与 lint-report。
12. 是否重新运行 target byte extraction CLI。
13. 是否确认 artifact 仍为 expected_target_length=16、target_length=16、len(target_bytes)=16。
14. 是否确认 artifact 仍为 executed_sample=false / static_only=true / runtime_validated=false。
15. 是否确认 artifact 仍为 candidate=null / known_candidate=""。
16. 是否没有动态执行样本。
17. 是否没有运行 solver / brute force。
18. 是否没有执行 inverse transform。
19. 是否没有提交原始样本、full solve_reports、IDA 数据库副产物或 .codex-skills 修改。
20. 是否 artifact_index 登记 source_run=round_20260605_cpp1_target_bytes_test_record_rework_v1。
21. 是否 artifact_index sha256 与实际 target bytes artifact 文件一致。
22. 是否 codex_execution_report.md 与 pytest_result.txt 对齐当前 decision_id/round_id。
23. tests_ran 是否完整列出 required commands，且无省略号。
24. pytest_result.txt 是否记录每条命令、Exit Code 和输出摘要。
```

---

## 6. Implementation Scope

首选路径：不改核心代码，只补跑测试并同步记录。

必须同步：

```text
codex_execution_report.md:
  report_id=report_20260605_cpp1_target_bytes_test_record_rework_v1
  round_id=round_20260605_cpp1_target_bytes_test_record_rework_v1
  based_on_decision_id=decision_20260605_cpp1_target_bytes_test_record_rework_v1
  status=SUCCESS only if all required commands pass

pytest_result.txt:
  Round=round_20260605_cpp1_target_bytes_test_record_rework_v1
  Decision=decision_20260605_cpp1_target_bytes_test_record_rework_v1
  Report=report_20260605_cpp1_target_bytes_test_record_rework_v1

artifact_index.json:
  latest_artifacts.local_reverse_cpp1_2f6fcb63_target_bytes=project_state\\local_reverse_cpp1_2f6fcb63_target_bytes.json
  latest_artifacts_v2.local_reverse_cpp1_2f6fcb63_target_bytes.freshness=current
  latest_artifacts_v2.local_reverse_cpp1_2f6fcb63_target_bytes.source_run=round_20260605_cpp1_target_bytes_test_record_rework_v1
  latest_artifacts_v2.local_reverse_cpp1_2f6fcb63_target_bytes.sha256=<actual file sha256>
  latest_artifacts_v2.local_reverse_cpp1_2f6fcb63_target_bytes.size_bytes=<actual file size>
```

Target bytes artifact must remain semantically unchanged except for generated_at if regenerated:

```text
expected_target_length=16
target_length=16
target_bytes_hex=d596c4f60745577776e5f64847f74817
candidate=null
known_candidate=""
```

---

## 7. Tests

必须运行并记录：

```bash
python -m py_compile reverse_agent/tool_runners.py
python -m py_compile reverse_agent/ida_scripts/extract_named_data.py
python -m py_compile reverse_agent/local_reverse_cpp1_target_byte_extract.py
python -m pytest -q tests/test_local_reverse_cpp1_target_byte_extract.py
python -m pytest -q tests/test_project_state.py
python -m reverse_agent.project_state lint-decision --state-dir project_state
python -m reverse_agent.project_state lint-report --state-dir project_state
python -m reverse_agent.local_reverse_cpp1_target_byte_extract --sample-id cpp1_2f6fcb63 --triage project_state/local_reverse_cpp1_2f6fcb63_static_triage.json --inventory project_state/local_reverse_inventory.json --out project_state/local_reverse_cpp1_2f6fcb63_target_bytes.json
git diff --check
git status --short
```

Expected results：

```text
1. All required commands Exit Code 0.
2. tests_ran includes python -m py_compile reverse_agent/tool_runners.py.
3. Artifact remains success with expected_target_length=16 and target_length=16.
4. Artifact includes executed_sample=false, static_only=true, runtime_validated=false.
5. Artifact does not contain candidate/flag/known_candidate.
6. artifact_index registers local_reverse_cpp1_2f6fcb63_target_bytes with freshness=current and source_run=round_20260605_cpp1_target_bytes_test_record_rework_v1.
7. git status --short does not include original samples, full solve_reports, IDA database side products, or .codex-skills.
```

---

## 8. Stop Conditions

立即停止并报告 `BLOCKED`：

```text
1. 无法补跑 py_compile reverse_agent/tool_runners.py。
2. 补跑测试导致 target bytes artifact 不再是 16 字节 success。
3. 需要动态执行样本才能完成。
4. 需要运行 solver / brute force 才能完成。
5. 需要执行 inverse transform 才能完成。
6. 需要提交原始样本、full solve_reports、IDA 数据库副产物或 .codex-skills 才能完成。
7. 修复过程中出现 candidate/known_candidate/flag 生成倾向。
```

完成条件：

```text
1. codex_execution_report.md、pytest_result.txt、decision_packet.md 的 decision_id/round_id 对齐。
2. tests_ran 完整列出所有 required commands，尤其包含 python -m py_compile reverse_agent/tool_runners.py。
3. project_state/local_reverse_cpp1_2f6fcb63_target_bytes.json 仍为 16 字节 success artifact。
4. Artifact includes expected_target_length=16, target_length=16, len(target_bytes)=16。
5. Artifact 不含 candidate/flag/known_candidate。
6. artifact_index source_run=round_20260605_cpp1_target_bytes_test_record_rework_v1。
7. required tests 全部记录。
8. 未动态执行样本，未运行 solver，未修改 .codex-skills，未提交大型副产物或原始样本。
```
