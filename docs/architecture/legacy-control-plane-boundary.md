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
transition prerequisites. No workflow is changed during the kernel round.
