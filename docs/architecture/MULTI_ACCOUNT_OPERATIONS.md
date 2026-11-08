# 多账户运维：统一视图、告警与回滚

本文说明如何运行和观察多账户调度。交付历史见
[交付边界与验收状态](MULTI_ACCOUNT_DELIVERY_STATUS.md)，策略生命周期见
[账户权重策略](MULTI_ACCOUNT_POLICY_LIFECYCLE.md)。

## 功能边界

本层只读：看见账户池、发现异常、留下记录。派发、准入和预算仍由既有组件决定。

| 能力 | 负责方 | 本层是否改变 |
|---|---|---|
| 账户凭据、同服务账户切换、请求重试 | Magpie | 否，只读其快照 |
| 硬准入、额度预留 | `quota_reservation`、`platform_quota_observations` | 否，诊断快照不写入 |
| 成本和 Token 上限 | 窗口预算，在 SQLite claim 边界强制 | 否，只读余量并告警 |
| 运行时长 | 自治窗口与 standing renewal | 否，只提示到期 |
| 隔离、退避、切换 | `cooldowns`、`scheduler`、`account_quarantine_guard` | 否，只展示 |
| 自进化 | `policy_lifecycle`，默认关闭 | 否，增加命令行回滚入口 |

浏览器没有任何策略权限。`/accounts` 页面和 `GET /api/platform/accounts` 都是只读的，
回滚只能在宿主停止后通过命令行执行。

### 复用与替换边界

| 组件 | 复用范围 | 替换边界 |
|---|---|---|
| Magpie | 账户、额度窗口、模型网关 | `fetch_magpie_snapshot` 是唯一入口；未启用时回退到本地额度观测 |
| Python `RotatingFileHandler` | 告警日志轮转 | `jsonl_sink` 是一个函数，可换成任何接收事件字典的 sink |
| `cmdk` | 命令面板的列表语义与键盘导航 | 只在 `conversation-panel.tsx` 使用 |
| Agent Canvas | 侧栏与工作台框架 | 见 `frontend/OPENHANDS_REUSE_MAP.md` |

没有引入 Prometheus、Temporal 或 Celery：当前单机本地场景下，它们要么与既有租约和窗口
语义重叠，要么需要额外常驻服务。重新评估条件见
[编排规范](MULTI_ACCOUNT_ORCHESTRATION_SPEC.md) 第 2 节。

## 关键模块

| 模块 | 职责 |
|---|---|
| `multi_account/status.py` `diagnose` | 把 Magpie 快照投影为全部账户的状态，含没有路由认领的账户；绝不作为准入证据 |
| `multi_account/pool_monitor.py` | 汇合感知、隔离、评分和策略为一个读模型；独立线程运行 |
| `multi_account/alerts.py` | 纯函数告警规则，以及把连续评估转为 raised/resolved 事件的账本 |
| `multi_account/cli.py` | `policy`、`alerts`、`rollback` 命令 |
| `task_service.py` `/api/platform/accounts` | 需要本地客户端 capability 的只读接口 |
| `frontend/src/routes/accounts.tsx` | 账户页；侧栏显示未处理告警数 |

监控线程独立于协调器 tick，这是有意的：协调器卡死时，告警不能依赖它自己的循环。
告警在每次评估时重新推导，所以重启不会留下陈旧告警。代价是重启后活动告警的起始时间重置，
并再记录一次 `raised`。

一次读取失败不代表账户有变化，所以读不到时保留最近一次结果，并用告警说明：Magpie 对应
`perception_unavailable`，反馈存储对应 `feedback_unavailable`，运行状态对应
`runtime_status_unavailable`。保留有界限：账户行超过 `observation_freshness_seconds` 后转为
STALE，不再声称健康。隔离告警来自内存中的隔离注册表，不依赖感知结果和账本文件，所以按
`connection_id` 记录的隔离也会上报，账本损坏时隔离依然按时到期。

### 账户为什么分"参与准入"和"仅观测"

