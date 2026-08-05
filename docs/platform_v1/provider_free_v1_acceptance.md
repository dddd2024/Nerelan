# Provider-free V1 Acceptance Harness

The provider-free acceptance harness proves the Platform V1 coordination middleware reaches `READY_FOR_HUMAN` without any model API call, Codex invocation, OpenHands invocation, GitHub network call, or nested agent. It exercises the real local components end-to-end against an isolated fixture Git repository and local bare remote.

## Harness architecture

The harness creates a self-contained fixture environment under `--workspace-root` and runs the real `PlatformV1Coordinator` against it:

```text
┌─ Fixture environment (under workspace-root) ──────────────────────┐
│                                                                   │
│  fixture-source-repo/        ← real Git repository (initial main) │
│  fixture-bare-remote.git/    ← real local bare remote             │
│  runs.sqlite3                ← real SQLiteRunStore database       │
│  workspaces/exec-*/          ← real GitWorktreeManager worktree   │
│  executor_counter.json       ← persisted executor call count      │
│  publisher_counters.json     ← persisted commit/push/create count │
│  simulated_pr.json           ← persisted simulated Draft PR state │
│                                                                   │
└───────────────────────────────────────────────────────────────────┘
```

### Real components

The harness uses these production components without modification:

```text
SQLiteRunStore          — real SQLite database, durable state and events
GitWorktreeManager      — real git worktree create/reconcile
LocalValidationRunner   — real subprocess execution of approved checks
GitHubPublicationAdapter.commit — real git add/commit
GitHubPublicationAdapter.push  — real git push to local bare remote
PlatformV1Coordinator   — real coordinator state machine
IssueTaskLoader.parse   — real task parsing and validation
```

### Fixture components

These components are fixture-specific replacements for external dependencies:

```text
DeterministicFixtureExecutor  — writes exactly one approved fixture file
LocalDraftPRPublisher         — real commit/push, simulated Draft PR
_FixtureGitHubAdapter         — returns SUCCESS workflow runs bound to exact head
```

The `LocalDraftPRPublisher` delegates `commit` and `push` to the production `GitHubPublicationAdapter` Git logic. Only `ensure_draft_pr` is simulated — it persists the Draft PR state to `simulated_pr.json` so restarts can discover and reuse the same PR. The `_FixtureGitHubAdapter` returns four SUCCESS workflow runs (CI, Decision Preflight, State Gate pull_request, State Gate push) bound to whatever exact head SHA is requested.

## Why this is not a pure mock test

The harness is not a pure mock test because:

1. **Real Git operations**: The fixture repository is a real Git repository with a real bare remote. The worktree is created by `git worktree add`. The commit is created by `git commit`. The push is `git push` to the bare remote. The local remote head is verified by `git ls-remote`.

2. **Real SQLite persistence**: The `SQLiteRunStore` uses a real SQLite database file. State transitions are durable. A process restart re-instantiates the store from the same database file and observes the same execution record, state, and event history.

3. **Real coordinator state machine**: The `PlatformV1Coordinator` runs its full state machine — `DISCOVERED` → `VALIDATED` → `WORKSPACE_READY` → `EXECUTOR_RUNNING` → `EXECUTOR_FINISHED` → `LOCAL_VALIDATED` → `COMMITTED` → `PUSHED` → `DRAFT_PR_OPEN` → `WORKFLOWS_OBSERVED` → `READY_FOR_HUMAN`.

4. **Real path validation**: The `GitHubPublicationAdapter.commit` calls `validate_changed_paths` to reject any file outside the approved `allowed_paths`. An executor that writes an unauthorized file is rejected at commit time.

5. **Real idempotency**: The resume path re-instantiates the store, coordinator, publisher, and executor from persisted state. It verifies that the execution ID, task digest, worktree, branch, commit SHA, local remote head, simulated PR, and workflow evidence are all identical. Side-effect counts (executor calls, commits, pushes, PR creations) remain at 1.

The only simulated surfaces are the Draft PR metadata (which would otherwise require `gh`) and the workflow observations (which would otherwise require GitHub Actions runs). Both are bound to the actual generated commit SHA.

## Run method

```powershell
python -m reverse_agent.platform_v1.provider_free_acceptance `
  --repo-dir F:/reverse-agent `
  --workspace-root F:/reverse-agent-workspaces/provider-free-v1
```

The harness exits `0` on success and emits canonical JSON to stdout.

## Output fields

```text
terminal                   — PLATFORM_V1_PROVIDER_FREE_E2E_COMPLETE on success
state                      — READY_FOR_HUMAN
model_calls                — 0 (no model API invoked)
network_calls              — 0 (no network commands invoked)
executor_calls             — 1 (deterministic executor called exactly once)
commit_count               — 1 (one real git commit)
push_count                 — 1 (one real git push)
draft_pr_create_count      — 1 (one simulated Draft PR created)
resume_idempotent          — true (restart produces identical state)
fixture_base_sha           — dynamic initial commit SHA of the fixture repo
execution_id               — stable execution ID derived from the task digest
task_digest                — SHA-256 of the normalized fixture task
worktree_path              — path to the real Git worktree
commit_sha                 — real commit SHA created by the coordinator
head_sha                   — head SHA pushed to the local bare remote
local_remote_head          — head SHA observed on the local bare remote
simulated_pr               — simulated Draft PR metadata (number, state, head_sha)
workflow_observations      — four SUCCESS workflow runs bound to exact head
execution_rows             — 1 (one execution row in SQLite)
first_run_state            — READY_FOR_HUMAN
resume_run_state           — READY_FOR_HUMAN
```

## Negative test coverage

The test suite (`tests/platform_v1/test_provider_free_acceptance.py`) verifies:

```text
Deterministic executor writes only the approved fixture file
Executor writing an unauthorized second path → commit rejected
Worktree base drift → rejected
Mismatched branch → rejected
Dirty worktree → rejected on reconcile
Diverged local remote branch → push rejected
Resume does not repeat commit
Resume does not repeat push
Resume does not repeat PR creation
Resume does not repeat executor call
Resume preserves execution_id, task_digest, commit_sha, head_sha, pr_number
Workflow head mismatch → STALE_HEAD
Missing required workflow → not READY_FOR_HUMAN
Failed workflow → REWORK_REQUIRED
Harness never invokes codex
Harness never invokes gh
Harness model_calls is 0
Harness network_calls is 0
```

## Next-stage real executor compatibility requirements

Before the live #115 canary can proceed, the following external compatibility issues must be resolved:

1. **Codex quota availability**: The trusted host must have Codex quota available. Current quota exhaustion classifies as `EXECUTOR_QUOTA_UNAVAILABLE` → `BLOCKED_EXTERNAL`, which is correct behavior but prevents live execution.

2. **Reasoning enum compatibility**: codex-cli 0.121.0 cannot parse the current provider reasoning enum (e.g. `max`). The client/server protocol mismatch classifies as `EXECUTOR_PROTOCOL_INCOMPATIBLE` → `BLOCKED_EXTERNAL`. A codex-cli version that supports the current enum is required.

3. **Live workflow observation**: The `_FixtureGitHubAdapter` must be replaced with the `LiveGitHubAdapter` for real GitHub Actions workflow observation. The coordinator already supports this via dependency injection.

4. **Live Draft PR creation**: The `LocalDraftPRPublisher.ensure_draft_pr` must be replaced with the production `GitHubPublicationAdapter.ensure_draft_pr` for real Draft PR creation via `gh`.

The provider-free harness does not claim that the real Codex canary has succeeded. It proves only that the coordination middleware is correct and complete without a provider.
