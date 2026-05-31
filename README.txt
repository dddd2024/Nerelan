Reverse Agent（GUI 逆向解题助手）

这是一个面向 CTF / RE 场景的 Windows GUI 逆向解题助手，目标是把静态分析、动态调试、模型辅助候选收敛、运行时验证和结构化证据报告整合成一个可复现的解题工作流。

当前项目不只是单次运行的 GUI 工具，还包含两条重要工程主线：

1. 批量 Harness：用于对样本集做可复现实验、可恢复重跑、样本级结果记录和聚合统计。
2. GPT + Codex 协作流：使用 `project_state/` 作为低 token、可提交到 GitHub 的状态接口，让网页端 GPT 负责决策审查，Codex 负责本地代码审计、实现、测试和状态归档。

当前重点样本是 `samplereverse`。截至 `project_state` 最新状态，主线仍是 `CompareAwareSearchStrategy` + `L15(prefix8)`；当前瓶颈位于 `compare_real_lhs_provenance_audit`，最新任务是改进 compare LHS last-writer instrumentation，并通过下一轮 bounded rerun 刷新 `write_monitor_health` 证据。


核心能力

- 输入：本地文件路径或 URL。
- 模式：自动判断 / 静态分析 / 动态调试。
- 模型：Copilot CLI 或 OpenAI 兼容接口。
- 工具链：IDA 自动化、OllyDbg / Frida / UIA 相关脚本自动化、可选 angr。
- 验证：支持 stdin 校验与 GUI（pywinauto）窗口级校验。
- 样本增强：`samplereverse` 已迁入 profile 主线，并使用 compare-aware search、runtime compare validation、bounded runtime sidecar audit。
- 输出：`solve_reports\` 下生成运行产物、证据报告、harness run 结果和工具 artifact。
- 低 token 协作：`project_state\` 下生成轻量状态文件，供 GPT / Codex 多轮接力使用。


项目结构

- `app.py`：程序入口。
- `launch_reverse_agent.bat`：Windows 启动脚本。
- `reverse_agent\gui.py`：GUI 主逻辑。
- `reverse_agent\pipeline.py`：主流程编排，包括证据采集、候选生成、验证和报告输出。
- `reverse_agent\harness.py`：批量评测 harness，支持 JSON 任务集、稳定 run name、config digest、case result、summary、resume 和 fail-fast。
- `reverse_agent\project_state.py`：GPT + Codex 协作状态构建器，负责从 `solve_reports` 压缩出 `project_state`，并支持 round archive / context pack。
- `reverse_agent\models.py`：Copilot CLI / 本地模型调用封装。
- `reverse_agent\tool_runners.py`：IDA / Olly / angr 等工具调用封装。
- `reverse_agent\profiles\samplereverse.py`：`samplereverse` profile 入口。
- `reverse_agent\strategies\compare_aware_search.py`：`samplereverse` 当前主策略，包含 compare-aware search 与多轮 bounded runtime audit。
- `reverse_agent\olly_scripts\`：OllyDbg / Frida / UIA 相关动态探针脚本入口。
- `reverse_agent\sample_solver.py`：`samplereverse` 旧专项搜索与回退 checkpoint；当前不应作为主线盲搜入口。
- `reverse_agent\reporter.py`：报告生成。
- `tests\`：pytest 测试集，重点覆盖 harness、project_state、compare-aware strategy 和 bounded audit schema / gate。
- `project_state\`：GPT 与 Codex 的轻量协作接口，应提交到 GitHub。
- `PROJECT_PROGRESS_LOG.txt`：人工总账，仅在状态包缺失、战略复盘或追溯历史失败方向时读取，不是每轮默认上下文。
- `solve_reports\`：运行产物目录，默认不应提交到 GitHub。
- `local_reverse_samples\`：本地逆向训练样本目录，用于放置用户自己的 `.exe`、`.dll`、题目附件、压缩包、notes、harness `case.json` 和本地 `solver.py`。该目录被 `.gitignore` 忽略，不上传 GitHub；适合保存版权不明确、体积较大、可能包含恶意逻辑或仅限本地使用的逆向例题。


快速开始

1) 安装依赖

`pip install -r requirements.txt`

2) 启动 GUI

`launch_reverse_agent.bat`

或：

`python app.py`

3) 可选：创建桌面快捷方式

`powershell -ExecutionPolicy Bypass -File .\create_desktop_shortcut.ps1`

4) 可选：安装高级求解依赖

`pip install angr`


批量 Harness

Harness 的目标是把 reverse-agent 作为可复现实验系统运行，而不是只依赖一次 GUI 手工尝试。

1) 本地导入单个逆向题目：

```powershell
python -m reverse_agent.local_samples add .\crackme.exe --case-id crackme_sha256_001
```

该命令会在被 Git 忽略的 `local_reverse_samples\crackme_sha256_001\` 下自动复制样本并生成：

```text
sample.exe
case.json
metadata.json
notes.md
```

不需要手写 `case.json`。如果省略 `--case-id`，命令会根据文件名和 SHA-256 前缀生成安全稳定的 case id。

2) 生成本地 Codex 解题入口：

```powershell
python -m reverse_agent.local_samples solve crackme_sha256_001
```

该命令会生成：

```text
local_reverse_samples\crackme_sha256_001\codex_task.md
```

`codex_task.md` 会说明样本路径、SHA-256、静态 harness 命令、后续本地 `solver.py` 输出位置，以及默认不要运行 IDA / OllyDbg / Frida runtime probe。后续单题 `solver.py` 应继续保存在 `local_reverse_samples\<case_id>\` 下，不提交 GitHub。

如果只想在生成任务时顺便运行现有静态 harness，可显式使用：

```powershell
python -m reverse_agent.local_samples solve crackme_sha256_001 --run-static-harness
```

3) 高级用法：手写 JSON 任务集，例如：

```json
{
  "cases": [
    {
      "case_id": "sample-local",
      "input_value": "E:\\samples\\sample.exe",
      "expected_flag": "flag{demo}",
      "category": "smoke",
      "tags": ["smoke", "gui"]
    }
  ]
}
```

手写任务集也可以引用被 Git 忽略的 `local_reverse_samples\`，例如：

```json
{
  "cases": [
    {
      "case_id": "crackme-sha256-001",
      "input_value": "local_reverse_samples/crackme_sha256_001/sample.exe",
      "expected_flag": "",
      "category": "hash_check",
      "tags": ["sha256", "static", "crackme"],
      "notes": "本地 SHA-256 判断类逆向练习样本"
    }
  ]
}
```

对应运行命令：

```powershell
python -m reverse_agent.harness --dataset .\local_reverse_samples\crackme_sha256_001\case.json --run-name crackme_sha256_001
```

4) 运行可复现实验：

`python -m reverse_agent.harness --dataset .\cases.json --run-name smoke_suite --analysis-mode "Static Analysis"`

5) 常用运行参数：

- `--run-name`：稳定运行名；同名重跑用于 resume。
- `--reports-dir`：报告根目录，默认 `solve_reports`。
- `--analysis-mode`：`Auto` / `Static Analysis` / `Dynamic Debug`。
- `--model-type`：`Copilot CLI` / `Local Model`。
- `--runtime-validation-enabled`：启用运行时验证。
- `--tool-enabled`、`--ida-enabled`、`--olly-enabled`：启用外部工具链。
- `--case-id`：只运行指定 case，可重复传入。
- `--tag`：只运行带指定标签的 case，可重复传入。
- `--limit`：限制运行样本数。
- `--fail-fast`：遇到失败立即停止。
- `--no-resume`：禁用断点续跑。

6) 结果目录：

- `solve_reports\harness_runs\<run_name>\run_manifest.json`：本次运行配置、git commit、dataset digest、config digest、case 列表。
- `solve_reports\harness_runs\<run_name>\case_results\*.json`：每个样本单独结果。
- `solve_reports\harness_runs\<run_name>\summary.json`：聚合统计。
- `solve_reports\harness_runs\<run_name>\summary.md`：人工可读汇总。
- `solve_reports\harness_runs\<run_name>\reports\`：本轮 pipeline 生成的报告和工具 artifact。

7) 断点续跑规则：

- 对同一个 `--run-name` 再次执行时，默认跳过已有 `case_results\*.json` 的样本。
- 如果同名 run 的 config digest 不一致，harness 会拒绝继续，避免把不同实验混在同一个 run 下。
- 若要做新实验，应使用新的 `--run-name`。


GPT + Codex 协作流

这是当前项目的主要长期协作模式。网页端 GPT 是决策手，Codex 是执行手，GitHub 仓库和 `project_state/` 是事实来源。

标准流程：

1) Codex 在本地生成低 token 状态文件：

`python -m reverse_agent.project_state build --reports-dir solve_reports --sample samplereverse`

必要时绑定具体 harness run：

`python -m reverse_agent.project_state build --reports-dir solve_reports --sample samplereverse --run-name <run_name>`

2) Codex 提交并推送轻量状态目录：

- `project_state\task_packet.json`
- `project_state\current_state.json`
- `project_state\artifact_index.json`
- `project_state\negative_results.json`
- `project_state\model_gate.json`
- `project_state\decision_packet.md`
- `project_state\codex_execution_report.md`
- `project_state\rounds\.gitkeep`

不要提交完整 `solve_reports\`。

3) 网页端 GPT 每轮优先读取：

- `project_state\task_packet.json`
- `project_state\current_state.json`
- `project_state\artifact_index.json`
- `project_state\negative_results.json`
- `project_state\codex_execution_report.md`

`PROJECT_PROGRESS_LOG.txt` 不是每轮默认上下文；只有在 `task_packet` 缺失、`context_level=3`、需要战略复盘、或需要追溯历史失败方向时再读取。

4) GPT 生成或更新：

`project_state\decision_packet.md`

DECISION_PACKET 固定包含：

1. Goal
2. Current Evidence
3. Do Not Do
4. Files To Inspect
5. Required Audit
6. Implementation Scope
7. Tests
8. Stop Conditions

5) Codex 读取 `decision_packet.md`，审计本地代码，做最小实现并运行测试。

6) Codex 写入执行报告：

`project_state\codex_execution_report.md`

报告应至少包含：

- Summary
- Files Changed
- Audit Result
- Implementation
- Tests
- Generated State Files
- Problems / Uncertainty
- Next Suggested Task

7) Codex 归档本轮状态：

`python -m reverse_agent.project_state archive-round`

8) 如需给 GPT 上传紧凑上下文包：

`python -m reverse_agent.project_state pack --out gpt_context_pack.zip`


project_state 文件说明

- `task_packet.json`：给 GPT 的当前任务包，包含 active strategy、artifact refs、current best、current bottleneck、do_not_do、model_gate 和 relevant files。
- `current_state.json`：当前样本压缩状态，包含主线、已知 transform、best candidates、最新 audit 摘要、function semantics 和当前瓶颈。
- `artifact_index.json`：从 `solve_reports` 抽取出的 artifact 索引，记录 latest harness run、latest summary、latest case results、latest artifacts、recent artifacts 和 missing 状态。
- `negative_results.json`：失败方向和禁止重复方向缓存，包含 hard block / soft block、证据 artifact、override 规则。
- `model_gate.json`：是否需要调用模型、上下文等级和原因。
- `decision_packet.md`：GPT 给 Codex 的下一轮任务。
- `codex_execution_report.md`：Codex 执行结果和下一步建议。
- `rounds/`：历史轮次归档目录。


当前 samplereverse 状态（截至 2026-05-18 project_state）

当前事实来源：`project_state/task_packet.json`、`current_state.json`、`artifact_index.json`、`negative_results.json`、`codex_execution_report.md`。

- active strategy：`CompareAwareSearchStrategy`
- profile：`samplereverse`
- current mainline：`L15(prefix8)`
- known transform：`input -> UTF-16LE -> Base64 -> RC4 -> compare flag{ prefix`
- current bottleneck：`compare_real_lhs_provenance_audit`
- current bottleneck reason：`instrumentation_incomplete`
- current task：`Improve compare lhs last-writer instrumentation`
- latest indexed harness run：`sr_lhs_last_writer_health_20260518_r2`
- latest indexed core artifact：`compare_real_lhs_provenance_audit.json`
- current best exact2 candidate：`78d540b49c59077041414141414141`
- current best exact2 runtime score：exact2 / distance5 `246`
- current best exact1/frontier candidate：`5a3e7f46ddd474d041414141414141`
- frontier score：exact1 / distance5 `258`

最新 Codex 报告中的关键结论：

- 已实现 `compare_real_lhs_provenance_audit` 的 observability repair。
- 新增 `write_monitor_health`，用于区分 collector / Stalker / write decoding 失效和真实 writer 缺失。
- 当前不应运行 Base64/RC4 probe，不应回到旧 `sample_solver`，不应扩 beam、topN、budget、timeout 或 frontier iteration。
- 下一步应只 bounded rerun `compare_real_lhs_provenance_audit` 路径，以刷新带 `write_monitor_health` 的运行时证据。
- `breakpoint_probe_allowed` 仍应保持 `false`，除非最终证明 actual arg0-intersecting writer 同时满足：连接到真实 compare arg0、candidate-dependent、并且 transform-material backed。


当前禁止重复方向

以下方向由 `negative_results.json` 维护，默认不得重复：

- 不回到旧 `sample_solver` 盲搜。
- 不只扩大 guided pool beam / budget。
- 不把 `compare_semantics_agree=false` 候选作为主 frontier。
- 不提交完整 `solve_reports\`。
- 不重复 exact2 basin value-pool 已验证集合。
- 不重复 H1/H3 fixed 8-candidate prefix8 + Base64 boundary contrast set。
- 不在没有新 runtime evidence 时重复 transform trace consistency audit。
- 不在确认 Base64/RC4 instruction hook 前重跑 Base64/RC4 breakpoint probe。
- 不忽略 compare return-site audit 已给出的 classification 而重复跑同一 hook set。
- 不在没有新增 instruction-level evidence 时重复 producer material confirmation。
- 不把 `0x4019e0`、`0x401b50`、`0x4018cd`、`0x401be3` 当成 Base64/RC4 material producer，除非有新的语义证据。
- 不在没有 real-lhs provenance evidence 时复用旧 `[ebp-0x1170]`。
- 不在 real lhs producer identification 前运行 Base64/RC4 breakpoint probe。


常用配置

Copilot CLI 推荐模板（Windows）：

- `gh copilot -p "{prompt}" --allow-all-tools --allow-all-paths -s`
- `copilot -p "{prompt}" --allow-all-tools --allow-all-paths -s`
- `github-copilot-cli -p "{prompt}" --allow-all-tools --allow-all-paths -s`

`samplereverse` 相关环境变量：

- `REVERSE_AGENT_SAMPLE_MAX_ATTEMPTS`：默认 `250000`
- `REVERSE_AGENT_SAMPLE_MAX_SECONDS`：默认 `21600`
- `REVERSE_AGENT_SAMPLE_RANDOM_SEED`：默认 `1337`
- `REVERSE_AGENT_SAMPLE_ENABLE_Z3`：如设为 `1` / `true`，启用样本专用 Z3 分区探测


测试建议

常用快速检查：

`python -m py_compile reverse_agent\strategies\compare_aware_search.py reverse_agent\project_state.py`

重点测试：

`python -m pytest -q tests\test_compare_aware_search_strategy.py tests\test_project_state.py`

全量测试：

`python -m pytest -q`

最近记录：

- 2026-05-18：`tests\test_compare_aware_search_strategy.py tests\test_project_state.py` -> `204 passed`
- 2026-05-17：全量 `python -m pytest -q` -> `272 passed`

注意：README 中的测试数字来自最近提交的 `project_state/codex_execution_report.md`，不是实时 CI 状态。新一轮修改后应以本地重新运行结果为准。


排障建议

1) IDA 未执行：检查 IDA 路径、脚本路径、样本路径和权限。
2) Copilot CLI 超时：使用非交互模板，并提高 GUI 或 harness 中的 timeout。
3) Olly / Frida / UIA 探针未执行：确认动态模式、Olly 路径、脚本入口、样本窗口状态和 artifact 输出 JSON 约定。
4) 未安装 angr：会自动跳过，不影响基础流程。
5) harness 同名 run 拒绝继续：检查 config digest 是否变化；如配置变化，应使用新的 `--run-name`。
6) GPT 上下文过大：优先读取 `project_state/`，不要默认读取完整 `solve_reports/` 或完整 `PROJECT_PROGRESS_LOG.txt`。
7) 下一步计划不确定：先让 Codex 重新执行 `python -m reverse_agent.project_state build`，不要凭空基于旧 README 或旧进度制定计划。


Git 与 artifact 约定

应提交：

- 源代码
- 测试
- `project_state\*.json`
- `project_state\*.md`
- `project_state\rounds\.gitkeep`
- 必要的小型文档

默认不应提交：

- `solve_reports\`
- 本地样本二进制
- API key / `.env`
- 大型运行日志
- 本地 IDE 缓存

提交前建议：

1. 运行相关测试。
2. 重新生成 `project_state`。
3. 检查 `negative_results.json` 是否阻止了重复方向。
4. 检查 `codex_execution_report.md` 是否说明了本轮改动、测试和不确定性。
5. 只提交轻量状态和必要代码，不提交完整运行产物。


当前推荐下一步

从最新状态看，下一轮不应扩大搜索，也不应回到 Base64/RC4 probe。推荐任务是：

1. 只 rerun bounded `compare_real_lhs_provenance_audit` path。
2. 使用新导出的 `write_monitor_health` 字段判断：
   - Stalker 是否启用；
   - followed thread 数量是否合理；
   - raw write count 是否为 0；
   - ring buffer 是否溢出；
   - decode failures 是否异常；
   - filtered / intersecting write count 是否真正为 0。
3. 若 raw writes 为 0 或 collector health 异常，先修 instrumentation；不要解释为真实 writer 不存在。
4. 若 raw writes 存在但不 intersect actual compare arg0，再进入更窄的 writer source / address range 审计。
5. 只有当真实 arg0 writer 被 runtime-backed 连接，并且 candidate-dependent transform material 证据闭合时，才允许重新考虑后续 material / Base64 / RC4 probe。
