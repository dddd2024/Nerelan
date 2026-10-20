# Project-level coordination: Claude Projects × OpenAI dot benchmark input (#1286)

> Scope: research and architecture input for issue #1286. Documentation only.
> Baseline main: `5324ec7` (2026-10-20). Risk tier R1.
> This document distinguishes **landed on main**, **planned under an existing owner issue**, and **missing**.
> It grants no execution authority and does not replace any owner issue listed below.

## 1. Status of #1286 acceptance items after this document

| Acceptance item | Status here |
|---|---|
| Mapping table: implemented vs planned vs missing, with code paths and non-claims | **Delivered** in §3 |
| Coordinator / Thread / Project Knowledge contract that reuses existing owners | **Delivered** in §4. The project facade (§4.1) is implemented read-only in `reverse_agent/platform_v1/project_overview.py`; the thread-envelope additions, write-scope checks and tier C store are not |
| One provider-free end-to-end fixture (concurrency, provenance isolation, memory precedence, evidence, restart) | **Partially implemented** in `tests/platform_v1/test_project_overview.py`: concurrency, dependency ordering, restart without duplicate dispatch, window expiry and zero model calls. Worktree/provenance isolation and memory precedence are **not** covered (§5.2) |
| Multi-run benchmark A / B / (C) with quality and real spend | **Protocol specified** in §5; **not run**. No numbers in this document are measurements of Nerelan |
| Decision memo: adopt / defer / reject per lesson | **Provisional** memo in §6. Every "adopt" is conditional on the §5 benchmark; nothing is promoted on this document alone |
| Link deltas to #260 / #296 / #379 / #1191 and scoped issues | **Delivered** in §7 as proposed deltas; no new issues were opened |

The issue therefore stays open after this change lands: the remaining fixture steps and the benchmark remain.

## 2. External sources and what was actually verified

| Source | Verified in this session? | What it states (paraphrased) |
|---|---|---|
| Claude, "Projects redesigned" (2026-09-17), https://claude.com/blog/projects-redesigned | **Yes**, fetched 2026-10-20 | A coordinator directs threads; each thread is a Claude Code cloud session; several threads run at once; every thread adds to and draws from a shared memory; a library collects uploaded files and artifacts; each thread works on its own branch and repo copy, and overlap resolves as an ordinary PR merge conflict; parallel threads can reach usage limits faster; per-project usage is visible and model/effort is selectable for coordinator and threads; beta for select Pro/Max subscribers |
| OpenAI dot overview, https://help.openai.com/en/articles/20001530-getting-started-with-your-dot | **No**. `help.openai.com` did not resolve from the research container | Taken from the #1286 issue snapshot only: always-on user-oriented agent, ongoing goals, dedicated cloud computer, connected apps, ChatGPT memory, in-progress / scheduled / completed activity |
| OpenAI dot privacy/security FAQ, https://help.openai.com/en/articles/20001529-dots-privacy-security-and-safety-faqs | **No**, same reason | Taken from the issue snapshot only: scope controlled by user permissions |

Non-claims:

- Provider-internal memory architecture, error recovery, merge gating and success rates of either product are **unverified**. Nothing below assumes them.
- Launch ordering and feature parity between the two products are not inferred beyond the dates above.
- The Owner's screenshot (coordinator ≈156.1k tokens vs a second thread ≈0) is **one UI observation**, not evidence that coordinators dominate cost. Introductory credits and session meters are pricing observations, not an engineering dependency.

### 2.1 First-hand observations from dogfooding Claude Projects on this repository

This repository is itself being developed inside a Claude Project (2026-10-20). These are single-project observations, not measurements, and they are recorded because they bear directly on §4:

- Each thread works on its own `claude/project-thread-*` branch and opens Draft PRs; the repository's own `landing-state-gate` and `Nerelan-Review` verdict remain the landing authority. The product's coordinator does **not** replace the repository gate.
- Shared project memory is a set of small files written by any thread. Entries are advisory: they record Owner preferences (language, autonomy limits, notification rules) and must be re-verified against the repository before acting. This matches tier C in §4.3, not tier A.
- A decision that only lived inside a thread was missed by the Owner while away; the fix was a rule that threads also raise one line to the coordinator. Lesson: a project facade needs one place that lists **blocked-on-Owner** items (§4.1).
- Threads can be idle without being finished; the Owner asked whether idle threads were "stopped or waiting". Lesson: thread state must distinguish *waiting on X* from *done* from *dead* (§4.1, #280/#281).

## 3. Capability mapping: implemented vs planned vs missing

Paths are relative to the repository root on `5324ec7`. "Implemented" means code is on main with tests under `tests/platform_v1`; it does not mean product-accepted.

| Lesson / capability | Claude Projects | dot (unverified) | Nerelan status | Where | Owner issue | Non-claim |
|---|---|---|---|---|---|---|
| Durable execution truth | Not documented | Not documented | **Implemented** | `reverse_agent/platform_v1/run_store.py` (`tasks`, `task_events`, `durable_runs`, checkpoints) | — | One SQLite TaskStore; no second store may be introduced |
| Goal → Spec → Plan → Tasks | Coordinator plans in chat | Ongoing goals | **Implemented** | `goal_service.py`, `agent_planner.py` (read-only planner; Owner approves plan) | #260 | Planner output is a proposal; it never launches work |
| Project-level facade (one view of goals, active/waiting threads, budget, open decisions, evidence) | Coordinator chat + thread list | Activity view | **Partial**: Goals, Runs read model, Roadmap phases exist; no single "project" aggregate with open decisions / blocked-on-Owner | `run_read_model.py`, `roadmap_service.py`, `control_store.py` (`platform_goals`, `platform_roadmap_phases`), `frontend/src` | #260, #280/#281 | Roadmap is display metadata, not authority |
| Coordinator role | Long-lived coordinator session | Always-on agent | **Partial**: crash-resumable coordinator exists for an Owner-activated window, as a role over durable rows (claims, receipts), not a chat | `unattended_coordinator.py`, `autonomy.py`, `control_store.py` (`platform_coordinator_claims`, `platform_operation_receipts`) | #1191, #1206 | No unbounded long-lived chat; coordinator holds no state of its own |
| Worker isolation (branch / worktree per task) | Branch + repo copy per thread | Dedicated cloud computer | **Implemented** | `repository_preparation.py` (`prepare_linked_worktree`, `planner_worktree`), `repository_workspace.py`, `workspace_drift.py` | #1279 / #1251 | Merge-conflict resolution between concurrent tasks is **not** automated |
| Bounded handoff between dependent tasks | Not documented (shared memory) | Not documented | **Implemented** for Git artifacts: approved input identity, frozen handoff contract | `artifact_handoff.py` (`freeze_handoff_contract`, `bind_consumer_input`, `check_input_snapshot`) | #296 / #642, #1279 | Ordering dependency never grants access to another task's worktree |
| Bounded context projection | Shared memory + thread context | ChatGPT memory | **Implemented** (task-scoped, rebuilt from durable rows, authority always `NONE`) | `context_builder.py`, `context_optimization.py`, `context_recovery.py`; `docs/benchmarks/context-builder-20261013` | #296 / #642 | No stored chat summary is consulted |
| Shared project knowledge (advisory memory with provenance / freshness / contradiction guards) | Shared memory across threads | Learns preferences | **Missing** in the product: no knowledge store in `reverse_agent/platform_v1` | — | #379 / #103 | Repository docs and AGENTS.md act as tier A today; there is no tier C store |
| File / artifact library | Project library | Connected apps | **Partial**: task evidence and changed files per task; publications | `run_store.py` (`task_evidence`, `task_changed_files`), `publication_controller.py`, `evidence_adapter.py` | #260 | No project-scoped library view |
| Concurrency + resource admission | Several threads at once; usage limits hit faster | — | **Implemented** window-bounded concurrency: the coordinator admits up to `max_concurrent_tasks` (1–8 per window) and fans distinct claimed tasks out as a parallel batch; plus budget reservations, usage charges and a quota pre-dispatch check. Each task's own team (planner/worker/reviewer) runs sequentially in `durable_execution.py` | `unattended_coordinator.py` (`_execute_claimed_batch`; `tests/platform_v1/test_unattended_coordinator.py::test_coordinator_uses_langgraph_send_for_real_parallel_batch`), `autonomy.py`, `quota_guard.py`, `usage_ledger.py`, `control_store.py` (`platform_budget_reservations`, `platform_usage_charges`) | #1248 / #1281 / #1170 | Disjoint write scopes between concurrent tasks are not checked; the benefit of concurrency has not been measured |
| Model / effort per role, and WHY a model was chosen | Selectable for coordinator and threads | — | **Implemented** routing with evidence-tiered priors | `model_router.py`, `model_profiles.py`, `routing_capabilities.py`, `routing_inputs.py` | #1248 | Priors are bootstrap estimates, not measured claims |
| Usage visibility by role / model | Per-project usage | — | **Partial**: one token ledger normalized across executors; no per-role project rollup in UI | `usage_ledger.py`, `reverse_agent/model_access/*` | #1281, #280 | Provider-reported cost is not a subscription invoice |
| Independent review before landing | PRs reviewed like any PR | User reviews results | **Implemented** for this repository; product-side reviewer stage exists in durable execution | `reverse_agent/landing_review.py`, `.github/workflows`, `durable_execution.py` (`POST_REVIEWER`) | #1140 / #1266 | Author self-review never counts |
| Controlled publication | Thread opens PR | — | **Implemented** (Draft PR only; never ready/merge/force) | `publication_controller.py` | #1266 | — |
| Restart / quota-window continuation | Cloud continuation | Always-on | **Implemented** core: leases, heartbeats, checkpoints, reconcile, startup preflight | `run_store.py` (lease/heartbeat columns), `durable_execution.py`, `unattended_coordinator.py` (`reconcile`), `startup_preflight.py` | #1191 / #1277 / #1206 | Expired window never auto-extends; fresh Owner authority required |
| Truthful runtime status (no false RUNNING; waiting vs done vs dead) | Thread status chips | in-progress / scheduled / completed | **Partial** | `run_read_model.py` (`backend_status_to_frontend_state`), `system_doctor.py` | #280 / #281 | — |
| Scheduled / proactive work | Routines (outside scope here) | Scheduled activity | **Partial**: remote job broker and research campaigns, Owner-configured | `remote_jobs.py`, `research_loop.py` | #1191 | No cross-project personal assistant |
| Human inbox → goals | Chat in project | Chat | **Implemented** | `inbox_service.py` | #260 | Captured ideas become Goals only through GoalService |
| Cost/quality benchmark harness | — | — | **Implemented** (provider-free arm comparison over frozen contracts) | `cost_quality_benchmark.py` | #1281 | Records are evidence, never authority |
| Provider-free end-to-end acceptance | — | — | **Implemented** for a single task | `provider_free_task_plane_acceptance.py` | — | Does not cover concurrent tasks, knowledge precedence or cross-task provenance |

## 4. Proposed Coordinator / Thread / Project Knowledge contract

This is a contract over existing records. It introduces **no** new orchestrator, database, thread store, model gateway or assistant product.

### 4.1 Coordinator = role over durable records

- **State authority:** TaskStore (`run_store.py`) for tasks and runs, `control_store.py` for goals, windows, claims, reservations, receipts and publications. The coordinator has no private state; a restarted coordinator reconstructs everything from these tables (`UnattendedCoordinator.reconcile`).
- **May:** create tasks only inside an approved Goal plan and an active autonomous window; reserve budget; dispatch; record receipts; request review; request Draft-PR publication.
- **May not:** widen scope, extend an expired window, mark ready or merge, or treat a worker's text as completion. Acceptance comes from `acceptance.py` and evidence, not claims.
- **Project facade (implemented read-only, `project_overview.py`; UI/API wiring is #260):** a read model aggregating per Goal: plan, tasks with state in {`queued`, `waiting_dependencies`, `waiting_window`, `running`, `validating`, `ready_for_review`, `blocked`, `failed`, `stale`, `unknown`}, window effective status and budget, escalation count, usage and publication links per task, and Owner actions in one list (`plan_goal`, `approve_plan`, `launch_goal`, `renew_window`, `review_result`, `resolve_blocked_task`, `resume_task`, `inspect_stale_task`) (§2.1 lesson). Derived only from existing rows through `RunReadModel`; authority is always `NONE`. Review verdicts are not yet included because the product has no verdict row to read.

### 4.2 Thread = one task execution with an explicit envelope

Each worker execution carries, already or as a small extension of existing task fields:

| Field | Existing source |
|---|---|
| task id, goal id | `tasks`, `platform_goal_task_links` |
| role and model, with routing reason | `model_router.select_model` output; persist the reason with the run observation |
| worktree and branch | `repository_preparation.prepare_linked_worktree`, `repository_workspace` |
| accepted input artifacts | `artifact_handoff` frozen handoff contract |
| read / write scope (allowlisted paths) | Goal plan task scope; `publication_controller` allowlist |
| dependencies | Goal plan |
| quota reservation | `platform_budget_reservations`, `quota_guard.check` |
| checkpoint | `durable_runs`, `durable_checkpoint_history` |

**Handoff rule:** a downstream task receives only the frozen, digest-bound handoff (`artifact_handoff`) plus a context packet from `context_builder` (authority `NONE`). No conversation replay.

**Recovery rule:** on restart, quota exhaustion or worker loss, the lease expires, `reconcile` re-derives state, accepted checkpoints and approved artifacts are kept, and the task resumes only if its Goal's window is still active. An expired window parks the task as `blocked_on_owner:renew_window`; it never auto-extends.

**Overlap rule:** two tasks of one Goal must declare disjoint write scopes, or be ordered by a dependency. Overlap that still occurs surfaces as a Git merge conflict at publication and is handled like any PR (the Claude Projects model), not silently auto-resolved.

### 4.3 Project knowledge tiers and precedence

| Tier | Content | Authority | Present today |
|---|---|---|---|
| A | Repository and Owner-controlled policy and accepted state: `AGENTS.md`, `docs/agents/**`, approved Goal plans, autonomy windows | Controls execution | Yes |
| B | Verified receipts and evidence: task evidence, review verdicts, CI results, operation receipts | Controls execution after policy resolution | Yes |
| C | Advisory project memory: preferences, decisions noted in passing, lessons, each with source, author, timestamp and expiry/review date | **Never** controls execution; may inform planning text | **No** (#379 / #103) |
| D | Ephemeral thread context | Task-local; discarded or summarized into B only via evidence | Yes (context packets) |

Precedence: A > B > C > D. A C entry that contradicts A or B is flagged stale and shown, not applied. A C entry older than its review date is shown with its age. Only A and B may change what is executed.

## 5. Evaluation protocol

### 5.1 Arms

- **A — single agent, sequential.** One capable executor, same permissions, same budget cap, tasks run one after another in one worktree.
- **B — current Nerelan.** `agent_planner` + `goal_service` + `unattended_coordinator` + `durable_execution` team with reviewer, using existing routing and the existing window concurrency (`max_concurrent_tasks` unchanged from the scenario's window policy). B keeps concurrency; it is not a serialized configuration.
- **C — coordinator facade.** Same as B, with the same `max_concurrent_tasks`, plus only the §4 additions: the project facade, disjoint write-scope checks and a tier-C knowledge store. Concurrency is therefore not a C variable. **Only after §4 is implemented** under its own work item; until then C is `NOT_TESTED`.
- **External black box (optional).** Claude Projects / dot on the same suite only where account access, cost and terms allow; otherwise `NOT_TESTED`, never inferred.

Each arm uses one `BenchmarkContract` (`cost_quality_benchmark.py`): same `base_commit`, requirements, acceptance, tools and resource-budget digests. Results are compared with `compare_arms`.

### 5.2 Provider-free fixture

Implemented in `tests/platform_v1/test_project_overview.py` with the real `UnattendedCoordinator`, a file-backed TaskStore and an injected deterministic task executor (the model router fails the test if reached): steps 1, 2 (concurrency and dependency ordering only), 4 (restart rebuilds the same overview and nothing is dispatched twice), 5 (expired window parks the Goal on `renew_window` without the overview writing) and 6. Not yet covered: separate worktrees and handoff provenance digests in step 2, because the injected executor bypasses worktree preparation, and step 3, which needs the #379 store.

Original specification:

Extend the pattern of `provider_free_task_plane_acceptance.py` with the deterministic fixture executor, in a new test under `tests/platform_v1`:

1. One Goal with three tasks: two with disjoint write scopes, one dependent on the first via a frozen handoff.
2. Run the two independent tasks concurrently; assert separate worktrees, no cross-task reads, distinct evidence rows, provenance digests matching the handoff contract.
3. Seed a tier-C note that contradicts the approved plan; assert the plan wins and the note is flagged stale. (Requires the #379 store; until then assert that no C input reaches the executor.)
4. Kill the host after the first checkpoint; restart; assert `reconcile` resumes from the checkpoint without duplicate dispatch and with the same evidence.
5. Expire the window mid-run; assert the task parks as blocked on the Owner and does not auto-extend.
6. Assert zero model calls.

### 5.3 Scenarios (fixture first, then authorized dogfood)

1. Two independent code tasks plus one overlapping-file conflict.
2. Multi-day task with context reset, quota exhaustion, supervisor loss and host restart.
3. Mid-task plan change with contradictory or stale memory.
4. REJECT → fix → re-review, CI failure, and a missing R2 Owner decision; no unauthorized landing.
5. Sparse project with one small task: coordination overhead must not exceed its benefit.

### 5.4 Metrics

Report per arm and per run, with at least three repeated runs per scenario and their variance:

- task success with exact verification (commit, checks, verdict); accepted work per PR
- independent-review findings; rework count
- wall-clock to first useful result
- input / cached / output tokens (`usage_ledger` five counters), estimated and observed cost / quota
- coordinator overhead % = coordinator-role tokens ÷ total tokens
- duplicate dispatch, blocked and idle time, cross-task conflicts
- restart fidelity (state equal before and after restart), Owner interventions

Each value is labelled `measured`, `estimated` or `external-claim`. Author and reviewer stay distinct.

## 6. Provisional decision memo

All rows are **provisional**. "Adopt" means "adopt if §5 shows equal or better quality-adjusted cost or long-running completion"; a row that fails that test becomes "reject".

| # | Lesson | Decision | Reason |
|---|---|---|---|
| 1 | Coordinator as a role over durable records, not a long-lived chat | **Adopt** (already the direction) | Matches `unattended_coordinator`; avoids an unbounded context and a second state store |
| 2 | One project facade with blocked-on-Owner list and truthful waiting/done/dead states | **Adopt**, low cost | Read model only; directly addresses the two §2.1 observations |
| 3 | Explicit thread envelope (§4.2) with persisted routing reason | **Adopt** | Mostly existing fields; adds explainability of model choice |
| 4 | Concurrent tasks within one Goal (already implemented, window-bounded) | **Keep; tune defaults only after measurement** | Run B at `max_concurrent_tasks` 1 vs >1 on scenarios 1 and 5 before raising defaults; Claude documents that parallelism burns quota faster |
| 5 | Shared advisory project memory (tier C) | **Defer** to #379 / #103, with precedence rules from §4.3 | Useful for preferences, but must never steer execution; needs provenance and staleness first |
| 6 | Automatic merge-conflict resolution between threads | **Reject** for now | Claude Projects itself treats overlap as an ordinary PR conflict; declare disjoint scopes instead |
| 7 | Always-on, cross-project personal assistant (dot-style) | **Reject** for current scope; optional later | Out of product boundary in AGENTS.md; different scope from project coordination |
| 8 | Per-role / per-model usage rollup in the UI | **Adopt** | Ledger exists; the gap is presentation (#280, #1281) |

## 7. Proposed deltas for owner issues

No new issues were opened. Each delta belongs to the existing owner:

- **#260:** project facade read model (§4.1) with `blocked_on_owner` list and per-Goal budget/verdict/PR summary.
- **#280 / #281:** state vocabulary distinguishing `waiting:<reason>`, `blocked_on_owner:<action>`, `stale` (lease expired) and `done`.
- **#296 / #642:** confirm the handoff rule in §4.2 (frozen handoff + authority-free context packet) as the only cross-task context path.
- **#379 / #103:** tier C store with source, author, timestamp, review date, contradiction flag; precedence A > B > C > D.
- **#1191 / #1206:** recovery rule in §4.2, including `blocked_on_owner:renew_window` on window expiry; fixture steps 4–5.
- **#1279 / #1251:** disjoint write-scope declaration per task, checked at plan validation.
- **#1248 / #1281:** persist routing reason with the run; per-role usage rollup; coordinator overhead metric.
- **#1286 (this issue):** remaining work is the uncovered §5.2 fixture steps and the §5 benchmark runs.
