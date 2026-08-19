"""Platform V2 governed, durable multi-Agent control plane.

The package keeps TaskStore as execution truth and adds persistent Goals,
owner-activated autonomous windows, dependency-aware coordination, capability
metadata, and allowlisted Draft publication around mature components.
"""

from __future__ import annotations

from .contracts import (
    ExecutionBinding,
    ExecutionEvidence,
    PlatformAcceptanceResult,
    PlatformWorkItem,
)
from .run_store import TaskStore, TaskStoreError
from .task_runtime import DeterministicFixtureExecutor, ExecutorRouter
from .control_store import PlatformControlStore
from .goal_service import GoalService

__all__ = [
    "DeterministicFixtureExecutor",
    "ExecutionBinding",
    "ExecutionEvidence",
    "GoalService",
    "PlatformControlStore",
    "PlatformAcceptanceResult",
    "PlatformWorkItem",
    "TaskStore",
    "TaskStoreError",
]
