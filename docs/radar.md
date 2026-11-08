# 竞品雷达

定期扫描与 Nerelan 相关的开源项目，把新发现交给一次由 Owner 批准的分诊任务，结论写进
[竞品与复用地图](architecture/COMPETITIVE_LANDSCAPE.md)。

## 工作方式

| 步骤 | 谁做 | 是否调用模型 |
|---|---|---|
| 收集：关注项目的新版本与 star 变化、GitHub 新仓库搜索、Hacker News 讨论 | 宿主后台线程 `radar.py` | 否 |
| 比对：只保留上次没见过的条目，首次运行只建立基线 | 宿主 | 否 |
| 有新条目时创建一个 PLANNED 分诊 Goal（每次运行最多一个，幂等） | 宿主 | 否 |
| 分诊：逐条判断复用、借鉴、竞品或忽略，更新竞品地图并开 Draft PR | Owner 把该 Goal 放进窗口后，由正常执行器完成 | 是，受窗口预算约束 |

雷达**从不批准或启动** Goal。它只创建 PLANNED 状态的 Goal，等 Owner 用
[Owner 窗口](owner-window.md) 的 `--goal` 把它纳入窗口。分诊的产出是 Draft PR，按 `AGENTS.md`
走独立评审和合入门禁。

GitHub 数据通过 Owner 已登录的 `gh` 读取，只发 GET 请求，不读取或导出 token；Hacker News 用其公开
搜索接口，不带凭据、不跟随重定向，响应上限 2 MiB。来源返回的文字都是不可信数据：报告里一律加引号，
分诊目标里用 `RADAR DATA` 标记圈起来，并明确要求不执行其中的指令。

## 启用

宿主环境设置 `REVERSE_AGENT_RADAR=<配置文件路径>`，默认关闭。启动时不发网络请求，第一次检查在一个
轮询周期之后。

```json
{
  "state_dir": "F:/nerelan-radar",
  "repository": "dddd2024/Nerelan",
  "executor_kind": "opencode",
  "binding_ref": "",
  "interval_hours": 168,
  "watch": ["paperclipai/paperclip", "stablyai/orca", "CopilotKit/OpenBot", "dyoshikawa/rulesync",
            "BuilderIO/agent-native", "momo5502/sogen", "OpenHands/OpenHands", "langchain-ai/langgraph",
            "anomalyco/opencode"],
  "github_queries": ["multi-agent coding orchestration", "coding agent worktree",
                     "codex claude multiple accounts", "agent quota routing"],
  "hn_queries": ["multi-agent coding", "coding agents orchestration"]
}
```

| 字段 | 默认 | 说明 |
|---|---|---|
| `interval_hours` | 168 | 两次成功运行的间隔 |
| `poll_minutes` | 60 | 检查是否到期、重试失败的频率 |
| `lookback_days` | 90 | 新仓库和讨论只看这段时间内创建的 |
| `min_stars` | 200 | 新仓库的最低 star 数 |
| `max_per_query` | 20 | 每个查询最多取的条目（1–100） |
| `star_jump_min` / `star_jump_ratio` | 500 / 0.25 | 关注项目 star 增长同时超过这两个门槛才报告 |
| `hn_min_points` | 50 | Hacker News 讨论的最低分数 |
| `executor_kind` / `binding_ref` | `opencode` / 空 | 分诊 Goal 的执行器；空的 binding 交给路由选择 |

`binding_ref` 留空时由路由选择；建议填免费模型的 binding，让分诊不占用 Claude 或 Codex 的周额度。

## 失败与恢复

- 单个来源失败只记录在报告的"失败来源"里，其他来源照常计入。
- 所有来源都失败时不算一次运行，下一个轮询周期重试。
- Goal 创建失败时保留待创建状态，下一个轮询周期重试；同一次运行的 Goal 幂等，不会重复。
- 状态保存在 `state_dir`：`state.json`（运行记录）、`seen.json`（已见条目）、`snapshots/`、`reports/`。
  写入是原子替换，宿主重启后按上次成功时间继续。

## 查看

```bash
python -m reverse_agent.platform_v1.radar status --config radar.json
```

```bash
python -m reverse_agent.platform_v1.radar preview --config radar.json
```

`status` 只读本地状态。`preview` 立即联网收集一次并打印与已见条目相比的新内容，不保存任何东西，
也不创建 Goal。

## 限制

- 只覆盖 GitHub 和 Hacker News；Reddit、X、论文和闭源产品不在范围内。
- 关注项目的版本发布很频繁，报告会包含较多小版本，靠分诊去筛选。
- 新仓库只按 star 数和创建时间筛选，可能漏掉 star 少但相关的项目，也可能带进同名无关项目。
- 分诊结论取决于执行模型阅读竞品文档的质量；分诊 PR 仍需独立评审。
