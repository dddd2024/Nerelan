# 多账户优化交付：反馈证据与可配置边界

本轮从 main `01478490c` 创建独立分支。开发时 127.0.0.1:8765/8766 无监听，
因此按 AGENTS.md 的有界 supervisor fallback 实现 R1 修复，不重放历史任务，
不启动或升级运行宿主。合并与部署是不同阶段；合并事实以 PR 门禁记录为准。

## 实现变更摘要

- 关闭模式自进化后立即停止消费旧 break-even，同时保留账本；Owner pin 继续优先。
- 复用 `orchestration_selector.update_break_even`，增加可提高、不可低于 3 的
  每模式、每规模带有效样本门槛。重启、调高门槛、样本裁剪后均从保留证据重新计算，
  不沿用不再满足门槛的旧推荐。没有新增学习算法。
- `accepted` 必须是布尔值；字符串 `"false"` 不再被强转成成功。
  非有限、负数、布尔或非数值测量保持 UNKNOWN；真实零成本继续保留。
- 可选 `outcome_id` 为同一次尝试提供有限保留窗口内的幂等反馈；冲突重放被拒绝，
  原记录不改。未提供身份的相同测量继续作为不同事件，不能据此宣称生产反馈已去重。
- 同宿主进程内同一路径的账本实例共用锁，更新前重读，保留交错写入的运行记录和其他分区。
  读取返回深复制。损坏账本拒绝覆写，交给既有可选调用 seam 处理不可用。
- 所有现有标量配置均可通过环境变量设置，并由 Pydantic 校验；没有新增依赖。

## 功能边界

核心目标仍是 local-first、在预授权边界内执行并受控落地软件变更。复用已有
LangGraph 适配层、TaskStore、durable execution、quota reservation、Magpie 接入及
Pydantic；本轮只修复反馈证据和配置入口。没有替换运行时、增加队列或通用插件管理器。
账户登录态和同服务切换继续交由已授权上游适配器承担，Nerelan 保留授权、硬准入和任务真相。
本轮不改变凭据、账户权限、实际预算、部署、CI 模型调用或独立评审要求。

## 关键模块

| 模块 | 职责 |
|---|---|
| `multi_account/config.py` | 校验账户状态、退避、权重、学习开关及样本门槛；读取环境标量 |
| `multi_account/evolution.py` | 归一结果、保留 UNKNOWN、同进程串行化、有限窗口幂等、复用决策核心 |
| `orchestration_selector.py` | 纯函数计算 single/team 成本交叉点，按模式及规模带核验有效样本 |
| `multi_account/status.py` / `cooldowns.py` | 既有观测分类与隔离；本轮不改变账户健康判断 |
| `trusted_host` / GoalService / coordinator | 既有生产准入、账户隔离、任务恢复；本轮不绕过或替换 |
| `usage_ledger` / `cost_report` | 既有成本证据；列表价、现金、额度机会成本分别报告，UNKNOWN 不等于免费 |

## 可配置项

除路由归属和账本路径外，环境变量名为 `REVERSE_AGENT_MULTI_ACCOUNT_` 加 Python
字段名的大写形式。例如 `REVERSE_AGENT_MULTI_ACCOUNT_ENABLE_SELF_EVOLUTION=false`。
显式 Python 参数优先于环境变量；无效值报错，不静默退回默认。配置在实例构建时读取，
修改环境变量不会热更新已经运行的实例；本轮不执行部署或重启。

