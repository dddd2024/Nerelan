```json decision_meta
{
  "schema_version": 1,
  "decision_id": "decision_20260621_prompt_docs_policy_integration_v1",
  "round_id": "round_20260621_prompt_docs_policy_integration_v1",
  "based_on_state_build_id": "state_20260618_134029_d6bd033d2532",
  "based_on_state_digest": "d6bd033d25324345cfd8ada0ac65db42bc86eb5017f3ffc92906fcd8b71cacb5",
  "status": "APPROVED",
  "mainline": "engineering_branch",
  "skill_profiles": ["reverse-agent-iteration@v2"]
}
```

```json decision_contract
{
  "previous_decision_id": "decision_20260621_policy_lint_prompt_consistency_v1",
  "previous_round_id": "round_20260621_policy_lint_prompt_consistency_v1",
  "previous_acceptance": "ACCEPTED",
  "primary_goal": "Add canonical prompt documents to the repository and include them in policy-lint scanning.",
  "command_plan_authority_required": true,
  "accepted_requires_prompt_docs_created": true,
  "accepted_requires_policy_lint_scans_prompt_docs": true,
  "accepted_requires_final_check_passed": true,
  "allowed_source_files": [
    "reverse_agent/project_gate.py",
    "tests/test_project_gate.py"
  ],
  "allowed_prompt_files": [
    "docs/prompts/project_workspace_prompt.md",
    "docs/prompts/codex_execution_prompt.md",
    "docs/prompts/README.md"
  ],
  "allowed_state_artifacts": [
    "project_state/codex_execution_report.md",
    "project_state/pytest_result.txt",
    "project_state/gates/command_plan.json",
    "project_state/gates/gate_profile_plan.json",
    "project_state/gates/preflight_result.json",
    "project_state/gates/policy_lint_result.json",
    "project_state/gates/report_summary_synthesis.json",
    "project_state/gates/final_gate_result.json",
    "project_state/gates/round_baseline.json",
    "project_state/gates/round_delta_summary.json",
    "project_state/gates/round_close_snapshot.json",
    "project_state/gates/run_closeout_result.json",
    "project_state/rounds/round_20260621_prompt_docs_policy_integration_v1/*"
  ],
  "forbidden_mutated_paths": [
    "project_state/current_state.json",
    "project_state/task_packet.json",
    "project_state/artifact_index.json",
    "project_state/negative_results.json",
    ".codex-skills/registry.json"
  ]
}
```

# DECISION_PACKET

## 1. Goal

Add canonical prompt documents to the repository and make policy-lint scan them by default.

The previous accepted round implemented `policy-lint / prompt-consistency v1`, but the scan target set is still limited to skills, README, and the current decision packet. This round should create bounded, version-controlled prompt documents for:

1. the project-level reverse-agent workspace prompt;
2. the local Codex execution prompt.

Then update policy-lint so these prompt documents are part of the default bounded scan surface. This makes future drift in long-lived prompts visible to tests and gates instead of being tracked only in chat history.

## 2. Current Evidence

Mainline: `engineering_branch`.

`task_packet.json` is background only. It still describes stale `samplereverse` work and must not control this round.

The previous round `decision_20260621_policy_lint_prompt_consistency_v1` is accepted. Its evidence showed:

- `codex_execution_report.md` had `status=SUCCESS` and `acceptance_recommendation=ACCEPTED`.
- `policy_lint_result.json` was generated.
- policy-lint detected six drift classes: obsolete profile names, Tests-over-command-plan authority, task_packet-over-decision_packet authority, default heavy-path reads, unsupported report statuses, and dynamic facts in skill files.
- policy-lint scanned only bounded files: `.codex-skills/*/SKILL.md`, `README.md`, and `project_state/decision_packet.md`.
- final-check passed with no blocking reasons.

Current gap:

- The project-level workspace prompt and Codex execution prompt are not yet committed as repository files.
- policy-lint cannot consistently scan those prompts because `docs/prompts/*` is not yet an active canonical prompt location.
- Future prompt-code drift can still happen outside the repo if these prompts remain only in chat history.

Existing capabilities to reuse:

- `reverse_agent.project_gate policy-lint`
- policy-lint artifact writer: `project_state/gates/policy_lint_result.json`
- existing policy-lint scan helpers and drift-class tests in `tests/test_project_gate.py`
- existing command-plan, report-summary, final-check, closeout, and round archive behavior

