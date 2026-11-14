# 交接：一步启动阶段与 Nerelan 监督（2026-11-09）

接手的对话先读这一节，再按需读 `AGENTS.md` 和下文链接的文档。

## 0. 一句话现状

当前阶段的目标是**一步启动**：像普通 agent 工具一样，一句话就能交给 Nerelan 无人值守地跑。
对应计划是 `docs/architecture/ONE_STEP_START_NERELAN_RUN.md`。工作方式也变了：

- 由 Claude 写计划、派任务、做监督、评审和落地，Nerelan（运行宿主）负责实现。
- 等系统达到第 5 节的毕业标准后，改为抽查，最后只看告警。

后端链路已经合入 main：预检 → 一句话起草 → 团队模板 → 卡片激活（#1431 正在落地）。
前端卡片（N1、N2、N6–N8）还没做，是第二、三批的任务。

## 1. Owner 决定（2026-11-09，都已生效）

| 主题 | 决定 |
|---|---|
| 预设 | 试跑：2h、并发 1、重试 1、300k token。一天（默认）：24h、1、2、2M。一周：7d、2、2、10M。都只开 Draft PR，付费 API 关闭 |
| 交互模式默认 | OpenCode + `token-sensenova/glm-5.2` |
| 安全姿态 | 不必严防本机其他 agent。默认在 UI 卡片上点"开始"即激活；原生对话框、终端验证码是可选的严格模式（`owner_window_settings.json` 的 `confirmation: "terminal"`）。agent 只有在 Owner 在对话里要求时才可以代为激活，只能用预设边界，并报告窗口 ID 和范围 |
| 预算 | Owner 窗口超出预留时按实际用量计费，窗口继续跑，到上限才停。免费模型的用量不计入上限 |
| 计费事实 | 只有 Codex 和 Claude 付费。workbuddy、trae 用积分，Magpie 每天自动领取，领取后 30 天过期，按 `subscription` 处理，要注意用量和过期时间。Magpie 里没有配置任何付款方式，copilot 和其他计费未知的上游可以用 |
| 基准快照 | 采用 `public-leaderboards@2026-10-20`（digest `731a7e89…`） |
| Issue 整理 | D 类核实后关闭（已关 41 个，见 `docs/architecture/ISSUE_TRIAGE_2026-11-09.md`） |
| 优先级 | 安全不能妨碍使用的方便。先完成主线，安全类工作放到最后（B 类：#384、#372、#447、#388、#380；沙箱和隐私规划：#298、#299、#303、#798、#789、#790） |

`#1372`（如果涉及工作流）仍按 R2 处理。`#118`（自动合并、发布、部署授权）仍需 Owner 单独决定。

## 2. 本阶段已合入的 PR

main 在写这份文档时是 `b6bc3236`。

| PR | 内容 |
|---|---|
| #1406 | 一步启动计划 |
| #1407 | 激活前预览路由：路由不到的 Goal 在询问 Owner 之前就拒绝 |
| #1408 | 未知用量计费 |
| #1409 | `POST /api/owner-window/preflight` |
| #1410 | 一句话起草 `POST /api/quick-start/draft`、预设、限值范围 |
| #1419 | 无密钥网关里带 `/` 的上游模型不算免费 |
| #1420 | Owner 窗口按任务预留；超出时按实际计费并继续；免费路由不计费 |
| #1424 | #1350（第一批 Nerelan 产出） |
| #1425 | Windows 端口独占（`SO_EXCLUSIVEADDRUSE`），两个宿主不能再同时监听 8765/8766 |
| #1430 | 团队模板：实现 + 评审两个任务，从文本推导检查项，Owner 窗口里自动发布 Draft PR |

## 3. 正在落地（交接时）

都已经和 main `b6bc3236` 合并，并拿到了 exact-head 的独立 ACCEPT（评审意见在各 PR 的评论里）。

| PR | 头 | 状态 |
|---|---|---|
| #1426 每账户周配速 | `ae39f8dc` | 落地脚本在跑 |
| #1421 窗口报告（#1413） | `1d03eb9d` | ACCEPT，排在 #1426 后面 |
| #1423 开机读取 run.env.json（#1415） | `2c6630b7` | 第一次被 REJECT（文档写错了），监督者按回退规则改了文档，重审 ACCEPT |
| #1431 卡片激活（R2 等价） | `9040c2fd` | ACCEPT，最后落地 |

**落地顺序很重要。** #1426、#1421、#1423 改的文件互不重叠，先落地它们，merge-main 之后 diff 不变，ACCEPT 可以 carry-over。
#1431 和这三个都有重叠（`task_service.py`、`trusted_host.py`、`docs/owner-window.md`），merge-main 后
diff 的上下文会变，carry-over 大概率失败，需要在新头上再做一次独立评审。

每个 PR 的落地步骤：

1. 落后于 main 就 merge `origin/main` 并推送。
2. 等 `baseline`、`state-gate`、`landing-state-gate` 在 exact head 上全绿。
3. 跑 `python -m reverse_agent.landing_review verdict --repository dddd2024/Nerelan --pr N --head SHA --auth-source gh`。
4. 用 `gh api -X PUT repos/dddd2024/Nerelan/pulls/N/merge -f merge_method=merge -f sha=SHA` 合并。
   `gh pr merge` 在这个仓库会报 "base branch policy prohibits"，即使检查都是绿的。

`landing-state-gate` 报 `no_review_verdict_for_exact_head`，说明 carry-over 不成立。重新做一次独立评审即可，**不要**绕过。

