# 交接：上手改动落地、部署、第一次委派运行暴露的问题（2026-11-11 下午）

接着 [`2026-11-11-first-use-and-run-host-handoff.md`](2026-11-11-first-use-and-run-host-handoff.md)（上午的交接）写。
上午那份的第 3、5 节里列的 PR 状态已经过时，以本文为准。时间均为 UTC，写于 16:00Z 左右。
"未做"和"未验证"都如实标出。

## 1. 现在的状态（一句话）

`main` 在 `935437c0`，运行主机已部署到这个版本、空闲；委派窗口 `owner-90df24b9…` 的 9 次启动已用完；
四个平台缺陷里两个已修复上线，另外两个和两个委派任务还开着（第 5 节）。

## 2. 本次合入 main 的 PR

每个都经过独立评审（不同会话的子代理，按 exact head 发 `Nerelan-Review` 判定），
`baseline`、`state-gate`、`landing-state-gate` 全绿，合并前跑了 `landing_review verdict`。

| PR | 内容 | 作者 | 备注 |
|---|---|---|---|
| #1456 | 一键确认"本机登录就是 Magpie 里的这个账号" | Codex CLI | |
| #1450 | 状态和失败代码显示成中文说明 | Codex CLI | 监督者改了 3 个 e2e 断言 |
| #1448 | README 先讲怎么跑通第一个任务 | Codex CLI | |
| #1452 | 装了任意一个受支持的 Agent CLI 即可启动 | Codex CLI | |
| #1451 | 下任务时自动选执行方式和模型 | Codex CLI | 监督者修了：仓库显示两次；机器人评审发现审批页对未固定绑定的团队目标禁用"生成计划/批准/启动"（P1） |
| #1444 | 评审走本机无密钥网关；评审者高一档 | Claude | 机器人评审发现环境代理会把评审 diff 送出本机（P2），改为不走代理的 `http_safe.urlopen_direct` |
| #1454 | 首页显示无人值守运行是否在推进 | Codex CLI | 监督者改了：停滞判断用 `unfinished_tasks` 而不是 `max_tasks`；用 #1450 的公共文案；只按 `active_window` 判断运行中；机器人评审发现改绑窗口后把旧窗口事件算成进展（P2），改为按本窗口的预算预留时间截断 |
| #1461 | 学会执行器报的"无权使用该模型"并同档改路由（#1460 第 1、2 条） | Claude | |
| #1463 | README 与 #1447/#1451/#1452 一致（#1457） | **Nerelan 自己** | 第一次评审 REJECT（留了一句错误的"保持 opencode 在 PATH"），监督者删掉这一句后通过 |
| #1466 | Codex 单行超过 256 KiB 时丢弃该行而不是让整轮失败（#1465） | Claude | 两轮评审 + 机器人评审：丢掉的若是最终回复则失败；丢掉的命令项若可能是工具启动失败则失败 |

**规律：** `chatgpt-codex-connector` 机器人在每次推送后发 P1/P2 评审线程，未解决的线程会挡住合并。
这次它提的 5 条全是真问题，要读、要修，不要直接点"已解决"。

## 3. 运行主机

- `F:\nerelan-run` 在 `935437c0`（分离头），15:50Z 重启。方式：`dev-down.ps1`，`git checkout --detach origin/main`，
  `scripts\windows\Start-NerelanAtLogon.ps1 -EnvFile F:\nerelan-run-config\run.env.json -NoBrowser`。
  依赖文件这次没有变化，没有跑 `npm ci`。
- 12:59Z 那次部署（到 `a19a48ed`）也是同样的方式。两次都是 Owner 当场同意的。
- **Magpie 账号关联：** Owner 说已在界面确认，但两条原生连接的 `account_ref` 实际都没写进去（原因未查；可能点到了别的主机，或请求静默失败）。
  监督者按 Owner 对 Codex 的确认，调用了同一个接口：
  `POST http://127.0.0.1:8765/api/connections/chatgpt-account/link-magpie-account`，body `{"account_ref":"c38efd6a74a2"}`。
  已写入 `F:\nerelan-run-data\model_setup_state.json`，重启后仍在。之后选路确实用上了 Codex。
  **Claude 账号（`dd0832f93b53`）没有关联**：Owner 没确认过 Claude 是同一个账号。
