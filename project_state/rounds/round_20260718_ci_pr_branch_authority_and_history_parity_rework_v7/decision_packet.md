```json decision_meta
{
  "schema_version": 1,
  "decision_id": "decision_20260718_ci_pr_branch_authority_and_history_parity_rework_v7",
  "round_id": "round_20260718_ci_pr_branch_authority_and_history_parity_rework_v7",
  "based_on_state_build_id": "state_20260618_134029_d6bd033d2532",
  "based_on_state_digest": "d6bd033d25324345cfd8ada0ac65db42bc86eb5017f3ffc92906fcd8b71cacb5",
  "status": "APPROVED",
  "mainline": "engineering_branch",
  "skill_profiles": ["reverse-agent-iteration@v2"]
}
```

```json decision_contract
{
  "follows_last_decision_id": "decision_20260717_ci_state_hygiene_and_preflight_parity_rework_v6",
  "follows_last_round_id": "round_20260717_ci_state_hygiene_and_preflight_parity_rework_v6",
  "previous_audit_outcome": "REWORK_REQUIRED",
  "restart_mode": "explicit_new_round_after_remote_stop_condition",
  "restart_authorized_by_user": true,
  "previous_round_artifacts_read_only": true,
  "required_profile": "full",
  "execution_branch": "agent/terminal-status-propagation-seal-restart-rework-v3",
  "base_branch": "main",
  "reuse_existing_draft_pr_number": 5,
  "previous_final_head_sha": "442a318b93ecab5a98f40fe20a88da046961ce02",
  "previous_decision_commit_sha": "6505a88df9ffc9b4ae48b8a50c28c180dc98acbb",
  "decision_commit_must_precede_implementation": true,
  "decision_content_digest_lock_required": true,
  "command_plan_branch_binding_required": true,
  "command_plan_digest_lock_required": true,
  "final_command_plan_precedes_substantive_execution": true,
  "external_remote_attestation_required": true,
  "remote_green_required_for_acceptance": true,
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

Repair the GitHub Actions parity defect that caused the v6 final commit to pass local validation and CI but fail both State Gate and Decision Preflight at the first `Project gate preflight` step.

The round has only two engineering targets:

1. make branch-local execution authority resolve the real PR head branch when GitHub Actions checks out a detached synthetic merge ref;
2. make the Decision-commit ancestry check operate with sufficient Git history, without bypassing or weakening the ancestry requirement.

Reuse all existing v6 packaging, command-plan, execution-log, report-summary, closeout, archive, context, manifest, seal, CI, State Gate, and Decision Preflight foundations. Do not redesign them.

The decision commit for this v7 round must precede implementation. After the implementation and all local evidence converge, create one final validation commit `S3`, push it to the same branch, stop branch mutation, and externally observe CI, State Gate, and Decision Preflight for exact `S3`.

## 2. Current Evidence

- `project_state/decision_packet.md` is the sole task authority after this v7 Decision is committed. `project_state/task_packet.json` remains background-only sample guidance and does not control this round.
- Current mainline is `engineering_branch`; this is a CI/Git authority-parity repair, not project-governance roadmap work, reverse-solving, tool integration, training-dataset work, Web work, or Runner work.
- Draft PR #5 is open, unmerged, mergeable, targets `main`, and uses branch `agent/terminal-status-propagation-seal-restart-rework-v3`.
- The v6 final PR head is `442a318b93ecab5a98f40fe20a88da046961ce02`.
- GitHub checks for exact v6 head completed as follows:
  - CI: `completed/success`;
  - State Gate: `completed/failure`;
  - Decision Preflight: `completed/failure`.
- Both failed workflows stopped at `Project gate preflight`; installation under Python 3.13 succeeded before that step.
- The State Gate evidence artifact records:
  - `branch_local_execution_authority = FAIL`;
  - `execution_branch = ""`;
  - expected branch = `agent/terminal-status-propagation-seal-restart-rework-v3`;
  - failures = `execution_branch_mismatch` and `decision_commit_not_ancestor`.
- GitHub Actions checked out `refs/remotes/pull/5/merge` in detached HEAD state. The checkout used the default shallow history (`fetch-depth: 1`).
- The current State Gate and Decision Preflight workflow files use `actions/checkout@v4` without an explicit history depth.
- The v6 Decision commit is `6505a88df9ffc9b4ae48b8a50c28c180dc98acbb`. A depth-1 synthetic merge checkout cannot reliably prove that commit is an ancestor even when the branch history is logically valid.
- v6 local evidence is otherwise substantial: the clean editable install/import check passed; the focused suite recorded `1551 passed`; local final-check is `PASSED`; local run-closeout is `PASSED`; the v6 round manifest and final seal exist.
- The v6 execution report nevertheless recommended `ACCEPTED` before required remote checks were available and marked audit items 31-34 `NOT_APPLICABLE`. That recommendation is not sufficient because the v6 Decision explicitly required all three remote workflows to succeed for the exact final commit.
- The v6 Stop Condition was triggered by failed State Gate and Decision Preflight. Therefore the v6 audit outcome is `REWORK_REQUIRED`, not `ACCEPTED`.
- `current_state.json`, `task_packet.json`, and parts of `artifact_index.json` still contain older `samplereverse` facts. They are not current evidence for this engineering round and remain read-only.
- `negative_results.json` is reverse-solving evidence. This round does not repeat any failed solving direction and does not read or commit full `solve_reports/`.
- The context packet and workstream registry exist. Roadmap entries are not execution authority.
- Existing capabilities already include branch-local Decision locking, command-plan authorization, execution-log synthesis, report-summary, final-check, run-closeout, round archive, post-final evidence sync, context packet, state manifest, final evidence seal, GitHub CI, State Gate, and Decision Preflight. This round repairs environment parity only and does not recreate those capabilities.
- Allowed capabilities are local deterministic Python, Git inspection, focused pytest, YAML inspection, a temporary virtual environment outside the repository when needed, read-only GitHub Actions observation, and controlled commit/push to the existing branch.
- Reverse tools, debuggers, emulators, model APIs, Runner dispatch, Web runtime, databases, cleanup apply, destructive operations, and heavy historical artifact reads are not allowed.
- Closeout is allowed only after the v7 command-plan is locked and the branch identity and ancestry tests pass locally.
- Intermediate checks on the v7 Decision commit may still fail before implementation. They are not acceptance evidence. Acceptance is based only on exact final commit `S3`.
- This round does not duplicate prompt consistency, policy lint, report-summary, execution-log, command-plan, final-check, context, state-manifest, archive, seal, or CI mechanisms.

## 3. Do Not Do

Do not:

- work on `main`, create another branch, or open another PR;
- merge PR #5;
- rebase, force-push, amend published history, delete branches, tag, or push directly to `main`;
- use `git add -A` or stage files outside the explicit allowlist;
- edit v4, v5, or v6 archived/sealed artifacts to make historical rounds pass;
- reuse v6 local `PASSED`, `SUCCESS`, `ACCEPTED`, context, manifest, archive, seal, or report claims as v7 acceptance evidence;
- weaken branch-local authority by accepting any detached HEAD, unknown branch, `refs/pull/*`, or arbitrary environment text as a valid execution branch;
- bypass the Decision ancestry check merely because execution occurs in GitHub Actions;
- treat missing Git history as proof of ancestry;
- remove the Decision-commit ancestor requirement;
- globally relax valid-mainline, skill-profile, forbidden-path, command-plan, or capability policy;
- modify `.github/workflows/ci.yml`; CI already succeeds and is not the failing surface;
- change packaging metadata, reverse-solving logic, sample solvers, harnesses, tool adapters, Runner, Job, frontend, User Solve, roadmap, database, cleanup, retention, or state-domain architecture;
- redesign `project_state/` or move/delete existing state files;
- run commands absent from the locked v7 command-plan;
- read full `solve_reports/` or `PROJECT_PROGRESS_LOG.txt`;
- create any commit after final validation commit `S3` while remote attestation is being observed;
- commit a remote-check receipt after `S3`.

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
- `project_state/rounds/round_20260717_ci_state_hygiene_and_preflight_parity_rework_v6/round_manifest.json`
- `.codex-skills/registry.json`

Required engineering files:

- `reverse_agent/project_gate.py`
- `tests/test_project_gate.py`
- `tests/test_decision_preflight.py`
- `.github/workflows/state-gate.yml`
- `.github/workflows/decision-preflight.yml`

Required external observations:

- PR #5 metadata and exact head SHA;
- v6 CI run `29649637009`;
- v6 State Gate run `29649637012`, job `88093625712`, and artifact `8431072331`;
- v6 Decision Preflight run `29649637025`, job `88093625717`;
- final v7 workflow runs and exact `S3` head SHA.

Do not inspect unrelated source trees unless an authorized focused test identifies a concrete in-scope dependency.

## 5. Required Audit

The final report must answer each item with artifact path or GitHub observation, concrete value, status, and conclusion:

1. Is execution still on branch `agent/terminal-status-propagation-seal-restart-rework-v3` and Draft PR #5 targeting `main`?
2. Is the v7 Decision `APPROVED`, `engineering_branch`, and bound to active `reverse-agent-iteration@v2`?
3. Is the v7 Decision commit an ancestor of every v7 implementation, evidence, final publication commit, and the GitHub PR merge test commit when full history is available?
4. Are v4-v6 archived/sealed artifacts unchanged?
5. Was the v7 Decision content locked before the final v7 command-plan was generated and locked?
6. Does the final command-plan bind the exact v7 IDs, branch, Decision digest, and Decision commit?
7. Does `_git_current_branch` preserve the normal local symbolic-branch result?
8. In detached HEAD CI, does `GITHUB_HEAD_REF` resolve the PR head branch exactly?
9. Is `GITHUB_REF` used only as a bounded fallback for `refs/heads/<branch>`?
10. Is `refs/pull/5/merge` rejected as an execution branch when `GITHUB_HEAD_REF` is absent?
11. With no trustworthy branch source, does preflight fail closed with an explicit diagnostic?
12. Do State Gate and Decision Preflight checkouts fetch sufficient history to prove Decision ancestry?
13. Is the Decision-commit ancestor check still enforced rather than bypassed?
14. Do tests cover valid local branch, detached PR branch, push branch, malformed refs, missing refs, valid ancestry, and missing-history diagnostics?
15. Are all changed files inside the v7 allowlist?
16. Do focused tests pass and cover every changed test file?
17. Do report-summary, execution-log, pytest metadata, final-check, context, state manifest, round manifest, closeout, and seal agree on v7 IDs and recommendation?
18. Were all commands authorized by the final command-plan and executed in recorded order?
19. Were merge, rebase, force-push, direct-main push, branch creation, and `git add -A` avoided?
20. Is final commit `S3` the PR head with no later branch mutation?
21. Did CI complete successfully for exact `S3`?
22. Did State Gate complete successfully for exact `S3`?
23. Did Decision Preflight complete successfully for exact `S3`?
24. Do exact `S3` remote results support the final recommendation?

## 6. Implementation Scope

### 6.1 Authority and restart

1. Treat this committed v7 Decision as the sole current task authority.
2. Verify the local branch can fast-forward to the remote branch without merge or rebase.
3. Verify PR #5 remains open, Draft, unmerged, and targets `main`.
4. Lock the v7 Decision content.
5. Generate and lock one branch-bound v7 command-plan before substantive source or workflow changes.
6. Record a new v7 execution segment. Do not append v7 evidence to the v6 round.

### 6.2 Branch identity repair

Make the smallest compatible change in `reverse_agent/project_gate.py` so branch resolution follows this precedence:

1. use the normal Git symbolic branch result when it is non-empty and not detached;
2. when detached, use non-empty `GITHUB_HEAD_REF` as the PR head branch;
3. otherwise parse `GITHUB_REF` only when it has the exact form `refs/heads/<branch>`;
4. never treat `refs/pull/<n>/merge`, `refs/pull/<n>/head`, tags, arbitrary strings, or missing values as valid execution branches;
5. preserve fail-closed behavior when no trustworthy branch identity exists.

Do not change the expected branch source: it remains the branch bound in the Decision and command-plan.

### 6.3 Ancestry parity repair

Preserve the existing Decision-commit ancestry requirement.

Make the smallest workflow change needed so GitHub Actions has enough history to evaluate it deterministically:

- configure the Checkout step in `.github/workflows/state-gate.yml` with sufficient history, preferably `fetch-depth: 0`;
- configure the Checkout step in `.github/workflows/decision-preflight.yml` with the same policy;
- do not modify `.github/workflows/ci.yml`;
- do not replace ancestry proof with an environment-only assertion;
- if a narrower explicit fetch is chosen instead of `fetch-depth: 0`, it must fetch both the v7 Decision commit and the tested head/merge commit and must be covered by tests or deterministic workflow validation.

### 6.4 Regression tests

Add or update tests only in the allowed test files to cover:

- normal checked-out branch;
- detached HEAD with `GITHUB_HEAD_REF`;
- push event with `GITHUB_REF=refs/heads/...`;
- PR merge ref with and without `GITHUB_HEAD_REF`;
- tag ref rejection;
- missing environment rejection;
- Decision commit ancestor success with sufficient history;
- missing/shallow history producing a blocking diagnostic rather than a false pass;
- invalid expected branch remaining rejected;
- State Gate and Decision Preflight checkout history configuration.

### 6.5 Allowed implementation and artifact paths

```text
reverse_agent/project_gate.py
tests/test_project_gate.py
tests/test_decision_preflight.py
.github/workflows/state-gate.yml
.github/workflows/decision-preflight.yml
project_state/state_manifest.json
project_state/context/current_context_packet.json
project_state/gates/*.json
project_state/pytest_result.txt
project_state/codex_execution_report.md
project_state/execution_report.md
project_state/rounds/round_20260718_ci_pr_branch_authority_and_history_parity_rework_v7/*
```

`project_state/decision_packet.md` is modified only by the already-authorized v7 Decision commit. Do not modify it during implementation.

All other source, workflow, test, roadmap, Skills, Runner, Job, frontend, User Solve, reverse-solving, packaging, database, cleanup, retention, sample, tool-integration, and historical archive paths are forbidden.

### 6.6 Publication boundary

After all local validation, closeout, archive, context/state sync, and seal are current:

1. stage only explicit allowed paths;
2. create one final validation commit `S3` on the existing branch;
3. push `S3` to the existing branch;
4. stop all branch mutation;
5. observe GitHub checks externally against exact `S3`;
6. do not commit a remote-check receipt after `S3`.

## 7. Tests

The final locked command-plan must authorize platform-appropriate equivalents of the following commands and no broader Git operations:

```text
Set-Location F:\reverse-agent
Get-Location
Test-Path F:\reverse-agent
git rev-parse --show-toplevel
git status --short
git log --oneline --decorate -n 12

python -m reverse_agent.project_gate preflight --state-dir project_state
python -m reverse_agent.project_gate gate-profile --state-dir project_state --profile full
python -m reverse_agent.project_gate command-plan --state-dir project_state
python -m reverse_agent.project_gate command-plan --state-dir project_state --json

python -m pytest tests/test_project_gate.py tests/test_decision_preflight.py -q
python -m pytest tests/test_project_gate.py tests/test_project_reports.py tests/test_decision_preflight.py tests/test_post_final_evidence_sync.py tests/test_project_state.py tests/test_project_jobs.py -q

python -m reverse_agent.project_gate preflight --state-dir project_state
python -m reverse_agent.project_gate report-summary --state-dir project_state
python -m reverse_agent.project_gate execution-log --state-dir project_state
python -m reverse_agent.project_gate final-check --state-dir project_state
python -m reverse_agent.project_gate run-closeout --state-dir project_state --round-id round_20260718_ci_pr_branch_authority_and_history_parity_rework_v7
python -m reverse_agent.project_gate close-round --state-dir project_state --round-id round_20260718_ci_pr_branch_authority_and_history_parity_rework_v7
python -m reverse_agent.project_gate post-final-evidence-sync --state-dir project_state
python -m reverse_agent.project_gate final-check --state-dir project_state
python -m reverse_agent.project_gate final-evidence-seal --state-dir project_state --round-id round_20260718_ci_pr_branch_authority_and_history_parity_rework_v7

git diff --check
git status --short
```

The test evidence must explicitly record the environment/ref cases, not only a single happy path.

The command-plan must authorize explicit-path staging, one final `S3` commit, and one push to the existing branch. It must not authorize `git add -A`, merge, rebase, force-push, direct push to `main`, or a new branch/PR.

External acceptance requires all of the following for exact final commit `S3`:

```text
CI = completed/success
State Gate = completed/success
Decision Preflight = completed/success
PR head SHA = S3
workflow head SHA = S3
no later branch commit
final-check = PASSED
run-closeout = PASSED
round manifest = current
context packet = current
state manifest = current
final evidence seal = current
```

## 8. Stop Conditions

Stop with `BLOCKED` or `REWORK_REQUIRED` and do not expand scope if:

- the branch cannot fast-forward to the remote branch without merge or rebase;
- PR #5, branch, Decision, digest, or expected branch identity cannot be verified;
- the v7 Decision or command-plan lock fails;
- a required command is absent from the locked command-plan;
- branch resolution requires accepting `refs/pull/*`, arbitrary detached HEAD, or untrusted environment values as valid branch authority;
- no trustworthy branch identity is available in CI;
- ancestry can pass only by removing, suppressing, or bypassing the Decision-commit ancestor check;
- the workflow remains depth-1 and cannot prove the v7 Decision commit ancestry;
- a workflow change outside State Gate or Decision Preflight is required;
- the fix requires broad policy weakening or another mainline;
- focused tests fail or do not cover all changed tests and ref cases;
- local preflight fails on the real execution branch;
- report ID, command output, exit code, execution-log, report-summary, final-check, context, manifest, archive, closeout, or seal parity fails;
- v4-v6 archived or sealed evidence changes;
- unrelated or forbidden paths change;
- publication requires merge, rebase, force-push, direct push to `main`, another branch, or another PR;
- any commit is added after final commit `S3`;
- PR head changes during attestation;
- CI, State Gate, or Decision Preflight fails or remains nonterminal for exact `S3`.

Do not solve a Stop Condition by weakening a gate, suppressing evidence, editing historical artifacts, or expanding to another mainline.
