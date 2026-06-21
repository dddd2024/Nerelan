```json codex_report_summary
{
  "schema_version": 1,
  "report_id": "codex_report_20260621_prompt_docs_policy_integration_v1",
  "round_id": "round_20260621_prompt_docs_policy_integration_v1",
  "based_on_decision_id": "decision_20260621_prompt_docs_policy_integration_v1",
  "status": "SUCCESS",
  "acceptance_recommendation": "ACCEPTED",
  "files_changed": [
    "docs/prompts/README.md",
    "docs/prompts/codex_execution_prompt.md",
    "docs/prompts/project_workspace_prompt.md",
    "project_state/codex_execution_report.md",
    "project_state/gates/command_plan.json",
    "project_state/gates/final_gate_result.json",
    "project_state/gates/gate_profile_plan.json",
    "project_state/gates/policy_lint_result.json",
    "project_state/gates/preflight_result.json",
    "project_state/gates/report_summary_synthesis.json",
    "project_state/gates/round_baseline.json",
    "project_state/gates/round_close_snapshot.json",
    "project_state/gates/round_delta_summary.json",
    "project_state/gates/run_closeout_result.json",
    "project_state/pytest_result.txt",
    "project_state/rounds/round_20260621_prompt_docs_policy_integration_v1/codex_execution_report.md",
    "project_state/rounds/round_20260621_prompt_docs_policy_integration_v1/decision_packet.md",
    "project_state/rounds/round_20260621_prompt_docs_policy_integration_v1/pytest_result.txt",
    "project_state/rounds/round_20260621_prompt_docs_policy_integration_v1/round_manifest.json",
    "reverse_agent/project_gate.py",
    "tests/test_project_gate.py"
  ],
  "tests_ran": [
    "python -m reverse_agent.project_gate command-plan --state-dir project_state",
    "python -m reverse_agent.project_gate command-plan --state-dir project_state --json",
    "python -m reverse_agent.project_gate report-summary --state-dir project_state",
    "python -m reverse_agent.project_gate final-check --state-dir project_state",
    "python -m reverse_agent.project_gate preflight --state-dir project_state",
    "python -m pytest tests/test_project_gate.py -q",
    "python -m reverse_agent.project_gate policy-lint --state-dir project_state",
    "python -m reverse_agent.project_gate decision-lint --state-dir project_state",
    "python -m pytest tests/test_project_gate.py tests/test_project_state.py -q",
    "python -m reverse_agent.project_gate run-closeout --state-dir project_state --round-id round_20260621_prompt_docs_policy_integration_v1"
  ],
  "generated_artifacts": [
    "project_state/codex_execution_report.md",
    "project_state/gates/command_plan.json",
    "project_state/gates/final_gate_result.json",
    "project_state/gates/gate_profile_plan.json",
    "project_state/gates/policy_lint_result.json",
    "project_state/gates/preflight_result.json",
    "project_state/gates/report_summary_synthesis.json",
    "project_state/gates/round_baseline.json",
    "project_state/gates/round_close_snapshot.json",
    "project_state/gates/round_delta_summary.json",
    "project_state/pytest_result.txt",
    "project_state/rounds/round_20260621_prompt_docs_policy_integration_v1/codex_execution_report.md",
    "project_state/rounds/round_20260621_prompt_docs_policy_integration_v1/decision_packet.md",
    "project_state/rounds/round_20260621_prompt_docs_policy_integration_v1/pytest_result.txt",
    "project_state/rounds/round_20260621_prompt_docs_policy_integration_v1/round_manifest.json"
  ],
  "referenced_artifacts": [],
  "required_closeout_artifacts": [
    "project_state/gates/policy_lint_result.json"
  ]
}
```

# CODEX_EXECUTION_REPORT

## Status

SUCCESS

## Required Audit

### 1. Which canonical prompt files were created, and what stable role does each file serve?

- Evidence: Three files created under `docs/prompts/`: `docs/prompts/project_workspace_prompt.md` (decision/audit planner prompt), `docs/prompts/codex_execution_prompt.md` (local Codex execution prompt), `docs/prompts/README.md` (directory documentation). Verified by `git status --short` showing all three as untracked, and by policy-lint scanning all three (scanned_files list includes them).
- Status: PASS
- Answer: Three canonical prompt files were created. `project_workspace_prompt.md` serves as the stable decision/audit planner prompt defining mainlines, evidence precedence, DECISION_PACKET requirements, CODEX_EXECUTION_REPORT requirements, audit outcomes, artifact freshness, negative_results, no default heavy artifact scans, mature tool priority, and profile names. `codex_execution_prompt.md` serves as the stable local Codex execution prompt defining working directory, startup checks, decision_packet authority, preflight before implementation, command-plan authority, allowed commands only, report/pytest_result requirements, closeout rules, final response fields, no remote mutation, and profile names. `README.md` documents that these files are stable prompt templates scanned by policy-lint.

### 2. How do the prompt docs preserve the current project rules: decision_packet authority, task_packet as background, command-plan authority, fast/standard/full profiles, report status values, and no default heavy artifact scans?

- Evidence: `project_workspace_prompt.md` states "decision_packet.md is the sole execution authority", "task_packet.json is background only", "command-plan is the command execution authority", "Profile names are fast, standard, and full. Do not introduce medium as a profile name", "codex_report_summary.status only allows: SUCCESS, PARTIAL, FAILED, BLOCKED", "Do not read full solve_reports/ or PROJECT_PROGRESS_LOG.txt by default". `codex_execution_prompt.md` states the same rules with "do not use" phrasing for prohibitions. policy-lint PASSED with zero findings on both files.
- Status: PASS
- Answer: Both prompt docs explicitly state all six project rules. Prohibitive examples like "do not use medium" and "do not write COMPLETED_WITH_LIMITATIONS as codex_report_summary.status" are phrased as negative guidance so policy-lint does not flag them. The profile names fast/standard/full are used consistently. The valid report status values (SUCCESS/PARTIAL/FAILED/BLOCKED) are listed. No default heavy artifact scans is stated as a prohibition.

