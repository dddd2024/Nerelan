# Architecture Spine 可信执行切换与当前轮证明重建计划 v1

## 0. 文档定位

本文记录对 PR #9 实现提交：

```text
70dd217b381d106085bce51857be5e8abdd2fa86
```

的独立审计结论，并定义 Architecture Spine v1 在进入合并审计前必须完成的下一轮定向修复。

本文是审计与实施路线，不直接授权命令执行。唯一执行权威仍是：

```text
project_state/decision_packet.md
```

本轮继续使用：

```text
repository: dddd2024/reverse-agent
branch: codex/architecture-spine-v1
Draft PR: #9
base: main
```

不得创建第二个实现分支、不得创建新 PR、不得合并 PR #9。

---

# 1. 审计结论

当前结论：

```text
REWORK_REQUIRED
```

本轮实现已经形成可保留的基础：

- `TrustedCommandRunner` 能按 `command_id` 从 plan 中取命令并真实启动 subprocess；
- raw stdout/stderr 可持久化并计算 SHA-256；
- authenticity 检查已经进入 `evaluate_reconciliation()`；
- runtime policy provider 已接入 LangGraph builder、work-item loader 和 classifier；
- command-level `allowed_mutated_paths` / `produced_artifacts` 已加入模型；
- mutation grant 检查已经进入 transition validator；
- report subject path 分类和 digest 数据结构已存在；
- exact-head CI 主测试成功。

但这些能力尚未完成正式执行切换。当前仍存在以下状态：

```text
CI = success
State Gate = failure
Decision Preflight = failure
current execution log = previous Decision
current local seal = previous Decision
current report = previous Decision and old HEAD
current raw evidence directory = absent
```

因此不能接受，也不能把本轮描述成“只差远端 seal”。

---

# 2. 阻塞发现

## F1 — Committed command plan 不是 active Decision 的确定性投影

严重度：`BLOCKING`

当前 `TransitionCommand.to_dict()` 已包含：

```text
allowed_mutated_paths
```

但 committed `project_state/gates/command_plan.json` 中的 command entries 没有该字段。

`transition-lint` 会比较：

```text
committed_plan.to_dict() == build_transition_command_plan(active_decision).to_dict()
```

因此 exact-head State Gate 和 Decision Preflight 都停在 `Transition lint`。

修复原则：

1. 由 generator 重新生成 command plan；
2. 禁止手工补字段；
3. preview 与 committed plan 必须同源；
4. 增加 round-trip 测试，确保所有 command 字段稳定序列化；
5. lint 必须在 clean checkout 中通过。

---

## F2 — Required test command 引用了不存在的测试文件

严重度：`BLOCKING`

当前 required command：

```text
python -m pytest tests/test_command_mutation_grants.py tests/test_transition_report.py tests/test_report_truth.py tests/test_provenance_integration.py -q
```

但仓库中不存在：

```text
tests/test_provenance_integration.py
```

这意味着即使 lint 修复，required command coverage 仍无法成立。

修复原则：

- 新增真实端到端测试文件；
- 测试必须覆盖 runner → raw evidence → authenticity → mutation grant → local seal → report binding；
- 不允许仅删除测试路径来降低验收要求。

---

## F3 — 当前轮仍复用上一轮 execution log、candidate、seal 和 report

严重度：`BLOCKING`

当前仓库中的以下文件仍属于：

```text
decision_20260721_architecture_spine_attestation_policy_seal_v1
```

而不是当前 active Decision：

```text
project_state/gates/execution_log.json
project_state/gates/reconciliation_candidate.json
project_state/gates/local_execution_seal.json
project_state/gates/changed_file_inventory.json
project_state/gates/remote_observation_payload.json
project_state/codex_execution_report.md
project_state/execution_report.md
project_state/pytest_result.txt
```

旧 execution log 仍含晚于日志生成时间的记录，且当前 raw evidence directory 不存在。

修复原则：

1. active Decision 改变时，旧 evidence bundle 必须自动标记 `STALE`；
2. 新 runner 不得向旧 Decision 日志追加记录；
3. candidate、seal、report 只能读取 identity 完全一致的 bundle；
4. 不得通过修改旧日志使其看起来属于新 Decision；
5. 新轮次必须从空 subject set 开始，由 runner 重新执行 required commands。

