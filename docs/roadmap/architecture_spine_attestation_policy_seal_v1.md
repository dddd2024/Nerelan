# Architecture Spine 证明链与策略绑定封口计划 v1

## 0. 文档定位

本文记录对 PR #9 当前实现提交：

```text
19c081410b3ee2bc9c81eeb52b0c0a21f200d02a
```

的独立审计结论，并定义 Architecture Spine v1 在进入合并审计前的最后一轮定向修复。

本文不是命令执行权威。执行权威只能来自：

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

不创建第二个实现分支，不创建新 PR，不合并 PR #9。

---

# 1. 审计结论

当前结论：

```text
REWORK_REQUIRED
```

但代码方向继续保留。上一轮已经真实完成：

- pre-execution 与 post-execution 命令入口拆分；
- required command coverage 检查；
- plan-driven operation/network 检查；
- runtime risk policy 数据结构和 classify node 接线；
- path contract 数据结构；
- transition-report 入口；
- focused tests；
- 当前实现 HEAD 的 CI、State Gate、Decision Preflight 均成功。

本轮不得推倒重写。剩余问题集中在：

```text
证据是否真实
策略是否由可信来源签发
生成物写入是否绑定到具体命令
本地证明与远端证明是否形成无循环封口
```

---

# 2. 审计发现

## F1 — Execution record 只做“非空检查”，不能证明真实性

严重度：`BLOCKING`

当前 ExecutionRecord 只验证字符串非空，没有验证：

- 时间是否为合法 RFC3339；
- 时间是否晚于当前时间；
- 命令时间是否单调；
- stdout/stderr digest 是否为真实 SHA-256；
- head_before/head_after 是否为 40 位 Git SHA；
- digest 是否对应真实输出；
- record 是否由 runner 生成而不是人工编辑。

当前 committed execution log 使用：

```text
sha256:tests_passed
sha256:empty
sha256:report_generated
```

这不是 64 位 SHA-256。

其时间范围为：

```text
2026-07-21T19:30:00Z
至
2026-07-21T20:13:01Z
```

在本次审计时这些时间仍位于未来，因此不能作为已观察事实。

此外，execution log 的 `generated_at` 为 `20:00:00Z`，但后续命令被记录到 `20:13:01Z`，内部时序矛盾。

### 修复原则

Execution log 必须由一个受控 recorder 生成，禁止执行 Agent 直接手写完成记录。

必须验证：

```text
RFC3339 UTC
started_at <= observed_at <= recorder_observed_at
not_future_with_tolerance
40-char git SHA
sha256:<64 lowercase hex>
stdout/stderr digest 可回算
command_id 与 plan 精确匹配
```

---

## F2 — 本地报告与 changed-file inventory 绑定了错误 HEAD

严重度：`BLOCKING`

当前报告和 inventory 绑定：

```text
head_sha: 5ee5cc9728249f9bf8b60bf052d561237cc830d4
```

这是 Decision commit，不是实现提交 `19c081...`。

当前 changed-file inventory 只列出：

```text
project_state/decision_packet.md
```

而实际实现提交相对 Decision commit 修改了二十多个代码、测试和 project_state 文件。

因此当前报告不能证明本轮实现范围。

### 修复原则

repo 内本地报告不得声称“最终 commit HEAD”。它应绑定：

```text
activation_base_sha
subject_tree_digest
subject_diff_digest
observed_worktree_paths
```

最终 commit/head 与远端检查由外部 publication seal 绑定，不能通过“再提交一次报告”实现。

---

## F3 — Remote observation 没有更新到真实 exact-head 事实

严重度：`BLOCKING`

当前 payload 仍为：

```text
head_sha: 5ee5cc...
REMOTE_NOT_OBSERVED
```

但实现提交 `19c081...` 的：

```text
CI
State Gate
Decision Preflight
```

已经全部成功。

### 修复原则

远端事实不得写回 repo 后再制造一个新 HEAD。

远端 publication seal 必须作为：

```text
PR audit comment
或 immutable workflow artifact
```

绑定 subject commit SHA、workflow run ID、workflow name、conclusion 和 observed_at。

---

## F4 — post-execution gate 存在自证循环

严重度：`BLOCKING`

`gate.post_execution` 本身是 required command，expected exit code 为 0。

但 reconciliation 在运行时会读取包含自己的 execution log。当前记录中该命令 exit code 为 1，因此 reconciliation 因自己的失败记录继续失败。

即使远端证据补齐，也需要先有一个“已经成功的 reconciliation 记录”才能证明 reconciliation 成功，形成循环。

### 修复原则

被验证对象不能包含当前验证动作自身。

拆分为：

```text
transition-reconcile-evaluate
  只读取已封存 subject records
  生成 candidate result

transition-seal-local
  验证 candidate result、subject digest 和 recorder digest
  生成 LOCAL_RECONCILED seal
```

`transition-seal-local` 不属于其自身 subject command set。

---

## F5 — required_evidence_source 模型混合了 local 命令和 CI 证明

严重度：`BLOCKING`

