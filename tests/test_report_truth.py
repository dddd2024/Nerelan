from __future__ import annotations

import pytest

from reverse_agent.architecture.report_truth import (
    ChangedFileInventory,
    RemoteObservation,
    ReportTruth,
)


# --- Test 14: changed-file inventory matches Git diff ---------------------


def test_changed_file_inventory_parsed_from_git_diff_name_only() -> None:
    """The inventory must come from the real ``git diff --name-only`` output."""

    diff = (
        "reverse_agent/control_plane/transition.py\n"
        "reverse_agent/architecture/risk_classifier.py\n"
        "tests/test_report_truth.py\n"
    )
    inventory = ChangedFileInventory.from_git_diff(
        diff,
        base_sha="a" * 40,
        head_sha="b" * 40,
    )
    assert inventory.paths == (
        "reverse_agent/control_plane/transition.py",
        "reverse_agent/architecture/risk_classifier.py",
        "tests/test_report_truth.py",
    )
    assert inventory.source == "git_diff_name_only"
    assert inventory.base_sha == "a" * 40
    assert inventory.head_sha == "b" * 40


def test_changed_file_inventory_strips_blank_lines_and_whitespace() -> None:
    diff = "  reverse_agent/example.py  \n\n\n  tests/test_example.py  \n"
    inventory = ChangedFileInventory.from_git_diff(
        diff,
        base_sha="a" * 40,
        head_sha="b" * 40,
    )
    assert inventory.paths == ("reverse_agent/example.py", "tests/test_example.py")


def test_changed_file_inventory_rejects_empty_diff() -> None:
    """An empty diff must fail closed rather than masquerade as no-op."""

    with pytest.raises(ValueError, match="empty_diff"):
        ChangedFileInventory.from_git_diff(
            "",
            base_sha="a" * 40,
            head_sha="b" * 40,
        )


def test_changed_file_inventory_rejects_identical_base_and_head() -> None:
    with pytest.raises(ValueError, match="identical_base_and_head"):
        ChangedFileInventory.from_git_diff(
            "reverse_agent/example.py\n",
            base_sha="a" * 40,
            head_sha="a" * 40,
        )


# --- Test 15: remote status is internally consistent ----------------------


def test_report_truth_blocks_when_remote_simultaneously_observed_and_pending() -> None:
    """The report must not claim exact-head checks are both observed and pending."""

    inventory = ChangedFileInventory(
        paths=("reverse_agent/example.py",),
        source="git_diff_name_only",
        base_sha="a" * 40,
        head_sha="b" * 40,
    )
    observation = RemoteObservation(
        head_sha="b" * 40,
        observed_at="2026-07-21T00:00:00Z",
        ci_status="REMOTE_PASSED",
        state_gate_status="REMOTE_PENDING",
        decision_preflight_status="REMOTE_PASSED",
    )
    truth = ReportTruth(
        changed_files=inventory,
        local_status="LOCAL_VALIDATED",
        remote_observation=observation,
    )
    assert truth.is_internally_consistent() is False
    reasons = truth.consistency_violations()
    assert any("remote_status_contradiction" in reason for reason in reasons)


def test_report_truth_consistent_when_all_remote_statuses_align() -> None:
    inventory = ChangedFileInventory(
        paths=("reverse_agent/example.py",),
        source="git_diff_name_only",
        base_sha="a" * 40,
        head_sha="b" * 40,
    )
    observation = RemoteObservation(
        head_sha="b" * 40,
        observed_at="2026-07-21T00:00:00Z",
        ci_status="REMOTE_PASSED",
        state_gate_status="REMOTE_PASSED",
        decision_preflight_status="REMOTE_PASSED",
    )
    truth = ReportTruth(
        changed_files=inventory,
        local_status="LOCAL_VALIDATED",
        remote_observation=observation,
    )
    assert truth.is_internally_consistent() is True
    assert truth.consistency_violations() == ()


