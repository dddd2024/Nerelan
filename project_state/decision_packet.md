```json decision_meta
{
  "schema_version": 1,
  "decision_id": "decision_20260716_closeout_order_provenance_rework_v1",
  "round_id": "round_20260716_closeout_order_provenance_rework_v1",
  "based_on_state_build_id": "state_20260618_134029_d6bd033d2532",
  "based_on_state_digest": "d6bd033d25324345cfd8ada0ac65db42bc86eb5017f3ffc92906fcd8b71cacb5",
  "status": "APPROVED",
  "mainline": "project_governance",
  "skill_profiles": ["reverse-agent-iteration@v2"]
}
```

```json decision_contract
{
  "follows_last_decision_id": "decision_20260710_post_closeout_required_audit_truth_rework_v1",
  "follows_last_round_id": "round_20260710_post_closeout_required_audit_truth_rework_v1",
  "previous_audit_outcome": "REWORK_REQUIRED",
  "required_profile": "full",
  "closeout_required": true,
  "close_round_required": true,
  "closeout_allowed": true,
  "pytest_required": true,
  "explicit_pytest_command_required": true,
  "canonical_closeout_order_required": true,
  "execution_log_chronology_required": true,
  "report_finalization_runtime_provenance_required": true,
  "final_archive_refresh_after_report_finalization_required": true,
  "round_manifest_provenance_fields_required": true,
  "report_alias_parity_required": true,
  "state_manifest_freshness_regression_preservation_required": true,
  "context_packet_sync_required": true,
  "post_final_evidence_sync_required": true,
  "command_plan_regeneration_required": true,
  "allowed_source_files": [
    "reverse_agent/project_gate.py",
    "reverse_agent/project_state.py"
  ],
  "allowed_test_files": [
    "tests/test_project_gate.py",
    "tests/test_project_reports.py",
    "tests/test_project_state.py"
  ],
  "allowed_project_state_files": [
    "project_state/state_manifest.json",
    "project_state/context/current_context_packet.json",
    "project_state/gates/*.json",
    "project_state/pytest_result.txt",
    "project_state/codex_execution_report.md",
    "project_state/execution_report.md",
    "project_state/rounds/round_20260716_closeout_order_provenance_rework_v1/*"
  ],
  "read_only_evidence_files": [
    "project_state/rounds/round_20260710_post_closeout_required_audit_truth_rework_v1/round_manifest.json",
    "project_state/rounds/round_20260710_post_closeout_required_audit_truth_rework_v1/codex_execution_report.md",
    "project_state/rounds/round_20260710_post_closeout_required_audit_truth_rework_v1/execution_report.md",
    "project_state/rounds/round_20260710_post_closeout_required_audit_truth_rework_v1/pytest_result.txt",
    "project_state/gates/run_closeout_result.json",
    "project_state/gates/execution_log.json",
    "project_state/gates/final_gate_result.json",
    "reverse_agent/project_runner_contract.py",
    "docs/roadmap/closeout_order_provenance_rework_plan.md"
  ],
  "forbidden_mutated_paths": [
    ".codex-skills/*",
    ".github/workflows/*",
    "frontend/*",
    "solve_reports/*",
    "training_materials/local_reverse/*",
    "reverse_agent/project_state_manifest.py",
    "reverse_agent/project_jobs.py",
    "reverse_agent/project_runner_contract.py",
    "reverse_agent/project_agent_runner.py",
    "reverse_agent/orchestrator_api.py",
    "reverse_agent/user_solve_*.py",
    "project_state/current_state.json",
    "project_state/task_packet.json",
    "project_state/artifact_index.json",
    "project_state/negative_results.json",
    "project_state/roadmap/workstreams.json",
    "project_state/domains/*",
    "project_state/jobs/*",
    "project_state/user_sessions/*",
    "project_state/archives/*",
    "project_state/deletions/*",
    "project_state/blob_store/*",
    "project_state/*.db",
    "project_state/index.sqlite",
    "docs/roadmap/*"
  ],
  "publication_authorization": {
    "granted_by_user": true,
    "applies_to": "manually_invoked_execution_agent_after_required_validation",
    "branch_strategy": "one_short_lived_branch_per_decision_or_pull_request",
    "allowed_branch": "agent/closeout-order-provenance-rework-v1",
    "base_branch": "main",
    "multiple_commits_on_same_branch_allowed": true,
    "reuse_same_branch_for_review_fixes_allowed": true,
    "new_branch_per_commit_required": false,
    "commit_allowed": true,
    "push_allowed": true,
    "draft_pr_allowed": true,
    "direct_push_to_main_allowed": false,
    "force_push_allowed": false,
    "merge_allowed": false,
    "rebase_allowed": false,
    "tag_mutation_allowed": false,
    "remote_branch_deletion_allowed": false,
    "workflow_mutation_allowed": false,
    "secrets_mutation_allowed": false,
    "git_add_all_allowed": false,
    "stage_only_explicit_allowed_paths": true,
    "publish_only_after_required_validation": true,
    "command_plan_must_explicitly_authorize_publication_commands": true,
    "publication_blocked_when_credentials_or_command_authority_missing": true,
    "delete_branch_after_merge_recommended": true
  }
}
```

