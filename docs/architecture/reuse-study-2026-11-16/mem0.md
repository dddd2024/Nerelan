# Mem0 2.2.1 — Agent 长期记忆 / Nerelan Source-Pinned 深审

> One project only · Research [#1655](https://github.com/dddd2024/Nerelan/issues/1655) · STATIC_SOURCE_REVIEW / NO TESTS / NO IMPLEMENTATION AUTHORITY

# Mem0 OSS 2.2.1 pinned-source deep audit — Agent episodic memory, long-task context, retrieval economics & provenance

> 2026-11-17 · `SINGLE_PROJECT / STATIC_SOURCE_REVIEW / R1_DOCS_ONLY / NO_INSTALL / NO_PROVIDER_CALL / NO_IMPL_AUTHORITY`

- Upstream: [mem0ai/mem0@`f1791daa86d469249c9b002f62644d58a1eb96a0`](https://github.com/mem0ai/mem0/commit/f1791daa86d469249c9b002f62644d58a1eb96a0), `pyproject.toml` identifies package `mem0ai 2.2.1`, Apache-2.0.
- Nerelan: [main@`5c69e891e3a559a23e7fd4e3115422c057df4438`](https://github.com/dddd2024/Nerelan/commit/5c69e891e3a559a23e7fd4e3115422c057df4438).
- Historical duplicate preflight: [#1576](https://github.com/dddd2024/Nerelan/issues/1576) and **31 preexisting hub comments**, Issues/PR/code searches for `Mem0` / `mem0ai/mem0` returned **no standalone pinned-source study**. Prior [Graphiti #1612](https://github.com/dddd2024/Nerelan/issues/1612), [Letta Code archival index #1576](https://github.com/dddd2024/Nerelan/issues/1576) and memory roadmap [#379](https://github.com/dddd2024/Nerelan/issues/379) are different sources or *owners*, not duplicate Mem0 audits.
- Research issue only. Permanent implementation ownership: [#379](https://github.com/dddd2024/Nerelan/issues/379) evidence-admitted experience, [#260](https://github.com/dddd2024/Nerelan/issues/260) project knowledge, [#103](https://github.com/dddd2024/Nerelan/issues/103) cross-Agent memory authority, [#296](https://github.com/dddd2024/Nerelan/issues/296)/[#642](https://github.com/dddd2024/Nerelan/issues/642) context projection, [#1286](https://github.com/dddd2024/Nerelan/issues/1286) coordinator/shared-memory benchmark, [#1527](https://github.com/dddd2024/Nerelan/issues/1527) task-accepted cost.

## 1. Source-specific findings (upstream pinned)

| Domain | Exact upstream source | Real observed mechanism | Nerelan classification |
|---|---|---|---|
| Agent/user/run identity | [main.py:739–758,760–879](https://github.com/mem0ai/mem0/blob/f1791daa86d469249c9b002f62644d58a1eb96a0/mem0/memory/main.py#L739-L879), [main.py:360–404](https://github.com/mem0ai/mem0/blob/f1791daa86d469249c9b002f62644d58a1eb96a0/mem0/memory/main.py#L360-L404) | `user_id/agent_id/run_id` filter+metadata, agent extraction if assistant messages and agent_id, invalid metadata identity keys stripped; this is *library filtering*, not host ACL | **BORROW_PATTERN / P1**: explicit `Owner+project+run+task+agent` scope projection; never trust externally provided filter as authorization |
| Extraction pipeline | [main.py:881–1016](https://github.com/mem0ai/mem0/blob/f1791daa86d469249c9b002f62644d58a1eb96a0/mem0/memory/main.py#L881-L1016) | old-memory top10 retrieved, last10 messages, one LLM fact extraction, batch embeddings, MD5 text dedup; `infer=False` writes messages verbatim; current OSS is ADD-only extraction | **BORROW_PATTERN / P1**, not auto-admit all text; preserve evidence refs and classify `CANDIDATE` before admission |
| LLM failure vs empty extraction | [main.py:957–991](https://github.com/mem0ai/mem0/blob/f1791daa86d469249c9b002f62644d58a1eb96a0/mem0/memory/main.py#L957-L991) | LLM call exception now raises `LLMError` (good), **but JSON parse exception sets `extracted_memories=[]`, persists source messages, returns []**; invalid output indistinguishable from a legitimate no-fact result | **REJECT_AS_AUTHORITY / P0 test**: `NO_FACTS` ≠ `PARSE_FAILED`; no false memory success after unusable extraction |
| Duplicate control | [main.py:925–939,1007–1045](https://github.com/mem0ai/mem0/blob/f1791daa86d469249c9b002f62644d58a1eb96a0/mem0/memory/main.py#L925-L939) | dedup checks only top10 similar existing memories + current batch; exact text MD5 prevents repeats inside observed set, **not a global idempotency key or semantic contradiction proof** | **BORROW_PATTERN** only: stable source-event digest + extraction-model/version + scope; exact retry idempotency & conflict links hosted by Nerelan |
| Persistence ordering | [main.py:1047–1100,1206–1212](https://github.com/mem0ai/mem0/blob/f1791daa86d469249c9b002f62644d58a1eb96a0/mem0/memory/main.py#L1047-L1100) | vector bulk insert fail → individual fallback; partial persisted subset returned; SQLite history written separately, history failure caught; entity links later best effort | **REJECT_DIRECT_DURABILITY**: no cross-store atomic guarantee or exactly-once source admission. Use existing TaskStore as truth, derive memory index repairably |
| Retrieval | [main.py:1393–1536,1642–1739](https://github.com/mem0ai/mem0/blob/f1791daa86d469249c9b002f62644d58a1eb96a0/mem0/memory/main.py#L1393-L1739) | semantic candidates top max(4k,60), keyword BM25 & entity boosts score candidates; **keyword-only matches not unioned into candidates** in this implementation; reranking optional, false on default | **BORROW_PATTERN / P1 experiment**: compare bounded lexical + semantic *union* vs original and deterministic Nerelan refs on real task retrieval |
| Temporal claims | [main.py:1446](https://github.com/mem0ai/mem0/blob/f1791daa86d469249c9b002f62644d58a1eb96a0/mem0/memory/main.py#L1446) and [migration](https://github.com/mem0ai/mem0/blob/f1791daa86d469249c9b002f62644d58a1eb96a0/docs/migration/oss-v2-to-v3.mdx#L332-L365) | OSS rejects `reference_date` and `timestamp` as platform-only; ADD-only retains contradicting old/new facts; expiration_date filters expired returns | **REJECT_AS_AUTHORITATIVE_CURRENT_STATE**; supersession/staleness/freshness/conflicts must come from #379 source facts, never ranking alone |
| API read/write identity | [main.py:1222–1268,1829–1902](https://github.com/mem0ai/mem0/blob/f1791daa86d469249c9b002f62644d58a1eb96a0/mem0/memory/main.py#L1222-L1268) | `get(memory_id)`, `update(memory_id)`, `delete(memory_id)` take raw memory ID; no per-call Owner/principal auth arg at OSS library boundary; `delete_all` requires one scoped filter | **P0 integration trust**: only trusted host may resolve ID within authorized scope; never expose raw IDs as universally writable/accessible |
| Memory format/history | [configs/base.py](https://github.com/mem0ai/mem0/blob/f1791daa86d469249c9b002f62644d58a1eb96a0/mem0/configs/base.py), [main.py:1975–2115](https://github.com/mem0ai/mem0/blob/f1791daa86d469249c9b002f62644d58a1eb96a0/mem0/memory/main.py#L1975-L2115) | additional vector store, separate local `~/.mem0/history.db`, embedded metadata, history for explicit update/delete | **REJECT_SECOND_TRUTH**: no shadow TaskStore and no free-standing authoritative “agent remembered” record |
| Telemetry | [telemetry.py:14–18,76–89,192–220](https://github.com/mem0ai/mem0/blob/f1791daa86d469249c9b002f62644d58a1eb96a0/mem0/memory/telemetry.py#L14-L18) | OSS `MEM0_TELEMETRY` defaults `True`, PostHog endpoint; sends environment/collection/provider class & event metadata (not necessarily raw memory contents) | **P0 DEPENDENCY GUARD**: if later installed, set `MEM0_TELEMETRY=False` *before import* in provider-free/privacy-sensitive Nerelan host, validate zero outbound events |
| Provenance / graph / benchmarks | [README](https://github.com/mem0ai/mem0/blob/f1791daa86d469249c9b002f62644d58a1eb96a0/README.md), [OSS migration](https://github.com/mem0ai/mem0/blob/f1791daa86d469249c9b002f62644d58a1eb96a0/docs/migration/oss-v2-to-v3.mdx#L14-L23) | managed benchmark numbers explicitly include proprietary platform optimizations; Graph memory removed from OSS; entity matching != graph memory. OSS hybrid available subject to vector-store support | **REJECT BENCHMARK TRANSFER**: cannot cite 92.5 LoCoMo / 94.4 LongMemEval as reproducible OSS gain or Nerelan savings |

## 2. Nerelan current-main comparison — preserve what works

| Nerelan source | Already implemented | Not yet proven |
|---|---|---|
| [context_builder.py:1–9](https://github.com/dddd2024/Nerelan/blob/5c69e891e3a559a23e7fd4e3115422c057df4438/reverse_agent/platform_v1/context_builder.py#L1-L9) | **ALREADY_REUSED** deterministic read-only packet reconstructed from durable TaskStore, Goal link, latest run, scoped Git; never treats generated prose as source truth | Cross-task semantic long-term memory retrieval |
| [context_optimization.py:14–37,44–80,83–136](https://github.com/dddd2024/Nerelan/blob/5c69e891e3a559a23e7fd4e3115422c057df4438/reverse_agent/platform_v1/context_optimization.py#L14-L136) | Digests, deterministic bounded lexical retrieval, context compaction under byte budget, source reference retention | Hybrid semantic+lexical indexed retrieval; real quality/cost gain over deterministic baseline |
| [context_recovery.py:72–81,165–219](https://github.com/dddd2024/Nerelan/blob/5c69e891e3a559a23e7fd4e3115422c057df4438/reverse_agent/platform_v1/context_recovery.py#L72-L81) | `authority=NONE`, source/scope digest guard, model-summary reservation prevents duplicate paid calls, output tied to exact input snapshot | Evidence-admitted experience promoted/invalidated across tasks, contradiction handling |
| [#379](https://github.com/dddd2024/Nerelan/issues/379), [#103](https://github.com/dddd2024/Nerelan/issues/103), [#1286](https://github.com/dddd2024/Nerelan/issues/1286) | Full **architecture owner / benchmark** declared, not implementation completion | Production admitted project memory/read ranking and independent evaluation |

## 3. The precise “copy what” proposal
1. **P0 preserve existing truth**: retain TaskStore/GitHub source authority, `context_builder` packet, current digest and scoped handoff. Do **not** route raw Mem0 output into Goal/Review/Owner grants.
2. **P1 reusable candidate extraction**: from confirmed task completion, verifier outcome and action receipt, extract only *candidate experience* with `source_run/task/evidence_digest/project/workspace/agent/extractor_model/prompt_version/quality`; allow explicit `NO_FACTS`, `PARSE_FAILED`, `EMBED_FAILED`, `PARTIAL_INDEX`, `NOT_ADMITTED`; never promote model-generated “I finished” without independent evidence.
3. **P1 recall over accepted memory**: reproduce Mem0's semantic+BM25+entity signals only if marginal value demonstrated; use **lexical-semantic candidate union** to avoid missing keyword-only facts; keep scope and freshness filter before ranking, then bounded context projection. Explicit supersession & conflict relations are required for current-state claims.
4. **P1 repairable index**: exact stable `admission_key=(project,source_digest,lesson_kind,extractor_version)` and authoritative acceptance record in existing TaskStore owner, vector/keyword store as rebuildable index. Partial writes must not be mistaken for accepted experiences. Do not add another SQLite authoritative DB.
5. **P1 real user value**: when worker returns after quota/stall/restart, show “Based on verified prior work [source] this approach helped”, never “agent remembers” without provenance; allow human to inspect/stale/disable advisory memories, not auto-expand permissions.
6. **P2 optional SDK**: only after pure repository-native candidate+retrieval A/B and acceptance benchmark, decide whether Mem0 OSS worth its embedding/LLM/vector store complexity and telemetry risk. The SDK is a replaceable adapter, not a mandatory dependency or cloud enrollment.

## 4. Provider-free negative cases & future controlled experiment (NOT RUN)

- Two near-simultaneous `add()` calls for same verified source: precisely one acceptance receipt; duplicate extraction may occur but no duplicate admitted lesson.
- LLM returns malformed JSON vs true `memory: []` vs 429/timeout: three distinguishable states; 429 must not be recorded as successful empty memory.
- Vector bulk insert partially succeeds then individual retry, SQLite history insert fails, entity linker fails: repaired index converges to TaskStore acceptance; no evidence-of-success based on vector hit alone.
- Run A/B, same `memory_id` known to attacker: no cross Owner/project get/update/delete/search, **even though OSS library doesn't enforce authorization**.
- Contradiction at T0/T1, superseded result: current active memory is evidence-fresh; old record remains for history but not current guidance. `expiration_date` alone doesn't certify source freshness.
- BM25-only exact ticket/filename or error class absent from semantic top60: compare union-candidate recall to OSS candidate-only scoring and existing context_optimization lexical retrieval.
- One failure with `infer=False`: verbatim unsafe output/agent self-claim must not become admitted lesson.
- Turn off `MEM0_TELEMETRY` before import, block network and verify zero PostHog/LLM/embedding requests in provider-free startup.
- Same tasks with no memory vs deterministic current retrieval vs candidate enhanced retrieval, controlled model/executor, score independently accepted completion, token/cached token, latency, retried errors, *actual Magpie spend where available* and stale-memory harm. Need per-accepted-task total cost, not vendor benchmarks.

**No tests executed**: no local Mem0 import, Qdrant/SQLite runtime, LLM/embedder model invocation, paid API, trial dataset or independent reviewer. Only pinned GitHub source reading and Nerelan code/Issue reconciliation.

## 5. No-go and licensing
Mem0 OSS `pyproject.toml` 2.2.1 / Apache-2.0; enabling full SDK also brings Qdrant/OpenAI/PostHog and separate history storage, which is not free for a local-first single-authority goal platform. README's claimed high scores refer to managed closed extensions, not direct OSS verification. Without multi-task accepted-quality lift *and* an acceptable memory harm and all-in cost envelope, **BORROW_PATTERN / DEFER SDK**, not a production dependency. New model calls, installation, auth, implementation, workflow changes, PR merging require separate authorized work.

**Final classification:** `BORROW_PATTERN` (ADD-only candidate extraction & scoped hybrid retrieval), `ALREADY_REUSED` (Nerelan deterministic context + digest recover), `REJECT` (unfiltered auto memory admission, cloned TaskStore/history DB, default telemetry, platform benchmark transfer). `DIRECT_REUSE` is **conditional future spike only**, not supported as an immediate product choice.

## 6. Agent 模块拆解：不是“所有对话都存起来”

### 6.1 来源分层与可信边界

```text
Authoritative current truth:
  Git HEAD / Owner Decision / TaskStore Goal, Task, Run, accepted evidence
                         |
                         v
   scope-checked context_builder -> digest-bound Context Packet
                         |
       accepted finished outcome + verifier + evidence ref
                         |
           candidate extractor (could use Mem0 pattern)
                         |
      admission gate #379: VERIFIED / REVIEW / REJECTED
                         |
         advisory memory index (rebuildable, non-authority)
                         |
   scoped retrieval -> freshness/conflict -> context projection
                         |
           next Agent task (candidate hints only)
```

Mem0 `agent_id` 仅表示提取逻辑可选择助手角色内容，并不证明“模型陈述的完成动作已经成功”。即使 `infer=True`、事实抽取成功，也不等于检验通过。**已经由 Nerelan 保存的原始执行事件更可信**；Agent 文本只是候选来源。

### 6.2 一个详细的应用场景

Nerelan 中某个 Goal 在连续执行时遇到某提供商 429 / quota stall，后来切换 executor+model 才完成，并通过独立审查：

- **可记忆**：任务类型、失败类别、scope、采用策略、成功构建的环境条件、验收引用、实际成本/时间归因（没有相关数据时标记 UNKNOWN）。
- **不能自动记忆为真**：“LLM 自己说已完成/已节省 50% 成本”“此 provider 永远不好用”“把 Owner 审批阈值改掉”。
- **下一轮检索**：先限定 repository / task class / active model/provider context，再取最近 verified 的相似失败与已知有效 workaround，优先可复现来源；只提供 advice，宿主仍以实时 quota、TaskStore、策略为准。
- **对用户显示**：“基于上次 [Issue/Run] 的已验收结果推荐此尝试；最近验证时间、适用执行器和费用依据如下”，而不是“AI 记得这样做”。

### 6.3 明确的 failure lattice

| Extraction | Index | Admission | Meaning |
|---|---|---|---|
| `NO_FACTS` | `NONE` | `NOT_APPLICABLE` | 有效 JSON 且证实无候选 |
| `PARSE_FAILED` | `NONE` | `BLOCKED` | 错误模型输出，不能当空记忆 |
| `LLM_RATE_LIMITED` | `NONE` | `DEFERRED` | 后续按照 Magpie/现有 provider failover 再试，不开启无限重试 |
| `EMBED_FAILED` | `NONE` | `PENDING_INDEX` | 有原始 verified source，尚未完成索引 |
| `EXTRACTED` | `PARTIAL_INDEX` | `REVIEW_REQUIRED` | 只记录被索引的 ID，没有足够完整性证据不能提升为 active |
| `EXTRACTED` | `INDEXED` | `ACCEPTED_EXPERIENCE` | 独立证据与 scope/contradiction/freshness 检验通过 |
| `EXTRACTED` | `INDEXED` | `SUPERSEDED` | 历史留存但当前不可作为建议的首选依据 |

这里的状态只是实现与测试提案，**未在 Nerelan 创建新表或运行引擎**；#379 拥有日后的精简 contract。

## 7. 插件/Pack 与外部检索模块的取舍

| 建议 | 取舍 |
|---|---|
| 在 Pack manifest 里声明知识来源与验证器 | **BORROW_PATTERN**；#253 已有完整声明，不新建 Mem0 专用 Pack 类型 |
| `Memory.add()` 的用户/Agent/Run ID | **BORROW_PATTERN**；作为 scope 过滤参考，不当 Owner 权限 |
| 复用 Qdrant / FAISS / PostgreSQL vector backend | **OPTIONAL_COMPONENT**：先基准测试小规模 deterministic lexical，只有召回效果值得才引新存储 |
| Mem0 hosted API + agent auto-signup | **REJECT_BY_DEFAULT**：把 Nerelan 账号/敏感长期经验导出到新云服务，不符合当前本地优先与单独授权边界 |
| Mem0 云端 Graph memory | **NOT IN OSS**：不要把 SaaS 图谱能力描述为可以直接抄的 OSS 项 |
| Mem0 SDK 自动 ADD-only | **BORROW_PATTERN**：减少 LLM 更新决策，但需要事后证据准入和旧记忆 supersession |
| Mem0 默认匿名遥测 | **REJECT AS DEFAULT**：即便采集是事件统计而非原始正文，Nerelan provider-free Host 也需要明确的无网络隐私默认值 |
| 真正的成本和效果 | **NEEDS EXPERIMENT**：与当前 `retrieve_context()` 做相同任务、相同模型预算下的检索/成功率/成本对照 |

## 8. 此轮研究的三项高价值反例

**反例 A — 检索独立性**：仓库事故编号 `OPS-1234` 几乎只通过关键词命中，语义检索前 60 项不含它。Mem0 这版先构造语义候选，再使用 BM25 和实体分提升这些候选，关键词独有结果未进入最终列表。Nerelan 若真要混合检索，候选阶段必须对两路做 union/dedup，再核对保留的 scope 和来源。

**反例 B — 单次请求部分成功**：Mem0 bulk vector insert 失败后逐条插入，其中一部分成功；后续 SQLite history 写入失败又被日志吞掉，实体 linking 还可能失败。直接按 SDK 的响应“部分成功”的 ID 构造“完整记忆已同步”会产生悖论。Nerelan 应以原始接受记录为唯一权威，索引差异可 repair。

**反例 C — 加入了错误事实**：单次事实抽取得到两个矛盾状态：`PR 尚未合并` 和 `PR 已合并`。ADD-only 保留两者，时间权重也不等于 GitHub 当前状态。Nerelan 不应让后者覆盖实时 GitHub/TaskStore；记忆必须带 last-verified/source-ref 和冲突/失效状态。

## 9. 精简的优先级和是否值得实施

- **当前 P0**：不触碰项目正在修复的持续执行失败；证明现有 digest-bound Context Packet、TaskStore 恢复链在运行中没有被新 memory layer 绕开。
- **P1 低成本单点实验**：在已有已验收任务记录上构造纯静态/无模型候选体验检索，检查跨任务重复失败的召回和来源准确性，**不用立即引 Mem0**。
- **P1 同预算 benchmark**：`A 当前 Nerelan deterministic `retrieve_context()``、`B evidence-scoped lexical candidates`、`C Mem0-style hybrid semantic+BM25+entity`，统一来源、任务规模、可见范围与最终独立验收，报告召回、precision、stale harm、token/latency/real cost、修复后完成率。
- **P2 package spike only if justified**：若 C 在质量约束下有可测且显著的 accepted-task 增益，再评估 Mem0 2.2.1 OSS；固定依赖/许可、禁止网络遥测、独立数据分区、维护成本、异常与 partial durability 都由原 owner Issues 做执行审批。

**核心价值判据**：不是 memory hit rate 提高，而是 **有严格来源约束的已验收 Goal 完成率、重复失败减少、质量约束下的单位完成总成本下降**。

## 10. 证据边界

本轮报告只使用 GitHub 固定上游 `mem0ai/mem0@f1791daa86d469249c9b002f62644d58a1eb96a0`、Nerelan `main@5c69e891e3a559a23e7fd4e3115422c057df4438` 与现存 Issue 文本；未实际安装/运行 Mem0、Qdrant、OpenAI 接口、LLM embedding、遥测实验或独立 reviewer。报告中的 test cases 均尚未执行。README benchmark 是 Mem0 托管平台的陈述，不作为本 OSS 性能或 Nerelan 成本事实。
