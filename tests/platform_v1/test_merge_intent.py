"""Tests for the Platform V1 mainline merge intent binding.

Verifies that the active Bootstrap intent binds PR #112, B2, and the exact
Issue #111 Decision and Command Plan digests. The PR97 v1-v4, PR108 v1, and
PR110 v1 and rejected PR112 v1/v2/v3/v4/v5 intents remain archived byte-for-byte.
"""

from __future__ import annotations

import hashlib
import json
import subprocess
from pathlib import Path

import pytest


REPO_ROOT = Path(__file__).resolve().parents[2]
INTENTS_DIR = REPO_ROOT / "project_state" / "mainline_merge_intents"
ACTIVE_PATH = INTENTS_DIR / "active.json"
ARCHIVE_V1_PATH = INTENTS_DIR / "archive" / "pr97_v1.json"
ARCHIVE_V2_PATH = INTENTS_DIR / "archive" / "pr97_v2.json"
ARCHIVE_V3_PATH = INTENTS_DIR / "archive" / "pr97_v3.json"
ARCHIVE_V4_PATH = INTENTS_DIR / "archive" / "pr97_v4.json"
ARCHIVE_PR108_PATH = INTENTS_DIR / "archive" / "pr108_v1.json"
ARCHIVE_PR110_PATH = INTENTS_DIR / "archive" / "pr110_v1.json"
ARCHIVE_PR112_PATH = INTENTS_DIR / "archive" / "pr112_v1.json"
ARCHIVE_PR112_V2_PATH = INTENTS_DIR / "archive" / "pr112_v2.json"
ARCHIVE_PR112_V3_PATH = INTENTS_DIR / "archive" / "pr112_v3.json"
ARCHIVE_PR112_V4_PATH = INTENTS_DIR / "archive" / "pr112_v4.json"
ARCHIVE_PR112_V5_PATH = INTENTS_DIR / "archive" / "pr112_v5.json"
ARCHIVE_PR112_V6_PATH = INTENTS_DIR / "archive" / "pr112_v6.json"
DECISION_PATH = REPO_ROOT / "project_state" / "decision_packet.md"
COMMAND_PLAN_PATH = REPO_ROOT / "project_state" / "gates" / "command_plan.json"

EXPECTED_PR97_BASE_SHA = "705a0bfd6638d51c688752f154433020225c4e99"
EXPECTED_BOOTSTRAP_BASE_SHA = "93984db182b7ee11b3ccb8795bb5fc3741205b92"
EXPECTED_BOOTSTRAP_DECISION_ID = (
    "decision_20260804_issue111_pr112_bootstrap_path_tree_seal_v6"
)
EXPECTED_V4_DECISION_ID = (
    "decision_20260802_issue100_platform_v1_authority_collector_v4"
)
EXPECTED_V3_DECISION_ID = (
    "decision_20260802_issue99_platform_v1_live_evidence_boundary_v3"
)
EXPECTED_V2_DECISION_ID = (
    "decision_20260802_issue98_platform_v1_trust_binding_rework_v2"
)
EXPECTED_V1_DECISION_ID = "decision_20260802_platform_v1_openhands_codex_acp_v1"
EXPECTED_PR97_V4_GIT_BLOB = "1afd619ef90df7b01255d1cd16b483190f616df6"
EXPECTED_PR108_V1_GIT_BLOB = "32ca8e328e28467fcbe1857b7d300152fc89bdf4"
EXPECTED_PR110_V1_GIT_BLOB = "bb7ce4c1c61a88e63e0bdc14e0ce2fa4967fc842"
EXPECTED_PR112_V1_GIT_BLOB = "639581296b8dfd8038871010f99aa68401568353"
EXPECTED_PR112_V2_GIT_BLOB = "770f19faba9e0f040656341beec0089ca87d3545"
EXPECTED_PR112_V3_GIT_BLOB = "3c246c1377df2504bb95fbd4d9865860b017b049"
EXPECTED_PR112_V4_GIT_BLOB = "78104b6ae6746b0b5bf3b409f7dd2054ca23fcd9"
EXPECTED_PR112_V5_GIT_BLOB = "64e555a98a1b748b2e320abb4559922bdc0d3649"
EXPECTED_PR112_V6_GIT_BLOB = "ed960c0e117051e8915b457028e4c0e5f0c3e07c"