# DECISION_PACKET

## 1. Goal

Complete one bounded `project_governance` rework round that repairs the closeout-order and provenance defects identified by the independent audit of `round_20260710_post_closeout_required_audit_truth_rework_v1`.

Establish one observable lifecycle:

```text
implementation and tests
→ preliminary report generation
→ stable run-closeout evidence generation
→ report finalization from observed run-closeout evidence
→ report-summary / execution-log / final-check refresh
→ final close-round archive refresh
→ archived/live parity verification
→ post-final context synchronization
```

The system must not claim that `close-round` was the final lifecycle action when the raw transcript proves that a later lifecycle-mutating command occurred. Runtime artifacts must prove that report finalization occurred before the final archive refresh.

The manually invoked execution Agent may use one short-lived branch, `agent/closeout-order-provenance-rework-v1`, for this complete decision and its review fixes. The same branch may contain multiple intentional commits. After all required validation passes, the Agent may push that branch and open a Draft PR to `main` only when the regenerated current command-plan explicitly authorizes the publication commands and credentials are available.

## 2. Current Evidence

- Current task authority is `project_state/decision_packet.md`. `project_state/task_packet.json` is background only.
- Current mainline is `project_governance`.
- The previous independent audit outcome is `REWORK_REQUIRED`.
- The previous raw `pytest_result.txt` and synthesized `execution_log.json` recorded an outer sequence where `close-round` was followed by `run-closeout`.
- The previous `final_gate_result.json` nevertheless reported `close_round_is_last_command_block=PASS`.
- The previous round manifest archive timestamp preceded the final `run_closeout_result.json` timestamp referenced by report finalization.
- Required Audit items 25 and 26 relied mainly on implementation descriptions rather than observed runtime provenance proving report finalization followed by final archive refresh.
- Existing `project_state/gates/command_plan.json` still belongs to `decision_20260710_post_closeout_required_audit_truth_rework_v1`; it is stale for this decision and must be regenerated before any implementation or publication command is executed.
- Existing report, pytest, execution-log, final-gate, run-closeout, context packet, and prior round manifest are evidence inputs only until regenerated for this round.
- `reverse_agent/project_runner_contract.py` is a non-dispatching foundation with `dispatch_enabled=false`, `executable=false`, and `external_invocations.remote_mutation=false`. This round must not claim that the existing automated Runner can publish.
- Publication permission applies only to a manually invoked execution Agent, the named short-lived branch, explicitly staged in-scope files, a current command-plan, and available credentials.
- Existing foundations that must be reused rather than duplicated include project-gate hard checks, command-plan authority, execution-log synthesis, report-summary synthesis, run-closeout, close-round archive, final-check, policy-lint, prompt-consistency, state-manifest freshness, post-final evidence sync, Job and Runner Contract foundations, and the manual-mode orchestrator foundation.
- Missing reverse-solving artifacts and legacy negative-result scope metadata are non-blocking because this is not a sample-solving round.
- No reverse tool, model API, Web runtime, database, scheduler, cleanup apply, or automated Runner dispatch is authorized.
- Heavy artifact reading is not authorized. Do not read the complete `solve_reports/` tree or `PROJECT_PROGRESS_LOG.txt`.
- Closeout is allowed only after the new order/provenance checks and required tests pass.
- This round does not repeat an existing capability: it strengthens the truth and chronology of the existing closeout implementation rather than creating a second closeout framework.

