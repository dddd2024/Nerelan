# 深度开源复用研究索引（Nerelan）

> 目的：**每次先查重，再逐一深入研究，最后在 GitHub 留痕**。本索引记录文档研究进度，不表示代码已复用、Benchmark 已通过或 Owner 已授权实施。
>
> 更新于 2026-11-16。执行前仍需搜索当前 GitHub Issues/PR/最近提交与聊天中已有的研究；本索引只是入口，不是替代实时检索的数据库。

## 正式研究记录

| 项目 / 范围 | 时间 | 深度 | GitHub 研究材料 | 关键判断 | 运行验证 |
|---|---|---|---|---|---|
| 约 30 个成熟组件，五个领域（账户、持久执行、Agent Runtime、编排、成本） | 2026-11-15 | 横向 + 部分源码级 | [reuse-study-2026-11-15](reuse-study-2026-11-15/README.md) | 先复用 Magpie/现有执行器，避免第二套状态与用量账本 | 见各分报告 |
| Paperclip（Adapter / Heartbeat / Workspace / Accounting / Plugin） | 2026-11-16 | 专项源码级 | [Paperclip 报告](reuse-study-2026-11-16/paperclip.md) · [#1562](https://github.com/dddd2024/Nerelan/issues/1562) | 只借鉴薄契约、工作区回传收据、队列公平性和证据处理，不引入第二套平台 | 未运行 |

## 已知先前研究 / 待核对与补录

此前在聊天中讨论或深入研究过以下项目/组件，但**本索引尚未逐项核验每一轮研究是否已由其他 Agent 正式落档**。下次选择它们之前，必须先检查聊天记录、GitHub 最近的 Issues/PR、文件搜索及源项目新版本，不能因本表缺少项目专属报告就当作全新研究：

- Cline / Roo、Continue、OpenHands、Goose、Aider、mini-SWE-agent、Orchestrator.inc
- Letta Code、Pi/pi-mono、OpenClaw、Plandex
- Deep Agents、Pydantic AI、FastMCP
- OpenCode、Codex、Gemini CLI、Hermes Agent、Qwen Code

这些名字表示**曾研究或被覆盖**，不表示它们都完成了同等深度的源码审计；待核验后应逐项补入正式表，并标出已知模块与未完成模块。

相关已有索引：[竞品与复用地图](COMPETITIVE_LANDSCAPE.md)、[11 月 15 日复用研究](reuse-study-2026-11-15/README.md)、[产品差异化研究 #1561](https://github.com/dddd2024/Nerelan/issues/1561)。

## 每次研究的固定查重和留痕要求

1. **查重**：查看本索引、已有专项报告、竞品地图、仓库文件搜索、**最近** Issues/PR/评论/提交，以及聊天层面的既有研究；区分“仅横向触及”与“某个源码模块已深入验证”。
2. **增量范围**：写清本轮**新研究哪几个模块**、此前已经研究过什么；若没有可证实增量，则换项目。
3. **源码版本**：引用 upstream 仓库、具体 Commit/Tag、文件/函数与许可证；不把 README 描述当成实测事实。
4. **Nerelan 对照**：检查现有 main 的真实代码与现有 Issue；明确“可直接用现成组件 / 借鉴设计 / 已经有 / 不该抄”。
5. **可证伪性**：输出优先级、最小实验、验收阈值、失败条件和未知之处；不把预测收益写成已验证收益。
6. **GitHub 写入**：创建或更新一个明确的 Research 记录，提交独立研究文档的 **Draft PR**，并更新本索引；**不直接提交 main**。创建 Issue 时检索同项目同模块，避免重复研究 Issue 和开发 Issue。
7. **治理**：研究记录不构成代码执行授权；R1/R2/R3、独立评审、CI 和受控合并遵守 [AGENTS.md](../../AGENTS.md)。没有验证的结果必须标注 *STATIC_SOURCE_REVIEW*。

## 当前状态

Paperclip 的报告目前由 [#1562](https://github.com/dddd2024/Nerelan/issues/1562) 跟踪；本索引与报告在研究 Draft PR 内等待审查。**不能在 PR 合并前把文件视为 main 已正式收录。**
