from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from .user_solve_contract import contains_internal_reference, redact_internal_references
from .user_solve_session import UserSolveSessionBundle


@dataclass(frozen=True)
class UserSolveHandoffPacket:
    handoff_id: str
    session_id: str
    user_summary: dict[str, Any]
    next_action: dict[str, Any]
    fallback_summary: dict[str, Any]
    developer_audit_refs: list[str] = field(default_factory=list)

    def __post_init__(self) -> None:
        if not str(self.handoff_id or "").strip():
            raise ValueError("handoff_id must be non-empty")
        if not str(self.session_id or "").strip():
            raise ValueError("session_id must be non-empty")
        if contains_internal_reference(self.to_user_dict()):
            raise ValueError("handoff user serialization leaked an internal reference")

    def to_user_dict(self) -> dict[str, Any]:
        return redact_internal_references(
            {
                "handoff_id": self.handoff_id,
                "session_id": self.session_id,
                "user_summary": dict(self.user_summary),
                "next_action": dict(self.next_action),
                "fallback_summary": dict(self.fallback_summary),
            }
        )

    def to_developer_dict(self) -> dict[str, Any]:
        payload = self.to_user_dict()
        payload["developer_audit_refs"] = list(self.developer_audit_refs)
        return payload


def build_handoff_packet(
    session: UserSolveSessionBundle,
    *,
    handoff_id: str | None = None,
) -> UserSolveHandoffPacket:
    user_payload = session.to_user_dict()
    developer_payload = session.to_developer_dict()
    return UserSolveHandoffPacket(
        handoff_id=handoff_id or f"handoff-{session.session_id}",
        session_id=session.session_id,
        user_summary={
            "status": user_payload["result"]["status"],
            "validation_status": user_payload["validation_status"],
            "evidence_status": user_payload["evidence_status"],
            "public_message": user_payload["public_message"],
        },
        next_action=user_payload["next_action"] or {},
        fallback_summary=user_payload["fallback_decision"],
        developer_audit_refs=[
            *developer_payload.get("developer_trace_refs", []),
            *developer_payload.get("artifact_references", []),
        ],
    )
