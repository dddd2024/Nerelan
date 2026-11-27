<!-- Research-only snapshot. Canonical tracking Issue #1697. Not runtime authority. -->

# Inspect AI pinned deep dive — evaluation identity, scoring coverage, scoring-only resume, Agent Bridge trust

> **2026-11-19 | SINGLE_PROJECT / STATIC_PINNED_SOURCE_AUDIT / RESEARCH_ONLY / NOT_INSTALLED / NO_TESTS_EXECUTED / NO_MODEL_SPEND / NOT_IMPLEMENTED**
>
> Upstream **one repository**: [UKGovernmentBEIS/inspect_ai@12e474464770eaed5b031e86a1f523b2f320015f](https://github.com/UKGovernmentBEIS/inspect_ai/tree/12e474464770eaed5b031e86a1f523b2f320015f) (MIT: [LICENSE](https://github.com/UKGovernmentBEIS/inspect_ai/blob/12e474464770eaed5b031e86a1f523b2f320015f/LICENSE)).
>
> Nerelan compared against [main@b48cc9b82893be222e2ccdb307dd4a81bebee935](https://github.com/dddd2024/Nerelan/tree/b48cc9b82893be222e2ccdb307dd4a81bebee935), via exact file reads / GitHub code search. Repo contents are read, not imported or run. **This audit neither authorizes dependency adoption nor creates a new implementation owner.**

## 0. 事前查重：为什么本轮是增量

- 查 **research hub #1576**（正文 + 已登记录）、11/15 横向 A–E 报告、此前 **Promptfoo [#1606](https://github.com/dddd2024/Nerelan/issues/1606)**、**Restate Python SDK #1694**、现有 **#1527** Agent×Model bake-off、**#1267** 成功成本对比与 GitHub `Inspect AI` / `inspect_ai` / `UKGovernmentBEIS` issues 和代码检索。没有找到此项目独立固定 SHA 源码研究。
- **已有研究不是零**：Promptfoo 已覆盖 Harness Provider 配对、测试工作区和缓存污染、tool trajectory grader/cost 与不可信断言。**本轮不重做它**。新增独有问题：
  1. 恢复评测时，如何证明某个样本是 **重新运行**、从日志 **复用**、从 checkpoint **续跑**，或**仅重新评分**？
  2. 评分器失败、无法评分样本应如何计入 `Nerelan accepted-per-cost` 分母？
  3. 外部 coding-agent 在宿主模型代理前允许带哪些请求头，是否能夹带账户/计费租户身份？

## 1. 上游源码可核事实

### A. Sample identity、动态分支与 retry 的来源证据（Eval / Agent / Context）

- [`src/inspect_ai/_eval/task/run.py` L265–342](https://github.com/UKGovernmentBEIS/inspect_ai/blob/12e474464770eaed5b031e86a1f523b2f320015f/src/inspect_ai/_eval/task/run.py#L265-L342)：`PreviousError` 继承跨 task attempt 的 error history、`InvalidatedPrior` 禁止复用或恢复、`EvalSampleSource` 按明确 **(sample id, epoch)** 查询旧结果，且区分有资格 seed 的旧日志。要区别“同一试验恢复”与“新独立试验”。
- [`run.py` L1617–1828](https://github.com/UKGovernmentBEIS/inspect_ai/blob/12e474464770eaed5b031e86a1f523b2f320015f/src/inspect_ai/_eval/task/run.py#L1617-L1828)：对 clean prior `EvalSample` **直接复用结果与旧样本用量**，不重跑 solver；非 clean 才选择 checkpoint 恢复 / 干净重跑；读旧 log 与 checkpoint 的并发 probe 有上限 **25**。**重要：复用旧 usage 是记录累计历史，不是新执行的实际花费，不能作为新的独立成功样本**。
- [`run.py` L377–411](https://github.com/UKGovernmentBEIS/inspect_ai/blob/12e474464770eaed5b031e86a1f523b2f320015f/src/inspect_ai/_eval/task/run.py#L377-L411)：anonymous dynamic sample id 形如 `dyn-<attempt-token>-<counter>`，token 取创建时间，源码明确指出**显式 id 与这种形状冲突可能使新 sample 误复用旧结果**。借鉴分层身份，不要复制该命名规则；Nerelan 应用随机/UUID + DB 唯一约束、明确实验 owner + cohort + trial + epoch。
- [`sample_source.py` L41–125](https://github.com/UKGovernmentBEIS/inspect_ai/blob/12e474464770eaed5b031e86a1f523b2f320015f/src/inspect_ai/_eval/task/sample_source.py#L41-L125)：`initial_samples`、`next_samples`、`sample_complete`、`sample_abandoned` 允许自适应样本补充。适合**探索性**寻找模型弱项；若根据不同模型效果动态投喂不同难度样本，**不能拿不同 cohort 的原始成功率作公平比较**。
- [`EvalSampleSummary` L301–385](https://github.com/UKGovernmentBEIS/inspect_ai/blob/12e474464770eaed5b031e86a1f523b2f320015f/src/inspect_ai/log/_log.py#L301-L385)保留 id、epoch、usage-by-role、错误、时长、retry、completed；[model usage](https://github.com/UKGovernmentBEIS/inspect_ai/blob/12e474464770eaed5b031e86a1f523b2f320015f/src/inspect_ai/model/_model_output.py#L17-L71)明确区分 fresh/cache read/cache write/reasoning 和 provider-reported USD cost（缺失 `total_cost` 是 None），但这并非 Magpie 的结算真实现金账。

### B. Agent 完成而 grader 未完成时的恢复：`resume_for_scoring`

- [`resume.py` L22–39](https://github.com/UKGovernmentBEIS/inspect_ai/blob/12e474464770eaed5b031e86a1f523b2f320015f/src/inspect_ai/util/_checkpoint/resume.py#L22-L39)：仅扫描**该 sample/epoch 当前尝试已复制的已提交 checkpoint**；最新 checkpoint trigger 为 `agent_complete` 才进入 `resume_for_scoring`，其他为 `resume`；无 checkpoint 时 `None`，并不能神奇地免重跑。
- [`agent/_react.py` L215–275](https://github.com/UKGovernmentBEIS/inspect_ai/blob/12e474464770eaed5b031e86a1f523b2f320015f/src/inspect_ai/agent/_react.py#L215-L275)：用 `cp.track` 注册 messages/output/attempt state，`resume_for_scoring` 时短路 Agent loop，仅继续后续评分。[`docs/checkpointing.qmd` L283–374](https://github.com/UKGovernmentBEIS/inspect_ai/blob/12e474464770eaed5b031e86a1f523b2f320015f/docs/checkpointing.qmd#L283-L374) 描述 tick→capture→**committed checkpoint file**→emit 的时序及边界。
- **Limitations** [`docs/checkpointing.qmd` L365–374](https://github.com/UKGovernmentBEIS/inspect_ai/blob/12e474464770eaed5b031e86a1f523b2f320015f/docs/checkpointing.qmd#L365-L374)：只在 Agent **turn 边界**做 checkpoint；长工具调用不能中途暂停；嵌套 limit scope 不恢复；**scoring-only resume 不重新执行 Agent 预算门禁**。因此 **不能以 checkpoint 恢复宣称跨远端 side-effect exactly-once**，也不能把重复 grader 开销漏记。Nerelan 已有外部-operation journal、fencing、UNKNOWN fail-closed，保留不改。
- [`docs/checkpointing.qmd` L214–224](https://github.com/UKGovernmentBEIS/inspect_ai/blob/12e474464770eaed5b031e86a1f523b2f320015f/docs/checkpointing.qmd#L214-L224) 的 snapshot 约束包括防止越界节点/特殊文件/跨路径硬链接、capture path 不可在 attempts 间改变；不建议把可恢复目录未经检查恢复到 Windows trusted host。

### C. Scorer 不是永远正确：有效判分率是独立指标

- [`docs/scoring-policy.qmd` L16–38, L57–100](https://github.com/UKGovernmentBEIS/inspect_ai/blob/12e474464770eaed5b031e86a1f523b2f320015f/docs/scoring-policy.qmd#L16-L100) 清楚区分 **incorrect**, **scoring error**（raise）、**unscored**（NaN）、**not applicable**（None）和 **solver partial scoring**；[`_eval/task/results.py` L405–432](https://github.com/UKGovernmentBEIS/inspect_ai/blob/12e474464770eaed5b031e86a1f523b2f320015f/src/inspect_ai/_eval/task/results.py#L405-L432) 将 NaN 的 unscored 排除出某些 metric 计算，并另计 `scored_samples` 与 `unscored_samples`。这允许`accuracy=0.5`只建立在2个可评分样本上，**不是所有预期样本的总体成功率**。
- [`tests/test_score_on_error.py` L115–225](https://github.com/UKGovernmentBEIS/inspect_ai/blob/12e474464770eaed5b031e86a1f523b2f320015f/tests/test_score_on_error.py#L115-L225) 有上游测试模拟 scorer 顺序、solver 出错后仍评分、scorer 再次出错；这些是源码阅读证据，**本轮没有实际跑 pytest**。
- [`scorer/_model.py` L35–105](https://github.com/UKGovernmentBEIS/inspect_ai/blob/12e474464770eaed5b031e86a1f523b2f320015f/src/inspect_ai/scorer/_model.py#L35-L105)：`model_role='grader'` **默认并非 required**，若没有绑定 grader，可能回退到正在评测的模型；多 grader majority **无多数票就 unscored**。所以“设置了 grader role”不等于独立审查，必须在宿主验证不同模型族、独立会话、冻结产物/对应合同。评测主真值仍是 Nerelan 的功能检查和独立 review（#653），LLM judge 只作辅助。

### D. Agent Bridge / Provider Account 安全边界

- [`src/inspect_ai/agent/_bridge/bridge.py` L85–260](https://github.com/UKGovernmentBEIS/inspect_ai/blob/12e474464770eaed5b031e86a1f523b2f320015f/src/inspect_ai/agent/_bridge/bridge.py#L85-L260)：独立沙箱客户端和 in-process 客户端有**不同**的 header admission 规则。`resolve_forward_client_headers` 拒绝 authorization, x-api-key, api-key, cookie, x-goog-api-key, `x-amz-` 与传输框架头等；`filter_sandbox_client_headers` 仅允许 `Accept-Encoding` 与宿主明确批准的 name+value。`OpenAI-Organization` / `x-goog-user-project` 不允许从不可信客户端直接指定。编码只允许宿主 HTTP 客户端能解码的项。
- 上游 [`tests/agent/test_bridge_headers.py` L1–200](https://github.com/UKGovernmentBEIS/inspect_ai/blob/12e474464770eaed5b031e86a1f523b2f320015f/tests/agent/test_bridge_headers.py#L1-L200) 覆盖大小写、SDK headers、鉴权与合法透传。**对 Nerelan 的价值**：即使 Agent CLI 在隔离空间运行，模型代理前也不能由它夹带账户/项目/计费组织 override，以免绕过 Magpie 路由和 Owner 账号边界。应把与 Magpie 的模型/账户选择保留在可信 host。
- 反面证据：[examples/http_proxy/README.md](https://github.com/UKGovernmentBEIS/inspect_ai/blob/12e474464770eaed5b031e86a1f523b2f320015f/examples/http_proxy/README.md) 明确 **network_mode:none 的容器网络策略**才是实际网络 egress 边界，mitmproxy 只是重映射；[`util/_sandbox/local.py` L26–115](https://github.com/UKGovernmentBEIS/inspect_ai/blob/12e474464770eaed5b031e86a1f523b2f320015f/src/inspect_ai/util/_sandbox/local.py#L26-L115) 的 `local` provider 实际通过本地 subprocess 执行，不能宣称安全沙箱。
- 插件扩展是 Python scorer/solver/tool code：**不运行未经信任的扩展代码**，Plugin 注册或评测断言不产生 Host 权限。

### E. Inspect eval concurrency 不是 Nerelan Goal 调度器

- [`_eval/eval.py` L804–808](https://github.com/UKGovernmentBEIS/inspect_ai/blob/12e474464770eaed5b031e86a1f523b2f320015f/src/inspect_ai/_eval/eval.py#L804-L808) 拒绝同一 Python 进程中两个同时调用 `eval_async`；其内部任务/样本并行是评测执行机制，不应替换 Nerelan 的长期 Goal/Coordinator/TaskStore 或 Magpie 账户池。

## 2. Nerelan 现状和复用分级

读取 Nerelan 最新可见源码：
- [`cost_quality_benchmark.py` L32–171](https://github.com/dddd2024/Nerelan/blob/b48cc9b82893be222e2ccdb307dd4a81bebee935/reverse_agent/platform_v1/cost_quality_benchmark.py#L32-L171) 有 `BenchmarkContract` 的 base/requirements/acceptance/tools/budget digest、按 TaskStore usage 汇总 UNKNOWN、受信调用方提供独立验收后才比较成本，且拒绝把 single task savings 概括成普遍节省。**ALREADY_REUSED**，不造第二评测数据库。
- [`model_profiles.py` L105–235](https://github.com/dddd2024/Nerelan/blob/b48cc9b82893be222e2ccdb307dd4a81bebee935/reverse_agent/platform_v1/model_profiles.py#L105-L235) 区分 provider/host/refusal/能力失败，按 binding 统计；不应把 scorer 的 failure 自动变成模型能力失败。
- [`capability_benchmarks.py`](https://github.com/dddd2024/Nerelan/blob/b48cc9b82893be222e2ccdb307dd4a81bebee935/reverse_agent/platform_v1/capability_benchmarks.py) 已有 benchmark prior snapshot、candidate/stage/adopt。新增适合围绕 trial-id / scoring coverage 形成可信证据，不替换 seed policy。
- 正式 Owner：[**#1527**](https://github.com/dddd2024/Nerelan/issues/1527) Agent×Model、[**#1267**](https://github.com/dddd2024/Nerelan/issues/1267) 单模型与多模型经济性、[**#653**](https://github.com/dddd2024/Nerelan/issues/653) 功能真值、[**#1504**](https://github.com/dddd2024/Nerelan/issues/1504) 成本等效预算、[**#1546**](https://github.com/dddd2024/Nerelan/issues/1546) durability、[**#299**](https://github.com/dddd2024/Nerelan/issues/299) sandbox、[**#790**](https://github.com/dddd2024/Nerelan/issues/790) 连接器和 [**#1342**](https://github.com/dddd2024/Nerelan/issues/1342) Magpie。**不增设重复实施 Issue**。

| 模块 | 裁决 | 最小值得学的设计 | 不照搬 |
|---|---|---|---|
| **Quality / Agent×Model** | **P0 BORROW_PATTERN** | denominator: requested trials / truly executed / reused / valid-scored / unscored / scorer error / independently accepted；失败归因不能丢样本 | 不以 grader accuracy 单值当发布/路由真值 |
| **Agent harness adapter** | **P1 BORROW_PATTERN** | 明确 evaluator arm / trial / epoch / attempt、executor family+version、frozen tool & policy digest；exploration vs confirmation cohorts | 不复制 Inspect solver loop 或第二 scheduler |
| **Resume / memory** | **P1 BORROW_PATTERN** | `AGENT_COMPLETED` + exact artifact receipt 后，分开执行 `SCORING_PENDING` → `SCORING_VERIFIED`；checkpoint 恢复以 committed marker 为准 | 不把 checkpoint 当外部调用去重或绕过预算 |
| **Plugin / tool / account bridge** | **P0 BORROW_PATTERN** | 不可信 CLI 不能传入 provider billing/tenant/authorization headers；host 审批 exact allowlist | 不复制 in-process 宽松规则到沙箱、不把 proxy 当隔离 |
| **Cost accounting** | **ALREADY_REUSED + P1** | 计入 grader/retry/abort/reuse、fresh/cache/reasoning；UNKNOWN cash 保留 | 不把 provider `total_cost` 等同已结算现金 |
| **Sandbox / engine** | **REJECT DIRECT** | 可借鉴 restore path validation fixture 和 user identity preflight | 不移植 Inspect evaluator / local subprocess 当沙箱 |

## 3. 可证伪的 provider-free fixture（尚未执行）

1. **P0 score coverage**: 10 个预期样本，2 个 scorer 报错、2 个 unscored、其余 6 个中 3 pass：报告 `valid_scoring_coverage=6/10`、`accuracy_of_scored=3/6`、`accepted_of_all=3/10`（独立验收尚应另算）。任何主成功率以 3/6 假装 3/10 则 FAIL。
2. **P0 independence**: 未绑定 grader 时 `model_role='grader'` 默认回退 candidate，host 必须标 `NOT_INDEPENDENT`，不可冒充不同模型家族独立评审。
3. **P1 retry provenance**: 一条样本先成功、第二条崩溃；resume 旧成功必须 `reused=true`，不创造第二条 fresh model request 或增加独立样本分母；重新尝试失败样本保留错误历史和每次真实调用费用。
4. **P1 scoring-only**: Fake executor agent 已完成、artifact+reply digest 已确认，模拟 grader 崩溃；恢复只重新评分，不重跑 agent，不重复 tool side effects。没有有效 snapshot/receipt → UNKNOWN/BLOCKED，不能因为 `agent_complete` 文本标签任意跳过。
5. **P0 ID collision**: 显式相同 sample id 不同 contract/epoch；动态样本产生旧格式 `dyn-...` 冲突；两者拒绝旧结果复用/报告冲突，不靠 timestamp 排他。
6. **P0 bridge header**: Fake CLI 带 `Authorization` / `OpenAI-Organization` / `x-goog-user-project` / `x-amz-date` / `cookie`、大小写变体、未知 feature headers，只有 host 授权 name+value 可过；直接网络 egress 仍须系统层隔离。
7. **P1 cash**: grader rerun / abort 原来已花 token、cache read / unknown usage，需在同一 evidence ledger 归因而不能归零或计算虚假节省；接受门槛沿用 #1267 比较每个 **accepted change** 的完整成本。

**Exit conditions**: 来源可追溯、分母不膨胀、无 reviewer fallback 独立性误判、无外部重派、无账号/凭据 egress 越权；若需要第二授权系统、第二用量账或依赖移植则 NO-GO。

## 4. Evidence / process status

**What was done**: read pinned upstream source, tests and documentation; inspected related existing Nerelan source/Issues; verified GitHub pre-research duplication; wrote research classification & provider-free fixtures.

**Not done**: installing/operating Inspect, running its tests or Nerelan tests, exercising paid providers, running a benchmark, proving correctness on Windows, changing product runtime, obtaining CI/reviewer approval, or merging. Research Issue/Draft PR alone are not functional acceptance or implementation permission.


---

## Filing status
- Canonical source audit: https://github.com/dddd2024/Nerelan/issues/1697
- Research navigation hub: https://github.com/dddd2024/Nerelan/issues/1576
- Draft documentation PR: pending creation as of this document's first commit; the authoritative PR link is in the research Issue and hub comment.
- Status: STATIC_SOURCE_REVIEW / NO_TEST_EXECUTION / NO_IMPLEMENTATION / NOT_MERGED.