def _load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def _parse_decision_meta() -> dict:
    from reverse_agent.project_state import extract_markdown_json_block
    text = DECISION_PATH.read_text(encoding="utf-8")
    result = extract_markdown_json_block(text, "decision_meta")
    if not result.get("found"):
        raise AssertionError("decision_meta JSON block not found in decision_packet.md")
    if result.get("parse_error"):
        raise AssertionError(f"decision_meta block parse error: {result['parse_error']}")
    return result


def _parse_decision_contract() -> dict:
    from reverse_agent.project_state import extract_markdown_json_block
    text = DECISION_PATH.read_text(encoding="utf-8")
    result = extract_markdown_json_block(text, "decision_contract")
    if not result.get("found"):
        raise AssertionError("decision_contract JSON block not found in decision_packet.md")
    if result.get("parse_error"):
        raise AssertionError(f"decision_contract block parse error: {result['parse_error']}")
    return result


# ---------------------------------------------------------------------------
# Active intent (dynamically bound to current Decision via parser)
# ---------------------------------------------------------------------------

class TestActiveMergeIntent:
    def test_active_file_exists(self) -> None:
        assert ACTIVE_PATH.exists(), f"active.json not found at {ACTIVE_PATH}"

    def test_active_binds_current_decision_source_pr(self) -> None:
        data = _load_json(ACTIVE_PATH)
        contract = _parse_decision_contract()
        expected_pr = contract["active_pr"]
        assert data["source_pr"] == expected_pr, (
            f"active source_pr={data['source_pr']} != Decision active_pr={expected_pr}"
        )

    def test_active_does_not_have_source_pr_zero(self) -> None:
        data = _load_json(ACTIVE_PATH)
        assert data["source_pr"] != 0, "active intent must not retain source_pr=0"

    def test_active_binds_current_decision_locked_base_sha(self) -> None:
        data = _load_json(ACTIVE_PATH)
        contract = _parse_decision_contract()
        expected_base = contract["activation_base_sha"]
        assert data["locked_base_sha"] == expected_base

    def test_active_binds_merge_method(self) -> None:
        data = _load_json(ACTIVE_PATH)
        assert data["allowed_merge_method"] == "merge"

    def test_active_binds_current_decision_id(self) -> None:
        data = _load_json(ACTIVE_PATH)
        meta = _parse_decision_meta()
        expected_id = meta["decision_id"]
        assert data["decision_identity"]["decision_id"] == expected_id

    def test_active_decision_content_sha256_is_64_hex(self) -> None:
        data = _load_json(ACTIVE_PATH)
        sha = data["decision_identity"]["decision_content_sha256"]
        assert isinstance(sha, str) and len(sha) == 64
        assert all(c in "0123456789abcdef" for c in sha)
        assert sha == hashlib.sha256(DECISION_PATH.read_bytes()).hexdigest()

    def test_active_command_plan_sha256_is_64_hex(self) -> None:
        data = _load_json(ACTIVE_PATH)
        sha = data["command_plan_sha256"]
        assert isinstance(sha, str) and len(sha) == 64
        assert all(c in "0123456789abcdef" for c in sha)
        assert sha == hashlib.sha256(COMMAND_PLAN_PATH.read_bytes()).hexdigest()

    def test_active_required_workflows_include_all_four(self) -> None:
        data = _load_json(ACTIVE_PATH)
        workflows = data["required_workflows"]
        assert "CI" in workflows
        assert "Decision Preflight" in workflows
        assert "State Gate (pull_request)" in workflows
        assert "State Gate (push)" in workflows

    def test_active_has_bounded_expiry(self) -> None:
        data = _load_json(ACTIVE_PATH)
        expires = data.get("expires_at", "")
        assert expires, "active intent must have a bounded expiry"
        assert expires.endswith("Z")

    def test_decision_meta_unique_and_valid(self) -> None:
        meta = _parse_decision_meta()
        assert meta["schema_version"] == 1
        assert isinstance(meta["decision_id"], str)
        assert isinstance(meta["round_id"], str)
        assert meta["status"] == "APPROVED"
        assert isinstance(meta.get("skill_profiles"), list)

    def test_decision_contract_unique_and_valid(self) -> None:
        contract = _parse_decision_contract()
        assert isinstance(contract["active_pr"], int)
        assert isinstance(contract["activation_base_sha"], str)
        assert isinstance(contract["required_branch"], str)
        assert isinstance(contract["starting_head"], str)
        assert contract["allowed_merge_method"] == "merge"
        assert contract["risk_tier"] == "R2"
        assert contract["decision_commit_must_precede_implementation"] is True

    def test_decision_id_format_matches_production(self) -> None:
        meta = _parse_decision_meta()
        assert meta["decision_id"].startswith("decision_")
        assert "_" in meta["decision_id"][9:]

    def test_round_id_matches_decision_id(self) -> None:
        meta = _parse_decision_meta()
        assert meta["round_id"].startswith("round_")
        assert meta["decision_id"][9:] == meta["round_id"][6:]

    def test_command_plan_id_matches_decision(self) -> None:
        plan = _load_json(COMMAND_PLAN_PATH)
        meta = _parse_decision_meta()
        assert plan["decision_id"] == meta["decision_id"]
        assert plan["round_id"] == meta["round_id"]


