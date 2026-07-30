from __future__ import annotations

from pathlib import Path

from reverse_agent.unattended.cli import main
from reverse_agent.unattended.readiness_probe import run_direct_readiness_probe


def test_direct_readiness_probe_rejects_unbounded_project_without_docker(
    tmp_path: Path,
) -> None:
    report = run_direct_readiness_probe(
        repository_root=tmp_path,
        compose_project="../unbounded",
    )
    assert report == {
        "status": "FAIL",
        "readiness": "FAIL",
        "states": (),
        "poll_count": 0,
        "deadline_seconds": 90,
        "max_poll_interval_milliseconds": 3000,
        "cleanup": "PASS",
        "failure_category": "compose_project_invalid",
    }


def test_cli_requires_bounded_compose_project() -> None:
    try:
        main(("attempt-readiness-probe",))
    except SystemExit as error:
        assert error.code == 2
    else:
        raise AssertionError("missing compose project accepted")