---

## F4 — TrustedCommandRunner 仍接受调用方注入整个 command plan

严重度：`BLOCKING`

当前调用方不能传入 command string，但可以构造并传入任意：

```text
TransitionCommandPlan
```

runner 会直接信任这个对象并执行其中的命令。

这只是把命令注入从 `command=` 转移到了 `plan=`，尚未形成真正的执行信任根。

修复原则：

实现：

```text
TrustedExecutionContext.from_state_dir(state_dir)
```

该入口必须自行：

1. 读取 active Decision；
2. 读取 committed command plan；
3. 重新生成 expected plan；
4. 验证 Decision/round identity；
5. 验证 deterministic plan equality；
6. 验证 active branch 和 ancestry；
7. 加载 capability policy、bootstrap state 和 gate state；
8. 只在全部通过后构造 runner。

生产 CLI 不得接受调用方提供 plan object、command string、authority origin、timestamps、digests 或 Git SHAs。

测试代码可以直接构造 plan，但该构造路径必须明确标记为 test-only，不得成为生产入口。

---

## F5 — Runner 执行前没有强制 command authorization

严重度：`BLOCKING`

当前 runner 找到 command ID 后直接执行，没有在 subprocess 前验证：

- execution surface；
- capability policy；
- network policy；
- bootstrap expiry；
- `allowed_only_after_validation`；
- required prior gates；
- command ID 唯一性；
- current plan digest。

特别是：

```text
publication.push_branch
```

虽然标记 `allowed_only_after_validation=true`，runner 本身没有执行该前置条件。

修复原则：

新增统一的：

```text
authorize_before_execute(context, command_id)
```

返回：

```text
AUTHORIZED
或
BLOCKED + machine-readable reasons
```

只有 `AUTHORIZED` 才能启动 subprocess。

---

## F6 — Execution log 追加不是跨轮次安全，也不是原子写入

严重度：`BLOCKING`

当前 `_append_to_log()`：

1. 文件存在时直接读取并追加；
2. 不验证 log 的 Decision/round/plan digest；
3. 使用直接 `write_text()`；
4. 没有 temporary file + fsync + atomic replace；
5. 没有文件锁；
6. sequence 通过“读取当前最大值 + 1”生成，存在并发重复和丢失更新风险。

在当前仓库中，首次运行新 runner 就可能把新记录追加到旧 Decision 日志。

修复原则：

- identity 不一致立即拒绝，禁止自动混合；
- 新 round 显式初始化新 log；
- 使用 lock + temporary file + fsync + atomic replace；
- sequence 在锁内分配；
- record ID、sequence 和 plan digest 必须唯一且连续；
- log header 必须包含 plan digest 和 activation base。

---

## F7 — mutated_paths 不是命令前后 delta

严重度：`BLOCKING`

当 `head_before == head_after` 时，runner 在命令结束后读取整个：

```text
git status --short
```

并把所有 dirty paths 归因于当前命令。

这会导致：

- pre-existing dirty paths 被错误归因；
- 多条命令重复认领相同 mutation；
- 无法证明哪个 command 生成了哪个 artifact；
- command-bound mutation grant 失去可信基础。

修复原则：

runner 必须在执行前后分别采集：

```text
HEAD
index tree
worktree status
tracked diff digest
untracked file inventory/digest
```

然后计算 command-local delta。

记录中增加：

```text
pre_state_digest
post_state_digest
mutation_delta_digest
```

mutation grant 只验证该 command-local delta。

---

## F8 — Command identity 仍存在 fallback 和歧义

严重度：`BLOCKING`

当前 mutation grant 在 `command_id` 缺失时会回退到 command string，并选择第一个匹配 entry。

command-plan validator 也只检查：

```text
canonical command + execution surface
```

没有检查 command ID 全局唯一。

修复原则：

- transition mode 中 command ID 必须存在；
- command ID 必须在 plan 内全局唯一；
- runner 以 `command_id + execution_surface` 解析；
- 删除 transition path 的 command-string fallback；
- legacy adapter 可以保留只读兼容，但不得产生可接受的新 execution evidence。

---

## F9 — Path risk floor 被错误实现成“只要敏感就阻塞”

严重度：`BLOCKING`

当前 validator 会把所有匹配 R2/R3 floor 的 observed path 直接作为 violation。

