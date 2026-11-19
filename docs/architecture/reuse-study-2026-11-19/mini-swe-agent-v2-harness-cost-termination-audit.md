<!-- R1 docs only. Canonical research Issue #1704. This file is not an implementation or runtime authority. -->

# mini-SWE-agent v2 pinned audit — minimal Agent Harness, terminal semantics, retry/cost attribution and Host trust

> **2026-11-19** · SINGLE_PROJECT / R1_SOURCE_RESEARCH_ONLY / PINNED_STATIC_REVIEW / TESTS_NOT_EXECUTED / NOT_INSTALLED / NOT_BENCHMARKED / NOT_IMPLEMENTED / NO R2/R3 AUTHORITY
>
> **Upstream:** [SWE-agent/mini-swe-agent@04d809ceab9df28f9adaed044884180159172930](https://github.com/SWE-agent/mini-swe-agent/commit/04d809ceab9df28f9adaed044884180159172930); [MIT license](https://github.com/SWE-agent/mini-swe-agent/blob/04d809ceab9df28f9adaed044884180159172930/LICENSE.md); **v2**, not v1. **Nerelan comparison:** [main@b48cc9b82893be222e2ccdb307dd4a81bebee935](https://github.com/dddd2024/Nerelan/commit/b48cc9b82893be222e2ccdb307dd4a81bebee935).
>
> A source audit is NOT a claim of real task completion, actual savings, Windows compatibility, installation approval, or safe untrusted execution.

## 0. 先查重、排除重合、选活跃版本

1. 搜索 Nerelan Issues `mini-swe-agent` / `mini-SWE-agent` / 标题、[research hub #1576](https://github.com/dddd2024/Nerelan/issues/1576) 的索引及旧聊恢复：mini-SWE-agent **在历史探索中提到过**，但未发现 v2 固定源码的独立专项。不能说此前从未研究。
2. 既有 [SWE-ReX #1578](https://github.com/dddd2024/Nerelan/issues/1578) 是**命令执行 Runtime/Environment**，不是 mini-SWE-agent v2 的 Agent Model Protocol / exit/cost semantics；[11-15 C-runtimes 横向报告](https://github.com/dddd2024/Nerelan/blob/main/docs/architecture/reuse-study-2026-11-15/C-runtimes.md) 也不能当本版本深入审查。
3. 搜索时考虑经典 `SWE-agent/SWE-agent`，但其 [README](https://github.com/SWE-agent/SWE-agent/blob/main/README.md) 明确标记已由 mini-SWE-agent 取代，因此本次只审**一个活跃仓库** `SWE-agent/mini-swe-agent`，而非重复研究旧 SWE-agent 或 SWE-ReX。
4. 现有实施 Owner：[#1527](https://github.com/dddd2024/Nerelan/issues/1527) Harness×Model 真实 bake-off、[#1267](https://github.com/dddd2024/Nerelan/issues/1267) accepted-per-cost、[#653](https://github.com/dddd2024/Nerelan/issues/653) 功能真值、[#1556](https://github.com/dddd2024/Nerelan/issues/1556) Liveness、[#1596](https://github.com/dddd2024/Nerelan/issues/1596) stall reroute、[#1504](https://github.com/dddd2024/Nerelan/issues/1504) budget/quotas、[#1342](https://github.com/dddd2024/Nerelan/issues/1342) Magpie usage、[#299](https://github.com/dddd2024/Nerelan/issues/299) sandbox、[#1546](https://github.com/dddd2024/Nerelan/issues/1546) durable. **不新增平行实施 Issue**。

## 1. 固定源码审读：真正能借鉴的 / 不能抄的

### A. Agent×Model×Environment 最小协议（**P1 BORROW_PATTERN / candidate harness for #1527**）

- [`src/minisweagent/__init__.py` L43–82](https://github.com/SWE-agent/mini-swe-agent/blob/04d809ceab9df28f9adaed044884180159172930/src/minisweagent/__init__.py#L43-L82)：`Model.query/format_message/format_observation_messages` 和 `Environment.execute/get_template_vars/serialize` 用极小 `Protocol` 解耦，Agent 不关心模型 API 和 Docker/Local。适合构造 Nerelan 的**外置纯基线 Harness adapter**；现有 [`task_runtime.py` L81–127, L505–575](https://github.com/dddd2024/Nerelan/blob/b48cc9b82893be222e2ccdb307dd4a81bebee935/reverse_agent/platform_v1/task_runtime.py#L505-L575) 已有 `ExecutorRouter`，不重写它。
- [`agents/default.py` L38–73, L88–159](https://github.com/SWE-agent/mini-swe-agent/blob/04d809ceab9df28f9adaed044884180159172930/src/minisweagent/agents/default.py#L38-L159)：步进 `query→execute_actions`，收集线性消息；`FormatError` 变成模型消息并累计计费；`InterruptAgentFlow` 变 exit。每 step 可以含**多个 action**，`execute_actions` 是 Python list comprehension 按序执行，无 Host side-effect receipt。
- [`models/utils/actions_toolcall.py` L11–77](https://github.com/SWE-agent/mini-swe-agent/blob/04d809ceab9df28f9adaed044884180159172930/src/minisweagent/models/utils/actions_toolcall.py#L11-L77)：**仅允许 bash function name**，对 JSON args/name 错误 `FormatError`；source supports tool-call IDs. Test matrix 包含 [text/toolcall/Responses API](https://github.com/SWE-agent/mini-swe-agent/blob/04d809ceab9df28f9adaed044884180159172930/tests/agents/test_default.py#L117-L151)。**不应该复制“只有 bash”作为 Nerelan 插件架构**，而是借鉴“最小可验证协议”的 harness baseline。
- [`models/litellm_model.py` L64–104](https://github.com/SWE-agent/mini-swe-agent/blob/04d809ceab9df28f9adaed044884180159172930/src/minisweagent/models/litellm_model.py#L64-L104)：将 API 原生消息转换为 action；格式解析失败时**保留原始响应和本次 cost**到错误消息（有不可序列化对象时 repr 兜底）。Nerelan 可借鉴 `transport succeeded / parse failed / cost possibly spent` 分离；保存应脱敏且走已有 TaskStore，不能把整个响应原样记录到 UI/日志。

### B. Exit Status vs Actual Accepted Change（**P0 NO-GO as truth**）

- [`environments/local.py` L45–56](https://github.com/SWE-agent/mini-swe-agent/blob/04d809ceab9df28f9adaed044884180159172930/src/minisweagent/environments/local.py#L45-L56) / [Docker L140–151](https://github.com/SWE-agent/mini-swe-agent/blob/04d809ceab9df28f9adaed044884180159172930/src/minisweagent/environments/docker.py#L140-L151)：stdout 去左空白后**首行**为 `COMPLETE_TASK_AND_SUBMIT_FINAL_OUTPUT` 且命令 exit 0 即抛 `Submitted`。此时只证明“环境输出了提交标记”，**未验证代码 patch、任务要求、独立 oracle 和 Git head**。即便恶意/出错脚本 echo marker 也可能结束：Nerelan 严格映射 `Submitted→EXECUTOR_DECLARED_DONE`，不得映射 `VALIDATED/ACCEPTED`。
- [`agents/default.py` L88–125](https://github.com/SWE-agent/mini-swe-agent/blob/04d809ceab9df28f9adaed044884180159172930/src/minisweagent/agents/default.py#L88-L125) `run()` 返回最后 exit message 的 `extra`，含 `exit_status/submission`，能区别 `Submitted`, `LimitsExceeded`, `TimeExceeded`, `RepeatedFormatError`, uncaught exceptions。对照 Nerelan [`task_execution.py` _dispatch_executor](https://github.com/dddd2024/Nerelan/blob/b48cc9b82893be222e2ccdb307dd4a81bebee935/reverse_agent/platform_v1/task_execution.py#L1143-L1260) 已有 executor result/failure classification + separate validation，**保留并完善区分**，不采用最终文本即完成规则。

### C. Timeout / Retry / Liveness（**P1 OBSERVABILITY, REJECT direct Host retry**）

- [`models/utils/retry.py` L9–26](https://github.com/SWE-agent/mini-swe-agent/blob/04d809ceab9df28f9adaed044884180159172930/src/minisweagent/models/utils/retry.py#L9-L26)：Tenacity **默认最多 10 次**、4–60 秒指数退避，部分异常 abort，其余重试由 model adapter 自己执行；[LiteLLM adapter L49–84](https://github.com/SWE-agent/mini-swe-agent/blob/04d809ceab9df28f9adaed044884180159172930/src/minisweagent/models/litellm_model.py#L49-L84) 一次 `Agent.query` 可能产生多次 Magpie/provider request。上层 `n_calls` 不是 provider-request count；内部重试/失败尝试消耗真实费用可能无返回 receipt。**Nerelan 不准把 n_calls 当精确费用或推断没有花钱；模型层重试需和 Magpie request-id 关联，必要时禁用嵌套重试，让 Host 控制 binding failover 和 UNKNOWN**。
- [`environments/local.py` L72–92](https://github.com/SWE-agent/mini-swe-agent/blob/04d809ceab9df28f9adaed044884180159172930/src/minisweagent/environments/local.py#L72-L92) 对 POSIX subprocess 设新 process group，超时 kill group，Windows 路径仅 `process.kill()`：Windows 后代进程是否全停止不能由此证明；`LocalEnvironment.execute` 吞异常生成负 returncode，模型可继续。对照 [#1556](https://github.com/dddd2024/Nerelan/issues/1556) 需要分 phase 知道“正在执行命令 / 模型等待 / 网络重试 / 未知”，本框架的 stdout/returncode 不足以替代 Nerelan 的 process-tree/idle 证据。
- [`agents/default.py` L130–159](https://github.com/SWE-agent/mini-swe-agent/blob/04d809ceab9df28f9adaed044884180159172930/src/minisweagent/agents/default.py#L130-L159)：`step_limit/cost_limit/wall_time_limit` 在**下一次模型查询之前**检查，不能硬性阻止已开始的昂贵一次调用或多个 bash action（时间上也不能中断 in-flight）。对照 [#1504](https://github.com/dddd2024/Nerelan/issues/1504) 单 attempt 预算超支现象，不能从仅设 `cost_limit` 推断真实额度受限。
- **跨-run状态风险**：[default.py L38–51, L88–96](https://github.com/SWE-agent/mini-swe-agent/blob/04d809ceab9df28f9adaed044884180159172930/src/minisweagent/agents/default.py#L38-L96) `n_calls`、`cost`、`_start_time` 在构造器初始化；`run()` 只重置 messages，不显式重置上述字段。**同一对象反复调用 run 的指标延续**；跨 trial 的公平性必须新实例/新 trial identity；尚无同对象 live test。

### D. Cost and quota missingness（**P0 REJECT zero-on-unknown**）

- [`litellm_model.py` L108–126](https://github.com/SWE-agent/mini-swe-agent/blob/04d809ceab9df28f9adaed044884180159172930/src/minisweagent/models/litellm_model.py#L108-L126)：`completion_cost` 非正时报错；但当 `cost_tracking=ignore_errors` 时，price lookup 错误变 `cost=0.0`。**这不是免费**，Nerelan 现有 [`cost_quality_benchmark.py` L58–166](https://github.com/dddd2024/Nerelan/blob/b48cc9b82893be222e2ccdb307dd4a81bebee935/reverse_agent/platform_v1/cost_quality_benchmark.py#L58-L166) 和 [`usage_ledger.py` L226–328](https://github.com/dddd2024/Nerelan/blob/b48cc9b82893be222e2ccdb307dd4a81bebee935/reverse_agent/platform_v1/usage_ledger.py#L226-L328) 已保留 cost/usage UNKNOWN 与独立验收；不接受改成 0 计费。
- `GLOBAL_MODEL_STATS` 和 `self.cost` 都是 SDK 自身估算/报告，不能充当 Magpie Request、订阅实际现金票据或每角色真实 tokens；call 失败但 provider 可能扣费，必须按平台已有 source-of-truth + evidence 分类。

### E. Environment / Plugin / Workspace trust（**P0 NO DIRECT ADOPT**）

- [`environments/local.py` L24–60](https://github.com/SWE-agent/mini-swe-agent/blob/04d809ceab9df28f9adaed044884180159172930/src/minisweagent/environments/local.py#L24-L60)：`shell=True` + `os.environ | config.env` + `get_template_vars` 可看整套 `os.environ`。这是信任宿主直接执行环境，**不是 OS sandbox**，不能在 Nerelan Windows host 上作为不可信 Agent 默认环境；`get_template_vars` 允许模板读取环境值，若低信任配置可控还涉及 Secret 进入 prompt 的风险。
- [`environments/docker.py` L74–161](https://github.com/SWE-agent/mini-swe-agent/blob/04d809ceab9df28f9adaed044884180159172930/src/minisweagent/environments/docker.py#L74-L161)：Docker `run_args` 可影响隔离，`forward_env` 明确透传所选宿主环境变量，`__del__` 调 cleanup 且实际 stop 是异步后台 shell。这**不是可验证的容器释放证据**，Host 必须 Own container identity/lifecycle and egress/secret policies。
- [`models/__init__.py` L92–113](https://github.com/SWE-agent/mini-swe-agent/blob/04d809ceab9df28f9adaed044884180159172930/src/minisweagent/models/__init__.py#L92-L113) / [`environments/__init__.py` L19–34](https://github.com/SWE-agent/mini-swe-agent/blob/04d809ceab9df28f9adaed044884180159172930/src/minisweagent/environments/__init__.py#L19-L34)：支持直接从配置指定 Python import path 加载 model/environment class，是开发者扩展点，**不是经过签名/权限审批的插件生命周期**。对于 Nerelan 的 Pack/MCP/Plugin，不可信 project config 绝不可直接成为任意 Python import authority。
- 项目重点是 bash-only Agent，不提供 Nerelan 需要的独立 MCP Tool host approval，故**Plugin 模块不复用此 runtime**；仍归属 [#790](https://github.com/dddd2024/Nerelan/issues/790)/[#303](https://github.com/dddd2024/Nerelan/issues/303)。

### F. Crash/trajectory integrity（**P1 BORROW event shape, REJECT durability claims**）

- [`agents/default.py` L159–190](https://github.com/SWE-agent/mini-swe-agent/blob/04d809ceab9df28f9adaed044884180159172930/src/minisweagent/agents/default.py#L159-L190)：每个 step / exception 在 finally 调 `save()`，JSON `Path.write_text` 直接覆写路径，**没有这里可见的 fsync/atomic rename、step fence、外部副作用 ledger 或 committed marker**。JSON trajectory != true durable recovery；run() 自身无 resume from checkpoint contract。
- 对照 Nerelan [`run_store.py` external operations](https://github.com/dddd2024/Nerelan/blob/b48cc9b82893be222e2ccdb307dd4a81bebee935/reverse_agent/platform_v1/run_store.py#L2974-L3229) 已具备 Intent/fencing/UNKNOWN fail-closed，不可由一个 `messages.json` 替代。JSON 轨迹更适合透明 Debug 与复现实验输入，落到 Nerelan 已有 Task Events 的**受限脱敏投影**。

## 2. 模块复用/实施归属矩阵

| Nerelan | 决策 | 借鉴切片 | 禁止复制 | Owner |
|---|---|---|---|---|
| Agent Harness | **P1 CONDITIONAL BENCHMARK** | `DefaultAgent` 极简固定对照：text/toolcall/responses 同任务相同 worktree/模型 | 不替换 OpenCode、TaskStore、Goal coordinator | #1527 |
| Model/Account Router | **ALREADY_REUSED + P0 safety** | 区分 agent step、SDK retry、Magpie request、usage receipt | 不引入第二网关、不把 SDK cost=0 当免费 | #1342/#1504 |
| Completion/Quality | **P0 BORROW_STATUS_MAPPING** | Submitted vs attempted vs artifact validated vs independently accepted | 不用 stdout marker 作为成功 oracle | #653/#1267 |
| Liveness | **P1 BORROW_DIAGNOSTICS** | command start/exit/timeout、format fail、model retry wait 独立事件 | 不把模型重试循环藏在一个“stalled”里 | #1556/#1596 |
| Environment/Sandbox | **REJECT DIRECT** | 确认短命 subprocess env 能力门槛 | 不直接本地 shell、不继承全部 host secrets | #299/#793 |
| Plugin/Pack/MCP | **NO DIRECT REUSE** | 动态模型/环境 class 映射只作可发现扩展点 | 不信任 repo-controlled import path 或工具 | #790/#303 |
| Durable State | **KEEP NERELAN** | 脱敏 trajectory 作为派生 Debug | 不复制非原子 JSON save 代替外部收据 | #1546/#1191 |

## 3. Provider-free 最小测试（均尚未运行，按 #1527 / #653 / #1556 归属）

1. **F1 Protocol adapter**：同 frozen sample/task/模型/工具/工作区，用 fake text parser、fake toolcalls、fake Responses API 对齐 `MODEL_RESPONSE, ACTION_STARTED, ACTION_EXIT, AGENT_DECLARED_DONE`。原始工具响应一律截断脱敏，不能把 status 当功能 PASS。
2. **F2 False submit**：一个 shell 命令仅 echo `COMPLETE_TASK_AND_SUBMIT_FINAL_OUTPUT` 而没有功能 patch；上游应返回 `Submitted`，Nerelan 接受裁决必须仍为 `UNKNOWN/REJECT`；另测非零 exit marker、间接输出、恶意内容。
3. **F3 Hidden retry**：fake model 前 2 次 429 后 3 次成功；`agent.n_calls=1`，真实 Magpie requests=3，包含所有消耗/UNKNOWN；绑定变化应由 Host 可见。明确区分 SDK retry count 与 task retry count。
4. **F4 Cost missing**：`ignore_errors` 模式，provider response 成功而 cost unknown，禁止转换为 `cash_cost=0` 或低成本排名胜者；单个模型调用超过当前预算，上限逻辑不能误报告被硬拦截。
5. **F5 Crash after action**：执行了外部副作用但 JSON trajectory 保存被中断或部分写；重启须查 Host durable external op receipt，UNKNOWN 时 fail-closed，禁止根据 messages.json 不存在而重复派发。
6. **F6 Process tree Windows**：模拟超时前创建子进程；不凭 `process.kill` 判断其子进程已清理；使用 Host-owned process identity 验证或标记 unresolved，不宣称已跑 Windows 实机。
7. **F7 Config trust**：把恶意 import path、额外 Docker run args、secret-bearing env 名、危险 bash 放进 untrusted repo config；Host 在安装/导入/执行前拒绝；没有强隔离时禁止启动。
8. **F8 Same agent reused**：一个 Agent 实例 run 两次，每次独立任务，基于固定源码验证 n_calls/cost/start_time 跨次延续；不能在同一对象采样后把累计值当单任务消费。
9. **F9 Real benchmark gate**：至少 trivial/medium/large 的**冻结同类任务**，同 executor/mode/模型条件跨 Harness A/B，计算 `independently_accepted changes / all admitted trials`、真实发生的 Magpie request+subscription cash/UNKNOWN、重试、wall-clock、tool errors。无真实 provider run/独立功能评估前不宣称“mini 更便宜 / 更强”。

**No-go**: 不能把 Host secrets 注入 untrusted local subprocess；不能把 Submitted 变 Accepted；不能把 cost UNKNOWN 变 zero；不能把 SDK retry 当唯一真实请求；不能因为 trajectory JSON 不完整就重复远端 side effect；不引入第二 scheduler/gateway/ledger。

## 4. 实际工作与证据边界

完成：固定上游 v2 commit、读取 Model/Agent/Env/Retry/Test 源码和配置及 MIT license，检索已有 Nerelan 研究/专项/现有实施 Owner，读取 Nerelan 同版本 ExecutorRouter/TaskExecution/TaskStore/CostBenchmark/ModelProfiles/UsageLedger，形成可证伪测试计划与模块裁决。

未完成：未安装运行 mini-swe-agent、未跑 upstream/Nerelan pytest、未发生真实 model/API 调用或任意 shell 行为、未进行 Windows 主机验证、未证明性能/节省、未运行 CI/独立评审、未合并。**研究结果只是静态源证据，不是实施或验收。**


---

## Publication and evidence links
- Canonical Issue: https://github.com/dddd2024/Nerelan/issues/1704
- Research hub: https://github.com/dddd2024/Nerelan/issues/1576
- Final Draft PR number recorded in the issue/hub after creation.
- Status: `PINNED_STATIC_SOURCE_REVIEW / NO_RUN_TESTS / NO_INSTALL / NO_MODEL_SPEND / NO_MERGE / NO_IMPLEMENTATION`.
