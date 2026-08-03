"""Tests for the Platform V1 mainline merge intent binding.

F28: Verifies that the active merge intent binds:
- source_pr: 106 (PR #106, not PR #97)
- The exact v2 Decision content SHA-256 and Command Plan SHA-256
- locked_base_sha, allowed_merge_method, required_workflows, bounded expiry

The v1, v2, v3, and v4 intents are archived verbatim. The v4 archive must be
byte-identical to the original ``active.json`` on the activation base
``fa4f240f7dffff78cdb182ce8655c2e2d7cb241f``.
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
ARCHIVE_PR106_V3_PATH = INTENTS_DIR / "archive" / "pr106_v3.json"
ARCHIVE_PR106_V4_PATH = INTENTS_DIR / "archive" / "pr106_v4.json"

# The v4 intent was the active intent on main at activation base fa4f240f.
V4_ACTIVATION_BASE_SHA = "fa4f240f7dffff78cdb182ce8655c2e2d7cb241f"
V4_EXPECTED_BASE_SHA = "705a0bfd6638d51c688752f154433020225c4e99"

# The v3 PR106 intent was the active intent at commit a96a0ef7, before the v4
# Intent archive and rebind commit.  The pr106_v3 archive must be byte-identical
# to active.json at that commit.
PR106_V3_ACTIVE_COMMIT = "a96a0ef7a5c706316f03401959e12bcf3a9f8c1c"

# The v4 PR106 intent was the active intent at commit 810bfff5, before the v5
# Intent archive and rebind commit.  The pr106_v4 archive must be byte-identical
# to active.json at that commit.
PR106_V4_ACTIVE_COMMIT = "810bfff5446ac2e54e85bc8624a1cf83d241778e"

EXPECTED_V2_DECISION_ID = (
    "decision_20260803_restore_path_a_state_gate_current_main_v2"
)
EXPECTED_V3_DECISION_ID_PR106 = (
    "decision_20260803_restore_path_a_state_gate_current_main_v3"
)
EXPECTED_V4_DECISION_ID_PR106 = (
    "decision_20260803_restore_path_a_state_gate_current_main_v4"
)
EXPECTED_V5_DECISION_ID_PR106 = (
    "decision_20260803_restore_path_a_state_gate_current_main_v7"
)
EXPECTED_V4_DECISION_ID = (
    "decision_20260802_issue100_platform_v1_authority_collector_v4"
)
EXPECTED_V3_DECISION_ID = (
    "decision_20260802_issue99_platform_v1_live_evidence_boundary_v3"
)
EXPECTED_V2_DECISION_ID_PR97 = (
    "decision_20260802_issue98_platform_v1_trust_binding_rework_v2"
)
EXPECTED_V1_DECISION_ID = "decision_20260802_platform_v1_openhands_codex_acp_v1"

EXPECTED_ACTIVE_BASE_SHA = V4_ACTIVATION_BASE_SHA
EXPECTED_ACTIVE_SOURCE_PR = 106


def _load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def _committed_blob(path: str, ref: str = "HEAD") -> bytes:
    return subprocess.check_output(
        ["git", "cat-file", "blob", f"{ref}:{path}"],
        cwd=REPO_ROOT,
    )


# ---------------------------------------------------------------------------
# Active v2 intent (PR #106, restore Path-A State Gate v2)
# ---------------------------------------------------------------------------

class TestActiveMergeIntent:
    def test_active_file_exists(self) -> None:
        assert ACTIVE_PATH.exists(), f"active.json not found at {ACTIVE_PATH}"

    def test_active_binds_source_pr_106(self) -> None:
        data = _load_json(ACTIVE_PATH)
        assert data["source_pr"] == EXPECTED_ACTIVE_SOURCE_PR, (
            "active intent must bind source_pr=106"
        )

    def test_active_does_not_have_source_pr_zero(self) -> None:
        data = _load_json(ACTIVE_PATH)
        assert data["source_pr"] != 0, "active intent must not retain source_pr=0"

    def test_active_binds_locked_base_sha(self) -> None:
        data = _load_json(ACTIVE_PATH)
        assert data["locked_base_sha"] == EXPECTED_ACTIVE_BASE_SHA

    def test_active_binds_merge_method(self) -> None:
        data = _load_json(ACTIVE_PATH)
        assert data["allowed_merge_method"] == "merge"

    def test_active_binds_v5_decision_id(self) -> None:
        data = _load_json(ACTIVE_PATH)
        assert data["decision_identity"]["decision_id"] == EXPECTED_V5_DECISION_ID_PR106

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

    def test_active_decision_content_sha256_matches_committed_blob(self) -> None:
        """The active intent's decision digest must match the committed Decision blob."""
        data = _load_json(ACTIVE_PATH)
        decision_blob = _committed_blob("project_state/decision_packet.md")
        expected = hashlib.sha256(decision_blob).hexdigest()
        assert data["decision_identity"]["decision_content_sha256"] == expected

    def test_active_command_plan_sha256_matches_committed_blob(self) -> None:
        """The active intent's command plan digest must match the committed Plan blob."""
        data = _load_json(ACTIVE_PATH)
        plan_blob = _committed_blob("project_state/gates/command_plan.json")
        expected = hashlib.sha256(plan_blob).hexdigest()
        assert data["command_plan_sha256"] == expected

    def test_active_required_workflows_include_all_four(self) -> None:
        data = _load_json(ACTIVE_PATH)
        workflows = data["required_workflows"]
        assert "CI" in workflows
        assert "Decision Preflight" in workflows
        assert "State Gate (pull_request_target)" in workflows
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
        assert data["locked_base_sha"] == V4_EXPECTED_BASE_SHA


