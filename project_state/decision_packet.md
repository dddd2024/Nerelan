```json decision_meta
{
  "schema_version": 1,
  "decision_id": "decision_20260717_ci_packaging_bootstrap_and_external_attestation_rework_v5",
  "round_id": "round_20260717_ci_packaging_bootstrap_and_external_attestation_rework_v5",
  "based_on_state_build_id": "state_20260618_134029_d6bd033d2532",
  "based_on_state_digest": "d6bd033d25324345cfd8ada0ac65db42bc86eb5017f3ffc92906fcd8b71cacb5",
  "status": "APPROVED",
  "mainline": "project_governance",
  "skill_profiles": ["reverse-agent-iteration@v2"]
}
```

```json decision_contract
{
  "follows_last_decision_id": "decision_20260717_branch_evidence_convergence_rework_v4",
  "follows_last_round_id": "round_20260717_branch_evidence_convergence_rework_v4",
  "previous_audit_outcome": "REWORK_REQUIRED",
  "required_profile": "full",
  "execution_branch": "agent/terminal-status-propagation-seal-restart-rework-v3",
  "base_branch": "main",
  "reuse_existing_draft_pr_number": 5,
  "decision_branch_mode": "branch_local_authority",
  "decision_commit_must_precede_implementation": true,
  "decision_content_digest_lock_required": true,
  "command_plan_branch_binding_required": true,
  "command_plan_digest_lock_required": true,
  "command_plan_precedes_execution_required": true,
  "remote_green_required_for_acceptance": true,
  "remote_attestation_mode": "external_head_observation_without_post_check_branch_mutation",
  "closeout_required": true,
  "close_round_required": true,
  "pytest_required": true,
  "allowed_source_files": [
    "pyproject.toml",
    ".github/workflows/ci.yml",
    ".github/workflows/state-gate.yml",
    ".github/workflows/decision-preflight.yml"
  ],
  "allowed_test_files": [
    "tests/test_packaging_metadata.py",
    "tests/test_project_gate.py",
    "tests/test_project_reports.py",
    "tests/test_project_state.py",
    "tests/test_project_jobs.py",
    "tests/test_post_final_evidence_sync.py",
    "tests/test_decision_preflight.py"
  ],
  "allowed_project_state_files": [
    "project_state/state_manifest.json",
    "project_state/context/current_context_packet.json",
    "project_state/gates/*.json",
    "project_state/pytest_result.txt",
    "project_state/codex_execution_report.md",
    "project_state/execution_report.md",
    "project_state/rounds/round_20260717_ci_packaging_bootstrap_and_external_attestation_rework_v5/*"
  ],
  "read_only_evidence_files": [
    "project_state/rounds/round_20260717_branch_evidence_convergence_rework_v4/*",
    "project_state/gates/final_evidence_seal.json",
    "project_state/gates/remote_check_observation.json",
    "project_state/next_round_plan_20260717_ci_repair_preparation.md",
    "project_state/current_state.json",
    "project_state/task_packet.json",
    "project_state/artifact_index.json",
    "project_state/negative_results.json",
    "project_state/roadmap/workstreams.json",
    ".codex-skills/registry.json"
  ],
  "forbidden_mutated_paths": [
    ".codex-skills/*",
    "frontend/*",
    "solve_reports/*",
    "training_materials/local_reverse/*",
    "reverse_agent/*",
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
    "commit_allowed": true,
    "push_allowed": true,
    "draft_pr_allowed": true,
    "direct_push_to_main_allowed": false,
    "force_push_allowed": false,
    "merge_allowed": false,
    "rebase_allowed": false,
    "tag_mutation_allowed": false,
    "remote_branch_deletion_allowed": false,
    "secrets_mutation_allowed": false,
    "git_add_all_allowed": false,
    "stage_only_explicit_allowed_paths": true,
    "publish_only_after_required_local_validation": true,
    "no_branch_mutation_after_final_validation_commit": true
  }
}
```

# DECISION_PACKET

## 1. Goal

Complete one bounded `project_governance` rework round on the existing Draft PR #5 branch:

```text
agent/terminal-status-propagation-seal-restart-rework-v3
```

Repair the repository packaging bootstrap that currently causes all three GitHub checks to fail at `Install package`, then establish a non-self-referential remote acceptance boundary.

