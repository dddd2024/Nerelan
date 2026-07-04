from __future__ import annotations

from dataclasses import dataclass, field
from enum import StrEnum
from typing import Any, Iterable, Mapping

from .user_solve_contract import redact_internal_references


class ToolCategory(StrEnum):
    STATIC = "static"
    DYNAMIC = "dynamic"
    SOLVER = "solver"
    VALIDATION = "validation"


class ToolAvailability(StrEnum):
    AVAILABLE = "available"
    MISSING = "missing"
    DISABLED = "disabled"


class ToolRiskLevel(StrEnum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


@dataclass(frozen=True)
class ToolProfile:
    tool_id: str
    label: str
    category: ToolCategory
    path_source: str
    availability: ToolAvailability
    capability_flags: tuple[str, ...] = field(default_factory=tuple)
    risk_level: ToolRiskLevel = ToolRiskLevel.LOW
    disabled_reason: str = ""
    unavailable_reason: str = ""

    def __post_init__(self) -> None:
        tool_id = str(self.tool_id or "").strip()
        label = str(self.label or "").strip()
        path_source = str(self.path_source or "").strip()
        if not tool_id:
            raise ValueError("tool_id must be non-empty")
        if not label:
            raise ValueError("label must be non-empty")
        if path_source and (":\\" in path_source or path_source.startswith("/")):
            raise ValueError("path_source must be a portable source label, not a local path")
        object.__setattr__(self, "tool_id", tool_id)
        object.__setattr__(self, "label", label)
        object.__setattr__(self, "path_source", path_source or "metadata")
        object.__setattr__(self, "category", ToolCategory(self.category))
        object.__setattr__(self, "availability", ToolAvailability(self.availability))
        object.__setattr__(self, "risk_level", ToolRiskLevel(self.risk_level))
        flags = tuple(sorted({str(item).strip() for item in self.capability_flags if str(item).strip()}))
        object.__setattr__(self, "capability_flags", flags)
        if self.availability == ToolAvailability.DISABLED and not str(self.disabled_reason or "").strip():
            raise ValueError("disabled tools must include disabled_reason")
        if self.availability == ToolAvailability.MISSING and not str(self.unavailable_reason or "").strip():
            raise ValueError("missing tools must include unavailable_reason")

    @property
    def can_execute_by_default(self) -> bool:
        return self.availability == ToolAvailability.AVAILABLE and self.risk_level == ToolRiskLevel.LOW

    def to_dict(self) -> dict[str, Any]:
        return redact_internal_references(
            {
                "tool_id": self.tool_id,
                "label": self.label,
                "category": self.category.value,
                "path_source": self.path_source,
                "availability": self.availability.value,
                "capability_flags": list(self.capability_flags),
                "risk_level": self.risk_level.value,
                "disabled_reason": self.disabled_reason,
                "unavailable_reason": self.unavailable_reason,
                "can_execute_by_default": self.can_execute_by_default,
            }
        )


def default_tool_profiles() -> tuple[ToolProfile, ...]:
    return (
        ToolProfile(
            tool_id="fast_strings",
            label="Fast strings scan",
            category=ToolCategory.STATIC,
            path_source="built_in_metadata",
            availability=ToolAvailability.AVAILABLE,
            capability_flags=("static_strings", "fixture_preview"),
            risk_level=ToolRiskLevel.LOW,
        ),
        ToolProfile(
            tool_id="ida_summary",
            label="IDA summary",
            category=ToolCategory.STATIC,
            path_source="user_config_placeholder",
            availability=ToolAvailability.MISSING,
            capability_flags=("ida_summary", "targeted_static_analysis"),
            risk_level=ToolRiskLevel.LOW,
            unavailable_reason="not_configured_for_fixture_preview",
        ),
        ToolProfile(
            tool_id="runtime_validation",
            label="Runtime validation",
            category=ToolCategory.VALIDATION,
            path_source="permission_controlled_runner",
            availability=ToolAvailability.DISABLED,
            capability_flags=("runtime_validation",),
            risk_level=ToolRiskLevel.HIGH,
            disabled_reason="real_sample_execution_forbidden_this_round",
        ),
    )


def load_tool_profiles(overrides: Iterable[Mapping[str, Any]] | None = None) -> tuple[ToolProfile, ...]:
    profiles = {profile.tool_id: profile for profile in default_tool_profiles()}
    for raw in overrides or []:
        profile = ToolProfile(
            tool_id=str(raw.get("tool_id") or ""),
            label=str(raw.get("label") or ""),
            category=raw.get("category") or ToolCategory.STATIC,
            path_source=str(raw.get("path_source") or "config"),
            availability=raw.get("availability") or ToolAvailability.MISSING,
            capability_flags=tuple(raw.get("capability_flags") or ()),
            risk_level=raw.get("risk_level") or ToolRiskLevel.LOW,
            disabled_reason=str(raw.get("disabled_reason") or ""),
            unavailable_reason=str(raw.get("unavailable_reason") or ""),
        )
        profiles[profile.tool_id] = profile
    return tuple(profiles[key] for key in sorted(profiles))


def tool_profile_snapshot(profiles: Iterable[ToolProfile] | None = None) -> dict[str, Any]:
    items = tuple(profiles or load_tool_profiles())
    return {
        "schema_version": 1,
        "fixture_only": True,
        "executes_tools": False,
        "deterministic_precedence": ["defaults", "explicit_overrides_by_tool_id"],
        "profiles": [item.to_dict() for item in items],
    }
