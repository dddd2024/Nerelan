from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from .user_solve_contract import contains_internal_reference, redact_internal_references
from .user_solve_handoff import UserSolveHandoffPacket
from .user_solve_request import UserSolveRequest
from .user_solve_session import UserSolveSessionBundle


@dataclass(frozen=True)
class UserSolveResponseEnvelope:
    request: UserSolveRequest
    session: UserSolveSessionBundle
    handoff: UserSolveHandoffPacket
    warnings: list[str] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)
    developer_audit: dict[str, Any] = field(default_factory=dict)

    def to_user_dict(self) -> dict[str, Any]:
        session_payload = self.session.to_user_dict()
        result = session_payload["result"]
        payload = {
            "request": self.request.to_user_dict(),
            "status": result["status"],
            "answer": result.get("answer", ""),
            "candidates": result.get("candidates", []),
            "confidence": result.get("confidence"),
            "validation_status": session_payload["validation_status"],
            "evidence_status": session_payload["evidence_status"],
            "public_message": session_payload["public_message"],
            "next_action": session_payload["next_action"],
            "fallback_summary": session_payload["fallback_decision"],
            "handoff": self.handoff.to_user_dict(),
            "warnings": list(self.warnings),
            "errors": list(self.errors),
        }
        return redact_internal_references(payload)

    def to_developer_dict(self) -> dict[str, Any]:
        payload = self.to_user_dict()
        payload["session"] = self.session.to_developer_dict()
        payload["handoff"] = self.handoff.to_developer_dict()
        payload["developer_audit"] = dict(self.developer_audit)
        return payload

    def validate_user_safe(self) -> None:
        if contains_internal_reference(self.to_user_dict()):
            raise ValueError("response user serialization leaked an internal reference")


def build_response_envelope(
    *,
    request: UserSolveRequest,
    session: UserSolveSessionBundle,
    handoff: UserSolveHandoffPacket,
    warnings: list[str] | None = None,
    errors: list[str] | None = None,
    developer_audit: dict[str, Any] | None = None,
) -> UserSolveResponseEnvelope:
    envelope = UserSolveResponseEnvelope(
        request=request,
        session=session,
        handoff=handoff,
        warnings=[str(item) for item in (warnings or []) if str(item).strip()],
        errors=[str(item) for item in (errors or []) if str(item).strip()],
        developer_audit=dict(developer_audit or {}),
    )
    envelope.validate_user_safe()
    return envelope
