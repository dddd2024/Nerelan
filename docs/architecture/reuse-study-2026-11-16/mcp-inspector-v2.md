# Official MCP Inspector v2 — Nerelan 适配级源码审计

> 单项目文档；本报告的研究登记单为 [#1650](https://github.com/dddd2024/Nerelan/issues/1650)。研究所述测试均属于待验证的契约，未安装、未运行。

# MCP Inspector v2 单项目源码深度审计（2026-11-17）

> `SINGLE_PROJECT / R1 DOCS_ONLY / STATIC_SOURCE_REVIEW / PROVIDER_FREE / NOT_INSTALLED / TESTS_NOT_EXECUTED / NO_IMPLEMENTATION_AUTHORITY`
> Upstream [modelcontextprotocol/inspector@`488c30d9d16e4993bc548ad298eb7450f5125c93`](https://github.com/modelcontextprotocol/inspector/commit/488c30d9d16e4993bc548ad298eb7450f5125c93) (**main** 发布线，开发主线是 v2/main); Nerelan [main@`5c69e891e3a559a23e7fd4e3115422c057df4438`](https://github.com/dddd2024/Nerelan/commit/5c69e891e3a559a23e7fd4e3115422c057df4438).

## 0. 前置去重
- 读取 [#1576](https://github.com/dddd2024/Nerelan/issues/1576) 及已有 **29** 条评论；检查相关 [Goose #1646](https://github.com/dddd2024/Nerelan/issues/1646)、[ToolHive #1590](https://github.com/dddd2024/Nerelan/issues/1590)、[Composio #1567](https://github.com/dddd2024/Nerelan/issues/1567)、[Dify #1571](https://github.com/dddd2024/Nerelan/issues/1571)；GitHub Issues/PR/代码搜索 `MCP Inspector` 和 `modelcontextprotocol/inspector`。
- 未找到官方 Inspector v2 的完整 pinned-source 专项；Goose PR #1647 的标题涉及 “inspector trust”，但其研究对象是 Goose 的 MCP 扩展租约和权限检查，**不是官方 Inspector 测试工具**。
- 与 #790 的 MCP **runtime owner** 严格区分：本轮是无模型、无真实外部 side-effect 的协议/故障/Skills 诊断模式，不宣称已有 Nerelan MCP Connector Runtime。
- **不新开实施 Issue**，实施仍归 #790（MCP）、#253（Pack+verifier）、#303（project config trust）、#447（egress）、#299（sandbox）、#789（hooks）、#361（reuse-first）。

## 1. 固定版本源码证据与与 Nerelan 的对照

| 主题 | Inspector 固定源码 | 真实语义 | Nerelan 模块裁定 |
|---|---|---|---|
| 官方 SDK 上多客户端 | [README](https://github.com/modelcontextprotocol/inspector/blob/488c30d9d16e4993bc548ad298eb7450f5125c93/README.md), [architecture](https://github.com/modelcontextprotocol/inspector/blob/488c30d9d16e4993bc548ad298eb7450f5125c93/docs/architecture.md), [InspectorClient](https://github.com/modelcontextprotocol/inspector/blob/488c30d9d16e4993bc548ad298eb7450f5125c93/core/mcp/inspectorClient.ts#L534) | Web/CLI/TUI/mcpdo 共用 InspectorClient，SDK 处理 MCP 协议；mcpdo 是另一个持久本地 daemon | **BORROW_PATTERN**：复用官方 SDK 和 CLI 作为可选测试工具，不移植第二宿主 daemon 或整套 Web UI |
| 静态连接 & 能力快照 | [cli-smoke-testing](https://github.com/modelcontextprotocol/inspector/blob/488c30d9d16e4993bc548ad298eb7450f5125c93/docs/cli-smoke-testing.md), [config.ts:375](https://github.com/modelcontextprotocol/inspector/blob/488c30d9d16e4993bc548ad298eb7450f5125c93/core/mcp/node/config.ts#L375) | `initialize` 为无工具调用的连通与协议握手；`--config` 只读，`--catalog` 可变；serverSourceConflict 拒绝多种来源混淆 | **DIRECT_OPTIONAL_TEST_TOOL / P1**：用于 #790 固定版本、固定协议/Server identity 的 provider-free smoke；结果仅作为证据，不授权任何后续 tools/call |
| 机器可读失败分类 | [exit-codes.ts:9–147](https://github.com/modelcontextprotocol/inspector/blob/488c30d9d16e4993bc548ad298eb7450f5125c93/core/cli/exit-codes.ts#L9-L147) | 3 auth、4 unreachable、5 tool、6 schema portability、7 bad skill、8 incomplete catalog、9 digest unverifiable、10 load threshold、11 429、12 OAuth destination refusal；envelope 带 retryAfterMs | **BORROW_PATTERN / P1**：Nerelan Connector tests 区分 `unsupported`, `blocked`, `unknown`, `failed`；严重程度和策略由 Nerelan owner 拥有；不可拿 CLI code 0 代替准入 |
| 真实测试服务器 | [test-servers.md](https://github.com/modelcontextprotocol/inspector/blob/488c30d9d16e4993bc548ad298eb7450f5125c93/docs/test-servers.md), [preset-registry.ts](https://github.com/modelcontextprotocol/inspector/blob/488c30d9d16e4993bc548ad298eb7450f5125c93/test-servers/src/preset-registry.ts), [test-server-stdio.ts:32–125](https://github.com/modelcontextprotocol/inspector/blob/488c30d9d16e4993bc548ad298eb7450f5125c93/test-servers/src/test-server-stdio.ts#L32-L125) | 组合 tools/resources/prompts/tasks/elicitation/sampling；stdio 真进程、HTTP 真 transport；`crash_server` 工具能故意在回应前/后退出 | **BORROW_PATTERN / P0 test requirement**：#790 优先引入 fixture 的测试形状；先从受控 Python/Node fake server 开始，必须检测 in-flight 收据是否 UNKNOWN；不得执行未知本地 MCP server |
| 进程崩溃收敛 | [crash reconciliation tests:115–270](https://github.com/modelcontextprotocol/inspector/blob/488c30d9d16e4993bc548ad298eb7450f5125c93/clients/web/src/test/integration/mcp/inspectorClient-crash-reconciliation.test.ts#L115-L270) | 真实连接断开时 pending sampling / elicitation 先清理再发 disconnect、事件只能发一次、in-flight 调用 reject | **BORROW_PATTERN / P0**：#790 的 disconnect→pending→final outcome 语义复验；工具副作用未确认时不能自动重放 |
| MCP 输出 schema 非强制提示 | [toolOutputValidation.ts:7–50](https://github.com/modelcontextprotocol/inspector/blob/488c30d9d16e4993bc548ad298eb7450f5125c93/core/mcp/toolOutputValidation.ts#L7-L50) | 有些 App 场景跳过 strict output validation，只报告 warning；即使 schema validator 编译失败也返回 undefined（不阻断） | **REJECT AS POLICY**：Inspector 是诊断 UI，不是授权器；Nerelan 受控 tool result → model/Host 的 required schema 不可把 `undefined` 视 PASS，需明确 `UNVERIFIABLE` |
| 凭据存储降级 | [secret-store-selection.ts](https://github.com/modelcontextprotocol/inspector/blob/488c30d9d16e4993bc548ad298eb7450f5125c93/core/auth/node/secret-store-selection.ts), [secret-storage.md](https://github.com/modelcontextprotocol/inspector/blob/488c30d9d16e4993bc548ad298eb7450f5125c93/docs/secret-storage.md) | 默认优先 keyring，失效可自动降级 file 或 memory（环境不同）；配置里的 header 不自动移入 secret store；文件可能明文 | **REJECT / P0 security negative**：不能让 Inspector 处理 Nerelan 真账号/Key；可选测试只用合成凭据，必须隔离 HOME 和文件输出，验证 no plaintext/secret logging |
| 本地复用连接 daemon | [mcpdo README](https://github.com/modelcontextprotocol/inspector/blob/488c30d9d16e4993bc548ad298eb7450f5125c93/clients/mcpdo/README.md), [daemon ensure.ts](https://github.com/modelcontextprotocol/inspector/blob/488c30d9d16e4993bc548ad298eb7450f5125c93/clients/mcpdo/src/daemon/ensure.ts) | mcpdo 会起持久 daemon、token、socket，并有版本握手，非“一次 CLI”无残留 | **REJECT FOR HOST / P2 concept**：Nerelan 已有 TaskStore/Host；不导入新的本地常驻连接权威 |
| Skills 样例验证 | [exit-codes.ts:37–101](https://github.com/modelcontextprotocol/inspector/blob/488c30d9d16e4993bc548ad298eb7450f5125c93/core/cli/exit-codes.ts#L37-L101), [skill-authoring.md](https://github.com/modelcontextprotocol/inspector/blob/488c30d9d16e4993bc548ad298eb7450f5125c93/docs/skill-authoring.md) | catalog 完整性/sha digest 未校验状态与 schema 错误不同；上游 skills:eval 用真实 Claude CLI 首轮/链式触发率，非 provider-free | **BORROW_PATTERN / P1**：#253 Pack verifier 区分 `conformant`, `incomplete`, `unverifiable`; Skills 触发评估是后续有预算的 experiment，不能把上游自测命中率当 Nerelan 结果 |
| 许可证 | [LICENSE](https://github.com/modelcontextprotocol/inspector/blob/488c30d9d16e4993bc548ad298eb7450f5125c93/LICENSE) | Apache-2.0 转换中，未取得重许可同意的旧源码仍 MIT，文档 CC-BY-4.0 | **Reference / no copy**：仅列引用与接口模式，copy 文件前逐文件检查许可和来源 |

## 2. Nerelan main 真实状态
- [capability_registry.py:1–5](https://github.com/dddd2024/Nerelan/blob/5c69e891e3a559a23e7fd4e3115422c057df4438/reverse_agent/platform_v1/capability_registry.py#L1-L5) 说明当前只是元数据 registry，**不是**插件管理器或 MCP Runtime。[`list()`](https://github.com/dddd2024/Nerelan/blob/5c69e891e3a559a23e7fd4e3115422c057df4438/reverse_agent/platform_v1/capability_registry.py#L73-L89) 只读 owner 选择目录的 JSON manifest，不执行代码。**ALREADY_REUSED**；不要把测试工具接入生产任务的自动执行路径。
- [claude_executor.py:72–95](https://github.com/dddd2024/Nerelan/blob/5c69e891e3a559a23e7fd4e3115422c057df4438/reverse_agent/platform_v1/claude_executor.py#L72-L95) 校验 machine-managed MCP config；[test_claude_managed_mcp_readiness.py](https://github.com/dddd2024/Nerelan/blob/5c69e891e3a559a23e7fd4e3115422c057df4438/tests/platform_v1/test_claude_managed_mcp_readiness.py) 是 **metadata-only / no provider** 的 fail-closed 早期测试，不能误报为“已实现通用 MCP Connector”。
- [#790](https://github.com/dddd2024/Nerelan/issues/790) 的永久策略是 `OFFICIAL_MCP_SDK_FIRST + VERSIONED_CAPABILITY_DISCOVERY + AUTHORITY_SEPARATION`。本次只补**验证层**，host policy、Pack digest、Owner grants、Magpie cost 不因一次 Inspector 通过而改变。

## 3. 最小可证伪矩阵（提案，未运行）
1. **P0 security/activation**：仓库带 project-local stdio MCP 声明，未经 trust grant 时只读 discovery，**0 进程启动、0 network**；通过 Inspector 的 `initialize` 必须不能提升授权。
2. **P0 crash**：受控 crashable fake server 在 `tools/call` accepted / response-lost 与 sent/unknown 两个时刻崩溃；前端/宿主的 pending 事件最终收敛，无双 `disconnect`，外部操作 `UNKNOWN` 不重放。
3. **P0 credentials**：没有系统 keyring、容器无持久 volume、配置带 Authorization header/stdio env 时 fail-closed 或显式内存隔离；不得把真实 secret 留在 `mcp.json`、`secrets.json`、stdout/stderr 或测试工件。
4. **P1 compatibility**：legacy 与 2026 modern protocol era 的 server/discover/capability/version 不兼容时显式 `UNSUPPORTED`，无静默降档；工具列表分页包括空 cursor 和临时不可用，未读完不可称完整。
5. **P1 schema**：格式错误、异常正则、`outputSchema` 缺 structuredContent、schema validator 编译失败；Host 对强约束应 `UNVERIFIABLE/REJECTED`，UI 可显示 warning 但不能授权。
6. **P1 response classes**：401、429 + Retry-After、connect timeout、5xx、tool isError、OAuth metadata URL 指向 link-local/cloud metadata；按 Host 真正语义分别 auth-hold/rate-hold/retry/blocked，不直接复刻 Inspector exit code。
7. **P1 Pack/Skills**：resources digest 匹配、不匹配、缺失、遍历超时；分别 VERIFIED/FAIL/UNVERIFIABLE/INCOMPLETE。Skill trigger 的模型成本评测独立于纯协议检查。
8. **P1 economics**：固定本地 provider-free 诊断耗时与失败定位覆盖率；未来有 MCP Runtime 时测真实 task acceptance + 消费成本，而非“多了一个 UI”。
9. **No-go**：如果引入 Inspector Node22+ 运行时、凭据文件、daemon、常驻 UI 的成本与攻击面高于上述 fixture/CLI 价值，保留官方 Inspector 为开发者手动诊断工具，而不是默认内嵌 Nerelan。

**未执行**：未安装 Inspector、未运行 `npx` 或 npm、未启动任意第三方 MCP server、未运行 provider/CI/Windows 跨进程测试。研究发现为 `STATIC_SOURCE_AUDIT`，不声称功能已验证、节省真实成本或已合并。

## 4. 对 Nerelan Agent/Plugin 产品体验的具体设计增量

Inspector 与 Nerelan 的定位差异不能被“它也能调用工具”所掩盖：

| 用户意图 | Inspector 当前能力 | Nerelan 应交付的产品语义 |
|---|---|---|
| “这款 Pack 能不能安装？” | Inspector 只验证给定 MCP endpoint/stdio server 的协议响应与工具 schema | 安装前显示 `DISCOVERED → TRUSTED_EXACT → ADMITTED`，没有许可时不能做主动 connect/tool call |
| “这个 MCP 工具为什么不能用？” | CLI JSON envelope + exit code（401/429/timeout/tool/schema） | Connector 卡片显示 `auth_required/rate_limited/unsupported/unknown`，可定位原因，不泄露 tokens |
| “插件突然断线会不会影响任务？” | crash fixture 检查 pending 清理、disconnect 恰一次 | Agent Goal 仍由 TaskStore 拥有，未知外部效果 `UNKNOWN`，task 保持可解释的 parked/reconcile 状态 |
| “更新插件后有没有回归？” | 真 stdio/HTTP smoke、可组合 tools/resources/prompts fixture | 保存每次 pin 版本、协议/能力摘要、测试通过/失败/缺失项，关键能力差异使该 Pack 的可用证据失效 |
| “Skill 内容是否可信？” | 技术校验（manifest/digest/资源完整性）；另有付费模型的 skill trigger eval | 先做纯协议完整性证据；真人/模型触发率是不同的经济性实验，不将‘模型会触发’当成‘工具已获授权’ |

### 4.1 测试序列 — 先握手后副作用

```text
Owner selects pack/version/connector
  └─ read-only manifest / exact digest / config-source trust (#303/#253)
       └─ preflight: endpoint/transport/protocol-era/capabilities (#790)
            └─ sandboxed fixture-only initialize, tools/list, pagination
                 ├─ incompatibility -> UNSUPPORTED / UNVERIFIABLE
                 ├─ trust grant absent -> BLOCKED (zero process/network)
                 └─ compatible -> advisory VERIFIED_PROTOCOL (NOT admitted)
                       └─ host policy exact operation + scoped token (#790/#447)
                            └─ real tool call if and only if authorized
                                 └─ side-effect receipt / UNKNOWN reconciliation (#1597)
```

**不变量**：`VERIFIED_PROTOCOL` 不是 `AUTHORIZED_TOOL_CALL`；插件返回的任何 `outputSchema`、结果、说明、OAuth metadata、prompt/tool description 均为来自外部服务的事实数据，不拥有宿主权限。

### 4.2 抄法和顺序

1. **先抄测试形状（P0）**：在现有 `tests/platform_v1` 以无真实账号的 fixture 实现 `initialize`、`tools/list`、schema/cursor、fake 401/429、crash-mid-call，并把 clear-pending/one-disconnect/UNKNOWN 加入验收；只测试已有接口，未有 MCP Runtime 时不得伪称 E2E。
2. **再使用官方 CLI（P1，条件启用）**：等到 #790 有真正的 connector adapter 和隔离边界，再决定调用已固定版本的 Inspector CLI 做 smoke；预算、依赖、Node 版本、可执行文件授权依 AGENTS，不默认 `npx latest` 下载执行。
3. **Pack 验证器（P1）**：#253 区分合规错误与读限、摘要缺失、动态资源无法证明；对比上游 7/8/9 退出类别，不复制 UI 与其 error handler。
4. **后置经济性（P2）**：当真实 MCP Pack 可用后，比较“无诊断→有诊断”对可发现故障率、修复时间、任务通过率及总成本的净影响；保持与 #1527 的 Executor×Model 路由独立。

### 4.3 不采用的组件及原因

- **mcpdo** 不进 Nerelan 主进程：需要新的驻留 daemon/socket/token/生命周期，破坏唯一 Host/TaskStore 权威；对单次固定协议验证价值不足。
- **Inspector Web UI** 不嵌入：只有工具调试价值，Nerelan 用户需要“能否执行/为什么阻塞/花费/需要何授权”，并不需要数千行 Inspector UI。
- **自动凭据降级** 不照抄：本地无 keyring 时依赖其 memory/file fallback 会改变持久性与泄露面；真实 Owner 凭据继续由既有账号/host 机制管理。
- **非阻断 schema warning** 不用于宿主权限、写入、敏感 egress 或证据验收；明确 unknown/failed，而不是 warning 即成功。
- **动态下载最新版** 不作为 CI/持续运行路径：上游文档也要求 pinned version，默认 npx latest 易漂移。

## 5. 安全与许可证边界

上游仓库 `main` 是最新 v2 发布线，`v2/main` 是开发主线；这里 **只审计了固定 main SHA**，不能默认其他分支或 npm tag 逐文件等价。README 标明 Node `^22.23.4 || ^24.22.1 || >=26.12.1`；该条件是**上游运行要求**，不是 Nerelan 已安装确认。项目的 LICENSE 处于 MIT→Apache-2.0 转换期，文档除 specification 适用 CC-BY-4.0；不直接拷贝上游文件，未来 vendoring 需逐文件做许可证确认。

Inspector 用于诊断未知 MCP server 时也可能触发 stdio 命令或 `tools/call` 副作用，即使 `initialize` 本身不调用工具。与第三方 MCP 服务器联调属于不同的安全边界；本轮未执行，后续必须只用已可信版本、无真实密钥、受控 workspace 与本地 loopback/固定 URL 白名单的合成目标做自动化。

## 6. 实际证据、缺口、结论与责任人

**证据等级**：读固定源码及 Nerelan main 的 source/Issues；未安装上游 Node 包，未运行上述 fixture，未进行性能、安全/成功率实测，未变更任何产品代码。报告属于 `STATIC_SOURCE_AUDIT`，不是 `VERIFIED` 或 `IMPLEMENTED`。

**唯一实施所有权**：
- #790：MCP Connector + Protocol/readiness/Crash cases；#303 + #299：配置发现与隔离；#447：OAuth destination/egress。
- #253：Pack/Skill digest+fixture registry；#789：lifecycle Hook 请求与授权边界。
- #1527：未来计量成本/质量（只有真正实现 Agent×Model×Pack 调用时）。
- #1576：本报告的长期查重索引；本轮新研究 Issue #1650 只保存研究证据。

**结论**：`BORROW_PATTERN` 为主，`DIRECT_OPTIONAL_TEST_TOOL` 仅限未来经授权、版本固定的 provider-free 测试环节。保持官方 SDK-first、不新建第二 MCP runtime/Plugin daemon/Host 状态源，避免将安全诊断通过与产品授权混为一谈。
