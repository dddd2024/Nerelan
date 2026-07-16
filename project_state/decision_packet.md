```json decision_meta
{
  "schema_version": 1,
  "decision_id": "decision_20260716_closeout_final_seal_and_publication_truth_rework_v2",
  "round_id": "round_20260716_closeout_final_seal_and_publication_truth_rework_v2",
  "based_on_state_build_id": "state_20260618_134029_d6bd033d2532",
  "based_on_state_digest": "d6bd033d25324345cfd8ada0ac65db42bc86eb5017f3ffc92906fcd8b71cacb5",
  "status": "APPROVED",
  "mainline": "project_governance",
  "skill_profiles": ["reverse-agent-iteration@v2"]
}
```

```json decision_contract
{
  "follows_last_decision_id": "decision_20260716_closeout_order_provenance_rework_v1",
  "follows_last_round_id": "round_20260716_closeout_order_provenance_rework_v1",
  "previous_audit_outcome": "REWORK_REQUIRED",
  "required_profile": "full",
  "closeout_required": true,
  "close_round_required": true,
  "closeout_allowed": true,
  "pytest_required": true,
  "explicit_pytest_command_required": true,
  "command_plan_precedes_execution_required": true,
  "command_plan_digest_lock_required": true,
  "execution_log_chronology_required": true,
  "required_audit_semantic_specificity_required": true,
  "final_evidence_seal_required": true,
  "publication_truth_required": true,
  "publication_observation_scope_required": true,
  "state_manifest_freshness_regression_preservation_required": true,
  "context_packet_sync_required": true,
  "post_final_evidence_sync_required": true,
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
    "project_state/rounds/round_20260716_closeout_final_seal_and_publication_truth_rework_v2/*"
  ],
  "read_only_evidence_files": [
    "project_state/rounds/round_20260716_closeout_order_provenance_rework_v1/round_manifest.json",
    "project_state/rounds/round_20260716_closeout_order_provenance_rework_v1/codex_execution_report.md",
    "project_state/rounds/round_20260716_closeout_order_provenance_rework_v1/execution_report.md",
    "project_state/rounds/round_20260716_closeout_order_provenance_rework_v1/pytest_result.txt",
    "project_state/gates/command_plan.json",
    "project_state/gates/execution_log.json",
    "project_state/gates/final_gate_result.json",
    "project_state/gates/run_closeout_result.json",
    "project_state/context/current_context_packet.json",
    "project_state/state_manifest.json",
    ".codex-skills/registry.json",
    ".codex-skills/reverse-agent-iteration/SKILL.md",
    "reverse_agent/project_runner_contract.py"
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
    "allowed_branch": "agent/closeout-final-seal-publication-truth-rework-v2",
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
    "publication_status_values": [
      "NOT_OBSERVED",
      "NOT_PERFORMED",
      "PUSHED",
      "DRAFT_PR_OPENED",
      "FAILED"
    ],
    "delete_branch_after_merge_recommended": true
  }
}
```

# DECISION_PACKET

## 1. Goal

Complete one bounded `project_governance` rework round that repairs the four remaining truth-chain defects found by the independent audit of `round_20260716_closeout_order_provenance_rework_v1`:

1. current command authority was generated after substantive execution had already started;
2. the Required Audit body used repeated generic templates instead of item-specific observed facts;
3. the final round manifest changed after final-check and post-final context sync, leaving the final live evidence unsealed;
4. the report claimed publication did not occur even though a later remote commit placed the round output on `main`.

Establish the following controlled lifecycle:

```text
startup status
→ decision-lint
→ gate-profile
→ current command-plan generation
→ command-plan digest lock
→ startup snapshot and round baseline
→ implementation and tests
→ report and closeout evidence generation
→ report finalization
→ final archive refresh
→ final-check
→ post-final context sync
→ state-manifest refresh
→ terminal final-evidence seal
→ optional controlled branch publication
→ optional publication receipt
```

The final-evidence seal must use a non-self-referential terminal boundary. It may bind a pre-seal transcript/event-chain prefix plus a terminal seal event, but it must not claim a whole-file digest that becomes invalid merely because the seal command itself is recorded.

## 2. Current Evidence

