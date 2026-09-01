# Research Baseline — Context Management and Repository Intelligence

Status: research-derived architecture baseline; **not an implementation claim**.

Owner Work Item: #513
Parent/implementation owners: #137, #260, #296, #379, #361
Related orchestration grounding: #508 / PR #509

## 1. Purpose

This document converts current research on long-horizon context management, repository retrieval and repository-level planning into Nerelan/reverse-agent architecture constraints.

It does **not** create a new context store, vector database, code-indexing platform, planner, Agent framework or execution source of truth. The existing roadmap remains authoritative for implementation sequencing.

The central problem is:

```text
long-running project history grows without bound
+
repository size grows
+
Agent sessions are finite and replaceable
+
retrieval itself has latency/token/error cost

therefore

more stored information != more model-facing context
```

The target is a system in which durable truth may grow while each Agent receives a bounded, task-specific, provenance-aware Context Projection.

---

## 2. Existing Nerelan foundations to preserve

The project already distinguishes persistent execution/project truth from one model session. Preserve the layered model fixed under #260/#296/#379:

```text
L0 Agent/model session
   ephemeral working context

L1 orchestration checkpoint / structured handoff
   bounded role-to-role continuity

L2 TaskStore / durable platform truth
   Goal / Spec / Plan / Tasks / runs / claims / receipts / budgets / evidence

L3 Git / GitHub repository truth
   current code / diffs / commits / branches / Issues / PRs / checks

L4 Project Knowledge / Experience Memory
   accepted facts / decisions / negative results / lessons / experiment outcomes
```

Permanent rule:

> An Agent session is disposable. Accepted project state must survive loss, truncation or replacement of L0.

Research below refines **how to retrieve, manage and project** those layers. It does not replace them.

---

## 3. Research inputs

### Context as a Tool — long-horizon context management

Canonical publication page:

- https://aclanthology.org/2026.findings-acl.1032/

Research lesson:

Context management should not be treated only as an emergency action after a token threshold is exceeded. It can be modeled as an active capability that recognizes context degradation, preserves stable task semantics, compresses older working material and retains high-fidelity recent evidence.

Nerelan implication:

```text
Agent working
    |
    +-> context remains sufficient -> continue
    |
    +-> context pressure / drift / repetition detected
            |
            v
       Context Management action
            |
            +-> preserve invariants / current goal / authority
            +-> preserve unresolved decisions
            +-> preserve current evidence identities
            +-> compress superseded exploration
            +-> discard irrelevant repetition
            v
       rebuilt bounded Context Projection
```

This is **research-derived / not yet implemented** unless an existing owner Issue explicitly says otherwise.

### ARC — active/reflection-driven context management

Canonical publication page:

- https://aclanthology.org/2026.findings-acl.930/

Research lesson:

Long-horizon Agent quality can degrade because context accumulates stale, duplicated or low-value material. Context should be actively monitored and reorganized rather than assumed to remain equally useful as it grows.

Nerelan implication:

Context pressure should eventually be observable through signals such as:

```text
input/context units per role
repeated repository reads
repeated tool calls
retrieved-but-unused context
superseded hypothesis count
context reconstruction frequency
resume success after session replacement
```

These are measurement candidates under #296/#260, not a new telemetry platform.

### Repoformer — selective repository retrieval

Canonical publication page:

- https://proceedings.mlr.press/v235/wu24a.html

Research lesson:

Repository retrieval is not universally beneficial. Retrieval has cost and low-quality retrieved context can harm generation. A system should decide **whether retrieval is needed** before paying for it.

Nerelan implication:

Reject the default architecture:

```text
Task
-> always retrieve N chunks
-> append everything
-> model
```

Prefer:

```text
Task
-> retrieval-need decision
    |
    +-> NO  -> use current bounded context
    |
    +-> YES -> construct repository query
                -> retrieve candidates
                -> rerank/filter
                -> project minimum useful evidence
```

This supports the #361 reuse-first rule: do not introduce a vector/RAG service merely because the feature is called memory or repository intelligence.

### CodeRAG — query construction and reranking for code retrieval

Canonical publication page:

