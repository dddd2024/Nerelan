```json decision_meta
{
  "schema_version": 1,
  "decision_id": "decision_20260717_ci_state_hygiene_and_preflight_parity_rework_v6",
  "round_id": "round_20260717_ci_state_hygiene_and_preflight_parity_rework_v6",
  "based_on_state_build_id": "state_20260618_134029_d6bd033d2532",
  "based_on_state_digest": "d6bd033d25324345cfd8ada0ac65db42bc86eb5017f3ffc92906fcd8b71cacb5",
  "status": "APPROVED",
  "mainline": "engineering_branch",
  "skill_profiles": ["reverse-agent-iteration@v2"]
}
```

```json decision_contract
{
  "follows_last_decision_id": "decision_20260717_ci_packaging_bootstrap_and_external_attestation_rework_v5",
  "follows_last_round_id": "round_20260717_ci_packaging_bootstrap_and_external_attestation_rework_v5",
  "previous_audit_outcome": "REWORK_REQUIRED",
  "restart_mode": "explicit_new_round",
  "previous_round_artifacts_read_only": true,
  "required_profile": "full",
  "execution_branch": "agent/terminal-status-propagation-seal-restart-rework-v3",
  "base_branch": "main",
  "reuse_existing_draft_pr_number": 5,
  "decision_commit_must_precede_implementation": true,
  "decision_content_digest_lock_required": true,
  "command_plan_branch_binding_required": true,
  "command_plan_digest_lock_required": true,
  "final_command_plan_precedes_substantive_execution": true,
  "command_plan_required_command_coverage": true,
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
    "commit_allowed": true,
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

Complete one bounded `engineering_branch` rework round on existing Draft PR #5 and the existing branch:

```text
agent/terminal-status-propagation-seal-restart-rework-v3
```

Build on the v5 packaging bootstrap instead of reimplementing it. Repair only the remaining engineering failures:

1. make Decision Preflight accept the legitimate `engineering_branch` CI/package repair round without weakening unrelated mainline policy;
2. prevent editable-install metadata such as `reverse_agent.egg-info/` from contaminating Git/state-diff evidence;
3. make command-plan generation cover the Decision-required clean environment, editable install, import check, focused tests, report/log, closeout, archive, context/state sync, seal, and publication commands;
4. make report-summary, execution-log, pytest metadata, final-check, context packet, state manifest, round archive, and final seal converge on the same v6 IDs and current evidence;
5. create one final validation commit `S2`, push it to the existing branch, stop mutating the branch, and let an external auditor read GitHub checks for exactly `S2`.

Do not create a new branch or PR. Do not merge PR #5 in this round.

## 2. Current Evidence

- `project_state/decision_packet.md` is the sole task authority. `project_state/task_packet.json` is background only and does not control this round.
- Current mainline is `engineering_branch`; this round is CI/package/gate engineering, not project-governance planning and not reverse-solving.
- Draft PR #5 is open, Draft, unmerged, targets `main`, and currently uses branch `agent/terminal-status-propagation-seal-restart-rework-v3`.
- The audited v5 final commit is `2254035636da9330fb6bce1327fefb818d6c8cc2`.
- v5 added a minimal `pyproject.toml`; current GitHub CI completed successfully and all three workflows passed `Install package`. The packaging bootstrap itself is therefore an existing foundation, not a feature to recreate.
- State Gate still failed at `Project gate report summary`.
- Decision Preflight still failed at `Decision preflight`; current evidence indicates the v5 `project_governance` classification conflicts with the existing CI/package preflight policy.
- v5 local focused tests recorded `1542 passed`, but the v5 command-plan omitted required clean-venv, editable-install, import-check, packaging-test, closeout, archive, context/state-sync, seal, and publication commands.
- v5 `pytest_result_summary.report_id` did not match the canonical report ID.
- v5 final-check remained `FAILED`; report-summary/execution-log/command-plan parity was incomplete.
- The current context packet and existing final seal still describe v4 evidence; the v5 round manifest is absent. These are stale or missing evidence, not current acceptance evidence.
- Existing foundations already include decision/content locking, command-plan, execution-log, report-summary, final-check, run-closeout, close-round archive, post-final evidence sync, context packet, state manifest, final seal, GitHub CI, State Gate, and Decision Preflight. This round must strengthen and align them, not implement replacements.
- The context packet and workstream registry exist. Roadmap/workstream entries are not execution authority.
- `current_state.json`, `task_packet.json`, and `artifact_index.json` contain older sample-oriented facts and are read-only for this round.
- `negative_results.json` belongs to reverse-solving. This round does not repeat any failed solving direction and does not read or commit full `solve_reports/`.
- Allowed capabilities are local deterministic Python, an isolated temporary virtual environment outside the repository, pip editable installation, focused pytest, read-only GitHub Actions log/artifact observation, and controlled commit/push to the existing branch.
- Reverse tools, debuggers, emulators, model APIs, Runner dispatch, Web runtime, databases, cleanup apply, and destructive state operations are not allowed.
- Closeout is allowed only after the final v6 command-plan is locked and all required local evidence is current.
- Final acceptance requires CI, State Gate, and Decision Preflight to complete successfully for the exact same final commit `S2`, with PR head still equal to `S2` and no later branch commit.
- This round does not duplicate prompt consistency, policy lint, report-summary, execution-log, command-plan, final-check, context, state-manifest, archive, seal, or CI foundations; it repairs their current parity and state-hygiene defects.

## 3. Do Not Do

Do not:

- work on `main`, create another branch, or open another PR;
- merge PR #5;
- rebase, force-push, amend published history, delete branches, tag, or push directly to `main`;
- use `git add -A` or stage files outside the explicit allowlist;
- modify v4 or v5 archived/sealed artifacts to make old rounds pass;
- reuse v4/v5 `PASSED`, `SUCCESS`, `ACCEPTED`, context, manifest, archive, seal, or remote observations as v6 acceptance evidence;
- change reverse-solving logic, sample solvers, harnesses, tool adapters, Runner, Job, frontend, User Solve, roadmap, database, cleanup, retention, or state-domain architecture;
- redesign `project_state/` or move/delete existing state files;
- introduce a heavy packaging framework or speculative runtime dependencies;
- weaken Decision Preflight globally merely to accept any mainline; the fix must be narrow and tested for valid and invalid mainlines;
- suppress report-summary or final-check failures instead of repairing their evidence inputs;
- treat generated `*.egg-info`, build, cache, or temporary files as current project evidence;
- run commands absent from the locked command-plan;
- read full `solve_reports/` or `PROJECT_PROGRESS_LOG.txt`;
- run reverse tools, runtime probes, debuggers, emulators, hooks, model APIs, databases, or cleanup apply;
- create any commit after final commit `S2` while remote attestation is being observed.

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
- `project_state/rounds/round_20260717_ci_packaging_bootstrap_and_external_attestation_rework_v5/*` when present

Required engineering files:

- `pyproject.toml`
- `.gitignore`
- `.github/workflows/ci.yml`
- `.github/workflows/state-gate.yml`
- `.github/workflows/decision-preflight.yml`
- `reverse_agent/project_gate.py`
- `reverse_agent/decision_preflight.py`
- `reverse_agent/post_final_evidence_sync.py`
- `reverse_agent/project_state.py`
- `tests/test_project_gate.py`
- `tests/test_project_reports.py`
- `tests/test_decision_preflight.py`
- `tests/test_post_final_evidence_sync.py`
- `tests/test_project_state.py`
- `tests/test_packaging_metadata.py` when created
- `.codex-skills/registry.json`

Required external observations:

- current branch and HEAD;
- `git status --short` before implementation;
- PR #5 head/base/draft/merge state;
- current v5 workflow runs and failed job steps;
- final v6 workflow runs, job steps, conclusions, and exact head SHA.

Do not inspect unrelated source trees unless an authorized clean install or focused test identifies a concrete in-scope dependency.

## 5. Required Audit

The final report must answer every numbered item separately. Each answer must include the artifact path or GitHub observation, field/step, concrete value, status, and item-specific conclusion.

1. Is the execution branch exactly `agent/terminal-status-propagation-seal-restart-rework-v3`?
2. Is Draft PR #5 still open, unmerged, and the sole review surface targeting `main`?
3. Is the v6 Decision commit an ancestor of every v6 implementation, test, evidence, and final publication commit?
4. Is the Decision `APPROVED`, `engineering_branch`, and bound to active `reverse-agent-iteration@v2`?
5. Is `decision_packet.md` the task authority and `task_packet.json` background only?
6. Were v4 and v5 archived/sealed artifacts left read-only?
7. Was the v6 Decision digest locked before the final command-plan was generated and locked?
8. Does the final command-plan bind the exact v6 IDs, branch, Decision digest, and Decision commit?
9. Does the final command-plan explicitly authorize every required clean-environment, install, import, pytest, reporting, log, closeout, archive, sync, seal, staging, commit, and push command?
10. Are commands omitted from the final command-plan explicitly listed with evidence-backed reasons, and were they not executed?
11. Does Decision Preflight accept this valid `engineering_branch` round while still rejecting invalid mainlines and forbidden capabilities in tests?
12. Does editable install succeed under Python 3.13 in a clean temporary virtual environment outside the repository?
13. Does `pyproject.toml` use minimal justified metadata and avoid speculative dependencies?
14. Are editable-install metadata and cache paths absent from the repository dirty-state evidence through deterministic ignore or isolation policy?
15. Do the workflow import checks pass for `reverse_agent.project_gate`, `reverse_agent.project_state`, `reverse_agent.post_final_evidence_sync`, and `reverse_agent.decision_preflight`?
16. Do focused tests pass and cover every changed or newly added test file?
17. Does `pytest_result_summary.report_id` exactly match the canonical v6 report ID?
18. Does the recorded command-plan JSON stdout contain the full commands array and match the live locked command-plan?
19. Do recorded exit codes match the final command-plan expected exit codes?
20. Does execution-log contain every required command in actual observed order with current v6 IDs?
21. Do `codex_execution_report.md`, `execution_report.md`, auto summaries, and `report_summary_synthesis.json` agree semantically?
22. Does report-summary pass in a workspace equivalent to GitHub Actions, without unreported generated files?
23. Does final-check pass with no active FAIL/FAILED checks?
24. Is the v6 context packet current and generated after the current final gate?
25. Is the v6 state manifest current and digest-consistent with all required live artifacts?
26. Does the v6 round manifest exist and match the live report, pytest result, execution report, and final recommendation?
27. Does run-closeout execute real current-round steps after the final command-plan lock and reach a status consistent with the report?
28. Does the v6 final seal bind the final command-plan, report, pytest result, execution-log, final gate, closeout, context, state manifest, and round manifest?
29. Were all changed paths inside the authorized v6 scope, with no unexplained inherited or generated dirty files?
30. Were prohibited Git operations avoided?
31. Is final commit `S2` the PR head with no later branch mutation?
32. Did CI complete successfully for exact `S2`?
33. Did State Gate complete successfully for exact `S2`?
34. Did Decision Preflight complete successfully for exact `S2`?
35. Do report, final-check, closeout, context, state manifest, round manifest, seal, PR head, and external workflow observations agree on the final recommendation?

## 6. Implementation Scope

### 6.1 Authority and restart

1. Fast-forward the local branch to the current remote branch only when necessary; do not merge or rebase.
2. Verify PR #5 and the exact current HEAD.
3. Lock the v6 Decision content.
4. Generate the v6 gate profile and branch-bound command-plan.
5. If the generated command-plan does not contain the required v6 commands, do not begin packaging/gate implementation. Repair only the command-plan generation and its tests within the allowed files, regenerate the command-plan, and replace the preliminary lock with one final canonical lock before any remaining substantive execution.
6. Record one explicit v6 restart segment when a preliminary command-plan is superseded. Acceptance evidence must use only the final locked command-plan segment.

### 6.2 Narrow engineering repair

Reuse the existing packaging and gate mechanisms. Make only evidence-backed changes needed to:

- add deterministic ignore/isolation handling for `reverse_agent.egg-info/`, `*.egg-info/`, build metadata, caches, and temporary validation outputs;
- keep `pyproject.toml` minimal and Python 3.13 compatible;
- make Decision Preflight support the valid `engineering_branch` CI/package repair case without relaxing unrelated restrictions;
- make command-plan generation capture Decision-required commands and omissions;
- make command-plan JSON stdout, execution-log, pytest metadata, report-summary, and final-check agree;
- generate current v6 context, state manifest, closeout, round archive, and final seal through existing mechanisms;
- preserve external attestation as a GitHub-side observation after final commit `S2`, not as a receipt committed after `S2`.

### 6.3 Allowed implementation paths

```text
pyproject.toml
.gitignore
.github/workflows/ci.yml
.github/workflows/state-gate.yml
.github/workflows/decision-preflight.yml
reverse_agent/project_gate.py
reverse_agent/decision_preflight.py
reverse_agent/post_final_evidence_sync.py
reverse_agent/project_state.py
tests/test_packaging_metadata.py
tests/test_project_gate.py
tests/test_project_reports.py
tests/test_decision_preflight.py
tests/test_post_final_evidence_sync.py
tests/test_project_state.py
project_state/state_manifest.json
project_state/context/current_context_packet.json
project_state/gates/*.json
project_state/pytest_result.txt
project_state/codex_execution_report.md
project_state/execution_report.md
project_state/rounds/round_20260717_ci_state_hygiene_and_preflight_parity_rework_v6/*
```

Workflow files may be modified only when source/test changes cannot make the existing bounded workflow pass. The report must explain each workflow change.

All Skills, Runner, Job, frontend, User Solve, reverse-solving, roadmap, database, cleanup, retention, sample, tool-integration, v4/v5 archive, and unrelated source paths are forbidden.

### 6.4 Publication boundary

After all local validation, closeout, archive, context/state sync, and seal are current:

1. stage only explicit allowed paths;
2. create one final validation commit `S2`;
3. push `S2` to the existing branch;
4. stop all branch mutation;
5. observe GitHub checks externally against exact `S2`;
6. do not commit a remote-check receipt after `S2`.

## 7. Tests

The final locked command-plan must contain exact platform-appropriate equivalents of all commands below. Place the temporary environment outside the repository.

```text
Set-Location F:\reverse-agent
Get-Location
Test-Path F:\reverse-agent
git rev-parse --show-toplevel
git status --short

python -m reverse_agent.project_gate preflight --state-dir project_state
python -m reverse_agent.project_gate gate-profile --state-dir project_state --profile full
python -m reverse_agent.project_gate command-plan --state-dir project_state
python -m reverse_agent.project_gate command-plan --state-dir project_state --json

python -m venv <temporary-path-outside-repository>
<temporary-python> -m pip install --upgrade pip
<temporary-python> -m pip install -e .
<temporary-python> -c "import reverse_agent.project_gate; import reverse_agent.project_state; import reverse_agent.post_final_evidence_sync; import reverse_agent.decision_preflight"
<temporary-python> -m pytest tests/test_packaging_metadata.py tests/test_project_gate.py tests/test_project_reports.py tests/test_decision_preflight.py tests/test_post_final_evidence_sync.py tests/test_project_state.py tests/test_project_jobs.py -q

python -m reverse_agent.project_gate report-summary --state-dir project_state
python -m reverse_agent.project_gate execution-log --state-dir project_state
python -m reverse_agent.project_gate final-check --state-dir project_state
python -m reverse_agent.project_gate run-closeout --state-dir project_state --round-id round_20260717_ci_state_hygiene_and_preflight_parity_rework_v6
python -m reverse_agent.project_gate close-round --state-dir project_state --round-id round_20260717_ci_state_hygiene_and_preflight_parity_rework_v6
python -m reverse_agent.project_gate post-final-evidence-sync --state-dir project_state
python -m reverse_agent.project_gate final-check --state-dir project_state
python -m reverse_agent.project_gate final-evidence-seal --state-dir project_state --round-id round_20260717_ci_state_hygiene_and_preflight_parity_rework_v6
```

If a listed CLI name differs in the current code, use the current supported equivalent and record the exact mapping in command-plan and report. Do not silently omit it.

The command-plan must also authorize explicit-path staging, one final commit, and one push to the existing branch. It must not authorize `git add -A`, merge, rebase, force-push, or direct push to `main`.

External acceptance requires all of the following for exact final commit `S2`:

```text
CI = completed/success
State Gate = completed/success
Decision Preflight = completed/success
PR head SHA = S2
workflow head SHA = S2
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

- the local branch cannot fast-forward to the remote branch without merge or rebase;
- branch, PR, Decision, or digest identity cannot be verified;
- Decision or final command-plan locking fails;
- the final command-plan cannot explicitly authorize every required command and omission;
- a required command would be executed outside the locked command-plan;
- Decision Preflight requires broad policy weakening or another mainline;
- the package fix requires speculative dependencies or a heavy packaging redesign;
- Python 3.13 editable install or import checks fail;
- generated `*.egg-info`, build, cache, or temporary files remain unexplained in Git/state evidence;
- focused tests fail or do not cover changed tests;
- report ID, command stdout, exit code, execution-log, report-summary, or final-check parity fails;
- current context, state manifest, round manifest, closeout, archive, or final seal cannot be generated consistently;
- v4/v5 archived or sealed evidence changes;
- unrelated or forbidden paths change;
- publication requires merge, rebase, force-push, direct push to `main`, or another PR;
- any commit is added after final commit `S2`;
- PR head changes during attestation;
- CI, State Gate, or Decision Preflight fails or remains nonterminal for `S2`.

Do not solve a Stop Condition by weakening a gate, suppressing evidence, editing historical artifacts, or expanding to another mainline.
