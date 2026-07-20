```json decision_meta
{
  "schema_version": 1,
  "decision_id": "decision_20260720_legacy_control_plane_transition_disposition_v1",
  "round_id": "round_20260720_legacy_control_plane_transition_disposition_v1",
  "based_on_state_build_id": "state_20260618_134029_d6bd033d2532",
  "based_on_state_digest": "d6bd033d25324345cfd8ada0ac65db42bc86eb5017f3ffc92906fcd8b71cacb5",
  "status": "APPROVED",
  "mainline": "project_governance",
  "skill_profiles": ["reverse-agent-iteration@v2"]
}
```

```json decision_contract
{
  "follows_last_decision_id": "decision_20260720_ci_preflight_bootstrap_order_rework_v10",
  "follows_last_round_id": "round_20260720_ci_preflight_bootstrap_order_rework_v10",
  "previous_audit_outcome": "REWORK_REQUIRED",
  "transition_authorized_by_user": true,
  "legacy_micro_rework_prohibited": true,
  "pr5_disposition": "FROZEN_MIGRATION_EVIDENCE",
  "pr5_audited_head_sha": "6a2867467c90cf37929787be3ba6061fcbb81312",
  "pr6_role": "QUEUED_PLAN_STORAGE_ONLY",
  "required_profile": "full",
  "fresh_execution_branch_from_current_main_required": true,
  "queued_packet_must_be_promoted_before_execution": true,
  "command_plan_precedes_substantive_execution": true,
  "execution_log_required": true,
  "pytest_required": true,
  "local_final_check_allowed": true,
  "local_closeout_allowed": true,
  "remote_attestation_required": false,
  "framework_installation_allowed": false,
  "workflow_mutation_allowed": false,
  "product_source_mutation_allowed": false,
  "runner_dispatch_allowed": false,
  "model_api_invocation_allowed": false,
  "external_reverse_tool_invocation_allowed": false,
  "destructive_operations_allowed": false,
  "merge_allowed": false,
  "direct_push_to_main_allowed": false,
  "force_push_allowed": false,
  "scope_policy": "one_mainline_project_governance_transition_disposition_only"
}
```

# DECISION_PACKET

## 1. Goal

Complete one bounded `project_governance` transition-disposition round that ends the serial repair cycle around the legacy control plane and establishes a clean, evidence-backed migration baseline.

This round does not repair v10 and does not install BMAD, LangGraph, Microsoft Agent Framework, MetaGPT, or ChatDev. It decides what to keep, what to adapt, what to replace, what to archive, and where the new architecture should begin.

Required outcomes:

1. freeze PR #5 as read-only migration evidence at exact head `6a2867467c90cf37929787be3ba6061fcbb81312`;
2. compare PR #5 against current `main` and divide its changes into independent capability groups;
3. identify which capabilities already exist on `main`, which exist only in PR #5, and which are merely legacy control-plane self-maintenance;
4. classify every material capability using exactly one primary disposition:
   - `KEEP_AS_IS`
   - `KEEP_AND_ADAPT`
   - `REPLACE_WITH_BMAD`
   - `REPLACE_WITH_LANGGRAPH`
   - `REPLACE_WITH_GITHUB`
   - `MOVE_TO_TRUST_LAYER`
   - `ARCHIVE_ONLY`
   - `DROP`
5. define the source of truth for product planning, engineering work items, runtime state, Git/CI/publication facts, high-risk authorization, binary-analysis evidence, and audit history;
6. decide whether the new architecture should start from current `main`, PR #5, or a selective integration baseline;
7. produce a file-level selective migration manifest for anything recommended to keep from PR #5;
8. refresh the framework-adoption workstream and split it into ordered follow-on workstreams;
9. define the first implementation round after disposition, without executing that round;
10. preserve the manual Decision/Codex path as a temporary compatibility path, but explicitly prohibit further v11/v12-style legacy closeout micro-rework;
11. produce schema-valid machine-readable artifacts and targeted tests;
12. finish with a truthful local report and local closeout. Remote State Gate success is not an acceptance condition for this planning/disposition round.

