```json decision_meta
{
  "schema_version": 1,
  "decision_id": "decision_20260531_local_sample_single_solver_round",
  "round_id": "round_20260531_local_sample_single_solver_round",
  "based_on_state_build_id": "state_20260527_153028_1d6dd81ecbd6",
  "based_on_state_digest": "1d6dd81ecbd615598f7b0fda09f1e859a4cba6a0d28b45711434e174ba6b5e02",
  "status": "APPROVED",
  "mainline": "engineering_branch",
  "skill_profiles": [
    "reverse-agent-iteration@v2"
  ]
}
```

# DECISION_PACKET

本轮属于 **engineering_branch**。目标是基于 `local_reverse_samples/` 中已经登记的一个真实逆向题目，完成一次 **单样本 solver 闭环**。

本轮不是继续改 `local_samples add/solve` 基础设施，也不是推进旧 `samplereverse` 主线。当前 `task_packet.task` / `derived_task` 仍然是旧 `samplereverse` 状态派生建议，不能作为本轮执行权威。本轮以本文件 `project_state/decision_packet.md` 为准。

## 1. Goal

从本地已登记样本中选择一个 case，写出该题的本地 solver：

```text
local_reverse_samples/<case_id>/
  sample.exe 或 sample.<ext>
  case.json
  metadata.json
  notes.md
  codex_task.md
  solver.py          # 本轮生成，但不得提交 GitHub
  solve_result.json  # 本轮可生成，但不得提交 GitHub
```

本轮目标：

```text
1. 在本地选择一个已登记样本 case_id。
2. 读取该样本的 metadata.json / case.json / notes.md / codex_task.md。
3. 静态分析 sample 文件，识别题目类型。
4. 在 local_reverse_samples/<case_id>/solver.py 中实现该题专用 solver。
5. 运行 solver.py，得到候选 flag / password / serial。
6. 将验证结果写入 local_reverse_samples/<case_id>/solve_result.json。
7. 在 project_state/codex_execution_report.md 中只总结方法、分类和结果，不提交样本、solver.py 或 solve_result.json。
```

本轮允许 Codex 真正读取本地样本文件的字节内容做静态分析，但 **默认不执行未知 exe**。

## 2. Current Evidence

上一轮已经完成并接受：

```text
previous_decision_id = decision_20260531_local_sample_intake_solve_bootstrap
previous_report_id = report_20260531_local_sample_intake_solve_bootstrap
previous_status = SUCCESS / ACCEPTED
```

上一轮已新增能力：

```text
1. reverse_agent/local_samples.py 已新增。
2. python -m reverse_agent.local_samples add <file> 可自动生成 case.json。
3. python -m reverse_agent.local_samples solve <case_id> 可生成 codex_task.md。
4. solve 默认不运行 IDA/Olly/Frida/runtime probe。
5. local_reverse_samples/ 内容不会进入 Git。
```

当前 `.gitignore` 已包含：

```text
local_reverse_samples/
```

当前 `project_state/pytest_result.txt` 已记录上一轮测试通过：

```text
python -m py_compile reverse_agent/local_samples.py
python -m pytest -q tests/test_local_samples.py
python -m pytest -q tests/test_harness.py
python -m reverse_agent.project_state lint-decision --state-dir project_state
python -m reverse_agent.project_state lint-report --state-dir project_state
git diff --check
git status --short
git check-ignore -v local_reverse_samples/
```

当前 `task_packet.task` / `derived_task` 仍然是旧 `samplereverse` 状态派生建议：

```text
task = Diagnose bounded compare hook path reachability
derived_task = Diagnose bounded compare hook path reachability
```

这些不是本轮执行任务。本轮由本 `decision_packet.md` 控制。

当前 skill profiles：

```text
reverse-agent-iteration@v2
```

不使用：

```text
samplereverse-frontier@v2
```

原因：本轮不推进 `samplereverse` 样本，不涉及 candidate、frontier、runtime evidence 或 artifact freshness 推进。

## 3. Do Not Do

严禁：

```text
1. 不提交 local_reverse_samples/ 下任何内容。
2. 不提交 sample.exe / .dll / .bin / .zip / .7z / .rar。
3. 不提交 solver.py。
4. 不提交 solve_result.json。
5. 不执行未知 sample.exe。
6. 不运行 IDA/Olly/Frida runtime probe。
7. 不运行 Base64/RC4 breakpoint probe。
8. 不运行 samplereverse harness。
9. 不修改 CompareAwareSearchStrategy。
10. 不修改 reverse_agent/profiles/samplereverse.py。
11. 不修改 .codex-skills/。
12. 不读取完整 solve_reports/。
13. 不读取完整 PROJECT_PROGRESS_LOG.txt。
14. 不把本地样本内容写入 project_state。
15. 不把单题 solver 泛化成项目策略，除非本轮只做建议、不改代码。
```

