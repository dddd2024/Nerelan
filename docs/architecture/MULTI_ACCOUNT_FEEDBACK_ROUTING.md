# 有界反馈参与生产选路

## 实现变更摘要

本切片从 main `9ae26109` 分支，复用已经存在的账户 EWMA、AccountScoreboard.bonus
和唯一的 `model_router.select_model`。不增加调度器、运行时、队列、依赖或预算权威。
开发时平台端口未监听，沿用已记录的有界 supervisor fallback；未启动或升级宿主。

原来账户反馈只进入账本和独立 scheduler 组件，实际任务路由没有消费。现在可显式启用
有界评分调整：可靠性、完整的相对列表价成本、完整的尝试时延只调整现有 cost score，
每个候选的绝对调整量不超过配置上限。硬过滤、可用性/额度优先级、Owner pin、付费授权、
能力与独立审查规则仍由原路由器控制。

默认关闭。关闭开关恢复原来的路由评分，保留反馈和失败历史。策略参数、输入样本、
比较基准、调整前评分及调整量进入已有 MODEL_SELECTED 决策证据；无需新增审计数据库。

## 功能边界

Nerelan 核心目标与治理门禁不变。本切片是现有决策链的可选输入，不直接选择上游物理
账户、不修改 binding/connection、不发起探针、不执行任务，也不授予任何预算或发布权限。
`account_routing=magpie` 时不提供本地排名策略，避免两个账户路由权威并存。

跨账户比较按现有 availability rank、quota penalty、能力 tier 和 cost class 分组。
成本/时延项要求同组至少两个不同账户、全部账户满足样本门槛，且各自该维度样本数等于
尝试数。缺失、旧格式或 UNKNOWN 覆盖不被当成免费或低延迟；该组整体停用相应比较项。
可靠性可以使用本身足够且新鲜的成功/失败反馈。旧样本无覆盖计数，不补造成本覆盖。

所有调整仍是经验提示，不证明不同任务分布下的因果收益，也不提供实际现金节省保证。

## 关键模块

| 模块 | 职责 |
|---|---|
| `multi_account/config.py` | 配置启用、样本门槛及最大调整量，复用 Pydantic 与已有环境入口 |
| `multi_account/scoring.py` | 复用 EWMA，记录成本/时延有效样本数；先清除过期统计再学习新样本，避免旧历史复活 |
| `multi_account/feedback_policy.py` | 生成带哈希的参数/样本快照；校验输入；复用 bonus；计算并一次性应用有界调整 |
| `multi_account.dispatch.routing_feedback_snapshot` | 只读已有账本；禁用/委托/不可用时返回无建议 |
| `trusted_host` | 为候选附加已配置账户身份，向原任务路由器传入可信反馈快照 |
| `model_router` | 硬过滤之后消费可选调整，按原优先级、pin、重试与独立性规则完成选择 |
| GoalService / MODEL_SELECTED | 复用现有决策记录保存可复算的候选调整证据 |

## 可配置项

| 字段 | 环境变量 | 默认/范围 |
|---|---|---|
| 主开关 | `REVERSE_AGENT_MULTI_ACCOUNT_ENABLED` | 默认关闭；显式 1 |
| `enable_feedback_routing` | `REVERSE_AGENT_MULTI_ACCOUNT_ENABLE_FEEDBACK_ROUTING` | false，单独选择启用生产调整 |
| `feedback_routing_min_attempts` | `REVERSE_AGENT_MULTI_ACCOUNT_FEEDBACK_ROUTING_MIN_ATTEMPTS` | 3，不得低于 3 |
| `feedback_routing_max_adjustment` | `REVERSE_AGENT_MULTI_ACCOUNT_FEEDBACK_ROUTING_MAX_ADJUSTMENT` | 0.1，范围 0–0.25 |
| `enable_account_scoring` | 原字段对应环境入口 | true；关闭即停用该策略 |
| `reliability_weight` / `cost_weight` / `latency_weight` | 原字段对应环境入口 | 12 / 10 / 5，非负且有限；再受最大调整量限制 |
| `score_ewma_alpha` | 原字段对应环境入口 | 0.25，(0,1]；只控制反馈平滑，不修改授权 |
| 路由归属 | `REVERSE_AGENT_ACCOUNT_ROUTING` | local；委托 Magpie 时不提供本地反馈排名 |

账户接入、额度阈值、退避/降级、成本上限、运行时长、日志和告警继续使用前序交付明确的
配置与 Owner window；本轮不创建第二套配置权威或新的外部告警通道。
模式自进化与账户评分仍是两个开关，不能用模式开关推断账户评分已停用。
环境在实例创建时读取；配置回退由受控重建/现有配置入口负责，本轮不部署或重启进程。

策略哈希是审计索引，不是签名或授权。候选证据包含实际参数、样本和比较基准，
可复算该次调整；它不自动获得 CI/独立审查认可，也不会触发自动策略发布。

## 验收结果

当前相关套件 **282 passed、6338 deselected**：

```text
python -m pytest tests/platform_v1 -q -k 'multi_account or feedback_routing_policy or model_router or model_routing_constraints or account_quarantine'
git diff --check
```

| 验收点 | 证据 |
|---|---|
| 实际消费 | host 的 `_resolve_task_model` 经过既有模型池，读取反馈后改变同等候选的选择 |
| 成本与时延 | 完整覆盖的便宜/低时延候选被选择；任一未知成本使整组价格项保持 UNKNOWN |
| 状态与样本 | 门槛不足或超过 30 天未更新的反馈不参与；旧历史过期后首个新样本只计一次 |
| 限幅 | 极大权重也受 0–0.25 的最大调整量约束 |
| 原硬边界 | pin、可用性、确认额度耗尽及 paid-spend 禁止仍优先 |
| 审计 | 候选证据重算产生相同调整和最终 cost score；哈希不匹配时整体不用反馈 |
| 无损回退 | 关闭专用开关或主开关恢复原选择，账本文件字节不变 |
| 维护扩展 | 原有相关路由回归通过，无新增依赖/调度脊柱/任务表 |

完整 exact-head CI、独立审查和最终合入状态见本切片 PR，专项测试不是整体产品验收。

## 已知限制与扩展点

1. 未部署。实际账户切换、长期连续运行、完整成本归因及经济性对照仍未验收，目标保持 active。
2. 历史任务分布和账户承担的工作量可能不同，经验均值不证明可比质量或成本收益。
   后续仍需同目标、同验收标准的控制实验。
3. 准入账户身份不等于上游实际物理账户回执；上游路由/请求关联与覆盖仍需独立证据。
4. 生产链缺精确 attempt latency 时不会训练延迟项；此维度可由未来的真实计时输入补齐。
5. 旧覆盖计数缺失时成本/时延项会持续 UNKNOWN，不推断缺失样本。恢复完整统计需有证据的
   新统计窗口设计，不能删除历史账本来制造完整覆盖。
6. 该快照提供参数版本索引、单次候选调整回放及关闭策略回退；完整策略历史、灰度晋升、
   回滚目标选择和自动限幅更新还需要闭合。本切片不把“哈希存在”当作完整策略治理系统。
7. 仍是单宿主反馈文档，不支持多宿主共享 JSON 写入；沿用前序反馈修复的并发边界。
