from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from .user_solve import FastSolveWrapper
from .user_solve_handoff import build_handoff_packet
from .user_solve_request import UserSolveRequest
from .user_solve_response import UserSolveResponseEnvelope, build_response_envelope


@dataclass
class UserSolveController:
    wrapper: FastSolveWrapper = field(default_factory=FastSolveWrapper)

    def solve(self, request: UserSolveRequest) -> UserSolveResponseEnvelope:
        payload = self._fixture_payload(request)
        session = self.wrapper.adapt_session_bundle(payload)
        handoff = build_handoff_packet(session)
        return build_response_envelope(
            request=request,
            session=session,
            handoff=handoff,
            warnings=["fixture_only_preview"],
            developer_audit={
                "controller": "UserSolveController",
                "fixture_only": True,
                "executes_external_tools": False,
                "persists_user_sessions": False,
                "processes_real_binaries": False,
                "dispatches_remote_work": False,
            },
        )

    @staticmethod
    def _fixture_payload(request: UserSolveRequest) -> dict[str, Any]:
        base: dict[str, Any] = {
            "session_id": request.request_id,
            "task_id": request.request_id,
            "mode": request.mode,
            "public_message": "Offline fixture preview only.",
            "developer_trace_ref": "offline_control_plane_fixture",
        }
        if request.candidate:
            return {
                **base,
                "selected_candidate": request.candidate,
                "confidence": 0.64,
                "validation_status": "pending",
            }
        return {
            **base,
            "missing_evidence": list(request.missing_evidence or ["targeted_decompile_missing"]),
        }
