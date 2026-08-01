# Codex Supervisor v0 — Audit Instructions (quota-free, fail-closed v0.2)

This document defines the deterministic, quota-free audit instructions for
the thin Codex Supervisor v0 implemented under Issue #92 (PR #93 rework).
No real Codex or model calls occur in this phase; the instructions describe
the contract an external audit result must satisfy and the project-specific
security rules the validator enforces.

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
| `scripts/supervisor_context.py` | Calls `git` and `gh`, outputs a bounded JSON repository context. Fail-closed: any required step failure raises `ContextError` and emits no context. |
| `scripts/supervisor_validate.py` | Validates an external audit result against the v0.2 closed schema, applies security rules, computes the stable cycle marker. |
| `scripts/supervisor_publish.py` | Searches existing issues (ALL states) for the marker, produces a dry-run `create_issue` / `update_issue` / `no_op` plan; writes only with explicit `--live` after live guard + TOCTOU re-query. |
| `docs/supervisor/audit-result.schema.json` | JSON Schema for the v0.2 audit-result contract (unknown fields rejected). |

## v0.2 audit-result contract (fail-closed)

The audit result MUST match this closed schema. Unknown fields at any level
(top level, finding, next_task) are rejected.

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

`acceptance_checks` is scanned for dangerous commands (push main, merge,
release, deploy, force push, rebase, reset --hard, credential/secret/token
access). Any match is rejected.

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
- `POLICY_MERGE_FORBIDDEN` — secondary scan flagged merge / auto-merge.
- `POLICY_MAIN_PUSH_FORBIDDEN` — secondary scan flagged push/write to main.
- `POLICY_RELEASE_FORBIDDEN` — secondary scan flagged release.
- `POLICY_DEPLOYMENT_FORBIDDEN` — secondary scan flagged deploy/deployment.
- `POLICY_CREDENTIAL_ACCESS_FORBIDDEN` — secondary scan flagged credentials,
  secrets, tokens, or ChatGPT session data.
- `POLICY_UNRELATED_MUTATION_FORBIDDEN` — secondary scan flagged
  closing/modifying unrelated Issues or PRs.
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

## Publication rules (fail-closed)

```
no matching marker              -> create_issue
matching marker + body changed  -> update_issue (title AND body together)
matching marker + body same     -> no_op
marker in two Issues            -> no_op + DUPLICATE_MARKER (zero writes)
closed Issue with same marker   -> no_op (no duplicate create)
```

The planner never proposes a second `create_issue` for an existing marker,
never closes issues, never modifies PRs, never touches main, and never
publishes credentials. Default mode is **dry-run** (zero GitHub writes);
writes occur only with explicit `--live`.

### Fail-closed rules

- **Discovery failure** (gh failure, invalid JSON, incomplete results) →
  zero writes.
- **Duplicate marker** (same marker in two Issues) → zero writes.
- **Body exceeding `MAX_BODY_LENGTH`** → rejected, NOT truncated.
- **Live guard** (before any live write) verifies ALL of:
  - `gh` login user is `dddd2024`;
  - worktree is clean;
  - current branch is `agent/codex-supervisor-foundation-v0` (never `main`);
  - `origin/main` equals `audited_main_sha`;
  - marker query completes successfully;
  - at most one Issue matches the marker.

  Any failure → zero `gh issue create` / `gh issue edit` calls.
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

## Context collection (fail-closed)

`supervisor_context.collect_context` raises `ContextError` and emits no
context when any required step fails:

- `git` invocation failure (non-zero exit) or timeout;
- `gh` invocation failure or timeout;
- empty or invalid JSON from `gh ... --json`;
- missing main SHA;
- missing Issue #90 goal or PR #93 facts.

Read failures are NEVER masked as empty Issue/PR lists. The context
collector records bounded Issue #90 goal information and PR #93 exact head,
CI success, and State Gate failure facts (run IDs and states only — no
stderr, env, token, cookie, or session data).

## Deferred real-Codex steps (quota recovery)

The following remain deferred until Codex quota recovery, to be driven by
Issue #90:

- Real authenticated Codex invocation.
- Real audit-quality evaluation by Codex.
- Supervisor-driven real GitHub Issue creation.
- Second real no-duplicate verification against live issues.
- Scheduled execution.
- Automatic execution of generated work items.
