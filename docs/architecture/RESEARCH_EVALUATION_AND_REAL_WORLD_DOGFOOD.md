# Research Baseline — Evaluation, Complexity Admission and Real-World Dogfood

Status: research-derived architecture baseline; **not an implementation claim**.

Owner Work Item: #513  
Parent/implementation owners: #137, #252, #253, #260, #361  
Related research grounding: #508 / PR #509

## 1. Purpose

This document translates current Agent/software-engineering evaluation research into Nerelan/reverse-agent rules for:

- deciding when a more complex Agent topology is justified;
- evaluating repeated-run reliability rather than one successful demonstration;
- accounting for statistical uncertainty;
- designing real-world dogfood beyond toy edits;
- mapping public benchmarks into project-specific evals without turning the repository into a benchmark platform.

The project already requires independent verification, evidence, budgets and real-provider dogfood. The research below sharpens **how improvement claims should be compared and promoted**.

Permanent research principle:

> A more sophisticated Agent architecture is not an improvement until it beats a simpler baseline on declared, repeated and independently verified measurements.

---

## 2. Research inputs

### Agentless — simple software-engineering baseline

Canonical paper artifact:

- https://lingming.cs.illinois.edu/publications/fse2025.pdf

Research lesson:

Strong repository-level software-engineering performance can be achieved with a comparatively simple localization -> repair -> validation process. This is a useful warning against assuming that more Agents, roles, messages or coordination layers automatically improve results.

Nerelan implication:

Every material increase in orchestration complexity should be compared against simpler candidates such as:

```text
Baseline A
single capable Agent + tools + deterministic verifier

Baseline B
planner -> executor -> deterministic verifier

Candidate C
adaptive multi-Agent topology
```

Candidate C should not become the default merely because it is architecturally richer.

### tau-bench — repeated interaction reliability

Canonical preprint page:

- https://arxiv.org/abs/2406.12045

Research lesson:

Interactive Agent evaluation should measure not only one trajectory's success but consistency across repeated attempts. `pass^k`-style reliability asks whether the system can continue succeeding when the same capability is exercised multiple times rather than benefiting from one lucky trajectory.

Nerelan implication:

For unattended operation:

```text
one PASS
!=
stable capability
```

Important workflows should eventually record repeated-run behavior under controlled conditions, especially when a new routing/topology/memory strategy is being promoted.

### Adding Error Bars to Evals — uncertainty-aware comparison

Canonical preprint page:

- https://arxiv.org/abs/2411.00640

Research lesson:

Small benchmark score differences may reflect sampling noise rather than true improvement. Evaluation should report uncertainty and use paired/comparable experimental design where possible.

Nerelan implication:

Reject promotion logic such as:

```text
Workflow A: 62%
Workflow B: 64%
therefore B is permanently better
```

without enough evidence.

Future #252 selector logic should be able to represent:

```text
sample size
paired task identity
mean/median outcome where meaningful
variance / uncertainty interval
repeated-run stability
cost / latency
verifier outcome
minimum practical effect threshold
```

Exact statistical method belongs to the eval implementation, not this document.

### TheAgentCompany — whole-environment knowledge work

Canonical publication page:

- https://proceedings.neurips.cc/paper_files/paper/2025/hash/0d744742f6fac4d1134c019b7cef3c8a-Abstract-Datasets_and_Benchmarks_Track.html

Research lesson:

Real Agent work spans more than editing code. It can require browsing, communication, application interaction, information gathering and software execution across a simulated organization.

Nerelan implication:

Whole-platform dogfood should eventually test the platform's composition of:

```text
Goal intake
planning
repository work
browser/tool activity where authorized
multi-step coordination
checkpoint/restart
budget enforcement
verification/evidence
publication boundary
product UI/readback
```

not only isolated source edits.

### SWE-bench Multimodal — visual software-engineering tasks

Canonical review artifact:

- https://openreview.net/pdf?id=riTiq3i21b

Research lesson:

Software-engineering tasks may require understanding screenshots, visual defects and UI state rather than only source text.

Nerelan implication:

The multimodal input direction under #287 and product/user-journey validation under #260 should eventually include tasks in which an image/screenshot is required evidence, not decorative context.

### SWE-PolyBench — multilingual repository tasks

Canonical preprint page:

- https://arxiv.org/abs/2504.08703

Research lesson:

Repository-level Agent performance can vary materially by programming language/ecosystem. A software-engineering platform should not infer universal capability from one Python-heavy benchmark.

Nerelan implication:

Pack/executor/model performance history should preserve task language/ecosystem as part of applicability instead of producing one global quality score.

### SWE-EVO — long-horizon software evolution

Canonical preprint page:

- https://arxiv.org/abs/2512.18470

Research lesson:

Longer software-evolution tasks spanning many files and validations are substantially harder than isolated issue repair. This better reflects the intended unattended project-development use case.

Nerelan implication:

Dogfood should eventually include a multi-step project evolution scenario in which the plan changes over time, multiple tasks interact and regressions must be caught before final acceptance.

### BeyondSWE — broader software-engineering task taxonomy

Canonical preprint page:

- https://arxiv.org/abs/2603.03194

Research lesson:

Software-engineering Agent quality is multi-dimensional; different systems may lead on different task classes. Cross-repository reasoning, dependency migration and other tasks expose limitations hidden by a single benchmark family.

Nerelan implication:

This supports capability- and Pack-specific routing rather than a permanent universal "best model" label.

This source is best treated as benchmark-taxonomy input and should be revalidated before implementation decisions because it is recent preprint work.

### WorkArena — realistic enterprise web/knowledge tasks

Canonical publication page:

- https://proceedings.mlr.press/v235/drouin24a.html

Research lesson:

Browser/enterprise tasks benefit from realistic application state and end-to-end task success criteria rather than synthetic one-step browser actions.

Nerelan implication:

Future browser/user-journey Packs should favor realistic multi-step scenarios and deterministic end-state assertions where possible.

### ExpeL — experiential learning across tasks

Canonical publication page:

- https://ojs.aaai.org/index.php/AAAI/article/view/29936

Research lesson:

Agents can extract reusable experience from prior tasks and use it in later tasks without parameter training.

Nerelan implication:

This supports #252 AIL-4 experience reuse, but promotion of experience must compose with the memory-admission/security constraints in `RESEARCH_AGENT_SECURITY_AND_MEMORY_TRUST.md` and #379.

Experience that appears useful in one run is not automatically durable knowledge.

---

## 3. Complexity Admission Gate

Research from Agentless and the broader Agent literature motivates a permanent architecture-quality rule.

Before introducing or promoting a materially more complex orchestration pattern, record a comparison against a simpler viable baseline.

Conceptual review:

```text
proposed complexity change
        |
        v
what problem does it solve?
        |
        v
simplest credible baseline
        |
        v
controlled comparison
        |
        +-> quality / verifier success
        +-> repeated-run stability
        +-> token / cost
        +-> latency
        +-> tool/repository calls
        +-> rework / retries
        +-> operational failure modes
        |
        v
PROMOTE / KEEP_EXPERIMENTAL / REJECT
```

### Complexity classes that require evidence

Examples:

```text
adding another Agent role
adding recursive critic/reviewer loops
adding dynamic topology selection
adding a new retrieval stage
adding a new memory layer
adding autonomous workflow search
adding a second executor in a critical path
adding another evaluation model/judge layer
```

This complements #361 Mature Component Reuse Gate:

```text
Reuse Gate asks:
  should Nerelan build this mechanism at all?

Complexity Admission asks:
  even if available, does adding this mechanism improve the product enough to justify its cost/failure surface?
```

No separate governance subsystem is required; this is a research-derived review criterion for future Work Items and #252 experiments.

---

## 4. Required evaluation dimensions

A mature comparison should not collapse all outcomes into one success percentage.

Candidate dimensions:

```text
quality / independent verifier result
repeated-run reliability
security invariants
reproducibility
latency
model/tool calls
token/input/output use
cost where observable
retry/rework count
failure category
human intervention count
context size
repository read count
publication/idempotency outcome
recovery after interruption
```

Not every experiment needs every metric. Each must predeclare the subset that can falsify its improvement hypothesis.

---

## 5. Repeated-run reliability

For capabilities that are expected to operate unattended, evaluate stability across repeated runs when feasible.

Conceptually track:

```text
single-run success
success across k repeated attempts
variance in cost/latency
failure-mode distribution
consistency of final verifier result
```

Use stable task identities and comparable environments where possible.

A routing/topology/memory improvement should not be promoted if it raises average score while creating unacceptable tail failures or highly unstable unattended behavior.

---

## 6. Uncertainty-aware promotion

#252 Autonomous Improvement should eventually separate:

```text
observed difference
from
credible/practically meaningful difference
```

Candidate promotion requirements:

1. experiments use comparable task inputs;
2. random/provider/environment variation is recorded where relevant;
3. repeated trials are used for stochastic workflows when affordable;
4. uncertainty is represented rather than hidden;
5. a minimum practical benefit can be required before accepting additional complexity;
6. the selector may return `NEEDS_MORE_EVIDENCE` or reject all candidates.

