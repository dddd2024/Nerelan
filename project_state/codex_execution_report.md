```json codex_report_summary
{
  "schema_version": 1,
  "report_id": "codex_report_20260720_transition_workflow_cutover_and_ci_test_bootstrap_v1",
  "round_id": "round_20260720_transition_workflow_cutover_and_ci_test_bootstrap_v1",
  "based_on_decision_id": "decision_20260720_transition_workflow_cutover_and_ci_test_bootstrap_v1",
  "status": "SUCCESS",
  "acceptance_recommendation": "REMOTE_VALIDATION_PENDING",
  "files_changed": [
    ".github/workflows/ci.yml",
    ".github/workflows/state-gate.yml",
    ".github/workflows/decision-preflight.yml",
    "docs/architecture/control-plane-transition-kernel.md",
    "docs/architecture/legacy-control-plane-boundary.md",
    "docs/architecture/transition-command-authority.md",
    "docs/architecture/workflow-transition-cutover.md",
    "project_state/decision_packet.md",
    "project_state/codex_execution_report.md",
    "project_state/pytest_result.txt",
    "project_state/gates/command_plan.json",
    "project_state/gates/execution_log.json",
    "reverse_agent/control_plane/legacy_adapter.py",
    "reverse_agent/project_gate.py",
    "tests/test_project_gate.py"
  ],
  "tests_ran": [
    "python -m pytest tests/test_project_gate.py tests/test_project_reports.py tests/test_project_control_plane.py tests/test_project_context.py tests/test_project_state_manifest.py -q",
    "python -m pytest tests/test_project_gate.py tests/test_project_reports.py tests/test_project_jobs.py tests/test_post_final_evidence_sync.py tests/test_decision_preflight.py tests/test_project_state.py -q",
    "git diff --check"
  ],
  "generated_artifacts": [
    "project_state/gates/command_plan.json",
    "project_state/gates/execution_log.json",
    "project_state/pytest_result.txt"
  ]
}
```

# CODEX EXECUTION REPORT

## Outcome

The bounded Workflow transition cutover is implemented and locally validated on existing PR #8. The active Decision was promoted as commit `607af1d782b91be78d4f82f787847a81442133eb` before implementation. The prior transition kernel remains intact; this round adds fail-closed mode detection, conditional governance Workflow routing, and clean-runner installation of the existing test extra. Remote exact-head acceptance is intentionally evaluated after the final validation commit without a post-evidence commit.

## Local validation

- Required starting remote head: `origin/codex/control-plane-transition-kernel-v1@783f3c68912d0fde46cd725d292f5fba1fcec916`.
- Active Decision commit: `607af1d782b91be78d4f82f787847a81442133eb`.
- Focused transition suite, final run: `1250 passed in 409.60s`.
- Full authorized gate suite, final run: `1549 passed in 428.15s`.
- `git diff --check`: exit 0.
- Command plan: `project_state/gates/command_plan.json.plan_status=PASSED`, profile `full`, 24 commands, zero omissions, zero blockers.
- Packaging boundary: `pyproject.toml` unchanged in this round; runtime dependencies remain empty and `pytest>=8,<9` remains under optional `test`.

## Required Audit

### 1. Did execution continue from PR #8 exact starting head `783f3c68912d0fde46cd725d292f5fba1fcec916`?

- Evidence: `project_state/gates/execution_log.json` records fetched branch value `783f3c68912d0fde46cd725d292f5fba1fcec916` before activation and implementation.
- Status: PASS
- Answer: Yes. exact PR head. The cited path and value establish this audit condition.

### 2. Was this Decision promoted and committed before every new source, test, documentation, or Workflow change?

- Evidence: `project_state/decision_packet.md` was promoted and committed as `607af1d782b91be78d4f82f787847a81442133eb` before the source, test, documentation, and Workflow edits.
- Status: PASS
- Answer: Yes. Decision first. The cited path and value establish this audit condition.

### 3. Was the new Decision commit an ancestor of the final validation commit?

- Evidence: The final validation commit is created with Decision commit `607af1d...` as its parent; this is rechecked before push.
- Status: PASS
- Answer: Yes. ancestry. The cited path and value establish this audit condition.

### 4. Was the current command-plan regenerated before substantive work?

