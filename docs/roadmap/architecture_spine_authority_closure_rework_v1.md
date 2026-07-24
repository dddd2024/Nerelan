# Architecture Spine 授权闭环修复计划 v1

## 0. 文档定位

本文定义 `Architecture Spine v1` 独立审计后的下一步修复范围。

本文是路线与实施边界文档，不直接授权命令执行。当前执行权威始终为：

```text
project_state/decision_packet.md
```

命令权威必须由执行 Agent 在读取新的 Decision 后，通过 transition control plane 生成：

```text
project_state/gates/command_plan.json
```

禁止手工伪造或事后补写 command plan。

本计划继续使用：

```text
branch: codex/architecture-spine-v1
Draft PR: #9
base: main
```

不创建新实现分支，不创建第二个 PR，不合并 PR #9。

---

## 1. 审计结论

`Architecture Spine v1` 的方向可保留，但当前状态为：

```text
REWORK_REQUIRED
```

当前主要问题不是 LangGraph、类型契约或基础测试失败，而是新的控制面还没有形成真实授权闭环：

1. 当前 command plan 只覆盖 bootstrap 命令，没有覆盖实际 Phase B、依赖安装、完整测试和最终验证命令；
2. transition preflight 可以在未提供真实 execution envelopes 时给出 `command_authority=PASS`；
3. `network_access_allowed=false` 等能力字段没有完整映射为机器可执行的禁止规则；
4. roadmap/reference 路径会被隐式加入可写范围；
5. R0-R3 分类主要依赖调用方声明的 operation，没有根据敏感路径自动提高风险；
6. 最终报告对 exact-head CI 是否已经观察存在相互矛盾的描述；
7. 变更文件清单没有完全由真实 Git diff 生成。

因此，下一轮只修复授权、风险、范围和事实闭环，不增加新的产品能力。

---

## 2. 本轮总目标

完成一个紧凑的 authority-closure rework，使新的 Architecture Spine 能够证明：

```text
Decision
→ machine-readable command contract
→ generated command plan
→ actual execution envelopes / execution log
→ transition reconciliation
→ deterministic risk and scope checks
→ truthful report
→ exact-head remote checks
```

最终必须满足：

1. 实际执行过的每条受控命令都能在当前 command plan 中找到精确授权；
2. 未声明命令、错误 execution surface、越界路径或禁止能力一律 fail closed；
3. reference path 与 mutable path 完全分离；
4. 风险等级同时取 operation、path 和 capability flags 的最高值；
5. 本地结果和 GitHub 远端结果在报告中具有明确的观察时间和状态；
6. PR #9 保持 Draft，修复完成后停止并等待独立审计。

---

## 3. 非目标

本轮明确不做：

```text
不安装 BMAD
不实现真实 Agent dispatch
不调用模型 API
不开始 Binary Evidence Firewall
不实现 EvidenceUnit / Claim Graph
不接入 IDA、Ghidra、debugger 或 emulator
不运行未知二进制
不修改 User Solve
不修改前端
不做数据库或队列
不清理旧 project_state
不修复无关 legacy closeout 链
不合并 PR #9
不直接推送 main
```

两个缺少 `audit_summary` 的历史审计文档继续作为已知 legacy limitation，不在本轮顺带修复，除非新的独立 Decision 明确授权。

---

# 4. Phase A：Command Contract v2

## 4.1 目标

把当前仅由字符串列表组成的 bootstrap command authority，升级为完整、结构化、可验证的 command contract。

每条命令至少包含：

```text
command
phase
required
expected_exit_codes
execution_surface
operations
network_policy
```

建议的 execution surface：

```text
local
ci_only
remote_observation
```

其中 `remote_observation` 只能读取 GitHub 事实，不能修改仓库。

## 4.2 必须实现

1. Decision 中增加结构化 `allowed_commands`；
2. `transition-command-plan` 从 active Decision 生成完整 plan，而不是只读取 bootstrap exception；
3. command plan 必须覆盖 Phase A、Phase B、最终验证和允许的 CI 命令；
4. 同一命令在不同 execution surface 上视为不同授权；
5. required、diagnostic 和 optional 命令必须可区分；
6. 不允许空命令、重复命令、空 expected exit code 或未知 execution surface；
7. command plan identity 必须与 active Decision 和 round 完全一致。

