# QUEUED DECISION CANDIDATE

```json queue_meta
{
  "schema_version": 1,
  "queue_status": "QUEUED_NOT_ACTIVE",
  "candidate_path": "project_state/queued_decisions/decision_20260719_mature_framework_adoption_control_plane_foundation_v1/decision_packet.md",
  "target_active_path": "project_state/decision_packet.md",
  "created_while_active_decision_running": true,
  "current_active_decision_at_creation": "decision_20260716_closeout_final_seal_and_publication_truth_rework_v2",
  "activation_policy": "Do not execute from the queued path. Activate only after the preceding round is independently audited as ACCEPTED or ACCEPTED_WITH_LIMITATIONS, main is synchronized, the candidate branch is rebased or refreshed against that accepted state, and this packet is promoted to project_state/decision_packet.md with a current command-plan generated before substantive execution.",
  "estimated_effort_class": "large_goal_mode_round",
  "effort_target_note": "Designed as an approximately twelve-hour-scale Codex engineering round. Stop when the acceptance criteria are met; do not pad work or expand scope merely to consume time."
}
```

```json decision_meta
{
  "schema_version": 1,
  "decision_id": "decision_20260719_mature_framework_adoption_control_plane_foundation_v1",
  "round_id": "round_20260719_mature_framework_adoption_control_plane_foundation_v1",
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
  "activation_requires_previous_audit": true,
  "allowed_previous_audit_outcomes": ["ACCEPTED", "ACCEPTED_WITH_LIMITATIONS"],
  "required_profile": "full",
  "closeout_required": true,
  "close_round_required": true,
  "pytest_required": true,
  "explicit_pytest_command_required": true,
  "command_plan_precedes_execution_required": true,
  "execution_log_required": true,
  "final_check_required": true,
  "context_packet_sync_required": true,
  "state_manifest_refresh_required": true,
  "publication_allowed": true,
  "publication_requires_user_authorization": true,
  "direct_push_to_main_allowed": false,
  "merge_allowed": false,
  "force_push_allowed": false,
  "rebase_allowed_during_execution": false,
  "workflow_mutation_allowed": false,
  "external_dependency_install_allowed": false,
  "model_api_invocation_allowed": false,
  "runner_dispatch_allowed": false,
  "external_reverse_tool_invocation_allowed": false,
  "destructive_operations_allowed": false,
  "framework_runtime_installation_allowed": false,
  "bmad_installation_allowed": false,
  "langgraph_installation_allowed": false,
  "microsoft_agent_framework_installation_allowed": false,
  "scope_policy": "one_mainline_project_governance_only"
}
```

# DECISION_PACKET

## 1. Goal

Complete one large, bounded `project_governance` foundation round that converts the recent mature-framework discussion into a machine-checkable adoption contract without prematurely installing or dispatching any new framework.

The round must establish a durable boundary between:

```text
BMAD Method
= product discovery, PRD, UX, architecture, epic, story, readiness, review, retrospective

LangGraph
= future Python workflow runtime, checkpoint, interrupt, resume, routing, and node orchestration

GitHub
= issue, branch, pull request, review, CI, commit, release, and publication truth

reverse-agent Trust Layer
= authority, taint, evidence, claim, counterevidence, action provenance, validation, and analysis capsule
```

The round must not merely write another prose roadmap. It must create a tested governance foundation that future BMAD and LangGraph integration decisions can consume.

Required outcomes:

1. inventory current reverse-agent capabilities before recommending replacement;
2. classify each capability as `RETAIN`, `RETAIN_AND_SHRINK`, `ADOPT_EXTERNAL`, `ADAPT`, `DEPRECATE_LATER`, or `DEFER`;
3. define a single source of truth for each category of fact;
4. define a normalized `WorkItemContract` for future Story-driven execution;
5. define risk levels `R0` through `R3` and the authorization required by each level;
6. define a lightweight `ExecutionEnvelope` for ordinary engineering work;
7. define when full `decision_packet` and `command_plan` remain mandatory;
8. add deterministic validators and gate artifacts for the adoption policy;
9. register the mature-framework adoption workstream without making roadmap state an execution authority;
10. preserve the current manual Decision/Codex workflow as a compatibility path;
11. produce exact follow-on decision boundaries for BMAD planning integration, LangGraph shadow mode, GitHub truth adapter, and Trust Layer schema foundation;
12. finish with tests, execution evidence, final-check, context synchronization, state-manifest refresh, closeout, and a bounded publication attempt only if authorized.

The target lifecycle is:

```text
accepted previous governance round
→ current-state and existing-capability audit
→ framework ownership ADR
→ machine-readable adoption manifest
→ WorkItemContract schema and validator
→ risk profile and ExecutionEnvelope schema
→ governance CLI gates
→ roadmap/workstream registration
→ compatibility and migration report
→ targeted tests
→ full tests
→ report and closeout
→ final-check
→ context/state refresh
→ optional branch publication
```

This is intentionally a large engineering round. It must remain one `project_governance` mainline and must not turn into direct framework installation, real Agent dispatch, Web implementation, reverse solving, or external tool integration.

## 2. Current Evidence

- At candidate creation time, the active task authority on `main` is `project_state/decision_packet.md` for `decision_20260716_closeout_final_seal_and_publication_truth_rework_v2`.
- This queued packet is not the current task authority and must not be executed from `project_state/queued_decisions/**`.
- The preceding round is still running at candidate creation time. Activation is blocked until that round is independently audited as `ACCEPTED` or `ACCEPTED_WITH_LIMITATIONS`.
- `project_state/task_packet.json` is old sample-oriented background and must not control this governance round.
- `project_state/context/current_context_packet.json` exists, but at candidate creation time it still references the preceding governance evidence and must be refreshed before activation if the accepted preceding round changed it.
- `project_state/roadmap/workstreams.json` exists and explicitly states that roadmap entries are not execution authority.
- Existing foundations already include project gate hard checks, command-plan authority, execution-log synthesis, report-summary synthesis, run-closeout, round archive, policy lint, prompt consistency, job lifecycle, runner contract foundations, manual Web orchestration foundations, artifact role taxonomy, state lifecycle design, context building, and state-manifest freshness checks.
- The current Runner foundation is deliberately non-dispatching. It must be reused as compatibility evidence and must not be represented as a production Agent runtime.
- Existing `decision_packet` and `command_plan` mechanisms are not to be deleted. Their role is to be narrowed for high-risk work in later rounds, not removed in this round.
- BMAD, LangGraph, Microsoft Agent Framework, MetaGPT, and ChatDev are not currently established as runtime facts in the repository. This round may document adoption boundaries but may not claim successful installation or integration.
- The mature-framework direction is a new governance direction. It must enter the roadmap/workstream registry before implementation rounds.
- The project-specific product core remains the hostile-binary Trust Layer: Binary Evidence Firewall, TrustLevel/TaintLabel, Claim and Counterevidence Graph, Action Provenance Guard, falsification-driven validation, cross-tool disagreement, and reproducible Analysis Capsule.
- Existing User Solve, manual Web orchestration, Runner contract, CI/state gate, reverse-solving, and external-tool workstreams must be mapped, not reimplemented.
- `reverse-agent-iteration@v2` is active in `.codex-skills/registry.json` and is the only generic workflow skill profile authorized for this round.
- Dynamic project facts must come from current project_state and GitHub, not from this queued document or prior chat memory.
- Heavy artifact trees such as full `solve_reports/**` remain out of scope.
- No external reverse tool, unknown binary execution, debugger, emulator, network framework installation, model API, Scheduler, queue, database migration, or real Agent dispatch is allowed.
- A future LangGraph integration must use the mature runtime directly rather than reimplementing checkpoint, interrupt, resume, routing, and generic orchestration.
- A future BMAD integration must use supported installation/customization mechanisms rather than copying and independently maintaining BMAD prompts.
- GitHub must remain the source of truth for branches, commits, pull requests, checks, and release/publication state.
- reverse-agent may retain normalized audit references to GitHub facts but must not create a competing publication-truth store.
- This round is allowed to update governance code, tests, schemas, roadmap/workstream records, architecture/roadmap documentation, current governance artifacts, and the current round archive only after activation.
- This round must explicitly identify where existing functionality already satisfies a proposed requirement. It must not describe existing command-plan, execution-log, report-summary, closeout, policy-lint, prompt-consistency, job lifecycle, runner contract, or manual orchestrator foundations as greenfield work.