| 类别 | 字段或入口 | 默认与约束 |
|---|---|---|
| 主开关 | `REVERSE_AGENT_MULTI_ACCOUNT_ENABLED` | 默认关闭，显式 `1` 启用已有可选 seam |
| 账户接入 | Connection `account_ref`、已有 binding 和适配器 | 只存非敏感身份；不自动登录或扩权 |
| 路由归属 | `REVERSE_AGENT_ACCOUNT_ROUTING` | `local`；`magpie/auto` 仍受原有确认条件约束 |
| 观测时效 | `observation_freshness_seconds` / `magpie_max_age_seconds` | 600 / 900 秒，前者不得超过后者 |
| 额度阈值 | `high_utilization_threshold` / `small_task_percent_ceiling` | 90 / 1 百分点，0–100，前者不小于后者 |
| 重路由与隔离 | `reroute_max_attempts` / `abnormal_account_cooldown_seconds` | 3 次 / 300 秒；组件能力不等于真实切换已验收 |
| 退避 | `failure_backoff_base_seconds` / `failure_backoff_multiplier` / `failure_backoff_max_seconds` | 30 秒 / 2 / 900 秒，最大值不小于初始值 |
| 状态持久化 | `persist_account_state` / `cooldown_memory_seconds` | true / 21600 秒；单宿主写入 |
| 评分及权重 | `enable_account_scoring` / `score_ewma_alpha` / `reliability_weight` / `cost_weight` / `latency_weight` | true / 0.25 / 12 / 10 / 5；生产评分排序仍待接线 |
| 模式自进化 | `enable_self_evolution` / `min_observations_per_mode` | true / 3；门槛只能提高；禁用后不使用模式学习结果 |
| 留存及账本 | `max_recorded_runs` / `REVERSE_AGENT_MULTI_ACCOUNT_STORE` | 500 / 原本地 runtime 路径；幂等仅覆盖保留事件 |
| 校准 | `calibration_feedback_enabled` | true；仍依赖足够的真实用量归因 |
| 成本、时长、并发、重试总限额 | 已有 Owner window 与任务合同 | 延续原批准上限；本轮不新增第二预算器，不批准扩限 |
| 日志与告警 | 已有 TaskStore 事件、阻塞原因、资源读模型 | 不自动创建外部通知；新增工作区告警草案尚未主线验收 |
| 策略限幅与回退 | 原权重边界、样本门槛及关闭模式学习 | 保留证据；本轮没有自动策略晋升、版本审计与灰度发布 |

`enable_self_evolution` 只控制模式建议；账户 EWMA 的开关是 `enable_account_scoring`，
两者不能当作一个总开关。生产路径的总体恢复受原合同、授权窗口和任务状态限制。

## 验收结果与标准

本轮专项命令：`python -m pytest tests/platform_v1 -q -k 'multi_account or orchestration_selector'`，
159 passed。完整平台套件、独立审查与 exact-head CI 的最终结果见对应 PR。
所有测试使用隔离临时状态，不调用真实 provider、不修改历史 TaskStore。

| 验收域 | 验收标准 | 当前证据 |
|---|---|---|
| 多账户整合 | 同 provider 多账户不串用身份、保留歧义与 UNKNOWN | 既有专项回归；真实登录隔离和切换未重新验证 |
| 状态感知 | 新鲜/陈旧/异常证据分类正确，不用 provider 汇总冒充账户观测 | 既有专项回归；当前无运行宿主采样 |
| 异常容错 | 隔离、恢复均守住原合同，保留失败及未知副作用 | #1379/#1381/#1383 已合入；整体真实故障链未验收 |
| 连续运行 | 24h→72h→7d，故障后无丢任务或无证据重放 | 未启动；模拟时间或 1 秒计时检查不能替代 |
| 成本与性能 | 同任务、同质量标准，全尝试成本完整归因及延迟分位达标 | 未建立真实对照；列表价观测不能证明现金节省 |
| 反馈优化有效 | 非布尔结果拒绝；禁用不读旧策略；提高门槛生效；重放不双计 | 本轮新增隔离回归通过；真实质量收益未证明 |
| 维护与扩展 | 复用唯一决策核心、环境配置受校验、不增加依赖或运行时 | 源码与专项测试可复核 |

## 已知限制与扩展点

1. JSON 原子替换和共享锁只覆盖同进程实例，不提供跨宿主事务。
   同一 accounts/cooldowns 分区的陈旧整段快照仍可能覆盖同分区更新；本轮只保证其他分区
   不被陈旧文档覆盖。未来需要多进程写入时应复用既有 SQLite 事务，不能把这个账本当队列。
2. `outcome_id` 需由真正的终态 seam 提供。同一 ID 保留窗口外的重放不能保证去重；
   现有测试报告 seam 缺模式、规模、完整成本和独立验收结论，仍不能驱动真实策略晋升。
3. 现有账本中历史错误布尔归一无法逆推恢复，本轮不重写历史。损坏文件需保留并调查，
   不自动清空。`reset()` 是既有显式清空 API，本轮不调用，也不把它当回滚方案。
4. 全面自进化还需审计版本、受控评估、限幅、回滚及真实生产消费证据。
   本轮关闭模式学习提供无损停用能力，不声称已有完整策略发布系统。
5. 原工作区成本/告警/时长草案保留，不能整体搬入主线。其“11/11”报告包含故障注入、
   重采样及短时探针；应按原始证据逐项验收，不能据总通过率宣称无人值守目标完成。