- Current task authority is `project_state/decision_packet.md`; `project_state/task_packet.json` remains background only.
- Current mainline is `project_governance`.
- The previous independent audit outcome is `REWORK_REQUIRED`.
- The previous report, pytest result, command-plan, execution log, final gate, context packet, state manifest, and round archive all carry the previous round IDs and are evidence inputs only for this rework.
- The previous round passed its selected test suite with `1542 passed`, so this is not a general test-failure round.
- The previous `execution_log.json` preserves an observed outer order in which `run-closeout` occurred before the current command-plan was generated. The command-plan therefore acted as retrospective coverage evidence rather than proven pre-execution authority.
- The previous `run_closeout_result.json` also executed pytest before generating command-plan evidence.
- The previous Required Audit body repeated substantially identical Evidence and Answer text across unrelated questions. Presence of 48 headings did not prove item-specific audit quality.
- The previous final gate was generated at `2026-07-16T12:40:10.684722Z`; the post-final context packet was generated at `2026-07-16T12:40:10.799950Z`; the current previous-round manifest records a later `archive_refreshed_at` of `2026-07-16T12:40:11.116119Z`. The final live manifest therefore changed after the artifacts that claimed to validate and synchronize it.
- The previous report classified publication as not performed and local-only, but repository commit `59b508fb8893dd0fc6e2e2b62a7a91482b294e42` contains the previous round output on `main`. The actor cannot be attributed from current project_state evidence, so the correct historical classification is `UNATTRIBUTED_REMOTE_MUTATION`, not proof of a particular Agent violation.
- Existing foundations must be reused: decision-lint, gate-profile, command-plan, execution-log synthesis, report-summary synthesis, run-closeout, close-round archive, final-check, state-manifest freshness, context builder, post-final sync, policy-lint, and prompt-consistency.
- `reverse_agent/project_runner_contract.py` remains a non-dispatching foundation. This round must not claim automated Runner publication support.
- The known Skill compatibility/drift issue is real but out of scope. `.codex-skills/*` is read-only in this round and must be handled by a later independent decision.
- Missing reverse-solving artifacts and legacy negative-result scope metadata are non-blocking for this governance round.
- No reverse tool, model API, Web runtime, database, cleanup apply, Scheduler, multi-workstream implementation, or automated Runner dispatch is authorized.
- Closeout and publication are allowed only after the current command-plan exists, its digest is locked, and all required validation passes.

## 3. Do Not Do

Do not:

- modify `.codex-skills/*`, `.github/workflows/*`, frontend, Runner, Job, User Solve, solver, harness, sample, or reverse-tool code;
- implement Skill Compatibility Gate, Goal/Plan/Task contracts, Scheduler, multi-workstream namespaces, Code Review Plane, LangGraph, databases, queues, or real Runner dispatch;
- modify `task_packet.json`, `current_state.json`, `artifact_index.json`, `negative_results.json`, `workstreams.json`, or domain/job/session state;
- read the full `solve_reports/` tree or `PROJECT_PROGRESS_LOG.txt`;
- run runtime reverse probes, debuggers, emulators, hooks, or model APIs;
- execute pytest, implementation, run-closeout, close-round, or publication commands before the current command-plan and digest lock exist;
- generate command-plan after substantive commands and use it to retroactively authorize them;
- replace the command-plan during execution without recording an explicit invalidation and restart;
- reorder transcript or execution-log entries to match planned order;
- accept repeated generic Required Audit answers such as “the listed fields prove this item”;
- infer `NOT_PERFORMED` from absence of local publication commands when no external repository observation exists;
- claim that a specific Agent performed the previous unattributed remote mutation;
- create a self-referential seal that embeds its own whole-file digest;
- modify any sealed artifact after the terminal seal;
- push directly to `main`;
- force-push, merge, rebase, tag, edit workflows or secrets, or delete remote branches;
- create a new branch per commit;
- use `git add -A` or stage unrelated files;
- publish before validation or execute publication commands absent from command-plan.

## 4. Files To Inspect

Required current and previous-round evidence:

- `project_state/decision_packet.md`
- `project_state/codex_execution_report.md`
- `project_state/execution_report.md`
- `project_state/pytest_result.txt`
- `project_state/state_manifest.json`
- `project_state/context/current_context_packet.json`
- `project_state/gates/command_plan.json`
- `project_state/gates/gate_profile_plan.json`
- `project_state/gates/preflight_result.json`
- `project_state/gates/execution_log.json`
- `project_state/gates/final_gate_result.json`
- `project_state/gates/run_closeout_result.json`
- `project_state/gates/run_closeout_execution_log.json`
- `project_state/gates/report_summary_synthesis.json`
- `project_state/gates/post_final_evidence_sync_result.json`
- `project_state/gates/round_close_snapshot.json`
- `project_state/rounds/round_20260716_closeout_order_provenance_rework_v1/round_manifest.json`
- `project_state/rounds/round_20260716_closeout_order_provenance_rework_v1/codex_execution_report.md`
- `project_state/rounds/round_20260716_closeout_order_provenance_rework_v1/pytest_result.txt`
- `reverse_agent/project_gate.py`
- `reverse_agent/project_state.py`
- `tests/test_project_gate.py`
- `tests/test_project_reports.py`
- `tests/test_project_state.py`
- `.codex-skills/registry.json`

Read-only context:

- `.codex-skills/reverse-agent-iteration/SKILL.md`
- `reverse_agent/project_runner_contract.py`
- `git log --oneline --decorate -n 20`
- `git status --short`
- remote branch and PR metadata only when publication is actually attempted or externally observed.

Do not inspect unrelated source trees unless a failing required test identifies an in-scope dependency and a Stop Condition is not triggered.

## 5. Required Audit

The final execution report must answer every item below separately. Each answer must identify the relevant artifact path, field name, observed value, and conclusion. Reusing one generic answer across unrelated items is not acceptable.

1. Is `decision_meta` valid JSON with the exact current decision and round IDs?
2. Is status `APPROVED`, mainline `project_governance`, and `reverse-agent-iteration@v2` active in registry?
3. Is `decision_packet.md` the sole current task authority and `task_packet.json` background only?
4. Is the previous audit outcome recorded as `REWORK_REQUIRED`?
5. Was the previous remote mutation classified as `UNATTRIBUTED_REMOTE_MUTATION` without assigning an unsupported actor?
6. Was the current gate profile generated before command-plan?
7. Was the current command-plan generated before every substantive implementation, pytest, closeout, or publication command?
8. Does the command-plan carry the exact current decision ID and round ID?
9. Was a canonical command-plan digest locked before substantive execution?
10. Did the locked command-plan remain unchanged, or was any invalidation followed by an explicit restart from startup?
11. Does every executed command appear in the locked command-plan or an explicitly permitted startup/status set?
12. Were all omitted commands withheld?
13. Does `pytest_result.txt` preserve actual observed order?
14. Does `execution_log.json` preserve the same chronology without reordering?
15. Does `run-closeout` reject or restart when no current locked command-plan exists?
16. Do Required Audit answers contain item-specific paths, fields, observed values, and conclusions?
17. Are duplicate or normalized-template audit answers absent except where the underlying question is genuinely identical?
18. Do questions about IDs, statuses, timestamps, digests, commands, and paths include the corresponding concrete values?
19. Do the final report aliases and report summaries agree semantically?
20. Is stable run-closeout evidence generated before report finalization?
21. Does report finalization bind the current run-closeout path, digest, generated time, and status?
22. Does final archive refresh occur after report finalization?
23. Do archived and live report and pytest aliases match at the archive boundary?
24. Is final-check generated after the final archive refresh it validates?
25. Is post-final context sync generated after the final gate state it references?
26. Is state-manifest refreshed after all sealed current artifacts reach their final pre-seal state?
27. Is `final_evidence_seal.json` generated after final-check, context sync, state-manifest refresh, and final archive refresh?
28. Does the seal bind the required artifact digests and the non-self-referential transcript/event-chain boundary?
29. Does the execution log end with a valid terminal seal event linked to the pre-seal chain head?
30. Does the pytest transcript contain no command after the permitted terminal seal block?
31. Were any sealed artifacts modified after the seal?
32. Does final-check or seal verification fail when any sealed digest, timestamp ordering, or terminal boundary is altered?
33. Does publication truth distinguish `NOT_OBSERVED` from `NOT_PERFORMED`?
34. If publication was performed, does the receipt record the allowed branch, base branch, implementation commit SHA, status, timestamp, and Draft PR metadata when available?
35. If publication was not externally observed, does the report avoid claiming that no remote mutation occurred?
36. Were direct push to `main`, force push, merge, rebase, tag, workflow mutation, secret mutation, remote branch deletion, and `git add -A` avoided?
37. Were only explicitly allowed source, test, state, and publication-receipt paths modified?
38. Were Skill files, CI workflows, Runner, frontend, User Solve, reverse-solving, databases, and other mainlines left untouched?
39. Did the selected pytest command pass and cover every changed test file?
40. Do final-check, run-closeout, close-round, final seal, reports, context, state manifest, and round manifest agree on the final recommendation?

