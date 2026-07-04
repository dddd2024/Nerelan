from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Mapping

from .user_solve_contract import contains_internal_reference, redact_internal_references


@dataclass(frozen=True)
class WorkbenchTaskTrace:
    trace_id: str
    request_id: str
    fixture_name: str
    source: str
    status: str
    validation_state: str
    candidate_state: str
    missing_evidence: tuple[str, ...] = field(default_factory=tuple)
    route_plan: Mapping[str, Any] = field(default_factory=dict)
    artifact_placeholders: tuple[str, ...] = field(default_factory=tuple)
    persisted: bool = False

    def __post_init__(self) -> None:
        if self.persisted:
            raise ValueError("workbench task traces must not persist task/session files")
        for field_name in ("trace_id", "request_id", "fixture_name", "source", "status"):
            if not str(getattr(self, field_name) or "").strip():
                raise ValueError(f"{field_name} must be non-empty")
        object.__setattr__(self, "missing_evidence", tuple(str(item) for item in self.missing_evidence if str(item).strip()))
        object.__setattr__(
            self,
            "artifact_placeholders",
            tuple(str(item) for item in self.artifact_placeholders if str(item).strip()),
        )

    def to_user_dict(self) -> dict[str, Any]:
        payload = {
            "trace_id": self.trace_id,
            "request_id": self.request_id,
            "fixture_name": self.fixture_name,
            "source": self.source,
            "status": self.status,
            "validation_state": self.validation_state,
            "candidate_state": self.candidate_state,
            "missing_evidence": list(self.missing_evidence),
            "route_plan": dict(self.route_plan),
            "artifact_placeholders": list(self.artifact_placeholders),
            "persisted": self.persisted,
            "fixture_only": True,
        }
        return redact_internal_references(payload)

    def to_developer_dict(self) -> dict[str, Any]:
        payload = self.to_user_dict()
        payload["developer_trace_kind"] = "synthetic_workbench_trace"
        return payload


def build_workbench_task_trace(
    *,
    fixture_name: str,
    response: Mapping[str, Any],
    route_plan: Mapping[str, Any],
) -> WorkbenchTaskTrace:
    request = response.get("request") if isinstance(response.get("request"), Mapping) else {}
    candidates = response.get("candidates") if isinstance(response.get("candidates"), list) else []
    fallback = response.get("fallback_summary") if isinstance(response.get("fallback_summary"), Mapping) else {}
    trace = WorkbenchTaskTrace(
        trace_id=f"trace-{fixture_name}",
        request_id=str(request.get("request_id") or f"demo-{fixture_name}"),
        fixture_name=fixture_name,
        source="fixture_catalog",
        status=str(response.get("status") or "ready"),
        validation_state=str(response.get("validation_status") or "unavailable"),
        candidate_state="present" if response.get("answer") or candidates else "absent",
        missing_evidence=tuple(fallback.get("missing_evidence") or ()),
        route_plan=route_plan,
        artifact_placeholders=("gate_snapshot_only",),
    )
    if contains_internal_reference(trace.to_user_dict()):
        raise ValueError("workbench trace user serialization leaked an internal reference")
    return trace
