# 多额度账户统一纳管与自进化闭环 · 交付说明（v6）

分支：`agent/multi-account-full-loop-20261106`　基线：`origin/main @ 2a268b1e`（2026-11-06）
口径：只写**本分支已实现、且有可复跑证据**的能力。仿真验收与真实账户验收分开记录，
不合并成"已完成"。

v5 交付了四条闭环（成本/告警/时长/策略）并做了与 main 的对账。本轮不再加模块，
只做三件事：**把验收推进到真实账户池**、**修掉"报告状态强于落地状态"的缺陷**、
**厘清与并行 PR 的策略边界**。

---

## 1. 实现变更摘要

| # | 变更 | 位置 | 性质 |
|---|---|---|---|
| 1 | 真实账户验收首次跑通并留证（Magpie 0.1.3186，11 账户 / 11 provider） | `scripts/multi_account_real_acceptance.py` | 验收 |
| 2 | CLI 失败不再只有 `returncode:1`：脱敏采集诊断 + 按生产词表分类 + 只对传输类失败再打一次 + `failure_kind` 回灌冷却/进化 | 同上 | 缺陷修复（可观测性） |
| 3 | 告警验收不再依赖"池当时正好不健康"：由真实健康分布推导期望，健康池不误报、病池不静默 | 同上 | 缺陷修复（验收有效性） |
| 4 | 分节写入失败后回滚内存分区，后续写入不会把被拒值"顺带"持久 | `multi_account/evolution.py` | 缺陷修复（数据一致性） |
| 5 | 策略步进/回滚先持久化后采纳；写入失败返回 `persist_failed`，版本、权重、审计三者不变 | `multi_account/policy.py` | 缺陷修复（审计真实性） |
| 6 | `observe()` 返回提交结果而不是提案 | `multi_account/policy.py` | 缺陷修复（对外报告） |
| 7 | 新增 42 例回归：37 例探针分类/重试/脱敏/告警期望（含 1 例"期望与引擎不漂移"）、4 例策略写入失败、1 例分节写入回滚 | `tests/platform_v1/test_multi_account_real_probe.py` 等 | 验收 |
| 8 | 交付状态文档补记本轮增量与 PR #1389 边界 | `docs/architecture/MULTI_ACCOUNT_DELIVERY_STATUS.md` | 文档 |

### 1.1 本轮修掉的缺陷（都会在长跑中静默失效）

| # | 现象（长跑中的表现） | 根因 | 修复 |
|---|---|---|---|
| a | 账户时不时失败，但反馈里只有"失败 1 次"，看不出是凭据失效、额度耗尽还是网络抖动 → 冷却长度与进化方向都选错 | 探针不采集诊断，不分类 | 采集尾部诊断并脱敏，分类为 `account_abnormal`/`quota_exhausted`/`transient`/`task_failed`，与 `trusted_host._record_task_outcome` 同一词表 |
| b | 账户被锁后仍被反复重试，烧掉本已耗尽的额度 | 探针对任何失败都重试一次 | 只有传输类失败（超时/连接重置/5xx）允许再打一次；账户级失败直接交给切换 |
| c | 告警验收在健康池上必然失败，在病池上必然通过 —— 它验的是"今天池坏不坏" | 断言 `bool(codes)` | 由观测到的健康分布推导期望码集，双向断言；另加"手写期望 vs 引擎"漂移测试 |
| d | 写入失败一次后，内存里留着被拒的分区；下一次任意成功写入把它一起写进磁盘 —— 一次没有任何审计记录的状态变更 | `patch` 先改内存再落盘，无回滚 | 失败即恢复该分区（或删除新建分区）后再抛出 |
| e | 审计链显示"策略 v7"，重启后实际是 v6，且 `rollback(7)` 找不到该版本 | `_save` 吞异常；`observe` 返回提案 | 先持久化后采纳；失败返回 `persist_failed` 且不推进版本 |

共同点：**对外报告的状态强于实际落地的状态**。单机长跑里没有人盯着，这类偏差会把
"看起来在自愈"变成"实际在漂移"。

### 1.2 复用范围与替换边界

