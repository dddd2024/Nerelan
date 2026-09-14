# Explicit project-state rounds only

Read this reference only when the active task selects the legacy/project-state round contract. It is not the startup order for ordinary R1 engineering and does not grant sample execution.

## Authority and evidence

Resolve the active APPROVED immutable Decision and generated plan first for Path B. The selected `task_packet.json`, `current_state.json`, `artifact_index.json`, `negative_results.json`, execution report and pytest result are evidence/background only. Suggested `task_packet.task` or `derived_task` never overrides active authority. Read only the task-relevant files under `project_state/`; there is no mandatory seven-file replay.

Use `artifact_index.latest_artifacts_v2` to distinguish current, stale and missing artifacts before using their contents. Do not scan full `solve_reports/` or inspect the newest harness run merely because it exists. Do not read `PROJECT_PROGRESS_LOG.txt` unless the current authority permits it and compact state is unusable, `model_gate.context_level=3` requests broader context, an explicit strategic retrospective needs it, or a state conflict requires historical wording. Record why any bounded historical read was necessary; stale artifacts remain historical evidence.

## Scope

An `engineering_branch` round is infrastructure, docs, skills, reporting, lint, sync or tests. Do not advance sample solving, runtime probes or candidate search without explicit authority. A separately authorized `reverse_solving` round uses its sample profile, fresh state and negative results; do not mix the two.

For an authorized solving round, identify the evidence-backed bottleneck rather than follow a fixed recipe: instrumentation, candidate generation/provenance, gate/filter diagnostics, refinement, the existing SMT path, validation consistency or reporting. Do not widen blind brute force without fresh evidence invalidating structured routes and explicit Decision authorization. Keep dynamic candidate values, thresholds, run names and artifact facts out of the generic skill.

## Environment and reports

Use the available authorized search tool. In a Windows Codex environment where bundled `rg.exe` is blocked, PowerShell `Get-ChildItem`, `Select-String` and `Get-Content` are alternatives; do not repeatedly retry a blocked binary or force Windows tooling on other surfaces. Keep broad recursive searches out of `solve_reports/` unless explicitly authorized.

Only when the active contract grants these report writes, update `project_state/codex_execution_report.md` with its required `codex_report_summary` and Decision/round identity, changed files/artifacts, actual checks/sync, acceptance recommendation, limitations and next task. Include the applicable pytest evidence. Do not write legacy report files for ordinary R1 by default. Engineering closeout must not imply that a reverse-solving runtime probe ran when none did. Follow the current report schema, not a historical completion claim.
