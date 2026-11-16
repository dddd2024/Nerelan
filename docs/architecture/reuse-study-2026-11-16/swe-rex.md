# SWE-ReX — 源码级专项研究（2026-11-16）

> **Research Issue**: [#1578](https://github.com/dddd2024/Nerelan/issues/1578) · **总台账**: [#1576](https://github.com/dddd2024/Nerelan/issues/1576) · **Status**: STATIC_SOURCE_REVIEW / NOT_TESTED / NOT_IMPLEMENTED
>
> **Documentation-only / No runtime authority.** 本文是静态代码审阅与 Nerelan 设计对照，不是上游或 Nerelan 的运行测试。主分支 CI、独立评审及集成收益均未验证。实施需沿用原有 Owner Issue 及治理门槛。

# SWE-ReX 源码深研：统一命令执行环境，而非替换 Agent 或协调器

> **研究日期**：2026-11-16 · **状态**：STATIC_SOURCE_REVIEW / NOT_INSTALLED / NOT_BENCHMARKED / DOCS_ONLY · **行动授权**：NONE
>
> **唯一研究对象**：[SWE-agent/SWE-ReX](https://github.com/SWE-agent/SWE-ReX)，MIT（含许可证保留要求），固定上游 `5c995c365dfb1fd5bc56fda688be5d8538f9931f`（上游提交 2026-03-02）。Nerelan 比对基线 `a7b6277772aefef33138921f357c459f259e718b`（2026-11-16）。

## 0. 去重证据 / 不创重复实施 Owner

检查 [研究总索引 #1576](https://github.com/dddd2024/Nerelan/issues/1576)（11/15 横向五领域、六份静态专项、19 个历史跨对话项目）、仓库 Issue 标题和正文 `SWE-ReX`/相关命名检索、main 的 `C-runtimes.md` / `B-durable.md` 以及既有 `#1527` 多 Harness、`#299` 沙箱、`#1191` 跨重启、`#1546` 持久性、`#296` 工作区、`#1342/#1531` 用量。未发现同名独立源码专项；邻接主题既有 Owner，不重复建立开发 Issue。本次增量只在**通用 Command/Interactive Session × Deployment 解耦、能力合同、请求幂等边界、远程文件转移证据**。

## 1. 上游源码证据

1. [`src/swerex/runtime/abstract.py`](https://github.com/SWE-agent/SWE-ReX/blob/5c995c365dfb1fd5bc56fda688be5d8538f9931f/src/swerex/runtime/abstract.py)：`AbstractRuntime` 将 `execute(Command)`（一次性命令）、`create_session/run_in_session/close_session`（可交互 Bash 会话）及 `read_file/write_file/upload/is_alive/close` 放入一个后端无关协议。会话具名，可区别结束状态、超时、exit code；**并不是** Agent/MCP/Plugin 调度。
2. [`src/swerex/deployment/abstract.py`](https://github.com/SWE-agent/SWE-ReX/blob/5c995c365dfb1fd5bc56fda688be5d8538f9931f/src/swerex/deployment/abstract.py) 和 [`deployment/config.py`](https://github.com/SWE-agent/SWE-ReX/blob/5c995c365dfb1fd5bc56fda688be5d8538f9931f/src/swerex/deployment/config.py)：`AbstractDeployment` 定义生命周期 `start/stop/is_alive/runtime`，配置 discriminated 类型选择 local、Docker/Podman、Modal、Fargate、remote、Daytona、dummy。不同后端**不保证相同隔离/持久性**。
3. [`runtime/local.py`](https://github.com/SWE-agent/SWE-ReX/blob/5c995c365dfb1fd5bc56fda688be5d8538f9931f/src/swerex/runtime/local.py)：`BashSession` 基于 pexpect，支持交互命令/中断和 exit-code 提取；`LocalRuntime.execute` 调用 `subprocess.run`，`read_file/write_file` 直接访问传入路径。local 不等于 sandbox；没有 Nerelan 所需的 host policy、路径 allowlist、持久收据。
4. [`runtime/remote.py`](https://github.com/SWE-agent/SWE-ReX/blob/5c995c365dfb1fd5bc56fda688be5d8538f9931f/src/swerex/runtime/remote.py) 与 [`server.py`](https://github.com/SWE-agent/SWE-ReX/blob/5c995c365dfb1fd5bc56fda688be5d8538f9931f/src/swerex/server.py)：请求附 `X-Request-ID`，远端仅缓存**最后一次**请求的响应；`ResponseManager` 明确承认多并发客户端不能保证幂等。RemoteRuntime `_request(..., num_retries=0)` 默认无重试；同一调用的 request id 即使重试也不构成跨崩溃持久 exactly-once。上传经 HTTP ZIP/FormData 和直接目标路径；server 没有 root-bound path policy 或冻结哈希证明。不可作为 Nerelan 任务重试/副作用核销/安全工件回传直接实现。
5. [`deployment/docker.py`](https://github.com/SWE-agent/SWE-ReX/blob/5c995c365dfb1fd5bc56fda688be5d8538f9931f/src/swerex/deployment/docker.py)：镜像选择、port token、容器启动/心跳/停止清理；`docker_args` 可传任意参数，因此容器运行不能自动推出强隔离。CLI 首先建立 Runtime，再执行命令，不包含 TaskStore/Owner policy/验收。
6. [`deployment/hooks/abstract.py`](https://github.com/SWE-agent/SWE-ReX/blob/5c995c365dfb1fd5bc56fda688be5d8538f9931f/src/swerex/deployment/hooks/abstract.py)：hook 只是 deployment 状态回调，**不是 Nerelan 的 Tool/Pack 插件生命周期**。上游仓库 MIT；本轮不复制源码。

## 2. 与 Nerelan main 的真实对照

- **已有（ALREADY_REUSED / KEEP）**：[`task_runtime.py:ExecutorRouter`](https://github.com/dddd2024/Nerelan/blob/a7b6277772aefef33138921f357c459f259e718b/reverse_agent/platform_v1/task_runtime.py)、[`task_execution.py:_dispatch_executor`](https://github.com/dddd2024/Nerelan/blob/a7b6277772aefef33138921f357c459f259e718b/reverse_agent/platform_v1/task_execution.py) 已抽象 `executor_kind` 并把结果接入验证与证据；[`remote_jobs.py`](https://github.com/dddd2024/Nerelan/blob/a7b6277772aefef33138921f357c459f259e718b/reverse_agent/platform_v1/remote_jobs.py) 已有 SSH Broker 的持久 Job ID/请求哈希、独占远端标记、进程身份、FAILED/LOST 语义、冻结输出与 SHA256 manifest（[既有文档](https://github.com/dddd2024/Nerelan/blob/a7b6277772aefef33138921f357c459f259e718b/docs/remote-jobs.md)）。不能换成 SWE-ReX 轻量 HTTP server 后丢失上述保障。
- **可借鉴设计（BORROW_PATTERN）**：在 `#1527` 现有 Harness Adapter 下增加独立的 `ExecutionEnvironment` 描述（一次命令 vs 交互会话、文件读写、后台任务、Docker/Podman/SSH 环境），明确 `probe/prepare/execute/interrupt/collect/finalize` 责任；让同一 Agent Harness 适配多个环境、反之亦然。仅提接口方案，未实现/未声称 Nerelan 缺少全部这些函数。
- **有条件直接复用（DIRECT_REUSE_CANDIDATE, NOT APPROVED）**：若真实调试 / 交互 REPL / 并行 benchmark 证明现有远程 Broker 的单次 Job 模型无法满足，**可以在受控容器中评估** SWE-ReX 作为低信任命令传输客户端；前面必须有 Nerelan 自己的 Policy、Sandbox capability、Durable TaskStore 和 Artifact receipt。不可默认启用本地 HostRuntime。
- **拒绝（REJECT）**：不移植 SWE-ReX server 的 last-response idempotency、无根目录约束上传、宽泛 `docker_args` 权限、未经证实的持久性与隔离；不重建 Gateway、MCP、Plugin Manager、TaskStore、审查器或成本账本。

## 3. 模块行动矩阵（产品/开发并重）

| 模块 | 决策 | 对 Nerelan 的用户收益 | 唯一归属 |
|---|---|---|---|
| Agent×Executor×Environment | BORROW_PATTERN | 同一 Harness 不被固定在单个环境；启动前显示不支持原因 | #1527 |
| 交互 shell / 命令输送 | CONDITIONAL_DIRECT_REUSE | 复杂调试长会话可能减少环境切换，但须先实证 | #1527, #299 |
| Workspace / 回传 | BORROW_PATTERN only | 用户看到远端结果已冻结、能否安全继续后续任务 | #296, #1191 |
| Sandbox / 权限 | REJECT as security authority | 保证不会把工作区误标为 OS 级隔离 | #299, #303 |
| Resume / retry / idempotency | KEEP Nerelan | 防重复副作用与静默丢任务 | #1191, #1546 |
| Plugin/Pack/MCP | NO_INCREMENT | SWE-ReX 不提供可复用插件权限模型 | #253, #789, #790 |
| Usage / cost | NO_INCREMENT | SWE-ReX 不提供 Magpie 请求级归因或质量成本调度 | #1342, #1531, #1267 |

## 4. 最小可证伪实验（全部尚未执行）

**E1 Provider-free 接口模拟**：一个 fake Harness 调用多个 fake environment；固定 task payload，创建独立 session A/B、打断/重建、输出含 exit code/有限长度与 UTF8，确认 capability rejection 可读；不要求立刻接真 Agent。

**E2 重试/故障注入**：同一 `X-Request-ID` 并发发送、一次结果到达但响应丢失、服务端重启后重发，记录远端副作用次数。验收：对需要 exactly-once 的操作必须仅执行一次或变成 `UNKNOWN/LOST` 需人工核销，不能静默重试；**预计上游 ResponseManager 无法独立通过，不把此当 Nerelan 已测结果**。

**E3 文件与沙箱边界**：目标路径越界、符号链接、权限、容器特权参数、无网络/只允许有限网络、凭证不可见、上传后被修改、下载中断；必要隔离缺失则 admission 拒绝，不能按“在 Docker 里”默认为安全。

**E4 成本/实用性验证**：与 Nerelan 现有 `remote_jobs.py` 进行**同任务**（单次 batch、交互调试、30 个并行小任务）对照：首次启动、任务成功/验收率、p95 时延、内存/网络、环境清理、失败重试、输出证据完整性。若环境切换未降低复杂度、未覆盖现有能力缺口、或可靠性下降，**NO-GO**。

## 5. 裁定与治理

**SELECTIVE_DESIGN_REUSE / PRIORITY P1**：把 Environment（命令承载环境）与 Harness（Agent 的规划、工具循环、模型接入）分层，是本次最有价值的增量。先通过 #1527 和 #299 的最小假客户端合同门槛，再考虑是否需要安装 SWE-ReX；实际安装/运行不受本 Issue 授权。无付费 API、远程服务器、第三方二进制执行，也无 CI / 独立复审通过的宣称。

本 Issue 与 #1576 互链；R1 Docs-only 研究 PR 另行登记。
