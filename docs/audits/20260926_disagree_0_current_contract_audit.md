# Audit: DISAGREE-0 当前契约审计 — Disagreement-Aware Multi-Model Collaboration / Governed Arbitration

> Audit material — not execution authority. This document records a PLANNING_ONLY contract audit for GitHub issue #994 (DISAGREE-0 阶段). It does not authorize commands, file changes, runner dispatch, workflow dispatch, sample solving, Web runtime, database work, deletion, migration, closeout, or close-round. Issue #994 明确标注 `PLANNING_ONLY` 且 `EXECUTION_AUTHORITY: NONE`; 本文档只产出规划与审计结论, 严禁修改任何运行时代码。任何实现须另立有界工作项, 按 AGENTS.md Path A 或 Path B 取得授权后执行。本文档不是授权。

> 编码声明: 本文件由文件编辑工具写入(非 shell 脚本), 全部中文为合法 UTF-8。文档语言为简体中文, 保留 issue 原文英文术语。

> 命名惯例: 沿用 `docs/audits/20260707_fast_close_round_key_fix_audit.md` 的 `<YYYYMMDD>_<topic>_audit.md` 惯例(见 `docs/audits/20260707_fast_close_round_key_fix_audit.md:1`)与头部审计性质声明句式(见 `docs/audits/20260707_fast_close_round_key_fix_audit.md:3`)。

> 行号核对声明: 以下每一条 `文件路径:行号` 均已用文件工具实际打开文件核对, 非凭印象编造。行号对应当前工作树的实际内容。

---

## 第 1 节 现有契约映射

契约强度三档定义:
- **强**: 代码强制、fail-closed, 模型自述无法覆盖。
- **中**: 文档与代码部分对齐, 存在未实现部分或仅结构性校验。
- **弱**: 仅 roadmap/文档承诺, 无对应代码路径。

### 1.1 #137 母平台路线图

- **issue 主旨**: 多 Agent manager/worker 编排是母平台能力方向, 当前尚未 operational。
- **现有实现位置**:
  - `docs/architecture/HISTORICAL_DEBT_MATRIX.md:90` — `| #137 | current mother-platform/capability direction | **KEEP** | resume after modernization core |`, 标注为保留方向。
  - `docs/architecture/HISTORICAL_DEBT_MATRIX.md:121` — `| trusted Draft PR publication controller | NO | NO | YES (#135) |`, 受信任 Draft PR 发布控制器尚未实现。
  - `docs/architecture/HISTORICAL_DEBT_MATRIX.md:123` — `| multi-Agent manager/worker orchestration | NO | NO | YES (#126/#137 Phase 5) |`, 多 Agent 编排明确标注为 Phase 5 且当前为 NO。
  - 唯一存在的多角色执行是**串行** `planner -> coder -> reviewer`: `reverse_agent/platform_v1/durable_execution.py:1806`(`for role in ("planner", "coder", "reviewer"):`)、`reverse_agent/platform_v1/opencode_executor.py:140`(`_SEQUENTIAL_ROLES = ("planner", "coder", "reviewer")`)。
- **现有契约强度**: **弱**。仅有 roadmap 语义承诺; 无并行编排, 无多模型协作契约, 多 Agent 编排在债务矩阵中标注为 NO。

### 1.2 #179 独立验证

- **issue 主旨**: 验证必须独立于执行者自述, 由可信证据判定, 而非由模型声称决定。
- **现有实现位置**:
  - `reverse_agent/platform_v1/acceptance.py:1` — 模块声明 `"""Deterministic accepter: derive acceptance from evidence, not agent claims.`。
  - `reverse_agent/platform_v1/acceptance.py:130` 与 `reverse_agent/platform_v1/acceptance.py:142` — 测试/CI 失败时 `agent_completion_claim` 只能追加 `(agent_claim_ignored)` 备注, 无法翻转 REWORK_REQUIRED 结论(见 `acceptance.py:127` 注释 `# 5. Tests (agent claim cannot override)` 与 `acceptance.py:139` `# 6. CI checks (agent claim cannot override)`)。
  - `reverse_agent/platform_v1/contracts.py:343` — `agent_completion_claim is recorded but never used to override Git or test failures.`。
  - `reverse_agent/platform_v1/contracts.py:346` — `F9: collection_mode and provenance can only be set to live/trusted by the internal trusted collector factory`。
  - `reverse_agent/platform_v1/evidence_adapter.py:3` — `F14: The production live collector (:func:`collect_live_evidence`) owns truth.`。
  - `reverse_agent/platform_v1/evidence_adapter.py:244` — `"""Create live evidence — the sole trusted factory.`(F27, 见 `evidence_adapter.py:246`)。
  - `reverse_agent/platform_v1/opencode_executor.py:16` — `Deterministic git diff --check validation runs independently of the` 模型自述状态。
- **现有契约强度**: **强**。测试/CI 失败不可被模型自述覆盖, 且有 fail-closed 代码路径支撑。
- **缺口**: 独立的是"确定性检查", 不是"另一个模型"。#179 与 #811 的模型级独立评审尚无对应实现。

### 1.3 #252 自适应/证据驱动路由

