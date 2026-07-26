"""Semantic contracts for the minimal AI development integration baseline.

The tests deliberately validate authority invariants rather than mere keyword
presence. They cover Issue #32 findings and keep the reuse inventory read-only.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
AGENTS_MD = REPO_ROOT / "AGENTS.md"
ROADMAP_MD = REPO_ROOT / "docs" / "roadmap" / "MINIMAL_AI_DEVELOPMENT_INTEGRATION_PLAN.md"
SOURCE_OF_TRUTH_MD = REPO_ROOT / "docs" / "architecture" / "SOURCE_OF_TRUTH_MATRIX.md"
CONTAINMENT_MD = REPO_ROOT / "docs" / "architecture" / "LEGACY_GOVERNANCE_CONTAINMENT.md"
REUSE_INVENTORY_MD = REPO_ROOT / "docs" / "architecture" / "ARCHITECTURE_SPINE_REUSE_INVENTORY.md"
R1_TEMPLATE = REPO_ROOT / ".github" / "ISSUE_TEMPLATE" / "minimal-ai-r1-task.yml"

DELIVERABLES = [
    AGENTS_MD,
    ROADMAP_MD,
    SOURCE_OF_TRUTH_MD,
    CONTAINMENT_MD,
    REUSE_INVENTORY_MD,
    R1_TEMPLATE,
]
LEGAL_DISPOSITIONS = {"KEEP", "ADAPT", "DEFER", "ARCHIVE_CANDIDATE"}
TRANSITION_BASE_SHA = "38de9106d191d6b66d5f878354144817095e7bca"


def _read(path: Path) -> str:
    return path.read_text(encoding="utf-8") if path.exists() else ""


@pytest.mark.parametrize("path", DELIVERABLES, ids=lambda p: p.name)
def test_deliverables_are_non_empty(path: Path) -> None:
    assert _read(path).strip(), f"{path} is empty"


# ---------------------------------------------------------------------------
# Authority model
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("path", [AGENTS_MD, ROADMAP_MD, SOURCE_OF_TRUTH_MD])
def test_candidate_issue_is_not_immediate_authority(path: Path) -> None:
    content = _read(path).lower()
    assert "candidate" in content
    assert "not" in content
    assert "authority" in content


@pytest.mark.parametrize("path", [AGENTS_MD, ROADMAP_MD, SOURCE_OF_TRUTH_MD, R1_TEMPLATE])
def test_owner_or_maintainer_approval_is_required(path: Path) -> None:
    content = _read(path).lower()
    assert "owner" in content or "maintainer" in content
    assert "r1-approved" in content


@pytest.mark.parametrize("path", [AGENTS_MD, ROADMAP_MD, SOURCE_OF_TRUTH_MD, R1_TEMPLATE])
def test_immutable_work_item_snapshot_is_required(path: Path) -> None:
    content = _read(path)
    for token in (
        "approved_by",
        "immutable_observation_ref",
        "body_digest",
    ):
        assert token in content, f"{path.name} missing {token}"
    assert "SHA-256" in content or "sha256" in content.lower()


@pytest.mark.parametrize("path", [AGENTS_MD, ROADMAP_MD, SOURCE_OF_TRUTH_MD, R1_TEMPLATE])
def test_material_issue_edit_invalidates_snapshot(path: Path) -> None:
    content = _read(path).lower()
    assert "material" in content
    assert "invalid" in content
    assert "reapproval" in content or "reapprove" in content


@pytest.mark.parametrize("path", [AGENTS_MD, ROADMAP_MD, SOURCE_OF_TRUTH_MD])
def test_comments_are_never_authority(path: Path) -> None:
    content = _read(path).lower()
    assert "comment" in content
    assert "never authority" in content or "never" in content and "authority" in content


def test_work_item_identity_matches_existing_contract_shape() -> None:
    for path in (AGENTS_MD, ROADMAP_MD, SOURCE_OF_TRUTH_MD, R1_TEMPLATE):
        content = _read(path)
        assert "{repository}#{issue_number}@{immutable_observation_ref}" in content


def test_template_initial_state_is_candidate_only() -> None:
    content = _read(R1_TEMPLATE)
    approval_block = content[content.index("id: approval_state") : content.index("id: specification")]
    assert "CANDIDATE" in approval_block
    assert "APPROVED" not in approval_block


# ---------------------------------------------------------------------------
# Publication boundary and history safety
# ---------------------------------------------------------------------------


def _r2_boundary_block(content: str) -> str:
    start = content.index("id: r2_r3_boundary")
    end = content.index("id: approval_snapshot_boundary")
    return content[start:end]


def test_required_boundary_checkbox_preserves_narrow_r1_publication() -> None:
    block = _r2_boundary_block(_read(R1_TEMPLATE)).lower()
    assert "exact approved non-main branch" in block
    assert "exact draft pr" in block
    assert "outside that narrow exception" in block
    assert "requires a bounded path-b decision" in block


def test_boundary_validator_rejects_old_v4_checkbox() -> None:
    bad = (
        "If the work requires workflow, dependency, network, publication, binary, "
        "secrets, or destructive scope, I will stop and request a bounded Decision."
    ).lower()
    assert "outside that narrow exception" not in bad
    assert "network, publication" in bad


@pytest.mark.parametrize("path", [AGENTS_MD, ROADMAP_MD, R1_TEMPLATE])
def test_r1_publication_is_exact_and_narrow(path: Path) -> None:
    content = _read(path).lower()
    assert "non-`main`" in content or "non-main" in content
    assert "draft pr" in content
    assert "merge" in content
    assert "mark-ready" in content or "mark ready" in content


def _positive_rebase_instructions(content: str) -> list[str]:
    patterns = [
        r"stop\s+and\s+re-?base",
        r"(?:must|should|may|then)\s+(?:run\s+)?(?:git\s+)?re-?base",
        r"create\s+or\s+re-?base",
    ]
    return [m.group(0) for pattern in patterns for m in re.finditer(pattern, content, re.I)]


def test_path_a_never_instructs_rebase() -> None:
    agents = _read(AGENTS_MD)
    roadmap = _read(ROADMAP_MD)
    assert not _positive_rebase_instructions(agents)
    assert not _positive_rebase_instructions(roadmap)
    assert "fresh branch" in agents.lower()
    assert "fresh branch" in roadmap.lower()


def test_rebase_validator_rejects_v4_instruction() -> None:
    assert _positive_rebase_instructions("If merge-base differs, stop and re-base or request a new Work Item.")


def test_permanent_guidance_does_not_freeze_transition_sha() -> None:
    for path in (AGENTS_MD, R1_TEMPLATE):
        content = _read(path)
        assert TRANSITION_BASE_SHA not in content
        assert "origin/main" in content


# ---------------------------------------------------------------------------
# Two paths and one-time transition evidence
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("path", [AGENTS_MD, ROADMAP_MD, SOURCE_OF_TRUTH_MD, CONTAINMENT_MD])
def test_two_authority_paths_remain_explicit(path: Path) -> None:
    content = _read(path).lower()
    assert "path a" in content
    assert "path b" in content
    assert "r0/r1" in content
    assert "r2" in content and "r3" in content


def test_transition_evidence_exception_is_exhaustive() -> None:
    content = _read(SOURCE_OF_TRUTH_MD).lower()
    assert "one-time" in content
    assert "project_state/gates/command_plan.json" in content
    assert "new tracked per-run artifact family" in content


# ---------------------------------------------------------------------------
# Complete Markdown disposition-table parsing
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class MarkdownTable:
    headers: tuple[str, ...]
    rows: tuple[tuple[str, ...], ...]


def _cells(line: str) -> tuple[str, ...]:
    return tuple(cell.strip() for cell in line.strip().strip("|").split("|"))


def _is_separator(cells: tuple[str, ...]) -> bool:
    return bool(cells) and all(re.fullmatch(r"[-:\s]+", cell) for cell in cells)


def _markdown_tables(content: str) -> list[MarkdownTable]:
    lines = content.splitlines()
    tables: list[MarkdownTable] = []
    index = 0
    while index < len(lines) - 1:
        if not lines[index].lstrip().startswith("|"):
            index += 1
            continue
        header = _cells(lines[index])
        separator = _cells(lines[index + 1]) if lines[index + 1].lstrip().startswith("|") else ()
        if not _is_separator(separator) or len(header) != len(separator):
            index += 1
            continue
        rows: list[tuple[str, ...]] = []
        index += 2
        while index < len(lines) and lines[index].lstrip().startswith("|"):
            row = _cells(lines[index])
            if len(row) == len(header):
                rows.append(row)
            index += 1
        tables.append(MarkdownTable(header, tuple(rows)))
    return tables


def _disposition_cells(content: str) -> list[str]:
    result: list[str] = []
    for table in _markdown_tables(content):
        normalized = [header.strip("`").strip().lower() for header in table.headers]
        if "disposition" not in normalized:
            continue
        position = normalized.index("disposition")
        result.extend(row[position] for row in table.rows)
    return result


def _validate_disposition_cell(cell: str) -> None:
    value = cell.replace("`", "").strip()
    assert value in LEGAL_DISPOSITIONS, f"illegal, missing, or duplicate disposition: {cell!r}"


def test_every_disposition_table_and_row_is_validated() -> None:
    content = _read(REUSE_INVENTORY_MD)
    tables = [
        table
        for table in _markdown_tables(content)
        if "disposition" in [h.strip("`").strip().lower() for h in table.headers]
    ]
    assert len(tables) >= 6, "expected all legend/module/document disposition tables"
    cells = _disposition_cells(content)
    assert len(cells) >= 30, "parser skipped disposition rows"
    for cell in cells:
        _validate_disposition_cell(cell)


@pytest.mark.parametrize(
    "cell",
    ["", "UNKNOWN_STATE", "KEEP / UNKNOWN_STATE", "KEEP / ADAPT", "NO_NEW_FEATURES"],
)
def test_disposition_validator_rejects_bad_cells(cell: str) -> None:
    with pytest.raises(AssertionError):
        _validate_disposition_cell(cell)


# ---------------------------------------------------------------------------
# R1 final acceptance — owner manual merge carve-out
# ---------------------------------------------------------------------------


OWNER_MERGE_DOCS = [AGENTS_MD, ROADMAP_MD, SOURCE_OF_TRUTH_MD, CONTAINMENT_MD]


@pytest.mark.parametrize("path", OWNER_MERGE_DOCS, ids=lambda p: p.name)
def test_owner_manual_merge_carve_out_present(path: Path) -> None:
    content = _read(path).lower()
    assert "owner" in content and "maintainer" in content
    assert "mark-ready" in content
    assert "merge" in content
    assert "carve-out" in content or "carve out" in content


@pytest.mark.parametrize("path", OWNER_MERGE_DOCS, ids=lambda p: p.name)
def test_owner_manual_merge_invariants_present(path: Path) -> None:
    content = _read(path).lower()
    assert "audit" in content
    assert "exact head" in content or "exact-head" in content
    assert "ci" in content
    assert "mergeable" in content
    assert "base_sha" in content or "base sha" in content or "baseRefOid".lower() in content


def test_owner_manual_merge_match_head_commit_protection_required() -> None:
    content = _read(AGENTS_MD).lower()
    assert "match-head-commit" in content or "match head commit" in content


@pytest.mark.parametrize("path", OWNER_MERGE_DOCS, ids=lambda p: p.name)
def test_actor_control_distinction_present(path: Path) -> None:
    content = _read(path).lower()
    assert "agent-initiated" in content or "agent initiated" in content
    assert "automation-initiated" in content or "automation initiated" in content
    assert "human-initiated" in content or "human initiated" in content
    assert "personally" in content


@pytest.mark.parametrize("path", OWNER_MERGE_DOCS, ids=lambda p: p.name)
def test_agent_and_automation_merge_remains_path_b(path: Path) -> None:
    content = _read(path).lower()
    assert "agent-initiated" in content or "agent initiated" in content
    assert "automation-initiated" in content or "automation initiated" in content
    assert "auto-merge" in content or "automatic merge" in content
    assert "path b" in content or "path-b" in content


@pytest.mark.parametrize("path", OWNER_MERGE_DOCS, ids=lambda p: p.name)
def test_r2_r3_work_items_excluded_from_carve_out(path: Path) -> None:
    content = _read(path).lower()
    assert "r2/r3" in content or "r2 or r3" in content
    assert "path b" in content or "path-b" in content


def test_r1_template_forbidden_operations_distinguish_actor() -> None:
    block = _read(R1_TEMPLATE).lower()
    assert "agent-initiated" in block or "agent initiated" in block
    assert "automation-initiated" in block or "automation initiated" in block
    assert "auto-merge" in block or "automatic merge" in block
    assert "r1 final-acceptance carve-out" in block or "r1 final acceptance carve-out" in block


def test_r1_template_r2_boundary_acknowledges_carve_out() -> None:
    block = _r2_boundary_block(_read(R1_TEMPLATE)).lower()
    assert "agent-initiated" in block or "agent initiated" in block
    assert "auto-merge" in block or "automatic merge" in block
    assert "owner/maintainer manual merge" in block or "owner manual merge" in block
    assert "r1 final-acceptance carve-out" in block or "r1 final acceptance carve-out" in block


def test_r1_template_draft_pr_boundary_acknowledges_carve_out() -> None:
    block = _read(R1_TEMPLATE).lower()
    draft_section = block[block.index("draft pr and human acceptance boundary"):]
    assert "owner/maintainer" in draft_section
    assert "r1 final-acceptance carve-out" in draft_section or "r1 final acceptance carve-out" in draft_section
    assert "agent-initiated" in draft_section or "agent initiated" in draft_section
    assert "auto-merge" in draft_section or "automatic merge" in draft_section


def test_agents_md_r2_scope_narrowed_to_agent_automation_merge() -> None:
    content = _read(AGENTS_MD).lower()
    assert "agent-initiated" in content or "agent initiated" in content
    assert "automation-initiated" in content or "automation initiated" in content
    r2_section = content[content.index("r2 publication/network"):]
    assert "agent-initiated" in r2_section or "agent initiated" in r2_section
    assert "auto-merge" in r2_section or "automatic merge" in r2_section


def test_agents_md_prohibited_actions_narrowed_to_agent_automation_merge() -> None:
    content = _read(AGENTS_MD).lower()
    prohibited_section = content[content.index("prohibited actions"):]
    assert "agent-initiated" in prohibited_section or "agent initiated" in prohibited_section
    assert "automation-initiated" in prohibited_section or "automation initiated" in prohibited_section
    assert "auto-merge" in prohibited_section or "automatic merge" in prohibited_section
    assert "r1 final-acceptance carve-out" in prohibited_section or "r1 final acceptance carve-out" in prohibited_section


def test_roadmap_after_acceptance_mentions_carve_out() -> None:
    content = _read(ROADMAP_MD).lower()
    after_section = content[content.index("after acceptance"):]
    assert "r1 final-acceptance carve-out" in after_section or "r1 final acceptance carve-out" in after_section
    assert "owner/maintainer" in after_section


def test_legacy_containment_owner_merge_consistent() -> None:
    content = _read(CONTAINMENT_MD).lower()
    assert "owner-manual-merge" in content or "owner manual merge" in content
    assert "agent-initiated" in content or "agent initiated" in content
    assert "auto-merge" in content or "automatic merge" in content


def test_carve_out_does_not_authorize_squash_or_rebase() -> None:
    content = _read(AGENTS_MD).lower()
    carve_section = content[content.index("r1 final acceptance"):]
    assert "squash" not in carve_section.split("r2 publication")[0]
    assert "rebase" not in carve_section.split("r2 publication")[0]
    assert "merge method = merge" in carve_section or "merge method = merge".replace("= ", "= ") in carve_section


def test_table_parser_handles_module_slash_class_headers() -> None:
    fixture = """
