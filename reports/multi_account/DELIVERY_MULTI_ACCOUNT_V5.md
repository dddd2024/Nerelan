# 多额度账户统一纳管与自进化闭环 · 交付说明（v5）

分支：`agent/multi-account-full-loop-20261106`　基线：`origin/main @ 2a268b1e`（2026-11-06）
口径：本文件只写**本分支已实现、且有可复跑证据**的能力。只读文档与真实账户长跑分开记录，
不合并成"已完成"。

---

## 1. 实现变更摘要

前几轮已经把"多账户纳管"做到了能感知、能隔离、能选路，并已按切片合入 main
（#1378/#1379/#1381/#1383/#1386/#1387）。但长跑必需的另外四件事在 main 上仍只有组件、
没有生产调用方：**成本上限、运行时长、告警送达、策略限幅与回滚**。
同时，承载这四件事的分支实现落后 main 73 个提交，直接沿用会覆盖 main 已合入的更强保证。

本轮因此做两件事，顺序不能颠倒：

1. **先对账**：把落后分支与当前 main 显式合并，逐处判断"谁的语义更强"，而不是二选一。
2. **再补闭环**：在 main 的语义之上补齐四条闭环，并让它们与 main 的原子反馈共用同一个临界区。

| # | 变更 | 位置 | 性质 |
|---|---|---|---|
| 1 | 与 `origin/main @ 2a268b1e` 合并，19 处冲突逐一解决 | 分支 HEAD | 对账 |
| 2 | 四模块落地：成本上限 / 告警 / 运行时长 / 策略链 | `multi_account/{budget,alerts,watchdog,policy}.py` | 新增（补缺） |
| 3 | 预算结算、心跳、策略步进挂进 main 的原子反馈临界区，`outcome_id` 重放不重复计入 | `multi_account/__init__.py` | 接线 |
| 4 | 环境变量面覆盖全部 57 个配置项（55 个标量 + 2 个自有变量），文档名优先、派生名兜底 | `multi_account/config.py`、`.env.example` | 可运维性 |
| 5 | 数值健壮性：`10**400` / `NaN` / `inf` 成本不再让准入与结算抛错 | `multi_account/budget.py` | 缺陷修复 |
| 6 | 运维入口：`status/accounts/budget/policy/audit/alerts/scores/rollback` | `multi_account/cli.py` | 可运维性 |
| 7 | 感知前置：Magpie 快照 → 观测表（白名单字段、60 秒去抖） | `multi_account/perception_sync.py`、`trusted_host.py` | 接线 |
| 8 | 新增 14 例回归：9 例跨模块连续性 + 4 例数值健壮性 + 1 例快照有限性 | `test_multi_account_continuity.py`、`test_multi_account_budget.py`、`test_multi_account_evolution.py` | 验收 |
| 9 | 合并产生的 3 组同名测试被去重（后者原本静默覆盖前者） | `test_multi_account_resilience.py`、`test_multi_account_host_wiring.py` | 缺陷修复 |
| 10 | 交付状态文档补记本轮增量 | `docs/architecture/MULTI_ACCOUNT_DELIVERY_STATUS.md` | 文档 |

### 1.1 对账时保留的 main 侧更强语义（不得回退）

| 主题 | main 的做法 | 本轮处置 |
|---|---|---|
| 账户反馈写入 | `record_account_feedback` 单事务原子写 + `outcome_id` 回执去重 + 冲突回执报错 | **保留为唯一写路径**；预算结算/心跳/策略步进并入同一把锁 |
| 配置校验 | `extra=forbid`、`allow_inf_nan=False`、strict int、跨字段一致性、非法环境值快速失败 | **保留**；仅在其上追加新字段与新约束 |
| 评分校验 | `_measurement` 拒绝 NaN/inf/超大值，`Field(ge=...)` | **保留**；新增字段沿用同一套校验风格 |
| 生产反馈选路 | `feedback_policy` 默认关闭、有界调整 | **保留**，本轮不触碰 |
| 治理文件 | `AGENTS.md` 为 R2 | **不修改**；合并时把分支对该文件的追加回退到 main 版本 |