Target sequence:

```text
freeze PR #5
→ compare PR #5 with current main
→ inventory independent capabilities
→ classify keep/adapt/replace/archive/drop
→ assign authoritative systems
→ select clean migration baseline
→ refresh workstreams
→ define follow-on decision sequence
→ validate artifacts
→ local report and closeout
```

## 2. Current Evidence

- The current strategic direction is user-authorized: stop spending rounds on serial legacy closeout repair and move to a structured migration using mature frameworks where appropriate.
- v10 was independently audited as `REWORK_REQUIRED`, not accepted.
- v10 exact head `6a2867467c90cf37929787be3ba6061fcbb81312` produced:
  - CI: success;
  - Decision Preflight: success;
  - State Gate: failure at `Project gate report summary`.
- The v10 functional Workflow change is narrow and potentially reusable: two preflight commands add `--allow-consumed`.
- The v10 committed execution report omitted the two actual Workflow files from `files_changed`, so clean-checkout report synthesis disagreed with Git commit truth.
- Several Required Audit answers were generic templates rather than question-specific evidence.
- These facts show that parts of the legacy control plane are useful, while its report/seal/remote-attestation composition is too self-referential to justify more micro-repair rounds before a planned architecture replacement.
- PR #5 is large, open, Draft, and contains many rounds of governance work. It must not be treated as one indivisible change set.
- PR #6 currently stores an older queued mature-framework plan whose predecessor acceptance condition is no longer valid. This packet supersedes that candidate.
- `project_state/decision_packet.md` remains the only active task authority after promotion. `task_packet.json`, roadmap entries, PR descriptions, and queued packets remain background or planning inputs.
- `project_state/current_state.json` is old sample-oriented state and cannot be assumed to describe current governance work.
- `project_state/context/current_context_packet.json` and `state_manifest.json` must be checked for freshness at activation; stale content cannot override GitHub and current live artifacts.
- Existing foundations must be inventoried before replacement recommendations. At minimum inspect:
  - project gate and Decision lint;
  - command-plan and command authority;
  - execution log;
  - report summary;
  - final-check, closeout, round archive, and seal;
  - policy lint and prompt consistency;
  - job lifecycle and Runner contract;
  - manual orchestrator and User Solve foundations;
  - CI/state gate and Decision Preflight;
  - state manifest, context packet, artifact index, and negative results;
  - evidence, validation, tool-action, and analysis-capsule concepts.
- Mature frameworks are layered rather than interchangeable:
  - BMAD is the candidate SDLC/planning method;
  - LangGraph is the candidate primary Python workflow runtime;
  - GitHub is the code/review/CI/publication fact source;
  - reverse-agent retains domain-specific Trust Layer responsibilities.
- MetaGPT and ChatDev are reference designs, not planned primary dependencies.
- Microsoft Agent Framework remains a future alternative or adapter candidate, not a simultaneous primary runtime.
- Existing full `decision_packet` and `command_plan` mechanisms may remain for R2/R3 high-risk work, but their future scope must be narrowed rather than assumed universal.
- The current Runner is non-dispatching and must not be presented as an implemented production runtime.
- The current round permits read-only inspection of PR #5 and current `main`, governance documents, schemas, and targeted tests.
- No runtime probe, reverse tool, debugger, emulator, unknown binary execution, external model call, framework installation, database migration, cleanup apply, or destructive operation is allowed.
- Full `solve_reports/**` and `PROJECT_PROGRESS_LOG.txt` remain excluded.
- Closeout is allowed locally after all disposition artifacts and tests are current. A legacy remote State Gate failure must be recorded as a limitation and must not trigger another legacy repair Decision.
- This round does not duplicate command-plan, execution-log, report-summary, closeout, policy-lint, prompt-consistency, Runner, or CI capabilities. It classifies their future disposition.

## 3. Do Not Do

Do not:

- execute this packet while it remains under `project_state/queued_decisions/**`;
- execute directly from PR #6 or treat PR #6 as current authority;
- continue v10 or create v11/v12 legacy closeout repair rounds;
- modify, merge, close, rebase, force-push, or mark PR #5 ready for review;
- modify PR #5 files or rewrite its round evidence;
- merge PR #6;
- install BMAD, LangGraph, Microsoft Agent Framework, MetaGPT, ChatDev, or any dependency;
- run package-manager network installation commands;
- implement WorkItem runtime, ExecutionEnvelope runtime, Agent dispatch, checkpointing, scheduling, queueing, or background workers;
- modify `.github/workflows/**`;
- modify production files under `reverse_agent/**`;
- modify frontend, User Solve, solver, harness, sample, training-data, tool-adapter, debugger, sandbox, or reverse-analysis code;
- create a database or SQLite index;
- delete, compact, archive-remove, tombstone, or cleanup-apply any state;
- treat all PR #5 content as required or all as disposable;
- claim a capability exists without a file, test, artifact, or Git diff reference;
- classify the same capability into multiple primary disposition categories;
- assign Git publication truth to project_state;
- assign binary trust semantics to BMAD, LangGraph, or GitHub;
- assign generic workflow checkpoint/retry/orchestration to custom reverse-agent code without a documented domain-specific reason;
- copy BMAD prompts into an independently maintained custom framework;
- choose both LangGraph and Microsoft Agent Framework as simultaneous primary runtimes;
- create generic wrappers that only rename external framework APIs;
- convert roadmap entries into execution authority;
- use `git add -A`;
- push directly to `main`, merge, tag, force-push, or alter secrets;
- read complete `solve_reports/**` or `PROJECT_PROGRESS_LOG.txt`;
- expand scope because unrelated tests or stale artifacts fail;
- repair a failing legacy remote State Gate as part of this round;
- end with vague language such as “continue improving.”

## 4. Files To Inspect

