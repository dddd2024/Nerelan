```json decision_meta
{
  "schema_version": 1,
  "decision_id": "decision_20260716_terminal_status_propagation_and_seal_restart_rework_v3",
  "round_id": "round_20260716_terminal_status_propagation_and_seal_restart_rework_v3",
  "based_on_state_build_id": "state_20260618_134029_d6bd033d2532",
  "based_on_state_digest": "d6bd033d25324345cfd8ada0ac65db42bc86eb5017f3ffc92906fcd8b71cacb5",
  "status": "APPROVED",
  "mainline": "project_governance",
  "skill_profiles": ["reverse-agent-iteration@v2"]
}
```

```json decision_contract
{
  "follows_last_decision_id": "decision_20260716_closeout_final_seal_and_publication_truth_rework_v2",
  "follows_last_round_id": "round_20260716_closeout_final_seal_and_publication_truth_rework_v2",
  "previous_audit_outcome": "REWORK_REQUIRED",
  "restart_mode": "explicit_new_round",
  "restart_reason": "previous round ended with run_closeout PASSED and final_evidence_seal PASSED while final_gate_result FAILED",
  "previous_artifacts_read_only": true,
  "required_profile": "full",
  "decision_branch_mode": "branch_local_authority",
  "execution_branch": "agent/terminal-status-propagation-seal-restart-rework-v3",
  "base_branch": "main",
  "decision_commit_must_precede_implementation": true,
  "decision_content_digest_lock_required": true,
  "command_plan_branch_binding_required": true,
  "command_plan_digest_lock_required": true,
  "command_plan_precedes_execution_required": true,
  "final_status_propagation_required": true,
  "final_check_stdout_atomicity_required": true,
  "generated_artifact_inventory_freeze_required": true,
  "required_audit_future_claim_policy_required": true,
  "final_evidence_seal_required": true,
  "seal_requires_final_gate_pass": true,
  "closeout_required": true,
  "close_round_required": true,
  "pytest_required": true,
  "explicit_pytest_command_required": true,
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
    "project_state/rounds/round_20260716_terminal_status_propagation_and_seal_restart_rework_v3/*"
  ],
  "read_only_evidence_files": [
    "project_state/rounds/round_20260716_closeout_final_seal_and_publication_truth_rework_v2/*",
    "project_state/gates/final_gate_result.json",
    "project_state/gates/run_closeout_result.json",
    "project_state/gates/final_evidence_seal.json",
    "project_state/gates/publication_result.json",
    "project_state/gates/command_plan.json",
    "project_state/gates/execution_log.json",
    "project_state/pytest_result.txt",
    "project_state/codex_execution_report.md",
    "project_state/execution_report.md",
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
    "allowed_branch": "agent/terminal-status-propagation-seal-restart-rework-v3",
    "base_branch": "main",
    "same_branch_for_decision_and_implementation": true,
    "multiple_commits_on_same_branch_allowed": true,
    "reuse_same_branch_for_review_fixes_allowed": true,
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
    "command_plan_must_explicitly_authorize_publication_commands": true,
    "publish_only_after_required_validation": true
  }
}
```

# DECISION_PACKET

## 1. Goal

Complete one bounded `project_governance` restart round on the same branch that contains this Decision. Repair only the terminal truth-chain defects left by the previous v2 execution:

1. `final_gate_result.json=FAILED` did not propagate to `run_closeout_result.json`, report status, acceptance recommendation, and seal status;
2. `final_evidence_seal.json` could remain `PASSED` while the final gate was `FAILED`;
3. the final generated-artifact inventory was incomplete or frozen at the wrong lifecycle point;
4. the final report still contained future-completion claims outside an explicit rework/limitations section;
5. final-check stdout, exit code, and the persisted final-gate artifact were not derived atomically from one final result.

This Decision uses branch-local authority. Codex must execute directly on:

```text
agent/terminal-status-propagation-seal-restart-rework-v3
```

The Decision commit on that branch must precede every implementation commit. The branch must remain the only execution and review-fix branch for this round.

Required lifecycle:

```text
fetch branch
→ verify exact branch
→ verify Decision commit is in branch history
→ lock Decision digest
→ decision-lint
→ gate-profile
→ generate branch-bound command-plan
→ lock command-plan digest
→ explicit restart snapshot
→ implementation and tests
→ generate all non-terminal gate artifacts
→ freeze generated/referenced artifact inventory
→ finalize reports
→ final-check atomically writes artifact, stdout, and exit code
→ propagate final status to closeout/report recommendation
→ post-final context and state-manifest refresh
→ generate seal only when final gate and terminal prerequisites pass
→ push further commits to the same branch only when command-plan authorizes publication
```

## 2. Current Evidence

