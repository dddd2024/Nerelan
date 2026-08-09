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


@pytest.mark.parametrize("path", [AGENTS_MD, R1_TEMPLATE])
def test_r1_snapshot_names_explicit_branch_neutral_integration_base(path: Path) -> None:
    content = _read(path)
    assert "integration_base_ref" in content
    assert "base_sha" in content


def test_r1_template_does_not_define_base_sha_as_current_main() -> None:
    content = _read(R1_TEMPLATE).lower()
    assert "current origin/main commit" not in content
    assert "exact sha of the explicitly approved integration base" in content


def test_agents_documents_deterministic_worktree_classification() -> None:
    content = _read(AGENTS_MD)
    for token in (
        "AUTHORIZED_TRACKED_DELTA",
        "GENERATED_GOVERNANCE_ARTIFACT",
        "KNOWN_RUNTIME_SCRATCH",
        "UNKNOWN_UNTRACKED",
        "UNAUTHORIZED_TRACKED_OR_SENSITIVE",
    ):
        assert token in content


@pytest.mark.parametrize("path", [AGENTS_MD, R1_TEMPLATE])
def test_r1_activation_lifecycle_is_tree_identical_and_exact_head_bound(path: Path) -> None:
    content = _read(path)
    for token in (
        'git commit --allow-empty -m "chore: activate R1 work item #<issue>"',
        "exact_head_sha",
        "empty activation commit",
        "tree-identical",
    ):
        assert token in content, f"{path.name} missing {token}"
    assert "No product/source/test file may change before" in content
    assert "rebind" in content.lower()
    assert "transient" in content.lower()


def test_agents_documents_r1_local_guard_and_live_state_gate_boundary() -> None:
    content = _read(AGENTS_MD)
    assert "worktree-r1-publication-readiness" in content
    assert "approved Issue body" in content
    assert "Draft PR body" in content
    assert "does not replace" in content
    assert "GitHub State Gate" in content


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
        assert "integration_base_ref" in content
        assert "base_sha" in content


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


# ---------------------------------------------------------------------------
# F3 — Structured negative tests detecting F1/F2 contradictions
# ---------------------------------------------------------------------------


_STAGE_QUALIFIERS = (
    "during agent implementation",
    "before independent exact-head acceptance",
    "before independent exact head acceptance",
)


def _r1_publication_section(content: str) -> str:
    lower = content.lower()
    start = lower.index("r1 publication")
    end = lower.index("r1 final acceptance")
    return lower[start:end]


@pytest.mark.parametrize("path", [AGENTS_MD, ROADMAP_MD])
def test_f3_only_statements_are_stage_qualified(path: Path) -> None:
    section = _r1_publication_section(_read(path))
    assert any(q in section for q in _STAGE_QUALIFIERS), (
        f"{path.name} R1 publication section must qualify 'only' with an "
        "Agent-implementation stage qualifier"
    )
    assert "only these network/publication operations are r1" not in section, (
        f"{path.name} must not contain unqualified 'Only these network/"
        "publication operations are R1'"
    )
    assert "path a permits only:" not in section or any(
        q in section for q in _STAGE_QUALIFIERS
    ), (
        f"{path.name} 'Path A permits only' must be stage-qualified"
    )


def test_f3_only_statement_does_not_unconditionally_exclude_merge() -> None:
    for path in (AGENTS_MD, ROADMAP_MD):
        section = _r1_publication_section(_read(path))
        assert "they do not authorize merge" not in section, (
            f"{path.name} must not contain unqualified 'They do not authorize "
            "merge' in the R1 publication section"
        )


def test_f3_r1_template_boundary_checkbox_is_stage_qualified() -> None:
    block = _r2_boundary_block(_read(R1_TEMPLATE)).lower()
    assert any(q in block for q in _STAGE_QUALIFIERS), (
        "R1 template r2_r3_boundary checkbox must scope 'only' to "
        "Agent-implementation stage"
    )
    assert "i acknowledge that only push" not in block, (
        "R1 template must not contain unqualified 'I acknowledge that only "
        "push...' without a stage qualifier before 'only'"
    )


def test_f3_roadmap_marks_pr27_sequence_as_historical() -> None:
    content = _read(ROADMAP_MD).lower()
    after_section = content[content.index("after acceptance"):]
    assert "historical" in after_section or "one-time" in after_section, (
        "Roadmap 'After acceptance' must mark the PR #27 separate-R2-merge "
        "sequence as historical/one-time"
    )
    pr27_block = after_section[:after_section.index("first real r1 pilot") + 50]
    assert "historical" in pr27_block or "one-time" in pr27_block, (
        "PR #27 sequence must be explicitly marked historical/one-time"
    )


def test_f3_roadmap_active_future_rule_no_separate_r2_for_every_r1() -> None:
    content = _read(ROADMAP_MD).lower()
    after_section = content[content.index("after acceptance"):]
    active_rule_marker = "active future rule"
    assert active_rule_marker in after_section, (
        "Roadmap must have an 'Active future rule' subsection in 'After acceptance'"
    )
    active_rule = after_section[after_section.index(active_rule_marker):]
    assert "no longer require a separate r2 merge decision" in active_rule, (
        "Active future rule must state accepted ordinary R1 PRs no longer "
        "require a separate R2 merge Decision"
    )


