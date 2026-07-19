```json decision_meta
{
  "schema_version": 1,
  "decision_id": "decision_20260719_remote_attestation_truth_and_ci_command_parity_rework_v8",
  "round_id": "round_20260719_remote_attestation_truth_and_ci_command_parity_rework_v8",
  "based_on_state_build_id": "state_20260618_134029_d6bd033d2532",
  "based_on_state_digest": "d6bd033d25324345cfd8ada0ac65db42bc86eb5017f3ffc92906fcd8b71cacb5",
  "status": "APPROVED",
  "mainline": "engineering_branch",
  "skill_profiles": ["reverse-agent-iteration@v2"]
}
```

```json decision_contract
{
  "follows_last_decision_id": "decision_20260718_ci_pr_branch_authority_and_history_parity_rework_v7",
  "follows_last_round_id": "round_20260718_ci_pr_branch_authority_and_history_parity_rework_v7",
  "previous_audit_outcome": "REWORK_REQUIRED",
  "restart_mode": "explicit_new_round_after_remote_stop_condition",
  "restart_authorized_by_user": true,
  "previous_round_artifacts_read_only": true,
  "required_profile": "full",
  "execution_branch": "agent/terminal-status-propagation-seal-restart-rework-v3",
  "base_branch": "main",
  "reuse_existing_draft_pr_number": 5,
  "previous_final_head_sha": "a151dd6fc83a3c01e4e2046fb05bff1eb22a03a4",
  "previous_decision_commit_sha": "3017c88f4a9d8abbf11f1bb8ed0fbcf5b853377b",
  "decision_commit_must_precede_implementation": true,
  "decision_content_digest_lock_required": true,
  "command_plan_branch_binding_required": true,
  "command_plan_digest_lock_required": true,
  "final_command_plan_precedes_substantive_execution": true,
  "new_execution_segment_required": true,
  "workflow_commands_must_be_command_plan_authorized": true,
  "ci_only_commands_require_local_transcript": false,
  "ci_only_commands_require_remote_execution_evidence": true,
  "external_remote_attestation_required": true,
  "pre_attestation_recommendation": "PENDING_EXTERNAL",
  "remote_green_required_for_external_acceptance": true,
  "post_attestation_commit_allowed": false,
  "context_sync_required": true,
  "state_manifest_required": true,
  "closeout_required": true,
  "close_round_required": true,
  "final_evidence_seal_required": true,
  "pytest_required": true,
  "publication_authorization": {
    "granted_by_user": true,
    "allowed_branch": "agent/terminal-status-propagation-seal-restart-rework-v3",
    "base_branch": "main",
    "reuse_existing_draft_pr_number": 5,
    "decision_commit_allowed": true,
    "implementation_commit_allowed": true,
    "push_allowed": true,
    "draft_pr_allowed": true,
    "direct_push_to_main_allowed": false,
    "force_push_allowed": false,
    "merge_allowed": false,
    "rebase_allowed": false,
    "git_add_all_allowed": false,
    "stage_only_explicit_allowed_paths": true,
    "post_attestation_commit_allowed": false
  }
}
```

# DECISION_PACKET

## 1. Goal

Complete one narrowly bounded `engineering_branch` rework round on the existing branch and Draft PR #5:

```text
branch: agent/terminal-status-propagation-seal-restart-rework-v3
base: main
PR: #5
```

Repair the remaining v7 acceptance and CI-parity defects without reopening the already-fixed detached-HEAD branch resolution or full-history ancestry work.

This round has four targets only:

1. introduce a backward-compatible pre-attestation state, `PENDING_EXTERNAL`, so an immutable final commit can truthfully state that remote checks have not yet completed;
2. make the locked `command_plan.json` authorize both local commands and exact CI-only workflow commands, while requiring local transcript evidence only for local commands;
3. make report-summary, final-check, closeout, round archive, context, state manifest, and final seal agree on local readiness without falsely claiming remote success;
4. ensure the final external audit, not a post-final branch commit, converts exact-head remote results into `ACCEPTED`, `ACCEPTED_WITH_LIMITATIONS`, `REWORK_REQUIRED`, or `BLOCKED`.

