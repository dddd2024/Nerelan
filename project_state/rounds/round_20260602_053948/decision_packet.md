```json decision_meta
{
  "schema_version": 1,
  "decision_id": "decision_20260606_cpp2_2f64e68d_training_status_blocked_overlay_v1",
  "round_id": "round_20260606_cpp2_2f64e68d_training_status_blocked_overlay_v1",
  "based_on_state_build_id": "state_20260602_053948_4e3984041cd7",
  "based_on_state_digest": "4e3984041cd78e5a412e28a53fa3441957ea87f43f62a9688c3e80ca4413678c",
  "status": "APPROVED",
  "mainline": "training_dataset",
  "skill_profiles": [
    "reverse-agent-iteration@v2"
  ]
}
```

# DECISION_PACKET

## 1. Goal

本轮主线是 **training_dataset**。

目标：修复本地训练集状态同步的一个证据消费缺口：`cpp2_2f64e68d` 已有 current 静态提取、runtime pair validation 和 mature backend probe 证据，但 `project_state/local_reverse_training_status.json` 仍把该样本列为 `inventory_only`。本轮只允许把这种“已静态提取候选、运行验证结果为 AMBIGUOUS_OUTPUT、成熟交互后端缺失”的样本同步为 **blocked**，并从待评估队列中移除；不得把 `ippio` 标记为已验证 candidate，也不得运行样本。

预期结果：

```text
cpp2_2f64e68d.training_status = blocked
cpp2_2f64e68d.known_candidate = ""
cpp2_2f64e68d.blocked_reason 来源于 current runtime/probe evidence，例如 AMBIGUOUS_OUTPUT 或 BLOCKED_MATURE_BACKEND_MISSING
cpp2_2f64e68d 不再作为 inventory_only 出现在 evaluation_queue
```

本轮是训练集状态/overlay 修复，不做新的逆向求解、不做 runtime validation、不接入新交互后端。

---

## 2. Current Evidence

`project_state/task_packet.json` 仍是旧 `samplereverse` advisory，不控制本轮。它包含旧任务 `Review bounded window discovery diagnostics`，同时明确：

```text
active_decision_packet=project_state/decision_packet.md
execution_scope=decision_packet_controls_current_round
local_reverse_task_packet_authority_note=Advisory only; project_state/decision_packet.md remains the execution authority.
```

当前 `project_state/current_state.json` 仍主要是旧 samplereverse 压缩状态：

```text
state_build_id=state_20260602_053948_4e3984041cd7
state_digest=4e3984041cd78e5a412e28a53fa3441957ea87f43f62a9688c3e80ca4413678c
```

上一轮 `decision_20260606_cpp2_2f64e68d_console_backend_test_safety_minimal_archive_closeout_v1` 已审计 ACCEPTED，active report 显示：

```text
status=SUCCESS
acceptance_recommendation=ACCEPTED
round_manifest_present=True
archive_status=archived
pytest_result_status=PASSED
```

CPP2 当前 artifact freshness：

```text
local_reverse_cpp2_2f64e68d_static_triage: current
  path=project_state\local_reverse_cpp2_2f64e68d_static_triage.json
  source_run=round_20260606_cpp2_2f64e68d_static_triage_schema_rework_v1

local_reverse_cpp2_2f64e68d_strcmp_handoff: current
  path=project_state\local_reverse_cpp2_2f64e68d_strcmp_handoff.json
  source_run=round_20260606_cpp2_2f64e68d_direct_strcmp_handoff_v1

local_reverse_cpp2_2f64e68d_runtime_pair_validation: current
  path=project_state\local_reverse_cpp2_2f64e68d_runtime_pair_validation.json
  source_run=round_20260606_cpp2_2f64e68d_runtime_pair_validation_v1

local_reverse_cpp2_2f64e68d_console_mature_backend_probe: current
  path=project_state\local_reverse_cpp2_2f64e68d_console_mature_backend_probe.json
  source_run=round_20260606_cpp2_2f64e68d_console_mature_backend_probe_contract_rework_v1
```

CPP2 direct strcmp handoff evidence：

```text
sample_id=cpp2_2f64e68d
source_tool=IDA
executed_sample=false
static_only=true
runtime_validated=false
compare_call_ea=0x40111C
compare_callee=_strcmp
static_candidate_text=ippio
status=READY_FOR_RUNTIME_VALIDATION
recommended_next_action=Static direct-strcmp candidate extracted. Runtime validation is required before marking solved.
```

CPP2 runtime pair validation evidence：

