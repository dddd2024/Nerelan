"""Manual acceptance wrapper: kill -9 → recover → invariants hold.

Skipped unless ``NERELAN_RUN_KILL9=1``: it starts a real child process and kills
it, which is too heavy and too flaky for the default CI selection. Run it with:

    NERELAN_RUN_KILL9=1 python -m pytest tests/platform_v1/test_kill9_acceptance.py -q

The script itself is ``scripts/lease_kill9_check.py``; this wrapper exists so the
acceptance is discoverable, and so a long-running unattended window can include
it deliberately.
"""
from __future__ import annotations

import os
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

pytestmark = pytest.mark.skipif(
    os.environ.get("NERELAN_RUN_KILL9") != "1",
    reason="set NERELAN_RUN_KILL9=1 to run the real kill -9 acceptance")


def test_kill9_recovery_keeps_the_lease_invariants():
    from scripts.lease_kill9_check import run

    verdict = run(keep=False)
    checks = verdict.get("checks") or {}
    assert verdict.get("error") is None, verdict.get("error")
    # The dead executor really ran before it was killed.
    assert checks["marker_written_before_kill"] is True
    # I1/I2/F1 across a real process boundary.
    assert checks["epoch_advanced_by_one"] is True
    assert checks["old_owner_fenced"] is True
    assert checks["dead_owner_write_refused"] is True
    assert checks["dead_owner_evidence_absent"] is True
    assert checks["workspace_taken_over"] is True
    assert checks["no_second_run"] is True
    assert verdict["ok"] is True
