```json decision_meta
{
  "schema_version": 1,
  "decision_id": "decision_20260717_branch_evidence_convergence_rework_v4",
  "round_id": "round_20260717_branch_evidence_convergence_rework_v4",
  "based_on_state_build_id": "state_20260618_134029_d6bd033d2532",
  "based_on_state_digest": "d6bd033d25324345cfd8ada0ac65db42bc86eb5017f3ffc92906fcd8b71cacb5",
  "status": "APPROVED",
  "mainline": "project_governance",
  "skill_profiles": ["reverse-agent-iteration@v2"]
}
```

```json decision_contract
{
  "follows_last_decision_id": "decision_20260716_terminal_status_propagation_and_seal_restart_rework_v3",
  "follows_last_round_id": "round_20260716_terminal_status_propagation_and_seal_restart_rework_v3",
  "previous_audit_outcome": "REWORK_REQUIRED",
  "restart_mode": "explicit_new_round",
  "restart_reason": "the v3 branch exists and completed local validation, but the final report cites an obsolete command-plan lock, the observed chronology still places substantive commands before the final lock, a lifecycle-order mismatch was marked PASS, and all three remote PR checks failed during package installation",
  "previous_round_artifacts_read_only": true,
  "required_profile": "full",
  "decision_branch_mode": "branch_local_authority",
  "execution_branch": "agent/terminal-status-propagation-seal-restart-rework-v3",
  "base_branch": "main",
  "decision_commit_must_precede_v4_implementation": true,
  "decision_content_digest_lock_required": true,
  "command_plan_branch_binding_required": true,
  "command_plan_digest_lock_required": true,
  "command_plan_precedes_execution_required": true,
  "explicit_restart_segment_required": true,
  "canonical_lock_snapshot_required": true,
  "required_audit_lock_parity_required": true,
  "startup_snapshot_order_required": true,
  "final_evidence_seal_required": true,
  "remote_check_observation_required": true,
  "remote_green_required_for_acceptance": true,
  "workflow_mutation_allowed": false,
  "packaging_mutation_allowed": false,
  "closeout_required": true,
  "close_round_required": true,
  "pytest_required": true,
  "explicit_pytest_command_required": true,
  "context_packet_sync_required": true,
  "state_manifest_freshness_required": true,
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
    "project_state/rounds/round_20260717_branch_evidence_convergence_rework_v4/*"
  ],
  "read_only_evidence_files": [
    "project_state/rounds/round_20260716_terminal_status_propagation_and_seal_restart_rework_v3/*",
    "project_state/gates/final_evidence_seal.json",
    "project_state/gates/publication_result.json",
    "project_state/gates/command_plan_lock.json",
    "project_state/gates/decision_content_lock.json",
    "project_state/gates/execution_log.json",
    "project_state/gates/final_gate_result.json",
    "project_state/gates/run_closeout_result.json",
    "project_state/pytest_result.txt",
    "project_state/codex_execution_report.md",
    "project_state/execution_report.md",
    "project_state/roadmap/workstreams.json",
    "project_state/current_state.json",
    "project_state/task_packet.json",
    "project_state/artifact_index.json",
    "project_state/negative_results.json",
    ".codex-skills/registry.json",
    ".codex-skills/reverse-agent-iteration/SKILL.md",
    ".github/workflows/ci.yml",
    ".github/workflows/state-gate.yml",
    ".github/workflows/decision-preflight.yml",
    "pyproject.toml"
  ],
  "forbidden_mutated_paths": [
    ".codex-skills/*",
    ".github/workflows/*",
    "pyproject.toml",
    "setup.py",
    "setup.cfg",
    "requirements*.txt",
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
    "reuse_existing_draft_pr_number": 5,
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

Complete one bounded `project_governance` rework round on the existing Draft PR branch:

```text
agent/terminal-status-propagation-seal-restart-rework-v3
```

Do not create a second implementation branch or a second PR.

The v3 implementation is not absent: it is present on Draft PR #5 and produced local tests, reports, closeout artifacts, a final gate, and a final evidence seal. This round must not repeat that implementation from zero. It must repair only the remaining evidence-convergence defects identified by independent branch-aware audit:

1. `codex_execution_report.md` Required Audit cites an obsolete command-plan lock digest, lock timestamp, and restart count rather than the final sealed lock;
2. the final `command_plan_lock.json` records `first_substantive_command_at` before its own final `command_plan_locked_at`, while the execution transcript still places `run-closeout` and pytest before command-plan generation;
3. the system records restart counters and invalidation text but does not expose one canonical post-restart execution segment proving that the invalidated prefix was discarded;
4. `startup_snapshot_immediate_after_startup_status` was marked `PASS` even though the observed sixth command was `run-closeout`, not `startup-snapshot`;
5. the publication receipt stopped at `checks_observation=IN_PROGRESS`, while the final remote observation is that CI, State Gate, and Decision Preflight all failed at `Install package`;
6. the current branch report self-recommends `ACCEPTED`, but remote checks are not green and the final report/lock evidence is internally inconsistent.

Required v4 lifecycle:

```text
fetch existing branch and PR
→ verify exact branch and current HEAD
→ verify v4 Decision commit is an ancestor of all v4 implementation/evidence commits
→ lock v4 Decision digest
→ decision-lint
→ gate-profile
→ generate branch-bound v4 command-plan
→ lock the exact v4 command-plan digest
→ create restart_segment.json before any substantive v4 command
→ capture startup snapshot and v4 round baseline
→ implement only evidence-convergence checks
→ run selected tests
→ generate reports from canonical final artifacts
→ verify report/lock/restart parity
→ final-check
→ close-round and archive
→ post-final context/state-manifest sync
→ final-evidence-seal
→ push to the same branch
→ observe Draft PR #5 remote checks to terminal state
```

A green local pytest run is necessary but not sufficient. Final acceptance requires local evidence convergence and terminal remote check observation.

## 2. Current Evidence

- Current task authority after this Decision commit is the branch-local `project_state/decision_packet.md` on `agent/terminal-status-propagation-seal-restart-rework-v3`. `task_packet.json` remains background only.
- Current mainline is `project_governance`.
- The current workstream registry exists and explicitly states that roadmap entries are not execution authority. It contains existing Project State, CI/state-gate, User Solve, Web, Runner, reverse-solving, and tool-integration workstreams. This round must not modify the registry or activate another workstream.
- The current context packet exists and identifies v3 as its sealed previous baseline. It confirms existing command-plan, execution-log, report-summary, final-check, run-closeout, archive, context-sync, state-manifest, policy-lint, prompt-consistency, Job, Runner-contract, Web-orchestrator, and state-hygiene foundations.
- `current_state.json`, `task_packet.json`, and `artifact_index.json` still contain older sample-oriented facts. They are not authority for this governance round and remain read-only.
- `negative_results.json` contains reverse-solving failures and the hard prohibition against committing full `solve_reports`. None of those directions is reopened or repeated.
- Existing v3 local evidence includes `1555 passed`, a v3 final gate marked `PASSED`, run-closeout marked `PASSED`, and a final evidence seal marked `PASSED`.
- Existing v3 report evidence is not internally converged: Required Audit cites lock digest `76c8d5a0...`, timestamp `2026-07-16T15:21:24.3340244Z`, and `restart_count=1`, while the final branch lock and seal bind digest `3b5c1b6d...`, timestamp `2026-07-16T15:56:17.7096176Z`, and `restart_count=2`.
- Existing final lock records `first_substantive_command_at=2026-07-16T15:22:05.2192179Z`, which precedes its final lock time. The transcript also records `run-closeout` and pytest before command-plan generation.
- Existing final-check records the startup-snapshot order check as `PASS`, despite its own observed command sequence showing `run-closeout` in the sixth position.
- Draft PR #5 exists and remains open. Its current remote checks reached terminal failure: CI, State Gate, and Decision Preflight each failed at the package-install step before project tests or project gates ran.
- The remote install failure is a current external blocker, but its root cause is not yet proven. This round may inspect logs and record the exact failure. It may not modify packaging or workflow files.
- Existing v3 round archives, seal, publication receipt, reports, and execution evidence are historical inputs and must not be edited in place.
- Artifact freshness for sample-solving artifacts is nonblocking because this is not a reverse-solving round.
- Local deterministic Python and tests are allowed. Reverse tools, runtime probes, debuggers, model APIs, Runner dispatch, Web runtime, database creation, cleanup apply, and destructive operations are not allowed.
- Closeout is allowed only after the current v4 Decision and command-plan locks exist and the restart segment proves all substantive v4 work occurred after the final lock.
- This round does not duplicate command-plan, execution-log, report-summary, final-check, run-closeout, archive, or seal systems. It strengthens their parity and lifecycle validation.

## 3. Do Not Do

Do not:

- work on `main`, `master`, or any branch other than `agent/terminal-status-propagation-seal-restart-rework-v3`;
- create a new branch or new PR;
- merge Draft PR #5;
- modify or regenerate the v3 round archive or v3 seal;
- edit v3 evidence to make the previous audit pass;
- reuse v3 `SUCCESS`, `ACCEPTED`, or `PASSED` as proof of v4 acceptance;
- treat `restart_count` alone as proof of a clean restart;
- accept a report whose lock digest, lock time, restart count, Decision digest, branch, or HEAD differs from the canonical final lock artifacts;
- accept a lifecycle-order check when the observed sequence contradicts the expected sequence;
- classify a required ordering check as advisory merely to keep final-check green;
- reorder transcript or execution-log entries;
- discard or hide failed remote checks;
- classify remote checks as green when they failed before project validation;
- modify `.github/workflows/*`, `pyproject.toml`, `setup.py`, `setup.cfg`, or dependency files;
- expand this round into a package-install or CI-workflow repair;
- modify Skills, Runner, Job, frontend, User Solve, reverse-solving, tool integration, roadmap, database, or cleanup systems;
- read the full `solve_reports/` tree or `PROJECT_PROGRESS_LOG.txt`;
- run reverse tools, runtime probes, debuggers, emulators, hooks, or model APIs;
- use `git add -A`;
- force-push, rebase, merge, tag, edit workflows or secrets, delete remote branches, or push directly to `main`;
- execute commands absent from the current locked command-plan;
- modify sealed artifacts after the v4 terminal seal.

## 4. Files To Inspect

Required current branch evidence:

- `project_state/decision_packet.md`
- `project_state/codex_execution_report.md`
- `project_state/execution_report.md`
- `project_state/pytest_result.txt`
- `project_state/state_manifest.json`
- `project_state/context/current_context_packet.json`
- `project_state/roadmap/workstreams.json`
- `project_state/current_state.json`
- `project_state/task_packet.json`
- `project_state/artifact_index.json`
- `project_state/negative_results.json`
- `project_state/gates/command_plan.json`
- `project_state/gates/command_plan_lock.json`
- `project_state/gates/decision_content_lock.json`
- `project_state/gates/execution_log.json`
- `project_state/gates/final_gate_result.json`
- `project_state/gates/run_closeout_result.json`
- `project_state/gates/run_closeout_execution_log.json`
- `project_state/gates/final_evidence_seal.json`
- `project_state/gates/publication_result.json`
- `project_state/gates/report_summary_synthesis.json`
- `project_state/gates/post_final_evidence_sync_result.json`
- `project_state/gates/round_close_snapshot.json`
- `project_state/rounds/round_20260716_terminal_status_propagation_and_seal_restart_rework_v3/*`
- `reverse_agent/project_gate.py`
- `reverse_agent/project_state.py`
- `tests/test_project_gate.py`
- `tests/test_project_reports.py`
- `tests/test_project_state.py`
- `.codex-skills/registry.json`

Read-only CI context:

- `.github/workflows/ci.yml`
- `.github/workflows/state-gate.yml`
- `.github/workflows/decision-preflight.yml`
- `pyproject.toml`
- GitHub Actions logs for PR #5 runs:
  - CI run `29522575928`
  - State Gate run `29522575937`
  - Decision Preflight run `29522576149`

Required Git observations:

- `git branch --show-current`
- `git status --short`
- `git log --oneline --decorate -n 40`
- `git merge-base --is-ancestor <v4_decision_commit> HEAD`
- Draft PR #5 head/base/draft state
- terminal status and failed step for each current remote check

Do not inspect unrelated source trees unless a failing required test identifies a direct in-scope dependency and no Stop Condition is triggered.

## 5. Required Audit

The final v4 report must answer each item separately with:

```text
question_number
artifact_path
field_name_or_observation
observed_value
status
item_specific_answer
```

Required questions:

1. Is the execution branch exactly `agent/terminal-status-propagation-seal-restart-rework-v3`?
2. Is Draft PR #5 still the only review surface and still unmerged?
3. Is the v4 Decision commit an ancestor of every v4 implementation and evidence commit?
4. Is the v4 Decision `APPROVED`, `project_governance`, and bound to active `reverse-agent-iteration@v2`?
5. Is `task_packet.json` background only and `decision_packet.md` the sole task authority?
6. Were the v3 round archive, v3 seal, and v3 publication receipt treated as read-only?
7. Was the v4 Decision digest locked before command-plan generation?
8. Does the v4 command-plan bind the exact Decision ID, round ID, branch, Decision digest, and branch HEAD?
9. Was the final v4 command-plan digest locked before every substantive v4 command?
10. Does one canonical `restart_segment.json` identify the invalidated prefix and the accepted post-restart segment?
11. Does the restart segment include a unique restart ID, invalidated chain head, lock digest, lock time, startup snapshot time, first substantive command time, and accepted chain head?
12. Is `first_substantive_command_after_restart_at` strictly later than the final lock time?
13. Are all substantive v4 commands inside the accepted post-restart segment?
14. Are invalidated pre-restart commands excluded from acceptance coverage rather than silently reordered?
15. Did the command-plan remain unchanged after final lock, or was another explicit invalidation and restart recorded?
16. Do report Required Audit values exactly match the canonical final Decision lock and command-plan lock?
17. Does the report use the final lock digest `observed_value` rather than an earlier lock?
18. Does the report use the final lock timestamp and final restart count?
19. Does report-summary synthesis reject report/lock mismatch?
20. Does final-check reject report/lock mismatch?
21. Is startup snapshot recorded immediately after the permitted fixed startup/status sequence?
22. Does a mismatch between expected and actual startup-snapshot position hard-fail when `startup_snapshot_order_required=true`?
23. Are final-check status, persisted JSON, stdout, and exit code derived from one final result?
24. Do execution log and pytest transcript preserve actual chronology?
25. Do all changed source/test files remain within the Decision allowlist?
26. Does the selected pytest command pass and cover every changed test file?
27. Do report aliases and structured summaries agree semantically?
28. Are current context and state manifest synchronized to v4 after the final gate?
29. Do live and archived report and pytest aliases match?
30. Does final seal bind the final v4 lock, final gate, report, context, state manifest, round manifest, and terminal execution boundary?
31. Were any sealed artifacts modified after the seal?
32. Does the publication receipt truthfully identify Draft PR #5, branch, implementation commit, and observation scope?
33. Were CI, State Gate, and Decision Preflight observed to terminal status after the latest push?
34. If any remote check failed, does the report avoid `ACCEPTED` and identify the exact workflow, job, and failed step?
35. If all three remote checks are green, does the report record their terminal run IDs and conclusions?
36. Were workflow, packaging, dependency, Skill, Runner, frontend, User Solve, reverse-solving, roadmap, database, and cleanup files left untouched?
37. Were direct push to `main`, force push, rebase, merge, tag mutation, workflow mutation, secret mutation, remote branch deletion, and `git add -A` avoided?
38. Do final-check, run-closeout, close-round, final seal, reports, context, state manifest, round manifest, publication receipt, and remote check observation agree on the final recommendation?

## 6. Implementation Scope

### 6.1 Preserve v3 as immutable evidence

Create a new v4 round. Do not modify any path under:

```text
project_state/rounds/round_20260716_terminal_status_propagation_and_seal_restart_rework_v3/
```

Do not overwrite the v3 seal. The v3 live artifacts may be superseded only through normal v4 generation after the v4 Decision and command-plan locks exist.

### 6.2 Add a canonical restart segment

Extend the existing gate system; do not create a second execution-log framework.

Generate an additive artifact such as:

```text
project_state/gates/restart_segment.json
```

It must contain at least:

```text
schema_version
decision_id
round_id
restart_id
restart_reason
invalidated_decision_id
invalidated_round_id
invalidated_command_plan_sha256
invalidated_execution_chain_head
accepted_command_plan_sha256
accepted_command_plan_locked_at
startup_snapshot_path
startup_snapshot_generated_at
first_substantive_command_after_restart_at
accepted_execution_chain_head
invalidated_prefix_excluded_from_acceptance
restart_status
```

Hard-fail when:

- the final lock time is not earlier than the first substantive accepted command;
- the accepted segment contains commands before the final lock;
- invalidated commands are counted as authorized accepted execution;
- a restart counter exists without a concrete restart artifact;
- report, execution log, command-plan lock, or seal references a different restart.

### 6.3 Canonical lock snapshot parity

Use `decision_content_lock.json`, `command_plan_lock.json`, and `restart_segment.json` as the canonical source for lock facts.

Report generation, report-summary, final-check, closeout, and seal must consume the same final fields:

```text
decision_packet_sha256
decision_locked_at
command_plan_sha256
command_plan_generated_at
command_plan_locked_at
restart_id
restart_count
first_substantive_command_after_restart_at
execution_branch
head_sha_at_plan_generation
```

Reject stale or intermediate lock values in report prose or Required Audit answers.

### 6.4 Make lifecycle ordering checks truthful

Strengthen the existing startup-snapshot ordering check.

When `startup_snapshot_order_required=true`:

```text
Set-Location
→ Get-Location
→ Test-Path
→ git rev-parse
→ git status
→ Decision/plan lock lifecycle
→ restart snapshot
→ round baseline
→ substantive execution
```

The implementation may represent Decision/plan locking through explicit non-substantive lifecycle events, but it must not claim that `startup-snapshot` was immediate when observed chronology shows another substantive command.

A check whose observed sequence contradicts its expected sequence must be `FAIL`, not `PASS` with `required=false`.

### 6.5 Report and final-check convergence

Update the existing report and final-check validators so that:

- Required Audit concrete values are resolved after the final lock;
- duplicate or stale lock answers fail;
- `SUCCESS`/`ACCEPTED` cannot coexist with a required lifecycle or parity failure;
- remote check failures prevent final `ACCEPTED` when `remote_green_required_for_acceptance=true`;
- remote check observation is distinct from local pytest success.

Do not create a second report format.

### 6.6 Remote CI observation handoff

Read the existing GitHub Actions logs and record:

```text
workflow_name
run_id
job_name
job_id
terminal_conclusion
failed_step
failure_summary
observed_at
```

The current known observation is that all three workflows failed at `Install package`.

This round may classify the failure and prove whether it is:

```text
repository_packaging_failure
workflow_environment_failure
transient_external_failure
unknown
```

It may not modify workflow or packaging files.

If correction requires `.github/workflows/*`, `pyproject.toml`, setup files, dependency files, runner image configuration, or secrets, stop and report `BLOCKED`. Generate a separate next Decision recommendation; do not expand this round.

### 6.7 Compatibility and bounded scope

- Preserve existing CLI names and legacy artifact readability.
- Add fields and strict-mode validation rather than replacing existing schemas.
- Reuse existing command-plan, execution-log, report-summary, final-check, closeout, archive, context, state-manifest, seal, and publication mechanisms.
- Modify only explicitly allowed source, test, and v4 project-state paths.
- Do not modify roadmap/workstream state in this round.
- Do not add a database, queue, Scheduler, Runner dispatch, Web execution, reverse-tool provider, or sample-solving capability.

## 7. Tests

The v4 Decision commit and v4 command-plan lock must exist before substantive tests.

The selected command must include at least:

```text
python -m pytest tests/test_project_gate.py tests/test_project_reports.py tests/test_project_state.py -q
```

A broader command-plan-selected regression command may include:

```text
tests/test_project_control_plane.py
tests/test_project_context.py
tests/test_project_state_manifest.py
```

Required regression coverage:

1. a report citing an obsolete command-plan digest fails;
2. a report citing an obsolete lock timestamp fails;
3. a report citing an obsolete restart count fails;
4. report-summary and final-check use the canonical final lock snapshot;
5. `first_substantive_command_at < command_plan_locked_at` fails without a valid restart segment;
6. restart count without `restart_segment.json` fails;
7. restart segment with a missing invalidated chain head fails;
8. restart segment with a mismatched accepted lock digest fails;
9. invalidated commands cannot satisfy accepted command coverage;
10. accepted post-restart commands must all occur after the final lock;
11. transcript and execution log preserve actual order;
12. startup-snapshot expected/actual mismatch fails under strict policy;
13. a lifecycle-order check cannot report PASS when its own observed sequence contradicts the expected sequence;
14. correct startup, lock, restart, baseline, test, report, closeout, and seal ordering passes;
15. report Required Audit lock values match final lock artifacts;
16. stale v3 artifacts remain readable but cannot support v4 current acceptance;
17. final gate failure propagates to report, closeout, recommendation, and seal;
18. remote checks marked failed prevent `ACCEPTED` when remote green is required;
19. remote checks marked completed/success with concrete run IDs can support acceptance;
20. `IN_PROGRESS` cannot be treated as terminal success;
21. missing remote observation cannot be reported as green;
22. workflow/package mutation remains prohibited;
23. existing state-manifest freshness, context sync, archive parity, report alias parity, and final seal tests remain passing;
24. legacy artifacts remain readable;
25. the complete v4 lifecycle passes.

Required generated evidence:

- `project_state/gates/decision_content_lock.json`
- `project_state/gates/command_plan.json`
- `project_state/gates/command_plan_lock.json`
- `project_state/gates/restart_segment.json`
- `project_state/gates/execution_log.json`
- `project_state/gates/remote_check_observation.json`
- `project_state/gates/report_summary_synthesis.json`
- `project_state/gates/final_gate_result.json`
- `project_state/gates/run_closeout_result.json`
- `project_state/gates/final_evidence_seal.json`
- `project_state/pytest_result.txt`
- `project_state/codex_execution_report.md`
- `project_state/execution_report.md`
- `project_state/context/current_context_packet.json`
- `project_state/state_manifest.json`
- `project_state/rounds/round_20260717_branch_evidence_convergence_rework_v4/round_manifest.json`
- archived v4 report and pytest aliases.

## 8. Stop Conditions

Stop implementation and report `BLOCKED` or `REWORK_REQUIRED` as appropriate if:

- the exact execution branch or Draft PR #5 cannot be verified;
- the v4 Decision commit is not an ancestor of v4 implementation/evidence commits;
- Decision lock, gate-profile, command-plan generation, or command-plan lock cannot validate v4 IDs and branch binding;
- substantive v4 execution has already occurred before the final v4 lock and cannot be discarded through a new explicit restart segment;
- the final lock digest changes without a recorded invalidation and restart;
- the system cannot distinguish invalidated transcript prefixes from accepted post-restart execution;
- report generation cannot be made to consume the canonical final lock snapshot;
- lifecycle-order validation still marks contradictory expected/actual sequences as PASS;
- required tests fail;
- report, execution log, final gate, closeout, context, state manifest, round manifest, seal, or publication evidence disagree;
- any v3 archived or sealed artifact must be modified;
- any v4 sealed artifact must be modified after seal generation;
- resolving GitHub Actions `Install package` failure requires changing workflows, packaging, dependency files, secrets, or another forbidden path;
- remote check logs or terminal conclusions cannot be obtained;
- remote checks remain failed after the latest authorized push;
- completing the task requires Skill, Runner, Job, frontend, User Solve, reverse-solving, tool-integration, roadmap, database, cleanup, or another mainline work;
- the working tree contains unrelated source/test changes that cannot be excluded from explicit staging;
- publication commands are absent from command-plan;
- publication requires direct push to `main`, force push, rebase, merge, workflow mutation, secret mutation, tag mutation, or branch deletion.

Do not expand scope to solve a Stop Condition. Preserve current evidence and write a concrete next-Decision recommendation.