`magpie_quota_windows` 只投影本仓有路由认领的服务（目前是 Codex 和 Claude）。这对硬准入是
正确的，否则别的服务的额度会影响派发决定。运维视图需要看到全部账户，所以有单独的
`diagnose` 投影，并用 `admission_evidence` 标出每个账户属于哪一类。页面上显示为"仅观测"。

## 可配置项

环境变量为 `REVERSE_AGENT_MULTI_ACCOUNT_` 加字段名大写，无效值由 Pydantic 在启动时拒绝。
例外是 `REVERSE_AGENT_ACCOUNT_ROUTING` 和 `REVERSE_AGENT_MULTI_ACCOUNT_STORE`。
参数在进程启动时读取，修改后需要重启。

| 类别 | 配置 | 默认 | 说明 |
|---|---|---|---|
| 账户接入 | `REVERSE_AGENT_MAGPIE`、`REVERSE_AGENT_MAGPIE_URL` | 关闭、`127.0.0.1:3425` | 只接受回环地址 |
| 总开关 | `REVERSE_AGENT_MULTI_ACCOUNT_ENABLED` | 关闭 | 同时控制反馈、监控线程和告警日志 |
| 额度阈值 | `high_utilization_threshold`、`reset_soon_threshold_seconds`、`observation_freshness_seconds` | 见 `config.py` | 决定健康分级 |
| 调度权重 | `reliability_weight`、`cost_weight`、`latency_weight`、`enable_feedback_routing`、`feedback_routing_max_adjustment` | 关闭、0.1 | 调整量硬上限 0.25 |
| 重试与降级 | `reroute_max_attempts`、`failure_backoff_base_seconds`、`failure_backoff_multiplier`、`failure_backoff_max_seconds` | 3、30、2、900 | 隔离时长取退避值与下限的较大者 |
| 隔离 | `abnormal_account_cooldown_seconds` | 300 | 下限；只有到期才解除 |
| 成本上限 | 窗口 `max_cost_micro_units`、`max_token_units`、`per_task_*_reservation` | 无上限 | 激活窗口时设置 |
| 运行时长 | 窗口 `expires_at`、`standing_renewal` | 单窗口至多 7 天 | 续期总计至多 90 天 |
| 监控 | `alert_interval_seconds` | 30 | 5–3600 |
| 告警阈值 | `alert_min_usable_accounts`、`alert_budget_warn_ratio`、`alert_stall_seconds` | 2、0.2、300 | |
| 日志 | `alert_log_path`、`alert_log_max_bytes`、`alert_log_backups` | 相对宿主工作目录、1 MB、3 | 总量有界 |
| 自进化开关 | `enable_policy_evolution`、`enable_account_scoring` | 关闭、开启 | 评分默认记录，只有开启反馈路由才影响选路 |
| 自进化限幅 | `policy_step_ratio`、`policy_max_weight_drift_ratio`、`policy_min_new_attempts` | 0.1、0.25、30 | 每个评估窗口最多一步 |

推荐的无人值守起步配置，先只观察，确认评分合理后再开启自进化：

```text
REVERSE_AGENT_MAGPIE=1
REVERSE_AGENT_MULTI_ACCOUNT_ENABLED=1
REVERSE_AGENT_MULTI_ACCOUNT_ENABLE_FEEDBACK_ROUTING=1
```

## 周额度配速

Owner 要求 Claude 和 Codex 的周额度不能提前用完（2026-11-07）。选路器对这两个订阅账户按时间配速：
若 `已用比例 + 本任务预计用量 > 本周已过时间比例 + slack`，或超过 `1 - reserve`，该候选被排除，理由
`weekly_pace`，并带 `retry_at`，由既有的临时资源等待机制到点重查。预计用量未校准时按 3 个百分点计。

| 配置（`model_routing_overrides.json` 的 `weekly_pace`） | 默认 |
|---|---|
| `enabled` | true |
| `executors` | `["codex", "claude_code"]` |
| `slack` | 0.10 |
| `reserve` | 0.10 |