### 1.2 复用范围与替换边界（"不重复建设"的判定）

| 类别 | 对象 | 处置 | 边界说明 |
|---|---|---|---|
| 复用 | Magpie（`quota` / `usage` / `quota wait`，只读） | 复用 | 只读观测与可选等待委托；**不接管**账户内切换、登录态、凭据 |
| 复用 | `durable_execution`、`control_store`、`quota_reservation` | 复用 | 租约、claim、预算、窗口、准入、标定全部沿用；新接缝只在这些调用**前后**插入 |
| 复用 | `orchestration_selector.break_even`、`delta_calibration` | 复用算法 | 只补持久化与反馈回路，未重写任何已测算法 |
| 复用 | `pydantic`、`sqlite`、标准库 | 复用 | 零新增第三方运行时依赖 |
| 新增（仅补缺） | `budget/alerts/watchdog/policy/cli/perception_sync` | 新增 | 均为 main 上**不存在**的能力，非并行实现 |
| 不引入 | Celery/RQ、Temporal/Prefect、Ray、第二套重试队列 | 不引入 | 与既有单机租约/预算语义重叠，引入即第二编排脊柱 |
| 不替换 | 原生 CLI provider 自持登录（逐步退出层） | 保留不动 | 不作为扩容目标 |
| 不改动 | `AGENTS.md`、`.github/workflows/**`、`landing_review.py` | 不改 | R2，需 Owner 决策 + 独立评审 |

---

## 2. 功能边界

### 2.1 已实现（默认关闭，`REVERSE_AGENT_MULTI_ACCOUNT_ENABLED=1` 才启用）

- **多账户统一纳管**：按 `account_ref` 保留每账户独立额度窗口，修正同 provider 多账户互相覆盖的缺陷。
- **持续状态感知**：七态健康分类（HEALTHY/DEGRADED/EXHAUSTED/ABNORMAL/STALE/UNKNOWN + reset_soon），
  含余量、新鲜度、重置时刻；单个坏观测不拖垮整池；观测源故障单独上报，不伪装成"池为空"。
- **异常容错**：有界重路由、双层冷却（任务级瞬时 + 账户级隔离）、指数退避封顶、dead-letter 留证、
  重启恢复隔离与评分。
- **成本限制**：滚动窗口上限，`allow/degrade/deny`；软阈值转最低成本账户；硬上限一律**等待不超支**；
  未知成本不记为 0。
- **运行时长**：单次运行墙钟预算 + 空闲预算；`conclude` 停止认领并排空在飞批次，`stop` 为硬升级。
- **告警**：规则化生成、`(code, subject)` 抑制、有界历史、宿主 sink 投递、可选本地 JSONL 与轮转。
- **自进化**：基于成功率/失败类型/成本/延迟的有界权重调整；限幅、样本门槛、版本链、审计、回滚。

### 2.2 明确不做（本轮边界）

- 不做账户凭据读写、登录态切换、同服务账户切换接管（属 Magpie）。
- 不新增调度器、消息队列、定时服务、数据库表或第三方运行时依赖。
- 不自动晋升策略、不修改授权/预算配置本身、不自行发布。
- 不包含部署、真实付费试跑、扩预算、历史 UNKNOWN 核销或门禁放松。
- 不修改治理文件（`AGENTS.md` 等 R2 路径），本轮无 R2 变更。

---

## 3. 关键模块

