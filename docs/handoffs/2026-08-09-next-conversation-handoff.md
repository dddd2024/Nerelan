# Next Conversation Handoff — 2026-08-09 15:33 +08:00

> Purpose: canonical handoff for the next Owner/audit conversation. Re-fetch all remote heads before mutation. This document is planning/audit context and grants no new local code authority.

## 1. Owner operating model

The user has delegated Owner-level repository governance to the assistant.

In the next conversation:

- perform GitHub-side audit/planning/PR/Issue work directly when tools permit;
- delegate only machine-local execution that genuinely requires the user's local environment to the local Agent;
- do not ask the user to perform GitHub operations the assistant can perform;
- before accepting any local Agent report, independently verify exact remote head, diff, PR/check state and scope;
- prefer mature components and thin adapters over greenfield reimplementation;
- do not weaken or bypass failed gates with PR-specific exceptions.

Primary repository: `dddd2024/reverse-agent`.

Historical local checkout `F:\reverse-agent` may contain preserved evidence from old #146/v24 work. Do not instruct a local Agent to reset/clean/stash/rebase/modify that checkout. Use isolated task directories/worktrees.

## 2. Current immutable/remote facts at handoff

### Main

`main` remains expected at:

`dd4cb074ab5b9baacf300706878b29bd745f12c3`

Re-fetch before relying on it.

### Modernization umbrella

Issue #148 is the active Owner-selected strategy:

`STRANGLER_MIGRATION + MATURE_COMPONENT_FIRST`

Rule:

```text
REUSE mature component
-> ADAPT through thin reverse-agent boundary
-> RETIRE superseded custom path
```

Do not add another permanent compatibility layer.

### Modernization planning branch

Planning branch before this handoff-file commit was:

`owner/repository-modernization-v2-planning@baa5e60c33489073acae656d3b3c87579e720224`

The branch head necessarily advances when this handoff file is committed. Re-fetch the branch exact head before the next Owner write.

### #149 / PR #150

#149 is completed. PR #150 was merged into the isolated planning branch, not `main`.

Merge commit:

`d7cf40b13ab0997e747597976f3c0929ab80c8d6`

#149 established the optional LangGraph execution seam and fixed the orchestration boundary:

- LangGraph owns workflow/orchestration mechanics;
- reverse-agent owns Task / Workspace / Policy / Evidence-Artifact semantics;
- TaskStore remains durable product truth;
- Multi-Agent orchestration is NOT an executor kind.

## 3. IMMEDIATE NEXT TASK: Owner-audit #151 remote implementation

Issue #151 remains open:

`Modernization V2 Task 2: LangGraph parallel worker team + verifier adapter`

Original canonical implementation head before local mutation:

`2a1da2a672dd9e123d03a30fdacdf55fef3c3cc4`

Important new handoff fact:

The remote task branch has already advanced by **2 commits** after that planning head.

Current observed remote head:

`owner/issue151-langgraph-worker-team-v1@acf022c8865973cef59a4da742db10ec023d01d8`

Head commit message:

`feat: add LangGraph parallel worker team adapter`

No local Final Report has been received in the current conversation for these commits.

No PR for the #151 branch was found at handoff time, and no commit statuses were attached to `acf022c...`.

Therefore the next conversation MUST NOT assume #151 is accepted.

### Observed diff shape from original task head to current #151 branch

11 files changed:

- `docs/architecture/LANGGRAPH_ORCHESTRATION_BOUNDARY.md`
- `docs/architecture/LANGGRAPH_TEAM_RUNTIME.md` (new)
- `reverse_agent/architecture/contracts.py`
- `reverse_agent/platform_v1/run_store.py`
- `reverse_agent/platform_v1/task_execution.py` (new)
- `reverse_agent/platform_v1/task_service.py`
- `reverse_agent/workflows/nodes/acceptance_gate.py`
- `reverse_agent/workflows/team_graph.py` (new)
- `tests/platform_v1/test_task_contracts.py`
- `tests/platform_v1/test_task_execution.py` (new)
- `tests/test_team_graph.py` (new)

No observed `frontend/**`, `.github/**`, `project_state/**` or `pyproject.toml` mutation in that compare.

The large `run_store.py` diff must be inspected carefully rather than assumed to be only lock indentation.

### Claims visible in the current #151 head that require independent Owner verification

The branch/documentation claims:

- native LangGraph `Send` fan-out;
- thin parent adapter between `DevelopmentWorkflowState` and team-specific state;
- one shared `TaskExecutionService` used by HTTP and worker execution;
- TaskStore concurrency probe exposed `sqlite3.InterfaceError`, leading to one `threading.RLock` per TaskStore;
- probe passes 20/20 after lock;
- structured `WorkerAssignment`, `WorkerExecutionResult`, `TeamExecutionResult`;
- verifier rejection propagates to parent acceptance;
- TaskStore remains the only durable truth;
- legacy `reverse_agent/orchestrator_*` remains untouched / `RETIRE_LATER`;
- no `executor_kind="multi_agent"`;
- no real model/provider call required for acceptance.

These are **claims from the branch**, not yet Owner-accepted evidence.

### #151 Owner audit checklist

First action in next conversation:

1. Re-fetch #151 branch exact head. If it is no longer `acf022c...`, audit the newer exact head instead and record drift.
2. Compare exact branch to `2a1da2...` and to its intended planning baseline.
3. Inspect both pushed commits and all 11 changed files, with special attention to:
   - `run_store.py`: lock coverage, transaction semantics, nested public calls, accidental behavior changes;
   - `task_execution.py`: lifecycle parity with old HTTP path, OpenCode kwargs, evidence ID derivation, validation-command semantics, error classification;
   - `task_service.py`: ensure it is genuinely thin and did not leave a second execution path;
   - `team_graph.py`: actual LangGraph `Send` fan-out/join, no custom scheduler/thread pool, deterministic result ordering, duplicate/empty assignment behavior;
   - `contracts.py`: validation and deterministic serialization, no duplicate TaskStore truth;
   - `acceptance_gate.py`: no-team backward compatibility and verifier rejection behavior;
   - tests: barrier actually proves parallelism, 20x claims are meaningful, real TaskStore + ExecutorRouter deterministic-fixture integration is tested.
4. Verify `pyproject.toml` unchanged and LangGraph remains pinned `1.0.5`.
5. Verify no forbidden path changes and no provider/credential logic.
6. If static audit is acceptable, create an Owner-controlled Draft PR from `owner/issue151-langgraph-worker-team-v1` to `owner/repository-modernization-v2-planning` using exact expected head, then observe exact-head CI.
7. Treat current legacy `State Gate` failures separately if they again arise solely from stale #134 authority; do not add a #151 exception.
8. Only after code + exact-head tests/CI are accepted may #151 be merged into planning and closed.
9. If the user supplies the local Final Report in the next conversation, compare every reported SHA/test count with the remote facts above; do not accept the report by assertion alone.

Terminal Owner decision should be one of:

`ISSUE151_ACCEPTED_AND_MERGED_TO_MODERNIZATION_PLANNING`

or

`ISSUE151_REWORK_REQUIRED`

or

`ISSUE151_BLOCKED_WITH_EVIDENCE`

## 4. #146 isolation warning

Draft PR #146 remains open, Draft, unmerged and mergeable at handoff.

Observed current head:

`owner/issue136-agent-canvas-reuse-spike-v2@9e6d98399c1a9ddac45d4b0d898726b23abcc3c2`

Its PR body currently contains a historical `v26` machine-local reconciliation authority, even though Modernization #148 previously froze #146 and explicitly forbade further v25/v26-style landing patching.

A new Owner override comment was posted during handoff:

- treat PR-body v26 authority as historical only;
- do not initiate reset/cleanup/reconciliation from it;
- no Ready/merge/rebase/force-push/new landing patching;
- preserve exact history/evidence until #148 selects the modernization-compatible landing/transplant disposition.

Do not make #146 the current workstream while #151 audit is incomplete.

Accepted #146 product evidence that should be preserved includes Agent Canvas v1.6.1 source reuse and the previously demonstrated real OpenCode task/readback path. #145 remains presentation debt.

## 5. Fixed architecture after #151

### Connection / Executor / Binding

Canonical document:

`docs/architecture/CONNECTION_EXECUTOR_BINDING_ARCHITECTURE.md`

Fixed model:

```text
Connection
= provider/service access + authentication

Executor
= OpenCode / Codex / OpenHands / another concrete Agent runtime

Binding
= Executor + Connection + Model
```

Authentication methods belong to Connection:

- `api_key` / env-backed secret;
- account login / OAuth when supported by mature upstream tooling;
- external CLI session;
- none for local endpoints.

User-level rule:

> Configure/authenticate once. Supported executor adapters reuse that Connection without asking for duplicate credential entry.

Do NOT achieve this by copying raw credentials into TaskStore, frontend task state, evidence, logs or unrelated executor credential stores.