## 3. Do Not Do

Do not:

- implement Goal, Plan, Task, Scheduler, multi-workstream namespaces, Code Review Plane, frontend scheduling, LangGraph, databases, queues, or real Runner dispatch;
- modify `reverse_agent/project_runner_contract.py` or claim that it supports remote mutation;
- modify `.github/workflows`, `.codex-skills`, frontend, User Solve, solver, harness, sample, or reverse-tool code;
- alter `task_packet.json`, `current_state.json`, `artifact_index.json`, `negative_results.json`, or `workstreams.json`;
- run dynamic reverse probes, debuggers, emulators, hooks, or model APIs;
- read the full `solve_reports/` tree or `PROJECT_PROGRESS_LOG.txt`;
- hand-author or reuse the stale previous-round command-plan as current authority;
- reorder execution-log entries to make them match the planned sequence;
- treat code-path descriptions as proof of runtime order;
- embed mutable self-referential report digests;
- push directly to `main`;
- force-push, merge, rebase, tag, edit secrets, delete remote branches, or edit workflows;
- create a new branch for each commit;
- use `git add -A` or stage unrelated files;
- publish before all required validation passes;
- execute publication commands absent from the current command-plan;
- treat user publication authorization as proof that credentials, Runner dispatch, or command authority exist.

## 4. Files To Inspect

Required:

- `project_state/decision_packet.md`
- `project_state/codex_execution_report.md`
- `project_state/execution_report.md`
- `project_state/pytest_result.txt`
- `project_state/state_manifest.json`
- `project_state/context/current_context_packet.json`
- `project_state/gates/command_plan.json`
- `project_state/gates/execution_log.json`
- `project_state/gates/final_gate_result.json`
- `project_state/gates/run_closeout_result.json`
- `project_state/gates/run_closeout_execution_log.json`
- `project_state/gates/report_summary_synthesis.json`
- `project_state/gates/round_close_snapshot.json`
- `project_state/rounds/round_20260710_post_closeout_required_audit_truth_rework_v1/round_manifest.json`
- `project_state/rounds/round_20260710_post_closeout_required_audit_truth_rework_v1/codex_execution_report.md`
- `project_state/rounds/round_20260710_post_closeout_required_audit_truth_rework_v1/pytest_result.txt`
- `reverse_agent/project_gate.py`
- `reverse_agent/project_state.py`
- `tests/test_project_gate.py`
- `tests/test_project_reports.py`
- `tests/test_project_state.py`
- `.codex-skills/registry.json`

Read-only context:

- `reverse_agent/project_runner_contract.py`
- `docs/roadmap/closeout_order_provenance_rework_plan.md`

Do not inspect unrelated source trees unless a failing required test directly identifies an in-scope dependency and the Stop Conditions are followed.

## 5. Required Audit

The final execution report must answer every item below with current artifact paths and observed runtime fields. Implementation descriptions alone are insufficient.

