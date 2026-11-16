# Nerelan 历史跨对话开源研究归档：检索目录和证据等级（2026-11-16）

> **唯一总入口：** [#1576 — 研究总 Issue](https://github.com/dddd2024/Nerelan/issues/1576)。本目录不创建第二份实施 Roadmap 或研究主 Issue。  
> **目的：** 将 **2026-11-16 其他 Nerelan 对话**中已做过的源码/机制深拆转化为 **可在 GitHub 浏览、逐项目查重、能回看具体上游源码** 的材料。此前总表仅记录名称和摘要，未达到这个目标。  
> **当前证据状态：** `HISTORICAL_CHAT_STUDY + SOURCE_SPOTCHECKED / NOT_RUNTIME_TESTED`。每页明确原始历史对话能证实什么、本次上游固定源码究竟核了哪些文件、哪些无法从历史补回。**不把归档时重新核过的代码版本说成旧会话使用的版本**。  
> **本轮事实：** 旧研究不代表已运行原项目、不代表性能实证、不代表过去已经在 GitHub 独立落库；归档 PR 合并前，本目录仅在 PR 分支。本文没有部署任何 Agent/插件/沙箱或使用凭据。

## 1. 本轮完成“逐项整理”的六个历史重点项目

| 项目 | GitHub 历史档案 | 原研究的关键机制 | 上游源码版本状态 | 取舍 |
|---|---|---|---|---|
| **Cline（附 Roo 比较）** | [cline-roo.md](cline-roo.md) | AgentPlugin、Hooks、Runtime Tool/Plugin、事件与中断；Roo 独立路径未恢复 | Cline：归档新核 `0eeb3231`；旧 SHA 未恢复；Roo 单独源码未校验 | Tool/Hook 生命周期与诊断可借鉴；不能替换 Host 授权 |
| **Pi / pi-mono** | [pi.md](pi.md) | Agent Loop、JSONL RPC、`agent_end` vs `agent_settled`、`steer/follow_up`、Session Tree/Extensions | **旧提交已核验** `22fc026b` | 优先候选多 Harness Executor；不可复制第二 Coordinator |
| **Letta Code** | [letta-code.md](letta-code.md) | Git MemFS、Memory Operation Lock、独立 Reflection Worktree、Memory Handoff/Skills | **旧提交已核验** `eadef1c` | 借鉴版本化记忆/受控反思；记忆不是权威或永久事实 |
| **Plandex** | [plandex.md](plandex.md) | Plan Versions、Pending Changes、Apply/Rewind、Tree-sitter File Map | 旧 SHA 遗失；**归档新核** `e2d77207` | 借鉴可审阅修改集和上下文地图；不复制完整计划引擎 |
| **OpenClaw** | [openclaw.md](openclaw.md) | Harness `supports(ctx)`、Session Compatibility、Manifest-first Activation/Generation | **旧提交已核验** `02dc185` | 借鉴能力协商与延迟插件激活；不接入其第二 Gateway |
| **Hermes Agent** | [hermes-agent.md](hermes-agent.md) | Kanban/DAG、Swarm Worker's handoff、Skill Readiness/Permissions | **旧提交已核验** `e96221fa`；旧对话自称“GitHub 已留痕”尚未找到实际旧专项 PR | 借鉴阻塞/派发可解释性、Artifact Handoff；不要第二 TaskStore |

### 这六项来源如何核查

- **来自旧对话的结论**：原聊天在 2026-11-16 多次按“一个项目一次、结合 Nerelan”的要求研究过上列范围。可恢复的是历史答案的标题、日期、技术要点和部分 SHA，**不是逐字完整对话**；没有可核验的 ChatGPT 对话永久链接。
- **本轮补核**：使用 GitHub 原仓库在固定 SHA 下查看真实文件。例如 Pi 的 [RPC 状态语义](https://github.com/earendil-works/pi/blob/22fc026b/packages/coding-agent/docs/rpc.md)、Letta 的 [Memory Operation](https://github.com/letta-ai/letta-code/blob/eadef1c/src/agent/memory-operation.ts)、Plandex 的 [Rewind](https://github.com/plandex-ai/plandex/blob/e2d772072efadbe41d2946d97d79be55532dbab5/app/cli/lib/rewind.go)、OpenClaw 的 [Activation Planner](https://github.com/openclaw/openclaw/blob/02dc185/src/plugins/activation-planner.ts)、Hermes 的 [Kanban Swarm](https://github.com/NousResearch/hermes-agent/blob/e96221fa/hermes_cli/kanban_swarm.py)、Cline 的 [Plugin Config Loader](https://github.com/cline/cline/blob/0eeb32315ee28e5cd80c879ba16bc96eecf17dfe/sdk/packages/core/src/extensions/plugin/plugin-config-loader.ts)。每篇正文还列其他已核验源码和反例。
- **没有补得的证据**：旧回合的每次工具操作/完整源码 Diff、缺失的上游旧 SHA（Cline、Plandex、Roo）、旧对话精确 URL、曾口头称已保存的独立 GitHub Issue/PR（尤其 Hermes）。**这几项保持 `PROVENANCE_GAP`，不能倒填或编造**。

## 2. 其它历史专项与候选的集中归档（13 个项目）

完整矩阵和模块级决策：[other-runtime-frameworks.md](other-runtime-frameworks.md)。

| 类别 | 项目 | 历史源码/记录 | 复用结论缩写 |
|---|---|---|---|
| Coding Harness | OpenCode | `367d24b7` | 原生事件、V1/V2 Protocol；不复制 Agent Loop |
| Coding Harness | Codex CLI / App Server | `630c0d75` | Python SDK/ExternalMessage，审批和环境继承需严格验证 |
| Coding Agent SDK | OpenHands Software Agent SDK | `1d4c0249` | RemoteConversation/Agent Server，容器隔离权限需验证 |
| Coding Harness | Gemini CLI | `4ed06ed0` | Headless/ACP、Checkpoint，禁用未授权自动批准与环境加载 |
| Coding Harness | Goose（已迁移 `aaif-goose/goose`） | `bf6e1df` / `0bf8b624` | MCP Extension Lease、Recipe→Pack |
| Context/Coding Agent | Continue | `5522c6f` | Context Providers、Repo Map/Index，保留 Task Owner |
| Context/Coding Agent | Aider | `5dc9490` | Repo Map/PageRank、Architect/Editor，避免自动提交 |
| Baseline Agent | mini-SWE-agent | `04d809c` | 极简 Bash Harness 比较基线，非 Sandbox |
| Coding Harness | Qwen Code | `2366c440` | Python SDK/ACP、Teams/Goals、Tool 权限和 env 反例 |
| Agent Framework | Deep Agents | `eab9304` | Middleware、Skills、Backend、Rubric，不换主图 |
| Agent Framework | Pydantic AI | `bc598a1` | Evals、WindowsWorkspace、DBOS 候选，工作区非沙箱 |
| MCP Framework | FastMCP | `ffc65c7` | ClientGroup/Tool Search/OAuth，优先复用 SDK |
| Multi-Agent Workspace | Orchestrator.inc | `ad93b42` | Harness Adapter / Event / PR Head 收据，非插件商店 |

以上短 SHA 和真正上游 README 已分别由 GitHub 定位核对，多个模块的具体源码路径也在详细文档中；**“源码引用验证”不等于运行性能/成本验证**。

## 3. 与现存正式资料及重复研究的关系

| 材料 | 状态 | 不可混淆 |
|---|---|---|
| [11/15 五领域横向研究](../../reuse-study-2026-11-15/README.md) | **main 已有** | 横向覆盖约 30 个开源/成熟组件，不等于各项目独立深拆 |
| [11/16 六份正式专项](../RESEARCH_SUMMARY.md) | 六份研究 Issue+报告+Draft PR；**未合并** | Paperclip、Mastra、Composio、K8s Agent Sandbox、Dify Plugin Daemon、Bifrost |
| **本历史目录** | 历史内容已恢复、部分固定源码补核；归档 Draft PR **未合并** | 六份独立历史重点项目 + 其它十三项，不得算作新增已测试的正式专项 |
| [研究 Hub #1576](https://github.com/dddd2024/Nerelan/issues/1576) | GitHub Issue 已存在、与本次归档相互链接 | 唯一研究导航入口，汇总所有来源 |

## 4. 历史来源核验与未来查重规则

1. 新一轮首先在 [#1576](https://github.com/dddd2024/Nerelan/issues/1576) 和本历史目录查重，再看 11/15 横向报告与六份正式研究及**尚未合并的 PR**。**当前没独立 Issue ≠ 没被研究**。
2. 若已研究同一项目同一机制，优先给原历史文档增加源码新版本、真实实验或新的反例；无需再写一份重复的初步介绍。
3. 使用代码级机制前补齐：真实固定 SHA、实际源文件与测试、适配当前 Nerelan main 的技术差异、是否经独立 review、成本/权限/恢复表现。历史 Chat 片段本身只支持 **research provenance**，不支持功能已存在或可投入生产的结论。
4. 未查实的旧 GitHub 留痕口头声明不得变成正式 GitHub 参考 ID；本归档自身在当前研究 PR 中形成**可核查的新证据**。
5. 避免新建重复 Implementation Issue：继续复用 #1527 Harness、#296 Context、#253 Pack、#790 MCP、#299 Sandbox、#1267 经济性、#1546 Durable Workflows、#1508 Goal DAG。
6. **记录状态语义：** `HISTORICAL_CHAT_STUDY` = 有旧对话具体讨论；`SOURCE_REF_VALIDATED` = 固定 SHA 下文件存在；`SOURCE_SPOTCHECKED` = 读过指定真实文件并核对机制；`ARCHIVE_TIME_SOURCE_SPOTCHECK` = 原研究 SHA 丢失，使用本次新固定点补证；`PROVENANCE_GAP` = 不能核实旧对话/Issue/PR/源码或测试；`NOT_RUNTIME_TESTED` = 没有实际安装/运行/成本评估。

**结论：** 在所有可恢复的历史对话范围内，项目名称、已知版本、关键模块、借鉴/拒绝和当前可核源码已经归档，并清楚保留不能恢复的原始证据缺口。**归档完整不等于旧聊天全部原文被重现，更不等于实证通过。**
