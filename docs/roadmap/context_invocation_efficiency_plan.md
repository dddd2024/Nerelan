# Context & Invocation Efficiency Roadmap

```text
STATUS: FIXED_LONG_TERM_CAPABILITY
AUTHORITY: PLANNING_REFERENCE_ONLY
EXECUTION_AUTHORITY: NONE
OWNING_PRODUCT: reverse-agent mother platform
```

This roadmap fixes **Context & Invocation Efficiency / 上下文与调用效率治理** as a permanent platform capability. It is not a one-off token-saving exercise and does not authorize runtime changes by itself.

The goal is to reduce unnecessary model context, model invocations, repeated retrieval, repeated Agent exploration, tool payload, latency and cost **without weakening durable truth, evidence, validation, authority, recovery or safety boundaries**.

## 1. Governing principles

Every future implementation must preserve these three rules:

1. **Only provide context required now.** An Agent should receive the smallest sufficient projection for its current role and step.
2. **Exclude irrelevant context.** Unrelated tools, Skills, memories, files, logs and Agent histories should not enter the prompt merely because they are available.
3. **Do not repeatedly provide already-known context.** Stable facts should be referenced, summarized, cached or projected rather than copied into every model call, except where provenance or independent verification requires re-reading the source.

The platform optimizes demand; `docs/roadmap/model_access_quota_budget_plan.md` remains the owning plan for provider quota, accounting, budgets and model/provider routing.

## 2. Architectural placement

```text
Goal / Task / Pack
        |
        v
Orchestration -------- Model Access / Budget
        |                    |
        +------ Context & Invocation Efficiency ------+
        |                    |                         |
        v                    v                         v
Context Projection      Invocation Policy        Telemetry
        |                    |                         |
        +------------- Execution ---------------------+
                             |
                             v
                 Durable truth + evidence
```

This layer is cross-cutting. It must integrate with:

- TaskStore and PlatformControlStore durable truth;
- LangGraph sequential/parallel team execution;
- Pack/Skill/tool/knowledge loading;
- model-access quota, budget and policy profiles;
- evidence and artifact provenance;
- Runs/frontend observability;
- deterministic validation and independent acceptance.

It must not create a second task store, a second budget system, or a parallel source of execution truth.

## 3. CIE-0 — Token, cost and latency attribution (P0)

The platform should be able to answer both:

- **How much did this run cost?**
- **Why did it cost that much?**

Target hierarchy:

```text
Run
 -> Task
   -> Agent / role
     -> Model call
       -> context/input components
       -> output
       -> cache behavior
       -> latency
       -> monetary cost
```

Where provider/gateway data exists, model-call attribution should distinguish at least:

```text
system_prompt
role_or_pack_instructions
task_context
history
memory
artifact_or_code_context
tool_schema
tool_result
output
cache_read
cache_write
latency
monetary_cost
```

Rules:

- preserve provider/gateway provenance and freshness;
- unsupported or unavailable fields remain explicit `unknown` / `unsupported` rather than fabricated;
- locally estimated values must not be presented as provider-authoritative;
- telemetry must not persist credentials, private reasoning, unrestricted tool payloads or unsanitized logs;
- aggregation order must be deterministic so parallel completion order is not a product contract.

Long-term frontend projection should make cost concentration visible by Run, Task, Agent and component without turning Runs into a raw log wall.

## 4. CIE-1 — Context Projection and history compaction (P0)

Durable platform state must remain authoritative. Model context is a **projection**, not a second state store.

Preferred flow:

```text
TaskStore / ControlStore / artifacts / evidence
                  |
                  v
          Context Projector
                  |
                  v
      bounded role-specific snapshot
                  |
                  v
                Agent
```

The projector should select only current-step facts such as:

- objective and current task;
- current plan step and dependencies;
- active constraints and authority boundary;
- relevant prior decisions;
- relevant file/symbol/artifact references;
- known failures and negative evidence;
- validation/evidence state;
- next required action.

Do not replay the full task conversation merely to reconstruct execution state. Long-running progress should live in durable structured records and checkpoints, while prompts receive bounded snapshots.

Compaction must preserve references back to the durable source so an Agent or verifier can re-open the original evidence when needed.

## 5. CIE-2 — Pack and Skill progressive disclosure (P0)

Progressive disclosure is a platform contract for future Pack architecture.

A Pack should expose a small first-level index before loading detailed content:

```text
Pack
 |- manifest
 |- capability index
 |- Agent/role index
 |- Skill index
 |- knowledge index
 |- tool registry
 `- resource/template/example references
```

Expected loading behavior:

```text
Pack manifest/capability index
        -> selected domain
        -> selected Skill / knowledge subset
        -> selected resources/examples/templates
```

Do not inject every Skill, rule, reference, example and tool definition from a Pack into every Agent call.

A Pack implementation should be able to declare:

- discovery metadata that is cheap to expose;
- load-on-demand resources;
- role-specific context bundles;
- evidence/provenance requirements;
- allowed tool/capability sets;
- optional context budgets or maximum projected size.

## 6. CIE-3 — Agent tool visibility and schema pruning (P0)

Tool permissions are both:

1. a **security boundary**; and
2. a **context boundary**.

An Agent should see only tools relevant and permitted for its current role/task. For example, a frontend role should not receive database-admin or production-deployment schemas merely because those capabilities exist elsewhere in the platform.

The platform should support a role/task-specific capability view:

```text
Agent role + task + policy + Pack
              |
              v
       visible capability set
              |
              v
     adapter-specific tool schema