| 模块 | 行数 | 职责 | 关键不变量 |
|---|---|---|---|
| `multi_account/__init__.py` | 487 | 门面：感知/调度/成本/告警/时长/进化组合 | 一个宿主只接触一个对象；反馈走同一把锁 |
| `multi_account/config.py` | 420 | 唯一配置面，构造即校验 | 非法组合**拒绝启动**，不静默取默认 |
| `multi_account/status.py` | 340 | 观测归一、健康分类、池化 | 坏观测不拖垮整池；观测故障与空池可区分 |
| `multi_account/budget.py` | 424 | 滚动窗口成本上限、预留/结算 | 拒绝只"挂起"并给出 `retry_at`；不可用测量降级不崩溃 |
| `multi_account/alerts.py` | 463 | 规则引擎、抑制、有界历史、JSONL 轮转 | 重复事实不重复告警；长跑磁盘有界 |
| `multi_account/watchdog.py` | 162 | 运行时长与空闲预算 | 到期只停止认领，不中断在飞工作 |
| `multi_account/policy.py` | 423 | 限幅权重链、审计、回滚 | 单步有界、总漂移有界、回滚本身可审计 |
| `multi_account/scheduler.py` | 382 | 账户选路、重路由、dead-letter | 学习分只在同一健康类内生效，不能越级 |
| `multi_account/evolution.py` | 375 | 单一原子状态文档（9 个分区） | 缺失分区不得在重启时被静默丢弃 |
| `multi_account/perception_sync.py` | 151 | Magpie 快照 → 观测表 | 只写白名单字段，不含凭据 |
| `multi_account/cli.py` | 142 | 运维只读视图 + 回滚 | 只读路径不产生副作用 |

---

## 4. 可配置项

共 57 项（55 个标量 + `account_routing` / `break_even_store_path` 两个自有变量），
全部可用环境变量设置并在构造时校验；`.env.example` 与代码中的映射表由测试相互约束。

| 组 | 代表配置项 | 默认值 | 说明 |
|---|---|---|---|
| 账户接入 | `REVERSE_AGENT_MULTI_ACCOUNT_ENABLED`、`..._STORE`、`REVERSE_AGENT_ACCOUNT_ROUTING` | 关闭 / 仓内路径 / `local` | 总开关、状态文档位置、选路归属 |
| 状态感知 | `..._FRESHNESS`、`..._MAGPIE_MAX_AGE`、`..._HIGH_UTILIZATION`、`..._RESET_SOON_SECONDS` | 1800 / 2400 / 90 / 1800 | 新鲜度与降级阈值 |
| 调度权重 | `..._RELIABILITY_WEIGHT`、`..._COST_WEIGHT`、`..._LATENCY_WEIGHT`、`..._SCORE_ALPHA` | 12 / 10 / 5 / 0.25 | 学习分的权重与平滑 |
| 重试与降级 | `..._REROUTE_ATTEMPTS`、`..._BACKOFF_BASE`、`..._BACKOFF_MULTIPLIER`、`..._BACKOFF_MAX`、`..._DEAD_LETTER` | 3 / 30 / 2 / 900 / 开 | 重路由与退避 |
| 隔离 | `..._ABNORMAL_COOLDOWN`、`..._COOLDOWN_MEMORY`、`..._PERSIST_STATE` | 300 / 21600 / 开 | 账户级隔离与重启恢复 |
| 成本上限 | `..._COST_BUDGET`、`..._COST_BUDGET_UNITS`、`..._COST_BUDGET_WINDOW`、`..._COST_BUDGET_SOFT_RATIO`、`..._COST_BUDGET_TASK_UNITS`、`..._COST_BUDGET_RESERVE_INFLIGHT`、`..._COST_BUDGET_RESERVATION_TTL` | 关 / 0 / 86400 / 0.8 / 0 / 关 / 900 | 开启时必须给正数上限 |
| 运行时长 | `..._WATCHDOG`、`..._MAX_RUN_SECONDS`、`..._MAX_IDLE_SECONDS`、`..._HARD_STOP_RATIO` | 开 / 0 / 0 / 1.25 | 0 = 不限 |
| 日志与告警 | `..._ALERTS`、`..._ALERT_QUIET`、`..._ALERT_MAX_HISTORY`、`..._ALERT_STREAK`、`..._ALERT_MIN_SUCCESS`、`..._ALERT_JOURNAL`、`..._ALERT_JOURNAL_MAX_BYTES` | 开 / 300 / 120 / 2 / 0.6 / 空 / 5MB | 抑制窗口、有界历史、本地 JSONL（拒绝 URL） |
| 自进化开关 | `..._SELF_EVOLUTION`、`..._SCORING`、`..._POLICY`、`..._CALIBRATION_FEEDBACK` | 开 / 开 / 开 / 开 | 各闭环独立开关 |
| 自进化限幅 | `..._POLICY_STEP`、`..._POLICY_DRIFT`、`..._POLICY_MAX_BONUS`、`..._POLICY_MIN_SAMPLES`、`..._POLICY_TARGET_SUCCESS`、`..._POLICY_AUDIT_ENTRIES` | 0.25 / 0.5 / 12 / 5 / 0.85 / 120 | 单步、总漂移、样本门槛、审计长度 |
| 生产选路（main 侧） | `..._FEEDBACK_ROUTING`、`..._FEEDBACK_ROUTING_MIN_ATTEMPTS`、`..._FEEDBACK_ROUTING_MAX_ADJUSTMENT` | 关 / 3 / 0.1 | 默认关闭，未由本轮改动 |