1. Is `decision_meta` valid JSON with `schema_version=1`?
2. Is status `APPROVED` and mainline `project_governance`?
3. Is `reverse-agent-iteration@v2` active in `.codex-skills/registry.json`?
4. Is `decision_packet.md` treated as the sole current task authority and `task_packet.json` as background only?
5. Is the previous independent audit outcome recorded as `REWORK_REQUIRED`?
6. Was the stale previous-round command-plan rejected and regenerated for this decision and round?
7. Does the regenerated command-plan carry the current decision ID and round ID?
8. Does the regenerated command-plan explicitly authorize every executed command and preserve omitted-command restrictions?
9. Were any unauthorized or omitted commands executed?
10. Is the round limited to closeout chronology and provenance repair?
11. Were the existing closeout, report-summary, execution-log, final-check, archive, state-manifest, and post-final-sync mechanisms reused rather than duplicated?
12. Does `pytest_result.txt` preserve the observed command order?
13. Does `execution_log.json` preserve the observed transcript chronology without reordering?
14. Do `pytest_result.txt` and `execution_log.json` agree on the final lifecycle-mutating command?
15. Does `final_gate_result.json` derive its command-order conclusion from the observed transcript?
16. Does final-check fail when the transcript proves a command occurred after the claimed final close-round?
17. Is stable run-closeout evidence generated before report finalization?
18. Does report finalization identify the live `run_closeout_result.json` path?
19. Does report finalization contain the full live run-closeout SHA-256?
20. Does report finalization match the live run-closeout `generated_at` and status?
21. Does report finalization record an observed `report_finalized_at`?
22. Is `report_finalized_at` later than or equal to the referenced stable closeout evidence time?
23. Does the final archive refresh occur after report finalization?
24. Does the final round manifest or equivalent closeout artifact record `archive_refreshed_at`?
25. Is `archive_refreshed_at >= report_finalized_at` proven by current artifact fields?
26. Does the final archive provenance record its basis and status?
27. Does the archived report digest match the final live report digest at archive time?
28. Do archived and live `codex_execution_report.md` match?
29. Do archived and live `execution_report.md` match?
30. Do archived and live `pytest_result.txt` match?
31. Does the round manifest match the final decision, report, pytest, and closeout state?
32. Do both report aliases carry semantically identical summary and report-finalization fields?
33. Does `report_summary_synthesis.json` match both final report aliases?
34. Does final-check include and pass chronology, report-finalization, archive-refresh, and archived/live parity checks?
35. Does final-check preserve `state_manifest_freshness=PASS`?
36. Does `current_context_packet.json` match the current decision and round after post-final sync?
37. Does post-final evidence sync prove that context was generated after the final gate state it references?
38. Does the final Required Audit body avoid placeholders, generic claims, contradictions, and future-tense completion claims?
39. Do Required Audit answers cite current artifact paths and observed fields rather than only function names or design steps?
40. Were all forbidden paths left untouched?
41. Were only explicitly allowed source, test, and project-state files modified?
42. Were no Runner, Web, workflow, model API, database, cleanup, reverse-tool, or sample-solving capabilities used?
43. Was publication withheld until required validation passed?
44. If publication occurred, was one short-lived branch reused for all commits and review fixes?
45. If publication occurred, were only explicit in-scope paths staged?
46. If publication occurred, did the current command-plan explicitly authorize branch/commit/push/PR commands?
47. If publication occurred, was direct push to `main`, force push, merge, rebase, tag mutation, workflow mutation, and secret mutation avoided?
48. If publication could not occur because credentials or command authority were absent, did the report state that limitation without claiming success?

## 6. Implementation Scope

Implement only the smallest compatible changes necessary to establish the canonical closeout lifecycle and runtime provenance.

### 6.1 Canonical Closeout Lifecycle

Establish one code path with this semantic order:

```text
startup and baseline
→ implementation and tests
→ preliminary report generation
→ preliminary validation
→ generate stable run-closeout evidence
→ finalize report from observed run-closeout evidence
→ refresh report-summary
→ refresh execution-log
→ refresh final-check
→ final close-round/archive refresh
→ final live/archive parity verification
→ post-final context sync
```

Do not allow an outer executor to compose `close-round` and `run-closeout` in an order that contradicts the canonical lifecycle.

### 6.2 Command-Order Truth

- Preserve actual order in `pytest_result.txt`.
- Preserve actual order in `execution_log.json`.
- Derive final-command conclusions from the raw observed transcript.
- Hard-fail when transcript, execution log, and final-gate order claims disagree.
- Keep command-plan coverage and expected-exit policy separate from runtime chronology.

### 6.3 Report-Finalization Provenance

Add or validate structured fields equivalent to:

```text
report_finalized_at
report_finalization_basis
run_closeout_result_path
run_closeout_result_sha256
run_closeout_generated_at
run_closeout_status
embedded_close_round_status
```

The final report must not embed its own digest or mutable final-gate/report-summary digests.

### 6.4 Final Archive-Refresh Provenance

Add or validate fields in `round_manifest.json` or an equivalent current closeout artifact:

```text
report_finalized_at
archive_refreshed_at
archive_refresh_basis
archived_report_sha256
live_report_sha256_at_archive
final_archive_refresh_status
```

Enforce:

```text
archive_refreshed_at >= report_finalized_at
archived_report_sha256 == live_report_sha256_at_archive
```

