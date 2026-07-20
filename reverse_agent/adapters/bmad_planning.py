"""Fixture-only BMAD planning reference adapter."""

from __future__ import annotations

from typing import Any, Mapping

from reverse_agent.architecture.contracts import PlanningReference


ALLOWED_ARTIFACT_TYPES = frozenset({"product_brief", "prd", "architecture", "story"})


def load_planning_reference(payload: Mapping[str, Any]) -> PlanningReference:
    reference = PlanningReference.from_mapping(payload)
    if reference.artifact_type not in ALLOWED_ARTIFACT_TYPES:
        raise ValueError(f"unsupported_planning_artifact:{reference.artifact_type}")
    return reference
