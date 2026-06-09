```json
{
  "schema_version": "1.0",
  "decision_id": "decision_20260609_repair_truncated_decision_packet_v1",
  "round_id": "round_20260609_repair_truncated_decision_packet_v1",
  "based_on_state_build_id": "state_20260608_152003_e6fc7ab3ce85",
  "based_on_state_digest": "e6fc7ab3ce8537d3a989adf7eeba7366ef987bf6887ee459b727c9417f958067",
  "status": "APPROVED",
  "mainline": "engineering_branch",
  "skill_profiles": ["reverse-agent-iteration"]
}
```

Goal
Repair project_state/decision_packet.md because the active decision packet is truncated and cannot be used as the next Codex execution authority. Produce a complete valid decision packet as the only intended change.

Current Evidence
The active decision file is project_state/decision_packet.md. The current file only contains decision_meta and a partial Goal line for decision.

Do Not Do
Do not run cpp2 analysis yet. Do not modify .codex-skills/. Do not commit full solve_reports/. Do not treat the truncated decision as executable.

Files To Inspect
project_state/decision_packet.md
project_state/task_packet.json
project_state/current_state.json
project_state/artifact_index.json
project_state/negative_results.json
project_state/codex_execution_report.md
project_state/pytest_result.txt
.codex-skills/registry.json

Required Audit
Confirm repaired decision_packet.md has all eight sections: decision_meta, Goal, Current Evidence, Do Not Do, Files To Inspect, Required Audit, Implementation Scope, Tests, Stop Conditions.

Implementation Scope
Replace project_state/decision_packet.md with a complete, valid decision packet. Allow bounded cpp2_f2738577 static triage/readiness after full sections included.

Tests
Run `python -m reverse_agent.project_state status` and existing decision/report lint checks. Record results in project_state/pytest_result.txt and project_state/codex_execution_report.md.

Stop Conditions
Stop if rewritten decision_packet.md is still truncated or skill profile missing.
