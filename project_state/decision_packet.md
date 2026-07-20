```json decision_meta
{
  "schema_version": 1,
  "decision_id": "decision_20260720_ci_preflight_bootstrap_order_rework_v10",
  "round_id": "round_20260720_ci_preflight_bootstrap_order_rework_v10",
  "based_on_state_build_id": "state_20260618_134029_d6bd033d2532",
  "based_on_state_digest": "d6bd033d25324345cfd8ada0ac65db42bc86eb5017f3ffc92906fcd8b71cacb5",
  "status": "APPROVED",
  "mainline": "engineering_branch",
  "skill_profiles": ["reverse-agent-iteration@v2"]
}
```

```json decision_contract
{
  "follows_last_decision_id": "decision_20260720_ci_consumed_decision_preflight_parity_rework_v9",
  "follows_last_round_id": "round_20260720_ci_consumed_decision_preflight_parity_rework_v9",
  "previous_round_outcome": "BLOCKED",
  "previous_blocker": "bootstrap_deadlock_between_final_command_plan_lock_and_future_ci_command_authorization",
  "restart_mode": "explicit_new_round_after_bootstrap_deadlock",
  "restart_authorized_by_user": true,
  "previous_round_artifacts_read_only": true,
  "required_profile": "full",
  "execution_branch": "agent/terminal-status-propagation-seal-restart-rework-v3",
  "base_branch": "main",
  "reuse_existing_draft_pr_number": 5,
  "previous_decision_only_head_sha": "9cc17eccd0a0c7944d0261b80b1e07967afe9462",
  "decision_commit_must_precede_implementation": true,
  "decision_content_digest_lock_required": true,
  "new_execution_segment_required": true,
  "bootstrap_preplan_window_required": true,
  "bootstrap_preplan_window_is_single_use": true,
  "bootstrap_preplan_allowed_paths": [
    ".github/workflows/state-gate.yml",
    ".github/workflows/decision-preflight.yml"
  ],
  "bootstrap_preplan_allowed_change": "append --allow-consumed to the existing Project gate preflight command in exactly two workflow files",
  "bootstrap_preplan_source_changes_allowed": false,
  "bootstrap_preplan_test_changes_allowed": false,
  "bootstrap_preplan_state_artifact_changes_allowed": false,
  "bootstrap_preplan_commit_allowed": false,
  "bootstrap_preplan_push_allowed": false,
  "bootstrap_preplan_generator_change_allowed": false,
  "bootstrap_preplan_manual_plan_fabrication_allowed": false,
  "bootstrap_preplan_only_executable_exception": "python -m reverse_agent.project_gate command-plan --state-dir project_state with optional --json",
  "final_command_plan_generated_from_bootstrap_edited_workflows": true,
  "final_command_plan_digest_lock_required": true,
  "final_command_plan_must_precede_source_test_state_and_report_changes": true,
  "bootstrap_failure_requires_workflow_revert_and_blocked_stop": true,
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

Resolve the v9 bootstrap deadlock and then complete the already-selected consumed-Decision CI preflight repair.

The v9 deadlock was:

```text
final command-plan must be locked before workflow changes
        +
current command-plan generator derives ci_commands from current workflows
        +
target workflows do not yet contain --allow-consumed
        =
no legal way to pre-authorize the target CI-only command
```

v10 introduces one explicit, single-use, fail-closed bootstrap window:

```text
commit and lock v10 Decision
        ↓
make exactly two uncommitted workflow-line edits
        ↓
immediately generate the canonical command-plan from those edited workflows
        ↓
verify and lock the final command-plan
        ↓
create the v10 execution segment
        ↓