This is not a reverse-solving round. Do not inspect or run sample binaries. Do not use IDA, Ghidra, debuggers, emulators, runtime probes, harnesses, or full `solve_reports/`.

## 3. Do Not Do

Do not redesign the policy system or implement full prompt generation from a manifest.

Do not add a database, message queue, workflow engine, or `execution_log.json`.

Do not rewrite `.codex-skills/` or `.codex-skills/registry.json`.

Do not treat prompt docs as dynamic project_state. Prompt docs must contain stable workflow rules only, not candidate values, run names, artifact freshness, runtime metrics, single-sample conclusions, or local transient paths except the stable local repo path `F:\reverse-agent` inside the Codex execution prompt.

Do not weaken policy-lint to make new prompt docs pass. If the prompt docs contain drift, fix the prompt wording rather than hiding findings.

Do not change profile names. The current profile names are `fast`, `standard`, and `full`; do not introduce `medium` as a profile.

Do not make Tests authoritative over command-plan. The prompt docs must state that command-plan is the command execution authority.

Do not mutate `project_state/current_state.json`, `project_state/task_packet.json`, `project_state/artifact_index.json`, `project_state/negative_results.json`, or `.codex-skills/registry.json`.

Do not continue `samplereverse` solving. Do not run samples, solvers, harnesses, runtime probes, IDA/Ghidra, debuggers, emulators, GUI workflows, or full `solve_reports/` scans.

Do not push, commit, create PRs, switch branches, rebase, merge, or modify remote state unless the user explicitly requests it in the current message.

## 4. Files To Inspect

Read default state files first:

1. `project_state/task_packet.json`
2. `project_state/current_state.json`
3. `project_state/artifact_index.json`
4. `project_state/negative_results.json`
5. `project_state/codex_execution_report.md`
6. `project_state/decision_packet.md`
7. `project_state/pytest_result.txt`
8. `.codex-skills/registry.json`

Then inspect only files relevant to this prompt-policy integration:

1. `reverse_agent/project_gate.py`
2. `tests/test_project_gate.py`
3. `.codex-skills/registry.json`
4. `.codex-skills/reverse-agent-iteration/SKILL.md`
5. `README.md`
6. `docs/prompts/` if it already exists
7. `project_state/gates/policy_lint_result.json`
8. `project_state/gates/command_plan.json`
9. `project_state/gates/final_gate_result.json`
10. `project_state/gates/report_summary_synthesis.json`

Historical files may be read only by exact path when needed for a focused regression fixture. Do not scan entire `project_state/rounds/`, full `solve_reports/`, or full `PROJECT_PROGRESS_LOG.txt`.

## 5. Required Audit

Answer all items in `project_state/codex_execution_report.md` before claiming success:

1. Which canonical prompt files were created, and what stable role does each file serve?
2. How do the prompt docs preserve the current project rules: decision_packet authority, task_packet as background, command-plan authority, fast/standard/full profiles, report status values, and no default heavy artifact scans?
3. How do the prompt docs avoid dynamic facts such as candidates, run names, artifact paths, freshness, runtime metrics, and single-sample conclusions?
4. How did policy-lint’s default scan surface change, and how is `docs/prompts/*.md` bounded?
5. What policy-lint findings were produced after adding the prompt docs, and why are they acceptable or fixed?
6. What tests prove policy-lint scans prompt docs and catches drift inside them?
7. What tests prove valid prompt wording is allowed and does not create false blocking failures?
8. How does this round preserve existing policy-lint, decision-command-plan conflict detection, command-plan authority, report-summary, final-check, and closeout behavior?

## 6. Implementation Scope

Implement one bounded feature: repository-backed canonical prompt documents plus policy-lint scanning for those documents.

Allowed source changes:

- `reverse_agent/project_gate.py`
- `tests/test_project_gate.py`

Allowed prompt/document files:

- `docs/prompts/project_workspace_prompt.md`
- `docs/prompts/codex_execution_prompt.md`
- `docs/prompts/README.md`

Allowed state/artifact updates:

- `project_state/codex_execution_report.md`
- `project_state/pytest_result.txt`
- `project_state/gates/command_plan.json`
- `project_state/gates/gate_profile_plan.json`
- `project_state/gates/preflight_result.json`
- `project_state/gates/policy_lint_result.json`
- `project_state/gates/report_summary_synthesis.json`
- `project_state/gates/final_gate_result.json`
- `project_state/gates/round_baseline.json`
- `project_state/gates/round_delta_summary.json`
- `project_state/gates/round_close_snapshot.json`
- `project_state/gates/run_closeout_result.json`
- `project_state/rounds/round_20260621_prompt_docs_policy_integration_v1/*` only if command-plan authorizes closeout

