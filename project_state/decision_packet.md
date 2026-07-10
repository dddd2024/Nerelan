```json decision_meta
{
  "schema_version": 1,
  "decision_id": "decision_20260710_post_closeout_required_audit_truth_rework_v1",
  "round_id": "round_20260710_post_closeout_required_audit_truth_rework_v1",
  "based_on_state_build_id": "state_20260618_134029_d6bd033d2532",
  "based_on_state_digest": "d6bd033d25324345cfd8ada0ac65db42bc86eb5017f3ffc92906fcd8b71cacb5",
  "status": "APPROVED",
  "mainline": "project_governance",
  "skill_profiles": ["reverse-agent-iteration@v2"]
}
```

```json decision_contract
{
  "follows_last_decision_id": "decision_20260710_state_manifest_freshness_rework_v1",
  "follows_last_round_id": "round_20260710_state_manifest_freshness_rework_v1",
  "previous_audit_outcome": "REWORK_REQUIRED",
  "required_profile": "full",
  "closeout_required": true,
  "close_round_required": true,
  "closeout_allowed": true,
  "pytest_required": true,
  "explicit_pytest_command_required": true,
  "required_audit_future_completion_claim_rejection_required": true,
  "required_audit_live_claim_alignment_required": true,
  "post_closeout_report_finalization_required": true,
  "report_finalization_block_required": true,
  "report_alias_parity_required": true,
  "state_manifest_freshness_regression_preservation_required": true,
  "context_packet_sync_required": true,
  "post_final_evidence_sync_required": true,
  "no_self_referential_report_digest_required": true,
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
    "project_state/rounds/round_20260710_post_closeout_required_audit_truth_rework_v1/*"
  ],
  "read_only_evidence_files": [
    "project_state/rounds/round_20260710_state_manifest_freshness_rework_v1/round_manifest.json",
    "project_state/rounds/round_20260710_state_manifest_freshness_rework_v1/codex_execution_report.md",
    "project_state/rounds/round_20260710_state_manifest_freshness_rework_v1/execution_report.md",
    "reverse_agent/project_state_manifest.py",
    "tests/test_project_state_manifest.py",
    "docs/roadmap/trustworthy_hostile_binary_analysis_long_term_plan.md"
  ],
  "forbidden_mutated_paths": [
    ".codex-skills/*",
    ".github/workflows/*",
    "frontend/*",
    "solve_reports/*",
    "training_materials/local_reverse/*",
    "reverse_agent/project_state_manifest.py",
    "reverse_agent/user_solve_contract.py",
    "reverse_agent/user_solve_state.py",
    "reverse_agent/user_solve_errors.py",
    "reverse_agent/user_solve_views.py",
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
  ]
}
```

# DECISION_PACKET

## 1. Goal

Advance one bounded `project_governance` rework round to repair the final truth chain of the existing Required Audit and closeout workflow.

The previous round successfully implemented current-file freshness validation for `state_manifest.json`. The live manifest, pytest, final gate, post-final context sync, run-closeout, and round archive all reached current passing states. The subsequent manual audit nevertheless returned `REWORK_REQUIRED` because the human-readable `## Required Audit` body was finalized too early and then became stale while later closeout artifacts were regenerated.

This round must do only the following:

```text
1. Reject future-tense completion claims in SUCCESS / ACCEPTED Required Audit answers.
2. Reject explicit SHA-256 or size claims that do not match current live evidence.
3. Bind the final report to the actual current run-closeout result through a small structured finalization block.
4. Establish a stable order: closeout evidence first, final report second, final archive refresh last.
5. Preserve the already-working state-manifest freshness validation without redesigning it.
6. Regenerate the current reports, gates, context, tests, and round archive with truthful final evidence.
```

The target is not another report framework. The target is to prevent a report from passing merely because its questions are present while its answers describe future actions, copied pre-closeout values, or claims contradicted by live artifacts.

## 2. Current Evidence

Current task authority:

```text
project_state/decision_packet.md
```

Current command authority:

```text
project_state/gates/command_plan.json
```

Current mainline:

```text
project_governance
```

