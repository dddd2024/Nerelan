# Architecture Spine 真实执行证明与运行时接线最终修复计划 v1

## 0. 文档定位

本文记录对 PR #9 实现提交：

```text
c3f053a027756edfa749bf9f7aba0f61c596a562
```

的独立审计结论，并定义 Architecture Spine v1 在进入最终合并审计前的最后一轮定向修复。

本文是审计与实施路线，不直接授权命令执行。执行权威只能来自：

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

上一轮新增的结构可以保留：

- `EvidenceRecorder`；
- `ReconciliationCandidate` 与 `LocalSeal`；
- 证据来源规范化类型；
- `AuthorizedRiskPolicyProvider`；
- command-bound mutation grant 数据字段；
- report subject binding 数据结构；
- focused tests；
- CI 主测试通过。

但这些模块大多停留在“存在并通过单元测试”，还没有形成真实、不可伪造、端到端接线的证明链。

本轮不得继续增加新的治理层。只能修复以下四类问题：

```text
真实执行证据
运行时策略接线
命令级写入授权
本地与远端封口
```

---

# 2. 审计发现

## F1 — 实现越出 active Decision 路径范围

严重度：`BLOCKING`

实现提交新增：

```text
reverse_agent/control_plane/evidence_source.py
reverse_agent/control_plane/report_binding.py
```

但上一轮 Decision 的 `allowed_mutated_paths` 未包含这两个文件。

exact-head State Gate 和 Decision Preflight 因此在 `transition-preflight` 阶段失败，报告：

```text
outside=[
  reverse_agent/control_plane/evidence_source.py,
  reverse_agent/control_plane/report_binding.py
]
```

结论：上一轮实现不满足自身授权边界，不能接受。

修复原则：

- 新 Decision 显式授权保留并修复这两个文件；
- 不修改 GitHub workflow 来绕过门禁；
- 不降低 path scope 检查强度。

---

## F2 — execution_log 仍不是可信的机器执行证据

严重度：`BLOCKING`

当前 execution log 声称：

```text
source = machine_generated_recorder
generated_at = 2026-07-21T08:07:45Z
```

但记录中的命令时间为：

```text
2026-07-21T19:30:00Z
至
2026-07-21T20:13:03Z
```

这些命令时间晚于日志生成时间，也晚于独立审计观察时间。

因此，即使 digest 已改成 64 位十六进制，日志仍不能证明命令真实执行。

当前 `EvidenceRecorder.record()` 仍允许调用方提供：

```text
command
raw_stdout
raw_stderr
exit_code
operations
mutated_paths
started_at
```

它本身不执行命令，也没有把 raw output 持久化为可复核证据。因此调用方仍可构造一份格式正确但事实不真的记录。

修复原则：

```text
record data must be observed, not supplied
```

---

## F3 — authenticity validator 未进入 local seal 的强制路径

严重度：`BLOCKING`

当前 `evaluate_reconciliation()` 主要检查：

- command ID 是否存在；
- command string 是否一致；
- exit code 是否在范围内；
- required command coverage 是否满足。

它没有强制验证：

- 时间不在未来；
- `generated_at >= max(observed_at)`；
- 时间按记录顺序单调；
- raw stdout/stderr 与 digest 对应；
- head SHA 在 Git 对象库中真实存在；
- bootstrap record 是否发生在 bootstrap expiry 之前；
- record 是否由受控 runner 写入。

结果是包含未来时间的 candidate 仍被标记为：

```text
RECONCILED
```

并进一步生成：

```text
LOCAL_RECONCILED
```

修复原则：任何 authenticity 错误必须在 candidate 生成前阻塞。

---

## F4 — bootstrap 生命周期与执行记录冲突

严重度：`BLOCKING`

当前 bootstrap state：

```text
BOOTSTRAP_EXPIRED
expired_at = 2026-07-21T08:48:28Z
```

但 execution log 中仍存在一个：

```text
authority_origin = bootstrap_exception
started_at = 2026-07-21T19:30:00Z
```

该记录发生在 expiry 之后，却仍进入 reconciliation subject。

修复原则：

- bootstrap authority 必须由 persisted state 和实际时间共同决定；
- caller 不能自行选择 `authority_origin`；
- expiry 后任何 bootstrap record 立即阻塞；
- bootstrap record 不得充当 normal-plan completion evidence。

---

## F5 — AuthorizedRiskPolicyProvider 尚未接入真实工作流

严重度：`BLOCKING`

`AuthorizedRiskPolicyProvider` 已存在，但实际工作流仍然：

