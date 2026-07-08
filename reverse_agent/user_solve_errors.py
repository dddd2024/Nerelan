from __future__ import annotations

from dataclasses import dataclass, field
from enum import StrEnum
from typing import Any

from .user_solve_contract import contains_internal_reference, redact_internal_references


class BlockedReason(StrEnum):
    POLICY = "policy"
    TOOL = "tool"
    ENVIRONMENT = "environment"
    SAMPLE_FORMAT = "sample_format"
    UNSUPPORTED = "unsupported"


class FailedReason(StrEnum):
    POLICY = "policy"
    TOOL = "tool"
    ENVIRONMENT = "environment"
    SAMPLE_FORMAT = "sample_format"
    UNSUPPORTED = "unsupported"
    ANALYSIS = "analysis"
    VALIDATION = "validation"


@dataclass(frozen=True)
class ReasonCode:
    code: str
    public_message: str
    retryable: bool = False

    def __post_init__(self) -> None:
        if not str(self.code or "").strip():
            raise ValueError("reason code must be non-empty")
        if contains_internal_reference(self.public_message):
            raise ValueError("public message cannot contain internal references")

    def to_user_dict(self) -> dict[str, Any]:
        return redact_internal_references(
            {
                "code": self.code,
                "public_message": self.public_message,
                "retryable": self.retryable,
            }
        )


BLOCKED_REASONS: dict[BlockedReason, ReasonCode] = {
    BlockedReason.POLICY: ReasonCode(
        code="policy",
        public_message="The request was blocked by policy.",
        retryable=False,
    ),
    BlockedReason.TOOL: ReasonCode(
        code="tool",
        public_message="A required tool is unavailable.",
        retryable=True,
    ),
    BlockedReason.ENVIRONMENT: ReasonCode(
        code="environment",
        public_message="The runtime environment does not meet requirements.",
        retryable=True,
    ),
    BlockedReason.SAMPLE_FORMAT: ReasonCode(
        code="sample_format",
        public_message="The uploaded sample format is not supported.",
        retryable=False,
    ),
    BlockedReason.UNSUPPORTED: ReasonCode(
        code="unsupported",
        public_message="This operation is not supported.",
        retryable=False,
    ),
}


FAILED_REASONS: dict[FailedReason, ReasonCode] = {
    FailedReason.POLICY: ReasonCode(
        code="policy",
        public_message="The operation failed due to a policy violation.",
        retryable=False,
    ),
    FailedReason.TOOL: ReasonCode(
        code="tool",
        public_message="The operation failed because a required tool errored.",
        retryable=True,
    ),
    FailedReason.ENVIRONMENT: ReasonCode(
        code="environment",
        public_message="The operation failed due to an environment error.",
        retryable=True,
    ),
    FailedReason.SAMPLE_FORMAT: ReasonCode(
        code="sample_format",
        public_message="The operation failed because the sample format was invalid.",
        retryable=False,
    ),
    FailedReason.UNSUPPORTED: ReasonCode(
        code="unsupported",
        public_message="The operation failed because it is unsupported.",
        retryable=False,
    ),
    FailedReason.ANALYSIS: ReasonCode(
        code="analysis",
        public_message="The operation failed during analysis.",
        retryable=False,
    ),
    FailedReason.VALIDATION: ReasonCode(
        code="validation",
        public_message="The operation failed during validation.",
        retryable=False,
    ),
}


@dataclass(frozen=True)
class UserSolveError:
    code: str
    public_message: str
    retryable: bool = False
    developer_diagnostics: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not str(self.code or "").strip():
            raise ValueError("error code must be non-empty")
        if contains_internal_reference(self.public_message):
            raise ValueError("public error message cannot contain internal references")

    def to_user_dict(self) -> dict[str, Any]:
        return redact_internal_references(
            {
                "code": self.code,
                "public_message": self.public_message,
                "retryable": self.retryable,
            }
        )

    def to_developer_dict(self) -> dict[str, Any]:
        payload = self.to_user_dict()
        payload["developer_diagnostics"] = dict(self.developer_diagnostics)
        return payload


ERRORS: dict[str, UserSolveError] = {
    "fixture_not_found": UserSolveError(
        code="fixture_not_found",
        public_message="That local demo fixture is not available.",
        retryable=False,
    ),
    "route_not_found": UserSolveError(
        code="route_not_found",
        public_message="That local demo route is not available.",
        retryable=False,
    ),
    "method_not_allowed": UserSolveError(
        code="method_not_allowed",
        public_message="That local demo route does not support this method.",
        retryable=False,
    ),
    "unsafe_request": UserSolveError(
        code="unsafe_request",
        public_message="The request is outside the fixture-only local demo boundary.",
        retryable=False,
    ),
}


def blocked_reason_payload(reason: BlockedReason | str) -> dict[str, Any]:
    if isinstance(reason, BlockedReason):
        key = reason
    else:
        try:
            key = BlockedReason(reason)
        except ValueError:
            key = BlockedReason.UNSUPPORTED
    base = BLOCKED_REASONS.get(key, BLOCKED_REASONS[BlockedReason.UNSUPPORTED])
    return base.to_user_dict()


def failed_reason_payload(reason: FailedReason | str) -> dict[str, Any]:
    if isinstance(reason, FailedReason):
        key = reason
    else:
        try:
            key = FailedReason(reason)
        except ValueError:
            key = FailedReason.ANALYSIS
    base = FAILED_REASONS.get(key, FAILED_REASONS[FailedReason.ANALYSIS])
    return base.to_user_dict()


def error_payload(code: str, *, developer_diagnostics: dict[str, Any] | None = None) -> dict[str, Any]:
    base = ERRORS.get(code, ERRORS["unsafe_request"])
    error = UserSolveError(
        code=base.code,
        public_message=base.public_message,
        retryable=base.retryable,
        developer_diagnostics=developer_diagnostics or {},
    )
    return error.to_user_dict()
