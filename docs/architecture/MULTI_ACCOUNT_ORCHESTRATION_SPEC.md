# 多额度账户统一调度与自进化架构规范

> 当前状态以 [交付边界与验收状态](MULTI_ACCOUNT_DELIVERY_STATUS.md) 为准。
> 下文为历史阶段记录，含已被独立审查否定的闭环/接线声明，不作为验收证据。

```text
STATUS: LOCAL IMPLEMENTATION ONLY — NOT MERGED, NOT ENABLED, NOT FIELD-VALIDATED
AUTHORITY: PLANNING_REFERENCE_ONLY
BASE_MAIN: 96cbe519a8b9d8cdb14fa1738cd0f692a168063b
IMPLEMENTED: reverse_agent/platform_v1/multi_account/ (+ tests/platform_v1/test_multi_account_*.py)
REVIEW RESPONSE: docs/architecture/MULTI_ACCOUNT_PLAN_REVIEW_RESPONSE.md
```

> **状态口径（2026-11-04 评审后修正）**：六个阶段不得合并成"已完成"。
>
> | 阶段 | 现状 |
> |---|---|
> | 设计完成 | ✅ 本文件 |
> | 本地实现 | ✅ 但目录仍为 untracked |
> | 本地测试通过 | ✅ `pytest -k multi_account` 83；`vitest` 602；`tsc` 干净 |
> | 合并 `main` | ❌ |
> | 生产路径启用 | ❌ flag 默认关闭 |
> | 真实场景验收 | ❌ 无真实账户/故障注入/长跑证据 |
>
> 因此下文中"已落地/已接入"一律读作"本地实现且本地测试通过"。评审的逐条处置见
> [评审回应](MULTI_ACCOUNT_PLAN_REVIEW_RESPONSE.md)。

> 本文件是**规划参考**，不是治理授权。它不批准任何删除、重构、合并或 R2/R3 动作；
> 每一项落地仍需按其风险分层走 `AGENTS.md` 的变更流程与独立评审。
> 事实分类遵循 `CURRENT_ARCHITECTURE_BASELINE.md` §8：已落地能力以 exact `main` 提交为准，
> 分支能力以 exact head + 证据为准，二者不得混同。
>
> 本轮已新增一个**接线层**包 `reverse_agent/platform_v1/multi_account/`，复用既有成熟资产
> （`magpie_account_quotas` / `quota_reservation` / `orchestration_selector` / `durable_execution`），
> 不引入第二编排脊柱、不重写既有算法。包内 31 个回归测试全部通过。剩余为**派发路径接线**
> （将感知/调度/自进化接到 `trusted_host`、`goal_service` 与前端），仍按 R1 走独立评审。

## 1. 定位与不变的核心目标

核心目标保持不变（`AGENTS.md` 与 baseline §1）：

- 产品身份：**local-first 无人值守软件工程执行基底**，带仓库自有的策略/证据边界。
- 终极目标：在**预授权边界内**，落地经独立验证的变更，而无需逐 PR 的人工仪式。
- 治理分层 R0–R3、独立评审、证据化落地、有界窗口 —— 本轮优化**不得削弱**其中任何一项。

本轮优化聚焦用户要求的五个能力域：

```text
A 多额度账户统一整合与调度
B 账户与额度状态感知
C 故障/额度不足/账户异常下的稳定执行
D 高性价比 · 长时间 · 不间断 · 无人值守
E 自进化（依任务结果与运行反馈优化调度/容错/资源利用/执行策略）
```

## 2. 复用优先原则（避免重复建设）

沿用 baseline §1 已确立的原则：

> 自研差异化只放在 **policy / evidence / verification / recovery / task truth /
> publication boundary / 高层能力编排**；其余优先复用成熟外部运行时。

### 2.1 处置决策（disposition）

沿用 `ARCHITECTURE_SPINE_REUSE_INVENTORY.md` 的 `KEEP / ADAPT / DEFER / ARCHIVE_CANDIDATE`
四态。本轮**不新增第四套兼容层**（baseline §9 现代化不变量）。

### 2.2 明确不引入（重复建设红线）

> **2026-11-04 评审修正**：以下为**当前不替换**，不是**架构定论**。每一项都附带"何时才重新评估"的
> 触发条件；在此之前迁移属于无证据的提前优化。

| 候选 | 当前判定 | 理由 | 重新评估的触发条件（需全部满足） |
|---|---|---|---|
| Celery / RQ / Dramatiq | 当前不引入 | 与已落地的 `durable_execution.py` + 租约 fencing + `unattended_coordinator` 语义重叠 | 出现跨机队列需求，且本地单机方案无法表达 |
| Temporal / DBOS / Prefect / Airflow | 当前不替换 | 引入第二编排脊柱违反 baseline §4（已选定 LangGraph）；但 LangGraph 的检查点不等于完整的工作流恢复 | 故障注入下出现**可复现**的丢任务或重复执行，且修复成本 > 迁移成本 |
| Ray | 不引入 | 本地单机场景，无分布式计算需求 | 单机并发成为实测瓶颈 |
| 自研第二套重试/队列层 | 仍禁止 | 现有 `retry_budget` / `quota_inflight` / claim renewal 已覆盖 | — |

### 2.3 允许引入的成熟依赖（低风险、横切能力）

仅在**当前确为空白**的横切能力上引入，且必须是"补缺"而非"替换"：

| 依赖 | 用途 | 前提 |
|---|---|---|
| OpenTelemetry SDK / Prometheus client | 统一可观测（当前无统一指标面） | 新增，不替换现有日志 |
| `pydantic` / `pydantic-settings` | 配置集中校验 + 启动快速失败 | 仅新模块；不重写现有手写校验 |
| `structlog` | 结构化 JSON 日志 + 请求 ID 贯穿 | 渐进，不改既有 logging 语义 |

### 2.4 内部已有资产：优先"接线"而非"重写"

这是本轮最重要的结论。**已有成熟算法因缺接线而闲置，是最大的隐性重复建设**：

- `orchestration_selector.py` 的 `break_even` / `update_break_even`：算法与测试完备，
  但**全仓仅出现在该文件自身**（已核实零生产调用、零持久化）→ 属"孤儿能力"。
- `model_access/magpie_usage.py`：任务级账户归因已实现，**零生产调用方**。
- `cost_quality_benchmark.py`：同样零生产引用。

> 做自进化时**不得重写这些算法**，应先补持久化与反馈回路。

## 3. 家底盘点（架构决策的事实基础）

| 能力域 | 现有实现 | 状态 | 缺口 |
|---|---|---|---|
| 额度观测 | `model_access/subscription_quota.py`、`magpie.py`、`quota_forecast.py`、`quota_reservation.py`（settlement / delta_calibration） | **成熟**，有测 | freshness 分散 |
| 账户归属 | `resources.py::_account_attribution`（五态：route_bound / no_route_identity / ambiguous_* / unobserved） | **已落地**（`test_resource_account_attribution.py`） | 前端完全不消费 |
| **多账户识别（三层）** | ①成本分类 `routing_inputs.py:28 GATEWAY_COST_CLASSES`：**10 个命名空间**，workbuddy / workbuddy-ai / trae-cn / copilot / codex / claude 均为 `subscription`；②额度观测归一 `subscription_quota.py:353 _MAGPIE_PROVIDER_KEYS`：**7 个别名**（codex/openai/chatgpt/claude-code/claude_code/anthropic/claude）→ 归一到 **2 个路由键**；③原生 CLI `contracts.py:89 NATIVE_CLI_PROVIDERS`（codex/claude-code，**逐步退出层**） | ①成熟 ②**缺口** ③legacy 退场中 | 额度观测仅归一到 codex/claude，其余 subscription 账户的窗口**无法进入准入决策**（`magpie_route_provider` 返回 `None`，仅作账户级遥测） |
| **账户↔路由绑定** | Connection 无 `account_ref` 持久字段；`trusted_host.py:870` 退化为 `connection_id` | **实际不存在** | Magpie `account_ref` 在派发路径被覆写丢弃 |
| **多账户池化** | `trusted_host.py:1048 _merge_magpie_quotas` 按 provider 逐键覆盖 `merged[key] = quota` | **最大缺陷** | 同 provider 多账户的独立窗口证据丢失 |
| 准入/调度 | `quota_reservation.py`（admission / task_need / window_need / goal_fit）、`quota_guard.py`、reroute | **成熟** | 与多账户联动弱 |
| 无人值守 | `autonomy.py`（单窗≤7d / standing≤90d）、`unattended_coordinator.py`、`durable_execution.py`（租约 fencing/崩溃恢复） | **成熟** | host sleep/休眠恢复**缺失** |
| 容错 | `goal_service.reroute_quota_held`、`fallback_ladder`、retry budget、`active_cancel.py` | **成熟** | dead letter / quarantine **零命中**；orphan claim 仅诊断（docstring 明示 NOT a reconciler） |
| 自进化 | `delta_calibration` / `attributable_calibration`（唯一闭环）、`capability_benchmarks` → `model_router` | 部分闭环 | `break_even` 无持久化、无回路 |

### 3.1 三层账户模型（边界澄清）

"多账户"在不同层含义不同，混淆它们会导致扩错层。实际 Connections 有 10 个 provider：

| 层 | 模块 | 回答的问题 | 现状 |
|---|---|---|---|
| ①成本/路由分类 | `routing_inputs.py:28 GATEWAY_COST_CLASSES`（10 个命名空间） | 这个账户按什么成本模型计费？ | **已识别** workbuddy / workbuddy-ai / trae-cn / copilot / codex / claude 为 `subscription` |
| ②额度观测归一 | `subscription_quota.py:353 _MAGPIE_PROVIDER_KEYS`（7 别名 → 2 路由键） | 这个账户的额度窗口能否进入准入决策？ | **真正缺口**：仅归一到 codex / claude |
| ③原生 CLI 自持登录 | `contracts.py:89 NATIVE_CLI_PROVIDERS` | CLI 自己持有登录态、Nerelan 不碰凭据 | **legacy，逐步退出** |

实际账户构成（两类语义不同，不可混为一谈）：

- **订阅型**（有额度窗口/套餐，需额度感知与池化调度）：Claude Code(Pro)、Codex(ChatGPT Plus)、Copilot(GitHub Education)、ZCode(Start Plan)、**WorkBuddy**、**WorkBuddy AI**
- **API key 按量型**（无订阅窗口，走成本而非额度）：Groq、OpenRouter、商汤 SenseNova、agnes

因此本轮缺口**不是"系统只认识两个账户"**（层①已识别 6 个 subscription 命名空间），而是：

