```json decision_meta
{
  "schema_version": 1,
  "decision_id": "decision_20260720_ci_consumed_decision_preflight_parity_rework_v9",
  "round_id": "round_20260720_ci_consumed_decision_preflight_parity_rework_v9",
  "based_on_state_build_id": "state_20260618_134029_d6bd033d2532",
  "based_on_state_digest": "d6bd033d25324345cfd8ada0ac65db42bc86eb5017f3ffc92906fcd8b71cacb5",
  "status": "APPROVED",
  "mainline": "engineering_branch",
  "skill_profiles": ["reverse-agent-iteration@v2"]
}
```

```json decision_contract
{
  "follows_last_decision_id": "decision_20260719_remote_attestation_truth_and_ci_command_parity_rework_v8",
  "follows_last_round_id": "round_20260719_remote_attestation_truth_and_ci_command_parity_rework_v8",
  "previous_audit_outcome": "REWORK_REQUIRED",
  "restart_mode": "explicit_new_round_after_exact_head_remote_failure",
  "restart_authorized_by_user": true,
  "previous_round_artifacts_read_only": true,
  "required_profile": "full",
  "execution_branch": "agent/terminal-status-propagation-seal-restart-rework-v3",
  "base_branch": "main",
  "reuse_existing_draft_pr_number": 5,
  "previous_final_head_sha": "38ac23d59119973d6154e49c26fde272bbc81298",
  "previous_decision_commit_sha": "d2807e0f976bc4a1304331c9947c327b8a92d93f",
  "decision_commit_must_precede_implementation": true,
  "decision_content_digest_lock_required": true,
  "command_plan_branch_binding_required": true,
  "command_plan_digest_lock_required": true,
  "command_plan_precedes_workflow_edit_required": true,
  "new_execution_segment_required": true,
  "strict_local_preflight_remains_default": true,
  "ci_final_commit_preflight_allows_consumed": true,
  "allow_consumed_scope": "decision_not_consumed_by_report_only",
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
  "queued_pr_6_must_remain_inactive": true,
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
Draft PR: #5
```

Repair only the remaining exact-head CI validation defect from v8:

1. preserve strict local execution-start preflight, where an already-consumed Decision remains blocked;
2. make State Gate and Decision Preflight explicitly validate immutable final commits with `preflight --allow-consumed`;
3. prove that `--allow-consumed` relaxes only `decision_not_consumed_by_report` and does not bypass Decision ID, Round ID, status, skill, branch authority, Decision ancestry, scope, capability, or command-plan checks;
4. make the locked v9 command-plan authorize the exact updated CI-only commands before either workflow file is edited;
5. keep local transcript and CI-only remote evidence semantics distinct;
6. produce one immutable final v9 validation commit for which CI, State Gate, and Decision Preflight all complete successfully;
7. leave final remote acceptance to an external audit without committing a remote receipt afterward.

Do not reopen the v8 implementation of `PENDING_EXTERNAL`, CI-only command surfaces, report-summary, execution-log, closeout, context synchronization, state manifest, round archive, or final seal except where new v9 evidence must be generated.

## 2. Current Evidence

- After this Decision commit, `project_state/decision_packet.md` is the sole current task authority. `project_state/task_packet.json` remains background-only sample guidance.
- Current mainline is `engineering_branch`. This is a CI/preflight composition repair, not project-governance roadmap work, reverse solving, tool integration, training-dataset work, Web work, Runner work, or User Solve work.
- Draft PR #5 is open, Draft, unmerged, mergeable, targets `main`, and uses branch `agent/terminal-status-propagation-seal-restart-rework-v3`.
- The independently audited v8 final head is `38ac23d59119973d6154e49c26fde272bbc81298`.
- Exact-head v8 GitHub results are:
  - CI: `completed/success`;
  - State Gate: `completed/failure` at `Project gate preflight`;
  - Decision Preflight: `completed/failure` at `Project gate preflight`.
- The uploaded State Gate evidence records:
  - `gate_status = BLOCKED`;
  - `decision_not_consumed_by_report = FAIL`;
  - `decision_execution_state = CONSUMED_BY_SUCCESS_REPORT`;
  - all other preflight checks shown in that artifact passed.
