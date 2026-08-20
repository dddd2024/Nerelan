"""Roadmap: non-authoritative phase display metadata over authoritative goals.

Phase status is always computed from member goal statuses. No code path in
this module writes a phase status field; the underlying table has none.
"""

from __future__ import annotations

from dataclasses import asdict
from typing import Any, Mapping

from .control_store import (
    GoalRecord,
    PlatformControlStore,
    RoadmapPhaseRecord,
    reject_sensitive_keys,
)
from .run_store import TaskStoreError

PHASE_STATUSES = frozenset({"PLANNED", "RUNNING", "BLOCKED", "COMPLETED"})


def derive_phase_status(goal_statuses: Mapping[str, str] | list[str] | tuple[str, ...]) -> str:
    """Pure function: member goal statuses -> phase status.

    INVALIDATED goals do not count toward the phase. An empty (or fully
    invalidated) phase is PLANNED.
    """

    if isinstance(goal_statuses, Mapping):
        statuses = [str(value) for value in goal_statuses.values()]
    else:
        statuses = [str(value) for value in goal_statuses]
    effective = [status for status in statuses if status != "INVALIDATED"]
    if not effective:
        return "PLANNED"
    if all(status == "COMPLETED" for status in effective):
        return "COMPLETED"
    if any(status == "BLOCKED" for status in effective):
        return "BLOCKED"
    if any(status == "RUNNING" for status in effective):
        return "RUNNING"
    return "PLANNED"


def phase_to_dict(
    phase: RoadmapPhaseRecord,
    *,
    status: str,
    goals: list[dict[str, Any]],
) -> dict[str, Any]:
    payload = asdict(phase)
    payload["status"] = status
    payload["derived_status"] = status
    payload["goals"] = goals
    return payload


class RoadmapService:
    """Phase CRUD and goal attachment; status stays derived-only."""

    def __init__(self, *, control_store: PlatformControlStore) -> None:
        self.control_store = control_store

    def create_phase(self, payload: Mapping[str, Any]) -> RoadmapPhaseRecord:
        reject_sensitive_keys(dict(payload))
        title = str(payload.get("title", "")).strip()
        if not title:
            raise TaskStoreError("roadmap_phase_title_required")
        try:
            position = int(payload.get("position", 0))
        except (TypeError, ValueError) as exc:
            raise TaskStoreError("roadmap_phase_position_invalid") from exc
        return self.control_store.create_roadmap_phase(
            title=title,
            position=position,
            description=str(payload.get("description", "")).strip(),
        )

    def list_phases(self) -> list[dict[str, Any]]:
        result: list[dict[str, Any]] = []
        for phase in self.control_store.list_roadmap_phases():
            members = self._member_goals(phase.id)
            status = derive_phase_status([member["status"] for member in members])
            result.append(phase_to_dict(phase, status=status, goals=members))
        return result

    def get_phase(self, phase_id: str) -> dict[str, Any]:
        phase = self.control_store.get_roadmap_phase(phase_id)
        members = self._member_goals(phase_id)
        status = derive_phase_status([member["status"] for member in members])
        return phase_to_dict(phase, status=status, goals=members)

    def attach(self, phase_id: str, goal_id: str) -> dict[str, Any]:
        self.control_store.attach_goal_to_phase(phase_id, goal_id)
        return self.get_phase(phase_id)

    def detach(self, phase_id: str, goal_id: str) -> dict[str, Any]:
        self.control_store.detach_goal_from_phase(phase_id, goal_id)
        return self.get_phase(phase_id)

    def _member_goals(self, phase_id: str) -> list[dict[str, Any]]:
        members: list[dict[str, Any]] = []
        for goal_id in self.control_store.list_phase_goal_ids(phase_id):
            goal: GoalRecord = self.control_store.get_goal(goal_id)
            members.append(
                {
                    "id": goal.id,
                    "title": goal.title,
                    "status": goal.status,
                    "repository": goal.repository,
                    "updated_at": goal.updated_at,
                }
            )
        return members