1. **层②归一不足**：Copilot / ZCode / WorkBuddy / WorkBuddy AI 有真实订阅窗口，却因
   `magpie_route_provider()` 返回 `None` 而只作账户级遥测，**进不了准入决策**。
2. **同 provider 多账户被砍**：`magpie_quota_windows` docstring 明示 "One account is chosen
   per provider"——`WorkBuddy` 与 `WorkBuddy AI` 两个真实账户只会保留余量最小的一个，
   无法池化。这与层②归一不足叠加，是当前多账户调度的主要损失面。

## 4. 功能边界

### 4.1 In Scope（本轮做）

1. **账户注册表**：Connection/ConnectionV3 增加 `account_ref` 持久字段 + 与 Magpie `account_ref` 双向绑定；派发路径不再退化为 `connection_id`。
2. **多账户池化**：`_merge_magpie_quotas` 保留 per-account 证据（复用已实现的 `magpie_account_quotas`），不再按 provider 静默覆盖。
3. **额度观测归一扩容**：只扩 `_MAGPIE_PROVIDER_KEYS`，使其覆盖 `GATEWAY_COST_CLASSES` 中已标为 `subscription` 的命名空间（workbuddy / workbuddy-ai / trae-cn / copilot 等），须有真实观测证据，不得臆造。**`NATIVE_CLI_PROVIDERS` 是逐步退出层，不作为扩容目标**（见 §5）。
4. **任务级归因接线**：`magpie_usage` 接入生产调用，闭环任务级用量归因。
5. **自进化回路**：`break_even` 增加持久化 + 接入调度决策，使 single vs agent_team 选择由实测反馈驱动。
6. **容错补缺**：dead letter 与 quarantine 机制（当前零命中）；host sleep 恢复后租约不误 fence。
7. **前端消费**：`resources.ts` 渲染 `account_attribution`（当前完全不消费）。

### 4.2 Out of Scope（明确不做）

- 不读取、转存或中转任何 provider 凭据（沿用 `contracts.py:86` 原生 CLI 自持登录原则）。
- 不引入第二编排框架 / 作业队列（§2.2）。
- 不做自动 merge / 发布授权（R3，需 Owner 显式指令）。
- 不实现通用强化学习框架；自进化限于**有界、可解释、可回滚的参数校准**。
- 不新增第四套兼容层（baseline §9）。
- 不修改 `AGENTS.md` / `.github/workflows/**` / `landing_review.py`（R2，需单独授权）。

## 5. 关键模块

| 域 | 模块 | 职责 | 本轮 disposition |
|---|---|---|---|
| A | `model_access/contracts.py` | provider/executor 契约；`NATIVE_CLI_PROVIDERS` 为原生 CLI 自持登录的**遗留层，逐步退出** | **DEFER**（不扩、不依赖；新能力走 Connection/Binding） |
| A | `model_access/store.py` | Connection/Binding 持久化 | **ADAPT**（增 `account_ref`） |
| A | `platform_v1/trusted_host.py` | 派发与额度合并 | **ADAPT**（修 `_merge_magpie_quotas` + 绑定） |
| B | `model_access/subscription_quota.py` | 窗口/额度解析 | **KEEP** |
| B | `model_access/resources.py` | 账户归属五态 | **KEEP**（补前端消费） |
| B | `platform_v1/quota_reservation.py` | 准入/标定/结算 | **KEEP** |
| C | `goal_service.py` / `model_router.py` / `fallback_ladder.py` | 重路由/降级 | **KEEP** |
| C | *(新增)* dead letter / quarantine | 终态失败隔离与留证 | **ADAPT**（新建，最小面） |
| D | `autonomy.py` / `unattended_coordinator.py` / `durable_execution.py` | 有界窗口/无人值守/崩溃恢复 | **KEEP**（补 host sleep） |
| E | `platform_v1/orchestration_selector.py` | single vs team 选择 | **ADAPT**（补持久化+回路，**不重写算法**） |
| E | `platform_v1/quota_reservation.py::delta_calibration` | 用量→成本率校准 | **KEEP**（唯一已闭环通路） |
| **A/B 新增** | `platform_v1/multi_account/status.py` | 账户/额度**状态感知** + 多账户池化（每账户保留，不按 provider 覆盖）；`pool_account_quotas` 是 `_merge_magpie_quotas` 的**即用替换** | **ADDED**（接线层，31 测试） |
| **B/C/D 新增** | `platform_v1/multi_account/scheduler.py` | **账户感知调度**：按余量/新鲜度/异常/实测评分选账户；额度不足/账户异常/任务失败的**有界重路由 + dead-letter**；每次 hold 给出 `retry_at` | **ADDED + v2** |
| **C/D 新增** | `platform_v1/multi_account/cooldowns.py` | **双层冷却**：任务级瞬时冷却 + 账户级隔离（可持久化）；连续失败**指数退避**并有上限 | **ADDED v2** |
| **E 新增** | `platform_v1/multi_account/scoring.py` | **账户级自进化**：可靠性/成本/时延 EWMA，折算为 headroom 等值加减分；有界、可解释、可回滚 | **ADDED v2** |
| **E 新增** | `platform_v1/multi_account/evolution.py` | **自进化回路**：`break_even` 持久化 + 反馈进 `select_orchestration`；`delta_calibration` 可选接线 | **ADDED** |
| **全局新增** | `platform_v1/multi_account/config.py` | 集中校验配置（启动快速失败，无密钥入库） | **ADDED** |
| **门面新增** | `platform_v1/multi_account/__init__.py` | `MultiAccountOrchestrator` 门面：组合感知+调度+自进化 | **ADDED** |
| **集成缝新增** | `platform_v1/multi_account/dispatch.py` | 受保护的派发接线层：每个入口失败即降级到旧行为，绝不阻塞派发 | **ADDED**（已测） |

## 6. 可配置项

| 配置项 | 默认值 | 说明 | 位置 |
|---|---|---|---|
| `NATIVE_CLI_PROVIDERS` | `codex`, `claude-code` | 可路由订阅 provider 注册表 | `contracts.py:89` |
| `_MAGPIE_PROVIDER_KEYS` | codex/openai/chatgpt→codex；claude-code | Magpie provider → 路由键 | `subscription_quota.py:353` |
| `connection.account_ref` | *无（新增）* | 账户级标识，绑定 Magpie `account_ref` | `store.py` |
| 单窗口时长上限 | 7 天 | 有界自主窗口上限 | `autonomy.py` |
| standing 视野上限 | 90 天 | 续期策略总视野 | `autonomy.py` |
| observation freshness | 600 s | 额度观测新鲜度 | `observation(freshness=600)` |
| `magpie.max_age_seconds` | 900 s | Magpie 快照最大年龄 | `magpie` 配置 |
| `REVERSE_AGENT_MAGPIE_URL` | `http://127.0.0.1:3425` | Magpie 环回地址 | `trusted_host.py:1056` |
| `OBSERVATION_WINDOW_TASKS` | 500 | 用量观测覆盖最近任务数 | `resources.py:25` |
| routing retry budget | 现有 | 重路由重试预算 | `goal_service.py` |
| task_need / window_need | 现有 | 准入额度需求 | `quota_reservation.py` |
| break_even 持久化 | *无（新增）* | 自进化参数存储 | `multi_account/evolution.py::SelfEvolutionStore`（JSON 原子写，路径可配） |
| `observation_freshness_seconds` | 600 | 额度观测新鲜度 → STALE | `multi_account/config.py` |
| `magpie_max_age_seconds` | 900 | Magpie 快照最大年龄 | `multi_account/config.py` |
| `high_utilization_threshold` | 90.0 | 进入 DEGRADED 的 used_percent | `multi_account/config.py` |
| `reset_soon_threshold_seconds` | 1800 | 触发 `reset_soon` 异常的窗口临近重置阈值 | `multi_account/config.py` |
| `reroute_max_attempts` | 3 | 单任务最多重路由账户数（超出→dead-letter/hold） | `multi_account/config.py` |
| `reroute_cooldown_seconds` | 30.0 | 重路由后该账户的静默期 | `multi_account/config.py` |
| `abnormal_account_cooldown_seconds` | 300.0 | 异常账户的隔离期 | `multi_account/config.py` |
| `small_task_percent_ceiling` | 1.0 | 允许落到 STALE/DEGRADED 账户的小任务 p80 上限 | `multi_account/config.py` |
| `dead_letter_enabled` | true | 终态失败是否隔离留证 | `multi_account/config.py` |
| `enable_self_evolution` | true | 是否持久化 break_even 并反馈 | `multi_account/config.py` |
| `calibration_feedback_enabled` | true | 是否把实测用量喂给 `delta_calibration` | `multi_account/config.py` |
| `standby_keepalive_interval_seconds` | 60.0 | 休眠/hibernated host 租约对账心跳 | `multi_account/config.py` |
| `failure_backoff_base_seconds` | 30.0 | 账户首次失败的冷却；随后按倍数增长（v2） | `multi_account/config.py` |
| `failure_backoff_multiplier` | 2.0 | 连续失败的指数退避倍数（v2） | `multi_account/config.py` |
| `failure_backoff_max_seconds` | 900.0 | 冷却上限，保证抖动账户最终回归（v2） | `multi_account/config.py` |
| `cooldown_memory_seconds` | 21600.0 | 失联 streak 记忆窗口；超期条目被 prune（v2） | `multi_account/config.py` |
| `persist_account_state` | true | 冷却与评分随重启恢复，避免重启后重击坏账户（v2） | `multi_account/config.py` |
| `enable_account_scoring` | true | 是否启用账户级实测反馈（v2） | `multi_account/config.py` |
| `score_ewma_alpha` | 0.25 | 账户反馈 EWMA 平滑系数（v2） | `multi_account/config.py` |
| `reliability_weight` | 12.0 | 可靠性 0→1 变化可移动的 headroom 等值分（v2） | `multi_account/config.py` |
| `cost_weight` | 10.0 | 相对最贵账户的最大扣分（v2） | `multi_account/config.py` |
| `latency_weight` | 5.0 | 相对最慢账户的最大扣分（v2） | `multi_account/config.py` |
| `max_recorded_runs` | 500 | 模式级账本保留上限，长跑不无限增长（v2） | `multi_account/config.py` |
| `account_routing` / `REVERSE_AGENT_ACCOUNT_ROUTING` | `local` | 账户路由归属：`local`/`magpie`/`auto`（`auto` 需 `REVERSE_AGENT_MAGPIE=1` **且** `REVERSE_AGENT_MAGPIE_ACCOUNT_SWITCHING=1` 才交给 Magpie） | `multi_account/config.py` |
| `REVERSE_AGENT_MAGPIE_ACCOUNT_SWITCHING` | *未设置* | 显式确认"本机 Magpie 账户切换行为已验证"；`auto` 的第二把锁 | `multi_account/routing.py` |
| `REVERSE_AGENT_MAGPIE_WAIT_TARGET` | *未设置* | provider/account 名；设置后长空闲等待（≥60s）改为委托 `magpie quota wait`（可被 stop 打断，单次上限 1h） | `trusted_host._quota_wait_target` |
| `REVERSE_AGENT_WORKSPACE_FENCE` | *未设置* | 工作区租约令牌（C3 F1）；默认关闭 → 不写任何文件、行为不变 | `workspace_fence.py` |
| `REVERSE_AGENT_MAGPIE_EXE` | *未设置* | Magpie CLI 绝对路径；非绝对/不存在视为未配置（用量接入用，只读） | `magpie_usage_ingest.py` |
| `REVERSE_AGENT_RUNTIME_DIR` | `<cwd>/.platform_v1_runtime` | 本地运行时目录（用量缓存落这里） | `magpie_usage_ingest.py::default_cache_path` |
| `REVERSE_AGENT_MULTI_ACCOUNT_ENABLED` | *未设置* | 多账户接缝总开关；未设为 `1` 时全部直通旧行为 | 各接缝 |
| `REVERSE_AGENT_MULTI_ACCOUNT_STORE` | *env* | 重定位 break_even 本地账本路径 | `MultiAccountConfig.from_env` |