| 类别 | 对象 | 处置 | 边界 |
|---|---|---|---|
| 复用 | Magpie（`quota` / `usage` / `quota wait`，只读） | 复用 | 只读观测与可选等待委托；不接管账户内切换、登录态、凭据 |
| 复用 | `durable_execution`、`control_store`、`quota_reservation`、`SelfEvolutionStore` | 复用 | 租约/claim/预算/窗口/准入/标定沿用；新接缝只在这些调用前后插入 |
| 复用 | `orchestration_selector.break_even`、`delta_calibration` | 复用算法 | 只补持久化与反馈回路 |
| 复用 | `pydantic`、`sqlite`、标准库 | 复用 | 零新增第三方运行时依赖 |
| 新增（仅补缺） | `budget/alerts/watchdog/policy/cli/perception_sync` | 新增 | main 上不存在的能力，非并行实现 |
| **并行实现需收敛** | PR #1389 的 `multi_account/policy_lifecycle.py`（Draft，未合入） | **不引入** | 见下 |
| 不引入 | Celery/RQ、Temporal/Prefect、Ray、第二套重试队列 | 不引入 | 与既有单机租约/预算语义重叠，引入即第二编排脊柱 |
| 不改动 | `AGENTS.md`、`.github/workflows/**`、`landing_review.py` | 不改 | R2，需 Owner 决策 + 独立评审 |

**与 #1389 的边界与收敛条件**：#1389 把"有界权重演化"改写为反馈文档里的**纯转移函数**，
其 PR 描述批评的是"独立可变账本 + best-effort 持久化"的早期原型。本分支的 `PolicyLedger`
状态本来就写在同一个原子文档的 `policy` 分区（`persist=_persister("policy")`），
本轮补上"写不进去就不算改过"之后，两者语义已对齐。因此：

- **单一运行时权威是本分支的 `policy.py`**，不存在两套策略引擎同时生效的路径；
- 若 #1389 先合入，应以其纯转移函数**替换** `PolicyLedger` 的规则演算（规则表与限幅数学
  是同一套），而不是并存；
- 两者都只动 `reliability/cost/latency` 三个权重与 bonus cap，不新增决策引擎、不新增预算权力。

---

## 2. 功能边界

### 2.1 已实现（默认关闭，`REVERSE_AGENT_MULTI_ACCOUNT_ENABLED=1` 才启用）

- **多账户统一纳管**：按 `account_ref` 保留每账户独立窗口，修正同 provider 多账户互相覆盖。
- **持续状态感知**：七态健康分类，含余量、新鲜度、重置时刻；单坏观测不拖垮整池；观测源
  故障与"池为空"可区分。
- **异常容错**：有界重路由、双层冷却（任务级瞬时 + 账户级隔离）、指数退避封顶、
  dead-letter 留证、重启恢复隔离与评分。
- **成本限制**：滚动窗口上限，`allow/degrade/deny`；软阈值转最低成本账户；硬上限等待不超支；
  未知成本不记为 0。
- **运行时长**：单次运行墙钟 + 空闲预算；`conclude` 停止认领并排空在飞批次，`stop` 硬升级。
- **告警**：规则化生成、`(code, subject)` 抑制、有界历史、宿主 sink、可选本地 JSONL 轮转。
- **自进化**：成功率/失败类型/成本/延迟驱动的有界权重调整；限幅、样本门槛、版本链、
  审计、回滚；**写入失败即不推进**（本轮）。
- **真实账户可验证性**：真实池感知、真实故障分类、真实调用延迟/成本、真实 30 天经济性
  四条证据链（本轮）。

### 2.2 明确不做

- 不做账户凭据读写、登录态切换、同服务账户切换接管（属 Magpie）。
- 不新增调度器、消息队列、定时服务、数据库表或第三方运行时依赖。
- 不自动晋升策略、不修改授权/预算配置本身、不自行发布。
- 不含部署、扩预算、历史 UNKNOWN 核销或门禁放松；不修改治理文件（R2）。

---

## 3. 关键模块