## 3. Do Not Do

Do not:

- execute this packet while it remains under `project_state/queued_decisions/**`;
- overwrite the currently running `project_state/decision_packet.md` before the preceding round is complete and audited;
- activate this round if the preceding audit is `REWORK_REQUIRED` or `BLOCKED`;
- combine this round with execution or audit repair from the preceding round;
- install BMAD, LangGraph, Microsoft Agent Framework, MetaGPT, ChatDev, or any other framework;
- run package-manager network commands such as `npm install`, `npx`, `pip install`, `uv add`, or equivalent;
- add framework lock-file changes or dependency metadata;
- implement real Agent dispatch, background workers, queues, schedulers, distributed execution, or autonomous continuation to a next decision;
- change the active task-authority rule during this round;
- remove `decision_packet`, `command_plan`, execution log, report summary, final-check, or closeout;
- make roadmap entries executable;
- create a second current task authority;
- duplicate GitHub issue, pull-request, commit, check, or release truth in project_state;
- modify `.github/workflows/**`;
- modify frontend or Web behavior;
- modify User Solve, solver, harness, sample, training data, or reverse-tool code;
- invoke IDA, Ghidra, debugger, emulator, sandbox, runtime probe, hook, or unknown binary execution;
- read full `solve_reports/**` or `PROJECT_PROGRESS_LOG.txt`;
- create a database or SQLite file;
- perform cleanup apply, deletion, tombstone apply, archive removal, or destructive migration;
- modify `.codex-skills/**` in this round;
- solve the known Skill compatibility/drift issue as a side task;
- create generic framework wrappers that merely rename existing framework APIs without project-specific policy value;
- build a second generic Runner beside the future selected runtime;
- support both LangGraph and Microsoft Agent Framework as simultaneous primary runtimes;
- state that LangGraph is selected because it is universally superior; the ADR must record project-specific reasons and reversal criteria;
- treat BMAD as a runtime or LangGraph as a product-management method;
- treat MetaGPT or ChatDev as required dependencies;
- claim the Trust Layer has been implemented if this round only defines governance contracts;
- broaden the scope because tests expose unrelated failures;
- use `git add -A`;
- force push, merge, rebase during execution, tag, alter secrets, or delete remote branches;
- push directly to `main`;
- publish before required validation passes;
- execute a command absent from the current generated command-plan;
- continue after a Stop Condition is reached.

## 4. Files To Inspect

### Required authority and current-state inputs

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
- `project_state/gates/execution_log.json`
- `project_state/gates/final_gate_result.json`
- `project_state/gates/run_closeout_result.json`
- preceding-round archive and manifest for `round_20260716_closeout_final_seal_and_publication_truth_rework_v2`
- `.codex-skills/registry.json`
- `.codex-skills/reverse-agent-iteration/SKILL.md`

### Required existing-capability inspection

- `reverse_agent/project_gate.py`
- `reverse_agent/project_state.py`
- `reverse_agent/project_state_manifest.py`
- `reverse_agent/project_context.py`
- `reverse_agent/project_jobs.py`
- `reverse_agent/project_runner_contract.py`
- `reverse_agent/project_agent_runner.py`
- `reverse_agent/orchestrator_api.py`
- report-summary and closeout implementation modules discovered from imports or CLI registration
- policy-lint and prompt-consistency implementation modules discovered from CLI registration
- tests covering the files above
- `docs/prompts/README.md`
- relevant existing roadmap and architecture documents only