这会导致已被 APPROVED Decision 明确授权的：

```text
project_state/gates/**
```

仍然因为 R2 而无条件失败。

风险等级应决定授权路线，不应把“风险存在”本身当成违规。

修复原则：

1. 计算 observed maximum risk tier；
2. 保留 path-risk floor，不降低风险；
3. 对明确位于 active APPROVED Decision scope 内的路径，将该 Decision 视为当前 round 的授权来源；
4. 只有未显式授权、超出 authorized tier、或 capability 冲突时才阻塞；
5. 输出 `observed_risk_tier` 和 `authorization_source`；
6. 不新增第二套复杂审批系统。

---

## F10 — Reference path 检查仍只看 outside_scope

严重度：`HIGH`

当前 reference-path check 使用 `outside_scope`，所以某 reference path 如果被误放进 allowed scope，就不会被判定为 reference mutation。

修复原则：

- reference read-only 检查必须针对所有 observed mutated paths；
- reference 与 mutable scope 冲突时 lint 直接失败；
- Decision、roadmap 和 architecture reference 默认只读。

---

## F11 — Report subject binding 仍未接入实际 report CLI

严重度：`BLOCKING`

`report_binding.py` 已有数据结构，但当前 committed report 仍然：

```text
head_sha = c97edca...
changed_files_count = 1
changed file = project_state/decision_packet.md
```

这说明 report generator 没有消费当前 implementation subject、current local seal 和 current evidence bundle。

修复原则：

`transition-report` 必须读取：

```text
active Decision
current command plan
current execution log
current reconciliation candidate
current local seal
actual git diff from activation base
```

并生成：

```text
implementation_paths
governance_paths
generated_artifact_paths
subject_tree_digest
subject_diff_digest
local_seal_digest
current Decision/round
```

任一输入 identity 不匹配时，报告状态必须是 `LOCAL_BLOCKED`。

---

# 3. 本轮唯一目标

完成真实的执行切换：

```text
active Decision
→ deterministic current plan
→ TrustedExecutionContext
→ pre-execution authorization
→ runner executes required command
→ command-local mutation delta
→ raw evidence + current log
→ authenticity + mutation reconciliation
→ current LOCAL_RECONCILED seal
→ current subject-bound report
→ immutable implementation commit
→ independent exact-head remote seal
```

本轮不是继续设计新治理概念。

---

# 4. 实施阶段

## Phase A — Authority projection recovery

1. 修复/验证 `allowed_mutated_paths` round-trip；
2. 重新生成 command plan 和 preview；
3. 新增 `tests/test_provenance_integration.py`；
4. transition-lint 在 clean checkout 通过；
5. command ID uniqueness 测试通过；
6. 当前旧证据被标记 stale，不被当成 completion evidence。

## Phase B — TrustedExecutionContext

实现生产入口：

```text
python -m reverse_agent.project_gate transition-run-command \
  --state-dir project_state \
  --command-id <ID>
```

CLI 只接受：

```text
state_dir
command_id
```

其余执行事实全部由系统读取或观察。

## Phase C — Pre-execution hard gate

在启动 subprocess 前验证：

```text
Decision identity
round identity
plan deterministic equality
plan digest
branch/base ancestry
execution surface
capability/network policy
bootstrap state
allowed_only_after_validation
command uniqueness
```

## Phase D — Atomic evidence journal

实现：

- round-specific journal initialization；
- cross-round rejection；
- file lock；
- atomic replace；
- monotonic sequence；
- plan digest binding；
- raw evidence content digest；
- command-local pre/post state snapshots。

## Phase E — Formal reconciliation

reconciliation 必须验证：

- current Decision/round only；
- plan digest exact match；
- raw evidence exists and digest matches；
- timestamps real and ordered；
- Git objects exist；
- bootstrap timing valid；
- required coverage complete；
- command-local mutation grant valid；
- no command-string fallback；
- no stale subject reuse。

## Phase F — Current report and local seal

生成当前轮：

```text
project_state/gates/execution_log.json
project_state/gates/evidence/**
project_state/gates/reconciliation_candidate.json
project_state/gates/local_execution_seal.json
project_state/gates/changed_file_inventory.json
project_state/gates/remote_observation_payload.json
project_state/codex_execution_report.md
project_state/execution_report.md
project_state/pytest_result.txt
```