# ---------------------------------------------------------------------------
# Archived v1 intent (PR-less, source_pr=0)
# ---------------------------------------------------------------------------

class TestArchivedV1Intent:
    def test_archive_v1_file_exists(self) -> None:
        assert ARCHIVE_V1_PATH.exists(), f"pr97_v1.json not found at {ARCHIVE_V1_PATH}"

    def test_archive_v1_has_source_pr_zero(self) -> None:
        """The v1 intent had source_pr=0 (PR-less); it must be preserved as-is."""
        data = _load_json(ARCHIVE_V1_PATH)
        assert data["source_pr"] == 0

    def test_archive_v1_binds_v1_decision_id(self) -> None:
        data = _load_json(ARCHIVE_V1_PATH)
        assert data["decision_identity"]["decision_id"] == EXPECTED_V1_DECISION_ID

    def test_archive_v1_has_locked_base_sha(self) -> None:
        data = _load_json(ARCHIVE_V1_PATH)
        assert data["locked_base_sha"] == EXPECTED_PR97_BASE_SHA


# ---------------------------------------------------------------------------
# Archived v2 intent (trust binding rework)
# ---------------------------------------------------------------------------

class TestArchivedV2Intent:
    def test_archive_v2_file_exists(self) -> None:
        assert ARCHIVE_V2_PATH.exists(), f"pr97_v2.json not found at {ARCHIVE_V2_PATH}"

    def test_archive_v2_binds_v2_decision_id(self) -> None:
        data = _load_json(ARCHIVE_V2_PATH)
        assert data["decision_identity"]["decision_id"] == EXPECTED_V2_DECISION_ID

    def test_archive_v2_preserves_v2_source_pr(self) -> None:
        data = _load_json(ARCHIVE_V2_PATH)
        assert data["source_pr"] == 97


# ---------------------------------------------------------------------------
# Archived v3 intent (live evidence boundary)
# ---------------------------------------------------------------------------

