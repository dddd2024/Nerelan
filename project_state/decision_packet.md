```json decision_meta
{
  "schema_version": 1,
  "decision_id": "decision_20260607_cpp2_2f64e68d_post_strcmp_oracle_extraction_v1",
  "round_id": "round_20260607_cpp2_2f64e68d_post_strcmp_oracle_extraction_v1",
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

目标：针对 `cpp2_2f64e68d`，从已经发现的 `_strcmp` 调用点和其后继分支中提取一个可审计的 **post-strcmp success/failure oracle**，解决上一轮 `winpty` pair validation 只能得到 `AMBIGUOUS_OUTPUT` 的问题。

本轮不重新验证 `ippio/jppio`，不把 `ippio` 标记为 solved。目标是生成一个结构化 oracle artifact，回答：

```text
1. strcmp(compare_call_ea=0x40111C) 的返回值如何被分支使用。
2. 哪条分支代表 candidate accepted，哪条分支代表 rejected。
3. success/reject 分支是否存在可观察输出字符串、返回码、API 调用或其他 runtime classifier 可用信号。
4. 现有 console validator 是否能基于该 oracle 安全分类；若不能，必须说明缺口。
```

预期产物：

```text
project_state/local_reverse_cpp2_2f64e68d_post_strcmp_oracle_extraction.json
project_state/artifact_index.json
project_state/local_reverse_training_status.json
project_state/codex_execution_report.md
project_state/pytest_result.txt
```

成功标准不是解出样本，而是得到 `oracle_status=ORACLE_CONFIRMED` 或 `oracle_status=ORACLE_AMBIGUOUS/BLOCKED` 的保守结论，并登记 provenance。只有当 oracle artifact 同时证明 success/reject 分支及可观察 classifier 信号时，下一轮才允许写一个单独的 bounded runtime revalidation decision。

---

## 2. Current Evidence

`project_state/task_packet.json` 仍是旧 `samplereverse` advisory，不控制本轮：

```text
active_decision_packet=project_state/decision_packet.md
execution_scope=decision_packet_controls_current_round
task=Review bounded window discovery diagnostics
local_reverse_task_packet_authority_note=Advisory only; project_state/decision_packet.md remains the execution authority.
```

上一轮 `cpp2_2f64e68d` final bounded winpty validation 已完成，但结果不是成功：

```text
project_state/local_reverse_cpp2_2f64e68d_pywinpty_runtime_validation.json:
  sample_id=cpp2_2f64e68d
  backend=winpty
  candidate_input=ippio
  negative_control_input=jppio
  max_runs=2
  executed_sample=true
  runtime_validated=false
  validation_status=AMBIGUOUS_OUTPUT
  outputs_differ=true
  candidate_accepted=false
  control_rejected=false
  candidate=null
  known_candidate=""
  solved=false
  blocked_reason=AMBIGUOUS_OUTPUT
```

当前 training status：

```text
project_state/local_reverse_training_status.json:
  cpp2_2f64e68d.training_status=blocked
  cpp2_2f64e68d.known_candidate=""
  cpp2_2f64e68d.blocked_reason=AMBIGUOUS_OUTPUT
  cpp2_2f64e68d.classification=console_winpty_runtime_validation_ambiguous
```

静态候选证据仍是 current：

```text
project_state/local_reverse_cpp2_2f64e68d_static_triage.json:
  ida_attempted=true
  ida_success=true
  source_tool=IDA
  executed_sample=false
  runtime_validated=false

project_state/local_reverse_cpp2_2f64e68d_strcmp_handoff.json:
  analysis_mode=direct_strcmp_static_handoff
  source_tool=IDA
  compare_call_ea=0x40111C
  compare_callee=_strcmp
  compare_nearby includes push offset Str2; "ippio" and push ecx; Str1
  static_candidate_text=ippio
  static_candidate_hex=697070696f
  status=READY_FOR_RUNTIME_VALIDATION
  runtime_validated=false
  solved=false
