# Platform V1 Codex E2E Coordinator

The trusted-host coordinator connects an approved R1 GitHub Issue to one isolated Codex execution and one Draft PR. It uses the existing Platform V1 contracts and exact-head GitHub adapter; it does not implement an agent loop, Git client, CI service, frontend, or merge automation.

## V1 accepted surface: provider-free coordination middleware

The V1 accepted surface is a **provider-free coordination middleware**. It proves the full vertical slice — authority intake, durable SQLite state, isolated worktree, bounded executor interface, local validation, commit/push lifecycle, Draft-PR abstraction, workflow observation, restart recovery, idempotency, and external-blocker classification — without requiring a model API call, Codex invocation, OpenHands invocation, or GitHub network access.

### Validated

```text
authority intake
durable SQLite state
isolated worktree
bounded executor interface
local validation
commit/push lifecycle
Draft-PR abstraction
workflow observation
restart recovery
idempotency
external-blocker classification
```

### Deferred

```text
real Codex/provider interoperability
quota availability
reasoning enum compatibility
live #115 canary
```

The live #115 Codex experiment is deferred because the trusted host has no Codex quota and codex-cli 0.121.0 cannot parse the current provider reasoning enum. V1 completion does not require or attempt a model call. The production Codex adapter remains injectable; external quota/protocol failures classify as `BLOCKED_EXTERNAL` rather than consume product-rework attempts.

## Operator commands

```powershell
python -m reverse_agent.platform_v1.cli run-e2e `
  --repo-dir F:/reverse-agent `
  --repository dddd2024/reverse-agent `
  --issue-number 115 `
  --workspace-root F:/reverse-agent-workspaces

python -m reverse_agent.platform_v1.cli resume `
  --repo-dir F:/reverse-agent `
  --repository dddd2024/reverse-agent `
  --issue-number 115 `
  --workspace-root F:/reverse-agent-workspaces

python -m reverse_agent.platform_v1.cli status `
  --repo-dir F:/reverse-agent `
  --repository dddd2024/reverse-agent `
  --issue-number 115 `
  --workspace-root F:/reverse-agent-workspaces
```

Every command emits canonical JSON. `status` and `cancel` read only local SQLite state. `run-e2e` and `resume` load the task and approval observation from GitHub; callers cannot supply paths, checks, success flags, or publication grants.

## Provider-free acceptance harness

The provider-free acceptance harness proves the V1 accepted surface without any external provider. It is executable via:

```powershell
python -m reverse_agent.platform_v1.provider_free_acceptance `
  --repo-dir F:/reverse-agent `
  --workspace-root F:/reverse-agent-workspaces/provider-free-v1
```

The harness creates an isolated fixture Git repository, local bare remote, SQLite database, worktree, deterministic executor, simulated Draft PR, and fixture workflow observations. It uses real `SQLiteRunStore`, `GitWorktreeManager`, `LocalValidationRunner`, `GitHubPublicationAdapter.commit`/`push`, and `PlatformV1Coordinator`. The Draft PR and workflow observations are fixture components that bind to the actual generated commit SHA. See [provider_free_v1_acceptance.md](provider_free_v1_acceptance.md) for details.

## Durable state

The default database is `.platform_v1_runtime/runs.sqlite3` under `repo-dir`. That directory is ignored by Git. The `executions` table stores the current state and reconciled Git/GitHub identities. The append-only `state_events` table records every transition.

Before a side effect, the current durable state represents its intent boundary. After the operation, the coordinator reads Git or GitHub truth and stores the resulting commit, head, PR, or workflow observation. A restart reuses the stable execution ID, worktree, branch, commit, and Draft PR.

## Safety boundary

The machine-readable Issue task block is the only execution authority. Issue prose is passed to Codex as read-only goal context and cannot broaden paths, checks, risk, or publication. The loader rejects closed Issues, missing owner approval events, wrong repository/base, broad or traversing paths, unrestricted shell commands, main branches, and any publication other than a Draft PR.

The coordinator never merges, marks ready, enables auto-merge, force-pushes, rebases, releases, deploys, or reads credential material. It uses the host's existing `codex` and `gh` sessions only through their documented CLI interfaces. Stored output is bounded, hashed, and redacted.

## Recovery and workflow classification

Ordinary product failures enter `REWORK_REQUIRED` within the task's bounded retry count. Base drift, branch conflicts, path violations, and credential-policy violations fail terminally. Exact-head workflows are classified as success, pending, product failure, policy failure, infrastructure timeout, stale head, or a known external gate blocker. The known State Gate copy-heuristic blocker is used only when the failed log matches its bounded signature.

### External executor blocker classification

Non-zero executor exits are classified deterministically before entering `REWORK_REQUIRED`:

```text
Codex usage limit / quota exhausted / no quota / rate limit / plan limit / capacity exceeded
→ EXECUTOR_QUOTA_UNAVAILABLE
→ BLOCKED_EXTERNAL

reasoning enum `max` unsupported / unknown variant / expected one of / protocol mismatch / xhigh
→ EXECUTOR_PROTOCOL_INCOMPATIBLE
→ BLOCKED_EXTERNAL
```

External blockers do not consume product-rework attempts, do not increment the attempt counter, and do not become `REWORK_LIMIT_EXHAUSTED`. A non-zero exit without an external signature falls through to the existing `PRODUCT_TEST_FAILURE` → `REWORK_REQUIRED` path.

### Required workflow verification

Before declaring `READY_FOR_HUMAN`, the coordinator verifies that all required workflow keys are present in the observations:

```text
CI / pull_request
Decision Preflight / pull_request
State Gate / pull_request
State Gate / push
```

Missing required workflows transition to `REWORK_REQUIRED` with `failure_classification=MISSING_REQUIRED_WORKFLOWS`. Stale-head observations (workflow head SHA differs from the expected head) transition to `REWORK_REQUIRED` with `failure_classification=STALE_HEAD`.
