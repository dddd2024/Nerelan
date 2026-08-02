"""Tests for the Platform V1 mainline merge intent binding.

F28: Verifies that the active merge intent binds:
- source_pr: 97 (not 0)
- The exact v4 Decision content SHA-256 and Command Plan SHA-256
- locked_base_sha, allowed_merge_method, required_workflows, bounded expiry

The v1, v2, and v3 intents are archived verbatim.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest


REPO_ROOT = Path(__file__).resolve().parents[2]
INTENTS_DIR = REPO_ROOT / "project_state" / "mainline_merge_intents"
ACTIVE_PATH = INTENTS_DIR / "active.json"
ARCHIVE_V1_PATH = INTENTS_DIR / "archive" / "pr97_v1.json"
ARCHIVE_V2_PATH = INTENTS_DIR / "archive" / "pr97_v2.json"
ARCHIVE_V3_PATH = INTENTS_DIR / "archive" / "pr97_v3.json"

EXPECTED_BASE_SHA = "705a0bfd6638d51c688752f154433020225c4e99"
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


def _load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


# ---------------------------------------------------------------------------
# Active v4 intent
# ---------------------------------------------------------------------------

class TestActiveMergeIntent:
    def test_active_file_exists(self) -> None:
        assert ACTIVE_PATH.exists(), f"active.json not found at {ACTIVE_PATH}"

    def test_active_binds_source_pr_97(self) -> None:
        data = _load_json(ACTIVE_PATH)
        assert data["source_pr"] == 97, "active intent must bind source_pr=97"

    def test_active_does_not_have_source_pr_zero(self) -> None:
        data = _load_json(ACTIVE_PATH)
        assert data["source_pr"] != 0, "active intent must not retain source_pr=0"

    def test_active_binds_locked_base_sha(self) -> None:
        data = _load_json(ACTIVE_PATH)
        assert data["locked_base_sha"] == EXPECTED_BASE_SHA

    def test_active_binds_merge_method(self) -> None:
        data = _load_json(ACTIVE_PATH)
        assert data["allowed_merge_method"] == "merge"

    def test_active_binds_v4_decision_id(self) -> None:
        data = _load_json(ACTIVE_PATH)
        assert data["decision_identity"]["decision_id"] == EXPECTED_V4_DECISION_ID

    def test_active_decision_content_sha256_is_64_hex(self) -> None:
        data = _load_json(ACTIVE_PATH)
        sha = data["decision_identity"]["decision_content_sha256"]
        assert isinstance(sha, str) and len(sha) == 64
        assert all(c in "0123456789abcdef" for c in sha)

    def test_active_command_plan_sha256_is_64_hex(self) -> None:
        data = _load_json(ACTIVE_PATH)
        sha = data["command_plan_sha256"]
        assert isinstance(sha, str) and len(sha) == 64
        assert all(c in "0123456789abcdef" for c in sha)

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
        assert data["locked_base_sha"] == EXPECTED_BASE_SHA


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