`task_packet.json` remains background only. It contains older `samplereverse` state and must not control this governance rework.

The previous implemented round is:

```text
decision_id: decision_20260710_state_manifest_freshness_rework_v1
round_id: round_20260710_state_manifest_freshness_rework_v1
report_id: codex_report_20260710_state_manifest_freshness_rework_v1
report status: SUCCESS
report recommendation: ACCEPTED
pytest: 1196 passed, exit code 0
final_gate_result.json: PASSED
state_manifest_freshness: PASS
post_final_evidence_sync_result.json: PASSED
run_closeout_result.json: PASSED
close_round_result.close_status: CLOSED
```

The previous round added and passed the correct foundational capability:

```text
state_manifest current artifact references are validated against live files;
stale decision_id is rejected;
stale round_id is rejected;
stale current-artifact SHA-256 is rejected;
stale current-artifact size is rejected;
missing required current files are rejected.
```

That capability is accepted as an existing foundation and must be reused. Do not reimplement or broaden it in this round.

The audit finding controlling this rework is report truth, not manifest truth.

The previous `codex_execution_report.md` and `execution_report.md` contained Required Audit answers that claimed final values from an earlier execution stage. Examples include:

```text
claimed pytest_result:
  sha256 prefix=e036bfa9021d94dc
  size_bytes=15387

current state_manifest pytest_result:
  sha256=7e19e489e26dcf2206640d78fc499470982b60c6cf178b83906dfaea5c1d06b6
  size_bytes=15517

claimed command_plan:
  sha256 prefix=721e1624ba1eda5a
  size_bytes=4845

current state_manifest command_plan:
  sha256=0b8c4238a95efbab4ff6da025da7baa575afcd7d8d2f5159eacf062c3dab8c95
  size_bytes=4845

claimed execution_log:
  sha256 prefix=f8b418865a1efa7a
  size_bytes=5784

current state_manifest execution_log:
  sha256=74754bf87fe7362f36cb8e0b11dee6250f719a761b75ffb0973292f440d46525
  size_bytes=5849

claimed final_gate_result:
  sha256 prefix=f17c17a4b9af63c9
  size_bytes=80891

current state_manifest final_gate_result:
  sha256=e890cb89e9c0fc93b810c3794f2cac82a15ed6304ed2cd453524783a629226a4
  size_bytes=83898

claimed report_summary_synthesis:
  sha256 prefix=3407bf966f504bcc
  size_bytes=14179

current state_manifest report_summary_synthesis:
  sha256=3c892afbd40551f803f2d12ec621fd7592d317f409b9e06b2ae183109f34b755
  size_bytes=14537

claimed run_closeout_result:
  sha256 prefix=57b5d3b33f4d72fa
  size_bytes=51303

current state_manifest run_closeout_result:
  sha256=67e045644e4bbe83071c821740d06049baa57fa675c5f8cb4bd5d0973ef051be
  size_bytes=53117
```

The previous report also used future-tense completion statements while marking the corresponding items `PASS`, including forms equivalent to:

```text
will be PASSED
will match
will be generated
after final-check
after close-round
```

It then claimed that no future-tense answers were present. That is internally contradictory.

Existing abilities that must be reused rather than duplicated:

```text
decision-lint
preflight
gate-profile
command-plan
execution-log
report-summary
Required Audit extraction and coverage
Required Audit placeholder detection
Required Audit question/answer alignment checks
report alias semantic parity
status-policy checks
state_manifest freshness validation
final-check
post-final evidence sync
run-closeout
close-round
round archive and round manifest
```

Current artifact state:

```text
state_manifest.json is current for the previous round;
current_context_packet.json is current and post-final synchronized;
workstreams.json exists but contains older lifecycle state and is not execution authority;
missing historical sample artifacts remain nonblocking for project_governance;
negative_results.json contains reverse_solving constraints only and must not be modified.
```

Capability permissions:

```text
local deterministic Python: allowed through command-plan
pytest: allowed through command-plan
existing project gate commands: allowed through command-plan
report and JSON artifact generation: allowed
external reverse tools: not allowed
sample solving: not allowed
model API invocation: not allowed
runner dispatch: not allowed
Web/frontend runtime: not allowed
remote workflow dispatch: not allowed
database creation: not allowed
cleanup/deletion/archive compaction apply: not allowed
```