> 全部配置须集中校验、启动快速失败；密钥只走环境变量/`.env`，绝不入库。
> 正式提交时须提供 `.env.example`（仅占位值）。

## 7. 验收标准（可测量）

每项须由**回归测试或可复核证据**支撑；自运行/夹具不算产品验收。

**A 多账户**
- A1：同 provider ≥2 个账户时，per-account 窗口证据**全部保留**；断言无静默丢弃（当前 `_merge_magpie_quotas` 不满足）。
- A2：`Connection` 持久化 `account_ref`；派发路径不再退化为 `connection_id`。
- A3：新增 provider 进入注册表后，其窗口可被观测并可参与准入。

**B 感知**
- B1：`/api/resources` 非 legacy 模式输出 `account_attribution` 五态，且前端渲染（当前完全不消费）。
- B2：额度不足时准入拒绝有明确 reason，不静默放行。

**C 容错**
- C1：额度不足触发 reroute 而非任务丢失；异常不得中断无人值守主循环。
- C2：终态失败进入 dead letter 并留证（当前零命中 → 须新增且有测）。
- C3：host sleep 恢复后，租约 reconcile **不误 fence** 仍存活的 executor。

**D 无人值守**
- D1：有界窗口内连续运行无人工干预；窗口到期按 standing 策略续期或干净停止。
- D2：崩溃重启后从检查点恢复，不重复派发、不丢任务。

**E 自进化**
- E1：`break_even` 有持久化且被调度决策实际调用（当前零生产引用 → 须闭合）。
- E2：`delta_calibration` 回路随实测更新成本率并影响后续路由。
- E3：`magpie_usage` 接入生产，任务级账户归因可查（当前零调用）。

**实现映射（multi_account 包，31 测试已落地，全部通过）**

| 验收项 | 覆盖测试 | 说明 |
|---|---|---|
| A1 同 provider ≥2 账户 per-account 证据全保留 | `test_multi_account_status.py::test_pool_account_quotas_preserves_all_accounts` | `pool_account_quotas` 复用 `magpie_account_quotas`，按 `account_ref` 保留，**不按 provider 静默覆盖** |
| B1 账户健康/余量/新鲜度/异常可感知 | `test_multi_account_status.py`（healthy/exhausted/abnormal/degraded/stale/unknown/reset_soon/health_summary） | `MultiAccountStatusMonitor` 输出 `AccountStatus`（pydantic，可直接喂前端） |
| C1 额度不足/异常触发重路由而非丢任务 | `test_multi_account_scheduler.py::test_reroute_moves_to_next_best` / `test_stateful_wrapper_excludes_failed_account` | `AccountAwareScheduler.on_failure` 有界重路由 |
| C2 终态失败进入 dead-letter 并留证 | `test_multi_account_scheduler.py::test_dead_letter_after_max_reroutes` | `reroute_max_attempts` 超出 → `dead_letter`（留 evidence） |
| C3 异常账户隔离避免抖动 | `test_multi_account_scheduler.py`（cooldown 由 `abnormal_account_cooldown_seconds` 控制） | 异常/失败账户进入冷却期 |
| E1 break_even 持久化并被调度决策实际调用 | `test_multi_account_evolution.py::test_break_even_persists_and_recommends` | `SelfEvolutionStore` + `recommend_mode` 闭环 |
| E2 实测反馈更新成本率并影响路由 | `test_multi_account_evolution.py::test_calibration_feedback_*` | 可选接线 `delta_calibration` |
| 配置集中校验、启动快速失败 | `test_multi_account_config.py` | `MultiAccountConfig` pydantic `extra=forbid` + 一致性校验 |

> 注：`account_ref` 在 `trusted_host` 派发路径**已部分接线**（见 `trusted_host.py:458/751/870`），
> 故 A2 的"派发不退化 connection_id"在分支中已具备；本轮把缺失的**多账户池化原语**与
> **状态感知/调度/自进化**补齐为独立、可测、可回滚的接线层。

**治理不变式（每轮必检）**
- G1：R0–R3 分层、独立评审、证据化落地、CI 必需检查**均未被削弱**。
- G2：无新增第四套兼容层。
- G3：未因本轮改动绕过任何 gate 或 ruleset。

**v2 加固验收（`tests/platform_v1/test_multi_account_resilience.py`）**

| 编号 | 标准（可测量） | 覆盖测试 |
|---|---|---|
| B3 | 真实 Magpie 窗口（含 `basis`/`availability`）可被感知，不再抛 `ValidationError` | `test_perceive_accepts_real_magpie_windows_with_basis_and_availability` |
| B4 | 空/异常快照返回 `{}` 而非异常；未知窗口字段保留于 `extra` | `test_pool_account_quotas_tolerates_empty_or_odd_snapshot` / `test_unknown_window_keys_are_preserved_not_fatal` |
| B5 | 单个畸形账户降级为 `UNKNOWN(perception_error)`，不影响同池其他账户 | `test_one_malformed_account_does_not_empty_the_pool` |
| B6 | 生成器入参下 `health_summary.total_accounts` 正确 | `test_health_summary_of_a_generator_counts_every_account` |
| C4 | 连续失败冷却指数增长且封顶 | `test_cooldown_escalates_and_is_capped` |
| C5 | 账户级隔离不被「新任务」清除；瞬时冷却可清除 | `test_new_task_clears_transient_cooldown_but_keeps_quarantine` |
| C6 | 成功清除瞬时冷却但不解除隔离 | `test_success_clears_quiet_time_but_not_quarantine` |
| C7 | 重启后隔离与评分恢复，不重击坏账户 | `test_quarantine_and_scores_survive_a_restart` |
| D3 | 每次 hold 给出 `retry_at`（额度重置或冷却到期时刻） | `test_hold_reports_when_capacity_returns` / `test_hold_reports_earliest_cooldown_expiry` |
| E4 | 同等健康度下，实测更可靠更省的账户胜出 | `test_measured_feedback_reorders_equally_healthy_accounts` |
| E5 | 评分**永不**把 DEGRADED 账户抬到 HEALTHY 之上 | `test_feedback_never_promotes_a_degraded_account_over_a_healthy_one` |
| E6 | 无实测数据时排序与 `best_headroom` 完全一致（默认行为不变） | `test_untrained_scoreboard_leaves_headroom_ordering_untouched` |
| E7 | 模式账本有界，超出 `max_recorded_runs` 丢最旧 | `test_run_ledger_is_bounded` |

**v2.1 补闭环验收**

| 编号 | 标准（可测量） | 覆盖测试 |
|---|---|---|
| E8 | 单任务列表价成本与工时可从用量账本算出（不可定价 → `None`，不记 0） | `test_task_feedback_metrics_prices_tokens_and_wall_time` / `test_task_feedback_metrics_never_invents_a_cost` |
| E9 | 实测成本进入账户评分（`mean_cost_units` / `mean_wall_seconds`） | `test_measured_cost_reaches_the_scoreboard` |
| B7 | 前端渲染账户归属五态 + 汇总，且措辞不把「已绑定路由」说成「正在使用」 | `frontend/tests/resource-account-attribution.test.tsx` |
| D4 | 空闲等待按最早冷却延长，且不超过 60 s 上限；有在飞任务/有派发/无 hint/抛错均退回轮询 | `test_coordinator_sleeps_until_the_hint_but_never_past_the_cap` |
| D5 | 编排器可给出「距最早冷却到期秒数」 | `test_orchestrator_exposes_seconds_until_the_earliest_cooldown` |

**v2.2 Magpie 只读接入验收（`tests/platform_v1/test_magpie_usage_ingest.py`）**