The round must produce one final validation commit `S`. After `S` is pushed, the branch must not be modified again during this round. CI, State Gate, and Decision Preflight must run against exactly `S`. Their terminal results are evaluated externally by the independent auditor and must not be written back through another branch commit.

Reuse the existing command-plan, execution-log, report-summary, final-check, run-closeout, close-round, context, state-manifest, and seal foundations. Do not implement another governance or remote-observation system.

## 2. Current Evidence

- The branch-local `project_state/decision_packet.md` is the sole current task authority. `project_state/task_packet.json` is older sample-oriented background and explicitly states that `decision_packet.md` controls the current round.
- Current mainline is `project_governance`.
- Draft PR #5 is open, unmerged, based on `main`, and uses `agent/terminal-status-propagation-seal-restart-rework-v3`.
- The branch head before this Decision commit was `35ff592d21e8d40786eea9fdd6972557c95340e7`.
- The v4 round is honestly closed as `REWORK_REQUIRED`: its report is `FAILED`, its final gate is non-accepting, its run-closeout failed, and its final evidence seal records `REWORK_REQUIRED`.
- v4 sealed and archived artifacts are historical read-only evidence. This round must not edit them to make v4 appear accepted.
- The v4 remote observation was bound to an older head, while the branch later advanced. This proves that writing remote results back into the same branch creates stale-head evidence.
- The current branch head checks are terminal failures: CI, State Gate, and Decision Preflight all fail at the `Install package` step.
- `.github/workflows/ci.yml`, `.github/workflows/state-gate.yml`, and `.github/workflows/decision-preflight.yml` invoke `python -m pip install -e .` under Python 3.13.
- No `pyproject.toml`, `setup.py`, or `setup.cfg` is present at the branch root. The first hypothesis is therefore missing editable-install packaging metadata. This is a hypothesis to validate, not permission for a broad packaging redesign.
- Existing capabilities include decision linting, command-plan authority and locking, execution-log chronology, report-summary synthesis, final-check, run-closeout, close-round archive, context sync, state-manifest freshness, final evidence sealing, publication truth, policy-lint, prompt-consistency, CI/state-gate workflows, Job foundations, Runner contract foundations, manual Web orchestration, and User Solve foundations.
- This round strengthens existing CI/governance integration and does not duplicate those capabilities.
- `project_state/current_state.json`, `task_packet.json`, and `artifact_index.json` remain stale sample-scoped material and are read-only/non-blocking for this governance round.
- `project_state/negative_results.json` contains reverse-solving restrictions. This round does not repeat those directions and does not inspect or commit `solve_reports`.
- `project_state/context/current_context_packet.json` and `project_state/roadmap/workstreams.json` exist. The workstream registry explicitly states that roadmap entries are not execution authority.
- Local deterministic Python, isolated virtual environments, tests, read-only Git/GitHub inspection, and the exact approved branch publication flow are allowed.
- Reverse tools, runtime binary probes, model APIs, Runner dispatch, Web runtime, databases, cleanup apply, destructive actions, and unrelated workstreams are not allowed.
- Closeout is allowed only after the current Decision content and command-plan are locked and the local clean-environment validation passes.
- Final acceptance is not produced by the execution Agent. It requires external observation that the three workflows completed successfully for the exact final validation commit `S`.

## 3. Do Not Do

Do not:

- create another branch or PR;
- merge PR #5;
- modify v4 archived or sealed artifacts;
- modify `project_state/next_round_plan_20260717_ci_repair_preparation.md`; it remains planning-only and is not task authority;
- edit historical evidence to hide prior failures;
- modify `reverse_agent/*`, frontend, Runner, Job, User Solve, reverse-solving, roadmap, database, cleanup, Skill, sample, or tool-integration code;
- read the complete `solve_reports/` tree or `PROJECT_PROGRESS_LOG.txt`;
- run reverse tools, debuggers, emulators, hooks, runtime probes, or model APIs;
- add speculative runtime dependencies without proving they are imported or required;
- introduce Poetry, Hatch, PDM, a monorepo tool, container build system, or another heavy packaging framework;
- change all three workflow files merely because they share the same failed step;
- change Python versions to hide a packaging error unless Python 3.13 incompatibility is demonstrated by concrete evidence;
- broaden the test suite or application architecture beyond what is needed to validate packaging and existing focused workflows;
- execute substantive commands before the current Decision and command-plan locks exist;
- execute commands absent from the locked command-plan;
- treat a command exit code listed as diagnostic as proof of acceptance;
- claim remote checks passed before observing their terminal results for the exact final commit;
- commit a post-check remote receipt to this branch after final validation commit `S`;
- create a self-referential sequence in which observing `S` creates `S+1` and invalidates the observation;
- use `git add -A`, stage unrelated files, direct-push to `main`, force-push, rebase, merge, tag, mutate secrets, or delete remote branches;
- modify sealed artifacts after the final local seal;
- start Trust Layer, roadmap replacement, Web, Runner, User Solve, tool integration, reverse solving, or another mainline.

