from __future__ import annotations

import pytest

from reverse_agent.architecture.report_truth import (
    ChangedFileInventory,
    RemoteObservation,
    ReportTruth,
)
from reverse_agent.control_plane.report_binding import (
    ClassifiedPaths,
    ReportSubjectBinding,
    classify_path,
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


# --- Phase F 9.2: changed-file inventory classification ------------------


def test_classify_path_sorts_real_code_into_implementation() -> None:
    """Real code and test paths are ``implementation``."""
    assert classify_path("reverse_agent/control_plane/transition.py") == "implementation"
    assert classify_path("reverse_agent/architecture/contracts.py") == "implementation"
    assert classify_path("tests/test_report_truth.py") == "implementation"
    assert classify_path("tests/test_development_graph.py") == "implementation"


def test_classify_path_sorts_decision_packet_into_governance() -> None:
    """The Decision itself is governance, not implementation."""
    assert classify_path("project_state/decision_packet.md") == "governance"


def test_classify_path_sorts_roadmap_into_governance() -> None:
    """The roadmap is governance, not implementation."""
    assert classify_path("docs/roadmap/architecture_spine_provenance_integration_final_rework_v1.md") == "governance"


def test_classify_path_sorts_gate_artifacts_into_generated() -> None:
    """Auto-generated report/gate artifacts are ``generated``."""
    assert classify_path("project_state/gates/command_plan.json") == "generated"
    assert classify_path("project_state/gates/execution_log.json") == "generated"
    assert classify_path("project_state/gates/final_gate_result.json") == "generated"
    assert classify_path("project_state/execution_report.md") == "generated"
    assert classify_path("project_state/codex_execution_report.md") == "generated"
    assert classify_path("project_state/pytest_result.txt") == "generated"


def test_changed_file_inventory_classifies_paths_into_three_buckets() -> None:
    """Phase F 9.2: the inventory must distinguish three path categories."""
    diff = (
        "reverse_agent/control_plane/transition.py\n"
        "tests/test_report_truth.py\n"
        "project_state/decision_packet.md\n"
        "docs/roadmap/architecture_spine_provenance_integration_final_rework_v1.md\n"
        "project_state/gates/command_plan.json\n"
        "project_state/execution_report.md\n"
    )
    inventory = ChangedFileInventory.from_git_diff(
        diff,
        base_sha="a" * 40,
        head_sha="b" * 40,
    )
    classified = ClassifiedPaths.from_paths(inventory.paths)
    assert classified.implementation_paths == (
        "reverse_agent/control_plane/transition.py",
        "tests/test_report_truth.py",
    )
    assert classified.governance_paths == (
        "docs/roadmap/architecture_spine_provenance_integration_final_rework_v1.md",
        "project_state/decision_packet.md",
    )
    assert classified.generated_artifact_paths == (
        "project_state/execution_report.md",
        "project_state/gates/command_plan.json",
    )


def test_changed_file_inventory_excludes_decision_from_implementation() -> None:
    """The Decision itself must not appear in ``implementation_paths``."""
    diff = (
        "reverse_agent/example.py\n"
        "project_state/decision_packet.md\n"
    )
    inventory = ChangedFileInventory.from_git_diff(
        diff,
        base_sha="a" * 40,
        head_sha="b" * 40,
    )
    classified = ClassifiedPaths.from_paths(inventory.paths)
    assert "project_state/decision_packet.md" not in classified.implementation_paths
    assert "project_state/decision_packet.md" in classified.governance_paths


def test_changed_file_inventory_excludes_generated_artifacts_from_implementation() -> None:
    """Auto-generated artifacts must not appear in ``implementation_paths``."""
    diff = (
        "reverse_agent/example.py\n"
        "project_state/gates/command_plan.json\n"
        "project_state/execution_report.md\n"
    )
    inventory = ChangedFileInventory.from_git_diff(
        diff,
        base_sha="a" * 40,
        head_sha="b" * 40,
    )
    classified = ClassifiedPaths.from_paths(inventory.paths)
    assert "project_state/gates/command_plan.json" not in classified.implementation_paths
    assert "project_state/execution_report.md" not in classified.implementation_paths
    assert "project_state/gates/command_plan.json" in classified.generated_artifact_paths
    assert "project_state/execution_report.md" in classified.generated_artifact_paths


# --- Phase F 9.1: report subject binding uses implementation paths --------


def test_report_subject_binding_includes_implementation_subject_paths() -> None:
    """Phase F 9.1: the binding must record ``implementation_subject_paths``."""
    binding = ReportSubjectBinding(
        activation_base_sha="a" * 40,
        subject_tree_digest="c" * 64,
        subject_diff_digest="d" * 64,
        observed_worktree_paths=("reverse_agent/example.py",),
        implementation_subject_paths=("reverse_agent/example.py",),
        local_seal_digest="e" * 64,
    )
    payload = binding.to_dict()
    assert payload["implementation_subject_paths"] == ["reverse_agent/example.py"]


def test_report_subject_binding_defaults_implementation_subject_paths_to_empty() -> None:
    """When not provided, ``implementation_subject_paths`` defaults to empty."""
    binding = ReportSubjectBinding(
        activation_base_sha="a" * 40,
        subject_tree_digest="c" * 64,
        subject_diff_digest="d" * 64,
        observed_worktree_paths=("reverse_agent/example.py",),
        local_seal_digest="e" * 64,
    )
    payload = binding.to_dict()
    assert payload["implementation_subject_paths"] == []