- https://aclanthology.org/2025.emnlp-main.1187/

Research lesson:

Repository retrieval quality depends on more than embeddings. Query construction, multiple retrieval paths and reranking can materially affect whether the model receives the right code context.

Nerelan implication:

Future repository intelligence should remain retrieval-backend neutral and support a staged candidate pipeline conceptually like:

```text
Task / current plan
    |
    v
query construction
    |
    +-> exact path / symbol references
    +-> lexical / full-text retrieval
    +-> dependency / reference graph retrieval
    +-> semantic retrieval only where justified
    |
    v
candidate union
    |
    v
rerank by task relevance + provenance + freshness
    |
    v
bounded Context Projection
```

Possible mature mechanics include SQLite FTS5, LSP, Tree-sitter-derived indexes, SCIP, CodeQL/graph information, ctags or other adapters already contemplated under #296/#361. No new code-intelligence platform is authorized here.

### CodePlan — repository-level planning and change impact

Canonical research page:

- https://www.microsoft.com/en-us/research/publication/codeplan-repository-level-coding-using-llms-and-planning-2/

Research lesson:

Repository-level modification is a planning problem in which one change can imply later dependent changes. A plan should be revisable as dependency/change-impact information is discovered.

Nerelan implication:

Do not assume:

```text
initial plan
-> immutable execution sequence
```

Prefer:

```text
initial Goal / Spec / Plan
-> execute bounded step
-> inspect actual repository/evidence impact
-> identify affected symbols/files/tests/contracts
-> preserve accepted completed work
-> revise only affected future plan
-> continue
```

Plan revision remains subject to current authority/policy and cannot silently broaden allowed paths or execution capability.

### MutaGReP — repository planning with bounded relevant context

Canonical preprint page:

- https://arxiv.org/abs/2502.15872

Research lesson:

Repository-level planning can benefit from grounding plans in concrete code symbols while using only a small relevant slice of repository context rather than copying an entire repository into the prompt.

Nerelan implication:

Planner context should favor stable identities:

```text
symbol / module / path
+ dependency/reference relation
+ exact current revision
+ relevant tests/contracts
+ current task constraints
```

rather than long free-form summaries that cannot be revalidated against the current repository.

---

## 4. Research-derived architecture rules

### 4.1 Context management is a capability, not a transcript policy

Future implementation under the canonical context owners should be able to request/perform context reconstruction deliberately.

The action should operate over durable sources; it must not become a hidden second memory authority.

### 4.2 Reconstruct context from truth; do not preserve one conversation forever

After restart, provider failover, Agent replacement or context truncation:

```text
current Goal / Spec / Plan / Task
+ current authority/policy
+ accepted structured handoff/checkpoint
+ exact current Git/GitHub state
+ relevant evidence
+ scoped accepted Project Knowledge
-> fresh bounded Context Projection
```

Do not replay the complete chat/event history by default.

### 4.3 Durable growth and prompt growth must be decoupled

A larger TaskStore, evidence history or Project Diary must not force linear prompt growth.

Required conceptual boundary:

```text
durable history
-> scoped retrieval
-> provenance/freshness/applicability validation
-> ranking
-> compression / structured projection
-> model context
```

Raw source evidence remains auditable outside the prompt.

### 4.4 Retrieval must earn its cost

A retrieval action should eventually be observable as a decision with at least:

```text
why retrieval was needed
which source classes were queried
which results were selected
which selected results were actually used
latency / context cost
whether retrieval improved or harmed the task outcome where measurable
```

This does not require logging private chain-of-thought.

### 4.5 Repository intelligence should be multi-signal, not vector-only

The preferred order remains reuse-first:

```text
exact known paths / current diff
-> relational/indexed metadata
-> lexical/full-text search
-> symbol/reference/dependency intelligence
-> semantic/vector retrieval only when measured need remains
```

No vector database is justified solely by future scale speculation.

### 4.6 Repository plans are evidence-revisable

A plan may be revised after discovering new dependency/change-impact evidence, but:

- completed accepted work remains durable;
- revision reason is recorded;
- authority/policy scope is rechecked;
- an Agent-generated revised plan never grants new authority;
- repeated churn is itself an efficiency/failure signal.

### 4.7 Negative results are high-value context

A relevant prior failed approach should be retrievable when its applicability still holds. This is one of the strongest ways for long-running work to avoid wasting repeated model/tool calls.

Negative-result retrieval remains advisory and cannot override current repository evidence.

---

## 5. Context Projection contract candidate

Research suggests a future projection object should conceptually be able to distinguish:

```text
stable_task_semantics
current_goal_and_acceptance
current_authority_constraints
current_plan_slice
accepted_checkpoint_or_handoff
exact_repository_state_refs
recent_high_fidelity_evidence
retrieved_project_knowledge
retrieved_negative_results
open_questions
known_conflicts_or_staleness
source/provenance refs
projection_budget
```

Exact schema belongs to the implementation owner. This document fixes only the semantic requirements.

---

## 6. Context/retrieval effectiveness metrics

Do not assume that a new retrieval or context mechanism is useful because it sounds sophisticated.

Candidate metrics:

```text
completion / verifier success
context units per accepted task
repository reads per accepted task
retrieval requests per task
retrieval selected-result use rate
repeated read reduction
repeated tool-call reduction
repeat-failure reduction
rework / retry count
latency
cost / token usage
resume success after L0 replacement
stale-memory exclusion rate
harmful-retrieval incidents
```

Compare a new mechanism to a simpler baseline before promotion.

---

## 7. Complexity and reuse boundary

This research does **not** justify:

```text
new generic RAG platform
new vector database by default
full-repository prompt replay
a second project-memory source of truth
a custom code-indexing ecosystem before mature adapters are tested
a new orchestration framework
a planner that can change authority boundaries
```

Preferred strategy:

```text
existing TaskStore / Git / GitHub / Project Knowledge truth
+ mature repository intelligence adapters
+ thin Nerelan retrieval/projection policy
```

Nerelan owns source precedence, provenance, scope, freshness, applicability, authority separation and product-facing Context Projection semantics.

---

## 8. Mapping to existing owners

### #260 Mother Platform Productization

Owns Project Diary / Knowledge Memory and long-running product experience.

### #296 Context & Invocation Efficiency

Owns context projection, code-intelligence/retrieval efficiency and invocation reduction.

### #379 Memory admission / context projection direction

Owns memory admission, applicability/freshness/conflict treatment and harmful/stale-memory handling.

### #361 Mature Component Reuse Gate

Requires mature search/index/code-intelligence primitives to be evaluated before custom infrastructure.

### #137 Mother Platform

Owns sequencing. Research here must not displace governance closure, real dogfood or higher-priority product work.

---

## 9. Adoption sequence suggested by the research

When implementation owners authorize future work, prefer incremental evidence:

```text
CTX-R0  measure current context/repeated-read/repeated-call behavior
CTX-R1  explicit bounded Context Projection from current durable sources
CTX-R2  selective retrieval-need decision + simple indexed retrieval
CTX-R3  symbol/reference/dependency-aware repository retrieval
CTX-R4  active context-management action / reconstruction policy
CTX-R5  measured semantic retrieval only if earlier mechanisms are insufficient
CTX-R6  evidence-backed adaptive projection/retrieval strategy
```

Each stage must be removable/downgradable when it does not beat its simpler baseline.

---

## 10. Terminal research position

```text
DURABLE_HISTORY_CAN_GROW
MODEL_CONTEXT_MUST_STAY_BOUNDED
CONTEXT_MANAGEMENT_IS_ACTIVE_AND_RECONSTRUCTIVE
RETRIEVAL_IS_SELECTIVE_NOT_AUTOMATIC
REPOSITORY_INTELLIGENCE_IS_MULTI_SIGNAL_AND_REUSE_FIRST
PLANS_MAY_REVISE_FROM_CHANGE_IMPACT_EVIDENCE
MEMORY_AND_RETRIEVAL_NEVER_BECOME_AUTHORITY
IMPLEMENTATION_REMAINS_WITH_EXISTING_OWNER_ISSUES
```