# ---------------------------------------------------------------------------
# Archived v2 intent (trust binding rework)
# ---------------------------------------------------------------------------

class TestArchivedV2Intent:
    def test_archive_v2_file_exists(self) -> None:
        assert ARCHIVE_V2_PATH.exists(), f"pr97_v2.json not found at {ARCHIVE_V2_PATH}"

    def test_archive_v2_binds_v2_decision_id(self) -> None:
        data = _load_json(ARCHIVE_V2_PATH)
        assert data["decision_identity"]["decision_id"] == EXPECTED_V2_DECISION_ID_PR97

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
# Archived v4 intent (platform_v1_authority_collector_v4_pr97)
# ---------------------------------------------------------------------------

class TestArchivedV4Intent:
    def test_archive_v4_file_exists(self) -> None:
        assert ARCHIVE_V4_PATH.exists(), f"pr97_v4.json not found at {ARCHIVE_V4_PATH}"

    def test_archive_v4_binds_v4_decision_id(self) -> None:
        data = _load_json(ARCHIVE_V4_PATH)
        assert data["decision_identity"]["decision_id"] == EXPECTED_V4_DECISION_ID

    def test_archive_v4_preserves_v4_source_pr(self) -> None:
        data = _load_json(ARCHIVE_V4_PATH)
        assert data["source_pr"] == 97

    def test_archive_v4_preserves_v4_locked_base_sha(self) -> None:
        data = _load_json(ARCHIVE_V4_PATH)
        assert data["locked_base_sha"] == V4_EXPECTED_BASE_SHA

    def test_archive_v4_preserves_v4_decision_content_sha256(self) -> None:
        data = _load_json(ARCHIVE_V4_PATH)
        sha = data["decision_identity"]["decision_content_sha256"]
        assert isinstance(sha, str) and len(sha) == 64
        assert all(c in "0123456789abcdef" for c in sha)

    def test_archive_v4_preserves_v4_command_plan_sha256(self) -> None:
        data = _load_json(ARCHIVE_V4_PATH)
        sha = data["command_plan_sha256"]
        assert isinstance(sha, str) and len(sha) == 64
        assert all(c in "0123456789abcdef" for c in sha)

    def test_archive_v4_preserves_v4_required_workflows(self) -> None:
        data = _load_json(ARCHIVE_V4_PATH)
        workflows = data["required_workflows"]
        assert "CI" in workflows
        assert "Decision Preflight" in workflows
        assert "State Gate (pull_request)" in workflows
        assert "State Gate (push)" in workflows

    def test_archive_v4_byte_identical_to_original_main_active_json(self) -> None:
        """The v4 archive must be byte-identical to the active.json on the
        activation base commit fa4f240f."""
        archive_blob = _committed_blob(
            "project_state/mainline_merge_intents/archive/pr97_v4.json"
        )
        original_blob = _committed_blob(
            "project_state/mainline_merge_intents/active.json",
            ref=V4_ACTIVATION_BASE_SHA,
        )
        assert archive_blob == original_blob, (
            "pr97_v4.json archive must be byte-identical to the original "
            "active.json on the activation base"
        )

    def test_archive_v4_sha256_matches_original_main_active_json(self) -> None:
        """The SHA-256 of the v4 archive must match the SHA-256 of the
        original active.json on the activation base."""
        archive_blob = _committed_blob(
            "project_state/mainline_merge_intents/archive/pr97_v4.json"
        )
        original_blob = _committed_blob(
            "project_state/mainline_merge_intents/active.json",
            ref=V4_ACTIVATION_BASE_SHA,
        )
        assert hashlib.sha256(archive_blob).hexdigest() == (
            hashlib.sha256(original_blob).hexdigest()
        )


