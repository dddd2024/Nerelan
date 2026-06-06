```json decision_meta
{
  "schema_version": 1,
  "decision_id": "decision_20260606_cpp2_2f64e68d_console_mature_backend_probe_contract_rework_v1",
  "round_id": "round_20260606_cpp2_2f64e68d_console_mature_backend_probe_contract_rework_v1",
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

目标：修复上一轮 `cpp2_2f64e68d` mature backend availability probe 的 artifact contract mismatch。上一轮功能方向基本正确，确实执行了成熟后端 availability probe，没有运行 `CPP2.exe`，也没有实现完整 ConPTY/Expect/terminal 后端；但实际生成和登记的 artifact 名称为：

```text
project_state/local_reverse_cpp2_2f64e68d_mature_backend_probe.json
artifact key=local_reverse_cpp2_2f64e68d_mature_backend_probe
```

而当前 decision 明确要求：

```text
project_state/local_reverse_cpp2_2f64e68d_console_mature_backend_probe.json
artifact key=local_reverse_cpp2_2f64e68d_console_mature_backend_probe
```

本轮只做 **artifact contract rework**：重命名/重登记 probe artifact，修正 report/pytest。不得重新执行 probe，也不得运行目标样本。

同时修正一个后续风险点：上一轮 probe 代码/报告中不得建议下一轮自研 `ctypes` ConPTY wrapper。Windows ConPTY API presence 只能作为系统能力信号；下一轮如需交互控制台验证，应优先安装或接入成熟 backend（pywinpty/winpty/wexpect），不能因为 API presence 就授权自研完整 backend。

本轮保持上一轮实质结论：

```text
probe_status=BLOCKED_MATURE_BACKEND_MISSING
can_attempt_interactive_console_validation_next=false
known_candidate=""
solved=false
```

---

## 2. Current Evidence

`project_state/task_packet.json` 仍是旧 `samplereverse` advisory，不控制本轮。当前执行权威是本 `project_state/decision_packet.md`。

`project_state/current_state.json` 仍主要是旧 samplereverse 压缩状态，`state_build_id=state_20260602_053948_4e3984041cd7`，`state_digest=4e3984041cd78e5a412e28a53fa3441957ea87f43f62a9688c3e80ca4413678c`。

上一轮提交：

```text
commit=77ceb8f2ba516683039dada6baadffc6a85bec83
message=feat(cpp2): add mature backend availability probe (BLOCKED_MATURE_BACKEND_MISSING)
decision_id=decision_20260606_cpp2_2f64e68d_console_mature_backend_probe_v1
round_id=round_20260606_cpp2_2f64e68d_console_mature_backend_probe_v1
```

上一轮有效事实：

```text
probe_status=BLOCKED_MATURE_BACKEND_MISSING
pywinpty=false
winpty=false
wexpect=false
pexpect=false
conpty_api_available=false
windows_platform=true
executed_target=false
runtime_validated=false
known_candidate=""
solved=false
no_custom_conpty_runner=true
no_expect_state_machine=true
no_terminal_emulator=true
```

上一轮审计失败点：

```text
1. expected path: project_state/local_reverse_cpp2_2f64e68d_console_mature_backend_probe.json
2. actual path:   project_state/local_reverse_cpp2_2f64e68d_mature_backend_probe.json
3. expected key:  local_reverse_cpp2_2f64e68d_console_mature_backend_probe
4. actual key:    local_reverse_cpp2_2f64e68d_mature_backend_probe
```

上一轮 report/pytest 闭合本身通过：

```text
lint-report Exit Code=0
project_state status: decision_consumed_by_report=True, decision_execution_state=CONSUMED_BY_SUCCESS_REPORT
```

但 artifact contract mismatch 仍需返工，不能 ACCEPTED。

当前 `negative_results.json` 仍禁止 old sample_solver blind search、仅扩 beam/budget、compare_semantics_agree=false primary frontier、提交 full solve_reports、无新证据重复 dynamic probe、Base64/RC4 breakpoint probe before lhs producer identification。本轮不触碰这些方向。

---

## 3. Do Not Do

严禁：

```text
1. 不运行 CPP2.exe。
2. 不重新运行 mature backend probe CLI。
3. 不重新运行 pair validator。
4. 不运行 IDA/Ghidra。
5. 不运行 debugger、OllyDbg、Frida hook、emulator、CompareProbe。
6. 不运行 solver、bruteforce、guided pool、symbolic search 或 constraint recovery。
7. 不测试任何 candidate/control 输入。
8. 不修改 project_state/local_reverse_cpp2_2f64e68d_runtime_pair_validation.json。
9. 不修改 project_state/local_reverse_cpp2_2f64e68d_static_triage.json。
10. 不修改 project_state/local_reverse_cpp2_2f64e68d_strcmp_handoff.json。
11. 不修改 project_state/local_reverse_training_status.json。
12. 不修改 project_state/local_reverse_evaluation_queue.json。
13. 不修改 training_materials/local_reverse/status_overlay.json。
14. 不修改 cpp1_7b504c54 的任何 artifact。
15. 不读取 full solve_reports 或 PROJECT_PROGRESS_LOG。
16. 不提交本地 binary、IDA database、raw temp、triage temp dir 或 full solve_reports。
17. 不把 mature backend probe 当作 candidate validation proof。
18. 不写 known_candidate=ippio。
19. 不设置 solved=true。
20. 不实现完整 ConPTY runner。
21. 不实现 Expect-like 状态机。
22. 不实现 terminal emulator。
23. 不新增 pywinpty/wexpect/pexpect 到 requirements 或 pyproject。
24. 不建议因为 ConPTY API presence 就自研完整 ctypes backend。
```

允许：

```text
1. 将 project_state/local_reverse_cpp2_2f64e68d_mature_backend_probe.json 重命名/复制为 project_state/local_reverse_cpp2_2f64e68d_console_mature_backend_probe.json。
2. 删除旧路径 project_state/local_reverse_cpp2_2f64e68d_mature_backend_probe.json，或者保留但从 artifact_index 移除；推荐删除旧路径，避免双 source of truth。
3. 更新 artifact_index.json，将 key 改为 local_reverse_cpp2_2f64e68d_console_mature_backend_probe。
4. 更新 artifact_index latest_artifacts_v2 中 path、sha256、size_bytes、modified_at、source_run。
5. 修改 reverse_agent/local_reverse_console_mature_backend_probe.py 中的 recommended_next_action 文案，移除“thin ctypes wrapper could be used”这类容易授权自研 backend 的表述。
6. 更新 tests/test_local_reverse_console_mature_backend_probe.py 中对应断言。
7. 更新 project_state/codex_execution_report.md 与 project_state/pytest_result.txt。
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
project_state/local_reverse_cpp2_2f64e68d_mature_backend_probe.json
project_state/local_reverse_cpp2_2f64e68d_runtime_pair_validation.json
project_state/local_reverse_cpp2_2f64e68d_strcmp_handoff.json
project_state/local_reverse_cpp2_2f64e68d_static_triage.json
reverse_agent/local_reverse_console_mature_backend_probe.py
tests/test_local_reverse_console_mature_backend_probe.py
.codex-skills/registry.json
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
2. 是否确认 task_packet.task 只是旧 samplereverse advisory。
3. 是否确认本轮主线为 tool_integration。
4. 是否确认本轮是 artifact contract rework，不是重新 probe。
5. 是否确认没有运行 CPP2.exe。
6. 是否确认没有重新运行 mature backend probe CLI。
7. 是否确认没有运行 pair validator。
8. 是否确认没有运行 IDA/Ghidra/debugger/hook/emulator/CompareProbe。
9. 是否确认没有运行 solver/bruteforce/guided pool/symbolic search。
10. 是否确认旧 artifact key/path 已替换为 decision 要求的 console_mature_backend_probe key/path。
11. 是否确认 artifact_index 不再登记 local_reverse_cpp2_2f64e68d_mature_backend_probe。
12. 是否确认 artifact_index 登记 local_reverse_cpp2_2f64e68d_console_mature_backend_probe 且 freshness=current。
13. 是否确认 probe artifact 内容保持 BLOCKED_MATURE_BACKEND_MISSING、known_candidate=""、solved=false。
14. 是否确认 no_custom_conpty_runner/no_expect_state_machine/no_terminal_emulator 仍为 true。
15. 是否确认代码/报告不再建议自研 ctypes ConPTY backend。
16. 是否确认没有修改 runtime_pair_validation/static_triage/strcmp_handoff artifacts。
17. 是否确认没有修改 training status、queue、overlay 或 cpp1 artifacts。
18. 是否确认 codex_report_summary 与本 decision_id/round_id 匹配。
19. 是否确认 pytest_result.txt 使用本 decision_id/report_id/round_id。
20. 是否确认 lint-report Exit Code 0，project_state status 消费当前 success report。
21. 是否确认 git status --short 和 git diff --name-status 只包含允许文件。
```

---

## 6. Implementation Scope

目标 artifact 路径必须为：

```text
project_state/local_reverse_cpp2_2f64e68d_console_mature_backend_probe.json
```

artifact_index 必须使用 key：

```text
local_reverse_cpp2_2f64e68d_console_mature_backend_probe
```

artifact_index latest_artifacts_v2 entry：

```text
kind=local_reverse_console_mature_backend_availability_probe
path=project_state\local_reverse_cpp2_2f64e68d_console_mature_backend_probe.json
freshness=current
source_run=round_20260606_cpp2_2f64e68d_console_mature_backend_probe_contract_rework_v1
sha256=<actual sha256 of renamed artifact>
size_bytes=<actual size>
modified_at=<UTC>
sample_id=cpp2_2f64e68d
```

probe artifact 内容必须保持：

```text
analysis_mode=console_mature_backend_availability_probe
mature_backend_priority=true
probe_status=BLOCKED_MATURE_BACKEND_MISSING
can_attempt_interactive_console_validation_next=false
executed_target=false
runtime_validated=false
known_candidate=""
solved=false
no_custom_conpty_runner=true
no_expect_state_machine=true
no_terminal_emulator=true
```

代码文案修正要求：

```text
如果 conpty_api_available=true 且 pywinpty/winpty/wexpect 都缺失，recommended_next_action 不能写“implement/use thin ctypes wrapper”。
应写："ConPTY API is present, but no mature Python backend is installed. Prefer adding/using a mature backend such as pywinpty or wexpect in a separate dependency decision before interactive validation."
```

允许修改：

```text
project_state/local_reverse_cpp2_2f64e68d_console_mature_backend_probe.json
project_state/local_reverse_cpp2_2f64e68d_mature_backend_probe.json  # delete or replace only
project_state/artifact_index.json
reverse_agent/local_reverse_console_mature_backend_probe.py
tests/test_local_reverse_console_mature_backend_probe.py
project_state/codex_execution_report.md
project_state/pytest_result.txt
```

不得修改：

```text
project_state/local_reverse_cpp2_2f64e68d_runtime_pair_validation.json
project_state/local_reverse_cpp2_2f64e68d_strcmp_handoff.json
project_state/local_reverse_cpp2_2f64e68d_static_triage.json
project_state/local_reverse_training_status.json
project_state/local_reverse_evaluation_queue.json
training_materials/local_reverse/status_overlay.json
project_state/local_reverse_cpp1_7b504c54_*.json
reverse_agent/local_reverse_console_pair_validator.py
reverse_agent/local_reverse_direct_strcmp_handoff.py
reverse_agent/local_reverse_single_sample_static_triage.py
reverse_agent/tool_runners.py
reverse_agent/ida_scripts/collect_evidence.py
reverse_agent/olly_scripts/*
.codex-skills/*
solve_reports/*
project_state/triage_*
requirements.txt
requirements-dev.txt
pyproject.toml
```

---

## 7. Tests

必须运行并记录：

```bash
python -m reverse_agent.project_state lint-decision --state-dir project_state
python -m py_compile reverse_agent/local_reverse_console_mature_backend_probe.py
python -m pytest -q tests/test_local_reverse_console_mature_backend_probe.py
python - <<'PY'
import json
from pathlib import Path
probe_path=Path('project_state/local_reverse_cpp2_2f64e68d_console_mature_backend_probe.json')
old_path=Path('project_state/local_reverse_cpp2_2f64e68d_mature_backend_probe.json')
assert probe_path.exists()
assert not old_path.exists()
probe=json.loads(probe_path.read_text(encoding='utf-8'))
index=json.loads(Path('project_state/artifact_index.json').read_text(encoding='utf-8'))
assert probe['schema_version']==1
assert probe['sample_id']=='cpp2_2f64e68d'
assert probe['analysis_mode']=='console_mature_backend_availability_probe'
assert probe['mainline']=='tool_integration'
assert probe['mature_backend_priority'] is True
assert probe['probe_status']=='BLOCKED_MATURE_BACKEND_MISSING'
assert probe['can_attempt_interactive_console_validation_next'] is False
assert probe['executed_target'] is False
assert probe['runtime_validated'] is False
assert probe['known_candidate']==''
assert probe['solved'] is False
assert probe['no_custom_conpty_runner'] is True
assert probe['no_expect_state_machine'] is True
assert probe['no_terminal_emulator'] is True
assert 'local_reverse_cpp2_2f64e68d_mature_backend_probe' not in index['latest_artifacts']
assert 'local_reverse_cpp2_2f64e68d_mature_backend_probe' not in index['latest_artifacts_v2']
assert index['latest_artifacts']['local_reverse_cpp2_2f64e68d_console_mature_backend_probe']=='project_state\\local_reverse_cpp2_2f64e68d_console_mature_backend_probe.json'
entry=index['latest_artifacts_v2']['local_reverse_cpp2_2f64e68d_console_mature_backend_probe']
assert entry['freshness']=='current'
assert entry['kind']=='local_reverse_console_mature_backend_availability_probe'
assert entry['sample_id']=='cpp2_2f64e68d'
assert entry['source_run']=='round_20260606_cpp2_2f64e68d_console_mature_backend_probe_contract_rework_v1'
print('cpp2 mature backend probe contract rework consistency OK')
PY
python -m pytest -q tests/test_project_state.py
python -m reverse_agent.project_state lint-report --state-dir project_state
python -m reverse_agent.project_state status --state-dir project_state
git diff --check
git status --short
git diff --name-status
```

`pytest_result.txt` 必须包含每条命令原文、Exit Code、输出摘要、PASSED/FAILED/BLOCKED 结果，以及本轮 decision_id、round_id、report_id。

---

## 8. Stop Conditions

立即停止并报告 `BLOCKED` 或 `REWORK_REQUIRED`：

```text
1. 旧 probe artifact 缺失且没有可迁移内容。
2. 迁移后 probe artifact 不再保持 BLOCKED_MATURE_BACKEND_MISSING / solved=false。
3. artifact_index 同时保留旧 key 和新 key。
4. 需要运行 CPP2.exe 才能继续。
5. 需要重新运行 mature backend probe CLI 才能继续。
6. 需要运行 pair validator、IDA/Ghidra、debugger/hook/emulator/CompareProbe 才能继续。
7. 需要修改 runtime/static/source artifacts、训练状态、队列、overlay 或 cpp1 artifacts 才能继续。
8. 需要新增 dependencies 才能继续。
9. 代码仍建议自研 ctypes ConPTY backend。
10. lint-report 或 project_state status 无法闭合。
11. git diff 包含 forbidden files。
```

成功完成的最低标准：

```text
1. probe artifact 路径与 key 完全匹配 decision contract。
2. 旧 mature_backend_probe key/path 不再作为 current artifact 登记。
3. probe 实质结论保持 BLOCKED_MATURE_BACKEND_MISSING。
4. 不运行目标、不重新探测、不验证 candidate。
5. 不修改 runtime/static/source artifacts、训练状态、队列、overlay 或依赖文件。
6. 不再建议自研 ctypes ConPTY backend。
7. report/pytest_result 与本 decision_id/round_id 匹配。
8. 所有测试与 git 检查真实记录。
```