Reuse the existing report-summary, execution-log, command-plan, closeout, archive, context, state-manifest, final-seal, CI, State Gate, and Decision Preflight foundations. Do not recreate them.

The committed v8 Decision must precede implementation. The final implementation/evidence commit must remain immutable while CI, State Gate, and Decision Preflight run. No remote receipt may be committed afterward.

## 2. Current Evidence

- After this Decision commit, `project_state/decision_packet.md` is the sole task authority. `project_state/task_packet.json` remains background-only sample guidance and does not control this round.
- Current mainline is `engineering_branch`. This is a gate/report/CI authorization repair, not project-governance roadmap work, reverse-solving, tool integration, training-dataset work, Web work, Runner work, or User Solve work.
- Draft PR #5 is open, unmerged, mergeable, targets `main`, and uses branch `agent/terminal-status-propagation-seal-restart-rework-v3`.
- The audited v7 final head is `a151dd6fc83a3c01e4e2046fb05bff1eb22a03a4`.
- GitHub checks for exact v7 head completed as follows:
  - CI run `29687546577`: `completed/success`;
  - State Gate run `29687546578`: `completed/failure`;
  - Decision Preflight run `29687546615`: `completed/failure`.
- The v7 branch/history repair itself worked:
  - State Gate checkout used `fetch-depth: 0`;
  - State Gate `Project gate preflight` passed;
  - Decision Preflight `Project gate preflight`, command-plan, and Decision preflight passed;
  - detached PR execution branch resolution and Decision ancestry are no longer the failing surface.
- The new remote failures are:
  - State Gate job `88194405031` failed at `Project gate report summary`;
  - Decision Preflight job `88194405106` failed at `Local CI parity`.
- The v7 report summary is `FAILED` with `acceptance_recommendation = REWORK_REQUIRED`.
- `project_state/gates/run_closeout_result.json` records `closeout_status = FAILED`, `workflow_execution_status = FAILED`, and `terminal_acceptance_status = REWORK_REQUIRED`.
- `project_state/gates/final_gate_result.json` records `gate_status = WARN`, not `PASSED`.
- The v7 report body nevertheless marks all 24 Required Audit items `PASS`, including claims that exact-head State Gate and Decision Preflight succeeded. Those claims conflict with GitHub observations and with the report's own empty remote-check summary.
- The committed `project_state/gates/local_ci_parity_result.json` is historical evidence from an older Decision and is not current v7 remote evidence. The current remote failure must be read from the exact v7 workflow artifact or job logs.
- The v7 command-plan authorizes local commands but does not represent every CI-only command executed by State Gate and Decision Preflight. CI commands must not gain implicit authority merely because they appear in workflow YAML.
- The v7 execution log warns that the required `final-evidence-seal` command was not recorded as a normal command entry and is represented only by a terminal event.
- The current context packet exists, but it was generated before the later live `final_gate_result.json` update and therefore cannot override the later `WARN` status. It must be refreshed during v8.
- The workstream registry exists and records `github_ci_and_state_gate` as roadmap work, but roadmap entries are not execution authority. This v8 Decision directly authorizes only the bounded repair described here.
- `based_on_state_build_id` and `based_on_state_digest` still identify the older sample-derived state build. Dynamic v8 facts come from the current branch, current project-state artifacts, and exact GitHub observations above; the old sample build is not treated as current engineering evidence.
- `current_state.json`, `task_packet.json`, `artifact_index.json`, and `negative_results.json` contain older `samplereverse` facts. They remain read-only and nonblocking for this engineering round.
- `negative_results.json` prohibits repeated reverse-solving directions and committing full `solve_reports/`. This round does not enter reverse solving and does not repeat those failures.
- Existing capabilities already include Decision locking, branch-bound command-plan generation, execution-log synthesis, report-summary synthesis, final-check, run-closeout, close-round, round archive, context packet, state manifest, final evidence seal, GitHub CI, State Gate, Decision Preflight, CI observation artifacts, policy-lint, and prompt-consistency. This round strengthens their composition only.
- Allowed capabilities are deterministic local Python, focused pytest, Git inspection, YAML inspection, existing project-gate commands, and read-only observation of GitHub Actions for exact commits.
- Reverse tools, debuggers, emulators, model APIs, Runner dispatch, Web runtime, databases, cleanup apply, destructive operations, and full historical artifact scans are not allowed.
- Closeout is allowed only after the v8 Decision and command-plan locks are current, a new v8 execution segment exists, local/CI command authorization parity passes, and pre-attestation status semantics pass focused tests.
- This round does not duplicate branch fallback, ancestry proof, prompt versioning, prompt consistency, policy-lint, report-summary, execution-log, command-plan, context, state-manifest, archive, seal, or CI mechanisms.