### Targeted repository searches

Before creating new code, search for all of the following concepts and record reusable foundations:

- `work_item`
- `execution_envelope`
- `risk_profile`
- `risk_level`
- `decision_contract`
- `runner_contract`
- `job lifecycle`
- `command-plan`
- `execution_log`
- `report-summary`
- `run-closeout`
- `policy-lint`
- `prompt-consistency`
- `GitHub publication`
- `source of truth`
- `manual orchestrator`
- `AgentRunner`
- `context packet`
- `workstream registry`

Do not inspect unrelated source trees after the inventory is sufficient.

## 5. Required Audit

The final execution report must answer every item separately with artifact path, field or section name, observed value, and conclusion.

1. Was this queued packet promoted to `project_state/decision_packet.md` before execution?
2. Was the preceding round independently audited as `ACCEPTED` or `ACCEPTED_WITH_LIMITATIONS`?
3. Do the active decision ID and round ID exactly match this packet?
4. Is status `APPROVED`, mainline `project_governance`, and `reverse-agent-iteration@v2` active?
5. Was the current command-plan generated before implementation, pytest, closeout, and publication commands?
6. Does command-plan preserve omitted commands and prohibit framework installation?
7. Was a current-state/context freshness check performed after the preceding round completed?
8. Was the roadmap confirmed as non-execution authority?
9. Was an existing-capability inventory generated before new implementation?
10. Does the inventory explicitly cover project_gate, command-plan, execution-log, report-summary, closeout, policy-lint, prompt-consistency, jobs, runner contract, manual orchestrator, CI/state gate, User Solve, and artifact/state governance?
11. Does every adoption recommendation identify an existing foundation where one exists?
12. Does the framework ownership ADR assign BMAD only to planning/development method responsibilities?
13. Does the ADR assign one future primary runtime and prohibit dual-primary runtime architecture?
14. Does the ADR assign GitHub as code and publication truth?
15. Does the ADR assign reverse-agent only to domain trust, authorization, evidence, and verification responsibilities?
16. Does the ADR include reversal criteria and known risks rather than presenting adoption as irreversible?
17. Is a machine-readable framework adoption manifest present and schema-valid?
18. Does the manifest classify capabilities using only the approved disposition values?
19. Does the manifest identify source-of-truth ownership for each capability?
20. Does the manifest identify compatibility mode and intended deprecation timing where applicable?
21. Is `WorkItemContract` defined as a future engineering work unit rather than a second current authority?
22. Does `WorkItemContract` include goal, scope, non-goals, acceptance criteria, architecture references, dependencies, risk level, and provenance?
23. Are risk levels R0, R1, R2, and R3 defined with deterministic authorization rules?
24. Does R0 remain read-only/planning?
25. Does R1 use a lightweight ExecutionEnvelope rather than a full Decision by default?
26. Do R2 and R3 require explicit human approval?
27. Does R3 preserve full decision and command-plan authority for unknown binaries, debugger/emulator activity, secrets, deletion, and high-privilege execution?
28. Does the ExecutionEnvelope prohibit scope broadening?
29. Does the ExecutionEnvelope have explicit allowed and forbidden operations?
30. Are schemas validated without installing new third-party packages?
31. Are deterministic validators implemented and covered by positive and negative tests?
32. Do CLI gates produce machine-readable artifacts with current decision and round IDs?
33. Do gate artifacts report `BLOCKED` rather than fabricate success when required inputs are missing?
34. Was `project_state/roadmap/workstreams.json` updated without marking roadmap entries as execution authority?
35. Were mature-framework adoption workstreams registered with clear lifecycle status and no false active round?
36. Were future BMAD integration, LangGraph shadow mode, GitHub truth adapter, and Trust Layer schema rounds separated rather than merged into this round?
37. Was current manual Decision/Codex execution preserved as a compatibility path?
38. Was real Runner dispatch left disabled?
39. Were `.codex-skills/**`, `.github/workflows/**`, frontend, User Solve, solver, harness, sample, and reverse-tool code unchanged?
40. Were no package-manager installation commands executed?
41. Were no model APIs or external reverse tools invoked?
42. Were no database, cleanup apply, deletion, or migration operations performed?
43. Did targeted tests run using explicit commands?
44. Did the full project test suite run unless a documented Stop Condition prevented it?
45. Does `pytest_result.txt` contain the actual command, result, and counts?
46. Does execution_log preserve actual chronology?
47. Does the final report distinguish implemented governance foundation from future framework integration?
48. Does report-summary agree with the detailed report and pytest evidence?
49. Did final-check pass on current artifacts?
50. Was the context packet synchronized after final-check as required by the current closeout policy?
51. Was the state manifest refreshed after the terminal artifact set was complete?
52. Was the round archive created with the exact current decision and round IDs?
53. If publication occurred, was it performed only on the allowed branch after validation?
54. If publication did not occur, is the report explicit and factually supported?
55. Were all Stop Conditions evaluated and reported?

