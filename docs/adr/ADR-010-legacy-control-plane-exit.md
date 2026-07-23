# ADR-010: Legacy Control Plane Exit

## Status

`ACCEPTED`

## Context

The legacy control plane remains necessary for historical readability but duplicates mutable state and imposes uniform governance cost. Immediate deletion would destroy auditability and rollback safety.

## Decision

Migrate monotonically through `ACTIVE_COMPATIBILITY -> READ_ONLY_COMPATIBILITY -> ARCHIVED -> REMOVED_FROM_RUNTIME`.

Move to read-only only after representative new-path R1/R2 tasks pass, new work enters the new path, GitHub truth is no longer mirrored as mutable publication truth, runtime evidence no longer enters ordinary source commits, and a rollback window is documented. Archive before runtime removal. Deletion requires a separate high-risk Decision.

## Alternatives considered

- Big-bang deletion: rejected due audit and rollback loss.
- Permanent dual-write: rejected because it preserves conflicting authorities.
- Leave legacy active indefinitely: rejected because new architecture never becomes authoritative.

## Consequences

Compatibility readers persist for a bounded period. New fields and Gates are not added to legacy except critical maintenance.

## Security implications

Single-writer cutover reduces stale authorization and ambiguous truth. Read-only archives retain forensic evidence without participating in runtime decisions.

## Migration implications

P1 integrates/fixes the Architecture Spine baseline; P2 performs containment and prepares read-only transition. Later evidence authorizes archive/removal.

## Revisit conditions

Transition timing may change based on evidence. The four states, single-writer rule, archive-before-removal, and separately authorized deletion remain.
