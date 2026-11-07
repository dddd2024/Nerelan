# 交接：多账户 24 小时真实长跑（2026-11-07）

接手的对话先读这一节。一个真实账户长跑正在后台独立运行，没有任何对话在监督它，结束时也不会通知谁。
接手者的工作是：确认它的状态，跑完后汇总证据，把脚本改动走完评审和落地。

## 1. 正在运行什么

| 项 | 值 |
|---|---|
| 进程 | `python -u scripts/multi_account_live_acceptance.py --resumable --soak-minutes 1440 --soak-interval 300 ...` |
| 启动 | 2026-11-07 05:31（系统时钟），由 `Install-LongRunAutostart.ps1 -StartNow` 无窗口启动 |
| 截止 | 2026-11-08 05:31（系统时钟），以 `soak_state.json` 的 `deadline` 为准 |
| 工作目录 | `F:\nerelan\.claude\worktrees\multi-account-scheduling-evolution-47567e`（Claude 工作区，见第 5 节） |
| 运行数据 | 上述目录下 `.platform_v1_runtime\soak-24h\` |
| 开机自启 | `%APPDATA%\Microsoft\Windows\Start Menu\Programs\Startup\Nerelan long run.lnk`，到期后由运行自己删除 |
| 频率与开销 | 每 5 分钟一次真实调用，约 288 次，每次约 70 token，只用低成本模型（`workbuddy-ai/hy4free`、`workbuddy/hy4free`、`trae-cn/Doubao-Seed-2.1-Turbo`） |
| 端口 | 宿主占用 `127.0.0.1:18765/18766`，与正式宿主的 8765/8766 不冲突 |

每一轮做的事：读真实 Magpie 账户池，由生产调度器 `MultiAccountOrchestrator.select` 选一个账户，
发一次真实调用，失败时最多切换 3 次，把结果送回生产反馈路径，再通过已认证的
`GET /api/platform/accounts` 读回账户视图。

## 2. 关机与重启

关机后重新开机、**登录**，再**手动打开 Magpie**（`F:\magpie\magpie.exe`，目前不随登录自启）。
登录时启动项会用同一条命令恢复运行：跳过故障注入，轮次编号接续，停机时间记为一次大间隔，
仍按原截止时间收尾。Magpie 未就绪时那几轮记为 held，不判失败。

只停在登录界面不会恢复。合上盖子或手动睡眠会暂停运行，表现为间隔变大。

## 3. 如何检查状态

```powershell
Get-Content .platform_v1_runtime\soak-24h\soak_progress.jsonl -Tail 5
```

```powershell
Get-NetTCPConnection -LocalPort 18766 -State Listen
```

- `soak_progress.jsonl` 每轮一行：`served` 是完成调用的服务，空表示 held；`failed` 是失败尝试；
  `gap_seconds` 远大于 300 表示期间停机或暂停；`alerts` 是当时的活动告警；`dispatchable` 是可派发账户数。
- 有监听说明进程在跑；没有监听且未到截止时间，说明它停了，等下次登录恢复，或手动运行 `soak-24h\resume.cmd`。
- `run.log` 有完整输出；`alerts.jsonl` 是告警的 raised/resolved 记录。

## 4. 跑完后要做的事

1. 确认已过截止时间，且 `evidence.json` 存在。如果最后一次运行没有正常收尾，在工作目录执行一次
   `soak-24h\resume.cmd`：过期运行只做汇总，会补写 `evidence.json`，不会再调用账户。
2. 读 `evidence.json` 里的两项：
   - `real_long_run_reached_its_deadline_without_errors`：轮数、各服务完成数、held、错误、启动次数、停机小时数、覆盖率。
   - `real_long_run_resumed_after_every_restart`：只有发生过重启才有，要求每次重启后都有新轮次。
3. 结合 `soak_progress.jsonl` 看：调度是否在账户间轮转，还是一直集中在 `trae-cn`；隔离解除后
   `workbuddy-ai` 是否重新被选中；是否出现过真实失败和切换；额度是否下降到触发告警。
4. 更新 `docs/architecture/MULTI_ACCOUNT_OPERATIONS.md` 的验收表和已知限制。只写证据支持的结论：
   没有真实失败就不能声称容错；有停机就写清覆盖率。
5. 推送分支 `claude/multi-account-long-soak`，开 Draft PR，请独立评审（新的上下文），按 `AGENTS.md`
   走 exact-head CI、Ready、`landing_review verdict --auth-source gh`、`gh pr merge --match-head-commit`。
   这是 R1 改动：只改 `scripts/` 和 `docs/`。

## 5. 风险与注意事项

- **工作区可能被清理**：运行目录在 Claude 会话的工作区里。跑完之前不要归档发起长跑的会话。
  目录被清理会导致运行中断，开机自启也会失败。
- **不要在同一目录手动再起一个实例**：已有实例时第二个会因端口被占而退出（返回码 3），这是预期行为。
- **提前停止**：结束占用 18766 的 `python` 进程，再运行
  `powershell -NoProfile -File scripts\windows\Install-LongRunAutostart.ps1 -Uninstall`。
- 运行目录 `.platform_v1_runtime\` 被 `.gitignore` 忽略，永远不要提交它。
- 旁边的 `soak-24h-nonresumable-*` 是改造前那次只有 2 轮的运行，不计入结论；
  `resume-test`、`autostart-test-1` 是验证用的短运行。

## 6. 本次已完成的工作

| PR | 内容 | 状态 |
|---|---|---|
| #1397 | 前端重构为常见 Agent 工具形态，命令面板用 `cmdk` | 已合入 `1ccb9a84` |
| #1398 | 全量账户视图、告警（独立线程）、运维 CLI 与回滚、`/accounts` 页、真实验收脚本 | 已合入 `87389ef8`，经过两次 REJECT 后 ACCEPT |
| 本地分支 `claude/multi-account-long-soak` | 长跑加固、关机恢复、开机自启 | 已推送，未开 PR |

长跑分支上的验证：强杀进程后从第 3 轮恢复（停机 66 秒，5/5）；按登录方式启动安装好的快捷方式，
到期后 18/18 并自动删除启动项；截止后重复执行只汇总；端口被占时第二个实例退出。

## 7. 仍未解决的问题

- 平台自己的任务在真实关机后能否恢复：这次恢复的是验收工具，平台任务的租约恢复和启动对账有测试，
  但没有在真实关机下验证。下一步应该让协调器在真实窗口里跑真实任务，经历一次关机。
- Magpie 不随登录自启：可在 `resume.cmd` 里检测 3425 端口，必要时启动 Magpie。这会改变启动项的行为，需要 Owner 同意。
- `admission_hold` 告警依赖 #1396，未合入前不会触发。
- #1398 评审接受的三条非阻塞问题：Magpie 长时间不可用时 `account_abnormal` 会误记 resolved；
  全部 STALE 时 `pool_no_usable_account` 会告警，尽管只是读不到；运行状态记忆没有过期时间。
- 告警没有外发渠道（IM、邮件、Webhook）。
- 成本是列表价估算，没有账单证据；反馈优化只验证了权重有界变化，没有真实任务上的收益对照。
- #1397 两张移动端设置页视觉基线仍是旧配色，但测试在阈值内通过，视觉门禁没有完全覆盖它们。