| 编号 | 标准（可测量） | 覆盖测试 |
|---|---|---|
| E10 | CSV 归一化保留令牌/成本/状态，**丢弃密钥名与错误体** | `test_parse_normalizes_rows_and_keeps_tokens` |
| E11 | 账户身份只以 `acct_<sha256前12>` 落盘，原始邮箱不出现 | `test_account_identity_is_hashed_and_never_persisted_raw` |
| E12 | 订阅/按量两口径分离，且未知成本记 `None` 而非 0 | `test_bases_never_blend_cash_and_allowance` / `test_unpriced_rows_are_counted_as_unknown_not_free` |
| E13 | 失败尝试的成本可归因（`failed_cost_share`） | `test_cost_facts_separate_accounts_and_expose_failed_spend` |
| E14 | 重叠窗口重复读取不重复计费；缓存有界 | `test_cache_dedupes_overlapping_windows_and_keeps_newest` |
| E15 | 未配置/超时/非零退出 → `available=False`，绝不抛错 | `test_ingest_without_a_configured_executable_degrades_quietly` |
| E16 | 只走一次有界子进程、`shell=False`、固定 argv | `test_ingest_parses_cli_output_through_one_bounded_call` |
| E17 | 仅当**恰好一个**尝试匹配时才归因；重叠尝试记为 `ambiguous` 且不均分 | `test_overlapping_attempts_of_the_same_agent_are_ambiguous_not_split` |
| E18 | 不同执行器的重叠尝试仍可唯一归因 | `test_overlapping_attempts_of_different_agents_stay_unambiguous` |
| E19 | 未完整归因的尝试成本为 `None`（禁止出现"$0/次"） | `test_unmatched_attempt_is_unknown_not_free` |
| E20 | 两侧周期不重叠时明确报 `overlap=none`，而非"匹配失败" | `test_disjoint_periods_are_reported_as_no_overlap_not_as_a_match_failure` |
| E21 | 新旧口径并列输出；legacy 因剔除失败尝试而系统性偏低（可测量） | `test_cost_report.py::test_report_keeps_legacy_and_all_in_side_by_side` |
| E22 | 无 Magpie 用量时拒绝编造 cash/quota，仍保留列表价回退 | `test_report_refuses_to_invent_magpie_numbers_without_usage` |
| E23 | 执行器把 agent 会话 id 写入完成事件（精确归因的前提） | `test_codex_executor.py::test_native_subprocess_worktree_progress_and_final_response` |
| E24 | 精确会话 id 优先于时间窗，且能消解"两个窗口都命中"的歧义 | `test_exact_session_id_beats_two_competing_time_windows` |
| E25 | 未知会话 id 自动回退时间窗；无 id 的旧任务仍可归因 | `test_unknown_session_falls_back_to_the_window` / `test_attempt_without_a_session_event_stays_attributable_by_time` |
| E26 | `auto` 仅在"启用 + 行为已确认"两把锁同时成立时交给 Magpie | `test_auto_needs_both_enablement_and_an_acknowledgement` |
| E27 | owner=magpie 时本地账户裁决不再否决重路由、不再产生本地等待提示 | `test_magpie_routing_stops_duplicating_the_account_verdict` / `test_magpie_routing_disables_the_local_idle_hint` |
| E28 | `quota wait` 适配有界、拒绝注入、缺二进制不抛错 | `test_magpie_wait.py`（8 例） |
| E29 | 快照可冻结复现；对比**不覆盖**基线 | `test_cost_report.py::test_snapshot_roundtrips_and_compare_writes_nothing` |
| E30 | 对比给出方向与相对变化，并保留 accepted 数；跨版本拒绝对比 | `test_compare_reports_the_direction_and_keeps_accepted_runs_in_view` / `test_compare_refuses_incomparable_versions` |
| E31 | `quota wait` 等待可被 stop 打断，且超时/取消都不留下子进程 | `test_magpie_wait.py::test_cancellation_stops_without_waiting_out_the_window` / `test_our_bound_fires_before_magpie_hangs` |
| E32 | 协调器仅在 opt-in 且等待够长时委托；`_stop` 即取消令牌 | `test_coordinator_delegates_only_long_waits_and_reports_capacity` / `test_coordinator_passes_its_stop_event_as_the_cancel_token` |
| E33 | 工作区令牌默认关闭时不写任何文件 | `test_lease_invariants.py::test_fencing_is_a_no_op_when_disabled` |

## 8. 分期路线

| 阶段 | 内容 | 依赖 |
|---|---|---|
| P0 | A1/A2 账户注册表 + 多账户池化修复 | 无（最大空白） |
| P1 | A3 provider 扩容 + B1 前端消费 | P0 |
| P2 | C1/C2 dead letter + quarantine + C3 host sleep | 无，可与 P0 并行 |
| P3 | E1 break_even 持久化回路 + E3 任务级归因接线 | P0 |
| P4 | D1/D2 长时无人值守实测验收 | P2 |

P0 与 P2 无依赖，可并行推进。

## 9. 风险与约束

- **不得臆造 provider 能力**：扩容 provider 表须有真实观测证据，禁止仅为"看起来支持"而加键。
- **不得重写已有算法**：`break_even`、`delta_calibration` 已有测试，只补接线与持久化。
- **治理优先**：本文件为规划参考；任何落地按其风险分层走独立评审，R2/R3 另需授权。
- **本轮不做**：凭据中转、自动合并、通用 RL、第二编排框架。

## 10. 已落地实现与派发接线待办

### 10.1 本轮新增（已测，31 测试通过）

包：`reverse_agent/platform_v1/multi_account/`

| 文件 | 职责 | 复用 |
|---|---|---|
| `config.py` | 集中校验配置；启动快速失败；无密钥入库 | pydantic |
| `status.py` | `AccountStatus`/`WindowStatus` 模型 + `MultiAccountStatusMonitor`；`pool_account_quotas` 即用替换 `_merge_magpie_quotas` | `magpie_account_quotas`、`parse_iso_time` |
| `scheduler.py` | 账户感知选账户 + 有界重路由/dead-letter | 纯决策逻辑，无 I/O |
| `evolution.py` | `SelfEvolutionStore`（JSON 原子写）+ `SelfEvolutionLoop`（闭环 `break_even`） | `orchestration_selector`、`quota_reservation.delta_calibration` |
| `__init__.py` | `MultiAccountOrchestrator` 门面 | 组合上述三者 |

设计要点：纯决策 + 注入观察源（生产默认 `pool_account_quotas`，测试用 fake）；重型依赖
（`subscription_quota`/`orchestration_selector`/`quota_reservation`）**仅在使用处延迟导入**，
因此该包可独立测试、可回滚（清空 break_even JSON 即回退自进化）、不增加第二个编排脊柱。

### 10.2 派发路径接线待办（仍按 R1 走独立评审）

| 待办 | 接入点 | 动作 | 状态 |
|---|---|---|---|
| 多账户池化真正生效 | `trusted_host.py::_merge_magpie_quotas`（1048） | 改用 `multi_account.merge_account_quotas`，按 `account_ref` 保留每账户（仍保留 provider 键，向后兼容） | ✅ 已接入（additive） |
| 调度决策接入 | `goal_service::_reroute_quota_held` | flag-gated `reroute_guard` 守卫：候选账户 EXHAUSTED/ABNORMAL 时跳过重路由（保稳定），数据来自注入式 `account_status_provider`/`binding_account_resolver` | ✅ Seam C 已落地（`_reroute_guard_skip` + `reroute_guard`，flag-gated，默认直通） |
| 状态感知接入统一资源视图 | `trusted_host._subscription_quotas` 与 `/api/resources` | 用 `perceive()` 输出补充 `account_attribution` |
| 自进化闭环 | `goal_service.create`（模式决策）+ `functional_validation._test_report`（accepted 裁决） | `recommend_mode` 进 `orchestration_mode`（仅实测证据覆盖旧默认）；`record_outcome` 记录 `accepted` | ✅ A/B 接缝已落地（flag-gated，`test_multi_account_seams.py`）；**账户级反馈 v2 已在协调器终态接缝落地**（`unattended_coordinator._report_account_feedback` → `trusted_host._report_account_feedback_to_brain`），成本/时延遥测仍待补（§11.5） |
| 前端消费 | `resources.ts` | 渲染 `AccountStatus`（pydantic 可直接序列化） |
| host sleep 恢复 | `durable_execution` 租约 reconcile | 用 `standby_keepalive_interval_seconds` 心跳；避免误 fence 存活 executor |

### 10.3 分期路线更新（对照 §8）

- **P0 多账户池化原语 + 派发接线**：✅ 已实现（`pool_account_quotas` / `merge_account_quotas`）并接入 `trusted_host._merge_magpie_quotas`（additive，向后兼容）。
- **P2 dead-letter / 重路由逻辑**：✅ 已实现于 `scheduler.py`（dead-letter/有界重路由）；**重路由守卫 Seam C 已接入 `goal_service`**（flag-gated，候选账户 EXHAUSTED/ABNORMAL 时跳过重路由）；**C3 host sleep 未做**。
- **P3 break_even 持久化回路**：✅ 算法+持久化已闭环（`evolution.py`）；**派发接缝 A/B 已落地**（`goal_service` 模式决策 + `functional_validation` 结果记录，均 flag-gated）；richer 成本遥测（cost/task_count/tokens/time）待在目标落库处补齐以真正驱动 measured break_even。
- **P1 provider 扩容 / 前端消费**、**P4 长时无人值守实测**：⏳ 仍待办（需真实观测证据与端到端实测）。

### 10.4 接入 `goal_service` / `functional_validation` 的最小改动草稿（R1，待独立评审 + CI）

`dispatch.py` 已就绪并测试。以下三处为真实生产接缝；全部以环境变量
`REVERSE_AGENT_MULTI_ACCOUNT_ENABLED=1` 为总开关（默认关，关时行为与旧版完全一致），
因此该 PR 对默认路径零风险，评审通过 + CI（`baseline`/`state-gate`/`landing-state-gate`）绿后即可落。

**A. 编排模式决策（自进化 E1 真正生效）—— `goal_service.py:162`（落点在 `create()` 的 `_resolve_orchestration_mode`）**

> 修订说明：原草稿写 `task_service.py:1021` 经复核**不可用**——`task_service` 的 run 模式仅接受
> `single`/`sequential_team`，`recommend_orchestration_mode` 会返回 `agent_team` 且**无证据时默认
> 返回 `agent_team`**，直接写入会触发 `run_store` 校验失败或把无证据目标默认改成 `agent_team`。
> 目标级 `orchestration_mode`（合法值 `single`/`sequential_team`/`agent_team`）的正确落点是
> `goal_service.create()`，故此处改用 `goal_service`。

```python
def _resolve_orchestration_mode(payload):
    explicit = payload.get("orchestration_mode") if "orchestration_mode" in payload else None
    if explicit:
        return str(explicit)                       # 显式 Owner 选择恒优先（pin）
    if os.environ.get("REVERSE_AGENT_MULTI_ACCOUNT_ENABLED") != "1":
        return "sequential_team"                   # 关：与旧版完全一致
    try:
        from .multi_account.dispatch import recommend_orchestration_mode
        rec = recommend_orchestration_mode({})     # 建目标时 planner 尚无 task_count 估计
        mode, reason = rec.get("mode"), rec.get("reason", "")
        # 仅当由"实测证据"驱动时才覆盖旧默认；默认阶梯分支被刻意忽略，
        # 故在 break_even 账本尚无数据前行为逐字节不变。
        if mode in ("single", "agent_team") and str(reason).startswith("measured_"):
            return str(mode)
    except Exception:
        pass
    return "sequential_team"
```