## 6. Implementation Scope

### 6.1 Capability inventory and adoption baseline

Create a machine-readable and human-readable inventory that maps current capabilities to future ownership.

Required outputs:

- `project_state/gates/framework_capability_inventory.json`
- `docs/architecture/mature_framework_capability_inventory.md`

The inventory must include at least:

- current implementation path;
- current maturity;
- current authority role;
- duplicate-risk assessment;
- target owner: BMAD, LangGraph, GitHub, reverse-agent Trust Layer, compatibility-only, or deferred;
- disposition: `RETAIN`, `RETAIN_AND_SHRINK`, `ADOPT_EXTERNAL`, `ADAPT`, `DEPRECATE_LATER`, or `DEFER`;
- migration prerequisite;
- compatibility requirement;
- evidence references.

### 6.2 Architecture Decision Record

Create:

- `docs/architecture/adr_mature_framework_adoption_and_authority_boundaries.md`

The ADR must include:

- context and problem statement;
- alternatives considered;
- why a layered adoption is selected;
- BMAD responsibility boundary;
- LangGraph responsibility boundary;
- Microsoft Agent Framework comparison and reevaluation trigger;
- MetaGPT/ChatDev borrowing boundary;
- GitHub fact ownership;
- reverse-agent Trust Layer ownership;
- Decision/Command Plan retained role;
- compatibility strategy;
- migration sequence;
- rollback/reversal criteria;
- known risks;
- explicit non-goals.

Do not claim external framework installation.

### 6.3 Machine-readable framework adoption manifest

Create a schema and current manifest:

- `project_state/schemas/framework_adoption_manifest.schema.json`
- `project_state/framework_adoption_manifest.json`

The manifest must include:

- schema version;
- decision and round IDs;
- selected planning method;
- selected future primary runtime;
- alternative runtime and reevaluation criteria;
- GitHub truth domains;
- reverse-agent truth domains;
- capability dispositions;
- prohibited duplicate implementations;
- compatibility mode;
- follow-on workstreams;
- freshness metadata;
- evidence references.

### 6.4 WorkItemContract foundation

Create:

- `project_state/schemas/work_item_contract.schema.json`
- `reverse_agent/project_work_items.py`
- `tests/test_project_work_items.py`
- `docs/architecture/work_item_contract.md`

The implementation must provide deterministic functions to:

- validate a WorkItemContract payload;
- normalize scope paths;
- validate required fields;
- reject duplicate or contradictory scope/non-goal entries;
- validate architecture references;
- validate dependency declarations;
- validate acceptance criteria;
- validate risk-level values;
- produce a gate result payload;
- avoid dispatching any Agent or command.

The schema must include:

- `work_item_id`;
- `source_type`;
- `source_reference`;
- `goal`;
- `scope`;
- `non_goals`;
- `acceptance_criteria`;
- `architecture_references`;
- `dependencies`;
- `risk_level`;
- `requested_capabilities`;
- `forbidden_operations`;
- `provenance`;
- `status`.

### 6.5 Risk profile and ExecutionEnvelope foundation

Create:

- `project_state/schemas/risk_profile.schema.json`
- `project_state/schemas/execution_envelope.schema.json`
- `reverse_agent/project_risk_profiles.py`
- `tests/test_project_risk_profiles.py`
- `docs/architecture/risk_profiles_and_execution_envelopes.md`

Required risk semantics:

```text
R0 = planning, research, read-only inspection; no Decision required
R1 = bounded source/document/test changes; lightweight ExecutionEnvelope
R2 = dependency, network, Git publication, workflow/policy, or data migration proposal; explicit approval and compact Decision
R3 = unknown binary execution, debugger/emulator, secrets, deletion, destructive cleanup, high privilege, or external side effects; full Decision + Command Plan + human approval
```

Validators must reject:

- unknown risk levels;
- R0 with write permissions;
- R1 with network, push, deletion, secrets, or unknown-binary execution;
- R2/R3 without required approval metadata;
- envelopes that broaden WorkItem scope;
- envelopes that allow operations explicitly forbidden by the WorkItem;
- envelopes with absolute or parent-traversal write paths;
- envelopes that claim execution authority while remaining a proposal.

### 6.6 Governance gates and artifacts

Extend existing governance code rather than creating an unrelated gate framework.

Allowed source updates:

- `reverse_agent/project_gate.py`
- `reverse_agent/project_state.py` only if necessary for current artifact metadata conventions
- new modules listed in this packet

Add deterministic CLI/gate support for:

- `framework-adoption-check`
- `work-item-lint`
- `risk-profile-check`
- `execution-envelope-check`

Required artifacts:

- `project_state/gates/framework_adoption_result.json`
- `project_state/gates/work_item_contract_result.json`
- `project_state/gates/risk_profile_result.json`
- `project_state/gates/execution_envelope_result.json`
- `project_state/gates/framework_adoption_snapshot.json`

Each artifact must include:

- schema version;
- artifact name and path;
- decision ID;
- round ID;
- mainline;
- generated timestamp;
- inputs consumed;
- input digests where available;
- validation status;
- errors and warnings;
- generated artifacts;
- explicit non-execution proof.

### 6.7 Roadmap and workstream registration

Update:

- `project_state/roadmap/workstreams.json`
- `docs/roadmap/mature_framework_adoption_migration_plan.md`

Register or normalize the following workstreams without activating them:

1. `mature_framework_adoption_control_plane`
   - family: `project_governance`
   - target status after successful closeout: `ACCEPTED`

2. `bmad_planning_layer_integration`
   - family: `engineering_branch`
   - target status: `READY_FOR_DECISION`
   - no installation in this round

3. `langgraph_shadow_runtime`
   - family: `engineering_branch`
   - target status: `ROADMAP_ACCEPTED`
   - must remain non-dispatching in its first round

4. `github_truth_adapter`
   - family: `project_governance`
   - target status: `ROADMAP_ACCEPTED`

5. `hostile_binary_trust_layer`
   - family: `engineering_branch`
   - target status: `ROADMAP_ACCEPTED`

Roadmap policy must remain:

```text
roadmap entry != execution authority
only project_state/decision_packet.md controls the active round
```

### 6.8 Compatibility and migration report

Create:

- `docs/architecture/current_to_target_control_plane_migration.md`
- `project_state/gates/framework_migration_readiness.json`

The report must map:

```text
current manual chat → Decision → Codex → audit
```

into staged compatibility:

```text
Stage 0: current manual flow preserved
Stage 1: BMAD planning artifacts feed a compatibility adapter
Stage 2: WorkItemContract produces a Decision draft, still manually approved
Stage 3: LangGraph shadow mode reads current contracts but cannot execute
Stage 4: R0/R1 controlled local execution
Stage 5: Draft PR and CI integration
Stage 6: R2/R3 high-risk actions through Decision, Command Plan, provenance, and HITL
```