- Current task authority for this execution is the `project_state/decision_packet.md` at the HEAD of `agent/terminal-status-propagation-seal-restart-rework-v3`, not the copy currently merged on `main`.
- `main` contains the v2 Decision through merge commit `5884cf2abb37945652ef166cf0e78fa24593b0d5`.
- The user supplied the current local v2 execution facts: selected tests passed with `1551 passed in 450.12s`; the command-plan digest remained locked; no implementation branch push or new PR was attempted; publication was recorded as `NOT_OBSERVED / NOT_ATTEMPTED`.
- The same local evidence reports a terminal contradiction: `run_closeout_result.json=PASSED`, `final_evidence_seal.json=PASSED`, and `final_gate_result.json=FAILED`.
- The final gate failed on `generated_artifacts_cover_gate_artifacts`, `required_audit_future_completion_claims_absent`, and `final_check_stdout_matches_gate_status`.
- The previous execution correctly stopped without editing sealed artifacts or claiming full success. Those previous v2 artifacts are read-only evidence and must not be repaired in place.
- Current GitHub `main` does not contain the local v2 implementation artifacts. This Decision therefore treats the user-supplied local evidence as the restart basis, while requiring the new v3 branch to generate and publish its own current artifacts.
- Existing foundations must be reused: command-plan locking, execution-log chronology, report-summary synthesis, final-check, run-closeout, close-round, state-manifest freshness, context sync, final seal, publication truth, policy-lint, and prompt-consistency.
- Existing foundations are not to be reimplemented from zero. The missing work is terminal status propagation, final inventory ordering, report semantic cleanup, and final-check atomicity.
- `reverse-agent-iteration@v2` is the selected repository Skill. Skill compatibility/drift hardening remains a separate future governance round and is not authorized here.
- No reverse tool, runtime probe, model API, Runner dispatch, Web runtime, CI workflow modification, database, cleanup apply, or other mainline is authorized.

## 3. Do Not Do

Do not:

- work on `main`, `master`, or any branch other than `agent/terminal-status-propagation-seal-restart-rework-v3`;
- merge this branch or create a second implementation branch;
- modify or regenerate the previous v2 round archive or previous v2 seal;
- convert a previous `FAILED` final gate into `PASSED` by editing evidence files;
- treat passing pytest as proof that final acceptance passed;
- let `run-closeout` report `PASSED` when the terminal final gate is `FAILED`;
- let an acceptance-type seal report `PASSED` when its bound final gate is not `PASSED`;
- generate the final artifact inventory before all non-terminal gate artifacts exist;
- generate additional current-round gate artifacts after the inventory and seal boundary unless they are explicitly excluded publication receipts;
- suppress future-completion findings by globally disabling the check;
- classify ordinary execution facts as future plans merely because words such as “will” appear inside quoted Decision text;
- print a final-check status before the complete result is known;
- produce stdout, exit code, and `final_gate_result.json` from separate calculations;
- modify `.codex-skills/*`, `.github/workflows/*`, Runner, Job, frontend, User Solve, reverse-solving, roadmap, database, or cleanup modules;
- read the full `solve_reports/` tree or `PROJECT_PROGRESS_LOG.txt`;
- use `git add -A`, force push, rebase, merge, tag mutation, workflow mutation, secret mutation, or direct push to `main`;
- execute publication commands that are not present in the current branch-bound command-plan.

## 4. Files To Inspect

Required:

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
- `project_state/gates/final_evidence_seal.json`
- `project_state/gates/publication_result.json`
- `project_state/gates/report_summary_synthesis.json`
- `project_state/gates/post_final_evidence_sync_result.json`
- `project_state/gates/round_close_snapshot.json`
- `project_state/rounds/round_20260716_closeout_final_seal_and_publication_truth_rework_v2/*`
- `reverse_agent/project_gate.py`
- `reverse_agent/project_state.py`
- `tests/test_project_gate.py`
- `tests/test_project_reports.py`
- `tests/test_project_state.py`
- `.codex-skills/registry.json`

Read-only context:

- `.codex-skills/reverse-agent-iteration/SKILL.md`
- `reverse_agent/project_runner_contract.py`
- `git status --short`
- `git branch --show-current`
- `git log --oneline --decorate -n 30`
- `git merge-base --is-ancestor <decision_commit> HEAD`

Do not inspect unrelated source trees unless a failing required test identifies a direct in-scope dependency and no Stop Condition is triggered.

## 5. Required Audit

The final report must answer each item with a concrete path, field or observation, observed value, and conclusion.