- Both `.github/workflows/state-gate.yml` and `.github/workflows/decision-preflight.yml` currently execute strict `python -m reverse_agent.project_gate preflight --state-dir project_state` against a final commit that intentionally contains its successful report.
- Strict local preflight is still correct before a new execution begins. It must not be globally weakened.
- Final-commit remote validation is a different surface: the Decision is expected to be consumed by the report, so the workflow must explicitly opt into `--allow-consumed`.
- v8 local evidence converged: the report used `PENDING_EXTERNAL`; selected pytest groups passed; final-check passed; run-closeout passed; close-round closed; context and state manifest were synchronized; the round was archived and sealed.
- The v8 report correctly left remote audit items pending instead of claiming future success.
- The current `state_manifest.json` and context packet identify v8 live evidence. They are current for v8 but must be regenerated for v9 before v9 closeout.
- `current_state.json`, `task_packet.json`, `artifact_index.json`, and `negative_results.json` still contain older `samplereverse` context. They are read-only and nonblocking for this engineering round.
- Artifact freshness currently reports 10 current references and 50 missing historical sample artifacts. Those sample artifacts are nonblocking for this non-sample engineering round.
- `negative_results.json` prohibits repeated reverse-solving searches and committing full `solve_reports/`. This round does not enter reverse solving or repeat those directions.
- Existing capabilities must be reused: decision-lint, strict preflight, `--allow-consumed`, branch-local authority, Decision ancestry, decision lock, command-plan generation and lock, execution segments, CI workflow coverage, local-CI parity, report-summary, execution-log, final-check, run-closeout, close-round, context builder, state manifest, archive, final seal, policy-lint, and prompt-consistency.
- This round does not implement a new preflight framework, command-plan framework, CI framework, report system, execution log, or seal. It repairs only their consumed-Decision validation composition.
- Allowed tools are deterministic local Python, focused pytest, Git inspection, YAML inspection, existing project-gate commands, and read-only exact-head GitHub observation after publication.
- No reverse tool, debugger, emulator, model API, Runner dispatch, Web runtime, database, cleanup apply, destructive operation, or external dependency installation is authorized.
- Full `solve_reports/`, full `PROJECT_PROGRESS_LOG.txt`, unrelated historical rounds, and unrelated heavy artifacts must not be read.
- Closeout is allowed only after the v9 Decision content and v9 command-plan are locked, a new v9 execution segment exists, target workflow commands are already authorized, tests pass, local-CI parity passes, and current-round report/evidence agree.
- Gate profile is `full`. The command-plan is the only command authority. Commands omitted by the command-plan must not run.
- `project_state/context/current_context_packet.json` exists, and `project_state/roadmap/workstreams.json` exists. The roadmap is not execution authority and must not be modified in this round.
- PR #6 remains `QUEUED_NOT_ACTIVE`; it must not be modified, merged, activated, or executed until PR #5 is independently accepted and integrated into `main`.

## 3. Do Not Do

Do not:

- work on `main`, create another branch, or open another PR;
- merge PR #5 or mark it ready for review during implementation;
- rebase, force-push, amend published history, delete branches, tag, or push directly to `main`;
- use `git add -A` or stage files outside the explicit allowlist;
- modify PR #6 or promote its queued Decision;
- edit v4-v8 archived or sealed artifacts to make historical rounds pass;
- replace or delete `decision_not_consumed_by_report`;
- make `--allow-consumed` the default for local execution-start preflight;
- let `--allow-consumed` bypass Decision ID, Round ID, Decision status, active skill, branch-local authority, Decision ancestry, scope, forbidden paths, capabilities, or command-plan checks;
- allow a failed, mismatched, stale, wrong-round, wrong-Decision, or unapproved report to satisfy consumed validation;
- infer remote success from local `PENDING_EXTERNAL` evidence;
- claim exact-head workflow success before GitHub reports terminal success;
- commit a remote-check receipt after the immutable final v9 validation commit;
- modify `.github/workflows/ci.yml`;
- skip preflight, report-summary, local-CI parity, final-check, closeout, archive, context/state refresh, or final seal merely to make workflows green;
- run any command absent from the locked v9 command-plan;
- modify packaging metadata or install BMAD, LangGraph, Microsoft Agent Framework, or any other new dependency;
- modify Runner, Jobs, Web, frontend, User Solve, reverse-solving, solver, harness, sample, tool adapter, database, cleanup, retention, roadmap, workstream, or state-domain architecture;
- read full `solve_reports/` or `PROJECT_PROGRESS_LOG.txt`;
- perform any branch mutation after the final v9 validation commit is pushed.