class TestArchivedV3Intent:
    def test_archive_v3_file_exists(self) -> None:
        assert ARCHIVE_V3_PATH.exists(), f"pr97_v3.json not found at {ARCHIVE_V3_PATH}"

    def test_archive_v3_binds_v3_decision_id(self) -> None:
        data = _load_json(ARCHIVE_V3_PATH)
        assert data["decision_identity"]["decision_id"] == EXPECTED_V3_DECISION_ID

    def test_archive_v3_preserves_v3_source_pr(self) -> None:
        data = _load_json(ARCHIVE_V3_PATH)
        assert data["source_pr"] == 97

    def test_archive_v3_preserves_v3_decision_content_sha256(self) -> None:
        data = _load_json(ARCHIVE_V3_PATH)
        sha = data["decision_identity"]["decision_content_sha256"]
        assert isinstance(sha, str) and len(sha) == 64
        assert all(c in "0123456789abcdef" for c in sha)

    def test_archive_v3_preserves_v3_command_plan_sha256(self) -> None:
        data = _load_json(ARCHIVE_V3_PATH)
        sha = data["command_plan_sha256"]
        assert isinstance(sha, str) and len(sha) == 64
        assert all(c in "0123456789abcdef" for c in sha)

    def test_archive_v3_preserves_v3_required_workflows(self) -> None:
        data = _load_json(ARCHIVE_V3_PATH)
        workflows = data["required_workflows"]
        assert "CI" in workflows
        assert "Decision Preflight" in workflows
        assert "State Gate (pull_request)" in workflows
        assert "State Gate (push)" in workflows


# ---------------------------------------------------------------------------
# Archived v4 intent (authority collector, exact B0 active bytes)
# ---------------------------------------------------------------------------

class TestArchivedV4Intent:
    def test_archive_v4_file_exists(self) -> None:
        assert ARCHIVE_V4_PATH.exists(), f"pr97_v4.json not found at {ARCHIVE_V4_PATH}"

    def test_archive_v4_is_exact_b0_active_blob(self) -> None:
        payload = ARCHIVE_V4_PATH.read_bytes()
        header = f"blob {len(payload)}\0".encode("ascii")
        assert hashlib.sha1(header + payload).hexdigest() == EXPECTED_PR97_V4_GIT_BLOB

    def test_archive_v4_binds_v4_decision_and_pr97(self) -> None:
        data = _load_json(ARCHIVE_V4_PATH)
        assert data["source_pr"] == 97
        assert data["decision_identity"]["decision_id"] == EXPECTED_V4_DECISION_ID
        assert data["locked_base_sha"] == EXPECTED_PR97_BASE_SHA


# ---------------------------------------------------------------------------
# Archived PR108 v1 intent (exact B1 active bytes)
# ---------------------------------------------------------------------------

class TestArchivedPR108Intent:
    def test_archive_pr108_file_exists(self) -> None:
        assert ARCHIVE_PR108_PATH.exists(), (
            f"pr108_v1.json not found at {ARCHIVE_PR108_PATH}"
        )

    def test_archive_pr108_is_exact_b1_active_blob(self) -> None:
        payload = ARCHIVE_PR108_PATH.read_bytes()
        header = f"blob {len(payload)}\0".encode("ascii")
        assert hashlib.sha1(header + payload).hexdigest() == EXPECTED_PR108_V1_GIT_BLOB

    def test_archive_pr108_binds_pr108_and_b0(self) -> None:
        data = _load_json(ARCHIVE_PR108_PATH)
        assert data["source_pr"] == 108
        assert data["decision_identity"]["decision_id"] == (
            "decision_20260804_issue107_state_gate_bootstrap_pr108_v1"
        )
        assert data["locked_base_sha"] == (
            "fa4f240f7dffff78cdb182ce8655c2e2d7cb241f"
        )


# ---------------------------------------------------------------------------
# Archived PR110 v1 intent (exact B2 active bytes)
# ---------------------------------------------------------------------------