```text
candidate_input=ippio
negative_control_input=jppio
executed_sample=true
runtime_validated=false
validation_status=AMBIGUOUS_OUTPUT
outputs_differ=false
candidate_accepted=false
control_rejected=false
candidate=null
known_candidate=""
solved=false
blocked_reason=AMBIGUOUS_OUTPUT
failure_reason=Candidate and negative control produced identical stdout, stderr, and return code. Cannot conservatively determine acceptance/rejection.
```

CPP2 mature backend probe evidence：

```text
probe_status=BLOCKED_MATURE_BACKEND_MISSING
can_attempt_interactive_console_validation_next=false
executed_target=false
runtime_validated=false
candidate=null
known_candidate=""
solved=false
blocked_reason=Windows platform but no mature backend available (pywinpty/winpty/wexpect/ConPTY API)
no_custom_conpty_runner=true
no_expect_state_machine=true
no_terminal_emulator=true
```

当前 training status 证据：

```text
project_state/local_reverse_training_status.json generated_at=2026-06-06T05:22:23Z
status_summary solved=2 blocked=4 inventory_only=23
cpp2_2f64e68d.training_status=inventory_only
cpp2_2f64e68d.known_candidate=""
cpp2_2f64e68d.blocked_reason=""
cpp2_2f64e68d.next_action=static triage and manual evaluation required
```

这说明 training status 生成时间早于 CPP2 current validation/probe artifacts，且现有 overlay 没有消费 `AMBIGUOUS_OUTPUT` / `BLOCKED_MATURE_BACKEND_MISSING` 这类 current blocked evidence。

已有相关能力：

```text
reverse_agent/local_reverse_training_status.py 已能读取 inventory、validated handoff、constraint recovery、IDA solver result、artifact_index。
_build_runtime_validation_overlay 目前只把 VALIDATED_SUCCESS / runtime_validated / solved / known_candidate 的 runtime artifact 标记为 solved。
_build_static_handoff_overlay 只接受 static_only + status=BLOCKED 的静态 blocked artifact。
tests/test_local_reverse_training_status.py 已覆盖 solved runtime overlay、非 success 不误标 solved、static blocked overlay、队列过滤和无真实本地路径输出。
```

`negative_results.json` 仍主要约束旧 samplereverse 方向。本轮不得触碰这些方向，尤其不得运行 solver/bruteforce/guided pool、不得提交 solve_reports、不得把 stale artifact 当 current。

是否允许运行工具：

```text
允许运行纯 Python 单元测试、project_state lint/status、training status metadata-only CLI。
不允许运行 CPP2.exe 或任何真实 binary target。
不允许运行 console pair validator CLI、mature backend probe CLI、IDA/Ghidra/debugger/hook/emulator/CompareProbe/solver。
不允许新增 pywinpty/wexpect/pexpect/ConPTY runner 或任何重型依赖。
```

是否允许读取重型 artifact：

```text
不允许默认读取完整 solve_reports 或 PROJECT_PROGRESS_LOG。
不允许读取 project_state/rounds 全量历史。
只允许读取与 cpp2_2f64e68d current artifact、training status、artifact_index、相关源码/测试直接相关的小文件。
```

---

## 3. Do Not Do

严禁：