---

## 5. 验收结果

### 5.1 验收脚本（虚拟时钟，确定性种子）

`python scripts/multi_account_acceptance.py` → **11/11 PASS**，复现于合并后的树上：

| 验收标准 | 结果 | 证据 |
|---|---|---|
| 多账户整合 | PASS | 4/4 账户被实际调度（21/37/23/55 次） |
| 状态感知 | PASS | 全窗口零观测错误，每轮均获得账户/额度/成本视图 |
| 异常容错·任务不丢失 | PASS | 完成 118 + 隔离 0 + 待续 2 = 120 |
| 异常容错·切换/重试/降级生效 | PASS | 切换 36、重试 18、等待/降级 361 |
| 成本上限不被突破 | PASS | 花费 11.983 ≤ 上限 12.0（利用率 99.9%） |
| 连续运行·遵守运行时长 | PASS | 虚拟 19.19h 判定 conclude，待续 2 |
| 性能·控制环开销 | PASS | 每轮约 0.58 ms（498 轮，真实 0.29 s） |
| 反馈优化·健康池不误调 | PASS | 无压力时权重不变（版本 0） |
| 反馈优化·异常池驱动变更 | PASS | 失败类型/成本反馈驱动 6 次有界变更 |
| 反馈优化·未使结果劣化 | PASS | 后半程成本 0.1035 vs 基线 0.1208；重试率 0.0 vs 0.3043 |
| 可审计可回滚 | PASS | 审计 6 条，版本链 v1..v6 |

### 5.2 回归测试

- 多账户相关：**282 例**（`-k multi_account`），全绿。
- 本轮新增 **14 例**。9 例跨模块连续性覆盖：一次重启后成本窗口/告警抑制/策略版本/运行时钟全部恢复、
  重放回执只结算一次、冲突回执被拒绝、上限到期自动可再准入、回滚回到基线且留审计、
  告警日志有界轮转、到期收束、健康池不误调；4 例固定极端数值行为（超大整数 / NaN / inf /
  窗口内外区分）；1 例固定反馈快照在 1e308 量级仍有限且 JSON 可序列化。
- 受影响面回归（引用 `multi_account` / `unattended_coordinator` / `trusted_host` / 成本链路的 66 个测试
  文件，共 2184 例）：**2173 passed、11 failed、5 skipped**。11 例失败全部集中在
  `test_dev_up_contract.py`（依赖本机 PowerShell 宿主的 `dev_up` 脚本），在**未改动**的
  `origin/main` 上同样为 11 failed / 53 passed，属本机既有环境限制，与本轮改动无关。