```

Do not establish a permanent `CLI > MCP` rule. A capability may have MCP, CLI, HTTP or native adapters. Selection should be explainable and may consider:

- permission/trust boundary;
- reliability;
- latency;
- payload/schema size;
- local/remote availability;
- cost;
- structured-result quality.

## 7. CIE-4 — Structured Agent Handoff Packet (P0)

Agent-to-Agent transfer should use a bounded structured packet by default rather than full conversation propagation.

Target conceptual contract:

```yaml
objective: ...
current_task: ...
decisions: [...]
constraints: [...]
relevant_files: [...]
artifact_refs: [...]
evidence_refs: [...]
known_failures: [...]
open_questions: [...]
next_action: ...
```

Properties:

- references durable artifacts/evidence instead of embedding them when possible;
- preserves provenance for decisions and facts;
- does not copy unrestricted prompts/responses/private reasoning;
- can be independently validated for required fields;
- can be re-projected for a downstream role;
- allows a downstream verifier to re-open source evidence rather than trusting a summary blindly.

## 8. CIE-5 — Stable-prefix and prompt-cache-aware compilation (P1)

Prompt construction should separate stable and dynamic material when provider semantics make caching useful.

Preferred shape:

```text
stable system policy
stable authority/safety contract
stable Agent role
stable tool/capability contract
stable Pack instructions
-----------------------------
dynamic goal/task
current context projection
new artifacts/tool results
current execution state
```

A future Prompt Compiler may record sanitized cache-related metadata such as:

```text
prefix_digest
cache_read_tokens
cache_write_tokens
cache_hit_or_miss
provider_cache_semantics
```

Cache optimization must never cause stale authority, stale execution state or stale evidence to be treated as current truth. Mutable authorization and run state remain dynamic inputs.

## 9. CIE-6 — Tool-output reduction with raw evidence retention (P1)

Large deterministic tool output should not automatically become model context.

Preferred flow:

```text
Tool / CLI / test / scanner output
              |
       +------+------+
       |             |
       v             v
Raw artifact     Output projector
(full evidence)  (bounded structured view)
       |             |
       +-------> Agent context
```

Examples:

- pytest: failed tests, relevant tracebacks, exit code and summary;
- compiler/linter: errors/warnings plus relevant file/line records;
- git diff: relevant hunks and changed-file summary;
- service/process status: bounded state/error fields;
- CI logs: failed job/step plus referenced raw artifact.

The full raw output remains available through artifact/evidence references when needed. Compression must not destroy auditability.

## 10. CIE-7 — Code-intelligence adapters (P1)

Repository tasks should prefer targeted code navigation before broad read/grep loops when reliable indexing exists.

Expose a generic Code Intelligence capability instead of hard-coding one project:

```text
symbol search
reference search
dependency/import search
call graph
file/symbol outline
semantic/code index query
```

Possible adapters include LSP, Tree-sitter-derived indexes, SCIP, CodeQL databases, ctags or other mature code-graph/index projects.

Fallback remains ordinary repository search/read when an index is absent, stale or insufficient. Index freshness/provenance must be explicit.

## 11. CIE-8 — Deterministic-action-first invocation policy (P1)

The cheapest reliable model call is the call that is not needed.

Before model invocation, the platform should be able to identify operations that are already deterministic, for example:

```text
git status
hashing
schema validation
pytest / lint / build execution
known migration/format commands
service start/stop/status through approved adapters
structured file conversion
fixed policy checks
```

Conceptual policy:

```text
Can an approved deterministic capability solve this step?
       | yes                         | no
       v                             v