## 3. Do Not Do

Do not:

- work on `main`, create another branch, or open another PR;
- merge PR #5 or mark it ready for review during implementation;
- rebase, force-push, amend published history, delete branches, tag, or push directly to `main`;
- use `git add -A` or stage files outside the explicit allowlist;
- edit v4-v7 archived or sealed artifacts to make historical rounds pass;
- reuse v7 `PASSED`, `SUCCESS`, remote, context, manifest, archive, seal, or report claims as v8 evidence;
- repeat the detached-HEAD branch fallback or `fetch-depth: 0` repair unless a regression test proves an actual defect;
- weaken branch-local authority, Decision ancestry, valid-mainline, active-skill, forbidden-path, capability, or command-plan policy;
- allow workflow YAML to authorize commands outside the locked command-plan;
- require CI-only commands to appear falsely as locally executed commands;
- treat missing remote results as success, `NOT_APPLICABLE`, or `PASS`;
- claim exact-head workflow success before GitHub reports terminal success;
- require a post-final branch commit to record remote observations;
- make State Gate or Decision Preflight inspect their own future conclusion;
- globally redesign all report statuses or all lifecycle schemas when one backward-compatible pre-attestation state is sufficient;
- modify `.github/workflows/ci.yml`; its exact v7 run succeeds;
- modify packaging metadata, reverse-solving logic, sample solvers, harnesses, tool adapters, Runner, Job orchestration, frontend, User Solve, roadmap, database, cleanup, retention, or state-domain architecture;
- redesign `project_state/`, move state files, delete files, or perform cleanup apply;
- run commands absent from the locked v8 command-plan;
- read full `solve_reports/` or `PROJECT_PROGRESS_LOG.txt`;
- create any branch commit after the final v8 validation commit while remote attestation is being observed;
- commit a remote-check receipt after the final v8 validation commit.

## 4. Files To Inspect

Required current evidence:

- `project_state/decision_packet.md`
- `project_state/task_packet.json`
- `project_state/current_state.json`
- `project_state/artifact_index.json`
- `project_state/negative_results.json`
- `project_state/codex_execution_report.md`
- `project_state/execution_report.md`
- `project_state/pytest_result.txt`
- `project_state/state_manifest.json`
- `project_state/context/current_context_packet.json`
- `project_state/roadmap/workstreams.json`
- `project_state/gates/command_plan.json`
- `project_state/gates/command_plan_lock.json`
- `project_state/gates/decision_content_lock.json`
- `project_state/gates/execution_log.json`
- `project_state/gates/report_summary_synthesis.json`
- `project_state/gates/final_gate_result.json`
- `project_state/gates/run_closeout_result.json`
- `project_state/gates/final_evidence_seal.json`
- `project_state/gates/restart_segment.json`
- `project_state/gates/local_ci_parity_result.json`
- `project_state/gates/ci_workflow_readiness_result.json`
- `project_state/gates/ci_run_evidence_result.json`
- `project_state/gates/ci_observation_reconcile_result.json`
- `project_state/rounds/round_20260718_ci_pr_branch_authority_and_history_parity_rework_v7/round_manifest.json`
- `.codex-skills/registry.json`