- 读主机状态的办法：任务 API（8766）要启动器的客户端会话；直接只读打开
  `file:F:/nerelan-run-data/tasks.sqlite3?mode=ro`。Model Control（8765）不检查会话。

## 4. 第一次委派运行：发生了什么

Owner 的要求："有些任务可以分配给系统完成，顺便从它的执行中看到问题。"

- 开了三个 Issue：#1457（README）、#1458（执行器探测）、#1459（目标详情页的选路预测缓存）。
- 用 `supervisor_requests` 起草、预检、激活（`day` 预设：24 小时、最多 9 个任务、8000 万 token、只开 Draft PR）。
  窗口 `owner-90df24b96fae1c681e03bfeb3e0bd733`，13:01Z 激活，2026-11-12 13:01Z 到期。
- 13:01–13:35Z 用完 9 次启动，记了 4116 万 token（大部分是失败启动的预留，见 #1460）。

| 时间 | 任务 | 绑定 | 结果 |
|---|---|---|---|
| 13:01 | #1457 | copilot kimi-k3（最便宜） | `Copilot: The requested model is not supported.` |
| 13:02 | #1458 | copilot kimi-k3 | 同上 |
| 13:03 | #1457 | workbuddy gpt-6.1-sol（升一档） | `not allowed for user type [personal_free_user]` |
| 13:04 | #1458 | workbuddy gpt-6.1-sol | 同上，一分钟后同一个绑定 |
| 13:05–13:08 | #1457 | trae doubao-seed-code（未验证） | 完成，改 1 个文件 → #1463 |
| 13:08–13:28 | #1458 | trae doubao-seed-code | 完成，改 2 个文件 → #1464，独立评审 REJECT |
| 13:28 | #1459 | copilot kimi-k3（排队时就定了） | 同第一行 |
| 13:30、13:33 | #1459 | chatgpt-gpt（Codex） | 两次 `codex_frame_limit_exceeded` |

后台验证（#1447）在窗口里正常工作，大约每分钟确认一个绑定可用；但它赶不上前几次分配。

### 暴露的平台缺陷

1. **#1460 — 模型被拒用后没学到，失败启动按未知用量扣预算。**
   - 原因 1：持久执行器把失败记为 `MODEL_UNAVAILABLE:<原因>`，选路历史和 `goal_service` 只认不带后缀的 `MODEL_UNAVAILABLE`。
   - 原因 2：Copilot 的措辞 "model is not supported" 不在标记列表里。
   - 原因 3、4：第一次调用就被拒的启动，预留（每个 888 万 token）记成 UNKNOWN 并计入窗口用量，还占一次 `max_tasks`。
   - **1、2 已由 #1461 修复上线**；3、4 未做。
2. **#1462 — 监督者起草的目标永远发布不了。** 起草的计划没有功能检查，只跑 `git diff --check`，
   不会生成 `AcceptedArtifact` 证据；协调器只发布有这条证据的任务。预检说没问题，目标显示 COMPLETED，没有任何提示。
   同一函数里 `SELECT task_id FROM platform_goal_task_links LIMIT 100` 不按窗口过滤、不排序（现在只有 59 行，还没触发）。**未做。**
3. **#1465 — Codex 一条大的命令输出就让整轮失败。** 解析器单行上限 256 KiB、整轮 2 MiB。**已由 #1466 修复上线**。
4. **执行器可用性一律当成 OpenCode 可用**（#1458，也是上午 #1453 被拒的根因）。系统这次的实现被拒，见下。

### 系统产出的质量（按独立评审）

- #1457：改对了 3 处中的 2.5 处，留了一句与新句子矛盾的话。监督者删一句后通过。
- #1458：方向对，但有 3 个阻断问题：每次构造模型存储都真实调用 `shutil.which`（没有这些 CLI 的机器上会让现有选路测试失败，CI 就是这样）；
  找到 Codex/Claude 的 CLI 就当成可用，跳过登录就绪检查；Windows 上漏掉 npm 装的 `.cmd`。已停放（PR #1464 保持 Draft，写了原因）。
