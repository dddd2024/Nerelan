```json decision_meta
{
  "schema_version": 1,
  "decision_id": "decision_20260701_codex_prompt_packet_v1",
  "round_id": "round_20260701_codex_prompt_packet_v1",
  "based_on_state_build_id": "state_20260618_134029_d6bd033d2532",
  "based_on_state_digest": "d6bd033d25324345cfd8ada0ac65db42bc86eb5017f3ffc92906fcd8b71cacb5",
  "status": "APPROVED",
  "mainline": "engineering_branch",
  "skill_profiles": ["reverse-agent-iteration@v2"]
}
```

```json decision_contract
{
  "previous_decision_id": "decision_20260701_current_handoff_packet_v1",
  "previous_round_id": "round_20260701_current_handoff_packet_v1",
  "previous_audit_outcome": "ACCEPTED",
  "phase_label": "phase_2_27_codex_prompt_packet",
  "primary_goal": "Create a current, non-dispatching Codex execution prompt packet derived from current_handoff_packet.json so a human operator can copy a bounded local execution prompt without reading scattered state files.",
  "command_plan_authority_required": true,
  "accepted_requires_current_codex_prompt_packet": true,
  "accepted_requires_prompt_packet_derived_from_current_handoff": true,
  "accepted_requires_no_runner_or_dispatcher": true,
  "accepted_requires_existing_current_handoff_not_regressed": true,
  "accepted_requires_existing_audit_inventory_not_regressed": true,
  "accepted_requires_existing_audit_readiness_not_regressed": true,
  "allowed_source_files": [
    "reverse_agent/project_gate.py",
    "tests/test_project_gate.py",
    "tests/test_project_reports.py"
  ],
  "preserve_only_files": [
    "reverse_agent/project_agent_runner.py",
    "reverse_agent/project_control_plane.py",
    "reverse_agent/project_jobs.py",
    "reverse_agent/project_runner_contract.py",
    "reverse_agent/project_audits.py",
    "reverse_agent/project_rounds.py",
    "reverse_agent/project_state.py",
    "tests/test_project_agent_runner.py",
    "tests/test_project_control_plane.py",
    "tests/test_project_state.py",
    "docs/prompts/*",
    ".github/workflows/*"
  ],
  "allowed_generated_or_updated_artifacts": [
    "project_state/codex_execution_report.md",
    "project_state/execution_report.md",
    "project_state/pytest_result.txt",
    "project_state/gates/*.json",
    "project_state/rounds/round_20260701_codex_prompt_packet_v1/*"
  ],
  "forbidden_mutated_paths": [
    "project_state/current_state.json",
    "project_state/task_packet.json",
    "project_state/artifact_index.json",
    "project_state/negative_results.json",
    ".codex-skills/registry.json",
    "docs/prompts/*",
    ".github/workflows/*",
    "solve_reports/*"
  ]
}
```

# DECISION_PACKET

## 1. Goal

Implement **Codex Prompt Packet v1**.

This round advances the engineering branch from a current machine-readable handoff packet to a bounded, copyable Codex execution prompt packet.

Primary objective:

1. Produce `project_state/gates/codex_prompt_packet.json` as a current, non-dispatching prompt packet derived from `project_state/gates/current_handoff_packet.json`.
2. The prompt packet must contain a complete local execution prompt that a human operator can copy into Codex or another local executor.
3. The prompt must preserve the project contract: `F:\reverse-agent`, startup checks, `decision_packet.md` as the only decision authority, `command-plan` as the only command execution authority, no remote mutation, allowed scope, forbidden scope, required tests, required artifacts, stop conditions, and report-writing requirements.
4. The prompt packet must be evidence-only. It must not execute commands, call model APIs, create jobs, schedule work, dispatch Codex, mutate remote state, or introduce a runner.
5. The prompt packet must be generated from current evidence and must reject stale or mismatched handoff/readiness/audit inventory data.