```

已存在相关工具能力，必须优先检查和复用，不允许新建重复 IDA/Ghidra runner：

```text
reverse_agent/local_reverse_ida_summary.py
reverse_agent/local_reverse_forced_ida_extract.py
reverse_agent/local_reverse_direct_strcmp_handoff.py
reverse_agent/local_reverse_compare_site.py
reverse_agent/ida_scripts/collect_evidence.py
reverse_agent/ida_scripts/forced_function_extract.py
reverse_agent/ida_scripts/extract_named_data.py
project_state/local_reverse_cpp2_2f64e68d_static_triage.json
project_state/local_reverse_cpp2_2f64e68d_strcmp_handoff.json
```

`negative_results.json` 主要记录旧 `samplereverse` 禁止方向。本轮不得触碰旧 `samplereverse` blind search、guided pool、Base64/RC4 breakpoint probe、CompareProbe 等方向。上一轮 `cpp2_2f64e68d` 的 `ippio/jppio` runtime 结果是 ambiguous，不是 candidate failure。

---

## 3. Do Not Do

严禁：

```text
1. 不把 task_packet.task 当作当前轮任务。
2. 不修改 project_state/decision_packet.md。
3. 不把 ippio 写入 known_candidate/candidate/solved。
4. 不重跑上一轮 ippio/jppio winpty runtime validation。
5. 不运行 CPP2.exe / Cpp2.exe / 任何真实训练样本。
6. 不运行 subprocess backend validation。
7. 不运行 solver、bruteforce、guided pool、symbolic search、constraint recovery。
8. 不运行 debugger、OllyDbg、x64dbg、Frida hook、emulator、CompareProbe。
9. 不扫描完整 solve_reports、PROJECT_PROGRESS_LOG.txt 或本地训练样本目录。
10. 不提交 .venv、site-packages、wheel、DLL、EXE、sample binary、solve_reports 或 .codex-skills。
11. 不新建重复 IDA/Ghidra/debugger 接口；已有工具能做的不要重写。
12. 不用 echo-only 的 winpty 输出差异当作 success/reject 证据。
13. 不根据静态字符串 "ippio" 单独标 solved；必须保持 runtime_validated=false。
```

允许：

```text
1. 读取 current cpp2 static triage、direct strcmp handoff、winpty validation artifact、training status。
2. 检查现有 IDA/Ghidra/static extraction 工具接口。
3. 如 current artifacts 已足够，直接生成 post-strcmp oracle artifact。
4. 如 current artifacts 不足，使用现有 IDA/IDAPython extraction path 做一次 bounded extraction，只围绕 compare_call_ea=0x40111C、所属函数、后继 basic blocks、相关输出字符串/API/return sites。
5. 如现有脚本缺少结构化 oracle 汇总能力，可新增一个很小的 Python 汇总器，但它只能消费现有 IDA/static artifact，不能自己解析二进制或重写 disassembler。
6. 有界更新 artifact_index、local_reverse_training_status、codex_execution_report、pytest_result。
7. 如果 oracle 仍不足，写 ORACLE_AMBIGUOUS 或 BLOCKED，并说明下一步缺口。
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
.codex-skills/registry.json
project_state/local_reverse_cpp2_2f64e68d_static_triage.json
project_state/local_reverse_cpp2_2f64e68d_strcmp_handoff.json
project_state/local_reverse_cpp2_2f64e68d_pywinpty_runtime_validation.json
project_state/local_reverse_training_status.json
reverse_agent/local_reverse_direct_strcmp_handoff.py
reverse_agent/local_reverse_compare_site.py
reverse_agent/local_reverse_ida_summary.py
reverse_agent/local_reverse_forced_ida_extract.py
reverse_agent/ida_scripts/collect_evidence.py
reverse_agent/ida_scripts/forced_function_extract.py
reverse_agent/ida_scripts/extract_named_data.py
tests/test_project_state.py
```

必要时读取：

```text
reverse_agent/project_state.py
reverse_agent/local_reverse_console_pair_validator.py
tests/test_local_reverse_console_pair_validator.py
training_materials/local_reverse/status_overlay.json
project_state/local_reverse_evaluation_queue.json
```

不要默认读取：

```text
solve_reports/ 全量
PROJECT_PROGRESS_LOG.txt 全量
project_state/rounds/ 全量历史
local_reverse_samples/ 或 E:\reverse 全量目录
```

---

## 5. Required Audit

Codex 报告必须回答：

```text
1. 是否确认当前 decision_packet 是本轮唯一执行权威。
2. 是否确认 task_packet.task 只是旧 samplereverse advisory。
3. 是否确认本轮主线为 reverse_solving。
4. 是否确认上一轮 winpty artifact 是 AMBIGUOUS_OUTPUT，不是 VALIDATED_SUCCESS。
5. 是否确认 cpp2_2f64e68d 当前仍 blocked，known_candidate=""，solved=false。
6. 是否确认没有运行 CPP2.exe / Cpp2.exe / 任何真实训练样本。
7. 是否确认没有重跑 ippio/jppio winpty 或 subprocess validation。
8. 是否确认没有运行 solver/bruteforce/symbolic/debugger/hook/emulator。
9. 是否列出现有 IDA/static 工具接口，并说明复用了哪些、为什么没有新建重复接口。
10. 是否说明 oracle extraction 的证据来源：current artifact、existing IDA extraction，或 bounded new artifact。
11. 是否给出 compare_call_ea、compare_callee、candidate string、branch condition、success path、failure path。
12. 是否列出 success/reject 分支可观察信号：输出字符串、API、return code、exit path 或明确说明缺失。
13. 是否明确 oracle_status 为 ORACLE_CONFIRMED / ORACLE_AMBIGUOUS / BLOCKED。
14. 如果 ORACLE_CONFIRMED，是否仍未把 ippio 标 solved，并只建议下一轮 bounded oracle-backed runtime revalidation。
15. 如果 ORACLE_AMBIGUOUS/BLOCKED，是否说明具体缺口，且没有扩大到 solver 或盲跑。
16. 是否更新 artifact_index latest_artifacts 和 latest_artifacts_v2 的 current provenance。
17. 是否有界更新 local_reverse_training_status，仅触碰 cpp2_2f64e68d。
18. 是否说明 negative_results 是否更新；若未更新，必须给出理由。
19. 是否确认 pytest_result.txt 使用本 decision_id/report_id/round_id，并记录命令、exit code、关键输出。
20. 是否确认 final lint-report 是写入本轮 report 后的最终成功记录。
21. 是否确认 git diff --check、git status --short、git diff --name-status 均有真实输出记录。
22. 是否确认 files_changed 完整列出所有实际变更文件。
23. 是否确认没有提交 .venv、site-packages、wheel、DLL、EXE、sample binary、solve_reports 或 .codex-skills。
```

---

## 6. Implementation Scope

小步推进，不跨主线扩张。

### Phase A — state and capability preflight

必须使用 `.venv\Scripts\python`。先读取并断言：

```text
project_state/local_reverse_cpp2_2f64e68d_strcmp_handoff.json:
  static_candidate_text=ippio
  compare_call_ea=0x40111C
  compare_callee=_strcmp
  status=READY_FOR_RUNTIME_VALIDATION
  solved=false

