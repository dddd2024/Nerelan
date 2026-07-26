"""Stable fail-closed errors for the base-platform protocol boundary."""

from __future__ import annotations

from dataclasses import dataclass
from types import MappingProxyType
from typing import Any, Mapping


@dataclass(frozen=True)
class BasePlatformError(ValueError):
    """Validation or policy failure with a stable machine-readable code."""

    code: str
    message: str
    details: Mapping[str, Any] | None = None

    def __post_init__(self) -> None:
        if not self.code or not self.code.replace("_", "").isalnum():
            raise ValueError("invalid_error_code")
        frozen_details = MappingProxyType(dict(self.details or {}))
        object.__setattr__(self, "details", frozen_details)
        ValueError.__init__(self, f"{self.code}: {self.message}")

    def to_dict(self) -> dict[str, Any]:
        return {
            "code": self.code,
            "message": self.message,
            "details": dict(self.details or {}),
        }


def fail(code: str, message: str, **details: Any) -> None:
    raise BasePlatformError(code=code, message=message, details=details)
