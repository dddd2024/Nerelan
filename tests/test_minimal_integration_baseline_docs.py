"""Tests for the minimal AI development integration baseline documentation.

These tests verify the six deliverable files produced by the p0 minimal
integration baseline round are non-empty, contain the required sections,
express a consistent R0/R1 authority model, and use only legal reuse
dispositions. They guard against the content acceptance failures found
by the independent audit of head 657b119.
"""

from __future__ import annotations

import re
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]

AGENTS_MD = REPO_ROOT / "AGENTS.md"
ROADMAP_MD = REPO_ROOT / "docs" / "roadmap" / "MINIMAL_AI_DEVELOPMENT_INTEGRATION_PLAN.md"
SOURCE_OF_TRUTH_MD = REPO_ROOT / "docs" / "architecture" / "SOURCE_OF_TRUTH_MATRIX.md"
CONTAINMENT_MD = REPO_ROOT / "docs" / "architecture" / "LEGACY_GOVERNANCE_CONTAINMENT.md"
REUSE_INVENTORY_MD = REPO_ROOT / "docs" / "architecture" / "ARCHITECTURE_SPINE_REUSE_INVENTORY.md"
R1_ISSUE_TEMPLATE = REPO_ROOT / ".github" / "ISSUE_TEMPLATE" / "minimal-ai-r1-task.yml"

SIX_DELIVERABLES = [
    ("AGENTS.md", AGENTS_MD),
    ("MINIMAL_AI_DEVELOPMENT_INTEGRATION_PLAN.md", ROADMAP_MD),
    ("SOURCE_OF_TRUTH_MATRIX.md", SOURCE_OF_TRUTH_MD),
    ("LEGACY_GOVERNANCE_CONTAINMENT.md", CONTAINMENT_MD),
    ("ARCHITECTURE_SPINE_REUSE_INVENTORY.md", REUSE_INVENTORY_MD),
    ("minimal-ai-r1-task.yml", R1_ISSUE_TEMPLATE),
]

LEGAL_REUSE_DISPOSITIONS = {"KEEP", "ADAPT", "DEFER", "ARCHIVE_CANDIDATE"}


def _read(path: Path) -> str:
    if not path.exists():
        return ""
    return path.read_text(encoding="utf-8")


# --- Deliverable files are non-empty ---


@pytest.mark.parametrize("name,path", SIX_DELIVERABLES, ids=[n for n, _ in SIX_DELIVERABLES])
def test_deliverable_file_is_non_empty(name: str, path: Path) -> None:
    content = _read(path)
    assert content.strip(), f"{name} is empty or whitespace-only; audit finding 1 regression"


# --- AGENTS.md required sections ---


def test_agents_md_has_required_sections() -> None:
    content = _read(AGENTS_MD)
    required = [
        "Repository purpose",
        "Current non-goals",
        "Startup checks",
        "Source-of-truth order",
        "Risk tiers",
        "R0/R1 allowed operations",
        "R2/R3 approval boundary",
        "Test commands",
        "Branch and PR rules",
        "Prohibited actions",
        "Stop conditions",
    ]
    missing = [section for section in required if section not in content]
    assert not missing, f"AGENTS.md missing sections: {missing}"


def test_agents_md_classifies_feature_branch_push_as_r1() -> None:
    content = _read(AGENTS_MD)
    assert "feature branch" in content.lower() or "feature-branch" in content.lower()
    assert "R1" in content
    assert "Draft PR" in content or "Draft pr" in content


# --- Roadmap required sections ---


def test_roadmap_has_required_sections() -> None:
    content = _read(ROADMAP_MD)
    required = [
        "Active development stack",
        "Risk tier model",
        "Legacy roadmap classification",
        "EXTENSION_CANDIDATE",
    ]
    missing = [section for section in required if section not in content]
    assert not missing, f"Roadmap missing sections: {missing}"


def test_roadmap_states_r0_r1_do_not_require_full_decision() -> None:
    content = _read(ROADMAP_MD)
    assert "R0/R1" in content or "R0/R1" in content.lower()
    assert "Decision" in content or "decision" in content
    assert "not" in content.lower() or "no longer" in content.lower()


# --- Source-of-truth matrix required sections ---


def test_source_of_truth_matrix_has_ownership_map() -> None:
    content = _read(SOURCE_OF_TRUTH_MD)
    assert "Ownership map" in content or "ownership map" in content.lower()
    assert "decision_packet.md" in content
    assert "command_plan.json" in content


# --- Containment doc required sections ---


