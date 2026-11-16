# D — Multi-agent orchestration and automated review loops

> **Superseded in part (2026-11-15):** the per-goal soft spend ceiling ("Raise to continue") and the replacement of `window.max_retries` below conflict with the Owner decision of 2026-11-15 (#1538): provider account quota is the only budget, and `max_retries` semantics stay. See the README corrections.

Study date 2026-11-15. Repository facts come from `gh api repos/<r>` and `/releases` on that date. The defects in scope are D10 (main), D4 (bounding unattended work after the Owner dropped window time, token and task caps) and D7 (task contract). D5 is covered only where it touches the review loop.

## 0. What Nerelan's loop does today (read from the checkout, head e0489d5a)

- `model_review.execute_review` freezes the exact producer head and tree in a detached worktree. It sends the reviewer the objective, spec, instruction, checks, functional evidence and exact diff (`MAX_DIFF_BYTES` = 1 MiB). It demands strict JSON in this shape: `ACCEPT` ⇒ `findings: []`, `REJECT` ⇒ at least one finding with `severity ∈ low|medium|high|critical` (`response_schema`).
- Independence is proved from **observed usage**, not from selection. `review_authors` collects the actual models of every author attempt, including replaced repair attempts. `require_independent` rejects any overlap with the reviewer's actual model. Codex and Claude Code executor reports must match the observations.
- The reviewer call is journaled as an RPC intent (`_claim_rpc_intent`). An unknown completion goes to BLOCKED and is never replayed. Workspace identity is checked before and after the call (`model_review_input_mutation`). Evidence is bound to the run, lease epoch, head, tree and digests.
- `goal_service._repair_rejected_reviews`: when a REJECT has verified evidence, it creates a repair attempt of the producer step. The repair gets a `ReviewRepair` evidence document with the findings. When the repair is READY_FOR_REVIEW, it creates a **fresh review attempt** (`model_review_refresh:`). The rounds are counted from `model_review_repair:` escalations, with `max_review_rounds=3`. The repair loop is also gated by the window's `max_retries` (`_routing_retries_spent(history) + 2 > window.max_retries`) and only runs while the window is ACTIVE. At either limit the loop sets `block_model_selection(... "model_review_round_limit" | "routing_retry_budget_exhausted")`.
- `landing_loop.LandingLoopController` publishes the reviewed head, posts `Nerelan-Review: <verdict> <head>`, and re-checks the verdict before merging (`invoke_verdict(state, claim)`).

Weak points against D10 and D4:
- (a) Any `low` finding forces REJECT, which means another full repair and review round.
- (b) The refreshed review is a new `task_resolver` choice, so the reviewer model can change between rounds. The reviewer gets the whole diff again, not "were the previous findings fixed?".
- (c) The round limit and the repair loop are coupled to the window (`window.max_retries`, `status='ACTIVE'`, `expires_at`). Dropping windows breaks them, or leaves them unbounded.
- (d) Exhausting the rounds leaves the goal BLOCKED with nothing for a human to act on.

---

## 1. OpenHands (resolver, GitHub integration, SDK critic and goal loop)

- **What it is:** OpenHands/OpenHands. MIT. Latest release v1.40.0 on 2026-11-12, last push 2026-11-15 (active). Mixed TypeScript/Python. The runtime is Docker-centric, so it fits Windows only through WSL/Docker Desktop. The resolver is a GitHub Action, so it runs in CI, not locally.
- **D10:**
  - The resolver is triggered by the `fix-me` label or an `@openhands-agent` comment. It can act on PR review comments and inline threads. In older versions it opens a draft PR on success and pushes a branch on failure. [docs](https://docs.openhands.dev/openhands/usage/run-openhands/github-action.md), [PyPI 0.3.0](https://pypi.org/project/openhands-resolver/0.3.0)
  - The SDK `run_goal(conversation, objective, judge_llm, max_iterations=10)` uses a **separate judge LLM** that returns `{score, complete, missing}`. The next iteration is prompted only with `missing`. On cap it returns `status="capped"`, and a bad judge JSON means "not complete". [convo-goal](https://docs.openhands.dev/sdk/guides/convo-goal)
  - The critic in Agent Canvas has a threshold of 0.6 and "Max Refinement Iterations" of 3. [critic](https://docs.openhands.dev/openhands/usage/agent-canvas/critic). [Iterative refinement](https://docs.openhands.dev/sdk/guides/iterative-refinement) uses `QUALITY_THRESHOLD`=90 and `MAX_ITERATIONS`=5, and passes feedback as a critique file.
  - The judge must be a separate `LLM` object. A different model family is not required.
- **D4:** The bound is an iteration count (`OPENHANDS_MAX_ITER`, `max_iterations`). In-loop enforcement of `max_budget_per_task` was not found. A benchmarks PR calls it future SDK work. [PR 741](https://github.com/OpenHands/benchmarks/pull/741)
- **D7:** The issue or PR text is the task itself, and repo microagents/AGENTS.md add rules. Not verified in depth.
- **Verdict:** **COPY-DESIGN.** Copy the `missing`-driven continuation and the capped status. Do not adopt the runtime: it needs Docker, duplicates Nerelan's executors, and its loop is author-adjacent rather than independence-proved. Cost: about 1 day inside `goal_service`.

## 2. PR-Agent (now The-PR-Agent/pr-agent)

- **What it is:** Moved out of qodo-ai to a community org. MIT, Python. Latest release v0.50.0 on 2026-11-07, last push 2026-11-15 (active). It runs as a CLI, a GitHub Action or a webhook, so it fits Windows and local use. Models are reached through LiteLLM (a `fallback_models` list).
- **D10:** It is a reviewer and suggester only, with no repair loop. The useful mechanisms are in [configuration.toml](https://raw.githubusercontent.com/The-PR-Agent/pr-agent/main/pr_agent/settings/configuration.toml):
  - `num_max_findings=6` caps reviewer noise.
  - `require_security_review=true` and `require_ticket_analysis_review=true` check the PR against the linked ticket's requirements.
  - `persistent_comment=true` edits one review comment instead of appending new ones.
  - `/improve` self-reflection scores each suggestion 0–10, and `suggestions_score_threshold` drops low-value ones. The docs advise a threshold no higher than 7–8. [self_reflection](https://qodo-merge-docs.qodo.ai/core-abilities/self_reflection)
  - `large_patch_policy="clip"` and `max_model_tokens=32000` handle large diffs. Nerelan just fails with `review_diff_too_large`.
  - `enable_auto_approval=false` defaults to off.
- **D4:** `ai_timeout=120` per call. No run budget (it is a single pass).
- **D7:** Ticket compliance means the reviewer gets the ticket as acceptance criteria. Nerelan already passes the objective, spec and checks.
- **Verdict:** **COPY-DESIGN.** Copy the findings cap, the severity/score threshold and large-diff clipping into `model_review.py`. Do not REPLACE it: its output is free-form PR comments with no ACCEPT/REJECT contract, no independence proof and no exact-head evidence. Optionally run it later as a second, advisory reviewer. Cost: hours.

## 3. AutoGen / AG2 / Microsoft Agent Framework

- **What they are:**
  - microsoft/autogen: last release python-v0.7.5 on 2025-09-30. It has been in maintenance mode since October 2025, and Microsoft Agent Framework is the successor. [VentureBeat](https://venturebeat.com/orchestration/microsoft-retires-autogen-and-debuts-agent-framework-to-unify-and-govern)
  - microsoft/agent-framework: MIT, python-1.26.0 on 2026-11-13.
  - ag2ai/ag2: a community fork. Apache-2.0, v1.3.1 on 2026-11-10 (active).
  - All are Python and run on Windows.
- **D4/D10:** AgentChat has **composable termination conditions**: `MaxMessageTermination`, `TokenUsageTermination`, `TimeoutTermination`, `ExternalTermination` (a programmatic "Stop" button), `TextMentionTermination("APPROVE")`, `FunctionalTermination`, and others. They combine with `|` and `&`. [termination docs](https://microsoft.github.io/autogen/stable/user-guide/agentchat-user-guide/tutorial/termination.html). This is the cleanest model of "run until stopped, plus a few safety stops". The window becomes an `ExternalTermination`, and the remaining caps become per-goal conditions.
- **Verdict:** **COPY-DESIGN** (the termination-condition algebra). Do not REPLACE: Nerelan already depends on LangGraph, AutoGen is frozen, and its conversation model does not fit durable, leased tasks. Cost: about 1–2 days to turn the window checks in `goal_service` and `control_store` into a small list of per-goal stop predicates.

## 4. CrewAI

- **What it is:** crewAIInc/crewAI. MIT, Python. Release 1.15.41 on 2026-11-12 (very active). Runs on Windows.
- **D10:**
  - Task `guardrail` (a function or a string turned into an LLM guardrail) returns `(False, error)`. The error goes back to the agent, which retries until `guardrail_max_retries` (default 3).
  - `human_input=True` puts a human on the final answer.
  - What happens after the retries are exhausted is not documented. [tasks](https://docs.crewai.com/en/concepts/tasks)
- **D4:**
  - Agent `max_iter` (docs default 20) forces a "best answer" at the limit.
  - `max_execution_time` defaults to None, and `max_rpm` is a rate cap.
  - [agents](https://docs.crewai.com/en/concepts/agents.md)
- **D7:** Every task must declare `description` **and** `expected_output`.
- **Verdict:** **COPY-DESIGN.** For D7, add an explicit, instruction-level `expected_output` field to the frozen task contract. The repair-loop design is already equal or better in Nerelan. Cost: small.

## 5. MetaGPT

- **What it is:** FoundationAgents/MetaGPT. MIT, Python. Last release v0.8.2 on 2025-03-09, last push 2026-01-21. Effectively dormant; the company's commercial product was renamed Atoms. [DataLearner](https://www.datalearner.com/en/blog/metagpt-rebrands-atoms-ai-business-building)
- **D4:** `Team.invest(investment)` sets `cost_manager.max_budget`. The run raises `NoMoneyException` when it exceeds the budget, and `run(n_round=…)` caps rounds (examples use investment 3.0, n_round 5). This is the source as seen on [HF mirror team.py](https://huggingface.co/spaces/tang-x/SPO/blob/main/metagpt/team.py), not verified on upstream.
- **Verdict:** **KEEP.** It is not maintained, and its hard-stop design is what the Owner just dropped.

## 6. Issue → PR factories: Open SWE ("Robin") and SWE-agent

- **langchain-ai/open-swe:** MIT. Nightly on 2026-11-15, very active. Now named Robin. Built on **LangGraph + Deep Agents**, the same stack Nerelan already uses.
  - Triggers are GitHub issues and PRs, Slack, Linear and schedules.
  - It has separate build, review, PR-chat and `/baby-sit` (CI-monitoring) workflows. Reviewers "do not commit or push", and PR chat excludes mutation tools.
  - An unreachable sandbox is not silently replaced.
  - No iteration or cost caps are stated. Running it as-is needs Managed Deep Agents, so it is cloud-oriented. [README](https://github.com/langchain-ai/open-swe)
- **SWE-agent:** MIT. Last release v1.1.0 in 2025-05, last push 2026-11-09. A research harness with no PR review loop.
- **Verdict:** **KEEP** (no REPLACE). Open SWE is not packaged for reuse ("not accepting contributions"; fork and adapt) and is not local-first. COPY-DESIGN the `/baby-sit` idea, a post-PR CI/review-comment watcher feeding repairs, if `landing_loop` grows it.

---

## Closed products (design references only)

| Product | Unattended run | Budget / limits presented to user | Review | Retry / repair |
|---|---|---|---|---|
| **Devin** | Async sessions | Per-session `max_acu_limit` on session creation ([API v1](https://docs.devin.ai/api-reference/v1/sessions/create-a-new-devin-session)). Monthly **Budgets** tree (account → pools → users) with warnings, persistent banners, and a "Request more ACUs" action at the limit. Requests can be auto-approved but are never auto-denied ([usage policies](https://docs.devin.ai/enterprise/features/usage-policies)). A per-session threshold makes Devin **sleep** until woken ([KB](https://knowledge.cognition.ai/articles/1715208244-for-people-confused-about-session-credit-limits)). | Devin Review counts toward budgets | Human wakes the session or raises the limit |
| **GitHub Copilot cloud agent** | One session per task, in an Actions runner | Originally **one premium request per session** ([changelog](https://github.blog/changelog/2025-07-10-github-copilot-coding-agent-now-uses-one-premium-request-per-session/)). Per-session AI-credit cap in CLI/SDK (`--max-ai-credits`, `/limits set max-ai-credits`, minimum 30). It is a **soft** cap: the agent stops cleanly, the in-flight response finishes, and you raise the cap to continue. No default, so it runs until done ([docs](https://docs.github.com/en/copilot/how-tos/copilot-cli/use-copilot-cli/set-session-limit)). A 59-minute session cap appears only in secondary sources (e.g. [developertoolkit](https://developertoolkit.ai/en/comparison/github-copilot/)); not found in official docs. | **Self-review with Copilot code review before opening the PR**, plus CodeQL, secret scanning and advisory checks ([blog 2026-02](https://github.blog/2026/02/whats-new-with-github-copilot-coding-agent/), [changelog](https://github.blog/changelog/2025-10-28-copilot-coding-agent-now-automatically-validates-code-security-and-quality/)). Same vendor: not independent. | `@copilot` comments from write-access users only. Batch comments with "Start a review" for one pass. Unassigning stops it. Workflows need approval ([review PRs](https://docs.github.com/en/copilot/how-tos/use-copilot-agents/cloud-agent/review-copilot-prs)) |
| **Codex cloud** | Cloud tasks | Plan **5-hour and weekly windows** shared with local use, then credits. At the limit the current turn may finish. No per-task cap was found ([pricing](https://learn.chatgpt.com/docs/pricing)). | `@codex review` or automatic review. **Flags only P0/P1** on GitHub. Rules come from AGENTS.md `## Code Review Rules`, scoped per file ([GitHub integration](https://learn.chatgpt.com/docs/third-party/github)). | Not found (no documented auto-fix loop) |
| **Google Jules** | Async tasks | **Daily task count (rolling 24 h) + concurrency**: 15/3, 100/15, 300/60. At the limit no new tasks start; running ones continue ([limits](https://jules.google/docs/usage-limits/)). | Built-in **critic** ("critic-augmented generation") reviews the patch before submission. Jules revises and the critic re-reviews "until no further issues remain". There is also a Planning Critic ([Google blog](https://developers.googleblog.com/en/meet-jules-sharpest-critic-and-most-valuable-ally/), [changelog 2026-01-26](https://jules.google/docs/changelog/2026-01-26-1)). Same family. | Iterates inside one task |
| **CodeRabbit** | Event-driven per push | **Reviews per developer per hour** (5/8/10/12 by plan, rolling). `auto_pause_after_reviewed_commits` (default 5) pauses incremental reviews ([rate limits](https://docs.coderabbit.ai/management/rate-limits), [auto review](https://docs.coderabbit.ai/configuration/auto-review)). | `auto_incremental_review` reviews only new pushes; `@coderabbitai full review` re-reviews from scratch. `request_changes_workflow` / `auto_approvals` approves only when the latest commit has a completed review, all threads are resolved and no pre-merge check fails ([docs](https://docs.coderabbit.ai/pr-reviews/request-changes-workflow)). | The author fixes; review resumes on the next push |

**D4 answer (how the field bounds runaway cost):**
- No product runs truly unbounded. None of them uses a global time window that strands work.
- Each bounds a **unit of work**: a session ACU cap (Devin), a session credit cap (Copilot), iterations (OpenHands, CrewAI), a review count or pause (CodeRabbit), or a task count and concurrency (Jules).
- Account-level spend is shown as a **budget meter with warnings and a "raise / request more" action**.
- When a limit is hit the stop is **soft**: the current turn finishes, then the run parks (sleep or stopped) and resumes when the limit is raised. Already-running work is never killed (Jules, Codex).
- This fits "run until stopped". Keep an explicit Stop (AutoGen `ExternalTermination`) plus per-goal soft ceilings that park and resume rather than block.

**D7 answer:**
- Every product treats the **Owner-authored task text as the instruction**: the issue body, the prompt, or `description` + `expected_output`.
- Repository rules come from AGENTS.md (Codex review rules, Copilot).
- Untrusted input is controlled by **who may speak**, not by wrapping the objective as data. Copilot passes only write-access comments and strips hidden HTML comments.
- Nerelan's #1532 came from putting the objective inside a "data, never instructions" packet. Fix: the Owner objective plus `expected_output` go in the instruction channel, and only third-party artifacts are data.

---

## What Nerelan's review loop does that the others do not

1. **Proved reviewer independence across the whole repair chain.** It uses actual models observed in usage records of every author attempt, including replaced repairs, and rejects any overlap. Copilot and Jules use same-vendor self-critique. The OpenHands judge is merely "a separate LLM". CodeRabbit and Codex are separate products, but nothing proves they differ from the author model.
2. **Exact-frozen-head evidence.** It binds head, tree, base, workspace identity and request and response digests, and checks for mutation before and after. The verdict marker on the PR is re-checked immediately before a matched-head merge. CodeRabbit's "latest commit reviewed" is the closest equivalent, but without digests.
3. **Exactly-once reviewer calls** through a journaled RPC intent. An unknown completion is never replayed. None of the others document this.
4. **Strict machine verdict contract** (`ACCEPT` ⇔ zero findings), with the findings fed verbatim into the repair contract (`ReviewRepair`).

## What Nerelan should copy

1. **A severity gate** (Codex P0/P1-only, PR-Agent `num_max_findings` and score threshold). Allow `ACCEPT` with low or medium notes, REJECT only on high or critical, and cap findings at about 6. This cuts repair rounds and churn.
2. **Incremental, finding-scoped re-review** (CodeRabbit incremental review, OpenHands `missing`). The refreshed review gets the previous findings plus the repair delta and must answer each finding as resolved or not. New findings are allowed only at high or critical. Keep the **same reviewer binding** across rounds unless it is unavailable, so the bar does not move.
3. **A useful terminal state at the round limit** (OpenHands "capped" plus push branch, Copilot "requests your review"). Publish a Draft PR with the outstanding findings and an `Owner decision needed` marker. Do not just BLOCK.
4. **Decouple from windows** (AutoGen termination algebra, Copilot and Devin soft per-session caps). The round limit stays per producer step (`max_review_rounds`). Replace `window.max_retries`, `status='ACTIVE'` and `expires_at` with per-goal stop predicates: Owner Stop, an optional per-goal soft spend ceiling that parks, and no-progress (same findings two rounds running). Show "spent / ceiling, Raise to continue".

## Top 3 actions (ranked)

1. **Re-gate the review loop on per-goal stop conditions instead of the window.**
   - Removes **D4** (stranding by window caps, goals tied to a window). It also removes the window coupling that made the repair loop fragile in **D5** (#1542/#1543 class) and **D10** (repairs blocked by `routing_retry_budget_exhausted`).
   - Design: AutoGen-style `ExternalTermination | goal_soft_ceiling | no_progress`. Soft park and resume as in Copilot `--max-ai-credits` and Devin sleep. The UI shows a budget meter with a Raise action.
   - Shrinks: `goal_service._repair_rejected_reviews` / `escalate_failed_tasks` window checks and `_routing_retries_spent`; window caps in `control_store.py` and `owner_window.py`; `unattended_coordinator.py` window gating.
2. **Severity-gated, finding-scoped incremental re-review with a sticky reviewer.**
   - Removes **D10** churn: rounds wasted on low findings, and a moving bar when the reviewer model changes. It indirectly reduces **D9** token burn by sending the delta and prior findings, not the full diff.
   - Design: Codex P0/P1, PR-Agent `num_max_findings`/threshold and `large_patch_policy=clip`, CodeRabbit incremental review, OpenHands `missing`.
   - Changes: `model_review.response_schema`, `execute_review` request building and the `review_diff_too_large` path; the `goal_service` refresh path (reuse the previous reviewer's `binding_ref`).
3. **Make the task contract instruction-first, with a hand-off at the round limit.**
   - Removes **D7** (#1532) and the dead-end BLOCKED at `model_review_round_limit` (**D10**).
   - Design: Owner objective plus CrewAI-style `expected_output` in the instruction channel. Repo review rules come from AGENTS.md (Codex `## Code Review Rules`) instead of the hard-coded `REVIEW_CHECKLIST`. At the limit, publish a Draft PR with the outstanding findings (OpenHands, Copilot).
   - Shrinks: `freeze_contract` / `freeze_handoff_contract` packet shaping; `model_review.REVIEW_CHECKLIST`. Small additions to `landing_loop.py`.