**B. 目标结果记录（自进化反馈闭环）—— `functional_validation.py:_test_report`（约 452 行后）**
```python
# 在 result["accepted"] 计算完成后（try/except 之外，result 已定）：
if os.environ.get("REVERSE_AGENT_MULTI_ACCOUNT_ENABLED") == "1":
    try:
        from .multi_account.dispatch import record_goal_outcome
        record_goal_outcome({
            "mode": None,                # 验证接缝处未知；由 §10.2 的"目标落库处"接缝补全
            "accepted": bool(result.get("accepted")),
            "cost_units": None, "task_count": None,
            "tokens": None, "wall_seconds": None, "size_band": None,
        })
    except Exception:
        pass
# record_goal_outcome 内部 try/except，失败仅 best-effort，绝不阻塞落地。
```
> 说明：验证接缝只能可靠提供 `accepted` 裁决；`cost_units`/`task_count`/`tokens`/`wall_seconds`
> 等成本遥测在 `goal_service` 目标落库处（§10.2 行 "自进化闭环"）才齐备。在补齐 richer 接缝前，
> 这些字段为 `None`，此类 run 不会推动 measured `break_even`——即"无数据则保持旧默认阶梯"的安全态。
> 该接缝已落地（见 `test_multi_account_seams.py`）。

**C. 账户感知重路由守卫（容错 C，附加而非替换既有 tier 路由）—— `goal_service.py::_reroute_quota_held`**

> 修订说明：原草稿用 `select_dispatch_account`（"选最优账户"语义）比对 `account_ref`，但重路由场景里 tier 路由已确定**候选 binding**，我们要回答的是"这个候选账户是否还健康"，而非"有没有更好的账户"。故改用针对性的 `reroute_guard`（仅当候选账户 EXHAUSTED/ABNORMAL 时 `skip=True`）。候选账户状态的数据源也改为**注入式** `account_status_provider`（来自 `platform_quota_observations`），避免把 `perceive()` 结果强行穿过 run 上下文。

```python
# GoalService.__init__ 新增两个可选注入（默认 None → 守卫为 no-op 直通，行为不变）：
#   account_status_provider: () -> Iterable[AccountStatus]   # 账户健康池
#   binding_account_resolver: (binding_ref) -> account_ref|None  # binding→账户映射
#
# _reroute_quota_held 在 tier 路由算出 decision 后、reroute_held_task 之前：
skip, candidate_account = _reroute_guard_skip(self, decision)
if skip:
    # 候选账户 EXHAUSTED/ABNORMAL：不把被 hold 的任务重路由到坏账户，保留等待（保稳定）
    self.store.add_event(task.id, event_type="MODEL_SELECTED", ...,
                         metadata={"guard": "account_health", "account_ref": candidate_account})
    continue
```

`_reroute_guard_skip(goal_service, decision)`（已抽到模块级，便于单测）：flag 关 / provider 或 resolver 缺失 / binding 不可映射 / 账户未知 / 任何异常 → `(False, None)`（绝不阻塞旧重路由）。`reroute_guard(statuses, account_ref)`（dispatch.py）：仅 EXHAUSTED/ABNORMAL → `skip=True`；STALE/UNKNOWN → 不跳过（保守：不确定坏就不阻塞）；异常 → 不跳过。

`trusted_host` 注入：`_goal_account_status_provider` 读 `platform_quota_observations`（每行 `evidence_json` 已是 `_canonical_windows` 形状，兼容 `_build_status`）→ `MultiAccountStatusMonitor.perceive()`；`_binding_account_resolver` 经 `list_bindings_public`→`list_connections_public` 取 `account_ref`（回退 `connection_id`）。两者均 try/except 兜底，任一失败 → 直通旧重路由。

> 已实现：`test_multi_account_seams.py`（`reroute_guard` 单测 + `_reroute_guard_skip` 集成单测：flag 关/缺 provider/EXHAUSTED→skip/HEALTHY→不 skip/binding 不可映射/provider 异常均安全）。`goal_service` 127 用例 + `functional_validation` 全绿（provider=None → 旧重路由行为不变）。

**D. 待补接缝（明确不做于本 PR）**：前端 `resources.ts` 消费 `AccountStatus`、richer 成本遥测在目标落库处补齐、C3 host sleep 恢复——单列 PR。



## 11. 加固版 v2：缺陷修复 + 长时无人值守收敛

本轮不扩功能边界，只把已落地的接线层做到**生产可用**：修掉会让整条链路静默失效的缺陷，
把「长时间不间断」真正需要的冷却/退避/唤醒时刻补齐，并让自进化第一次拥有账户级反馈。

### 11.1 已修复缺陷（含复现证据）

| # | 现象 | 根因 | 影响面 | 修复 |
|---|---|---|---|---|
| 0 | `CombinedTrustedHost` 构造完成后 `_started_servers` / `_research_loop` 不存在，`start()` 抛 `AttributeError`，`stop()` 也抛 | 上一轮的 Seam C 辅助方法被插在 `__init__` **中间**，`__init__` 提前结束，其后半段初始化语句变成 `_binding_account_resolver` 的尾部语句 | **致命**：宿主无法启动；且每次调用绑定解析器都会把 `_started_servers` 等状态重置一次（`test_trusted_host.py` 26 例失败） | 把被吞掉的初始化段移回 `__init__`；解析器恢复为纯查询 |
| 1 | 真实 Magpie 快照喂入 `perceive()` 抛 `ValidationError: basis Extra inputs are not permitted` | `WindowStatus` 用 `extra="forbid"`，但上游窗口自带 `basis`/`availability`/`anchor` | **致命**：`trusted_host._goal_account_status_provider` 用 `try/except` 兜底返回 `[]`，于是感知/调度/自进化**静默全失效**，系统退化为旧行为且无告警 | 补 `basis`/`availability`/`unlimited` 字段；未知键进 `extra`；`name` 归一为 `window` |
| 2 | `pool_account_quotas({"accounts": []})` 抛 `UnboundLocalError: enriched` | `enriched = {}` 误缩进进入第一个 `for` 循环体 | 空/无账户快照直接 500 | 初始化提到循环外，并容忍非 list 的 `accounts` |
| 3 | `health_summary(gen)` 的 `total_accounts` 恒为 0 | 先遍历一遍再 `len(list(statuses))`，生成器已耗尽 | 仪表盘/协调器误判「无账户」 | 一次性物化 |
| 4 | 单个账户窗口畸形导致整池感知失败 | `_build_status` 无隔离 | 一个坏账户拖垮所有账户 | 单账户异常降级为 `UNKNOWN(perception_error)` |
| 5 | 冷却状态不落盘、无退避 | 仅内存 `dict`，固定 30/300 s | 重启后立刻重击坏账户；抖动账户被反复重试 | 新增 `cooldowns.py`：双层 + 指数退避 + 持久化 |
| 6 | 自进化账本随运行时间无限增长 | `runs` 只 append | 长跑内存/文件膨胀、每次写入 O(n) 重算 | `max_recorded_runs` 环形保留 |

> 缺陷 1 是本轮最重要的发现：它意味着「多账户调度」在此前实际上**从未在真实证据上生效过**。
> 修复后 `test_multi_account_resilience.py::test_perceive_accepts_real_magpie_windows_with_basis_and_availability`
> 用与 `magpie_quota_windows` 完全一致的窗口形状做回归。

### 11.2 新增模块

| 模块 | 职责 | 复用 | 明确不做 |
|---|---|---|---|
| `cooldowns.py` | 任务级瞬时冷却 + 账户级隔离；指数退避；`retry_at`；快照/恢复 | `MultiAccountConfig` | 不做调度决策、不派发、不碰凭据 |
| `scoring.py` | 账户级 EWMA（可靠性/成本/时延）→ headroom 等值加减分 | `MultiAccountConfig` | 不做通用 RL、不做绝对成本建模 |

设计约束（与 §2.2 红线一致）：
- 评分**只在一个健康度档位内重排**，健康度仍是第一排序键 —— 稳定性优先于省钱。
- 评分权重全部可配，默认值让「无数据时」与旧行为**逐位一致**（`best_headroom`），便于灰度与回滚。
- 全部状态落在同一个原子写 JSON 文档（`runs` / `break_even` / `accounts` / `cooldowns`），
  回滚动作就是删除该文件的对应段。

### 11.3 新增派发接缝

| 接缝 | 位置 | 行为 | 失败时 |
|---|---|---|---|
| 账户结果反馈 | `unattended_coordinator._report_account_feedback` → `trusted_host._report_account_feedback_to_brain` | 每次任务终态上报一次：成功清冷却+提可靠度，失败按分类冷却（`auth/unauthorized/rate_limit/login/session` → 隔离，`quota/limit_hit` → 额度冷却，其余 → 任务失败冷却） | 回调异常仅记 `account_feedback_failed:*`，绝不影响主循环 |
| 人工解除隔离 | `MultiAccountOrchestrator.scheduler.clear_quarantine()` | 运维在确认账户恢复后一键放行 | — |

开关仍为 `REVERSE_AGENT_MULTI_ACCOUNT_ENABLED=1`；关闭时所有接缝直通，行为与旧版完全一致。

### 11.4 运维处置手册（无人值守场景）

| 场景 | 观察点 | 期望行为 | 人工动作 |
|---|---|---|---|
| 某账户额度耗尽 | `AccountStatus.health=EXHAUSTED`、`retry_at` | 池内其他账户接管；全部耗尽则 hold 到最早重置 | 无 |
| 账户凭据失效 | `health=ABNORMAL`、`anomaly_flags=["abnormal:..."]` | 隔离 `abnormal_account_cooldown_seconds` 起，逐次翻倍至上限 | 修复凭据后 `clear_quarantine()` |
| 账户抖动 | `CooldownRegistry.get(ref).streak` 递增 | 冷却 30→60→120→…→900 s 封顶 | 无 |
| 进程被杀/重启 | 状态文件 `cooldowns` 段 | 隔离与 streak 原样恢复，不重击 | 无 |
| 任务反复失败 | `decision=dead_letter` + evidence | 终态隔离留证，不再消耗额度 | 查看 evidence，修任务或计划 |
| 成本偏高 | `account_scores[ref].mean_cost_units` | 同健康度下更省的账户被优先选中 | 调 `cost_weight` |
| 需要整体回退 | — | 删除状态文件或清零 `accounts`/`cooldowns` 段即回到纯余量调度 | — |

### 11.5 本轮未闭环（诚实清单）

1. ~~**账户级成本/时延遥测**~~ **已闭环（v2.1）**：`usage_ledger.task_feedback_metrics`
   按任务汇总 `task_usage_observations` 的归一化计数并套用 `model_access.pricing.equivalent_cost`
   得到**列表价 USD**，工时取 `tasks.created_at → updated_at`；宿主在两处终态上报时一并喂入
   `record_account_outcome(cost_units=…, wall_seconds=…)`。无法定价的模型返回 `None` 而**不记为 0**
   （避免把未知成本当成免费）。`cost_weight` / `latency_weight` 自此生效。