only then permit tests, source changes if proven necessary, state/report generation, closeout, commit, and push
```

The bootstrap window exists only to let the existing generator observe the exact future CI-only commands. It is not a general exception to command authority and must not be reused by later rounds without a new Decision.

The final functional target remains:

1. local execution-start preflight remains strict and blocks a Decision already consumed by a successful current-round report;
2. State Gate and Decision Preflight use explicit `--allow-consumed` when validating an immutable final commit that necessarily contains its successful report;
3. `--allow-consumed` relaxes only `decision_not_consumed_by_report` and does not bypass Decision ID, round ID, status, skill, branch, ancestry, scope, report identity, command-plan, or artifact-currentness checks;
4. the locked command-plan contains the exact updated CI-only commands and passes local-CI parity;
5. CI, State Gate, and Decision Preflight all complete successfully for one immutable final v10 head;
6. external audit decides the final acceptance without a post-attestation repository commit.

Reuse the existing preflight, command-plan, workflow parser, local-CI parity, execution-log, report-summary, final-check, closeout, archive, context, state-manifest, final-seal, CI observation, and external-attestation foundations. Do not recreate them.

## 2. Current Evidence

- After this Decision commit, `project_state/decision_packet.md` is the sole current task authority. `project_state/task_packet.json` remains background-only and cannot control execution.
- Current mainline is `engineering_branch`. This is a bounded CI/control-plane sequencing repair, not project-governance roadmap work, reverse-solving, tool integration, training-dataset work, Web work, Runner work, User Solve work, database work, or framework adoption work.
- Draft PR #5 is open, unmerged, mergeable, targets `main`, and uses branch `agent/terminal-status-propagation-seal-restart-rework-v3`.
- v8 exact final head `38ac23d59119973d6154e49c26fde272bbc81298` produced:
  - CI: `completed/success`;
  - State Gate: `completed/failure` at `Project gate preflight`;
  - Decision Preflight: `completed/failure` at `Project gate preflight`.
- The exact v8 remote blocker was `decision_not_consumed_by_report` with `decision_execution_state = CONSUMED_BY_SUCCESS_REPORT`.
- v8 local implementation, pytest, report-summary, execution-log, final-check, run-closeout, close-round, context, state manifest, round archive, and final seal converged locally. Those capabilities are not reopened except where v10 must generate new current-round artifacts.
- v9 Decision commit is `9cc17eccd0a0c7944d0261b80b1e07967afe9462`.
- Codex correctly stopped v9 without file changes, commits, pushes, reverse probes, or scope expansion because v9 required the final locked command-plan to contain commands that the existing generator could only discover after the forbidden workflow edits.
- The current command-plan generator reads executable commands from current workflow files when constructing `ci_commands`.
- The two current workflow preflight commands still omit `--allow-consumed`.
- Therefore a final plan generated before either workflow edit cannot contain the target commands, while a workflow edit before the v9 final-plan lock was forbidden.
- v10 resolves only this sequencing contradiction. It does not authorize a manual plan, an invented CI command, an unlocked implementation phase, or a general weakening of command authority.
- The bootstrap mutation is limited to two exact workflow command lines and remains uncommitted until the canonical command-plan is generated, verified, and locked.
- The only executable operation allowed before the canonical plan lock is the existing command-plan generation meta-operation, with optional JSON rendering. This exception is necessary to create the authority artifact itself and must not be broadened.
- If the current generator does not emit both updated exact commands after the two uncommitted edits, Codex must revert those edits and stop `BLOCKED`; it may not modify the generator, fabricate a plan, or continue.
- Current `state_manifest.json` exists and identifies current Decision, command-plan, execution-log, report, final-check, and pytest roles. Missing historical sample artifacts are nonblocking for this engineering round.
- Current context packet exists. It must be refreshed only after the v10 final local gate, not used to override newer live artifacts.
- Workstream registry exists. Roadmap entries are not execution authority and must not be modified in this round.
- `negative_results.json` contains historical reverse-solving constraints. This round does not enter reverse solving and must not repeat those directions.
- Existing active skill `reverse-agent-iteration@v2` is valid for this generic engineering workflow.
- Existing capabilities already include Decision locking, branch-bound command-plan generation, CI-only command surfaces, local-CI parity, execution segments, execution-log synthesis, report-summary synthesis, final-check, run-closeout, close-round, round archive, context packet, state manifest, final evidence seal, GitHub CI, State Gate, Decision Preflight, and CI observation artifacts.
- This round must strengthen composition and sequencing only; it must not reimplement command-plan, report-summary, execution-log, closeout, policy-lint, prompt-consistency, CI observation, or final-seal systems.
- Allowed tools are deterministic local Python, focused pytest, Git inspection, YAML inspection, existing project-gate commands, and read-only exact-head GitHub workflow observation after publication.
- Reverse tools, debuggers, emulators, model APIs, Runner dispatch, Web runtime, databases, cleanup apply, destructive operations, full historical artifact scans, and external binary execution are forbidden.
- Heavy artifacts and full `solve_reports/` are not allowed.
- Closeout is allowed only after the canonical v10 plan is locked, the v10 execution segment exists, local-CI parity passes, focused tests pass, and all v10 report/evidence artifacts are current.
- PR #6 remains `QUEUED_NOT_ACTIVE`. It is not current authority and cannot be modified, merged, activated, or executed in this round.
- This round does not duplicate an existing feature. It addresses a newly observed bootstrap ordering defect between existing command-plan generation and workflow authorization.

## 3. Do Not Do

Do not:

- work on `main`, create another branch, or open another PR;
- merge PR #5 or mark it ready for review during implementation;
- rebase, force-push, amend published history, delete branches, tag, or push directly to `main`;
- use `git add -A` or stage files outside the explicit allowlist;
- edit v4-v9 archived or sealed artifacts to make historical rounds pass;
- reuse v8 or v9 IDs, locks, command-plan digest, restart identity, report, pytest, context, manifest, archive, seal, or acceptance claims as v10 evidence;
- treat v9 as implemented; it ended `BLOCKED` without substantive work;
- modify `reverse_agent/project_gate.py`, tests, project-state artifacts, reports, context, manifests, or archives before the canonical v10 command-plan is generated and locked;
- modify any file during the bootstrap window except the two exact workflow files;
- modify any line in those workflow files during the bootstrap window except the existing `Project gate preflight` command lines;
- add, remove, rename, reorder, skip, or weaken workflow steps during the bootstrap window;
- commit or push the bootstrap-only workflow edits before the final command-plan is verified and locked;
- manually edit or fabricate `project_state/gates/command_plan.json`;
- modify the command-plan generator during the bootstrap window;
- create a separate unofficial bootstrap plan or use another path as command authority;
- use workflow YAML as implicit command authority after the final plan exists;
- leave the two workflow edits in place if canonical plan generation fails or omits either target command;
- run arbitrary shell, Python, pytest, Git mutation, workflow, report, closeout, or state-generation commands before the final plan lock;
- interpret the command-plan generation bootstrap exception as permission for any other command;
- delete `decision_not_consumed_by_report` or make `--allow-consumed` the default;
- let `--allow-consumed` bypass wrong Decision, wrong round, wrong report, failed report, non-APPROVED Decision, inactive skill, wrong branch, missing ancestry, forbidden path, stale artifact, or command-plan checks;
- modify `.github/workflows/ci.yml`;
- skip `report-summary`, `local-ci-parity`, tests, final-check, closeout, archive, context/state synchronization, or final seal to make remote checks green;
- claim remote `PASS` before exact-head GitHub checks are terminal and successful;
- commit a remote receipt or rewrite reports after the final validation commit;
- modify or activate PR #6;
- install BMAD, LangGraph, Microsoft Agent Framework, MetaGPT, ChatDev, or any new dependency;
- modify roadmap, workstreams, Skills, prompts, Runner, Job orchestration, frontend, User Solve, reverse-solving, sample solvers, harnesses, tool adapters, packaging, database, cleanup, retention, or state-domain architecture;
- run reverse tools, debuggers, emulators, unknown binaries, model APIs, network probes, or destructive operations;
- read complete `solve_reports/` or `PROJECT_PROGRESS_LOG.txt`.

## 4. Files To Inspect

Required current authority and state:

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
.codex-skills/registry.json
```