Repeat check:

```text
Do not build another report system.
Do not build another state manifest system.
Do not build another command-plan, execution-log, report-summary, final-check, or closeout framework.
Extend the existing Required Audit and final-check path only enough to enforce final evidence truth.
```

## 3. Do Not Do

Do not perform reverse-solving work, sample execution, candidate search, runtime probing, dynamic debugging, emulation, hooking, or external binary analysis.

Do not implement the hostile-binary Trust Layer, Binary Evidence Firewall, Claim Graph, Counterevidence Graph, Action Provenance Guard, Analysis Capsule, or Trust Workbench in this round.

Do not modify the hostile-binary long-term roadmap.

Do not modify roadmap workstreams or attempt to correct their older lifecycle fields in this round.

Do not modify `reverse_agent/project_state_manifest.py`. The current manifest builder and freshness validator are accepted foundations for this rework.

Do not create a parallel execution-report format, parallel final gate, parallel manifest, parallel closeout command, or separate audit database.

Do not solve the defect merely by deleting all evidence values or replacing them with vague statements such as:

```text
validated successfully
everything matches
the gate passed
current evidence is correct
```

Required Audit answers must remain substantive and question-specific.

Do not permit `SUCCESS / ACCEPTED` answers containing unresolved completion language such as:

```text
will be
will match
will report
will be generated
will be refreshed
to be generated
to be updated
after the final command
after closeout completes
```

Do not hard-code the report's own SHA-256 into that same report.

Do not require a report to embed the final report's own digest. That creates a self-referential value which changes when the report changes.

Do not require the report to copy a final-gate digest that will be regenerated after report finalization. Use the structured live gate result and final-check status instead.

Do not silently treat an abbreviated digest prefix as proof of an exact SHA-256 match. If an accepted report explicitly claims an exact SHA-256, it must use the full 64-character value and it must match live evidence.

Do not weaken status-policy, report-summary, manifest freshness, alias parity, command authorization, pytest, final-check, post-final sync, run-closeout, or archive checks merely to make the round pass.

Do not modify:

```text
project_state/current_state.json
project_state/task_packet.json
project_state/artifact_index.json
project_state/negative_results.json
project_state/roadmap/workstreams.json
project_state/domains/*
project_state/jobs/*
project_state/user_sessions/*
.codex-skills/*
.github/workflows/*
frontend/*
solve_reports/*
training_materials/local_reverse/*
project_state/archives/*
project_state/deletions/*
project_state/blob_store/*
project_state/*.db
project_state/index.sqlite
docs/roadmap/*
```

Do not read full `solve_reports/`, full `PROJECT_PROGRESS_LOG.txt`, or full historical round directories.

## 4. Files To Inspect

Required authority and current state:

```text
project_state/decision_packet.md
.codex-skills/registry.json
project_state/task_packet.json
project_state/current_state.json
project_state/artifact_index.json
project_state/negative_results.json
project_state/state_manifest.json
project_state/context/current_context_packet.json
project_state/roadmap/workstreams.json
project_state/codex_execution_report.md
project_state/execution_report.md
project_state/pytest_result.txt
```

Required current gate evidence:

```text
project_state/gates/command_plan.json
project_state/gates/execution_log.json
project_state/gates/report_summary_synthesis.json
project_state/gates/final_gate_result.json
project_state/gates/run_closeout_result.json
project_state/gates/run_closeout_execution_log.json
project_state/gates/post_final_evidence_sync_result.json
project_state/gates/post_final_evidence_sync_snapshot.json
project_state/gates/round_baseline.json
project_state/gates/round_delta_summary.json
project_state/gates/round_close_snapshot.json
```

Previous-round read-only evidence:

```text
project_state/rounds/round_20260710_state_manifest_freshness_rework_v1/round_manifest.json
project_state/rounds/round_20260710_state_manifest_freshness_rework_v1/codex_execution_report.md
project_state/rounds/round_20260710_state_manifest_freshness_rework_v1/execution_report.md
project_state/rounds/round_20260710_state_manifest_freshness_rework_v1/pytest_result.txt
```

