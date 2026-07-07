# Next Step After Scoped Metadata Foundation

> **Roadmap material — not execution authority.** This document records the next recommended project-governance steps after `round_20260706_scoped_state_metadata_foundation_big_step_v1`. It does not authorize commands, file changes, runner dispatch, workflow dispatch, sample solving, Web runtime, database work, deletion, or migration. Only `project_state/decision_packet.md` controls an execution round, and only `project_state/gates/command_plan.json` controls commands for that round.

## 1. Current Position

The latest scoped metadata foundation round should be treated as accepted with limitations rather than as a complete state-taxonomy migration.

What is accepted:

```text
Phase A scoped metadata foundation:
- source-level support for scope/domain/mainline/role/freshness metadata;
- tests for scoped metadata behavior and legacy compatibility;
- final-check/report-summary visibility for scoped metadata coverage;
- run-closeout and final-check status-truthfulness repaired.
```

What is not accepted yet:

```text
- full on-disk scoped metadata visibility in every current state artifact;
- project_state/domains/* creation;
- reverse_solving current_state copy;
- negative_results split;
- top-level current_state summary conversion;
- hard-fail enforcement for new missing scope metadata;
- Web/frontend runtime;
- runner dispatch or automation.
```

The important current limitation is that scoped metadata support exists in builders and tests, but current on-disk `state_manifest.json` / `artifact_index.json` may still show legacy coverage warnings until they are regenerated through an authorized governance round.

## 2. Recommended Next Mainline

Next mainline:

```text
project_governance
```

Do not switch to reverse-solving, tool integration, Web, database, or runner dispatch in the next round. The next useful step is still state-governance hygiene.

## 3. Recommended Next Work Item

Recommended next work item:

```text
Scoped Metadata Visibility Refresh / Phase A.1
```

Purpose:

```text
Materialize the already-implemented Phase A scoped metadata support into current on-disk governance artifacts and make the warning/coverage story unambiguous before creating domain directories.
```

This is intentionally smaller than Phase B. It should close the accepted-with-limitations gap before the project starts creating `project_state/domains/*`.

## 4. Why Phase A.1 Comes Before Phase B

Phase B creates domain skeletons. That is safe only after the current top-level governance files can clearly report:

```text
- which files are global governance state;
- which files are reverse-solving legacy/sample state;
- which files are gate artifacts;
- which files are roadmap/workstream artifacts;
- which entries are legacy-compatible but missing scoped metadata;
- which warnings are non-blocking and why.
```

If Phase B starts while `state_manifest.json` and `artifact_index.json` still surface legacy warnings without clear materialized metadata, later migration phases become harder to audit.

## 5. Phase A.1 Scope

Allowed conceptual scope for a future decision:

```text
1. Regenerate or refresh state_manifest.json so the scoped_metadata section is visible on disk.
2. Regenerate or refresh artifact_index.json so scope_metadata and scope_coverage are visible on disk.
3. Ensure negative_results scoped upgrade remains backward compatible.
4. Ensure final-check/report-summary distinguish:
   - non-blocking historical/sample backlog;
   - missing legacy metadata;
   - current-round metadata regressions.
5. Add or adjust tests only where needed for materialized on-disk output.
6. Keep all changes inside project_governance.
```

This work should reuse existing mechanisms:

```text
- project_gate;
- project_state_manifest;
- artifact_index builder;
- negative_results helpers;
- report-summary;
- final-check;
- execution-log;
- run-closeout;
- workstream registry.
```

It must not introduce a second manifest format, a new database, a new state registry, or a parallel closeout mechanism.

## 6. Candidate Future Decision Boundary

A future `DECISION_PACKET` may use a goal like:

```text
Materialize Phase A scoped metadata into current on-disk governance artifacts and remove ambiguous scoped metadata coverage warnings without starting Phase B domain skeleton creation.
```

Candidate allowed files:

```text
reverse_agent/project_state.py
reverse_agent/project_state_manifest.py
reverse_agent/project_gate.py
reverse_agent/project_reports.py
tests/test_project_state.py
tests/test_project_state_manifest.py
tests/test_project_gate.py
tests/test_project_reports.py
project_state/state_manifest.json
project_state/artifact_index.json
project_state/negative_results.json
project_state/gates/* generated artifacts
project_state/rounds/<new_round_id>/* generated artifacts
```

