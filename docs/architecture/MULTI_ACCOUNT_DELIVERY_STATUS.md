# 多账户优化：交付边界与验收状态

本文件校正同目录历史规划文档。第一阶段 PR #1378 的修正 head
`2520e3f755bf5e35749f251828c1871294992c72` 经独立 ACCEPT 与全部必需检查，已合入 main
`cd087399d89170a352b36247c0df80ae4354d5fe`。完整 Linux 平台基线为 6421 passed、33 skipped。
第二阶段 #1379 的修正 head `c9ab14647bfc9188e91bb726b3dc9c592f098df3` 已经相同门禁合入 main
`3075bfac3fb204249792b9abf80a681793347c58`，平台基线为 6442 passed、33 skipped。
第三阶段 #1381 的修正 head `68c4a0e3f162f4320c8b5460a3c159cbb682d910` 已合入 main
`0b5ba18138133aa639a9303fe88c2927044908d5`，平台基线为 6459 passed、33 skipped，修复了 #1380。
首次资源阻塞的自动恢复 #1383 已合入 main `01478490c`，关闭了 #1382。
当前反馈证据修复及配置入口见 [反馈验证交付](MULTI_ACCOUNT_FEEDBACK_VERIFICATION.md)，
具体合入状态以对应 PR 为准。**未部署、未启用，完整产品目标仍未验收。**
后续生产尝试反馈归属、成本完整性和原子重放修复见
[尝试反馈交付](MULTI_ACCOUNT_ATTEMPT_FEEDBACK.md)，每个切片单独走 exact-head 门禁。
反馈进入原生产路由器的默认关闭、有界策略见 [反馈选路](MULTI_ACCOUNT_FEEDBACK_ROUTING.md)；
具体合入状态与真实运行验收继续分开记录。
单测、CLI 帮助和进程级探针均不能替代真实生产验收。

## 本轮增量：成本 / 告警 / 时长 / 策略闭环（候选分支，未合入）

前几轮把账户纳管做到了"能感知、能隔离、能选路"，但四件长跑必需的事仍只有模块、
没有生产调用方：成本上限、运行时长、告警送达、策略限幅/回滚。本轮增量补齐这四条闭环，
并把分支与 main 的 73 个提交做过一次显式对账（不覆盖 main 的原子反馈与更严格校验）。

| 新增模块 | 职责 | 与既有实现的关系 |
|---|---|---|
| `multi_account/budget.py` | 滚动窗口成本上限，`allow/degrade/deny` + 预留/结算/TTL | 复用 `quota_reservation` 语义，不新增账本 |
| `multi_account/alerts.py` | 规则化告警、`(code, subject)` 抑制、有界历史、可选 JSONL 日志与轮转 | 复用宿主 sink，不新增消息系统 |
| `multi_account/watchdog.py` | 单次运行墙钟与空闲预算，`continue/conclude/stop` | 复用既有协调器循环，不新增调度器 |
| `multi_account/policy.py` | 有界、限幅、可审计、可回滚的调度权重链 | 只调既有权重，不新增决策引擎 |
| `multi_account/cli.py` | 运维只读视图与回滚入口 | 复用同一 store，不新增服务 |
| `multi_account/perception_sync.py` | Magpie 快照 → 观测表（仅白名单字段） | 复用 `ControlStore` 写入，不接管凭据 |

对账时保留的 main 侧更强保证（不得回退）：`record_account_feedback` 的单事务原子写入与
`outcome_id` 重放去重、配置与评分的严格校验、`feedback_policy` 的生产选路开关。
本轮的预算结算、心跳与策略步进一律挂在该临界区内，重放回执不重复结算、不重复累计样本。

仍未验收的部分与本文件其余部分一致：**未部署、未启用、未在真实账户长跑**。
本地验证为 provider-free（虚拟时钟 + 单元/接线/连续性回归）；真实账户故障注入、
宿主休眠恢复与 24h+ 长跑仍需对应环境的操作授权。验收脚本的通过不构成真实成本结论。

详细结构（实现摘要 / 功能边界 / 关键模块 / 可配置项 / 验收结果 / 已知限制）见
[多账户闭环交付说明](../../reports/multi_account/DELIVERY_MULTI_ACCOUNT_V5.md)。

## 功能边界与复用

Nerelan 保持 local-first 受控开发平台定位：目标与任务真相、授权、预算、独立验证、
恢复证据与受控合入属于本仓。账户凭据、同服务账户切换、请求重试与额度等待优先复用
Magpie；编排复用既有 LangGraph 适配层和 TaskStore。本轮不增加运行时、队列或依赖。
CLI 能力存在不证明本机切换行为已经验证。

