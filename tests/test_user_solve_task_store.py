import pytest

from reverse_agent.user_solve_task_lifecycle import build_demo_task_payload
from reverse_agent.user_solve_task_store import (
    list_demo_tasks,
    read_demo_task,
    validate_demo_task_path,
    write_demo_task,
)


def test_demo_task_store_writes_only_demo_pattern(tmp_path) -> None:
    state_dir = tmp_path / "project_state"
    payload = build_demo_task_payload(
        task_id="demo_manual_mode_task",
        decision_id="decision_x",
        round_id="round_x",
    )

    result = write_demo_task(state_dir, payload)

    assert result["write_status"] == "PASSED"
    assert result["path"] == "project_state/solve_tasks/demo_manual_mode_task.json"
    assert read_demo_task(state_dir, "demo_manual_mode_task")["task_id"] == "demo_manual_mode_task"
    assert list_demo_tasks(state_dir)[0]["validation_status"] == "PASSED"


def test_demo_task_store_rejects_unsafe_paths(tmp_path) -> None:
    state_dir = tmp_path / "project_state"

    with pytest.raises(ValueError):
        validate_demo_task_path(state_dir, "../project_state/solve_tasks/demo_bad.json")
    with pytest.raises(ValueError):
        validate_demo_task_path(state_dir, "project_state/solve_tasks/live_bad.json")
