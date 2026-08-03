# Project Governance Context

Project governance context artifacts make current-state intake deterministic for planning and audit rounds. They live under `project_state/` because they are generated from current evidence and may change every round.

The authority chain remains unchanged:

- `project_state/decision_packet.md` is task authority.
- `project_state/gates/command_plan.json` is command authority.
- `project_state/pytest_result.txt`, gate artifacts, and execution reports remain audit evidence.
- `state_manifest.json`, `current_context_packet.json`, and `workstreams.json` are indexes, not fact-source replacements.

Dynamic facts must not be copied into long-term prompt docs or `.codex-skills/`. Future GPT planning should read the current context packet, then verify claims against the referenced `project_state` files.

## current_context_packet.json freshness and cross-Agent scope

`current_context_packet.json` is a repository-shared index only when read from the same exact commit and verified current. It must be checked for freshness by comparing:

```text
commit SHA
Decision ID
round ID
generated_at
source digest
```

If any freshness field cannot be verified against the current observed state, the packet must be treated as stale and re-read from the current repository state before use.

`current_context_packet.json` does not synchronize ChatGPT, Codex, OpenHands, Claude/Cursor/Trae, or any other product-private memory. It is a generated index over repository and GitHub state, not a bridge between Agent products. Product-private memory remains advisory only and must not be presented as repository fact without a tracked citation. See `docs/architecture/CROSS_AGENT_CONTEXT_CONTRACT.md` for the full layered model and conflict-resolution order.

This layer is compatible with manual GPT audit plus Codex execution because it is file-backed, deterministic, non-dispatching, and validated by `python -m reverse_agent.project_gate project-governance-context --state-dir project_state`.
