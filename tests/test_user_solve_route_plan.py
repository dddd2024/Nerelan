from reverse_agent.user_solve_route_plan import build_route_plan


def test_route_plan_candidate_requires_validation_but_does_not_execute() -> None:
    plan = build_route_plan(
        {
            "status": "candidate_found",
            "validation_status": "pending",
            "evidence_status": "building",
        },
        fixture_name="candidate",
    ).to_dict()

    assert plan["executed"] is False
    action = plan["planned_actions"][0]
    assert action["kind"] == "validate_candidate"
    assert action["permission_required"] is True
    assert action["executable_now"] is False


def test_route_plan_verified_returns_answer_only_when_validation_passed() -> None:
    plan = build_route_plan(
        {
            "status": "verified",
            "validation_status": "passed",
            "evidence_status": "complete",
        },
        fixture_name="verified",
    ).to_dict()

    assert plan["planned_actions"][0]["kind"] == "return_answer"
