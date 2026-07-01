```json decision_meta
{
  "schema_version": 1,
  "decision_id": "decision_20260701_current_handoff_packet_v1",
  "round_id": "round_20260701_current_handoff_packet_v1",
  "based_on_state_build_id": "state_20260618_134029_d6bd033d2532",
  "based_on_state_digest": "d6bd033d25324345cfd8ada0ac65db42bc86eb5017f3ffc92906fcd8b71cacb5",
  "status": "APPROVED",
  "mainline": "engineering_branch",
  "skill_profiles": ["reverse-agent-iteration@v2"]
}
```

```json decision_contract
{
  "previous_decision_id": "decision_20260701_status_policy_and_audit_inventory_v1",
  "previous_round_id": "round_20260701_status_policy_and_audit_inventory_v1",
  "previous_audit_outcome": "ACCEPTED",
  "phase_label": "phase_2_26_current_handoff_packet",
  "primary_goal": "Create a current, non-dispatching Codex handoff packet that packages the active decision, command-plan authority, required startup checks, allowed scope, test contract, and audit readiness evidence for manual/local executor use.",
  "command_plan_authority_required": true,
  "accepted_requires_current_handoff_packet": true,
  "accepted_requires_no_duplicate_runner_or_dispatcher": true,
  "accepted_requires_existing_audit_inventory_not_regressed": true,
  "accepted_requires_existing_audit_readiness_packet_not_regressed": true,
  "accepted_requires_command_plan_authority_preserved": true,
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
    "project_state/rounds/round_20260701_current_handoff_packet_v1/*"
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

Implement **Current Handoff Packet v1**.

This round advances the engineering branch from validated audit/readiness artifacts to a bounded, current handoff artifact for manual or local Codex execution.

Primary objective:

1. Produce `project_state/gates/current_handoff_packet.json` as the single current evidence packet an executor can read before work.
2. The packet must summarize the active decision, command-plan authority, required startup sequence, allowed and forbidden paths, test contract, expected generated artifacts, audit inventory status, audit readiness status, closeout expectations, and stop conditions.
3. The packet must be evidence-only and non-dispatching. It must not start Codex, call model APIs, run commands, schedule work, or mutate remote state.
4. If an older handoff artifact or runner bundle already exists, inspect it and reuse its schema ideas where safe, but do not revive stale IDs as current evidence and do not implement a new runner/dispatcher.

Target outcome:

- `codex_execution_report.md` status: `SUCCESS`.
- acceptance recommendation: `ACCEPTED`.
- `pytest_result.txt` status: `PASSED`.
- `final-check`: `PASSED`.
- `run-closeout`: `PASSED`.
- `close-round`: `CLOSED`.
- `current_handoff_packet.json`: current decision ID, current round ID, current report ID, evidence-only, non-dispatching, command-plan aligned.
- `audit_inventory_result.json`: remains current and validated.
- `audit_readiness_packet.json`: remains `READY`, `PASSED`, `no_action_required`.
- No Web/API/CI/runner/database/scheduler expansion.

## 2. Current Evidence

Mainline: `engineering_branch`.

`project_state/decision_packet.md` controls this round. `project_state/task_packet.json` remains background only.

Previous round: `decision_20260701_status_policy_and_audit_inventory_v1` / `round_20260701_status_policy_and_audit_inventory_v1`.

Previous audit outcome: `ACCEPTED`.

Accepted evidence from previous round:

- `codex_execution_report.md` matched the current decision and reported `SUCCESS` / `ACCEPTED`.
- `pytest_result.txt` was current and `PASSED`.
- focused pytest included `tests/test_project_reports.py` and passed.
- `status_policy_valid` was repaired to `PASS`, with canonical source `execution_report_summary`.
- `audit_inventory_result.json` became current, validated three audit files, and was evidence-only.
- `audit_readiness_packet.json` remained `READY`, `PASSED`, evidence-only, and `no_action_required`.
- `run_closeout_result.json` passed and close-round was `CLOSED`.

Engineering gap now being addressed:

- Current decision/report/gate evidence is valid, but executor handoff is still distributed across multiple state files.
- Historical handoff or runner artifacts exist in `project_state/gates/` as stale/nonblocking evidence. They must be inspected before implementation and either reused conceptually or explicitly left stale.
- The project needs one current, bounded, non-dispatching packet for Codex/operator use before any future execution.

Artifact freshness policy:

- Current-round gate artifacts must carry `decision_20260701_current_handoff_packet_v1` and `round_20260701_current_handoff_packet_v1`.
- Historical artifacts may be referenced only as historical/nonblocking unless rebuilt this round with current IDs.
- Missing historical sample artifacts remain nonblocking background.
- The handoff packet is generated state, not a long-term skill.

Command-plan policy:

- `command-plan` remains the command authority.
- Codex may only execute command-plan authorized commands.
- The handoff packet may summarize allowed commands, but it must not override command-plan.
- Startup order remains strict: the five startup commands, then `startup-snapshot` as the first project gate.
- Existing `execution_order_policy` may remain coverage/expected-exit based, but it must stay explicit and validated.

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

Do not put dynamic run-specific facts, artifact freshness, runtime metrics, local paths beyond the existing `F:\reverse-agent` startup contract, or single-round conclusions into `.codex-skills/`.

Do not make the handoff packet executable. It must not include any field that implies it can launch commands or mutate state.

Do not weaken audit inventory, audit readiness, final-check, command-plan, startup, or closeout checks merely to produce a clean packet.

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

1. `project_state/gates/command_plan.json`
2. `project_state/gates/final_gate_result.json`
3. `project_state/gates/report_summary_synthesis.json`
4. `project_state/gates/audit_inventory_result.json`
5. `project_state/gates/audit_readiness_packet.json`
6. `project_state/gates/execution_log.json`
7. `project_state/gates/run_closeout_result.json`
8. `project_state/gates/round_delta_summary.json`

Inspect existing handoff/runner artifacts before implementation:

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
8. Did Codex inspect existing handoff/runner artifacts or code before adding the current handoff packet?
9. Did implementation avoid creating a new runner, dispatcher, scheduler, queue, service, Web/API layer, CI workflow, or external integration?
10. Does `current_handoff_packet.json` exist with current decision ID, round ID, and report ID?
11. Does the handoff packet identify `decision_packet.md` as the decision authority?
12. Does the handoff packet identify `command_plan.json` as the command execution authority?
13. Does the handoff packet include the required startup sequence and startup-snapshot-first rule?
14. Does the handoff packet summarize allowed source/test paths and forbidden paths from the decision contract?
15. Does the handoff packet summarize required tests and the pytest command including `tests/test_project_reports.py`?
16. Does the handoff packet include expected generated artifacts and artifact freshness policy?
17. Does the handoff packet summarize current `audit_inventory_result.json` status?
18. Does the handoff packet summarize current `audit_readiness_packet.json` status?
19. Does the handoff packet summarize closeout expectations and stop conditions?
20. Is the handoff packet evidence-only, non-dispatching, non-executable, and non-mutating?
21. Does final-check validate handoff packet freshness, evidence-only fields, and command-plan alignment?
22. Does final-check reject stale handoff packet IDs when current handoff is required?
23. Does final-check reject a handoff packet that claims authority over command-plan or omits command-plan authority?
24. Did command-plan include the handoff packet gate and preserve explicit `execution_order_policy`?
25. Did audit inventory remain current and validated?
26. Did audit readiness remain `READY`, `PASSED`, and `no_action_required`?
27. Did report-summary synthesis pass with no diffs?
28. Did final report summary match pytest, changed files, generated artifacts, decision ID, round ID, current handoff status, audit inventory status, and audit readiness status?

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
- `project_state/rounds/round_20260701_current_handoff_packet_v1/*`

Required behavior:

1. Add or repair a bounded project gate that writes `project_state/gates/current_handoff_packet.json`.
2. If an equivalent existing handoff packet generator already exists, reuse/extend it instead of creating a duplicate concept.
3. `current_handoff_packet.json` must include:
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
   - required_tests;
   - expected_artifacts;
   - artifact_freshness_policy;
   - audit_inventory_status;
   - audit_readiness_status;
   - closeout_expectations;
   - stop_conditions;
   - evidence_only;
   - executable;
   - can_execute;
   - mutates_state;
   - warnings;
   - errors.
4. The packet must not contain secrets, local-only runtime metrics, bulky solve report content, command outputs beyond references, or generated candidate data.
5. final-check must validate the packet when the decision contract requires it.
6. command-plan must include the handoff packet gate if the gate is required for acceptance.
7. report-summary synthesis must include current handoff packet status in generated artifacts and summary matching.
8. Existing audit inventory behavior must not regress.
9. Existing audit readiness behavior must not regress.
10. Existing command-plan authority and startup/closeout order checks must not regress.

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
python -m reverse_agent.project_gate report-summary --state-dir project_state
python -m reverse_agent.project_gate execution-log --state-dir project_state
python -m reverse_agent.project_gate final-check --state-dir project_state
python -m reverse_agent.project_gate run-closeout --state-dir project_state --round-id round_20260701_current_handoff_packet_v1
python -m reverse_agent.project_gate final-check --state-dir project_state
```

If the exact CLI name differs, use the existing project_gate subcommand and record the actual command in `pytest_result.txt`.

Required regression coverage:

- stale handoff packet IDs fail final-check when current handoff is required;
- packet missing command-plan authority fails;
- packet claiming it can execute or mutate state fails;
- packet missing startup contract fails;
- packet missing allowed/forbidden scope fails;
- packet missing audit inventory or audit readiness status fails;
- packet omitting required tests fails;
- current packet passes with current IDs and evidence-only fields;
- audit inventory remains current and validated;
- audit readiness remains READY/PASSED/no_action_required;
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
- implementation requires real runner, dispatcher, scheduler, Web/API, database, workflow, external service, or remote state changes.

Stop with `REWORK_REQUIRED` if:

- `current_handoff_packet.json` is missing, stale, malformed, or not current-round aligned;
- handoff packet is executable, dispatching, mutating, or claims authority over command-plan;
- final-check does not validate handoff packet freshness and evidence-only fields;
- final-check accepts stale handoff IDs when current handoff is required;
- command-plan omits the required handoff packet gate;
- audit inventory regresses or becomes stale;
- audit readiness regresses from READY/PASSED/no_action_required;
- status-policy false warning regresses;
- focused pytest omits `tests/test_project_reports.py`;
- pytest, report-summary, execution-log, audit-inventory, audit-readiness, current-handoff-packet, final-check, run-closeout, or post-closeout final-check fails;
- close-round is not CLOSED;
- closeout nested failure scan finds active failures;
- forbidden files are modified.
