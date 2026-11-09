# 一句话启动：交给 Nerelan 完成的执行计划（2026-11-09）

Owner 要求：本阶段目标是"一句话启动"（`ONE_STEP_START_PLAN.md`），主要为了方便、像通用 Agent 工具一样；
剩余工作写成完整计划，由 Nerelan 自己执行，监督者只负责准备、评审和落地。

## 1. 现状

| 步骤 | 内容 | 状态 | 位置 |
|---|---|---|---|
| 1 | Owner 窗口激活前逐任务预选路（修复 #1407 的 REJECT：预选路与启动共用 `GoalService._route_tasks`） | 已完成，未推送 | 本地分支 `claude/one-step-route-preview`（基于 #1407） |
| 2 | 激活前预检 `OwnerWindowAdmission.preflight` + `POST /api/owner-window/preflight` | 已完成，未推送 | `claude/one-step-preflight`（叠在 1 上） |
| 3–4 后端 | 一句话成稿 `POST /api/quick-start/draft` + 三个预设 | 已完成，未推送 | `claude/one-step-quick-start`（叠在 2 上） |
| 5 | 原生对话框确认多目标 Owner 窗口 + `POST /api/owner-window/activate` | 代码草稿，缺测试和文档 | `claude/one-step-native-dialog`（WIP 提交） |
| 3–4 前端、6、7、8 | 见第 3 节 | 未开始 | 交给 Nerelan |

验证：步骤 1–4 的相关测试 116 个通过（`test_owner_window.py`、`test_quick_start.py`、`test_native_owner_dialog.py`），
`test_goal_service.py`、`test_host_atomic_window.py`、`test_native_goal_admission.py`、`test_task_service.py`、
`test_trusted_host*.py` 通过；全量 `tests/platform_v1` 尚未跑完。

Owner 决定（2026-11-09）：确认方式 A+B，对话框由宿主渲染关键边界；预设按方案第 4 节；交互模式默认
OpenCode + `token-sensenova/glm-5.2`。

## 2. 分工原则

- **Nerelan 做**：边界清楚、改动集中、有明确测试的 R1 任务。执行器是免费模型（OpenCode + glm-5.2 等），
  每次尝试 600 秒，所以每个 Issue 只做一件事，写清要改的文件、接口形状和测试。
- **监督者做**：推送并落地已完成的步骤 1–4；步骤 5（扩大授权范围，按 R2 同等审查）；评审 Nerelan 的 Draft PR
  并按 `AGENTS.md` 落地。Nerelan 只开 Draft PR，不合入。
- 理由：步骤 1–4 已写好并测试过，重做浪费额度；步骤 5 改变"谁能证明是 Owner"，不适合交给免费模型首次实现。

## 3. 交给 Nerelan 的 Issue

每条都是一个 `agent_team` 目标、一个 `implement` 任务。共同规则（写入每个 Issue）：不改 `AGENTS.md`、
`docs/agents/**`、`.github/workflows/**`、`landing_review.py`、依赖文件；前端用现有组件和 `ra-*` 样式；
提交前运行指定测试和 `git diff --check`。

### 第一批（互不依赖，前提：步骤 1–4 已合入）

**N1 前端：一句话启动的接口客户端**
- 在 `frontend/src/lib/platform-client.ts` 加 `draftQuickStart({text, repository, preset?})`（`POST /api/quick-start/draft`）
  和 `preflightOwnerWindow(request)`（`POST /api/owner-window/preflight`）；类型放在 `frontend/src/types`
  （或现有 schema 目录），字段与 `docs/owner-window.md`"激活前预检""一句话成稿与预设"两节一致。
- 在 `hooks/use-platform.ts` 加对应的 TanStack Query mutation。
- 测试：Vitest 覆盖请求路径、请求体、错误码透传（`quick_start_issue_not_open:<n>` 等）。

**N2 前端：错误码的中文说明**
- 新建 `frontend/src/lib/start-errors.ts`：把 `owner_selection_confirmation_unavailable`、`owner_window_*`、
  `quick_start_*`、`native_owner_identity_unavailable_or_changed` 等错误码映射成一句中文说明和处理建议；
  未知码原样显示。
- 测试：每个已知码有说明，带参数的码（`:1350`）能解析参数，未知码不丢失。

**N3 窗口结束报告（步骤 7）**
- 新建 `reverse_agent/platform_v1/window_report.py`：给定窗口 ID，只读汇总目标与任务状态、失败分类、
  已开的 Draft PR（从任务记录读取）、按绑定统计的 Token 与耗时、窗口停止原因；输出 dict 和 Markdown。
- 加 `GET /api/windows/<id>/report`（只读）和命令行 `python -m reverse_agent.platform_v1.window_report <id>`。
- 测试：用 `tests/platform_v1/test_unattended_coordinator.py` 的窗口夹具构造完成、失败、`usage_unknown` 三种情况。