def test_report_truth_consistent_when_remote_not_observed() -> None:
    """``REMOTE_NOT_OBSERVED`` for all three signals is internally consistent."""

    inventory = ChangedFileInventory(
        paths=("reverse_agent/example.py",),
        source="git_diff_name_only",
        base_sha="a" * 40,
        head_sha="b" * 40,
    )
    observation = RemoteObservation(
        head_sha="",
        observed_at="",
        ci_status="REMOTE_NOT_OBSERVED",
        state_gate_status="REMOTE_NOT_OBSERVED",
        decision_preflight_status="REMOTE_NOT_OBSERVED",
    )
    truth = ReportTruth(
        changed_files=inventory,
        local_status="LOCAL_VALIDATED",
        remote_observation=observation,
    )
    assert truth.is_internally_consistent() is True


# --- Test 16: stale observation cannot support a new head ---------------


def test_stale_remote_observation_cannot_support_new_head() -> None:
    """If remote observation was for an old head, the report is not truthful."""

    inventory = ChangedFileInventory(
        paths=("reverse_agent/example.py",),
        source="git_diff_name_only",
        base_sha="a" * 40,
        head_sha="c" * 40,  # current head is c
    )
    observation = RemoteObservation(
        head_sha="b" * 40,  # observed against older head b
        observed_at="2026-07-20T00:00:00Z",
        ci_status="REMOTE_PASSED",
        state_gate_status="REMOTE_PASSED",
        decision_preflight_status="REMOTE_PASSED",
    )
    truth = ReportTruth(
        changed_files=inventory,
        local_status="LOCAL_VALIDATED",
        remote_observation=observation,
    )
    assert truth.is_internally_consistent() is False
    reasons = truth.consistency_violations()
    assert any("stale_remote_observation" in reason for reason in reasons)


def test_remote_observation_is_stale_for_different_head() -> None:
    observation = RemoteObservation(
        head_sha="b" * 40,
        observed_at="2026-07-21T00:00:00Z",
        ci_status="REMOTE_PASSED",
        state_gate_status="REMOTE_PASSED",
        decision_preflight_status="REMOTE_PASSED",
    )
    assert observation.is_stale_for("c" * 40) is True
    assert observation.is_stale_for("b" * 40) is False


def test_report_truth_blocks_when_local_failed_but_remote_passed() -> None:
    """A LOCAL_FAILED status must contradict REMOTE_PASSED remote status."""

    inventory = ChangedFileInventory(
        paths=("reverse_agent/example.py",),
        source="git_diff_name_only",
        base_sha="a" * 40,
        head_sha="b" * 40,
    )
    observation = RemoteObservation(
        head_sha="b" * 40,
        observed_at="2026-07-21T00:00:00Z",
        ci_status="REMOTE_PASSED",
        state_gate_status="REMOTE_PASSED",
        decision_preflight_status="REMOTE_PASSED",
    )
    truth = ReportTruth(
        changed_files=inventory,
        local_status="LOCAL_FAILED",
        remote_observation=observation,
    )
    assert truth.is_internally_consistent() is False
    reasons = truth.consistency_violations()
    assert any("local_remote_status_contradiction" in reason for reason in reasons)


def test_report_truth_to_dict_preserves_provenance() -> None:
    """``to_dict`` must record source provenance for downstream consumers."""

    inventory = ChangedFileInventory(
        paths=("reverse_agent/example.py",),
        source="git_diff_name_only",
        base_sha="a" * 40,
        head_sha="b" * 40,
    )
    observation = RemoteObservation(
        head_sha="b" * 40,
        observed_at="2026-07-21T00:00:00Z",
        ci_status="REMOTE_PASSED",
        state_gate_status="REMOTE_PASSED",
        decision_preflight_status="REMOTE_PASSED",
    )
    truth = ReportTruth(
        changed_files=inventory,
        local_status="LOCAL_VALIDATED",
        remote_observation=observation,
    )
    payload = truth.to_dict()
    assert payload["changed_files"]["source"] == "git_diff_name_only"
    assert payload["remote_observation"]["head_sha"] == "b" * 40
    assert payload["local_status"] == "LOCAL_VALIDATED"
    assert payload["internally_consistent"] is True
