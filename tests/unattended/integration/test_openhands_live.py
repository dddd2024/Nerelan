from __future__ import annotations

import os
from pathlib import Path

import pytest

from reverse_agent.unattended.openhands import OpenHandsAdapter, UrllibJsonTransport


@pytest.mark.skipif(
    os.environ.get("UNATTENDED_OPENHANDS_INTEGRATION") != "1",
    reason="set UNATTENDED_OPENHANDS_INTEGRATION=1 for the pinned live stack",
)
def test_selected_openhands_health_surface() -> None:
    adapter = OpenHandsAdapter(
        UrllibJsonTransport(
            os.environ.get(
                "ATTEMPT_AGENT_SERVER_BASE_URL", "http://localhost:8000"
            ),
            session_api_key=os.environ.get("ATTEMPT_SESSION_API_KEY"),
        ),
        host_workspace_root=Path(
            os.environ.get("UNATTENDED_WORKSPACE_ROOT", ".var/unattended")
        ).absolute(),
    )
    assert adapter.health() == {"/alive": "PASS", "/health": "PASS"}
