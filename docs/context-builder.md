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

## Errors

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