- **issue 主旨**: 按证据与能力选择模型/供应商/执行器。
- **现有实现位置**:
  - `reverse_agent/platform_v1/task_runtime.py:388`(`class ExecutorRouter:`)、`task_runtime.py:394`(注册表只有 `deterministic_fixture` 与 `opencode`)、`task_runtime.py:411`(`dispatch_execute` 仅按 `executor_kind` 精确取工厂, **无能力/证据评分, 无运行时切换**)。
  - `reverse_agent/platform_v1/binding_resolver.py:84`(`def resolve(`)、`binding_resolver.py:96`(`raise BindingResolutionError("binding_disabled")`)、`binding_resolver.py:112`(`connection_disabled`)、`binding_resolver.py:120`(`executor_not_operational`)——均为 fail-closed 拒绝, 不做能力评分。
  - `reverse_agent/platform_v1/capability_registry.py:1`(`deliberately metadata, not a package manager or plugin runtime`)、`capability_registry.py:34`(`BUILTIN_CAPABILITIES`)、`capability_registry.py:77`(`def response` 只输出能力清单与 digest)。
  - `docs/roadmap/model_access_quota_budget_plan.md:18`(`eventually become one input to model/provider selection`——即当前**尚未**成为输入)、`docs/roadmap/model_access_quota_budget_plan.md:38`(`Do not create a second unrelated API-key management subsystem`)、`docs/roadmap/model_access_quota_budget_plan.md:46`(`Do not reimplement generic token/cost accounting or generic gateway routing`)。
  - 配额/预算目前只是**准入**资源, 不参与选择: `reverse_agent/platform_v1/autonomy.py:96`(`window_budget_summary`)、`autonomy.py:153`(`max_token_units`)、`autonomy.py:172`(`enforcement_class` 二选一 `HARD_ADMISSION_ENFORCED`/`POST_RUN_OBSERVED`)。
- **现有契约强度**: **弱到中**。路由存在但是**静态注册表查找**; 证据驱动/能力驱动选择只有 roadmap 目标, 无代码路径。
- **关键约束**: 现有架构明确禁止再造第二个路由器, 见 `AGENTS.md:7`(`reuse mature runtimes rather than copying them`)与 `docs/roadmap/model_access_quota_budget_plan.md:46`。

### 1.4 #379 Champion-Challenger

- **issue 主旨**: 挑战者-冠军的对抗式评估机制。
- **现有实现位置**: 仓库内**无任何** `champion`/`challenger` 符号(全库 grep 无命中)。最接近的确定性对照机制在旧域: `reverse_agent/strategies/compare_aware_search.py:4205`(`any_runtime_disagreement = any(`)、`compare_aware_search.py:4332`(`"recommendation": "stop_and_fix_first" if any_runtime_disagreement else "demote"` )、`compare_aware_search.py:4375`(`if not helper_runtime_consistent or any_runtime_disagreement`)、`compare_aware_search.py:4413`(`"expected_improvement_signal"` 含 `without compare_semantics disagreement`)。
- **现有契约强度**: **弱**。不存在当前平台(platform_v1)内的 Champion-Challenger 契约; `compare_aware_search` 属 legacy reverse 域, 且其"disagreement"是**运行时指标一致性**判定, 不是模型结论分歧。
- **审计结论**: #379 在当前平台中**没有对应实现**, 这是 DISAGREE-0 的主要空白。

### 1.5 #653 默认验证只检查补丁格式

- **issue 主旨**: 默认验证面只覆盖补丁卫生, 不覆盖功能正确性。
- **现有实现位置**:
  - `reverse_agent/platform_v1/task_runtime.py:72`(`_APPROVED_VALIDATION_COMMANDS` 只有 `git_diff_check`、`git_status_porcelain`)。
  - `task_runtime.py:77`(`VALIDATION_SURFACE_PATCH_HYGIENE`)与 `task_runtime.py:78`(`VALIDATION_SURFACE_FUNCTIONAL`)两个面。
  - `task_runtime.py:81`(命令->面映射)、`task_runtime.py:101`(`validation_command_surface`, 未知命令 fail-closed 为 `UNKNOWN`)、`task_runtime.py:104`(`A zero exit code is not enough to promote patch-hygiene evidence to functional proof`)。
  - `docs/functional-validation.md:113`(`Patch hygiene, functional verification, review readiness and Draft publication remain distinct`)。
  - `docs/functional-validation.md:50`(`Verification requires an actual implementation delta ... at least one executed passing test per check`——功能面要求)。
  - `docs/functional-validation.md:71`(`A deterministic fixture may have FIXTURE_VERIFIED evidence but never verified: true`)。
- **现有契约强度**: **中**。契约本身**准确区分**了两类验证面并 fail-closed, 但默认路径(无 owner 选择 checks)只能产出 PATCH_HYGIENE 证据, 功能正确性默认无证明。
- **审计定位**: #653 是"分歧无法被确定性证据裁决"的根因之一——当验证面停留在补丁卫生时, 模型间的功能分歧没有权威证据可裁。

### 1.6 #811 独立评审 Agent