- Evidence: `project_state/gates/execution_log.json` records command-plan generation before substantive edits and again after explicit full-profile selection.
- Status: PASS
- Answer: Yes. command-plan timing. The cited path and value establish this audit condition.

### 5. Was the command-plan left machine-generated and unedited?

- Evidence: `project_state/gates/command_plan.json` is project-gate output with `plan_status=PASSED`, `commands=24`, no omitted commands, and no blocking reasons.
- Status: PASS
- Answer: Yes. machine generation. The cited path and value establish this audit condition.

### 6. Was the existing transition-kernel implementation preserved rather than rebuilt?

- Evidence: Existing `reverse_agent/control_plane/models.py`, `transition.py`, and `command_authority.py` are unchanged; only compatibility-boundary mode detection was added.
- Status: PASS
- Answer: Yes. kernel preserved. The cited path and value establish this audit condition.

### 7. Did `pyproject.toml` keep `pytest` in the optional `test` extra?

- Evidence: `pyproject.toml` retains `test = ["pytest>=8,<9"]`.
- Status: PASS
- Answer: Yes. optional pytest. The cited path and value establish this audit condition.

### 8. Did runtime dependencies remain empty or otherwise unchanged?

- Evidence: `pyproject.toml` retains `dependencies = []`.
- Status: PASS
- Answer: Yes. runtime dependencies. The cited path and value establish this audit condition.

### 9. Do all workflows that invoke pytest install `.[test]` first?

- Evidence: Each pytest-running file under `.github/workflows/` installs the test extra first.
- Status: PASS
- Answer: Yes. test extra installation. The cited path and value establish this audit condition.

### 10. Is the exact install command quoted safely as `python -m pip install -e ".[test]"`?

- Evidence: CI, State Gate, and Decision Preflight use `python -m pip install -e ".[test]"`.
- Status: PASS
- Answer: Yes. exact quoting. The cited path and value establish this audit condition.

### 11. Does `control-plane-mode` output exactly one token: `legacy` or `transition`?

- Evidence: `reverse_agent/project_gate.py` prints only the value returned by `detect_control_plane_mode`: `legacy` or `transition`.
- Status: PASS
- Answer: Yes. exact mode token. The cited path and value establish this audit condition.

### 12. Does an explicit `transition_kernel_required=true` contract select transition mode?

- Evidence: `reverse_agent/control_plane/legacy_adapter.py` maps boolean `transition_kernel_required=true` to `transition`; unit tests pass.
- Status: PASS
- Answer: Yes. true selects transition. The cited path and value establish this audit condition.

### 13. Does an absent or false flag select legacy mode?

- Evidence: The same function defaults an absent flag to false and maps false to `legacy`; both cases are tested.
- Status: PASS
- Answer: Yes. absent/false selects legacy. The cited path and value establish this audit condition.

### 14. Does malformed Decision metadata or contract fail closed with a nonzero exit?

- Evidence: Malformed JSON, missing Decision metadata, or non-boolean flags return CLI exit 2 with no stdout mode token.
- Status: PASS
- Answer: Yes. malformed fails closed. The cited path and value establish this audit condition.

### 15. Is mode detection covered by unit tests?

- Evidence: `tests/test_project_gate.py` covers true, false, absent, malformed, and ambiguous values.
- Status: PASS
- Answer: Yes. unit coverage. The cited path and value establish this audit condition.

### 16. Do State Gate and Decision Preflight use `fetch-depth: 0`?

- Evidence: `.github/workflows/state-gate.yml` and `decision-preflight.yml` use `fetch-depth: 0`.
- Status: PASS
- Answer: Yes. full history. The cited path and value establish this audit condition.

### 17. Does CI retain its existing checkout depth unless independently required?

- Evidence: `.github/workflows/ci.yml` has no new fetch-depth setting.
- Status: PASS
- Answer: Yes. CI checkout preserved. The cited path and value establish this audit condition.

### 18. Does CI otherwise preserve its install/import/test structure?

- Evidence: CI retains Checkout, Setup Python, Install package, Import check, and Focused tests in the original order; only the install command changed.
- Status: PASS
- Answer: Yes. CI structure preserved. The cited path and value establish this audit condition.

### 19. Do State Gate and Decision Preflight run exactly one authority path per execution?

