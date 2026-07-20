"""Authority rules for architecture inputs."""

from __future__ import annotations

from .contracts import PlanningReference


def planning_reference_can_authorize(_reference: PlanningReference) -> bool:
    """Planning artifacts are context and can never authorize execution."""

    return False