Required current state after activation:

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
project_state/gates/execution_log.json
project_state/gates/report_summary_synthesis.json
project_state/gates/final_gate_result.json
project_state/gates/run_closeout_result.json
.codex-skills/registry.json
```

Required Git comparisons:

```text
current main
PR #5 exact head 6a2867467c90cf37929787be3ba6061fcbb81312
PR #6 queued-plan branch
full changed-file list for PR #5
per-file diff/statistics grouped by capability
commit history sufficient to identify capability boundaries
```

Required capability implementation areas, only as needed:

```text
reverse_agent/project_gate.py
reverse_agent/project_state.py
reverse_agent/project_state_manifest.py
reverse_agent/project_context.py
reverse_agent/project_jobs.py
reverse_agent/project_runner_contract.py
reverse_agent/project_agent_runner.py
reverse_agent/orchestrator_api.py
reverse_agent/decision_preflight.py
User Solve modules discovered from repository search
Evidence/validation/tool-action modules discovered from repository search
related focused tests
docs/prompts/README.md
relevant architecture and roadmap documents
```

Targeted searches:

```text
command-plan
execution_log
report-summary
final-check
run-closeout
final-evidence-seal
policy-lint
prompt-consistency
job lifecycle
runner contract
manual orchestrator
User Solve
WorkItem
ExecutionEnvelope
risk level
checkpoint
interrupt
resume
GitHub publication
source of truth
EvidenceUnit
Claim
Counterevidence
ToolAction
AnalysisCapsule
```

Do not inspect unrelated trees after the evidence is sufficient.

## 5. Required Audit

The final report must answer each item separately with exact artifact/file path, observed value, and conclusion:

1. Was this packet promoted to `project_state/decision_packet.md` before execution?
2. Was execution started from a fresh branch based on current `main` rather than PR #5 or PR #6?
3. Was v10 recorded as `REWORK_REQUIRED` and strategically superseded rather than accepted?
4. Did PR #5 remain unchanged and frozen at the audited head?
5. Was PR #5 compared against the activation-time `main`?
6. Does the capability inventory cover every material changed file in PR #5?
7. Are capabilities grouped by function rather than by historical round alone?
8. Does every capability identify implementation files, tests, artifacts, dependencies, and current-main overlap?
9. Does every capability have exactly one primary disposition category?
10. Are useful v10 Workflow changes classified independently from legacy report/closeout machinery?
11. Are existing command-plan, execution-log, report-summary, closeout, policy-lint, prompt-consistency, jobs, Runner, User Solve, CI, context, manifest, and evidence capabilities explicitly inventoried?
12. Does the authority matrix assign BMAD only to SDLC/planning responsibilities?
13. Does it assign one primary runtime candidate and prohibit dual-primary runtime architecture?
14. Does it assign GitHub as the source of truth for branch, commit, PR, review, CI, merge, and release facts?
15. Does it reserve high-risk authorization and binary-analysis trust semantics for reverse-agent?
16. Does the migration disposition identify capabilities that are self-maintenance of the legacy control plane?
17. Does the selective migration manifest provide file-level keep/adapt/archive/drop instructions?
18. Does the baseline recommendation explicitly choose `CURRENT_MAIN`, `PR5`, or `SELECTIVE_INTEGRATION_BASELINE` and justify the choice?
19. Does the baseline recommendation include rollback and compatibility implications?
20. Does the transition packet define the first follow-on implementation Decision with exact scope and non-goals?
21. Are roadmap/workstream entries updated without becoming execution authority?
22. Were no frameworks installed and no product/runtime code changed?
23. Were targeted tests actually run and recorded in `pytest_result.txt`?
24. Does the final report list actual changed files based on Git diff rather than a hand-written incomplete list?
25. Are all Required Audit answers question-specific rather than template repetition?
26. Did local final-check and closeout run, or was any legacy-only failure explicitly recorded without spawning another repair round?
27. Was no remote State Gate success claimed or required?
28. Is the next action a concrete implementation Decision rather than “continue improving”?

## 6. Implementation Scope

This round is documentation, registry, schema, and evidence work only.

Required new or updated outputs:

```text
docs/architecture/legacy-control-plane-disposition.md
docs/architecture/framework-authority-matrix.md
docs/roadmap/framework-transition-phases.md

project_state/context/framework_transition_packet.json
project_state/roadmap/workstreams.json
project_state/gates/pr5_capability_inventory.json
project_state/gates/pr5_migration_disposition.json
project_state/gates/framework_authority_matrix.json
project_state/gates/transition_baseline_recommendation.json
project_state/gates/selective_migration_manifest.json

project_state/schemas/pr5_capability_inventory.schema.json
project_state/schemas/pr5_migration_disposition.schema.json
project_state/schemas/framework_transition_packet.schema.json

