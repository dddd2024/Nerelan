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
Legacy Decisions continue through the existing project-gate functions. The
`control-plane-mode` command reads only the named Decision metadata and contract
blocks and prints exactly `legacy` or `transition`. Missing or malformed blocks,
or a non-boolean transition flag, fail nonzero instead of silently choosing a
pipeline.

State Gate and Decision Preflight use that token to run exactly one authority
path. Rolling back the Workflow cutover means restoring their previous routing
while leaving the kernel modules intact; no legacy artifact or command needs to
be rewritten.

The next bounded workstream is independent audit and hardening of the accepted
transition surface. It is not started by this cutover round.