class TestArchivedPR110Intent:
    def test_archive_pr110_file_exists(self) -> None:
        assert ARCHIVE_PR110_PATH.exists(), (
            f"pr110_v1.json not found at {ARCHIVE_PR110_PATH}"
        )

    def test_archive_pr110_is_exact_b2_active_blob(self) -> None:
        payload = ARCHIVE_PR110_PATH.read_bytes()
        header = f"blob {len(payload)}\0".encode("ascii")
        assert hashlib.sha1(header + payload).hexdigest() == EXPECTED_PR110_V1_GIT_BLOB

    def test_archive_pr110_binds_pr110_and_b1(self) -> None:
        data = _load_json(ARCHIVE_PR110_PATH)
        assert data["source_pr"] == 110
        assert data["decision_identity"]["decision_id"] == (
            "decision_20260804_issue109_pr110_bootstrap_test_rebind_v1"
        )
        assert data["locked_base_sha"] == (
            "4aacd7f614342f5ca123b2afccdb9a49df886775"
        )


# ---------------------------------------------------------------------------
# Archived rejected PR112 v1 intent (exact v1 active bytes)
# ---------------------------------------------------------------------------

class TestArchivedPR112V1Intent:
    def test_archive_pr112_v1_file_exists(self) -> None:
        assert ARCHIVE_PR112_PATH.exists(), (
            f"pr112_v1.json not found at {ARCHIVE_PR112_PATH}"
        )

    def test_archive_pr112_v1_is_exact_rejected_active_blob(self) -> None:
        payload = ARCHIVE_PR112_PATH.read_bytes()
        header = f"blob {len(payload)}\0".encode("ascii")
        assert hashlib.sha1(header + payload).hexdigest() == EXPECTED_PR112_V1_GIT_BLOB

    def test_archive_pr112_v1_preserves_identity_and_base(self) -> None:
        data = _load_json(ARCHIVE_PR112_PATH)
        assert data["source_pr"] == 112
        assert data["decision_identity"]["decision_id"] == (
            "decision_20260804_issue111_pr112_bootstrap_v13_retry_v1"
        )
        assert data["locked_base_sha"] == EXPECTED_BOOTSTRAP_BASE_SHA


# ---------------------------------------------------------------------------
# Archived rejected PR112 v2 intent (exact v2 active bytes)
# ---------------------------------------------------------------------------

class TestArchivedPR112V2Intent:
    def test_archive_pr112_v2_file_exists(self) -> None:
        assert ARCHIVE_PR112_V2_PATH.exists(), (
            f"pr112_v2.json not found at {ARCHIVE_PR112_V2_PATH}"
        )

    def test_archive_pr112_v2_is_exact_rejected_active_blob(self) -> None:
        payload = ARCHIVE_PR112_V2_PATH.read_bytes()
        header = f"blob {len(payload)}\0".encode("ascii")
        assert hashlib.sha1(header + payload).hexdigest() == EXPECTED_PR112_V2_GIT_BLOB

    def test_archive_pr112_v2_preserves_identity_and_base(self) -> None:
        data = _load_json(ARCHIVE_PR112_V2_PATH)
        assert data["source_pr"] == 112
        assert data["decision_identity"]["decision_id"] == (
            "decision_20260804_issue111_pr112_candidate_test_semantic_guard_v2"
        )
        assert data["locked_base_sha"] == EXPECTED_BOOTSTRAP_BASE_SHA


# ---------------------------------------------------------------------------
# Archived rejected PR112 v3 intent (exact v3 active bytes)
# ---------------------------------------------------------------------------