## 6. Implementation Scope

### 6.1 Pre-execution command authority

Strengthen existing command-plan handling; do not create a second command system.

Required lifecycle:

```text
startup status
→ decision-lint
→ gate-profile
→ command-plan
→ command-plan --json
→ command-plan digest lock
→ startup snapshot
→ round baseline
→ substantive execution
```

Implement or validate structured fields equivalent to:

```text
command_plan_path
command_plan_sha256
command_plan_generated_at
command_plan_locked_at
command_plan_lock_status
command_plan_decision_id
command_plan_round_id
first_substantive_command_at
```

Hard-fail when:

- a substantive command precedes the current plan lock;
- `run-closeout` begins before plan lock;
- pytest occurs before plan lock;
- the plan digest changes after lock without explicit invalidation and restart;
- a later plan is used to retroactively authorize earlier commands.

Startup path checks and read-only Git status commands may remain outside command-plan only if they are explicitly classified as the fixed startup set.

### 6.2 Required Audit semantic specificity

Extend the existing report/final-check validation instead of creating a separate report framework.

For every Required Audit item require:

```text
question_number
artifact_path
field_name_or_observation
observed_value
status
item_specific_answer
```

Reject:

- empty or placeholder answers;
- answers that merely restate the question;
- generic phrases that refer to an undifferentiated evidence list;
- normalized duplicate answers across unrelated questions;
- answers to ID/status/time/digest/path questions that omit the concrete value;
- evidence lists dominated by unrelated artifacts.

Legacy reports remain readable, but current decisions with `required_audit_semantic_specificity_required=true` must use the strict policy.

### 6.3 Terminal final-evidence seal

Add or strengthen a terminal artifact such as:

```text
project_state/gates/final_evidence_seal.json
```

The seal must bind at least:

```text
decision_id
round_id
report_id
sealed_at
final_gate_path and sha256
run_closeout_path and sha256
context_packet_path and sha256
state_manifest_path and sha256
round_manifest_path and sha256
live_report_path and sha256
archived_report_path and sha256
live_pytest_path and archive parity evidence
report_summary_path and sha256
command_plan_path and locked sha256
execution_event_chain_head_before_seal
pytest_transcript_prefix_sha256
seal_status
```

Avoid self-reference by using an explicit terminal boundary:

- the seal binds the execution event-chain head before the terminal seal event;
- the terminal execution event records the seal digest and previous chain head;
- the pytest transcript may append only one terminal seal command block after the sealed prefix;
- no substantive or lifecycle-mutating command may follow that block;
- no artifact listed in `sealed_artifacts` may change after seal generation.

Publication-receipt artifacts may be explicitly outside `sealed_artifacts`, but they must not modify any sealed artifact or retroactively alter the accepted closeout facts.

### 6.4 Publication truth and receipt

Use truthful observation scopes:

```text
NOT_OBSERVED: local evidence cannot determine whether external publication occurred
NOT_PERFORMED: both local execution and required external observation prove no publication occurred
PUSHED: the allowed branch was pushed
DRAFT_PR_OPENED: the allowed branch was pushed and a Draft PR was opened
FAILED: publication was attempted but did not complete
```

Add or validate an artifact equivalent to:

```text
project_state/gates/publication_result.json
```

When publication is performed, record:

```text
publication_status
observation_scope
branch
base_branch
implementation_commit_sha
published_at
push_result
pr_number
pr_url
pr_state
command_plan_authorization
receipt_parent_sha
```

A publication receipt may be committed in a later commit on the same short-lived branch. It must describe the implementation commit and PR observation without attempting to embed the receipt commit's own SHA.

The execution Agent may publish only through:

```text
agent/closeout-final-seal-publication-truth-rework-v2
→ Draft PR
→ main
```

The Agent may create multiple intentional commits on that same branch. It must not create a new branch per commit and must not merge the PR.

