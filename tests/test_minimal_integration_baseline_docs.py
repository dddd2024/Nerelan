"""Semantic contract tests for the minimal AI development integration baseline.

These tests verify the six deliverable files produced by the p0 minimal
integration baseline round are non-empty, contain the required sections,
and express a SEMANTICALLY CONSISTENT R0/R1 authority model. They replace
the v3 keyword-presence tests with exact invariant tests and structured
parsing that fail on the F1-F5 contradictions found by the v3 audit
(Issue #31).

Covered findings:
  F1 — R1 authority model must not be contradicted by unconditional
       Decision/Command-Plan authority statements.
  F2 — R1 publication (branch push, Draft PR) must be a narrow exception;
       R2 publication must be precisely bounded; the R1 risk-justification
       prompt must not deny the narrow R1 network/publication exception.
  F3 — Permanent operating guidance must not hard-code the transition base
       SHA; the Work Item base must be bound to the current origin/main.
  F4 — The one-time tracked transition-evidence exception must be explicit.
  F5 — Containment authority labels must be qualified as transition/R2-R3.
  F6 — Reuse-inventory data rows must each have exactly one legal disposition.
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
TRANSITION_BASE_SHA = "38de9106d191d6b66d5f878354144817095e7bca"


def _read(path: Path) -> str:
    if not path.exists():
        return ""
    return path.read_text(encoding="utf-8")


# =====================================================================
# Deliverable files are non-empty
# =====================================================================


@pytest.mark.parametrize("name,path", SIX_DELIVERABLES, ids=[n for n, _ in SIX_DELIVERABLES])
def test_deliverable_file_is_non_empty(name: str, path: Path) -> None:
    content = _read(path)
    assert content.strip(), f"{name} is empty or whitespace-only"


# =====================================================================
# F1 — R1 authority model must not be contradicted
# =====================================================================


def _unconditional_authority_statements(content: str) -> list[str]:
    """Find unconditional statements that ALL execution authority lives in Decision + Command Plan.

    Matches patterns like:
      'execution authority lives in project_state/decision_packet.md and ... command_plan.json'
      'Execution authority lives in ...'
    but does NOT match statements qualified by 'transition', 'R2/R3', 'transition round', etc.
    """

    patterns = [
        r"[Ee]xecution authority lives in `?project_state/decision_packet\.md`?",
        r"[Ss]ole round authority",
        r"[Ss]ole round execution authority",
        r"[Aa]ll execution authority lives in",
    ]
    hits = []
    for pat in patterns:
        for m in re.finditer(pat, content):
            window_start = max(0, m.start() - 200)
            window_end = min(len(content), m.end() + 200)
            window = content[window_start:window_end].lower()
            qualifying = any(
                term in window
                for term in ("transition", "r2", "r3", "transition round", "r2/r3", "r2-r3")
            )
            if not qualifying:
                hits.append(m.group(0))
    return hits


def test_f1_roadmap_no_unconditional_decision_authority() -> None:
    content = _read(ROADMAP_MD)
    hits = _unconditional_authority_statements(content)
    assert not hits, (
        f"Roadmap contains unconditional Decision/Command-Plan authority statements "
        f"that contradict the ordinary R0/R1 model: {hits}"
    )


def test_f1_source_of_truth_no_unconditional_decision_authority() -> None:
    content = _read(SOURCE_OF_TRUTH_MD)
    hits = _unconditional_authority_statements(content)
    assert not hits, (
        f"Source-of-truth matrix contains unconditional Decision/Command-Plan authority "
        f"statements that contradict the ordinary R0/R1 model: {hits}"
    )


def test_f1_agents_md_no_unconditional_decision_authority() -> None:
    content = _read(AGENTS_MD)
    hits = _unconditional_authority_statements(content)
    assert not hits, (
        f"AGENTS.md contains unconditional Decision/Command-Plan authority statements "
        f"that contradict the ordinary R0/R1 model: {hits}"
    )


def test_f1_two_authority_paths_defined() -> None:
    """Each core document must define two explicit authority paths."""

    for name, path in [
        ("AGENTS.md", AGENTS_MD),
        ("roadmap", ROADMAP_MD),
        ("source_of_truth", SOURCE_OF_TRUTH_MD),
        ("containment", CONTAINMENT_MD),
    ]:
        content = _read(path)
        assert "ordinary R0/R1" in content.lower() or "ordinary r0/r1" in content.lower() or "R0/R1 path" in content, (
            f"{name} does not define the ordinary R0/R1 authority path"
        )
        assert (
            "transition" in content.lower()
            and ("R2" in content or "r2" in content)
        ), f"{name} does not define the transition/R2-R3 authority path"


def test_f1_issue_body_vs_comments_distinction() -> None:
    """Documents must distinguish Work Item Issue body (authoritative for R1) from comments (never authority)."""

    for name, path in [
        ("AGENTS.md", AGENTS_MD),
        ("source_of_truth", SOURCE_OF_TRUTH_MD),
    ]:
        content = _read(path)
        assert "Issue body" in content or "Work Item" in content, (
            f"{name} does not reference the Issue body / Work Item"
        )
        assert "comment" in content.lower(), (
            f"{name} does not distinguish Issue/PR comments from the Issue body"
        )


# =====================================================================
# F2 — R1 publication is a narrow exception; R2 publication is bounded
# =====================================================================


def test_f2_r1_publication_narrow_exception_defined() -> None:
    """R1 publication must be defined as a narrow exception (bounded branch push + Draft PR only)."""

    for name, path in [("AGENTS.md", AGENTS_MD), ("roadmap", ROADMAP_MD)]:
        content = _read(path)
        assert "non-main" in content.lower() or "non-`main`" in content, (
            f"{name} does not bound R1 push to non-main branch"
        )
        assert "Draft PR" in content or "Draft pr" in content, (
            f"{name} does not bound R1 publication to Draft PR"
        )
        assert "no merge" in content.lower() or "merge" in content.lower(), (
            f"{name} does not state the no-merge constraint on R1 publication"
        )


def test_f2_r2_publication_precisely_bounded() -> None:
    """R2 publication must be precisely bounded (main push, merge, mark-ready, etc.)."""

    for name, path in [("AGENTS.md", AGENTS_MD), ("roadmap", ROADMAP_MD)]:
        content = _read(path)
        for term in ["direct", "main", "merge"]:
            assert term in content.lower(), f"{name} does not bound R2 publication term: {term}"
        assert "mark" in content.lower() and "ready" in content.lower(), (
            f"{name} does not bound R2 mark-ready"
        )


def test_f2_r1_template_risk_justification_allows_narrow_publication() -> None:
    """The R1 risk-justification prompt must NOT deny the narrow R1 publication exception.

    A valid R1 task that pushes a branch and creates a Draft PR must be able to truthfully
    complete the justification. The prompt must not require 'No operation touches network, publication'.
    """

    content = _read(R1_ISSUE_TEMPLATE)
    denial_patterns = [
        r"[Nn]o operation touches[^.]*network",
        r"[Nn]o operation touches[^.]*publication",
        r"[Nn]etwork[^.]*publication[^.]*forbidden",
    ]
    for pat in denial_patterns:
        assert not re.search(pat, content), (
            f"R1 template risk-justification prompt denies the narrow R1 publication exception: pattern {pat}"
        )


def test_f2_r1_template_authorizes_branch_push_and_draft_pr() -> None:
    content = _read(R1_ISSUE_TEMPLATE)
    assert "feature-branch" in content.lower() or "feature branch" in content.lower(), (
        "R1 template does not reference feature-branch push"
    )
    assert "Draft PR" in content or "Draft pr" in content or "draft" in content.lower(), (
        "R1 template does not reference Draft PR creation"
    )


# =====================================================================
# F3 — No hard-coded permanent main SHA
# =====================================================================


def test_f3_agents_md_does_not_hard_code_permanent_main_sha() -> None:
    """Permanent operating guidance must not hard-code the transition base SHA as a forever requirement."""

    content = _read(AGENTS_MD)
    forbidden_patterns = [
        r"`main` is fixed (?:forever|at) `?" + re.escape(TRANSITION_BASE_SHA),
        r"main.*fixed.*" + re.escape(TRANSITION_BASE_SHA[:12]),
        r"Confirm `?main`? is fixed at `?" + re.escape(TRANSITION_BASE_SHA),
    ]
    for pat in forbidden_patterns:
        assert not re.search(pat, content), (
            f"AGENTS.md hard-codes the transition base SHA as a permanent main requirement: pattern {pat}"
        )


def test_f3_agents_md_uses_work_item_bound_base() -> None:
    """AGENTS.md must derive base SHA from the approved Work Item / current origin/main."""

    content = _read(AGENTS_MD)
    assert (
        "current" in content.lower() and "origin/main" in content.lower()
    ) or "Work Item" in content or "base_sha" in content, (
        "AGENTS.md does not bind base SHA to the current origin/main or Work Item"
    )


def test_f3_r1_template_does_not_hard_code_permanent_main_sha() -> None:
    content = _read(R1_ISSUE_TEMPLATE)
    placeholder_patterns = [r"<current origin/main SHA>", r"<current", r"origin/main"]
    has_placeholder = any(re.search(pat, content) for pat in placeholder_patterns)
    assert has_placeholder, (
        "R1 template does not use a generic placeholder for the current origin/main SHA"
    )


# =====================================================================
# F4 — One-time tracked transition-evidence exception is explicit
# =====================================================================


def test_f4_source_of_truth_has_transition_evidence_exception() -> None:
    """The source-of-truth matrix must explicitly identify the one-time transition-evidence exception."""

    content = _read(SOURCE_OF_TRUTH_MD)
    assert (
        "one-time" in content.lower()
        or "one time" in content.lower()
        or "transition-evidence" in content.lower()
        or "transition evidence" in content.lower()
    ), "Source-of-truth matrix does not declare a one-time transition-evidence exception"
    assert (
        "project_state/gates" in content
        or "bootstrap" in content.lower()
        or "command_plan" in content
        or "preflight" in content.lower()
    ), "Source-of-truth matrix does not reference the tracked transition-evidence files"


def test_f4_source_of_truth_prohibits_new_artifact_family() -> None:
    content = _read(SOURCE_OF_TRUTH_MD)
    assert "new" in content.lower() and "artifact" in content.lower(), (
        "Source-of-truth matrix does not address new artifact family creation"
    )


# =====================================================================
# F5 — Containment authority labels qualified as transition/R2-R3 only
# =====================================================================


def test_f5_containment_decision_authority_qualified() -> None:
    """Containment doc must qualify decision_packet.md / command_plan.json authority as transition/R2-R3 only."""

    content = _read(CONTAINMENT_MD)
    for term in ["decision_packet.md", "command_plan.json"]:
        if term in content:
            windows = []
            for m in re.finditer(re.escape(term), content):
                window_start = max(0, m.start() - 150)
                window_end = min(len(content), m.end() + 150)
                windows.append(content[window_start:window_end].lower())
            qualified = any(
                "transition" in w or "r2" in w or "r3" in w
                for w in windows
            )
            assert qualified, (
                f"Containment doc mentions {term} but does not qualify as transition/R2-R3 only"
            )


def test_f5_containment_two_authority_paths() -> None:
    content = _read(CONTAINMENT_MD)
    assert "R0/R1" in content or "ordinary R0/R1" in content.lower(), (
        "Containment doc does not reference the ordinary R0/R1 authority path"
    )


# =====================================================================
# F6 — Reuse inventory: every data row has exactly one legal disposition
# =====================================================================


def _parse_reuse_disposition_rows(content: str) -> list[tuple[str, str]]:
    """Parse reuse-inventory disposition table rows.

    Returns list of (row_text, disposition_token) for each data row.
    Skips header and separator rows.
    """

    rows = []
    in_table = False
    for line in content.splitlines():
        stripped = line.strip()
        if not stripped.startswith("|"):
            in_table = False
            continue
        cells = [c.strip() for c in stripped.strip("|").split("|")]
        if len(cells) < 2:
            continue
        if cells[0].lower() == "module" or cells[0].lower() == "document" or cells[0].lower() == "fact class":
            in_table = True
            continue
        if all(re.match(r"^[-:\s]+$", c) for c in cells):
            continue
        if not in_table:
            continue
        disposition_cell = cells[1] if len(cells) > 1 else ""
        rows.append((stripped, disposition_cell))
    return rows


def test_f6_reuse_inventory_every_data_row_has_legal_disposition() -> None:
    content = _read(REUSE_INVENTORY_MD)
    rows = _parse_reuse_disposition_rows(content)
    assert rows, "Reuse inventory has no parseable disposition data rows"
    for row_text, disposition_cell in rows:
        tokens = re.findall(r"[A-Z_]+", disposition_cell)
        legal_tokens = [t for t in tokens if t in LEGAL_REUSE_DISPOSITIONS]
        illegal_tokens = [t for t in tokens if t not in LEGAL_REUSE_DISPOSITIONS and t.isupper() and len(t) > 2]
        assert len(legal_tokens) == 1, (
            f"Reuse inventory row must have exactly one legal disposition; "
            f"found {legal_tokens} in: {row_text}"
        )
        assert not illegal_tokens or all(
            t in ("NO_NEW_FEATURES",) for t in illegal_tokens
        ) is False, (
            f"Reuse inventory row uses illegal disposition token(s) {illegal_tokens}: {row_text}"
        )


def test_f6_reuse_inventory_no_no_new_features_disposition() -> None:
    content = _read(REUSE_INVENTORY_MD)
    rows = _parse_reuse_disposition_rows(content)
    for row_text, disposition_cell in rows:
        assert "NO_NEW_FEATURES" not in disposition_cell, (
            f"Reuse inventory row uses NO_NEW_FEATURES as a disposition: {row_text}"
        )


# =====================================================================
# Required sections still present (kept from v3 but tightened)
# =====================================================================


def test_agents_md_has_required_sections() -> None:
    content = _read(AGENTS_MD)
    required = [
        "Repository purpose",
        "Current non-goals",
        "Risk tiers",
        "R0/R1",
        "R2/R3",
        "Branch and PR rules",
        "Prohibited actions",
        "Stop conditions",
    ]
    missing = [section for section in required if section not in content]
    assert not missing, f"AGENTS.md missing sections: {missing}"


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