1. Is the current branch exactly `agent/terminal-status-propagation-seal-restart-rework-v3`?
2. Is the Decision commit an ancestor of every implementation and evidence commit?
3. Is the branch-local Decision marked `APPROVED`, `project_governance`, and bound to `reverse-agent-iteration@v2`?
4. Was the Decision content digest locked before implementation?
5. Does the command-plan record the exact branch, Decision ID, round ID, Decision digest, and branch HEAD used at generation?
6. Was the command-plan generated and locked before substantive execution?
7. Did the command-plan digest remain unchanged, or was an explicit restart recorded?
8. Is the previous v2 round identified as `REWORK_REQUIRED` and read-only?
9. Does the new round record `restart_from_decision_id`, `restart_from_round_id`, and the previous terminal contradiction?
10. If final-check fails, does `run-closeout` avoid `PASSED`?
11. If final-check fails, does the report avoid `SUCCESS` and `ACCEPTED`?
12. If final-check fails, does the seal avoid an acceptance-type `PASSED` status?
13. Does the acceptance recommendation derive from the terminal final-gate status?
14. Does closeout distinguish orchestration completion from acceptance success?
15. Are all non-terminal gate artifacts generated before the final inventory is frozen?
16. Does the frozen generated-artifact inventory cover all current gate artifacts used by final-check and reports?
17. Are publication receipts and other explicitly post-seal artifacts excluded without altering accepted closeout facts?
18. Are no required current artifacts generated after the seal boundary?
19. Are future-completion claims absent from execution-fact sections?
20. Are future plans allowed only in explicit `Limitations`, `Rework Required`, or `Next Decision` sections?
21. Does the future-claim checker avoid flagging quoted Decision requirements or historical descriptions as current completion claims?
22. Are final-check stdout, persisted JSON status, and exit code derived from one completed result object?
23. Does `final_check_stdout_matches_gate_status` pass using the same invocation evidence?
24. Does a failed final-check return the expected nonzero exit code?
25. Does a passed final-check print and persist `PASSED` only after all checks complete?
26. Does the seal bind the final gate artifact that actually determined terminal status?
27. Does seal verification reject any digest, timestamp, or terminal-status mismatch?
28. Are previous sealed v2 artifacts unchanged?
29. Do report aliases and report summaries agree on status and recommendation?
30. Do context, state manifest, round manifest, closeout, final gate, reports, and seal agree on one terminal recommendation?
31. Did the selected pytest command pass and cover every changed test file?
32. Were all modified source, test, state, and publication paths explicitly allowed?
33. Were Skills, workflows, Runner, frontend, User Solve, reverse-solving, databases, and roadmap left untouched?
34. If publication occurs, was the same execution branch reused and were all commands explicitly authorized?
35. Were direct push to `main`, force push, rebase, merge, tag mutation, workflow mutation, secret mutation, remote branch deletion, and `git add -A` avoided?

## 6. Implementation Scope

### 6.1 Branch-local authority and explicit restart

Add or validate branch-bound fields in the current Decision/command-plan evidence, including equivalents of:

```text
execution_branch
base_branch
decision_commit_sha
decision_packet_sha256
decision_locked_at
head_sha_at_plan_generation
restart_from_decision_id
restart_from_round_id
previous_final_gate_status
previous_seal_status
restart_reason
previous_artifacts_read_only
```

Preflight must hard-fail when the current branch is `main`, when the branch does not match the Decision, or when the Decision commit is not an ancestor of HEAD.

The current branch may already contain local uncommitted v2 implementation changes. Preserve them only if they are confined to allowed paths and do not modify the new Decision commit. If unrelated or conflicting changes exist, stop rather than stash, discard, or stage them silently.

### 6.2 Terminal status propagation

Use one canonical terminal status computation.

Required propagation:

```text
final_gate FAILED
→ terminal_acceptance_status = REWORK_REQUIRED
→ run_closeout cannot be PASSED as acceptance status
→ report status cannot be SUCCESS
→ acceptance_recommendation = REWORK_REQUIRED
→ acceptance-type seal cannot be PASSED
```

If orchestration completed but acceptance failed, record two distinct concepts such as:

```text
workflow_execution_status = COMPLETED
terminal_acceptance_status = REWORK_REQUIRED
```

Do not overload `PASSED` to mean both “commands ran” and “round accepted.”

### 6.3 Seal preconditions and restart semantics

Before creating an acceptance-type seal, require:

- final gate `PASSED`;
- report status and recommendation support acceptance;
- generated-artifact inventory complete;
- report semantic checks passed;
- stdout/status/exit-code parity passed;
- context and state-manifest freshness passed;
- no sealed artifact mutation after the boundary.

When these conditions fail, either refuse to generate an acceptance seal or emit a clearly non-accepting seal status such as `FAILED` or `REWORK_REQUIRED`.

Do not rewrite the previous v2 seal. The new round must reference it as historical read-only evidence.

### 6.4 Generated-artifact inventory freeze

Enforce this order:

```text
generate all current non-terminal gate artifacts
→ compute generated/referenced artifact inventory
→ write finalized report aliases
→ run final-check
→ post-final context and state-manifest refresh
→ generate terminal seal
```