### 3. How do the prompt docs avoid dynamic facts such as candidates, run names, artifact paths, freshness, runtime metrics, and single-sample conclusions?

- Evidence: policy-lint was run on the actual project state with `gate_status: PASSED` and `findings: []`. The prompt docs contain only stable workflow rules. The only local path referenced is `F:\reverse-agent`, which is the stable canonical repo path explicitly allowed by the decision packet and exempted by policy-lint. No candidate hex strings, run names, artifact paths with round IDs, runtime metrics, or single-sample conclusions appear in any prompt doc.
- Status: PASS
- Answer: The prompt docs contain only stable workflow rules. No dynamic facts (candidates, run names, artifact paths, freshness, runtime metrics, single-sample conclusions) are present. The only local path is `F:\reverse-agent`, which is the stable repo path exempted by policy-lint because the decision packet explicitly allows it in the Codex execution prompt.

### 4. How did policy-lint’s default scan surface change, and how is `docs/prompts/*.md` bounded?

- Evidence: `_POLICY_LINT_SCAN_GLOBS` in `reverse_agent/project_gate.py` was extended to include `docs/prompts/*.md`. The glob only matches files directly in `docs/prompts/`, not in subdirectories or in `docs/` itself. The `is_long_lived_text` flag is set to True only for paths starting with `.codex-skills/` or `docs/prompts/`. The test `test_policy_lint_prompt_docs_do_not_scan_arbitrary_docs` verifies that `docs/other.md` is not scanned.
- Status: PASS
- Answer: The scan surface was extended by adding `docs/prompts/*.md` to `_POLICY_LINT_SCAN_GLOBS`. This glob is bounded to only files directly in `docs/prompts/`. Files in `docs/` outside `docs/prompts/` are not scanned. The `is_long_lived_text` flag (which enables dynamic fact detection) is only set for `.codex-skills/` and `docs/prompts/` prefixed paths.

### 5. What policy-lint findings were produced after adding the prompt docs, and why are they acceptable or fixed?

- Evidence: During development, two false-positive finding classes were produced and fixed. First, `unsupported_report_status` (FAIL) on `codex_execution_prompt.md` when listing `COMPLETED_WITH_LIMITATIONS` as a valid conclusion value — fixed by adding `conclusion` to the exemption regex. Second, `dynamic_fact_in_skill` (WARN) on `codex_execution_prompt.md` for `F:\reverse-agent` references — fixed by adding an exemption for the stable repo path. After both fixes, policy-lint reports `gate_status: PASSED` with `findings: []` and `warnings: []`.
- Status: PASS
- Answer: Two false-positive finding classes were produced during development and both were fixed. The `COMPLETED_WITH_LIMITATIONS` false positive was fixed by exempting "conclusion" context. The `F:\reverse-agent` false positive was fixed by exempting the stable repo path. After fixes, policy-lint reports PASSED with zero findings.

### 6. What tests prove policy-lint scans prompt docs and catches drift inside them?

- Evidence: Three tests in `tests/test_project_gate.py` prove scanning and drift detection: `test_policy_lint_scans_prompt_docs` (obsolete profile name detected), `test_policy_lint_detects_drift_in_prompt_docs` (Tests-over-command-plan drift detected), `test_policy_lint_detects_dynamic_facts_in_prompt_docs` (candidate hex string detected). All 18 policy-lint tests pass (17 existing + 1 new for stable path exemption).
- Status: PASS
- Answer: Three tests prove prompt docs are scanned and drift is detected: `test_policy_lint_scans_prompt_docs` (obsolete profile), `test_policy_lint_detects_drift_in_prompt_docs` (Tests-over-command-plan), and `test_policy_lint_detects_dynamic_facts_in_prompt_docs` (candidate hex string). All pass.

### 7. What tests prove valid prompt wording is allowed and does not create false blocking failures?

- Evidence: Three tests prove valid prompt wording passes: `test_policy_lint_clean_prompt_docs_pass` (no FAIL findings for valid wording), `test_policy_lint_prompt_docs_do_not_scan_arbitrary_docs` (arbitrary docs not scanned), `test_policy_lint_exempts_stable_repo_path_in_prompt_docs` (stable path exempted). Additionally, policy-lint was run on the actual committed prompt docs and reports `gate_status: PASSED` with `findings: []`.
- Status: PASS
- Answer: Three tests prove valid prompt wording passes without false blocking failures. The actual committed prompt docs also pass policy-lint with zero findings, confirming no false positives remain.

### 8. How does this round preserve existing policy-lint, decision-command-plan conflict detection, command-plan authority, report-summary, final-check, and closeout behavior?

- Evidence: All 989 tests pass (691 in `test_project_gate.py` + 298 in `test_project_state.py`), including all existing policy-lint v1 tests, decision-command-plan conflict detection tests, command-plan authority tests, report-summary tests, final-check tests, and closeout tests. The `_POLICY_LINT_SCAN_GLOBS` extension is additive. The `is_long_lived_text` parameter rename is a pure refactor. The two exemption additions are conditional and additive. preflight PASSED, command-plan PASSED, decision-lint OK, policy-lint PASSED, run-closeout PASSED.
- Status: PASS
- Answer: All existing behavior is preserved. The changes are purely additive: a new scan glob, a parameter rename (same semantics), and two conditional exemptions. All 989 existing tests pass, confirming no regression in policy-lint v1, decision-command-plan conflict detection, command-plan authority, report-summary, final-check, or closeout behavior.