| 模块 | 职责及实际消费边界 |
|---|---|
| `model_access` / `trusted_host` | 身份与硬准入；保留 main 的账户命名空间、重复身份冲突检查与本机 CLI 独立证据；provider 汇总不能替代账户证据 |
| `multi_account.status` | 观测归一、新鲜度、健康分类；单个坏观测不拖垮整池 |
| `cooldowns` / `scoring` | fallback 隔离与有界 EWMA；终态反馈已接线；异常隔离现进入生产选路，评分排序尚未接线 |
| `dispatch` | 可选建议与反馈入口；失败回退不替代授权、预算及硬额度准入 |
| `evolution` | 复用 break-even 算法；生产决策没有规模、验证反馈没有完整模式/成本，模式学习尚未闭环 |
| `magpie_usage_ingest` / `cost_report` | 只读成本证据；请求关联不证明完整覆盖，无完整性证据时严格现金/额度 all-in 为 UNKNOWN |
| `durable_execution` / coordinator | 原有租约恢复；C3 令牌仅保留组件探针，撤出不完整生产调用，不提供新的生产写入 fencing |
| frontend resources | 显示账户归属；“路由已绑定”不等于“正在使用” |

不包含凭据读写、登录态切换、部署、真实付费试跑、扩预算、历史 UNKNOWN 核销或门禁放松。
自进化不得修改授权、自行发布或自动晋升未经验证的策略。

## 本轮监督与修正

### 首次资源阻塞恢复（#1382，独立 R1 候选）

此前 `agent_team` Goal 首次选模时若全池暂不可用，会生成空 binding 的 BLOCKED Task，
但协调器只扫描可运行任务。即使账户恢复，Goal/Task 仍停在 BLOCKED，解析器也不会再被调用。
该行为已通过真实 GoalService/ControlStore/Coordinator 与模拟可用性的隔离探针复现。

实现继续复用现有目标、任务、窗口、事件与准入链，不增加队列、定时服务、依赖或表结构：

| 模块 | 新增职责及边界 |
|---|---|
| `model_router.ModelSelectionError` | 从完整排除集合汇总临时资源原因和可重查时间；不依赖截断为 10 项的展示列表；固定绑定只考虑其自身资源原因 |
| `GoalService._launch` | 仅在主开关开启且初始失败明确属于临时额度/隔离时，生成版本化 `initial_resource_wait` 标记；捕获当次仓库基线 |
| `GoalService.reconsider_initial_models` | 到期只重做观察与选模；显式 `probe_availability=False`，不借轮询发推理可用性探针；仍检查真实额度和能力 |
| `GoalService._commit_initial_selection` | 同一写事务内比较窗口时间、权限、目标/事件/执行标识、作者版本、历史证据和契约；更新原 Task、选模事件及 Goal 汇总 |
| `AutonomyService._check_window_authority` | 提取并复用原有策略摘要、Owner decision 摘要与 delegation slot 校验，未放宽授权条件；准备及提交时都复核 |
| `UnattendedCoordinator` | 复用宿主已注入的 GoalService；有空闲槽位时重查初始等待，再走原有硬准入与声明周期 |

标记绑定 Task/执行标识、Goal/版本/计划/产物摘要和冻结基线。只有从未派发的初始任务可恢复；
空 binding、BLOCKED 状态本身不是授权或“未执行”的证明。任何 claim、durable run、预算/发布/
用量/收费/外部 intent、worker 事件、已准备工作区/模型配置/验证结果等证据，都会阻止自动重激活。
UNKNOWN 及原始失败事件、冻结检查与交接契约均保留，不清理、不重置、不自动核销。
恢复必须存在批准计划所要求的功能检查、交接/导出及必需产物契约，并将已有契约内容与计划逐项比对。
契约缺失不代表“不需要检查”；缺失、语义不符或作者契约版本在解析期间变化时只保持阻塞，不重建批准证据。

恢复沿用同一个 Task 和 execution_id，不创建重试任务，不在实际准入前增加 tasks_started 或 retries_used。
native 执行器只能使用初次等待时冻结的基线，不能在恢复时读取新的 live HEAD。策略拒绝或真实的
内容拒绝、Owner 排除、能力/评审独立性失败会停在可解释的 BLOCKED，不能借资源恢复绕过。

评审有单独的“等待初始作者选择”标记，仅当作者确因上述资源问题暂未选定时使用。
按批准的完整祖先关系先恢复作者，再根据冻结模型/执行器、任务/执行版本、选模事件及用量身份快照选评审；
不猜测未绑定作者或 UNKNOWN。提交时再次比较快照，阻止解析期间来源变更。图较大时可跨轮补齐，
不会因只恢复作者而永久遗留没有路由的评审；真实独立性失败不继续自动轮询。