- **issue 主旨**: 由独立 Agent 进行评审, 与执行者分离。
- **现有实现位置**:
  - `reverse_agent/platform_v1/opencode_executor.py:924`(`_ROLE_REVIEWER_INSTRUCTIONS`): reviewer 非修复角色, 唯一写入 `.reverse-agent-handoff/review.md`, `opencode_executor.py:932` 明确 `Your ONLY authorized write target is`, `opencode_executor.py:939` 明确 `You MUST NOT fix a defect you discover`。
  - `reverse_agent/platform_v1/opencode_executor.py:338`(reviewer 权限块: edit 全 deny 仅放行 `review.md`, bash 仅 `git diff*`/`git status*`, `task`/`webfetch`/`websearch` 全 deny, 见 `opencode_executor.py:346`/`:347`)。
  - `reverse_agent/platform_v1/opencode_executor.py:108`(`class RoleContext:`: `role` 取 planner/coder/reviewer 之一)。
  - `reverse_agent/platform_v1/durable_execution.py:2281`(`elif r == "reviewer":` reviewer 阶段)、`durable_execution.py:2297`(`if reviewer_post != _coder_snap:` 对比 coder 指纹)、`durable_execution.py:2300`(`"classification": "reviewer_product_mutation"`)、`durable_execution.py:2307`(`failure_classification="reviewer_product_mutation"`)。
  - `reverse_agent/platform_v1/task_execution.py:627`(`invalid_review = _validate_review_handoff(` 非 durable 路径同样校验 review handoff)。
- **现有契约强度**: **中**。评审**角色隔离**与**无修复权**是代码强制的(权限配置 + 产品 diff 指纹比对); 但 `review.md` 的**语义内容不被校验**——`reverse_agent/platform_v1/opencode_executor.py:2226`(`"""Validate a bounded handoff file`)的检查项仅为 exists/非符号链接/不越界/常规文件/非空/≤128KiB(见 `opencode_executor.py:2229`-`:2235`), `opencode_executor.py:2253`(`_validate_plan_handoff`)与 `opencode_executor.py:2259`(`_validate_review_handoff`)是同一 `_validate_handoff_file` 的两条薄封装。
- **审计定位**: reviewer 结论是一个**未被任何判定逻辑消费的自由文本**, 是最典型的高价值分歧点。

### 1.7 #812 运行期模型/供应商故障转移

- **issue 主旨**: 运行中模型或供应商故障时的转移。
- **现有实现位置**:
  - `reverse_agent/platform_v1/task_service.py:60`(`FAILURE_CLASSIFICATION_TO_TEST_STATUS` 含 `model_provider_unavailable`(`task_service.py:67`)、`auth_provider_route_failure`(`task_service.py:68`)、`network_provider_failure`(`task_service.py:69`), 全部映射为 `PENDING`)。
  - `reverse_agent/platform_v1/opencode_executor.py:1305`(`"failure_classification": "timeout"` )、`opencode_executor.py:1321`(`failure_classification="timeout"`)、`opencode_executor.py:1335`(`failure_classification="cli_unavailable"`)、`opencode_executor.py:1460`(`failure_classification="deterministic_validation_failure"`)、`opencode_executor.py:1648`(`classification = "server_transport_failed"`)。
  - `reverse_agent/platform_v1/task_runtime.py:399`(`def register`)、`task_runtime.py:405`(`def replace`)——注册表可替换, 但**替换是部署期动作, 不是运行期转移**。
  - `reverse_agent/platform_v1/binding_resolver.py:20`(`DEFAULT_MODEL_CONTROL_URL = "http://127.0.0.1:8765"`, 单一路由目标)、`binding_resolver.py:21`(`DEFAULT_TIMEOUT_SECONDS = 3.0`)。
  - `reverse_agent/model_access/provider_usage.py:1`(`Provider-neutral usage/quota contracts and provider-free parsers.`)。
  - `docs/model-access.md:21`(`"executor": "openhands"` profile 内 `executor` 字段为静态绑定, 见 `docs/model-access.md:15`-`:25` profile 结构)。
- **现有契约强度**: **弱**。故障被**分类并降级为 PENDING**, 等待 owner 决策; 不存在自动 failover 链。
- **审计定位**: 失败分类目前是**执行器自分类的单来源结论**, 无跨模型共识, 也无确定性证据复核。

---

## 第 2 节 概率性分歧决策点清单

> 对"无处理"的情况必须显式写明。每项给出代码位置、结论如何产生、分歧表现形态、当前系统如何处理。