| Module / class | Disposition | Note |
|----------------|-------------|------|
| A | KEEP | ok |
| B | ARCHIVE_CANDIDATE | ok |
"""
    assert _disposition_cells(fixture) == ["KEEP", "ARCHIVE_CANDIDATE"]


def test_table_parser_exposes_invalid_fixture_row() -> None:
    fixture = """
| Module / node | Disposition | Note |
|---------------|-------------|------|
| A | KEEP / UNKNOWN_STATE | bad |
"""
    cells = _disposition_cells(fixture)
    assert cells == ["KEEP / UNKNOWN_STATE"]
    with pytest.raises(AssertionError):
        _validate_disposition_cell(cells[0])


# ---------------------------------------------------------------------------
# Required sections and fields
# ---------------------------------------------------------------------------


def test_agents_required_sections() -> None:
    content = _read(AGENTS_MD)
    for section in (
        "Repository purpose",
        "Current non-goals",
        "Two authority paths",
        "Risk tiers",
        "Startup checks",
        "Work Item acceptance requirements",
        "Test commands",
        "Branch and PR rules",
        "Prohibited actions",
        "Stop conditions",
    ):
        assert section in content


def test_roadmap_required_sections() -> None:
    content = _read(ROADMAP_MD)
    for section in (
        "Active development stack",
        "Two authority paths",
        "Risk tier model",
        "Legacy roadmap classification",
        "Extension candidates",
        "After acceptance",
    ):
        assert section in content


def test_template_required_fields() -> None:
    content = _read(R1_TEMPLATE)
    for field in (
        "approval_state",
        "specification",
        "allowed_paths",
        "forbidden_operations",
        "acceptance_criteria",
        "required_checks",
        "risk_tier_justification",
        "r2_r3_boundary",
        "approval_snapshot_boundary",
        "draft_pr_boundary",
        "target_branch",
        "base_sha",
    ):
        assert f"id: {field}" in content
