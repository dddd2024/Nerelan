from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Iterable

from .user_solve_contract import UserSolveMode, contains_internal_reference, redact_internal_references


_SAFE_INPUT_KINDS = {"fixture", "demo", "synthetic"}
_UNSAFE_REFERENCE_MARKERS = (
    ":\\",
    "://",
    "project_state/",
    "project_state\\",
    "solve_reports/",
    "solve_reports\\",
    "training_materials/",
    "training_materials\\",
)


def _clean_list(values: Iterable[str] | None) -> list[str]:
    return [str(item) for item in (values or []) if str(item).strip()]


def _contains_unsafe_reference(value: Any) -> bool:
    text = str(value).lower()
    return contains_internal_reference(value) or any(marker.lower() in text for marker in _UNSAFE_REFERENCE_MARKERS)


@dataclass(frozen=True)
class UserSolveRequest:
    request_id: str
    mode: UserSolveMode | str = UserSolveMode.AUTO
    input_kind: str = "fixture"
    fixture_name: str = "candidate"
    candidate: str = ""
    missing_evidence: list[str] = field(default_factory=list)
    public_context: dict[str, Any] = field(default_factory=dict)
    developer_context_refs: list[str] = field(default_factory=list)
    persistent_session_requested: bool = False

    def __post_init__(self) -> None:
        if not str(self.request_id or "").strip():
            raise ValueError("request_id must be non-empty")
        mode = self.mode if isinstance(self.mode, UserSolveMode) else UserSolveMode(str(self.mode))
        object.__setattr__(self, "mode", mode)
        input_kind = str(self.input_kind or "").strip().lower()
        if input_kind not in _SAFE_INPUT_KINDS:
            raise ValueError("input_kind must be fixture, demo, or synthetic")
        object.__setattr__(self, "input_kind", input_kind)
        object.__setattr__(self, "missing_evidence", _clean_list(self.missing_evidence))
        object.__setattr__(self, "developer_context_refs", _clean_list(self.developer_context_refs))
        if self.persistent_session_requested:
            raise ValueError("persistent user sessions are not supported by the offline control plane")
        if _contains_unsafe_reference(self.fixture_name) or _contains_unsafe_reference(self.candidate):
            raise ValueError("request user fields cannot contain local paths or internal project references")
        if _contains_unsafe_reference(self.public_context):
            raise ValueError("public request context cannot contain local paths or internal project references")

    def to_user_dict(self) -> dict[str, Any]:
        payload = {
            "request_id": self.request_id,
            "mode": self.mode.value,
            "input_kind": self.input_kind,
            "fixture_name": self.fixture_name,
            "candidate": self.candidate,
            "missing_evidence": list(self.missing_evidence),
            "public_context": dict(self.public_context),
        }
        return redact_internal_references(payload)

    def to_developer_dict(self) -> dict[str, Any]:
        payload = self.to_user_dict()
        payload["developer_context_refs"] = list(self.developer_context_refs)
        payload["persistent_session_requested"] = self.persistent_session_requested
        return payload


def demo_request(name: str) -> UserSolveRequest:
    demo = str(name or "").strip().lower().replace("_", "-")
    if demo in {"candidate", "candidate-found"}:
        return UserSolveRequest(
            request_id="demo-candidate",
            mode=UserSolveMode.FAST,
            input_kind="fixture",
            fixture_name="candidate",
            candidate="flag{demo_candidate}",
            public_context={"source": "fixture"},
        )
    if demo in {"missing-evidence", "missing_evidence", "missing"}:
        return UserSolveRequest(
            request_id="demo-missing-evidence",
            mode=UserSolveMode.FAST,
            input_kind="fixture",
            fixture_name="missing-evidence",
            missing_evidence=["targeted_decompile_missing"],
            public_context={"source": "fixture"},
        )
    if demo == "blocked":
        return UserSolveRequest(
            request_id="demo-blocked",
            mode=UserSolveMode.AUTO,
            input_kind="fixture",
            fixture_name="blocked",
            public_context={"source": "fixture"},
        )
    if demo == "failed":
        return UserSolveRequest(
            request_id="demo-failed",
            mode=UserSolveMode.FAST,
            input_kind="fixture",
            fixture_name="failed",
            public_context={"source": "fixture"},
        )
    if demo == "verified":
        return UserSolveRequest(
            request_id="demo-verified",
            mode=UserSolveMode.FAST,
            input_kind="fixture",
            fixture_name="verified",
            candidate="flag{demo_verified}",
            public_context={"source": "fixture"},
        )
    raise ValueError("demo must be candidate, missing-evidence, blocked, failed, or verified")
