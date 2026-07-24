# Transition Command Authority

Transition commands are machine-readable entries containing the command text,
phase, required flag, expected exit codes, and an execution surface (`local` or
`ci_only`). Command identity is canonicalized only by whitespace; shell syntax
is not evaluated or broadened.

Authorization is fail-closed:

- a command absent from the plan is denied;
- the same text on a different execution surface is denied;
- duplicate command/surface identities are invalid;
- missing expected exit codes or unknown surfaces are invalid.

For the cutover round, the compatibility adapter imports entries from the
existing generated `command_plan.json` and adds the explicit local surface. It
does not scrape commands from Markdown. Future transition Decisions can emit
the same schema directly.

CI-only commands remain distinct from commands approved for local execution.
This prevents a remote-only operation from becoming locally executable merely
because its text appears in an evidence document.

The Workflow cutover contract is the named `workflow_contract` JSON block in
the active Decision. It separately reviews the remote install, mode detection,
transition authority, and focused-test commands. Local Codex execution remains
bound to the generated local command plan.