class TestArchivedPR112V3Intent:
    def test_archive_pr112_v3_file_exists(self) -> None:
        assert ARCHIVE_PR112_V3_PATH.exists(), (
            f"pr112_v3.json not found at {ARCHIVE_PR112_V3_PATH}"
        )

    def test_archive_pr112_v3_is_exact_rejected_active_blob(self) -> None:
        payload = ARCHIVE_PR112_V3_PATH.read_bytes()
        header = f"blob {len(payload)}\0".encode("ascii")
        assert hashlib.sha1(header + payload).hexdigest() == EXPECTED_PR112_V3_GIT_BLOB

    def test_archive_pr112_v3_preserves_identity_and_base(self) -> None:
        data = _load_json(ARCHIVE_PR112_V3_PATH)
        assert data["source_pr"] == 112
        assert data["decision_identity"]["decision_id"] == (
            "decision_20260804_issue111_pr112_utf8_semantic_guard_v3"
        )
        assert data["locked_base_sha"] == EXPECTED_BOOTSTRAP_BASE_SHA


# ---------------------------------------------------------------------------
# Archived rejected PR112 v4 intent (exact v4 active bytes)
# ---------------------------------------------------------------------------

class TestArchivedPR112V4Intent:
    def test_archive_pr112_v4_file_exists(self) -> None:
        assert ARCHIVE_PR112_V4_PATH.exists(), (
            f"pr112_v4.json not found at {ARCHIVE_PR112_V4_PATH}"
        )

    def test_archive_pr112_v4_is_exact_rejected_active_blob(self) -> None:
        payload = ARCHIVE_PR112_V4_PATH.read_bytes()
        header = f"blob {len(payload)}\0".encode("ascii")
        assert hashlib.sha1(header + payload).hexdigest() == EXPECTED_PR112_V4_GIT_BLOB

    def test_archive_pr112_v4_preserves_identity_and_base(self) -> None:
        data = _load_json(ARCHIVE_PR112_V4_PATH)
        assert data["source_pr"] == 112
        assert data["decision_identity"]["decision_id"] == (
            "decision_20260804_issue111_pr112_marker_movement_guard_v4"
        )
        assert data["locked_base_sha"] == EXPECTED_BOOTSTRAP_BASE_SHA


# ---------------------------------------------------------------------------
# Archived rejected PR112 v5 intent (exact v5 active bytes)
# ---------------------------------------------------------------------------

class TestArchivedPR112V5Intent:
    def test_archive_pr112_v5_file_exists(self) -> None:
        assert ARCHIVE_PR112_V5_PATH.exists(), (
            f"pr112_v5.json not found at {ARCHIVE_PR112_V5_PATH}"
        )

    def test_archive_pr112_v5_is_exact_rejected_active_blob(self) -> None:
        payload = ARCHIVE_PR112_V5_PATH.read_bytes()
        header = f"blob {len(payload)}\0".encode("ascii")
        assert hashlib.sha1(header + payload).hexdigest() == EXPECTED_PR112_V5_GIT_BLOB

    def test_archive_pr112_v5_preserves_identity_and_base(self) -> None:
        data = _load_json(ARCHIVE_PR112_V5_PATH)
        assert data["source_pr"] == 112
        assert data["decision_identity"]["decision_id"] == (
            "decision_20260804_issue111_pr112_long_validation_budget_v5"
        )
        assert data["locked_base_sha"] == EXPECTED_BOOTSTRAP_BASE_SHA


# ---------------------------------------------------------------------------
# Archived PR112 v6 intent (exact last-active-before-migration bytes)
# ---------------------------------------------------------------------------

class TestArchivedPR112V6Intent:
    def test_archive_pr112_v6_file_exists(self) -> None:
        assert ARCHIVE_PR112_V6_PATH.exists(), (
            f"pr112_v6.json not found at {ARCHIVE_PR112_V6_PATH}"
        )

    def test_archive_pr112_v6_is_exact_active_blob_before_migration(self) -> None:
        payload = ARCHIVE_PR112_V6_PATH.read_bytes()
        header = f"blob {len(payload)}\0".encode("ascii")
        assert hashlib.sha1(header + payload).hexdigest() == EXPECTED_PR112_V6_GIT_BLOB

    def test_archive_pr112_v6_preserves_identity_and_base(self) -> None:
        data = _load_json(ARCHIVE_PR112_V6_PATH)
        assert data["source_pr"] == 112
        assert data["decision_identity"]["decision_id"] == (
            "decision_20260804_issue111_pr112_bootstrap_path_tree_seal_v6"
        )
        assert data["locked_base_sha"] == EXPECTED_BOOTSTRAP_BASE_SHA


