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

## Scoped positive-evidence contract

`terminal_receipt.verify_terminal_receipt` is a separate read-only classifier;
it does not change the audit reader or planner. Trusted host code must supply
an original binding snapshot, a provider receipt source, and an independently
configured cryptographic trust anchor. There is no production implementation,
default trusted key, JSON ingestion route, or release helper. The only working
source/anchor pair is explicitly test-only, using a synthetic HMAC key.

The signed v1 canonical payload covers the original task/run, claim owner/epoch
and expiry, window and expiry, policy ID/revision/digest, executor/execution and
binding reference, run lease owner/epoch/expiry, reservation composite identity
and amounts, provider operation ID, provider/key/receipt identity, terminal
outcome, fresh query challenge and validity interval (at most 60 seconds).
The provider must attest cessation of **all effects of the original execution**;
acknowledging a cancel request or local SUCCESS is insufficient. An adapter must
authenticate the provider response and enforce pinned keys, signature algorithm
and revocation policy through its trust anchor. A caller-supplied boolean is
never an anchor. Dependencies are trusted code, not a sandbox against malicious
Python implementations; an always-true injected anchor defeats that trust boundary.

UNKNOWN covers missing dependencies, missing/invalid signatures, mismatches,
stale/future receipts, replayed challenges and provider/anchor failures. A fresh
challenge requires a fresh attested provider query about the original effect;
an old terminal receipt alone cannot be replayed. Successful classification is
evidence only: budget remains UNKNOWN (this format has no spend attestation),
and release_allowed is always false. No receipt IDs are durably consumed and
no CAS is implemented. A later independently reviewed adapter/transition must
re-read and atomically compare every original fence, preserve UNKNOWN spend,
deduplicate its reconciliation receipt and maintain the orphan hold until its
separate release requirements are satisfied.

For **each of the three stale ACTIVE Claims**, the missing external evidence is:

- An authenticated original provider operation/execution identity mapped to the
  exact original task/run, executor and binding reference.
- An independently attested terminal-effect result covering that identity and
  every claim, window, policy, lease and reservation field listed above, with a
  fresh challenge, receipt identity, validity interval and verifiable signature.
- A pinned provider trust root/key identity and documented verification and
  revocation API. No trustworthy provider receipt API has been established here.
- Separately authenticated actual spend/usage, if budget reconciliation is
  desired; absence of spend evidence cannot establish zero usage.

The three Claim IDs and their binding values are not in the supplied repository
evidence; no per-Claim values or outcomes can truthfully be asserted here.
These requirements apply separately to all three, not as a shared terminal proof.
No live store, provider, production window or Claim was inspected or changed.
