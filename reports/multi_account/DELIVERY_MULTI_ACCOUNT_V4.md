# 多额度账户统一纳管 · 优化与完善交付说明（v4）

生成时间：2026-11-05　分支：`agent/multi-account-magpie-reuse-c3`　基线：`39882f73`
口径：本文件只描述**本分支已实现且有测试/脚本可复核**的能力；未合并、未默认启用、未做真实账户长跑，
三者分开标注，不合并成"已完成"。

---

## 1. 实现变更摘要

本轮的目标不是再造一套调度，而是把前几轮**已实现但悬空**的能力接到真实派发路径上。
v3 的 `budget.py` / `watchdog.py` / `alerts.py` / `policy.py` 有 182 例回归测试，但
`start_run` / `run_verdict` / `drain_alerts` / `admit_cost` 在全仓**零生产调用方**（已 grep 复核）——
也就是说，"成本上限""运行时长""告警"在真实运行中的实际效力为零：模块正确，但没有任何人问它。

| # | 变更 | 文件 | 性质 |
|---|---|---|---|
| 1 | 协调器主循环接入 5 个可选接缝：运行计时窗口、有界裁决、成本准入、告警排空、进度心跳 | `reverse_agent/platform_v1/unattended_coordinator.py`（+148） | 接线 |
| 2 | 宿主按开关注入上述接缝，并提供有界告警尾巴 | `reverse_agent/platform_v1/trusted_host.py`（+65） | 接线 |
| 3 | `admit_cost` 增加 `reserve` 参数，**默认改为 False**；新增 `run_progress` 接缝 | `multi_account/dispatch.py` | 缺陷修复 |
| 4 | 配置面 16/43 → 48/50 可达，自进化限幅真正可从环境设置 | `multi_account/config.py` | 能力补齐 |
| 5 | `.env.example` 新增完整占位清单（48 个变量 + 3 个自有变量） | `.env.example`（+124） | 可运维性 |
| 6 | 新增 21 例回归（15 接线 + 6 配置/文档一致性） | `tests/platform_v1/test_multi_account_host_wiring.py`（新）、`test_multi_account_config.py` | 验收 |
| 7 | 规范追加 §14 并修正 §13.6 | `docs/architecture/MULTI_ACCOUNT_ORCHESTRATION_SPEC.md` | 文档 |

### 1.1 本轮修掉的缺陷（都会让"长跑无人值守"静默失效）

| # | 现象 | 根因 | 影响 | 修复 |
|---|---|---|---|---|
| 12 | 成本上限对真实派发**零约束** | `admit_cost` 无调用方 | 上限只是仿真里的数字 | 在 `authorize` 之后、`claim_task` **之前**准入；拒绝即本轮停止认领 |
| 13 | 运行时长上限**从不生效** | `start_run`/`run_verdict` 无调用方 | 无人值守只能靠人工 kill 或首个空闲退出 | 开跑计时、每轮派发前裁决；`conclude` 停认领但排空在飞批次 |
| 14 | 告警只入队、永不送达 | `drain_alerts` 无调用方 | `_pending` 积压且无人可见 | 每轮排空一次并投递宿主 sink |
| 15 | 账户解析失败时 watchdog 不心跳 | 心跳只搭在 `record_account_outcome` 上 | `max_idle_seconds` 会把**仍在完成工作**的运行判成空闲并收束 | 新增独立的 `run_progress`，与账户归因解耦 |
| 16 | `admit_cost` 默认 `reserve=True` 且无人结算 | 默认值与唯一调用场景不符 | 一旦接入即产生永不释放的预留，最终拒绝**每一次**派发 | 默认改 `False`，并在 `dispatch`/`.env.example` 写明理由 |

### 1.2 复用范围与替换边界（明确"不重复建设"）

