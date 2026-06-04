```json decision_meta
{
  "schema_version": 1,
  "decision_id": "decision_20260604_affine_static_feature_extraction_v1",
  "round_id": "round_20260604_affine_static_feature_extraction_v1",
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

上一轮已经接受 `affine_8cfebe03` 的静态证据提取计划和工具能力审计。目标样本仍是：

```text
sample_id: affine_8cfebe03
relative_path: 逆向课程2024春补考03/affine.exe
sha256: 8cfebe030f2d9fced106881e5aa6b2d81d162d31230dd3418b8fc3b15a5ef659
size_bytes: 196688
training_status: inventory_only
```

上一轮产物已经确认允许的静态动作包括 `static_triage`、`static_strings`、`static_file_type`、`static_entropy`、`static_pe_headers`、`static_import_names`、`static_constants`，并明确禁止运行样本、debugger、runtime probe、bruteforce、upload_binary。

本轮目标：**复用已有 `static_feature_extractor.py` 对 affine.exe 做纯静态特征提取**，生成当前样本的静态证据结果。

必须完成：

```text
1. 读取 project_state/local_reverse_affine_static_evidence_plan.json。
2. 确认 affine_8cfebe03 仍是目标样本，且仍为 inventory_only。
3. 解析 LOCAL_REVERSE_ROOT + relative_path 得到本地样本路径。
4. 复用已有 static_feature_extractor.py，不新建重复静态扫描器。
5. 只做纯静态读取，不执行 affine.exe。
6. 采集：
   - file_format / PE 识别结果
   - ASCII strings
   - entropy
   - keyword hits
   - interesting constants / byte patterns
   - 可用的 PE header 或 import 线索