Required current gate evidence:

```text
project_state/gates/command_plan.json
project_state/gates/command_plan_lock.json
project_state/gates/decision_content_lock.json
project_state/gates/restart_segment.json
project_state/gates/preflight_result.json
project_state/gates/execution_log.json
project_state/gates/report_summary_synthesis.json
project_state/gates/final_gate_result.json
project_state/gates/run_closeout_result.json
project_state/gates/final_evidence_seal.json
project_state/gates/local_ci_parity_result.json
project_state/gates/ci_workflow_readiness_result.json
project_state/gates/ci_run_evidence_result.json
project_state/gates/ci_observation_reconcile_result.json
```

Required engineering files:

```text
.github/workflows/ci.yml
.github/workflows/state-gate.yml
.github/workflows/decision-preflight.yml
reverse_agent/project_gate.py
reverse_agent/decision_preflight.py
tests/test_project_gate.py
tests/test_project_reports.py
tests/test_decision_preflight.py
tests/test_post_final_evidence_sync.py
tests/test_project_state.py
tests/test_project_jobs.py
```

Required read-only prior-round evidence:

```text
project_state/rounds/round_20260719_remote_attestation_truth_and_ci_command_parity_rework_v8/*
project_state/decision_packet.md at commit 9cc17eccd0a0c7944d0261b80b1e07967afe9462
```

