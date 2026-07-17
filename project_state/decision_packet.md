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

Repair the packaging bootstrap that currently causes CI, State Gate, and Decision Preflight to fail at `Install package`, and establish a non-self-referential remote acceptance boundary.

The execution must produce one final validation commit `S`. After `S` is pushed, this round must not mutate the branch again. GitHub checks must run against exactly `S`; the independent auditor reads those terminal checks directly and does not commit a receipt that would create `S+1`.

Reuse the existing decision, command-plan, execution-log, report-summary, final-check, closeout, archive, context, state-manifest, seal, and CI foundations. Do not create a second control plane.

## 2. Current Evidence

- Current task authority is branch-local `project_state/decision_packet.md`; `task_packet.json` is older sample-oriented background only.
- Current mainline is `project_governance`.
- PR #5 is open, Draft, unmerged, based on `main`, and uses branch `agent/terminal-status-propagation-seal-restart-rework-v3`.
- v4 ended honestly as `REWORK_REQUIRED`: report `FAILED`, non-accepting final gate, failed run-closeout, and final seal `REWORK_REQUIRED`.
- v4 archive and sealed evidence are historical read-only inputs. They must not be edited to make v4 pass.
- The previous remote observation was bound to an older head and became stale when another branch commit was added. Therefore remote check results must not be written back through a post-check branch commit.
- Current PR checks for CI, State Gate, and Decision Preflight all reach terminal failure at the `Install package` step.
- The three workflows use Python 3.13 and execute `python -m pip install -e .`.
- No root `pyproject.toml`, `setup.py`, or `setup.cfg` was found. Missing packaging metadata is the leading hypothesis, but the exact job log must confirm the failure before implementation.
- Existing foundations already cover command-plan authority and locking, execution chronology, report synthesis, final-check, closeout/archive, context/state-manifest freshness, final sealing, publication truth, policy-lint, prompt-consistency, CI/state-gate, Job, Runner contract, manual Web orchestration, and User Solve.
- This round strengthens existing packaging/CI integration and does not reimplement those capabilities.
- `current_state.json`, `task_packet.json`, and `artifact_index.json` contain stale sample facts and are read-only/non-blocking for this governance round.
- `negative_results.json` is reverse-solving scope; this round does not repeat those directions and does not inspect or commit full `solve_reports`.
- Context packet and workstream registry exist; the registry states roadmap entries are not execution authority.
- Allowed capabilities: local deterministic Python, isolated virtual environments, focused tests, read-only Git/GitHub inspection, and the exact approved branch publication flow.
- Forbidden capabilities: reverse tools, runtime binary probes, model APIs, Runner dispatch, Web runtime, databases, cleanup apply, destructive actions, and unrelated workstreams.
- Local closeout is allowed only after the v5 Decision and command-plan are locked and clean-environment validation passes.
- Final acceptance requires external confirmation that all three workflows succeeded for exact final commit `S` and that the PR head remained `S`.

## 3. Do Not Do

Do not:

- create another branch or PR;
- merge PR #5;
- modify v4 archived or sealed artifacts;
- modify `project_state/next_round_plan_20260717_ci_repair_preparation.md`; it is planning-only, not authority;
- edit historical evidence to conceal prior failures;
- modify `reverse_agent/*`, Skills, Runner, Job, frontend, User Solve, reverse-solving, roadmap, database, cleanup, sample, or tool-integration code;
- read full `solve_reports/` or `PROJECT_PROGRESS_LOG.txt`;
- run reverse tools, debuggers, emulators, hooks, runtime probes, or model APIs;
- add dependencies copied from the local environment without import/workflow evidence;
- introduce Poetry, Hatch, PDM, containers, release automation, lockfiles, or another heavy packaging framework;
- alter all workflows merely because they share a failed step;
- change Python versions to hide an error unless Python 3.13 incompatibility is demonstrated;
- run substantive commands before the current Decision and command-plan locks exist;
- execute commands absent from command-plan;
- claim remote success before observing terminal checks for exact `S`;
- commit a remote receipt, plan, regenerated report, or evidence file after `S`;
- use `git add -A`, stage unrelated files, direct-push to `main`, force-push, rebase, merge, tag, mutate secrets, or delete remote branches;
- modify sealed artifacts after the local seal;
- start Trust Layer, Web, Runner, User Solve, tool integration, reverse solving, or another mainline.

## 4. Files To Inspect

Required governance evidence:

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

Required packaging/CI evidence:

- root packaging inventory: `pyproject.toml`, `setup.py`, `setup.cfg`, requirement files;
- `.github/workflows/ci.yml`
- `.github/workflows/state-gate.yml`
- `.github/workflows/decision-preflight.yml`
- imports used by modules and tests exercised by those workflows;
- complete failing job logs, especially `Install package` output;
- current branch, HEAD, PR head/base/draft/merge state.

Do not inspect unrelated source trees unless clean install or an authorized focused test identifies a concrete in-scope dependency.

## 5. Required Audit

The final report must answer every item separately with evidence path or Git observation, field/step, concrete value, status, and conclusion.

1. Is the branch exactly `agent/terminal-status-propagation-seal-restart-rework-v3`?
2. Is Draft PR #5 still open, unmerged, and the sole review surface?
3. Is the final v5 Decision commit an ancestor of every v5 implementation/evidence commit?
4. Is decision metadata valid with exact v5 IDs, `APPROVED`, `project_governance`, and active `reverse-agent-iteration@v2`?
5. Is `decision_packet.md` task authority and `task_packet.json` background only?
6. Are v4 archive and seal artifacts unchanged?
7. Was Decision content locked before command-plan generation?
8. Does command-plan bind exact IDs, branch, Decision digest, and Decision commit?
9. Was command-plan locked before file mutation, clean install, pytest, closeout, or publication?
10. Do current GitHub jobs show all three failures at `Install package`?
11. Is the exact install error recorded rather than inferred only from the step name?
12. Was missing/invalid packaging metadata confirmed before changing it?
13. Is the packaging fix the smallest standard mechanism needed for editable install?
14. Are dependencies derived from concrete imports and workflow needs?
15. If workflow commands changed, were changes necessary and limited to affected workflows?
16. Was Python 3.13 retained unless incompatibility was proven?
17. Does clean isolated editable installation succeed?
18. Do workflow-imported modules import in the clean environment?
19. Did selected pytest pass and cover changed tests?
20. Were only allowed implementation/test/state paths modified?
21. Were `reverse_agent/*` and unrelated mainlines untouched?
22. Do report aliases and synthesized summaries agree?
23. Do execution log and pytest transcript preserve chronology?
24. Are context and state manifest current after final local gate state?
25. Do live/archive report and pytest aliases match?
26. Does the final local seal bind report, gate, closeout, context, state manifest, round manifest, and command-plan lock?
27. Does local evidence say remote acceptance is pending rather than already accepted?
28. Was final validation commit `S` created and pushed only after local validation?
29. Did the branch remain unchanged after `S`?
30. Were no post-check receipt or evidence commits added?
31. Were prohibited Git operations avoided?
32. Does the execution Agent avoid final `ACCEPTED` before external observation?
33. Is external audit instructed to check all three workflows against exact `S`?
34. Does any failed/nonterminal remote check keep the result `REWORK_REQUIRED` or `BLOCKED`?
35. If all three checks pass for `S`, may external audit return `ACCEPTED` without another branch mutation?

## 6. Implementation Scope

### 6.1 Lock current authority

Before substantive work:

1. verify branch, PR, and HEAD;
2. verify the final v5 Decision commit is present;
3. run decision-lint;
4. generate full gate profile;
5. generate branch-bound command-plan;
6. lock Decision content and command-plan digests;
7. record startup snapshot and round baseline.

Do not reuse v4 locks as v5 authority.

### 6.2 Diagnose install failure

Capture complete `Install package` logs and classify the cause as one of:

```text
missing_packaging_metadata
invalid_packaging_metadata
package_discovery_failure
dependency_resolution_failure
python_313_incompatibility
workflow_command_error
other_evidence_backed_failure
```

Record the exact error in the report. Do not guess solely from the failed step name.

### 6.3 Minimal packaging bootstrap

If missing packaging metadata is confirmed, preferred first fix is:

- add one root `pyproject.toml` using a standard PEP 517 backend;
- configure package discovery for `reverse_agent`;
- declare a Python range compatible with workflow Python 3.13;
- declare only proven runtime dependencies;
- provide narrowly scoped test dependencies only when required.

Do not add multiple packaging systems or release infrastructure.

Workflow files may change only if minimal metadata cannot support the existing install command or clean test dependencies require a justified equivalent command.

### 6.4 Packaging regression coverage

`tests/test_packaging_metadata.py` may verify deterministically:

- required `pyproject.toml` sections;
- discovery of `reverse_agent`;
- declared Python compatibility includes 3.13;
- workflow install commands are consistent;
- no heavy packaging system was introduced.

It must not access the network.

### 6.5 Clean environment validation

Command-plan must include equivalent isolated validation:

```text
python -m venv <temporary-path>
<temporary-python> -m pip install --upgrade pip
<temporary-python> -m pip install -e .
<temporary-python> -c "import reverse_agent.project_gate; import reverse_agent.project_state; import reverse_agent.post_final_evidence_sync; import reverse_agent.decision_preflight"
<temporary-python> -m pytest tests/test_project_gate.py tests/test_project_reports.py tests/test_project_jobs.py tests/test_post_final_evidence_sync.py tests/test_decision_preflight.py tests/test_project_state.py tests/test_packaging_metadata.py -q
```

When a justified test extra is used, record and use the exact form consistently. Do not rely on global environment packages.

### 6.6 Local closeout and seal

After clean install/import/tests pass:

- generate report-summary and execution-log evidence;
- run final-check and current closeout/archive pipeline;
- synchronize context and state manifest;
- archive v5 report/pytest aliases;
- generate final local seal.

Local report must distinguish:

```text
local_implementation_status
local_validation_status
remote_attestation_status
final_acceptance_status
```

Before push, `remote_attestation_status` must be `PENDING_EXTERNAL_OBSERVATION`; the execution Agent must not claim final acceptance.

### 6.7 Final commit and external attestation

Create one final validation commit `S` containing only approved implementation and v5 evidence. Push `S` to the existing branch.

After push:

- do not mutate the branch;
- do not commit a remote receipt;
- do not regenerate project_state artifacts;
- observe GitHub checks read-only;
- preserve `S` as exact attested head.

External acceptance requires:

```text
CI = completed/success
State Gate = completed/success
Decision Preflight = completed/success
PR head SHA = S
observed workflow head SHA = S
no later branch commit
```

The independent auditor returns `ACCEPTED`, `REWORK_REQUIRED`, or `BLOCKED` without another branch commit.

## 7. Tests

Minimum authority setup:

```text
python -m reverse_agent.project_gate decision-lint --state-dir project_state
python -m reverse_agent.project_gate gate-profile --state-dir project_state
python -m reverse_agent.project_gate command-plan --state-dir project_state
```

Required clean validation is the isolated install/import/pytest sequence in Implementation Scope. If `tests/test_packaging_metadata.py` is not created, command-plan must explicitly omit it with an evidence-backed reason.

Regression coverage must prove:

1. clean editable install succeeds;
2. `reverse_agent` is discoverable;
3. workflow-imported modules import;
4. metadata supports workflow Python 3.13;
5. affected workflows use a valid consistent install command;
6. missing/malformed packaging metadata is detected;
7. no unproven dependency is introduced;
8. v4 evidence remains unchanged;
9. local evidence cannot claim remote success;
10. final commit candidate is recorded without predicting future checks;
11. post-check branch mutation is prohibited.

Required evidence:

- `project_state/pytest_result.txt`
- `project_state/codex_execution_report.md`
- `project_state/execution_report.md`
- selected current `project_state/gates/*.json`
- current context/state manifest
- v5 archive and round manifest
- final local evidence seal.

## 8. Stop Conditions

Stop with `BLOCKED` or `REWORK_REQUIRED` if:

- branch/PR is not the approved target;
- final v5 Decision commit is not ancestor of implementation;
- Decision or command-plan locks fail;
- substantive execution occurred before locks and cannot be cleanly restarted;
- exact install error cannot be obtained;
- failure is not packaging-related and requires another mainline;
- fix requires `reverse_agent/*` or another forbidden path;
- dependencies cannot be justified by concrete evidence;
- clean editable install fails after bounded fix;
- Python 3.13 cannot be retained without broader work;
- selected tests fail;
- workflow changes exceed the three named files or alter unrelated behavior;
- report, log, context, state manifest, archive, or seal disagree;
- v4 evidence changes;
- unrelated changes cannot be excluded from explicit staging;
- pushing `S` requires force push, rebase, direct main push, or another prohibited operation;
- any branch commit is added after `S`;
- PR head changes during attestation;
- any of CI, State Gate, or Decision Preflight fails or remains nonterminal for `S`;
- remote results can only be recorded through a self-referential post-check commit;
- merge is required to complete the round.

Do not expand scope to solve a Stop Condition. Preserve evidence and wait for independent audit of exact final commit `S`.