| # | 决策点 | 代码位置 | 结论如何产生 | 分歧形态 | 当前处理 |
|---|---|---|---|---|---|
| D1 | planner 计划内容 | `reverse_agent/platform_v1/opencode_executor.py:891`(`_ROLE_PLANNER_INSTRUCTIONS`); 产物 `.reverse-agent-handoff/plan.md`; 校验 `reverse_agent/platform_v1/durable_execution.py:2222`(`invalid = _validate_plan_handoff`)、`durable_execution.py:2235`(`_handoff_digest`) | 模型自由文本写入唯一允许路径(`opencode_executor.py:329` `".reverse-agent-handoff/plan.md": "allow"`) | 拆分粒度、路径集合、验收分解不同 | **仅结构校验**(`opencode_executor.py:2226`-`:2235` 六项 exists/非符号链接/不越界/常规文件/非空/≤128KiB), 语义正确性**无处理** |
| D2 | coder 实现选择 | `reverse_agent/platform_v1/opencode_executor.py:906`(`_ROLE_CODER_INSTRUCTIONS`); 权限 `opencode_executor.py:355`(`"coder"` 仅 deny 危险命令)、`opencode_executor.py:373`(`does NOT install a wildcard product edit deny`) | 模型自主选择编辑范围与方案 | 不同实现路径、不同文件集合 | 只有"是否有产品 diff"门(`durable_execution.py:2267` `if not _coder_snap:`、`durable_execution.py:2277` `failure_classification="no_coder_product_diff"`); 方案优劣**无处理** |
| D3 | reviewer 评审结论 | `reverse_agent/platform_v1/opencode_executor.py:924`(`_ROLE_REVIEWER_INSTRUCTIONS`)、`opencode_executor.py:932`(唯一写目标 `review.md`); 校验 `reverse_agent/platform_v1/durable_execution.py:2281`(`elif r == "reviewer":`)、`durable_execution.py:2282`(`invalid_rev = _validate_review_handoff`) | 模型自由文本写入 `review.md` | accept / rework / block 的分歧 | **无处理**: review 内容不被解析、不进入任何状态机; reviewer 无权修复(`opencode_executor.py:939`) |
| D4 | verifier 功能验证结论 | `reverse_agent/platform_v1/capability_registry.py:49`(`"deterministic-verifier"` 能力)、`reverse_agent/platform_v1/task_runtime.py:72`(allowlist 命令) | 由 allowlist 命令退出码产生, 非模型产生 | 确定性结果 vs 模型声称; 或补丁卫生被误读为功能通过 | 部分处理: 面分离 fail-closed(`task_runtime.py:101`、`task_runtime.py:104`); 但跨模型"我认为测试覆盖了"这类分歧**无处理** |
| D5 | acceptance 与 goal completion evidence | `reverse_agent/platform_v1/acceptance.py:32`(`def evaluate_acceptance`)、`acceptance.py:38`(决策序 1-7)、`acceptance.py:49`/`:54`/`:79`/`:109`/`:119`/`:128`/`:140`/`:153`; `reverse_agent/platform_v1/goal_service.py:52`(`completion_scope: EXECUTION_ONLY`)、`goal_service.py:53`(`remote_acceptance: NOT_OBSERVED`) | 完全确定性: 策略->绑定->路径范围->diff->测试->CI | 模型声称完成 vs 确定性判定 | **处理充分**: 模型自述不可覆盖(`acceptance.py:130`、`acceptance.py:142`; `contracts.py:343`) |
| D6 | plan revision 判定 | `reverse_agent/platform_v1/goal_service.py:92`(`if goal.revision != expected_revision:`)、`goal_service.py:93`(`goal_revision_mismatch`)、`goal_service.py:101`(`save_goal_plan`); 契约冻结 `reverse_agent/platform_v1/functional_validation.py:119`(`def freeze_contract`)、`functional_validation.py:133`(`functional_contract_conflict`) | 乐观锁 revision 比对 + 契约 digest 比对 | 是否"需要修计划"的判断 | 身份冲突被 fail-closed 拒绝; 但"何时应当修订计划"的**语义判断无处理** |
| D7 | binding/model 选择 | `reverse_agent/platform_v1/binding_resolver.py:84`(`def resolve`); `reverse_agent/platform_v1/task_runtime.py:411`(`def dispatch_execute`); profile `docs/model-access.md:21`(`"executor": "openhands"` 静态绑定) | 部署期静态配置 + loopback 元数据校验 | 哪个模型/供应商适合 | **无运行时选择逻辑**: resolver 只做一致性校验并 fail-closed(`binding_resolver.py:96`/`:112`/`:120`); 无证据驱动评分 |
| D8 | 失败分类 | `reverse_agent/platform_v1/task_service.py:60`(映射表); `reverse_agent/platform_v1/opencode_executor.py:1305`/`:1321`(`timeout`)、`:1335`(`cli_unavailable`)、`:1460`(`deterministic_validation_failure`)、`:1648`(`server_transport_failed`) | 执行器/传输层自分类的字符串常量 | 同为超时但判为 `timeout` vs `network_provider_failure` vs `model_provider_unavailable` | **单来源、无复核**: 直接映射为 PENDING/FAIL(`task_service.py:60`), 持久化于 `reverse_agent/platform_v1/run_store.py:352`(tasks 表 `failure_classification TEXT NOT NULL`)、写入口 `run_store.py:3070`(`UPDATE tasks SET failure_classification`)、`reverse_agent/platform_v1/run_read_model.py:618`(`_safe_text(task.failure_classification)`) |
| D9 | 角色越界判定 | `reverse_agent/platform_v1/durable_execution.py:2237`(`if planner_post != baseline:`)、`durable_execution.py:2240`(`planner_product_mutation`)、`durable_execution.py:2297`(`if reviewer_post != _coder_snap:`)、`durable_execution.py:2300`/`:2307`(`reviewer_product_mutation`); 指纹采集 `reverse_agent/platform_v1/opencode_executor.py:2271`(`def _collect_product_diff`) | 确定性产品 diff 指纹比对 | 模型自述"我只读了" vs 指纹事实 | 处理充分且确定性; 但**这是指纹判定, 不是模型判定**, 不存在真分歧 |

**小结**: D4/D5/D6/D9 属于"模型结论 vs 确定性证据"型; D1/D2/D3/D7 属于"模型 vs 模型"型且**当前完全无处理**; D8 是"单来源分类"型。模型 vs 模型型分歧(D1/D2/D3/D7)是 DISAGREE-0 需要填补的核心空白。

---