| 模块 | 行数 | 职责 | 关键不变量 |
|---|---|---|---|
| `multi_account/__init__.py` | 487 | 门面：感知/调度/成本/告警/时长/进化组合 | 一个宿主只接触一个对象；反馈走同一把锁 |
| `multi_account/config.py` | 420 | 唯一配置面，构造即校验 | 非法组合**拒绝启动**，不静默取默认 |
| `multi_account/status.py` | 340 | 观测归一、健康分类、池化 | 坏观测不拖垮整池；观测故障 ≠ 空池 |
| `multi_account/budget.py` | 431 | 滚动窗口成本上限、预留/结算 | 拒绝只挂起并给 `retry_at`；不可用测量降级不崩溃 |
| `multi_account/alerts.py` | 463 | 规则引擎、抑制、有界历史、JSONL 轮转 | 重复事实不重复告警；长跑磁盘有界 |
| `multi_account/watchdog.py` | 162 | 运行时长与空闲预算 | 到期只停止认领，不中断在飞工作 |
| `multi_account/policy.py` | 456 | 限幅权重链、审计、回滚 | 单步有界、总漂移有界、**写不进去就不算改过** |
| `multi_account/scheduler.py` | 382 | 账户选路、重路由、dead-letter | 学习分只在同一健康类内生效 |
| `multi_account/evolution.py` | 380 | 单一原子状态文档（9 分区） | 分节写入全有或全无；缺失分区不被重启丢弃 |
| `multi_account/perception_sync.py` | 151 | Magpie 快照 → 观测表 | 只写白名单字段，不含凭据 |
| `multi_account/cli.py` | 142 | 运维只读视图 + 回滚 | 只读路径不产生副作用 |
| `scripts/multi_account_real_acceptance.py` | 620 | 真实池验收与证据生成 | 失败必须有类型；诊断必须脱敏且有界 |

---

## 4. 可配置项

共 57 项（55 个标量 + `account_routing` / `break_even_store_path`），全部可用环境变量设置，
构造时校验；`.env.example` 与代码映射表由测试相互约束。

| 组 | 代表配置项 | 默认值 | 说明 |
|---|---|---|---|
| 账户接入 | `..._MULTI_ACCOUNT_ENABLED`、`..._STORE`、`..._ACCOUNT_ROUTING` | 关闭 / 仓内路径 / `local` | 总开关、状态文档位置、选路归属 |
| 状态感知 | `..._FRESHNESS`、`..._MAGPIE_MAX_AGE`、`..._HIGH_UTILIZATION`、`..._RESET_SOON_SECONDS` | 1800 / 2400 / 90 / 1800 | 新鲜度与降级阈值 |
| 调度权重 | `..._RELIABILITY_WEIGHT`、`..._COST_WEIGHT`、`..._LATENCY_WEIGHT`、`..._SCORE_ALPHA` | 12 / 10 / 5 / 0.25 | 学习分权重与平滑 |
| 重试与降级 | `..._REROUTE_ATTEMPTS`、`..._BACKOFF_BASE`、`..._BACKOFF_MULTIPLIER`、`..._BACKOFF_MAX`、`..._DEAD_LETTER` | 3 / 30 / 2 / 900 / 开 | 重路由与退避 |
| 隔离 | `..._ABNORMAL_COOLDOWN`、`..._COOLDOWN_MEMORY`、`..._PERSIST_STATE` | 300 / 21600 / 开 | 账户级隔离与重启恢复 |
| 成本上限 | `..._COST_BUDGET`、`..._UNITS`、`..._WINDOW`、`..._SOFT_RATIO`、`..._TASK_UNITS`、`..._RESERVE_INFLIGHT`、`..._RESERVATION_TTL` | 关 / 0 / 86400 / 0.8 / 0 / 关 / 900 | 开启时必须给正数上限 |
| 运行时长 | `..._WATCHDOG`、`..._MAX_RUN_SECONDS`、`..._MAX_IDLE_SECONDS`、`..._HARD_STOP_RATIO` | 开 / 0 / 0 / 1.25 | 0 = 不限 |
| 日志与告警 | `..._ALERTS`、`..._ALERT_QUIET`、`..._ALERT_MAX_HISTORY`、`..._ALERT_STREAK`、`..._ALERT_MIN_SUCCESS`、`..._ALERT_JOURNAL`、`..._ALERT_JOURNAL_MAX_BYTES` | 开 / 300 / 120 / 2 / 0.6 / 空 / 5MB | 抑制窗口、有界历史、本地 JSONL（拒绝 URL） |
| 自进化开关 | `..._SELF_EVOLUTION`、`..._SCORING`、`..._POLICY`、`..._CALIBRATION_FEEDBACK` | 开 / 开 / 开 / 开 | 各闭环独立开关 |
| 自进化限幅 | `..._POLICY_STEP`、`..._POLICY_DRIFT`、`..._POLICY_MAX_BONUS`、`..._POLICY_MIN_SAMPLES`、`..._POLICY_TARGET_SUCCESS`、`..._POLICY_AUDIT_ENTRIES` | 0.25 / 0.5 / 12 / 5 / 0.85 / 120 | 单步、总漂移、样本门槛、审计长度 |
| 生产选路（main 侧） | `..._FEEDBACK_ROUTING`、`..._MIN_ATTEMPTS`、`..._MAX_ADJUSTMENT` | 关 / 3 / 0.1 | 默认关闭，未由本分支改动 |