特别限制：

```text
本轮可以读 sample 文件做静态分析；
本轮默认不能直接运行 sample.exe。
如果必须动态运行样本才能继续，应停止并报告 BLOCKED，等待用户确认是否在 VM / 沙箱中执行。
```

## 4. Files To Inspect

默认读取：

```text
project_state/task_packet.json
project_state/current_state.json
project_state/artifact_index.json
project_state/negative_results.json
project_state/codex_execution_report.md
project_state/decision_packet.md
project_state/pytest_result.txt
```

必须本地检查：

```text
local_reverse_samples/
local_reverse_samples/*/metadata.json
local_reverse_samples/*/case.json
local_reverse_samples/*/codex_task.md
local_reverse_samples/*/notes.md
```

选中一个样本后必须检查：

```text
local_reverse_samples/<case_id>/sample.*
local_reverse_samples/<case_id>/metadata.json
local_reverse_samples/<case_id>/case.json
local_reverse_samples/<case_id>/codex_task.md
local_reverse_samples/<case_id>/notes.md
```

允许新增但不得提交：

```text
local_reverse_samples/<case_id>/solver.py
local_reverse_samples/<case_id>/solve_result.json
local_reverse_samples/<case_id>/analysis_notes.md
```

允许修改并提交：

```text
project_state/codex_execution_report.md
project_state/pytest_result.txt
```

不应修改：

```text
reverse_agent/local_samples.py
tests/test_local_samples.py
reverse_agent/harness.py
reverse_agent/strategies/compare_aware_search.py
.codex-skills/
```

如果发现上一轮工具有阻断性 bug，先报告 `BLOCKED`，不要把本轮扩大成基础设施修复。

## 5. Required Audit

Codex 报告必须回答：

```text
1. 本轮选择了哪个 case_id。
2. 选择依据是什么：
   - 如果用户通过 LOCAL_REVERSE_CASE_ID 指定，则使用该 case；
   - 否则选择 local_reverse_samples/ 下最近修改且包含 codex_task.md 的 case。
3. 样本文件路径是什么。
4. 样本 sha256 / size_bytes 是多少。
5. 题目初步分类是什么：
   - string_compare
   - hash_check
   - xor_or_bitshift
   - base64_or_encoding
   - rc4_or_stream_cipher
   - aes_or_des
   - seh_or_exception
   - gui_check
   - unknown
6. 静态分析依据是什么：
   - strings
   - imports
   - constants
   - compare pattern
   - hash constants
   - crypto table
   - byte transform loop
   - packed/obfuscated indicator
7. 是否生成 solver.py。
8. solver.py 的输入输出约定是什么。
9. 是否运行 solver.py。
10. solver.py 输出了什么候选结果。
11. 是否生成 solve_result.json。
12. 是否没有执行 sample.exe。
13. 是否没有运行 runtime probe。
14. 是否没有提交 local_reverse_samples/ 内容。
15. 是否没有修改 .codex-skills/。
16. 是否没有修改 samplereverse 主线。
17. 如果发现可复用模式，应写入 Next Suggested Task，而不是直接修改项目策略。
```

## 6. Implementation Scope

本轮执行流程：

### 6.1 选择样本

优先规则：

```powershell
$env:LOCAL_REVERSE_CASE_ID
```

如果用户或环境显式指定 `LOCAL_REVERSE_CASE_ID`，必须使用该 case。

如果没有指定，则 Codex 本地执行：

```powershell
Get-ChildItem .\local_reverse_samples -Directory |
  Where-Object { Test-Path "$($_.FullName)\codex_task.md" } |
  Sort-Object LastWriteTime -Descending |
  Select-Object -First 1
```

如果没有任何可用 case，停止并报告：

```text
BLOCKED: no registered local sample with codex_task.md
```

### 6.2 静态分析样本

允许执行类似如下的本地静态读取：

```powershell
python - <<'PY'
from pathlib import Path
p = Path(r"local_reverse_samples/<case_id>/sample.exe")
data = p.read_bytes()
print(len(data))
print(data[:64].hex())
PY
```

允许做：