Allowed implementation files:

```text
reverse_agent/project_gate.py
reverse_agent/project_state.py
```

Allowed test files:

```text
tests/test_project_gate.py
tests/test_project_reports.py
tests/test_project_state.py
```

Read-only regression files:

```text
reverse_agent/project_state_manifest.py
tests/test_project_state_manifest.py
```

Allowed generated state and report files:

```text
project_state/state_manifest.json
project_state/context/current_context_packet.json
project_state/gates/*.json
project_state/pytest_result.txt
project_state/codex_execution_report.md
project_state/execution_report.md
project_state/rounds/round_20260710_post_closeout_required_audit_truth_rework_v1/*
```

## 5. Required Audit

The final execution report must contain a human-readable `## Required Audit` body answering every item below. Each answer must cite a concrete current artifact path and observed field or status. Answers must describe completed observations, not future work.

```text
1. Is decision_meta valid JSON with schema_version=1?
2. Is status APPROVED and mainline project_governance?
3. Is reverse-agent-iteration@v2 active?
4. Is task_packet treated as background only?
5. Is the previous manual audit outcome correctly recorded as REWORK_REQUIRED?
6. Is this round limited to Required Audit final-evidence truth and closeout ordering?
7. Is the previous state-manifest freshness implementation preserved rather than duplicated?
8. Which stale digest/size claims were present in the previous report?
9. Which future-tense completion claims were present in the previous report?
10. Why did the previous final-check pass despite those stale or future-tense report claims?
11. Does an accepted report now reject future-tense completion claims in Evidence and Answer fields?
12. Does an accepted report now reject a statement claiming that no future-tense claims exist when such claims are present?
13. If a Required Audit answer explicitly claims an exact SHA-256, is the full 64-character value required?
14. If a Required Audit answer explicitly claims an exact SHA-256, is it checked against the live file or current manifest entry?
15. If a Required Audit answer explicitly claims size_bytes, is it checked against the live file or current manifest entry?
16. Are abbreviated digest prefixes prevented from being presented as exact equality evidence?
17. Does the final report avoid embedding its own SHA-256?
18. Does the final report avoid embedding mutable final-gate or report-summary digests that change after report finalization?
19. Is a structured report_finalization block present in both report aliases?
20. Does report_finalization match the current decision_id, round_id, and report_id?
21. Does report_finalization identify project_state/gates/run_closeout_result.json as its closeout evidence source?
22. Does report_finalization contain the full live run_closeout_result SHA-256?
23. Does report_finalization match the live run_closeout generated_at and closeout_status?
24. Does report_finalization match the embedded close_round_result.close_status?
25. Was the report finalized after the current run-closeout evidence existed?
26. Was the final explicit close-round/archive refresh performed after report finalization?
27. Does the archived report match the final live report?
28. Do execution_report.md and codex_execution_report.md agree on summary fields and report_finalization?
29. Does pytest_result.txt match the current decision, round, and report?
30. Does pytest_result.txt record the exact pytest command and exit code 0?
31. Does command_plan.json exist, pass, and explicitly cover pytest, report-summary, execution-log, final-check, run-closeout, and close-round?
32. Were any omitted or unauthorized commands executed?
33. Does execution_log.json agree with pytest_result.txt, command_plan.json, and run-closeout evidence?
34. Does report_summary_synthesis.json match the final reports?
35. Does final_gate_result.json include and pass Required Audit future-claim and live-claim checks?
36. Does final_gate_result.json preserve state_manifest_freshness=PASS?
37. Does current_context_packet.json match the current decision and round after post-final sync?
38. Does post_final_evidence_sync_result.json report PASSED with context_generated_after_final_gate=true?
39. Does run_closeout_result.json report PASSED?
40. Does the final close-round result report CLOSED?
41. Does the new round_manifest exist and match final live reports, pytest, decision, and closeout state?
42. Were all forbidden paths left untouched?
43. Were no runner, Web, workflow, model API, database, cleanup, reverse-tool, or sample-solving capabilities used?
44. Does the final Required Audit body contain only current observed evidence and no placeholder, generic, contradictory, or future-tense completion answers?
```

