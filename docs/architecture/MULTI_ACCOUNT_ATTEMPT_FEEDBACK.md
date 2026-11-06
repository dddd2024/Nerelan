# 多账户尝试反馈：归属、完整性和原子重放

## 实现变更摘要

本轮接续 #1384，从 main `9ae261092be77e72a18f47bb3deb1679d759e238` 开发。
开发时本机 8765/8766 仍无监听，因此使用 AGENTS.md 允许的有界 supervisor fallback，
只实现 R1 反馈修复；没有启动、升级宿主或执行真实 provider 调用。

已修复的生产反馈缺陷：

- 完成回调从对应 COMPLETE claim 与已结算 reservation 取得冻结账户，按 window/epoch
  限定用量。绑定后来被改成另一个账户，不会把旧尝试训练给新账户。
- 普通 API/OpenCode 路由在原 claim 事务内把非敏感反馈身份写入已有 `estimate_json`；
  不填写 subscription quota 的 `account_ref/quota_state`，不制造额度证据或修改硬准入。
- 一次尝试中任何未知模型、缺失 token 分项或非有限价格均使总列表价估算保持 UNKNOWN，
  不再把“能计价的部分”作为完整成本。现金未知而全部 token 已知时，可单独报告列表价估算。
  完整 token 先按模型汇总再调用原计价核心，避免逐条取整吞掉小额费用。
- 已完成 claim 的回执身份进入生产反馈 seam。评分、隔离和去重回执在同一个原子文档中提交，
  同进程同路径的多个实例先重读状态；失败写入不消费回执，也不先改变内存评分。
- 同回执相同反馈重放无副作用；冲突反馈拒绝且保留原证据。
- 账户评分拒绝非布尔结果，忽略负数、布尔和非有限成本/延迟测量；加载时拒绝异常评分条目。
- 任务创建到更新时间包括排队、等待及重试，不能当作响应延迟；报告标注这个口径，
  生产评分只接受明确的 `attempt_elapsed`，本轮没有凭空补一个延迟值。

## 功能边界

复用现有 TaskStore 用量表、ControlStore claim/reservation、原子反馈账本、CooldownRegistry、
AccountScoreboard 与离线 models.dev 列表价快照。不增加依赖、队列、计价模型或预算权威。
TaskStore 的预算结算、UNKNOWN hold、任务状态和授权不被此反馈写入改变。
上游运行时与账户切换继续由既有适配器负责，本轮不实现新的登录或凭据管理。

这使后续评分消费建立在可归属、可重放的反馈上；生产评分排序、策略版本晋升、完整
终态独立验收反馈和实际质量/成本收益仍待闭合，不以此组件修复宣称整体完成。

## 关键模块

| 模块 | 职责 |
|---|---|
| `usage_ledger.task_feedback_metrics` | 读取完成 claim 的精确尝试用量、冻结账户和回执身份；区分完整列表价估算与 UNKNOWN |
| `trusted_host._report_account_feedback_to_brain` | 消费冻结身份；跳过未完成/不可读的 claim；不把任务生命周期当响应延迟 |
| host quota preparer / coordinator / `ControlStore.claim_task` | 转交并在原准入事务中冻结 API 路由反馈元数据；验证绑定一致；不绕过预算或改订阅额度判定 |
| `multi_account.dispatch` | 传递可选回执身份，仍为 best-effort 可选 seam |
| `SelfEvolutionStore.record_account_feedback` | 同进程共享锁下重读、校验、检测重放，原子提交三项状态；写失败回滚内存候选 |
| `MultiAccountOrchestrator` | 原子提交成功后同步内存评分与冷却；持久化关闭时只保留内存状态 |
| `AccountScoreboard` | 复用原 EWMA 与权重；明确数值校验，避免非有限值污染排序 |

## 可配置项

沿用 #1384 的环境变量规则：`REVERSE_AGENT_MULTI_ACCOUNT_` 加字段名大写。
本轮没有更改既有默认值、扩大预算或创建新的授权窗口。

