# Context Builder (Platform V1)

`reverse_agent/platform_v1/context_builder.py` rebuilds a bounded, read-only
Context Packet for one Task. It uses only these inputs:

- durable TaskStore rows;
- the existing `platform_goals` and `platform_goal_task_links` tables;
- the latest durable run observation;
- scoped Git metadata.

It never reads a stored chat summary, calls a model, uses the network, creates a
database or changes a Task. The packet carries `authority: "NONE"`.

```python
packet = build_context_packet(store, task_id=..., workspace=repo_dir,
                              expected_head=40_hex_sha, budget_bytes=16384,
                              visible_task_ids=None, visible_paths=())
text = render_context_packet(packet)  # canonical JSON; budget = len(text.encode("utf-8"))
```

## Schema (`schema_version = 1`)

- **`task`**: `id`, `repository`, `status`, `execution_id`, `title`. `status`
  is the real durable status, so `READY_FOR_REVIEW` is never relabelled.
- **`goal`**: `null`, or `id`, `revision`, `artifact_digest`, `objective`,
  `spec_markdown`, `plan_markdown`. Only a link to the Goal's current revision
  counts. A task linked only to an older revision fails with
  `context_goal_stale`.
- **`tasks`**: one summary per visible task: `id`, `status`, `execution_id`,
  `title`, `failure_classification`. The current task is always included.
- **`git`**: `head`, `diff_digest` and `changed_paths`. Each entry in
  `changed_paths` has `path`, `staged`, `unstaged` and `untracked`.
- **`sources`**: each source has `kind` (`task`, `evidence`, `goal`,
  `checkpoint` or `git`), `ref`, `version`, `digest` and `status`, where
  `status` is `CURRENT`, `UNRESOLVED` or `CONFLICT`.
  - The digest is a canonical SHA-256 of the projected source, computed before
    compaction.
  - Evidence sources add `category`, `evidence_status` and `value`. They never
    include `detail` or raw JSON. Their digest covers the original row.
  - Evidence stays `UNRESOLVED`: a matching stored detail digest does not prove
    that the referenced artifact exists or is current. A contradictory detail
    digest is `CONFLICT`. Only validated SHA-256 identities enter `version`.
  - The checkpoint source is built from `run_id`, `execution_id` and
    `accepted_checkpoint`. It is a reference, not authority.
- **`history`**: the events of the visible tasks. Each event has only `id`,
  `type`, `timestamp`, `title` and `description`. Neither `raw_log` nor metadata
  is included.
- **`omissions`**: non-negative aggregate counters: `excluded_tasks`,
  `redacted_fields`, `goal_text_truncated`, `event_descriptions_truncated`,
  `history_events_omitted` and `titles_truncated`.

## Visibility and paths

`visible_task_ids=None` makes all tasks linked to the current Goal visible, as
long as they are in the same repository. An explicit list can only narrow that
set. Excluded task IDs and their evidence or events never appear in the packet.
Excluded runtime IDs are redacted across every projected field. When visibility
excludes peers, free-form Goal objective/specification/plan text is withheld;
it may embed peer instructions without naming their runtime IDs. Its original
source digest remains available. Omission is counted in `redacted_fields`.

`visible_paths` must be exact repository-relative POSIX paths. The builder
rejects these paths:

- absolute paths, drive letters, backslashes, `.`/`..`/empty segments and
  `.git`;
- paths that pass through a symlink or Windows reparse point (junction), and
  directory scopes, including deleted directories with tracked descendants.

When `visible_paths` is empty, the packet contains no filenames.

## Git

- Git is run without a shell, with a scrubbed `GIT_*` environment and with
  these settings: `core.hooksPath=<devnull>`, `core.fsmonitor=false`,
  `--literal-pathspecs`, `--no-ext-diff` and `--no-textconv`.
- `HEAD` must equal `expected_head`, both before and after observation.
  Otherwise the build fails with `context_head_stale`.
- `origin` is normalized with `normalize_github_origin` and must match the Task
  repository.
- Staged and unstaged binary diffs of the allowed paths go into the diff digest.
- Untracked allowed paths go into the digest by blob ID. The ID comes from
  `git hash-object --no-filters`, so this process never opens the files.
- Excluded paths never affect the digest.
- Scoped dirty differences are observed again before returning; concurrent
  drift fails with `context_git_changed` instead of certifying mixed input.
- Global/system Git configuration is disabled. Configured local clean, smudge
  and process filters are disabled explicitly before any diff operation.
  Diff provenance therefore describes the files without filter conversion.

## Budget and compaction

`budget_bytes` must be an `int` from 1024 to 262144. `bool` is rejected. When
the packet is over budget, the builder compacts it in a fixed order:

1. Goal markdown.
2. The Goal objective.
3. Event descriptions.
4. Non-important events. The latest event of each task, and any
   failure/blocked/interrupted/cancelled/error/rejected/escalated event, is
   always kept.
5. Titles.

If identities, source references and the checkpoint/failure facts still do not
fit, the build fails with `context_budget_insufficient`. The JSON text itself is
never truncated.

History keeps SQLite append order, including events sharing a timestamp.
Decision-labelled events retain their references through compaction; raw log
and metadata fields are not read into the event projection.

## Execution integration

Goal-linked native GPT/Claude execution and OpenCode role execution rebuild the
packet before every role call, including the shared durable-resume path. The
launch event records its digest and byte size. The prompt labels the packet as
data and preserves the executor's existing authority envelope.

