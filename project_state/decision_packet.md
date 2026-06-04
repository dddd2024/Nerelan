```json decision_meta
{
  "schema_version": 1,
  "decision_id": "decision_20260604_fix_local_reverse_inventory_audit_findings_v1",
  "round_id": "round_20260604_fix_local_reverse_inventory_audit_findings_v1",
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

本轮目标是修复上一轮 `local_reverse_metadata_inventory_v1` 的审计问题。上一轮已经建立了本地逆向样本 metadata inventory 的基础，但审计发现 inventory 质量和测试记录存在缺口，不能直接接受。

本轮只做返工修复，不进入样本求解，不生成 candidate，不上传原始样本。

必须完成：

```text
1. 修复 inventory 扫描过滤策略，避免把 IDE 配置、工程配置、缓存文件登记成训练样本。
2. 修复 cases metadata 的 input_value，使后续本地 harness 能通过 LOCAL_REVERSE_ROOT 定位样本。
3. 修复 GitHub-safe inventory 和 project_state inventory 的路径策略，避免不必要的本地绝对路径进入可提交文件。
4. 修正 codex_execution_report.md 中与实际测试数量不一致的问题。
5. 补齐 pytest_result.txt 中缺失的 lint-report、git diff --check、git status --short 记录。
6. 重新生成 inventory、cases 和报告。
```

---

## 2. Current Evidence

上一轮 Codex 报告显示：

```text
1. 已新增 reverse_agent/local_reverse_inventory.py。
2. 已生成 training_materials/local_reverse/inventory.json。
3. 已生成 training_materials/local_reverse/cases/*.json。
4. 已生成 project_state/local_reverse_inventory.json。
5. 报告声称扫描 E:\reverse 得到 72 个条目和 72 个 cases。
```

审计结论为 `REWORK_REQUIRED`，原因如下：

```text
1. training_materials/local_reverse/inventory.json 中出现 .idea/.gitignore、.idea/*.xml、*.iml 等非逆向样本条目，说明扫描结果被工程配置文件污染。
2. pytest_result.txt 未记录 lint-report、git diff --check、git status --short。
3. codex_execution_report.md 声称 test_local_reverse_inventory.py 有 12 个测试，但 pytest_result.txt 记录为 11 passed。
4. cases/*.json 的 input_value 只是相对路径，不含 LOCAL_REVERSE_ROOT，占位策略和 README 描述不一致。
5. project_state/local_reverse_inventory.json 仍包含 samples_root=E:\reverse；这不是原始样本泄露，但应改成更干净的 root hint 策略。
```

当前任务仍由本 `project_state/decision_packet.md` 控制。`task_packet.task` 中的旧 samplereverse 派生任务只是背景，不覆盖本轮。

---

## 3. Do Not Do

严禁：

```text
1. 不上传 E:\reverse 中的原始样本文件。
2. 不复制 E:\reverse 到仓库。
3. 不提交 local_reverse_samples 下的本地内容。
4. 不提交 solve_reports 全量目录。
5. 不运行动态分析、调试或 runtime probe。
6. 不生成 candidate、flag 或 solver result。
7. 不修改 .codex-skills。
8. 不引入数据库、服务端平台或重型工作流系统。
9. 不把单题事实写入长期 skill。
10. 不扩大到 reverse_solving 或 tool_integration 主线。
```

允许：

```text
1. 修改 inventory 过滤逻辑。
2. 修改 cases metadata 生成逻辑。
3. 更新 inventory、cases、README、报告和测试记录。
4. 增加 focused unit tests。
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
tests/test_local_reverse_inventory.py
training_materials/local_reverse/README.md
training_materials/local_reverse/inventory.json
training_materials/local_reverse/cases/
project_state/local_reverse_inventory.json
```

必要时检查：

```text
reverse_agent/local_samples.py
reverse_agent/harness.py
tests/test_local_samples.py
tests/test_project_state.py
.gitignore
README.txt
```

不要默认读取完整历史产物目录或完整进度日志。

---

## 5. Required Audit

Codex 报告必须回答：

```text
1. 过滤策略是否排除了 .idea、.vscode、.git、__pycache__ 等工程目录。
2. 过滤策略是否排除了 .iml、IDE XML、缓存和明显非样本配置文件。
3. 是否仍保留常见逆向样本/附件扩展的 metadata-only 登记能力。
4. GitHub-safe inventory 是否不含本地绝对路径。
5. project_state inventory 是否使用 LOCAL_REVERSE_ROOT 或 root_hint，而不是直接依赖硬编码本机路径。
6. cases metadata 的 input_value 是否与 README 的 LOCAL_REVERSE_ROOT 策略一致。
7. cases metadata 是否仍可被 reverse_agent.harness.load_harness_cases 读取。
8. 是否没有提交原始样本、本地样本目录或完整运行产物目录。
9. 是否没有运行动态分析、调试或 runtime probe。
10. codex_report_summary.based_on_decision_id 是否等于 decision_20260604_fix_local_reverse_inventory_audit_findings_v1。
11. pytest_result.txt 是否记录真实测试命令，并包含 lint-report、git diff --check、git status --short。
12. codex_execution_report.md 中测试数量是否与 pytest_result.txt 一致。
```

---

## 6. Implementation Scope

允许修改：

```text
reverse_agent/local_reverse_inventory.py
tests/test_local_reverse_inventory.py
training_materials/local_reverse/README.md
training_materials/local_reverse/inventory.json
training_materials/local_reverse/cases/*.json
project_state/local_reverse_inventory.json
project_state/codex_execution_report.md
project_state/pytest_result.txt
```

推荐修复方式：

```text
1. 在 local_reverse_inventory.py 中增加默认 exclude_dirs，例如 .idea、.vscode、.git、__pycache__、.pytest_cache。
2. 增加默认 exclude_extensions，例如 .iml、.xml、.log、.tmp、.cache；如果未来确实要登记题目说明文件，应通过显式参数开启。
3. 增加 include_extensions 或 sample_extensions，默认优先纳入 .exe、.dll、.bin、.dat、.elf、.so、.apk、.jar、.class、.zip、.7z、.rar 等样本/附件类型；只保存 metadata，不保存内容。
4. cases input_value 推荐改为 ${LOCAL_REVERSE_ROOT}/<relative_path>。
5. GitHub-safe inventory 使用 samples_root_hint=LOCAL_REVERSE_ROOT。
6. project_state/local_reverse_inventory.json 可记录 samples_root_hint 和 source_root_label，但不要提交真实绝对路径。
7. 更新 README，说明过滤规则和 LOCAL_REVERSE_ROOT 解析策略。
8. 重新生成 inventory 与 cases，确保不再出现 .idea 或 IDE 配置项。
```

如果担心扩展名过滤误删真实题目附件，Codex 应停止并报告 `BLOCKED_NEEDS_SAMPLE_EXTENSION_POLICY`，不要随意丢弃样本。

---

## 7. Tests

必须运行并记录：

```text
python -m py_compile reverse_agent/local_reverse_inventory.py
python -m pytest -q tests/test_local_reverse_inventory.py
python -m pytest -q tests/test_local_samples.py
python -m pytest -q tests/test_project_state.py
python -m reverse_agent.project_state lint-decision --state-dir project_state
python -m reverse_agent.project_state lint-report --state-dir project_state
git diff --check
git status --short
```

测试最低覆盖：

```text
1. tmp_path 中混合真实样本扩展和 .idea/.xml/.iml 时，只登记样本类文件。
2. GitHub-safe inventory 不含本地绝对路径。
3. project_state inventory 使用 root hint，不硬编码 E:\reverse。
4. cases input_value 使用 LOCAL_REVERSE_ROOT 策略。
5. cases metadata 可被 harness loader 读取。
6. 缺失 samples root 时给出清晰错误。
7. README 存在 metadata-only 与过滤策略说明。
```

---

## 8. Stop Conditions

立即停止并报告 `BLOCKED`：

```text
1. 无法确定哪些扩展应算逆向样本，过滤会明显误删训练材料。
2. 修复 cases input_value 需要改 harness.py 才能兼容。
3. GitHub-safe inventory 无法避免本地绝对路径。
4. 需要上传原始样本才能继续。
5. project_state lint 失败且无法小范围修复。
```

完成条件：

```text
1. inventory 过滤后不再登记 .idea、IDE XML、IML 等配置文件。
2. inventory 与 cases 重新生成。
3. README 说明 metadata-only、过滤策略和 LOCAL_REVERSE_ROOT。
4. 测试、lint-report、git diff --check、git status --short 均记录通过。
5. codex_execution_report.md 与 pytest_result.txt 对齐本 decision_id。
6. 未提交任何原始样本。
```
