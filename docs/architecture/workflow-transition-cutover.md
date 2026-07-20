# Workflow Transition Cutover

The CI workflow keeps its existing checkout, Python setup, import check, and
focused-test order. It installs `.[test]` so a clean runner receives the optional
pytest dependency without moving test tooling into runtime dependencies.

State Gate and Decision Preflight fetch full Git history and run
`control-plane-mode`. A valid explicit `transition_kernel_required=true`
contract selects the transition path:

1. transition lint;
2. transition command-plan validation;
3. transition preflight;
4. the existing focused pytest step.

A valid absent or false flag selects the preserved legacy path. Every legacy
step retains its command and order and is guarded by the legacy condition. The
transition steps use the transition condition. Therefore one run cannot execute
both authority chains. Evidence upload remains unconditional with `if: always()`.

Malformed Decision metadata, missing named blocks, unreadable files, or a
non-boolean transition flag fail before either path is selected. Mode stdout is
one newline-terminated token so GitHub output capture is deterministic.

Rollback restores the previous workflow routing and base editable-install
command while leaving the transition kernel modules intact. The next bounded
workstream is independent audit and hardening; it is identified here but not
started by this round.