2. ~~**前端消费**~~ **已闭环（v2.1）**：`resources.ts` 新增 `AccountAttribution` 读模型（五态 +
   `summary`），`resource-overview.tsx` 在账户行渲染归属徽章并在账户区展示汇总；
   措辞严格区分「已绑定路由」与「正在使用」。覆盖：`frontend/tests/resource-account-attribution.test.tsx`（5 例）。
3. ~~**精确唤醒**~~ **已闭环（v2.1，受上限约束）**：协调器新增 `idle_wait(dispatched)` 与可选
   `idle_wait_hint`；仅在**空闲 tick 且无在飞任务**时，按最早冷却到期时间延长等待，
   上限 `IDLE_WAIT_CAP_SECONDS=60s`，因此新目标最多晚 1 分钟被拾取。无 hint / 抛错 / 提示 ≤0
   一律退回 `poll_interval`（默认行为不变）。
   *仍属部分闭环*：提示来源目前只有**账户冷却**；纯额度窗口重置尚未计入 hint（窗口重置时间已在
   `AccountStatus.next_reset_at` 暴露，接入即可）。
4. **休眠 host**：`standby_keepalive_interval_seconds` 尚未接入 `durable_execution` 租约对账（C3 未闭环）。
   该改动会触碰租约 fencing 语义，误配可能导致重复派发，**必须**在独立评审下单独推进，不在本轮范围。
   → **已单独立项**：[C3 租约与恢复一致性](C3_LEASE_RECOVERY_PROJECT.md)（含失败模式 F1–F6、
   不变式 I1–I5、故障注入矩阵、验收标准）。立项文档只定义问题与验收，**未改动任何租约代码**。

剩余第 4 项为独立小改动；未完成前系统行为安全（默认不启用 hint 时逐字节等价旧行为）。

## 12. 能力归属与约束分级（2026-11-04 评审后新增）

评审的核心质疑是「Nerelan 是否在重做 Magpie 已做的事」。结论：**方向成立，但需先审计再定分工**；
在此之前不删除现有代码，只把它明确标注为待审计的**账户层 fallback**。

### 12.1 三层归属（目标态）

| 层 | 负责 | 不负责 |
|---|---|---|
| **Magpie** | 账户接入、凭据、额度观测、**账户内**切换、网关路由、请求级重试、`quota wait` | 任务拆分、模型能力评估、质量验收、全局预算、跨模型语义等价 |
| **Nerelan** | 任务级决策：拆不拆、用哪个模型/执行器、跨模型切换、检查点、预算、验收、自进化 | 账户内负载均衡（若 Magpie 已提供）、凭据中转 |
| **Executor** | 实际执行、会话与上下文 | 资源与预算决策 |

判定规则（一句话）：**"同一服务内换账户"归 Magpie；"换一个具备等价能力的模型"归 Nerelan。**

### 12.2 Magpie 能力审计（2026-11-04 已完成，见 [审计报告](MAGPIE_CAPABILITY_AUDIT_2026-11-04.md)）

| # | 审计问题 | 结论 | 依据 |
|---|---|---|---|
| M1 | 版本与开放端点 | **已核实** | 应用 `0.12.6`，协议 `magpie 0.1.2782`，环回 `127.0.0.1:3425` |
| M2 | 账户内自动切换 | **已支持（CLI）** | `accounts switch <agent> next`、`group add … routing=usage\|pace\|fast\|cheap\|drain` |
| M3 | `quota wait` | **已支持（CLI）** | `quota wait <provider\|account> --timeout <d>` |
| M4 | 命名空间覆盖 | **11 账户 / 11 provider**，含 `workbuddy`、`workbuddy-ai`、`trae-cn`、`copilot`、`zcode` | `quota --json` 聚合（仅计数，无身份） |
| M5 | 请求级账户归因 + 真实成本 | **已支持且强于本仓** | `usage --csv` 含 `cost_usd`、`provider_account`、`tries`、`swapped`、`served_model` |
| M6 | provider 级故障降级 | **已支持** | `provider fallback <id> <provider/model>…` |

**处置（重要）**：M2/M3/M5/M6 均属"上游已有"，因此

- 本仓的账户选择、冷却退避、`retry_at`、空闲等待、列表价成本 → **降级为 fallback**，
  仅在 Magpie 未启用 / 不可用 / 未覆盖该 provider 时生效；
- 新增可配置项 `REVERSE_AGENT_ACCOUNT_ROUTING = magpie | local | auto`（默认 `auto`：
  Magpie 在位走 magpie，否则 local）。**该开关尚未实现**，实现前须先完成 §12.2 的行为实测（M2/M3）。

**未实测项（诚实标注）**：`accounts switch`、`quota wait`、`provider fallback` 只验证了
**CLI 能力存在性**，未执行（会改动用户登录态/阻塞/改路由配置），故标记"能力已确认、行为未实测"。
行为验证需 Owner 在场的独立窗口，且不属于本轮授权范围。

**当前事实（已核实）**：`model_access/magpie.py:251-256` 只调用 `/api/hello`、`/v1/models`、
`/v1/magpie/quotas?kept=1` 三个**只读**端点。因此本仓今天的 Magpie 集成是"观测源"，
尚未利用其路由/等待/成本能力。

### 12.3 约束分级：可降级 vs 不可绕过

| 约束 | 实现位置 | 失败时 | 级别 |
|---|---|---|---|
| 额度硬准入 | `control_store.prepare_quota_admission` → `quota_reservation.admission`（`control_store.py:1771-1774`） | 抛错即拒绝 → `QUOTA_WAIT` | **硬 / fail-closed** |
| 授权与身份 | `autonomy.check_task_scope` / `check_strict_task_admission` | 拒绝 | **硬 / fail-closed** |
| 预算与 WIP | `platform_budget_reservations` / claim | 拒绝 | **硬 / fail-closed** |
| 账户健康预筛 | `goal_service._reroute_guard_skip` → `dispatch.reroute_guard` | 异常 → 放行重路由 | **软 / fail-open**（仅提示；目标仍过硬准入） |
| 模式推荐、账户评分、学习反馈 | `multi_account.dispatch.*` | 异常 → 旧默认 | **软 / fail-open**（无资源后果） |

规则：**任何新增接缝必须先声明级别**。硬约束不得因为新模块异常而降级；软约束不得被当作
准入判定的替代品。这条规则此前只存在于代码结构里，现作为规范要求。

### 12.4 经济性口径（两个指标，禁止只引用一个）

```text
cost_per_accepted        = 合格运行中已测成本 / 合格运行数          （老口径，不含失败成本）
cost_per_accepted_all_in = 全部尝试的已知成本 / 独立验收合格结果数   （新口径，含失败/重试）
```

任一尝试成本未知时，`all_in` 整体为 `None`（未知 ≠ 0）。实现：`orchestration_selector.all_in_economics`。

**对照实验工具（决策 1 的前置）**：同一命令支持冻结快照与快照对比：

```bash
# 0) 先自检：数据够不够跑对照（ready 才继续，退出码可脚本化）
python -m reverse_agent.platform_v1.cost_report --doctor --last 7d
# 1) 冻结一份基线（实验开始前）
python -m reverse_agent.platform_v1.cost_report --last 7d --save baseline.json --label local-routing-7d
# 2) 切换策略后，与基线对比（只读，不会覆盖基线）
python -m reverse_agent.platform_v1.cost_report --last 7d --compare baseline.json --label magpie-routing-7d
```

`--doctor` 逐项检查：Magpie CLI 已配置 / 服务可达 / 窗口内有用量行 / **存在带 `agent_session_id` 的任务** /
两侧窗口重叠；缺哪项就直接点名（退出码 1），避免"跑出一份漂亮的 n/a 报告"这种静默失败。

对比输出每个口径的 `before → after`、`delta`、`relative`，并在同一行给出 `accepted`，
因为"更便宜但合格数更少"是**退步**而不是省钱。跨 schema 版本的快照拒绝比较（`ValueError`），
避免字段语义变化被当成收益。

**并列统计的产物**：`reverse_agent/platform_v1/cost_report.py`
（`python -m reverse_agent.platform_v1.cost_report --last 6h`）。它同时输出 `legacy` / `list_price` /
`cash` / `quota` 四组数，并附带 caveats（列表价≠账单、订阅现金为 0、未归因记 null）。
归因未完整或数据窗口不重叠时一律 `n/a`，不生成可用于决策的假数字。
**切换决策目标函数到新口径属于算法变更**，需 Owner 决策 + 独立评审；在此之前两份口径必须并列报告。

### 12.5 修订后的路线

原 §8 的 P0–P4 以"模块开发"为轴，已被
[评审回应 §7](MULTI_ACCOUNT_PLAN_REVIEW_RESPONSE.md) 的 P0–P5 取代：
**P0 事实审计 → P1 统一资源 → P2 可靠性 → P3 经济性 → P4 受控自进化 → P5 长期验收**，
完成条件一律以"真实账户 / 真实故障 / 可测量收益"表述，而非"模块已实现"。

## 13. v3：成本上限、告警、运行时长与受限自进化（2026-11-05）

本轮不扩功能边界，补齐 §6 可配置项与 §7 验收标准中**尚未闭环的四类能力**：成本限制、
告警、运行时长、自进化的限幅/审计/回滚。全部改动仍集中在
`reverse_agent/platform_v1/multi_account/`，不新增第三方依赖（仅标准库 + 既有 pydantic）。

### 13.1 新增模块与职责边界

| 模块 | 职责 | 复用 | 明确不做 |
|---|---|---|---|
| `budget.py` | 滚动窗口成本上限：`allow` / `degrade` / `deny` 准入、预留-结算防并发超支、`retry_at` 精确到"哪笔花费滚出窗口" | `usage_ledger.task_feedback_metrics` 的 `cost_units` 口径（列表价 USD），本模块只累加、不定价 | 不做定价、不调额度、不阻塞既有派发（禁用即全量 `allow`） |
| `alerts.py` | 规则化告警 + `(code, subject)` 去重静默 + 重复计数 + 有界历史；sink 注入 | 感知结果、冷却表、评分板、预算状态 | 不做网络投递（webhook 属宿主扩展点），不做告警升级值班表 |
| `watchdog.py` | 运行时长/空闲判定：`continue` / `conclude` / `stop`，`remaining_seconds` 供协调器定长休眠 | `MultiAccountConfig` | 不自己取消任务（取消语义留在 `durable_execution`） |
| `policy.py` | 策略版本链：有界步长调整调度权重、clamp、审计、按版本回滚 | `scoring.failure_profile()`、`MultiAccountConfig` | 不做通用 RL、不改结构性旋钮（重路由次数/冷却/超时） |

