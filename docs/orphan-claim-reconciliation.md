# Orphan claim reconciliation evidence (#1206)

`orphan_claim_plan.plan_orphan_claim` is an R0, provider-free dry-run observation
of one explicit task/run, not an R1 durable transition. It never opens a window,
releases a claim/reservation, appends a receipt, charges usage, or dispatches work.
FAILED/INTERRUPTED Tasks, expired leases/windows and an empty external-operation
table do not prove remote termination. Usage remains UNKNOWN, never assumed zero.

The current external-operation representation records caller-supplied result
strings. Its optional run lease fence does not authenticate remote terminal
outcomes or bind the original coordinator claim, expired window, exact policy
and reservation. Control operation receipts likewise are local audit records,
not authoritative remote terminal receipts. Thus TERMINAL_VERIFIED is reserved
and currently unreachable; even matching SUCCESS bookkeeping stays UNKNOWN.

Blocked R1 work: establish an authoritative positive terminal receipt format and
trusted ingestion/verifier binding task ID, run ID, coordinator owner/epoch,
run lease/epoch, original expired window, policy ID/revision/digest, exact
reservation and actual terminal outcome. A future transition must revalidate all
bindings with compare-and-swap in one transaction and persist exactly one neutral
reconciler receipt, preserving UNKNOWN usage. A planner result is never write
authority and cannot be replayed to release anything.

This isolated change adds no coordinator or claim-release implementation. Draft
#1210 was not accessed (GitHub is outside this task's scope); integration must be
reviewed against its exact diff by the supervisor before any R1 work is combined.
Synthetic tests are evidence of fail-closed behavior, not product acceptance or
proof about the three production Claims. No production state was inspected.
