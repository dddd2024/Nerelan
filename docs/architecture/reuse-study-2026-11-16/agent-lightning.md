# Agent Lightning v1.0.3 — Nerelan 对照式深度研究

> 研究 Issue [#1662](https://github.com/dddd2024/Nerelan/issues/1662) · 固定源码、静态核查 · 2026-11-17 · R1 documentation-only · no implementation authority

# Agent Lightning 1.0.3 — pinned source: training-quality agent traces, reward hacking controls, rollout ownership

Date: 2026-11-17. Scope: SINGLE_UPSTREAM / PINNED_STATIC_SOURCE_REVIEW / R1_DOCS_ONLY. Execution authority NONE; tests/install/model calls NOT PERFORMED.

Upstream: [microsoft/agent-lightning at 2070bad5113e52f1aa2e5bdba822d4b24b197c05](https://github.com/microsoft/agent-lightning/commit/2070bad5113e52f1aa2e5bdba822d4b24b197c05) (MIT, Python >=3.12, package v1.0.3).
Nerelan current main: [5c69e891e3a559a23e7fd4e3115422c057df4438](https://github.com/dddd2024/Nerelan/commit/5c69e891e3a559a23e7fd4e3115422c057df4438).

## 0. Duplicate check before selecting
Read research hub [#1576](https://github.com/dddd2024/Nerelan/issues/1576) and all **34 archived project comments** before selection, searched Issues/PR/code for agent-lightning, microsoft/agent-lightning and Agent Lightning. No standalone pinned-source Agent Lightning deep audit. Prior Promptfoo #1606, DBOS #1623, Inngest #1648, Mem0 #1655, Deep Agents #1657, Agent Zero #1659 refer to different projects. Focus here is specifically v1.0.3 learning/evaluation harness, not old v0.x API.

## 1. Source-grounded decisions

| Area | Source-level evidence | Verdict for Nerelan |
|---|---|---|
| Architecture | [README](https://github.com/microsoft/agent-lightning/blob/2070bad5113e52f1aa2e5bdba822d4b24b197c05/README.md), [docs/05-basics.md](https://github.com/microsoft/agent-lightning/blob/2070bad5113e52f1aa2e5bdba822d4b24b197c05/docs/05-basics.md): v1.0 3 components = training API gateway, local/K8s Rollout Controller, verl trainer; existing agent talks via OpenAI-compatible endpoint | BORROW_PATTERN evaluation boundary, REJECT second production gateway/dispatcher |
| Trace lineage | [schemas.py L13-L67](https://github.com/microsoft/agent-lightning/blob/2070bad5113e52f1aa2e5bdba822d4b24b197c05/agentlightning/schemas.py#L13-L67), [events.py L46-L66](https://github.com/microsoft/agent-lightning/blob/2070bad5113e52f1aa2e5bdba822d4b24b197c05/agentlightning/server/routes/events.py#L46-L66): rollout_id + attempt_id + typed/open events; request/response, retry/status/usage and reward source fields; RewardData is NOT enforced by Store | BORROW_PATTERN P0: join Nerelan Task/Attempt, model request and independent verifier evidence. Reward text cannot self-authorize acceptance |
| Model proxy | [proxy.py L39-L108 L120-L174 L247-L278](https://github.com/microsoft/agent-lightning/blob/2070bad5113e52f1aa2e5bdba822d4b24b197c05/agentlightning/server/proxy.py): model endpoint stable via rollout-id hash, train/validation parameter rewrite, return_token_ids and logprobs, non-streaming only, captures normal response status/tokens/retries | BORROW_PATTERN training-only exact-token trace provenance; REJECT replacing Magpie accounts, quota, failover, cost; protect raw prompt/response privacy |
| Token triplets | [rollout_adapter.py](https://github.com/microsoft/agent-lightning/blob/2070bad5113e52f1aa2e5bdba822d4b24b197c05/agentlightning/verl/rollout_adapter.py), [events.py L125-L176 L212-L231](https://github.com/microsoft/agent-lightning/blob/2070bad5113e52f1aa2e5bdba822d4b24b197c05/agentlightning/server/routes/events.py#L212-L231): token-ID trace assembly and mismatch diagnosis; same prompt token IDs collapsed for training; do not dedup billing or side effects by same prompt |
| Reward integrity | [agl_rollout_manager.py L470-L539](https://github.com/microsoft/agent-lightning/blob/2070bad5113e52f1aa2e5bdba822d4b24b197c05/agentlightning/verl/agl_rollout_manager.py#L470-L539): ignores HTTP-error/empty response-token events for trainable triplets, selects last reward event and stores rollout status. [rollout_adapter.py L985-L989](https://github.com/microsoft/agent-lightning/blob/2070bad5113e52f1aa2e5bdba822d4b24b197c05/agentlightning/verl/rollout_adapter.py#L985-L989): missing reward filled by configurable value (default zero), while has_reward tracked separately | BORROW_PATTERN P0: distinguish OBSERVED_ZERO, UNKNOWN/NO_VERDICT, INFRA_FAILURE, VERIFIED_ACCEPT; never treat filled zero as independent failure |
| Storage | [server/store.py](https://github.com/microsoft/agent-lightning/blob/2070bad5113e52f1aa2e5bdba822d4b24b197c05/agentlightning/server/store.py): Rollout/Event/Models are plain MODULE-LEVEL IN-MEMORY DICTS. [schemas.py L77-L102](https://github.com/microsoft/agent-lightning/blob/2070bad5113e52f1aa2e5bdba822d4b24b197c05/agentlightning/schemas.py#L77-L102): terminal states. Idempotent creation and state transitions do NOT make a durable store | ALREADY_IMPLEMENTED: Nerelan SQLite TaskStore/append-only evidence; REJECT production rollout store |
| Local/K8s | [local_reconciler.py L111-L115 L137-L182](https://github.com/microsoft/agent-lightning/blob/2070bad5113e52f1aa2e5bdba822d4b24b197c05/agentlightning/controller/local_reconciler.py#L137-L182): native Windows local mode explicitly unsupported; missing local PID when RUNNING -> FAILED; K8s reconciler owns ephemeral Jobs | REJECT lost-handle-as-failed logic for Nerelan, preserve durable reconciliation/side-effect receipts |
| Async training | [docs/35-asynchronous-training.md](https://github.com/microsoft/agent-lightning/blob/2070bad5113e52f1aa2e5bdba822d4b24b197c05/docs/35-asynchronous-training.md): carry over incomplete groups; training weight-sync proxy pause sends 429; old-policy traces require freshness correction | BORROW_PATTERN P2 version/freshness metadata; REJECT interpreting training pause 429 as Magpie quota exhausted |
| Reward-hack prevention | [smith_agent.py L23-L82 L257-L299 L516-L560 L590-L626](https://github.com/microsoft/agent-lightning/blob/2070bad5113e52f1aa2e5bdba822d4b24b197c05/examples/swe_smith/agents/smith_agent.py#L257-L299) hides answer-bearing Git history, blocks network fetches/package installs/harness edits as regex backstop, restores hidden tests for verifier; F2P+P2P pass, timeout disqualifies | BORROW_PATTERN P0 sealed benchmark, independent tests, actual egress deny, prevent answer leakage and test tamper; REJECT regex as OS security boundary |
| Quality vs efficiency | [smith_agent.py L892-L918](https://github.com/microsoft/agent-lightning/blob/2070bad5113e52f1aa2e5bdba822d4b24b197c05/examples/swe_smith/agents/smith_agent.py#L892-L918): turn/prompt-length penalties only on solved TRAIN samples; VALIDATION keeps unshaped reward for checkpoint selection | BORROW_PATTERN P0: success must pass first, cost/token/runs optimized second. Do not conflate lower tokens with valid completion |
| Hooks/compute | [hooks.py L19-L63](https://github.com/microsoft/agent-lightning/blob/2070bad5113e52f1aa2e5bdba822d4b24b197c05/agentlightning/hooks.py#L19-L63) dynamically executes hook Python; [docs/75-example-coding-agent.md](https://github.com/microsoft/agent-lightning/blob/2070bad5113e52f1aa2e5bdba822d4b24b197c05/docs/75-example-coding-agent.md) coding RL example needs 4x B200 + K8s/two-machine. Upstream reports Qwen3.5-9B 41.8% -> 56.4% SWE-bench Verified after ~6K tasks (self-reported, NOT reproduced here) | REJECT hooks inside trusted Host; DEFER vLLM/verl trainer and full RL until independently measured advantage |

## 2. Nerelan real code overlap, NOT a blank-slate product

- [run_store.py](https://github.com/dddd2024/Nerelan/blob/5c69e891e3a559a23e7fd4e3115422c057df4438/reverse_agent/platform_v1/run_store.py): durable SQLite TaskStore, append-only task_events, task_evidence and durable_runs; canonical after restart. Do not replace with in-memory Rollout store.
- [goal_service.py](https://github.com/dddd2024/Nerelan/blob/5c69e891e3a559a23e7fd4e3115422c057df4438/reverse_agent/platform_v1/goal_service.py): controlled Goal->Plan->Task / Owner window, attempts and recovery.
- [model_router.py](https://github.com/dddd2024/Nerelan/blob/5c69e891e3a559a23e7fd4e3115422c057df4438/reverse_agent/platform_v1/model_router.py): uses bootstrap priors vs measured success, quota and cost. Its source says 3 completed attempts per bucket establish evidence (80% success, <=20% timeout) — avoid claiming RL is necessary to establish routing.
- [context_builder.py](https://github.com/dddd2024/Nerelan/blob/5c69e891e3a559a23e7fd4e3115422c057df4438/reverse_agent/platform_v1/context_builder.py): source-bound read-only authority=NONE context; raw traces cannot become Owner authorizations.
- Existing canonical owners [#379](https://github.com/dddd2024/Nerelan/issues/379) evaluate/memory/promotion; [#1267](https://github.com/dddd2024/Nerelan/issues/1267) real overhead cost; [#1527](https://github.com/dddd2024/Nerelan/issues/1527) agent-model bakeoff; [#1342](https://github.com/dddd2024/Nerelan/issues/1342) Magpie readings; [#299](https://github.com/dddd2024/Nerelan/issues/299) sandbox; [#303](https://github.com/dddd2024/Nerelan/issues/303) untrusted workspace; [#253](https://github.com/dddd2024/Nerelan/issues/253) Pack eval. DO NOT duplicate implementation ownership.

## 3. Minimal useful future design

Existing TaskStore accepted Task/Attempt plus immutable repo, executor, model, binding, context digest + actual Magpie usage (no second ledger) -> offline read-only, redacted eval export (rollout sample ID, event sequence ID, attempt_ID, public task, version, verifier reference/test hashes, observed reward flag, F2P/P2P, timestamp, failure reason, full actual cost) -> contamination-resistant champion/challenger comparison -> existing #379 independent promotion/rollback.

This is useful without gradient training. Do not log default full model requests/tokens to third-party analytics: risk of credentials, hidden eval answers, cross-workspace data. Export only by explicit scoped policy.

## 4. Proposed tests — NOT RUN

1. No access from worker to reference patch, hidden F2P tests or evaluator script.
2. OS/container network deny except allowlisted model/gateway; regex blockers not authoritative.
3. Tool attempts to inspect Git reference history, fetch source by curl/urllib, install original package, alter pytest/conftest, fake successful stdout must fail.
4. Verifier independently checks F2P+P2P, timeout/skip/incomplete not counted as resolved.
5. Missing reward != observed reward zero, missing cost != free request, missing trace != proved failed.
6. Every model-call trace resolves to exact Task/Attempt/model/executor/version and actual Magpie request, no duplicate accounting for equal prompts.
7. Native Windows local runner unsupported in upstream; comparison test uses supported isolated runner only.
8. A 429 from training weight update not confused with exhausted quota; continued work only after explicit status.
9. Rollout/controller crash cannot erase Nerelan durable attempt/evidence or trigger duplicate external side effect.
10. Champion/challenger fixed splits by task/repository/commit, not leaking benchmark answer between candidate and evaluation.
11. Stale routing snapshots and reward logs may inform research but never auto-promote a new policy.
12. Compare accepted-task success, actual full spend, tokens, retry count, latency and contaminated task fraction. Disallow quality regression in exchange for lower token cost.

## 5. Final decision / limitations

**BORROW_PATTERN (trajectory + anti-cheating eval) / ALREADY_IMPLEMENTED (durable goal, context, real routing) / REJECT_RUNTIME_CLONE (gateway + scheduler + memory store) / DEFER_RL (trainer).** P0 evaluation integrity and unknown/zero distinction; P1 read-only offline export and champion/challenger; P2 isolated RL only if measured.

Only pinned GitHub source and current main files examined; no installation, GPU run, Python pytest, Docker/K8s, provider call, exploit, actual benchmark, independent review or CI performed. Published upstream improvements are NOT Nerelan results or independently reproduced.

## 6. More precise ownership comparison: why not embed AGL proxy or trainer in Nerelan

### 6.1 Where data is already owned

Nerelan already has an append-only TaskStore for real work, replayable task_events, durable_runs and task_evidence. GoalService is the authorized orchestration owner; model_router uses priors and actual measured evidence. Magpie owns account pools, quotas, actual token/usage attribution and provider failover. AGL v1.0.3 is a **training data plane**, not a drop-in production dispatcher.

A conceptual bridge should therefore be an OFFLINE DATA EXPORT, not a new network service; source is the existing read-only persisted Task/Run/event rows and Magpie usage records. It should never influence real execution until the independently reviewed #379 policy-promotion stage. No extra on-device model or new task ledger required.

### 6.2 Concrete data dictionary (proposal only)

| Column | Source of truth | Rules |
|---|---|---|
| task_id, attempt_id, parent_goal | Nerelan TaskStore | Always explicit; cannot be inferred from prompt hash |
| route_candidate, executor_kind, model, binding_id | Nerelan actual selection and host adapter | Record actual selected combination and exact config revision, not only proposed |
| prompt_digest, context_packet_digest, repository/head | Host context snapshot | Data provenance; summaries authority NONE |
| model_call_id, usage_observed, usage_status | Magpie per-request settlement where available | 0 != missing; request IDs not guaranteed if no record |
| replay_version, adapter_version, eval_suite_version | pinned owner-approved metadata | Old versions preserved; cannot silently upgrade test harness |
| verdict | independent verifier in protected environment | ACCEPT, REJECT, INCONCLUSIVE, TEST_INFRA_ERROR etc; no AI self-grade |
| evaluation_result | F2P/P2P/test timeout, hash, stdout ref | Raw trace remains reviewable; validation identity is separate from agent |
| reward_observed and reward_value | derived for offline evaluation | Scalar only after verified provenance; NONE must not be default 0 for product |
| failure_classification, retry_count, time/cost | TaskStore and Magpie | Need per-attempt + aggregate all failed/wait/retry costs |
| policy_candidate_hash and promotion_state | #379 champion/challenger | promotion requires outside candidate and holdout check, reversible |

**Privacy:** AGL proxy captures full request and response. A safety-preserving Nerelan export should prefer salted digests, redacted explanations, references and limited audit views; raw request/response only by explicit scoped permission, no automatic central logging. Model-account API keys must never enter offline samples.

### 6.3 AGL capabilities that are technically narrower than product wording suggests

- AGL Gateway's model proxy picks one endpoint per rollout by hash and rewrites sampling/return_token_ids, enabling stable prefix cache and exact-token RL trajectory. It is **not** a quota-aware multi-provider router. Upstream non-streaming-only proxy is a compatibility limitation for production OpenCode/Codex/Claude usage.
- AGL Rollout state has versions and ID-based idempotent create, but its v1.0.3 server/store.py explicitly declares only in-memory dictionaries. End-to-end durability is not guaranteed by its state machine, nor does local_reconciler have the external-operation receipts Nerelan depends on. Native Windows local runner explicitly raises; if the local controller loses a process handle to a RUNNING rollout, its code transitions it to FAILED instead of proving the external process dead.
- AGL v1.0.3's RewardData is a helper, not a strongly typed approval gate; all event types are appended. The manager obtains the last reward event from the event list and uses a default-zero fallback for missing ones, while separately tracking coverage. This is **fine for an RL batch when configured**, not strong evidence of accepted user work.
- AGL's synchronous controller and 4 B200 example is a training system requiring infra separation. It shouldn't be presented as straightforwardly runnable with just existing Windows Nerelan and some available models.

### 6.4 Software engineer benchmark: test answers are an attack surface

The most concrete source is the SWE-smith coding harness, not the advertised benchmark delta. Its built-in agent evaluation:
- verifies a task-specific injected bug and records a patch.
- keeps the canonical reference fix and deleted fail-to-pass tests away from the agent by physically relocating the repository .git into a separate path.
- uses source-level stop patterns for Git, fetches, package install and test-config editing as a **defense in depth**.
- states that actual network egress must be blocked by Kubernetes NetworkPolicy; without it, Python/other network clients can download answer code.
- restores hidden F2P tests in the verifier phase, computes binary resolved only if F2P + scoped P2P pass and evaluation does not timeout.
- keeps raw success for validation but applies optional length/prompt penalties to already-solved training episodes; test quality cannot be bought by lower token usage.

Nerelan's future real-harness bakeoff must distinguish **a real user's normal task** (Git may be essential) from **a frozen benchmark** (Git/remote downloads can leak the answer and invalidate measurements). Data collection should not accidentally make production execution less capable. Sealing is a property of the evaluation environment only.

### 6.5 Training split and sample selection

The pinned upstream doc notes 59,136 original SWE-smith candidate tasks from 128 Python repositories, with empty descriptions and unavailable branches excluded, more-than-200-test tasks removed, four exploratory probes per remaining task, all-4-success tasks filtered, mixed outcomes retained and additional 0-of-4 hard tasks added. Final dataset approximately 6,000 training and 400 validation. This is a sophisticated **hardness and information-gain sampling** heuristic. We can borrow its evaluation dataset selection, **not** the benchmark figures as evidence of Nerelan improvements.

For Nerelan, choose paired tasks by repository and difficulty, stratify per executor and model, keep full failed-attempt costs, use a holdout that has not been optimized repeatedly, and report confidence intervals for accepted-success and total cost per accepted task. Failure categories should include insufficient quota, 429 model overload vs intentional training pause, tool corruption, context overflow, long stall and evaluator infrastructure failure.

## 7. Minimal experiments in sequence (future implementation owners, not run today)

**A. Provider-free baseline census and verifier leakage audit (P0, existing #1527/#299):** list actual recent accepted tasks, accessible test fixtures, possible withheld answers and files visible to workers. Build 4 negative-control attacks (git history, network fetch, package download, test tamper). Prove egress is denied by actual execution sandbox, not by instruction prompt; if not, label benchmark contaminated/uncontrolled.

**B. Read-only typed trace export (P1, #379/#1342):** take a bounded set of existing TaskStore receipts and Magpie request records. Run deterministic schema-only join and consistency check, verify status distinctions and exact ID links. No new model call or second usage ledger. Ensure unknown remains unknown.

**C. Paired champion/challenger routing eval (P1, #1267/#1527):** same frozen tasks and verifier, compare real harness×model pairs. Initially shadow-offline when possible, otherwise separately authorized bounded runs; measure accepted tasks per true total cost, failure/retry rate, latency and p95. Validate no winner simply cherry-picks easy tasks or lost charges.

**D. Optional training experiment only if warranted (P2, #379):** isolated Linux + vLLM/verl stack, verified split, no production secrets/accounts, model-specific true token IDs, training provenance and cost audit. Compare against a no-training policy/champion baseline. Do not merge into production gateway before independent quality and cost gains.

## 8. Decision gates (few, not heavyweight bureaucracy)

- Evidence gate: every task used for learning has a pinned test/answer boundary, independent verifier and no training/validation leakage.
- Accounting gate: missing reward/usage is not zero, retry and failed attempts count; actual Magpie settled spend where known.
- Reuse gate: if a thin read-only export and routing policy outperform new trainers in accepted success/spend, do not import RL.
- Authority gate: only preexisting Owner-approved promotion process (#379), not an LLM self-rating or AGL hook, can activate new routing/model changes.

**Final outcome is research only**. Not proof of AGL runtime capability or live installed framework. No test performed or CI checked.