| 类别 | 对象 | 处置 | 说明 |
|---|---|---|---|
| 复用 | Magpie CLI/只读端点 `quota` / `usage --csv` / `quota wait` | **复用**，只读观测 + 可选等待委托 | 不接管账户内切换；凭据不经过本仓 |
| 复用 | `durable_execution`（租约 fencing / 崩溃恢复）、`control_store`（claim / 预算 / 窗口）、`quota_reservation`（准入 / 标定 / 结算） | **复用**，不改语义 | 新接缝只在它们**前后**插入，不做并行实现 |
| 复用 | `orchestration_selector.break_even`、`quota_reservation.delta_calibration` | **复用算法**，只补持久化与反馈回路 | 未重写任何已测算法 |
| 复用 | `pydantic` | **复用** | 仅新模块；未重写既有手写校验 |
| 新增（仅补缺） | `multi_account/budget.py`、`watchdog.py`、`alerts.py`、`policy.py` | **新增** | 仅标准库 + 既有 pydantic，零新第三方依赖 |
| 不引入 | Celery/RQ/Dramatiq、Temporal/DBOS/Prefect、Ray、第二套重试队列 | **不引入** | 与既有单机租约/预算语义重叠；引入即第二编排脊柱 |
| 不替换 | `NATIVE_CLI_PROVIDERS` 原生 CLI 自持登录 | **保留不动** | 属逐步退出层，不作为扩容目标 |
| 不改动 | `AGENTS.md` 治理规则、`.github/workflows/**`、`landing_review.py` | **不改** | R2，需 Owner 决策 + 独立评审 |

---

## 2. 功能边界

### 2.1 已实现（本分支，默认关闭）

- **多账户统一纳管**：按 `account_ref` 保留每账户独立额度窗口，不再按 provider 静默覆盖；同 provider 多账户可池化。
- **状态感知**：健康度七态（HEALTHY / DEGRADED / EXHAUSTED / ABNORMAL / STALE / UNKNOWN / reset_soon），含余量、新鲜度、异常标记、重置时刻。
- **异常容错**：有界重路由、双层冷却（任务级瞬时 + 账户级隔离）、指数退避封顶、dead-letter 留证、重启恢复隔离与评分。
- **成本限制**：滚动窗口上限（`allow` / `degrade` / `deny`），软阈值转最低成本账户，硬上限一律等待不超支。
- **运行时长**：单次运行墙钟预算 + 空闲预算；`conclude` 停认领、`stop` 为硬升级；在飞批次始终排空。
- **告警**：规则化生成 + `(code, subject)` 去重静默 + 有界历史 + 宿主投递点。
- **自进化**：账户级 EWMA（可靠性/成本/时延）与池级策略链；变更**有界步长 + clamp + 审计 + 按版本回滚**。

### 2.2 明确不做

- 不读取、转存或中转任何 provider 凭据（账户身份仅以 `acct_<sha256前12>` 落盘）。
- 不做自动 merge / 发布 / 打标签（R3，需 Owner 显式指令）。
- 不实现通用强化学习；自进化限于有界、可解释、可回滚的参数校准，且**不得**修改结构性旋钮（重路由次数、冷却时长、隔离语义、健康度排序优先级）。
- 不引入第二编排框架、作业队列或分布式计算层。
- 不改变浏览器端权限边界（仍无 shell / 文件系统 / 凭据 / 合并权）。

### 2.3 开关语义（三层，缺一不启用）

| 层 | 开关 | 默认 | 作用 |
|---|---|---|---|
| 总开关 | `REVERSE_AGENT_MULTI_ACCOUNT_ENABLED=1` | 未设置 | 未设置时宿主注入 `{}`，协调器构造与旧版逐位一致 |
| 账户归属 | `REVERSE_AGENT_ACCOUNT_ROUTING` = `local`\|`magpie`\|`auto` | `local` | `auto` 需 **两把锁**：`REVERSE_AGENT_MAGPIE=1` 且 `REVERSE_AGENT_MAGPIE_ACCOUNT_SWITCHING=1` |
| 单能力 | `cost_budget_enabled` / `max_run_duration_seconds` / `alerts_enabled` … | 全部保守关闭 | 单项开启不影响其他项 |

---

## 3. 关键模块

