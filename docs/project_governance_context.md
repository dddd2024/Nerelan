# Project Governance Context

Project governance context artifacts make current-state intake deterministic for planning and audit rounds. They live under `project_state/` because they are generated from current evidence and may change every round.

The authority chain remains unchanged:

- `project_state/decision_packet.md` is task authority.
- `project_state/gates/command_plan.json` is command authority.
- `project_state/pytest_result.txt`, gate artifacts, and execution reports remain audit evidence.
- `state_manifest.json`, `current_context_packet.json`, and `workstreams.json` are indexes, not fact-source replacements.

Dynamic facts must not be copied into long-term prompt docs or `.codex-skills/`. Future GPT planning should read the current context packet, then verify claims against the referenced `project_state` files.

This layer is compatible with manual GPT audit plus Codex execution because it is file-backed, deterministic, non-dispatching, and validated by `python -m reverse_agent.project_gate project-governance-context --state-dir project_state`.
