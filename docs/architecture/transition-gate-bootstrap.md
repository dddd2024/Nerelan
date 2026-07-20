# Transition Gate Bootstrap

The transition gate now derives its command plan, required branch, activation base, path scope, and forbidden operations from the active structured Decision contract.

`transition-command-plan` deterministically projects `bootstrap_exception_commands` into the current `command_plan.json`. `transition-lint` recomputes that projection and blocks identity drift or manual command changes. `transition-preflight` reads the active Decision scope and audits only changes after the Decision commit plus current staged and unstaged changes.

Malformed or incomplete contracts fail closed. Legacy-mode dispatch behavior is unchanged.
