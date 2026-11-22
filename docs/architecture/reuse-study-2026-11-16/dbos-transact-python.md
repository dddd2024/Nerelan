<!-- Research-only evidence; not an implementation approval. -->
> 本报告研究记录：[#1623](https://github.com/dddd2024/Nerelan/issues/1623)；研究索引：[#1576](https://github.com/dddd2024/Nerelan/issues/1576)。
> 研究对象和 Nerelan 代码版本见文内；静态审计，尚未进行 Windows 实测与源码引入。

# DBOS Transact Python — Nerelan Goal-level 持久运行源码深审（2026-11-17）

> **研究状态**：RESEARCH_ONLY / STATIC_SOURCE_REVIEW / NOT_INSTALLED / NO_RUNTIME_TEST / NOT_IMPLEMENTED / NO_IMPLEMENTATION_AUTHORITY
>
> **唯一上游**：[dbos-inc/dbos-transact-py@2cf279cf380152b426ecd451d573ccc41f5715a6](https://github.com/dbos-inc/dbos-transact-py/commit/2cf279cf380152b426ecd451d573ccc41f5715a6)，MIT `LICENSE`；**Nerelan 基线**：[main@c96732520f3bd5329fc254bc95a91c05768d3ef8](https://github.com/dddd2024/Nerelan/commit/c96732520f3bd5329fc254bc95a91c05768d3ef8)。

## 0. 查重与唯一实施归属

- 检查 [#1576 研究总索引](https://github.com/dddd2024/Nerelan/issues/1576)、`docs/architecture/reuse-study-2026-11-15/B-durable.md`（**已有横向比较**）、[既有 DBOS spike #1546](https://github.com/dddd2024/Nerelan/issues/1546)，以及 GitHub Issues、PR 中 `DBOS`/`dbos-transact` 检索；未找到独立 DBOS 固定 SHA 源码专项或研究 Draft PR。已覆盖的功能背景不重复当作新增发现。
- Microsoft Agent Framework [#1608](https://github.com/dddd2024/Nerelan/issues/1608) 已研究 checkpoint/side effect，但不是 DBOS 的恢复/队列实现。
- **实施唯一 Owner：#1546**；相关 #1530（liveness/failover）、#1191（长任务）、#120（lease/resume）、#1527（executor）、#1531（usage）、#299（sandbox）。本 Issue 只提交可复核的技术依据和最小实验，不重复创建实施 Issue。

## 1. 固定上游源码：真正能抄的设计

| 机制 | Pin 后源码 | 事实 / 容易误读处 |
|---|---|---|
| Workflow / versioned launch recovery | [`dbos/_dbos.py#L978-L1008`](https://github.com/dbos-inc/dbos-transact-py/blob/2cf279cf380152b426ecd451d573ccc41f5715a6/dbos/_dbos.py#L978-L1008), [`dbos/_recovery.py#L14-L27`](https://github.com/dbos-inc/dbos-transact-py/blob/2cf279cf380152b426ecd451d573ccc41f5715a6/dbos/_recovery.py#L14-L27) | 启动时只筛选当前 `executor_id` + `app_version` 的 PENDING；先重新入队而非直接再次跑；别把“启动后所有旧任务会恢复”当无条件承诺。 |
| Recovery fencing | [`dbos/_sys_db.py#L5657-L5690`](https://github.com/dbos-inc/dbos-transact-py/blob/2cf279cf380152b426ecd451d573ccc41f5715a6/dbos/_sys_db.py#L5657-L5690), [`_core.py#L1270-L1335`](https://github.com/dbos-inc/dbos-transact-py/blob/2cf279cf380152b426ecd451d573ccc41f5715a6/dbos/_core.py#L1270-L1335) | PENDING→ENQUEUED SQL 按旧 executor ID 和状态条件更新；新 dequeue 有 `owner_xid`；用于控制 *workflow runner* 的重复领取，**不证明外部 CLI/GitHub/API 只调用一次**。 |
| Step replay boundary | [`dbos/_core.py#L2423-L2600`](https://github.com/dbos-inc/dbos-transact-py/blob/2cf279cf380152b426ecd451d573ccc41f5715a6/dbos/_core.py#L2423-L2600), [`_sys_db.py#L3485-L3518`](https://github.com/dbos-inc/dbos-transact-py/blob/2cf279cf380152b426ecd451d573ccc41f5715a6/dbos/_sys_db.py#L3485-L3518) | 步骤进入前查记录；完成后才 `record_operation_result`。**外部副作用已成功、数据库收据尚未写时 crash，重放仍有可能再调用。** 默认 `retries_allowed=False` 仅关闭异常重试，不消除 crash/replay 窗口。 |
| Timeout / cancellation | [`dbos/_dbos.py#L1586-L1620`](https://github.com/dbos-inc/dbos-transact-py/blob/2cf279cf380152b426ecd451d573ccc41f5715a6/dbos/_dbos.py#L1586-L1620), [`_core.py#L2441-L2465`](https://github.com/dbos-inc/dbos-transact-py/blob/2cf279cf380152b426ecd451d573ccc41f5715a6/dbos/_core.py#L2441-L2465) | Step `timeout_seconds` 和 `preemptible` 只支持 async；同步 CLI 不是加装超时参数便可安全中断，`asyncio` 取消亦非 OS 子进程终止证明。没有 Nerelan 所需的输出/心跳 idle timeout 替代品。 |
| Queue fairness + collision | [`dbos/_queue.py#L72-L112`](https://github.com/dbos-inc/dbos-transact-py/blob/2cf279cf380152b426ecd451d573ccc41f5715a6/dbos/_queue.py#L72-L112), [`_queue.py#L645-L660`](https://github.com/dbos-inc/dbos-transact-py/blob/2cf279cf380152b426ecd451d573ccc41f5715a6/dbos/_queue.py#L645-L660) | `worker_concurrency`, `global_concurrency`, `partition_concurrency`, `partition_limiter` 能提供 admission 思路；**当前明确不允许 partition key 与 deduplication ID 同时传**，不能直接设计“按账户分区且 dedup ID 去重”。 |
| SQLite / migration | [`dbos/_sys_db_sqlite.py#L23-L53`](https://github.com/dbos-inc/dbos-transact-py/blob/2cf279cf380152b426ecd451d573ccc41f5715a6/dbos/_sys_db_sqlite.py#L23-L53), [`#L54-L128`](https://github.com/dbos-inc/dbos-transact-py/blob/2cf279cf380152b426ecd451d573ccc41f5715a6/dbos/_sys_db_sqlite.py#L54-L128), [`dbos/_dbos_config.py`](https://github.com/dbos-inc/dbos-transact-py/blob/2cf279cf380152b426ecd451d573ccc41f5715a6/dbos/_dbos_config.py) | 独立 SQLAlchemy engine，SQLite busy_timeout=30s 和 `BEGIN IMMEDIATE` 迁移锁；**不解决** Nerelan TaskStore 原先共享 sqlite 连接/锁问题。 |
| Dependency / licence | [`pyproject.toml`](https://github.com/dbos-inc/dbos-transact-py/blob/2cf279cf380152b426ecd451d573ccc41f5715a6/pyproject.toml), [`LICENSE`](https://github.com/dbos-inc/dbos-transact-py/blob/2cf279cf380152b426ecd451d573ccc41f5715a6/LICENSE) | MIT / Python >=3.10，SQLite 是默认 system-DB 路径候选；还依赖 SQLAlchemy、psycopg、croniter 等。Nerelan 当前 Python >=3.13；真正 Windows 3.13 兼容待验证，不能用 classifiers 代替实测。 |

## 2. 与 Nerelan main 的真实缺陷对照

| Nerelan 主体（已存在） | 分类 | 该抄什么 / 不该抄什么 |
|---|---|---|
| [`control_store.py#L1104-L1175`](https://github.com/dddd2024/Nerelan/blob/c96732520f3bd5329fc254bc95a91c05768d3ef8/reverse_agent/platform_v1/control_store.py#L1104-L1175) 的 `runnable_tasks` SQL (window/claim/quota/依赖)、[`#L1176-L1222`](https://github.com/dddd2024/Nerelan/blob/c96732520f3bd5329fc254bc95a91c05768d3ef8/reverse_agent/platform_v1/control_store.py#L1176-L1222) 的 `refresh_goal_status` repair-chain 推断 | **BORROW_PATTERN / REPLACE_CANDIDATE under #1546** | 尝试用一个 Goal = durable workflow 表达 `plan→implement→review→repair→review` 和显式 `WAIT_QUOTA/WAIT_OWNER/WAIT_APPROVAL`；旧 SQL 推断仅在试验成功后删除。不能同时维持两个权威状态机。 |
| [`unattended_coordinator.py#L226-L247`](https://github.com/dddd2024/Nerelan/blob/c96732520f3bd5329fc254bc95a91c05768d3ef8/reverse_agent/platform_v1/unattended_coordinator.py#L226-L247) 的 sweep、[`goal_service.py#L1262-L1283`](https://github.com/dddd2024/Nerelan/blob/c96732520f3bd5329fc254bc95a91c05768d3ef8/reverse_agent/platform_v1/goal_service.py#L1262-L1283) 的 repair/admission | **BORROW_PATTERN** | 状态转移由事件和持久工作流程序决定，不从 FAILED/ESCALATION 行反复猜；窗口/Goal 增量加入必须继续适配 Owner 持续运行语义（#1538），不能变回“窗口到期使任务丢失”。 |
| `TaskStore`、lease epoch、外部 RPC intent、workspace/PR/Review receipts、独立审查/受控 landing | **ALREADY_REUSED / KEEP** | DBOS 的 workflow id / owner_xid **不替代**外部操作幂等键、UNKNOWN/LOST、证据冻结、预算、Owner 权限、独立审查与 Magpie 用量账目。需要两库关联 `goal_id, workflow_id, task_id, attempt_id, effect_key, receipt_hash`，且接受跨库非原子状态。 |
| 账号限额路由、CLI 长时间执行、ExecutorRouter、Tool/Pack/MCP | **REJECT as replacement** | DBOS 不是 Agent Harness/模型选择器/插件沙箱/网关，也不提供 heartbeat 驱动的外部 CLI liveness；拒绝引入第二个 Agent runtime、Gateway、TaskStore、approval authority。 |

## 3. 最小可证伪实验（交由 #1546；本轮尚未运行）

1. **E1 Windows/Python3.13/SQLite provider-free**：独立 `dbos.sqlite` + 现有 `tasks.sqlite3`，在目标 Windows host 跑迁移、2 个并发 goal、100 次短步骤，统计数据库锁冲突和恢复时间；失败/锁或无法启动即 NO-GO。
2. **E2 crash gap matrix**：在 *外部执行前*、*CLI 已修改 workspace 但收据未写*、*收据已写但 DBOS step 未提交*、*review 返回但状态未提交* 4 点强杀重启；断言准确 DONE / UNKNOWN / PARKED，绝不二次执行非幂等动作，保留 ledger。
3. **E3 stale runner + failover**：旧 executor 仍活着但被误认为死亡；重复 `recover_workflows`，模拟 429、stall 和不同账户重派。旧 runner 必须被 Host lease+epoch fencing 挡住；恢复必须选可用账户而非同模型死循环，不能把恢复队列原子 claim 误当外部执行互斥。
4. **E4 partition + dedup collision**：同一账户两个 task 与两个账户同 task，并发 `queue_partition_key`、`deduplication_id` 组合确认显式拒绝；方案改为独立 task admission key + queue partition 和 host durable receipt，不能吞失败。
5. **E5 code/version update + run stop**：更换 workflow code 和 `app_version` 后重启，观察旧 PENDING 是否被自动捡起；Owner Stop、取消、shutdown/long CPU task 的外部进程是否真停/回收；如果有 stranded run 或幽灵副作用，NO-GO。
6. **E6 真实增益门槛**：按 #1546 要求统计实际可删旧代码 >~3000 行，端到端 goal 成功/独立验收率、崩溃恢复率、p95 时延、额外磁盘写入、全成本；若净代码下降不足或运行更不可靠，则 **NO-GO / 仅抄状态机与 queue-fencing 设计**。

## 4. 结论

**SELECTIVE_REUSE / CONDITIONAL DBOS SPIKE (P1; 不替代当前 P0 连续运行故障修复)**。
- 不建议现在替换宿主执行器或部署 DBOS 为生产引擎；建议 #1546 先做限域双库 provider-free spike。
- 采用动作需要 R2 依赖变更、冻结证据与 exact-head CI/独立复审；静态研究不构成实施批准。
- 本 Issue 的实际完成仅为固定源码审查与评估设计；**未安装 DBOS，未跑 Windows/SQLite/Crash 实测，未进行成本测量。** 研究报告 Draft PR 后续回链，并在 #1576 登记。


## 5. 开发与用户视角的优先级（供 #1546 试验设计使用）

- **用户痛点**：长任务进度突然消失、恢复后重复付费/重复修改、等待额度时无解释、回到应用看不出上次停止在哪里；价值不在工作流名字，而在可恢复且可审计的完成率。
- **开发最小切入**：先做可注入的 Goal transition port，旧 `TaskStore` 仍为唯一可读写产品真相；DBOS 实验代码只允许在独立 fixture + dbos.sqlite 中运行，必须通过双库 crash-gap 测试才能考虑迁移。
- **不变信任边界**：Owner 授权、Magpie 请求归因、租约 epoch、收据/证据冻结、独立验收、GitHub publication 不能从 DBOS 工作流状态推导为安全完成。将 workflow status 显示给用户时需要与 receipt 有双向可追踪的映射。
- **优先序**：P0 的 stall/配额/usage 事故修复优先；P1 DBOS spike；P2 状态 UI。开发收益必须按验收成功的目标/总花费衡量，不能只按删除行数。

> 验证状态：STATIC_SOURCE_REVIEW。本文所有 E1–E6 均属于**尚未执行的实验设计**，不是已通过的测试结果。文件为 R1 docs-only Draft PR 证据，不能作为 R2 上线授权。
