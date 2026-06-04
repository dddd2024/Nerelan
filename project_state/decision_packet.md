```json decision_meta
{
  "schema_version": 1,
  "decision_id": "decision_20260604_local_reverse_training_status_overlay_v1",
  "round_id": "round_20260604_local_reverse_training_status_overlay_v1",
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

上一轮已经完成 `E:\reverse` 的 metadata-only inventory 返工：样本清单不再写入真实本地路径，`source_root_label` 已改为 `LOCAL_REVERSE_ROOT`，cases 使用 `${LOCAL_REVERSE_ROOT}/<relative_path>`。

本轮目标不是解题，而是生成训练集状态层：

```text
1. 读取 metadata inventory。
2. 读取已有 local_reverse 求解/阻塞结果。
3. 合并出每个样本的 training status。
4. 标记 solved / validated / blocked / inventory_only / needs_triage。
5. 生成下一批优先评估队列。
6. 复用已有 local_reverse_corpus.py 的 triage 能力，不重复造扫描器。
```

必须输出：

```text
project_state/local_reverse_training_status.json
project_state/local_reverse_evaluation_queue.json
training_materials/local_reverse/status_overlay.json
```

本轮不生成 candidate，不运行 solver，不运行 IDA/Ghidra，不运行动态调试。

---

## 2. Current Evidence

当前已有两个相关基础：

```text
1. reverse_agent/local_reverse_inventory.py 负责 metadata-only inventory 和 cases。
2. reverse_agent/local_reverse_corpus.py 已存在，能做本地语料扫描、静态特征提取、triage 标签和 recommended samples。
```

`local_reverse_corpus.py` 已有 triage 标签：

```text
xor / shift / array_compare / strcmp / serial_check / base64 / rc4 / des / aes / hash / packed_or_obfuscated / unknown
```

也已有 `build_training_state()` 和 `recommend_next_samples()`，能够输出训练状态、triage summary 和 recommended next samples。

因此本轮不能再新建第三套 corpus scanner。应整合：

```text
local_reverse_inventory.py 负责 metadata/cases
local_reverse_corpus.py 负责 triage/recommendation
新增或增强的 status overlay 负责 solved/blocked 状态合并
```

已有三个样本状态必须回填：

```text
Cpp1.exe：validated / solved，candidate = hookapi
sha_256.exe：blocked，NO_BOUNDED_HASH_PREIMAGE_DOMAIN
CPP2.exe：blocked 或 needs_solver，transform known，但 candidate 未验证
```

这些状态应来自已有 project_state 文件：

```text
project_state/local_reverse_validated_candidate_handoff.json
project_state/local_reverse_constraint_recovery_result.json
project_state/local_reverse_ida_solver_result.json
```

不能手写到 `.codex-skills/`。

当前任务仍由本 `project_state/decision_packet.md` 控制。`task_packet.task` 中的旧 samplereverse 派生任务只是背景，不覆盖本轮。

---

## 3. Do Not Do

严禁：

```text
1. 不上传 E:\reverse 原始样本。
2. 不复制样本到仓库。
3. 不运行 solver。
4. 不生成 candidate。
5. 不运行 IDA/Ghidra。
6. 不运行动态调试、runtime probe、Frida、OllyDbg、x64dbg。
7. 不新建第三套 corpus scanner。
8. 不把单题结果写入 .codex-skills。
9. 不修改 samplereverse 主线。
10. 不提交 solve_reports 全量目录。
```

允许：

```text
1. 增强 local_reverse_corpus.py 的输出合并能力。
2. 新增轻量 status overlay 模块。
3. 新增 focused tests。
4. 生成 project_state 和 training_materials 下的 metadata/status JSON。
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
reverse_agent/local_reverse_inventory.py
reverse_agent/local_reverse_corpus.py
tests/test_local_reverse_inventory.py
project_state/local_reverse_inventory.json
training_materials/local_reverse/inventory.json
training_materials/local_reverse/cases/
project_state/local_reverse_validated_candidate_handoff.json
project_state/local_reverse_constraint_recovery_result.json
project_state/local_reverse_ida_solver_result.json
```

必要时检查：

```text
project_state/local_reverse_ida_summary.json
project_state/local_reverse_forced_ida_extraction_result.json
tests/test_project_state.py
```

不要默认读取完整：

```text
solve_reports/
PROJECT_PROGRESS_LOG.txt
project_state/rounds/
```

---

## 5. Required Audit

Codex 报告必须回答：

```text
1. 是否复用了 local_reverse_inventory.py。
2. 是否复用了或整合了 local_reverse_corpus.py，而不是新建第三套 scanner。
3. 是否读取了已有 validated/blocked 结果。
4. Cpp1.exe 是否被标记为 solved/validated。
5. sha_256.exe 是否被标记为 blocked: NO_BOUNDED_HASH_PREIMAGE_DOMAIN。
6. CPP2.exe 是否被标记为 blocked 或 needs_solver，且不能声称 solved。
7. 是否生成 local_reverse_training_status.json。
8. 是否生成 local_reverse_evaluation_queue.json。
9. evaluation queue 是否优先选择简单、可静态分析、未 solved 的样本。
10. 是否没有上传原始样本。
11. 是否没有运行动态分析或 solver。
12. pytest_result.txt 是否记录真实测试命令。
13. codex_report_summary.based_on_decision_id 是否等于 decision_20260604_local_reverse_training_status_overlay_v1。
```

---

## 6. Implementation Scope

推荐新增：

```text
reverse_agent/local_reverse_training_status.py
tests/test_local_reverse_training_status.py
```

也可以选择增强：

```text
reverse_agent/local_reverse_corpus.py
```

但必须避免复制 `local_reverse_inventory.py` 的扫描逻辑。

推荐 CLI：

```powershell
python -m reverse_agent.local_reverse_training_status build `
  --inventory project_state\local_reverse_inventory.json `
  --github-inventory training_materials\local_reverse\inventory.json `
  --validated project_state\local_reverse_validated_candidate_handoff.json `
  --constraint-recovery project_state\local_reverse_constraint_recovery_result.json `
  --solver-result project_state\local_reverse_ida_solver_result.json `
  --out project_state\local_reverse_training_status.json `
  --queue-out project_state\local_reverse_evaluation_queue.json `
  --github-status-out training_materials\local_reverse\status_overlay.json
