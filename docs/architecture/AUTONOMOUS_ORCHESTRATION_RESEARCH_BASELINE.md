# Autonomous Orchestration Research Baseline

> Status: research/architecture baseline for #508.  
> Parent directions: #137 Mother Platform and #252 Autonomous Improvement Loop.  
> This document records research-derived design constraints and future adoption targets. It does **not** claim that research-only capabilities are already implemented and grants no execution authority.

## 1. Why this baseline exists

Nerelan / reverse-agent already has a real orchestration substrate. The project is therefore not looking for another generic multi-Agent framework. The useful question is narrower and more difficult:

> How should the platform decide which Agents, tools, executors and topology to use for a task, change that topology when evidence changes, remember effective workflows, evaluate the process independently, and later improve orchestration through bounded experiments without weakening policy or durable truth?

The literature reviewed here is absorbed as architectural guidance for that problem.

The permanent reuse rule is:

```text
LangGraph
  = orchestration mechanics / graph execution

TaskStore
  = durable runtime truth

Connection / Executor / Binding
  = concrete access and execution selection

Policy / authority / budgets
  = hard admission constraints

Verifier / evidence
  = independent acceptance boundary

Research-derived adaptive layer
  = topology selection, workflow memory, process evaluation,
    evidence-backed optimization and bounded self-improvement
```

Do not replace the existing stack merely because a paper ships its own framework.

---

## 2. Current repository baseline: what is already solved

The following are already part of the project baseline and must not be reopened as greenfield architecture work without a measured defect:

- LangGraph is the selected orchestration spine;
- sequential team execution exists;
- LangGraph `Send` fan-out / join exists;
- distinct durable TaskStore tasks can execute in bounded parallel batches;
- each task retains independent claim, budget, evidence and recovery semantics;
- TaskStore remains the durable source of execution truth rather than graph-local memory;
- worker results are normalized into structured team results;
- a verifier can reject a team even when individual execution reports success;
- acceptance is separated from executor self-report;
- recovery and resume remain per durable task rather than introducing a second workflow database;
- existing executor/runtime surfaces are reused rather than building another generic Agent shell.

This means the next orchestration gap is **not** "add multiple Agents" or "add a scheduler". The remaining research gap is adaptive orchestration above the proven execution substrate.

---

## 3. Canonical research inputs and adopted lessons

### 3.1 Magentic-One — orchestrator as a continuing control loop

