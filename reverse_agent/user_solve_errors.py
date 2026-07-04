from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from .user_solve_contract import contains_internal_reference, redact_internal_references


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


def error_payload(code: str, *, developer_diagnostics: dict[str, Any] | None = None) -> dict[str, Any]:
    base = ERRORS.get(code, ERRORS["unsafe_request"])
    error = UserSolveError(
        code=base.code,
        public_message=base.public_message,
        retryable=base.retryable,
        developer_diagnostics=developer_diagnostics or {},
    )
    return error.to_user_dict()