`scoring.py` 增补：`AccountScore.failure_kinds` 失败类型直方图、`cost_total/wall_total` 累计量
（池级趋势用真实"每次尝试均值"，避免账户构成变化导致中位数漂移）、`failure_profile()` 汇总裁剪。
`scheduler.py` 增补：预算准入前置（`deny` → 带 `retry_at` 的 hold，不计入账户冷却）、
`degrade` → 同健康度档位内按实测成本排序、`bonus_cap` 对学习型加分的硬截断。

### 13.2 边界：什么被限制，什么不被绕过

| 约束 | 可降级 | 硬约束 |
|---|---|---|
| 成本 | 软阈值（`cost_budget_soft_ratio`）→ 转最低成本账户 | 硬上限（`cost_budget_units`）→ 一律等待，不超支 |
| 额度 | 小任务可用 STALE 账户（`small_task_percent_ceiling`） | 100%/rejected 账户绝不派发 |
| 账户 | 冷却到期自动恢复 | 隔离期内的账户即使有成功回报也不解除（仅 `clear_quarantine()`） |
| 策略 | 权重可在 ±`drift` 内调整 | 结构性旋钮、健康度排序优先级、隔离语义不可被自进化修改 |
| 运行 | `conclude` 停止派发但放行在飞任务 | `stop` 只在超过 `hard_stop_ratio × deadline` 时触发 |

默认值原则不变：预算默认关闭、运行时默认不限、告警默认只入内存（`alert_log_enabled=False`），
因此**未显式配置的部署行为与 v2.1 逐位一致**。

### 13.3 新增可配置项（环境变量为 `REVERSE_AGENT_MULTI_ACCOUNT_*`）

| 类别 | 键 | 默认 | 说明 |
|---|---|---|---|
| 成本 | `cost_budget_enabled` / `_units` / `_window_seconds` | `false` / `0` / `86400` | 启用时必须给正上限，否则启动即失败 |
| 成本 | `cost_budget_soft_ratio` | `0.8` | 达到该比例转最低成本账户 |
| 成本 | `cost_budget_default_task_units` | `0` | 无预估时的保守单次预测；0 表示只按已发生花费判定 |
| 成本 | `cost_budget_include_reservations` | `true` | 在飞预留计入上限，防并发超支 |
| 告警 | `alerts_enabled` / `alert_quiet_seconds` / `alert_max_history` | `true` / `300` / `120` | 去重窗口与有界历史 |
| 告警 | `alert_failure_streak_threshold` / `alert_min_success_rate` / `alert_min_samples` | `2` / `0.6` / `3` | 抖动与可靠性阈值 |
| 告警 | `alert_log_enabled` | `false` | 是否同时写 `reverse_agent.multi_account` 日志 |
| 运行 | `watchdog_enabled` / `max_run_duration_seconds` / `max_idle_seconds` | `true` / `0` / `0` | 0 = 不限 |
| 运行 | `watchdog_hard_stop_ratio` | `1.25` | 超期后升级为 `stop` 的倍率 |
| 策略 | `policy_enabled` / `policy_step_ratio` | `true` / `0.25` | 每周期最大单步变更比例 |
| 策略 | `policy_max_weight_drift_ratio` / `policy_max_bonus_points` | `0.5` / `12` | 漂移与加分硬限幅 |
| 策略 | `policy_min_samples` / `policy_target_success_rate` / `policy_audit_max_entries` | `5` / `0.85` / `120` | 评估门槛与审计容量 |

### 13.4 本轮修复的缺陷（由新测试与验收仿真发现）

| # | 现象 | 根因 | 影响 | 修复 |
|---|---|---|---|---|
| 7 | 重启后预算窗口、告警去重、策略链、运行时钟**全部丢失** | `SelfEvolutionStore._empty()` 只列旧四段，`_load()` 用它做白名单，新段被静默丢弃 | 每次崩溃即忘记当日花费/隔离/策略版本，长跑必然超支 | `_empty()` 扩为完整段清单，并加回归测试 |
| 8 | 观测源抛错时 `perceive()` 直接上抛 | fetch 未包裹 | 遥测故障会让感知周期崩溃，或被误读为"无账户" | 捕获后返回空池并记 `last_error`，`observe()` 额外发 `perception_failed` 告警 |
| 9 | 只上报主机事件时误发 `no_accounts_observed` | `evaluate()` 把"未传状态"与"观测为空"混为一谈 | 每次策略变更都附带一条假告警 | `statuses=None` 表示"本次不评估池"，显式 `[]` 才发空池告警 |
| 10 | "稳定"规则把已在基线的权重继续下调 | 用 clamp 下界当目标而非基线 | 自进化本身成为漂移源 | 改为"朝基线走一步且不越过基线" |
| 11 | 池级告警与账户级告警重复 | 两者独立生成 | 全池异常时刷屏，运维开始忽略告警 | 全池判定覆盖同义账户级告警 |

### 13.5 验收结果（可复现）

```bash
python scripts/multi_account_acceptance.py     # 虚拟时钟 24h，四个场景，输出 reports/multi_account/
python -m pytest tests/platform_v1/test_multi_account_*.py -q   # 182 passed
```

关键数字（种子 7，`reports/multi_account/acceptance_latest.md`）：

| 验收标准 | 证据 |
|---|---|
| 多账户整合 | 4/4 账户均被实际调度（21/37/23/55 次） |
| 状态感知 | 全窗口零观测错误 |
| 异常容错 | 切换 36 次、重试 18 次、等待/降级 361 次，任务 0 丢失 |
| 成本上限 | 花费 11.983 ≤ 上限 12.0（利用率 99.9%） |
| 连续运行 | 虚拟 19.19h 后按 `conclude` 收束，遵守运行时长 |
| 性能 | 每轮控制环 0.28 ms（498 轮真实耗时 0.14 s） |
| 反馈优化 | 健康池 v0 不变；异常池 v1..v6 有界变更；后半程成本 0.1035 vs 基线 0.1208，重试率 0.00 vs 0.30 |
| 可审计可回滚 | 6 条审计（含 `changed_keys`），`rollback_policy(n)` / `0` 可回退 |

### 13.6 仍属未闭环

1. ~~**宿主接线**~~ **已闭环（v4）**：协调器主循环现在在 `REVERSE_AGENT_MULTI_ACCOUNT_ENABLED=1`
   时接上 `start_run` / `run_verdict` / `drain_alerts` / `admit_cost` / `run_progress` 五个接缝
   （见 §14）。未启用时 `{}` 不注入，行为逐位等价旧循环。
2. **告警投递**：默认落到宿主的有界内存尾巴（`multi_account_alerts()`）与可选的
   `alert_log_enabled` 日志行；IM/webhook 需宿主注入 sink（不引入网络依赖）。
3. **成本口径**：`cost_units` 仍为列表价估算；Magpie `usage --csv` 的现金口径接入后，
   预算上限可切换到真实账单口径（需 Owner 决策，属口径变更）。

## 14. v4：把 v3 的旋钮真正接到派发路径（2026-11-05）

v3 的实现是**正确但悬空**的：`budget.py` / `watchdog.py` / `alerts.py` 有 182 个测试，
却没有任何生产调用方 —— `start_run`、`run_verdict`、`drain_alerts`、`admit_cost` 全仓零引用
（已用 grep 复核）。因此"成本上限""运行时长""告警"在真实运行中的实际效力为零。
本轮只做接线，不改算法、不扩边界。

### 14.1 接线点（全部可选，未注入即旧行为）

| 接缝 | 协调器位置 | 行为 | 失败时 |
|---|---|---|---|
| `run_start` | `_run()` 开跑一次 | 打开本次运行的计时窗口 | `run_start_failed:*`，不阻塞派发 |
| `run_verdict` | `_run()` 每轮派发**之前** | `conclude`/`stop` → 停止认领并让在飞批次自然排空 | `run_verdict_failed:*` → 视为 `continue`（时钟坏了不能静默结束无人值守运行） |
| `cost_admission` | `_tick_impl()` 在 `authorize` 之后、`claim_task` **之前** | `deny` → 本轮停止认领；任务保持队列位置，**不认领、不丢弃** | `cost_admission_failed:*` → fail-open 放行 |
| `alert_source` + `alert_sink` | `_run()` 每轮一次 | 排空告警并投递给宿主 sink | 两侧各自兜底，永不中断循环 |
| `run_progress` | 每次任务终态 | 计入 idle/已用时判定 | 仅记账，异常不外抛 |

设计约束：

- **conclude ≠ 取消**。`conclude` 只停止"开始新工作"，`_run` 的 `finally` 仍 join 在飞批次，
  因此有界收束不会截断证据（测试：`test_a_conclude_verdict_lets_work_in_flight_land`）。
- **cost 只按已发生花费判定**。宿主不携带 per-task token，故 `admit_cost` 以
  `reserve=False` 调用：未结算的预留会永久占用额度，最终把每一次派发都拒掉——这比"轻微超支"
  更糟。超出上界不超过在飞并发批次的成本，已在文档与 `.env.example` 中写明。
  `dispatch.admit_cost` 的 `reserve` 默认值因此由 `True` 改为 `False`。
- **run_progress 与 account_feedback 解耦**。账户解析失败时旧实现不会心跳，`max_idle_seconds`
  会把仍在完成工作的运行判成空闲而收束；现在二者独立计数。

### 14.2 可配置面补齐（此前 16/43 可达 → 现 48/50）

v3 的 `_ENV_SCALARS` 只映射了 43 个字段中的 16 个，**自进化限幅**
（`policy_step_ratio`、`policy_max_weight_drift_ratio`、`policy_min_samples`、
`policy_target_success_rate`）根本无法从部署面设置，"策略变更可配置"只在 Python 内成立。
本轮把全部字段纳入映射，仅两个"自有变量"字段除外（`account_routing` →
`REVERSE_AGENT_ACCOUNT_ROUTING`、`break_even_store_path` → `REVERSE_AGENT_MULTI_ACCOUNT_STORE`）。

三条回归把该属性钉住：

- `test_every_knob_is_reachable_from_the_environment` —— 新增字段若未决定如何配置，测试即失败；
- `test_the_self_evolution_clamps_are_settable_from_the_environment` —— 限幅可设；
- `test_the_env_example_documents_every_variable` —— `.env.example` 与实际变量不漂移。

### 14.3 新增可观测项

`coordinator.status()` 追加四个键（未注入时为默认值，旧语义不变）：