以下命令执行 surface 是 `local`，但 required evidence source 被声明为 `exact_head_ci`：

```text
test.evidence_control_plane
test.runtime_risk_graph
test.report_truth
```

execution log 已记录这些本地测试通过，但 local reconciler仍把它们判为 missing，因为当前实现对所有 `exact_head_ci` 项无条件返回 missing。

同时，GitHub Actions 的成功不能自动证明这些具体 command_id 被执行，除非 workflow 显式产出 command-id attestation。

### 修复原则

证据要求必须区分：

```text
local_command_evidence
ci_check_attestation
repository_state_attestation
```

本地 focused tests 使用 `local_command_evidence`。

CI 只证明明确声明的 check identity，例如：

```text
ci.workflow.ci
ci.workflow.state_gate
ci.workflow.decision_preflight
```

不得用一个 workflow success 推断任意本地 command_id 已执行。

---

## F6 — Runtime RiskPolicySnapshot 没有真正绑定 active Decision

严重度：`BLOCKING`

当前 workflow identity 不包含：

```text
decision_id
round_id
policy_digest
```

classify node 在 workflow identity 缺少这些字段时，会回退使用 policy 自己提供的 ID，因此 identity check 近似自我比较。

RiskPolicySnapshot.from_mapping 会忽略外部提供的 policy_digest，并根据 payload 中的规则重新计算一个 digest。调用方可以在保留同一 Decision ID 的情况下替换更低的 path/capability risk 规则，再获得一个新的自洽 digest。

### 修复原则

Risk policy 必须由可信 provider 从 active Decision 生成，而不是由 workflow caller 提供。

必须实现：

```text
AuthorizedRiskPolicyProvider
→ load active Decision
→ produce canonical policy
→ compute policy_digest
→ bind digest into WorkflowIdentity
→ classifier verifies supplied snapshot digest == authorized digest
```

任何规则、ID 或 digest 漂移必须 BLOCKED。

---

## F7 — generated artifact exemption 只绑定路径，没有绑定生成命令

严重度：`HIGH`

当前 generated artifact path 被整体排除于 allowed scope 和 path-risk 检查。

但是代码没有验证该路径是否由指定 generator command 写入。任意 envelope 只要声明修改某个 generated artifact path，就可能获得同样豁免。

### 修复原则

command plan 必须支持：

```text
allowed_mutated_paths
produced_artifacts
```

豁免条件必须是：

```text
record.command_id == designated_generator_command_id
AND
mutated_path in command.produced_artifacts
```

不能存在全局“只要路径是 generated artifact 就豁免”的规则。

---

## F8 — 状态字段仍然互相矛盾

严重度：`HIGH`

当前：

```text
execution_log.gate_status = PASSED
codex_execution_report.local_status = LOCAL_VALIDATED
reconciliation_result.gate_status = BLOCKED
remote_observation = REMOTE_NOT_OBSERVED
```

这些状态不能同时构成完成证明。

### 修复原则

统一状态机：

```text
EVIDENCE_RECORDED
LOCAL_RECONCILIATION_BLOCKED
LOCAL_RECONCILED
REMOTE_NOT_OBSERVED
REMOTE_ATTESTED
ACCEPTED
```

`execution_log` 只能声明记录是否可解析，不能声明整个 round PASSED。

---

# 3. 本轮目标

建立无自证循环的两级封口：

```text
Local Execution Seal
+
Remote Publication Seal
=
Architecture Spine Acceptance
```

本轮完成后不再继续扩展治理体系。

---

# 4. Phase A — Machine-generated Evidence Recorder

实现统一 recorder：

```text
python -m reverse_agent.project_gate transition-record ...
```

要求：

1. 命令执行和 record 写入由同一受控入口完成；
2. 自动获取真实开始/结束时间；
3. 自动计算 stdout/stderr SHA-256；
4. 自动读取 head_before/head_after；
5. 自动记录 command_id、surface、operations 和 mutated paths；
6. 禁止手写 `outcome` 替代原始证据；
7. 原始 stdout/stderr 可作为本地临时 evidence bundle，不必全部提交 Git；
8. committed summary 必须可由 evidence bundle 重建。

负向测试：

- future timestamp；
- malformed digest；
- non-monotonic time；
- fake head SHA；
- digest mismatch；
- manually claimed command ID；
- missing raw evidence；
- execution after bootstrap expiry claiming bootstrap authority。

---

# 5. Phase B — Remove Self-Reconciliation

新增：

```text
transition-reconcile-evaluate
transition-seal-local
```

规则：

- evaluate 的 subject records 在执行前封存；
- subject digest 固定后，不再将 evaluator/sealer 自身加入 subject；
- local seal 包含 subject digest、plan digest、Decision identity 和 result digest；
- local seal 只验证 local/repository evidence；
- exact-head CI 不进入 local seal；
- local seal 成功状态为 `LOCAL_RECONCILED`。

删除或兼容弃用当前自指的 `gate.post_execution` required evidence 语义。

---

# 6. Phase C — Evidence Requirement Normalization

command contract 增加：