Standalone legacy tasks keep their existing prompts; the public builder also
supports explicit reconstruction for those tasks. This compatibility choice
does not bypass stale-Goal rejection for tasks that have Goal links.

Read projection uses one SQLite snapshot under the existing store lock. Current
Goal revision controls the selected links. Failed tasks retained in that
revision's escalation records remain visible by default, so moving work to a
stronger Agent or reopening the store does not erase failed attempts. Explicit
visibility restrictions can withhold those tasks as well.

Durable execution keeps the existing restricted store facade. Its additional
read-only projection method verifies the bound task, execution, run, lease owner
and epoch, unexpired lease and admitted workspace/revision before and after
building context. It returns text without exposing database or mutation APIs.

The [production follow-up and real development trial report](benchmarks/context-builder-20261013/README.md)
separates successful process-restart context consumption from rejected or timed-out
benchmark artifacts and unknown cash/quota observations.

## P0-2 follow-up: bounded context and recovery

Goal-linked native and OpenCode execution now use schema version 2. The legacy
public builder defaults to version 1; `optimize=True` opts into version 2.
Canonical UTF-8 JSON, including index/trigger metadata and optional summaries,
fits the supplied byte budget. Compression keeps structured task states,
execution identities, Goal revision, checkpoint and Git sources. It removes
Goal prose, clips history descriptions and chooses recent critical events before
other recent events. Omissions and clipping are explicit. If the structured core
cannot fit, reconstruction fails instead of discarding current truth.

The full sanitized projection stays in the existing TaskStore. Internal
`full_projection=True` is working data for bounded retrieval, never a model
prompt or browser-selectable flag. No artifact files, raw logs or metadata are
read for retrieval. Original event/evidence/Goal references and digests form a
deterministic catalog. Empty queries browse it; lexical queries and exact refs
retrieve visible entries. Oversized entries return a labelled excerpt with the
original digest. Changed snapshots fail closed rather than mixing revisions.

Authenticated local clients can POST to `/api/tasks/{task_id}/context/{action}`:

| Action | Body fields | Result |
| --- | --- | --- |
| `packet` | optional `budget_bytes` (default 16384) | fresh compact packet with snapshot/index |
| `retrieve` | `expected_snapshot`, optional `query`, `refs`, `budget_bytes` (512–65536), `limit` (1–32) | bounded catalog matches/excerpts |
| `summary` | `expected_snapshot`, optional `timeout` (1–90 seconds) | explicit saved-native-account summary result |
| `handoff` | `expected_snapshot`, `from_agent`, `to_agent` | immutable source-bound handoff identifier |
| `recover` | `handoff_id`, `agent_id`, optional `budget_bytes` | handoff plus freshly rebuilt packet |

Workspace and visibility come from trusted host configuration. Browser paths,
bindings and scope overrides never grant authority. Handoff agent names are
labels, not authentication or permission. Host APIs retain the existing local
client capability and Origin checks. The trusted source workspace is used before
a durable run; an admitted durable run uses its own workspace. A missing durable
workspace fails closed. The Python service also supports explicitly restricted
task/path views, and refuses native AI summaries for those views because the
native read-only runtime could read repository files outside that projection.

The summary trigger is deterministic: sanitized original context exceeds 65536
bytes and has at least 32 events. A trigger never calls a provider. Only the
explicit `summary` action resolves the configured native planner account and
reuses the existing read-only CLI runner. Input is independently bounded to
32768 bytes, output to 4096 bytes, and existing secret redaction runs before
persistence. Source bindings cover the events actually supplied, with compression
metadata retained. Usage is the native runner's reported usage or UNKNOWN; no
cash/quota savings are inferred. Startup and CI remain provider-free.

Summary reservations and outcomes use derived `ContextSummary` evidence;
handoffs use `ContextHandoff`. Neither contributes to authoritative source
digests or invalidates its own input. Duplicate requests reuse the recorded
outcome. A reservation surviving process loss remains RUNNING with an unknown
outcome; restart does **not** retry that potentially paid call or advertise a
completed summary. This slice does not reconcile or retry interrupted summary
jobs. Completed summaries survive restart and are included as advisory prose
only while visibility, Goal revision, execution, Git scope and supplied source
digests still match. Publication revalidates the full input inside a write
transaction after the model returns; raced input produces a FAILED receipt.

Recovery rejects changed Goal/execution/Git/visibility anchors and mismatched
receiver labels. Task statuses and checkpoints are read again, so advancing
state never comes from the old handoff or summary. Retrieval is deterministic
text search within one task/Goal projection; cross-task semantic memory and
vector search remain outside this slice.

### Error codes

`ContextBuilderError(ValueError)` has a `.code`, and its message is the code
only. The codes are:

- `context_invalid_argument`
- `context_budget_invalid`
- `context_head_invalid`
- `context_head_stale`
- `context_git_changed`
- `context_path_invalid`
- `context_visibility_invalid`
- `context_workspace_invalid`
- `context_git_failed`
- `context_repository_mismatch`
- `context_task_not_found`
- `context_store_failed`
- `context_goal_stale`
- `context_budget_insufficient`
- `context_packet_invalid`
- `context_snapshot_stale`
- `context_reference_unavailable`
- `context_transaction_invalid`
- `context_handoff_stale`
- `context_summary_scope_restricted`
- `context_summary_binding_invalid`
- `context_summary_not_needed`