复用边界：输入全部来自 Magpie（已用比例与重置时间）。Magpie 面板上的"配速 +20%"没有通过接口或
`magpie quota --json` 提供，所以账户页用同一定义（已用比例减本周已过时间比例）显示，读数与面板一致。
Magpie 只在额度用完时才拦截，并可能继续消耗积分，所以提前放慢必须在选路器里做。

已验证的 Codex 提前重置公告会让位于既有 drain 规则（#1248、#1281），规则与时间推断见 `docs/codex-reset-signals.md`，由 `REVERSE_AGENT_CODEX_RESET_WATCH=1` 启用。重置实际发生后，Magpie 的新窗口
会让配速按新的一周重算。Codex 持有的重置卡由 Magpie 管理，账户页只显示数量和最早过期时间。

## 告警

| 代码 | 级别 | 含义 |
|---|---|---|
| `pool_no_usable_account` | critical | 没有可派发账户，任务等待 |
| `window_budget_exhausted` | critical | 窗口成本或 Token 预算耗尽 |
| `coordinator_stopped` | critical | 窗口有效，但协调器未运行 |
| `coordinator_stalled` | critical | 协调器运行中，但超过阈值没有完成一轮 |
| `pool_capacity_low` | warning | 可派发账户低于阈值 |
| `account_quarantined`、`account_abnormal` | warning | 单个账户隔离或异常 |
| `window_budget_low` | warning | 预算余量低于阈值 |
| `perception_unavailable`、`feedback_unavailable`、`runtime_status_unavailable` | warning | 对应来源读取失败，显示的是最近一次结果 |
| `coordinator_error`、`admission_hold`、`goals_stranded` | warning | 协调器报告的问题 |
| `account_exhausted`、`window_expiring` | info | 额度用尽；窗口一小时内到期且未配置续期 |

`admission_hold` 读取协调器状态的 `admission_holds` 字段。该字段由 #1396 提供，合入之前
不会触发这条告警。

投递渠道目前是日志、JSONL 文件和账户页。要接入 IM 或邮件，实现一个接收事件字典的函数
传给 `AlertLedger` 即可；外发渠道涉及对外发送，需要 Owner 明确配置。

## 常用操作

```bash
python -m reverse_agent.platform_v1.multi_account.cli policy
```

```bash
python -m reverse_agent.platform_v1.multi_account.cli alerts --limit 20
```

```bash
python -m reverse_agent.platform_v1.multi_account.cli rollback --target 0 --expected-revision 7
```

回滚会创建新版本，不删除历史。反馈存储只在单进程内串行化写入，所以任务 API 端口有进程监听时
命令会拒绝，返回 `host_running`；只有连接被拒绝才算宿主已停止。默认端口取
`REVERSE_AGENT_TASK_SERVICE_PORT`，宿主用其他端口时需要传 `--task-api`。`--target 0` 回到 Owner 基线，`--expected-revision` 防止基于过期视图回滚。
需要立即止损时，关闭 `enable_policy_evolution` 并重启，路由马上回到配置基线。

## 验收

可重复执行：

```bash
python scripts/multi_account_live_acceptance.py --soak-minutes 15 --evidence out.json
```

脚本在隔离端口和隔离运行目录启动真实宿主，用真实账户发起低成本调用。检查名前缀说明证据的
性质：`real_` 是真实账户或真实网络；`injected_` 是把合成结果送入生产路径，反应是真的，
起因不是，因为无法让真实账户按需出故障。故障切换循环在脚本内，每一步决定由生产调度器做出，
但它不是协调器在运行任务。

