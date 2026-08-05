# Platform V1 Codex E2E Coordinator

The trusted-host coordinator connects an approved R1 GitHub Issue to one isolated Codex execution and one Draft PR. It uses the existing Platform V1 contracts and exact-head GitHub adapter; it does not implement an agent loop, Git client, CI service, frontend, or merge automation.

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

## Durable state

The default database is `.platform_v1_runtime/runs.sqlite3` under `repo-dir`. That directory is ignored by Git. The `executions` table stores the current state and reconciled Git/GitHub identities. The append-only `state_events` table records every transition.

Before a side effect, the current durable state represents its intent boundary. After the operation, the coordinator reads Git or GitHub truth and stores the resulting commit, head, PR, or workflow observation. A restart reuses the stable execution ID, worktree, branch, commit, and Draft PR.

## Safety boundary

The machine-readable Issue task block is the only execution authority. Issue prose is passed to Codex as read-only goal context and cannot broaden paths, checks, risk, or publication. The loader rejects closed Issues, missing owner approval events, wrong repository/base, broad or traversing paths, unrestricted shell commands, main branches, and any publication other than a Draft PR.

The coordinator never merges, marks ready, enables auto-merge, force-pushes, rebases, releases, deploys, or reads credential material. It uses the host's existing `codex` and `gh` sessions only through their documented CLI interfaces. Stored output is bounded, hashed, and redacted.

## Recovery and workflow classification

Ordinary product failures enter `REWORK_REQUIRED` within the task's bounded retry count. Base drift, branch conflicts, path violations, and credential-policy violations fail terminally. Exact-head workflows are classified as success, pending, product failure, policy failure, infrastructure timeout, stale head, or a known external gate blocker. The known State Gate copy-heuristic blocker is used only when the failed log matches its bounded signature.