## 4. Files To Inspect

Required current evidence:

```text
project_state/decision_packet.md
project_state/task_packet.json
project_state/current_state.json
project_state/artifact_index.json
project_state/negative_results.json
project_state/codex_execution_report.md
project_state/execution_report.md
project_state/pytest_result.txt
project_state/state_manifest.json
project_state/context/current_context_packet.json
project_state/roadmap/workstreams.json

project_state/gates/command_plan.json
project_state/gates/command_plan_lock.json
project_state/gates/decision_content_lock.json
project_state/gates/preflight_result.json
project_state/gates/restart_segment.json
project_state/gates/execution_log.json
project_state/gates/report_summary_synthesis.json
project_state/gates/local_ci_parity_result.json
project_state/gates/final_gate_result.json
project_state/gates/run_closeout_result.json
project_state/gates/final_evidence_seal.json

.codex-skills/registry.json
```

Required engineering files:

```text
reverse_agent/project_gate.py
reverse_agent/decision_preflight.py
tests/test_project_gate.py
tests/test_project_reports.py
tests/test_decision_preflight.py
.github/workflows/ci.yml
.github/workflows/state-gate.yml
.github/workflows/decision-preflight.yml
```

Read-only v8 archive:

```text
project_state/rounds/round_20260719_remote_attestation_truth_and_ci_command_parity_rework_v8/round_manifest.json
project_state/rounds/round_20260719_remote_attestation_truth_and_ci_command_parity_rework_v8/decision_packet.md
project_state/rounds/round_20260719_remote_attestation_truth_and_ci_command_parity_rework_v8/codex_execution_report.md
project_state/rounds/round_20260719_remote_attestation_truth_and_ci_command_parity_rework_v8/execution_report.md
project_state/rounds/round_20260719_remote_attestation_truth_and_ci_command_parity_rework_v8/pytest_result.txt
```

Required external observations:

```text
PR #5 metadata and exact current head SHA
v8 CI run 29697859077
v8 State Gate run 29697859062 and uploaded preflight evidence
v8 Decision Preflight run 29697859089
final v9 CI, State Gate, and Decision Preflight runs for the immutable final v9 head
```

Do not inspect unrelated source trees unless an authorized focused test identifies a concrete in-scope dependency.

## 5. Required Audit

The final v9 report must answer every item separately with an artifact path or exact GitHub observation, concrete value, status, and conclusion:

1. Is execution still on branch `agent/terminal-status-propagation-seal-restart-rework-v3` and Draft PR #5 targeting `main`?
2. Is the v9 Decision `APPROVED`, `engineering_branch`, and bound to active `reverse-agent-iteration@v2`?
3. Is the committed v9 Decision the sole task authority, with `task_packet.json` background-only?
4. Is the v9 Decision commit an ancestor of every v9 implementation, evidence, final publication, and PR merge-test commit?
5. Are v4-v8 archived and sealed artifacts unchanged?
6. Does a new v9 execution segment exist with v9 IDs, v9 Decision digest, v9 command-plan digest, v9 startup time, and a new restart identity?
7. Was v9 Decision content locked before the final v9 command-plan was generated and locked?
8. Did the locked command-plan exist before either workflow file was edited?
9. Does the final command-plan bind the exact v9 IDs, branch, Decision digest, Decision commit, and plan digest?
10. Does strict local preflight still fail when the current Decision is already consumed by a matching successful report?
11. Does strict local preflight pass for a fresh, unconsumed, otherwise valid v9 Decision before execution begins?
12. Does `preflight --allow-consumed` relax only `decision_not_consumed_by_report`?
13. Does consumed validation still reject a wrong Decision ID?
14. Does consumed validation still reject a wrong Round ID?
15. Does consumed validation still reject a failed or non-success report state where current policy requires success/local readiness?
16. Does consumed validation still reject a non-`APPROVED` Decision?
17. Does consumed validation still reject inactive or mismatched Skill profiles?
18. Does consumed validation still reject invalid branch-local authority or Decision ancestry?
19. Does consumed validation still reject forbidden paths, capability violations, and command-plan conflicts?
20. Does State Gate use the exact CI-only command `python -m reverse_agent.project_gate preflight --state-dir project_state --allow-consumed`?
21. Does Decision Preflight use the same explicit consumed-validation command?
22. Is `.github/workflows/ci.yml` unchanged?
23. Did the locked command-plan authorize both updated workflow commands as CI-only commands before workflow edits?
24. Do those CI-only entries require remote execution evidence and not local transcript evidence?
25. Does `local-ci-parity` fail closed for the old unauthorized strict workflow command and pass for the new authorized consumed-validation command?
26. Does the execution log avoid fabricating CI-only commands as local execution?
27. Do focused tests cover strict versus consumed preflight, mismatched identities, failed reports, branch authority, ancestry, scope, and command-plan protections?
28. Did all required pytest commands complete successfully with real output and exit code 0?
29. Did report-summary pass with concrete, item-specific Required Audit evidence?
30. Did execution-log synthesis pass with observed chronology and command provenance?
31. Did final-check pass for v9 IDs and current artifacts?
32. Did run-closeout pass and close-round produce `CLOSED` for v9?
33. Are context, state manifest, round manifest, report, pytest result, closeout, and seal current and mutually consistent?
34. Is `final-evidence-seal` represented as an authorized executed command and terminal event?
35. Are all changed files inside the v9 allowlist?
36. Were merge, rebase, force-push, direct-main push, new branch, new PR, and `git add -A` avoided?
37. Did PR #6 remain unchanged and `QUEUED_NOT_ACTIVE`?
38. Is the final v9 validation commit the exact PR #5 head with no later branch commit?
39. Did CI complete successfully for the exact final v9 head?
40. Did State Gate complete successfully for the exact final v9 head?
41. Did Decision Preflight complete successfully for the exact final v9 head?
42. Do exact-head remote results support the external audit conclusion without any post-final repository mutation?

Items 38-42 must remain `PENDING_EXTERNAL` in committed local evidence and are decided only by the independent external audit.

## 6. Implementation Scope

### 6.1 Authority and restart

1. Treat this committed v9 Decision as the sole task authority.
2. Verify the local branch can fast-forward to the current remote branch without merge or rebase.
3. Verify PR #5 remains open, Draft, unmerged, and targets `main`.
4. Lock the v9 Decision content.
5. Generate and lock one branch-bound v9 command-plan before any substantive source, test, workflow, report, or state modification.
6. The command-plan must already authorize the target workflow commands containing `--allow-consumed` before workflow files are edited.
7. If the current generator cannot authorize the target commands from this Decision before workflow edits, stop with `BLOCKED`; do not edit workflows first and authorize retrospectively.
8. Create a new v9 execution segment. Do not append v9 evidence to v8 or reuse the v8 restart identity.

### 6.2 Strict local preflight boundary

Preserve default behavior:

```text
python -m reverse_agent.project_gate preflight --state-dir project_state
```

Default strict preflight must:

- pass for a fresh, valid, unconsumed Decision before execution;
- fail for a matching Decision already consumed by its successful report;
- continue checking all existing authority, scope, capability, and command-plan constraints.

Do not change existing local execution prompts or startup policy to use `--allow-consumed`.

### 6.3 Explicit consumed validation boundary

The explicit command:

```text
python -m reverse_agent.project_gate preflight --state-dir project_state --allow-consumed
```

may pass only when:

- the Decision and report identities match;
- the Decision is `APPROVED`;
- the requested Skill is active and version-compatible;
- branch-local authority and Decision ancestry are valid;
- the report state is valid for final-commit local readiness;
- scope, forbidden paths, capabilities, artifact freshness policy, and command-plan consistency still pass.

