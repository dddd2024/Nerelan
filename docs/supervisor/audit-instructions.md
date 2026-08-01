# Codex Supervisor v0 — Audit Instructions (fail-closed v0.4)

This document defines the deterministic audit instructions for
the thin Codex Supervisor v0 implemented under Issue #92 (PR #93 rework).
The scripts do not invoke a model themselves; a bounded external Codex shadow
audit may consume the collected Context and must return schema `0.2` JSON.

## v0.4 exact-state closure

The audit-result schema remains `0.2`. v0.4 tightens collection and optional
live-update enforcement without adding a framework:

1. Every parameterized `gh api` read uses explicit `--method GET`.
2. Context collection requires local `HEAD == PR headRefOid` and GitHub
   `refs/heads/main == origin/main`; the verified GitHub SHA becomes
   `main_sha`.
3. Check-run pagination requires a stable integer `total_count`, retains all
   successful, failed, and pending records, and rejects malformed records,
   incomplete pages, more than 10 pages, or more than 500 total records.
4. Inside the publication lock, an `update_issue` re-reads all Issues and
   requires the target to remain open with exactly one planned Marker,
   unchanged title/body SHA-256 preimages, no duplicate Marker, and a freshly
   recomputed `update_issue` plan. Any concurrent change produces zero writes.

## v0.3 fail-closed closure

This revision documents the **v0.3 fail-closed closure** rework of the
supervisor scripts. The audit-result **schema** (`schema_version`) remains
`"0.2"` — the v0.3 changes are enforcement behaviors, not structural
schema changes. The changes are:

1. **Checks collection** — Checks are fetched via `gh api` `check-runs`
   bound to the exact head SHA, NOT `gh pr checks` (whose non-zero exit was
   wrongly treated as "no checks"). Failed checks are retained with
   `name`, `status`, `conclusion`, and a bounded `run_url`. Network
   failure, timeout, invalid JSON, or incomplete pagination raises a
   bounded error and emits no Context.
2. **Issue Marker discovery** — Uses paginated `gh api repos/<repo>/issues`
   with `state=all` (NOT `gh issue list --state all --limit 100`). Pull
   Request entries returned by the `/issues` endpoint are filtered out.
   Any page failure, invalid JSON, entry missing `number`/`body`/`state`,
   or over-cap result is fail-closed. Malformed entries are NOT silently
   skipped.
3. **Remote main verification** — Before any live GitHub Issue write, the
   GitHub-side `refs/heads/main` SHA is queried via `gh api`. The
   GitHub-side main MUST equal `audited_main_sha` AND the local
   `origin/main` MUST equal the GitHub-side main. Any drift → zero writes.
4. **Closed-Issue Marker handling** — Same Marker in a closed Issue with
   identical content → `no_op`. Same Marker in a closed Issue with
   different content → `CLOSED_MARKER_REQUIRES_OWNER` (zero writes, no
   auto-edit, no reopen, no surrogate create). Multiple Markers in one
   Issue, or the same Marker in two Issues → fail-closed.
5. **Permission / command checks** — `requested_operations` remains the
   authoritative permission grant. The natural-language scan of `goal` and
   `execution_prompt` NO LONGER skips negated sentences: a forbidden
   operation keyword is rejected directly. Legitimate prohibitions belong
   in `forbidden_scope`, not prompt negation. `acceptance_checks` use
   word-boundary command/token rules (see below).
6. **Active PR configurable** — Issue #90 is the configurable goal Issue
   (`--goal-issue`). The active PR is supplied via `--active-pr <number>`
   or derived from the current branch via `gh api pulls`. Zero or multiple
   matches → fail-closed. PR #93 is no longer hardcoded.
7. **Single-machine publish lock** — A runtime-only exclusive lock (stdlib
   only) is acquired in the system temp directory before any live guard /
   Marker query / GitHub mutation. Atomically acquired via `O_EXCL`,
   released in `finally`. If the lock already exists, zero writes. This
   lock is single-machine only — it does NOT provide cross-machine
   distributed atomicity.
8. **Volatile evidence** — The exact implementation HEAD, CI run IDs, and
   State Gate run IDs are NOT recorded in tracking docs as "current facts"
   (they expire on every push). Stable repository-hygiene facts are
   recorded; volatile results are published as PR #93 comments after
   Actions complete.

