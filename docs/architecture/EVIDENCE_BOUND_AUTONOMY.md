# Evidence-bound autonomous work

Owner direction: [#252](https://github.com/dddd2024/Nerelan/issues/252#issuecomment-5892002899).
First bounded implementation: [#1033](https://github.com/dddd2024/Nerelan/issues/1033).
This document describes the product contract and implementation boundaries. It is
not an authority grant and does not replace AGENTS.md or Path A / Path B.

## Goal

Within an explicitly activated scope, capability set, lifetime and budget, AI
may take over observation, prioritization, task preparation, in-scope delegated
approval, implementation, repair, review coordination, delivery and maintenance.
The owner should not have to repeat approval for every already-authorized step.

Every completion claim must be supported by admissible evidence appropriate to
that claim. An executor submits a candidate; it cannot certify its own success.
Unknown, missing, stale, skipped or wrong-artifact evidence is not PASS. A correct
final artifact does not excuse unauthorized or destructive behavior on the way.

The guarantee has separate layers:

1. Every completed claim has a verification record (coverage).
2. The record came from an admissible verifier of the intended artifact and
   environment, not a generated narrative (validity).
3. The specification and tests cover the relevant real-world requirements
   (semantic sufficiency, which must be assessed rather than assumed).

Passing bounded tests is not a universal proof. Claims must state scope,
assumptions, version, environment, remaining uncertainty and invalidation rules.

## Implemented in EBA-0

| Surface | Behavior | Not implied |
| --- | --- | --- |
| `path_a.verify_path_a_r1` | Authorization-only results keep `product_accepted` and `implementation_complete` false in all stages. Existing authorization, denial and Ready-stage fields retain their prior semantics. | This does not decide whether another independent acceptance path has verified the product. False here means not established by this gate, not a functional FAIL. |
| `path_a.write_task_check_outputs` | The GitHub output-file head is `DeltaObservation.head_sha`, not an undefined variable. | No new selected check, authority or workflow is introduced. |
| `control_plane.work_item_preflight` | Read-only API and module CLI aggregate structural R1 candidate defects before approval is requested. | This is an opt-in diagnostic, not yet a mandatory Issue-creation hook, approval service or R2 Decision compiler. |
| `tests/platform_v1/test_evidence_bound_autonomy.py` | Provider-free positive and negative regressions live in the existing blocking Platform V1 test suite. | These tests do not demonstrate a whole autonomous project or a real-provider user journey. |

### Preapproval usage

Export the candidate Issue body to a local UTF-8 file, then run:

```text
python -m reverse_agent.control_plane.work_item_preflight --issue-body-file candidate.md --repository dddd2024/Nerelan
```

Optional observations are explicit inputs:

```text
--observed-base-sha
--observed-head-sha
--occupied-path
--pr-body-file
--issue-number
--repo-root
```

Supply each option with its observed value; repeat `--occupied-path` for multiple
concrete paths. No GitHub or Git command is run to manufacture those observations.
Use `--repo-root` only for the checkout whose test-target existence is being
checked. A partial checkout is not evidence of full repository readiness.

Exit code 0 means `APPROVAL_READY`: no defects were found in this bounded static
R1 diagnostic. Exit code 1 means `NEEDS_REVISION`; exit code 2 is an unreadable or
invalid input file (argument usage errors also use argparse's exit code 2).
JSON output never grants approval, implementation, Ready, merge or completion.

The diagnostic reuses current Path-A normalization/digests, allowed-path and
snapshot parsers, command-token validation, risk floors and fixed test selection.
It adds section-boundary/ambiguity checks and reports multiple defects together.
For example, the historical `git diff --name-only <base_sha>..<exact_head_sha>`
checks block is rejected before requesting a label, using the existing rule.

Limits and deliberate exclusions:

- Inputs are bounded regular UTF-8 files; the CLI rejects final symlinks,
  non-regular files, oversize data and invalid encoding. It does not create,
  modify, approve or execute a submitted Work Item.
- This first static-ready implementation requires concrete literal paths.
  Glob scopes return `path_scope_requires_expansion`, because an offline
  validator cannot establish the risk of every future file a glob could cover.
  This is a conservative diagnostic limitation, not a change to Path-A policy.
- Up to 128 declared paths, 256 occupied paths and 64 diagnostics are retained;
  truncated diagnostics remain non-ready. Error details do not echo Issue prose
  or submitted command values.
- Required sections and their aliases must be unambiguous. An absent Draft
  snapshot before activation is normal. A candidate body containing a canonical
  authority-like snapshot is rejected. An optional Draft snapshot must parse and
  bind to the supplied body, repository, branch, base and optional issue/head.
- Base/head/occupancy values are caller-supplied observations, not verified live
  facts or an atomic snapshot. Cross-file semantic dependencies need review.
- `selected_checks` comes from the existing fixed mapping, not commands copied
  from the Issue; it is not a complete inventory of every applicable CI workflow.
  `test_targets_present` is only an existence observation when a root and mapped
  targets were checked successfully. No tests are executed by this diagnostic.
- A safe-looking filename is not a complete semantic risk assessment. Existing
  path-risk coverage is reused, not silently expanded or declared exhaustive.
- Semantically sufficient requirements, approver identity, live approval events,
  revocation, immutable authority, exact checkout identity and concurrent
  ownership remain the responsibility of the actual authority/acceptance path.
  Material Issue edits still require reapproval under the current policy.

## Ownership and reuse

| Existing owner | Responsibility |
| --- | --- |
| #118 | One activated bounded policy, in-scope worker delegation, budgets, expiry, revocation, operation receipts and external-state reconciliation. |
| #653 | Functional obligations, verifier provenance, exact artifact/environment binding and honest completion projection. Keep already-landed functional evidence. |
| #379 | Generator/evaluator/promotion separation, Champion/Challenger, protected regression cases, staged promotion and rollback. |
| #342 | Typed requirements, execution vehicles, supersession and idempotent lifecycle reconciliation. |
| #721 | Explicit safe base-refresh authority; filename disjointness alone is insufficient. |
| #252 | Evidence-backed project-level planning and continuing work, without replacing the other owners. |

Reuse TaskStore, existing functional contracts/evidence, executor bindings,
GitHub observation and durable execution. Do not add another task database,
authority engine, general LLM judge, agent runtime or evidence store for this plan.

## Target end-to-end contract (later slices)

### Acceptance before implementation

Bind requirement revision, observable obligations, protected invariants,
verification method, required environment, excluded scope and failure criteria
before executing. AI may draft a contract but cannot silently lower it after
seeing a failing implementation. Contract changes create explicit revisions
under the existing delegated policy and independent validation.

### Independent verification

Developer tests aid iteration; independent acceptance reads actual artifacts and
external state. A different model reading the same narrative is not independent
state observation. Verification should combine deterministic checks, real
composition/browser/API checks, and scoped semantic review where appropriate.
Hidden test instances may challenge overfitting, but user requirements are not
secret. Mocks/digital twins cannot prove a real account's entitlement or quota.

The candidate may not control the only verifier, protected cases, evidence
signing identity or promotion authority that certifies that same candidate.
Verifier updates themselves require a separate acceptance path and comparison
against the known-good verifier. A candidate policy cannot approve itself.

### Claim binding and projection

Reuse existing records to bind each claim to its requirement revision, exact
artifact, verifier/policy version, environment, actual outcome, observation time,
coverage, evidence references and invalidation conditions. Provenance alone is
not semantic correctness. Executor-written PASS text is not an execution record.

Keep authorization, execution end, checks, functional acceptance, review,
merge, deployment and long-term outcome distinct. Generate task status and user
summaries from trusted observations, not free-form executor assertions. A parent
goal is not complete merely because its child tasks are green; omitted or
postponed obligations remain visible and require goal-level acceptance.

### Durable continuation

A real service must persist observe -> admit -> execute -> verify -> reconcile
-> continue. A long prompt is not a durable scheduler. Recovery is allowed only
while authorization remains valid, the recovery action is within scope, budgets
remain, and uncertain external side effects have been reconciled. Repeating a
request after timeout must not duplicate a PR, merge, publication or charge.
Revocation is not an infrastructure fault to erase with an automatic reapproval.
Use expiring ownership/fencing for concurrent supervisors and bound cumulative
retries, cost, time and no-progress cycles. Retain failed evidence.

## Delivery phases

EBA-0 is the narrow foundation listed above. These later stages are not complete
merely because EBA-0 passes tests:

- EBA-1 (#653): connect existing obligations/evidence to trusted task and goal
  completion, including actual artifact/environment checks and honest unknowns.
- EBA-2 (#118/#252): in-scope autonomous approval and durable next-action
  selection; external supervisors no longer hand-copy labels/SHA/snapshots.
- EBA-3 (#118): authorized delivery, post-deploy observation, revocation and
  uncertain-side-effect reconciliation under independent acceptance.
- EBA-4 (#379): measured promotion of working methods and separately governed
  verifier/policy changes with protected regressions and rollback.

## Evaluation and adversarial acceptance

Compare current supervision, simple autonomy, multi-agent text review and
evidence-bound autonomy using comparable tasks, models and budgets. Measure
false acceptance alongside real completed work, human interventions, duration,
total cost and later regressions/reopenings. A system that never finishes must
not win merely because it never falsely accepts. Roughly 30-50 tasks can start
an experiment; zero observed errors is not proof of zero future risk.

Challenge at least: no implementation, wrong/old artifact, tests not run, all
critical tests skipped, forged PASS logs, stale evidence replay, mock-only
success, cancellation without stopping, revoked authority, successful external
side effect followed by client timeout, and a candidate modifying its own sole
acceptance oracle. Also retain correct-but-different implementations to detect
false rejection. Full end-to-end evidence is required before enabling the
corresponding autonomous capability; this document is not that evidence.