Required engineering files:

- `reverse_agent/project_gate.py`
- `reverse_agent/decision_preflight.py`
- `tests/test_project_gate.py`
- `tests/test_project_reports.py`
- `tests/test_decision_preflight.py`
- `.github/workflows/ci.yml` as read-only input
- `.github/workflows/state-gate.yml`
- `.github/workflows/decision-preflight.yml`

Required external observations:

- PR #5 metadata and exact current head SHA;
- v7 CI run `29687546577`;
- v7 State Gate run `29687546578`, job `88194405031`, and its evidence artifact;
- v7 Decision Preflight run `29687546615`, job `88194405106`, and its evidence artifact;
- final v8 workflow runs and exact final v8 head SHA.

Do not inspect unrelated source trees unless an authorized focused test identifies a concrete in-scope dependency.

## 5. Required Audit

The final v8 report must answer each item with an artifact path or GitHub observation, concrete value, status, and conclusion:

1. Is execution still on branch `agent/terminal-status-propagation-seal-restart-rework-v3` and Draft PR #5 targeting `main`?
2. Is the v8 Decision `APPROVED`, `engineering_branch`, and bound to active `reverse-agent-iteration@v2`?
3. Is the committed v8 Decision the sole task authority, with `task_packet.json` background-only?
4. Is the v8 Decision commit an ancestor of every v8 implementation, evidence, final publication commit, and PR merge-test commit?
5. Are v4-v7 archived and sealed artifacts unchanged?
6. Does a new v8 execution segment exist with v8 IDs, v8 Decision digest, v8 command-plan digest, v8 startup time, and no reused v4 restart identity?
7. Was v8 Decision content locked before the final v8 command-plan was generated and locked?
8. Does the final command-plan bind the exact v8 IDs, branch, Decision digest, Decision commit, and plan digest?
9. Does the command-plan distinguish local commands from CI-only commands without weakening either command authority?
10. Does every executable command in `.github/workflows/ci.yml`, `state-gate.yml`, and `decision-preflight.yml` have exact command-plan authorization or an explicitly accepted non-project setup classification?
11. Are CI-only commands exempt only from local transcript requirements, while still requiring exact remote workflow evidence?
12. Does `local-ci-parity` fail closed for an unauthorized workflow command and pass for an authorized CI-only command?
13. Is `PENDING_EXTERNAL` available only when the Decision explicitly requires external attestation and forbids post-attestation commits?
14. Does `PENDING_EXTERNAL` mean local prerequisites passed but no claim is made about remote conclusions?
15. Do report-summary and Required Audit reject false remote `PASS` claims when remote observations are absent, stale, from another Decision, or for another head SHA?
16. Can final-check, run-closeout, close-round, context sync, state manifest, archive, and final seal converge on truthful local readiness without claiming external acceptance?
17. Is `PENDING_EXTERNAL` never treated as final `ACCEPTED` inside the repository?
18. Does the external audit remain the only authority that converts exact-head remote results into one of the four allowed audit conclusions?
19. Is the current context packet generated after the final live local gate and bound to its digest?
20. Do report-summary, execution-log, pytest metadata, final-check, context, state manifest, round manifest, closeout, and seal agree on v8 IDs and the pre-attestation recommendation?
21. Is every required local command recorded with command, kind, exit code, stdout/stderr provenance, and observed chronology?
22. Is `final-evidence-seal` recorded as an authorized executed command and not only as an ungrounded terminal event?
23. Do focused tests cover report truth, pending-external semantics, command-plan CI surfaces, stale remote evidence, head-SHA binding, execution segment identity, and final-seal logging?
24. Are all changed files inside the v8 allowlist?
25. Were merge, rebase, force-push, direct-main push, branch creation, new PR creation, and `git add -A` avoided?
26. Is the final v8 validation commit the PR head with no later branch commit?
27. Did CI complete successfully for exact final v8 head?
28. Did State Gate complete successfully for exact final v8 head?
29. Did Decision Preflight complete successfully for exact final v8 head?
30. Do exact-head remote results support the external audit conclusion without any post-final repository mutation?