Current truth: API configuration in reverse-agent Model Control is NOT automatically inherited by OpenCode today.

GitHub is a separate repository-domain connection, not a model-provider Connection.

### Product Setup & Connections

Canonical plan:

`docs/roadmap/PRODUCT_SETUP_CONNECTIONS_PLAN.md`

This is the next product phase AFTER #151 acceptance.

Scope:

- Connection / Executor / Binding split;
- API/account/external-session adapter behavior;
- GitHub repository connection via mature GitHub App/OAuth/`gh`/existing credential mechanisms;
- coherent connection probing;
- thin Windows double-click launcher reusing `dev-up.ps1` / `dev-down.ps1` lifecycle;
- current Settings live-probe UX mismatch cleanup.

Do not build a new OAuth system or process manager from scratch.

Current startup truth:

`dev-up.ps1` is a **one-command** development stack, not a true one-click/double-click product launcher.

## 6. Freshness / anti-staleness architecture

Issue #152 is planned only; it grants no implementation authority yet.

Canonical document:

`docs/architecture/FRESHNESS_AND_DRIFT_GOVERNANCE.md`

Selected mature stack:

```text
Renovate
  -> primary dependency/upstream drift watcher
  -> Dependency Dashboard
  -> normal dependency update PRs
  -> custom managers for non-standard pins

GitHub Actions
  -> semantic compatibility/freshness checks
  -> PR impact revalidation
  -> scheduled review-age checks

CODEOWNERS + GitHub Rulesets
  -> ownership/review + required Freshness status

OPA Bundles later
  -> policy distribution/version activation after Rego adoption
```

Dependabot is fallback only if Renovate is unavailable. Do not let Renovate and Dependabot manage the same ecosystems concurrently.

Reverse-agent-specific implementation should stay thin:

- `governance/freshness-registry.yaml`;
- impact/dependency relationships;
- compatibility fixtures/tests;
- freshness state calculation;
- sanitized reports.

States:

`FRESH / REVIEW_REQUIRED / STALE / BLOCKED`

Core invariant:

> A critical Skill/policy/adapter is not current merely because its file exists. Its declared dependencies, compatibility evidence and verification age must still be valid.

## 7. Fixed near-term order

```text
#149 LangGraph seam                         DONE
        ↓
#151 parallel team + verifier              CURRENT — AUDIT FIRST
        ↓
Product Setup & Connections
        ↓
#152 Freshness Automation Foundation
        ↓
real OpenCode Multi-Agent dogfood
+ Pack / Skill growth
        ↓
continue state/governance/CI/frontend debt burn-down
```

Do not jump directly from an unreviewed #151 branch to real OpenCode Multi-Agent dogfood.

## 8. Broader debts retained under #148

Still relevant after the near-term product track:

- P0 verification/fix candidate: tuple-container recursive evidence redaction in `opencode_executor.py`;
- stale Decision/authority lifecycle (`active` historical state problem);
- #147 baseline dirty vs current-round delta;
- #142 one typed/preactivation Decision validation path;
- #143 outer execution-surface compatibility;
- #144 semantic artifact identity;
- #145 frontend real-task validation truth;
- CI State Gate / Decision Preflight historical duplication and PR-specific logic;
- eventual GitHub Rulesets-native repository protection;
- stale backlog/docs retirement;
- #135 trusted Draft PR publication controller still needed before unattended publication.

Do not solve these by adding more old-protocol compatibility branches.

## 9. Source-of-truth priority

When facts conflict, use:

1. exact current GitHub branch/PR head and diff;
2. active #148 and bounded task Issue;
3. canonical planning-branch architecture/roadmap docs;
4. accepted exact-head test/CI evidence;
5. older Issue/PR body/history only as historical evidence;
6. conversation memory only as advisory context.

This is especially important for #146 because its PR body contains stale-looking historical authority that conflicts with the Owner freeze.

## 10. Suggested opening instruction for next conversation

The next user can paste:

> 继续 reverse-agent Owner 审计。先读取 GitHub 上的 `docs/handoffs/2026-08-09-next-conversation-handoff.md`、#148、#151、#152，并重新核对 main / planning / #151 / #146 exact heads。不要直接相信上一轮的本地 Agent 报告。第一优先级是独立审计 #151 当前远端实现；完成你可以直接完成的 GitHub Owner 工作，只有必须依赖本机运行环境的工作才交给本地 Agent。发现纰漏先修计划/治理边界，再给新的本地执行提示词。不要继续 #146 的 v25/v26 旧治理路径。