1. 在 `load_work_item_node()` 中创建不含 Decision、round、policy digest 的 `WorkflowIdentity`；
2. 由调用方在 state 中提供 `risk_policy_snapshot`；
3. `classify_risk_node()` 在 identity 字段缺失时回退使用 policy 自己的 Decision/round；
4. classify node 没有比较 workflow identity 中的 `policy_digest`；
5. provider 的 `verify()` 没有进入 graph runtime。

因此 provider 只是独立模块和单元测试，不是运行时信任根。

修复原则：

```text
active Decision
→ AuthorizedRiskPolicyProvider
→ bound WorkflowIdentity
→ verified RiskPolicySnapshot
→ classify_risk
```

调用方不能自行注入政策。

---

## F6 — command-bound mutation grant 尚未进入 transition gate

严重度：`BLOCKING`

`validate_mutation_grants()` 已实现，但 `validate_transition()` 仍先依据全局：

```text
generated_artifact_paths
```

把所有生成物路径从 allowed-scope 与 path-risk 检查中排除。

这仍然是全局路径豁免，不是命令级授权。

修复原则：

- 删除全局 generated artifact exemption；
- 每个 execution record 的所有 mutated paths 都必须匹配该 command ID 的 `produced_artifacts` 或 `allowed_mutated_paths`；
- `generated_artifact_paths` 只能作为产物目录清单，不能授予写权限；
- mutation grant 检查必须进入 pre/post gate 的正式结果。

---

## F7 — report binding 数据结构未接入实际报告生成

严重度：`BLOCKING`

当前报告仍然绑定：

```text
head_sha = c97edca2...
changed_files_count = 1
changed file = project_state/decision_packet.md
```

没有覆盖实现提交 `c3f053a...` 修改的代码、测试和 gate 产物。

当前 changed-file inventory 和 remote observation 也仍指向 Decision commit，而不是实现 subject。

虽然 `report_binding.py` 已建立，但实际 `transition-report` 输出没有使用 subject tree digest、subject diff digest 和 local seal digest。

修复原则：报告必须绑定内容 subject，而不是伪装成最终远端 HEAD。

---

## F8 — 本地 seal 状态与远端门禁事实冲突

严重度：`BLOCKING`

当前仓库同时声称：

```text
local_execution_seal.status = LOCAL_RECONCILED
execution_log.gate_status = PASSED
report.local_status = LOCAL_VALIDATED
```

但 exact-head：

```text
CI = success
State Gate = failure
Decision Preflight = failure
```

本地 seal 可以只证明本地内容，但当前本地内容本身仍有 scope 与证据真实性问题，因此不能继续保留 `LOCAL_RECONCILED`。

修复原则：旧 seal、candidate、execution log 必须标记为 superseded 或重新生成，不能沿用。

---

# 3. 本轮总目标

完成以下无循环证明链：

```text
active Decision
→ generated command plan
→ trusted command runner executes exact plan entry
→ raw evidence stored content-addressably
→ execution record derived from observation
→ authenticity validation
→ command-bound mutation validation
→ local reconciliation candidate
→ local content seal
→ implementation commit
→ exact-head remote checks
→ independent PR publication seal
```

本轮完成后，不再继续扩展治理架构。

---

# 4. Phase A — 修正授权范围并废止旧证明

## 4.1 新 Decision 必须显式授权

新增或保留：

```text
reverse_agent/control_plane/evidence_source.py
reverse_agent/control_plane/report_binding.py
reverse_agent/control_plane/evidence_recorder.py
reverse_agent/control_plane/local_seal.py
reverse_agent/control_plane/command_authority.py
reverse_agent/control_plane/transition.py
reverse_agent/architecture/policy_provider.py
reverse_agent/architecture/contracts.py
reverse_agent/workflows/development_graph.py
reverse_agent/workflows/nodes/load_work_item.py
reverse_agent/workflows/nodes/classify_risk.py
reverse_agent/project_gate.py
```

只允许与本计划直接相关的测试和 gate 产物。

## 4.2 旧产物处理

以下产物不得继续作为本轮通过证据：

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

新实现必须从空 execution subject 开始重新生成。

---

# 5. Phase B — Trusted Command Runner

## 5.1 唯一执行入口

实现一个受控入口，例如：

```text
python -m reverse_agent.project_gate transition-run-command \
  --state-dir project_state \
  --command-id <ID>
```

该入口必须：

