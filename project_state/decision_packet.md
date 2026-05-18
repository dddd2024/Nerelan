# DECISION_PACKET.md

本轮是 Phase 1A + Phase 1D 的返工任务，不推进 `samplereverse` 逆向主线，不进入 Phase 2，也不实现 Phase 1B/1C/1E/1F。

## 1. Goal

修复上一次 Phase 1A + Phase 1D 实现中的状态一致性与归档语义问题，使 `project_state` 的身份锚点和 `archive-round` 结果可以被 GPT/Codex 稳定接力使用。

本轮目标只包括：

1. 修正 `round_manifest.json` 的文件路径语义。
2. 让归档 manifest 同时记录 `source_path` 与 `archived_path`，避免 replay 时混淆当前文件和归档副本。
3. 补充测试，确保 manifest 记录的 `archived_path` 指向 `project_state/rounds/<round_id>/...` 下的归档文件，并且 sha256 与归档副本一致。
4. 更新 `codex_execution_report.md`，明确 Phase 1A + Phase 1D 的实际完成情况、测试结果和仍未完成项。
5. 写入真实测试结果到 `project_state/pytest_result.txt`，再执行 `archive-round`。
6. 重新生成并提交一致的 `project_state` 状态文件。

不要把本轮任务解释为继续追 `0x401b50`、`0x258c`、Base64/RC4、last-writer 或其他逆向主线。

## 2. Current Evidence

上一轮实现已经完成一部分 Phase 1A + Phase 1D 原型：

- `reverse_agent/project_state.py` 已增加：
  - `STATE_SCHEMA_VERSION = 2`
  - `DEFAULT_WORKFLOW_STATUS = "REPORT_AVAILABLE"`
  - `DEFAULT_CURRENT_OWNER = "web_gpt"`
  - `DEFAULT_REVIEW_STATUS = "PENDING_REVIEW"`
  - `STATE_DIGEST_EXCLUDED_KEYS`
  - `_state_digest()`
  - `apply_state_identity()`
- `build_project_state()` 会把 `schema_version`、`state_build_id`、`round_id`、`state_digest` 写入 `current_state.json`，并把 `based_on_state_digest` 写入 `task_packet.json`。
- `archive_round()` 已经能生成 `project_state/rounds/<round_id>/round_manifest.json`。
- `tests/test_project_state.py` 已补充身份字段、digest、round_manifest 和 archive 幂等测试。

但是审查发现当前实现仍有阻断问题：

1. `task_packet.json`、`decision_packet.md`、`codex_execution_report.md` 三者语义不一致。
   - `task_packet.json` 当前指向 `Trace 0x401b50 return, branch, or exception outcome`。
   - 旧 `decision_packet.md` 指向 `compare_real_lhs_provenance_audit` write-monitor 修复。
   - `codex_execution_report.md` 仍描述旧的 observability repair。
2. `current_state.json` 和 `task_packet.json` 混入大量历史 artifact，导致当前状态过度膨胀。
3. `round_manifest.json` 的 `files.*.path` 当前指向 `project_state/current_state.json` 等当前工作区文件，而不是归档副本，replay 语义不清。
4. `round_manifest.json` 的 `source_git_commit` 是生成状态时的 HEAD，而不是提交后的 commit；需要在报告中明确该字段语义，必要时增加 `state_generated_from_git_commit` 命名或说明。
5. `project_state/rounds/<round_id>/pytest_result.txt` 只有占位文本：`No pytest_result.txt was available for this round.`，不能证明本轮测试已运行。

本轮只返工这些问题。

## 3. Do Not Do

不要做以下事情：

- 不要进入 Phase 2。
- 不要实现 `lint-decision`。
- 不要实现 `latest_artifacts_v2` / freshness。
- 不要实现 `decision_meta` / `codex_report_summary`。
- 不要新增 `project_state/schema.md`，除非只做极小文档说明且不影响本轮代码范围。
- 不要修改 `reverse_agent/strategies/compare_aware_search.py`。
- 不要修改 `reverse_agent/olly_scripts/*`。
- 不要运行 Base64/RC4 breakpoint probe。
- 不要回旧 `sample_solver`。
- 不要扩大 beam、topN、budget、timeout、frontier iteration。
- 不要提交完整 `solve_reports/`。
- 不要默认读取完整 `PROJECT_PROGRESS_LOG.txt`。
- 不要把本轮状态重建成新的逆向任务。

## 4. Files To Inspect

优先审计这些文件：

```text
reverse_agent/project_state.py
tests/test_project_state.py
project_state/task_packet.json
project_state/current_state.json
project_state/decision_packet.md
project_state/codex_execution_report.md
project_state/rounds/round_20260518_111005/round_manifest.json
project_state/rounds/round_20260518_111005/pytest_result.txt
```

只在必要时查看：

```text
README.txt
docs/phase1_project_state_stability_plan.md
project_state/artifact_index.json
project_state/negative_results.json
project_state/model_gate.json
```

不要默认读取完整 `solve_reports/` 或完整 `PROJECT_PROGRESS_LOG.txt`。

## 5. Required Audit

实现前必须先审计并在 `codex_execution_report.md` 中说明：