### 5.3 本轮修掉的缺陷（都会在长跑中静默失效）

| # | 现象 | 根因 | 修复 |
|---|---|---|---|
| a | `10**400` 成本让准入/结算抛 `OverflowError` | `float()` 直接转换外部遥测 | 统一 `_finite_units`，不可用测量降级为"未知成本"，仍按预留计费并标记 unpriced |
| b | NaN 成本让上限比较失真 | NaN 参与比较恒为 False | 同上，NaN/inf 一律拒绝 |
| c | 合并后 3 组同名测试互相覆盖 | 两侧同名测试并入同一模块 | 去重，保留语义更强的版本 |
| d | 非法环境值静默回退默认（放宽限制） | `from_env` 吞掉解析错误 | 交回 pydantic 校验，部署**快速失败** |
| e | 1e308 级成本累加成 `inf`，整份反馈快照被路由器丢弃 | 新增累计总量无上限保护 | 总量在浮点上限前饱和，文档保持有限可比较 |
| f | 成本视图把"窗口内无花费"显示成"从未花费" | 只报 `spent_units` | 同时报 `records_in_window` / `records_total` |

### 5.4 本地实测口径与未完成项

- 本机（Windows，32 核）串行跑 `tests/platform_v1` 全量 6798 例约需数小时；`pytest-xdist`
  因仓库内 `object()` 参数化 ID 不可跨进程稳定而无法收集。
- 因此本地以"受影响面"（66 个测试文件）作回归口径，全量基线仍以 CI `baseline` 为准。
- **真实账户验收未做**：真实 Magpie 混合池、真实故障注入、宿主休眠恢复、24h/72h/7d 长跑
  均需对应环境的操作授权，本轮不宣称。
- 验收脚本的通过不等于真实省钱结论（其为虚拟时钟仿真，不含真实计费与网络抖动）。

---

## 6. 已知限制与扩展点

### 6.1 已知限制

1. **未部署、未启用**：`REVERSE_AGENT_MULTI_ACCOUNT_ENABLED` 默认关闭；开启后行为变化需在真实池复验。
2. **成本基准仍是列表价估算**：`usage_ledger` 给的是 list-price，不是账单现金；缺导出完整性证据时
   成本为 UNKNOWN 而非 0。
3. **单机语义**：状态文档是本地 JSON 原子替换，只防半文件，不提供跨进程事务或分布式租约。
4. **预留释放依赖 TTL**：协调器没有逐任务回执时，未结算的预留靠 TTL 过期释放（默认 900 s），
   因此并发上限的边界是"在飞窗口"而非严格单笔。
5. **策略链是规则驱动，不是学习器**：可解释、可回滚，但不会发现规则外的更优策略。
6. **Windows 本地全量回归未跑完**：见 §5.4；CI 基线以 Linux 为准。

### 6.2 扩展点（按性价比排序）

1. **真实池灰度**：先只开感知与告警（只读），再开成本上限（`deny` 只挂起不丢任务），最后开策略链。
2. **成本证据补全**：把 Magpie `usage` 导出完整性与本仓 `cost_report` 对账，把 UNKNOWN 降为可解释的少数。
3. **长跑验收**：24h → 72h → 7d，至少 3 次休眠唤醒、2 次强杀，核对任务、租约、成本三者一致。
4. **策略灰度**：在 `policy.py` 增加"影子评估"——记录提案但不生效，用真实数据比较提案与基线。
5. **多机**：若未来需要跨机并发，先把状态文档换成带租约的共享存储；在那之前不引入第二套队列。

---

## 复现

```bash
python scripts/multi_account_acceptance.py                      # 11/11 验收
python -m pytest tests/platform_v1 -k multi_account -q          # 282 例
python -m reverse_agent.platform_v1.multi_account.cli status     # 运维视图
```