Target outcome:

- `codex_execution_report.md` status: `SUCCESS`.
- acceptance recommendation: `ACCEPTED`.
- `pytest_result.txt` status: `PASSED`.
- `final-check`: `PASSED`.
- `run-closeout`: `PASSED`.
- `close-round`: `CLOSED`.
- `current_handoff_packet.json`: remains current, evidence-only, non-dispatching, and command-plan aligned.
- `codex_prompt_packet.json`: current decision ID, current round ID, current report ID, derived from current handoff packet, copyable prompt present, evidence-only, non-executable, non-dispatching.
- `audit_inventory_result.json`: remains current and validated.
- `audit_readiness_packet.json`: remains `READY`, `PASSED`, `ACCEPTED`, `no_action_required`.
- No runner, dispatcher, scheduler, Web/API layer, database, CI workflow, or external integration changes.

## 2. Current Evidence

Mainline: `engineering_branch`.

`project_state/decision_packet.md` controls this round. `project_state/task_packet.json` remains background only.

Previous round: `decision_20260701_current_handoff_packet_v1` / `round_20260701_current_handoff_packet_v1`.

Previous audit outcome: `ACCEPTED`.

Accepted evidence from previous round:

- `current_handoff_packet.json` exists with current decision/round/report IDs.
- It identifies `decision_packet.md` as decision authority.
- It identifies `command_plan.json` as command execution authority and states the packet cannot override command-plan.
- It includes startup contract, allowed scope, forbidden scope, required tests, expected artifacts, artifact freshness policy, audit inventory status, audit readiness status, closeout expectations, stop conditions, and historical handoff artifacts inspected.
- It is evidence-only, non-executable, non-dispatching, and non-mutating.
- The prior readiness mismatch was repaired: handoff readiness now matches `audit_readiness_packet.json` with `READY` / `ACCEPTED` / `no_action_required`.
- `audit_inventory_result.json` is current and includes four audit files.
- `audit_readiness_packet.json` is current and `READY` / `ACCEPTED` / `no_action_required`.
- `final_gate_result.json` passed with no blocking reasons or warnings.
- `run_closeout_result.json` passed and close-round was `CLOSED`.

Engineering gap now being addressed:

- `current_handoff_packet.json` is structured evidence, but a human still needs to manually convert it into a safe Codex execution prompt.
- This round should generate that prompt as a controlled artifact without implementing execution or dispatch.
- The prompt packet should reduce copy/paste mistakes while preserving the command-plan authority boundary.

Artifact freshness policy:

- Current-round gate artifacts must carry `decision_20260701_codex_prompt_packet_v1` and `round_20260701_codex_prompt_packet_v1`.
- Historical artifacts may be referenced only as historical/nonblocking unless rebuilt with current IDs in this round.
- `codex_prompt_packet.json` is generated state, not a long-term skill.
- The prompt packet may include a prompt text string, but it must not write to `docs/prompts/*`.

Command-plan policy:

- `command-plan` remains the command authority.
- Codex may only execute commands authorized by command-plan.
- The generated prompt may tell the local executor to run command-plan and then obey it, but the prompt itself does not authorize commands.
- Existing execution order policy may remain `coverage_expected_exit_not_strict_wall_clock`, but it must remain explicit and final-check validated.
- Startup order remains strict: five startup commands, then `startup-snapshot` as the first project gate.

## 3. Do Not Do

Do not create or modify a real runner, dispatcher, scheduler, service, queue, database, Web/API layer, CI workflow, or external integration.

Do not modify these preserve-only modules unless a future decision explicitly authorizes that work:

- `reverse_agent/project_agent_runner.py`
- `reverse_agent/project_control_plane.py`
- `reverse_agent/project_jobs.py`
- `reverse_agent/project_runner_contract.py`
- `reverse_agent/project_audits.py`
- `reverse_agent/project_rounds.py`
- `reverse_agent/project_state.py`