Required external observations:

```text
PR #5 metadata and current head
v8 final head 38ac23d59119973d6154e49c26fde272bbc81298
v8 CI run 29697859077
v8 State Gate run 29697859062
v8 Decision Preflight run 29697859089
v9 Decision-only head 9cc17eccd0a0c7944d0261b80b1e07967afe9462
final v10 exact-head CI, State Gate, and Decision Preflight runs
```

Do not inspect unrelated source trees unless an authorized focused test identifies a concrete in-scope dependency after the final command-plan lock.

## 5. Required Audit

The final v10 report must answer every item separately with a concrete artifact path or GitHub observation, value, status, and conclusion:

1. Is execution still on `agent/terminal-status-propagation-seal-restart-rework-v3` and Draft PR #5 targeting `main`?
2. Is v10 `APPROVED`, `engineering_branch`, and bound to active `reverse-agent-iteration@v2`?
3. Is the committed v10 Decision the sole current authority, with `task_packet.json` background-only?
4. Is the v10 Decision commit an ancestor of every v10 implementation, evidence, and final publication commit?
5. Are v4-v9 archived or previously published artifacts unchanged?
6. Does the report record that v9 ended `BLOCKED` without substantive changes, commits, or pushes?
7. Was v10 Decision content locked before the bootstrap mutation window opened?
8. Were pre-bootstrap hashes or exact contents captured for both workflow files?
9. During the bootstrap window, were only the two authorized workflow files modified?
10. In each workflow, was only the existing `Project gate preflight` command changed?
11. Was the only textual change the addition of `--allow-consumed`?
12. Were no source, test, state, report, context, manifest, archive, or other workflow files modified before final plan lock?
13. Were the bootstrap edits uncommitted and unpushed until the final command-plan was verified and locked?
14. Was canonical command-plan generation the only executable pre-plan exception used?
15. Did the generated command-plan include the exact updated State Gate command with workflow path and CI-only execution surface?
16. Did it include the exact updated Decision Preflight command with workflow path and CI-only execution surface?
17. For both commands, is local transcript not required and exact remote execution evidence required?
18. Was the canonical command-plan digest locked before source, test, state, report, context, manifest, archive, or additional workflow work?
19. Does a new v10 execution segment exist with v10 IDs, Decision digest, plan digest, startup time, and unique restart identity?
20. Does local strict preflight without `--allow-consumed` still block a current Decision consumed by a successful current-round report?
21. Does workflow validation with `--allow-consumed` pass only for a valid consumed current Decision?
22. Does wrong Decision ID still fail under `--allow-consumed`?
23. Does wrong round ID still fail under `--allow-consumed`?
24. Does a failed or non-success report still fail under `--allow-consumed`?
25. Does a non-APPROVED Decision or inactive skill still fail?
26. Do wrong branch, missing Decision ancestry, forbidden path, stale evidence, and command-plan mismatch still fail?
27. Is `.github/workflows/ci.yml` unchanged?
28. Does `local-ci-parity` pass for all three workflows with zero required gaps?
29. Are CI-only commands absent from the local transcript while still represented by exact workflow authority?
30. Did focused tests cover bootstrap order, strict-versus-consumed preflight, wrong identities, failed reports, workflow parity, and immutable-head evidence?
31. Does `pytest_result.txt` contain real commands, outputs, exit codes, and passing totals consistent with the report?
32. Do report-summary and execution-log pass with v10 IDs and truthful chronology?
33. Does final-check pass?
34. Does run-closeout pass and close-round produce `CLOSED`?
35. Are context, state manifest, round manifest, archived report, archived pytest, and final seal current and mutually consistent?
36. Are all changed files inside the v10 allowlist?
37. Were merge, rebase, force-push, direct-main push, branch creation, new PR creation, and `git add -A` avoided?
38. Is PR #6 still untouched and `QUEUED_NOT_ACTIVE`?
39. Is the final v10 validation commit the exact PR #5 head with no later branch commit?
40. Did CI complete successfully for the exact final v10 head?
41. Did State Gate complete successfully for the exact final v10 head?
42. Did Decision Preflight complete successfully for the exact final v10 head?
43. Were exact-head remote results observed externally without a post-attestation commit?
44. Do the exact-head results support one of the four allowed final audit conclusions?