## 4. Files To Inspect

Required current evidence:

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
- `project_state/gates/final_evidence_seal.json`
- `project_state/gates/report_summary_synthesis.json`
- `project_state/rounds/round_20260717_branch_evidence_convergence_rework_v4/*`
- `.codex-skills/registry.json`

Required packaging and workflow evidence:

- repository root file inventory relevant to packaging;
- `pyproject.toml`, `setup.py`, `setup.cfg`, and requirement files if present;
- `.github/workflows/ci.yml`
- `.github/workflows/state-gate.yml`
- `.github/workflows/decision-preflight.yml`
- imports used by the packages exercised in the three workflows;
- current failing workflow job logs, especially the complete `Install package` output;
- current PR #5 head/base/draft/merge state.

Do not inspect unrelated source trees unless the clean editable install or an authorized focused test identifies a concrete in-scope dependency.

## 5. Required Audit

The final execution report must answer each item separately with artifact path or Git observation, field/step name, concrete observed value, status, and item-specific conclusion.

1. Is the execution branch exactly `agent/terminal-status-propagation-seal-restart-rework-v3`?
2. Is Draft PR #5 still open, unmerged, and the sole review surface?
3. Is this v5 Decision commit an ancestor of every v5 implementation, test, evidence, and publication commit?
4. Is `decision_meta` valid with exact v5 IDs, `APPROVED`, `project_governance`, and active `reverse-agent-iteration@v2`?
5. Is `decision_packet.md` the sole task authority and `task_packet.json` background only?
6. Are v4 archive and seal artifacts unchanged?
7. Was the v5 Decision content digest locked before command-plan generation?
8. Does the command-plan bind the exact Decision ID, round ID, branch, Decision digest, and Decision commit SHA?
9. Was the command-plan locked before package inspection commands that modify files, clean-install validation, pytest, closeout, or publication?
10. Does the captured GitHub job evidence show all three current failures at `Install package`?
11. Is the exact install error recorded, rather than inferred only from the step name?
12. Was absence or invalidity of packaging metadata confirmed before creating or changing it?
13. Does the packaging fix use the smallest supported mechanism needed for `pip install -e .` or an explicitly justified equivalent?
14. Are runtime and test dependencies derived from concrete imports and workflow needs rather than copied from the local environment?
15. If workflow install commands changed, was the change necessary and consistent across only the affected workflows?
16. Were Python-version changes avoided unless incompatibility was concretely proven?
17. Does a clean isolated environment successfully install the project?
18. Does the clean environment import every module imported by the three workflows?
19. Did the selected focused pytest command pass and cover every changed test file?
20. Were only allowed packaging, workflow, test, and generated current-round evidence paths modified?
21. Were `reverse_agent/*` and all unrelated mainlines left untouched?
22. Do report aliases and synthesized summaries agree?
23. Do execution log and pytest transcript preserve actual chronology?
24. Are context and state manifest current after the final local gate state?
25. Do live and archived v5 report and pytest aliases match at the archive boundary?
26. Does the v5 final seal bind the final local report, gate, closeout, context, state manifest, round manifest, command-plan lock, and final validation commit candidate?
27. Is the local report explicit that external remote acceptance is still pending at the local seal boundary?
28. Was the final validation commit `S` pushed only after local validation and sealing completed?
29. Was the branch left unchanged after `S` was pushed?
30. Were no post-check receipt, plan, report, or evidence commits added after `S`?
31. Were direct push to `main`, force push, merge, rebase, tag mutation, secret mutation, branch deletion, and `git add -A` avoided?
32. Does the execution report avoid claiming final `ACCEPTED` before external observation of the exact `S` checks?
33. Is the external auditor instructed to verify CI, State Gate, and Decision Preflight against the exact `S` SHA?
34. If any remote check fails, does the round remain `REWORK_REQUIRED` with the failing workflow/job/step preserved?
35. If all three remote checks pass for `S`, is external audit allowed to return `ACCEPTED` without another branch mutation?