Do not write or modify `docs/prompts/*`.

Do not put this prompt into `.codex-skills/`; it is a current dynamic artifact, not a long-term stable skill.

Do not perform reverse solving, sample solving, runtime probing, dynamic debugging, emulator work, IDA/Ghidra/OllyDbg execution, or heavy historical scanning.

Do not read full `solve_reports/`, full historical round directories, or full `PROJECT_PROGRESS_LOG.txt`.

Do not modify:

- `project_state/current_state.json`
- `project_state/task_packet.json`
- `project_state/artifact_index.json`
- `project_state/negative_results.json`
- `.codex-skills/registry.json`
- `.github/workflows/*`
- `docs/prompts/*`

Do not make the prompt packet executable. It must not include fields implying it can launch commands, dispatch Codex, schedule work, call APIs, or mutate state.

Do not weaken handoff, audit inventory, audit readiness, final-check, command-plan, startup, or closeout checks merely to produce a clean prompt packet.

Do not commit, push, create PRs, switch branches, rebase, merge, or modify remote state unless the user explicitly asks the executor to upload results.

## 4. Files To Inspect

Read first:

1. `project_state/task_packet.json`
2. `project_state/current_state.json`
3. `project_state/artifact_index.json`
4. `project_state/negative_results.json`
5. `project_state/decision_packet.md`
6. `project_state/codex_execution_report.md`
7. `project_state/execution_report.md`
8. `project_state/pytest_result.txt`
9. `.codex-skills/registry.json`

Inspect bounded current gate artifacts:

1. `project_state/gates/current_handoff_packet.json`
2. `project_state/gates/command_plan.json`
3. `project_state/gates/final_gate_result.json`
4. `project_state/gates/report_summary_synthesis.json`
5. `project_state/gates/audit_inventory_result.json`
6. `project_state/gates/audit_readiness_packet.json`
7. `project_state/gates/execution_log.json`
8. `project_state/gates/run_closeout_result.json`
9. `project_state/gates/round_delta_summary.json`

Inspect existing handoff/runner artifacts only as bounded historical evidence:

1. `project_state/gates/agent_runner_handoff_bundle.json` if present
2. `project_state/gates/agent_runner_handoff_validation.json` if present
3. `project_state/gates/agent_runner_dry_run_result.json` if present
4. `project_state/gates/runner_contract_result.json` if present

Inspect implementation and tests:

1. `reverse_agent/project_gate.py`
2. `tests/test_project_gate.py`
3. `tests/test_project_reports.py`

Read-only context if needed:

1. `reverse_agent/project_agent_runner.py`
2. `reverse_agent/project_runner_contract.py`
3. `tests/test_project_agent_runner.py`

Do not scan full `solve_reports/`, full historical round directories, or full `PROJECT_PROGRESS_LOG.txt`.

## 5. Required Audit

The execution report must answer these items with direct evidence:

1. Did startup commands confirm `F:\reverse-agent`, repo root, and clean `git status --short` before any project gate?
2. Was `startup-snapshot` still the immediate sixth command and first project gate?
3. Did `decision_meta` remain valid and APPROVED on `engineering_branch`?
4. Did `reverse-agent-iteration@v2` remain active in `.codex-skills/registry.json`?
5. Did Codex treat `decision_packet.md` as authority and `task_packet.json` as background only?
6. Did implementation stay within allowed source/test files?
7. Were preserve-only and forbidden files not modified?
8. Did implementation avoid creating a runner, dispatcher, scheduler, service, Web/API layer, CI workflow, queue, database, or external integration?
9. Did Codex inspect `current_handoff_packet.json` before generating the prompt packet?
10. Does `codex_prompt_packet.json` exist with current decision ID, round ID, and report ID?
11. Does the prompt packet declare it is derived from current `current_handoff_packet.json`?
12. Does the prompt packet include a complete copyable prompt string or structured prompt sections?
13. Does the prompt tell the executor to start in `F:\reverse-agent` and run the five startup commands before project gates?
14. Does the prompt state that `decision_packet.md` is the only decision authority and `task_packet.json` is background only?
15. Does the prompt state that `command-plan` is the only command execution authority?
16. Does the prompt forbid commands not authorized by command-plan?
17. Does the prompt preserve allowed source/test scope and forbidden path scope?
18. Does the prompt include required pytest commands, including `tests/test_project_reports.py`?
19. Does the prompt require `pytest_result.txt` and `codex_execution_report.md` updates?
20. Does the prompt require audit inventory, audit readiness, current handoff packet, prompt packet, final-check, run-closeout, and post-closeout final-check evidence?
21. Is the prompt packet evidence-only, non-executable, non-dispatching, and non-mutating?
22. Does final-check validate prompt packet freshness and derivation from current handoff packet?
23. Does final-check reject stale prompt packet IDs when current prompt packet is required?
24. Does final-check reject a prompt packet that claims authority over command-plan or permits unauthorized commands?
25. Does final-check reject a prompt packet that omits startup, decision authority, command-plan authority, required tests, or forbidden scope?
26. Did audit inventory remain current and validated?
27. Did audit readiness remain `READY`, `PASSED`, `ACCEPTED`, and `no_action_required`?
28. Did final report summary match pytest, changed files, generated artifacts, decision ID, round ID, current handoff status, prompt packet status, audit inventory status, and audit readiness status?

## 6. Implementation Scope

Allowed source/test changes:

- `reverse_agent/project_gate.py`
- `tests/test_project_gate.py`
- `tests/test_project_reports.py`

Allowed generated or updated artifacts:

- `project_state/codex_execution_report.md`
- `project_state/execution_report.md`
- `project_state/pytest_result.txt`
- `project_state/gates/*.json`
- `project_state/rounds/round_20260701_codex_prompt_packet_v1/*`

Required behavior:

1. Add or repair a bounded project gate that writes `project_state/gates/codex_prompt_packet.json`.
2. If an equivalent existing prompt packet generator already exists, reuse or extend it instead of creating a duplicate concept.
3. `codex_prompt_packet.json` must include:
   - schema_version;
   - artifact_name;
   - gate_name;
   - gate_status;
   - decision_id;
   - round_id;
   - report_id;
   - mainline;
   - generated_at;
   - source_handoff_packet;
   - source_handoff_digest or equivalent content hash if available;
   - prompt_title;
   - prompt_text or prompt_sections;
   - startup_contract;
   - decision_authority;
   - command_plan_authority;
   - allowed_scope;
   - forbidden_scope;
   - required_tests;
   - required_artifacts;
   - required_report_updates;
   - stop_conditions;
   - evidence_only;
   - executable;
   - can_execute;
   - mutates_state;
   - can_dispatch;
   - remote_mutation_allowed;
   - warnings;
   - errors.
4. The prompt text must be deterministic from current decision/handoff evidence and must not include secrets, tokens, credentials, bulky solve report content, runtime metrics, or candidate data.
5. The prompt packet must not write to `docs/prompts/*` or `.codex-skills/*`.
6. final-check must validate the prompt packet when the decision contract requires it.
7. command-plan must include the prompt packet gate if the gate is required for acceptance.
8. report-summary synthesis must include current prompt packet status in generated artifacts and summary matching.
9. Existing current handoff behavior must not regress.
10. Existing audit inventory behavior must not regress.
11. Existing audit readiness behavior must not regress.
12. Existing command-plan authority and startup/closeout checks must not regress.

## 7. Tests

Startup sequence must be recorded first:

```powershell
Set-Location F:\reverse-agent
Get-Location
Test-Path F:\reverse-agent
git rev-parse --show-toplevel
git status --short
python -m reverse_agent.project_gate startup-snapshot --state-dir project_state
```

Required focused pytest command:

```powershell
python -m pytest tests/test_project_gate.py tests/test_project_reports.py tests/test_project_state.py -q
```

Required gate commands must be authorized by command-plan. At minimum command-plan should cover:

```powershell
python -m reverse_agent.project_gate command-plan --state-dir project_state
python -m reverse_agent.project_gate command-plan --state-dir project_state --json
python -m reverse_agent.project_gate preflight --state-dir project_state --allow-consumed
python -m reverse_agent.project_gate audit-inventory --state-dir project_state
python -m reverse_agent.project_gate audit-readiness-packet --state-dir project_state
python -m reverse_agent.project_gate current-handoff-packet --state-dir project_state
python -m reverse_agent.project_gate codex-prompt-packet --state-dir project_state
python -m reverse_agent.project_gate report-summary --state-dir project_state
python -m reverse_agent.project_gate execution-log --state-dir project_state
python -m reverse_agent.project_gate final-check --state-dir project_state
python -m reverse_agent.project_gate run-closeout --state-dir project_state --round-id round_20260701_codex_prompt_packet_v1
python -m reverse_agent.project_gate final-check --state-dir project_state
```

If the exact CLI name differs, use the existing project_gate subcommand and record the actual command in `pytest_result.txt`.

Required regression coverage:

- stale prompt packet IDs fail final-check when current prompt packet is required;
- prompt packet missing current handoff source fails;
- prompt packet derived from stale handoff fails;
- prompt packet missing startup contract fails;
- prompt packet missing decision authority fails;
- prompt packet missing command-plan authority fails;
- prompt packet claiming it can override command-plan fails;
- prompt packet allowing unauthorized commands fails;
- prompt packet missing required pytest with `tests/test_project_reports.py` fails;
- prompt packet missing forbidden scope fails;
- prompt packet executable/dispatching/mutating fields fail;
- current valid prompt packet passes;
- current handoff remains current and valid;
- audit inventory remains current and validated;
- audit readiness remains READY/PASSED/ACCEPTED/no_action_required;
- command-plan execution_order_policy remains explicit;
- final-check and closeout exit 0.

Write all top-level commands, exit codes, and pytest pass/fail counts to `project_state/pytest_result.txt`.

## 8. Stop Conditions

Stop with `BLOCKED` if:

- startup path or repo root is wrong;
- startup `git status --short` has dirty source/test files outside allowed baseline;
- startup-snapshot is not immediate after startup status commands;
- any project gate runs before startup-snapshot;
- decision metadata or skill profile is invalid;
- command-plan is missing or unsafe;
- implementation requires preserve-only or forbidden paths;
- implementation requires a real runner, dispatcher, scheduler, Web/API layer, database, workflow, external service, or remote state changes.

Stop with `REWORK_REQUIRED` if:

- `codex_prompt_packet.json` is missing, stale, malformed, or not current-round aligned;
- prompt packet is executable, dispatching, mutating, or claims authority over command-plan;
- prompt packet omits current handoff source or derives from stale handoff data;
- prompt packet omits startup contract, decision authority, command-plan authority, required tests, allowed scope, forbidden scope, report update requirements, or stop conditions;
- prompt packet allows unauthorized commands or remote mutation;
- final-check does not validate prompt packet freshness, derivation, and evidence-only fields;
- final-check accepts stale prompt IDs when current prompt packet is required;
- command-plan omits the required prompt packet gate;
- current handoff packet regresses or becomes stale;
- audit inventory regresses or becomes stale;
- audit readiness regresses from READY/PASSED/ACCEPTED/no_action_required;
- status-policy false warning regresses;
- focused pytest omits `tests/test_project_reports.py`;
- pytest, report-summary, execution-log, audit-inventory, audit-readiness, current-handoff-packet, codex-prompt-packet, final-check, run-closeout, or post-closeout final-check fails;
- close-round is not CLOSED;
- closeout nested failure scan finds active failures;
- forbidden files are modified.