Required report finalization metadata:

Both `project_state/codex_execution_report.md` and `project_state/execution_report.md` must contain an equivalent fenced JSON block:

```json report_finalization
{
  "schema_version": 1,
  "decision_id": "decision_20260710_post_closeout_required_audit_truth_rework_v1",
  "round_id": "round_20260710_post_closeout_required_audit_truth_rework_v1",
  "report_id": "codex_report_20260710_post_closeout_required_audit_truth_rework_v1",
  "basis": "post_closeout_live_artifacts",
  "run_closeout_result_path": "project_state/gates/run_closeout_result.json",
  "run_closeout_result_sha256": "<full current 64-character SHA-256>",
  "run_closeout_generated_at": "<current observed timestamp>",
  "run_closeout_status": "PASSED",
  "embedded_close_round_status": "CLOSED",
  "report_self_digest_embedded": false
}
```

The block is additive metadata inside the existing reports. It is not a new report format and must remain backward-compatible for earlier decisions that do not require it.

## 6. Implementation Scope

Implement one narrow extension to the existing report/Required Audit/final-check path.

### A. Future completion claim validation

For reports whose status/recommendation claims acceptance:

```text
status=SUCCESS or accepted equivalent
acceptance_recommendation=ACCEPTED or ACCEPTED_WITH_LIMITATIONS
```

inspect the `Evidence:` and `Answer:` content of each Required Audit item.

Reject unresolved future completion claims, including bounded forms such as:

```text
will be
will match
will report
will be generated
will be refreshed
to be generated
to be updated
after final-check it will
after close-round it will
after this round's command
```

Question headings and quoted descriptions of the previous failed report must not create false positives. Validation must target the current item's evidence and answer assertions.

A report that contains future completion claims must not pass by adding a later sentence saying that no such claims exist.

### B. Live digest and size claim alignment

Extend the existing Required Audit alignment path so that, when an accepted report explicitly asserts metadata for a known artifact:

```text
artifact path or recognized artifact role
sha256=<value>
size_bytes=<integer>
```

the assertion is compared with current live evidence.

Rules:

```text
1. Exact SHA-256 equality claims require a full 64-character hexadecimal digest.
2. A full digest claim must match the live file or the current state_manifest entry.
3. A size_bytes claim must match the live file or the current state_manifest entry.
4. A stale full digest is a hard failure.
5. A stale size is a hard failure.
6. A digest prefix may be shown only as a non-authoritative display prefix and must not be described as exact equality.
7. Report-self SHA-256 claims are forbidden in the same report.
8. Final-gate/report-summary digest duplication in prose is not required; their current status and IDs should be cited through live structured artifacts.
```

The validator must remain bounded. It does not need natural-language understanding of arbitrary prose. It must reliably cover the explicit evidence syntax used by the project's Required Audit reports.

### C. Post-closeout report finalization

Add a backward-compatible parser and validator for the `report_finalization` JSON block.

When `decision_contract.post_closeout_report_finalization_required=true`:

```text
1. Both report aliases must contain the block.
2. Both blocks must be semantically identical.
3. decision_id, round_id, and report_id must match the current decision/report.
4. run_closeout_result_path must be the live current artifact.
5. run_closeout_result_sha256 must be the full live digest.
6. run_closeout_generated_at must match the live artifact.
7. run_closeout_status must match closeout_status and must be PASSED for acceptance.
8. embedded_close_round_status must match run_closeout_result.close_round_result.close_status and must be CLOSED for acceptance.
9. report_self_digest_embedded must be false.
```

The stable lifecycle for this round must be:

```text
1. Implement and test.
2. Generate preliminary current report content without accepted future claims.
3. Run the authorized run-closeout workflow to create current closeout evidence.
4. Finalize both reports using the observed run_closeout_result.
5. Regenerate report-summary, execution-log, state manifest, final-check, and post-final context evidence as authorized.
6. Run the final explicit close-round/archive refresh after report finalization.
7. Verify archived reports equal final live reports.
8. Do not edit either report after the final archive refresh.
```

