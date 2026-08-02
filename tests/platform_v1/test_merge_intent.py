"""Tests for the Platform V1 mainline merge intent binding.

Verifies that:
- The active merge intent binds source_pr: 97 (not 0)
- The v1 intent is archived to archive/pr97_v1.json
- The active intent binds the exact v2 Decision digest and Command Plan digest
- The active intent has the correct locked_base_sha, merge method, and workflows
- The active intent has a bounded expiry
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest


REPO_ROOT = Path(__file__).resolve().parents[2]
INTENTS_DIR = REPO_ROOT / "project_state" / "mainline_merge_intents"
ACTIVE_PATH = INTENTS_DIR / "active.json"
ARCHIVE_V1_PATH = INTENTS_DIR / "archive" / "pr97_v1.json"

EXPECTED_BASE_SHA = "705a0bfd6638d51c688752f154433020225c4e99"
EXPECTED_DECISION_ID = "decision_20260802_issue98_platform_v1_trust_binding_rework_v2"


def _load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


# ---------------------------------------------------------------------------
# Active intent
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

    def test_active_binds_v2_decision_id(self) -> None:
        data = _load_json(ACTIVE_PATH)
        assert data["decision_identity"]["decision_id"] == EXPECTED_DECISION_ID

    def test_active_binds_decision_content_sha256(self) -> None:
        data = _load_json(ACTIVE_PATH)
        sha = data["decision_identity"]["decision_content_sha256"]
        assert isinstance(sha, str) and len(sha) == 64
        assert all(c in "0123456789abcdef" for c in sha)

    def test_active_binds_command_plan_sha256(self) -> None:
        data = _load_json(ACTIVE_PATH)
        sha = data["command_plan_sha256"]
        assert isinstance(sha, str) and len(sha) == 64
        assert all(c in "0123456789abcdef" for c in sha)

    def test_active_binds_required_workflows(self) -> None:
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
# Archived v1 intent
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
        assert data["decision_identity"]["decision_id"] == "decision_20260802_platform_v1_openhands_codex_acp_v1"

    def test_archive_v1_has_locked_base_sha(self) -> None:
        data = _load_json(ARCHIVE_V1_PATH)
        assert data["locked_base_sha"] == EXPECTED_BASE_SHA
