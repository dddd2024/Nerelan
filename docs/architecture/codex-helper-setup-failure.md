# Native Codex helper setup failure (#1202)

At base `e1e333eb4493122ff7a9f55972ebca2721a11c43`, the adapter already
passes `--ignore-user-config` and, on Windows, `-c windows.sandbox="elevated"`.
It launches without a shell, with an allowlisted child environment, an isolated
linked worktree, and a Windows process job. The readiness probe checks CLI flags
and managed login status; it does not identify the CLI version or prove tool
process creation. Environment filtering, shell availability, workspace setup and
CLI version remain possible differences from standalone operation, not proven
causes. No live environment, account or native CLI was probed for this change.

The existing guard rejects completed command items with status `failed` and exit
code `-1`. The bounded extension also recognizes a completed `command_execution`
whose `aggregated_output` contains both `helper_unknown_error` and
`setup refresh had errors`, regardless of missing or contradictory exit metadata.
Only fixed diagnostic evidence is projected for that item; its command and raw
output are omitted. Intermediate updates, model prose and either phrase alone
do not trigger this additional guard. Other diagnostic shapes remain unknown.

The executor returns `codex_tool_launch_failed` before patch validation or an
`EXECUTOR_COMPLETED` event, even if the CLI exits zero and reports a completed
turn. Existing durable runtime semantics mark the Task FAILED and its Goal
BLOCKED. This does not introduce a WAITING Task state or change retry policy.

Provider-free JSONL and local subprocess/SQLite fixtures verify failure handling,
not a repaired Windows helper or successful embedded Goal execution. A successful
standalone prompt/tool run does not establish full embedded Goal acceptance.
The precise setup-refresh root cause remains unknown; this change contains false
success and does not claim to repair native process creation.