- 两个任务都没跑测试（计划里没有功能检查，见 #1462），这也是质量问题的一部分来源。

### 监督者代发布的做法

主机发布不了时，监督者把任务工作区的改动原样拿出来开 Draft PR：
在 `F:\nerelan-run-data\task_workspaces\<task>` 里 `git add -N .` 后 `git diff HEAD --binary`，
从任务的基线提交开分支、应用补丁，PR 说明里写明作者是 Nerelan、窗口和绑定、监督者没有改内容。
#1463、#1464 就是这样开的。

## 5. 接下来做什么（按价值排序）

1. **#1462：让起草的目标能发布。** 不修的话，每次委派都要监督者手工代发布，而且系统产出不跑测试。
   最小做法：起草时按 Issue 提到的文件选一个功能检查（pytest/vitest 的具体文件），或者预检拒绝并说明原因；
   不能发布的 READY 任务在目标上写出原因；发布扫描按窗口过滤、去掉 100 行上限。
2. **#1460 第 3、4 条：失败启动不要按整份预留扣预算、不要占任务数。** 这次 9 次启动里 6 次是这种失败。
   第一次调用就被拒且没有任何成功回复的，按零用量结算并留证据；是否计入 `max_tasks` 要定（建议计入重试次数而不是任务数，保证有界）。
3. **#1458 重做，然后再看 #1453。** 要求：和 `dev-up.ps1` 共用一个探测规则（包括 `.cmd`）；测试里注入探测函数、不碰真实 PATH；
   原生执行器的登录就绪判断不变；选路拒绝时给出明确原因。适合再交给系统做一次（先修 #1462），作为对比。
4. **#1459** 还没人做出来。也可以再交给系统。
5. 上午交接里留下的：#1447 评审的跟进（被隔离过的账号仍会被探测一次、探测期间持锁、探测用量不计入窗口预算、
   成功但从未使用的绑定每 24 小时再探测一次）；#1445 的其余跟进；积分到期（#1429）；Magpie 能力对照（#1342）；
   设置层方案（本地分支 `claude/user-settings-layer`，未推送）。
6. 想关联 Claude 账号的话，Owner 先确认 Magpie 里的 Claude 账号和本机 Claude Code 登录是同一个。

## 6. 本次的 Owner 决定和偏好

- 部署到运行主机前先问（两次部署都当场问过、得到同意）；"等当前任务跑完再部署"。
- 删除远程分支要 Owner 指示：一次错误推送建了名为 `HEAD` 的远程分支，经 Owner 同意后删除。
- 有些任务交给系统做，借它的执行发现问题；监督者负责独立评审、修平台缺陷、记录。
- Codex 账号与 Magpie 账号关联：Owner 确认（Claude 未确认）。

## 7. 操作上要注意的

- 合并要求：exact-head 的 ACCEPT（或合格的合并 main 结转）、三个必需检查全绿、**所有评审线程已解决**、分支与 main 同步。
  一个 PR 落地后其余的都会落后，按顺序一个一个合，每次先合并 main 再等 CI。
  main 改过同一个文件时结转不成立（diff 不再逐字节相同），要新的评审。
- 首页相关的前端 PR 会在 `frontend/e2e/snapshots/*/home-*.png` 上冲突：取 main 的图，提交信息带
  `[update-visual-baselines]`，等 CI 生成 `ci-visual-baselines/<sha>` 分支后取回图片再提交。
- 推送时写全 `HEAD:refs/heads/<分支>`，不要用可能为空的变量（`HEAD:$var` 建出过名为 `HEAD` 的分支）。
- 在 Bash 的 heredoc 里写 Python 时 `\\n` 可能变成 `\n`；改代码的脚本用文件工具写。
- `tests/platform_v1/test_http_safe.py` 里重定向用例的 POST 情形在 Windows 本机约十次失败一次（未改动的代码路径），CI 正常。
- 全量 `tests/platform_v1` 在运行主机开着时会卡在 `test_magpie_launch`（#1435），本机跑时排除它。