If final-check itself generates or changes artifacts that must appear in reports, redesign the inventory to include those deterministic terminal artifacts without requiring post-seal report mutation. Use an explicit terminal-artifact manifest if needed, but do not create a second unrelated artifact index system.

### 6.5 Required Audit future-claim policy

Make the check section-aware.

Execution-fact and Required Audit sections must describe only observed facts. Future or conditional work is allowed only in explicitly recognized sections such as:

- `Limitations`;
- `Rework Required`;
- `Next Decision`.

Quoted Decision requirements, test names, historical descriptions, and field values must not be misclassified as completion claims. Do not globally disable the check.

### 6.6 Atomic final-check output

Refactor final-check so that one complete result object controls:

```text
final_gate_result.json
stdout status
stderr diagnostics
process exit code
```

Required sequence:

```text
collect all checks
→ calculate terminal result
→ persist result atomically
→ print the same result
→ return the matching exit code
```

No final `PASSED` text may be emitted before all checks finish.

### 6.7 Compatibility and publication

Preserve existing CLI names and legacy artifact readability where possible. Use additive fields or strict-mode checks rather than unrelated rewrites.

All Decision, implementation, test, evidence, and review-fix commits remain on:

```text
agent/terminal-status-propagation-seal-restart-rework-v3
```

The same Draft PR remains open throughout the round. Codex must not merge it.

## 7. Tests

After branch, Decision, and command-plan locks are established, run at least:

```text
python -m pytest tests/test_project_gate.py tests/test_project_reports.py tests/test_project_state.py -q
```

The command-plan may authorize the existing broader governance regression suite.

Add coverage for:

1. execution on `main` fails branch preflight;
2. wrong execution branch fails;
3. implementation commit not descended from the Decision commit fails;
4. Decision digest mutation after lock fails;
5. branch-bound command-plan metadata mismatch fails;
6. previous failed round can start only through an explicit new-round restart;
7. previous seal remains read-only during restart;
8. final gate `FAILED` forces terminal recommendation `REWORK_REQUIRED`;
9. final gate `FAILED` prevents run-closeout acceptance `PASSED`;
10. final gate `FAILED` prevents report `SUCCESS` and recommendation `ACCEPTED`;
11. final gate `FAILED` prevents an acceptance-type seal `PASSED`;
12. orchestration completion and acceptance status are represented separately;
13. incomplete generated-artifact inventory fails;
14. all required gate artifacts present before freeze passes;
15. a new required artifact generated after inventory freeze fails;
16. a sealed artifact modified after seal fails;
17. future-completion text in execution-fact sections fails;
18. future plans in an explicit `Next Decision` section pass;
19. quoted Decision requirements are not false positives;
20. stdout `PASSED` with artifact `FAILED` fails;
21. exit code and artifact status mismatch fails;
22. one complete result object produces matching stdout, JSON, and exit code;
23. report aliases and summaries propagate `REWORK_REQUIRED` consistently;
24. valid full lifecycle produces consistent `PASSED` artifacts;
25. existing command-plan lock, publication truth, state-manifest freshness, archive parity, context sync, and legacy compatibility tests remain passing.

Required generated evidence:

- `project_state/pytest_result.txt`
- `project_state/codex_execution_report.md`
- `project_state/execution_report.md`
- current branch-bound command-plan and lock evidence
- current `project_state/gates/*.json` required by the selected profile
- current final gate, closeout result, final seal, publication result, context packet, and state manifest
- `project_state/rounds/round_20260716_terminal_status_propagation_and_seal_restart_rework_v3/*`

## 8. Stop Conditions

Stop and report `BLOCKED` or `REWORK_REQUIRED` if:

- Codex is not on the exact execution branch;
- the Decision commit is not an ancestor of HEAD;
- the Decision digest or branch-bound command-plan cannot be locked;
- unrelated working-tree changes cannot be excluded safely;
- current implementation requires editing the previous v2 seal or archive;
- final status propagation still allows a failed final gate to coexist with accepted closeout, report, or seal states;
- artifact inventory cannot reach a stable pre-seal boundary without self-reference;
- stdout, exit code, and persisted final-gate status cannot be made atomic within the allowed modules;
- required tests fail;
- final-check, closeout, report, context, state manifest, round manifest, seal, or publication evidence disagree;
- completing the fix requires changing Skills, workflows, Runner, Job, frontend, User Solve, reverse-solving, roadmap, databases, cleanup, or another mainline;
- publication commands are missing from the current command-plan;
- publishing would require direct push to `main`, force push, rebase, merge, workflow mutation, secret mutation, or staging unrelated files.

Do not expand scope to resolve a Stop Condition. Preserve the current artifacts, write the exact blocker to the report, and keep all work on the same branch and Draft PR.
