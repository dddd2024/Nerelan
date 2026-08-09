# Current Architecture Baseline — 2026-08-09

> Scope: factual baseline for Repository Modernization V2 (#148).
> Baseline main: `dd4cb074ab5b9baacf300706878b29bd745f12c3`.
> This document distinguishes **landed on main**, **accepted on an unmerged branch**, and **planned only**. Those states must not be conflated.

## 1. Current product identity

reverse-agent is currently best described as a **local-first unattended software-engineering execution substrate** with a repository-owned policy/evidence boundary.

The current product is no longer accurately described as only a minimal integration baseline or a reverse-engineering task runner.

The architectural intent is:

```text
User / Owner
  -> task/control surface
  -> Task API / TaskService
  -> durable TaskStore
  -> executor routing
  -> isolated workspace execution
  -> independent validation + evidence
  -> review UI
  -> trusted publication boundary (planned, not yet landed)
```

The repository should reuse mature external runtimes and UI components where they are stronger than repository-owned alternatives. Repository-owned differentiation belongs primarily in policy, evidence, verification, recovery, task truth, publication boundaries and higher-level capability orchestration.

## 2. Landed on `main@dd4cb074...`

### 2.1 Task/runtime plane

Current main contains the Platform V1 task foundation:

- loopback Task API;
- TaskService lifecycle;
- SQLite-backed `TaskStore` in `reverse_agent/platform_v1/run_store.py`;
- persistent task records, events, changed-file and evidence readback;
- idempotency primitives;
- `ExecutorRouter`;
- deterministic fixture executor;
- real `OpenCodeExecutor`;
- linked-worktree isolation for real OpenCode execution;
- deterministic local validation independent of model self-report;
- model-profile reference plumbing;
- permission/policy reference fields;
- recursive evidence/secret redaction mechanisms;
- one-click local dev lifecycle from #133 / PR #134.

### 2.2 Frontend on main

Main contains a functional frontend task surface connected to the real Task API:

```text
create task
-> execute task
-> read persisted task state
-> activity/events
-> changed files
-> evidence
```

The frontend client supports `deterministic_fixture` and `opencode` executors.

However, main does **not** yet contain the final Agent Canvas v1.6.1 source-forked workbench from #136 / Draft PR #146.

### 2.3 Governance/control plane on main

Main currently contains multiple generations of repository governance:

- tracked `project_state/decision_packet.md`;
- generated gate artifacts under `project_state/gates/`;
- active mainline merge intent state;
- transition kernel / preflight implementation;
- legacy and Path-A/Path-B compatibility behavior;
- GitHub Actions workflows that still contain historical migration-specific paths.

These mechanisms are functional enough to have governed prior merges, but they are **not considered a clean final architecture**. Modernization V2 treats them as migration targets.

## 3. Accepted but not landed: #136 / Draft PR #146

Draft PR #146 is preserved evidence, not mainline truth.

Accepted branch facts include:

- selected reuse disposition: `AGENT_CANVAS_PINNED_SOURCE_FORK_SELECTED`;
- pinned upstream: `OpenHands/agent-canvas` v1.6.1, upstream commit `43f091baf135142ed6c146f888f44a957141193f`;
- reverse-agent Task API / TaskStore / executor / evidence plane preserved;
- Agent Canvas-derived sidebar/workbench/resize presentation source reused;
- real persisted OpenCode task reached:
  - backend `READY_FOR_REVIEW`;
  - frontend `READY_FOR_HUMAN`;
  - executor `opencode`;
  - validation exit code `0`;
  - exactly one intended changed file;
- accepted 1440x900 real-task visual evidence exists;
- no merge/Ready transition has occurred.

Therefore the correct claim is:

> **The real frontend -> Task API -> OpenCode -> validation -> persisted readback path has been demonstrated on the #136 branch, but the corrected Agent Canvas presentation layer is not yet on main.**

## 4. Not yet operational: multi-Agent orchestration

The repository does **not** currently have a demonstrated production multi-Agent collaboration vertical slice.

What exists today:

- one task can be routed to one registered executor;
- executor abstraction is pluggable;
- #103 defines cross-Agent memory/source-of-truth semantics;
- #126 defines a Codex native-multi-agent compatibility research round;
- #137 defines the future capability/multi-Agent architecture;
- #118 defines later worker delegation policy concepts.

What has **not** been proven as current product capability:

```text
manager Agent -> spawn worker Agents
structured parent -> child task handoff
parallel worker execution
worker -> parent artifact/result handoff
dependency graph / join semantics
bounded replan across multiple Agents
multi-Agent recovery/checkpointing
cross-provider child routing
policy-enforced worker delegation
```

Until one exact-head real vertical slice proves these properties, documentation must say **planned / research**, not `supported`.

## 5. Publication boundary status

Trusted GitHub Draft PR publication remains planned in #135.

The real OpenCode executor is intentionally not trusted with arbitrary GitHub publication credentials or merge authority.

Current accepted product boundary is therefore:

```text
Frontend
-> Task API
-> OpenCode linked worktree
-> deterministic validation
-> READY_FOR_REVIEW / READY_FOR_HUMAN
-> human/Owner handoff
```

The future #135 path is:

```text
explicit publish request
-> trusted server-owned publication controller
-> bounded commit/push
-> exactly one Draft PR
```

Automatic merge is not part of the current V1 closure.

## 6. Current architecture inconsistencies to remove

### 6.1 Stale module descriptions

`reverse_agent/platform_v1/__init__.py` still describes Platform V1 as not implementing a second executor/database/frontend even though TaskStore, OpenCode and frontend now exist.

`task_runtime.py` documentation still describes a fixture-only round even though `ExecutorRouter` registers both fixture and OpenCode execution.

These are documentation/code-comment drift, not the intended architecture.

### 6.2 Runtime naming drift

`run_store.py` now implements `TaskStore`; old backlog items still describe a RunStore/coordinator/execution-adapter architecture that was superseded by later implementation.

A rename may be appropriate, but only after import/API impact is audited.

### 6.3 Frontend semantic fallback debt

`frontend/src/lib/task-client.ts` still contains mock/provider-free era fallback behavior. #145 specifically tracks real validation state displaying `PENDING` despite authoritative persisted validation success when `frontend_task.testStatus` is absent.

### 6.4 State lifecycle ambiguity

`project_state/mainline_merge_intents/active.json` and `project_state/decision_packet.md` can remain bound to already-completed landing work. This makes `active` semantically ambiguous and causes later authority/gate behavior to depend on historical residue.

### 6.5 Legacy reverse-state artifacts

Historical reverse-engineering state files remain under `project_state/` with names that can look globally current. They must be reclassified or archived so that platform runtime truth and legacy challenge-state evidence cannot be confused.

### 6.6 Governance split-brain

Decision semantics currently emerge from several places simultaneously:

- Decision markdown structure;
- transition compiler/lint/preflight;
- legacy/Path-A/Path-B compatibility paths;
- workflow-specific logic;
- tests that encode required fields/semantics;
- mainline merge-intent handling.

Modernization must converge these into one explicit typed contract and one validation path.

## 7. Security verification priority

`OpenCodeExecutor` recursive evidence redaction requires a focused regression audit for tuple/container handling before broader refactoring. Modernization Phase 1 treats this as a P0 verification/fix candidate.

Do not infer exploitability without a reproducing test, but do not defer the audit behind cosmetic architecture cleanup.

## 8. Source-of-truth classification during modernization

Until Modernization V2 completes:

| Fact class | Source |
|---|---|
| Landed code capability | exact `main` commit |
| Branch-only accepted capability | exact PR/branch head + evidence |
| Active modernization direction | #148 + modernization planning branch |
| Historical implementation evidence | old PR/branch/Issue, explicitly historical |
| Runtime task truth | TaskStore/API persisted state |
| Private Agent/session memory | advisory only |
| Legacy reverse challenge state | domain-specific historical/compatibility evidence only |

No single old roadmap, Issue body or `project_state/current_*` file should be treated as global current architecture truth without checking this classification.

## 9. Modernization invariant

Every modernization phase must satisfy both conditions:

1. the preserved single-Agent real task vertical slice remains reproducible;
2. one superseded path is removed or archived when its replacement becomes authoritative.

Modernization must reduce architecture count, not add a fourth compatibility layer.