| 键 | 含义 |
|---|---|
| `run_conclusion` | 运行如何收束：`run_conclude:<reason>` / `run_stop:<reason>`，空 = 仍在跑或未启用 |
| `last_verdict` | 最近一次裁决原文（含 `remaining_seconds` 等） |
| `cost_holds` | 因成本上限而未认领的候选次数（"hold 而非 drop" 的证据） |
| `alerts_delivered` | 已投递告警条数 |

宿主侧另有 `multi_account_alerts(limit)`：有界（200）的最近告警尾巴，供运维面读取。

### 14.4 验收（本轮新增 21 例，包内共 203 例）

```bash
python -m pytest tests/platform_v1/test_multi_account_host_wiring.py -q   # 15 passed
python -m pytest tests/platform_v1/test_multi_account_config.py -q        # 21 passed
```

| 标准 | 覆盖测试 |
|---|---|
| 有界运行真的会结束（无需人工 stop） | `test_a_conclude_verdict_ends_the_loop_without_a_stop_request` |
| 收束不截断在飞工作 | `test_a_conclude_verdict_lets_work_in_flight_land` |
| 坏时钟不得结束运行 | `test_an_unknown_or_failing_verdict_never_ends_a_run` / `test_a_non_dict_verdict_is_treated_as_continue` |
| 成本拒绝 = 保留而非丢弃 | `test_a_denied_cost_admission_holds_the_task_without_claiming` |
| 成本放行不改行为 | `test_an_allowing_cost_admission_changes_nothing` |
| 预算故障 fail-open | `test_a_broken_cost_seam_fails_open` |
| 告警只排空一次并送达 | `test_alerts_are_drained_into_the_injected_sink` / `test_the_host_keeps_a_bounded_alert_tail` |
| 投递失败不中断循环 | `test_a_raising_alert_sink_does_not_lose_the_loop` |
| 无账户归因也算进展 | `test_an_attempt_counts_as_progress_without_a_resolvable_account` |
| 未启用时零注入、零行为变化 | `test_the_host_injects_nothing_unless_the_feature_is_enabled` / `test_without_hooks_the_loop_and_its_payload_are_unchanged` |
| 预留不泄漏 | `test_the_host_cost_seam_never_leaks_a_reservation` |

### 14.5 仍然未闭环（诚实清单）

1. **预算预留式防并发超支未接**：`cost_budget_include_reservations` 在当前宿主路径上无效，
   因为宿主不携带 token。要闭合需把 token 按 task_id 贯穿 claim→settle 并在全部 abandon 路径
   release；漏一条路径就会永久锁死预算，故单列改动。
2. **C3 租约与休眠恢复**：仍未动（[C3 项目](C3_LEASE_RECOVERY_PROJECT.md)），且与 `stop` 语义
   相邻，必须独立评审。
3. **真实账户/故障注入长跑**：24h 验收仍是虚拟时钟仿真（§13.5），真实账户下的长跑证据待补。
4. **全量回归未在本机跑完**：全仓 `pytest` 触发 pytest 内部 `MemoryError`；`tests/platform_v1`
   单独串跑 43 分钟未收敛（socket/durable 用例）。本轮按改动所在面分组取证：多账户 203、
   协调器/宿主 227、额度/目标/任务服务 417。全量结论以 CI 的 `baseline`/`state-gate` 为准。

## 15. 真实账户验收（2026-11-05，Owner 授权）

前几轮的所有证据都来自合成账户与虚拟时钟。本节记录第一次**对真实机器、真实账户**的验收，
以及它暴露出的三个真实缺口。

环境：Magpie 桌面版 `0.1.2945`（GUI，loopback `127.0.0.1:3425`，**无 CLI**）；
`claude` 2.1.300 与 `codex` 可调用；`magpie` 不在 PATH（`magpie_usage_ingest` 期望的 CLI 不存在）。

### 15.1 真实池

`fetch_magpie_snapshot()` 返回 **11 个账户 / 11 个 provider**：
claude、codex、copilot、minimax-code、opencode-zen-free、openrouter、raccoon、trae-cn、
workbuddy、workbuddy-ai、zcode。真实额度举例：codex 5h 用 0% / 7d 用 43%；
workbuddy 额外额度用 72.78%；trae-cn 用 37.04%。

### 15.2 发现并修复的三个真实缺口

| # | 缺口（真实证据） | 影响 | 修复 |
|---|---|---|---|
| R1 | `platform_quota_observations` 有 **0 行**：该表只在 `claim_task` 的准入路径内被写 | 首次派发前感知**全盲**：Magpie 报 11 个账户，大脑看到 0 个 | 新增 `control_store.record_quota_observation(s)`（按 `observed_at` 单调，不倒退）+ `multi_account/perception_sync.py`（快照→观测行，PII 白名单）+ `trusted_host.sync_multi_account_observations()` |
| R2 | 只同步一次会**固化**：Magpie 惰性读取，`observation_freshness_seconds` 默认 600 s，读数老化后全池转 STALE | "持续感知"实际只成立几分钟；实测可用账户从 7 衰减到 1 | 协调器新增 `pool_refresh` 接缝，按 **reconcile 节奏**刷新（60 s 去抖），且**不在感知/路由路径上**发网络请求 |
| R3 | 部分不可观测**完全静默**：规则只在"全部 STALE/UNKNOWN"时告警 | 11 个账户里 4 个不可用（36%）时，运维面只看到"7 个健康" | 新增 `perception_partial`（WARNING，≥2 个且 ≥25% 不可观测，池级去重） |

### 15.3 真实调用与真实成本

每账户一次最小请求（`Reply with exactly: OK`），沙箱只读、180 s 硬超时、超时最多重试 1 次：

| 账户 | 结果 | 墙钟 | 计费 | 口径 |
|---|---|---|---|---|
| claude-code | 成功 | 8.2–12.6 s | **$0.00228–0.00432** | CLI 上报 `total_cost_usd`（列表价） |
| codex | 成功 1 次 / 超时 2 次 | 22.2 s（成功时） | 未上报 | `priced=false`，入账并标记，**不当作免费** |

codex 的超时是环境事实（内部 MCP 握手卡住），不是账户故障；探针按"超时最多重试一次、
仍失败则如实上报"处理，而不是重试到静默。

真实 30 天经济性（`/v1/magpie/usage`）：**5502 次调用 / 194 次错误 / 43 次重试 /
成本 $58.6993 / 未计价 2338 次**。按账户错误率：0.857、0.420、0.044、0.031、0.024、
0.019、0.003、0.002；全池成功率 0.9647。

### 15.4 验收结果（`scripts/multi_account_real_acceptance.py --live`）

`11/11 PASS`，报告：`reports/multi_account/real_acceptance_latest.md`。

| 验收项 | 结果 | 关键证据 |
|---|---|---|
| 多账户整合 | PASS | 11 账户 / 11 provider，无按 provider 折叠 |
| 状态感知 | PASS | 落库 11、读回 11；FRESH 6 / STALE 3 / UNKNOWN 2（修正保鲜期后可用 6，此前为 0） |
| 调度选中真实可用账户 | PASS | `minimax-code`（HEALTHY，headroom 100，`best_headroom`） |
| 异常容错 | PASS | 对真实错误率最高账户（copilot 0.857）注入故障 → reroute 到另一真实账户 |
| 真实账户调用 | PASS | claude 11–14 s / $0.0020–0.0023；codex 超时如实上报 |
| 未知成本不为免费 | PASS | 1 计价 + 1 未计价，未计价入账 `priced=false` |
| 成本上限 | PASS | 以真实 30 天花费 $58.6993 为基线，双倍请求被 `cost_budget_exhausted` 拒绝 |
| 告警 | PASS | 真实池触发 `perception_partial` |
| 自进化下限 | PASS | 真实成功率 0.9647 > 目标 0.85 → **不改权重**（版本 0） |
| 自进化生效 | PASS | 真实 0.857 错误率账户重采样 → v2，2 条审计，回滚后回基线 |
| 运行时长 | PASS | 真实时钟 1.05 s 后 `conclude`（`run_deadline_reached`） |

探针总花费：**约 $0.002/次**（单次 claude 调用，随上下文略有浮动）。

### 15.5 "系统改自己"记录

感知落库模块 `multi_account/perception_sync.py` 与其 10 例测试由**本平台自己的账户执行器**
（`claude -p`，工作区写权限，13 轮，花费 $0.0182）写出。它无法在本环境运行测试（其 shell
入口直接失败），因此由监督者按 `AGENTS.md` 的兜底条款复核：契约逐条比对、单测实跑
（10 passed），并补上控制库写入、宿主同步、刷新节奏与告警规则。
**agent 产出的代码未经其自身验证，一律视为草稿。**

### 15.6 本轮仍未闭环

1. ~~`magpie_usage_ingest` 仍期望 CLI~~ **已闭合（Owner 2026-11-05 批准口径变更）**：
   新增 `read_usage_http()` / `facts_from_http()`，`ingest(source="auto"|"cli"|"http")` 在无 CLI 时
   自动改读 `/v1/magpie/usage`；`cost_report --source` 与 `--doctor` 同步支持。真实结果：
   5502 调用 / 194 错误 / **$58.6993** / 8 个账户，`basis_provenance="magpie_http_reported_cost"`。
   口径诚实性：HTTP 只有**一个合计**，没有逐请求行，也没有现金/订阅二分，因此
   `cash_usd`/`quota_value_usd` 保持 0，合计放进 `reported_cost_usd`/`spend_total`，并标
   `split_unavailable=true`；`failed_cost_share=null`（错误被计数但未被定价）。
   逐请求归因仍需 CLI。
2. ~~保鲜期与 provider 读取节奏不匹配~~ **已闭合**：默认 `observation_freshness_seconds`
   600 → **1800**、`magpie_max_age_seconds` 900 → **2400**（保持 `freshness < max_age` 不变量）。
   实测复核：同一真实池在该默认下 **HEALTHY 6 / STALE 3 / UNKNOWN 2**（可用 6，2600 前是 0）；
   3 个真正陈旧（48–99 分钟）仍被判 STALE，说明规则没有被放宽到失效。
   回归：`test_a_lazily_read_account_stays_usable_for_half_an_hour`、
   `test_a_genuinely_stale_reading_is_still_caught`。
3. codex CLI 的 MCP 启动偶发挂起（>180 s），未定位；已按超时上报，不影响调度正确性。
4. 真实长跑（数小时无人值守 + 真实故障）仍未做；本节是**单轮真实验收**，不是长跑证据。
5. 真实池里仍有 2 个账户长期 UNKNOWN（`zcode`、`opencode-zen-free`：Magpie 从未给出读数）。
   `perception_partial` 会持续提示；这是上游观测缺失，不是本仓可修的问题。
