"""Platform V1 thin adapter: OpenHands Agent Canvas + Codex ACP vertical slice.

This package provides only the thin policy/evidence/acceptance adapter between
the reverse-agent governance layer and the pinned OpenHands Agent Canvas +
Codex ACP platform surface. It does not implement a second executor, agent
loop, sandbox, database, or frontend.
"""

from __future__ import annotations

from .contracts import (
    ExecutionBinding,
    ExecutionEvidence,
    PlatformAcceptanceResult,
    PlatformWorkItem,
)

__all__ = [
    "ExecutionBinding",
    "ExecutionEvidence",
    "PlatformAcceptanceResult",
    "PlatformWorkItem",
]
