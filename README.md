# Reverse Agent

Reverse Agent is a Windows GUI reverse-engineering assistant for CTF / RE scenarios.

## Engineering Round Closeout

For the default engineering-round closeout workflow, see [docs/run_closeout.md](docs/run_closeout.md).

Key points:

- `project_state/decision_packet.md` is the sole execution authority for each round.
- `project_state/task_packet.json` is advisory only.
- `run-closeout` is the default closeout command after implementation work.
- `command-plan` recommends `run-closeout` when the decision contract requires it, with manual fallback for unsupported cases.
- Required Audit answers must be substantive for `SUCCESS` or `ACCEPTED` reports.
- Live `project_state build` must not be run when the active decision forbids it.