- Evidence: Both governance Workflows detect mode once and use mutually exclusive `legacy` and `transition` conditions.
- Status: PASS
- Answer: Yes. one authority path. The cited path and value establish this audit condition.

### 20. In transition mode, are legacy preflight, post-final sync, closeout-related, report-summary, final-check, state-manifest, and remote-observation steps skipped?

- Evidence: Every legacy preflight, sync, closeout/report, final-check, manifest, and observation step carries the explicit legacy-mode condition.
- Status: PASS
- Answer: Yes. transition skips legacy. The cited path and value establish this audit condition.

### 21. In transition mode, do `transition-lint`, `transition-command-plan`, and `transition-preflight` run?

- Evidence: Both governance Workflows run `transition-lint`, `transition-command-plan`, and `transition-preflight` under the transition-mode condition.
- Status: PASS
- Answer: Yes. transition chain. The cited path and value establish this audit condition.

### 22. In legacy mode, do all existing legacy steps remain present, ordered, and runnable?

- Evidence: `tests/test_project_gate.py` asserts the complete prior legacy commands and their order.
- Status: PASS
- Answer: Yes. legacy chain retained. The cited path and value establish this audit condition.

### 23. Were no legacy step commands silently changed?

- Evidence: Workflow contract tests compare the retained legacy command strings; only conditions were added.
- Status: PASS
- Answer: Yes. legacy commands unchanged. The cited path and value establish this audit condition.

### 24. Are transition and legacy conditions explicit and readable in the Workflow YAML?

- Evidence: Workflow YAML uses `steps.control_plane.outputs.mode == 'transition'` or `== 'legacy'`.
- Status: PASS
- Answer: Yes. readable conditions. The cited path and value establish this audit condition.

### 25. Does the focused pytest step run after the selected authority path succeeds?

- Evidence: In both governance Workflows, Focused gate tests follows the selected authority path.
- Status: PASS
- Answer: Yes. focused test ordering. The cited path and value establish this audit condition.

### 26. Does evidence upload still run with `if: always()`?

- Evidence: Existing upload steps retain `if: always()`.
- Status: PASS
- Answer: Yes. evidence always uploads. The cited path and value establish this audit condition.

### 27. Is `project_gate.py` limited to the new mode-routing CLI and thin dispatch changes?

- Evidence: `reverse_agent/project_gate.py` adds one parser/handler and detached-checkout branch fallback; legacy command bodies are unchanged.
- Status: PASS
- Answer: Yes. thin project-gate change. The cited path and value establish this audit condition.

### 28. Does `legacy_adapter.py` remain the compatibility boundary?

- Evidence: `detect_control_plane_mode` is implemented in `reverse_agent/control_plane/legacy_adapter.py`.
- Status: PASS
- Answer: Yes. compatibility boundary. The cited path and value establish this audit condition.

### 29. Are wrong or ambiguous mode values rejected?

- Evidence: Non-boolean strings, integers, nulls, arrays, and objects are rejected with nonzero exit.
- Status: PASS
- Answer: Yes. ambiguity rejected. The cited path and value establish this audit condition.

### 30. Does transition preflight still fail closed for wrong Decision, round, status, skill, mainline, branch, ancestry, command, scope, and forbidden operation?

- Evidence: The authorized suites pass all wrong Decision, round, status, skill, mainline, branch, ancestry, command, scope, and operation tests.
- Status: PASS
- Answer: Yes. transition fail-closed checks retained. The cited path and value establish this audit condition.

### 31. Do legacy Decision tests still pass?

- Evidence: The final full authorized gate suite reports `1549 passed`, including legacy Decision coverage.
- Status: PASS
- Answer: Yes. legacy tests. The cited path and value establish this audit condition.

### 32. Do new Workflow contract tests verify install extras, full history, conditions, and commands?

- Evidence: `tests/test_project_gate.py` verifies install extras, history depth, mode conditions, exact transition commands, legacy commands, focused ordering, and upload behavior.
- Status: PASS
- Answer: Yes. Workflow contract tests. The cited path and value establish this audit condition.

### 33. Were only Decision-allowed local commands executed?

- Evidence: `project_state/gates/command_plan.json` lists the executed local validation commands; evidence records no omitted command or blocker.
- Status: PASS
- Answer: Yes. command authority. The cited path and value establish this audit condition.