**配置及性能边界**：仍由 `REVERSE_AGENT_MULTI_ACCOUNT_ENABLED`（默认关闭）门控自动标记和重查。
内部 `INITIAL_MODEL_RECHECK_SECONDS=60`；已知资源到期时间按 1–60 秒范围安排，否则保守等 60 秒。
默认每轮最多 25 次路由解析（递归作者也计入），这是解析预算，**不是全部数据库扫描的硬上限**。
空闲、未标记或未到期目标不重载策略或发推理探针；作者尚未明确时只读取已有身份。
SQLite/RLock、目录/额度观测等原有调用仍有自身等待边界，未承诺整个 tick 的严格时限。

委托准入复用注入服务并传递禁止推理探针的意图，但现有固定检查器、零模型调用的委托边界保持不变，
不会因此获得通用模型执行授权。旧版、未标记的 BLOCKED/FAILED/UNKNOWN 记录不自动迁移或重试。

回归入口：`tests/platform_v1/test_initial_resource_recovery.py`，覆盖实际 launch→tick 恢复一次、持续等待、
作者/评审、独立连接竞争、版本/窗口/策略/事件/作者漂移、所有历史门槛、契约与基线保留、探针禁止及回滚。
这些是 provider-free 集成证据；真实账户混合池、成本收益与分级长跑仍需另行验收。

### 心跳存储故障恢复（C3 F3，#1380）

复用既有心跳和 TaskStore：仅对真实 SQLite BUSY/LOCKED 包装错误进行最多三次连续失败调用，
短停止事件等待，成功后复位。续期在获得数据库写锁后检查 owner、epoch 和持久 expiry，
过期租约不能被恢复心跳续活。单调时钟上限补充数据库检查；停止原因使用有限代码日志。
可复跑测试与完整限制见 [C3 实现记录](C3_LEASE_RECOVERY_PROJECT.md)。这不是完整休眠恢复或写入 fencing。

### 异常隔离生产接线（独立 R1 后续）

`dispatch.account_quarantine_guard` 是软建议，复用原冷却注册表，不新增队列或重试层。
仅对仍有效的账户级 `QUARANTINE` 生效；任务级瞬时冷却不跨任务屏蔽账户。统一按
`connection.account_ref`（缺失时为 connection id）识别，因此同账户多连接一起避让。

- `trusted_host._quota_check` 将隔离投影到现有候选检查，任务选模明确排除此原因，并附 `retry_at`。
- `_quota_guarded` 沿用既有同模型/更强备用路由；无替代账户时返回既有 `QUOTA_WAIT` 拒绝路径。
- `GoalService` 的额度等待重路由守卫也读取同一隔离，未收到新额度观测时仍能避让坏账户。
- 隔离到期恢复资格。固定绑定不能强制走坏账户；Magpie 接管、开关关闭或可选状态不可用时保持旧路由。
- 状态建议失败后仍执行旧额度检查，不能绕过硬额度准入、付款授权、能力边界或独立评审身份约束。
- 终态反馈只把明确的 provider 认证失败代码记作全局隔离；本地 `server_session_error`、
  作者身份或宿主授权错误不属于账户认证失败。历史隔离保持原到期时间，不重写既有证据。
- 宿主自身的 `QUOTA_WAIT:account_quarantined:no_alternative` 不产生新的学习反馈，
  防止反复等待被误当作 provider 失败，从而无限续长同一隔离。

全池隔离不会新增自动重试队列；角色路由沿用 `QUOTA_WAIT`，任务选模沿用不可用错误并在排除证据中
记录 `retry_at`。自动恢复初始选模与长跑行为仍需在后续任务生命周期验收中验证。
回归入口为 `tests/platform_v1/test_account_quarantine_routing.py`，实际调用宿主选模、角色回退
和 GoalService 守卫。普通评分排序、模式自进化与 C3 不在此切片范围。

