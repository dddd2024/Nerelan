# Approved functional checks

Goal tasks can select host-owned checks before owner review:

```json
{
  "id": "T001",
  "title": "Implement the requested behavior",
  "instruction": "Implement and verify the acceptance criteria",
  "validation_checks": [
    {"profile_id": "python_pytest", "working_directory": "."},
    {"profile_id": "npm_test", "working_directory": "frontend"}
  ]
}
```

The persisted plan lists these checks. Editing a planned task changes the Goal's
artifact digest and revision. An approved plan is immutable; amend and review the
Goal again before changing its checks. Launch atomically freezes the checks,
catalog digest/version, Goal/revision/artifact identity, repository and admitted
source HEAD with Task creation in the existing SQLite evidence table. A repeated
launch returns the same Tasks and contracts. No additional execution store or
database migration is used.

The current catalog has two profiles:

| Profile | Installed runtime | Accepted test evidence |
| --- | --- | --- |
| `python_pytest` | Host Python running `-m pytest -q -p no:cacheprovider` | Host-selected temporary JUnit report |
| `npm_test` | Installed Node and npm CLI, running `npm test` | `node --test` with TAP, or `vitest run` with a temporary JUnit report |

The server adds fixed reporting arguments. Other npm test scripts, lifecycle
`pretest`/`posttest` hooks and project `.npmrc` files are explicitly unsupported.
There is no installation fallback. npm runs offline with isolated empty user and
global configuration, an isolated cache, disabled audits/funding/update notices,
and closed stdin. Provider credentials and parent Python/Node injection flags
are not copied into the child environment. This is process and command policy,
not an operating-system sandbox for repository test code.

Up to eight distinct profile/directory pairs may be selected. Directories must
resolve inside the actual prepared repository; traversal, absolute paths and
escaping directory links fail. The caller cannot supply argv, executable paths,
shell commands, environment overrides or timeout overrides. Each check has a
600-second deadline. The runner drains and hashes output while retaining at most
4096 bytes for report parsing; raw output is not stored as functional evidence.
JUnit files are temporary and limited to 8 MiB. Windows jobs contain the child
before it resumes and terminate descendants on close. Other hosts use an owned
process group. A timed-out check or dangling output stream fails.

Verification requires an actual implementation delta for an implementation task,
all selected checks to succeed, at least one executed passing test per check, no
failed tests, supplementary Git whitespace hygiene, and unchanged exact Git HEAD
and private-index tree identities across the checks. Zero collected tests,
entirely skipped suites, syntax errors, failed assertions, changed base/contract
or modification during validation cannot produce verified evidence. The existing
private-index snapshot preserves the real Git index. Test coverage and the quality
of assertions remain part of owner review; passing a selected suite does not prove
every product requirement.

Ordinary and durable single/sequential execution use the same oracle after the
executor finishes. Sequential handoff files are removed before taking the tested
artifact snapshot. Durable evidence uses the existing lease-fenced TaskStore
writes. Accepted executor roles are not replayed after restart. Recovery from an
accepted validation checkpoint rechecks the persisted result binding and current
artifact; it cannot turn a failed or stale result into success.

`approved_functional_checks` identifies this validation surface. Task frontend
projections expose `functionalValidation`, and Run validation exposes
`functional`. These projections require the frozen contract, matching result
digest, current execution identity and successful per-check evidence. An exit
code of zero by itself is insufficient. A deterministic fixture may have
`FIXTURE_VERIFIED` evidence but never `verified: true`. Legacy Tasks without a
selected contract continue to expose hygiene results without functional proof.
GitHub workflow-name `required_checks` remains a separate publication contract.

This backend capability does not authorize publication or merge and does not
complete F03's user-facing acceptance. Check selection, review and proof display
still need full UI integration and product acceptance under parent issue #653.