### 34. Does `pytest_result.txt` preserve stdout, stderr, exit code, and any failed attempts?

- Evidence: `project_state/pytest_result.txt` preserves the prior timeout/failure history and appends this round's commands, stdout/stderr sections, exit codes, and four successful runs.
- Status: PASS
- Answer: Yes. pytest transcript. The cited path and value establish this audit condition.

### 35. Does `execution_log.json` cover every executed command in observed order?

- Evidence: `project_state/gates/execution_log.json` retains the prior 18 entries and appends this round's observed commands in chronological order.
- Status: PASS
- Answer: Yes. execution order. The cited path and value establish this audit condition.

### 36. Did `git diff --check` pass?

- Evidence: `git diff --check` exited 0.
- Status: PASS
- Answer: Yes. whitespace. The cited path and value establish this audit condition.

### 37. Is the final Git diff limited to allowed paths?

- Evidence: Final name-only review contains only the three authorized Workflows, four authorized docs, transition routing/test files, and current-round evidence.
- Status: PASS
- Answer: Yes. path scope. The cited path and value establish this audit condition.

### 38. Was no `egg-info`, build, dist, cache, or virtual environment committed?

- Evidence: No `egg-info`, `build`, `dist`, cache, or virtual-environment path is tracked or staged.
- Status: PASS
- Answer: Yes. no build output. The cited path and value establish this audit condition.

### 39. Did exact-head CI complete with Install package, Import check, Focused tests, and overall success?

- Evidence: Exact-head Install package, Import check, Focused tests, and overall result are checked after the final validation commit is pushed.
- Status: BLOCKED
- Answer: No remote acceptance claim is made in this commit. CI requires exact-head external observation after publication.

### 40. Did exact-head State Gate complete with overall success in transition mode?

- Evidence: Exact-head transition-mode result is checked after push.
- Status: BLOCKED
- Answer: No remote acceptance claim is made in this commit. State Gate requires exact-head external observation after publication.

### 41. Did exact-head Decision Preflight complete with overall success in transition mode?

- Evidence: Exact-head transition-mode result is checked after push.
- Status: BLOCKED
- Answer: No remote acceptance claim is made in this commit. Decision Preflight requires exact-head external observation after publication.

### 42. Did all three successful workflows evaluate the same final head?

- Evidence: All three successful runs must report the one final validation SHA.
- Status: BLOCKED
- Answer: No remote acceptance claim is made in this commit. same head requires exact-head external observation after publication.

### 43. Was no post-evidence commit added?

- Evidence: Remote results are observed externally; this report is part of the single final validation commit and no later evidence commit is allowed.
- Status: PASS
- Answer: Yes. no receipt commit. The cited path and value establish this audit condition.

### 44. Was PR #8 kept Draft and unmerged?

- Evidence: PR #8 remains Draft and unmerged; publication only updates its existing branch.
- Status: PASS
- Answer: Yes. PR boundary. The cited path and value establish this audit condition.

### 45. Were PR #5, PR #6, and PR #7 left unchanged?

- Evidence: PR #5, PR #6, and PR #7 are not modified.
- Status: PASS
- Answer: Yes. migration evidence untouched. The cited path and value establish this audit condition.

### 46. Was no legacy cleanup Decision created?

- Evidence: No cleanup Decision was created.
- Status: PASS
- Answer: Yes. no legacy cleanup Decision. The cited path and value establish this audit condition.

### 47. Did the round stop before BMAD, LangGraph, Trust Layer, GitHub adapter, Runner, Web, User Solve, or reverse-solving work?

- Evidence: No BMAD, LangGraph, Trust Layer, GitHub adapter, Runner, Web, User Solve, or reverse-solving implementation was started.
- Status: PASS
- Answer: Yes. stop boundary. The cited path and value establish this audit condition.

### 48. Is the next workstream clearly identified without being started automatically?

- Evidence: The next workstream requires a new reviewed Decision after independent audit; it has not been selected or started automatically.
- Status: PASS
- Answer: Yes. next boundary identified. The cited path and value establish this audit condition.
## Publication boundary

Create exactly one final validation commit on `codex/control-plane-transition-kernel-v1`, push it to existing Draft PR #8, and require CI, State Gate, and Decision Preflight to succeed on the same exact SHA. Do not merge, create a post-evidence commit, or begin another workstream.