Closeout must fail if report finalization is not followed by a final archive refresh.

### 6.5 Required Audit Runtime Evidence

Required Audit answers for report-finalization and final archive-refresh order must cite live artifact fields and timestamps. They may cite implementation locations as supporting context, but not as the sole evidence.

### 6.6 Compatibility and File Scope

- Preserve existing public fields and CLI behavior unless a new optional provenance field is required.
- Keep legacy artifacts readable.
- Do not migrate unrelated state files.
- Do not modify modules outside the explicit allowlist.
- Generated artifacts are limited to current gate/report/context/state-manifest files and the current round archive.

### 6.7 Controlled Publication

After all required validation passes, a manually invoked Agent may:

```text
create or reuse agent/closeout-order-provenance-rework-v1
stage only explicit in-scope files
create multiple intentional commits on that branch
push that branch
open a Draft PR targeting main
```

Only do so when the regenerated current command-plan explicitly lists the exact publication commands and credentials are available. Publication failure must not invalidate a successfully completed local implementation, but it must be reported as a limitation and must not be represented as completed publication.

## 7. Tests

Run the exact pytest command selected by the regenerated command-plan. It must include at least:

```text
python -m pytest tests/test_project_gate.py tests/test_project_reports.py tests/test_project_state.py -q
```

Add regression coverage for all of the following:

1. A transcript where `close-round` occurs before a later `run-closeout` fails chronology validation.
2. `execution_log.json` cannot reorder transcript entries to satisfy the planned order.
3. A mismatch between the transcript final command and the final-gate claim fails.
4. `report_finalized_at` missing when required fails.
5. `archive_refreshed_at` missing when required fails.
6. `archive_refreshed_at < report_finalized_at` fails.
7. Report finalization without a subsequent final archive refresh fails.
8. Archived report digest differing from the final live report digest fails.
9. Report aliases with different finalization fields fail.
10. Required Audit items using only function descriptions and no runtime artifact fields fail.
11. Stale previous-round command-plan IDs fail current preflight or command authority validation.
12. Correct lifecycle order passes:

```text
stable closeout evidence
→ report finalization
→ summary/log/final-check refresh
→ final close-round/archive refresh
→ parity verification
```

13. Existing state-manifest freshness behavior remains passing.
14. Existing post-final context sync behavior remains passing.
15. Publication commands absent from command-plan are rejected.
16. Direct push to `main`, force push, merge, rebase, tag mutation, workflow mutation, and `git add -A` remain prohibited by the Decision and execution prompt.

Required generated evidence:

- `project_state/pytest_result.txt`
- `project_state/codex_execution_report.md`
- `project_state/execution_report.md`
- current `project_state/gates/*.json` required by the selected profile
- `project_state/rounds/round_20260716_closeout_order_provenance_rework_v1/round_manifest.json`
- final archived report and pytest aliases for the current round

## 8. Stop Conditions

Stop implementation and report `BLOCKED` or `REWORK_REQUIRED` as appropriate if any of the following occurs:

- `decision-lint`, preflight, or regenerated command-plan cannot validate the current decision and round;
- the current state build ID or digest no longer matches the decision basis and the project requires a new state build;
- completing the fix requires modifying a forbidden path;
- completing the fix requires changing workflows, Runner contracts, Job schemas, frontend, User Solve, reverse-solving, databases, or other mainlines;
- the canonical lifecycle cannot be established without creating a second closeout framework;
- tests cannot prove transcript chronology, report-finalization timing, final archive-refresh timing, and archived/live parity;
- the final report contains future-tense completion claims, stale exact metadata, placeholders, or contradictions;
- state-manifest freshness or post-final context synchronization regresses;
- required tests fail;
- final-check fails;
- the final round archive does not match the final live report and pytest evidence;
- publication is requested but the command-plan does not explicitly authorize the exact commands;
- publication credentials are unavailable;
- the working tree contains unrelated changes that cannot be safely excluded from staging;
- the named branch cannot be created or reused without force push, rebase, or overwriting unrelated work.

Do not expand scope to solve a stop condition. Record the blocker in `project_state/codex_execution_report.md`, preserve the execution log and pytest evidence, and stop.