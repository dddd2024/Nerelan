# Pre-merge Authorization and Mainline Merge Validation (P1A-v2, Issue #22)

## Problem

PR #21 introduced a `MainlineIntegrationReceipt` design where the receipt file
was named by the merge commit SHA and had to exist *inside* the merge commit
being validated. This created a self-referential lifecycle: the merge commit's
SHA depends on its tree (which contains the receipt), and the receipt's
filename depends on the merge commit's SHA. Issue #22 audited this as
`REWORK_REQUIRED`.

## Solution

The rework splits the lifecycle into two independent artifacts:

1. **Pre-merge Authorization** (`MainlineMergeAuthorization`): committed in the
   accepted PR head *before* merge. Authorizes the implementation, tests, and
   publication of the replacement branch. Does **not** authorize the merge
   itself.

2. **Post-merge Receipt** (`MainlineIntegrationReceipt`): emitted as audit
   *output* after the merge. Records what was validated. Is **not** a
   prerequisite for validating the merge commit.

This separation eliminates the self-referential lifecycle: the authorization
exists before the merge, the merge is validated directly at HEAD, and the
receipt is an output that never needs to be inside the merge commit being
validated.

## Pre-merge Authorization Artifact

The `MainlineMergeAuthorization` is committed at a fixed path:

```
project_state/mainline_authorizations/active.json
```

A fixed path is used instead of naming the file by the accepted head SHA
because the SHA depends on the tree (which contains the file), creating a
circular dependency. Stale-authorization prevention comes from:

- `locked_base_sha` matching the merge's first parent.
- `second_parent_parent_matches_accepted_head`: the authz commit (second
  parent) must sit directly on top of the declared implementation head, so a
  stale authz copied into an unrelated branch cannot validate a different
  merge.
- Decision ID and Decision content digest checks binding the authz to the
  committed Decision artifact.
- Command Plan digest check binding the authz to the locked plan.

### Fields

| Field | Purpose |
|-------|---------|
| `schema_version` | Always `1`. |
| `authorization_id` | Unique identifier for this authorization. |
| `source_pr` | PR number this authorization was created for. |
| `accepted_head_sha` | Advisory: the implementation head the observations bind to. Cannot equal the authz commit's SHA (self-referential). The validator uses the merge's second parent as ground truth. |
| `locked_base_sha` | The base commit the merge's first parent must match. |
| `allowed_merge_method` | Must be `merge` (not squash/rebase). |
| `decision_identity` | `{decision_id, decision_content_digest}` binding the authz to the committed Decision. |
| `command_plan_digest` | SHA-256 of the committed Command Plan. |
| `required_workflow_observations` | Exact-head CI observations with trust-source contracts. |
| `minimum_trust_source` | Trust floor: `github_actions_run` for production, `local_asserted` for local testing. |
| `human_r2_approval_reference` | Explicit R2 approval reference. |
| `merge_tree_policy` | `equal_to_accepted_head_tree` or `allow_conflict_resolution`. |
| `authorization_status` | `active`, `expired`, or `superseded`. |
| `committed_at` | Timestamp the authz was committed. |

## Mainline Merge Validation Gate

The `mainline-merge-validation` gate runs on pushes to `main` and validates
the actual two-parent merge commit at HEAD:

1. **head_is_two_parent_merge**: HEAD is exactly one two-parent merge commit.
2. **authorization_present**: `active.json` exists in the second parent's tree.
3. **first_parent_matches_locked_base**: first parent == `locked_base_sha`.
4. **second_parent_parent_matches_accepted_head**: the authz commit's parent
   == `accepted_head_sha`, binding the authz to the exact implementation head.
5. **merge_method**: `allowed_merge_method == "merge"`.
6. **merge_tree_policy**: merge tree satisfies the declared equality/conflict
   policy.
7. **decision_digest**: Decision content digest matches the committed Decision
   in the accepted head's tree.
8. **decision_identity**: Decision ID in the authz matches the actual Decision
   file.
9. **command_plan_digest**: Command Plan digest matches the committed locked
   plan.
10. **authorization_status**: authz is `active`.
11. **required_workflow_observations**: all 4 required run names present with
    `success` conclusions.
12. **workflow_observation_heads**: observations bind to the declared
    accepted head.
13. **observation_trust_boundary**: observations meet the declared
    `minimum_trust_source`.
14. **r2_approval_reference**: non-empty human R2 approval reference.

## Post-merge Receipt

The `MainlineIntegrationReceipt` is emitted by
`emit_mainline_integration_receipt()` after the merge is validated. It records:

- Merge commit SHA, both parents, both trees.
- Authorization ID and decision identity.
- Observation references.
- Validation status and blocking reasons.
- Receipt context SHA (the commit from which the receipt is emitted, which may
  differ from the merge commit).

The receipt can be emitted from a *later* commit (e.g. one that stores the
receipt) by passing `merge_commit_sha=` to reference the merge commit. The
validator does not require `receipt_commit_HEAD == receipt.merge_commit_sha`.

## Workflow Routing

Both `state-gate.yml` and `decision-preflight.yml` route main pushes to:

- **Main integration baseline**: validates the frozen PR #9 integration
  invariant (`github.ref == 'refs/heads/main'`).
- **Mainline merge validation**: validates the actual merge commit at HEAD
  (`github.ref == 'refs/heads/main'`).

The transition preflight step is guarded by
`github.ref != 'refs/heads/main'` so it runs on PRs but not on main pushes,
where the baseline and merge-validation gates take over.

## Test Coverage

- `tests/test_integration_baseline.py`: 4 tests for the frozen baseline
  invariant.
- `tests/test_premerge_authorization.py`: 17 tests (1 positive lifecycle +
  15 negative cases + 1 workflow routing test).
- `tests/test_current_merge_validation.py`: 6 tests for the post-merge receipt
  semantics.

All tests use hermetic temporary git repositories; no network access required.
