<!-- R1 docs-only / Research not product implementation / Upstream Apache-2.0 source not copied -->
> **Canonical source audit:** [Issue #1643](https://github.com/dddd2024/Nerelan/issues/1643) · **Central research index:** [#1576](https://github.com/dddd2024/Nerelan/issues/1576) · **Upstream** `huggingface/smolagents@e1249d373d58db6abc73882ee394f6bb3854c89f` · **Nerelan main** `3cd7e622d032a8f4f4b22d08c02277141eae97d0`.

# smolagents pinned-source 深度复用审计：CodeAgent、ToolCalling、SubAgent、Tool/MCP、Python 执行超时与接受/成本事实

> **2026-11-17 · SINGLE_UPSTREAM · R1 RESEARCH_ONLY · STATIC_SOURCE_AUDIT + STDLIB_SEMANTICS_MICROTEST · NO_SDK_INSTALL · NO_MODEL_CALL · NO_REAL_SANDBOX_TEST · NO_IMPLEMENTATION_AUTHORITY**  
> **上游固定 SHA**：[huggingface/smolagents@e1249d373d58db6abc73882ee394f6bb3854c89f](https://github.com/huggingface/smolagents/commit/e1249d373d58db6abc73882ee394f6bb3854c89f)；[`LICENSE` Apache-2.0](https://github.com/huggingface/smolagents/blob/e1249d373d58db6abc73882ee394f6bb3854c89f/LICENSE)。该 SHA 的 `pyproject.toml` 是版本来源，**不臆造当前发布版号**。  
> **Nerelan 固定基线**：[main@3cd7e622d032a8f4f4b22d08c02277141eae97d0](https://github.com/dddd2024/Nerelan/commit/3cd7e622d032a8f4f4b22d08c02277141eae97d0)。核心评测指标：在真实 Owner 边界、持续运行与独立验收约束下，**每个独立验收成功 Goal 的全成本**及成功率；不能仅数 Agent 步数或生成 Token。

## 0. 先查重：本项目之前没有独立专项

在选题前搜索 GitHub Nerelan 的 Issues/PR 关键词 `smolagents`、`huggingface/smolagents`、`smol agents`，核对 [#1576 研究总索引](https://github.com/dddd2024/Nerelan/issues/1576) 的当时 **26** 条既有评论，并读最新 [AGENTS.md](https://github.com/dddd2024/Nerelan/blob/3cd7e622d032a8f4f4b22d08c02277141eae97d0/AGENTS.md) Governance v2.1。**没找到本项目独立 pinned-source Issue/PR**。虽已研究 Pydantic AI #1639（Python Toolsets/Deferred）、TaskWeaver #1641（Jupyter Plugin/Kernel）、Agentbox #1637（Owner 安全）、SWE-ReX #1578（执行环境）、ToolHive #1590（MCP）、Pi Herdsman #1631（sub-agent ownership）、Rulesync #1629，但本项目新增的是 **code-as-action 的模型往返经济性、AST Interpreter 超时的线程池关闭语义、assert-based final check、remote code executor 与 managed agents 的不兼容、Hub/MCP Tool code trust 的执行效果**。

本研究仅讨论**一个上游**。所有实施映射既有 owner：[#1527 executor×model bake-off](https://github.com/dddd2024/Nerelan/issues/1527)、[#1508 true multi-Agent](https://github.com/dddd2024/Nerelan/issues/1508)、[#253 Packs](https://github.com/dddd2024/Nerelan/issues/253)、[#790 MCP](https://github.com/dddd2024/Nerelan/issues/790)、[#299 execution sandbox](https://github.com/dddd2024/Nerelan/issues/299)、[#303 workspace trust](https://github.com/dddd2024/Nerelan/issues/303)、[#1596 liveness](https://github.com/dddd2024/Nerelan/issues/1596)、[#1546 goal engine](https://github.com/dddd2024/Nerelan/issues/1546)、[#296 context](https://github.com/dddd2024/Nerelan/issues/296)、[#280 observability](https://github.com/dddd2024/Nerelan/issues/280)、[#361 reuse gate](https://github.com/dddd2024/Nerelan/issues/361)。**不创建重复实施 Issue**。

## 1. 十个源码模块与可借鉴边界

| 区块 / 上游 pinned source | 源码真实行为（有界事实） | 对 Nerelan 的复用判定 |
|---|---|---|
| **S1 Code-as-action** [`agents.py:1500-1635`](https://github.com/huggingface/smolagents/blob/e1249d373d58db6abc73882ee394f6bb3854c89f/src/smolagents/agents.py#L1500-L1635)、[`#L1670-L1764`](https://github.com/huggingface/smolagents/blob/e1249d373d58db6abc73882ee394f6bb3854c89f/src/smolagents/agents.py#L1670-L1764) | `CodeAgent` 让模型输出 Python 代码块（或结构化 code），一次代码运行可连续组合多个工具调用、中间数据/循环。默认为 **`executor_type='local'`**，若不显式指定远端 executor 不会自动走隔离容器；`LocalPythonExecutor` 不是安全 sandbox。该形式可能减少模型↔工具交替次数，但实际成本取决于生成代码长度、错误纠正、工具费用、Reviewer 费用和恢复重试。 | **BORROW_PATTERN P1/实验**：做安全受限的 **CodeAction orchestration** 作为可选 (harness,model,task) 对照实验；只有 Host-supplied pre-authorized Tool bindings 可用，不能执行任意 Python 的 OS 权限；无净收益不开发新 runtime。 |
| **S2 JSON Tool Calling** [`agents.py:1230-1450`](https://github.com/huggingface/smolagents/blob/e1249d373d58db6abc73882ee394f6bb3854c89f/src/smolagents/agents.py#L1230-L1450) | `ToolCallingAgent` 接模型的显式 tool calls，多调用使用线程池并发；`parallel_calls` 以 tool_call_id 为键，输出按 ID 排序整理，**并发执行不等于外部副作用有序/幂等/有 Host 授权**。 | **ALREADY_REUSED**：Nerelan 已有独立 Executor 和 LangGraph Fanout；借鉴同任务 Code-vs-JSON 调度性能比较，禁止并行造成发布、支付、repo 写入等副作用竞态。 |
| **S3 managed subagents** [`agents.py:294-414`](https://github.com/huggingface/smolagents/blob/e1249d373d58db6abc73882ee394f6bb3854c89f/src/smolagents/agents.py#L294-L414)、[`#L436-L540`](https://github.com/huggingface/smolagents/blob/e1249d373d58db6abc73882ee394f6bb3854c89f/src/smolagents/agents.py#L436-L540)、[`#L1575-L1620`](https://github.com/huggingface/smolagents/blob/e1249d373d58db6abc73882ee394f6bb3854c89f/src/smolagents/agents.py#L1575-L1620) | ManagedAgents 与 tools 并列注册且名称不能重复；上级可把子 Agent 当 callable；不过 `CodeAgent.create_python_executor()` 对 **remote executor + managed_agents** 明确 `raise Exception('Managed agents are not yet supported with remote code execution.')`。轻量 callable 不提供 TaskStore 独立 task/lease/epoch/Owner delegation/跨进程续接的承诺。 | **ALREADY_REUSED + REJECT REPLACEMENT**：继续用 LangGraph Send/DAG+TaskStore，受信调用应有 `childTaskId/parentTaskId/ownerGrant/attemptEpoch/receipt`，不把子 Agent 的 Python 函数调用当 durable multi-Agent。 |
| **S4 Tool contracts & lazy setup** [`tools.py:98-137`](https://github.com/huggingface/smolagents/blob/e1249d373d58db6abc73882ee394f6bb3854c89f/src/smolagents/tools.py#L98-L137)、[`#L144-L212`](https://github.com/huggingface/smolagents/blob/e1249d373d58db6abc73882ee394f6bb3854c89f/src/smolagents/tools.py#L144-L212)、[`#L231-L256`](https://github.com/huggingface/smolagents/blob/e1249d373d58db6abc73882ee394f6bb3854c89f/src/smolagents/tools.py#L231-L256) | Tool 记录 name、description、inputs、output_type、optional output_schema；检查 forward 签名与输入一致；昂贵 setup 在第一次真实调用时执行而非注册时执行。验证 tool metadata/签名 ≠ 证明本体没有权限/副作用。 | **BORROW_PATTERN P1**：Pack/Plugin 的 typed signature、明确 tool namespace、可缓存的 lazy setup；必须有不同阶段 `declared→admitted→initialized→executed`，且 Host 对每次操作再授权。 |
| **S5 Hub/MCP 是 code trust，不只是配置** [`tools.py:517-575`](https://github.com/huggingface/smolagents/blob/e1249d373d58db6abc73882ee394f6bb3854c89f/src/smolagents/tools.py#L517-L575)、[`#L910-L1109`](https://github.com/huggingface/smolagents/blob/e1249d373d58db6abc73882ee394f6bb3854c89f/src/smolagents/tools.py#L910-L1109)、[`agents.py:1065-1113`](https://github.com/huggingface/smolagents/blob/e1249d373d58db6abc73882ee394f6bb3854c89f/src/smolagents/agents.py#L1065-L1113) | `Tool.from_hub(... trust_remote_code=False)` 默认拒绝执行远程工具，显式 true 后拉取源码；`Tool.from_code()` 通过 `exec(tool_code,module.__dict__)` 加载。MCP 转换为 Tool 也要求类似信任确认，因为其 wrapper 能向外部服务调用。**用户明确选择信任第三方代码不等于 Host 允许无限制读本机凭据**。 | **BORROW_PATTERN P0 安全边界**：安装/下载只是获取物件，必须固定可核验来源/sha + 允许的能力与独立受限执行空间；**REJECT** 未经 Owner/Host 按工具、目标、效果授权就 `exec` 未审 Repo/Hub 代码或自动安装可运行包。 |
| **S6 LocalPythonExecutor & import allowlist** [`local_python_executor.py:1561-1676`](https://github.com/huggingface/smolagents/blob/e1249d373d58db6abc73882ee394f6bb3854c89f/src/smolagents/local_python_executor.py#L1561-L1676)、[`#L1689-L1769`](https://github.com/huggingface/smolagents/blob/e1249d373d58db6abc73882ee394f6bb3854c89f/src/smolagents/local_python_executor.py#L1689-L1769)、[SECURITY.md](https://github.com/huggingface/smolagents/blob/e1249d373d58db6abc73882ee394f6bb3854c89f/SECURITY.md) | 自写 AST evaluator 限制导入和部分 builtins/while 次数，保留 Python state；上游类注释及 SECURITY.md 都**明确承认 LocalPythonExecutor 不是安全沙箱/安全边界**。授权一个 Python import 或向 static tools 注入可调用函数后，其底层对文件、网络、外部服务的效果仍需要宿主级控制。 | **REJECT 当 untrusted sandbox**。Nerelan 不可把 AST/Import allowlist 当 R3 权限/网络/秘钥隔离；如果需要代码执行，进程/container/worker 完整隔离＋Host Tool Proxy/不注入凭据，先测试后采用。 |
| **S7 超时 vs 线程结束（源码+stdlib 复核）** [`local_python_executor.py:279-321`](https://github.com/huggingface/smolagents/blob/e1249d373d58db6abc73882ee394f6bb3854c89f/src/smolagents/local_python_executor.py#L279-L321)、[`tests/test_local_python_executor.py:2175-2305`](https://github.com/huggingface/smolagents/blob/e1249d373d58db6abc73882ee394f6bb3854c89f/tests/test_local_python_executor.py#L2175-L2305) | 上游 `timeout()` 用 `with ThreadPoolExecutor(max_workers=1) as executor: future.result(timeout=...)`，捕捉 FuturesTimeoutError 并抛 ExecutionTimeoutError；**with 的 `__exit__` 调用 shutdown(wait=True)，异常传播前要等待仍在运行的 thread**。上游注释说明线程无法杀死，这与“caller will receive a TimeoutError and can continue execution”直觉容易冲突。其测试检查抛出异常，但所读测试没有 assert 真实 wall-clock 上界。我们做了不导入 SDK 的 Python 标准库同构复核：`sleep(0.35)`、`future.result(timeout=0.03)`，得到 `elapsed_until_runtime_error=0.351s`。**这是 stdlib 语义证据，不是 upstream E2E 运行证据**。 | **P0 LIVENESS REJECT**：不能用上述 thread+context 超时作为 Worker kill/safe cancel/lease handoff 证明；需独立进程/remote exec deadline、进程组 kill/reap/readback、TaskStore 旧 epoch fence，异常对外部 side effect 仍 UNKNOWN。 |
| **S8 final_answer_checks 的 assert（源码+stdlib）** [`agents.py:581-622`](https://github.com/huggingface/smolagents/blob/e1249d373d58db6abc73882ee394f6bb3854c89f/src/smolagents/agents.py#L581-L622)、[`tests/test_agents.py:664-728`](https://github.com/huggingface/smolagents/blob/e1249d373d58db6abc73882ee394f6bb3854c89f/tests/test_agents.py#L664-L728) | `_validate_final_answer` 调用 `assert check_function(final_answer,self.memory,agent=self)`；在 Python `-O` 优化模式**assert 表达式不执行**。无 SDK 安装的 stdlib 复核：`python -c 'effects=[];assert effects.append("checked") is None;print(bool(effects))'` 为 true，`python -O` 为 false。即使正常模式下检查通过，它也只是一条 Agent 内回调，不等于 GitHub exact-head CI/独立 reviewer。 | **P0 QUALITY REJECT**：绝不能用 `final_answer_checks` 替代可持久验收。Host check 必须由独立系统执行、明确失败/结果证据，不能依赖可被环境优化消除的 `assert`。 |
| **S9 Remote Executors、自动包安装和 Pickle** [`remote_executors.py:53-141`](https://github.com/huggingface/smolagents/blob/e1249d373d58db6abc73882ee394f6bb3854c89f/src/smolagents/remote_executors.py#L53-L141)、[`#L307-L333`](https://github.com/huggingface/smolagents/blob/e1249d373d58db6abc73882ee394f6bb3854c89f/src/smolagents/remote_executors.py#L307-L333)、[`#L551-L709`](https://github.com/huggingface/smolagents/blob/e1249d373d58db6abc73882ee394f6bb3854c89f/src/smolagents/remote_executors.py#L551-L709)、[`serialization.py:1-72`](https://github.com/huggingface/smolagents/blob/e1249d373d58db6abc73882ee394f6bb3854c89f/src/smolagents/serialization.py#L1-L72) | E2B/Docker/Modal/Blaxel 同 `PythonExecutor` 协议分支；Remote `send_tools` 将各 Tool `to_dict()['requirements']` 合集调用 `install_packages`，后者在运行 Kernel 里动态 `!pip install`，可能引入安装时副作用或供应链变化；基础镜像在 Dockerfile `FROM python:3.12-bullseye`，非 digest pin。SafeSerializer 默认 `allow_pickle=False` 是良好边界，但 true 后 `pickle.loads` 可执行任意代码；Docker 默认 `container_run_kwargs` 可放宽参数，源码不能证明默认断网/no host mounts。 | **BORROW_PATTERN**：统一 local/remote executor contract、JSON-safe typed output、cleanup、provider-free fixture。**REJECT** 自动安装未审核依赖、可变镜像、Pickle 在低信任端启用、把容器启动成功等同已验证隔离。 |
| **S10 Agent Memory、steps、token usage** [`memory.py:50-147`](https://github.com/huggingface/smolagents/blob/e1249d373d58db6abc73882ee394f6bb3854c89f/src/smolagents/memory.py#L50-L147)、[`agents.py:195-255`](https://github.com/huggingface/smolagents/blob/e1249d373d58db6abc73882ee394f6bb3854c89f/src/smolagents/agents.py#L195-L255)、[`#L436-L540`](https://github.com/huggingface/smolagents/blob/e1249d373d58db6abc73882ee394f6bb3854c89f/src/smolagents/agents.py#L436-L540)、[`monitoring.py:36-114`](https://github.com/huggingface/smolagents/blob/e1249d373d58db6abc73882ee394f6bb3854c89f/src/smolagents/monitoring.py#L36-L114) | 每 ActionStep 可记 `code_action/tool_calls/observations/model_output/token_usage`，规划也占额外模型开销；`RunResult.state` 仅 `success/max_steps_error`，`max_steps` 触顶后仍可能生成备用 final answer，但标记 max_steps_error；`TokenUsage` 仅统计输入/输出 token，与所有 provider attempt/账户实际费用不能等同；Memory 的可序列化记录不证明动作只执行一次或外部 SideEffect 已完成。 | **BORROW_PATTERN P1/UX**：代码执行步的可读 evidence、Model 输入/输出 token 观察、遗失结果的明确 UNKNOWN；但实际费用只能来自 Magpie request-level，GitHub acceptance 只能由 review/CI。 |

## 2. Nerelan main 真实模块对照（按已有归属，而非另建系统）

| Nerelan pinned main | 已有 / 新需求 | 复用结论 |
|---|---|---|
| [`task_runtime.py:108-117,511-576`](https://github.com/dddd2024/Nerelan/blob/3cd7e622d032a8f4f4b22d08c02277141eae97d0/reverse_agent/platform_v1/task_runtime.py#L108-L117)、[#1527](https://github.com/dddd2024/Nerelan/issues/1527) | **ALREADY_REUSED** ExecutorRouter 与中立 Executor protocol，OpenCode/Codex/Claude/Fixture 作为 Harness；不需要 smolagents 抢管 Owner 账户/Magpie/Runner。 | 可以考虑 **CodeAction harness 的 provider-free 实验适配器**，仅当有独立的被授权 Tool/Exec sandbox，评估 Code-vs-ToolCalling 成本与成功率。 |
| [`workflows/team_graph.py:82-150`](https://github.com/dddd2024/Nerelan/blob/3cd7e622d032a8f4f4b22d08c02277141eae97d0/reverse_agent/workflows/team_graph.py#L82-L150)、[`#L215-L381`](https://github.com/dddd2024/Nerelan/blob/3cd7e622d032a8f4f4b22d08c02277141eae97d0/reverse_agent/workflows/team_graph.py#L215-L381)、[#1508](https://github.com/dddd2024/Nerelan/issues/1508) | 已有 LangGraph Send fanout、Planner/Coder/Reviewer 顺序/Verifier；避免把 managed agents 作为纯函数丢掉任务签名。 | 借鉴调用接口但必须由 TaskStore 创建 Child Task/Owner scope，不允许 CodeAgent local 能用、remote 就突然失去控制的多Agent架构。 |
| [`capability_registry.py:1-123`](https://github.com/dddd2024/Nerelan/blob/3cd7e622d032a8f4f4b22d08c02277141eae97d0/reverse_agent/platform_v1/capability_registry.py#L1-L123)、[#253](https://github.com/dddd2024/Nerelan/issues/253)、[#790](https://github.com/dddd2024/Nerelan/issues/790) | Pack 仅是 metadata，不是任意第三方 Python 代码安装器；MCP/工具并非全可执行。 | Tool signatures、lazy setup、MCP→Host Proxy 适配和固定 repo revision/输出 schema 是增量；**reject** 用 `trust_remote_code=True` 替代 Owner 授权、Pack 直接 `exec` Hub code。 |
| [`control_store.py:365-410`](https://github.com/dddd2024/Nerelan/blob/3cd7e622d032a8f4f4b22d08c02277141eae97d0/reverse_agent/platform_v1/control_store.py#L365-L410)、[`goal_service.py:240-318`](https://github.com/dddd2024/Nerelan/blob/3cd7e622d032a8f4f4b22d08c02277141eae97d0/reverse_agent/platform_v1/goal_service.py#L240-L318)、[#1596](https://github.com/dddd2024/Nerelan/issues/1596)、[#1546](https://github.com/dddd2024/Nerelan/issues/1546) | TaskStore OperationReceipts/Claims/Epoch/BudgetReservations 已建，且 stalled/retry 分支需区分未完成 external operations。 | **最高价值负例**是 S7：失去响应和超时错误不等于 Worker 停止/工作副作用取消；先做到 Process Kill/Reap+readback+fence+UNKNOWN，再谈 CodeAgent 自动恢复。 |
| [`run_read_model.py:571-611`](https://github.com/dddd2024/Nerelan/blob/3cd7e622d032a8f4f4b22d08c02277141eae97d0/reverse_agent/platform_v1/run_read_model.py#L571-L611)、[#280](https://github.com/dddd2024/Nerelan/issues/280) | 区分 `USAGE_UNKNOWN` 和 `provider_request_receipt: UNVERIFIED`，不把任务启动当计费请求。 | 借鉴步骤级 code digest/action outcome，标记 Usage 可视度而不是“成功时便宜了”，用 Magpie 实际 provider-request cost。 |
| [`SOURCE_OF_TRUTH_MATRIX.md:61-69`](https://github.com/dddd2024/Nerelan/blob/3cd7e622d032a8f4f4b22d08c02277141eae97d0/docs/architecture/SOURCE_OF_TRUTH_MATRIX.md#L61-L69)、[#299](https://github.com/dddd2024/Nerelan/issues/299)、[#303](https://github.com/dddd2024/Nerelan/issues/303) | TaskStore task/lease/Owner、Magpie provider billing/secret 和 GitHub CI/merge 各有唯一真相。 | LocalPythonExecutor 明言不是 sandbox，remote 包安装、Pickle、container 参数都是独立的 trust boundary。Host 要验证每个实际 Tool 调用及所需账户能力，禁止 worker 直接持有 gateway 秘钥。 |

### 用户视角的实际收益假说（不是已验证结论）

在大量 Tool 分散任务里，用户的需求不是切换一个 Agent 品牌，而是 **更快完成任务、更少消耗模型调用、更少人工介入，而且能追溯每一步真实操作/验证**。当 `CodeAction` 一次模型生成多次只读/纯计算工具调用时，可能减少 LLM round trips；但若它不能为每个外部 effect 提供独立 Owner receipt，任何初期 Token 节省都可能被恢复重复、审查、错误带来的更高成本抵消。先在可验证的只读 Tool 集合上测量、再按 effect class 逐步开放。

## 3. 八组实验门（除 stdlib microtests 外均未执行）

1. **M1 / CodeAction vs JSON ToolCalling**（#1527）：同 30–100 组 Task/同模型/同工具策略/独立验收，纯计算、只读 Repo、受限写入三类；测每 accepted Goal **所有 provider 请求**、总实际花费、模型轮数、执行时延、调试重试数和证据齐全率。若模型编写代码带来额外错误或测试负担，使完成成本不降，则 NO-GO。仅一个选择值不宣称模型原理上的费用收益。
2. **M2 / Thread timeout + effects**（#1596）：给动作绑定 `timeout=0.1s`，模拟 Worker 执行 1s 与永不返回；必须能在不等待不可信线程完成的情况下恢复调度器，并证明进程组停止/旧 Epoch 输出无法再提交；对未知 SideEffect 必须 PARK 直到 readback。上游标准库同构复核 0.03/0.35 得 0.351s；**没有运行 smolagents upstream 的 pytest**。
3. **M3 / Final-answer integrity under -O**（#1508/#1527）：正常/优化解释器分别执行拒绝性检查；不得因 `python -O` 跳过核心验收； independent GitHub exact-head CI/reviewer 必须仍拒绝失败，即使 Agent 自报 success。stdlib 复核：普通 Python 执行 assert expression，`-O` 跳过；**不是上游集成测试**。
4. **M4 / Remote managed-agent vs local**（#1508/#299）：同一 Manager 委派给 Child、分别 local 和 remote；remote 官方源码直接 raise，不能 silent downgrade local。Nerelan 必须让 child 在同样授权/安全环境创建 TaskStore child ID/epoch，而非借 Agent callable 继承父进程全部权限。
5. **M5 / Tool/MCP trust and dependency installation**（#253/#790/#303）：无信任 Hub tool、已审且 pin revision、MCP wrapper、动态工具包 `requirements`、import-time effects、`trust_remote_code=True` 的不同 Caller/Owner；只有 manifest/Owner批准/沙箱前提同时满足才可安装/调用，不能 Agent 自报 trusted。禁止默认处理含真实用户凭据的样本。
6. **M6 / Serialization + container hardening**（#299）：`allow_pickle=False`，强行载入 `pickle:` 字节；应拒绝。镜像 digest、显式 egress、mount、credentials、kernel gateway port binding、Windows host/container 管理需证明，而不是“Docker 窗口正常”。
7. **M7 / Parallel actions and replay**（#1508/#1546）：同 ToolCall ID、不同 ToolCall ID、写同一 Git worktree、跨 Agent Target、超时后迟到成功；每个 effect 先有 TaskStore durable intent/Owner claim+exact target，保持同 ID 不重复副作用；收到异常/最后答案不当 acceptance。
8. **M8 / Prompt/token memory vs security/audit**（#296/#280）：`AgentMemory` long code+logs、summary_mode、步骤数上限后的 final answer 生成；测 Token+真实 Magpie 费用、trace truncation、错误记忆覆盖/遗失以及 GUI 的“code ran/verified/unknown”区别。不能从 Memory 有 token numbers 推断真实 provider billing。

**Go/No-Go**：M2 不限时返回/旧线程还在产生 SideEffect、M3 优化模式跳验收、M4 不受信地 local 降级、M5 不受信 Hub/MCP 代码或自动 pip、M6 pickled RCE/容器凭证泄露、M7 重复外部 SideEffect 即 **NO-GO**。M1 没有真实成功成本改善也 **NO-GO**。这些是后续代码实施 gate，非已通过的测试。

## 4. 可复核 stdlib 行为微实验与证据等级

两个微实验都只是 Python 标准库测试，不导入/安装 smolagents，不读取用户环境或密钥，验证的是**上游源码使用的语言/执行器语义**：

**E1 — Timeout Context Exit**
```python
from concurrent.futures import ThreadPoolExecutor, TimeoutError
from time import perf_counter, sleep
start = perf_counter()
try:
    with ThreadPoolExecutor(max_workers=1) as pool:
        future = pool.submit(sleep, 0.35)
        try:
            future.result(timeout=0.03)
        except TimeoutError:
            raise RuntimeError("timeout")
except RuntimeError:
    print(round(perf_counter() - start, 3))
# observed: 0.351 seconds; this reflects wait=True on context exit, not 0.03-second prompt handoff
```

**E2 — Assertions and Python optimization**
```text
python -c 'effects=[];assert effects.append("checked") is None;print(bool(effects))' -> True
python -O -c 'effects=[];assert effects.append("checked") is None;print(bool(effects))' -> False
```

两次都是无模型费用、无上游实际运行的独立 minimal reproducible language semantics checks。没有证明所有 smolagents 安装/版本在所有系统上的时序，也不将安全设计意见包装成已被利用漏洞或 CVE。上游已有 [timeout pytest tests](https://github.com/huggingface/smolagents/blob/e1249d373d58db6abc73882ee394f6bb3854c89f/tests/test_local_python_executor.py#L2175-L2305) 与 [final-check tests](https://github.com/huggingface/smolagents/blob/e1249d373d58db6abc73882ee394f6bb3854c89f/tests/test_agents.py#L664-L728)，**没有在这轮执行它们**。维护者可用独立隔离环境追加真实产品回归。

## 5. 最终裁定 / 不允许覆盖的权威

- **ALREADY_REUSED**：ExecutorRouter、LangGraph Send、TaskStore task/Goal 及 claims/epochs、Host receipt/grant、Magpie per-request 费用与账户、GitHub exact-head CI/Review。
- **BORROW_PATTERN**：CodeAction 减少多步模型交互的 **可测假说**、Tool contracts+lazy setup、Managed-agent callable 的表面 API、local/remote Executor typed interface、safe serializer default、Step/Code/Tool/Observation provenance。
- **REJECT**：LocalPythonExecutor 作为安全隔离；基于 ThreadPoolExecutor 的超时作为 Worker kill；`assert final_answer_checks` 替代独立验收；remote managed-agent 支持的虚假宣称；未审核来源 `trust_remote_code` / MCP wrapper 视为宿主授权；Remote auto-pip 安装与未经检查的 pickle；token usage 当真实成本；把 CodeAgent 作为第二执行/任务权威。
- **DIRECT_REUSE**：**not approved**。上游 Apache-2.0 允许许可证下使用，但没有证明在 Windows、Magpie、Host scope 或真实任务成本质量下的净收益；本轮没有复制上游代码到 Nerelan。

**治理状态**：查重完成、固定 SHA/许可证、对应最新 Nerelan main、阅读关键真实代码/测试/安全说明，执行 2 个标准库语义微实验；**无 SDK 安装、无 pytest、无服务商调用、无 Windows/remote sandbox E2E、无付费 benchmark、无实现改动**。仅允许 docs-only Draft PR 归档；未经 exact-head CI 和独立 review 不合入 main。


## 6. 交接边界与阻塞项

研究仅支持 Existing #1527 做 Cost/Quality/Windows 工具隔离实验的 design options，不允许通过本 docs-only Draft PR 新增任意 Python Agent runtime、联网下载 Hub/MCP Tool、启用 Pickle、扩大 import 权限、改变 Owner grant 或 Magpie 账户读写路径。Q/A 中的两个 Python 标准库示例属于可复核的**语言语义 microtests**，不应当被算作 `pytest` 或 upstream SDK integration PASS。没有 exact-head CI/独立 reviewer acceptance/merge 证明；静态审计尚不能给 smolagents 真实产品收益背书。
