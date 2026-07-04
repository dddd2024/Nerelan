from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Iterable

from .tool_profiles import ToolAvailability, ToolProfile, load_tool_profiles
from .user_solve_contract import redact_internal_references


@dataclass(frozen=True)
class RunnerCapability:
    runner_id: str
    platform: str
    available_tools: tuple[str, ...] = field(default_factory=tuple)
    missing_tools: tuple[str, ...] = field(default_factory=tuple)
    disabled_tools: tuple[str, ...] = field(default_factory=tuple)
    permission_flags: tuple[str, ...] = field(default_factory=tuple)
    supported_features: tuple[str, ...] = field(default_factory=tuple)
    can_dispatch: bool = False
    executes_external_tools: bool = False

    def __post_init__(self) -> None:
        if not str(self.runner_id or "").strip():
            raise ValueError("runner_id must be non-empty")
        object.__setattr__(self, "available_tools", tuple(sorted(set(self.available_tools))))
        object.__setattr__(self, "missing_tools", tuple(sorted(set(self.missing_tools))))
        object.__setattr__(self, "disabled_tools", tuple(sorted(set(self.disabled_tools))))
        object.__setattr__(self, "permission_flags", tuple(sorted(set(self.permission_flags))))
        object.__setattr__(self, "supported_features", tuple(sorted(set(self.supported_features))))
        if self.can_dispatch or self.executes_external_tools:
            raise ValueError("fixture workbench capability cannot dispatch or execute tools")

    def to_dict(self) -> dict[str, Any]:
        return redact_internal_references(
            {
                "runner_id": self.runner_id,
                "platform": self.platform,
                "available_tools": list(self.available_tools),
                "missing_tools": list(self.missing_tools),
                "disabled_tools": list(self.disabled_tools),
                "permission_flags": list(self.permission_flags),
                "supported_features": list(self.supported_features),
                "can_dispatch": self.can_dispatch,
                "executes_external_tools": self.executes_external_tools,
            }
        )


def capability_from_profiles(
    profiles: Iterable[ToolProfile] | None = None,
    *,
    runner_id: str = "fixture-local-workbench",
    platform: str = "local_metadata_only",
) -> RunnerCapability:
    items = tuple(profiles or load_tool_profiles())
    available = tuple(item.tool_id for item in items if item.availability == ToolAvailability.AVAILABLE)
    missing = tuple(item.tool_id for item in items if item.availability == ToolAvailability.MISSING)
    disabled = tuple(item.tool_id for item in items if item.availability == ToolAvailability.DISABLED)
    features = sorted({flag for item in items for flag in item.capability_flags if item.availability == ToolAvailability.AVAILABLE})
    return RunnerCapability(
        runner_id=runner_id,
        platform=platform,
        available_tools=available,
        missing_tools=missing,
        disabled_tools=disabled,
        permission_flags=("fixture_only", "no_real_sample_execution", "no_remote_dispatch"),
        supported_features=tuple(features),
    )


def capability_snapshot(profiles: Iterable[ToolProfile] | None = None) -> dict[str, Any]:
    capability = capability_from_profiles(profiles)
    return {
        "schema_version": 1,
        "fixture_only": True,
        "capability": capability.to_dict(),
    }
