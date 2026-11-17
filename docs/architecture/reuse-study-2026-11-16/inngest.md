# Inngest — 固定源码深度审计：持久 Step、重试、并发与跨部署恢复

> 2026-11-17 | ONE PROJECT | R1 DOCS-ONLY | STATIC_SOURCE_AUDIT | NO EXECUTION / NO INSTALL / NOT VERIFIED / NO IMPLEMENTATION AUTHORITY
>
> Nerelan: [main@5c69e891](https://github.com/dddd2024/Nerelan/commit/5c69e891e3a559a23e7fd4e3115422c057df4438)
> · Upstream: [inngest/inngest@ef60fe90](https://github.com/inngest/inngest/commit/ef60fe903a4ada1b436cefc5d272e7a037e66d12)
> · Research Issue [#1648](https://github.com/dddd2024/Nerelan/issues/1648)
> · Canonical index [#1576](https://github.com/dddd2024/Nerelan/issues/1576)

## 0. 去重和新增问题

先检查 #1576 与 28 条已有研究索引评论、GitHub Issues/PR/代码关键词 'Inngest'、已有 DBOS/Temporal/LangGraph 研究。main 的 [B-durable.md 第 88–90 行](https://github.com/dddd2024/Nerelan/blob/5c69e891e3a559a23e7fd4e3115422c057df4438/docs/architecture/reuse-study-2026-11-15/B-durable.md#L88-L90) 明确“未深入研究 Inngest”。这不是首次提及持久工作流，更不是再评估是否重写 Nerelan。**本轮只填 Inngest 专项源码缺口**：Nerelan 连续模式中已完成的步骤如何持久记账、丢失 ACK 的副作用如何处理、等待中的 Goal 是否占并发、跨部署步骤身份如何固定。

已归档的 DBOS、Temporal、Paperclip、Mastra、Goose、Pydantic AI 等不得以不同项目名重开。当前相关实施所有权：[DBOS spike #1546](https://github.com/dddd2024/Nerelan/issues/1546)、[PENDING dispatch 对账 #1597](https://github.com/dddd2024/Nerelan/issues/1597)、[429 分类 #1530](https://github.com/dddd2024/Nerelan/issues/1530)、[用量 #1531](https://github.com/dddd2024/Nerelan/issues/1531)、[Agent×Model #1527](https://github.com/dddd2024/Nerelan/issues/1527)。

## 1. 上游代码结构与实质结论

| 模块 | 固定版本证据 | 机制 / 风险 |
|---|---|---|
| SDK/server 边界 | [README.md](https://github.com/inngest/inngest/blob/ef60fe903a4ada1b436cefc5d272e7a037e66d12/README.md), [SDK_SPEC.md](https://github.com/inngest/inngest/blob/ef60fe903a4ada1b436cefc5d272e7a037e66d12/docs/SDK_SPEC.md) | Event+Scheduler 将函数排入 queue；executor 拆解阶段，state store 持久化 step 输出/错误；SDK 的 call request 通过重放发现及 memoize 上一步。不是简单 Python decorator 生成持久效果。 |
| Step 收据 | [SDK_SPEC.md 的 Steps/Memoizing/Recovery](https://github.com/inngest/inngest/blob/ef60fe903a4ada1b436cefc5d272e7a037e66d12/docs/SDK_SPEC.md) | 已完成 Step 通过稳定 ID 和序列化结果读回。外部效果已发生但结果未写入 state 的间隙依然是 **at-least-once** 风险，而不是 exactly-once。 |
| Retry 分类 | [queue.go L195–268](https://github.com/inngest/inngest/blob/ef60fe903a4ada1b436cefc5d272e7a037e66d12/pkg/execution/queue/queue.go#L195-L268), [executor/run_context.go L112–120](https://github.com/inngest/inngest/blob/ef60fe903a4ada1b436cefc5d272e7a037e66d12/pkg/execution/executor/run_context.go#L112-L120), [executor/util.go L180–194](https://github.com/inngest/inngest/blob/ef60fe903a4ada1b436cefc5d272e7a037e66d12/pkg/execution/executor/util.go#L180-L194) | queue.ShouldRetry 先遍历嵌套错误；NonRetryableError 阻断通用重试；AlwaysRetryableError 可越过配置的 max attempts。Nerelan 不能把后者当无上界的预算豁免。 |
| Lease 及续期 | [redis_state/queue.go L870–1050](https://github.com/inngest/inngest/blob/ef60fe903a4ada1b436cefc5d272e7a037e66d12/pkg/execution/state/redis_state/queue.go#L870-L1050), [queue/shard_lease.go L164–214](https://github.com/inngest/inngest/blob/ef60fe903a4ada1b436cefc5d272e7a037e66d12/pkg/execution/queue/shard_lease.go#L164-L214) | Lease 创建到期 ULID；续期必须传原 lease ID；shard 续期失败令对应处理者退出，不继续对外宣称所有权。 |
| 并发计量 | [enums/concurrency_mode.go](https://github.com/inngest/inngest/blob/ef60fe903a4ada1b436cefc5d272e7a037e66d12/pkg/enums/concurrency_mode.go), [inngest/concurrency.go](https://github.com/inngest/inngest/blob/ef60fe903a4ada1b436cefc5d272e7a037e66d12/pkg/inngest/concurrency.go) | 内部区分 Run/Step 容量；公开 [Step concurrency 文档](https://www.inngest.com/docs/durable-execution/flow-control/concurrency) 表示 sleep、wait 等非执行等待不占执行 slot。 |
| 去重边界 | [consts.go L138–143](https://github.com/inngest/inngest/blob/ef60fe903a4ada1b436cefc5d272e7a037e66d12/pkg/consts/consts.go#L138-L143), [Idempotency 文档](https://www.inngest.com/docs/durable-execution/guides-and-advanced/idempotency) | FunctionIdempotencyPeriod 为 24 小时。连续无期限任务不能用固定时窗取代持久 operation identity，也不能误认为外部 effect exactly-once。 |
| 版本兼容 | [SDK_SPEC.md](https://github.com/inngest/inngest/blob/ef60fe903a4ada1b436cefc5d272e7a037e66d12/docs/SDK_SPEC.md), [Versioning 文档](https://www.inngest.com/docs/durable-execution/guides-and-advanced/versioning) | 更改正在运行步骤的 ID 会变成全新工作，即使旧副作用已经生效。顺序/逻辑变化和 SDK 重新发现也需回归验证。 |
| 许可/部署 | [LICENSE.md](https://github.com/inngest/inngest/blob/ef60fe903a4ada1b436cefc5d272e7a037e66d12/LICENSE.md), [README License](https://github.com/inngest/inngest/blob/ef60fe903a4ada1b436cefc5d272e7a037e66d12/README.md) | Inngest server/CLI 是 SSPL-1.0 + future Apache-2.0（DOSP）组合，SDK 许可 Apache-2.0；复制服务端代码/再分发应先法务核对。本轮不安装或部署 server。 |

**注意**：表格给出的源码事实与设计推论不同。上游 SDK/Server 的完整 runtime 行为未在 Nerelan 上运行验证；“成功步骤读回”不等于执行器工作区、Reviewer、GitHub 写入都天然可重放。

## 2. Nerelan 当前真实实现对照

| Nerelan 面 | 当前源码/Issue | 裁定 | 可借鉴的最小增量 |
|---|---|---|---|
| TaskStore 与 durable run | [run_store.py](https://github.com/dddd2024/Nerelan/blob/5c69e891e3a559a23e7fd4e3115422c057df4438/reverse_agent/platform_v1/run_store.py) 定义 lease_owner、lease_epoch、heartbeat_at_ms、lease_expiry_ms；[C3 lease recovery](https://github.com/dddd2024/Nerelan/blob/main/docs/architecture/C3_LEASE_RECOVERY_PROJECT.md) | **ALREADY_REUSED** | 已有 fencing / 心跳，不另抄 Inngest Redis queue 或存储引擎。只增加针对老 epoch 回写的组合回归。 |
| Provider liveness | [goal_service.py L178–199](https://github.com/dddd2024/Nerelan/blob/5c69e891e3a559a23e7fd4e3115422c057df4438/reverse_agent/platform_v1/goal_service.py#L178-L199) + [quota_guard.py L164–199](https://github.com/dddd2024/Nerelan/blob/5c69e891e3a559a23e7fd4e3115422c057df4438/reverse_agent/platform_v1/quota_guard.py#L164-L199), [#1596](https://github.com/dddd2024/Nerelan/issues/1596) 已 closed | **ALREADY_REUSED** | stall reroute、binding cool-down、持续模式 backoff 现有代码已有，不重提“换模型重试”作为新功能。 |
| 恢复过程中的 PENDING 外部请求 | [#1597](https://github.com/dddd2024/Nerelan/issues/1597) | **BORROW_PATTERN · P0** | 在原 operation store 上为单个外部副作用定义稳定 identity、相位及收据；崩溃后只能在有证据时将 PENDING 转为确定状态，UNKNOWN 一律 park。 |
| Goal-level 持久引擎 | [#1546 DBOS spike](https://github.com/dddd2024/Nerelan/issues/1546) | **BORROW_PATTERN · P1** | Inngest 的稳定 step ID / replay 兼容性进入 DBOS spike 的对照用例；不新建第二类引擎试点。 |
| Active capacity / wait | [continuous run #1538](https://github.com/dddd2024/Nerelan/issues/1538), [#1546](https://github.com/dddd2024/Nerelan/issues/1546) | **BORROW_PATTERN · P1** | 区分正在占用 executor 的 attempt 与 waiting Goal：等待 quota/approval/review 时不占执行槽，但 Owner 全局 concurrency 始终是硬上限。只加观测/测试，不私自更改 Owner 授权。 |
| 上游错误 | [#1530](https://github.com/dddd2024/Nerelan/issues/1530), [#1596](https://github.com/dddd2024/Nerelan/issues/1596) | **BORROW_PATTERN · P0** | 明确 nonretryable scope（永久 credit/auth）、retry-after time（真实 reset time）和 transient retry（另一可用 binding）；复用 Magpie/provider evidence。 |
| 账本与成本 | [#1531](https://github.com/dddd2024/Nerelan/issues/1531), [#1342](https://github.com/dddd2024/Nerelan/issues/1342) | **REJECT COPY** | 用量从 Magpie 原生 request/attempt 归因；不复制 Inngest State Store 作为第二成本账本。 |
| Agent / Executor / Plugin / MCP | [#1527](https://github.com/dddd2024/Nerelan/issues/1527), [#790](https://github.com/dddd2024/Nerelan/issues/790), [#253](https://github.com/dddd2024/Nerelan/issues/253) | **NO NEW DIRECT REUSE** | Inngest 的编排机制不是多执行器能力 contract 或 MCP 插件权限系统；不混为一谈。 |
| 用户视角 | [#1561](https://github.com/dddd2024/Nerelan/issues/1561), [#280](https://github.com/dddd2024/Nerelan/issues/280) | **BORROW_PATTERN · P2** | Goal UI 仅显示可信 phase、last step receipt、pending reason、下一次可重试时间、UNKNOWN 是否需人工核对；不展示无依据的“已恢复成功”。 |

**结论：** 没有发现超越现有 #1546/#1597 所有权、足以直接替换当前 Python+SQLite 本地优先架构的理由。Inngest 的价值是帮助检验我们的协议边界，而不是引入新 server。License 也使直接移植服务端代码风险较高。

## 3. 更精确的可以“抄”的协议形状（建议，不代表已实现）

一个外部操作只生成一个稳定 business operation ID，不随 retry、模型切换或部署而改变：

| 字段 | 意义 |
|---|---|
| goal_id / plan_step_id | 长时逻辑目标和步骤；不要使用一次性的 process id 当真相 |
| operation_id | 外部 side-effect 唯一身份；由 Goal+step+operation kind 稳定推导，跨 24h 保留 |
| phase_kind / phase_version | PREPARE、DISPATCH、SETTLE、REVIEW、PUBLISH 等明确阶段和版本 |
| lease_epoch / owner | 防止旧 worker 继续回写；claim/renew 受 store owner 校验 |
| status | NOT_STARTED → PENDING → CONFIRMED / DEFINITELY_NOT_EXECUTED / UNKNOWN；UNKNOWN 不准自动变成功或无成本 |
| effect_receipt | request/session/job identity、时间、外部已完成证据、digest，而不是盲信模型的完成声明 |
| next_eligible_at / hold_scope | 区分账户/供应商阻塞、step 可重试时间、总并发和执行槽 |

操作决策原则：先 read receipt，再看是否允许调用；若 PENDING 且无事实级 reconciliation 证据就 park；若 receipt 已确认则只返回保存的结果；若确证未执行可复用相同 operation_id；只在任命的新 epoch 下继续。若是真正不能提供幂等保障的外部 API，要保留 UNKNOWN 冲突给 Supervisor/Owner，而不是自动消去。

这是一份**验收 contract 提案**，不是要求把全部字段塞进新表；优先用现有 TaskStore/operation trail 的真实字段和升级约束，禁止建立第二账本/第二状态源。

## 4. 最小故障测试 / Go–No-Go（未执行）

| Case | 刺激 | 期望不变量 | 所属 Issue |
|---|---|---|---|
| F1 | 准备 worktree 完成后，dispatch 前 kill -9 | 复用或重建 workspace，无新 Goal/重复外部调用 | #1597 |
| F2 | 调用已被 provider 接受、ACK 丢失 | operation=PENDING/UNKNOWN，不得重放至有确证 | #1597 |
| F3 | phase receipt 事务提交后 kill -9 | 只读已有收据，外部 call 数=1 | #1597/#1546 |
| F4 | 旧 worker lease 失效，另一个 epoch 领取 | 旧 epoch 拒绝写回，不能清理新 owner workspace | #1546 |
| F5 | 同时 3 个等待配额、1 个可执行任务，限额并发=1 | 仅真正执行 attempt 占槽，Owner 总并发限制不放宽 | #1546 |
| F6 | step ID 改名、函数逻辑重排后 redeploy | 版本门禁检测，避免把已完成副作用当新 step 重放 | #1546 |
| F7 | 相同 operation 在第 25 小时重试 | 仍去重/审计；24h cache 不能当防线 | #1597 |
| F8 | gateway 记录 429/credits、agent 静默 | 分类 account hold，按 reset time 或 Owner 解封；不白耗 900s | #1530 |
| F9 | 有无 Inngest/DBOS 的相同任务对比 | 独立验收成功率↑且真实完整成本↓；否则不迁移 | #1546/#1527 |

**DBOS 的既有 Go 条件不放宽**：#1546 需要 Windows/Python3.13 的进程强杀验证、不会重复外部请求、重绑定成功、净替换约 3k 行才值得推进。Inngest 不另起一轮第二 workflow 引擎试验。任何新增 dependency 属 R2，需明确 Owner 决定。

## 5. 证据级别与接下来的动作

- **已做**：实时 GitHub 查重；读取固定上游 commit 的 README/SDK_SPEC/queue/executor/lease/concurrency/idempotency/LICENSE 与当前 Nerelan 的 AGENTS、run_store、goal_service、quota_guard、B-durable；关联现有实施 Issue。没有把 #1596 已 closed 的能力误列为待实现。
- **未做**：clone、安装 Inngest CLI/server、执行 upstream 单测、执行 Nerelan pytest、真实 crash/redeploy 实验、模型或 Magpie 请求、性能/经济性 benchmark；不能声称可运行、实现、节省成本或避免副作用。
- **第一优先**：在 #1597 的已有实现路径补 F2/F3/F7 作为阻断用例，先观察现有 store 是否已覆盖。后续由 #1546 执行 F4–F6，#1530 执行 F8，#1527 纳入 F9。
- **不可复制**：Inngest Server / Scheduler / Redis Queue 作为第二存储或运行时；24h 去重时限作为永久 ID；AlwaysRetryable 越权绕过 Owner 限额；未经核查的服务端源代码拷贝。
- **本次裁定**：`BORROW_PATTERN`；`STATIC_SOURCE_AUDIT`；R1 docs-only Draft PR，CI/独立 exact-head review 未过之前不是合入 main 的事实。
