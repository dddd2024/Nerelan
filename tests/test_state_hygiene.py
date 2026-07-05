from pathlib import Path

from reverse_agent.state_hygiene import build_state_hygiene_retention_bundle
from tests.test_state_governance import _write_state


def test_state_hygiene_facade_remains_non_destructive(tmp_path: Path) -> None:
    state_dir = tmp_path / "project_state"
    _write_state(state_dir)

    bundle = build_state_hygiene_retention_bundle(state_dir=state_dir)

    assert bundle["cleanup_apply_allowed"] is False
    assert bundle["destructive_operation_performed"] is False
    assert bundle["cleanup_plan"]["deleted_files"] == []
    assert bundle["retention_policy"]["cleanup_apply_allowed"] is False
