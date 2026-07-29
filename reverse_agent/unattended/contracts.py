"""Small immutable contracts used by the v0 unattended baseline."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping


@dataclass(frozen=True, slots=True)
class MinimalWorkItem:
    owner: str
    repository: str
    issue_number: int
    risk_tier: str
    allowed_paths: tuple[str, ...]
    forbidden_operations: tuple[str, ...] = ()
    approval_granted: bool = False
    auto_merge_allowed: bool = False
    max_attempts: int = 1


@dataclass(frozen=True, slots=True)
class ResolvedExecutionPolicy:
    unattended_allowed: bool
    approval_required: bool
    allowed_paths: tuple[str, ...]
    forbidden_operations: tuple[str, ...]
    auto_merge_allowed: bool
    max_attempts: int


@dataclass(frozen=True, slots=True)
class ExecutionHandle:
    workflow_id: str
    attempt: int
    conversation_id: str | None = None


@dataclass(frozen=True, slots=True)
class TaskSubmission:
    handle: ExecutionHandle
    instruction: str
    workspace: str


@dataclass(frozen=True, slots=True)
class AcceptanceResult:
    accepted: bool
    checks: tuple[str, ...]
    detail: str = ""


@dataclass(frozen=True, slots=True)
class FailureEnvelope:
    code: str
    message: str
    retryable: bool
    details: Mapping[str, Any] | None = None
