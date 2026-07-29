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
    executor_key_file = os.environ.get("UNATTENDED_LITELLM_EXECUTOR_KEY_FILE")
    if not executor_key_file:
        pytest.fail("UNATTENDED_LITELLM_EXECUTOR_KEY_FILE is required")
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
        executor_api_key=Path(executor_key_file).read_text(encoding="utf-8").strip(),
    )
    assert adapter.health() == {"/alive": "PASS", "/health": "PASS"}