# ---------------------------------------------------------------------------
# Archived pr106_v3 intent (restore Path-A State Gate v3 for PR #106)
# ---------------------------------------------------------------------------

class TestArchivedPr106V3Intent:
    def test_archive_pr106_v3_file_exists(self) -> None:
        assert ARCHIVE_PR106_V3_PATH.exists(), (
            f"pr106_v3.json not found at {ARCHIVE_PR106_V3_PATH}"
        )

    def test_archive_pr106_v3_binds_v3_decision_id(self) -> None:
        data = _load_json(ARCHIVE_PR106_V3_PATH)
        assert data["decision_identity"]["decision_id"] == EXPECTED_V3_DECISION_ID_PR106

    def test_archive_pr106_v3_preserves_source_pr(self) -> None:
        data = _load_json(ARCHIVE_PR106_V3_PATH)
        assert data["source_pr"] == 106

    def test_archive_pr106_v3_preserves_locked_base_sha(self) -> None:
        data = _load_json(ARCHIVE_PR106_V3_PATH)
        assert data["locked_base_sha"] == EXPECTED_ACTIVE_BASE_SHA

    def test_archive_pr106_v3_preserves_decision_content_sha256(self) -> None:
        data = _load_json(ARCHIVE_PR106_V3_PATH)
        sha = data["decision_identity"]["decision_content_sha256"]
        assert isinstance(sha, str) and len(sha) == 64
        assert all(c in "0123456789abcdef" for c in sha)

    def test_archive_pr106_v3_preserves_command_plan_sha256(self) -> None:
        data = _load_json(ARCHIVE_PR106_V3_PATH)
        sha = data["command_plan_sha256"]
        assert isinstance(sha, str) and len(sha) == 64
        assert all(c in "0123456789abcdef" for c in sha)

    def test_archive_pr106_v3_preserves_required_workflows(self) -> None:
        data = _load_json(ARCHIVE_PR106_V3_PATH)
        workflows = data["required_workflows"]
        assert "CI" in workflows
        assert "Decision Preflight" in workflows
        assert "State Gate (pull_request_target)" in workflows
        assert "State Gate (push)" in workflows

    def test_archive_pr106_v3_byte_identical_to_v3_active(self) -> None:
        """The pr106_v3 archive must be byte-identical to the active.json at
        the commit where v3 was the active intent."""
        archive_blob = _committed_blob(
            "project_state/mainline_merge_intents/archive/pr106_v3.json"
        )
        original_blob = _committed_blob(
            "project_state/mainline_merge_intents/active.json",
            ref=PR106_V3_ACTIVE_COMMIT,
        )
        assert archive_blob == original_blob, (
            "pr106_v3.json archive must be byte-identical to the "
            "active.json at commit " + PR106_V3_ACTIVE_COMMIT
        )

    def test_archive_pr106_v3_sha256_matches_v3_active(self) -> None:
        """The SHA-256 of the pr106_v3 archive must match the SHA-256 of the
        active.json at the v3 active commit."""
        archive_blob = _committed_blob(
            "project_state/mainline_merge_intents/archive/pr106_v3.json"
        )
        original_blob = _committed_blob(
            "project_state/mainline_merge_intents/active.json",
            ref=PR106_V3_ACTIVE_COMMIT,
        )
        assert hashlib.sha256(archive_blob).hexdigest() == (
            hashlib.sha256(original_blob).hexdigest()
        )


