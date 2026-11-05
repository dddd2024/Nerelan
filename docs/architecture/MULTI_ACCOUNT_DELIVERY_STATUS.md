# 多账户优化：交付边界与验收状态

本文件校正同目录历史规划文档。第一阶段 PR #1378 的修正 head
`2520e3f755bf5e35749f251828c1871294992c72` 经独立 ACCEPT 与全部必需检查，已合入 main
`cd087399d89170a352b36247c0df80ae4354d5fe`。完整 Linux 平台基线为 6421 passed、33 skipped。
本轮后续仅补异常账户隔离的生产消费路径。**未部署、未启用，完整产品目标仍未验收。**
单测、CLI 帮助和进程级探针均不能替代真实生产验收。

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
| `REVERSE_AGENT_MULTI_ACCOUNT_ENABLED` | 关闭；可选反馈/建议不替代既有准入 |
| `REVERSE_AGENT_MULTI_ACCOUNT_STORE` | `.platform_v1_runtime/multi_account_break_even.json`；进程级状态，不允许多个宿主共享写入 |
| `REVERSE_AGENT_ACCOUNT_ROUTING` | `local`；支持 `local/magpie/auto`，不配置上游路由 |
| `REVERSE_AGENT_MAGPIE_ACCOUNT_SWITCHING` | 关闭；`auto` 同时要求它和 Magpie 启用标志为 1 |
| `REVERSE_AGENT_MAGPIE_EXE` | 无；只读 CLI 显式路径，CI 零真实 provider 调用 |
| `REVERSE_AGENT_MAGPIE_WAIT_TARGET` | 无；可取消等待仍需真实停机验证 |
| 观测新鲜度 / 快照上限 | 600 / 900 秒 |
| 重路由次数 / 退避 | 3 次；30 秒起、2 倍、900 秒封顶，仅为 fallback 能力 |
| 异常隔离 / 历史窗口 | 300 / 21600 秒；迟到成功不能解除活跃隔离 |
| EWMA alpha / 保留运行数 | 0.25 / 500；生产评分选路待接线 |

回退采用关闭开关并保留状态证据；不删除历史数据或清除 UNKNOWN。
JSON 原子替换只防半文件，不提供跨进程事务或审计日志保证。

## 验收与推进顺序

| 阶段 | 验收标准 | 现状 |
|---|---|---|
| P0 基线复用 | main/候选分开、模块责任唯一、独立 review | 第一阶段修正后独立 ACCEPT、必需 CI 通过并合入；后续切片单独过门禁 |
| P1 统一账户 | 同 provider 多账户、跨 provider、订阅+API 混合可归因；歧义不猜 | 身份与异常隔离已接线；真实调度与生产评分排序待验收 |
| P2 稳定运行 | 耗尽/异常/断网/上游不可用/重启注入；无丢任务、不受控重放 | 部分组件回归；恢复与副作用链待验收 |
| P3 成本质量 | 全部尝试及规划/验证开销完整归因；三成本基准分列；同任务同验收标准对照 | 缺导出完整性证据；任务就绪状态不等于独立验收，不能据此宣称省钱 |
| P4 自进化 | 规模与终态反馈生产闭环；策略版本、回放、灰度、回滚；独立评估质量不降 | 算法组件存在，生产闭环和策略晋升待实现 |
| P5 长跑 | 24h→72h→7d；24h 至少 3 次休眠唤醒、2 次强杀，守住任务与租约证据 | 未运行；组件 kill9 探针不替代真实恢复验收 |
| 合入 | exact-head CI、独立 ACCEPT、Ready 后 landing-state-gate、合入前 verdict、matched-head merge | #1378 已完成；每个后续切片重新检查，不豁免门禁 |

优先闭合 P1/P2 生产消费路径并采集 P3 证据，再优化策略。P5 以实际经过时间和持久运行
证据验收。真实账户故障注入、宿主休眠与部署须有对应环境的明确操作授权。