## 第 3 节 分歧分类

### 3.1 实质性分歧(可升级)

判定必须满足「同一上下文 + 同一目标身份」前提下, 结论**可操作后果不同**。最小证据集合:

1. **身份同一性证据**: 同一 `goal_id` / `goal_revision` / `execution_id` / `base_sha`(参照 `reverse_agent/platform_v1/contracts.py:337`(`class ExecutionEvidence`)的绑定字段语义、`reverse_agent/platform_v1/goal_service.py:92`(`if goal.revision != expected_revision:`)的 revision 语义)。
2. **结论的规范化形式**: 可脱离散文表达的枚举/结构化结论(参照 `reverse_agent/platform_v1/acceptance.py:38`(`Decision order (fail-closed at each step):`)的七步决策序风格, 即有限有序判定)。
3. **后果差异证据**: 两结论会导致不同的状态转移(例如 `ACCEPTED` vs `REWORK_REQUIRED`, 见 `reverse_agent/platform_v1/contracts.py:29`(`VALID_ACCEPTANCE_STATUSES`)。

### 3.2 非实质性分歧(禁止升级)

仅措辞、格式、风格、篇幅、章节顺序、术语偏好差异, 且规范化后结论相同。

最小证据: 规范化映射后两侧结论相等(等价于 `reverse_agent/platform_v1/task_runtime.py:101`(`validation_command_surface`)的"未知即 fail-closed"的反向: 已知等价即等价)。

### 3.3 明确禁止升级的分歧类别

- 措辞/标点/大小写/语言风格、Markdown 排版与表格样式;
- 计划文档章节顺序与措辞, 只要覆盖的路径集合与验收项规范化后相同;
- 任何仅涉及私有思维链/推理过程的差异(见第 5 节 (l));
- 非实质性分歧**禁止**触发二次模型调用、**禁止**消耗升级预算(`reverse_agent/platform_v1/autonomy.py:188`(`max_retries` 0-5)不得用于此)。

### 3.4 关键前提校验(对应验收条目 c)

在声称"真模型分歧"之前, 必须先校验上下文与目标身份是否一致; 不一致时判定为**假分歧**(上下文/目标身份不同), 不得进入仲裁, 也不得计为分歧率。

---

## 第 4 节 标注夹具语料 corpus

### 4.1 JSON Schema

顶层为 `{"schema_version": "1", "cases": [Case, ...]}`。

**Case 字段:**

| 字段 | 类型 | 含义 | 必需 |
|---|---|---|---|
| `case_id` | string | 稳定唯一 ID, 形如 `disagree-0-c01` | 是 |
| `decision_point` | string | 分歧点标识, 取自 D1-D9 | 是 |
| `context_identity` | object | `{goal_id, goal_revision(int), execution_id, base_sha}`; 用于身份同一性校验 | 是 |
| `goal_intent` | string | 被评审的目标意图简述(provider-free 纯文本) | 是 |
| `party_a` | object | `{model_id, provider_id, conclusion_summary, conclusion_normalized, evidence_refs, defect_claims}` | 是 |
| `party_b` | object | 同 `party_a` 结构 | 是 |
| `evidence_refs` | array<object> | 双方共享的权威证据: `{ref_type(one of git_diff_check/test_result/ci_check/allowed_paths/risk_tier), ref_value, authority(one of deterministic/model_claim/absent)}` | 是 |
| `classification` | string(enum) | `REAL_SUBSTANTIVE` / `REAL_EVIDENCE_INSUFFICIENT` / `FAKE_CONTEXT_MISMATCH` / `MINORITY_HARD_DEFECT` / `NO_EVIDENCE_BOTH` / `COSMETIC_ONLY` | 是 |
| `minimal_evidence_for_judgment` | array<string> | 判定该分类所必需的最小证据项 | 是 |
| `escalation_allowed` | bool | 是否允许升级(`COSMETIC_ONLY` 与 `FAKE_CONTEXT_MISMATCH` 必须为 false) | 是 |
| `expected_terminal_state` | string(enum) | 期望显式终态: `RESOLVED_BY_EVIDENCE` / `UNRESOLVED_EXPLICIT_BLOCK` / `NO_ACTION_COSMETIC` / `CONTEXT_MISMATCH_REJECT` | 是 |
| `arbitrator_output` | object | `{decision(enum), bound_refusal(one of null/acceptance_criteria/policy)}`; 仲裁者仅可有界决策输出 | 是 |
| `provenance` | object | `{model_ids, provider_ids}`; 候选与结论必须保留模型与供应商来源 | 是 |
| `private_chain_of_thought` | string(enum) | 固定为 `NOT_STORED` | 是 |
| `notes` | string | 说明(可选) | 否 |

**约束校验规则:**
- `classification == COSMETIC_ONLY` => `escalation_allowed == false` 且 `expected_terminal_state == NO_ACTION_COSMETIC`;
- `classification == FAKE_CONTEXT_MISMATCH` => `escalation_allowed == false` 且 `expected_terminal_state == CONTEXT_MISMATCH_REJECT`;
- `classification == MINORITY_HARD_DEFECT` => 少数方必须持有 `authority == deterministic` 的 `evidence_refs`, 且 `arbitrator_output.decision` 不得为多数票结果;
- 所有 `conclusion_summary` 必须是纯文本, 不得依赖真实模型调用。

### 4.2 标注用例表(12 例, 覆盖 6 类分类)

> 用例为 provider-free 的纯文本结论对, 不需要真实模型调用。

| case_id | decision_point | classification | 纯文本结论对(A / B) | 最小证据 | 期望终态 |
|---|---|---|---|---|---|
| c01 | D3 reviewer | REAL_SUBSTANTIVE(可证据裁决) | A: `review.md 无阻断缺陷, 可进入验收` / B: `patch 引入未处理异常路径, 必须返工` | `git_diff_check` 通过 + 测试失败 1 项(`authority: deterministic`) | RESOLVED_BY_EVIDENCE(取确定性测试失败 -> REWORK_REQUIRED) |
| c02 | D2 coder | REAL_SUBSTANTIVE(可证据裁决) | A: `允许修改 reverse_agent/platform_v1/acceptance.py` / B: `该路径不在 allowed_paths 内, 必须拒绝` | `allowed_paths` 白名单 + 实际 changed_paths(`authority: deterministic`) | RESOLVED_BY_EVIDENCE(超出范围 -> BLOCKED_APPROVAL) |
| c03 | D1 planner | REAL_EVIDENCE_INSUFFICIENT | A: `拆为 2 个串行任务` / B: `拆为 5 个含并行任务` | 无 `max_concurrent_tasks` 之外的规划证据; `reverse_agent/platform_v1/autonomy.py:186` 上限为 8 但无任务数下限依据 | UNRESOLVED_EXPLICIT_BLOCK |
| c04 | D4 verifier | REAL_EVIDENCE_INSUFFICIENT | A: `测试已覆盖需求` / B: `测试未覆盖该分支` | 仅有 `FIXTURE_VERIFIED`, 无 `verified: true`(`docs/functional-validation.md:71`) | UNRESOLVED_EXPLICIT_BLOCK |
| c05 | D8 失败分类 | REAL_SUBSTANTIVE(可证据裁决) | A: `分类为 network_provider_failure(PENDING, 可重试)` / B: `分类为 malformed_executor_output(FAIL, 终止)` | 实际进程退出码 + stdout 摘要(`authority: deterministic`) | RESOLVED_BY_EVIDENCE |
| c06 | D5 acceptance | FAKE_CONTEXT_MISMATCH | A(针对 revision 3): `已验收` / B(针对 revision 5): `未验收` | `goal_revision` 不同(`reverse_agent/platform_v1/goal_service.py:92`) | CONTEXT_MISMATCH_REJECT(禁止升级) |
| c07 | D2 coder | FAKE_CONTEXT_MISMATCH | A(base_sha `abc123...`): `改动正确` / B(base_sha `def456...`): `改动错误` | `base_sha` 不同(`reverse_agent/platform_v1/contracts.py:337`) | CONTEXT_MISMATCH_REJECT(禁止升级) |
| c08 | D3 reviewer | MINORITY_HARD_DEFECT | A+A(2 方, 多数): `无缺陷` / B(1 方): `存在空指针解引用, 附 git diff 行证据` | B 持 `authority: deterministic` 的行级 diff 证据 | RESOLVED_BY_EVIDENCE(多数票不得推翻硬缺陷) |
| c09 | D1 planner | NO_EVIDENCE_BOTH | A: `先改测试再改实现` / B: `先改实现再补测试` | 双方均无任何权威证据(`authority: absent`) | UNRESOLVED_EXPLICIT_BLOCK |
| c10 | D4 verifier | NO_EVIDENCE_BOTH | A: `功能已通过` / B: `功能未通过` | 双方均无执行证据, 无 test_result(`authority: absent`) | UNRESOLVED_EXPLICIT_BLOCK |
| c11 | D1 planner | COSMETIC_ONLY | A: `计划分三节, 标题用小写` / B: `计划分三节, 标题用大写` | 规范化后路径集合与验收项相同 | NO_ACTION_COSMETIC(禁止升级) |
| c12 | D3 reviewer | COSMETIC_ONLY | A: `建议改为表格排版` / B: `建议改为列表排版` | 规范化结论均为"无阻断缺陷" | NO_ACTION_COSMETIC(禁止升级) |

> 覆盖校验: 真分歧可证据裁决(c01/c02/c05)、真分歧证据不足(c03/c04)、假分歧(c06/c07)、少数方硬缺陷(c08)、双方无证据(c09/c10)、非实质性分歧(c11/c12)。六类齐全。

---

## 第 5 节 逐条追溯(a-p)

> 状态三档: `已满足(现有契约)` / `部分满足` / `不满足(需后续工作项)`。本文档阶段为 PLANNING_ONLY, 除 (a)/(j) 外的条目**预期均为不满足或部分满足**, 文档的任务是**如实标注**而非声称达成。

| 项 | 状态 | 追溯与依据 |
|---|---|---|
| (a) 普通低风险工作不自动调用多模型 | **已满足** | 执行器按 `executor_kind` 单一路由(`reverse_agent/platform_v1/task_runtime.py:411`); `orchestration_mode` 默认 `sequential_team`(`reverse_agent/platform_v1/goal_service.py:77`); 无任何自动多模型调用路径 |
| (b) 实质性分歧可脱离原始散文独立表示 | **不满足** | review/plan handoff 仅为自由文本, 校验只有文件级(`reverse_agent/platform_v1/opencode_executor.py:2226`-`:2235`)。corpus schema 中的 `conclusion_normalized` 是设计, 非实现 |
| (c) 声称真分歧前先校验上下文与目标身份 | **不满足** | 无分歧检测逻辑; 但可用的身份字段已存在(`reverse_agent/platform_v1/contracts.py:337`-`:375`、`reverse_agent/platform_v1/goal_service.py:92`) |
| (d) 有权威确定性证据时先尝试证据 | **部分满足** | 验收路径确为证据优先(`reverse_agent/platform_v1/acceptance.py:38` 决策序); 但无"先查证据再叫模型"的分歧裁决环节 |
| (e) 硬缺陷证据的少数方不被多数票推翻 | **不满足** | 当前不存在多数票机制(因此也不存在被推翻风险); corpus c08 定义了期望行为 |
| (f) 二次意见选择尊重能力/策略/本地性/预算/配额 | **不满足** | `reverse_agent/platform_v1/capability_registry.py:1` 明确仅为元数据; `reverse_agent/platform_v1/binding_resolver.py:20` 单一路由; 预算仅在准入侧(`reverse_agent/platform_v1/autonomy.py:153`、`autonomy.py:172`) |
| (g) 仲裁者仅有有界决策输出且无权改写验收标准或策略 | **不满足** | 无仲裁者; 现有 fail-closed 策略是代码常量(`reverse_agent/platform_v1/policy_adapter.py:60`、`reverse_agent/platform_v1/contracts.py:37`), 模型无写入路径, 这一点可作设计约束基线 |
| (h) 分歧升级受显式 token/成本/时间/轮次预算封顶 | **部分满足** | 窗口级预算存在(`reverse_agent/platform_v1/autonomy.py:186`(`max_concurrent_tasks` 1-8)、`autonomy.py:187`(`max_tasks` 1-100)、`autonomy.py:188`(`max_retries` 0-5); `autonomy.py:153`-`:160` token/成本预留); 但不作用于分歧升级, 且缺少时间与轮次维度的分歧专用封顶 |
| (i) 未决案例以显式状态终止而非无限辩论 | **部分满足** | 有界重试已存在(`reverse_agent/platform_v1/contracts.py:23`(`MAX_ATTEMPTS = 2`)、`reverse_agent/platform_v1/acceptance.py:168`(`def can_retry` 仅允许一次)); 但这是执行重试, 不是分歧终态。corpus `UNRESOLVED_EXPLICIT_BLOCK` 是设计 |
| (j) 执行器自述不得推翻独立验收 | **已满足** | `reverse_agent/platform_v1/acceptance.py:130`、`acceptance.py:142`(agent_claim_ignored)、`reverse_agent/platform_v1/contracts.py:343`(`recorded but never used to override`) |
| (k) 每个候选与结论保留模型与供应商来源 | **不满足** | `ExecutionEvidence` 无模型/供应商字段(`reverse_agent/platform_v1/contracts.py:361`-`:375`); 模型标识仅存在于静态 profile(`docs/model-access.md:21`)。corpus `provenance` 字段是设计 |
| (l) 不存储也不展示私有思维链 | **部分满足** | 证据层有递归脱敏与截断(`reverse_agent/platform_v1/opencode_executor.py:147`(`_SECRET_KEYS`)、`opencode_executor.py:202`-`:209`(`_redact_recursively`); `reverse_agent/platform_v1/run_read_model.py:58`-`:66`(secret regex)、`run_read_model.py:87`-`:93`(`_safe_text`)); 且 raw 输出不作为功能证据持久化(`docs/functional-validation.md:45`); 但无"思维链"这一显式命名类型的禁止声明, 需在设计中显式化 |
| (m) 分歧结果可回流路由/评估证据但不得立即成为全局策略 | **不满足** | 路由为静态注册表(`reverse_agent/platform_v1/task_runtime.py:394`), 能力清单位于 `reverse_agent/platform_v1/capability_registry.py:34`; `reverse_agent/platform_v1/roadmap_service.py:3` 明确 `Phase status is always computed from member goal statuses. No code path in this module writes a phase status field`——这是可复用的"不立即成为策略"基线 |
| (n) 领域 Pack 的仲裁规则复用同一底座而非分叉 | **部分满足** | Pack 复用底座已有先例: `reverse_agent/platform_v1/capability_registry.py:3`(`not a package manager or plugin runtime`)、`capability_registry.py:64`(`pack_dir` 加载 JSON manifest)、`capability_registry.py:94`(`reject_sensitive_keys(payload)` 强制安全约束); 但无仲裁规则, 需声明复用 `reverse_agent/platform_v1/policy_adapter.py:60` 而非新建策略引擎 |
| (o) 不引入第二个 TaskStore/调度器/路由器/验证器框架/策略引擎 | **部分满足** | 现有唯一实例: `reverse_agent/platform_v1/run_store.py:313`(`class TaskStore:`)、`reverse_agent/platform_v1/task_runtime.py:388`(`class ExecutorRouter`)、`reverse_agent/platform_v1/acceptance.py:32`(`def evaluate_acceptance`)、`reverse_agent/platform_v1/policy_adapter.py:60`(`def validate_work_item`); `AGENTS.md:7` 与 `docs/roadmap/model_access_quota_budget_plan.md:46` 为禁止再造的书面约束 |
| (p) 不抢占真实供应商试运行/产品化/证据驱动路由关键路径 | **部分满足** | 关键路径已文档化: `docs/functional-validation.md:122`(`Full live user-flow, desktop/Edge and provider acceptance under parent issue #653 remains separate`)、`docs/roadmap/model_access_quota_budget_plan.md:18`(资源信号将成为选择输入); DISAGREE-0 必须声明为旁路审计、不阻塞上述路径 |

---

## 第 6 节 非目标与授权声明

### 6.1 非目标清单(逐条列出)

1. **不做常开模型委员会**(无 always-on multi-model panel): 当前架构仅串行 `planner -> coder -> reviewer`(`reverse_agent/platform_v1/durable_execution.py:1806`), 不引入常驻多模型面板。
2. **不做通用辩论框架**(无 general-purpose debate framework): 不构建无界辩论循环。
3. **不做盲目多数票接受**(no blind majority voting): corpus c08(`MINORITY_HARD_DEFECT`)明确少数方硬缺陷证据不得被多数票推翻。
4. **不做第二个验证器或路由器**: 现有唯一实例为 `reverse_agent/platform_v1/task_runtime.py:388`(`ExecutorRouter`)与 `reverse_agent/platform_v1/acceptance.py:32`(`evaluate_acceptance`); 见 `docs/roadmap/model_access_quota_budget_plan.md:46`(`Do not reimplement generic ... gateway routing`)。
5. **不授予模型自我工具与凭据**: 与 `reverse_agent/platform_v1/opencode_executor.py:877`(`You MUST NOT read credentials, tokens, cookies, authentication configuration, secret stores, or environment secrets`)的凭据禁止、`reverse_agent/platform_v1/binding_resolver.py:29`(`_SECRET_KEYS = {` 黑名单)一致。
6. **不静默变更验收标准**: 与 `reverse_agent/platform_v1/goal_service.py:92`(`if goal.revision != expected_revision:`) revision fail-closed、`reverse_agent/platform_v1/functional_validation.py:133`(`functional_contract_conflict`)契约冲突拒绝一致。
7. **不做无界升级循环**: 与 `reverse_agent/platform_v1/contracts.py:23`(`MAX_ATTEMPTS = 2  # at most one bounded retry`)一致。
8. **不自动合并/发布/部署**: 与 `reverse_agent/platform_v1/contracts.py:37`(`FORBIDDEN_PUBLICATION_OPERATIONS`)、`reverse_agent/platform_v1/publication_controller.py:4`(`It never marks ready, merges, force-pushes, rebases, tags or releases`)一致。

### 6.2 授权声明

本阶段为 `PLANNING_ONLY`, `EXECUTION_AUTHORITY: NONE`。任何实现须**另立有界工作项**, 按 AGENTS.md Path A(`r1-approved` + body digest SHA-256 + 不可变快照)或 Path B(`project_state/decision_packet.md` + `project_state/gates/command_plan.json` + `PRE_EXECUTION_AUTHORIZED`)取得授权后执行。本文档不是授权。

---

## 交付说明

### 唯一交付物

- 路径: `docs/audits/20260926_disagree_0_current_contract_audit.md`(新增, UTF-8, 简体中文, 保留英文术语)
- 写入方式: 文件编辑工具(非 shell 脚本), 以避免控制台管道破坏中文编码。
- 结构: 头部审计性质声明 -> 第 1 节(7 条契约映射) -> 第 2 节(9 项决策点) -> 第 3 节(分歧分类) -> 第 4 节(schema + 12 例) -> 第 5 节(a-p 全 16 项) -> 第 6 节(8 类非目标 + 授权声明) -> 交付说明。

### 验证命令与实际输出

> 说明: 本工作树环境中 `git` 不在默认 PowerShell `PATH` 解析范围内, 需通过完整路径调用。以下使用 `Start-Process` 方式调用 `E:\Program Files\Git\cmd\git.exe`, 工作目录为当前工作树根。

**1) `git status --short`**