# ---------------------------------------------------------------------------
# New active (v4/PR106) differs from pr106_v3 archive
# ---------------------------------------------------------------------------

class TestActiveV4DiffersFromPr106V3Archive:
    def test_active_decision_id_differs_from_pr106_v3(self) -> None:
        active = _load_json(ACTIVE_PATH)
        v3 = _load_json(ARCHIVE_PR106_V3_PATH)
        assert (
            active["decision_identity"]["decision_id"]
            != v3["decision_identity"]["decision_id"]
        )

    def test_active_decision_content_sha256_differs_from_pr106_v3(self) -> None:
        active = _load_json(ACTIVE_PATH)
        v3 = _load_json(ARCHIVE_PR106_V3_PATH)
        assert (
            active["decision_identity"]["decision_content_sha256"]
            != v3["decision_identity"]["decision_content_sha256"]
        )

    def test_active_command_plan_sha256_differs_from_pr106_v3(self) -> None:
        active = _load_json(ACTIVE_PATH)
        v3 = _load_json(ARCHIVE_PR106_V3_PATH)
        assert active["command_plan_sha256"] != v3["command_plan_sha256"]

    def test_active_intent_id_differs_from_pr106_v3(self) -> None:
        active = _load_json(ACTIVE_PATH)
        v3 = _load_json(ARCHIVE_PR106_V3_PATH)
        assert active["intent_id"] != v3["intent_id"]


# ---------------------------------------------------------------------------
# Archived pr106_v4 intent (restore Path-A State Gate v4 for PR #106)
# ---------------------------------------------------------------------------

class TestArchivedPr106V4Intent:
    def test_archive_pr106_v4_file_exists(self) -> None:
        assert ARCHIVE_PR106_V4_PATH.exists(), (
            f"pr106_v4.json not found at {ARCHIVE_PR106_V4_PATH}"
        )

    def test_archive_pr106_v4_binds_v4_decision_id(self) -> None:
        data = _load_json(ARCHIVE_PR106_V4_PATH)
        assert data["decision_identity"]["decision_id"] == EXPECTED_V4_DECISION_ID_PR106

    def test_archive_pr106_v4_preserves_source_pr(self) -> None:
        data = _load_json(ARCHIVE_PR106_V4_PATH)
        assert data["source_pr"] == 106

    def test_archive_pr106_v4_preserves_locked_base_sha(self) -> None:
        data = _load_json(ARCHIVE_PR106_V4_PATH)
        assert data["locked_base_sha"] == EXPECTED_ACTIVE_BASE_SHA

    def test_archive_pr106_v4_preserves_decision_content_sha256(self) -> None:
        data = _load_json(ARCHIVE_PR106_V4_PATH)
        sha = data["decision_identity"]["decision_content_sha256"]
        assert isinstance(sha, str) and len(sha) == 64
        assert all(c in "0123456789abcdef" for c in sha)

    def test_archive_pr106_v4_preserves_command_plan_sha256(self) -> None:
        data = _load_json(ARCHIVE_PR106_V4_PATH)
        sha = data["command_plan_sha256"]
        assert isinstance(sha, str) and len(sha) == 64
        assert all(c in "0123456789abcdef" for c in sha)

    def test_archive_pr106_v4_preserves_required_workflows(self) -> None:
        data = _load_json(ARCHIVE_PR106_V4_PATH)
        workflows = data["required_workflows"]
        assert "CI" in workflows
        assert "Decision Preflight" in workflows
        assert "State Gate (pull_request_target)" in workflows
        assert "State Gate (push)" in workflows

    def test_archive_pr106_v4_byte_identical_to_v4_active(self) -> None:
        """The pr106_v4 archive must be byte-identical to the active.json at
        the commit where v4 was the active intent."""
        archive_blob = _committed_blob(
            "project_state/mainline_merge_intents/archive/pr106_v4.json"
        )
        original_blob = _committed_blob(
            "project_state/mainline_merge_intents/active.json",
            ref=PR106_V4_ACTIVE_COMMIT,
        )
        assert archive_blob == original_blob, (
            "pr106_v4.json archive must be byte-identical to the "
            "active.json at commit " + PR106_V4_ACTIVE_COMMIT
        )

    def test_archive_pr106_v4_sha256_matches_v4_active(self) -> None:
        """The SHA-256 of the pr106_v4 archive must match the SHA-256 of the
        active.json at the v4 active commit."""
        archive_blob = _committed_blob(
            "project_state/mainline_merge_intents/archive/pr106_v4.json"
        )
        original_blob = _committed_blob(
            "project_state/mainline_merge_intents/active.json",
            ref=PR106_V4_ACTIVE_COMMIT,
        )
        assert hashlib.sha256(archive_blob).hexdigest() == (
            hashlib.sha256(original_blob).hexdigest()
        )