The readiness artifact must remain `NOT_READY_FOR_RUNTIME_INSTALL` unless all governance prerequisites are satisfied. This round must not mark BMAD or LangGraph as installed.

### 6.9 Tests

Add or update only governance-related tests:

- `tests/test_project_work_items.py`
- `tests/test_project_risk_profiles.py`
- `tests/test_project_framework_adoption.py`
- `tests/test_project_gate.py`
- `tests/test_project_state.py` only if required by new metadata
- `tests/test_project_reports.py` only if required by new report fields

Tests must cover:

- valid and invalid adoption manifests;
- duplicate capability prevention;
- source-of-truth ownership conflicts;
- valid R0/R1/R2/R3 profiles;
- escalation rules;
- WorkItem scope/non-goal conflicts;
- envelope scope broadening;
- forbidden operation inheritance;
- unsafe path rejection;
- missing approval metadata;
- current decision/round mismatch;
- missing input artifacts;
- machine-readable gate output;
- non-dispatch proof;
- compatibility with existing runner contract and job foundations;
- roadmap remains non-authoritative;
- current manual flow remains valid.

### 6.10 Reports and closeout

Update current activated-round artifacts according to existing governance conventions:

- `project_state/pytest_result.txt`
- `project_state/codex_execution_report.md`
- `project_state/execution_report.md`
- `project_state/gates/execution_log.json`
- `project_state/gates/report_summary_synthesis.json`
- `project_state/gates/final_gate_result.json`
- `project_state/gates/run_closeout_result.json`
- `project_state/context/current_context_packet.json`
- `project_state/state_manifest.json`
- `project_state/rounds/round_20260719_mature_framework_adoption_control_plane_foundation_v1/**`

The report must not call the framework integration complete. The correct result is a tested adoption/control-plane foundation and a set of ready follow-on decisions.

### 6.11 Allowed mutation scope

After activation, allowed source and documentation paths are limited to:

- `reverse_agent/project_gate.py`
- `reverse_agent/project_state.py` only when necessary
- `reverse_agent/project_work_items.py`
- `reverse_agent/project_risk_profiles.py`
- `reverse_agent/project_framework_adoption.py`
- `tests/test_project_work_items.py`
- `tests/test_project_risk_profiles.py`
- `tests/test_project_framework_adoption.py`
- `tests/test_project_gate.py`
- `tests/test_project_state.py` only when necessary
- `tests/test_project_reports.py` only when necessary
- `docs/architecture/mature_framework_capability_inventory.md`
- `docs/architecture/adr_mature_framework_adoption_and_authority_boundaries.md`
- `docs/architecture/work_item_contract.md`
- `docs/architecture/risk_profiles_and_execution_envelopes.md`
- `docs/architecture/current_to_target_control_plane_migration.md`
- `docs/roadmap/mature_framework_adoption_migration_plan.md`
- `project_state/framework_adoption_manifest.json`
- `project_state/schemas/framework_adoption_manifest.schema.json`
- `project_state/schemas/work_item_contract.schema.json`
- `project_state/schemas/risk_profile.schema.json`
- `project_state/schemas/execution_envelope.schema.json`
- `project_state/roadmap/workstreams.json`
- current governance gate, report, context, state-manifest, and current-round archive artifacts required by closeout

Any additional source path requires a Stop Condition and a new Decision, not silent expansion.

## 7. Tests

The command-plan must be generated and digest-locked before running any test command.

Minimum required test sequence:

1. Decision and profile validation:

```powershell
python -m reverse_agent.project_gate decision-lint
python -m reverse_agent.project_gate gate-profile
python -m reverse_agent.project_gate command-plan
```

2. New targeted unit tests:

```powershell
python -m pytest tests/test_project_work_items.py tests/test_project_risk_profiles.py tests/test_project_framework_adoption.py -q
```