Before remote checks finish, items 27-30 must be reported as `PENDING_EXTERNAL`, not `PASS`. They are decided by the external audit after the immutable final commit has terminal workflow results.

## 6. Implementation Scope

### 6.1 Authority and restart

1. Treat this committed v8 Decision as the sole current task authority.
2. Verify the local branch can fast-forward to the remote branch without merge or rebase.
3. Verify PR #5 remains open, Draft, unmerged, and targets `main`.
4. Lock the v8 Decision content.
5. Generate and lock one branch-bound v8 command-plan before substantive source, test, workflow, report, or state changes.
6. Create a new v8 execution segment. Do not reuse `restart_20260717_v4_01` and do not append v8 evidence to v7.

### 6.2 Two-stage acceptance truth

Add the smallest backward-compatible representation needed for:

```text
LOCAL EXECUTION COMPLETE
        ↓
PENDING_EXTERNAL
        ↓
external audit reads exact-head workflow results
        ↓
ACCEPTED / ACCEPTED_WITH_LIMITATIONS / REWORK_REQUIRED / BLOCKED
```

Requirements:

- `PENDING_EXTERNAL` is allowed only when the current Decision explicitly requires external remote attestation.
- It means all required local implementation, tests, report, execution-log, final-check, closeout, archive, context, state-manifest, and seal prerequisites have passed.
- It does not mean any remote workflow has succeeded.
- Required Audit remote items remain `PENDING_EXTERNAL` before terminal observations.
- Missing, stale, wrong-Decision, wrong-round, or wrong-head remote evidence must never become `PASS`.
- Existing Decisions that do not opt into this contract retain current status behavior.
- Do not add a general workflow engine or redesign unrelated lifecycle states.

### 6.3 Command-plan CI execution surfaces

Extend the existing command-plan contract in the smallest compatible way so it can represent:

- local commands that require local transcript evidence;
- CI-only commands that are authorized for exact workflow files and require remote workflow evidence;
- non-project setup steps such as `actions/checkout`, Python setup, and package installation, classified explicitly rather than silently ignored.

The final `command_plan.json` must either contain an explicit `ci_commands` collection or an equivalent schema that provides, for each CI-only command:

- exact command string;
- kind;
- workflow path;
- execution surface;
- required/optional status;
- expected exit codes;
- whether local transcript is required;
- whether remote execution evidence is required.

`local-ci-parity` must compare workflow commands against this locked authority. It must not demand that CI-only commands appear as locally executed commands, and it must not allow workflow commands absent from the plan.

### 6.4 Report, closeout, and external audit boundary

Repair only the status and evidence composition necessary to make these statements simultaneously true:

- the immutable final commit contains truthful local evidence;
- local artifacts do not claim future remote success;
- State Gate and Decision Preflight can validate the commit's local readiness and command authority;
- external audit can later use exact-head GitHub observations without a repository mutation.

The report must use concrete evidence for each Required Audit answer. Generic phrases such as “satisfied by required_audit_coverage” are not sufficient for live branch, head, workflow, closeout, or remote claims.

### 6.5 Execution-log and final-seal provenance

Ensure:

- all required local commands are represented in execution order;
- `final-evidence-seal` is a normal authorized command record with exit code and artifact provenance;
- a terminal event may reference the seal but cannot replace the command record;
- run-closeout and close-round do not report success while a required local command is missing;
- CI-only commands are recorded by exact workflow evidence, not fabricated into the local transcript.

### 6.6 Workflow changes

Treat `.github/workflows/ci.yml` as read-only.

Modify `.github/workflows/state-gate.yml` or `.github/workflows/decision-preflight.yml` only if a minimal change is necessary to consume the new command-plan execution-surface contract or truthful pre-attestation state.