### 6.5 Compatibility and bounded scope

- Preserve existing CLI names and public artifact fields unless an additive field or strict-mode check is required.
- Keep legacy artifacts readable.
- Reuse existing gate, report, archive, context, and state-manifest mechanisms.
- Do not migrate unrelated project_state files.
- Do not modify Skill files even though their compatibility issue is known.
- Generated artifacts are limited to current gate/report/context/state-manifest files, current round archive, final seal, and publication receipt.

## 7. Tests

Generate and lock the current command-plan before running substantive tests. The selected command must include at least:

```text
python -m pytest tests/test_project_gate.py tests/test_project_reports.py tests/test_project_state.py -q
```

A broader command-plan-selected regression command may include the existing control-plane, context, and state-manifest suites, but it must remain within current authority.

Add regression coverage for all of the following:

1. pytest before command-plan lock fails.
2. run-closeout before command-plan lock fails.
3. a later command-plan cannot retroactively authorize earlier commands.
4. command-plan digest change after lock fails unless the round explicitly restarts.
5. execution-log and transcript preserve actual chronology.
6. repeated generic Required Audit answers fail strict validation.
7. an answer that lacks the concrete requested ID, status, timestamp, digest, command, or path fails.
8. item-specific answers with concrete observed values pass.
9. final archive refresh after final-check fails terminal ordering.
10. context sync before the final gate it references fails.
11. state-manifest or round-manifest mutation after seal fails.
12. any sealed artifact digest mismatch fails.
13. invalid execution event-chain terminal linkage fails.
14. a substantive command after the terminal seal transcript block fails.
15. the seal does not require or embed its own whole-file digest.
16. `NOT_OBSERVED` is not treated as `NOT_PERFORMED`.
17. external publication uncertainty cannot be reported as proof of no remote mutation.
18. publication on any branch other than the allowed branch fails.
19. direct push to `main`, force push, merge, rebase, tag mutation, workflow mutation, secret mutation, remote branch deletion, and `git add -A` remain prohibited.
20. a valid controlled branch push and Draft PR receipt is accepted when exact commands are authorized.
21. the previous unattributed remote mutation is reported without unsupported actor attribution.
22. existing state-manifest freshness, report alias parity, archive parity, and post-final context sync tests remain passing.
23. existing legacy artifacts remain readable.
24. the correct complete lifecycle passes.

Required generated evidence:

- `project_state/pytest_result.txt`
- `project_state/codex_execution_report.md`
- `project_state/execution_report.md`
- current `project_state/gates/*.json` required by the selected profile
- `project_state/gates/final_evidence_seal.json`
- `project_state/gates/publication_result.json` when publication is attempted or externally observed
- `project_state/rounds/round_20260716_closeout_final_seal_and_publication_truth_rework_v2/round_manifest.json`
- final archived report and pytest aliases for the current round.

## 8. Stop Conditions

Stop implementation and report `BLOCKED` or `REWORK_REQUIRED` as appropriate if:

- `decision-lint`, gate-profile, command-plan generation, or command-plan lock cannot validate the current decision and round;
- substantive execution has already occurred before current plan lock and cannot be discarded by a clean explicit restart;
- completing the fix requires modifying a forbidden path;
- completing the fix requires changing Skill files, workflows, Runner contracts, Job schemas, frontend, User Solve, reverse-solving, databases, or another mainline;
- strict Required Audit validation cannot distinguish item-specific evidence from repeated templates;
- the final seal requires a self-referential digest cycle that is not resolved by the approved terminal-boundary design;
- any sealed artifact must be modified after seal generation;
- transcript, execution log, final gate, context, state manifest, round manifest, reports, or seal disagree;
- required tests fail;
- final-check, closeout, archive parity, context sync, state-manifest freshness, or seal verification fails;
- publication is requested but exact publication commands are absent from command-plan;
- publication credentials are unavailable;
- the named branch cannot be created or reused without force push, rebase, or overwriting unrelated work;
- the working tree contains unrelated changes that cannot be excluded from explicit staging;
- publication would require direct push to `main`, merge, workflow mutation, secret mutation, or another prohibited action.

Do not expand scope to solve a Stop Condition. Record the blocker in the execution report and preserve current execution evidence. Do not start Skill Compatibility Gate or multi-workstream planning until this rework is independently accepted.