Paper: [Magentic-One: A Generalist Multi-Agent System for Solving Complex Tasks](https://arxiv.org/abs/2411.04468)

Primary lesson:

```text
plan
-> execute
-> observe progress
-> detect stalls/errors
-> re-plan
```

Adopt:

- orchestration must remain active after the initial plan;
- progress and failure evidence should be first-class inputs to later routing decisions;
- re-planning should be explicit and explainable rather than hidden in a long prompt;
- a run may stop, retry, change topology or escalate based on observed state.

Do not copy:

- a monolithic orchestrator state that competes with TaskStore as durable truth.

Nerelan mapping:

- TaskStore + events/evidence provide the durable observations;
- the adaptive orchestration layer may use those observations to propose the next bounded graph/topology;
- policy/authority remains external to the orchestrator.

### 3.2 DyLAN — dynamic team selection and early stopping

Paper/code: [Dynamic LLM-Agent Network (DyLAN)](https://github.com/SALT-NLP/DyLAN)

Primary lesson:

- a fixed Agent roster is wasteful and often task-inappropriate;
- inference-time team selection can improve efficiency;
- contribution signals can inform which Agents remain useful;
- early stopping is a legitimate orchestration decision.

Adopt:

```text
Task
-> derive capability requirements
-> identify compatible candidate Agents / tools / executors
-> remove candidates that add no justified capability
-> execute only the bounded team needed
-> allow early termination when acceptance evidence is already sufficient
```

Do not adopt a paper-specific Agent Importance Score as product truth before Nerelan has its own operational/eval history. Contribution scoring must be evidence-backed and version-scoped.

### 3.3 GPTSwarm — orchestration as an explicit graph optimization problem

Paper: [GPTSwarm: Language Agents as Optimizable Graphs](https://proceedings.mlr.press/v235/zhuge24a.html)

Primary lesson:

- an Agent system can be represented as a computational graph;
- nodes represent operations/Agents/tools;
- edges represent information flow;
- both node behavior and graph connectivity can be optimized.

Adopt the representation principle:

```text
CandidateTopology
  nodes = roles / Agents / tools / verifiers / transformations
  edges = dependency and information-flow relationships
```

The topology must be inspectable, serializable and attributable to the decision that selected it.

Do not adopt GPTSwarm as a second runtime. LangGraph remains the graph execution engine. GPTSwarm informs how Nerelan should **reason about and evaluate candidate graphs**, not how graph execution should be reimplemented.

### 3.4 AFlow — workflow generation as bounded search over executable structures

Paper: [AFlow: Automating Agentic Workflow Generation](https://proceedings.iclr.cc/paper_files/paper/2025/hash/5492ecbce4439401798dcd2c90be94cd-Abstract-Conference.html)

Primary lesson:

- workflow design can be treated as a search problem over code/graph-represented workflows;
- execution feedback should drive refinement;
- smaller/cheaper models can become competitive when the workflow is better designed.

Adopt later, after real operational/eval history exists:

```text
bounded candidate workflow generation
-> execute against declared eval set
-> collect quality / cost / latency / failure evidence
-> compare candidates
-> retain the winning pattern with provenance
```

Hard constraint:

> Search/optimization may choose only among policy-compatible candidates. It cannot weaken authority, policy, budget, credential or sandbox constraints in order to improve a score.

Do not import AFlow as a parallel framework. The search layer should emit candidate LangGraph-compatible topologies or higher-level orchestration specifications.

### 3.5 Agent Workflow Memory — procedural memory, not chat memory

Paper: [Agent Workflow Memory](https://proceedings.mlr.press/v267/wang25bx.html)

Primary lesson:

- long-horizon Agents benefit from inducing reusable workflows from previous trajectories;
- workflows can be retrieved selectively for later tasks;
- procedural memory can reduce repeated planning and unnecessary steps.

Adopt:

```text
successful / informative run evidence
-> extract reusable WorkflowPattern
-> attach applicability conditions and provenance
-> retrieve for a later similar task
-> adapt under current constraints
-> verify again
```

A reusable workflow is not durable runtime truth and is never automatic authority.

Every stored workflow pattern should be scoped by at least:

- task/problem family;
- required capabilities;
- executor/model/tool compatibility;
- source run/evidence references;
- success/failure history;
- version/freshness information;
- known preconditions;
- policy assumptions;
- invalidation conditions.

The project should prefer extending existing evidence/project-knowledge structures before inventing a separate memory database.

### 3.6 Agent-as-a-Judge — evaluate the trajectory, not only the final artifact

Paper: [Agent-as-a-Judge: Evaluate Agents with Agents](https://proceedings.mlr.press/v267/zhuge25a.html)

Primary lesson:

- outcome-only evaluation loses important information about Agentic execution;
- an evaluator can inspect intermediate behavior and provide process-level feedback.

Adopt as a complement to deterministic verification:

```text
execution trace / structured events
+ changed files / artifacts
+ tests / deterministic checks
+ policy events / retries / failures
-> ProcessEvaluation
-> acceptance / re-plan / escalation evidence
```

Permanent boundary:

- deterministic checks remain authoritative where deterministic truth is available;
- an Agent judge may add semantic/process evaluation but cannot replace hard policy, tests, security checks or exact-head acceptance;
- the worker being evaluated must not be the sole authority that accepts its own work.

### 3.7 ADAS — automated design belongs inside the experiment loop

Paper: [Automated Design of Agentic Systems](https://proceedings.iclr.cc/paper_files/paper/2025/hash/36b7acf6f6010652b3f2a433774a66fe-Abstract-Conference.html)

Primary lesson:

- prompts, tools, workflows and combinations can themselves become the search space;
- a meta-Agent can generate new Agent designs as code.

Adopt only as a long-term #252/Ail experiment mechanism:

```text
meta-agent proposes candidate orchestration design
-> candidate receives bounded identity
-> isolated execution
-> independent eval/verifier
-> compare against baseline
-> accept/reject/defer
```

Never allow a meta-Agent to grant its own authority or silently modify the verifier/policy that judges it.

### 3.8 Darwin Gödel Machine — self-modification requires empirical validation and isolation

Paper: [Darwin Gödel Machine: Open-Ended Evolution of Self-Improving Agents](https://arxiv.org/abs/2505.22954)

Primary lesson:

- Agent implementations can iteratively modify themselves;
- an archive of diverse candidates supports open-ended exploration;
- empirical benchmark validation is the practical acceptance mechanism used by the work.

Relevant to Nerelan only at the mature end of #252.

Required Nerelan constraints are stricter than "candidate benchmark improved":

```text
candidate self-change
-> isolated branch/workspace/sandbox
-> immutable baseline identity
-> declared eval suite
-> independent verifier
-> security/policy regression checks
-> cost/latency/reliability comparison
-> rollback path
-> explicit authority boundary
```

Self-modification must not imply self-merge, self-release or the ability to redefine the acceptance mechanism that judges the candidate.

### 3.9 AutoGen and MetaGPT — useful abstractions, not replacement runtimes

Papers:

- [AutoGen: Enabling Next-Gen LLM Applications via Multi-Agent Conversation](https://www.microsoft.com/en-us/research/publication/autogen-enabling-next-gen-llm-applications-via-multi-agent-conversation-framework/)
- [MetaGPT: Meta Programming for A Multi-Agent Collaborative Framework](https://proceedings.iclr.cc/paper_files/paper/2024/hash/6507b115562bb0a305f1958ccc87355a-Abstract-Conference.html)

Absorb:

- Agents should have explicit roles/capabilities rather than being indistinguishable chat participants;
- intermediate artifacts and structured handoffs matter;
- SOPs are useful reusable domain knowledge;
- multi-Agent collaboration needs explicit communication/control structure.

Do not absorb:

- fixed software-company role chains as a universal topology;
- another conversational Agent runtime beside LangGraph.

MetaGPT-like SOPs fit better as Pack/workflow templates or WorkflowPatterns that can be selected or omitted according to task needs.

### 3.10 SWE-agent and OpenHands — the interface/runtime boundary affects Agent quality

Papers:

- [SWE-agent: Agent-Computer Interfaces Enable Automated Software Engineering](https://proceedings.neurips.cc/paper_files/paper/2024/hash/5a7c947568c1b1328ccc5230172e1e7c-Abstract-Conference.html)
- [OpenHands: An Open Platform for AI Software Developers as Generalist Agents](https://proceedings.iclr.cc/paper_files/paper/2025/hash/a4b6ad6b48850c0c331d1259fc66a69c-Abstract-Conference.html)

Absorb:

- Agent performance depends strongly on the execution/tool interface, not only model quality;
- shell/file/browser/editing actions need stable, understandable semantics;
- sandbox and evaluation infrastructure are part of Agent architecture.

Nerelan mapping:

- continue using mature executors/adapters rather than rebuilding coding-agent runtimes;
- treat tool/interface capability metadata as an input to routing;
- Pack compatibility and sandbox requirements should constrain topology selection before optimization.

---

## 4. Target autonomous-orchestration control loop

The research baseline converges on the following target architecture:

```text
Task / Goal subtask
        |
        v
CapabilityRequirement extraction
        |
        v
Candidate Agent / Tool / Executor / WorkflowPattern set
        |
        v
HARD FILTER
  policy
  authority
  secrets
  sandbox
  environment
  compatibility
  budget admission
        |
        v
CandidateTopology generation / retrieval
        |
        v
Evidence-backed routing / selection
        |
        v
LangGraph execution
        |
        +-----------------------------+
        |                             |
        v                             v
TaskStore events/evidence       deterministic checks
        |                             |
        +-------------+---------------+
                      v
              ProcessEvaluation
                      |
        +-------------+--------------+
        |             |              |
        v             v              v
      ACCEPT        RE-PLAN       ESCALATE/STOP
        |
        v
WorkflowPattern / routing evidence update
```

The critical ordering is intentional:

> **Hard policy and compatibility filtering happens before learned, heuristic or search-based optimization.**

Optimization decides among authorized compatible choices; it does not decide what is authorized.

---

## 5. Conceptual contracts to add in later bounded implementation

These names are architectural concepts, not declarations that code already exists.

### 5.1 `CapabilityRequirement`

Represents what the task requires before choosing a team.

Candidate fields:

```text
capabilities
required_tools
repository/write needs
network needs
browser needs
sandbox_level
verification_requirements
artifact_types
latency/cost constraints
parallelizable
human_review_requirement
```

### 5.2 `CandidateTopology`

Represents one inspectable possible orchestration graph.

Candidate fields:

```text
topology_id
nodes
edges
roles
bindings
workflow_patterns
estimated_cost
estimated_latency
compatibility_evidence
source = generated | retrieved | static_baseline
provenance
```

### 5.3 `RoutingDecision`

Records why one topology/binding set was selected.

Candidate fields:

```text
task_id
candidate_topology_ids
hard_filter_results
selected_topology_id
objective_weights
historical_evidence_refs
selection_reason
uncertainty
model/tool/version identities
```

The decision must be reproducible enough to explain "why this team/topology?" after the run.

### 5.4 `WorkflowPattern`

Represents reusable procedural memory extracted from prior evidence.

Candidate fields:

```text
pattern_id
problem_family
capability_requirements
topology_template
preconditions
applicability_scope
source_run_refs
verifier/eval outcomes
known_failure_modes
version/freshness scope
policy assumptions
invalidation_conditions
```

A WorkflowPattern is advisory/retrievable knowledge, not execution authority.

### 5.5 `ProcessEvaluation`

Represents semantic evaluation of the run trajectory in addition to deterministic results.

Candidate fields:

```text
run/task identity
trace/evidence refs
requirement-level findings
process defects
unnecessary steps
recovery quality
policy anomalies
semantic quality findings
confidence
recommended disposition
```

It cannot override deterministic failure or hard policy rejection.

---

## 6. Evidence needed before adaptive routing becomes real product behavior

Do not implement "smart routing" from intuition alone.

The project should first accumulate sanitized run/eval history such as:

```text
task_family
required_capability
role
topology
executor
provider/model/version
tool/runtime versions
attempt/retry history
duration
token/cost usage
failure classification
process-evaluation findings
verifier result
rework count
final acceptance
```

Only then should Nerelan learn or optimize:

- Agent/team selection;
- topology choice;
- workflow retrieval;
- model/executor/tool routing;
- early stopping;
- re-plan triggers.

Until enough evidence exists, explicit deterministic baselines should remain available for comparison and rollback.

---

## 7. Research-derived adoption sequence inside the existing roadmap

This baseline does **not** create a new parallel roadmap. It refines #137 and #252.

### Near term — preserve current critical path

```text
governance/reliability closure
-> real-provider dogfood
-> productization / user-journey proof
-> first deep Pack
```

Do not delay those tasks merely to add experimental orchestration complexity.

### Evidence collection phase

Add/standardize the telemetry needed to answer:

- which capabilities were required?
- which topology/binding was used?
- what failed?
- what did the verifier/process evaluator observe?
- what did the run cost?
- did the same workflow succeed repeatedly?

### Adaptive routing phase

Introduce:

1. `CapabilityRequirement` extraction;
2. hard compatibility/policy filtering;
3. multiple inspectable candidate topologies;
4. evidence-backed routing among those candidates;
5. explainable routing decisions;
6. deterministic fallback topology.

DyLAN and GPTSwarm are the strongest conceptual inputs here.

### Workflow-memory phase

Introduce reusable `WorkflowPattern` extraction/retrieval with applicability/freshness constraints.

Agent Workflow Memory is the primary research input here.

### Process-evaluation phase

Extend independent evaluation from final artifacts to trajectory-level semantics while preserving deterministic acceptance.

Agent-as-a-Judge is the primary input here.

### Bounded workflow-search phase

Under #252 AIL-2/Ail-3, allow multiple candidate workflows/topologies to compete in isolated experiments.

AFlow/GPTSwarm provide the main search/optimization model.

### Automated Agent-design phase

Only after the experiment/eval substrate is trustworthy, permit ADAS-style meta-Agent generation of new orchestration designs.

### Self-modification phase

Darwin Gödel Machine-style self-modification belongs at the mature end of #252, with stronger Nerelan policy, sandbox, provenance, regression and publication boundaries than benchmark performance alone.

---

## 8. Explicit non-goals

The literature review does **not** justify any of the following:

- replacing LangGraph with AutoGen, MetaGPT, GPTSwarm or AFlow;
- adding an `executor_kind="multi_agent"`;
- creating a second task/workflow database;
- treating graph-local state as durable truth;
- always invoking every available Agent;
- hard-coding a universal Planner -> Coder -> Tester -> Reviewer chain;
- using an Agent judge as a substitute for tests/security/policy;
- letting workflow memory act as authority;
- optimizing cost/quality using claims without measured run history;
- allowing a meta-Agent to weaken policy or redefine its own acceptance criteria;
- allowing self-improvement to imply autonomous merge/release/deploy.

---

## 9. Architecture invariants produced by this research review

These are the durable conclusions to preserve in future design work:

1. **Orchestration is adaptive control, not a one-time decomposition step.**
2. **Agent/team membership should be task- and evidence-dependent, not fixed globally.**
3. **Candidate workflows/topologies should be explicit graph objects that can be inspected, compared and reproduced.**
4. **LangGraph remains execution mechanics; research layers select and optimize graphs above it.**
5. **TaskStore remains durable execution truth; memory and graph state do not replace it.**
6. **Policy, authority, sandbox, credential and compatibility constraints are hard filters before optimization.**
7. **Procedural/workflow memory must be provenance-, applicability- and freshness-scoped.**
8. **Process-level semantic evaluation complements but never replaces deterministic verification.**
9. **Workflow/Agent optimization must happen through bounded experiments with explicit baselines and independent evaluation.**
10. **Self-generated plans and self-modifications never grant their own authority.**
11. **The system must support `stop`, `reject`, `defer` and `escalate`, not only retry until something passes.**
12. **New research is absorbed as thin decision/evaluation layers around mature components, not as framework proliferation.**

---

## 10. Reading order for future implementation work

For an engineer implementing the next adaptive-orchestration layer, read in this order:

1. Magentic-One — continuing orchestration/re-planning model;
2. DyLAN — dynamic team selection and early stopping;
3. GPTSwarm — graph representation and topology optimization;
4. Agent Workflow Memory — reusable procedural memory;
5. Agent-as-a-Judge — trajectory-level evaluation;
6. AFlow — bounded workflow search from execution feedback;
7. ADAS — automated Agent-system design;
8. Darwin Gödel Machine — self-modification under empirical evaluation;
9. SWE-agent / OpenHands — execution/tool-interface constraints;
10. AutoGen / MetaGPT — historical multi-Agent composition/SOP context.

The order reflects Nerelan's needs, not paper prestige: first make orchestration adaptive and measurable, then make it reusable, then optimize it, and only then consider self-design/self-modification.

---

## 11. Resulting project position

The research does not invalidate the current architecture. It sharpens the next layer.

Nerelan should evolve from:

```text
predefined tasks
-> predefined compatible topology
-> governed durable execution
-> verifier
```

into:

```text
task
-> capability analysis
-> policy-compatible dynamic team/topology selection
-> governed durable execution
-> deterministic + process-level evaluation
-> re-plan / accept / stop
-> provenance-scoped workflow learning
-> later bounded topology/Agent-design optimization
```

The differentiating product capability is therefore not "many Agents". It is **governed, durable, evidence-driven adaptive orchestration**.