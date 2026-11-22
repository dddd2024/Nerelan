# Kubernetes SIG Apps Agent Sandbox 源码级研究：沙箱强度、Claim 归属、Warm Pool、Router 认证和资源回收

> **时间：** 2026-11-16  
> **状态：** `STATIC_SOURCE_REVIEW / NOT_INSTALLED / NOT_TESTED / NO_IMPLEMENTATION_AUTHORITY`  
> **上游仓库：** [kubernetes-sigs/agent-sandbox](https://github.com/kubernetes-sigs/agent-sandbox)，冻结 commit [`454d3353e5c2`](https://github.com/kubernetes-sigs/agent-sandbox/commit/454d3353e5c26c561dd6de389f32f7f285030e38)；[Apache-2.0](https://github.com/kubernetes-sigs/agent-sandbox/blob/454d3353e5c26c561dd6de389f32f7f285030e38/LICENSE)。  
> **Nerelan 比较基线：** main [`a7b6277772ae`](https://github.com/dddd2024/Nerelan/commit/a7b6277772aefef33138921f357c459f259e718b)。  
> **研究留痕：** [#1569](https://github.com/dddd2024/Nerelan/issues/1569)；正式 Sandbox 能力规划唯一 Owner 仍是 [#299](https://github.com/dddd2024/Nerelan/issues/299)。  
> **验证范围：** 仅阅读上游 Go 控制器、CRD、Python SDK、Router Auth、Threat Model、示例、官方文档及 Nerelan 的源码与 Issues。**没有**部署 Kubernetes、运行 Sandbox、验证性能/逃逸隔离、安装 SDK、调用模型或在生产环境更改权限。

## 0. 选择项目之前的查重

- 读取最新研究索引：目前统一 `docs/architecture/REUSE_RESEARCH_INDEX.md` 尚在等待的研究分支（Paperclip PR #1563 → Mastra #1565 → Composio #1568），未出现在当前 main。
- 核查 `docs/architecture/reuse-study-2026-11-15/`、`COMPETITIVE_LANDSCAPE.md`、2026-11-16 创建的 Issues/PR、文件搜索和 Issues/PR 搜索：没有找到针对 `SandboxClaim`、`SandboxWarmPool`、`SandboxTemplate` 或 Router 身份验证的 **Kubernetes SIG Apps Agent Sandbox 专项逐源码研究**。
- **存在已研究内容：** [#299](https://github.com/dddd2024/Nerelan/issues/299) 已把该项目列为可选复用后端，且已提出 Host/Workspace/Sandbox 三重边界、能力契约、安全要求、Windows local-first、不应自建容器引擎。因此本研究不再把“需要沙箱”“沙箱能力描述”包装成新发明；仅补上项目特有的真实实现细节和可证伪风险。
- 筛选时看过 Daytona，但其公开原仓库 [README](https://github.com/daytonaio/daytona/blob/main/README.md) 明确宣布 2026-06 后核心代码转私有并停止开源维护，GitHub 于 2026-10-03 归档；不应把旧公开仓库当成持续维护的生产基础。仅是排除理由，本轮**不深拆 Daytona**。
- **增量范围：** Kubernetes Sandbox (desired/observed status)、Claim + 模板 + Warm Pool、Router 安全与 sandboxd、网络策略更新、Python SDK 领取/恢复/回收、Warm Pool 的隐藏成本。

## 1. 上游定位及能复用什么

上游提供的是 Kubernetes 原生、状态持久的单实例工作负载抽象，核心 CRD `Sandbox`，额外的 `SandboxTemplate`、`SandboxWarmPool`、`SandboxClaim` 供模板化管理和预热领取。

| 对象 | 源码位置 | 真正含义 | Nerelan 借鉴 |
|---|---|---|---|
| `Sandbox` | [`api/v1beta1/sandbox_types.go`](https://github.com/kubernetes-sigs/agent-sandbox/blob/454d3353e5c26c561dd6de389f32f7f285030e38/api/v1beta1/sandbox_types.go) | 期望的 Pod、Service、PVC 生命周期 + 观测状态 | Task 外部执行环境身份和健康回执 |
| `SandboxTemplate` | [`extensions/api/v1beta1/sandboxtemplate_types.go`](https://github.com/kubernetes-sigs/agent-sandbox/blob/454d3353e5c26c561dd6de389f32f7f285030e38/extensions/api/v1beta1/sandboxtemplate_types.go) | 管理员控制的 Pod 配置、网络策略、注入约束 | Policy 编译后的冻结 Sandbox Profile |
| `SandboxWarmPool` | [`sandboxwarmpool_controller.go`](https://github.com/kubernetes-sigs/agent-sandbox/blob/454d3353e5c26c561dd6de389f32f7f285030e38/extensions/controllers/sandboxwarmpool_controller.go) | 预创建空闲沙箱降低领取延迟 | 有证据时才考虑预热，不必默认存在 |
| `SandboxClaim` | [`sandboxclaim_controller.go`](https://github.com/kubernetes-sigs/agent-sandbox/blob/454d3353e5c26c561dd6de389f32f7f285030e38/extensions/controllers/sandboxclaim_controller.go) | 用户侧领取/绑定，状态反映 Sandbox | Attempt → Sandbox UID 的证明关系 |
| Python SDK | [`sandbox_client.py`](https://github.com/kubernetes-sigs/agent-sandbox/blob/454d3353e5c26c561dd6de389f32f7f285030e38/clients/python/agentic-sandbox-client/k8s_agent_sandbox/sandbox_client.py) | 领取、等待 Ready、接入、关闭/删除 | 可选远端执行环境适配接口 |
| Router / sandboxd | [`sandbox-router/authz/authorizer.go`](https://github.com/kubernetes-sigs/agent-sandbox/blob/454d3353e5c26c561dd6de389f32f7f285030e38/sandbox-router/authz/authorizer.go), [`auth.go`](https://github.com/kubernetes-sigs/agent-sandbox/blob/454d3353e5c26c561dd6de389f32f7f285030e38/packages/sandboxd/pkg/server/auth.go) | HTTP 代理的目标访问授权 + Pod 内命令服务 | 宿主 broker 的身份/命令授权边界 |

**根本边界：** 它本身是 Sandbox *Orchestrator*，**不是** gVisor、Kata、VM 或内核级安全隔离的替代品；是否真的强隔离取决于 Pod RuntimeClass、Kubernetes 节点、CNI、ServiceAccount、RBAC、NetworkPolicy 和 admission。不能因为 `Sandbox` CRD Ready 就给 Nerelan 任务标记“强安全”。

## 2. 模块 A：期望 Running 与实际 Ready 是两件事（P1）

源码：[`api/v1beta1/sandbox_types.go`](https://github.com/kubernetes-sigs/agent-sandbox/blob/454d3353e5c26c561dd6de389f32f7f285030e38/api/v1beta1/sandbox_types.go)、[`controllers/sandbox_controller.go`](https://github.com/kubernetes-sigs/agent-sandbox/blob/454d3353e5c26c561dd6de389f32f7f285030e38/controllers/sandbox_controller.go)。

- `spec.operatingMode=Running` 是管理员/调用方要求控制器保持 Pod 存在的**目标状态**，不能证明 Pod 已经可用。
- `Ready=True` 只有对应 Pod 处于 Running、满足 Pod Ready、有 Pod IP 且必要 Service 就绪才能成立。`Finished`、`Suspended`、`PodScheduled` 和 `observedGeneration` 具有独立含义。
- 如果有多个 Pod 被同一 Sandbox UID 声明控制，Controller 返回 `MultiplePods` 异常状态，不擅自挑一个继续；这种“歧义不能当成功”值得借鉴。
- SDK 的 `wait_for_sandbox_ready()` 等待 Condition；旧 Condition 可能来自旧 Generation，必须验证观测代数与 UID。

**Nerelan 不应做：** 把 `SandboxReady` 当作 Task 成功、Verifier 成功或模型完成。应使用：

`SANDBOX_ALLOCATED -> SANDBOX_READY -> EXECUTOR_RUNNING -> ARTIFACT_RECEIVED -> VALIDATED -> SANDBOX_CLEANUP_VERIFIED`

这是**建议的外部环境生命周期事件序列**，不是建议再造一套 TaskStore 主状态机。原 TaskStore/ExecutorResult 和独立验收仍为权威；未确认环境 Ready 就不能进入执行。

## 3. 模块 B：Claim 归属和复用的 UID 防 ABA（P1）

源码：
- [`clients/python/.../sandbox_client.py`](https://github.com/kubernetes-sigs/agent-sandbox/blob/454d3353e5c26c561dd6de389f32f7f285030e38/clients/python/agentic-sandbox-client/k8s_agent_sandbox/sandbox_client.py)
- [`clients/python/.../claim_adoption.py`](https://github.com/kubernetes-sigs/agent-sandbox/blob/454d3353e5c26c561dd6de389f32f7f285030e38/clients/python/agentic-sandbox-client/k8s_agent_sandbox/claim_adoption.py)
- [`extensions/controllers/sandboxclaim_controller.go`](https://github.com/kubernetes-sigs/agent-sandbox/blob/454d3353e5c26c561dd6de389f32f7f285030e38/extensions/controllers/sandboxclaim_controller.go)

源码中 Python SDK 支持传入 `claim_name`、`adopt_existing`。当创建遇到真正 `AlreadyExists` 的 409 时，会读取旧 Claim，检查未在删除中、对应正确 Warm Pool，并确认具有 UID 与 resourceVersion；后续 Watch 可带 `expected_uid` 避免同名资源被删除再创建后的身份混淆。

但 `validate_claim_for_adoption` 只负责 K8s Claim / WarmPool 的一致性，**不读取 Nerelan Task/Owner 授权，也不证明某位最终用户拥有该沙箱**；那是上层 RBAC/宿主系统职责。

如果 Nerelan 将来接此后端，建议一次 Attempt 的 Sandbox Lease 冻结至少：

`{task_id, attempt_id, owner_authorization_digest, backend_id, namespace, claim_name, claim_uid, sandbox_uid, template_digest, policy_digest, required_observed_generation}`。

不能只依赖可重用的 Claim 名称或 Pod IP；对恢复中的 `adopt_existing` 必须由可信宿主重新校验 Task/Owner/Attempt 关系、UID、授权有效性和原操作是否已经派发。Name collision 不应默默复用另一个 Task 的工作区。

额外发现：Claim Reconciler 对刚创建资源还未进入 Informer Cache 的情况，有 `200ms` 到 `5s` 的有界退避；Warm Candidate 默认只等约 `2s` 的 IP 观测就可能走冷启动。这些是运行时服务质量参数，**不能从“Claim 返回”推导已启动快**。

## 4. 模块 C：Warm Pool 的隐藏冷启动与经济性（P1/P2）

源码：
- [`extensions/api/v1beta1/sandboxtemplate_types.go`](https://github.com/kubernetes-sigs/agent-sandbox/blob/454d3353e5c26c561dd6de389f32f7f285030e38/extensions/api/v1beta1/sandboxtemplate_types.go)
- [`extensions/api/v1beta1/sandboxclaim_types.go`](https://github.com/kubernetes-sigs/agent-sandbox/blob/454d3353e5c26c561dd6de389f32f7f285030e38/extensions/api/v1beta1/sandboxclaim_types.go)
- [`docs/performance-tuning.md`](https://github.com/kubernetes-sigs/agent-sandbox/blob/454d3353e5c26c561dd6de389f32f7f285030e38/docs/performance-tuning.md)

关键差异：Warm Pool 预先创建的 Pod **不是任意 Claim 都可采用**。

- Claim 注入 `spec.env` 时，**强制冷启动**：不能将 env 动态注入已经运行的预热 Pod。
- Claim 提供 `spec.volumeClaimTemplates` 时，同样强制冷启动。
- `spec.additionalPodMetadata` 有单独的允许标签/注释规则，在满足限制时可在领取后贴入，不等价于注入环境变量。
- 为了每任务传入密钥或动态卷而默认采用 Warm Pool，可能一边付预热占用成本、一边每次仍付冷启动成本。
- Pool Reconciler 有受缓存写入确认约束的 refill 机制；单池补充和 claim burst 的性能不是一个指标，不能把文档的 Kubernetes 压测吞吐量当成单台 Windows 机器的 Nerelan 性能。

Nerelan 核心目标是**每个独立验收成功任务的真实总成本**；应该把沙箱预算写成（假设未来实际使用此后端）：

`Cost = PoolIdleResource + ColdStart/Provisioning + ActiveCompute + Network/Storage + FailedAttempts + Recovery + ModelCost + Validation`

纯 Benchmark 比较：在无任何云服务/密钥条件下使用仿真后端验证 `warm_eligible` 判定；等有现成被批准的 K8s 集群时才测真实冷/热启动和闲置成本；若容量小、长任务多或每 Task 有动态环境，则先不设置 Warm Pool。

## 5. 模块 D：模板安全默认值不是 Nerelan 的安全要求（P0）

源码：
- [`extensions/api/v1beta1/sandboxtemplate_types.go`](https://github.com/kubernetes-sigs/agent-sandbox/blob/454d3353e5c26c561dd6de389f32f7f285030e38/extensions/api/v1beta1/sandboxtemplate_types.go)
- [`extensions/controllers/sandboxtemplate_controller.go`](https://github.com/kubernetes-sigs/agent-sandbox/blob/454d3353e5c26c561dd6de389f32f7f285030e38/extensions/controllers/sandboxtemplate_controller.go)
- [`docs/security/threat_model.md`](https://github.com/kubernetes-sigs/agent-sandbox/blob/454d3353e5c26c561dd6de389f32f7f285030e38/docs/security/threat_model.md)
- [`examples/quickstart/README.md`](https://github.com/kubernetes-sigs/agent-sandbox/blob/454d3353e5c26c561dd6de389f32f7f285030e38/examples/quickstart/README.md)

1. **不是强隔离默认开启：** quickstart 的 KIND 路径明确没有配置 gVisor/Kata。上游 README 自述底层隔离依赖 RuntimeClass。K8s Pod 无法自动等价于 “强沙箱”。
2. **模板的 Secure Default 会允许公网：** `NetworkPolicyManagement=Managed` 默认建立一份 **按 SandboxTemplate 共享**的策略。入站通常只允许 Sandbox Router，出站默认允许公网、拦截部分内部网段/云元数据地址。对 Nerelan 的 `network_mode=NONE` 或固定的联网白名单任务，默认配置**不满足要求**，需要额外管理的精确网络规则和实际 CNI 测试。Kubernetes L3/L4 NetworkPolicy 也不等于 HTTP 域名/路径级出站控制。
3. **共享 Policy 会作用于所有旧任务：** 模板更新会修改同一个模板共享的 NetworkPolicy，并影响已运行/未来的沙箱。Nerelan 若冻结了某 Attempt 的策略摘要，模板更新后需重新做有效权限检查或使用不可变模板/版本隔离，不能再声称原环境不变。
4. **没有“自动隔离 Node/RBAC/Secret”：** 必须限制 ServiceAccount Token、hostPath、privileged、Docker Socket、容器系统能力、资源 limits、横向网络访问。Template 默认 `envVarsInjectionPolicy=Disallowed` 是合理方向；不应开启 `Overrides` 允许 Claim 覆盖受信任环境的关键变量。

**具体文档漂移：** [`examples/warmpool-quickstart/secure-sandboxtemplate.yaml`](https://github.com/kubernetes-sigs/agent-sandbox/blob/454d3353e5c26c561dd6de389f32f7f285030e38/examples/warmpool-quickstart/secure-sandboxtemplate.yaml) 文件顶部注释写“为每个 Sandbox 创建独立 NetworkPolicy”，但 [Template Controller](https://github.com/kubernetes-sigs/agent-sandbox/blob/454d3353e5c26c561dd6de389f32f7f285030e38/extensions/controllers/sandboxtemplate_controller.go) 实际按 `<template-name>-network-policy` 创建/更新 **每模板一份**；[更详细的官方网络管理说明](https://github.com/kubernetes-sigs/agent-sandbox/blob/454d3353e5c26c561dd6de389f32f7f285030e38/examples/policy/network-policy-management/README.md) 也确认是模板共享。不能仅凭老的示例注释决定安全性质。

## 6. 模块 E：Router 权限必须单独启用，不能直接“有沙箱即安全”（P0）

源码：
- [`sandbox-router/authz/authorizer.go`](https://github.com/kubernetes-sigs/agent-sandbox/blob/454d3353e5c26c561dd6de389f32f7f285030e38/sandbox-router/authz/authorizer.go)
- [`sandbox-router/authz/scopedtoken.go`](https://github.com/kubernetes-sigs/agent-sandbox/blob/454d3353e5c26c561dd6de389f32f7f285030e38/sandbox-router/authz/scopedtoken.go)
- [`packages/sandboxd/pkg/server/auth.go`](https://github.com/kubernetes-sigs/agent-sandbox/blob/454d3353e5c26c561dd6de389f32f7f285030e38/packages/sandboxd/pkg/server/auth.go)
- [`sandbox-router/README.md`](https://github.com/kubernetes-sigs/agent-sandbox/blob/454d3353e5c26c561dd6de389f32f7f285030e38/sandbox-router/README.md)

上游 Router 的 `Authorizer` 是 per-request 准入接口，`AuthorizationTarget` 包含 `namespace, sandbox name/UID, port, HTTP method, path` 并对方法/路径做规范化。**其默认实例 `AllowAll` 不检查用户身份**：官方注释把它定位于开发集群或在 Router 前已有授权网关的部署。

因此 Nerelan 使用 Router 时不能把 API Key 或 Pod 命名当作跨任务访问控制。至少需要：
- Router 只能通过可信入口访问；
- TokenReview/受限 Token/经审核的网关强制请求级身份、目标 Sandbox UID/Namespace、端口和方法绑定；
- 不允许“凭任意用户提供的 X-Sandbox-ID 或 Pod-IP 就得到任务 Shell”；需限制客户端能指定的路由覆盖；
- 保留审计时的授权失败分类，不输出凭据；Transport TLS、证书/Origin/网关职责明确；
- Pod 内 sandboxd 可使用单独 token 认证，源码支持把 token SHA256 digest 留在配置中以避免泄露原文，但 Router Token 与 sandboxd Token 是两层控制，均不能替代 Nerelan 当前 Owner 权限。

对 Nerelan 尤其关键的是**宿主有权决定任务后端与工具执行**：即便底层 Router 通过它自己的认证，Sandbox 内生成的外部文件和日志仍是不可信数据，必须经过现有 Artifact/Evidence 验收。

## 7. 模块 F：Client Close、停止、真正销毁不是一回事（P1）

源码：
- [`clients/python/.../sandbox.py`](https://github.com/kubernetes-sigs/agent-sandbox/blob/454d3353e5c26c561dd6de389f32f7f285030e38/clients/python/agentic-sandbox-client/k8s_agent_sandbox/sandbox.py)
- [`clients/python/.../sandbox_client.py`](https://github.com/kubernetes-sigs/agent-sandbox/blob/454d3353e5c26c561dd6de389f32f7f285030e38/clients/python/agentic-sandbox-client/k8s_agent_sandbox/sandbox_client.py)
- [`extensions/api/v1beta1/sandboxclaim_types.go`](https://github.com/kubernetes-sigs/agent-sandbox/blob/454d3353e5c26c561dd6de389f32f7f285030e38/extensions/api/v1beta1/sandboxclaim_types.go)

- `Sandbox.close_connection()` 只断开端口转发/HTTP Session，**远端 K8s Sandbox 仍在运行**。
- `SandboxClient(cleanup=False)` 是默认配置，即调用方异常退出后不应期待 Python 进程自行删除 Sandbox；即使 `cleanup=True`，进程强杀/断电也不能依赖 `atexit`。
- 显式命名的 `claim_name` 会被排除自动清理；这适合预期长期持久执行环境，但不等价于 Task 完成后自动释放基础设施。
- Claim 生命周期 `ShutdownTime`、`TTLSecondsAfterFinished`、`ShutdownPolicy` 与常驻 `restartPolicy=Always` 有相互作用，不能仅凭“一小时 TTL”假设进程一直运行时会按预想释放；应使用有绝对截止的 ShutdownTime + 控制面 Reaper 双重治理。

Nerelan 最小适配证据：`allocated_at / ready_at / execution_started / execution_finished / artifact_reconciled / cleanup_requested / cleanup_confirmed`；Cleanup Pending 不是已释放，资源费用在确认前保留 UNKNOWN 或实际观测。

## 8. 对 Nerelan 的复用决策

| 模块 | 处理方式 | 优先级 | 当前负责人 |
|---|---|---|---|
| Capability requirement / backend capability | **已有**：#299 固定要求，继续采用它；不创建新平台 | P0 已规划 | [#299](https://github.com/dddd2024/Nerelan/issues/299) |
| Claim UID / observedGeneration / state split | **借鉴**适配器恢复身份合同；失败关闭 | P1 | #299、[#796](https://github.com/dddd2024/Nerelan/issues/796) |
| Router Authorizer + sandboxd scoped access | **借鉴 & 验证**；默认 AllowAll 禁止用于敏感环境 | P0 风险验证 | #299/#303 |
| RuntimeClass / NetworkPolicy / Pod Security | **配置责任**；强隔离不依赖 CRD 名称 | P0 风险验证 | #299 |
| Warm Pool 预热 | **延后**：先跑成本/资格仿真；无必要不建设 | P2 | #299/资源调度 |
| Python SandboxClient / execution handle | **有 K8s 需求才可试用**，薄适配而非新的执行器大管家 | P2 | #796 + #299 |
| 新 Controller/TaskStore、全项目引入 Kubernetes | **拒绝**，Windows/local-first 不能被强制迁移 | REJECT | AGENTS.md / #299 |
| 使用不受信任的示例作为安全承诺 | **拒绝**，以 Controller 源码+集群测试为准 | REJECT | #299 |

### 适配器候选合同（研究提案，非已实现）

`SandboxLease = {backend, backend_version, task_id, attempt_id, requested_isolation, verified_isolation, template_digest, policy_digest, namespace, claim_name, claim_uid, sandbox_uid, observed_generation, ready_evidence, artifact_receipt, cleanup_state}`

此合同让 Windows 原生受限执行、Windows 沙箱、Docker/Podman 和可选 Kubernetes 后端共享 **Nerelan 上层要求**，不假装实现等价内核级保护。Policy 判定必须来自 Host；Sandbox Pod/模板的自报不能自行升级 `verified_isolation`。若要求 `SANDBOX_STRONG` 但运行环境没有强隔离 backend，应拒绝而不是降级成工作区执行。

## 9. 可证伪的最小验证（尚未做）

| 测试 | 设计 | 必须通过 |
|---|---|---|
| S1 安全能力门槛 | Provider-free 假后端分别宣称 Kind default / gVisor / Kata；缺项检查 | `SANDBOX_STRONG` 拒绝普通 KIND；无精确网络限制拒绝 `NONE` / allowlist-only |
| S2 路由认证 | 设计假的 Router Authorizer / 不同 Tenant UID/端口/路径、模拟缺少 Elicitation | 无已准入身份绝不能执行，拒绝显式原因可审计；不允许落到 AllowAll |
| S3 UID / Resume | 同名 Claim 被删除重建、旧 Ready Condition、旧 Attempt 的恢复信号 | 姓名相同但 UID/Generation 不匹配，拒绝重用 |
| S4 Warm Eligibility | 默认模板、Claim env、Claim PVC、metadata-only 分组 | env/PVC 一律标记冷启动；排队/费用说明正确 |
| S5 Policy Mutations | 任务已冻结，Template 共享 NetworkPolicy 中途改变 | 再准入或清晰阻断；不能继续声称旧网络规则有效 |
| S6 Cleanup Recovery | Client close、进程异常终止、超时、资源已删而 Claim 残留 | 只有真实确认删除才标记已释放；残留可审计和重新接管 |
| S7 端到端真实 K8s（未来条件满足） | 实测可信 K8s RuntimeClass、CNI、RBAC、敏感地址 egress、同步数据回执和成本 | 失败结果可追溯，且在成本/成功率上超过已选本地 backend，否则 no-go |

**所有 S1–S6 先用 Fake Backend/静态 Fixture 做**，不需要真实账户或下载安装。S7 只有 Owner 已有或明确批准的 K8s 基础设施时才考虑。此轮没有执行任何测试，成本/性能全部是待证伪假说。

## 10. 用户视角：真正的产品收益

对于 Nerelan 用户，沙箱不是独立的“安装 Kubernetes”按钮，而是任务详情上的可信行为：

- “这个任务会运行不可信代码，当前本机执行器**不满足隔离要求**；已选择已授权的隔离后端 / 明确阻止执行”，而非悄悄降低安全级别；
- “沙箱已申请，但尚未 Ready / 当前没有安全可用容量 / 资源已经清理”，不把任务耗时、云费用当作零；
- Agent 失败后允许恢复已验证的工作区和证据，不因旧 Claim 同名就误接管别的执行；
- 如果多账户和多 Agent 的总成本下降有实证，才能宣称有经济价值；否则普通本地任务不应该承担多一套 Kubernetes 的设置成本。

**结论：SELECTIVE_REUSE_CONDITIONAL。** 在已有真实 K8s 需求与可信集群时，上游是一个值得试用的成熟 Sandbox 控制面候选；现阶段最有价值的复用是 UID/Generation/网络策略/认证/清理等设计与测试合同。其底层内核隔离仍依赖另一个成熟 Runtime，不能直接把它当成 Windows local-first 的默认执行器。

## 11. 留痕与审查边界

- **研究 Issue** [#1569](https://github.com/dddd2024/Nerelan/issues/1569)；**正式平台权威**仍是 #299。
- 本文应由 **R1 docs-only Draft PR against current main** 提交，并在当前 main 的开源复用地图添加一条研究索引链接。先前三个研究的统一索引位于**未合并的堆叠 PR 链**，不为此创建第四层依赖，也不新建第二套统一目录；待统一索引进入 main 后再核对补录。
- 独立评审与 exact-head CI 必须按 [AGENTS.md](../../AGENTS.md) 执行。本轮只是静态研究；未进行容器隔离攻击验证、真实经济性测量、CI、Reviewer verdict、合并或部署。