```text
1. 提取 ASCII / UTF-16LE 字符串。
2. 搜索 flag、key、password、serial、wrong、correct、success、fail 等提示。
3. 搜索 hash 常量、Base64 字符表、RC4 S-box 初始化模式、XOR/rotate 常见循环。
4. 检查 PE imports。
5. 检查明显壳/压缩痕迹。
6. 根据静态证据写 analysis_notes.md。
```

不允许默认执行：

```text
sample.exe
OllyDbg
IDA runtime
Frida
动态断点
网络访问
```

### 6.3 写 solver.py

`solver.py` 必须是单题本地 solver，放在：

```text
local_reverse_samples/<case_id>/solver.py
```

要求：

```text
1. 不依赖项目外部重型库。
2. 优先纯 Python。
3. 必须有 main()。
4. 必须打印候选 flag/password/serial。
5. 如果只能部分还原，应输出 partial result 和 unknown reason。
6. 不写入 Git tracked 路径。
7. 不读取 project_state 作为输入。
```

推荐结构：

```python
from __future__ import annotations


def solve() -> str:
    # TODO: implement per-sample transform reversal
    return ""


def main() -> None:
    result = solve()
    print(result)


if __name__ == "__main__":
    main()
```

### 6.4 运行 solver.py

允许运行：

```powershell
python .\local_reverse_samples\<case_id>\solver.py
```

运行后写：

```text
local_reverse_samples/<case_id>/solve_result.json
```

格式：

```json
{
  "case_id": "<case_id>",
  "status": "SOLVED | PARTIAL | BLOCKED",
  "candidate": "<candidate>",
  "confidence": "high | medium | low",
  "evidence": [
    "static strings matched",
    "hash matched",
    "transform reversed"
  ],
  "sample_executed": false,
  "runtime_probe_used": false
}
```

### 6.5 报告项目状态

更新：

```text
project_state/codex_execution_report.md
project_state/pytest_result.txt
```

报告中只允许写摘要，不要粘贴样本大段字节、完整反汇编或本地私有文件内容。

允许写：

```text
case_id
sha256
size_bytes
classification
solver status
candidate result
reusable pattern suggestion
tests/commands ran
```

不允许写：

```text
完整样本内容
完整 solver.py 内容
本地绝对敏感路径
完整反汇编 dump
```

## 7. Tests

必须运行：

```text
python .\local_reverse_samples\<case_id>\solver.py
git status --short
git check-ignore -v local_reverse_samples/
python -m reverse_agent.project_state lint-decision --state-dir project_state
python -m reverse_agent.project_state lint-report --state-dir project_state
git diff --check
```

如果修改了 `project_state/codex_execution_report.md` 和 `pytest_result.txt`，必须确认：

```text
python -m reverse_agent.project_state lint-report --state-dir project_state
```

通过。

不要求运行：

```text
python -m pytest -q
python -m pytest -q tests/test_local_samples.py
真实 sample.exe
IDA/Olly/Frida runtime probe
samplereverse harness
```

如果 solver.py 需要第三方库，必须先停止并说明原因，不要直接引入新依赖。

## 8. Stop Conditions

立即停止并报告 `BLOCKED`：

```text
1. local_reverse_samples/ 不存在。
2. 找不到任何包含 metadata.json / case.json / codex_task.md 的 case。
3. 选中的 case 缺少 sample 文件。
4. sample 文件明显不是可分析的本地题目附件。
5. solver 必须执行 sample.exe 才能继续。
6. solver 必须使用 IDA/Olly/Frida runtime probe 才能继续。
7. solver 必须联网或下载外部资源。
8. 需要修改 reverse_agent/harness.py 或 local_samples.py 才能继续。
9. lint-report 无法通过且原因不是本轮可安全修复的问题。
```

完成条件：

```text
1. 选中一个真实本地 case。
2. 完成静态分析记录。
3. 生成 local_reverse_samples/<case_id>/solver.py。
4. 成功运行 solver.py。
5. 生成 solve_result.json。
6. project_state/codex_execution_report.md 记录本轮摘要。
7. project_state/pytest_result.txt 记录真实命令。
8. local_reverse_samples/ 内容仍未进入 Git。
9. 未执行未知 sample.exe。
10. 未运行 runtime probe。
```

下一轮如果这个 solver 成功，再做 **能力抽象**：把本题中可复用的模式，例如 SHA/MD5 识别、XOR/位移还原、Base64/RC4 组合、SEH 异常跳转等，提炼成项目级 detector 或 solver 模板。
