"""Roadmap contract tests: phase status is derived-only from member goals."""

import pytest

from reverse_agent.platform_v1.control_store import PlatformControlStore
from reverse_agent.platform_v1.roadmap_service import (
    RoadmapService,
    derive_phase_status,
)
from reverse_agent.platform_v1.run_store import TaskStore, TaskStoreError


@pytest.fixture()
def roadmap():
    store = TaskStore()
    control = PlatformControlStore(store)
    return RoadmapService(control_store=control), control


def _make_goal(control, key: str, title: str = "goal") -> str:
    return control.create_goal(
        title=title,
        objective="objective",
        repository="dddd2024/reverse-agent",
        idempotency_key=key,
    ).id


def test_derive_phase_status_pure_function_matrix() -> None:
    assert derive_phase_status([]) == "PLANNED"
    assert derive_phase_status(("DRAFT",)) == "PLANNED"
    assert derive_phase_status(("PLANNED", "APPROVED")) == "PLANNED"
    assert derive_phase_status(("RUNNING", "DRAFT")) == "RUNNING"
    assert derive_phase_status(("RUNNING", "COMPLETED")) == "RUNNING"
    assert derive_phase_status(("BLOCKED", "RUNNING")) == "BLOCKED"
    assert derive_phase_status(("COMPLETED", "COMPLETED")) == "COMPLETED"
    assert derive_phase_status(("COMPLETED", "DRAFT")) == "PLANNED"
    assert derive_phase_status(("INVALIDATED",)) == "PLANNED"
    assert derive_phase_status(("INVALIDATED", "COMPLETED")) == "COMPLETED"
    assert derive_phase_status({"g1": "RUNNING", "g2": "DRAFT"}) == "RUNNING"


def test_phase_table_has_no_status_column(roadmap) -> None:
    """Structural proof: phase status cannot be written because the column
    does not exist."""
    _, control = roadmap
    columns = {
        row["name"]
        for row in control._conn.execute("PRAGMA table_info(platform_roadmap_phases)")
    }
    assert "status" not in columns
    assert "derived_status" not in columns


def test_goal_status_change_flips_phase_status_without_phase_write(roadmap) -> None:
    _, control = roadmap
    phase = control.create_roadmap_phase(title="P0", position=1)
    goal_id = _make_goal(control, "rm-1")
    control.attach_goal_to_phase(phase.id, goal_id)

    before_row = dict(
        control._conn.execute(
            "SELECT * FROM platform_roadmap_phases WHERE id = ?", (phase.id,)
        ).fetchone()
    )
    service = RoadmapService(control_store=control)
    assert service.get_phase(phase.id)["derived_status"] == "PLANNED"

    control.save_goal_plan(
        goal_id,
        expected_revision=1,
        spec_markdown="s",
        plan_markdown="p",
        tasks=[{"id": "T001", "title": "t", "instruction": "i"}],
        acceptance_criteria=["c"],
    )
    control.approve_goal(goal_id, expected_revision=1)
    control.mark_goal_running(goal_id, revision=1, window_id="window-x")

    changes_before = control._conn.total_changes
    view = service.get_phase(phase.id)
    assert view["derived_status"] == "RUNNING"
    assert view["goals"][0]["status"] == "RUNNING"

    after_row = dict(
        control._conn.execute(
            "SELECT * FROM platform_roadmap_phases WHERE id = ?", (phase.id,)
        ).fetchone()
    )
    assert after_row == before_row
    assert control._conn.total_changes == changes_before


def test_attach_is_idempotent_and_detachable(roadmap) -> None:
    _, control = roadmap
    phase = control.create_roadmap_phase(title="P0", position=1)
    goal_id = _make_goal(control, "rm-2")
    control.attach_goal_to_phase(phase.id, goal_id)
    control.attach_goal_to_phase(phase.id, goal_id)
    assert control.list_phase_goal_ids(phase.id) == (goal_id,)
    control.detach_goal_from_phase(phase.id, goal_id)
    assert control.list_phase_goal_ids(phase.id) == ()
    with pytest.raises(TaskStoreError):
        control.detach_goal_from_phase(phase.id, goal_id)


def test_attach_validates_phase_and_goal_exist(roadmap) -> None:
    _, control = roadmap
    goal_id = _make_goal(control, "rm-3")
    with pytest.raises(TaskStoreError):
        control.attach_goal_to_phase("phase-missing", goal_id)
    phase = control.create_roadmap_phase(title="P0", position=1)
    with pytest.raises(TaskStoreError):
        control.attach_goal_to_phase(phase.id, "goal-missing")


def test_list_phases_orders_by_position_and_derives_each(roadmap) -> None:
    service, control = roadmap
    later = control.create_roadmap_phase(title="P1", position=2)
    earlier = control.create_roadmap_phase(title="P0", position=1)
    empty = control.create_roadmap_phase(title="P2", position=3)
    goal_a = _make_goal(control, "rm-a")
    goal_b = _make_goal(control, "rm-b")
    control.attach_goal_to_phase(earlier.id, goal_a)
    control.attach_goal_to_phase(later.id, goal_b)
    control.save_goal_plan(
        goal_b,
        expected_revision=1,
        spec_markdown="s",
        plan_markdown="p",
        tasks=[{"id": "T001", "title": "t", "instruction": "i"}],
        acceptance_criteria=["c"],
    )
    control.approve_goal(goal_b, expected_revision=1)
    control.mark_goal_running(goal_b, revision=1, window_id="window-y")

    phases = service.list_phases()
    assert [phase["title"] for phase in phases] == ["P0", "P1", "P2"]
    assert [phase["derived_status"] for phase in phases] == [
        "PLANNED",
        "RUNNING",
        "PLANNED",
    ]
    assert [len(phase["goals"]) for phase in phases] == [1, 1, 0]


def test_create_phase_requires_title_and_rejects_secrets(roadmap) -> None:
    service, _ = roadmap
    assert service.create_phase({"title": "P0", "position": 1}).title == "P0"
    with pytest.raises(TaskStoreError):
        service.create_phase({"title": "", "position": 1})
    with pytest.raises(TaskStoreError):
        service.create_phase({"title": "x", "position": 1, "password": "hunter2hunter2"})