| 入口 | 默认及边界 |
|---|---|
| `REVERSE_AGENT_MULTI_ACCOUNT_ENABLED` | 默认关闭，`1` 启用已有反馈 seam |
| `persist_account_state` | true；false 时账户评分、隔离和回执均只在内存保留 |
| `enable_account_scoring` | true；false 时仍按既有规则记录隔离，不更新 EWMA |
| `max_recorded_runs` | 500；同时限定已处理账户回执保留数；窗口外重放不承诺幂等 |
| `score_ewma_alpha` / 权重 | 0.25 / reliability 12、cost 10、latency 5；本轮不自动修改权重 |
| `REVERSE_AGENT_MULTI_ACCOUNT_STORE` | 原本地 JSON 路径；仅允许一个宿主进程写入 |
| 账户接入、额度阈值、退避、降级 | 延续现有 binding/connection、健康观测和有界重路由配置 |
| 成本、时长、并发、重试上限 | 延续已批准 Owner window 与任务合同；没有采用 #1385 所列预算草案 |
| 日志、告警、自进化开关与限幅 | 延续现有事件/阻塞读模型及各自配置；本轮不自动发送外部通知或晋升策略 |

回退可关闭可选反馈 seam，保留账本和历史 TaskStore；不使用清空账本作为回滚方案。
缺少精确 attempt latency 时该维度保持 UNKNOWN，不用任务生命周期代填。

## 验收结果

专项命令：

```text
python -m pytest tests/platform_v1 -q -k 'multi_account or account_quarantine or usage_ledger or account_feedback_integrity'
git diff --check
```

当前专项 **188 passed、6441 deselected**，差异格式检查通过。
账户反馈及协调器/停机相关套件另有 **88 passed**，覆盖新增准入元数据转交。
完整平台 CI、独立审查和受控落地结果以本切片 PR 的 exact head 记录为准。

| 要求 | 本轮验证证据 | 整体状态 |
|---|---|---|
| 账户整合与归属 | 当前 binding 改变后仍训练冻结账户 | 精确 claim 反馈已覆盖；真实登录态切换仍待验收 |
| API 生产接线 | 实际 host preparer → coordinator → claim → completion → feedback 路径，执行中修改绑定仍回馈准入账户 | 隔离 fixture；不证明真实上游物理账户选择 |
| 状态与异常 | 未结算/异常结算不训练；非有限值不进评分；既有隔离回归通过 | 不替代真实故障链验证 |
| 重试与连续性 | 旧 epoch 不混入新尝试；重启重放不双计、不延长隔离 | 不证明进程崩溃后全部任务恢复 |
| 并发与持久化 | 四实例交错更新同账户 24 次全部保留；原子替换失败后可安全重试 | 限同一宿主进程 |
| 成本正确性 | 已知+未知模型/缺分项保持总价 UNKNOWN；零值与未知区分 | 列表价估算不等于现金账单或节省 |
| 反馈优化 | 生产终态身份接线，重复/冲突/无效反馈受控 | 评分排序与独立收益对照尚未实现 |
| 维护与扩展 | 复用现有表、评分、隔离及价格快照，没有新增依赖 | 结构化来源可继续接入真实 attempt 延迟 |

## 已知限制与扩展点

1. JSON 原子替换与共享锁不是跨进程事务。禁止多个宿主写同一文件；若有此需求，
   应复用既有 SQLite 事务存储。其他旧的整分区快照 API 不因本轮修复自动获得逐事件事务语义。
2. 回执保留有上限；超出留存窗口不承诺去重。冲突重放不会自动“补齐”价格或更换账户。
3. 没有协调器 claim 的手工任务仍只有 task 范围反馈，无法证明跨重试的精确身份；
   本轮不补造回执、不修改历史任务，也不重写此前错误训练的旧样本。
4. 成本完整性仅指该尝试已持久化 token 观测的完整可计价性，不证明上游无漏报或账单覆盖完整。
   真正的三成本口径、失败开销和价格快照时效仍须独立验收。
5. 账户回执和评分快照提供可复核状态，不是完整、不可篡改的策略审计日志。
   策略版本、灰度、限幅和无损回滚仍在完整目标范围内。
6. 本轮未部署、未真实试跑、未完成 24h/72h/7d 连续运行验收；目标保持 active。
7. 冻结身份是已配置的准入元数据，不是上游签发的路由回执；不能据此证明实际收费账户。
   旧 reservation 没有身份时不回填当前映射，保留 UNKNOWN 并跳过账户训练。