tests/test_framework_transition_artifacts.py
```

After activation, the normal current-round evidence may also be updated:

```text
project_state/decision_packet.md
project_state/pytest_result.txt
project_state/codex_execution_report.md
project_state/execution_report.md
project_state/state_manifest.json
project_state/context/current_context_packet.json
project_state/gates/command_plan.json
project_state/gates/execution_log.json
project_state/gates/report_summary_synthesis.json
project_state/gates/final_gate_result.json
project_state/gates/run_closeout_result.json
project_state/rounds/round_20260720_legacy_control_plane_transition_disposition_v1/*
```

Artifact requirements:

### `pr5_capability_inventory.json`

Each capability record must contain:

```text
capability_id
name
category
summary
pr5_files
main_files
pr5_only_files
tests
artifacts
dependencies
current_main_overlap
legacy_self_maintenance
risk_if_dropped
evidence_refs
```

### `pr5_migration_disposition.json`

Each record must contain:

```text
capability_id
primary_disposition
rationale
target_owner
files_to_keep
files_to_adapt
files_to_archive
files_to_drop
compatibility_requirement
follow_on_workstream
acceptance_evidence
```

### `framework_authority_matrix.json`

Must assign exactly one primary authority for each fact class:

```text
product_discovery_and_prd
architecture_and_story_definition
engineering_work_item
workflow_runtime_state
checkpoint_and_resume
branch_commit_pr_review
ci_and_release_truth
high_risk_authorization
command_allowlist
binary_observation
claim_and_counterevidence
validation_status
audit_history
```

### `transition_baseline_recommendation.json`

Must choose one:

```text
CURRENT_MAIN
PR5
SELECTIVE_INTEGRATION_BASELINE
```

The recommendation must include rejected alternatives, migration cost, rollback path, and the exact first implementation round.

### Workstream update

Register ordered workstreams at minimum:

```text
legacy-control-plane-disposition
selective-capability-integration
bmad-planning-adapter
langgraph-shadow-runtime
github-truth-adapter
trust-layer-schema-foundation
web-workbench-transition
```

Only the disposition workstream may be marked active during this round.

No file under `reverse_agent/**` or `.github/workflows/**` may be modified.

## 7. Tests

Before substantive work, generate and obey the current command-plan.

Required targeted checks, when present in the generated command-plan:

```powershell
python -m reverse_agent.project_gate decision-lint --state-dir project_state
python -m reverse_agent.project_gate policy-lint --state-dir project_state
python -m reverse_agent.project_gate prompt-consistency --state-dir project_state
python -m pytest tests/test_framework_transition_artifacts.py -q
python -m pytest tests/test_framework_transition_artifacts.py tests/test_project_state.py tests/test_project_context.py -q
python -m reverse_agent.project_gate report-summary --state-dir project_state
python -m reverse_agent.project_gate execution-log --state-dir project_state
python -m reverse_agent.project_gate final-check --state-dir project_state
python -m reverse_agent.project_gate run-closeout --state-dir project_state --round-id round_20260720_legacy_control_plane_transition_disposition_v1
python -m reverse_agent.project_gate close-round --state-dir project_state --round-id round_20260720_legacy_control_plane_transition_disposition_v1
git diff --check
```

The new test must validate:

- all required JSON artifacts exist;
- all schemas parse;
- every inventory record has a unique `capability_id`;
- every capability has exactly one primary disposition;
- all referenced files exist on `main`, PR #5, or are explicitly marked historical;
- authority matrix fact classes have exactly one primary owner;
- baseline recommendation uses an allowed enum;
- selective migration manifest references known capability IDs;
- workstream ordering is acyclic;
- PR #5 audited head is recorded exactly;
- no artifact claims v10 `ACCEPTED`;
- no artifact authorizes framework installation or legacy micro-rework.

Do not run the entire legacy 1500-test control-plane suite unless a changed file or generated command-plan explicitly requires it.

Write all real test output to `project_state/pytest_result.txt`.

## 8. Stop Conditions

Stop and report `BLOCKED` without expanding scope if:

- PR #5 head no longer equals the audited frozen head and no new independent audit exists;
- PR #5 cannot be compared to activation-time `main`;
- material PR #5 files cannot be assigned to a capability group;
- a capability cannot be classified without modifying product code;
- the round begins repairing v10 report-summary, final-seal, closeout, or remote State Gate behavior;
- a framework installation or runtime implementation becomes necessary;
- `.github/workflows/**` or `reverse_agent/**` would need modification;
- completing the inventory would require full `solve_reports/**` or destructive state operations;
- the migration baseline cannot be chosen among the three allowed values;
- multiple primary authorities are assigned to one fact class;
- the workstream graph contains a cycle or activates more than one mainline;
- tests fail and repair requires leaving the allowed file set;
- Required Audit answers are generated as repeated templates rather than evidence-specific conclusions;
- the final recommendation is vague or does not identify the first implementation Decision;
- a legacy remote State Gate failure is treated as a reason to create another micro-rework round.

On successful completion, stop after producing the disposition artifacts and the exact next implementation Decision boundary. Do not automatically begin BMAD or LangGraph integration.