Required implementation behavior:

1. Create `docs/prompts/project_workspace_prompt.md` containing the stable project-level rules for GPT as decision/audit planner: mainlines, evidence precedence, DECISION_PACKET requirements, CODEX_EXECUTION_REPORT requirements, audit outcomes, artifact freshness, negative_results, no default heavy artifact scans, and mature tool priority.
2. Create `docs/prompts/codex_execution_prompt.md` containing the stable local Codex execution rules: `F:\reverse-agent`, startup checks, first `git status` baseline, decision_packet authority, task_packet background, preflight before implementation, command-plan authority, allowed commands only, report/pytest_result requirements, closeout rules, final response fields, and no remote mutation unless explicitly requested.
3. Optionally create `docs/prompts/README.md` to document that these files are stable prompt templates and not dynamic state.
4. Extend policy-lint’s bounded scan surface to include `docs/prompts/*.md` and only that prompt directory, not arbitrary docs or historical outputs.
5. Ensure policy-lint does not flag valid prohibitive examples such as "do not use medium" or "do not write COMPLETED_WITH_LIMITATIONS as codex_report_summary.status".
6. Add focused tests proving prompt docs are scanned and drift inside prompt docs is detected.
7. Add focused tests proving the committed prompt docs pass policy-lint without blocking findings.
8. Preserve existing policy-lint v1 drift classes and all previous gate behavior.

Do not generate prompts from code or a policy manifest in this round. Do not add new long-term state files outside `docs/prompts/`.

## 7. Tests

Run startup checks first:

```powershell
Set-Location F:\reverse-agent
Get-Location
Test-Path F:\reverse-agent
git rev-parse --show-toplevel
git status --short
```

Run preflight before implementation:

```powershell
python -m reverse_agent.project_gate preflight --state-dir project_state
```

If preflight passes, run command-plan and follow only command-plan-authorized commands:

```powershell
python -m reverse_agent.project_gate command-plan --state-dir project_state --json
```

Targeted tests:

```powershell
python -m pytest tests/test_project_gate.py -q
```

Run policy-lint only if command-plan explicitly includes or authorizes it:

```powershell
python -m reverse_agent.project_gate policy-lint --state-dir project_state
```

Final validation commands, only when authorized by command-plan:

```powershell
python -m reverse_agent.project_gate decision-lint --state-dir project_state
python -m pytest tests/test_project_gate.py tests/test_project_state.py -q
python -m reverse_agent.project_gate report-summary --state-dir project_state
python -m reverse_agent.project_gate final-check --state-dir project_state
```

Run closeout only if command-plan explicitly includes or authorizes the closeout command for this round:

```powershell
python -m reverse_agent.project_gate run-closeout --state-dir project_state --round-id round_20260621_prompt_docs_policy_integration_v1
```

If closeout runs, rerun report-summary and final-check afterward.

Record all executed commands, stdout/stderr, exit codes, and final conclusion in `project_state/pytest_result.txt`. The structured summary must match this decision_id and round_id.

## 8. Stop Conditions

Stop and report `BLOCKED` or `REWORK_REQUIRED` if:

1. preflight fails before implementation for unrelated reasons;
2. this requires prompt generation, a full policy manifest, a database, workflow engine, or execution-log migration;
3. source changes outside `reverse_agent/project_gate.py` and `tests/test_project_gate.py` are needed;
4. prompt/document changes outside `docs/prompts/project_workspace_prompt.md`, `docs/prompts/codex_execution_prompt.md`, and `docs/prompts/README.md` are needed;
5. policy-lint scans heavy runtime outputs, full `project_state/rounds/`, full `solve_reports/`, or full `PROJECT_PROGRESS_LOG.txt` by default;
6. the prompt docs contain dynamic one-run facts, sample candidates, run names, freshness, runtime metrics, or single-sample conclusions;
7. policy-lint produces blocking failures on the newly committed prompt docs without a precise intentional test case;
8. command-plan authority, policy-lint, decision-command-plan conflict detection, report-summary, final-check, or closeout regresses;
9. `codex_execution_report.md`, `pytest_result.txt`, or gate artifacts use stale decision_id/round_id;
10. tests fail or any required command exit code is nonzero;
11. closeout archive files are created but not listed in `files_changed` and `generated_artifacts`.
