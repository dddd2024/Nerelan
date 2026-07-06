from pathlib import Path

from reverse_agent.state_index_readiness import (
    build_state_index_readiness_result,
    build_state_index_readiness_schema,
    validate_state_index_readiness_result,
)


def _write_state(state_dir: Path) -> None:
    state_dir.mkdir()
    (state_dir / "gates").mkdir()
    (state_dir / "decision_packet.md").write_text(
        """```json decision_meta
{
  "schema_version": 1,
  "decision_id": "decision_20260705_governance_operations_bundle_big_step_v1",
  "round_id": "round_20260705_governance_operations_bundle_big_step_v1",
  "status": "APPROVED",
  "mainline": "project_governance",
  "skill_profiles": ["reverse-agent-iteration@v2"]
}
```
""",
        encoding="utf-8",
    )


def test_state_index_readiness_is_schema_only_and_creates_no_database(tmp_path: Path) -> None:
    state_dir = tmp_path / "project_state"
    _write_state(state_dir)

    schema = build_state_index_readiness_schema(state_dir=state_dir)
    result = build_state_index_readiness_result(state_dir=state_dir)

    assert set(schema["tables"]) >= {"decisions", "rounds", "artifacts", "executions", "audits", "workstreams", "backlog_notices"}
    assert result["gate_status"] == "PASSED"
    assert result["sqlite_read_index_only"] is True
    assert result["project_state_remains_audit_fact_source"] is True
    assert result["database_file_created"] is False
    assert result["database_files_present"] == []
    assert not (state_dir / "index.sqlite").exists()
    assert validate_state_index_readiness_result(result) == []
