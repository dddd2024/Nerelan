"""Concrete serialization-safe contracts for the Gate 2 Temporal boundary."""

from __future__ import annotations

from dataclasses import dataclass

_FAILURE_CODES = frozenset(
    {
        "ATTEMPT_CLEANUP_FAILED",
        "ATTEMPT_LAUNCH_FAILED",
        "ATTEMPT_READINESS_FAILED",
        "ATTEMPT_READINESS_TIMEOUT",
        "ATTEMPT_READINESS_CONTRACT",
        "OPENHANDS_LIFECYCLE_FAILED",
        "TASK_SUBMISSION_FAILED",
    }
)
_FAILURE_STAGES = frozenset(
    {"cleanup", "launch", "readiness", "start_conversation", "collect_result"}
)


@dataclass(frozen=True, slots=True)
class LaunchAttemptResult:
    container_name: str
    state: str
    image_digest: str
    workspace_destination: str
    network_name: str
    privileged: bool
    no_new_privileges: bool
    read_only_rootfs: bool


@dataclass(frozen=True, slots=True)
class AttemptReadinessResult:
    alive: bool
    health: bool
    poll_count: int
    last_state: str


@dataclass(frozen=True, slots=True)
class AttemptReadinessProgress:
    state: str
    poll_count: int
    elapsed_milliseconds: int
    next_delay_milliseconds: int


@dataclass(frozen=True, slots=True)
class OpenHandsLifecycleResult:
    conversation_id: str
    attempt: int
    lifecycle_state: str
    reconciled: bool


@dataclass(frozen=True, slots=True)
class TaskSubmissionEvidence:
    verdict: str
    summary: str
    changed_paths: tuple[str, ...]
    commands_executed: tuple[str, ...]
    test_evidence: tuple[str, ...]
    limitations: tuple[str, ...]
    failure_reason: str | None


@dataclass(frozen=True, slots=True)
class CleanupResult:
    attempt_container_absent: bool
    attempt_workspace_absent: bool


@dataclass(frozen=True, slots=True)
class SanitizedFailureCategory:
    code: str
    stage: str
    retryable: bool

    def __post_init__(self) -> None:
        if self.code not in _FAILURE_CODES:
            raise ValueError("invalid_failure_code")
        if self.stage not in _FAILURE_STAGES:
            raise ValueError("invalid_failure_stage")
        if not isinstance(self.retryable, bool):
            raise ValueError("invalid_failure_retryable")


@dataclass(frozen=True, slots=True)
class ActivityProgress:
    stage: str
    completed: bool


@dataclass(frozen=True, slots=True)
class Gate2WorkflowResult:
    submission: TaskSubmissionEvidence
    cleanup: CleanupResult
    result_label: str