| 模块 | 职责 | 边界（不做什么） |
|---|---|---|
| `multi_account/status.py` | 账户/窗口状态感知与多账户池化；`pool_account_quotas` 是多账户合并的即用替换 | 不做调度决策 |
| `multi_account/scheduler.py` | 账户感知选账户；有界重路由 + dead-letter；预算准入前置；`retry_at` | 无 I/O，不派发 |
| `multi_account/cooldowns.py` | 双层冷却、指数退避、隔离期、快照/恢复 | 不碰凭据，不做派发 |
| `multi_account/scoring.py` | 账户级 EWMA → headroom 等值加减分；失败类型直方图 | 不做通用 RL，不做绝对成本建模；**只在一个健康度档位内重排** |
| `multi_account/budget.py` | 滚动窗口成本上限；预留/结算；`retry_at` 精确到"哪笔花费滚出窗口" | 不定价、不调额度；禁用即全量 `allow` |
| `multi_account/alerts.py` | 规则化告警 + 去重静默 + 有界历史；sink 注入 | 不做网络投递（webhook 为宿主扩展点） |
| `multi_account/watchdog.py` | 运行时长 / 空闲判定；`remaining_seconds` 供定长休眠 | 不自己取消任务（取消语义留在 `durable_execution`） |
| `multi_account/policy.py` | 策略版本链：有界步长、clamp、审计、按版本回滚 | 不改结构性旋钮；不做通用 RL |
| `multi_account/evolution.py` | `break_even` 持久化 + 反馈进 `select_orchestration`；可选 `delta_calibration` | 不重写既有算法 |
| `multi_account/config.py` | 集中校验；启动快速失败；**全字段环境可达**；无密钥入库 | 不读凭据 |
| `multi_account/dispatch.py` | 受保护接缝层：每个入口失败即降级到旧行为（fail-open），绝不阻塞派发 | 不做业务决策 |
| `multi_account/__init__.py` | `MultiAccountOrchestrator` 门面：组合感知 + 调度 + 预算 + 告警 + 运行时长 + 策略 | 不引入第二编排脊柱 |
| `unattended_coordinator.py` | **本轮新增接线**：运行窗口、有界裁决、成本准入、告警排空、进度心跳 | 接缝全部可选，未注入即旧行为 |
| `trusted_host.py` | 宿主注入点 + 有界告警尾巴 `multi_account_alerts()` | 未启用时零注入 |

数据流（一轮控制环）：

```text
感知 perceive(快照) → 状态/池化 → 成本准入 admit ─┬─ deny → 本轮停止认领（hold，不丢弃）
                                                └─ allow/degrade → 选账户 → claim → 执行
执行终态 → 账户反馈（冷却/评分/成本结算/心跳） → 策略评估（有界步长+审计）
        → 告警入队 → 下一轮排空 → 宿主 sink（内存尾巴 / 可选日志 / 可替换 webhook）
每轮派发前：run_verdict → continue | conclude（停认领，排空在飞）| stop
```

---

## 4. 可配置项

全部通过环境变量设置，前缀 `REVERSE_AGENT_MULTI_ACCOUNT_`；完整占位清单见 `.env.example`。
`test_every_knob_is_reachable_from_the_environment` 与 `test_the_env_example_documents_every_variable`
钉住"模型字段 ⇄ 环境变量 ⇄ 文档"三者不漂移。

| 类别 | 主要键 | 默认 | 说明 |
|---|---|---|---|
| 接入/归属 | `ENABLED`、`STORE`、`REVERSE_AGENT_ACCOUNT_ROUTING` | 关 / 默认运行时目录 / `local` | 总开关、本地账本路径、账户归属 |
| 额度阈值 | `FRESHNESS`、`MAGPIE_MAX_AGE`、`HIGH_UTILIZATION`、`RESET_SOON_SECONDS`、`SMALL_TASK_CEILING` | 600s / 900s / 90% / 1800s / 1.0 | 新鲜度、降级阈值、临重置、小任务上限 |
| 调度与重试 | `REROUTE_ATTEMPTS`、`REROUTE_COOLDOWN`、`ABNORMAL_COOLDOWN`、`BACKOFF_BASE/MULTIPLIER/MAX`、`COOLDOWN_MEMORY`、`DEAD_LETTER` | 3 / 30s / 300s / 30s·2x·900s / 21600s / true | 有界重路由、双层冷却、退避封顶、终态隔离 |
| 调度权重 | `RELIABILITY_WEIGHT`、`COST_WEIGHT`、`LATENCY_WEIGHT`、`SCORE_ALPHA`、`SCORING` | 12 / 10 / 5 / 0.25 / true | 实测反馈折算为 headroom 等值分 |
| 成本上限 | `COST_BUDGET`、`_UNITS`、`_WINDOW`、`_SOFT_RATIO`、`_TASK_UNITS`、`_RESERVATIONS` | false / 0 / 86400s / 0.8 / 0 / true | 启用时必须给正上限，否则启动失败 |
| 运行时长 | `WATCHDOG`、`MAX_RUN_SECONDS`、`MAX_IDLE_SECONDS`、`HARD_STOP_RATIO` | true / 0（不限）/ 0（不限）/ 1.25 | 0 = 不限 |
| 日志与告警 | `ALERTS`、`ALERT_QUIET`、`ALERT_MAX_HISTORY`、`ALERT_STREAK`、`ALERT_MIN_SUCCESS`、`ALERT_MIN_SAMPLES`、`ALERT_LOG` | true / 300s / 120 / 2 / 0.6 / 3 / false | 去重窗口、有界历史、抖动阈值、日志开关 |
| 自进化开关 | `SELF_EVOLUTION`、`CALIBRATION_FEEDBACK`、`MIN_MODE_OBSERVATIONS`、`MAX_RECORDED_RUNS` | true / true / — / 500 | 账本有界，长跑不无限增长 |
| 自进化限幅 | `POLICY`、`POLICY_STEP`、`POLICY_DRIFT`、`POLICY_MAX_BONUS`、`POLICY_MIN_SAMPLES`、`POLICY_TARGET_SUCCESS`、`POLICY_AUDIT_ENTRIES` | true / 0.25 / 0.5 / 12 / 5 / 0.85 / 120 | 单步上限、总漂移上限、加分硬截断、样本门槛、审计容量 |