```text
?? .reverse-agent-handoff/
?? docs/audits/20260926_disagree_0_current_contract_audit.md
```

解读: `.reverse-agent-handoff/` 为 planner 角色的运行期 handoff 目录(非本任务产物, 属已知运行期 scratch); `docs/audits/20260926_disagree_0_current_contract_audit.md` 为本任务唯一新增文件。无任何已跟踪文件改动。

**2) `git diff --stat`**

```text
(空输出)
```

解读: 新增未跟踪文件不进入 `git diff --stat`(未暂存)。无任何已跟踪文件改动。

**3) `git diff --check`**

```text
(空输出, 退出码 0)
```

解读: 无空白错误(whitespace errors)。

### 自检清单

- [x] 除新审计文件外无其它已跟踪文件改动(`git diff --stat` 为空)
- [x] 中文 UTF-8 无乱码(已用文件工具复读确认, 见下)
- [x] 六节齐全, 第 5 节 16 项(a-p)齐全, 第 4 节 12 例覆盖 6 类分类
- [x] 每个结论都有真实存在的 `文件路径:行号`(均已实际打开文件核对)
- [x] 交付说明含 `git status --short`、`git diff --stat`、`git diff --check` 的实际输出
- [x] 未修改任何运行时/产品源码; 未提交、未推送、未开 PR、未合并、未 tag/release