7. 生成 project_state/local_reverse_affine_static_feature_result.json。
8. 生成 project_state/local_reverse_affine_static_feature_summary.json。
9. 必要时把新 artifact 登记到 artifact_index 或要求 project_state build。
10. 更新 codex_execution_report.md 和 pytest_result.txt。
```

本轮不要求解出 flag，不生成 candidate，不写 solver，不运行 IDA/Ghidra。IDA/Ghidra 只能作为下一轮可选动作。

---

## 2. Current Evidence

当前 `local_reverse_affine_static_evidence_plan.json` 已存在，确认 `affine.exe` 的 `training_status` 是 `inventory_only`，`mainline` 是 `tool_integration`。

当前工具能力审计显示：

```text
static_feature_extractor.py: present
tool_runners.py: present
local_reverse_ida_summary.py: present
local_reverse_ida_guided_solver.py: present
local_reverse_forced_ida_extract.py: present
local_reverse_targeted_static_reextract.py: present
Ghidra runner: missing
```

这说明本轮应先复用 `static_feature_extractor.py`，不要直接跳到新建 Ghidra/IDA runner。

`static_feature_extractor.py` 的可复用能力包括 PE format detection、ASCII string extraction、Shannon entropy、keyword scanning、interesting constant extraction。

上一轮测试和 lint 已通过，`pytest_result.txt` 记录 `test_project_state.py`、`lint-decision`、`lint-report`、`git diff --check`、`git status --short` 全部 Exit code 0。

当前 `task_packet.json` 仍保留旧 samplereverse 派生任务，但它只是 advisory；本轮以本 `project_state/decision_packet.md` 为执行权威。

---

## 3. Do Not Do

严禁：

```text
1. 不上传 E:\reverse 原始样本。
2. 不复制 affine.exe 到仓库。
3. 不运行 affine.exe。
4. 不运行 solver。
5. 不生成 candidate、flag 或最终答案。
6. 不运行 IDA/Ghidra。
7. 不运行动态调试、runtime probe、Frida、OllyDbg、x64dbg、emulator。
8. 不回到 old sample_solver blind search。
9. 不扩大 beam/budget/bruteforce。
10. 不提交 solve_reports 全量目录。
11. 不修改 .codex-skills。
12. 不新建重复 static extractor、IDA runner 或 Ghidra runner。
13. 不把 affine 单题结论写入长期 skill。
```

允许：

```text
1. 读取本地样本文件的 bytes 做纯静态分析。
2. 使用已有 static_feature_extractor.py。
3. 生成 project_state 下的小型 JSON 结果。
4. 如果现有 static_feature_extractor 缺少 CLI，可以新增很薄的 wrapper，但不得复制扫描逻辑。
5. 更新 report 和 pytest_result。
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
project_state/local_reverse_affine_static_evidence_plan.json
project_state/local_reverse_affine_tool_capability_audit.json
project_state/local_reverse_inventory.json
project_state/local_reverse_evaluation_queue.json
project_state/local_reverse_training_status.json
training_materials/local_reverse/status_overlay.json
reverse_agent/static_feature_extractor.py
tests/test_project_state.py
```

必要时检查：

```text
reverse_agent/local_reverse_inventory.py
reverse_agent/local_reverse_corpus.py
reverse_agent/tool_runners.py
tests/test_local_reverse_inventory.py
tests/test_local_reverse_training_status.py
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
1. 是否确认 affine_8cfebe03 仍为目标样本。
2. 是否确认 affine_8cfebe03 仍为 inventory_only，未误标 solved。
3. 是否通过 LOCAL_REVERSE_ROOT 定位本地样本。
4. 如果 LOCAL_REVERSE_ROOT 未设置或样本不存在，是否停止并报告 BLOCKED。
5. 是否复用了 static_feature_extractor.py。
6. 是否没有新建重复静态扫描器。
7. 是否只做纯静态读取，没有执行样本。
8. 是否没有运行 solver、IDA/Ghidra、debugger 或 runtime probe。
9. 是否生成 local_reverse_affine_static_feature_result.json。
10. 是否生成 local_reverse_affine_static_feature_summary.json。
11. 是否记录字符串、熵、关键词、常量、文件格式等静态证据。
12. 是否没有上传原始样本。
13. 是否没有提交 solve_reports 全量目录。
14. pytest_result.txt 是否记录真实测试命令且全部 Exit code 0。
15. codex_report_summary.based_on_decision_id 是否等于 decision_20260604_affine_static_feature_extraction_v1。
```

---

## 6. Implementation Scope

允许新增：

```text
project_state/local_reverse_affine_static_feature_result.json
project_state/local_reverse_affine_static_feature_summary.json
```

允许修改：

```text
project_state/codex_execution_report.md
project_state/pytest_result.txt
```

如果需要薄 wrapper，允许新增：

```text
reverse_agent/local_reverse_static_feature_run.py
tests/test_local_reverse_static_feature_run.py
```

但只有在 `static_feature_extractor.py` 没有可直接调用入口时才允许。wrapper 必须只做：

```text
1. 从 inventory/status 中定位 sample。
2. 拼接 LOCAL_REVERSE_ROOT 和 relative_path。
3. 调用 static_feature_extractor 现有函数。
4. 写 JSON。
```

不得复制字符串提取、熵计算、PE 识别、关键词扫描逻辑。

`local_reverse_affine_static_feature_result.json` 建议结构：

```json
{
  "schema_version": 1,
  "sample_id": "affine_8cfebe03",
  "relative_path": "逆向课程2024春补考03/affine.exe",
  "sha256": "8cfebe030f2d9fced106881e5aa6b2d81d162d31230dd3418b8fc3b15a5ef659",
  "size_bytes": 196688,
  "analysis_mode": "static_only",
  "executed_sample": false,
  "tool_used": "reverse_agent/static_feature_extractor.py",
  "file_format": {},
  "entropy": {},
  "strings": {
    "count": 0,
    "selected": []
  },
  "keyword_hits": {},
  "interesting_constants": [],
  "static_findings": [],
  "limitations": []
}
```

`local_reverse_affine_static_feature_summary.json` 建议结构：

```json
{
  "schema_version": 1,
  "sample_id": "affine_8cfebe03",
  "summary": {
    "likely_category": "unknown|affine_or_shift|strcmp|crypto|packed_or_obfuscated",
    "confidence": "low|medium|high",
    "evidence_count": 0,
    "has_compare_strings": false,
    "has_input_prompt": false,
    "has_affine_constants": false,
    "needs_ida_static_export": true
  },
  "recommended_next_mainline": "tool_integration",
  "recommended_next_action": "run_ida_static_export|targeted_static_reextract|solver_design",
  "forbidden_next_actions": [
    "runtime_probe",
    "execute_sample",
    "bruteforce",
    "upload_binary"
  ]
}
```

---

## 7. Tests

必须运行并记录：

```text
python -m pytest -q tests/test_project_state.py
python -m reverse_agent.project_state lint-decision --state-dir project_state
python -m reverse_agent.project_state lint-report --state-dir project_state
git diff --check
git status --short
```

如果新增 Python wrapper/test，则必须额外运行：

```text
python -m py_compile reverse_agent/local_reverse_static_feature_run.py
python -m pytest -q tests/test_local_reverse_static_feature_run.py
```

如果只直接调用已有模块并生成 JSON，则无需新增测试文件，但必须在 `pytest_result.txt` 说明没有新增代码。

所有 required commands 必须 Exit code 0。若任何命令失败，`codex_execution_report.md` 不得写 `SUCCESS/ACCEPT`。

---

## 8. Stop Conditions

立即停止并报告 `BLOCKED`：

```text
1. LOCAL_REVERSE_ROOT 未设置，无法定位 affine.exe。
2. affine.exe 本地文件不存在。
3. affine.exe 的 sha256 与 inventory 不一致。
4. 需要执行样本才能获得证据。
5. 需要运行 IDA/Ghidra 才能完成本轮。
6. 需要读取完整 solve_reports 才能完成本轮。
7. 需要上传原始样本才能完成本轮。
8. static_feature_extractor.py 不可复用，且新增 wrapper 会变成重复实现。
9. 输出会泄露 E:\reverse 或其他真实本地绝对路径。
```

完成条件：

```text
1. affine.exe 静态特征结果已生成。
2. summary 明确下一步是否需要 IDA 静态导出。
3. 样本未执行。
4. 未运行 solver、IDA/Ghidra、动态调试。
5. 未上传原始样本。
6. report/pytest 记录对齐本 decision_id。
7. lint-decision、lint-report、git diff --check 通过。
```