回滚动作：删除账本文件的对应段（`budget` / `cooldowns` / `accounts` / `policy` / `watchdog`）即回到纯余量调度；
或在 API 侧调用 `rollback_policy(n)`（`0` = 配置基线），每次回滚本身也入审计。

---

## 5. 验收结果

### 5.1 回归测试

```text
tests/platform_v1/test_multi_account_*.py                    225 passed
  ├─ test_multi_account_host_wiring.py（本轮新增）             24 passed
  ├─ test_multi_account_perception_sync.py（agent 产出，监督复跑） 10 passed
  ├─ test_multi_account_config.py（本轮 +6）                    21 passed
  └─ test_multi_account_alerts.py（本轮 +3，perception_partial）22 passed

协调器 / 宿主组合（6 文件：trusted_host, unattended_coordinator,
  coordinator_dynamic_refill, coordinator_shutdown, startup_reconcile,
  agent_escalation）                                          227 passed, 3 skipped

额度 / 目标 / 任务服务（9 文件：confirmed_quota_admission, goal_service,
  quota_forecast, quota_hold_reroute, quota_inflight_checkpoint,
  quota_inflight_wiring, quota_reservation, resource_account_attribution,
  task_service）                                              417 passed（84 s）
```

> `tests/platform_v1` 全目录串跑在本机超过 43 分钟未收敛（socket/HTTP 与 durable 用例拖慢，
> 与此前记录的沙箱 SIGTERM 现象一致），故按"改动所在面"分组取证，未以"全绿"表述。

### 5.2 24h 虚拟时钟验收（可复现）

```bash
python scripts/multi_account_acceptance.py     # 种子 7，虚拟时钟 24h，4 个场景
```

`11/11 PASS`（`reports/multi_account/acceptance_latest.md`）：

| 验收标准 | 结果 | 证据 |
|---|---|---|
| 多账户整合 | PASS | 4/4 账户实际承担任务（21/37/23/55 次） |
| 状态感知 | PASS | 全窗口零观测错误，每轮均获得账户/额度/成本视图 |
| 异常容错·任务不丢失 | PASS | 完成 118 + 隔离 0 + 待续 2 = 120 |
| 异常容错·切换/重试/降级 | PASS | 切换 36 次、重试 18 次、等待/降级 361 次 |
| 成本上限不被突破 | PASS | 花费 11.983 ≤ 上限 12.0（利用率 99.9%） |
| 连续运行·遵守运行时长 | PASS | 虚拟 19.19h 后按 `conclude` 收束，待续 2 |
| 性能·控制环开销 | PASS | 每轮约 0.35 ms（498 轮真实耗时 0.17 s） |
| 反馈优化·健康池不误调 | PASS | 无压力时不改权重（版本 0） |
| 反馈优化·异常池驱动变更 | PASS | 失败类型/成本驱动 6 次有界变更（v1..v6） |
| 反馈优化·未使结果劣化 | PASS | 后半程成本 0.1035 vs 0.1208；重试率 0.0 vs 0.30 |
| 可审计可回滚 | PASS | 审计 6 条（含 `changed_keys`），版本链可回滚 |