# ---------------------------------------------------------------------------
# v4 active intent differs from v3 archive
# ---------------------------------------------------------------------------

class TestV4DiffersFromV3:
    def test_v4_decision_id_differs_from_v3(self) -> None:
        active = _load_json(ACTIVE_PATH)
        v3 = _load_json(ARCHIVE_V3_PATH)
        assert active["decision_identity"]["decision_id"] != v3["decision_identity"]["decision_id"]

    def test_v4_decision_content_sha256_differs_from_v3(self) -> None:
        active = _load_json(ACTIVE_PATH)
        v3 = _load_json(ARCHIVE_V3_PATH)
        assert (
            active["decision_identity"]["decision_content_sha256"]
            != v3["decision_identity"]["decision_content_sha256"]
        )

    def test_v4_command_plan_sha256_differs_from_v3(self) -> None:
        active = _load_json(ACTIVE_PATH)
        v3 = _load_json(ARCHIVE_V3_PATH)
        assert active["command_plan_sha256"] != v3["command_plan_sha256"]

    def test_v4_intent_id_differs_from_v3(self) -> None:
        active = _load_json(ACTIVE_PATH)
        v3 = _load_json(ARCHIVE_V3_PATH)
        assert active["intent_id"] != v3["intent_id"]


# ---------------------------------------------------------------------------
# Immutability regression: Decision bytes match the unique Decision commit,
# or (for a clean product-only landing) are inherited byte-for-byte from
# starting_head with no Decision-modifying commit in the range.
# ---------------------------------------------------------------------------

def _blob_at(reefspec: str) -> str:
    try:
        return subprocess.check_output(
            ["git", "rev-parse", reefspec],
            cwd=REPO_ROOT,
            encoding="utf-8",
            errors="strict",
        ).strip()
    except subprocess.CalledProcessError:
        return ""


def _decision_modifying_commits(starting_head: str) -> list[str]:
    log_out = subprocess.check_output(
        ["git", "rev-list", f"{starting_head}..HEAD"],
        cwd=REPO_ROOT,
        encoding="utf-8",
    ).strip()
    commits = [c for c in log_out.splitlines() if c]
    mod_commits: list[str] = []
    for sha in commits:
        names = subprocess.check_output(
            ["git", "diff-tree", "--no-commit-id", "--name-only", "-r", sha],
            cwd=REPO_ROOT,
            encoding="utf-8",
            errors="strict",
        ).strip()
        if "project_state/decision_packet.md" in names.splitlines():
            mod_commits.append(sha)
    return mod_commits


