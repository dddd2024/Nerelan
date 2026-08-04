"""Tests for the Platform V1 mainline merge intent binding.

Verifies that the active Bootstrap intent binds PR #112, B2, and the exact
Issue #111 Decision and Command Plan digests. The PR97 v1-v4, PR108 v1, and
PR110 v1 and rejected PR112 v1 intents remain archived byte-for-byte.
"""

from __future__ import annotations

import hashlib
import json
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
DECISION_PATH = REPO_ROOT / "project_state" / "decision_packet.md"
COMMAND_PLAN_PATH = REPO_ROOT / "project_state" / "gates" / "command_plan.json"

EXPECTED_PR97_BASE_SHA = "705a0bfd6638d51c688752f154433020225c4e99"
EXPECTED_BOOTSTRAP_BASE_SHA = "93984db182b7ee11b3ccb8795bb5fc3741205b92"
EXPECTED_BOOTSTRAP_DECISION_ID = (
    "decision_20260804_issue111_pr112_candidate_test_semantic_guard_v2"
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


def _load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


# ---------------------------------------------------------------------------
# Active PR112 Bootstrap intent
# ---------------------------------------------------------------------------

class TestActiveMergeIntent:
    def test_active_file_exists(self) -> None:
        assert ACTIVE_PATH.exists(), f"active.json not found at {ACTIVE_PATH}"

    def test_active_binds_source_pr_112(self) -> None:
        data = _load_json(ACTIVE_PATH)
        assert data["source_pr"] == 112, "active intent must bind source_pr=112"

    def test_active_does_not_have_source_pr_zero(self) -> None:
        data = _load_json(ACTIVE_PATH)
        assert data["source_pr"] != 0, "active intent must not retain source_pr=0"

    def test_active_binds_locked_base_sha(self) -> None:
        data = _load_json(ACTIVE_PATH)
        assert data["locked_base_sha"] == EXPECTED_BOOTSTRAP_BASE_SHA

    def test_active_binds_merge_method(self) -> None:
        data = _load_json(ACTIVE_PATH)
        assert data["allowed_merge_method"] == "merge"

    def test_active_binds_bootstrap_decision_id(self) -> None:
        data = _load_json(ACTIVE_PATH)
        assert data["decision_identity"]["decision_id"] == EXPECTED_BOOTSTRAP_DECISION_ID

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
