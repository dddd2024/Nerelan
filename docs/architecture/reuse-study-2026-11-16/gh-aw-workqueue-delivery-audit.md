# gh-aw：可信交付、工作队列与插件权限的源码深审

**Research Issue:** [#1614](https://github.com/dddd2024/Nerelan/issues/1614) · **Canonical research hub:** [#1576](https://github.com/dddd2024/Nerelan/issues/1576)

**2026-11-16 · Static pinned-source study · NO_INSTALL / NO_MODEL_CALL / NO_RUNTIME_TEST / NOT_IMPLEMENTED / DOCS_ONLY / NO_IMPLEMENTATION_AUTHORITY**

> **2026-11-16 · RESEARCH_ONLY / STATIC_SOURCE_REVIEW / DOCS_ONLY / NO_RUNTIME_TEST / NOT_IMPLEMENTED / NO_IMPLEMENTATION_AUTHORITY**
> 
> 唯一上游：[github/gh-aw@5f2275ce3cc45fca96336962a7e02eb1fd52b8f7](https://github.com/github/gh-aw/commit/5f2275ce3cc45fca96336962a7e02eb1fd52b8f7)（根 [LICENSE](https://github.com/github/gh-aw/blob/5f2275ce3cc45fca96336962a7e02eb1fd52b8f7/LICENSE) MIT）。Nerelan 对照：[main@0a9997046386bac5ca291410ce428c160f3ea763](https://github.com/dddd2024/Nerelan/commit/0a9997046386bac5ca291410ce428c160f3ea763)。
> 
> **审查性质**：固定 SHA 源码与上游测试的静态检查；没有运行 gh-aw、GitHub Actions、Go tests、Nerelan tests、模型、插件或真实凭据。源码内测试文件只能证明测试存在与其设计意图，不能证明本宿主已通过。

## 0. Duplication gate

先读 [#1576](https://github.com/dddd2024/Nerelan/issues/1576) 单一研究入口、已覆盖的 11/15 五领域报告、历史 Draft [#1577](https://github.com/dddd2024/Nerelan/pull/1577) 归档、最近的 [#1612 Graphiti](https://github.com/dddd2024/Nerelan/issues/1612)、[#1609 OpenAI Agents SDK](https://github.com/dddd2024/Nerelan/issues/1609)、A2A/AG-UI/ToolHive/Promptfoo/Google ADK、GitHub Issue/PR 全文搜索 `github/gh-aw` / `GitHub Agentic Workflows`。在既有 #135/#252/#299/#595/#612/#361 找到**零散指称**，并未找到独立固定源码专项，GitHub PR 查询未见已有 gh-aw 专项。与 DBOS、Paperclip 的调度主题有重叠，但本次的**增量技术问题**是 *GitHub workqueue ledger + native output independent readback + effect scope + phase-gated connector*；不是第二次泛泛介绍 Agent 或重复建生产实施 Issue。

## 1. 与 Nerelan 当前事实的对照（明确“已有”与“待验证”）

- [AGENTS.md](https://github.com/dddd2024/Nerelan/blob/0a9997046386bac5ca291410ce428c160f3ea763/AGENTS.md) 已有独立 Reviewer、exact-head CI（baseline/state-gate/landing-state-gate）、禁止 Ruleset bypass 和 R2/R3 Owner 授权。gh-aw 的“安全发布”不能降低这些现有规则。
- [`reverse_agent/platform_v1/goal_service.py` L175–300](https://github.com/dddd2024/Nerelan/blob/0a9997046386bac5ca291410ce428c160f3ea763/reverse_agent/platform_v1/goal_service.py#L175-L300) 已将外部操作 `SUCCESS/RECONCILED` 与 `PENDING/UNKNOWN` 区分；租约、未知外部副作用阻止第二次派发。应对照其副作用收据生命周期，而不是宣称 Nerelan 没有 receipts。
- [`task_execution.py` L330–450](https://github.com/dddd2024/Nerelan/blob/0a9997046386bac5ca291410ce428c160f3ea763/reverse_agent/platform_v1/task_execution.py#L330-L450) 已有 fencing、Checkpoint、受信宿主 validation；[`policy_adapter.py`](https://github.com/dddd2024/Nerelan/blob/0a9997046386bac5ca291410ce428c160f3ea763/reverse_agent/platform_v1/policy_adapter.py) 已有 fail-closed 风险与路径范围限制。
- 原有实施归属：[持续运行 #1538](https://github.com/dddd2024/Nerelan/issues/1538)、[恢复引擎 spike #1546](https://github.com/dddd2024/Nerelan/issues/1546)、[长期自我改进 #252](https://github.com/dddd2024/Nerelan/issues/252)、[插件/连接器 #790](https://github.com/dddd2024/Nerelan/issues/790)、[#253 Pack](https://github.com/dddd2024/Nerelan/issues/253)、[#447 Egress](https://github.com/dddd2024/Nerelan/issues/447)、[#179 Security](https://github.com/dddd2024/Nerelan/issues/179)、[#1267 Outcome Economics](https://github.com/dddd2024/Nerelan/issues/1267)、[#1575 Refactor](https://github.com/dddd2024/Nerelan/issues/1575)。

## 2. 模块逐段深拆：抄机制，不复制平台

| 模块 | 冻结上游源码/静态证据 | Nerelan 复用点 | 决策 |
|---|---|---|---|
| **Work Queue** | [`pkg/workqueue/README.md` L5–105](https://github.com/github/gh-aw/blob/5f2275ce3cc45fca96336962a7e02eb1fd52b8f7/pkg/workqueue/README.md#L5-L105)：独立 `work-queue` Git 分支上 `work-queue.jsonl` 是 gh-aw 的原生权威账本；`Projection` 是经验证重放的衍生状态；`PlanNext` 只选计划不修改 Projection | **不**移植 Git queue ledger，不复制第二套 Goal/TaskStore/Coordinator 或把 GitHub 变成 Nerelan 运行状态真相；借鉴“只读计划与提交操作分离”及可解释原因 | **ALREADY_REUSED + BORROW_PATTERN P1** |
| **不可变请求与检查点** | [`pkg/workqueue/replay.go` L43–145](https://github.com/github/gh-aw/blob/5f2275ce3cc45fca96336962a7e02eb1fd52b8f7/pkg/workqueue/replay.go#L43-L145)、[`checkpoint.go` L298–417](https://github.com/github/gh-aw/blob/5f2275ce3cc45fca96336962a7e02eb1fd52b8f7/pkg/workqueue/checkpoint.go#L298-L417)：验证请求 ID/actor/policy epoch、历史 checkpoint Git parent hash、commit projection；[`branch_checkpoint_test.go` L141–240](https://github.com/github/gh-aw/blob/5f2275ce3cc45fca96336962a7e02eb1fd52b8f7/pkg/workqueue/branch_checkpoint_test.go#L141-L240) 有损坏历史与重复出版反例 | 复用为 TaskStore 的 **provider-free fixtures**：旧 attempt、旧 policy digest、重放相同 Operation、主分支变更时只允许有证据的状态推进 | **BORROW_PATTERN P1; REJECT second ledger** |
| **效果授权及 Claim 生命周期** | [`resource_scope.go` L19–168,280–350](https://github.com/github/gh-aw/blob/5f2275ce3cc45fca96336962a7e02eb1fd52b8f7/pkg/workqueue/resource_scope.go#L280-L350) 校验资源身份、Subject/immutable Work scope、冻结 Worker Profile；[`effect_scope_test.go` L65–169](https://github.com/github/gh-aw/blob/5f2275ce3cc45fca96336962a7e02eb1fd52b8f7/pkg/workqueue/effect_scope_test.go#L65-L169) 测试同批兄弟 Claim 权限、Result 后拒绝新操作但保持旧请求只读确认 | Nerelan 的 Goal/Attempt/Owner grant 本已存在，候选补齐 **`effect_authorization` 的原始任务、仓库、资源、epoch、工具操作身份绑定**；完成后的“新的写动作”必须禁止，“确认旧结果”仍可 readback | **BORROW_PATTERN P0 test** |
| **安全输出与独立读回** | [`delivery_host.go` L14–55,130–169,319–375](https://github.com/github/gh-aw/blob/5f2275ce3cc45fca96336962a7e02eb1fd52b8f7/pkg/workqueue/delivery_host.go#L319-L375)：`NativeDeliveryInventory` 必须来自可信进程 callback（不是 stdout/file/artifact）；`NativeOutputVerifier` 由宿主事先注册；目标再经 `AuthorizeEffect`，独立 readback 后才能生成 `DeliveryVerification`；[`evidence.go` L264–305](https://github.com/github/gh-aw/blob/5f2275ce3cc45fca96336962a7e02eb1fd52b8f7/pkg/workqueue/evidence.go#L264-L305) 校验实际原始 Actions Run/Principal/HeadSHA | **P0** 为 GitHub Draft PR、标签、Issue 更新等外部动作加入“模型声称完成 ≠ 可信读回完成”反例，严格保持 Nerelan 原有 R2/R3 Gate；不让代理输出创建新的 verifier | **BORROW_PATTERN P0** |
| **交付证据分离** | [`delivery_evidence.go` L10–130](https://github.com/github/gh-aw/blob/5f2275ce3cc45fca96336962a7e02eb1fd52b8f7/pkg/workqueue/delivery_evidence.go#L10-L130) 对 evidence 限长/校验、限定 completed claim、单次 immutable evidence；[`delivery_evidence_test.go` L74–164](https://github.com/github/gh-aw/blob/5f2275ce3cc45fca96336962a7e02eb1fd52b8f7/pkg/workqueue/delivery_evidence_test.go#L74-L164) 明确 evidence 自身不能宣布 delivery verified | 保留 external operation `PENDING/UNKNOWN/RECONCILED/SUCCESS` 的强区分；只能由 host readback 把 UNKNOWN 提升，不能仅凭 agent JSON/截图/文本 | **BORROW_PATTERN P0** |
| **GitHub Workflow 安全输出工厂** | [`compiler_safe_output_jobs.go` L13–114](https://github.com/github/gh-aw/blob/5f2275ce3cc45fca96336962a7e02eb1fd52b8f7/pkg/workflow/compiler_safe_output_jobs.go#L13-L114) 分开 Agent、可选检测 Job、safe outputs Job 和 conclusion / fan-out；威胁检测可显式禁用；[`action_pins.go` L17–50](https://github.com/github/gh-aw/blob/5f2275ce3cc45fca96336962a7e02eb1fd52b8f7/pkg/workflow/action_pins.go#L17-L50) pin Actions SHA | 可借鉴 **proposal→validation/threat check→trusted publisher→readback** 拆分、固定依赖版本；仅 docs 研究，不自动修改 Nerelan `.github/workflows`（R2 Governance 边界） | **BORROW_PATTERN P1** |
| **Connector / Plugin Runtime** | [`pkg/connectors/runtime.go` L18–181](https://github.com/github/gh-aw/blob/5f2275ce3cc45fca96336962a7e02eb1fd52b8f7/pkg/connectors/runtime.go#L18-L181)：`SecretResolver(ctx,phase,name)` 宿主授信，`AllowedOrigins` 单独提供、仅 https、禁止 redirects、按 `mcp/context/safe-output` 能力与写入开关区分、未知传输故障不默认重放 | 适用于 #790 Connector Runtime：每个请求由 Host 门禁确定 phase/allowed origin/secret reference/写权限，Magpie 仍负责模型账号，不建第二账户池 | **BORROW_PATTERN P1** |
| **Firewall/Intent Policy** | [`pkg/workflow/firewall.go` L24–60](https://github.com/github/gh-aw/blob/5f2275ce3cc45fca96336962a7e02eb1fd52b8f7/pkg/workflow/firewall.go#L24-L60) 若沙箱被显式关掉，Firewall 可停；[`pkg/intent/policy.go` L32–38,90–107](https://github.com/github/gh-aw/blob/5f2275ce3cc45fca96336962a7e02eb1fd52b8f7/pkg/intent/policy.go#L32-L38) **明确标注 Intent Policy 的绝大部分字段仅用于审计，尚未接入运行时强制 enforcement** | UI/配置中的“policy configured”≠安全已生效；宿主执行前二次验证，缺强隔离不能降级成“成功”。不能假设 gh-aw 全部策略已强制执行 | **REJECT defaults as authority** |

## 3. 具体产品差异与收益判断

**现实用户体验**：连续运行几小时后，用户不应见到“Agent 已说合并/评论/创建完”但实际 GitHub 没动作，或反之因超时又重复写一遍。应该展示 3 个可解释状态：`PROPOSED`（代理提议）、`EXTERNAL_UNKNOWN`（可能执行，等读回）、`VERIFIED`（host 独立读回 + 当前权限/版本匹配）。原任务和 Reviewer 的结果另行处理，不能混同。

**边界线**：gh-aw 基于 GitHub Actions 的独立 queue ledger 是它自己的主状态系统；Nerelan 当前 local-first、Windows、TaskStore、Magpie、多 Harness、exact-head CI/独立 Review 均不可被替换。尤其当前 #1538 指定“不以总窗口 token/task/time cap 作为停止条件”，gh-aw 的队列层 retry/资源限制不得未经 Owner 决策直接反向覆盖。无需新建 dev Issue；复用 existing #1546/#1538/#790/#179/#252。

## 4. 最小证伪测试（提议，未执行）

1. **假收据**：Worker stdout 写 `success`、artifact 内自带 receipt，GitHub 对应 PR/Issue 其实不存在；Host 必须保持 `UNKNOWN`，拒绝进到 Result/Accepted。
2. **迟到副作用**：API 请求超时后第二 Worker 被调度，旧 Worker 实际已经创建 GitHub Issue；恢复应先读回同一外部对象，**不自动再次创建**。
3. **权限过期**：授权相同工具名但不同目标 Repo、PR、Run、Grant generation；旧授权不能用于新的资源写操作。
4. **兄弟 Claim**：同批两个 Worker，A 验证完成后 A 的新写入应被拒，B 在有效 Grant 下继续；A 先前请求的只读收据查询仍允许。
5. **队列/Checkpoint Replay**：模拟乱序操作、过期 epoch、重复 requestId、历史 SHA 不匹配、截断 checkpoint，必须 fail-closed；结果只能由当前可靠 TaskStore/Host readback 决定，不转成 Git branch ledger。
6. **插件 phase 边界**：MCP/read-only phase 试图用 safe-output 凭据、HTTPS 跳转至非允许 host、注入新的 origin、丢失 AllowWrites；全部应在宿主拒绝且无模型/外网调用。
7. **安全输出编译器“关闭检测”**：compile-time 允许关闭 threat detection 不得导致 Nerelan Host 在相同配置下默认接受恶意或未授权写入；编译检查不能代替执行时权限。
8. **经济性/体验**：同一任务测 `verified external effects per human intervention`、重复写入率、UNKNOWN 修复时长、独立验收成功率及完整 Magpie 机会成本/现金成本，不能只比 gha runner 耗时。

## 5. 执行建议

- **P0：测试优先**：`independent readback`、`unknown effect never replay blindly`、`sibling claim/authorization epoch`，归已有 Goal/Task/发布与政策测试；先确认真实覆盖缺口。
- **P1：模块设计借鉴**：Connector Phase/AllowedOrigins/Host-owned secrets、输入纯规划/执行可追溯签收、调试可解释输出。归 #790/#447/#179。
- **P2：只读可解释性**：UI 展示计划/执行/验证的不同状态；仅在减少人工介入并提高可靠性后考虑。
- **REJECT**：安装 gh-aw 全套 GitHub Actions Runner/第二 Work Queue、从 Agent JSON 动态加载 Host verifier、把 compiled intent policy 当已生效、自动开启远端/付费操作、更改 `.github/workflows` 或 Nerelan AGENTS 治理。

**研究留痕不等于实施授权**，本轮没有授予 R2/R3，更不意味着该项目满足 Nerelan 生产门槛。仅保留可复查的源码证据、去重结论和有真实失败标准的反例。

## 6. Follow-up ownership and evidence status

- Existing owners only: #1538 / #1546 (continuous and durable execution), #252 (autonomous improvement), #790 / #253 / #447 (connectors/pack/egress), #179 (security), #1267 (economic benchmarks), #1575 (refactor). Research is not a new product owner or implementation approval.
- Hypotheses need isolated provider-free fixtures before any Go/TS port, then real accepted-result economics. Do not assume upstream Go tests passed; their source is checked only. R2/R3 operations and CI/protected-branch modifications remain outside scope.