The flag must suppress only the blocking effect of `decision_not_consumed_by_report`. It must not convert unrelated failures to warnings or passes.

Inspect the existing implementation first. Modify `reverse_agent/project_gate.py` only if current behavior does not satisfy this boundary. Modify `reverse_agent/decision_preflight.py` only if it is the actual implementation owner for a failing required condition.

### 6.4 Workflow changes

Treat `.github/workflows/ci.yml` as read-only.

In both:

```text
.github/workflows/state-gate.yml
.github/workflows/decision-preflight.yml
```

replace only the final-commit validation preflight command with the exact equivalent of:

```text
python -m reverse_agent.project_gate preflight --state-dir project_state --allow-consumed
```

Preserve:

- `actions/checkout@v4`;
- `fetch-depth: 0`;
- Python version and package installation;
- branch authority and ancestry behavior;
- all downstream gate steps;
- failing-step visibility;
- evidence artifact upload;
- current workflow triggers and permissions unless a focused regression proves a strictly necessary in-scope adjustment.

Do not skip preflight or make it non-blocking.

### 6.5 Command-plan and CI parity

The final locked command-plan must classify each updated preflight invocation as:

```text
execution_surface: ci_only
local_transcript_required: false
remote_execution_evidence_required: true
required: true
expected_exit_codes: [0]
```

It must preserve exact workflow path and exact command string.

`local-ci-parity` must prove:

- both updated commands are authorized;
- the old strict workflow command is not treated as current authorization for the modified workflow lines;
- setup steps remain explicitly classified;
- CI-only commands are not required in the local transcript;
- missing or altered workflow commands fail closed.

### 6.6 Tests

Add or strengthen focused tests for:

```text
fresh valid Decision + strict preflight -> PASS
consumed matching Decision + strict preflight -> BLOCKED
consumed matching Decision + --allow-consumed -> PASS
wrong Decision ID + --allow-consumed -> BLOCKED
wrong Round ID + --allow-consumed -> BLOCKED
failed/ineligible report + --allow-consumed -> BLOCKED
unapproved Decision + --allow-consumed -> BLOCKED
inactive/mismatched Skill + --allow-consumed -> BLOCKED
invalid branch authority + --allow-consumed -> BLOCKED
invalid Decision ancestry + --allow-consumed -> BLOCKED
forbidden path/capability conflict + --allow-consumed -> BLOCKED
command-plan conflict + --allow-consumed -> BLOCKED
both workflow commands exactly authorized -> PASS
old or altered workflow preflight command -> FAIL
```

Preserve existing detached-HEAD, full-history ancestry, `PENDING_EXTERNAL`, remote-truth, report-summary, execution-log, and final-seal regressions.

### 6.7 Report and closeout

Generate new v9 artifacts rather than rewriting v8:

- v9 report and execution-report alias;
- v9 pytest result;
- v9 decision/content and command-plan locks;
- v9 execution segment and execution log;
- current report-summary, final-check, closeout, context, state manifest, archive, and final seal;
- `project_state/rounds/round_20260720_ci_consumed_decision_preflight_parity_rework_v9/*`.

The committed report must use `PENDING_EXTERNAL` for exact-head remote items. It must not claim that CI, State Gate, or Decision Preflight succeeded before external observation.

Required Audit answers must cite concrete fields and values; repeated generic wording is insufficient.

### 6.8 Allowed modified paths

```text
project_state/decision_packet.md
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
project_state/rounds/round_20260720_ci_consumed_decision_preflight_parity_rework_v9/*
```

`reverse_agent/project_gate.py` and `reverse_agent/decision_preflight.py` are conditional implementation paths. Leave them unchanged when existing flag behavior already satisfies the required security boundary.

All other source, workflow, test, roadmap, Skill, Runner, Job, frontend, User Solve, reverse-solving, packaging, database, cleanup, retention, sample, tool-integration, and historical archive paths are forbidden.

### 6.9 Publication boundary

After all local v9 validation, closeout, archive, context/state synchronization, and seal evidence converge truthfully:

