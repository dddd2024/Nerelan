# Nerelan 八项基础能力基线（2026-11-13）

```text
STATUS: FOUNDATION_CAPABILITY_TAXONOMY
AUTHORITY: PLANNING_REFERENCE_ONLY
EXECUTION_AUTHORITY: NONE
OWNER: Existing canonical Issues (listed below)
SCOPE: Classification / deduplication / acceptance framing only
```

## 目的与边界

这份文档将曾被当作「新方向」讨论的八类能力统一归为 **Nerelan 的基础能力（foundation）**，不是新增八条研发主线，也不声明已经完成。它们应服务于长期的目标：在质量/风险约束下，让 Nerelan 尽可能经济、可靠地完成真实任务，并逐步扩展到非代码领域。资源与账户整合是支撑性基础设施，而不是唯一产品价值。

**本文件仅分类、索引和提出验收口径；不替代现行产品路线、Issue 权限、测试结果或运行宿主证据，不提供执行授权。** 状态需按实时代码、CI、宿主实测和独立验收更新。Issue 的 `open` 状态及规划文本都不能证明功能已经交付。

## 基础能力地图

| 基础能力 | 明确的用户价值 | GitHub 现有归属（不另起重复 Issue） | 最低有效验收（示例） |
|---|---|---|---|
| F1. 经验积累与有界自我改进 | 避免反复犯同一种错误；在可审计的边界内变好 | [#252](https://github.com/dddd2024/Nerelan/issues/252), [#379](https://github.com/dddd2024/Nerelan/issues/379) | 失败归因→证据筛选→经验准入→后续任务 A/B 受益→可撤销；不能凭自述宣称进化 |
| F2. 真实任务的模型/工作方式选择 | 按质量、成本、耗时、风险选择单模型、团队和执行器，而不只看模型标价 | [#1267](https://github.com/dddd2024/Nerelan/issues/1267), [#1264](https://github.com/dddd2024/Nerelan/issues/1264)；路由归既有主线 | 同起点真实任务对照；记录总 token/订阅额度变化、重试、独立接受率、时间；以每个**验收通过**结果的总成本作比较；未知用量必须保持 UNKNOWN |
| F3. 独立质量验证与证据 | 降低「Agent 宣称完成，但产物错误」的概率 | [#653](https://github.com/dddd2024/Nerelan/issues/653), [#811](https://github.com/dddd2024/Nerelan/issues/811), [#379](https://github.com/dddd2024/Nerelan/issues/379) | 对精确产物版本实施确定性检查+适当独立审查；测漏报/误报；验证者不得自授通过 |
| F4. 多天/跨重启长期运行与恢复 | 避免断电、额度耗尽、进程退出导致进度与外部副作用丢失 | [#1191](https://github.com/dddd2024/Nerelan/issues/1191), [#120](https://github.com/dddd2024/Nerelan/issues/120) | 真正中断→重建状态→核销外部作业/额度→一次恢复→不重复副作用；真宿主长跑，不以测试夹具代替 |
| F5. 多 Agent 协作、分歧与选择 | 必要时多个代理分工、相互质疑，找到更好的方法 | [#994](https://github.com/dddd2024/Nerelan/issues/994), [#1267](https://github.com/dddd2024/Nerelan/issues/1267) | 实际异构模型运行、独立分支并发有重叠证据；分歧由外部证据仲裁；与单 Agent 比较收益/额外开销 |
| F6. 长期记忆与项目知识 | 减少重复读取、上下文遗失、过时结论干扰 | [#103](https://github.com/dddd2024/Nerelan/issues/103), [#296](https://github.com/dddd2024/Nerelan/issues/296), [#379](https://github.com/dddd2024/Nerelan/issues/379) | 事实与推测可区分；每条经验有来源/时效/适用范围；变更后可失效；测量真实任务上下文节省与质量 |
| F7. 可重复的实验与基准评测 | 不靠感觉来证明哪种模型/Harness/策略更好 | [#1267](https://github.com/dddd2024/Nerelan/issues/1267), [#379](https://github.com/dddd2024/Nerelan/issues/379) | 冻结任务集与版本、控制环境、重复测量、保留失败样本、比较置信区间/不确定性、避免测试集泄漏 |
| F8. 可复用领域 Pack 与工作流 | 从代码拓展到科研、视频、数据分析等，无需复制一套内核 | [#253](https://github.com/dddd2024/Nerelan/issues/253), [#814](https://github.com/dddd2024/Nerelan/issues/814) | 单个 Pack 能声明工具、能力、环境、产物、权限与验收；能在既有执行层运行，不能靠直接改内核实现每个领域 |

## 分层理解：把基础能力组合成闭环

```text
用户 Goal / Intent（见 #515）
  → F2 选择执行方式；F8 提供专业能力与工具
  → F4 在授权内持久执行；F5 必要时协作或仲裁
  → F3 独立验证实际交付；F7 记录可比较证据
  → F6 保留有效知识；F1 有界地改善后续工作
```

核心不是在每次任务都启用全部八项，而是 **按任务成本/风险选择最小充分的流程**；小任务不应被分解/评审/调度开销吞没，大任务则需要可恢复和充分验收。

## 复用优先原则

- **不重复造执行器/多 Agent 框架**：沿用既有 OpenCode、Codex、Claude Code、LangGraph 集成；成熟库已有的功能先实测可行性再决定是否补薄适配层。
- **不重复造资源网关**：Magpie 等现成资源/用量能力是事实来源之一；Nerelan 只负责任务约束、预测、策略与证据链，且需识别 UNKNOWN。
- **不重复造持久化源**：TaskStore 是运行事实来源；GitHub 是分支、PR、CI 的事实来源。
- **不重复造第二套学习/验证模块**：F1、F3、F6、F7 复用 #252/#379 等现有归属，任务实验与产品运行共用证据身份。
- **不自授执行权**：实验、经验、Issue、本文档只产生建议和可审核证据；权限、预算、风险门禁由可信宿主和 Owner 规则控制。

## 实施与优先级（非新增排期）

1. **近期：证明能用**。按 [2026-11-10 项目审计](PROJECT_AUDIT_AND_ROADMAP_2026-11-10.md) 的阶段 0/1 先完成实际交互、可靠任务交付和故障修复，不以补全 F1–F8 为借口延误真实验收。
2. **随后：可评价**。先让 F3/F7 和 F2 拿到可靠的同起点、可重复的真实任务证据；[既有 #1267](https://github.com/dddd2024/Nerelan/issues/1267) 给出了单模型/团队成本盈亏点的实证路径。
3. **接着：能改进**。在 F6 的有来源、可失效经验基础上，逐步验证 F1 对后续任务的净收益；优先使用小规模、可回滚的策略更新。
4. **之后：可拓展**。只有长时执行 F4 及 F8 的产物/验收契约被实际证明后，才扩大跨领域无人值守范围。

## 新能力提案的去重准则

以后提议「新鲜能力」时，先问：

1. 它是否只是 F1–F8 的另一名称、细分任务或更好的实现？若是，直接补充原 Issue。
2. 它是否解决了此前没有被定义清楚的**新用户问题或结果类型**（而非「换一种模型/框架」）？
3. 与 [#515](https://github.com/dddd2024/Nerelan/issues/515)（意图编译）、[#795](https://github.com/dddd2024/Nerelan/issues/795)（中途指导）、[#814](https://github.com/dddd2024/Nerelan/issues/814)（交付产物）、[#252](https://github.com/dddd2024/Nerelan/issues/252)（自治改进）、[#260](https://github.com/dddd2024/Nerelan/issues/260)（产品层）等是否重合？
4. 是否有明确首个用户场景、最小可检验原型、对照方案、风险与止损指标？
5. 能否用既有 TaskStore、Magpie、GitHub、MCP、Pack、已有执行器完成，而不引入第二套控制面？

只有通过上述判断，才值得新增探索 Issue。未经独立验证的新方向不得写成已确认的竞争优势。

## 本次归档说明

- 本文是八项**基础能力分类与现有 Issue 对照**，不是进度完成报告。
- 未创建重复能力 Issue；未更改现行 Owner 授权、执行策略或测试门禁。
- 新的前沿候选能力先讨论与去重，再根据 Owner 选择正式立项。