project_state/local_reverse_cpp2_2f64e68d_pywinpty_runtime_validation.json:
  validation_status=AMBIGUOUS_OUTPUT
  runtime_validated=false
  candidate_accepted=false
  control_rejected=false
  known_candidate=""
  solved=false

project_state/local_reverse_training_status.json:
  cpp2_2f64e68d.training_status=blocked
  cpp2_2f64e68d.known_candidate=""
```

然后检查现有工具接口：

```text
reverse_agent/local_reverse_direct_strcmp_handoff.py
reverse_agent/local_reverse_compare_site.py
reverse_agent/local_reverse_ida_summary.py
reverse_agent/local_reverse_forced_ida_extract.py
reverse_agent/ida_scripts/collect_evidence.py
reverse_agent/ida_scripts/forced_function_extract.py
reverse_agent/ida_scripts/extract_named_data.py
```

如果 preflight 失败，停止并写 `oracle_status=BLOCKED`，不得运行样本。

### Phase B — bounded post-strcmp oracle extraction

优先级：

```text
1. 优先从 current static triage / strcmp handoff artifact 中提取。
2. 如果 current artifact 不含后继分支和输出路径，使用现有 IDA/IDAPython extraction path 做一次 bounded static extraction。
3. 只围绕 compare_call_ea=0x40111C、所属函数、紧邻 basic blocks、success/reject 分支、相关输出字符串/API/return sites。
4. 如果没有可用 IDA 环境或现有 runner 无法 bounded 提取，写 BLOCKED，不新建重复 runner。
```

目标 artifact schema 至少包含：

```text
schema_version=1
sample_id=cpp2_2f64e68d
mainline=reverse_solving
analysis_mode=post_strcmp_oracle_extraction
source_tool=IDA|existing_artifacts|mixed
source_artifact_freshness=current
executed_sample=false
runtime_validated=false
compare_call_ea=0x40111C
compare_callee=_strcmp
candidate_from_static=ippio
branch_condition=<jz/jnz/test/cmp details or unknown>
success_path=<address/evidence or unknown>
failure_path=<address/evidence or unknown>
success_observable_signals=[]
failure_observable_signals=[]
echo_only_runtime_difference_from_previous_validation=true|false|unknown
can_classify_runtime_output=true|false
oracle_status=ORACLE_CONFIRMED|ORACLE_AMBIGUOUS|BLOCKED
blocked_reason=<empty or specific>
candidate=null
known_candidate=""
solved=false
next_allowed_action=<bounded oracle-backed revalidation | classifier improvement | manual static review>
generated_at=<timestamp>
```

判断规则：

```text
ORACLE_CONFIRMED:
  必须同时有 strcmp result branch、success path、failure path、且至少一个可观察 success/reject classifier 信号。
  即使确认，也不得标 solved；只能把 next_action 写成 bounded oracle-backed runtime revalidation。

