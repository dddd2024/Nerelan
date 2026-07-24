# Main Integration Baseline

Transition preflight is an execution-authority check for a named engineering
branch. It intentionally rejects a different branch, including `main`. Once an
accepted branch is merged, rerunning that branch check on `main` is therefore
both incorrect and guaranteed to fail.

Mainline validation uses a separate frozen integration receipt. The receipt
records the previous main commit, accepted subject head, merge commit, ordered
parents, expected tree, exact-head successful workflow runs, and the frozen
head of the next dependent PR.

`integration-baseline` fails closed unless:

1. the receipt conforms to `integration_baseline.schema.json`;
2. the previous main, subject, and merge commit objects exist;
3. the merge has exactly the recorded parents in the recorded order;
4. the merge tree, subject tree, and recorded tree are identical;
5. both parents are ancestors of the merge;
6. the merge is an ancestor of the checked-out `HEAD`;
7. all four accepted workflow runs bind the exact subject head.

Pull requests and non-main branches continue to run transition lint, command
plan generation, and transition preflight. Pushes to `main` run transition
lint, command plan generation, and the frozen integration-baseline check.
This preserves branch-scoped execution authority without weakening mainline
ancestry and content verification.