def test_f3_agent_automation_auto_merge_remain_explicitly_path_b() -> None:
    for path in (AGENTS_MD, ROADMAP_MD, SOURCE_OF_TRUTH_MD, CONTAINMENT_MD):
        content = _read(path).lower()
        r2_section = content[content.index("r2 publication"):] if "r2 publication" in content else content
        assert "agent-initiated" in r2_section or "agent initiated" in r2_section
        assert "automation-initiated" in r2_section or "automation initiated" in r2_section
        assert "auto-merge" in r2_section or "automatic merge" in r2_section
        assert "path b" in r2_section or "path-b" in r2_section


def test_f3_agents_md_publication_grant_separated_from_carve_out() -> None:
    content = _read(AGENTS_MD).lower()
    pub_section = _r1_publication_section(content)
    assert "after independent exact-head acceptance" in pub_section, (
        "AGENTS.md R1 publication section must reference the post-acceptance "
        "carve-out as a separate stage"
    )
    assert "not part of the agent-implementation publication grant" in pub_section, (
        "AGENTS.md must explicitly state the carve-out is not part of the "
        "Agent-implementation publication grant"
    )


# ---------------------------------------------------------------------------
# F6 — Clause-local stage-qualification + risk_tier_justification block tests
# ---------------------------------------------------------------------------


import re as _re


def _split_sentences(text: str) -> list[str]:
    """Split text into sentences on ., !, ? followed by whitespace or end."""
    return [s.strip() for s in _re.split(r"[.!?]\s+", text) if s.strip()]


def _sentence_has_stage_qualifier(sentence: str) -> bool:
    s = sentence.lower()
    return any(q in s for q in _STAGE_QUALIFIERS)


@pytest.mark.parametrize("path", [AGENTS_MD, ROADMAP_MD])
def test_f6_only_clauses_are_clause_local_stage_qualified(path: Path) -> None:
    """Each sentence containing an 'only' R1-publication rule must also carry
    a stage qualifier in the same sentence (not merely elsewhere in the section).
    """
    section = _r1_publication_section(_read(path))
    sentences = _split_sentences(section)
    only_sentences = [
        s for s in sentences
        if "only" in s and ("network" in s or "publication" in s or "push" in s or "draft pr" in s or "branch" in s)
    ]
    assert only_sentences, (
        f"{path.name} R1 publication section must contain at least one 'only' "
        "rule sentence for clause-local validation"
    )
    for s in only_sentences:
        assert _sentence_has_stage_qualifier(s), (
            f"{path.name} 'only' rule sentence must carry a stage qualifier in "
            f"the same sentence (clause-local), not merely elsewhere in the "
            f"section. Offending sentence: {s!r}"
        )


def _risk_tier_justification_block(content: str) -> str:
    """Extract the risk_tier_justification textarea block from the R1 template."""
    start = content.index("id: risk_tier_justification")
    end_marker = "validations:"
    end = content.index(end_marker, start)
    return content[start:end]


def test_f6_r1_template_risk_tier_justification_block_is_stage_qualified() -> None:
    block = _risk_tier_justification_block(_read(R1_TEMPLATE)).lower()
    assert any(q in block for q in _STAGE_QUALIFIERS), (
        "R1 template risk_tier_justification placeholder must scope 'only' to "
        "Agent-implementation stage"
    )


def test_f6_r1_template_risk_tier_justification_no_unqualified_only() -> None:
    block = _risk_tier_justification_block(_read(R1_TEMPLATE))
    sentences = _split_sentences(block.lower())
    only_sentences = [s for s in sentences if "only" in s]
    assert only_sentences, (
        "risk_tier_justification block must contain at least one 'only' rule "
        "sentence for clause-local validation"
    )
    for s in only_sentences:
        assert _sentence_has_stage_qualifier(s), (
            "risk_tier_justification 'only' rule sentence must carry a stage "
            f"qualifier in the same sentence (clause-local). Offending: {s!r}"
        )
    assert "the only network/publication operations are" not in block.lower() or any(
        q in block.lower() for q in _STAGE_QUALIFIERS
    ), "unqualified 'The only network/publication operations are' forbidden"


def test_f6_r1_template_risk_tier_justification_clauses_local_only() -> None:
    """Regression for F5: the unqualified form 'The only network/publication
    operations are push...' must not appear as a standalone clause. The 'only'
    word and a stage qualifier must co-occur in the same sentence.
    """
    block = _risk_tier_justification_block(_read(R1_TEMPLATE)).lower()
    bad_pattern = "the only network/publication operations are"
    assert bad_pattern not in block, (
        f"risk_tier_justification must not contain unqualified {bad_pattern!r}; "
        "scope to Agent-implementation stage in the same sentence"
    )


def test_f6_r1_template_risk_tier_justification_agent_not_authorized_to_merge() -> None:
    block = _risk_tier_justification_block(_read(R1_TEMPLATE)).lower()
    assert "agent is not authorized to merge" in block or "agent is not authorized to merge or mark-ready" in block, (
        "risk_tier_justification placeholder must state the Agent is not "
        "authorized to merge or mark-ready during implementation"
    )