```

`local_reverse_training_status.json` 建议结构：

```json
{
  "schema_version": 1,
  "generated_at": "...",
  "source_inventory": "project_state/local_reverse_inventory.json",
  "sample_count": 29,
  "status_summary": {
    "solved": 1,
    "blocked": 2,
    "needs_triage": 0,
    "inventory_only": 26
  },
  "samples": [
    {
      "sample_id": "...",
      "relative_path": "...",
      "sha256": "...",
      "category": "...",
      "tags": ["local", "reverse"],
      "training_status": "solved|blocked|needs_triage|inventory_only",
      "known_candidate": "",
      "blocked_reason": "",
      "evidence_sources": [],
      "next_action": ""
    }
  ]
}
```

`local_reverse_evaluation_queue.json` 建议结构：

```json
{
  "schema_version": 1,
  "generated_at": "...",
  "queue_policy": "simple_static_first_unsolved_only",
  "items": [
    {
      "rank": 1,
      "sample_id": "...",
      "relative_path": "...",
      "reason": "PE sample with crypto/cipher tag, unsolved, small size",
      "proposed_next_mainline": "tool_integration",
      "allowed_actions": ["static_triage", "IDA evidence extraction if explicitly approved"],
      "forbidden_actions": ["runtime_probe", "bruteforce", "upload_binary"]
    }
  ]
}
```

排序建议：

```text
1. 排除 solved。
2. 排除明显 solver_script/support_file，除非作为辅助材料。
3. 优先小型 PE / source_challenge。
4. 优先 string/xor/shift/array_compare/base64 这类简单静态题。
5. hash 题放后面，除非已有 bounded domain。
6. DES/RC4 等 crypto 题作为第二批。
```

---

## 7. Tests

必须运行并记录：

```text
python -m py_compile reverse_agent/local_reverse_training_status.py
python -m pytest -q tests/test_local_reverse_training_status.py
python -m pytest -q tests/test_local_reverse_inventory.py
python -m pytest -q tests/test_project_state.py
python -m reverse_agent.project_state lint-decision --state-dir project_state
python -m reverse_agent.project_state lint-report --state-dir project_state
git diff --check
git status --short
```

测试最低覆盖：

```text
1. inventory + validated handoff 能合并出 solved Cpp1。
2. blocked constraint recovery 能合并出 sha_256 blocked。
3. CPP2 不能被误标为 solved。
4. inventory_only 样本能进入候选评估队列。
5. solved 样本不会进入 evaluation queue。
6. status_overlay 不含真实本地绝对路径。
7. 没有原始样本内容进入输出 JSON。
```

---

## 8. Stop Conditions

立即停止并报告 `BLOCKED`：

```text
1. 无法可靠匹配 inventory sample_id 与已有 validated/blocked 结果。
2. local_reverse_inventory.py 与 local_reverse_corpus.py 的 sample_id 规则冲突，且不能小范围兼容。
3. 需要运行 solver 或动态验证才能判断状态。
4. 需要读取完整 solve_reports 才能完成合并。
5. 输出会泄露本地绝对路径。
```

完成条件：

```text
1. 生成 local_reverse_training_status.json。
2. 生成 local_reverse_evaluation_queue.json。
3. 生成 training_materials/local_reverse/status_overlay.json。
4. Cpp1 标为 solved/validated。
5. sha_256 标为 blocked。
6. CPP2 不误标 solved。
7. 下一批 evaluation queue 明确。
8. 测试和 lint 记录完整。
```