### 5.3 用户要求的验收项 → 证据映射

| 要求 | 证据 | 状态 |
|---|---|---|
| 多账户整合 | 池化按 `account_ref` 保留（`test_pool_account_quotas_preserves_all_accounts`）+ 4/4 账户均被调度 | 达成 |
| 状态感知 | 七态 `AccountStatus` + 感知失败降级为 `UNKNOWN(perception_error)` 且发告警 | 达成 |
| 异常容错 | 重路由/隔离/退避/dead-letter/重启恢复（`test_quarantine_and_scores_survive_a_restart` 等） | 达成 |
| 连续运行 | 运行预算收束 + 在飞排空（`test_a_conclude_verdict_lets_work_in_flight_land`）+ 24h 仿真 | 达成（虚拟时钟） |
| 成本与性能达标 | 上限 99.9% 利用率不越界；控制环 0.35 ms/轮 | 达成（仿真的真实耗时） |
| 反馈优化有效 | 异常池 6 次有界变更且未劣化；健康池零变更 | 达成 |
| 维护与扩展便利 | 单文件单职责 + 三个总开关 + 全字段环境可达 + `.env.example` + 审计/回滚 | 达成 |
| 策略可配置/可审计/可回滚 | 限幅全部环境可达；`policy_audit` 含 `changed_keys`；`rollback_policy(n)` | 达成 |

---

## 6. 真实账户验收（2026-11-05，Owner 授权后新增）

前五节全部建立在合成账户与虚拟时钟上。在 Owner 授权真实账户后补做了真实验收，
它推翻了"感知已闭环"的判断，并暴露三个真实缺口：

| # | 真实证据 | 影响 | 修复 |
|---|---|---|---|
| R1 | `platform_quota_observations` **0 行**；该表只在 `claim_task` 准入路径内被写 | 首次派发前感知**全盲**：Magpie 报 11 个账户，大脑看到 0 个 | `control_store.record_quota_observation(s)`（`observed_at` 单调）+ `perception_sync.py` + 宿主 `sync_multi_account_observations()` |
| R2 | 惰性读数 + 600 s 保鲜期；只同步一次则全池老化 | 可用账户数实测从 **7 衰减到 1** | 协调器 `pool_refresh` 接缝，按 reconcile 节奏刷新（60 s 去抖）；网络请求**不进**感知/路由路径 |
| R3 | 规则只在"全部 STALE/UNKNOWN"时告警 | 4/11 不可用（36%）时完全静默 | 新增 `perception_partial` 告警 |

**真实池**：11 账户 / 11 provider（claude、codex、copilot、minimax-code、
opencode-zen-free、openrouter、raccoon、trae-cn、workbuddy、workbuddy-ai、zcode）。

**真实调用**（每账户一次最小请求）：

| 账户 | 结果 | 墙钟 | 计费 |
|---|---|---|---|
| claude-code | 成功 | 8.2–12.6 s | $0.00228–0.00432（CLI 上报） |
| codex | 成功 1 / 超时 2 | 22.2 s | 未上报 → `priced=false`，入账不当免费 |

**真实 30 天经济性**：5502 调用 / 194 错误 / 43 重试 / **$58.6993** / 未计价 2338。
账户错误率 0.857、0.420、0.044、0.031、0.024、0.019、0.003、0.002；全池成功率 0.9647。

**真实验收 11/11 PASS**（`scripts/multi_account_real_acceptance.py --live`，
报告 `real_acceptance_latest.md`）：整合、感知、调度、容错（对真实 0.857 错误率账户注入故障
后切换）、真实调用、未知成本、上限（真实花费基线）、告警、自进化双向（健康池不改 / 压力下
v2 且可回滚）、真实时钟运行上限。探针花费 **$0.00228**。

**"系统改自己"**：`perception_sync.py` + 测试由平台自己的 `claude` 执行器写出（13 轮，
$0.0182）；它无法自测，由监督者复核并补齐控制库写入、宿主同步、刷新节奏与告警规则。

## 7. 已知限制与扩展点

### 7.1 已知限制（诚实清单）