1. `archive_round()` 当前如何选择 `round_id`。
2. `archive_round()` 当前是否先复制文件再写 `round_manifest.json`。
3. `round_manifest.json` 中 `files.*.path` 当前指向的是源文件还是归档副本。
4. `tests/test_project_state.py` 当前为什么没有发现 `path` 语义问题。
5. `source_git_commit` 当前语义是“state 生成时 HEAD”还是“提交后 HEAD”。
6. `project_state/pytest_result.txt` 是否存在；如果不存在，为什么归档中出现占位文本。
7. 当前 `task_packet.json` 为什么会从 Phase 1 架构任务变成 `Trace 0x401b50 return, branch, or exception outcome`。
8. 是否需要在本轮避免重建 `task_packet.json` 为逆向任务；如果必须重建，则要在 `codex_execution_report.md` 中明确说明生成命令、run-name 和产生该任务的原因。

## 6. Implementation Scope

允许修改：

```text
reverse_agent/project_state.py
tests/test_project_state.py
project_state/codex_execution_report.md
project_state/pytest_result.txt
project_state/rounds/<new_round_id>/round_manifest.json
project_state/rounds/<new_round_id>/pytest_result.txt
```

允许重新生成：

```text
project_state/artifact_index.json
project_state/current_state.json
project_state/negative_results.json
project_state/model_gate.json
project_state/task_packet.json
```

但如果重新生成这些状态文件导致当前任务再次跳回逆向主线，必须在报告中说明，并不要把它标记为 Phase 1 完成。

### 6.1 修正 round_manifest 路径语义

将 manifest 中每个文件条目从：

```json
{
  "path": "project_state\\current_state.json",
  "sha256": "..."
}
```

改为类似：

```json
{
  "source_path": "project_state\\current_state.json",
  "archived_path": "project_state\\rounds\\round_20260518_111005\\current_state.json",
  "sha256": "..."
}
```

对于 `git_diff.patch` 和 `pytest_result.txt` 这种只在 round 目录中生成或补充的文件，也应保持一致结构：

```json
{
  "source_path": null,
  "archived_path": "project_state\\rounds\\round_20260518_111005\\git_diff.patch",
  "sha256": "..."
}
```

或者如果实现更简单，也可以保留 `path` 字段但必须让它指向归档副本路径；不过推荐使用 `source_path + archived_path`，语义更清楚。

### 6.2 补充 archive_round 测试

新增或修改测试，确保：

1. `round_manifest["files"][name]["archived_path"]` 指向 `project_state/rounds/<round_id>/<name>`。
2. `archived_path` 文件存在。
3. `sha256` 与 `archived_path` 文件内容一致。
4. 对于源文件类状态文件，`source_path` 指向 `project_state/<name>`。
5. 对于 `git_diff.patch` 和没有源文件的占位/运行结果，`source_path` 可以为 `null` 或按实现约定明确记录。
6. 同一 round 重复归档时，如果 manifest 等价，应返回 `no-op`；如果文件内容变化，应拒绝覆盖。

### 6.3 写入真实 pytest_result

运行测试后，将真实输出写入：

```text
project_state/pytest_result.txt
```

建议命令：

```powershell
python -m py_compile reverse_agent\project_state.py
python -m pytest -q tests\test_project_state.py
```

可接受的 `pytest_result.txt` 至少应包含：

```text
python -m py_compile reverse_agent\project_state.py -> passed
python -m pytest -q tests\test_project_state.py -> <真实结果>
```

然后再运行：

```powershell
python -m reverse_agent.project_state archive-round
```

确保新 round 的 `pytest_result.txt` 不再是占位文本。

### 6.4 更新 codex_execution_report.md

报告必须明确：

- 本轮是 Phase 1A + Phase 1D 返工。
- 已修正 `round_manifest` 路径语义。
- 已补测试。
- 已运行哪些命令，结果是什么。
- 是否重新 build 了 `project_state`。
- 如果 `task_packet.json` 仍然指向逆向任务，要说明这是由当前 `samplereverse` artifact 事实生成的，而不是 Phase 1 架构任务本身。
- Phase 1B/1C/1E/1F 未实现，不得声称 Phase 1 完成。

## 7. Tests

必须运行并记录输出：

```powershell
python -m py_compile reverse_agent\project_state.py
python -m pytest -q tests\test_project_state.py
```

如果本地有 `solve_reports`，再运行：

```powershell
python -m reverse_agent.project_state build --reports-dir solve_reports --sample samplereverse --run-name sr_lhs_last_writer_health_fix_20260518_r3
python -m reverse_agent.project_state status
python -m reverse_agent.project_state archive-round
```

如果本地没有 `solve_reports`，不要伪造完整运行结果；使用测试 fixture 验证即可，并在报告中说明本地缺少运行产物。

## 8. Stop Conditions

遇到以下情况必须停止并报告：

1. 需要大规模重构 `build_artifact_index()` 才能修复本轮问题。
2. 需要修改 `compare_aware_search` 主策略。
3. 需要修改 Olly/Frida/UIA sidecar 脚本。
4. 需要读取完整 `solve_reports/` 才能完成测试。
5. `round_manifest` 新旧结构会破坏现有测试或下游读取方，但无法以兼容方式双写。
6. 无法获得真实 pytest 输出。
7. `task_packet.json`、`decision_packet.md`、`codex_execution_report.md` 无法在本轮保持一致。

## Acceptance Criteria

本轮返工可接受的条件：

1. `round_manifest.json` 的文件路径语义清楚，不再只指向当前工作区源文件。
2. `tests/test_project_state.py` 能验证 manifest 中归档路径存在，并且 sha256 匹配归档副本。
3. `project_state/pytest_result.txt` 或新 round 中的 `pytest_result.txt` 包含真实测试输出。
4. `codex_execution_report.md` 明确说明 Phase 1A + 1D 完成状态和未完成项。
5. 不修改逆向主策略，不引入 Phase 2 内容。
6. 不把 Phase 1B/1C/1E/1F 声称为完成。
