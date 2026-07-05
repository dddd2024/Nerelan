from reverse_agent.user_solve_task_api import handle_task_request


def test_task_api_creates_demo_task_under_bounded_route(tmp_path) -> None:
    state_dir = tmp_path / "project_state"

    response = handle_task_request(
        "POST",
        "/api/manual/tasks/demo",
        {"task_id": "demo_api_task"},
        state_dir=state_dir,
        decision_id="decision_x",
        round_id="round_x",
    )

    assert response["status_code"] == 200
    assert response["body"]["task"]["task_id"] == "demo_api_task"
    assert response["production_service"] is False