ORACLE_AMBIGUOUS:
  能定位 strcmp 和候选，但无法确认分支语义或 runtime 可观察信号。
  保持 blocked/unsolved。

BLOCKED:
  缺少 current artifact、IDA/tool unavailable、compare_call mismatch、target mismatch、或 bounded extraction 失败。
  保持 blocked/unsolved。
```

### Phase C — project_state updates

必须更新：

```text
project_state/local_reverse_cpp2_2f64e68d_post_strcmp_oracle_extraction.json
project_state/artifact_index.json
project_state/codex_execution_report.md
project_state/pytest_result.txt
```

根据 outcome 有界更新或保持：

```text
project_state/local_reverse_training_status.json
training_materials/local_reverse/status_overlay.json
project_state/local_reverse_evaluation_queue.json
project_state/negative_results.json
```

只能触碰 `cpp2_2f64e68d`。不得重建全量 inventory，不得改其他样本状态。

artifact_index 必须同时更新：

```text
latest_artifacts["local_reverse_cpp2_2f64e68d_post_strcmp_oracle_extraction"]
latest_artifacts_v2["local_reverse_cpp2_2f64e68d_post_strcmp_oracle_extraction"]
```

`latest_artifacts_v2` 字段至少包含：

```text
kind=local_reverse_post_strcmp_oracle_extraction
path=project_state\local_reverse_cpp2_2f64e68d_post_strcmp_oracle_extraction.json
freshness=current
source_run=round_20260607_cpp2_2f64e68d_post_strcmp_oracle_extraction_v1
sha256=<actual artifact sha256>
size_bytes=<actual artifact size>
modified_at=<artifact generated_at or filesystem mtime>
sample_id=cpp2_2f64e68d
```

### Phase D — report

`codex_execution_report.md` 顶部必须包含 fenced JSON block：

```json codex_report_summary
{
  "schema_version": 1,
  "report_id": "report_20260607_cpp2_2f64e68d_post_strcmp_oracle_extraction_v1",
  "round_id": "round_20260607_cpp2_2f64e68d_post_strcmp_oracle_extraction_v1",
  "based_on_decision_id": "decision_20260607_cpp2_2f64e68d_post_strcmp_oracle_extraction_v1",
  "status": "SUCCESS|BLOCKED|FAILED",
  "acceptance_recommendation": "ACCEPTED|ACCEPTED_WITH_LIMITATIONS|REWORK_REQUIRED|BLOCKED",
  "files_changed": [],
  "tests_ran": [],
  "generated_artifacts": []
}
```

报告必须写清楚 oracle outcome，不得只写“提取完成”。

---

## 7. Tests

所有 Python 命令必须使用 `.venv\Scripts\python`。

必须运行并记录：

```text
.venv\Scripts\python -m py_compile reverse_agent/local_reverse_direct_strcmp_handoff.py
.venv\Scripts\python -m py_compile reverse_agent/local_reverse_compare_site.py
.venv\Scripts\python -m py_compile reverse_agent/local_reverse_ida_summary.py
.venv\Scripts\python -m py_compile reverse_agent/local_reverse_forced_ida_extract.py
.venv\Scripts\python -m pytest -q tests/test_project_state.py
.venv\Scripts\python -m reverse_agent.project_state lint-decision --state-dir project_state
<bounded oracle extraction command or artifact synthesis command; must not execute target sample>
.venv\Scripts\python -m reverse_agent.project_state lint-report --state-dir project_state   # final after report write
.venv\Scripts\python -m reverse_agent.project_state status --state-dir project_state
git diff --check
git status --short
git diff --name-status
```

如果新增很小的 extractor/synthesizer 文件，必须额外运行：

```text
.venv\Scripts\python -m py_compile <new_file>
.venv\Scripts\python -m pytest -q <directly related new_or_existing_test_file>
```

必须做内容断言并在报告中写明：

```text
1. post-strcmp oracle artifact exists。
2. artifact sample_id=cpp2_2f64e68d。
3. artifact executed_sample=false。
4. artifact runtime_validated=false。
5. artifact compare_call_ea=0x40111C。
6. artifact candidate_from_static=ippio。
7. artifact known_candidate=""。
8. artifact solved=false。
9. oracle_status is ORACLE_CONFIRMED / ORACLE_AMBIGUOUS / BLOCKED。
10. artifact_index registers current provenance。
11. local_reverse_training_status remains blocked unless only classification/next_action is updated。
12. git diff --name-status only contains allowed files。
```

---

## 8. Stop Conditions

必须停止并写 `status=BLOCKED` 或 `status=FAILED`，不得写 solved，如果出现任一情况：

```text
1. current static triage / strcmp handoff / previous winpty artifact 缺失或 freshness 不可确认。
2. compare_call_ea 不是 0x40111C，或 static_candidate_text 不是 ippio。
3. 需要运行 CPP2.exe / Cpp2.exe 才能继续。
4. 需要重跑 ippio/jppio runtime validation 才能继续。
5. 需要 solver/bruteforce/symbolic/debugger/hook/emulator 才能继续。
6. 现有 IDA/static extraction 工具不足，且必须新建重复 IDA runner 才能继续。
7. 只能得到 echo-only runtime difference，无法证明 success/reject 分支。
8. 需要修改 .codex-skills 或读取完整 solve_reports/PROJECT_PROGRESS_LOG 才能继续。
9. 任何 artifact 想把 candidate/known_candidate 写成 ippio 或 solved=true。
10. pytest_result.txt 无法对应本 decision_id/report_id/round_id。
11. lint-report 在最终报告写入后仍失败。
```