## 6. Implementation Scope

### 6.1 Authority, synchronization, and Decision lock

1. Work only in `F:\reverse-agent` on branch `agent/terminal-status-propagation-seal-restart-rework-v3`.
2. Synchronize by fast-forward only. Do not merge or rebase.
3. Verify PR #5 remains open, Draft, unmerged, and targets `main`.
4. Verify the local branch contains the committed v10 Decision and that the working tree has no unexpected changes.
5. Treat this v10 Decision as the sole authority.
6. Lock the v10 Decision content before any bootstrap edit.
7. Record the v10 Decision commit SHA, Decision digest, current branch, and exact pre-bootstrap hashes or contents of:
   - `.github/workflows/state-gate.yml`;
   - `.github/workflows/decision-preflight.yml`.

### 6.2 Single-use pre-plan bootstrap window

After the v10 Decision is locked, open one single-use bootstrap window.

During this window, make exactly these two uncommitted edits:

```yaml
# .github/workflows/state-gate.yml
- run: python -m reverse_agent.project_gate preflight --state-dir project_state
+ run: python -m reverse_agent.project_gate preflight --state-dir project_state --allow-consumed
```

```yaml
# .github/workflows/decision-preflight.yml
- run: python -m reverse_agent.project_gate preflight --state-dir project_state
+ run: python -m reverse_agent.project_gate preflight --state-dir project_state --allow-consumed
```

No other line, spacing, step name, trigger, permission, checkout setting, command, test list, or artifact upload configuration may change in the bootstrap window.

The workflow edits must remain uncommitted and unpushed.

The only executable bootstrap exception is canonical plan generation:

```text
python -m reverse_agent.project_gate command-plan --state-dir project_state
python -m reverse_agent.project_gate command-plan --state-dir project_state --json
```

Use only the minimum invocation(s) required by the existing control plane. Do not run pytest, arbitrary Python, Git mutation, report, closeout, state generation, or other gate commands before final plan lock.

The generated canonical plan must contain both exact updated commands, bound to the correct workflow paths, marked CI-only, with local transcript not required and remote evidence required.

If either command is absent, altered, mapped to the wrong workflow, treated as a local command, or otherwise not exactly authorized:

1. revert the two uncommitted workflow edits to their pre-bootstrap contents;
2. preserve the v10 Decision commit;
3. write no fabricated plan or evidence;
4. stop `BLOCKED`.

Do not modify the generator to escape this stop condition.

### 6.3 Final plan lock and execution segment

After canonical plan generation succeeds:

1. validate the plan IDs, branch binding, Decision digest, Decision commit, workflow paths, exact commands, execution surfaces, evidence requirements, and omitted commands;
2. lock the final canonical command-plan digest;
3. verify the two workflow edits still exactly match the locked plan;
4. create a new v10 execution segment with a unique restart identity;
5. only after these steps may normal source, test, state, report, context, manifest, archive, and final-seal work begin.

The locked command-plan is then the sole command authority for the remainder of v10.

### 6.4 Functional validation and minimal implementation

The preferred implementation is workflow-only if the existing `--allow-consumed` behavior already satisfies the security boundary.

After final plan lock, inspect and test the current implementation.

Required semantics:

```text
strict local preflight + current successful consumed report
→ BLOCKED by decision_not_consumed_by_report

preflight --allow-consumed + valid current successful consumed report
→ PASSED, subject to every other gate

preflight --allow-consumed + wrong Decision
→ BLOCKED

preflight --allow-consumed + wrong round
→ BLOCKED

preflight --allow-consumed + failed/non-success report
→ BLOCKED

preflight --allow-consumed + non-APPROVED Decision
→ BLOCKED

preflight --allow-consumed + inactive skill
→ BLOCKED

preflight --allow-consumed + wrong branch or missing Decision ancestry
→ BLOCKED

preflight --allow-consumed + forbidden scope, stale artifact, or command-plan mismatch
→ BLOCKED
```

Modify `reverse_agent/project_gate.py` or `reverse_agent/decision_preflight.py` only if a focused authorized test proves that the current implementation violates one of these exact semantics. Do not redesign preflight generally.

Modify tests only to cover the v10 bootstrap order and the exact strict-versus-consumed security boundary. Reuse existing test helpers and fixtures.

### 6.5 CI command parity

Run the existing workflow coverage/readiness/parity gates after final plan lock.

Requirements:

- `.github/workflows/ci.yml` remains byte-for-byte unchanged;
- both updated preflight commands exactly match entries in the locked plan;
- every other executable command in all three workflows remains authorized or explicitly classified as accepted setup;
- CI-only commands are not fabricated into local execution history;
- remote execution evidence remains required for the exact final head;
- zero required parity gaps remain.

### 6.6 Reports, state, and closeout

After implementation and tests pass:

1. generate truthful v10 pytest evidence;
2. synthesize report-summary and execution-log;
3. answer all Required Audit items with concrete evidence;
4. run final-check;
5. run run-closeout and close-round;
6. refresh context only after the current final gate;
7. refresh state manifest and v10 round manifest;
8. archive only the current v10 round artifacts;
9. run post-final evidence sync as required;
10. run final-check again if the normal closeout sequence requires it;
11. create the v10 final evidence seal;
12. keep remote items `PENDING_EXTERNAL` before exact-head workflow results exist.

### 6.7 Allowed paths

Bootstrap-window writable paths only:

```text
.github/workflows/state-gate.yml
.github/workflows/decision-preflight.yml
```

After final command-plan lock, the complete v10 allowlist is:

```text
.github/workflows/state-gate.yml
.github/workflows/decision-preflight.yml
reverse_agent/project_gate.py
reverse_agent/decision_preflight.py
tests/test_project_gate.py
tests/test_project_reports.py
tests/test_decision_preflight.py
project_state/state_manifest.json
project_state/context/current_context_packet.json
project_state/gates/*.json
project_state/pytest_result.txt
project_state/codex_execution_report.md
project_state/execution_report.md
project_state/rounds/round_20260720_ci_preflight_bootstrap_order_rework_v10/*
```

`reverse_agent/project_gate.py`, `reverse_agent/decision_preflight.py`, and tests may change only after final plan lock and only when focused evidence proves a required minimal correction or regression test is necessary.

All other source, workflow, test, project-state, roadmap, Skills, prompts, Runner, Job, frontend, User Solve, reverse-solving, packaging, database, cleanup, retention, sample, tool-integration, and historical archive paths are forbidden.

### 6.8 Publication boundary

After local v10 evidence converges truthfully:

1. stage only explicit allowed paths;
2. create one final v10 validation commit on the existing branch;
3. push it to the existing branch;
4. stop all branch mutation;
5. observe CI, State Gate, and Decision Preflight for that exact commit;
6. perform external audit from exact-head GitHub observations;
7. do not commit a remote receipt, amend history, or rewrite the report after remote checks.

The v10 Decision commit and any intermediate Decision-only workflows are not final acceptance evidence.

## 7. Tests

### 7.1 Read-only startup checks

Use the platform-appropriate equivalents authorized by the control plane:

```text
Set-Location F:\reverse-agent
Get-Location
Test-Path F:\reverse-agent
git rev-parse --show-toplevel
git status --short
git log --oneline --decorate -n 12
```

Verify branch and remote state without merge or rebase.

### 7.2 Pre-plan bootstrap verification

Before bootstrap edits, record exact workflow contents or digests.

After the exact two uncommitted edits, use only canonical command-plan generation:

```text
python -m reverse_agent.project_gate command-plan --state-dir project_state
python -m reverse_agent.project_gate command-plan --state-dir project_state --json
```

The second invocation is required only if the existing lock/inspection process needs JSON output; do not duplicate commands merely to create volume.

Before locking, verify the generated plan contains exactly:

```text
python -m reverse_agent.project_gate preflight --state-dir project_state --allow-consumed
```

for both:

```text
.github/workflows/state-gate.yml
.github/workflows/decision-preflight.yml
```

with:

```text
execution_surface = ci_only
local_transcript_required = false
remote_execution_evidence_required = true
```

### 7.3 Post-lock governance checks

After the canonical plan is locked and the v10 execution segment exists, run only plan-authorized equivalents of:

```text
python -m reverse_agent.project_gate decision-lint --state-dir project_state
python -m reverse_agent.project_gate preflight --state-dir project_state
python -m reverse_agent.project_gate gate-profile --state-dir project_state --profile full
python -m reverse_agent.project_gate command-plan --state-dir project_state
python -m reverse_agent.project_gate command-plan --state-dir project_state --json
python -m reverse_agent.project_gate ci-workflow-coverage --state-dir project_state
python -m reverse_agent.project_gate ci-workflow-readiness --state-dir project_state
python -m reverse_agent.project_gate local-ci-parity --state-dir project_state
```

The strict local preflight invocation must remain without `--allow-consumed`.

### 7.4 Focused tests

Run plan-authorized equivalents of:

```text
python -m pytest tests/test_project_gate.py tests/test_project_reports.py tests/test_decision_preflight.py -q
```

Focused tests must cover:

- the bootstrap ordering contract;
- exact two-file workflow mutation;
- plan generation from edited workflow commands;
- plan lock preceding source/test/state/report mutation;
- strict preflight blocking a consumed Decision;
- `--allow-consumed` passing only the valid consumed current Decision case;
- wrong Decision, wrong round, failed report, non-APPROVED Decision, inactive skill, wrong branch, missing ancestry, forbidden scope, stale evidence, and plan mismatch failures;
- `.github/workflows/ci.yml` remaining unchanged;
- workflow command parity with zero required gaps.

### 7.5 Related regression

Run plan-authorized equivalents of:

```text
python -m pytest tests/test_project_gate.py tests/test_project_reports.py tests/test_decision_preflight.py tests/test_post_final_evidence_sync.py tests/test_project_state.py tests/test_project_jobs.py -q
```

Existing detached-HEAD, full-history ancestry, PENDING_EXTERNAL, execution segment, final-seal logging, report truth, context freshness, and closeout tests must remain green.

### 7.6 Final evidence sequence

Run only locked-plan-authorized equivalents of:

```text
python -m reverse_agent.project_gate report-summary --state-dir project_state
python -m reverse_agent.project_gate execution-log --state-dir project_state
python -m reverse_agent.project_gate audit-readiness-packet --state-dir project_state
python -m reverse_agent.project_gate current-handoff-packet --state-dir project_state
python -m reverse_agent.project_gate final-check --state-dir project_state
python -m reverse_agent.project_gate run-closeout --state-dir project_state --round-id round_20260720_ci_preflight_bootstrap_order_rework_v10
python -m reverse_agent.project_gate close-round --state-dir project_state --round-id round_20260720_ci_preflight_bootstrap_order_rework_v10
python -m reverse_agent.project_gate post-final-evidence-sync --state-dir project_state
python -m reverse_agent.project_gate final-check --state-dir project_state
python -m reverse_agent.project_gate final-evidence-seal --state-dir project_state --round-id round_20260720_ci_preflight_bootstrap_order_rework_v10
git diff --check
git status --short
```

Write real command output and exit codes to `project_state/pytest_result.txt` and the execution log. Do not claim commands that were not executed.

### 7.7 External acceptance

After one final validation commit is pushed, external audit requires:

```text
PR head SHA = exact final v10 validation commit
CI = completed/success for exact final v10 head
State Gate = completed/success for exact final v10 head
Decision Preflight = completed/success for exact final v10 head
no later branch commit
no post-attestation repository mutation
```

Before those observations exist, remote Required Audit items remain `PENDING_EXTERNAL`.

## 8. Stop Conditions

Stop immediately with `BLOCKED` if any of the following occurs:

- the local branch cannot fast-forward to the remote PR #5 branch without merge or rebase;
- PR #5 is closed, merged, no longer Draft, no longer targets `main`, or uses another branch;
- the v10 Decision is not the branch-local `project_state/decision_packet.md` authority;
- Decision lint fails, the skill is inactive, or Decision ID/round/mainline is invalid;
- v10 Decision content cannot be locked before bootstrap edits;
- unexpected local changes exist and cannot be classified without touching them;
- a pre-bootstrap workflow hash or exact-content snapshot cannot be recorded;
- the bootstrap mutation requires changing any file other than the two allowed workflows;
- any workflow line other than the existing `Project gate preflight` run line changes during bootstrap;
- either target command differs from the exact required `--allow-consumed` form;
- any source, test, state, report, context, manifest, archive, or other workflow file changes before final plan lock;
- any bootstrap workflow edit is committed or pushed before final plan lock;
- any executable command other than the canonical command-plan generation meta-operation is required before final plan lock;
- the current generator cannot emit both exact target CI-only commands from the uncommitted workflow edits;
- generated plan entries have wrong workflow paths, execution surfaces, evidence requirements, Decision IDs, round IDs, branch binding, digest, or command strings;
- final command-plan cannot be locked after successful generation;
- either bootstrap workflow edit no longer matches the locked plan;
- resolving plan generation would require modifying the generator before plan lock, manually fabricating a plan, or weakening command authority;
- bootstrap failure occurs and the two workflow files cannot be restored exactly to their pre-bootstrap contents;
- a unique v10 execution segment cannot be created after final plan lock;
- `--allow-consumed` changes strict local preflight default behavior;
- `--allow-consumed` permits wrong Decision, wrong round, failed report, unapproved Decision, inactive skill, wrong branch, missing ancestry, forbidden path, stale evidence, or command-plan mismatch;
- `.github/workflows/ci.yml` must change;
- local-CI parity has any required gap;
- tests fail and repair requires leaving the allowlist or expanding the mainline;
- report, execution-log, pytest, final-check, context, state manifest, round manifest, closeout, archive, or seal cannot converge on v10 IDs and truthful `PENDING_EXTERNAL` status;
- v4-v9 archived or sealed evidence changes;
- PR #6 is modified, merged, activated, or executed;
- any merge, rebase, force-push, direct-main push, new branch, new PR, `git add -A`, destructive action, model call, Runner dispatch, reverse-tool execution, or unrelated scope is required;
- a branch commit is created after the final validation commit while exact-head checks are being observed;
- CI, State Gate, or Decision Preflight fails for the exact final v10 head;
- GitHub cannot provide terminal exact-head evidence for all three required workflows.

On a bootstrap stop condition, restore only the two uncommitted workflow edits to the recorded pre-bootstrap contents, preserve the v10 Decision commit, write no false success evidence, and stop. Do not continue to another task or activate PR #6.