One green CI run remains necessary evidence for a code candidate but is insufficient evidence for a broad claim that a new Agent strategy is globally better.

---

## 7. Benchmark-to-product mapping rule

Public benchmarks are evidence sources, not the product acceptance authority.

Permanent mapping:

```text
public benchmark finding
-> identify relevant capability/task family
-> construct/adopt bounded Nerelan eval fixture
-> run through current executor/model/Pack/policy boundary
-> collect Nerelan verifier/evidence/budget/recovery data
-> decide applicability
```

Do not:

```text
paper reports benchmark gain
-> mark Nerelan architecture decision as proven
```

Benchmark versions, task distributions and environment assumptions must remain explicit.

---

## 8. Whole-platform dogfood matrix

The mother-platform roadmap already requires real-provider full dogfood. Research suggests extending the long-term dogfood program across orthogonal dimensions rather than repeatedly testing one happy-path code edit.

### 8.1 Horizon

```text
single bounded task
multi-task Goal
multi-phase Goal
long-running software-evolution scenario
```

### 8.2 Task modality

```text
text-only
text + files
text + image/screenshot
browser/tool state where authorized
```

### 8.3 Repository scale/change scope

```text
single-file
multi-file
dependency-aware cross-module
large repository context
```

### 8.4 Language/ecosystem

```text
Python
JavaScript / TypeScript
another independently supported Pack/ecosystem
```

Do not add languages merely to chase a benchmark. Use task families relevant to actual supported product claims.

### 8.5 Runtime properties

```text
parallel eligible work
checkpoint/restart
worker failure with successful sibling
retry/replan
budget exhaustion/block
provider/tool unavailability
independent verification
idempotent Draft publication
```

### 8.6 Security properties

```text
untrusted repository content
indirect prompt injection fixture
project-local config trust boundary
sandbox-required execution where applicable
memory poisoning/staleness fixture
```

### 8.7 Product/user-journey properties

```text
setup/configuration
Goal creation
run progress understanding
blocked/error recovery
validation/evidence inspection
completion/publication understanding
```

Deterministic browser E2E and black-box exploratory Agent QA remain complementary as already directed by #137/#260.

---

## 9. Suggested canonical dogfood suites

These are research-derived test-shape recommendations, not implementation authority.

### DOGFOOD-A — reliable bounded repository task

```text
real Goal
-> Plan/Tasks
-> model/executor work
-> verifier
-> evidence
-> Draft publication
```

Run repeatedly to establish a reliability baseline.

### DOGFOOD-B — interruption and recovery

```text
real Goal
-> parallel eligible tasks
-> force/simulate process interruption
-> restart/reconcile
-> preserve completed sibling
-> continue without duplicate execution
-> final verifier/evidence
```

### DOGFOOD-C — long-horizon repository evolution

```text
multi-step feature/refactor/migration
-> plan revision from repository evidence
-> multiple commits/tasks
-> regression checks
-> negative-path event
-> final integration validation
```

### DOGFOOD-D — multimodal UI defect

```text
screenshot/image + textual goal
-> locate relevant frontend code
-> change
-> deterministic browser/visual evidence where authorized
-> verifier
```

### DOGFOOD-E — adversarial Agent/tool content

```text
legitimate task
+ malicious repository/web/tool text
-> no unauthorized side effect
-> legitimate objective preserved
-> security boundary evidence
```

### DOGFOOD-F — experience reuse

```text
Task class X fails with approach A
-> negative result admitted with provenance
-> later comparable Task X'
-> retrieve applicable negative result
-> avoid blind repetition
-> measure benefit/harm
```

---

## 10. Autonomous Improvement experiment contract

Research-derived refinement for #252:

Each material optimization hypothesis should predeclare:

```text
problem/task family
baseline
candidate
expected mechanism
primary metric
safety/security invariants
cost/latency budget
number/repetition strategy where feasible
falsification threshold
promotion threshold
rollback condition
applicability scope
```

After execution:

```text
raw results
-> independent verifier/eval evidence
-> uncertainty/reliability analysis
-> complexity/cost comparison
-> ACCEPT / REJECT / DEFER / NEEDS_MORE_EVIDENCE
```

The candidate cannot redefine the verifier/evaluation criterion used to accept itself unless separately authorized.

---

## 11. Experience reuse evaluation

Inspired by ExpeL and aligned with #252/#379:

Do not evaluate memory only by retrieval precision.

