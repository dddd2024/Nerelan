```json decision_meta
{"schema_version":1,"decision_id":"decision_20260609_archive_current_archive_round_and_rebuild_state_v1","round_id":"round_20260609_archive_current_archive_round_and_rebuild_state_v1","based_on_state_build_id":"state_20260608_152003_e6fc7ab3ce85","based_on_state_digest":"e6fc7ab3ce8537d3a989adf7eeba7366ef987bf6887ee459b727c9417f958067","status":"APPROVED","mainline":"engineering_branch","skill_profiles":["reverse-agent-iteration@v2","samplereverse-frontier@v2"]}
```

# DECISION_PACKET

## Goal

Archive the currently accepted archive-governance round (`round_20260609_archive_ollydbg_preflight_round_v1`) and refresh project-state handoff metadata.

## Current Evidence

- Previous archive-governance round is ACCEPTED.
- Old OllyDbg preflight round already has a manifest.
- Current archive round itself is not archived yet.
- task_packet/current_state still point to historical samplereverse state and should remain advisory, not execution authority.
- No reverse-solving evidence should be promoted in this round.

## Do Not Do

- Do not run OllyDbg, IDA, Ghidra, x64dbg, emulator, debugger, hook, sidecar.
- Do not execute samples.
- Do not perform solver search, candidate generation, runtime probes.
- Do not modify .codex-skills.
- Do not read full solve_reports.

## Files To Inspect

- project_state/decision_packet.md
- project_state/codex_execution_report.md
- project_state/pytest_result.txt
- project_state/current_state.json
- project_state/task_packet.json
- project_state/artifact_index.json
- project_state/rounds/round_20260609_archive_ollydbg_preflight_round_v1/*

## Required Audit

- Verify current archive round is archived.
- Verify round_manifest exists.
- Verify report/decision/pytest IDs match.
- Verify no runtime or reverse-solving actions occurred.
- Verify stale artifacts remain stale.

## Implementation Scope

Only state-governance files, round manifests, report, pytest_result, and project-state refresh outputs may change.

## Tests

python -m reverse_agent.project_state status
python -m reverse_agent.project_state lint-decision
python -m reverse_agent.project_state lint-report
python -m pytest tests/test_project_state.py -q

## Stop Conditions

Stop if archive requires external tools, sample execution, solver execution, or modification of .codex-skills.