---

## 5. 验收结果

### 5.1 真实账户验收（本次新增，证据可复跑）

`python scripts/multi_account_real_acceptance.py --live` → **11/11 PASS**，
本次真实调用花费 **$0.004321**。

| 验收标准 | 结果 | 真实证据 |
|---|---|---|
| 多账户整合 | PASS | Magpie 0.1.3186，**11 账户 / 11 provider**（claude、codex、copilot、minimax-code、opencode-zen-free、openrouter、raccoon、trae-cn、workbuddy、workbuddy-ai、zcode），按 `account_ref` 逐一保留 |
| 状态感知 | PASS | 真实快照落库后读回 11/11；FRESH 6 / STALE 3 / UNKNOWN 2；健康 HEALTHY 6 / STALE 3 / UNKNOWN 2 |
| 调度选真实账户 | PASS | 选中 `2826269bbabf`（minimax-code，HEADROOM 100%，理由 `best_headroom`） |
| 异常容错（真实故障源） | PASS | 失败账户取自**真实 30 天错误率最高者** `7605419d1a61`（copilot，错误率 0.8571），切换至 `2826269bbabf`（minimax-code） |
| 真实调用（延迟/成本） | PASS | claude-code **8.36 s / $0.0043206**（1 次成功）；codex **19.96 s**，不上报成本 → 记 `priced=false` |
| 未知成本不入零 | PASS | `spent_units` 只累计已计价部分，未计价调用入账并标记 |
| 成本上限 | PASS | 真实 30 天花费 **$58.6993**，上限 $59.6993 时 2× 花费被 `deny(cost_budget_exhausted)`，小额仍 `degrade`；30 天未计价调用 2338 次 |
| 告警与池一致 | PASS | 期望 `perception_partial`（5/11 不可观测）＝实际 `perception_partial`；无预算误报 |
| 健康池不被误调 | PASS | 真实池成功率 0.9647 > 目标 0.85 → 策略版本保持 0、审计 0 条 |
| 自进化可审计可回滚 | PASS | 用真实错误率 0.8571 重采样 → 策略 v1→v2，回滚追加 v3 且有效权重回基线 |
| 运行时长（真实时钟） | PASS | 1.05 s 后 `run_deadline_reached` → `conclude` |

### 5.2 仿真验收（虚拟时钟、确定性种子）

`python scripts/multi_account_acceptance.py` → **11/11 PASS**（与本轮代码同树复跑）：

| 验收标准 | 结果 | 证据 |
|---|---|---|
| 多账户整合 | PASS | 4/4 账户被调度（21/37/23/55 次） |
| 状态感知 | PASS | 全窗口零观测错误 |
| 异常容错·不丢任务 | PASS | 118 完成 + 0 隔离 + 2 待续 = 120 |
| 异常容错·切换/重试/降级 | PASS | 切换 36、重试 18、等待/降级 361 |
| 成本上限不被突破 | PASS | 11.983 ≤ 12.0（利用率 99.9%） |
| 连续运行·运行时长 | PASS | 虚拟 19.19 h 判定 conclude，待续 2 |
| 性能·控制环开销 | PASS | **0.499 ms/轮**（498 轮，真实 0.2484 s） |
| 反馈·健康池不误调 | PASS | 版本 0 |
| 反馈·异常池驱动变更 | PASS | 6 次有界变更 |
| 反馈·未使结果劣化 | PASS | 后半程成本 0.1035 vs 基线 0.1208；重试率 0.0 vs 0.3043 |
| 可审计可回滚 | PASS | 审计 6 条，版本链 v1..v6 |

### 5.3 回归测试