class TestDecisionImmutability:
    def test_single_decision_commit_in_range(self) -> None:
        """At most one commit modifies decision_packet.md in starting_head..HEAD.

        Case A: a Decision-modifying commit exists -> there is exactly one.
        Case B: no Decision-modifying commit exists -> this is a legal clean
        product-only landing that inherits an immutable Decision; the test
        still proves the range contains no hidden Decision mutation.
        """
        contract = _parse_decision_contract()
        starting_head = contract["starting_head"]
        mod_commits = _decision_modifying_commits(starting_head)
        if not mod_commits:
            assert _blob_at(
                f"{starting_head}:project_state/decision_packet.md"
            ), (
                "clean product-only landing requires an inherited Decision "
                "blob present at starting_head"
            )
            assert (
                _blob_at(
                    f"{starting_head}:project_state/decision_packet.md"
                )
                == _blob_at("HEAD:project_state/decision_packet.md")
            ), (
                "clean product-only landing inherited a Decision whose bytes "
                "diverged from HEAD"
            )
            return
        assert len(mod_commits) == 1, (
            f"expected at most 1 Decision-modifying commit, got {len(mod_commits)}"
        )

    def test_decision_bytes_unchanged_since_commit(self) -> None:
        """HEAD's Decision blob equals the blob of the unique Decision commit,
        or (when no Decision commit exists) equals the inherited blob at
        starting_head -- proving no later commit altered Decision bytes.
        """
        contract = _parse_decision_contract()
        starting_head = contract["starting_head"]
        head_blob = _blob_at("HEAD:project_state/decision_packet.md")
        mod_commits = _decision_modifying_commits(starting_head)
        if not mod_commits:
            assert head_blob, (
                "clean product-only landing requires the Decision blob at HEAD"
            )
            assert head_blob == _blob_at(
                f"{starting_head}:project_state/decision_packet.md"
            ), (
                "clean product-only landing inherited a Decision whose bytes "
                "diverged from HEAD"
            )
            return
        assert len(mod_commits) == 1, (
            f"expected exactly 1 Decision-modifying commit to compare bytes, "
            f"got {len(mod_commits)}"
        )
        assert (
            _blob_at(f"{mod_commits[0]}:project_state/decision_packet.md")
            == head_blob
        ), "Decision file bytes changed after its commit"

    def test_decision_commit_precedes_implementation(self) -> None:
        """In starting_head..HEAD the single Decision-modifying commit is the
        oldest commit (appears first in reverse-chronological rev-list order),
        i.e. it precedes any later implementation commit.

        When no Decision-modifying commit exists this is a legal clean
        product-only landing: the inherited Decision bytes are verified in
        test_decision_bytes_unchanged_since_commit instead.
        """
        contract = _parse_decision_contract()
        starting_head = contract["starting_head"]
        mod_commits = _decision_modifying_commits(starting_head)
        if not mod_commits:
            assert (
                _blob_at(
                    f"{starting_head}:project_state/decision_packet.md"
                )
                == _blob_at("HEAD:project_state/decision_packet.md")
            )
            return
        assert len(mod_commits) == 1, (
            f"expected exactly 1 Decision-modifying commit to order, "
            f"got {len(mod_commits)}"
        )
        log_out = subprocess.check_output(
            ["git", "rev-list", f"{starting_head}..HEAD"],
            cwd=REPO_ROOT,
            encoding="utf-8",
        ).strip()
        commits = [c for c in log_out.splitlines() if c]
        assert commits, "no commits in starting_head..HEAD"
        idx = commits.index(mod_commits[0])
        assert idx == len(commits) - 1, (
            f"Decision commit must be the oldest commit after starting_head "
            f"(index {idx}, expected {len(commits) - 1} in newest-first rev-list)"
        )

    def test_no_duplicate_decision_json_blocks(self) -> None:
        """Decision file must contain exactly one decision_meta and one decision_contract block."""
        text = DECISION_PATH.read_text(encoding="utf-8")
        import re
        meta_blocks = re.findall(r"```json\s+decision_meta\n", text)
        contract_blocks = re.findall(r"```json\s+decision_contract\n", text)
        assert len(meta_blocks) == 1, f"expected 1 decision_meta block, found {len(meta_blocks)}"
        assert len(contract_blocks) == 1, f"expected 1 decision_contract block, found {len(contract_blocks)}"

    def test_decision_json_blocks_parse(self) -> None:
        """Decision JSON blocks must parse and be internally consistent."""
        from reverse_agent.project_state import extract_markdown_json_block
        meta = _parse_decision_meta()
        contract = _parse_decision_contract()
        active = _load_json(ACTIVE_PATH)
        assert meta["decision_id"].startswith("decision_")
        assert isinstance(contract["active_pr"], int) and contract["active_pr"] > 0
        assert len(contract["activation_base_sha"]) == 40
        assert all(c in "0123456789abcdef" for c in contract["activation_base_sha"])
        assert contract["active_pr"] == active["source_pr"]
        assert contract["activation_base_sha"] == active["locked_base_sha"]