Tool / script / native action       Model reasoning
```

This is not permission to bypass authority. Deterministic actions still require the same operation/path/risk authorization as any other execution.

## 12. CIE-9 — Cost-aware orchestration (long-term)

Orchestration should eventually compare more than one feasible topology when doing so is useful.

Candidate evaluation inputs may include:

```text
capability fit
quality/confidence requirement
expected context volume
expected model-call count
expected tool payload
prompt-cache opportunity
expected latency
provider/model availability
quota headroom
budget/cost
parallelism and coordination overhead
verification requirement
```

Example product-level explanation:

```text
single-agent:   lower coordination overhead, high projected context
3-agent team:   lower projected context, moderate coordination overhead
6-agent team:   excessive startup/handoff cost for this task
selected:       3-agent team
reason:         meets quality target inside balanced policy and budget
```

Important boundaries:

- more Agents are not assumed to be cheaper;
- fixed `1 TL + N workers` is not a platform contract;
- economic optimization never bypasses authorization, Trust/Decision/Command-Plan gates, evidence or validation;
- existing `economy`, `balanced`, `quality-first`, `latency-first` and `custom` model-access policies remain compatible inputs rather than duplicated policy systems.

## 13. Ephemeral extractor pattern

Large raw inputs may be processed by a short-lived extractor/summarizer when that reduces repeated context in a long-lived parent Agent.

Examples:

- large issue/requirements documents;
- CI logs;
- large JSON payloads;
- PDFs/design exports;
- scanner reports;
- network traces;
- large repository metadata.

Output should be a structured context artifact carrying:

```text
summary
source_artifact_ref
evidence_refs
extraction_method
confidence_or_limitations
```

The parent Agent receives the bounded artifact rather than the entire raw source by default. The raw source remains retrievable for verification.

## 14. Measurement and acceptance model

Optimization is valid only when quality and governance remain intact.

Future experiments should compare an optimized path against a defined baseline and record at minimum where observable:

```text
total input/output tokens
context component breakdown
model-call count
tool-call count
tool-result bytes projected into context
cache read/write/hit data
wall-clock latency
monetary cost
validation outcome
verification/acceptance outcome
retries and failures
```

A change is not accepted merely because it reduces tokens. It must preserve required validation, evidence and independent acceptance. Cost reductions obtained by omitting necessary verification are invalid.

No permanent target such as "50% reduction" is fixed as a product requirement; savings depend on provider, task, repository and topology. Targets should be evidence-based per workload class.

## 15. Phased implementation plan

### Phase CIE-0 — measurement contract

- define sanitized invocation/cost attribution records;
- integrate gateway/provider usage provenance where available;
- expose Run -> Task -> Agent -> call aggregation;
- no orchestration changes yet.

### Phase CIE-1 — Context Projection and handoff

- define role-specific Context Projection contract;
- define structured Agent Handoff Packet;
- prove durable state remains authoritative;
- add compaction/reference behavior for long-running tasks.

### Phase CIE-2 — progressive capability loading

- Pack/Skill progressive-disclosure metadata;
- role/task tool visibility;
- tool-schema pruning;
- bounded context budgets where useful.

### Phase CIE-3 — output and retrieval efficiency

- structured output projectors with raw artifact retention;
- code-intelligence adapter interface;
- fallback/freshness semantics.

### Phase CIE-4 — cache-aware prompt compilation

- stable-prefix/dynamic-suffix contract;
- cache telemetry where provider support exists;
- prove mutable authority/state is never frozen into stale cache material.

### Phase CIE-5 — deterministic invocation reduction

- classify deterministic steps that need no model reasoning;
- use existing trusted adapters rather than model round-trips;
- record why a model call was skipped or required.

### Phase CIE-6 — cost-aware topology selection

- estimate multiple feasible topologies;
- integrate model-access quota/budget/policy signals;
- emit deterministic human-readable selection reasons;
- retain explicit fallback topology.

Each phase requires a separately authorized implementation Work Item; this roadmap grants none.

## 16. Permanent boundaries

Do not:

- create a second durable workflow or telemetry truth that competes with TaskStore/control-store truth;
- duplicate provider quota/budget accounting already owned by model access;
- expose credentials, unrestricted raw logs or private reasoning for observability;
- optimize by dropping required validation, evidence or independent acceptance;
- make a single code-graph, CLI reducer, MCP server or telemetry product mandatory without a measured requirement;
- assume all tasks benefit from decomposition into more Agents;
- make cache hits an authority or freshness signal;
- let economic routing widen repository, operation, permission or publication authority;
- treat locally estimated provider usage/cost as authoritative provider balance;
- use full-chat propagation as the default Agent handoff mechanism.

## 17. Complete-capability acceptance criteria

The long-term capability is complete only when the platform can demonstrate all of the following:

1. a Run can explain token/cost concentration by Task, Agent and context component when the underlying provider exposes sufficient data;
2. unavailable accounting fields remain explicit rather than fabricated;
3. long-lived execution state is projected from durable truth instead of reconstructed from full conversation replay;
4. Pack/Skill/tool/knowledge content is progressively loaded according to task and role;
5. each Agent receives a bounded visible tool/capability set;
6. Agent handoffs use structured referenced packets by default;
7. raw tool output is retained as evidence while bounded projections enter model context;
8. code intelligence can narrow repository reads through an adapter with explicit freshness/fallback;
9. cache-aware prompt compilation can exploit stable prefixes without caching mutable authority as current truth;
10. deterministic steps can avoid unnecessary model calls while remaining governed;
11. orchestration can explain why a chosen topology is preferred under quality, latency, quota and budget constraints;
12. all optimization remains subordinate to authority, verification, evidence and safety rules.

## 18. Architectural decision summary

Fixed direction:

```text
Treat model context as a bounded projection, not a state store.
Measure cost before optimizing it.
Load Pack/Skill/tool/knowledge progressively.
Treat tool visibility as both permission and context policy.
Pass structured handoff packets instead of full histories.
Preserve raw evidence while projecting compact tool results.
Prefer targeted code intelligence before broad repository reads when reliable.
Avoid model calls for already-deterministic approved actions.
Use prompt-cache-aware stable prefixes where safe and supported.
Make cost/context efficiency an input to future topology selection, never an authority override.
```
