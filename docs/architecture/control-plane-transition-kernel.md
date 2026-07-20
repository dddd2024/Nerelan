# Control Plane Transition Kernel

The transition kernel is an independent, fail-closed authorization path for
architecture migration rounds. It evaluates explicit Decision, Git, command,
scope, and operation facts. It does not infer acceptance from the legacy
closeout chain.

## Validation order

1. exact Decision and round identity;
2. `APPROVED` status, active skills, and legal mainline;
3. expected branch, activation base, and Decision ancestry;
4. command-plan identity and explicit command contracts;
5. allowed paths, forbidden paths, and forbidden operations.

The result is deterministic: the same authority and execution envelopes
produce the same checks and blocking reasons. An undeclared command, a command
on the wrong execution surface, or any scope violation blocks the transition.

The kernel never reads `startup_snapshot.json`, `round_baseline.json`, legacy
closeout/final-check/final-seal results, `state_manifest.json`, report-summary
artifacts, or remote-observation mirrors. Those files may exist as compatibility
evidence, but they cannot authorize a transition.

## Compatibility and rollback

Transition mode is opt-in through `decision_contract.transition_kernel_required`.
Legacy Decisions continue through the existing project-gate functions. Rolling
back the transition path means removing the new CLI routing and modules; no
legacy artifact or command needs to be rewritten.

The next bounded round is Workflow transition cutover: it may switch the State
Gate and Decision Preflight workflows to the new CLI only after this kernel is
independently accepted.
