from pathlib import Path

from reverse_agent.project_workstreams import (
    WORKSTREAM_STATES,
    build_workstream_registry,
    validate_workstream_registry,
)


DECISION_ID = "decision_20260705_project_governance_context_registry_v1"
ROUND_ID = "round_20260705_project_governance_context_registry_v1"


def _write_state(state_dir: Path) -> None:
    state_dir.mkdir()
    (state_dir / "decision_packet.md").write_text(
        f"""```json decision_meta
{{
  "schema_version": 1,
  "decision_id": "{DECISION_ID}",
  "round_id": "{ROUND_ID}",
  "status": "APPROVED",
  "mainline": "project_governance",
  "skill_profiles": ["reverse-agent-iteration@v2"]
}}
```

```json decision_contract
{{
  "follows_last_accepted_round_id": "round_20260704_manual_mode_web_orchestrator_mvp_big_step_v1"
}}
```
""",
        encoding="utf-8",
    )


def test_workstream_registry_has_one_active_current_round(tmp_path: Path) -> None:
    state_dir = tmp_path / "project_state"
    _write_state(state_dir)

    registry = build_workstream_registry(state_dir=state_dir)
    active = [item for item in registry["workstreams"] if item["status"] == "ACTIVE_ROUND"]

    assert tuple(registry["lifecycle_states"]) == WORKSTREAM_STATES
    assert len(active) == 1
    assert active[0]["workstream_id"] == "project_governance_context_registry"
    assert active[0]["active_decision_id"] == DECISION_ID
    assert active[0]["active_round_id"] == ROUND_ID
    assert all(item["is_execution_authority"] is False for item in registry["workstreams"])
    assert {item["workstream_id"] for item in registry["workstreams"]} >= {
        "user_solve_layer",
        "agent_runner_dispatch",
        "github_ci_and_state_gate",
        "reverse_solving_capability_matrix",
        "tool_integration_ida_ghidra_debugger",
        "sqlite_query_index",
    }
    assert validate_workstream_registry(registry, decision_id=DECISION_ID, round_id=ROUND_ID) == []
    assert (state_dir / "roadmap" / "workstreams.json").exists()