## 4. 运行宿主与长跑

| 项 | 值 |
|---|---|
| 运行宿主 checkout | `F:\nerelan-run`，**仍在 `8a468cbf`（#1408）**，没有包含后面的修复 |
| 运行库 | `F:/nerelan-run-data/tasks.sqlite3`（`REVERSE_AGENT_TASK_DB_DIR`） |
| Owner 配置 | `F:\nerelan-run-config\`：`run.env.json`、`Activate-LongRun.ps1`（里面还是第一批重跑的 goal ID）、`longrun_status.py` 等诊断脚本 |
| 路由覆盖 | `F:/nerelan-run-data/model_routing_overrides.json`：`weekly_pace.require_fresh: true`，81 个 Magpie 模型 `cost_class: free`（workbuddy、trae 不在其中） |
| 绑定 | 143 个 Magpie 模型用 opencode 执行器。`claude/*`、`codex/*`、`auto/*` 和非文本模型**没有**绑定 |
| 进程 | Magpie 在 `127.0.0.1:3425`。宿主在 8765/8766（PID 会变，用 `netstat -ano` 查） |
| 第一批窗口 | `owner-4d2ee88b…`，ACTIVE 到 2026-11-10 09:11Z；任务都已结束，用量约 19.6M token |

第一批结果（6 个 Goal）：

- #1413、#1414、#1415、#1350、#1336 跑到 READY。
- #1336 一个文件都没改，是**假成功**，记为 #1427。
- #1285 超时；升级时选了窗口池外的 `copilot/gpt-6.1-sol`，失败，记为 #1428。
- 宿主当时不会自己发布 PR。监督者手动发了 #1421–#1424，#1430 修复了这个问题。
- 评审结果：#1421、#1423、#1424 ACCEPT（#1423 在新头上先 REJECT，修正后 ACCEPT）；#1422 REJECT，挂在 #1414 上。

## 5. 监督的毕业标准

达到下面全部条件后改为抽查，之后只看告警：

- 连续 3 批，独立评审首次 ACCEPT 率 ≥ 80%，且没有假成功。
- 20 个任务内，系统自评和监督者评审的一致率 ≥ 90%，没有错误的 ACCEPT。
- 没有因平台缺陷导致的窗口停止。
- 没有越界行为（main、密钥、付费 API、池外模型）。

第一批：5/6 到 READY，独立评审 ACCEPT 3/4，有 1 个假成功，有 1 次池外升级，**未达标**。

## 6. 接下来按顺序做

1. **完成第 3 节的落地。** #1431 很可能要在新头上重审。
2. **更新运行宿主。** 先问 Owner：这会动正在运行的宿主，第一批窗口还是 ACTIVE。
   - 把 `F:\nerelan-run` 更新到新的 main 并重启，记得先停旧宿主，#1425 之后两个宿主不能共存。
   - 动 `claude/*`、`codex/*` 之前先确认 Magpie 的实时账户标签。#1426 的评审指出：如果标签是
     `anthropic`、`claude-code` 这类名字而不是 `claude`，在 `require_fresh` 下这些模型会一直被挂起。
     需要的话先做一个小修，用 `magpie_route_provider` 归一化标签。
   - 然后才把这两类模型按 opencode 执行器绑定。
3. **小修 #1430 的非阻塞意见。** `quick_start.checks_from_text` 推导出的测试路径要先经过
   `functional_validation._relative_path_invalid` 校验，免得非法路径留下一个没有计划的 Goal。
4. **第二批**，用 quick_start 团队模板 → 预检 → Owner 在卡片上点"开始"（#1431 合入后可用）：
   - #1411 N1、#1412 N2（前端一句话启动和错误说明）；
   - 重试 #1414、#1285、#1336；
   - 平台缺陷 #1427（零改动判为失败）、#1428（升级不能出池）、#1429（积分配速）；
   - A 类里几个指名了测试的项。
   每批结束后，对照第 5 节写一份监督报告。
5. **第三批**：#1416–#1418（N6–N8，确认卡片和首页入口），#1300、#1298、#1278、#1251。
6. A 类剩余的复核项，C 类按 Owner 的优先级拆分；B 类安全项放在最后。

## 7. 注意事项

- **Windows 换行。** 用 Python 改文件要写 `open(..., newline="")`，否则会把整个文件改成 CRLF，出现几千行的 diff。
- **不要在 `claude/owner-window-ui-activation` 的工作区里提交无关改动。** 那是 #1431 的分支。
- **独立评审**都用一个新的 general-purpose 子代理，看 exact head，在独立的 detached worktree 里跑测试。
  评审意见先写到文件，再由监督者用 `gh pr comment --body-file` 发出去。
  最后一行是 `Nerelan-Review: ACCEPT|REJECT <sha>`。
- **监督者回退。** Nerelan 的 PR 被 REJECT 而修复很小时，监督者可以直接修，但要在 PR 上记录回退，并重新找人独立评审（#1423 就是这么处理的）。
- **R2。** 改到 `AGENTS.md`、`docs/agents/**`、`.github/workflows/**`、`landing_review.py`
  或依赖时，PR 正文要写明对应的 Owner 决定，评审要明确确认没有削弱门禁。
- **相关文档。**
  - `docs/owner-window.md`：预检、一句话起草、卡片激活、开机恢复。
  - `docs/architecture/MULTI_AGENT_ROUTING_PLAN.md`：多 Agent 路由的 A/B/C 三个阶段。
  - `docs/architecture/ISSUE_TRIAGE_2026-11-09.md`：Issue 分类和关闭记录。
