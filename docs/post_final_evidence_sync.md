# Post-Final Evidence Sync

`post-final-evidence-sync` is a local project gate that keeps the current context packet aligned with final-check evidence for the active decision round.

The gate reads `project_state/decision_packet.md`, `project_state/gates/final_gate_result.json`, and `project_state/context/current_context_packet.json`. It may refresh the context packet through `reverse_agent.project_context_builder`, then writes:

- `project_state/gates/post_final_evidence_sync_result.json`
- `project_state/gates/post_final_evidence_sync_snapshot.json`
- `project_state/context/current_context_packet.json`

The gate is intentionally non-dispatching. It does not run agents, contact external model services, mutate remote state, execute reverse samples, create branches, push commits, open pull requests, or perform cleanup/archive apply actions.

Before final-check has produced current-round evidence, the gate can pass with explicit pre-final or stale-final warnings. After final-check runs for the current decision, the context packet must report current final-check status and the sync artifact must remain safety-clean.
