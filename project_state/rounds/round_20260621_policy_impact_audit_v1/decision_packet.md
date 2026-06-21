```json decision_meta
{
  "schema_version": 1,
  "decision_id": "decision_20260621_policy_impact_audit_v1",
  "round_id": "round_20260621_policy_impact_audit_v1",
  "based_on_state_build_id": "state_20260618_134029_d6bd033d2532",
  "based_on_state_digest": "d6bd033d25324345cfd8ada0ac65db42bc86eb5017f3ffc92906fcd8b71cacb5",
  "status": "APPROVED",
  "mainline": "engineering_branch",
  "skill_profiles": ["reverse-agent-iteration@v2"]
}
```

```json decision_contract
{
  "previous_decision_id": "decision_20260621_prompt_docs_policy_integration_v1",
  "previous_round_id": "round_20260621_prompt_docs_policy_integration_v1",
  "previous_acceptance": "ACCEPTED",
  "primary_goal": "Add Policy Impact Audit v1 for policy-sensitive engineering changes.",
  "command_plan_authority_required": true,
  "accepted_requires_policy_impact_audit_artifact": true,
  "accepted_requires_policy_impact_required_audit_coverage": true,
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
    "project_state/gates/policy_impact_audit.json",
    "project_state/gates/report_summary_synthesis.json",
    "project_state/gates/final_gate_result.json",
    "project_state/gates/round_baseline.json",
    "project_state/gates/round_delta_summary.json",
    "project_state/gates/round_close_snapshot.json",
    "project_state/gates/run_closeout_result.json",
    "project_state/rounds/round_20260621_policy_impact_audit_v1/*"
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

Implement Policy Impact Audit v1 for policy-sensitive engineering changes.

The previous accepted round moved long-lived prompts into `docs/prompts/` and made policy-lint scan them. The next gap is impact accounting: when a round changes policy-sensitive code or text, the report should explicitly state whether prompts, skills, command-plan, final-check, policy-lint, tests, and report status semantics are affected. This prevents silent drift where engineering rules change but the stable prompt docs, tests, and audit criteria are not reviewed.

This round must add a bounded, testable policy-impact audit capability. It should produce a structured artifact and make final acceptance depend on substantive impact analysis when the round changes policy-sensitive files.

## 2. Current Evidence

Mainline: `engineering_branch`.

`task_packet.json` is background only. It still describes stale `samplereverse` work and must not control this round.

The previous round `decision_20260621_prompt_docs_policy_integration_v1` is accepted. Its evidence showed:

- `codex_execution_report.md` had `status=SUCCESS` and `acceptance_recommendation=ACCEPTED`.
- `docs/prompts/project_workspace_prompt.md`, `docs/prompts/codex_execution_prompt.md`, and `docs/prompts/README.md` were created.
- `policy_lint_result.json` had `gate_status=PASSED`, scanned the prompt docs, and had no findings.
- `final_gate_result.json` had `gate_status=PASSED`, no blocking reasons, and `recommended_next_action=no_action_required`.
- command-plan authority, report-summary synthesis, status policy, and required audit coverage all passed.

Existing relevant capabilities to reuse:

- `reverse_agent.project_gate` CLI structure and artifact-writing conventions
- `round_delta_summary.json` for changed-file detection
- `policy-lint` and `policy_lint_result.json`
- `decision-lint`, `preflight`, `command-plan`, `report-summary`, `final-check`, and `run-closeout`
- required audit coverage checks in final-check
- bounded prompt docs under `docs/prompts/*.md`
- tests in `tests/test_project_gate.py`

This is not a reverse-solving round. Do not inspect or run sample binaries. Do not use IDA, Ghidra, debuggers, emulators, runtime probes, harnesses, or full `solve_reports/`.

## 3. Do Not Do

Do not redesign the whole policy system or introduce a full policy manifest.

Do not add a database, message queue, workflow engine, or `execution_log.json`.

Do not generate prompts from code. Prompt docs may be updated only to mention stable Policy Impact Audit rules if needed.

Do not weaken policy-lint, decision-command-plan conflict detection, command-plan authority, report-summary synthesis, final-check, or closeout.

Do not make Policy Impact Audit a substitute for actual tests. It is an audit layer over policy-sensitive changes, not a replacement for pytest or gates.

Do not change profile names. The current profile names are `fast`, `standard`, and `full`; do not introduce `medium` as a profile.

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

Then inspect only files relevant to this engineering check:

1. `reverse_agent/project_gate.py`
2. `tests/test_project_gate.py`
3. `docs/prompts/README.md`
4. `docs/prompts/project_workspace_prompt.md`
5. `docs/prompts/codex_execution_prompt.md`
6. `project_state/gates/round_delta_summary.json`
7. `project_state/gates/policy_lint_result.json`
8. `project_state/gates/command_plan.json`
9. `project_state/gates/final_gate_result.json`
10. `project_state/gates/report_summary_synthesis.json`

Historical files may be read only by exact path when needed for a focused regression fixture. Do not scan entire `project_state/rounds/`, full `solve_reports/`, or full `PROJECT_PROGRESS_LOG.txt`.

## 5. Required Audit

Answer all items in `project_state/codex_execution_report.md` before claiming success:

1. What file patterns are considered policy-sensitive by Policy Impact Audit v1, and why?
2. How does the audit determine that prompt docs, skills, command-plan, final-check, report-summary, policy-lint, or report status semantics may be affected?
3. What structured artifact is written, and what fields does it contain?
4. When does Policy Impact Audit produce FAIL, WARN, or PASS?
5. How does final-check consume or verify the Policy Impact Audit result?
6. How does the audit avoid requiring heavy scans of `solve_reports/`, full `project_state/rounds/`, or full `PROJECT_PROGRESS_LOG.txt`?
7. What tests prove policy-sensitive source changes require a substantive policy impact answer, while ordinary non-policy changes do not create false failures?
8. How does this round preserve existing prompt docs, policy-lint, decision-command-plan conflict detection, command-plan authority, report-summary, final-check, and closeout behavior?

## 6. Implementation Scope

Implement one bounded feature: Policy Impact Audit v1 for policy-sensitive changes.

Allowed source changes:

- `reverse_agent/project_gate.py`
- `tests/test_project_gate.py`

Allowed prompt/document changes, only if needed to document the new stable audit rule:

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
- `project_state/gates/policy_impact_audit.json`
- `project_state/gates/report_summary_synthesis.json`
- `project_state/gates/final_gate_result.json`
- `project_state/gates/round_baseline.json`
- `project_state/gates/round_delta_summary.json`
- `project_state/gates/round_close_snapshot.json`
- `project_state/gates/run_closeout_result.json`
- `project_state/rounds/round_20260621_policy_impact_audit_v1/*` only if command-plan authorizes closeout

Required implementation behavior:

1. Add a CLI entrypoint such as `python -m reverse_agent.project_gate policy-impact --state-dir project_state` or integrate an equivalent policy-impact check into an existing gate, while still writing `project_state/gates/policy_impact_audit.json`.
2. Detect policy-sensitive changed files from `round_delta_summary.json` or equivalent current delta evidence. At minimum, treat these as policy-sensitive:
   - `reverse_agent/project_gate.py`
   - `tests/test_project_gate.py` when testing gate/policy behavior
   - `docs/prompts/*.md`
   - `.codex-skills/**`
   - `.codex-skills/registry.json`
   - `project_state/decision_packet.md` when live decision changes during execution
   - gate/report schema or status-policy related code paths in `project_gate.py`
3. Write `project_state/gates/policy_impact_audit.json` with schema_version, gate_name, gate_status, decision_id, round_id, policy_sensitive_files, impacted_domains, required_report_topics, missing_report_topics, warnings, blocking_reasons, and recommended_next_action.
4. Require substantive report coverage for impacted domains when policy-sensitive files changed. At minimum, domains should include prompt_docs, skills, command_plan, final_check, report_summary, policy_lint, report_status_schema, and tests.
5. Classify as FAIL when policy-sensitive changes are present but the report omits required impact coverage; WARN when impact is plausible but no hard evidence requires a block; PASS when coverage is present or no policy-sensitive files changed.
6. Integrate the check into final-check or report-summary so a `SUCCESS/ACCEPTED` report cannot silently skip policy impact analysis for policy-sensitive changes.
7. Add focused regression tests for policy-sensitive source changes, prompt-doc changes, no-impact ordinary changes, missing report coverage, and successful report coverage.
8. Preserve existing policy-lint, prompt docs, command-plan authority, report-summary, final-check, closeout, and decision-command-plan conflict behavior.

Do not add a full policy manifest, prompt generation, or execution-log storage in this round.

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

Run policy-lint and policy-impact only if command-plan explicitly includes or authorizes them:

```powershell
python -m reverse_agent.project_gate policy-lint --state-dir project_state
python -m reverse_agent.project_gate policy-impact --state-dir project_state
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
python -m reverse_agent.project_gate run-closeout --state-dir project_state --round-id round_20260621_policy_impact_audit_v1
```

If closeout runs, rerun report-summary and final-check afterward.

Record all executed commands, stdout/stderr, exit codes, and final conclusion in `project_state/pytest_result.txt`. The structured summary must match this decision_id and round_id.

## 8. Stop Conditions

Stop and report `BLOCKED` or `REWORK_REQUIRED` if:

1. preflight fails before implementation for unrelated reasons;
2. this requires a full policy manifest, prompt generation, database, workflow engine, or execution-log migration;
3. source changes outside `reverse_agent/project_gate.py` and `tests/test_project_gate.py` are needed;
4. prompt/document changes outside `docs/prompts/project_workspace_prompt.md`, `docs/prompts/codex_execution_prompt.md`, and `docs/prompts/README.md` are needed;
5. Policy Impact Audit requires heavy runtime output scans, full `project_state/rounds/`, full `solve_reports/`, or full `PROJECT_PROGRESS_LOG.txt` by default;
6. Policy Impact Audit blocks ordinary non-policy changes without a clear policy-sensitive file reason;
7. command-plan authority, policy-lint, decision-command-plan conflict detection, report-summary, final-check, or closeout regresses;
8. `codex_execution_report.md`, `pytest_result.txt`, or gate artifacts use stale decision_id/round_id;
9. tests fail or any required command exit code is nonzero;
10. closeout archive files are created but not listed in `files_changed` and `generated_artifacts`.