## Scope and non-goals

The supervisor is a **thin layer over `git` / `gh` / `json` / `hashlib`**. It
deliberately does NOT introduce a Backend Protocol, FixtureAuditBackend
product module, SubprocessCodexBackend framework, Snapshot class hierarchy,
Publication Planner class system, GitHub Adapter, workflow engine, database,
checkpoint, or Provider Registry. Those remain out of scope; the quota-free
foundation composes mature tools directly.

## Files

| File | Purpose |
|------|---------|
| `scripts/supervisor_context.py` | Calls `git` and `gh`, outputs a bounded JSON repository context. Fail-closed: any required step failure raises `ContextError` and emits no context. v0.3: checks via `gh api check-runs` bound to exact head; goal Issue and active PR are configurable. |
| `scripts/supervisor_validate.py` | Validates an external audit result against the v0.2 closed schema, applies security rules, computes the stable cycle marker. v0.3: no negation skip; word-boundary command/token checks; operation–prompt consistency. |
| `scripts/supervisor_publish.py` | Searches existing issues (ALL states) for the marker via paginated `gh api`, produces a dry-run `create_issue` / `update_issue` / `no_op` plan; writes only with explicit `--live` after live guard + TOCTOU re-query. v0.3: paginated discovery, remote main verification, closed-marker handling, single-machine publish lock. |
| `docs/supervisor/audit-result.schema.json` | JSON Schema for the v0.2 audit-result contract (unknown fields rejected). Schema structure is unchanged in v0.3. |

## v0.2 audit-result contract (fail-closed)

The audit result MUST match this closed schema. Unknown fields at any level
(top level, finding, next_task) are rejected. The schema version remains
`"0.2"` in v0.3 — v0.3 changes are enforcement behaviors, not structure.

```json
{
  "schema_version": "0.2",
  "repository": "dddd2024/reverse-agent",
  "audited_main_sha": "<full 40-hex-char SHA>",
  "status": "continue | revise | stop",
  "findings": [
    { "claim": "Bounded claim", "evidence": ["verifiable reference"] }
  ],
  "next_task": null | {
    "title": "Next task",
    "goal": "One bounded goal",
    "allowed_scope": ["path or operation"],
    "forbidden_scope": ["path or operation"],
    "requested_operations": ["closed-whitelist operation"],
    "acceptance_checks": ["deterministic check"],
    "execution_prompt": "Complete prompt"
  }
}
```

`schema_version` MUST be exactly `"0.2"`. `repository` MUST exactly equal
the expected repository. `audited_main_sha` MUST be a full 40-hex SHA and
MUST exactly equal the expected main SHA (case-insensitive). `status` MUST
be exactly one of `continue`, `revise`, `stop`. `next_task` MAY be `null`
but MUST NOT be a list (at most one next task).

## Authority model — `requested_operations` is authoritative

`next_task.requested_operations` is the **authoritative** permission grant.
It MUST be a non-empty subset of this closed whitelist:

```
read_repository
edit_bounded_files
run_checks
push_named_branch
create_or_update_draft_pr
```

Any operation not in this whitelist is forbidden. The following are NEVER
permitted, and listing them in `requested_operations` is rejected:

```
push_main
merge
mark_ready
auto_merge
release
deploy
credential_access
close_issue
delete_branch
rewrite_history
```

The natural-language keyword scan of `allowed_scope`, `goal`, and
`execution_prompt` is a **secondary** guard only — it can additionally
reject (e.g. flag "merge" mentioned in `allowed_scope`), but the absence of
a keyword does NOT authorize an operation that is absent from
`requested_operations`.

### v0.3 — no negation skip

In v0.3 the secondary scan NO LONGER skips negated sentences in `goal` or
`execution_prompt`. A phrase like "Do not merge" or "Never push to main"
is **rejected** because the forbidden operation keyword (`merge`, `push to
main`) is present. Legitimate prohibitions MUST be expressed as
`forbidden_scope` entries, not as natural-language negation in the prompt.
This prevents an auditor from smuggling a forbidden operation into a prompt
under the guise of a prohibition.

## `acceptance_checks` command/token rules (v0.3)

`acceptance_checks` are scanned with **word-boundary matching** so that
safe commands are allowed while dangerous ones are rejected:

- **Allowed**: `git merge-base HEAD origin/main` (the token `merge` is
  followed by `-`, not a word boundary, so it is not flagged).
- **Rejected commands** (word-boundary match):
  - `gh pr merge` — merge / auto-merge
  - `git push origin main`, `git push main`, `push main`, `push to main`
  - `git push --force`, `force push`, `force-push`, `push -f`
  - `rebase`, `reset --hard` (history rewrite)
  - `release`, `gh release`
  - `deploy`, `deployment`
  - `read credentials`, `read secrets`, `read token`
  - `git branch -D`, `git branch -d`, `git push --delete` (branch deletion)
- **Rejected shell metacharacters** (substring match — these tokens are
  unambiguous):
  - `&&`, `||` (shell chaining)
  - `$(` (command substitution)
  - `` ` `` (backtick)
  - ` | ` (pipe), ` > ` / ` >> ` / ` < ` (redirection)
  - `; ` (command separator)

Any match is rejected with `POLICY_DANGEROUS_ACCEPTANCE_CHECK` or
`POLICY_SHELL_METACHAR_FORBIDDEN`.

## Operation–prompt consistency (v0.3)

The validator verifies that `requested_operations` matches what the prompt
describes:

- `allowed_scope` defines the bounded scope that the task may access. It does
  not itself grant or imply mutation authority.
- `requested_operations` remains the authoritative permission grant. When
  `edit_bounded_files` is absent, every repository path in `allowed_scope` is
  read-only.
- Repository edit authority is required only for positive repository-artifact
  mutation intent in `goal` or `execution_prompt`. Strong edit verbs are
  checked as bounded whole-word patterns. Generic metadata/reporting verbs
  such as `create`, `update`, `change`, `write`, `add`, `remove`, and `delete`
  imply repository mutation only when the same finite clause names a
  repository artifact or explicit path.
- Draft PR metadata changes require `create_or_update_draft_pr`, not
  `edit_bounded_files`.
- A directly negated edit occurrence is not positive edit intent. The
  validator splits text with a finite delimiter set, so a separate positive
  edit instruction in the same prompt is still detected.
- If `goal` or `execution_prompt` mentions `push` (whole word),
  `push_named_branch` MUST be in `requested_operations`.
- If `goal` or `execution_prompt` mentions `draft pr`, `update pr`, or
  `pr description`, `create_or_update_draft_pr` MUST be in
  `requested_operations`.

A mismatch is rejected with `OPERATION_PROMPT_INCONSISTENCY`.

## Validation rejections (finite, machine-readable)

The validator rejects, with finite error codes:

- `INVALID_JSON` — payload is not a JSON object.
- `SCHEMA_VERSION_MISMATCH` — `schema_version` is not `"0.2"`.
- `REPOSITORY_MISMATCH` — `repository` does not equal the expected value.
- `INVALID_MAIN_SHA_FORMAT` — `audited_main_sha` is not a full 40-hex SHA.
- `MAIN_SHA_MISMATCH` — `audited_main_sha` does not equal the expected SHA.
- `UNKNOWN_FIELD` — any field outside the closed set (top level, finding, or next_task).
- `INVALID_STATUS` — status missing or not in `{continue, revise, stop}`.
- `FINDINGS_MISSING` — findings missing or empty.
- `FINDING_NO_EVIDENCE` — a finding lacks non-empty evidence.
- `FINDING_INVALID_CLAIM` — a finding has no non-empty claim.
- `NEXT_TASK_ALLOWED_SCOPE_EMPTY` — `allowed_scope` empty.
- `NEXT_TASK_SCOPE_TOO_BROAD` — `allowed_scope` contains `*`, `**`, `**/*`,
  `.`, `./`, `./**`, `all`, `entire repository`, `whole repo`, etc.
- `NEXT_TASK_OPERATIONS_REQUIRED` — `requested_operations` missing or empty.
- `NEXT_TASK_OPERATION_UNKNOWN` — `requested_operations` contains an
  operation not in the closed whitelist.
- `NEXT_TASK_ACCEPTANCE_CHECKS_REQUIRED` — `acceptance_checks` empty.
- `NEXT_TASK_FORBIDDEN_SCOPE_INVALID` — `forbidden_scope` element is not a
  non-empty string or exceeds the length cap.
- `POLICY_DANGEROUS_ACCEPTANCE_CHECK` — `acceptance_checks` contains a
  dangerous command.
- `POLICY_SHELL_METACHAR_FORBIDDEN` — `acceptance_checks` contains shell
  chaining, substitution, redirection, or command separator metacharacters.
- `POLICY_BRANCH_DELETION_FORBIDDEN` — `acceptance_checks` contains branch
  deletion (`git branch -D`, `git push --delete`, etc.).
- `POLICY_MERGE_FORBIDDEN` — secondary scan flagged merge / auto-merge.
- `POLICY_MAIN_PUSH_FORBIDDEN` — secondary scan flagged push/write to main.
- `POLICY_RELEASE_FORBIDDEN` — secondary scan flagged release.
- `POLICY_DEPLOYMENT_FORBIDDEN` — secondary scan flagged deploy/deployment.
- `POLICY_CREDENTIAL_ACCESS_FORBIDDEN` — secondary scan flagged credentials,
  secrets, tokens, or ChatGPT session data.
- `POLICY_UNRELATED_MUTATION_FORBIDDEN` — secondary scan flagged
  closing/modifying unrelated Issues or PRs.
- `OPERATION_PROMPT_INCONSISTENCY` — `requested_operations` does not match
  the operations described in `goal` / `execution_prompt` / `allowed_scope`.
- `FIELD_TOO_LONG` / `FIELD_TOO_MANY` — a bounded limit was exceeded.

Validation failure never proceeds to marker computation or publication
planning.

## Stable cycle marker (v0.2)

The marker is a SHA-256 digest over the canonical JSON encoding of:

```
repository
exact main SHA (40 hex chars, lowercased)
schema_version (fixed "0.2")
policy_version (fixed "0.2")
normalized next_task.goal
sorted, de-duplicated next_task.allowed_scope
sorted, de-duplicated next_task.forbidden_scope
sorted, de-duplicated next_task.requested_operations
sorted, de-duplicated next_task.acceptance_checks
```

Marker format:

```
<!-- reverse-agent-supervisor-cycle:<sha256> -->
```

A material change to **any** covered field changes the marker. Acceptance-
check and scope order have no semantics, so they are sorted before hashing.
Whitespace is collapsed. Same semantic inputs produce the same marker.

## Publication rules (fail-closed, v0.3)

```
no matching marker                       -> create_issue
matching marker + body changed (OPEN)    -> update_issue (title AND body together)
matching marker + body same (OPEN)       -> no_op
matching marker + body same (CLOSED)     -> no_op (no duplicate create)
matching marker + body changed (CLOSED)  -> no_op + CLOSED_MARKER_REQUIRES_OWNER
marker in two Issues                     -> no_op + DUPLICATE_MARKER (zero writes)
multiple markers in one Issue            -> no_op + MULTI_MARKER_IN_ISSUE (zero writes)
```

The planner never proposes a second `create_issue` for an existing marker,
never closes issues, never reopens issues, never modifies PRs, never
touches main, and never publishes credentials. Default mode is **dry-run**
(zero GitHub writes); writes occur only with explicit `--live`.

### v0.3 — Issue discovery (paginated, fail-closed)

Issue discovery uses `gh api repos/<repo>/issues?state=all` with explicit
pagination (`per_page=100`, `page=1..10`). The `/issues` endpoint returns
Pull Request entries (those carrying a `pull_request` field); these are
filtered out — they are NOT Issues. Any of the following is fail-closed
(zero writes):

- Any page failure (non-zero exit or timeout).
- Empty output where a non-empty page was expected.
- Invalid JSON on any page.
- An entry that is not a JSON object.
- An entry missing `number`, `body`, or `state`.
- Exceeding the safety cap (`MAX_TOTAL_ISSUES=500`).

Malformed entries are NOT silently skipped — the discovery fails closed.

### v0.3 — remote main verification

Before any live GitHub Issue write, `verify_remote_main` queries
`gh api repos/<repo>/git/refs/heads/main` and `git rev-parse
refs/remotes/origin/main`. ALL of the following must hold:

- GitHub-side `refs/heads/main` SHA is a full 40-hex SHA equal to
  `audited_main_sha`.
- Local `origin/main` SHA equals the GitHub-side main SHA.

Any failure → zero `gh issue create` / `gh issue edit` calls.

### v0.3 — live guard (full pre-write check)

Before any live write, `live_guard` verifies ALL of:

- `gh api user` returns login `dddd2024`;
- worktree is clean (`git status --porcelain` empty);
- current branch is `agent/codex-supervisor-foundation-v0` (never `main`);
- GitHub-side `refs/heads/main` equals `audited_main_sha` (Task 3);
- local `origin/main` equals the GitHub-side main (Task 3);
- marker query completes successfully (no discovery failure, no duplicate).

Any failure → zero writes. The live path is wrapped in a single-machine
publish lock (Task 7).

### v0.3 — single-machine publish lock

The live path acquires `PublishLock` (stdlib only) in the system temp
directory via `O_CREAT | O_EXCL` (atomic). The lock is held across the
entire live path (live guard + TOCTOU re-query + GitHub mutation) and
released in `finally`. If the lock already exists, zero writes.

This lock is **single-machine only**. It does NOT coordinate across hosts
and does NOT coordinate with processes that bypass it. It is a guard
against accidental concurrent live publications on the same machine (e.g.
two terminals running `--live` in parallel).

### Fail-closed rules (carried from v0.2)

- **Discovery failure** (gh failure, invalid JSON, incomplete results) →
  zero writes.
- **Duplicate marker** (same marker in two Issues) → zero writes.
- **Multiple markers in one Issue** → zero writes.
- **Body exceeding `MAX_BODY_LENGTH`** → rejected, NOT truncated.
- **TOCTOU re-query**: immediately before any live write, the marker is
  re-queried. If the marker appeared or duplicated since the plan was
  computed, zero writes.

## Bounded limits

Issues, PRs, and commits are capped (`MAX_ISSUES=50`, `MAX_PRS=50`,
`MAX_COMMITS=50`). Titles, bodies, claims, evidence, scopes, prompts,
operations, and acceptance checks are length- and count-capped. The context
collector never includes full environment variables, full GitHub Actions
logs, full repository contents, API keys, tokens, cookies, ChatGPT session
data, or local authentication files.

Pagination safety caps: `MAX_ISSUE_PAGES=10`, `MAX_CHECK_PAGES=10`,
`PAGE_SIZE=100`, `MAX_TOTAL_ISSUES=500`.

## Context collection (fail-closed, v0.3)

`supervisor_context.collect_context` raises `ContextError` and emits no
context when any required step fails:

- `git` invocation failure (non-zero exit) or timeout;
- `gh` invocation failure or timeout;
- empty or invalid JSON from `gh ... --json` or `gh api`;
- missing main SHA;
- missing goal Issue facts;
- check-runs API failure, invalid JSON, or incomplete pagination;
- active-PR derivation returning zero or multiple matches.

Read failures are NEVER masked as empty Issue/PR lists. The context
collector records bounded goal Issue information and active PR facts
(exact head, checks). Checks are fetched via `gh api` `check-runs` bound
to the exact head SHA; failed checks are retained with `name`, `status`,
`conclusion`, and a bounded `run_url` (no stderr, env, token, cookie, or
session data).

### v0.3 — configurable goal Issue and active PR

- `--goal-issue <number>` (default `90`) — the Issue carrying the bounded
  goal. Issue #90 is the default but is NOT hardcoded.
- `--active-pr <number>` — the active PR for exact-head/check facts. If
  omitted, the PR is derived from the current branch via
  `gh api repos/<repo>/pulls?head=<owner>:<branch>&state=open`. Exactly
  one match is required; zero or multiple → `ContextError`.

## Volatile evidence handling (v0.3)

The exact implementation HEAD, CI run IDs, and State Gate run IDs change
on every push and are NOT recorded in tracking documents as "current
facts". Stable repository-hygiene facts (branch counts, dispositions,
audited main SHA, implementation branch name) are recorded in
`docs/repository-hygiene-report.md`. Volatile results (exact Head, CI
run ID, State Gate run ID) are published as PR #93 comments after
Actions complete, where they can be timestamped and superseded without
invalidating the stable document.

## Deferred real-Codex steps (quota recovery)

The following remain deferred until Codex quota recovery, to be driven by
Issue #90:

- Real authenticated Codex invocation.
- Real audit-quality evaluation by Codex.
- Supervisor-driven real GitHub Issue creation.
- Second real no-duplicate verification against live issues.
- Scheduled execution.
- Automatic execution of generated work items.
