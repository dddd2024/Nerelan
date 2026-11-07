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

### 账户为什么分"参与准入"和"仅观测"

`magpie_quota_windows` 只投影本仓有路由认领的服务（目前是 Codex 和 Claude）。这对硬准入是
正确的，否则别的服务的额度会影响派发决定。运维视图需要看到全部账户，所以有单独的
`diagnose` 投影，并用 `admission_evidence` 标出每个账户属于哪一类。页面上显示为"仅观测"。

## 可配置项

环境变量统一为 `REVERSE_AGENT_MULTI_ACCOUNT_` 加字段名大写，无效值由 Pydantic 在启动时拒绝。
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
| 日志 | `alert_log_path`、`alert_log_max_bytes`、`alert_log_backups` | 运行目录、1 MB、3 | 总量有界 |
| 自进化开关 | `enable_policy_evolution`、`enable_account_scoring` | 关闭 | |
| 自进化限幅 | `policy_step_ratio`、`policy_max_weight_drift_ratio`、`policy_min_new_attempts` | 0.1、0.25、30 | 每个评估窗口最多一步 |

推荐的无人值守起步配置，先只观察，确认评分合理后再开启自进化：

```text
REVERSE_AGENT_MAGPIE=1
REVERSE_AGENT_MULTI_ACCOUNT_ENABLED=1
REVERSE_AGENT_MULTI_ACCOUNT_ENABLE_ACCOUNT_SCORING=1
REVERSE_AGENT_MULTI_ACCOUNT_ENABLE_FEEDBACK_ROUTING=1
```

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
| `perception_unavailable` | warning | 读不到账户状态，不等于账户池为空 |
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

回滚会创建新版本，不删除历史。反馈存储只在单进程内串行化写入，所以宿主运行时命令会拒绝，
返回 `host_running`。`--target 0` 回到 Owner 基线，`--expected-revision` 防止基于过期视图回滚。
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
| 反馈优化 | `injected_outcomes_evolve_the_policy_within_bounds` | 版本前进，权重在限幅内变化 |
| 策略进入路由 | `evolved_policy_reaches_the_production_router_snapshot` | 路由快照带生效版本 |
| 可回滚 | `policy_rollback_restores_the_baseline_as_a_new_version` | 新版本恢复基线 |
| 维护便利 | 监控、告警、CLI 共 3 个新模块 | 无新运行时、队列或常驻服务 |

## 已知限制

- 最长真实运行只有 15 分钟。没有 24 小时、72 小时或 7 天的长跑，也没有休眠唤醒或强杀恢复的真实验证。
- 验收的调用是直接发给 Magpie 网关的，没有经过协调器运行一个完整任务。
- 成本是列表价估算，不是账单现金；验收的调用只记录 Token 数。
- 反馈优化的有效性只验证了"权重按规则变化并进入路由"，没有在真实任务上对照出成本或
  成功率的改善。
- "仅观测"的账户不参与准入，其额度耗尽不会阻止派发，只有 Magpie 自身的失败会反馈回来。
- 告警没有外发渠道；无人值守时需要有人看日志或账户页。
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
