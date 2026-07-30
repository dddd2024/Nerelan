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
        "WORKSPACE_ROOT_MISSING",
        "WORKSPACE_ROOT_NOT_DIRECTORY",
        "WORKSPACE_ROOT_SYMLINK_REJECTED",
        "WORKSPACE_ROOT_OWNER_MISMATCH",
        "WORKSPACE_ROOT_MODE_MISMATCH",
        "WORKSPACE_ROOT_NOT_WRITABLE",
        "WORKSPACE_ROOT_HOST_IDENTITY_MISMATCH",
        "ATTEMPT_DIRECTORY_PROVISION_FAILED",
    }
)
_FAILURE_STAGES = frozenset(
    {
        "workspace_preflight",
        "cleanup",
        "launch",
        "readiness",
        "start_conversation",
        "collect_result",
    }
)


@dataclass(frozen=True, slots=True)
class WorkspaceRootPreflightResult:
    source_kind: str
    root_uid: int
    root_gid: int
    root_mode: int
    controller_uid: int
    controller_gid: int
    agent_uid: int
    agent_gid: int
    root_exists: bool
    root_is_directory: bool
    root_is_symlink: bool
    owner_matches_policy: bool
    mode_matches_policy: bool
    controller_atomic_probe: bool
    attempt_directory_provisioned: bool
    agent_exact_attempt_write: bool
    agent_root_denied: bool
    agent_sibling_denied: bool
    agent_outside_denied: bool
    host_controller_identity_match: bool

    def __post_init__(self) -> None:
        if self.source_kind != "volume":
            raise ValueError("invalid_workspace_source_kind")
        for name in (
            "root_uid",
            "root_gid",
            "root_mode",
            "controller_uid",
            "controller_gid",
            "agent_uid",
            "agent_gid",
        ):
            value = getattr(self, name)
            if isinstance(value, bool) or not isinstance(value, int) or value < -1:
                raise ValueError(f"invalid_{name}")
        if self.root_mode < 0 or self.root_mode > 0o777:
            raise ValueError("invalid_workspace_root_mode")
        required_true = (
            self.root_exists,
            self.root_is_directory,
            self.owner_matches_policy,
            self.mode_matches_policy,
            self.controller_atomic_probe,
            self.attempt_directory_provisioned,
            self.agent_exact_attempt_write,
            self.agent_root_denied,
            self.agent_sibling_denied,
            self.agent_outside_denied,
            self.host_controller_identity_match,
        )
        if self.root_is_symlink or not all(required_true):
            raise ValueError("workspace_preflight_result_must_pass")


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

    def __post_init__(self) -> None:
        if not self.alive or not self.health:
            raise ValueError("readiness_result_must_be_ready")
        if isinstance(self.poll_count, bool) or self.poll_count < 1:
            raise ValueError("invalid_readiness_poll_count")
        if self.last_state != "alive":
            raise ValueError("invalid_readiness_success_state")


@dataclass(frozen=True, slots=True)
class AttemptReadinessProgress:
    state: str
    poll_count: int
    elapsed_milliseconds: int
    next_delay_milliseconds: int

    def __post_init__(self) -> None:
        if self.state not in {
            "connection_refused",
            "timeout",
            "HTTP_not_ready_status",
        }:
            raise ValueError("invalid_readiness_progress_state")
        for name in (
            "poll_count",
            "elapsed_milliseconds",
            "next_delay_milliseconds",
        ):
            value = getattr(self, name)
            if isinstance(value, bool) or not isinstance(value, int) or value < 0:
                raise ValueError(f"invalid_{name}")
        if self.poll_count < 1 or self.next_delay_milliseconds < 1:
            raise ValueError("invalid_readiness_progress_bounds")


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