1. 从当前 command plan 按 command ID 读取命令；
2. 拒绝调用方传入替代 command string；
3. 在执行前读取真实 UTC 时间和 Git HEAD；
4. 自己启动 subprocess；
5. 捕获 raw stdout/stderr；
6. 执行后再次读取 UTC 时间和 Git HEAD；
7. 通过 Git diff/status 计算实际 mutated paths；
8. 计算真实 SHA-256；
9. 写入 raw evidence；
10. 原子追加 execution record。

调用方不得直接传入：

```text
started_at
observed_at
head_before
head_after
stdout_digest
stderr_digest
raw_stdout
raw_stderr
command
authority_origin
```

## 5.2 Raw evidence storage

建议目录：

```text
project_state/gates/evidence/<record_id>/stdout.bin
project_state/gates/evidence/<record_id>/stderr.bin
project_state/gates/evidence/<record_id>/metadata.json
```

metadata 必须保存 raw evidence 相对路径和 digest。

禁止把 raw evidence 仅保存在临时内存中后丢弃。

## 5.3 Record identity

每条记录至少绑定：

```text
record_id
command_id
plan_digest
decision_id
round_id
sequence
started_at
observed_at
head_before
head_after
stdout_digest
stderr_digest
raw_stdout_path
raw_stderr_path
mutated_paths
authority_origin
```

---

# 6. Phase C — Authenticity Gate

candidate 生成前必须逐条检查：

1. RFC3339 UTC 格式；
2. `started_at <= observed_at <= evaluation_time + tolerance`；
3. record sequence 时间单调；
4. execution log `generated_at >= max(observed_at)`；
5. Git SHA 格式正确；
6. Git SHA 对象可被仓库解析；
7. stdout/stderr 文件存在；
8. raw bytes digest 与 record 完全一致；
9. command ID、command string、plan digest 一致；
10. bootstrap authority 与 expiry 时间一致；
11. normal record 不能冒充 bootstrap；
12. bootstrap record 不能满足 normal required command。

任一失败：

```text
candidate.status = BLOCKED
local seal = LOCAL_RECONCILIATION_BLOCKED
```

---

# 7. Phase D — Command-Bound Mutation Enforcement

每条 command plan entry 增加或使用：

```text
allowed_mutated_paths
produced_artifacts
```

规则：

1. 所有 observed mutated path 必须属于该 command 的授权集合；
2. 不能只因为路径位于 `project_state/gates/**` 就自动豁免；
3. generator command 只能生成自己声明的 artifact；
4. report command 不能修改 command plan；
5. command-plan generator 不能修改 report；
6. evaluator 只能生成 candidate；
7. sealer 只能生成 local seal；
8. recorder 只能写 evidence store 和 execution log；
9. forbidden paths 永远优先于 produced-artifact grant。

`validate_mutation_grants()` 必须进入正式 gate 结果，并有负向测试。

---

# 8. Phase E — Runtime Risk Policy 真正接线

## 8.1 Graph construction

`build_development_graph()` 必须接收可信 provider 或由受控 factory 从 active Decision 创建 provider。

禁止调用方直接把任意 policy snapshot 放进初始 state。

## 8.2 Work item loading

`load_work_item_node()` 必须通过 provider 生成：

```text
WorkflowIdentity(
  decision_id,
  round_id,
  policy_digest
)
```

并将 provider 生成的 canonical snapshot 写入 state。

## 8.3 Risk classification

`classify_risk_node()` 必须拒绝：

- identity 缺少 Decision ID；
- identity 缺少 round ID；
- identity 缺少 policy digest；
- snapshot digest 与 identity 不一致；
- provider verify 失败；
- caller supplied snapshot 与 authorized snapshot 不一致。

删除当前“identity 缺失时回退使用 policy 自身 ID”的行为。

## 8.4 端到端测试

必须通过完整 graph 证明：

1. workflow path 自动升级到 R2；
2. binary/secrets path 自动升级到 R3；
3. 降低 path-risk rule 后被 provider 拒绝；
4. 替换 policy digest 后被拒绝；
5. 使用旧 Decision policy replay 被拒绝；
6. 未提供 policy 的调用方不能绕过 provider。

---

# 9. Phase F — Report Subject Binding

## 9.1 Local subject

本地报告绑定：

```text
activation_base_sha
implementation_subject_paths
subject_tree_digest
subject_diff_digest
local_seal_digest
```

`implementation_subject_paths` 应包含本轮真实代码和测试修改，不包含：

- Decision 本身；
- roadmap；
- 自动生成的 report/gate artifact；
- remote observation。

## 9.2 Changed-file inventory

必须区分：

```text
implementation_paths
generated_artifact_paths
governance_paths
```