未发现运行中的 Python 平台宿主，依据 AGENTS.md 监督者回退规则在隔离检出实施。
原工作区治理修改、运行数据及原分支完整保留。独立上下文对原 head 的
[REJECT](https://github.com/dddd2024/Nerelan/pull/1378#issuecomment-6648185480)
始终保留，修正后必须取得新的 exact-head verdict。

- 集成 main 时保留已合入的账户证据隔离，避免旧候选覆盖身份修复。
- 复现并修复第 1025 次连续失败的退避溢出；验证 2000 次故障仍封顶。
- 迟到失败不能解除或缩短活跃隔离；隔离过期后的成功允许清除失败历史。
- 启用后的派发工厂使用配置持久文件；关闭时工厂不写状态。
- 不再凭账户名称判断订阅；计费证据不足保持 UNKNOWN，非有限配置数值拒绝。
- 重复 session 记歧义；缺归因、定价或完整覆盖时严格经济指标 UNKNOWN。
- 快照升至 schema 2，拒绝与旧的不完整成本口径比较。
- 撤出只在执行前运行的 C3 令牌检查：执行后产物和恢复路径未获保护。

## 配置与回退

| 配置 | 默认及约束 |
|---|---|
| `REVERSE_AGENT_MULTI_ACCOUNT_ENABLED` | 关闭；门控可选反馈及初始资源等待恢复，不替代既有准入 |
| `REVERSE_AGENT_MULTI_ACCOUNT_STORE` | `.platform_v1_runtime/multi_account_break_even.json`；进程级状态，不允许多个宿主共享写入 |
| `REVERSE_AGENT_ACCOUNT_ROUTING` | `local`；支持 `local/magpie/auto`，不配置上游路由 |
| `REVERSE_AGENT_MAGPIE_ACCOUNT_SWITCHING` | 关闭；`auto` 同时要求它和 Magpie 启用标志为 1 |
| `REVERSE_AGENT_MAGPIE_EXE` | 无；只读 CLI 显式路径，CI 零真实 provider 调用 |
| `REVERSE_AGENT_MAGPIE_WAIT_TARGET` | 无；可取消等待仍需真实停机验证 |
| 观测新鲜度 / 快照上限 | 600 / 900 秒 |
| 重路由次数 / 退避 | 3 次；30 秒起、2 倍、900 秒封顶，仅为 fallback 能力 |
| 异常隔离 / 历史窗口 | 300 / 21600 秒；迟到成功不能解除活跃隔离 |
| EWMA alpha / 保留运行数 | 0.25 / 500；生产评分选路待接线 |
| `HEARTBEAT_STORAGE_MAX_FAILURES` | 内部固定 3 次连续失败调用；成功复位，不是增加 3 次重试 |
| 心跳重试等待 | `min(1秒, heartbeat_window × 0.1)`；不强制中断既有 SQLite/RLock 阻塞 |
| `INITIAL_MODEL_RECHECK_SECONDS` | 内部 60 秒；已知到期时间按 1–60 秒安排，否则等 60 秒 |
| `reconsider_initial_models(limit=25)` | 每轮路由解析预算；不代表全部数据库扫描上限，不新增推理探针 |

回退采用关闭开关并保留状态证据；不删除历史数据或清除 UNKNOWN。
JSON 原子替换只防半文件，不提供跨进程事务或审计日志保证。

## 验收与推进顺序

| 阶段 | 验收标准 | 现状 |
|---|---|---|
| P0 基线复用 | main/候选分开、模块责任唯一、独立 review | 第一阶段修正后独立 ACCEPT、必需 CI 通过并合入；后续切片单独过门禁 |
| P1 统一账户 | 同 provider 多账户、跨 provider、订阅+API 混合可归因；歧义不猜 | 身份与异常隔离已接线；首次资源等待恢复候选有回归，真实调度与生产评分排序待验收 |
| P2 稳定运行 | 耗尽/异常/断网/上游不可用/重启注入；无丢任务、不受控重放 | F3 SQLite 锁故障修复已合入；整体恢复与副作用链待验收 |
| P3 成本质量 | 全部尝试及规划/验证开销完整归因；三成本基准分列；同任务同验收标准对照 | 缺导出完整性证据；任务就绪状态不等于独立验收，不能据此宣称省钱 |
| P4 自进化 | 规模与终态反馈生产闭环；策略版本、回放、灰度、回滚；独立评估质量不降 | 算法组件存在，生产闭环和策略晋升待实现 |
| P5 长跑 | 24h→72h→7d；24h 至少 3 次休眠唤醒、2 次强杀，守住任务与租约证据 | 未运行；组件 kill9 探针不替代真实恢复验收 |
| 合入 | exact-head CI、独立 ACCEPT、Ready 后 landing-state-gate、合入前 verdict、matched-head merge | #1378/#1379/#1381 已完成；每个后续切片重新检查，不豁免门禁 |

优先闭合 P1/P2 生产消费路径并采集 P3 证据，再优化策略。P5 以实际经过时间和持久运行
证据验收。真实账户故障注入、宿主休眠与部署须有对应环境的明确操作授权。
