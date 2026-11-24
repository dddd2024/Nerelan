"""#1462: a goal the host can never publish says so, and the landing scan is per window. Provider-free."""
from __future__ import annotations

import pytest

from test_goal_functional_checks import goal_checks  # noqa: F401 - fixture reuse
from test_model_review_execution import review_setup  # noqa: F401 - fixture reuse
from test_model_review_toolless import toolless  # noqa: F401 - fixture reuse
from reverse_agent.platform_v1 import artifact_handoff
from reverse_agent.platform_v1.artifact_handoff import publication_blocker, published_plan_tasks
from reverse_agent.platform_v1.control_store import PlatformControlStore
from reverse_agent.platform_v1.goal_service import GoalService

CHECK = [{"profile_id": "python_pytest", "working_directory": ".", "targets": ["tests/test_x.py"]}]
TEAM = [{"id": "implement", "kind": "code", "validation_checks": CHECK},
        {"id": "review", "kind": "review", "dependencies": ["implement"],
         "artifact_input": {"plan_task_id": "implement"}, "validation_checks": CHECK}]


class TestPublicationRule:
    def test_only_a_checked_result_handed_to_a_review_is_published(self):
        assert published_plan_tasks(TEAM) == {"implement"}
        assert publication_blocker(TEAM, "implement") == ""
        # The review consumes the result; it is never published itself.
        assert publication_blocker(TEAM, "review") == ""

    @pytest.mark.parametrize("task, reason", [
        ({"id": "implement", "kind": "code"}, "no_functional_checks"),
        ({"id": "implement", "kind": "code", "validation_checks": CHECK}, "no_review_handoff"),
    ])
    def test_a_lone_implementation_is_never_published(self, task, reason):
        assert published_plan_tasks([task]) == set()
        assert publication_blocker([task], "implement") == reason

    def test_a_malformed_input_publishes_nothing(self):
        assert published_plan_tasks([{"id": "a", "artifact_input": {"plan_task_id": "../x"}}]) == set()


class TestWindowScan:
    def test_ready_tasks_are_read_per_window_in_plan_order(self, toolless):
        store = toolless["store"]
        control = PlatformControlStore(store)
        goal = control.get_goal(control.goal_id_for_task(toolless["producer"]))
        assert store.get_task(toolless["producer"]).status == "READY_FOR_REVIEW"
        ready = control.ready_window_tasks(goal.window_id)
        assert toolless["producer"] in ready
        assert control.ready_window_tasks("another-window") == ()
        indexes = {row[1] for row in store._conn.execute("PRAGMA index_list(platform_goals)")}
        assert "idx_platform_goal_window" in indexes

    def test_a_published_producer_has_no_blocker_and_a_missing_proof_is_named(self, toolless):
        store = toolless["store"]
        control = PlatformControlStore(store)
        goal_id = control.goal_id_for_task(toolless["producer"])
        goals = GoalService(store=store, control_store=control)
        links = {link["task_id"]: link for link in goals.detail(goal_id)["task_links"]}
        assert links[toolless["producer"]]["publication_blocked"] == ""
        assert links[toolless["consumer"]]["publication_blocked"] == ""
        # Without its AcceptedArtifact the producer can never be published: say why.
        store._conn.execute("DELETE FROM task_evidence WHERE task_id = ? AND category = ?",
                            (toolless["producer"], artifact_handoff.ACCEPTED_CATEGORY))
        links = {link["task_id"]: link for link in goals.detail(goal_id)["task_links"]}
        assert links[toolless["producer"]]["publication_blocked"] == "functional_validation_not_accepted"