```text
evidence_requirement:
  source
  subject
  required
```

来源只允许：

```text
local_command_evidence
repository_state_attestation
ci_check_attestation
```

本地 focused tests 由 recorder 证明。

远端检查只使用固定 check identities：

```text
CI
State Gate
Decision Preflight
```

remote seal 不伪造对应的 shell command envelope。

---

# 7. Phase D — Decision-issued Runtime Risk Policy

实现 `AuthorizedRiskPolicyProvider`：

1. 从 active Decision 读取 path-risk floor 和 capability rules；
2. 规范化排序并计算 digest；
3. WorkflowIdentity 增加 Decision/round/policy digest；
4. graph entrypoint 从 provider 注入 sealed snapshot；
5. caller 不能直接提交任意 snapshot；
6. `RiskPolicySnapshot.from_mapping` 必须验证 payload digest；
7. classifier 同时验证 identity 和 authorized digest；
8. checkpoint replay 时 policy digest 不一致必须 BLOCKED。

必须有 tampering tests：

- 同 ID 修改 path risk；
- 同 ID 修改 capability risk；
- 伪造 digest；
- replay 使用旧 policy；
- 缺少 provider；
- caller-supplied lower-risk policy。

---

# 8. Phase E — Command-bound Mutation Grants

每条写命令必须明确：

```text
allowed_mutated_paths
produced_artifacts
```

验证顺序：

```text
command authorization
→ command-specific path grant
→ forbidden path check
→ reference path check
→ path-risk classification
→ artifact production check
```

不得再对 generated artifact path 做全局豁免。

---

# 9. Phase F — Local Report and External Publication Seal

## 9.1 Local report

本地报告绑定：

```text
activation_base_sha
subject_tree_digest
subject_diff_digest
observed_worktree_paths
local_seal_digest
```

不得声称最终 remote HEAD。

`pytest_result` 必须包含真实命令、退出码、pass/fail/skip 数量和 evidence digest，不能只写“测试证据由测试自己产生”。

## 9.2 Remote publication seal

本地实现提交并推送后，由独立审计读取 GitHub：

```text
subject_commit_sha
CI run id + conclusion
State Gate run id + conclusion
Decision Preflight run id + conclusion
observed_at
```

把 seal 写入 PR comment，不提交回分支。

只有：

```text
LOCAL_RECONCILED
AND
REMOTE_ATTESTED
```

才能推荐 `ACCEPTED`。

---

# 10. 测试要求

至少覆盖：

1. evidence timestamp/digest/head 格式和真实性；
2. recorder 自动生成记录；
3. 手写记录不能成为 acceptance evidence；
4. evaluator/sealer 不验证自身；
5. required local commands 完整覆盖；
6. CI check attestation 不冒充 local command；
7. policy digest tampering；
8. policy identity mismatch；
9. replay with stale policy；
10. command-specific path grants；
11. wrong command writing generated artifact；
12. local report真实 diff inventory；
13. contradictory statuses blocked；
14. remote seal绑定 exact subject commit；
15. new commit invalidates old remote seal。

运行：

```text
focused evidence tests
runtime policy tests
report/seal tests
control-plane tests
full repository diagnostic
git diff --check
```

完整测试中历史 audit-document failure 可继续记录为 legacy diagnostic limitation，但不得隐藏。

---

# 11. 非目标

本轮不做：

```text
不安装 BMAD
不启动真实 Agent dispatch
不调用模型 API
不实现 Evidence Trust Schema
不实现 Binary Evidence Firewall
不修改 frontend
不修改 User Solve
不执行未知二进制
不修复无关 legacy audit documents
不扩展旧 closeout/final-seal 系统
不创建新 PR
不合并 PR #9
```

---

# 12. 验收条件

只有以下全部成立才可推荐 `ACCEPTED`：

1. execution records 由受控 recorder 生成；
2. 时间、digest、head 和 raw evidence 可验证；
3. 不存在未来时间和伪 digest；
4. local reconciliation 不包含自身；
5. required local evidence 完整；
6. exact-head CI 作为独立 check attestation；
7. local report绑定真实 subject tree/diff；
8. runtime policy由 active Decision provider 签发；
9. workflow identity绑定 policy digest；
10. policy tampering fail closed；
11. generated artifacts 写入绑定指定 command_id；
12. 状态机不存在 PASSED/BLOCKED 矛盾；
13. focused tests 通过；
14. full suite事实完整记录；
15. subject commit 的 CI、State Gate、Decision Preflight 全部成功；
16. remote publication seal作为 PR comment 发布；
17. PR #9 保持 Draft，等待最后独立审计。

如果任一真实性、策略绑定或无循环封口条件未满足，结果保持：

```text
REWORK_REQUIRED
```

---

# 13. 通过后的下一步

本轮通过独立审计后：

1. 将 PR #9 标记为 Ready for Review；
2. 完成一次合并前人工检查；
3. 合并 Architecture Spine；
4. 停止继续开发治理基础设施；
5. 新建独立产品阶段，开始 Evidence Trust Schema Foundation。