## 6. Implementation Scope

### 6.1 Decision and command authority

Before substantive work:

1. verify branch, PR, and current HEAD;
2. verify this Decision commit is on the branch;
3. run decision-lint;
4. generate the full gate profile;
5. generate a branch-bound command-plan;
6. create Decision and command-plan digest locks;
7. record startup snapshot and round baseline.

Do not reuse v4 locks or command-plan as v5 authority.

### 6.2 Diagnose the editable-install failure

Obtain the complete `Install package` log for the current branch head and classify the failure as one of:

```text
missing_packaging_metadata
invalid_packaging_metadata
package_discovery_failure
dependency_resolution_failure
python_313_incompatibility
workflow_command_error
other_evidence_backed_failure
```

Record the exact error text in the execution report within normal quotation limits. Do not guess the class from the workflow step name alone.

### 6.3 Minimal packaging bootstrap

Preferred first implementation, only if evidence confirms missing packaging metadata:

- add one minimal root `pyproject.toml` using a standard PEP 517 backend;
- declare the project package discovery needed for `reverse_agent`;
- declare the supported Python range consistent with the code and workflow;
- declare only proven runtime dependencies;
- provide a narrowly scoped test dependency mechanism when required by the workflows.

Do not add multiple packaging systems. Do not introduce lockfiles or release automation.

Workflow files may be changed only when the minimal packaging metadata cannot make their existing install command valid, or when a clean test dependency install is otherwise impossible. Any workflow change must be identical in purpose and separately justified.

### 6.4 Packaging regression test

A new `tests/test_packaging_metadata.py` is allowed. It should remain deterministic and may verify:

- required `pyproject.toml` sections exist;
- package discovery includes `reverse_agent`;
- declared Python compatibility includes the workflow version;
- workflow install commands are mutually consistent;
- forbidden heavy packaging systems were not introduced.

It must not invoke the network.

### 6.5 Clean-environment validation

Use an isolated temporary virtual environment. The locked command-plan must include equivalent commands for:

```text
python -m venv <temporary-path>
<temporary-python> -m pip install --upgrade pip
<temporary-python> -m pip install -e .
<temporary-python> -c "import reverse_agent.project_gate; import reverse_agent.project_state; import reverse_agent.post_final_evidence_sync; import reverse_agent.decision_preflight"
<temporary-python> -m pytest tests/test_project_gate.py tests/test_project_reports.py tests/test_project_jobs.py tests/test_post_final_evidence_sync.py tests/test_decision_preflight.py tests/test_project_state.py tests/test_packaging_metadata.py -q
```

If an approved test extra is required, substitute the exact evidence-backed editable-install form and keep it consistent with the workflows.

Do not rely on packages already installed in the developer's global environment.

### 6.6 Local governance closeout

After clean installation and focused tests pass:

- generate report-summary and execution-log evidence;
- run final-check;
- run close-round/run-closeout in the order required by the current gate implementation;
- synchronize context and state manifest;
- archive the v5 report and pytest aliases;
- generate the final local evidence seal.

The local report must distinguish:

```text
local_implementation_status
local_validation_status
remote_attestation_status
final_acceptance_status
```

At the pre-push seal boundary, `remote_attestation_status` must be `PENDING_EXTERNAL_OBSERVATION`, and the execution Agent must not claim final `ACCEPTED`.

### 6.7 Final validation commit and external attestation

Create one final validation commit `S` containing only the approved implementation and v5 evidence. Push `S` to the existing branch.

After pushing `S`:

- do not modify the branch;
- do not commit a remote receipt;
- do not regenerate project_state artifacts;
- observe GitHub checks read-only;
- preserve `S` as the exact attested head.

The independent auditor, not the execution Agent, must read GitHub's current workflow state for `S` and return one of:

```text
ACCEPTED
REWORK_REQUIRED
BLOCKED
```

External acceptance requires all of:

```text
CI = completed/success
State Gate = completed/success
Decision Preflight = completed/success
observed head SHA = S
PR head SHA = S
no later branch commit
```

No additional branch commit is required or allowed to record this external verdict.

### 6.8 Allowed generated artifacts

Generated current-round artifacts are limited to:

- current report and pytest aliases;
- current context and state manifest;
- current `project_state/gates/*.json` selected by the gate profile;
- `project_state/rounds/round_20260717_ci_packaging_bootstrap_and_external_attestation_rework_v5/*`.

Do not modify v4 artifacts or unrelated project_state domains.

## 7. Tests

The current command-plan is the command authority. It must be generated and locked before substantive execution.

Minimum required validation:

```text
python -m reverse_agent.project_gate decision-lint --state-dir project_state
python -m reverse_agent.project_gate gate-profile --state-dir project_state
python -m reverse_agent.project_gate command-plan --state-dir project_state
```

Clean-environment validation must include:

```text
python -m venv <temporary-path>
<temporary-python> -m pip install --upgrade pip
<temporary-python> -m pip install -e .
<temporary-python> -c "import reverse_agent.project_gate; import reverse_agent.project_state; import reverse_agent.post_final_evidence_sync; import reverse_agent.decision_preflight"
<temporary-python> -m pytest tests/test_project_gate.py tests/test_project_reports.py tests/test_project_jobs.py tests/test_post_final_evidence_sync.py tests/test_decision_preflight.py tests/test_project_state.py tests/test_packaging_metadata.py -q
```

When `tests/test_packaging_metadata.py` is not created because no packaging file changes are required, the command-plan must omit it explicitly and record the reason.

Add regression coverage for:

1. editable install succeeds from a clean environment;
2. `reverse_agent` is discoverable after installation;
3. the four workflow-imported modules import successfully;
4. workflow Python 3.13 is compatible with declared metadata;
5. all affected workflows use an evidence-backed install command;
6. missing or malformed packaging metadata is detected;
7. no unproven runtime dependency is introduced;
8. v4 artifacts remain unchanged;
9. reports cannot claim remote success at the local seal boundary;
10. the final commit SHA intended for attestation is recorded without claiming its future check result;
11. post-check branch mutation is prohibited by the Decision and publication procedure.

Required generated evidence:

- `project_state/pytest_result.txt`
- `project_state/codex_execution_report.md`
- `project_state/execution_report.md`
- selected current `project_state/gates/*.json`
- current context and state manifest
- v5 round archive and round manifest
- final local evidence seal.

The execution Agent must stop after pushing final validation commit `S` and observing checks read-only. It must not create another commit.

## 8. Stop Conditions

Stop and report `BLOCKED` or `REWORK_REQUIRED` as appropriate if:

- the current branch or PR is not the approved branch/PR;
- this Decision commit is not an ancestor of implementation work;
- Decision or command-plan locking fails;
- substantive execution occurred before the current locks and cannot be discarded through an explicit clean restart;
- obtaining the complete install error requires unauthorized credentials or mutation;
- the failure is not packaging-related and fixing it requires another mainline;
- a valid fix requires modifying `reverse_agent/*` or another forbidden path;
- dependency requirements cannot be derived from concrete imports or existing documented contracts;
- the clean editable install fails after the bounded packaging fix;
- Python 3.13 compatibility cannot be retained without a broader engineering decision;
- selected tests fail;
- workflow changes exceed the three named files or alter unrelated behavior;
- report aliases, execution log, context, state manifest, archive, or seal disagree;
- v4 sealed or archived artifacts change;
- unrelated working-tree changes cannot be excluded from explicit staging;
- final validation commit `S` cannot be pushed without force push, rebase, direct push to `main`, or another prohibited operation;
- any branch commit is created after `S` during this round;
- PR head changes while remote checks are being attested;
- CI, State Gate, or Decision Preflight fails or does not reach a terminal state for `S`;
- remote results can only be recorded by creating a self-referential post-check commit;
- merge would be required to complete the round.

Do not expand scope to solve a Stop Condition. Preserve evidence and wait for independent audit of the exact final validation commit.
