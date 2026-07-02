```json decision_meta
{
  "schema_version": 1,
  "decision_id": "decision_20260701_local_execution_loop_foundation_v1",
  "round_id": "round_20260701_local_execution_loop_foundation_v1",
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
  "phase_label": "phase_2_27_local_execution_loop_foundation",
  "primary_goal": "Create a bounded local execution loop foundation that packages executor handoff, copyable Codex prompt, and audit precheck into current evidence-only gate artifacts without creating a runner or dispatcher.",
  "command_plan_authority_required": true,
  "accepted_requires_local_execution_bundle": true,
  "accepted_requires_codex_prompt_packet": true,
  "accepted_requires_audit_precheck": true,
  "accepted_requires_current_handoff_not_regressed": true,
  "accepted_requires_existing_audit_inventory_not_regressed": true,
  "accepted_requires_existing_audit_readiness_not_regressed": true,
  "accepted_requires_no_runner_or_dispatcher": true,
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
    "project_state/rounds/round_20260701_local_execution_loop_foundation_v1/*"
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

Implement **Local Execution Loop Foundation v1**.

This round is an engineering-branch step that moves the project from scattered, individually valid state artifacts toward a reusable local execution loop foundation.

Primary objective:

1. Produce `project_state/gates/local_execution_bundle.json` as the current, evidence-only bundle for a local human/Codex execution round.
2. Produce `project_state/gates/codex_prompt_packet.json` as a copyable local execution prompt derived from the current bundle and current handoff evidence.
3. Produce `project_state/gates/audit_precheck_result.json` as a bounded pre-audit gate that tells GPT whether Codex output is structurally ready for final audit or should be rejected before manual audit.
4. Keep `project_state/gates/current_handoff_packet.json` current and validated as the lower-level handoff artifact.
5. Preserve command-plan authority: the bundle and prompt may summarize allowed commands, but only `command-plan` authorizes execution.
6. Do not implement a runner, dispatcher, scheduler, service, queue, Web/API layer, database, GitHub Actions workflow, API caller, or remote automation.

Target outcome:

- `codex_execution_report.md` status: `SUCCESS`.
- acceptance recommendation: `ACCEPTED`.
- `pytest_result.txt` status: `PASSED`.
- `final-check`: `PASSED`.
- `run-closeout`: `PASSED`.
- `close-round`: `CLOSED`.
- `local_execution_bundle.json`: current decision ID, current round ID, current report ID, command-plan aligned, evidence-only, non-dispatching, non-mutating.
- `codex_prompt_packet.json`: current decision ID, current round ID, current report ID, derived from `local_execution_bundle.json` and `current_handoff_packet.json`, copyable prompt present, non-executable.
- `audit_precheck_result.json`: current decision ID, current round ID, current report ID, checks report/pytest/final-check/closeout/readiness/bundle consistency, and returns `READY_FOR_GPT_AUDIT` or `DO_NOT_ACCEPT`.
- `current_handoff_packet.json`: remains current, evidence-only, non-dispatching, and command-plan aligned.
- `audit_inventory_result.json`: remains current and validated.
- `audit_readiness_packet.json`: remains `READY`, `PASSED`, `ACCEPTED`, `no_action_required`.

## 2. Current Evidence

Mainline: `engineering_branch`.

`project_state/decision_packet.md` controls this round. `project_state/task_packet.json` remains background only.

Previous accepted round: `decision_20260701_current_handoff_packet_v1` / `round_20260701_current_handoff_packet_v1`.

Previous audit outcome: `ACCEPTED`.

Accepted evidence from previous round:

- `current_handoff_packet.json` exists with current decision/round/report IDs for the previous round.
- It identifies `decision_packet.md` as decision authority.
- It identifies `command_plan.json` as command execution authority and states the packet cannot override command-plan.
- It includes startup contract, allowed scope, forbidden scope, required tests, expected artifacts, artifact freshness policy, audit inventory status, audit readiness status, closeout expectations, stop conditions, and historical handoff artifacts inspected.
- It is evidence-only, non-executable, non-dispatching, and non-mutating.
- The earlier readiness mismatch was repaired: handoff readiness matched `audit_readiness_packet.json` with `READY` / `ACCEPTED` / `no_action_required`.
- `audit_inventory_result.json` was current and included four audit files.
- `audit_readiness_packet.json` was current and `READY` / `ACCEPTED` / `no_action_required`.
- `final_gate_result.json` passed with no blocking reasons or warnings.
- `run_closeout_result.json` passed and close-round was `CLOSED`.

Engineering gap now being addressed:

- The current project has decision, handoff, command-plan, report, pytest, final-check, and closeout artifacts, but local execution still requires an operator to manually reconstruct the workflow from multiple files.
- A larger engineering step should package the local execution contract and pre-audit checks as current gate artifacts.
- This must remain a local/manual foundation: no automated dispatch, no API execution, no new runner.

Artifact freshness policy:

- Current-round gate artifacts must carry `decision_20260701_local_execution_loop_foundation_v1` and `round_20260701_local_execution_loop_foundation_v1`.
- Historical artifacts may be referenced only as historical/nonblocking unless rebuilt with current IDs in this round.
- `local_execution_bundle.json`, `codex_prompt_packet.json`, and `audit_precheck_result.json` are generated state artifacts, not long-term skills.
- Dynamic prompts and run-specific facts must not be written to `.codex-skills/` or `docs/prompts/*`.

Command-plan policy:

- `command-plan` remains the only command execution authority.
- Codex may only execute commands authorized by `command-plan.commands`.
- `command-plan.omitted_commands` must not be executed.
- The local execution bundle and prompt packet may summarize commands, but cannot authorize commands.
- Existing execution order policy may remain `coverage_expected_exit_not_strict_wall_clock`, but it must stay explicit and final-check validated.
- Startup order remains strict: five startup commands, then `startup-snapshot` as the first project gate.

## 3. Do Not Do

Do not create or modify a real runner, dispatcher, scheduler, service, queue, database, Web/API layer, CI workflow, external integration, API caller, remote executor, or remote automation.

Do not modify these preserve-only modules unless a future decision explicitly authorizes that work:

- `reverse_agent/project_agent_runner.py`
- `reverse_agent/project_control_plane.py`
- `reverse_agent/project_jobs.py`
- `reverse_agent/project_runner_contract.py`
- `reverse_agent/project_audits.py`
- `reverse_agent/project_rounds.py`
- `reverse_agent/project_state.py`

Do not write or modify `docs/prompts/*`.

Do not put local execution bundle facts, prompt text, artifact freshness, runtime metrics, or round-specific conclusions into `.codex-skills/`.

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

Do not make any of the new artifacts executable. They must not include fields implying they can launch commands, dispatch Codex, schedule work, call APIs, or mutate local or remote state.

Do not weaken current handoff, audit inventory, audit readiness, final-check, command-plan, startup, report-summary, execution-log, or closeout checks merely to produce clean new artifacts.

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
5. `project_state/gates/execute_decision_result.json` if present
6. `project_state/gates/run_round_result.json` if present

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
8. Did implementation avoid creating a runner, dispatcher, scheduler, service, Web/API layer, CI workflow, queue, database, external integration, API caller, or remote automation?
9. Did Codex inspect the current handoff, command-plan, audit inventory, audit readiness, final-check, and closeout artifacts before implementing the bundle?
10. Does `local_execution_bundle.json` exist with current decision ID, round ID, and report ID?
11. Does the bundle declare `decision_packet.md` as the decision authority and `task_packet.json` as background only?
12. Does the bundle declare `command_plan.json` as the only command execution authority?
13. Does the bundle include startup contract and startup-snapshot-first rule?
14. Does the bundle include allowed scope, forbidden scope, required tests, required artifacts, report update requirements, and stop conditions?
15. Does the bundle reference `current_handoff_packet.json` and `codex_prompt_packet.json`?
16. Is the bundle evidence-only, non-executable, non-dispatching, and non-mutating?
17. Does `codex_prompt_packet.json` exist with current decision ID, round ID, and report ID?
18. Is the prompt packet derived from current `local_execution_bundle.json` and current `current_handoff_packet.json`?
19. Does the prompt packet include a complete copyable prompt or structured prompt sections?
20. Does the prompt preserve `F:\reverse-agent`, startup checks, decision authority, task_packet background status, command-plan authority, allowed scope, forbidden scope, required tests, pytest_result writing, codex_execution_report writing, and no-push/no-commit rules?
21. Does `audit_precheck_result.json` exist with current decision ID, round ID, and report ID?
22. Does audit precheck validate report/decision/round matching, pytest_result presence, pytest command coverage, final-check status, run-closeout status, close-round status, audit readiness, current handoff, local execution bundle, and prompt packet status?
23. Does audit precheck return `READY_FOR_GPT_AUDIT` only when required evidence is present and aligned?
24. Does audit precheck return `DO_NOT_ACCEPT` or equivalent blocking state when report, pytest, ID alignment, final-check, closeout, readiness, bundle, or prompt packet evidence is missing or failed?
25. Does final-check validate local execution bundle freshness and evidence-only fields?
26. Does final-check validate prompt packet freshness and derivation from the current bundle/handoff?
27. Does final-check validate audit precheck status and recommendation?
28. Did final report summary match pytest, changed files, generated artifacts, decision ID, round ID, current handoff status, local execution bundle status, prompt packet status, audit precheck status, audit inventory status, and audit readiness status?

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
- `project_state/rounds/round_20260701_local_execution_loop_foundation_v1/*`

Required behavior:

1. Add or repair a bounded project gate that writes `project_state/gates/local_execution_bundle.json`.
2. Add or repair a bounded project gate that writes `project_state/gates/codex_prompt_packet.json` as part of the local execution loop foundation.
3. Add or repair a bounded project gate that writes `project_state/gates/audit_precheck_result.json`.
4. If equivalent existing generators already exist, reuse or extend them instead of creating duplicate concepts.
5. `local_execution_bundle.json` must include:
   - schema_version;
   - artifact_name;
   - gate_name;
   - gate_status;
   - decision_id;
   - round_id;
   - report_id;
   - mainline;
   - generated_at;
   - decision_authority;
   - command_plan_authority;
   - startup_contract;
   - allowed_scope;
   - forbidden_scope;
   - required_commands_summary;
   - required_tests;
   - required_artifacts;
   - required_report_updates;
   - current_handoff_packet;
   - codex_prompt_packet;
   - audit_precheck_result;
   - audit_inventory_status;
   - audit_readiness_status;
   - closeout_expectations;
   - stop_conditions;
   - evidence_only;
   - executable;
   - can_execute;
   - can_dispatch;
   - mutates_state;
   - remote_mutation_allowed;
   - warnings;
   - errors.
6. `codex_prompt_packet.json` must include a complete prompt or structured prompt sections that are deterministic from current bundle/handoff/decision evidence.
7. `audit_precheck_result.json` must include:
   - schema_version;
   - artifact_name;
   - gate_name;
   - gate_status;
   - decision_id;
   - round_id;
   - report_id;
   - checks;
   - audit_recommendation;
   - blocking_reasons;
   - warnings;
   - evidence_only;
   - executable;
   - can_execute;
   - mutates_state.
8. `audit_precheck_result.json.audit_recommendation` must use explicit values such as `READY_FOR_GPT_AUDIT` and `DO_NOT_ACCEPT`.
9. The new artifacts must not contain secrets, tokens, credentials, bulky solve report content, runtime metrics, or candidate data.
10. The new artifacts must not write to `docs/prompts/*` or `.codex-skills/*`.
11. final-check must validate the bundle, prompt packet, and audit precheck when this decision contract requires them.
12. command-plan must include the new required gates if they are required for acceptance.
13. report-summary synthesis must include the new artifacts in generated artifacts and summary matching.
14. Existing current handoff behavior must not regress.
15. Existing audit inventory behavior must not regress.
16. Existing audit readiness behavior must not regress.
17. Existing command-plan authority, startup checks, pytest evidence, report-summary, execution-log, final-check, closeout, and archive behavior must not regress.

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
python -m reverse_agent.project_gate local-execution-bundle --state-dir project_state
python -m reverse_agent.project_gate audit-precheck --state-dir project_state
python -m reverse_agent.project_gate report-summary --state-dir project_state
python -m reverse_agent.project_gate execution-log --state-dir project_state
python -m reverse_agent.project_gate final-check --state-dir project_state
python -m reverse_agent.project_gate run-closeout --state-dir project_state --round-id round_20260701_local_execution_loop_foundation_v1
python -m reverse_agent.project_gate final-check --state-dir project_state
```

If exact CLI names differ, use the existing project_gate subcommands and record the actual commands in `project_state/pytest_result.txt`.

Required regression coverage:

- stale local execution bundle IDs fail final-check when current bundle is required;
- local execution bundle missing decision authority fails;
- local execution bundle missing command-plan authority fails;
- local execution bundle claiming it can execute, dispatch, mutate state, or override command-plan fails;
- local execution bundle missing startup contract, allowed scope, forbidden scope, required tests, report update requirements, or stop conditions fails;
- stale prompt packet IDs fail final-check when current prompt packet is required;
- prompt packet missing current bundle or current handoff source fails;
- prompt packet derived from stale bundle/handoff fails;
- prompt packet claiming it can override command-plan or allow unauthorized commands fails;
- prompt packet missing required pytest with `tests/test_project_reports.py` fails;
- audit precheck missing report, pytest_result, final-check, closeout, readiness, bundle, prompt, or ID alignment returns `DO_NOT_ACCEPT` or blocking state;
- audit precheck returns `READY_FOR_GPT_AUDIT` only when all required evidence is present and aligned;
- current valid bundle, prompt packet, and audit precheck pass;
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
- implementation requires a real runner, dispatcher, scheduler, Web/API layer, database, workflow, external service, API caller, remote executor, or remote state changes.

Stop with `REWORK_REQUIRED` if:

- `local_execution_bundle.json` is missing, stale, malformed, or not current-round aligned;
- local execution bundle is executable, dispatching, mutating, or claims authority over command-plan;
- local execution bundle omits startup contract, decision authority, command-plan authority, allowed scope, forbidden scope, required tests, report update requirements, required artifacts, closeout expectations, or stop conditions;
- `codex_prompt_packet.json` is missing, stale, malformed, or not current-round aligned;
- prompt packet omits current bundle or current handoff source;
- prompt packet derives from stale bundle/handoff data;
- prompt packet is executable, dispatching, mutating, or claims authority over command-plan;
- prompt packet permits unauthorized commands or remote mutation;
- `audit_precheck_result.json` is missing, stale, malformed, or not current-round aligned;
- audit precheck returns `READY_FOR_GPT_AUDIT` while report, pytest, ID alignment, final-check, closeout, readiness, current handoff, local execution bundle, or prompt packet evidence is missing or failed;
- audit precheck cannot produce a blocking recommendation for structurally invalid Codex output;
- final-check does not validate bundle, prompt packet, and audit precheck freshness and evidence-only fields;
- command-plan omits required bundle, prompt packet, or audit precheck gates;
- current handoff packet regresses or becomes stale;
- audit inventory regresses or becomes stale;
- audit readiness regresses from READY/PASSED/ACCEPTED/no_action_required;
- status-policy false warning regresses;
- focused pytest omits `tests/test_project_reports.py`;
- pytest, report-summary, execution-log, audit-inventory, audit-readiness, current-handoff-packet, codex-prompt-packet, local-execution-bundle, audit-precheck, final-check, run-closeout, or post-closeout final-check fails;
- close-round is not CLOSED;
- closeout nested failure scan finds active failures;
- forbidden files are modified.