| 验收项 | 证据 | 结果 |
|---|---|---|
| 多账户整合 | `real_pool_lists_every_magpie_account` | 真实账户池 11 个账户全部可见 |
| 状态感知 | 同上，及 `real_feedback_reaches_the_pool_view` | 健康分级与真实调用反馈可见 |
| 异常容错 | `real_failover_serves_on_another_account` | 隔离后由另一个真实账户完成调用 |
| 隔离恢复 | `real_quarantine_expires_and_the_alert_resolves` | 到期恢复，告警自动解除 |
| 告警留痕 | `real_alert_log_records_both_transitions` | raised 与 resolved 都写入 JSONL |
| 连续运行 | `real_soak_*` | 15 分钟 15 轮全部由真实账户完成（trae-cn 13、workbuddy-ai 2），接口零错误，p50 1.9 秒、最长 5.54 秒。期间没有真实失败，所以这是稳定性证据，不是容错证据 |
| 24 小时长跑 | `real_long_run_reached_its_deadline_without_errors`、`real_long_run_resumed_after_every_restart` | 2026-11-07 05:31 至 11-08 05:31，计划 288 轮、实际 145 轮，覆盖率 50.3%：中途关机约 11.9 小时，开机登录后由启动项恢复，轮次接续，到期自动收尾并删除启动项。143 轮由真实账户完成（workbuddy-ai 140、trae-cn 3），2 轮因 Magpie 未启动记为 held，轮次错误与账户视图错误均为 0，p50 1.58 秒、最长 3.48 秒。trae-cn 的 3 轮发生在开头注入故障隔离 workbuddy-ai 期间；隔离解除后调度器重新选中 workbuddy-ai 并一直保持，没有在账户间轮转。期间没有真实失败和切换，`perception_unavailable` 在 Magpie 启动后自动解除，`claude` 额度耗尽告警一直保持到结束 |
| 反馈优化 | `injected_outcomes_evolve_the_policy_within_bounds` | 版本前进，权重在限幅内变化 |
| 策略进入路由 | `evolved_policy_reaches_the_production_router_snapshot` | 路由快照带生效版本 |
| 可回滚 | `policy_rollback_restores_the_baseline_as_a_new_version` | 新版本恢复基线 |
| 维护便利 | 监控、告警、CLI 共 3 个新模块 | 无新运行时、队列或常驻服务 |

## 已知限制

- 最长真实运行是一次 24 小时计划、实际覆盖 50.3% 的长跑：真实关机恢复验证了 1 次，强杀恢复只在短运行中验证过；没有 72 小时或 7 天的长跑，也没有满覆盖的 24 小时证据。
- 长跑期间没有发生真实失败，所以它只证明稳定性和关机恢复，不证明真实故障下的容错。
- 低成本候选中调度器在 workbuddy-ai 健康时始终选它，长跑没有体现账户间的负载分摊。
- Magpie 不随登录自启，关机恢复后在它启动前的轮次只能记为 held。
- 验收的调用是直接发给 Magpie 网关的，没有经过协调器运行一个完整任务。
- 成本是列表价估算，不是账单现金；验收的调用只记录 Token 数。
- 反馈优化的有效性只验证了"权重按规则变化并进入路由"，没有在真实任务上对照出成本或
  成功率的改善。
- "仅观测"的账户不参与准入，其额度耗尽不会阻止派发，只有 Magpie 自身的失败会反馈回来。
- 告警没有外发渠道；无人值守时需要有人看日志或账户页。
- 容量告警把"仅观测"账户也算作可派发，所以 `pool_no_usable_account` 可能在可路由账户
  都耗尽时保持沉默。
- `coordinator_error` 会一直保持，直到协调器的 `last_error` 被覆盖，常常要到重启。
- `coordinator_stalled` 的阈值是固定秒数，耗时很长的合法落地步骤可能触发它。
- 回滚要停宿主，因为反馈存储没有跨进程锁。
- 真实宿主的账户页未在真实浏览器中走通：浏览器需要由 Node 代理持有 capability，本次
  只验证了接口返回与 mock 页面渲染。

## 扩展点

| 需求 | 接入位置 |
|---|---|
| 外发告警（IM、邮件、Webhook） | `AlertLedger` 的 sink |
| 新告警规则 | `alerts.py` 增加一个纯函数分支 |
| 新账户来源 | `PoolMonitor` 的 `fetch_snapshot` |
| 更多可路由服务 | `subscription_quota._MAGPIE_PROVIDER_KEYS`，这会改变准入，需单独评审 |
| 指标导出 | 读 `PoolMonitor.view()`，不需要改写调度路径 |