# ---------------------------------------------------------------------------
# New active (v5/PR106) differs from pr106_v4 archive
# ---------------------------------------------------------------------------

class TestActiveV5DiffersFromPr106V4Archive:
    def test_active_decision_id_differs_from_pr106_v4(self) -> None:
        active = _load_json(ACTIVE_PATH)
        v4 = _load_json(ARCHIVE_PR106_V4_PATH)
        assert (
            active["decision_identity"]["decision_id"]
            != v4["decision_identity"]["decision_id"]
        )

    def test_active_decision_content_sha256_differs_from_pr106_v4(self) -> None:
        active = _load_json(ACTIVE_PATH)
        v4 = _load_json(ARCHIVE_PR106_V4_PATH)
        assert (
            active["decision_identity"]["decision_content_sha256"]
            != v4["decision_identity"]["decision_content_sha256"]
        )

    def test_active_command_plan_sha256_differs_from_pr106_v4(self) -> None:
        active = _load_json(ACTIVE_PATH)
        v4 = _load_json(ARCHIVE_PR106_V4_PATH)
        assert active["command_plan_sha256"] != v4["command_plan_sha256"]

    def test_active_intent_id_differs_from_pr106_v4(self) -> None:
        active = _load_json(ACTIVE_PATH)
        v4 = _load_json(ARCHIVE_PR106_V4_PATH)
        assert active["intent_id"] != v4["intent_id"]


# ---------------------------------------------------------------------------
# New active (v2/PR106) differs from v4 archive
# ---------------------------------------------------------------------------

class TestActiveV2DiffersFromV4Archive:
    def test_active_decision_id_differs_from_v4(self) -> None:
        active = _load_json(ACTIVE_PATH)
        v4 = _load_json(ARCHIVE_V4_PATH)
        assert (
            active["decision_identity"]["decision_id"]
            != v4["decision_identity"]["decision_id"]
        )

    def test_active_decision_content_sha256_differs_from_v4(self) -> None:
        active = _load_json(ACTIVE_PATH)
        v4 = _load_json(ARCHIVE_V4_PATH)
        assert (
            active["decision_identity"]["decision_content_sha256"]
            != v4["decision_identity"]["decision_content_sha256"]
        )

    def test_active_command_plan_sha256_differs_from_v4(self) -> None:
        active = _load_json(ACTIVE_PATH)
        v4 = _load_json(ARCHIVE_V4_PATH)
        assert active["command_plan_sha256"] != v4["command_plan_sha256"]

    def test_active_intent_id_differs_from_v4(self) -> None:
        active = _load_json(ACTIVE_PATH)
        v4 = _load_json(ARCHIVE_V4_PATH)
        assert active["intent_id"] != v4["intent_id"]

    def test_active_source_pr_differs_from_v4(self) -> None:
        active = _load_json(ACTIVE_PATH)
        v4 = _load_json(ARCHIVE_V4_PATH)
        assert active["source_pr"] != v4["source_pr"]

    def test_active_locked_base_sha_differs_from_v4(self) -> None:
        active = _load_json(ACTIVE_PATH)
        v4 = _load_json(ARCHIVE_V4_PATH)
        assert active["locked_base_sha"] != v4["locked_base_sha"]
