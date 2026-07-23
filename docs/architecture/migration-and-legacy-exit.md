# Migration and Legacy Control Plane Exit

## Status

`ACCEPTED` by P0 Architecture Constitution.

## Purpose

Define the staged, auditable, and irreversible migration from the Legacy Control Plane while preserving historical readability and rollback safety.

## Authority

This document is the unique authority for legacy lifecycle states, transition criteria, PR #9 integration ordering, and P1/P2 separation.

## Scope

The lifecycle is fixed:

```text
ACTIVE_COMPATIBILITY
-> READ_ONLY_COMPATIBILITY
-> ARCHIVED
-> REMOVED_FROM_RUNTIME
```

## Non-goals

- No PR #9 merge or mutation in P0.
- No legacy deletion, mass state rewrite, or repository hygiene implementation in P0.
- No P1/P2 work is implicitly authorized by this document.

## Context

PR #9 is accepted only at exact head `43418818af61d9be3208d2444fd6ce5120f73fab` and remains Draft, open, and unmerged. Its integration requires a separate P1 Decision that preserves accepted ancestry.

## Decisions

### ACTIVE_COMPATIBILITY

Legacy entries may start legacy work while the new control path has not completed representative R1/R2 tasks. No new legacy fields or Gates are added except critical correctness/security maintenance.

### READ_ONLY_COMPATIBILITY

Historical state and Decisions remain readable. New work cannot start through legacy entrypoints, write legacy runtime-evidence locations, or create mutable publication mirrors.

### ARCHIVED

Legacy data is immutable and excluded from runtime decisions. It remains available for audit and migration verification through explicit archive readers.

### REMOVED_FROM_RUNTIME

Production runtime does not read legacy control-plane state. Only offline migration/archive tooling remains.

Transition prerequisites include representative new-path R1/R2 completions, GitHub truth no longer copied into mutable mirrors, new runtime evidence outside source commits, all new Work Items entering the new path, a documented rollback window, and an independently authorized removal action.

PR #9 integration sequence for P1:

1. Re-verify exact accepted head and required checks.
2. Compare current `main` with the PR base.
3. Do not rebase, squash, or mutate the accepted head.
4. Integrate using a method that preserves accepted commit ancestry.
5. Verify the integrated result on `main`.
6. Mark Architecture Spine `FROZEN_BASELINE`.
7. Reopen only for demonstrated security/correctness defects.

## Invariants

- State transitions are monotonic unless an explicit rollback inside the documented window is invoked.
- Historical Decisions remain readable but cannot authorize new-generation workflows after read-only transition.
- Deletion requires a separate high-risk Decision.
- P1 integration and P2 hygiene are different work packages.

## Interfaces

- A lifecycle registry exposes current state and transition evidence.
- Compatibility readers are read-only after transition.
- GitHub supplies merge truth; local reports link to it and do not mirror it as mutable authority.
- Artifact migration preserves digest, provenance, retention, and original identity.

## Failure modes

- Legacy and new paths both accept new work.
- Historical state is deleted before archive verification.
- Accepted PR #9 ancestry is rewritten.
- Runtime evidence continues entering ordinary source commits.
- A rollback resets facts without an audit record.

## Security implications

Removing legacy writers reduces ambiguous authority and stale authorization. Read-only preservation maintains forensic traceability. Separate removal authorization prevents cleanup from becoming an accidental destructive migration.

## Migration impact

P1 integrates and freezes PR #9. P2 performs repository hygiene and containment, then moves legacy to read-only when exit criteria pass. Later evidence confirms archive/removal readiness.

## Acceptance criteria

- Four lifecycle states and entry/exit meanings are explicit.
- PR #9 exact-head integration is deferred to P1.
- P2 containment is separate from P1.
- Rollback and deletion boundaries are explicit.

## Related ADRs

- [ADR-010 Legacy Control Plane Exit](../adr/ADR-010-legacy-control-plane-exit.md)
- [ADR-004 Unique Source of Truth](../adr/ADR-004-unique-source-of-truth.md)
