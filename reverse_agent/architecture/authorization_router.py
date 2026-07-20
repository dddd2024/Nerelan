"""Explicit routing helper for risk decisions."""

from .contracts import ArchitectureDecision
from .risk import WorkflowRoute


def authorization_route(decision: ArchitectureDecision) -> WorkflowRoute:
    return decision.route
