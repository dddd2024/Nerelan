# Long-running research campaigns

Set `REVERSE_AGENT_RESEARCH_CAMPAIGN` to an Owner-written JSON file to enable
the trusted host's campaign loop. Without it, startup creates no campaign.
The repository must match the origin identity of `REVERSE_AGENT_REPO_DIR`.
The host starts the remote job broker first, when configured.

```json
{
  "campaign_id": "synthetic-matmul-001",
  "repository": "dddd2024/jev-nerelan",
  "objective": "Investigate the hypothesis and document evidence and uncertainty.",
  "state_dir": "F:/nrl-research/campaigns",
  "executor_kind": "codex",
  "binding_ref": "chatgpt-gpt",
  "max_rounds": 12,
  "max_hours": 72,
  "max_job_wait_hours": 24,
  "max_resume_wait_minutes": 60,
  "max_consecutive_failed_rounds": 2,
  "poll_seconds": 30,
  "push": false
}
```

The loop creates idempotent agent-team Goals and uses the existing planner,
approval and launch services. Planning and execution require a current ACTIVE
window covering the repository. The loop never activates or extends windows.
The orchestration code itself makes no model calls; the existing agent planner
and normal Goal tasks perform model work through the configured host adapters.
Existing window capabilities, authority and budgets still apply.

Use a dedicated, clean research repository checkout. Its default branch comes
from local `origin/HEAD`, falling back to local `main` or `master`; no fetch is
performed. Task commits (publication evidence, retained accepted artifacts, or
the completed durable task worktree's HEAD) are merged locally with merge
commits. Native task agents do not commit: for a completed durable task at
POST_VALIDATION, the host reuses the existing temporary-index snapshot helper
to retain its uncommitted result as a deterministic local task commit. This
preserves the task worktree's HEAD and real index and checks repository identity,
object-store identity, approved-base ancestry and patch hygiene. Retention is
execution evidence, not functional or scientific acceptance. Tasks without
commit evidence or an eligible durable result are recorded as integration errors.
Conflicts are aborted and other tasks continue.
Unrelated repository changes pause integration; they are never discarded.
The research checkout does not use Nerelan's own landing gate.

Each objective requires reading and updating `RESEARCH_LOG.md`, inspecting prior
results, stating uncertainty, and writing `CAMPAIGN_DONE.md` with justification
when finished or unable to meet the objective. Round records report whether the
research log exists after integration; this is evidence, not scientific acceptance.

Remote experiments use only the [remote job protocol](remote-jobs.md), with ids
prefixed `r<n>-`. All server research directories, experiment files, raw data,
temporary files and caches must remain inside the broker job directory under
`~/wjc`. The campaign loop never submits or replays jobs itself. It discovers
new outbox requests in integrated commits and reads the broker's local receipts.
Jobs can remain pending for hours without creating another Goal. A round waits
for each job to reach RESULT_COLLECTED (or REJECTED, with nothing to collect);
FAILED, LOST and TIMED_OUT receipts stay pending until the broker actually
collects a result. Waiting is bounded by `max_job_wait_hours` (default 24);
past it, unfinished jobs are recorded as JOB_WAIT_EXPIRED and whatever is
collected is imported. Without a configured broker, a round with jobs records
NO_BROKER and continues instead of waiting.

Results, manifests, receipts and logs are copied into `results/<job_id>/` after
manifest size/hash verification, then verified again and committed as
`round <n>: results`. Durable snapshots and file ownership records allow an
interrupted copy or commit to resume without overwriting unrelated files.
Manifest mismatches are recorded for the affected job. The first results commit
adds `results/.gitattributes` (`* -text`) so evidence is never end-of-line
converted (for example by Git for Windows' `core.autocrlf`) and every task
worktree sees the manifest's exact bytes; a different existing rule pauses the
results commit. Receipt broker bindings accept the committed request either as
raw blobs or as checked out through the repository's filters. Receipt collection or
successful commands alone do not establish functional or scientific acceptance.
Merge and results commits use an explicit loop identity, independent of the
host repository's git config. A crash can leave the loop's own uncommitted
import temporaries; on the next tick they are removed only when the round
records prove the loop created them, while any other working-tree changes still
pause integration.

State is stored under `<state_dir>/<campaign_id>/state.json` and
`rounds/<n>.json`, with append-only transition histories and atomic replacement.
Keep this directory durable, outside task worktrees, and do not edit state while
the host is running. An OS lock excludes simultaneous campaign ticks. Restart
uses the same Goal idempotency key and reconciles completed merges/imports.
While the round's Goal is still RUNNING and the active window can resume an
INTERRUPTED task (`resume_task` capability and retry budget left), the round
waits for the coordinator's normal resume, at most `max_resume_wait_minutes`
(default 60), so the task's work and any job it already requested are
integrated in this round. Otherwise interrupted tasks finish their round as
INTERRUPTED and are mentioned in the next objective; the loop itself never
replays them. Broker runs with the round's job prefix whose request was never
integrated are recorded as `orphaned_jobs` and named in the next objective;
their results are not imported, because evidence must match a committed request.

The loop pauses without an active window, stops at `max_hours`, `max_rounds`,
`CAMPAIGN_DONE.md`, or a `<state_dir>/<campaign_id>/STOP` file, and enters
`PAUSED_FAILING` after the configured consecutive failed rounds. A round counts
as failed when its Goal failed or no task commit was integrated. STOPPED,
COMPLETED, EXPIRED and PAUSED_FAILING are durable terminal decisions; restarting
the host does not clear them. Start a new campaign id after addressing a failed
setup. Window pauses resume automatically when an eligible window appears.
When STOP or `max_hours` lands while a round's goal is still running, the round
records it clearly; the goal itself is left to its window, never cancelled.

Optional `"push": true` attempts `git push origin <branch>` once after each
round. Errors are recorded; pushes are not retried automatically. Local-only is
the default. Host shutdown stops the loop before stopping the broker.

Read-only status, without starting services or contacting a provider/server:

```text
python -m reverse_agent.platform_v1.research_loop status --campaign campaign.json --json
```
