# Codex Supervisor v0 — Audit Instructions (quota-free)

This document defines the deterministic, quota-free audit instructions for
the thin Codex Supervisor v0 implemented under Issue #92. No real Codex or
model calls occur in this phase; the instructions describe the contract an
external audit result must satisfy and the project-specific security rules
the validator enforces.

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
| `scripts/supervisor_context.py` | Calls `git` and `gh`, outputs a bounded JSON repository context. |
| `scripts/supervisor_validate.py` | Validates an external audit result, applies security rules, computes the stable cycle marker. |
| `scripts/supervisor_publish.py` | Searches existing issues for the marker, produces a dry-run `create_issue` / `update_issue` / `no_op` plan; writes only with explicit `--live`. |
| `docs/supervisor/audit-result.schema.json` | JSON Schema for the minimal audit-result contract. |

## Minimal audit-result contract

```json
{
  "status": "continue | revise | stop",
  "findings": [
    { "claim": "Bounded claim", "evidence": ["verifiable reference"] }
  ],
  "next_task": null | {
    "title": "Next task",
    "goal": "One bounded goal",
    "allowed_scope": ["path or operation"],
    "forbidden_scope": ["path or operation"],
    "acceptance_checks": ["deterministic check"],
    "execution_prompt": "Complete prompt"
  }
}
```

`status` MUST be exactly one of `continue`, `revise`, `stop`. `next_task`
MAY be `null` but MUST NOT be a list (at most one next task).

## Validation rejections (finite, machine-readable)

The validator rejects, with finite error codes:

- `INVALID_JSON` — malformed JSON.
- `INVALID_STATUS` — status missing or not in the allowed set.
- `FINDINGS_MISSING` — findings missing or empty.
- `FINDING_NO_EVIDENCE` — a finding lacks non-empty evidence.
- `FINDING_INVALID_CLAIM` — a finding has no non-empty claim.
- `NEXT_TASK_ACCEPTANCE_CHECKS_REQUIRED` — `acceptance_checks` empty.
- `NEXT_TASK_ALLOWED_SCOPE_EMPTY` — `allowed_scope` empty.
- `NEXT_TASK_SCOPE_TOO_BROAD` — `allowed_scope` contains `*`, `**`, `**/*`, `.`, `./`, or whole-repo markers.
- `POLICY_MERGE_FORBIDDEN` — requests merge / auto-merge.
- `POLICY_MAIN_PUSH_FORBIDDEN` — requests push/write to main.
- `POLICY_RELEASE_FORBIDDEN` — requests release.
- `POLICY_DEPLOYMENT_FORBIDDEN` — requests deployment.
- `POLICY_CREDENTIAL_ACCESS_FORBIDDEN` — requests reading/publishing credentials, secrets, tokens, or ChatGPT session data.
- `POLICY_UNRELATED_MUTATION_FORBIDDEN` — requests closing/modifying unrelated Issues or PRs.
- `FIELD_TOO_LONG` / `FIELD_TOO_MANY` — a bounded limit was exceeded.

Validation failure never proceeds to marker computation or publication
planning.

## Stable cycle marker

The marker is a SHA-256 digest over a canonical JSON encoding of:

```
repository
main SHA
schema version (fixed 0.1)
policy version (fixed 0.1)
normalized next_task.goal
sorted, de-duplicated next_task.acceptance_checks
```

Marker format:

```
<!-- reverse-agent-supervisor-cycle:<sha256> -->
```

Acceptance-check order has no semantics, so checks are sorted before hashing.
Whitespace is collapsed. Same semantic inputs produce the same marker; a
material change to main SHA, goal, policy version, or acceptance checks
changes the marker.

## Publication rules

```
no matching marker     -> create_issue
matching marker + body changed -> update_issue
matching marker + body same    -> no_op
```

The planner never proposes a second `create_issue` for an existing marker,
never closes issues, never modifies PRs, never touches main, and never
publishes credentials. Default mode is **dry-run** (zero GitHub writes);
writes occur only with explicit `--live`.

## Bounded limits

Issues, PRs, and commits are capped (`MAX_ISSUES=50`, `MAX_PRS=50`,
`MAX_COMMITS=50`). Titles, bodies, claims, evidence, scopes, and prompts are
length-capped. The context collector never includes full environment
variables, full GitHub Actions logs, full repository contents, API keys,
tokens, cookies, ChatGPT session data, or local authentication files.

## Deferred real-Codex steps (quota recovery)

The following remain deferred until Codex quota recovery, to be driven by
Issue #90:

- Real authenticated Codex invocation.
- Real audit-quality evaluation by Codex.
- Supervisor-driven real GitHub Issue creation.
- Second real no-duplicate verification against live issues.
- Scheduled execution.
- Automatic execution of generated work items.