```text
1. 不运行 CPP2.exe。
2. 不运行任何真实 binary target。
3. 不运行 console pair validator CLI。
4. 不运行 mature backend probe CLI。
5. 不运行任何真实 candidate/control 输入。
6. 不访问 E:\reverse、D:\reverse、C:\reverse、F:\reverse、~/reverse 或 LOCAL_REVERSE_ROOT/REVERSE_ROOT 指向的真实样本路径，除非只是保留 metadata 中已有 relative_path。
7. 不运行 IDA/Ghidra。
8. 不运行 debugger、OllyDbg、Frida hook、emulator、CompareProbe。
9. 不运行 solver、bruteforce、guided pool、symbolic search 或 constraint recovery。
10. 不把 `ippio` 写成 known_candidate、candidate、solved candidate 或 flag。
11. 不把 `AMBIGUOUS_OUTPUT` 当成 runtime_validated。
12. 不把 mature backend 缺失改造成自研 ConPTY/Expect/terminal emulator。
13. 不新增 pywinpty、wexpect、pexpect 或其他 runtime 依赖。
14. 不修改 sample binary、训练样本目录或 solve_reports。
15. 不提交完整 solve_reports。
16. 不修改 `.codex-skills/*`。
17. 不读取完整 PROJECT_PROGRESS_LOG.txt。
18. 不修改与 training status overlay 无关的 solver、IDA runner、validator、mature backend probe 实现。
```

允许：

```text
1. 最小修改 reverse_agent/local_reverse_training_status.py。
2. 最小修改 tests/test_local_reverse_training_status.py。
3. 重新生成 project_state/local_reverse_training_status.json。
4. 重新生成 project_state/local_reverse_evaluation_queue.json。
5. 重新生成 training_materials/local_reverse/status_overlay.json。
6. 新建 project_state/local_reverse_cpp2_2f64e68d_training_status_sync.json，作为本轮同步小 artifact。
7. 更新 project_state/artifact_index.json，为本轮 training status sync artifact 登记 current provenance。
8. 更新 project_state/codex_execution_report.md 和 project_state/pytest_result.txt。
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
reverse_agent/local_reverse_training_status.py
tests/test_local_reverse_training_status.py
project_state/local_reverse_training_status.json
project_state/local_reverse_evaluation_queue.json
training_materials/local_reverse/status_overlay.json
project_state/local_reverse_cpp2_2f64e68d_static_triage.json
project_state/local_reverse_cpp2_2f64e68d_strcmp_handoff.json
project_state/local_reverse_cpp2_2f64e68d_runtime_pair_validation.json
project_state/local_reverse_cpp2_2f64e68d_console_mature_backend_probe.json
```

必要时读取：

```text
training_materials/local_reverse/inventory.json
project_state/local_reverse_inventory.json
reverse_agent/project_state.py
```

不要默认读取：

```text
solve_reports/ 全量
PROJECT_PROGRESS_LOG.txt 全量
project_state/rounds/ 全量历史
本地 E:\reverse 样本目录
```

---

## 5. Required Audit

Codex 报告必须回答：

```text
1. 是否确认当前 decision_packet 是本轮唯一执行权威。
2. 是否确认 task_packet.task 只是旧 samplereverse advisory。
3. 是否确认本轮主线为 training_dataset。
4. 是否确认上一轮 minimal archive closeout 已 SUCCESS/ACCEPTED/PASSED/archived。
5. 是否确认 cpp2_2f64e68d 四个 source artifacts 均为 current。
6. 是否确认 direct strcmp candidate ippio 仍只是 static candidate，不是 validated known_candidate。
7. 是否确认 AMBIGUOUS_OUTPUT 被同步为 blocked，而不是 solved。
8. 是否确认 BLOCKED_MATURE_BACKEND_MISSING 被同步为 blocked，并优先解释当前 validation blocker。
9. 是否确认 cpp2_2f64e68d 不再是 inventory_only。
10. 是否确认 cpp2_2f64e68d 不再进入 evaluation_queue。
11. 是否确认 generated status/overlay 不含 E:\reverse、D:\reverse、C:\reverse、F:\reverse 或其他绝对本地样本路径。
12. 是否确认没有运行 CPP2.exe 或任何真实 target。
13. 是否确认没有运行 pair validator CLI/runtime validation。
14. 是否确认没有运行 mature backend probe CLI。
15. 是否确认没有运行 IDA/Ghidra/debugger/hook/emulator/CompareProbe/solver。
16. 是否确认没有修改 .codex-skills、solve_reports 或无关 solver/validator/probe 代码。
17. 是否确认 codex_report_summary 与本 decision_id/round_id 匹配。
18. 是否确认 pytest_result.txt 使用本 decision_id/report_id/round_id。
19. 是否确认 lint-decision、相关 pytest、lint-report/status 结果真实记录。
20. 是否确认 git status --short 和 git diff --name-status 只包含允许文件。
```

---

## 6. Implementation Scope

小步实现，不跨主线扩张。

建议实现方式：

```text
1. 在 reverse_agent/local_reverse_training_status.py 中新增或重构 runtime/probe status overlay，不破坏现有 _build_runtime_validation_overlay 成功路径。
2. 对 current runtime validation artifacts：
   - VALIDATED_SUCCESS + runtime_validated=true + solved=true + known_candidate 非空 => solved，保持现有行为。
   - AMBIGUOUS_OUTPUT / VALIDATED_FAILURE / BLOCKED 且 solved=false => blocked，blocked_reason 使用 artifact.blocked_reason、failure_reason 或 validation_status。
   - 对 blocked/ambiguous artifact 不输出 known_candidate。
3. 对 current mature backend availability probe artifacts：
   - probe_status=BLOCKED_MATURE_BACKEND_MISSING 或 can_attempt_interactive_console_validation_next=false 且 solved=false => blocked。
   - evidence_sources 应包含 console_mature_backend_probe / mature_backend_missing / source:<artifact file>。
   - 若同一样本同时有 ambiguous runtime pair validation 和 mature backend blocked probe，优先保留 mature backend blocked 作为当前 next_action/blocker。
4. 在 build_training_status 合并逻辑中，允许 overlay 返回 training_status=blocked 或 solved；不要再假定 runtime overlay 命中必然 solved。
5. 增加 tests/test_local_reverse_training_status.py 用例：
   - AMBIGUOUS_OUTPUT runtime pair artifact marks sample blocked, not solved, known_candidate empty。
   - BLOCKED_MATURE_BACKEND_MISSING probe marks sample blocked。
   - mature backend blocked priority overrides ambiguous runtime blocked for same sample。
   - validated success still marks solved，防止回归。
6. 运行 metadata-only training status CLI 重新生成 status/queue/github overlay。
7. 写入 project_state/local_reverse_cpp2_2f64e68d_training_status_sync.json，至少包含：
   - schema_version
   - sample_id=cpp2_2f64e68d
   - mainline=training_dataset
   - source_artifacts
   - source_artifact_freshness=current
   - training_status=blocked
   - known_candidate=""
   - blocked_reason
   - candidate_was_static_only=true
   - runtime_validated=false
   - solved=false
   - executed_target=false for this sync artifact
8. 更新 project_state/artifact_index.json 的 latest_artifacts/latest_artifacts_v2，登记 local_reverse_cpp2_2f64e68d_training_status_sync 为 current。
```

不得修改：

```text
reverse_agent/local_reverse_console_pair_validator.py
reverse_agent/local_reverse_console_mature_backend_probe.py
任何 IDA/Ghidra runner
任何 solver
.codex-skills/*
solve_reports/*
```

---

## 7. Tests

必须运行并记录：

```text
python -m py_compile reverse_agent/local_reverse_training_status.py
python -m pytest -q tests/test_local_reverse_training_status.py
python -m pytest -q tests/test_project_state.py
python -m reverse_agent.local_reverse_training_status --inventory project_state/local_reverse_inventory.json --out project_state/local_reverse_training_status.json --queue-out project_state/local_reverse_evaluation_queue.json --github-status-out training_materials/local_reverse/status_overlay.json
python -m reverse_agent.project_state lint-decision --state-dir project_state
python -m reverse_agent.project_state lint-report --state-dir project_state
python -m reverse_agent.project_state status --state-dir project_state
git diff --check
git status --short
git diff --name-status
```

必须做内容断言并在报告中写明：

```text
1. project_state/local_reverse_training_status.json 中 cpp2_2f64e68d.training_status == blocked。
2. project_state/local_reverse_training_status.json 中 cpp2_2f64e68d.known_candidate == ""。
3. project_state/local_reverse_evaluation_queue.json 不包含 cpp2_2f64e68d。
4. training_materials/local_reverse/status_overlay.json 不包含 E:\reverse / D:\reverse / C:\reverse / F:\reverse。
5. project_state/local_reverse_cpp2_2f64e68d_training_status_sync.json 存在并记录 source_artifact_freshness=current。
```

如果 `project_state/local_reverse_inventory.json` 在当前 checkout 中缺失，可改用 `training_materials/local_reverse/inventory.json`，但必须在报告中说明，不得扫描本地 E:\reverse。

---

## 8. Stop Conditions

必须停止并写 `status=BLOCKED` 或 `status=FAILED`，不得写 SUCCESS/ACCEPTED，如果出现任一情况：

```text
1. 任一 cpp2_2f64e68d source artifact 缺失、stale 或无法读取。
2. 需要运行 CPP2.exe、pair validator CLI、mature backend probe CLI、IDA/Ghidra/debugger/hook/emulator/solver 才能继续。
3. 代码改动会把 ippio 标记为 known_candidate、candidate、solved 或 flag。
4. AMBIGUOUS_OUTPUT 被误分类为 solved。
5. 生成的 GitHub-safe overlay 出现本地绝对路径。
6. 需要新增 pywinpty/wexpect/pexpect 或自研 ConPTY/Expect/terminal emulator。
7. pytest、py_compile、lint-decision、lint-report 或 status 任一失败且无法在本轮范围内最小修复。
8. artifact_index 更新需要重建完整 solve_reports 或读取重型历史目录。
9. 修改范围超出本 decision 的 Implementation Scope。
```
