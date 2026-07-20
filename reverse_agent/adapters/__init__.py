"""Structured, non-mutating architecture adapters."""

from .bmad_planning import load_planning_reference
from .github_truth import GitHubTruthObservation
from .github_work_item import load_github_work_item

__all__ = ["GitHubTruthObservation", "load_github_work_item", "load_planning_reference"]
