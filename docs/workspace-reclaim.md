# Workspace reclaim

Task execution leaves one linked worktree per task under `task_workspaces/`.
`reverse_agent.platform_v1.workspace_reclaim` removes the ones that can no
longer hold work: clean, pushed, idle for the retention period, task terminal,
not a planner worktree, not locked. Anything else is kept and reported with
the reason; locked files and long paths are skipped and logged, never forced.

## Manual sweep

```text
python -m reverse_agent.platform_v1.workspace_reclaim --root <task_workspaces> --task-db <tasks.sqlite3>
python -m reverse_agent.platform_v1.workspace_reclaim --root <task_workspaces> --task-db <tasks.sqlite3> --apply
```

The first command is a dry run. `--include-clones` also considers standalone
clones; the automatic mode below never does. `--preserve` (with `--task-db`)
also reclaims the worktree of a terminal task that holds uncommitted or
unpushed work: the working tree, the index and reflog-only commits are first
written to `refs/nerelan/reclaimed/<task>/<sha>` in the shared repository. A
worktree whose work cannot be kept, or that changes meanwhile, stays. Get work
back with `git worktree add <dir> refs/nerelan/reclaimed/<task>/<sha>`.

## Automatic reclaim in the trusted host

Off by default. Set before starting the host:

| Variable | Default | Meaning |
| --- | --- | --- |
| `REVERSE_AGENT_WORKSPACE_RECLAIM` | `off` | `report` logs what would be removed; `apply` removes it |
| `REVERSE_AGENT_WORKSPACE_RECLAIM_RETENTION_DAYS` | `3` | a task must have been terminal, and its tree untouched, this long |
| `REVERSE_AGENT_WORKSPACE_RECLAIM_POLL_MINUTES` | `15` | how often finished tasks are checked (minimum 1) |
| `REVERSE_AGENT_WORKSPACE_RECLAIM_INTERVAL_HOURS` | `24` | how often the whole root is swept (minimum 1) |
| `REVERSE_AGENT_WORKSPACE_RECLAIM_PRESERVE` | off | `1` is `--preserve` |
| `REVERSE_AGENT_WORKSPACE_RECLAIM_LOW_DISK_GB` | `10` | below this much free space the host warns and sweeps early, at most hourly |
| `REVERSE_AGENT_WORKSPACE_RECLAIM_LOW_DISK_RETENTION_DAYS` | `1` | retention of those early sweeps (minimum 0.25) |

Invalid values fall back to the default and an unknown mode stays off. The
first check runs one poll after startup, so starting the host does no extra
work. Each poll handles every task whose workspace exists and whose last
update is older than the retention period, once per process. The full sweep
also covers directories with no task row; its time and last report are kept in
`workspace_reclaim_state.json` next to the task database, so a restart does
not sweep again early.

Try `report` first and read the host log (`workspace reclaim: would remove
...`) before switching to `apply`.