3. Existing governance regression tests:

```powershell
python -m pytest tests/test_project_gate.py tests/test_project_state.py tests/test_project_reports.py -q
```

4. New deterministic gates using fixture or current round inputs defined by implementation:

```powershell
python -m reverse_agent.project_gate framework-adoption-check
python -m reverse_agent.project_gate work-item-lint
python -m reverse_agent.project_gate risk-profile-check
python -m reverse_agent.project_gate execution-envelope-check
```

5. Full test suite:

```powershell
python -m pytest -q
```

6. Closeout sequence using only commands authorized by the current command-plan:

```text
report finalization
→ report-summary synthesis
→ run-closeout
→ close-round/archive refresh
→ final-check
→ post-final context sync
→ state-manifest refresh
→ terminal evidence completion
```

7. Optional publication checks only if current user authorization and command-plan explicitly permit them:

```text
explicit-path staging only
→ commit on allowed short-lived branch
→ push branch
→ optional Draft PR
```

The actual command strings must match repository CLI syntax discovered during implementation. Do not invent a passing gate by writing artifact files manually when the CLI or validator fails.

`project_state/pytest_result.txt` must record:

- exact commands;
- start/end or observed timestamps according to existing policy;
- exit codes;
- passed/failed/skipped counts;
- whether the full suite ran;
- any limitation or Stop Condition.

## 8. Stop Conditions

Stop immediately and report `BLOCKED` if any of the following occurs:

1. this packet has not been promoted from the queued path to `project_state/decision_packet.md`;
2. the preceding round has not completed;
3. the preceding independent audit is not `ACCEPTED` or `ACCEPTED_WITH_LIMITATIONS`;
4. current `main` or the execution branch does not contain the accepted preceding-round evidence;
5. active decision ID, round ID, mainline, or skill profile does not match this packet;
6. current command-plan is missing, stale, generated after substantive execution, or mismatched;
7. context packet or state manifest is stale in a way that prevents a trustworthy current baseline;
8. an existing capability materially overlaps proposed new code and no reuse/adaptation design is provided;
9. implementation requires BMAD, LangGraph, Microsoft Agent Framework, MetaGPT, ChatDev, or other package installation;
10. implementation requires network access;
11. implementation requires `.github/workflows/**` changes;
12. implementation requires `.codex-skills/**` changes;
13. implementation requires frontend, User Solve, solver, harness, sample, training-data, or reverse-tool changes;
14. implementation requires real Runner dispatch, subprocess orchestration beyond authorized deterministic local commands, Scheduler, queue, or background service;
15. implementation requires database creation or migration;
16. implementation requires deletion, cleanup apply, tombstone apply, or destructive migration;
17. roadmap would become execution authority;
18. a second primary runtime is introduced;
19. GitHub publication facts would be duplicated as an independent project_state truth source;
20. WorkItemContract or ExecutionEnvelope would become an alternative current task authority;
21. R2 or R3 operations can occur without explicit human approval;
22. an unknown binary, debugger, emulator, external reverse tool, model API, or secret is accessed;
23. required tests fail and the fix requires files outside allowed scope;
24. the full test suite reveals an unrelated failure that cannot be resolved without crossing scope;
25. execution log chronology cannot be established truthfully;
26. report-summary or final-check disagrees with observed evidence;
27. final artifacts change after the terminal validation boundary without re-running the required closeout sequence;
28. publication would require direct main push, force push, merge, rebase, workflow mutation, secret mutation, tag mutation, or remote branch deletion;
29. any command is absent from command-plan or listed in omitted commands;
30. the work expands merely to meet the nominal effort target after acceptance criteria are already satisfied.

If a Stop Condition is triggered:

- do not silently narrow or broaden the task;
- preserve all truthful partial evidence;
- write the required reports with outcome `BLOCKED`;
- identify the exact stopping condition, artifact, observed value, and required follow-up Decision;
- do not generate or execute the next round automatically.
