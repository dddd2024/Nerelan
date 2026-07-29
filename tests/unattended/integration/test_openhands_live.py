from __future__ import annotations

import os

import pytest

from reverse_agent.unattended.openhands import OpenHandsAdapter, UrllibJsonTransport


@pytest.mark.skipif(
    os.environ.get("UNATTENDED_OPENHANDS_INTEGRATION") != "1",
    reason="set UNATTENDED_OPENHANDS_INTEGRATION=1 for the pinned live stack",
)
def test_selected_openhands_health_surface() -> None:
    adapter = OpenHandsAdapter(
        UrllibJsonTransport(
            os.environ.get("OPENHANDS_BASE_URL", "http://localhost:8000"),
            session_api_key=os.environ.get("OH_SESSION_API_KEYS_0"),
        )
    )
    assert adapter.health() == {"/alive": "PASS", "/health": "PASS"}