def test_containment_doc_has_four_tiers() -> None:
    content = _read(CONTAINMENT_MD)
    for tier in ("RETAIN", "READ_ONLY_COMPATIBILITY", "NO_NEW_FEATURES", "DEFERRED"):
        assert tier in content, f"Containment doc missing tier: {tier}"


def test_containment_doc_has_lifecycle() -> None:
    content = _read(CONTAINMENT_MD)
    assert "ACTIVE_COMPATIBILITY" in content
    assert "ARCHIVED" in content
    assert "REMOVED_FROM_RUNTIME" in content


# --- Reuse inventory: only legal dispositions ---


def test_reuse_inventory_has_legal_dispositions_only() -> None:
    content = _read(REUSE_INVENTORY_MD)
    assert "KEEP" in content
    assert "ADAPT" in content
    assert "DEFER" in content
    assert "ARCHIVE_CANDIDATE" in content
    assert "Disposition legend" in content or "disposition legend" in content.lower()
    assert "NO_NEW_FEATURES" not in content, (
        "Reuse inventory must not contain NO_NEW_FEATURES as a disposition; "
        "only KEEP/ADAPT/DEFER/ARCHIVE_CANDIDATE are legal"
    )


def test_reuse_inventory_disposition_table_uses_legal_values() -> None:
    content = _read(REUSE_INVENTORY_MD)
    table_rows = re.findall(r"\|[^|]*\|[^|]*\|[^|]*\|", content)
    for row in table_rows:
        if "Disposition" in row:
            continue
        for token in ("KEEP", "ADAPT", "DEFER", "ARCHIVE_CANDIDATE", "NO_NEW_FEATURES"):
            if token in row:
                assert token in LEGAL_REUSE_DISPOSITIONS, (
                    f"Reuse inventory row uses illegal disposition: {token}"
                )


# --- R1 Issue template required fields ---


def test_r1_issue_template_has_required_fields() -> None:
    content = _read(R1_ISSUE_TEMPLATE)
    required = [
        "specification",
        "allowed_paths",
        "forbidden_operations",
        "acceptance_criteria",
        "required_checks",
        "risk_tier_justification",
        "r2_r3_boundary",
        "draft_pr_boundary",
    ]
    missing = [field for field in required if field not in content]
    assert not missing, f"R1 Issue template missing fields: {missing}"


def test_r1_issue_template_acknowledges_r2_r3_boundary() -> None:
    content = _read(R1_ISSUE_TEMPLATE)
    assert "R2/R3" in content
    assert "bounded Decision" in content or "bounded decision" in content.lower()


# --- R1 authority semantics consistency across documents ---


def test_r1_authority_model_is_consistent_across_documents() -> None:
    agents = _read(AGENTS_MD)
    roadmap = _read(ROADMAP_MD)
    source_of_truth = _read(SOURCE_OF_TRUTH_MD)
    containment = _read(CONTAINMENT_MD)
    template = _read(R1_ISSUE_TEMPLATE)

    documents = {
        "AGENTS.md": agents,
        "roadmap": roadmap,
        "source_of_truth": source_of_truth,
        "containment": containment,
        "r1_template": template,
    }

    for name, content in documents.items():
        assert "R1" in content, f"{name} does not mention R1"

    for name, content in documents.items():
        if name == "containment":
            continue
        assert "Decision" in content or "decision" in content, (
            f"{name} does not reference Decision authority"
        )

    assert "R0/R1" in roadmap or "R0/R1" in roadmap.lower(), (
        "Roadmap must state the R0/R1 lightweight authority model"
    )

    assert "not" in roadmap.lower() and "Decision" in roadmap, (
        "Roadmap must state R0/R1 does not require full Decision"
    )

    for name, content in documents.items():
        if "R2" in content and "R3" in content:
            assert "fail" in content.lower() or "closed" in content.lower() or "bounded" in content.lower(), (
                f"{name} mentions R2/R3 but does not state fail-closed or bounded authorization"
            )


def test_feature_branch_push_is_classified_as_r1() -> None:
    agents = _read(AGENTS_MD)
    roadmap = _read(ROADMAP_MD)
    source_of_truth = _read(SOURCE_OF_TRUTH_MD)

    for name, content in [("AGENTS.md", agents), ("roadmap", roadmap), ("source_of_truth", source_of_truth)]:
        if "push" in content.lower() and "branch" in content.lower():
            assert "R1" in content, f"{name} discusses push/branch but does not classify as R1"
        if "Draft PR" in content or "Draft pr" in content:
            assert "R1" in content, f"{name} discusses Draft PR but does not classify as R1"
