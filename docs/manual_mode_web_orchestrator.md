# Manual Mode Web Orchestrator

The manual-mode orchestrator is a local, deterministic preview of how a Web console can guide work without gaining execution authority.

It preserves three boundaries:

- `project_state/decision_packet.md` remains the decision authority.
- `project_state/gates/command_plan.json` remains the command authority.
- Manual result import is structured evidence only; it never upgrades a claim into real sample verification.

The static console under `frontend/manual_mode_console/` reads fixture data only. It has no build step, network calls, production service, database, queue, scheduler, remote runner, model API call, or external analysis invocation.