## 4.3 Bootstrap 例外

由于当前 generator 尚不能读取结构化 `allowed_commands`，新的 Decision 可以设置一次性 bootstrap exception，只允许修改 command parser、plan builder、transition validator 及其测试。

例外在以下条件全部成立后立即失效：

```text
current command plan generated
transition-lint = PASSED
transition-preflight = PASSED
plan identity matches active Decision
```

例外不得覆盖 Architecture Spine 风险分类、报告生成或其他 Phase B-E 代码。

---

# 5. Phase B：实际执行对账

## 5.1 目标

消除“空 envelopes 也能证明 command authority”的问题。

## 5.2 必须实现

1. transition preflight 必须接收真实 execution envelopes，或读取结构化 execution log；
2. 每个执行记录至少包含：

```text
command
execution_surface
exit_code
mutated_paths
operations
started_at / observed_at
```

3. preflight 必须逐条调用 command authorization；
4. command plan 中不存在的命令必须阻塞；
5. execution surface 不匹配必须阻塞；
6. 真实执行记录缺失时不能把 command authority 标记为通过；
7. 允许区分：

```text
PRE_EXECUTION_AUTHORIZED
POST_EXECUTION_RECONCILED
```

8. 报告不得用后者伪装前者；
9. bootstrap exception 中发生的命令必须单独标记，而不是伪装成由最终 plan 预先授权。

---

# 6. Phase C：Capability Policy 完整映射

## 6.1 目标

保证 Decision 中的能力布尔值不是说明文字，而是真正进入门禁。

## 6.2 必须覆盖

```text
network_access_allowed
runner_dispatch_allowed
model_api_invocation_allowed
external_reverse_tool_invocation_allowed
unknown_binary_execution_allowed
destructive_operations_allowed
direct_push_to_main_allowed
merge_allowed
force_push_allowed
rebase_during_execution_allowed
bmad_installation_allowed
```

## 6.3 网络策略

网络权限必须按 execution surface 表达：

```text
local:
  network_access = false

ci_only:
  package_install = allowed only for declared workflow commands

remote_observation:
  read-only GitHub observation only
```

本地 `git pull`、在线依赖解析、远程 API 调用不能因为未映射字段而自动通过。

---

# 7. Phase D：路径范围与风险下限

## 7.1 Reference 与 Mutable 分离

Decision 必须分别保存：

```text
reference_paths
allowed_mutated_paths
forbidden_mutated_paths
```

规则：

1. `roadmap_path`、`source_*`、`reference_*` 默认只读；
2. 被引用的文件不能自动获得写权限；
3. 所有可写路径必须显式进入 `allowed_mutated_paths`；
4. 同一路径同时出现在 allowed 和 forbidden 时必须阻塞；
5. 不允许通过父目录通配符意外扩大写入范围。

## 7.2 Path Risk Floor

最终风险等级必须为：

```text
max(operation_risk, path_risk, capability_flag_risk)
```

最低规则包括：

```text
.github/workflows/**              → 至少 R2
pyproject.toml / dependency lock → 至少 R2
project_state/decision_packet.md → 至少 R2
project_state/gates/**           → 至少 R2
.env / secrets / credentials     → R3
未知二进制和样本路径             → R3
调试器、模拟器、hook 配置        → R3
删除、权限和特权远程目标         → R3
```

调用方把 workflow 修改错误声明为 `source_edit` 时，系统仍必须自动升级到 R2。

未知操作继续 `BLOCKED`；无法识别但疑似敏感的路径也应 fail closed。

---

# 8. Phase E：报告与 GitHub Truth 闭环

## 8.1 本地状态

报告必须区分：

```text
LOCAL_VALIDATED
LOCAL_PARTIAL
LOCAL_FAILED
```

## 8.2 远端状态

远端事实必须来自带来源和观察时间的 GitHub observation：

```text
REMOTE_NOT_OBSERVED
REMOTE_PENDING
REMOTE_PASSED
REMOTE_FAILED
```

