import json
from pathlib import Path

from reverse_agent.state_hygiene import (
    build_state_hygiene_dashboard_feed,
    build_state_hygiene_retention_bundle,
    validate_state_hygiene_dashboard_feed,
)
from tests.test_state_governance import _write_state


def test_state_hygiene_facade_remains_non_destructive(tmp_path: Path) -> None:
    state_dir = tmp_path / "project_state"
    _write_state(state_dir)

    bundle = build_state_hygiene_retention_bundle(state_dir=state_dir)

    assert bundle["cleanup_apply_allowed"] is False
    assert bundle["destructive_operation_performed"] is False
    assert bundle["cleanup_plan"]["deleted_files"] == []
    assert bundle["retention_policy"]["cleanup_apply_allowed"] is False


def test_state_hygiene_dashboard_feed_is_static_json(tmp_path: Path) -> None:
    state_dir = tmp_path / "project_state"
    _write_state(state_dir)
    (state_dir / "gates" / "cleanup_apply_review_result.json").write_text(
        json.dumps({"gate_status": "PASSED", "review_status": "READY_FOR_HUMAN_REVIEW"}),
        encoding="utf-8",
    )
    (state_dir / "gates" / "round_compaction_dry_run.json").write_text(
        json.dumps({"dry_run_status": "PASSED"}),
        encoding="utf-8",
    )
    (state_dir / "gates" / "state_index_readiness_result.json").write_text(
        json.dumps({"gate_status": "PASSED", "readiness_status": "SCHEMA_READY_NO_DATABASE"}),
        encoding="utf-8",
    )
    (state_dir / "gates" / "lifecycle_transition_guard_result.json").write_text(
        json.dumps({"gate_status": "PASSED", "real_cleanup_apply_deferred": True}),
        encoding="utf-8",
    )
    (state_dir / "roadmap" / "workstreams.json").write_text(
        json.dumps({"workstreams": [{"workstream_id": "governance_operations_bundle", "status": "ACTIVE_ROUND"}]}),
        encoding="utf-8",
    )

    feed, summary = build_state_hygiene_dashboard_feed(state_dir=state_dir)

    assert validate_state_hygiene_dashboard_feed(feed) == []
    assert feed["dashboard_feed_only"] is True
    assert feed["web_runtime_started"] is False
    assert feed["workstream_state"]["active_ids"] == ["governance_operations_bundle"]
    assert summary["dashboard_status"] == "READY"