Measure whether admitted experience actually improves later work:

```text
repeat-failure reduction
rework reduction
tool-call reduction
context/token reduction
verifier success change
latency/cost change
harmful/stale-memory rate
```

Memory should be removable/downgraded if historical experience causes regressions under changed applicability conditions.

---

## 12. Routing/eval history applicability

A performance record should eventually retain relevant context such as:

```text
task_family
language/ecosystem
Pack/version
executor/version
provider/model/version
tool/runtime configuration
repository scale/change scope
context/retrieval strategy
topology/workflow identity
security/isolation profile
verifier identity/version
```

This prevents a result from one narrow benchmark being treated as universal routing truth.

---

## 13. Failure taxonomy

For comparison and routing, distinguish at least relevant classes:

```text
PLANNING_FAILURE
CONTEXT/RETRIEVAL_FAILURE
EXECUTOR_FAILURE
MODEL_OUTPUT_FAILURE
TOOL/PROTOCOL_FAILURE
PROVIDER/QUOTA_FAILURE
POLICY_BLOCK
SANDBOX/SECURITY_FAILURE
VALIDATION_FAILURE
REPRODUCIBILITY_FAILURE
PUBLICATION_FAILURE
BUDGET_EXHAUSTED
USER/REQUIREMENT_AMBIGUITY
UNKNOWN
```

Exact taxonomy remains implementation-owned. Avoid collapsing all non-PASS outcomes into one score.

---

## 14. Complexity budget

A candidate that improves quality may still be rejected if it introduces disproportionate operational burden.

Track where relevant:

```text
number of Agent roles
number of model calls
number of tool calls
context volume
coordination messages
new dependencies/services
new persistent state
new security boundaries
new recovery modes
new user-visible concepts
```

The goal is not minimum complexity at all costs. The goal is **justified complexity**.

---

## 15. Reuse boundary

This research does **not** justify:

```text
a new generic benchmark platform
a custom browser automation framework beside mature tools
a custom statistical package
a public model leaderboard as platform truth
running every public benchmark in CI
a second evaluation event store
a new Agent framework solely for benchmark parity
```

Prefer mature benchmark datasets/tools for research and thin Nerelan adapters/fixtures around current TaskStore, evidence, verifier and Pack contracts.

---

## 16. Mapping to existing owners

### #137 Mother Platform

Owns real-provider dogfood sequencing and product-level completion claims.

### #252 Autonomous Improvement Loop

Owns hypotheses, bounded experiments, evidence-based selection and experience reuse. This document strengthens comparison/repetition/uncertainty rules.

### #253 Pack Productization

Owns domain-specific eval suites, verifier contracts and performance history.

### #260 Productization

Owns user-journey validation, Agent Runs/readback and multimodal product behavior.

### #361 Mature Component Reuse Gate

Owns the requirement to reuse mature benchmark/testing/statistics/browser mechanisms rather than build commodity substitutes.

---

## 17. Suggested future adoption sequence

Only when existing owners authorize implementation:

```text
EVAL-R0  define simple baselines for current real dogfood
EVAL-R1  record repeated-run reliability + typed failure categories
EVAL-R2  uncertainty-aware candidate comparison under #252
EVAL-R3  expand dogfood to long-horizon/multimodal/multi-ecosystem task classes
EVAL-R4  use Pack/task-family performance history for objective routing
EVAL-R5  continuous improvement promotion only after evidence beats simpler baseline
```

---

## 18. Terminal research position

```text
ONE_SUCCESSFUL_RUN_DOES_NOT_PROVE_RELIABILITY
MORE_AGENT_COMPLEXITY_DOES_NOT_IMPLY_MORE_CAPABILITY
EVERY_COMPLEXITY_INCREASE_NEEDS_A_SIMPLE_BASELINE
EVAL_DIFFERENCES_REQUIRE_UNCERTAINTY_AWARE_INTERPRETATION
PUBLIC_BENCHMARKS_ARE_INPUTS_NOT_PRODUCT_AUTHORITY
REAL_DOGFOOD_MUST_EXPAND_ACROSS_HORIZON_MODALITY_SCALE_LANGUAGE_RECOVERY_SECURITY_AND_UX
EXPERIENCE_REUSE_MUST_BE_MEASURED_FOR_BENEFIT_AND_HARM
AUTONOMOUS_IMPROVEMENT_MUST_BE_ABLE_TO_REJECT_ALL_CANDIDATES
IMPLEMENTATION_REMAINS_WITH_EXISTING_OWNER_ISSUES
```