同一份最终报告不得同时声称“已经观察 exact-head checks”与“仍等待观察”。

## 8.3 文件清单

`files_changed` 必须从真实 Git diff 自动生成，不允许：

- 用目录名代替具体文件；
- 遗漏 Decision、roadmap、workflow 或 project_state 变更；
- 把历史文件误列为本轮修改；
- 根据计划范围推测实际 diff。

## 8.4 最终更新顺序

```text
local validation
→ push current branch
→ observe exact remote head
→ observe CI / State Gate / Decision Preflight
→ regenerate final report from observations
→ stop for audit
```

PR 必须保持 Draft，不得自动 merge。

---

# 9. 测试计划

## 9.1 Command authority

必须新增负向测试：

1. plan 外命令被拒绝；
2. local 命令不能在 ci_only surface 冒用；
3. 缺少真实 execution records 时 reconciliation 不得通过；
4. bootstrap 命令和 normal 命令不会混淆；
5. structured command contract 能稳定序列化；
6. Decision identity 改变后旧 plan 立即失效。

## 9.2 Capability policy

1. local network 禁止；
2. 声明的 CI package install 可通过；
3. 未声明网络命令被阻塞；
4. model、runner、binary、reverse tool 和 destructive flags 全部进入门禁。

## 9.3 Path scope

1. reference-only roadmap 不可修改；
2. allowed 与 forbidden 冲突时阻塞；
3. workflow 路径自动提升到 R2；
4. secret 路径自动提升到 R3；
5. operation 低报不能降低 path risk floor；
6. 未知敏感路径阻塞。

## 9.4 Report truth

1. remote pending 与 remote passed 不会同时出现；
2. changed files 与 Git diff 完全一致；
3. exact-head SHA 必须与 observation 一致；
4. 旧 observation 不能支撑新 HEAD；
5. 本地 partial 不得报告为 full pass。

---

# 10. 建议执行顺序

```text
1. 提交新的 Decision，锁定本轮 scope
2. 使用一次性 bootstrap exception 修复 structured command-plan generator
3. 生成当前 Decision 的完整 command plan
4. transition-lint
5. transition-preflight
6. 实现 execution reconciliation
7. 实现 capability policy 映射
8. 分离 reference/mutable paths
9. 实现 path risk floor
10. 修复 report truth 与 diff inventory
11. 运行 focused tests
12. 运行 control-plane tests
13. 运行 full repository diagnostic
14. git diff --check
15. push 到 codex/architecture-spine-v1
16. 观察 exact-head 三项远端检查
17. 更新最终报告
18. 停止，等待独立审计
```

---

# 11. 验收条件

本轮只有在以下条件全部满足时才能推荐 `ACCEPTED`：

1. active Decision 能生成完整 structured command plan；
2. 实际执行记录与 plan 逐条对账；
3. 任意未声明命令 fail closed；
4. 所有能力布尔值进入机器门禁；
5. 本地网络禁令真实生效；
6. reference path 不会被隐式提升为可写；
7. risk classifier 使用 operation、path、capability 的最高风险；
8. workflow、dependency、decision 和 gate 修改至少为 R2；
9. secret、binary、debugger、destructive 操作为 R3；
10. focused suites 通过；
11. transition lint 和 preflight 通过；
12. full suite 结果被如实记录；
13. changed-file inventory 与真实 Git diff 一致；
14. exact-head CI、State Gate、Decision Preflight 均被真实观察；
15. 最终报告中不存在 remote 状态矛盾；
16. PR #9 仍为 Draft，未合并。

若 command authorization、scope、risk 或 report truth 任一项未闭合，结果必须是：

```text
REWORK_REQUIRED
```

不得因为 focused tests 通过而降低上述要求。

---

# 12. 修复后的下一步

本轮通过独立审计后，才允许进入下一个独立阶段：

```text
BMAD planning adapter evaluation
或
Evidence Trust Schema Foundation
```

二者不得在本轮自动开始。

项目应在此处正式结束“治理系统继续修复治理系统”的循环：旧治理链保持兼容但不再扩展；普通工程状态交给 GitHub 和 LangGraph，高风险路径只保留精简、真实、可验证的 Trust Authorization。