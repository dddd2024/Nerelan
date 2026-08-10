from __future__ import annotations

import re
from pathlib import Path


REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
STATE_GATE_WORKFLOW = REPOSITORY_ROOT / ".github" / "workflows" / "state-gate.yml"


def _job_block(workflow: str, job_name: str) -> str:
    match = re.search(
        rf"(?ms)^  {re.escape(job_name)}:\n(?P<body>.*?)(?=^  [A-Za-z0-9_-]+:\n|\Z)",
        workflow,
    )
    assert match is not None, f"workflow job not found: {job_name}"
    return match.group("body")


def _first_checkout_block(job: str) -> str:
    match = re.search(
        r"(?ms)^      - name: Checkout\n(?P<body>.*?)(?=^      - name: |\Z)",
        job,
    )
    assert match is not None, "main State Gate Checkout step not found"
    return match.group("body")


def test_main_state_gate_checkout_binds_exact_pr_head_with_sha_fallback() -> None:
    workflow = STATE_GATE_WORKFLOW.read_text(encoding="utf-8")
    state_gate_job = _job_block(workflow, "state-gate")
    checkout = _first_checkout_block(state_gate_job)

    assert "ref: ${{ github.event.pull_request.head.sha || github.sha }}" in checkout
    assert "github.event.pull_request.head.sha" in checkout
    assert "github.sha" in checkout