1. **未合并、未默认启用**。所有能力在 `REVERSE_AGENT_MULTI_ACCOUNT_ENABLED=1` 后生效；未启用时行为逐位等价旧版。
2. **真实证据仍是单轮，不是长跑**。§6 覆盖 11 个真实账户的单轮感知/调度/容错/调用/成本，
   但没有数小时无人值守 + 真实故障注入的长跑证据；24h 那轮仍是**虚拟时钟仿真**。
3. **成本口径为列表价估算**。`cost_units` 基于列表价，不是账单；真实 30 天 $58.6993 是
   Magpie 的列表价合计。`magpie_usage_ingest` 期望的 CLI 在本机不存在（安装只有 GUI +
   HTTP `/v1/magpie/usage`），切现金口径属**口径变更**，需 Owner 决策。
4. **预算不含并发预留**。宿主不携带 per-task token，故上限约束"已发生花费"而非"已发生 + 在飞"；超出上界不超过一个在飞批次的成本。带 token 的预留式防超支需要贯穿 claim→settle 及全部 abandon 路径，漏一条即永久锁死预算，故单列。
5. **告警默认只到内存尾巴 + 可选日志**。IM/webhook 需替换宿主 sink；`_pending` 不持久化，崩溃前未排空的告警会丢（窗口已缩到一轮循环）。
6. **C3 租约与休眠恢复未做**。`standby_keepalive_interval_seconds` 尚未接入 `durable_execution` 租约对账（[C3 项目](C3_LEASE_RECOVERY_PROJECT.md)），因会触碰 fencing 语义而单列。
7. **账户切换行为未实测**。本机 Magpie 是 GUI 版（`0.1.2945`，只有 loopback HTTP，无 CLI），
   仓库里 `quota wait` / `accounts switch` 的 CLI 前提不成立；`REVERSE_AGENT_MAGPIE_WAIT_TARGET`
   因此无效。切换仍靠本仓调度，`auto` 归属需第二把锁显式确认。
8. **全量测试未在本机跑完**。全仓 `pytest` 先触发 pytest 内部 `MemoryError`（源码解析阶段，非用例失败）；
   `tests/platform_v1` 单独串跑 43 分钟未收敛（socket/durable 用例）。故本轮以"改动所在面"分组取证
   （见 §5.1），未以"全量通过"表述；CI 侧需以 `baseline` / `state-gate` 为准。

### 7.2 扩展点

| 方向 | 接入点 | 前置条件 |
|---|---|---|
| 真实账单成本口径 | `usage_ledger` → `budget.cost_units` | Owner 口径决策 + 独立评审；两份口径先并列报告 |
| 预留式并发防超支 | `dispatch.admit_cost(reserve=True)` + 按 task_id 贯穿 settle/release | 全部 abandon 路径覆盖 + 故障注入验证 |
| 告警投递 | `CombinedTrustedHost._deliver_account_alerts` | 替换为 webhook/IM，需网络依赖审批（当前刻意不引入） |
| 额度窗口重置纳入空闲等待 | `AccountStatus.next_reset_at` → `idle_wait_seconds` | 与冷却 hint 合并取最早 |
| 休眠主机租约对账 | `durable_execution.reconcile_expired_runs` | C3 项目立项与评审 |
| 新 provider 扩容 | `subscription_quota._MAGPIE_PROVIDER_KEYS` | **必须有真实观测证据**，禁止"看起来支持"就加键 |
| 新调度维度 | `scoring.py` 权重 + `policy.py` 规则 | 保持"健康度优先于省钱"不变式与 clamp 上限 |

---

## 复现命令

```bash
python -m pytest tests/platform_v1/test_multi_account_*.py -q          # 225 passed
python -m pytest tests/platform_v1/test_multi_account_host_wiring.py -q # 24 passed
python scripts/multi_account_acceptance.py                             # 11/11 PASS（虚拟时钟 24h）
python scripts/multi_account_real_acceptance.py --live                 # 11/11 PASS（真实账户）
python -m reverse_agent.platform_v1.cost_report --doctor --last 7d      # 对照实验自检
```

## 关联文档

- [多账户调度与自进化架构规范](MULTI_ACCOUNT_ORCHESTRATION_SPEC.md)（§14 为本轮接线记录）
- [Magpie 能力审计](MAGPIE_CAPABILITY_AUDIT_2026-11-04.md)
- [C3 租约与恢复一致性项目](C3_LEASE_RECOVERY_PROJECT.md)
- [AGENTS.md](../../AGENTS.md) —— 治理、风险分层与发布边界