- 多账户面：**324 passed**（`pytest tests/platform_v1 -k multi_account`）。
- 受影响面（65 个引用 `multi_account` / `unattended_coordinator` / `trusted_host` /
  `cost_report` 的测试文件，分三批串行）：**2113 passed、11 failed、4 skipped、2 deselected**。
  11 例失败全部在 `test_dev_up_contract.py`（依赖本机 PowerShell 宿主），在**未改动**的
  `origin/main` 上同样 11 failed → 本机既有环境限制，与本轮无关。
- 本轮新增 **42 例**：37 例探针（13 组分类、7 组重试判定、4 组脱敏、7 组告警期望、1 组
  "手写期望 vs 引擎不漂移"、2 组尝试次数、3 组成功短路）；4 例策略写入失败（不报版本、
  可恢复、回滚被拒、快照可重启加载）；1 例分节写入回滚。

### 5.4 口径说明

- 真实账户验收在**本机**（Windows，Magpie 本机网关 + 已登录 CLI）完成，单次调用 1 个 prompt，
  无凭据读取；账户身份只用 Magpie 已截断的 sha256。
- 本轮 3 次 live 运行中有 1 次 claude-code 真实失败（7.92 s，`returncode:1`）。该次运行暴露了
  缺陷 a（无法归因），修复后同账户 8–9 s 成功；修复后的分类路径由 37 例单测覆盖，
  **live 故障腿是条件性的**：只有真实发生失败时才会执行（本次 SKIP，已在报告中显式标注）。
- 仿真验收通过不等于真实省钱结论；成本基准仍是列表价估算，不是账单现金。

---

## 6. 已知限制与扩展点

### 6.1 已知限制

1. **未部署、未启用**：`REVERSE_AGENT_MULTI_ACCOUNT_ENABLED` 默认关闭。
2. **成本是列表价估算**：`usage_ledger` 给的是 list-price；缺导出完整性证据时为 UNKNOWN 而非 0。
   本机 30 天 2338/（总调用）次未计价，这部分只能"不当作免费"，不能准确计费。
3. **单机语义**：状态文档是本地 JSON 原子替换，只防半文件与分节污染，不提供跨进程事务。
4. **预留释放依赖 TTL**（默认 900 s）：并发上限的边界是"在飞窗口"，不是严格单笔。
5. **策略链是规则驱动，不是学习器**：可解释、可回滚，但不会发现规则外的更优策略。
6. **未做 24h+/休眠唤醒/强杀长跑**：本轮只有最长 20 分钟级的进程内验证与单次真实调用。
7. **Windows 全量回归未跑完**（6798 例，串行约 3 小时；`pytest-xdist` 因 `object()` 参数化 ID
   不可跨进程收集）：以受影响面 + CI Linux 基线为准。
8. **live 故障腿条件执行**：真实池全绿时该项 SKIP，不伪造故障。

### 6.2 扩展点（按性价比排序）

1. **受控故障注入**：给验收脚本加一个显式 `--inject-fault`（例如临时无效凭据），让“真实失败
   被分类并切换”这条腿每次都能跑，且仍花 0 元。
2. **真实池灰度**：先只开感知与告警（只读），再开成本上限（`deny` 只挂起不丢任务），
   最后开策略链。
3. **成本证据补全**：把 Magpie `usage` 导出完整性与本仓 `cost_report` 对账，把 UNKNOWN
   从 2338 次降为可解释的少数。
4. **长跑验收**：24h → 72h → 7d，至少 3 次休眠唤醒、2 次强杀，核对任务、租约、成本三者一致。
5. **与 #1389 收敛**：以其纯转移函数替换 `PolicyLedger` 的规则演算，保留本轮"写不进去不算改过"
   的持久化语义。
6. **策略影子评估**：记录提案但不生效，用真实数据比较提案与基线，再决定是否放权。

---

## 复现

```bash
python scripts/multi_account_acceptance.py                      # 11/11 仿真验收
python scripts/multi_account_real_acceptance.py --live          # 11/11 真实账户验收（约 $0.004）
python -m pytest tests/platform_v1 -k multi_account -q          # 324 例
python -m reverse_agent.platform_v1.multi_account.cli status    # 运维视图
```

真实账户验收需要本机 Magpie 网关在 `127.0.0.1:3425` 监听；不可用时脚本以退出码 2
显式报告 `magpie unavailable`，不会伪造证据。