Preserve:

- `actions/checkout@v4`;
- `fetch-depth: 0`;
- branch authority checks;
- Decision ancestry checks;
- existing failing-step visibility;
- evidence artifact upload.

Do not skip `report-summary`, `local-ci-parity`, or final validation merely to make checks green.

### 6.7 Allowed implementation and artifact paths

```text
reverse_agent/project_gate.py
reverse_agent/decision_preflight.py
tests/test_project_gate.py
tests/test_project_reports.py
tests/test_decision_preflight.py
.github/workflows/state-gate.yml
.github/workflows/decision-preflight.yml
project_state/state_manifest.json
project_state/context/current_context_packet.json
project_state/gates/*.json
project_state/pytest_result.txt
project_state/codex_execution_report.md
project_state/execution_report.md
project_state/rounds/round_20260719_remote_attestation_truth_and_ci_command_parity_rework_v8/*
```

`reverse_agent/decision_preflight.py` may change only if the current implementation owner for exact-head or local-CI parity semantics is there. Otherwise leave it unchanged.

`project_state/decision_packet.md` is modified only by this already-authorized v8 Decision commit. Do not modify it during implementation.

All other source, workflow, test, roadmap, Skills, Runner, Job, frontend, User Solve, reverse-solving, packaging, database, cleanup, retention, sample, tool-integration, and historical archive paths are forbidden.

### 6.8 Publication boundary

After all local v8 validation, closeout, archive, context/state sync, and seal evidence converge truthfully:

1. stage only explicit allowed paths;
2. create one final v8 validation commit on the existing branch;
3. push it to the existing branch;
4. stop all branch mutation;
5. observe CI, State Gate, and Decision Preflight for that exact commit;
6. perform external audit from GitHub observations;
7. do not commit a remote receipt or rewrite the report after remote checks.

The v8 Decision commit itself may trigger intermediate failing workflows before implementation. Those runs are not final acceptance evidence.

## 7. Tests

The final locked command-plan must authorize platform-appropriate equivalents of the following local commands and no broader Git operations:

```text
Set-Location F:\reverse-agent
Get-Location
Test-Path F:\reverse-agent
git rev-parse --show-toplevel
git status --short
git log --oneline --decorate -n 12

python -m reverse_agent.project_gate decision-lint --state-dir project_state
python -m reverse_agent.project_gate preflight --state-dir project_state
python -m reverse_agent.project_gate gate-profile --state-dir project_state --profile full
python -m reverse_agent.project_gate command-plan --state-dir project_state
python -m reverse_agent.project_gate command-plan --state-dir project_state --json

python -m pytest tests/test_project_gate.py tests/test_project_reports.py tests/test_decision_preflight.py -q
python -m pytest tests/test_project_gate.py tests/test_project_reports.py tests/test_decision_preflight.py tests/test_post_final_evidence_sync.py tests/test_project_state.py tests/test_project_jobs.py -q

python -m reverse_agent.project_gate local-ci-parity --state-dir project_state
python -m reverse_agent.project_gate report-summary --state-dir project_state
python -m reverse_agent.project_gate execution-log --state-dir project_state
python -m reverse_agent.project_gate final-check --state-dir project_state
python -m reverse_agent.project_gate run-closeout --state-dir project_state --round-id round_20260719_remote_attestation_truth_and_ci_command_parity_rework_v8
python -m reverse_agent.project_gate close-round --state-dir project_state --round-id round_20260719_remote_attestation_truth_and_ci_command_parity_rework_v8
python -m reverse_agent.project_gate post-final-evidence-sync --state-dir project_state
python -m reverse_agent.project_gate final-check --state-dir project_state
python -m reverse_agent.project_gate final-evidence-seal --state-dir project_state --round-id round_20260719_remote_attestation_truth_and_ci_command_parity_rework_v8

git diff --check
git status --short
```

The same locked command-plan must authorize, as CI-only commands, every executable command currently present in:

```text
.github/workflows/ci.yml
.github/workflows/state-gate.yml
.github/workflows/decision-preflight.yml
```

At minimum, the CI authorization set must cover the exact workflow invocations for:

```text
pytest
preflight
command-plan
post-final-evidence-sync
job-lifecycle
audit-inventory
audit-readiness-packet
current-handoff-packet
local-execution-bundle
codex-prompt-packet
audit-precheck
report-summary
execution-log
ci-workflow-coverage
ci-workflow-readiness
decision-preflight
ci-run-evidence
local-ci-parity
ci-observation-schema
ci-observation-handoff
ci-observation-reconcile
ci-artifact-manifest
ci-audit-handoff-bundle
final-check
```

The tests must explicitly cover:

- backward compatibility for Decisions without external attestation;
- valid `PENDING_EXTERNAL` for an opted-in Decision with complete local evidence;
- rejection of `PENDING_EXTERNAL` when local evidence is incomplete;
- rejection of false remote `PASS` claims;
- stale, wrong-Decision, wrong-round, wrong-head, nonterminal, failure, and success remote observations;
- local versus CI-only command authorization;
- unauthorized workflow command failure;
- CI-only command not requiring local transcript;
- CI-only command requiring remote workflow evidence;
- new v8 execution segment identity;
- final-evidence-seal command record and terminal-event consistency;
- State Gate and Decision Preflight workflow parity;
- existing detached-HEAD and ancestry regression tests remaining green.

Local pre-attestation acceptance requires:

```text
focused tests = PASSED
local-ci-parity = PASSED
report-summary = PASSED
execution-log = PASSED
final-check = PASSED
run-closeout = PASSED
close-round = CLOSED
context packet = current
state manifest = current
round manifest = current
final evidence seal = current
report recommendation = PENDING_EXTERNAL
no remote item falsely marked PASS
```

External audit acceptance additionally requires:

```text
PR head SHA = exact final v8 commit
CI = completed/success for exact final v8 commit
State Gate = completed/success for exact final v8 commit
Decision Preflight = completed/success for exact final v8 commit
no later branch commit
external audit conclusion is supported by exact-head observations
```

## 8. Stop Conditions

Stop with `BLOCKED` or `REWORK_REQUIRED` and do not expand scope if:

- the branch cannot fast-forward to the remote branch without merge or rebase;
- PR #5, branch, v8 Decision, digest, or expected branch identity cannot be verified;
- the v8 Decision or command-plan lock fails;
- a new v8 execution segment cannot be created without editing historical segment evidence;
- a required local or CI-only command is absent from the locked command-plan;
- command-plan parity can pass only by ignoring executable workflow commands;
- CI-only commands can be represented only by falsely claiming local execution;
- `PENDING_EXTERNAL` requires a broad unrelated status or lifecycle redesign;
- local readiness can pass only by treating missing remote results as success;
- remote truth can be preserved only by creating a post-final branch commit;
- report-summary, final-check, closeout, archive, context, manifest, or seal requires false future-completion claims;
- the fix requires modifying `.github/workflows/ci.yml`;
- the fix requires weakening branch authority, Decision ancestry, command authorization, forbidden-path, or evidence freshness policy;
- focused tests fail or do not cover every changed test file and required status/CI-parity case;
- local preflight fails on the real execution branch;
- report ID, command output, exit code, execution-log, report-summary, final-check, context, manifest, archive, closeout, seal, or recommendation parity fails;
- `final-evidence-seal` remains missing from normal execution-log command records;
- v4-v7 archived or sealed evidence changes;
- unrelated or forbidden paths change;
- publication requires merge, rebase, force-push, direct push to `main`, another branch, or another PR;
- any branch commit is added after the final v8 validation commit;
- PR head changes during attestation;
- CI, State Gate, or Decision Preflight fails or remains nonterminal for the exact final v8 commit.

Do not solve a Stop Condition by weakening a gate, suppressing evidence, editing historical artifacts, fabricating remote success, or expanding to another mainline.