If the existing closeout implementation can enforce this ordering with a smaller equivalent change, use that existing lifecycle. Do not introduce a new daemon, runner, workflow, or report service.

### D. Final-check integration

Add explicit, actionable checks to the existing final gate, such as equivalent names:

```text
required_audit_future_completion_claims_absent
required_audit_live_metadata_claims_match
report_finalization_present
report_finalization_alias_parity
report_finalization_matches_live_closeout
report_finalization_no_self_digest
final_report_archived_parity
```

Failures must identify:

```text
report path
Required Audit item number where applicable
artifact path or role
claimed value
observed value
failure type
```

Do not suppress existing checks.

### E. Backward compatibility

Preserve all of the following:

```text
decisions without post_closeout_report_finalization_required remain readable;
historical reports without report_finalization remain readable;
non-accepted BLOCKED/PARTIAL/FAILED reports may describe unresolved future actions when clearly marked unresolved;
state_manifest historical and missing_optional semantics remain unchanged;
missing historical sample artifacts remain nonblocking for project_governance;
report alias support remains intact;
existing state_manifest freshness checks remain intact.
```

### F. Allowed modifications

Permitted source files:

```text
reverse_agent/project_gate.py
reverse_agent/project_state.py
```

`reverse_agent/project_state.py` may be modified only if the existing report-block extraction or report-lint helper needs the backward-compatible `report_finalization` parser. Do not make unrelated state changes.

Permitted test files:

```text
tests/test_project_gate.py
tests/test_project_reports.py
tests/test_project_state.py
```

Permitted generated artifacts:

```text
project_state/state_manifest.json
project_state/context/current_context_packet.json
project_state/gates/*.json
project_state/pytest_result.txt
project_state/codex_execution_report.md
project_state/execution_report.md
project_state/rounds/round_20260710_post_closeout_required_audit_truth_rework_v1/*
```

Do not modify any other source, test, roadmap, workflow, frontend, solver, User Solve, tool integration, database, cleanup, or sample file.

## 7. Tests

The executable command list must come from the generated command plan. `command_plan.omitted_commands` must not be executed.

Minimum focused pytest command:

```text
python -m pytest tests/test_project_gate.py tests/test_project_reports.py tests/test_project_state.py tests/test_project_state_manifest.py -q
```

A broader governance test command is allowed only if generated by command-plan and kept within this mainline.

Required command coverage:

```text
python -m reverse_agent.project_gate decision-lint --state-dir project_state
python -m reverse_agent.project_gate preflight --state-dir project_state
python -m reverse_agent.project_gate gate-profile --state-dir project_state
python -m reverse_agent.project_gate command-plan --state-dir project_state
python -m reverse_agent.project_gate command-plan --state-dir project_state --json
python -m pytest tests/test_project_gate.py tests/test_project_reports.py tests/test_project_state.py tests/test_project_state_manifest.py -q
python -m reverse_agent.project_gate report-summary --state-dir project_state
python -m reverse_agent.project_gate execution-log --state-dir project_state
python -m reverse_agent.project_gate final-check --state-dir project_state
python -m reverse_agent.project_gate run-closeout --state-dir project_state --round-id round_20260710_post_closeout_required_audit_truth_rework_v1
python -m reverse_agent.project_gate close-round --state-dir project_state --round-id round_20260710_post_closeout_required_audit_truth_rework_v1
```

Required behavioral tests:

```text
1. SUCCESS / ACCEPTED report with "will be PASSED" in an Answer field fails.
2. SUCCESS / ACCEPTED report with "will match after final-check" fails.
3. A report that contains a future completion claim and later says "no future-tense claims exist" fails.
4. A quoted historical description of the previous failure does not falsely fail when the current Answer is completed and truthful.
5. SUCCESS / ACCEPTED report with an exact stale 64-character SHA-256 claim fails.
6. SUCCESS / ACCEPTED report with a stale size_bytes claim fails.
7. A digest prefix described as exact SHA-256 equality fails.
8. A correct full digest and size claim for a stable live artifact passes.
9. A report that embeds its own SHA-256 fails.
10. A current decision requiring report_finalization fails when the block is missing.
11. report_finalization with a stale run_closeout_result SHA-256 fails.
12. report_finalization with wrong generated_at, decision_id, round_id, report_id, status, or embedded close status fails.
13. Mismatched report_finalization blocks between report aliases fail.
14. A correct report_finalization block passes.
15. Earlier decisions without the new contract flag remain backward-compatible.
16. BLOCKED/PARTIAL reports may describe unresolved next actions when status truthfully marks them unresolved.
17. Final-check reports actionable claimed-versus-observed metadata details.
18. Existing state_manifest freshness tests continue to pass unchanged.
19. Final archive report digest equals the final live report digest.
20. Reports modified after final archive refresh are rejected until close-round is rerun.
```

Required outputs:

```text
project_state/state_manifest.json
project_state/gates/command_plan.json
project_state/gates/execution_log.json
project_state/gates/report_summary_synthesis.json
project_state/gates/final_gate_result.json
project_state/gates/post_final_evidence_sync_result.json
project_state/gates/post_final_evidence_sync_snapshot.json
project_state/gates/run_closeout_result.json
project_state/gates/run_closeout_execution_log.json
project_state/context/current_context_packet.json
project_state/pytest_result.txt
project_state/codex_execution_report.md
project_state/execution_report.md
project_state/rounds/round_20260710_post_closeout_required_audit_truth_rework_v1/round_manifest.json
```

## 8. Stop Conditions

Stop with `BLOCKED` if:

```text
1. project_state/decision_packet.md cannot be read.
2. .codex-skills/registry.json cannot be read.
3. reverse-agent-iteration@v2 is not active.
4. command-plan cannot be generated.
5. live previous-round reports, run_closeout_result, state_manifest, or final_gate evidence cannot be read.
6. the repair requires modifying a forbidden path.
7. the repair requires Web, CI mutation, runner dispatch, database, cleanup, deletion, roadmap mutation, external reverse tools, sample execution, or model API access.
```

Stop with `REWORK_REQUIRED` if:

```text
1. pytest fails or is not recorded.
2. command-plan omits explicit pytest.
3. command-plan omits report-summary, execution-log, final-check, run-closeout, or close-round.
4. an accepted Required Audit answer still contains a future completion claim.
5. a report claims no future completion language while such language remains.
6. a stale exact SHA-256 claim passes.
7. a stale size_bytes claim passes.
8. a digest prefix is accepted as exact equality evidence.
9. report_finalization is missing when required.
10. report_finalization differs between the two report aliases.
11. report_finalization does not match live run_closeout_result evidence.
12. a report embeds its own SHA-256.
13. report-summary does not match the final reports.
14. execution_report.md and codex_execution_report.md disagree.
15. final-check does not expose the new report-truth checks.
16. final_gate_result.json does not pass.
17. the existing state_manifest_freshness check regresses or fails.
18. current_context_packet.json is stale after post-final sync.
19. post_final_evidence_sync_result.json is missing or not PASSED.
20. run_closeout_result.json does not pass.
21. final close-round status is not CLOSED.
22. the archived reports do not match final live reports.
23. either report is modified after final archive refresh without rerunning close-round.
24. the new round_manifest is missing or inconsistent.
25. any forbidden path is modified.
26. any omitted or unauthorized command is executed.
27. the report answers are generic, placeholder-only, policy-only, contradictory, or unsupported by current evidence.
```

Acceptance target:

```text
ACCEPTED only if Required Audit answers are finalized from current post-closeout evidence, contain no unresolved future completion claims, contain no stale metadata assertions, use a valid report_finalization block, preserve state-manifest freshness, pass pytest and all gates, synchronize context after the final gate, and archive reports that exactly match the final live reports.

ACCEPTED_WITH_LIMITATIONS is allowed only for explicitly historical and nonblocking warnings unrelated to current Required Audit truth, report finalization, command authorization, tests, state-manifest freshness, context sync, closeout, or archive parity.

Otherwise return REWORK_REQUIRED or BLOCKED.
```
