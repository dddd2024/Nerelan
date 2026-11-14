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
clones; the automatic mode below never does. Both commands finish with the free
space on each root's volume.

## Automatic reclaim in the trusted host

On by default. Set before starting the host to change it:

| Variable | Default | Meaning |
| --- | --- | --- |
| `REVERSE_AGENT_WORKSPACE_RECLAIM` | `apply` | `apply` removes; `report` only logs what would be removed; `off` disables it |
| `REVERSE_AGENT_WORKSPACE_RECLAIM_RETENTION_DAYS` | `3` | a task must have been terminal, and its tree untouched, this long |
| `REVERSE_AGENT_WORKSPACE_RECLAIM_POLL_MINUTES` | `15` | how often finished tasks are checked (minimum 1) |
| `REVERSE_AGENT_WORKSPACE_RECLAIM_INTERVAL_HOURS` | `24` | how often the whole root is swept (minimum 1) |
| `REVERSE_AGENT_WORKSPACE_MIN_FREE_GB` | `20` | below this much free space, reclaim harder (see below); `0` disables |
| `REVERSE_AGENT_WORKSPACE_PRESSURE_RETENTION_DAYS` | `0.5` | retention used while below that target |
| `REVERSE_AGENT_WORKSPACE_MIN_START_FREE_GB` | `2` | below this, a new task worktree is refused; `0` disables |

Invalid values fall back to the default and an unknown mode stays off. The
first check runs one poll after startup, so starting the host does no extra
work. Each poll handles every task whose workspace exists and whose last
update is older than the retention period, once per process. The full sweep
also covers directories with no task row; its time and last report are kept in
`workspace_reclaim_state.json` next to the task database, so a restart does
not sweep again early.

Use `report` to read the host log (`workspace reclaim: would remove ...`)
without removing anything.

## Low disk space

While the volume holding the root is below `REVERSE_AGENT_WORKSPACE_MIN_FREE_GB`,
every poll runs a full sweep with the pressure retention and logs a warning.
Pressure only shortens the wait. Every other check still applies, so dirty,
unpushed, locked or running work is kept however full the disk is, and the
warning continues until an operator frees space.

Below `REVERSE_AGENT_WORKSPACE_MIN_START_FREE_GB`, task preparation stops with
`workspace_disk_space_low` before running `git worktree add`, so a nearly full
disk fails one task cleanly instead of partway through its work.

Caches that a sandboxed run left unlistable (`.nt`, `.pytest_cache`) no longer
keep a tree. If the host account also cannot delete them, the removal is
reported as failed and the leftover needs an administrator.