**N4 交互模式默认执行器（步骤 8）**
- 前端"新建任务"默认执行器由 `deterministic_fixture` 改为 OpenCode，绑定取 `token-sensenova/glm-5.2`
  对应的绑定（没有该绑定时提示去账户页添加，不静默回退到测试执行器）；表单上标注"此模式需要你在场"。
- 改动集中在 `frontend/src/hooks/use-tasks.ts` 和新建任务的表单组件。
- 测试：默认值、无绑定提示、仍可手动选择其他执行器。

**N5 运行配置随窗口保存（步骤 6）**
- `scripts/windows/Start-NerelanAtLogon.ps1` 支持从任务库目录下的 `run.env.json` 读取环境（现有
  `-EnvFile` 参数保留，优先级更高）；路径一律正斜杠；缺文件时按现状启动。
- 补充 `docs/owner-window.md`"开机恢复"一小节。
- 测试：已有的 PowerShell 测试方式，或在 `tests/` 里用 Python 解析脚本参数的静态测试（参考现有脚本测试）。

### 第二批（依赖 N1、N2；第一批落地后再建目标）

**N6 前端：确认卡片（步骤 4）**
- 新路由 `/start`：显示成稿结果——每个目标的标题与任务、每个任务的预计模型（`preview`）、模型池与未提供项、
  预检逐项结果（失败项显示 N2 的说明）。
- 预设切换（试跑 / 一天 / 一周）和可展开的参数编辑；参数一变就重新预检。
- "开始"按钮：预检全部通过才可点；步骤 5 落地前，按钮旁显示可复制的终端命令
  `python -m reverse_agent.platform_v1.owner_window --goal … --hours … …`（由请求参数生成）。
- 测试：Vitest 组件测试覆盖通过、失败、切换预设三种状态；视觉基线按现有方式补一张。

**N7 前端：首页输入框接入一句话启动（步骤 3 的界面）**
- 首页 `GoalComposer` 提交时调用 `draftQuickStart`，成功后跳到 `/start?goals=…&preset=…`；保留"只建草稿"
  的旧入口作为次要操作。
- 测试：提交、跳转、错误显示。

### 第三批（依赖步骤 5 落地）

**N8 前端："开始"走宿主原生对话框**
- 点"开始"调用 `POST /api/owner-window/activate`，请求期间显示"请在弹出的系统对话框中确认（60 秒内）"；
  成功跳到任务页并显示窗口；拒绝或超时显示 N2 的说明，并保留终端命令作为备用。
- 测试：等待、成功、拒绝、超时四种状态。

## 4. 执行步骤

| # | 谁 | 做什么 | 需要 Owner |
|---|---|---|---|
| 1 | 监督者 | 推送步骤 1–4：步骤 1 更新到 #1407，2 和 3–4 各开一个 Draft PR；独立评审，按 `AGENTS.md` 落地 | 否（已授权开发） |
| 2 | 监督者 | 按第 3 节在 GitHub 建 Issue N1–N8（第二、三批先建，标明依赖） | 是：在仓库里发布 Issue |
| 3 | 监督者 | `F:\nerelan-run` 更新到新的 `main`，重启宿主 | 是：动正在运行的宿主 |
| 4 | 监督者 | 用 `QuickStart.draft` 为第一批 N1–N5 建目标（`agent_team`、试跑或一天预设），先跑预检，结果全部通过；把目标 ID 和参数写进 `Activate-LongRun.ps1` | 否 |
| 5 | Owner | 运行 `Activate-LongRun.ps1`，在终端输入确认码 | 是（只能本人） |
| 6 | Nerelan | 逐个完成第一批，开 Draft PR | — |
| 7 | 监督者 | 评审并落地第一批；失败的写清原因回到 Issue，下一窗口重试 | 否 |
| 8 | 监督者 | 同时完成步骤 5（补测试、文档，R2 同等审查后落地） | 否（Owner 已决定） |
| 9 | 重复 4–7 | 第二批 N6–N7，然后第三批 N8 | 每批一次确认 |

最后一批落地后验收（`ONE_STEP_START_PLAN.md` 第 7 节）：Owner 在首页输入一句话 → 确认卡片 → 系统对话框点"是"，
不打开终端、不写文件，窗口开始运行。

## 5. 风险

- 免费模型可能做不完前端卡片这类较大的任务：N6 失败两次就拆成"展示"和"预设编辑"两个 Issue。
- Nerelan 的任务在同一个窗口里并发 1，没有跨目标依赖排序，所以按批次建窗口，不把有依赖的放进同一批。
- 首个窗口仍要用终端确认码；这正是本阶段要消除的步骤，在 N8 和步骤 5 落地前无法避免。
- 步骤 1–4 还没有独立评审；如果评审要求修改，第一批的目标要等它们落地后再建。