1. stage only explicit allowed paths;
2. create one final v9 validation commit on the existing branch;
3. push it to the existing branch;
4. stop all branch mutation;
5. observe CI, State Gate, and Decision Preflight for that exact commit;
6. perform independent external audit from GitHub observations;
7. do not commit a remote receipt or rewrite reports after remote checks.

The v9 Decision commit may trigger intermediate failing workflows before implementation. Those runs are not final acceptance evidence.

## 7. Tests

The locked command-plan must authorize platform-appropriate equivalents of the following local commands and no broader Git operations:

```text
Set-Location F:\reverse-agent
Get-Location
Test-Path F:\reverse-agent
git rev-parse --show-toplevel
git status --short
git log --oneline --decorate -n 12

git fetch origin agent/terminal-status-propagation-seal-restart-rework-v3

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
python -m reverse_agent.project_gate run-closeout --state-dir project_state --round-id round_20260720_ci_consumed_decision_preflight_parity_rework_v9
python -m reverse_agent.project_gate close-round --state-dir project_state --round-id round_20260720_ci_consumed_decision_preflight_parity_rework_v9
python -m reverse_agent.project_gate post-final-evidence-sync --state-dir project_state
python -m reverse_agent.project_gate final-check --state-dir project_state
python -m reverse_agent.project_gate final-evidence-seal --state-dir project_state --round-id round_20260720_ci_consumed_decision_preflight_parity_rework_v9

git diff --check
git status --short
```

The same locked command-plan must authorize as CI-only commands every executable command in:

```text
.github/workflows/ci.yml
.github/workflows/state-gate.yml
.github/workflows/decision-preflight.yml
```

For both State Gate and Decision Preflight, the exact authorized preflight command must be:

```text
python -m reverse_agent.project_gate preflight --state-dir project_state --allow-consumed
```

Local pre-attestation completion requires:

```text
decision-lint = PASSED
strict startup preflight = PASSED before the Decision is consumed
command-plan = current and locked before workflow edits
new v9 execution segment = current
focused tests = PASSED
related regression tests = PASSED
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
PR #5 head SHA = exact final v9 validation commit
CI = completed/success for exact final v9 head
State Gate = completed/success for exact final v9 head
Decision Preflight = completed/success for exact final v9 head
no later branch commit
PR #6 remains unchanged and inactive
external audit conclusion is supported by exact-head observations
```

## 8. Stop Conditions

Stop with `BLOCKED` or `REWORK_REQUIRED`, as applicable, if any of the following occurs:

- the local branch cannot fast-forward to the current remote PR #5 branch without merge or rebase;
- PR #5 is no longer open, Draft, unmerged, or targeting `main`;
- the v9 Decision commit is not an ancestor of implementation or final commits;
- v9 Decision content or command-plan cannot be locked before substantive execution;
- the command-plan cannot authorize the target `--allow-consumed` workflow commands before workflow edits;
- workflow files are edited before target command authorization exists;
- strict local preflight is weakened or begins accepting consumed Decisions by default;
- `--allow-consumed` bypasses any check other than `decision_not_consumed_by_report`;
- wrong Decision, wrong Round, failed report, unapproved Decision, inactive Skill, invalid branch, invalid ancestry, forbidden path, capability violation, or command-plan conflict passes consumed validation;
- `.github/workflows/ci.yml` must be modified to continue;
- `local-ci-parity` fails after the authorized repair;
- focused or regression tests fail and repair requires an out-of-scope path;
- v4-v8 archived or sealed artifacts change;
- PR #6 changes, merges, or becomes active;
- a new branch or PR is required;
- merge, rebase, force-push, direct-main push, `git add -A`, deletion, or destructive cleanup is required;
- local report, pytest, execution-log, final-check, closeout, archive, context, state manifest, or seal cannot converge on v9 IDs and `PENDING_EXTERNAL`;
- any branch commit appears after the final v9 validation commit while remote attestation is being observed;
- CI, State Gate, or Decision Preflight fails for the exact final v9 head;
- exact-head GitHub evidence is unavailable or cannot be bound to the final PR head.

Complete this Decision and stop. Do not activate or execute the queued mature-framework plan in PR #6.
