# Current Merge Validation

## Problem (Issue #20)

The historical `integration-baseline` gate only proves the frozen PR #9 merge
remains in ancestry and still has the recorded tree.  It does **not** bind the
current `main` HEAD to the PR currently being merged, that PR's accepted exact
head, the current merge commit's ordered parents, the current merge tree, the
current Decision/Command Plan, or the exact-head checks for the current PR.

After PR #19 or any later transition PR is merged, the `main` push gate can
pass merely because the historical PR #9 merge remains an ancestor.  It
therefore does not provide post-merge authorization or content identity for
the merge that just changed `main`.

## Solution

`current-merge-validation` is a separate gate that runs **in addition to** the
historical `integration-baseline` gate on pushes to `main`.  It binds the
current `HEAD` to an accepted `MainlineIntegrationReceipt`.

### Receipt selection (deterministic, no mutable "latest")

Receipts are stored at:

```
project_state/mainline_receipts/<merge_commit_sha>.json
```

The gate looks up `project_state/mainline_receipts/<HEAD>.json`.  If no receipt
exists for the current `HEAD`, the gate **fails closed**.  A stale historical
receipt cannot validate a later unrelated commit because the file is named by
the merge commit SHA.

### Receipt schema

`project_state/schemas/mainline_integration_receipt.schema.json` requires:

| Field | Purpose |
|-------|---------|
| `schema_version` | `1` |
| `receipt_id` | Stable identifier for the receipt |
| `source_pr` | PR number that was merged |
| `decision_identity` | Decision that authorized the merge |
| `base_sha` | Main HEAD before the merge |
| `accepted_head_sha` | Exact-head accepted subject of the PR |
| `merge_commit_sha` | The merge commit created on `main` |
| `ordered_parent_shas` | `[base_sha, accepted_head_sha]` in order |
| `accepted_head_tree_sha` | Tree of the accepted subject head |
| `merge_tree_sha` | Tree of the merge commit |
| `require_tree_equality` | If `true`, merge tree must equal subject tree |
| `receipt_digest` | `sha256:` over identity fields (tamper detection) |
| `required_exact_head_runs` | Four successful runs binding `accepted_head_sha` |
| `observed_at` | ISO-8601 UTC timestamp |

### `receipt_digest` (tamper detection)

`receipt_digest` is a SHA-256 over the JSON-canonicalised identity fields
(`source_pr`, `decision_identity`, `base_sha`, `accepted_head_sha`,
`merge_commit_sha`).  The gate recomputes the digest and compares it to the
stored value.  A receipt tampered with a different PR or Decision fails the
`receipt_identity` check.

### Gate checks

`current-merge-validation` fails closed unless:

1. the receipt conforms to `mainline_integration_receipt.schema.json`;
2. `HEAD` equals `merge_commit_sha`;
3. the stored `receipt_digest` matches the recomputed digest;
4. the merge's second parent equals `accepted_head_sha`;
5. the observed parent order equals `ordered_parent_shas`;
6. the merge tree equals `merge_tree_sha` (and, when `require_tree_equality`
   is `true`, also equals the subject tree and `accepted_head_tree_sha`);
7. all four `required_exact_head_runs` bind `accepted_head_sha` with
   `conclusion: success`;
8. the run names are exactly `CI`, `Decision Preflight`,
   `State Gate (pull_request)`, and `State Gate (push)`.

## Pre-merge to post-merge receipt flow

1. A PR is accepted at exact head `X` after all four workflow runs succeed.
2. A separate R2 merge Decision authorises the merge.
3. The merge creates commit `M` with ordered parents `[base, X]`.
4. A `MainlineIntegrationReceipt` is committed at
   `project_state/mainline_receipts/<M>.json`, binding `M`, `X`, `base`,
   parents, trees, runs, PR, and Decision.
5. On the next push to `main`, `current-merge-validation` looks up
   `project_state/mainline_receipts/<HEAD>.json`.  If `HEAD == M`, the receipt
   is found and validated.  If `HEAD` is a later commit, no receipt exists and
   the gate fails closed until a new receipt is committed.

This preserves `expected_head_sha` and human R2 approval: the receipt is only
created **after** the merge is authorised, and the gate only passes when `HEAD`
exactly matches the recorded merge commit.

## Workflow routing

```
transition mode + pull request / non-main
  -> transition-lint
  -> transition-command-plan
  -> transition-preflight

transition mode + main
  -> historical frozen-baseline invariant (integration-baseline)
  -> current-merge authorization (current-merge-validation)
```

Both checks must pass on `main`.  The historical invariant proves the accepted
PR #9 integration remains present and unchanged.  The current-merge check
proves the current `HEAD` is tied to an accepted current merge receipt.

## Pre-merge Authorization vs post-merge Receipt

Two distinct R2 Decisions govern the lifecycle:

| Stage | Decision | What it authorizes |
|-------|----------|--------------------|
| Pre-merge | `decision_20260724_p1a_current_merge_bound_mainline_validation_v1` | Implement the gate, publish the replacement branch, run exact-head CI. Does NOT authorize merge. `current-merge-validation` intentionally fail-closes on this branch because no receipt exists for the current HEAD. |
| Post-merge | separate R2 merge Decision (future) | Merge the replacement PR AND commit `MainlineIntegrationReceipt` at `project_state/mainline_receipts/<merge_commit_sha>.json` binding the actual merge commit. |

This separation preserves `expected_head_sha` and human R2 approval:

- The receipt is only created **after** the merge is authorised.
- The gate only passes when `HEAD` exactly matches the recorded merge commit.
- A stale receipt cannot validate a later commit because receipts are selected
  deterministically by HEAD sha.

## Supersession of PR #19

PR #19 implemented the historical `integration-baseline` gate but did not bind
the current `main` HEAD to the current merge (Issue #20 blocking finding).
This Decision opens a replacement branch (`codex/p1a-current-merge-validation-v2`)
from `origin/main` rather than mutating PR #19, and combines both gates in a
single coherent implementation. PR #19's audited head
(`38a0a934d92e2cb6eef508b2b32ec580d976b058`) is kept as frozen audit history.