Candidate documentation updates, if needed:

```text
docs/roadmap/project_state_domain_taxonomy_supplement.md
docs/roadmap/next_step_after_scoped_metadata_foundation.md
```

## 7. Do Not Do in Phase A.1

Do not do any of the following:

```text
- do not create project_state/domains/*;
- do not move files;
- do not delete files;
- do not split negative_results.json;
- do not convert top-level current_state.json into a global summary;
- do not modify task_packet.json;
- do not run sample solving;
- do not run candidate search;
- do not run runtime validation on samples;
- do not run IDA, Ghidra, OllyDbg, debugger, emulator, MCP, or external reverse tools;
- do not implement Web/frontend runtime;
- do not create a database or queue;
- do not dispatch GitHub Actions;
- do not dispatch local, remote, or automatic runners;
- do not perform cleanup apply, deletion manifest write, tombstone write, or archive compaction apply.
```

## 8. Acceptance Criteria for Phase A.1

A future Phase A.1 round should be accepted only if:

```text
1. decision_meta is valid, APPROVED, and mainline=project_governance.
2. command_plan carries the current decision_id and round_id.
3. pytest_result is PASSED.
4. report-summary is PASSED.
5. execution-log is PASSED and records every command-plan required command.
6. final-check is PASSED.
7. run-closeout is PASSED.
8. state_manifest.json visibly surfaces scoped_metadata or equivalent scoped coverage.
9. artifact_index.json visibly surfaces scope_metadata and scope_coverage or equivalent scoped coverage.
10. negative_results.json remains list-style compatible.
11. legacy/sample missing artifacts remain non-blocking for non-sample governance rounds.
12. no forbidden paths are modified.
13. no project_state/domains/* directory is created.
14. the execution report does not claim Phase B/C/D/E/F completion.
```

## 9. Stop Conditions for Phase A.1

A future execution should stop with `BLOCKED` if:

```text
- repository root is not F:\reverse-agent or equivalent;
- project_state/decision_packet.md cannot be read;
- .codex-skills/registry.json does not mark reverse-agent-iteration@v2 active;
- command-plan cannot be generated;
- refreshing scoped metadata requires file moves, deletion, archive apply, or domain directory creation;
- the work would require Web, database, runner dispatch, workflow dispatch, sample solving, or external reverse tools.
```

A future execution should stop with `REWORK_REQUIRED` if:

```text
- report status and audit conclusion disagree;
- final-check fails;
- run-closeout fails;
- scoped metadata coverage is still ambiguous after the refresh;
- on-disk state_manifest/artifact_index still do not expose the intended Phase A metadata;
- current_state.json or task_packet.json is modified;
- project_state/domains/* is created;
- Phase B/C/D/E/F is claimed complete without a separate decision.
```

## 10. After Phase A.1

Only after Phase A.1 is accepted should the project consider Phase B:

```text
Phase B — Domain Skeleton
```

Phase B should only create domain skeleton metadata and manifests, not migrate live state yet. The safe Phase B target is:

```text
project_state/domains/
  README.md
  governance/README.md
  reverse_solving/README.md
  user_solve/README.md
  tool_integration/README.md
  training_dataset/README.md
```

Even Phase B should not copy `current_state.json`, split `negative_results.json`, or change top-level state semantics. Those remain Phase C/D/E.

## 11. Practical Next-Step Recommendation

The next `DECISION_PACKET` should be Phase A.1, not Phase B.

Recommended order:

```text
1. Phase A.1 — materialize scoped metadata visibility in on-disk governance artifacts.
2. Phase B — create empty domain skeletons with README/manifests only.
3. Phase C — copy reverse-solving current_state into reverse_solving domain scope.
4. Phase D — split negative_results with compatibility shim.
5. Phase E — convert top-level current_state into global summary.
6. Phase F — harden final-check for new scope metadata regressions.
```

This keeps the project on the normal pace path while avoiding a premature state migration.