所有文件必须属于同一 Decision、round、plan digest 和 implementation subject。

## Phase G — Independent publication seal

1. commit implementation and current local evidence；
2. push once；
3. freeze branch；
4. 独立审计 exact HEAD；
5. 读取 CI、State Gate、Decision Preflight run IDs；
6. 在 PR 评论中写 publication seal；
7. 不再提交新 report 改变 HEAD。

---

# 5. 必须新增的测试

## 5.1 Authority projection

- generated plan includes every command field；
- committed plan equals deterministic projection；
- command ID duplicate blocks；
- missing required test file blocks lint/readiness。

## 5.2 Runner authority

- caller-provided plan cannot reach production runner；
- arbitrary command string cannot execute；
- wrong Decision/round blocks；
- stale plan digest blocks；
- CI-only command cannot run locally；
- `allowed_only_after_validation` blocks before seal；
- expired bootstrap command blocks before execution；
- network command without exact exception blocks。

## 5.3 Journal integrity

- old-round log cannot be appended；
- concurrent append does not lose records；
- sequence is unique and monotonic；
- interrupted write preserves previous valid log；
- raw evidence is present and digest-verifiable；
- log generated_at is after all observations。

## 5.4 Mutation provenance

- pre-existing dirty path is not attributed to command；
- one command cannot claim another command's artifact；
- untracked file delta is detected；
- tracked edit delta is detected；
- missing command ID blocks；
- duplicate command string cannot bypass ID binding。

## 5.5 Risk and references

- R2 path inside explicit APPROVED scope is recorded as R2 and authorized, not auto-blocked；
- R2 path outside scope blocks；
- R3 capability conflict blocks；
- reference path mutation blocks even if mistakenly allowed elsewhere；
- reference/mutable conflict blocks lint。

## 5.6 End-to-end

`tests/test_provenance_integration.py` 必须真实执行一个安全临时仓库流程：

```text
Decision
→ plan generation
→ preflight
→ trusted runner
→ evidence journal
→ mutation reconciliation
→ local seal
→ report subject binding
```

不得使用手工构造的 success artifact 代替实际流程。

---

# 6. 非目标

本轮禁止：

```text
不增加新的治理层
不增加第二个 workflow runtime
不修改 GitHub workflows
不修改 pyproject.toml
不安装 BMAD
不 dispatch Agent
不调用模型 API
不运行未知二进制
不调用 IDA/Ghidra/debugger/emulator
不修改 frontend
不修改 User Solve
不修改 reverse-solving business logic
不修复无关 legacy closeout
不创建新分支或新 PR
不 merge/rebase/force-push/tag/release
不开始 Evidence Trust Schema
不开始 Binary Evidence Firewall
```

---

# 7. 验收条件

只有以下条件全部满足，才允许推荐 `ACCEPTED`：

1. exact active Decision 能生成完整 deterministic plan；
2. committed plan 与 expected plan 完全一致；
3. required test 文件全部存在；
4. transition-lint 通过；
5. pre-execution gate 通过；
6. production runner 不接受 caller-supplied plan；
7. 每条 subject command 通过 production runner 执行；
8. execution log 只包含当前 Decision/round；
9. raw evidence 完整且 digest 可验证；
10. journal 原子、锁定、sequence 单调；
11. mutation delta 为 command-local before/after delta；
12. mutation grant 无 command-string fallback；
13. path risk floor 正确分类并绑定 active Decision 授权；
14. reference paths 对所有 mutations 保持只读；
15. current reconciliation 为 `RECONCILED`；
16. current local seal 为 `LOCAL_RECONCILED`；
17. report 绑定真实 implementation subject；
18. focused tests 通过；
19. full suite 结果如实记录；
20. exact-head CI、State Gate、Decision Preflight 全部成功；
21. publication seal 绑定 exact HEAD 和三个 run IDs；
22. PR #9 仍为 Draft 且未合并。

任一项不满足，结论保持：

```text
REWORK_REQUIRED
```

---

# 8. 本轮之后

本轮通过独立审计后，应停止 Architecture Spine 治理修复循环。

下一阶段只能从以下二者中选择一个新的产品阶段：

```text
Evidence Trust Schema Foundation
或
Binary Evidence Firewall
```

不得自动开始。