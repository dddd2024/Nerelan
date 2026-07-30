from __future__ import annotations

import asyncio
import os
import uuid

import pytest

from reverse_agent.unattended.probe import run_temporal_probe


@pytest.mark.skipif(
    os.environ.get("UNATTENDED_TEMPORAL_INTEGRATION") != "1",
    reason="set UNATTENDED_TEMPORAL_INTEGRATION=1 for the pinned live stack",
)
def test_temporal_activity_and_replay_against_pinned_stack() -> None:
    report = asyncio.run(
        run_temporal_probe(
            address=os.environ.get("TEMPORAL_ADDRESS", "localhost:7233"),
            namespace=os.environ.get("TEMPORAL_NAMESPACE", "default"),
            probe_workflow_id=f"unattended:gate2/integration:issue:76:{uuid.uuid4().hex}",
        )
    )
    assert report["temporal_connection"] == "PASS"
    assert report["activity_execution"] == "PASS"
    assert report["workflow_history_secret_scan"] == "PASS"
    assert report["workflow_replay"] == "PASS"
    assert report["cleanup"] == "PASS"
    assert report["result"]["verdict"] == "PROVIDER_FREE_RUNTIME_PROOF"
