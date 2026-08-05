"""Platform V1 policy, evidence, and trusted-host coordination adapters.

The package remains a thin integration layer around installed Codex, Git, and
GitHub tooling. It owns bounded SQLite coordination but does not implement an
agent loop, sandbox, CI service, merge automation, or frontend.
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
