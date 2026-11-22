<!-- RESEARCH_ONLY / DOCS_ONLY / STATIC_SOURCE_REVIEW. No upstream code copied; no executable generated. -->
> **Canonical research hub:** [#1576](https://github.com/dddd2024/Nerelan/issues/1576) · **Study Issue:** [#1629](https://github.com/dddd2024/Nerelan/issues/1629) · **Source pin:** `dyoshikawa/rulesync@0cf7642` · **Nerelan pin:** `main@c967325`.

# Rulesync 固定源码深审：多执行器规则编译、Shared Config 所有权、Permissions/Hook/MCP 语义损失与 Nerelan 的信任边界

> **2026-11-17** · **RESEARCH_ONLY / STATIC_SOURCE_REVIEW / NOT_INSTALLED / NOT_BENCHMARKED / DOCS_ONLY / NO_IMPLEMENTATION_AUTHORITY**  
> **唯一上游**：[dyoshikawa/rulesync@0cf7642ba9bb0fe78711bc5697d3024e15be82f2](https://github.com/dyoshikawa/rulesync/commit/0cf7642ba9bb0fe78711bc5697d3024e15be82f2)，`package.json` v43.9.0、MIT [LICENSE](https://github.com/dyoshikawa/rulesync/blob/0cf7642ba9bb0fe78711bc5697d3024e15be82f2/LICENSE)。**Nerelan 对照**：[main@c96732520f3bd5329fc254bc95a91c05768d3ef8](https://github.com/dddd2024/Nerelan/commit/c96732520f3bd5329fc254bc95a91c05768d3ef8)。没安装、没引入 Node 依赖、没执行生成命令或模型。

## 0. 查重和独立增量

- 检查 [#1576 总索引](https://github.com/dddd2024/Nerelan/issues/1576)（20 条当时已有评论）、GitHub Issues/PR 对 `rulesync` / `dyoshikawa` 的检索、仓库代码搜索，未发现单独的 Rulesync pinned-source Issue/PR。
- 已有 [`COMPETITIVE_LANDSCAPE.md: Rulesync`](https://github.com/dddd2024/Nerelan/blob/c96732520f3bd5329fc254bc95a91c05768d3ef8/docs/architecture/COMPETITIVE_LANDSCAPE.md) 仅把它列作“统一生成各 Agent 配置”的竞品候选且写明 **AGENTS.md 仍是权威**；[`docs/radar.md`](https://github.com/dddd2024/Nerelan/blob/c96732520f3bd5329fc254bc95a91c05768d3ef8/docs/radar.md) 提及不代表源码审计或验证。
- 既有研究 Kimi/Google ADK/ACP/Pi-Harness/Shipyard 等覆盖 Runtime/Plugin/协议，**本轮只研究 Rulesync 多目标配置生成、损失说明和安全边界**，不重复构建 Agent Loop。
- 已有实施归属：[Workspace 信任 #303](https://github.com/dddd2024/Nerelan/issues/303)，[Hook #789](https://github.com/dddd2024/Nerelan/issues/789)，[MCP/Connector #790](https://github.com/dddd2024/Nerelan/issues/790)，[Pack #253](https://github.com/dddd2024/Nerelan/issues/253)，[多执行器 #1527](https://github.com/dddd2024/Nerelan/issues/1527)，[复用门 #361](https://github.com/dddd2024/Nerelan/issues/361)。不新建重复实施 Issue。

## 1. 上游源码级证据与不能直接抄的风险

| 模块 | 固定源码 | 具体机制 / 限制 |
|---|---|---|
| **Canonical source → target** | [README](https://github.com/dyoshikawa/rulesync/blob/0cf7642ba9bb0fe78711bc5697d3024e15be82f2/README.md)；[`src/lib/generate.ts:899-1005`](https://github.com/dyoshikawa/rulesync/blob/0cf7642ba9bb0fe78711bc5697d3024e15be82f2/src/lib/generate.ts#L899-L1005) | 一份 `.rulesync/` Rules/MCP/Commands/Subagents/Skills/Hooks/Permissions/Checks 配置产生各工具文件。部分工具/feature 只在 project/global/simulated 模式支持，表格“✅”**不证明 1:1 语义或运行时生效**。 |
| **共享文件写入顺序** | [`shared-file-derive.ts:18-65`](https://github.com/dyoshikawa/rulesync/blob/0cf7642ba9bb0fe78711bc5697d3024e15be82f2/src/lib/shared-file-derive.ts#L18-L65)、[`#L203-L269`](https://github.com/dyoshikawa/rulesync/blob/0cf7642ba9bb0fe78711bc5697d3024e15be82f2/src/lib/shared-file-derive.ts#L203-L269)、[`generate.ts:590-704`](https://github.com/dyoshikawa/rulesync/blob/0cf7642ba9bb0fe78711bc5697d3024e15be82f2/src/lib/generate.ts#L590-L704) | 多个 feature 写 `.claude/settings.json` 等共享文件时，从 Processor 声明推导写入依赖图，缺边/循环/未知依赖直接报错；顺序不是依赖源码文件的自然遍历。**值得在 Nerelan 生成链借鉴不静默覆盖**。上游有 `getSettablePaths` 抛错后忽略路径的注释（`settablePathsForScope`），因此风险更高的 Nerelan 预检应 fail closed，而非假设所有写入都被图覆盖。 |
| **字段所有权与合并** | [`shared-config-gateway.ts:45-83`](https://github.com/dyoshikawa/rulesync/blob/0cf7642ba9bb0fe78711bc5697d3024e15be82f2/src/features/shared/shared-config-gateway.ts#L45-L83)、[`#L1737-L1815`](https://github.com/dyoshikawa/rulesync/blob/0cf7642ba9bb0fe78711bc5697d3024e15be82f2/src/features/shared/shared-config-gateway.ts#L1737-L1815) | `SHARED_CONFIG_OWNERSHIP` 明确 feature 拥有哪些顶层 key；未声明无权写；分 `replace-owned-keys` 和 `deep-merge`，严格保持非管理字段；JSON5 不可安全修改时拒绝整个重写，尽量避免用户配置丢失。**可复用模式**，但生成器保存的只是“写什么”，不负责 Nerelan 运行授权。 |
| **Plan / dry-run** | [`generate-plan.ts:14-78`](https://github.com/dyoshikawa/rulesync/blob/0cf7642ba9bb0fe78711bc5697d3024e15be82f2/src/lib/generate-plan.ts#L14-L78)、[`cli/generate.ts:109-242`](https://github.com/dyoshikawa/rulesync/blob/0cf7642ba9bb0fe78711bc5697d3024e15be82f2/src/cli/commands/generate.ts#L109-L242) | v2 计划按功能排序列出 `write/delete` 的 file/dir/key；`--check` 的 delete-only drift 也返回非零；部分 source load failure 不能误报“up to date”。**计划不是安全事务**：未绑定 pre-image/content digest、Owner/TTL/approval，也不保证 plan 授权后同字节执行。Nerelan 若用于执行前审批必须额外绑定输入 hash+路径/权限+执行器版本+前置文件 hash。 |
| **Orphan cleanup** | [`orphan-sweep.ts:15-106`](https://github.com/dyoshikawa/rulesync/blob/0cf7642ba9bb0fe78711bc5697d3024e15be82f2/src/lib/orphan-sweep.ts#L15-L106)、[`#L139-L226`](https://github.com/dyoshikawa/rulesync/blob/0cf7642ba9bb0fe78711bc5697d3024e15be82f2/src/lib/orphan-sweep.ts#L139-L226)、[`generate.ts:939-1005`](https://github.com/dyoshikawa/rulesync/blob/0cf7642ba9bb0fe78711bc5697d3024e15be82f2/src/lib/generate.ts#L939-L1005) | 注册**本次全目标**生成文件及子树，再把 orphan delete 推迟到所有 feature 写完后；跟随链接检查真实落点并在无法解析时保留+警告，避免共享目录一个 target 删除另一个 target 的新文件。可借鉴“所有权+延迟清理”；**不应默认打开 --delete**，且运行时必须检测 race/保护敏感目录。 |
| **Permission semantics** | [`opencode-permissions.ts:57-109`](https://github.com/dyoshikawa/rulesync/blob/0cf7642ba9bb0fe78711bc5697d3024e15be82f2/src/features/permissions/opencode-permissions.ts#L57-L109)、[`#L375-L430`](https://github.com/dyoshikawa/rulesync/blob/0cf7642ba9bb0fe78711bc5697d3024e15be82f2/src/features/permissions/opencode-permissions.ts#L375-L430)、[`codexcli-permissions.ts:458-555`](https://github.com/dyoshikawa/rulesync/blob/0cf7642ba9bb0fe78711bc5697d3024e15be82f2/src/features/permissions/codexcli-permissions.ts#L458-L555) | OpenCode action-only 类别会把 pattern rules 按 **deny > ask > allow** 收缩为单值，部分不支持的权限类别直接 warning/skip，MCP 命名不能映射时保留为可能不匹配的字面 key；Codex profile 只支持 read/edit/write/webfetch（bash 单独写规则文件），其它类别跳过/警告。**WARN ≠ 权限已执行，安全规则不能容许安全降级到 warn-and-skip**。 |
| **Codex unmanaged settings** | [`codexcli-permissions.ts:927-967`](https://github.com/dyoshikawa/rulesync/blob/0cf7642ba9bb0fe78711bc5697d3024e15be82f2/src/features/permissions/codexcli-permissions.ts#L927-L967) | 重生成会保留 Rulesync 不管理的 profile/network keys，并警告用户审查。Nerelan 不能将“保留未知安全字段”当作“验证字段安全”，尤其限制变化时应需要 Owner review。 |
| **Hook executable outputs** | [`opencode-hooks.ts:26-106`](https://github.com/dyoshikawa/rulesync/blob/0cf7642ba9bb0fe78711bc5697d3024e15be82f2/src/features/hooks/opencode-hooks.ts#L26-L106) | OpenCode hooks 不是单一 JSON，生成**插件代码文件**。上游 `toRulesyncHooks` 直接 Not implemented，因此不是双向可逆转换。Hook 转译可能跨“静态配置→可执行代码”的信任边界，必须按**新 executable code**审阅、hash、审批、隔离。 |
| **MCP env ref** | [`mcp-env-var-format.ts:1-127`](https://github.com/dyoshikawa/rulesync/blob/0cf7642ba9bb0fe78711bc5697d3024e15be82f2/src/features/mcp/mcp-env-var-format.ts#L1-L127) | Canonical env 引用转换为目标工具不同的 env/header 变量占位符（例如 OpenCode brace 格式），其值在**配置阶段不解析为密钥**。这只处理**语法**，不是凭证最小暴露/secret masking/工具授权。 |
| **MCP install scope** | [`src/mcp/install.ts:53-112`](https://github.com/dyoshikawa/rulesync/blob/0cf7642ba9bb0fe78711bc5697d3024e15be82f2/src/mcp/install.ts#L53-L112) | 模型调用的 install MCP 命令拒绝 project 外 file:// source 与 user scoped gh install，符合工具调用最小范围。但 CLI install 本身支持远程 source，不能以“有 lockfile”推断代码可信。 |
| **Fetched skill/lock** | [`sources-lock.ts:16-90`](https://github.com/dyoshikawa/rulesync/blob/0cf7642ba9bb0fe78711bc5697d3024e15be82f2/src/lib/sources-lock.ts#L16-L90)、[`sources-artifacts.ts:17-90`](https://github.com/dyoshikawa/rulesync/blob/0cf7642ba9bb0fe78711bc5697d3024e15be82f2/src/lib/sources-artifacts.ts#L17-L90) | Source lock 写 resolved 40-hex SHA、skill/rule content integrity；某些远端 Skill 脚本保留 executable bit。此类文件内容属于 **不可信执行素材**，Nerelan 需分 digest 完整性、来源可信性和运行授权；旧锁迁移时 integrity 可能为空（`sources-lock.ts:80-108`）。 |
| **Target unsupported** | [`generate.ts:442-477`](https://github.com/dyoshikawa/rulesync/blob/0cf7642ba9bb0fe78711bc5697d3024e15be82f2/src/lib/generate.ts#L442-L477) | Feature 无 native/project/global support 时可能 warning + skip，也有 simulated 选项。Nerelan 若生成与 Owner 权限相关的限制，必须把 missing/skip 标为 **BLOCKING_DRIFT**，不能只靠生成成功判定合规。 |
| **许可证/实现成本** | [`package.json`](https://github.com/dyoshikawa/rulesync/blob/0cf7642ba9bb0fe78711bc5697d3024e15be82f2/package.json)、[`LICENSE`](https://github.com/dyoshikawa/rulesync/blob/0cf7642ba9bb0fe78711bc5697d3024e15be82f2/LICENSE) | MIT 的 npm/Node 依赖与 Nerelan Python/local-first 运行层不同；当前研究**不建议引入 Node CLI 到受信运行路径**。若要试用，仅在隔离 fixture/CI 的离线生成层评估依赖成本和产物。 |

## 2. Nerelan 当前真实实现对照：最重要的“无效复用”陷阱

| Nerelan 当前 main 权威和路径 | 分级 | 最小可取增量 / 不应做的事 |
|---|---|---|
| [`task_runtime.py:511-555 ExecutorRouter`](https://github.com/dddd2024/Nerelan/blob/c96732520f3bd5329fc254bc95a91c05768d3ef8/reverse_agent/platform_v1/task_runtime.py#L511-L555)，[#1527](https://github.com/dddd2024/Nerelan/issues/1527) | **ALREADY_REUSED + BORROW_PATTERN** | 多执行器配置版本与 capability matrix，生成对应的静态/可选说明文件，**不能把统一配置等同统一 Executor runtime**。 |
| [`codex_executor.py:175-188`](https://github.com/dddd2024/Nerelan/blob/c96732520f3bd5329fc254bc95a91c05768d3ef8/reverse_agent/platform_v1/codex_executor.py#L175-L188) | **CRITICAL REJECT/UNUSED** | Nerelan 受信 Codex 命令含 `--ignore-user-config`、`--ephemeral`、强制 `--sandbox`；Rulesync 写到 `.codex/config.toml` 等文件可能**根本不会被该执行路径读取**。如果为了让 Rulesync 生效移除 ignore-user-config，反而重新引入用户/仓库配置风险。不许如此绕过。 |
| [`claude_executor.py:135-162`](https://github.com/dddd2024/Nerelan/blob/c96732520f3bd5329fc254bc95a91c05768d3ef8/reverse_agent/platform_v1/claude_executor.py#L135-L162) | **CRITICAL REJECT/UNUSED** | 当前 Nerelan Claude `--restricted --strict-mcp-config --tools ...`，`PROJECT_CONFIG=()`；生成的 hooks/MCP/permissions/skills **不是受信执行的事实**。不得为统一化牺牲 `--restricted` 安全边界。 |
| [`opencode_executor.py:433-510`](https://github.com/dddd2024/Nerelan/blob/c96732520f3bd5329fc254bc95a91c05768d3ef8/reverse_agent/platform_v1/opencode_executor.py#L433-L510) | **BORROW_PATTERN + VERIFY** | Nerelan 现有角色级 runtime JSON permission：planner/reviewer/coder 分工；可离线对照 Rulesync 的 OpenCode v1/v2 输出语义，但不能让 `.rulesync` 对 Runtime permission 产生更宽覆盖，不能覆盖角色级 deny。 |
| [`SOURCE_OF_TRUTH_MATRIX.md:61-69`](https://github.com/dddd2024/Nerelan/blob/c96732520f3bd5329fc254bc95a91c05768d3ef8/docs/architecture/SOURCE_OF_TRUTH_MATRIX.md#L61-L69)、[`AGENTS.md`](https://github.com/dddd2024/Nerelan/blob/c96732520f3bd5329fc254bc95a91c05768d3ef8/AGENTS.md) | **KEEP AUTHORITY** | Owner 批准、TaskStore operation receipt、Magpie credentials、外部审查独立。Rulesync 只是**非权威只读/生成投影工具**，产物必须可追溯到 approved source digest，永不取代权限系统。 |
| [`capability_registry.py:74-115`](https://github.com/dddd2024/Nerelan/blob/c96732520f3bd5329fc254bc95a91c05768d3ef8/reverse_agent/platform_v1/capability_registry.py#L74-L115) 与 [#253](https://github.com/dddd2024/Nerelan/issues/253) | **ALREADY_REUSED + BORROW_PATTERN** | 当前 Pack manifest 限于 bounded JSON metadata，无 third-party code。可以用 Rulesync 产出各 Executor 的 declarative Skill/MCP 模板，但安装与执行权限仍在 #253/#303/#790 的独立门。 |
| [#789](https://github.com/dddd2024/Nerelan/issues/789) Hooks、[#790](https://github.com/dddd2024/Nerelan/issues/790) MCP、[#303](https://github.com/dddd2024/Nerelan/issues/303) repo config | **BORROW_PATTERN** | 引入 `compiler IR + capability support + per-target loss report + owned-file diff` 的验证概念；**拒绝**把生成的 Hook 代码/自动下载 Skill 当安全配置，拒绝 MCP secret ref 自动解密/注入。 |

**用户视角**：想在应用中为同一项目切换 Agent 时，不必重复维护多份指令和技能，并能看到每种 Executor 哪些能力/规则有效、哪些无效。**开发者视角**：把“统一配置输入”变成明确的**不可执行 IR / 编译计划 / 部署收据**，减少复制粘贴与无声语义漂移，而不是用一个 Node CLI 来管理长期任务或扩权。

## 3. 最小可证伪实验（此轮**未执行**，交已有 owner）

1. **Config-01 / 无效配置检测**（#1527）：用已有 Nerelan Codex `--ignore-user-config` 和 Claude `--restricted` fixture；Rulesync 生成配置后启动这些受信路径，必须报告 **NOT_CONSUMED**，禁止 UI/合规检查声称“策略生效”。
2. **Config-02 / 权限语义保守性**（#303/#789）：canonical `bash/read/webfetch/MCP` 混合 allow/ask/deny，跨 OpenCode V1/V2、Codex、Claude。比较目标进程实际拒绝行为；`WARN_AND_SKIP` 的安全规则必须使 enable fail-closed，MCP key 无法映射也必须阻断（不是“生成后用户自己看”）。
3. **Config-03 / 多功能共享文件**（#253/#790）：MCP + permissions + hooks + ignore 同时写同一 JSONC/TOML/YAML 文件、原文含评论和用户字段；必须保持非管理字段、明确 key ownership、冲突 FAIL，并与计划/实际 diff 一致。
4. **Config-04 / Cleanup 与可逃逸路径**（#303）：不同工具生成到同一个目录、symlink/junction/大小写别名、生成期间根文件变化、orphan delete；不允许删除任何非本轮或非该 Owner 管理的内容。Windows NTFS 链接与权限需要真实平台测。
5. **Config-05 / 执行代码从配置冒出**（#253/#789）：Hook 转成 JS plugin、远端 Skill 含 executable scripts、MCP server 直接可执行；即使 Rulesync plan/lockfile 正确，也需独立源审查、hash/exec grant、进程隔离或拒绝，不得绕过 Host/Owner。
6. **Config-06 / 生成计划与实写竞争**（#361）：Preview plan v2 → 手工修改目标文件/source source hash → apply，必须拒绝旧计划，需有 expected input/output digest/permission diff/Owner allowed operations（上游本身没有这些授权）。
7. **Config-07 / 价值评测**（#1527）：记录新增配置后多 Executor 可复用指令的数量、语义覆盖率、误配置率、setup time、被拒绝权限次数、运行成功率、模型使用成本；若 Codex/Claude 仍不读这些配置，则对其 runtime 配置收益记为零，不能计为“已统一”。

**P0/P1**：P0 继续优先修持续运行 stalls/配额/真实成本，不把配置编译排到更前；若多执行器实际启用，**P1** 做 Config-01/02 + 共享文件 ownership 的 provider-free fixture，P2 才考虑 UI 预览和范围内的 optional Rulesync 生成。安全语义不等价、未知执行权限或文件删除不明则 **NO-GO**。

## 4. 决策和证据状态

- **SELECTIVE_BORROW_PATTERN**：所有权声明 + 有序写入 DAG + versioned change plan + delayed orphan sweep + unsupported feature / loss reporting + env-ref syntax projection + source lock integrity。
- **ALREADY_REUSED / KEEP**：`AGENTS.md` 和 Owner 运行授权、TaskStore 权威/receipts、ExecutorRouter 与角色原生 permission config、Pack declarative metadata。
- **REJECT**：以生成的文件替代受信 Host 运行安全门、放宽 Codex/Claude 启动限制、warning-and-skip 安全规则、自动加载可执行 Hook/Skill/MCP、把 lock SHA 误称为 publisher trust、将 Node CLI 作为另一套插件/账户/Agent 管理器。
- **DIRECT_REUSE**：MIT 法律上可评估，但**本轮不批准引入**；仅可在既有实施 owner 下做隔离离线试用，并比较库依赖成本与 Python 最小生成适配器的净收益。

**证据仅为静态源码检查**：未安装 Rulesync、未运行 Jest/Vitest、未运行 E2E、未用真实 Codex/Claude/OpenCode、未进行跨平台文件写入、未算 ROI；未通过 Nerelan exact-head CI / 独立审查。Docs-only Draft PR 在创建后双向登记至本 Issue 与 #1576；不代表已进入 main。


## 5. 实施交接纪律

本文仅分析成熟机制与产品风险，**不将 Rulesync 作为第二套配置治理权威**。若现有 #303/#789/#790/#253/#1527 要验证，先做 provider-free 配置编译对比与真实执行路径消费情况的负向测试；没有 exact-head CI/独立 review 不能认定任何代码已被接受。没有 Node/npm 安装、外部 Skills 下载或对 Nerelan TaskStore/Owner/Magpie 的变更。
