# Arize Phoenix — Nerelan 评测恢复、OpenTelemetry、证据与真实成本深度审计

> [研究 Issue #1672](https://github.com/dddd2024/Nerelan/issues/1672) · 2026-11-17 · R1 docs-only · source fixed at 8b409d4531cda2844d5f172119835cfe43ab8a9b

# Arize Phoenix — pinned-source observability / experiment / eval / real-cost reuse audit

STATUS: R1_DOCS_ONLY / static upstream + Nerelan source review
UPSTREAM: Arize-ai/phoenix@8b409d4531cda2844d5f172119835cfe43ab8a9b (main)
NERELAN: dddd2024/Nerelan main@6cb20fc8502fa7ccc1d6a629b0a7a3c8aecf987b
DATE: 2026-11-17
AUTHORITY: NONE; no code execution, third-party installation or model invocation.

## 0. Pre-selection dedup AND lifecycle screening
Read [#1576](https://github.com/dddd2024/Nerelan/issues/1576): **38 existing research-hub comments**. Search Nerelan Issues/PR/code for `Arize Phoenix`, `Arize-ai/phoenix` and `phoenix`: no standalone pinned-source Phoenix audit. Earlier Langfuse/OTel broad landscape and Promptfoo #1606 / PyRIT #1670 overlap the **topic**, not the upstream code and experiment semantics. Do not create duplicate implementation owner issues.

Screened `microsoft/promptflow` first: it was unduplicated but the upstream README fixed at 33a68c9d3cf349d7fdfad1f41969af27543c0406 states **new development not recommended**, Microsoft Foundry/Azure ML retirement April 20, 2027 and runtime image security updates stopped. This candidate was **rejected at preselection** (not deeply researched or recorded as another project study). This audit covers Phoenix **only**.

## 1. Licensing, packaging and maintainability (important)
- [Root LICENSE](https://github.com/Arize-ai/phoenix/blob/8b409d4531cda2844d5f172119835cfe43ab8a9b/LICENSE) + [pyproject.toml](https://github.com/Arize-ai/phoenix/blob/8b409d4531cda2844d5f172119835cfe43ab8a9b/pyproject.toml) explicitly: **Elastic License 2.0**, not OSI Apache/MIT. This license has restrictions on providing software as a hosted/managed service and other conditions. Source-readable != universal permission to copy/ship product components.
- [phoenix-evals/pyproject.toml](https://github.com/Arize-ai/phoenix/blob/8b409d4531cda2844d5f172119835cfe43ab8a9b/packages/phoenix-evals/pyproject.toml) and [its LICENSE](https://github.com/Arize-ai/phoenix/blob/8b409d4531cda2844d5f172119835cfe43ab8a9b/packages/phoenix-evals/LICENSE): **Elastic-2.0**, not Apache; models/evaluators must not be represented as fully permissive reusable SDK.
- [phoenix-client/pyproject.toml](https://github.com/Arize-ai/phoenix/blob/8b409d4531cda2844d5f172119835cfe43ab8a9b/packages/phoenix-client/pyproject.toml), [LICENSE](https://github.com/Arize-ai/phoenix/blob/8b409d4531cda2844d5f172119835cfe43ab8a9b/packages/phoenix-client/LICENSE); [phoenix-otel/pyproject.toml](https://github.com/Arize-ai/phoenix/blob/8b409d4531cda2844d5f172119835cfe43ab8a9b/packages/phoenix-otel/pyproject.toml), [LICENSE](https://github.com/Arize-ai/phoenix/blob/8b409d4531cda2844d5f172119835cfe43ab8a9b/packages/phoenix-otel/LICENSE): Apache-2.0 **package-specific**; check linked dependencies + notices before actual reuse.
- Upstream main is active; no deployment or license eligibility tested. Prefer OpenTelemetry/OpenInference standard interfaces over extracting ELv2 server code.

## 2. Specific code findings and Nerelan dispositions

| Upstream unit | Concrete source observation | Disposition |
|---|---|---|
| [phoenix-otel register](https://github.com/Arize-ai/phoenix/blob/8b409d4531cda2844d5f172119835cfe43ab8a9b/packages/phoenix-otel/src/phoenix/otel/otel.py#L65-L140) | register creates OpenTelemetry TracerProvider, project tag, endpoint, batch/simple processors, optional OpenInference auto-instrument, optional global provider, headers and API key. **Defaults** `auto_instrument=False`, `batch=False`, `set_global_tracer_provider=True`; [TracerProvider](https://github.com/Arize-ai/phoenix/blob/8b409d4531cda2844d5f172119835cfe43ab8a9b/packages/phoenix-otel/src/phoenix/otel/otel.py#L201-L280) defaults simple exporter. | **DIRECT_REUSE_CANDIDATE P1** Apache-2.0 OTEL client package only after version/security review; first prefer already available standard OTel. Instrument spans as supplemental, never Host-authoritative TaskStore truth. Opt-in, local collector, bounded/export drop policy. |
| [Experiment client](https://github.com/Arize-ai/phoenix/blob/8b409d4531cda2844d5f172119835cfe43ab8a9b/packages/phoenix-client/src/phoenix/client/experiments/__init__.py#L17-L84) | run_experiment over versioned dataset, per example/repetition task, separately run evaluators. [resume_experiment L464](https://github.com/Arize-ai/phoenix/blob/8b409d4531cda2844d5f172119835cfe43ab8a9b/packages/phoenix-client/src/phoenix/client/experiments/__init__.py#L464-L500) selects missing/errored example–repetition; [evaluate_experiment L684](https://github.com/Arize-ai/phoenix/blob/8b409d4531cda2844d5f172119835cfe43ab8a9b/packages/phoenix-client/src/phoenix/client/experiments/__init__.py#L684-L728) evaluates existing outputs without re-running task. | **BORROW_PATTERN P0** frozen cohort/repetitions, append-only attempt records, rescore existing evidence, precise missing-vs-failed, no duplicate model calls for scorer-only changes. Not another Goal/Task scheduler. |
| [ExperimentRun API](https://github.com/Arize-ai/phoenix/blob/8b409d4531cda2844d5f172119835cfe43ab8a9b/src/phoenix/server/api/routers/v1/experiment_runs.py#L26-L40) | identity: `experiment_id` + `dataset_example_id` + `repetition_number`; output, start/end, trace_id, error. [L104–163](https://github.com/Arize-ai/phoenix/blob/8b409d4531cda2844d5f172119835cfe43ab8a9b/src/phoenix/server/api/routers/v1/experiment_runs.py#L104-L163): successful run update 409; errored run **replaced in place**, deletes non-human annotations related to previous failed output; preserves human annotations. | **BORROW_PATTERN** separate task outcome from evaluator annotation and surface stale scores. **REJECT exact persistence** for Nerelan: do not delete old verifier results on retry. Use immutable TaskStore attempt identity and append new evaluation revision referencing the new output; preserve human and old automated results. |
| [Missing/failed eval resume](https://github.com/Arize-ai/phoenix/blob/8b409d4531cda2844d5f172119835cfe43ab8a9b/src/phoenix/server/api/routers/v1/experiment_runs.py#L303-L450) | Query returns evaluations absent or with `error IS NOT NULL`, page/filter; failed scorer ≠ scored outcome. [Missing runs](https://github.com/Arize-ai/phoenix/blob/8b409d4531cda2844d5f172119835cfe43ab8a9b/src/phoenix/server/api/routers/v1/experiments.py#L628-L717) returns missing and errored runs, grouped by dataset and repetition. | **BORROW_PATTERN P0** independent `TASK_EXECUTION_DONE` vs `VERIFIER_PENDING` / `VERIFIER_ERROR` and resume only missing stage. Preserve user work while retries occur. |
| [Evaluator score](https://github.com/Arize-ai/phoenix/blob/8b409d4531cda2844d5f172119835cfe43ab8a9b/packages/phoenix-evals/src/phoenix/evals/evaluators.py#L160-L239) | `Score(name, score, label, explanation, metadata, kind, direction)` and [Evaluator](https://github.com/Arize-ai/phoenix/blob/8b409d4531cda2844d5f172119835cfe43ab8a9b/packages/phoenix-evals/src/phoenix/evals/evaluators.py#L305-L396) input_schema, kind `human/llm/code`, async adapter and evaluator spans with potentially detailed input/output attributes. | **BORROW_PATTERN P1** small neutral eval schema (score, direction, reason, kind, revision, evidence hash); **NO DIRECT COPY** from Elastic-2.0 eval package without separate license analysis. A judge model is not independent acceptance by itself. |
| [Cost tracking](https://github.com/Arize-ai/phoenix/blob/8b409d4531cda2844d5f172119835cfe43ab8a9b/src/phoenix/server/cost_tracking/span_cost_calculator.py#L1-L43) | Uses span attributes, run start_time, model store/current token prices, calculates SpanCost or **None** if missing. This is **token/price-estimated** cost, not proof provider settled charges. | **REJECT as authoritative billing**. Magpie usage requests/account settlement owns actual cost; Phoenix-style span cost remains `ESTIMATED`, `UNKNOWN`, or auxiliary reconciliation diagnostic. Include all failed attempts, verifier, router, subscription quota. |
| [Telemetry privacy](https://github.com/Arize-ai/phoenix/blob/8b409d4531cda2844d5f172119835cfe43ab8a9b/src/phoenix/server/api/redaction.py#L1-L124) | Request GraphQL argument/input redaction, schema-driven; distinct from instrumented LLM prompt/response confidentiality. `phoenix.otel.register(auto_instrument=True)` can propagate tool/LLM spans. | **BORROW_PATTERN P0** pre-export allowlist/redaction and never raw secrets; **REJECT** assumption GraphQL-layer redaction universally sanitizes prompt bodies, tool results, or token headers. Default instrumentation off. |
| [Experiment runner](https://github.com/Arize-ai/phoenix/blob/8b409d4531cda2844d5f172119835cfe43ab8a9b/src/phoenix/server/daemons/experiment_runner.py) | Full background scheduler, per-experiment state-machine, rate-limit token buckets, retries, work items and model calls. | **REJECT RUNTIME CLONE**. Nerelan already has TaskStore durable coordination, GoalService long-run retry and Magpie quota routing. Do not add second scheduler/provider client or store. |
| [Experiment scope](https://github.com/Arize-ai/phoenix/blob/8b409d4531cda2844d5f172119835cfe43ab8a9b/packages/phoenix-client/src/phoenix/client/resources/experiments/types.py#L128-L150) | TestCase/execution object identity, eval run references, evaluator interface; process-level variants have explicit identities. | **BORROW_PATTERN P1** plan/fixture version and evaluator revision with evidence. One logical task/fixture/repetition ≠ many retry attempts; don't conflate. |

## 3. Current Nerelan code (fixed main)
- [run_store.py](https://github.com/dddd2024/Nerelan/blob/6cb20fc8502fa7ccc1d6a629b0a7a3c8aecf987b/reverse_agent/platform_v1/run_store.py): SQLite authoritative Task/Run/event and idempotency, durable receipts (already). No replacement.
- [goal_service.py](https://github.com/dddd2024/Nerelan/blob/6cb20fc8502fa7ccc1d6a629b0a7a3c8aecf987b/reverse_agent/platform_v1/goal_service.py): persistent Owner-scoped Goal→Spec→Plan→Tasks, retry/reconcile (already).
- [task_runtime.py](https://github.com/dddd2024/Nerelan/blob/6cb20fc8502fa7ccc1d6a629b0a7a3c8aecf987b/reverse_agent/platform_v1/task_runtime.py): ExecutorRouter and deterministic fixture executor (already).
- [magpie.py](https://github.com/dddd2024/Nerelan/blob/6cb20fc8502fa7ccc1d6a629b0a7a3c8aecf987b/reverse_agent/model_access/magpie.py): default-off quota observation; incomplete request-level settlement, tracked under #1342. Phoenix's price estimates do not repair it.
- [capability_registry.py](https://github.com/dddd2024/Nerelan/blob/6cb20fc8502fa7ccc1d6a629b0a7a3c8aecf987b/reverse_agent/platform_v1/capability_registry.py): metadata-only Pack declarations; no arbitrary plugin loading.
- Existing owners: [#1527](https://github.com/dddd2024/Nerelan/issues/1527) real Agent×model harness eval; [#379](https://github.com/dddd2024/Nerelan/issues/379) champion/challenger independent verification; [#1267](https://github.com/dddd2024/Nerelan/issues/1267) all-in cost; [#1342](https://github.com/dddd2024/Nerelan/issues/1342) Magpie true usage and audit; [#280](https://github.com/dddd2024/Nerelan/issues/280) trace/activity UX; [#253](https://github.com/dddd2024/Nerelan/issues/253) Pack; [#447](https://github.com/dddd2024/Nerelan/issues/447) egress privacy. No new runtime owner.

## 4. Proposed reduced Nerelan evaluation & telemetry contract
```text
BenchmarkCohort = immutable dataset SHA + frozen task IDs + scenario/repetition set
Attempt = goal_id, task_id, attempt_id, executor/version, model_binding,
          planned_fixture_id, started/ended, host receipt IDs, trace_id?
Evaluation = attempt_id, evaluator_id/revision, criterion_digest, evidence_hash,
             verdict {PASS, FAIL, UNKNOWN, ERROR}, source {code,human,llm},
             explanation_redacted, recorded_at
PriceObservation = attempt_id, estimate_usd?, settled_usd?, status
                   {SETTLED, ESTIMATE_ONLY, UNKNOWN}, magpie_request_ids[]
```
Trace/Span annotations may describe *observed* Agent behavior, but must not certify authorization, task completion, billing or allow reading sealed hidden verifier inputs. Every evaluation revision is append-only and attributable, not rewritten.

## 5. User-facing outcomes and test matrix (NOT RUN)
T01 3 retries but 1 logical test example; task completion denominator 1, total spend includes 3.
T02 task completed but scorer failed => verifier error, not accepted.
T03 scorer-only revision => reuse immutable output, do not rerun paid model/real external tool.
T04 errored task re-run => preserve old automatic and human evaluator history, attach new output/score separately.
T05 same case with 3 repetitions => 3 planned test units (not 3 retries).
T06 duplicate span export / missing parent => de-dupe telemetry, never double-bill.
T07 missing span price / unknown model => COST_UNKNOWN rather than 0.
T08 Phoenix calculated token-price estimate differs from Magpie settled bill => show both, settled wins.
T09 failure attempts, verification, retries and planner costs all charged to full goal.
T10 secret in LLM prompt/tool args; exporters default off, redacted evidence; GraphQL redaction alone not enough.
T11 tracing collector unavailable => Goal/TaskStore no loss, telemetry marked dropped/unavailable.
T12 score artifact signed by same worker tries to self-approve => reject, Host verifier owns accept.
T13 deleted/revised fixture source data => pin exact original cohort SHA and do not substitute.
T14 session/agent model context includes hidden expected outputs => verifier isolation denies.
T15 batch resume after interrupted eval => only missing/failed evaluator stage reruns, not confirmed side effect.
T16 compare telemetry/experiment overhead vs baseline: accepted task fraction, p95 delay, memory, network, real charge and redaction omissions.
All examples are planned tests, not executed.

## 6. Priorities and decision
P0: Stable dataset-example/repetition/attempt identity, no evaluator error-as-pass, append-only evaluator revisions, correct cost facts vs estimate, zero-leak telemetry gate.
P1: Opt-in OpenTelemetry/OpenInference tracing, low-overhead local export and activity UI, detached eval/re-eval over existing immutable evidence.
P2: Optional Phoenix external visualization via permissive Apache-2.0 client/OTel adapter only after offline prototype, threat model, license and actual A/B. No default always-on backend.
ALREADY_IMPLEMENTED: central TaskStore, GoalService, route/authorization, independent verifier ownership and Magpie resources.
REJECT: ELv2 server/evaluator code direct cloning as unrestricted Open Source, second orchestration DB/scheduler, Phoenix price-based billing, unattended auto-instrumentation of secrets, evaluator rewriting old evidence.
DEFER: shipping Phoenix UI/service/hosted model observability or automatic eval LLM scoring.

No local code, tests, CI, model/provider bills, secret or deployment changes. Research R1 only and Draft PR; independent reviewer required for eventual merge.
## 7. 开发者与用户视角：真正有价值的最小模块

### 7.1 让同一个用户任务的多次尝试与多个评分器可解释

Phoenix 的实验 Run 使用 dataset_example_id 和 repetition_number 识别具体实验单元。一个实际 Run 还可附带 trace_id，代表可以从回答质量追溯到工具与模型调用链，而不需要把所有 prompt 明文塞入 Run 表。Nerelan 的 Goal->TaskStore 目前已经拥有持久身份，所以不应该引入第二套 ExperimentRun 表直接驱动 Agent；只需增加固定的 benchmark_case_id / repetition_number / fixture_digest 关联以及只读实验结果投影。

例如用户查看 Agent A + 模型 X 与 Agent B + 模型 Y 哪组更可靠时，应看到同一批固定任务样本、每组的独立验收比例、完整失败原因、所有 attempt 成本，以及每个案例的可展开执行 Span。这个对产品体验的贡献远比新建一个复杂的“实验工作流编辑器”更大。

### 7.2 评分是独立动作，而不是完成任务的别名

Phoenix API 的两个查询区分：
- 缺失的任务 Run 和已有错误 Run：归入待执行的 Run 集合；
- 缺失某个评分器的 Annotation，或者其 error 不为空：归入待评分集合。

它还有 evaluate_experiment / resume_evaluation 接口，允许已完成的真实输出继续接受评分。这对 Nerelan 的独立验收非常有用：应能在不重跑有外部副作用的任务时，修复一个失败的校验器。但注意 Phoenix 内部将原错误 Run 替换时，会删除不再适用的非人工评分注释以保证新输出没有错误沿用。Nerelan 不应复制删除旧数据的方式，而应追加 EvaluationRevision，使用原输入/输出哈希绑定旧评分；新输出对应新 revision，保留整个法证历史。

源证据：
- [ExperimentRun create/upsert](https://github.com/Arize-ai/phoenix/blob/8b409d4531cda2844d5f172119835cfe43ab8a9b/src/phoenix/server/api/routers/v1/experiment_runs.py#L104-L163)
- [Incomplete eval query](https://github.com/Arize-ai/phoenix/blob/8b409d4531cda2844d5f172119835cfe43ab8a9b/src/phoenix/server/api/routers/v1/experiment_runs.py#L303-L449)
- [Incomplete run query](https://github.com/Arize-ai/phoenix/blob/8b409d4531cda2844d5f172119835cfe43ab8a9b/src/phoenix/server/api/routers/v1/experiments.py#L628-L715)
- [Client evaluation API](https://github.com/Arize-ai/phoenix/blob/8b409d4531cda2844d5f172119835cfe43ab8a9b/packages/phoenix-client/src/phoenix/client/experiments/__init__.py#L684-L728)

Nerelan 推荐状态枚举：EVAL_NOT_STARTED、EVAL_RUNNING、EVAL_PASSED、EVAL_FAILED、EVAL_ERROR、EVAL_UNAVAILABLE、EVAL_SUPERSEDED，而不是从模型自评分自动进入 ACCEPTED。

### 7.3 质量与成本的分母必须是不同集合

以四个 planned benchmark cases 为例：
- Case A：Agent 第一次执行超时，第二次执行通过。质量分子只增加 1；真实成本必须累计两次调用。
- Case B：一次完成，评分器失败。不能算独立通过；但模型调用已经付费。
- Case C：任务执行成功、评分失败后修复评分器再次评分；不应重发真实工具操作或再次付费执行相同 Agent。
- Case D：样本未调度。必须留在覆盖率分母中，不能删除它提升仪表盘指标。

Phoenix span-cost 使用 token_usage + 历史/当前 model prices 估计；它既不知道所有失败的请求，也不知道用户订阅/统一账号池的实际套餐消耗。Nerelan 应将指标切成两条账：
- Magpie 请求记录中真实 settled amount 优先，若未知显式标为 UNKNOWN；
- Trace 的 estimated_usd 用作辅助用量或核对，不得覆盖真实账单，也不能把 None 转成 0。

具体建议观测值：goal_id/task_id/attempt_id，model_binding/provider/account_pool_key 的非秘密引用，subagent/executor_kind，trace_id/span_id，magpie_request_id，attempt_status，verification_revision，settled/estimated/unknown cost status。Span 数量不是模型调用次数，Span token 求和需先识别包含/重复聚合的父子跨度，否则会重复计费。

### 7.4 日志/Trace 的数据治理是首要集成门槛

Phoenix 的 OTEL register 可以用简单或批处理 SpanProcessor，开启 auto_instrument 还会追踪已安装的 OpenInference 扩展。这些行为可能包含原始模型 input/output、工具参数、外部文档、文件路径和账户元数据。其服务端 redaction.py 主要处理服务自身 GraphQL 请求字段的敏感信息，不能认定所有发往 collector 的应用 Span 都已经自动去敏。

对 Nerelan 更合适的默认方式：
1. 控制面状态仍通过 TaskStore，只导出 allowlist 字段而非 prompt/tool 全量明文；
2. 明确 opt-in instrumentation，优先现有标准 OpenTelemetry SDK / OpenInference 约定；
3. 对 connector/账号请求只放匿名引用，不输出 Magpie 凭据、Owner grant 秘密或 hidden test 输入；
4. 出口网络由 Host 授权，默认 local collector；remote collection 必须明确同意；
5. collector 离线时不能阻塞 Task 状态落库和系统恢复；显示 TRACE_UNAVAILABLE 而非任务失败；
6. 用 OTel trace_id 关联 TaskStore Receipt 是只读关系，Span 属性永远不提升权限或任务验收事实；
7. 审查客户端包的 Apache-2.0 许可证与实际依赖；不能把 ELv2 eval 服务端框架直接一起打包。

### 7.5 为什么不推荐把 Phoenix 的 daemon 直接接到长期任务服务

Upstream experiment_runner.py 明确包含后台 experiment 调度、内部待执行 work item、LLM client 适配、rate limit token buckets、重试和持久化工作；这些实现已与 Nerelan TaskStore/GoalService/Magpie 部分重叠。引入它会制造两个运行事实源，导致任务已完成但评分器重试触发第二轮真实模型调用、额度被重复结算、恢复逻辑互相干扰。

可以仅借鉴其管理思想：任务执行与评分执行两个 independently resumable phases，同时只在依赖阶段成功且目标不变时继续评分。实际调度仍由 Nerelan 生产组件完成。

### 7.6 与此前项目相比，本轮真正的新收获

| 已有深审 | 核心结论 | Phoenix 新的增量 |
|---|---|---|
| Promptfoo #1606 | 测试框架和评分场景 | 可独立恢复的实验 Run vs Evaluation Annotation；Trace 桥接和 license-aware client |
| PyRIT #1670 | 攻击结果四态和逻辑单元统计 | 输出重运行时自动评分与人工注释不同的失效策略；后续单独重评 |
| Agent Lightning #1662 | RL 轨迹和训练样例控制 | 实验数据行、重复次数、外部评估关联与 OTel 追踪，不涉及训练模型 |
| NeMo Guardrails #1665 | 实时工具检查 | 调用证据可以被验证器评价，但 Trace 本身不是授权决策 |
| Langfuse/OTel 泛调研 | 统一 Trace 标准 | Phoenix 实际 Apache client vs Elastic server/eval 包边界，以及已读具体的 upsert/delete/incomplete 查询 |

Prompt flow 被弃用的候选已在本轮前置筛选终止，不形成第二个研究报告。

## 8. 最小 MVP，分级推进并设验证门槛

M0 — provider-free fixture: 按 cohort_id、case_id、repeat 和 AttemptID 固定一个微型封闭数据集；模拟失败/重跑/评分失败/重新评分/错误状态和 cost unknown，复用 TaskStore，不启动 Agent 或外部费用。

M1 — verifier revision: 同一个已完成 Attempt 在 2 个评分版本下单独评价；验证旧结果完整保留且旧 evaluator 无法自我提高 Owner 授权；评估错误不算 ACCEPT。

M2 — local OTel projection: 导出最少必要的已去敏 spans，模拟 collector 挂掉，核实 TaskStore 独立存续。对用户只显示 activity stream 和可解释性，不展示原始 chain-of-thought、隐藏题解和秘密。

M3 — real Agent×Model bakeoff: 固定同一任务集，按实际执行器+模型绑定记录多次尝试和 Magpie 真实用量，独立验收+成本全纳入；比较是否能改善完成率、真正节约成本，而不是只让 dashboard 更漂亮。

M4 — optional external Phoenix visualization: 只有本地评估、许可与数据出境模型通过审查，且额外服务运行成本在真实实验里收益明显时，才以标准 OTEL 协议/Apache client 方式做实验性集成；不建生产默认依赖。

## 9. 没有做的事情

本轮只通过 GitHub 连接读取原项目固定 commit 和 Nerelan 固定 main 的源码、版本声明、license 和研究 owner issues；没有安装 arize-phoenix、phoenix-client、phoenix-otel，也没有启动 Collector、跑实测 span、调用 evaluator/LLM、访问/改变任何账号凭据、进行真实成本 A/B、执行 CI 或独立评审。上面的测试矩阵是后续实施合同，不是成功证据。

**最终裁定：BORROW_PATTERN（评测状态和可审计重评）；DIRECT_REUSE_CANDIDATE（Apache client/otel，可选、需验证）；REJECT（ELv2 服务端全量移植、第二调度器、价格估计替代 Magpie）；DEFER（完整 Phoenix UI/部署）。**
