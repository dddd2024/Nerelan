# Legacy Control Plane Boundary

The legacy control plane remains the authority for existing Decisions. Its
startup snapshot, round baseline, report synthesis, final checks, closeout,
state mirrors, and CI observation artifacts are preserved without behavioral
changes in this round.

The transition path is separate. `project_gate.py` exposes thin routing for
`transition-lint`, `transition-command-plan`, and `transition-preflight`; the
validation implementation lives under `reverse_agent.control_plane`.

The compatibility adapter has only three responsibilities:

- identify explicit transition Decisions;
- convert the existing machine-generated command plan into typed command
  contracts;
- dispatch an explicitly selected transition validator while leaving the
  legacy validator unchanged for every other Decision.

It does not copy legacy gate logic or treat legacy acceptance artifacts as
transition prerequisites.

## Workflow boundary

Valid Decisions without `transition_kernel_required=true` produce the `legacy`
mode token. Governance workflows retain every legacy step, command, and order,
with explicit legacy-only conditions. Transition Decisions run transition lint,
command-plan validation, and transition preflight instead; the legacy acceptance
chain is skipped. Malformed Decisions do not fall back to either path.

The exact rollback is to restore unconditional legacy workflow routing while
leaving the transition kernel and mode detector installed.