不得再只列 `decision_packet.md`。

## 9.3 Local report status

只有以下全部成立时才可写：

```text
LOCAL_RECONCILED
```

- authenticity gate 通过；
- mutation grants 通过；
- required local commands 覆盖；
- focused tests 通过；
- full diagnostic 如实记录；
- local seal digest 匹配；
- report subject binding 完整。

否则必须写：

```text
LOCAL_BLOCKED
```

---

# 10. Phase G — External Publication Seal

本地实现完成后：

```text
commit implementation
→ push branch
→ stop modifying branch
→ independent audit exact HEAD
```

独立审计检查：

```text
CI
State Gate
Decision Preflight
```

最终 publication seal 只写入 PR comment，至少包含：

```text
subject_head_sha
local_seal_digest
subject_tree_digest
CI run id + conclusion
State Gate run id + conclusion
Decision Preflight run id + conclusion
observed_at
auditor verdict
```

任一检查失败：

```text
REWORK_REQUIRED
```

全部成功且本地 seal 可信：

```text
ACCEPTED_FOR_MERGE_REVIEW
```

不得在 publication seal 后再提交报告。

---

# 11. 测试要求

## Evidence authenticity

- 未来 timestamp 被拒绝；
- generated_at 早于 command 被拒绝；
- 非单调时间被拒绝；
- malformed digest 被拒绝；
- raw evidence digest mismatch 被拒绝；
- 不存在的 Git SHA 被拒绝；
- caller supplied command string 被拒绝；
- caller supplied started_at 被拒绝；
- bootstrap expiry 后记录被拒绝；
- 手工 JSON 不能直接进入 seal。

## Mutation grants

- report command 写 command-plan 被拒绝；
- evaluator 写 seal 被拒绝；
- unknown command 写 generated artifact 被拒绝；
- produced artifact grant 不能覆盖 forbidden path；
- 全局 generated path 不再形成豁免。

## Runtime policy

- provider 被完整 graph 使用；
- workflow identity 三项绑定不可为空；
- digest mismatch 被阻塞；
- policy content tampering 被阻塞；
- stale Decision policy 被阻塞。

## Report truth

- implementation inventory 覆盖真实代码和测试；
- generated/governance path 分类正确；
- local report 不包含未观察的 remote success；
- report binding 与 local seal 一致；
- final head 由 external seal 提供。

---

# 12. 建议执行顺序

```text
1. 激活新的 Decision
2. 生成当前 command plan
3. transition-lint
4. transition-preflight --mode pre
5. 修复 scope 与 evidence runner bootstrap
6. 用真实 runner 重新建立空 execution log
7. 关闭 bootstrap
8. 实现 authenticity integration
9. 实现 command-bound mutation enforcement
10. 接入 AuthorizedRiskPolicyProvider 到完整 graph
11. 接入 report subject binding
12. 使用 runner 执行 focused tests
13. 使用 runner 执行 control-plane tests
14. 使用 runner 执行 full diagnostic
15. 使用 runner 执行 report generation
16. evaluate reconciliation
17. seal local
18. git diff --check
19. commit and push once
20. stop for independent exact-head audit
```

---

# 13. 验收条件

本轮只有在以下条件全部满足时才能进入合并审计：

1. exact Decision scope 无越界文件；
2. execution log 全部由 runner 生成；
3. 无未来时间、无手工时间；
4. raw stdout/stderr 可读取并通过 digest 验证；
5. Git SHA 可验证；
6. bootstrap lifecycle 与 record 时间一致；
7. authenticity validator 是 candidate 的硬前置；
8. local seal 不接受手工构造记录；
9. mutation grant 绑定 command ID；
10. 全局 generated artifact exemption 已删除；
11. policy provider 接入完整 graph；
12. workflow identity 绑定 Decision、round、policy digest；
13. classify node 不再使用自我回退；
14. report 覆盖真实 implementation subject；
15. changed inventory 不再只有 Decision 文件；
16. local seal 为可信 `LOCAL_RECONCILED`；
17. exact-head CI 成功；
18. exact-head State Gate 成功；
19. exact-head Decision Preflight 成功；
20. PR 保持 Draft 且未合并。

任一条件不满足：

```text
REWORK_REQUIRED
```

---

# 14. 本轮之后

本轮通过后，停止 Architecture Spine 治理修复。

下一步不再创建新的治理 Decision，而是在合并 PR #9 后进入独立产品阶段：

```text
Evidence Trust Schema Foundation
```

或先进行一次 BMAD planning adapter 评估。

不得在本轮自动开始上述工作。