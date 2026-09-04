from __future__ import annotations

import base64
import hashlib
import json
import os
import re
import subprocess
from copy import deepcopy
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import pytest

from reverse_agent.github_remote_verifier import (
    GitHubEvidenceError,
    GitHubRemoteAcceptanceVerifier,
)
from reverse_agent.mainline_landing import (
    CANONICAL_WORKFLOW_POLICY,
    CURRENT_PREMERGE_WORKFLOW_POLICY,
    TRUSTED_PREMERGE_WORKFLOW_PROFILES,
    validate_active_merge_intent,
    _validate_intent,
    canonical_digest,
    emit_mainline_integration_receipt,
    resolve_premerge_workflow_profile,
    validate_premerge_attestation,
    validate_future_merge,
    validate_pr60_recovery,
    owner_landing_content_digest,
    FALSE_NONE_REQUIRED_CONTEXTS,
)


REPO_ROOT = Path(__file__).resolve().parents[1]
NOW = datetime(2026, 7, 28, 8, 0, tzinfo=timezone.utc)


def _git(repo: Path, *args: str) -> str:
    return subprocess.run(
        ["git", *args],
        cwd=repo,
        check=True,
        capture_output=True,
        text=True,
    ).stdout.strip()


class FakeVerifier:
    def __init__(
        self,
        *,
        fail: str = "",
        merged_at: str | None = "2026-07-27T00:00:00Z",
        remote_merge_commit_sha: str | None = None,
        merged: bool = True,
    ) -> None:
        self.fail = fail
        self.merged_at = merged_at
        self.remote_merge_commit_sha = remote_merge_commit_sha
        self.merged = merged

    def verify_pr(self, **kwargs: Any) -> dict[str, Any]:
        if self.fail == "pr":
            return {"verified": False, "reason": self.fail}
        expected_merge = kwargs.get("expected_merge_commit_sha")
        checks_pass = (
            expected_merge is None
            or self.remote_merge_commit_sha is None
            or expected_merge == self.remote_merge_commit_sha
        ) and (
            kwargs.get("require_merged") is None
            or self.merged is kwargs["require_merged"]
        )
        if not checks_pass:
            return {"verified": False, "reason": "pr_mismatch"}
        return {
            "verified": True,
            "reason": self.fail,
            "pr": {
                "merged": self.merged,
                "merged_at": self.merged_at,
                "merge_commit_sha": self.remote_merge_commit_sha
                or expected_merge,
            },
        }

    def verify_workflow_run(self, **kwargs: Any) -> dict[str, Any]:
        bad = self.fail == "workflow" or kwargs["run_id"] <= 0
        return {"verified": not bad, "reason": self.fail, "run": kwargs}

    def verify_issue_comment(self, **_: Any) -> dict[str, Any]:
        return {"verified": self.fail != "comment", "reason": self.fail}

    def verify_ref_file_sha256(self, **_: Any) -> dict[str, Any]:
        return {"verified": self.fail != "ref", "reason": self.fail}


def _future_repo(
    tmp_path: Path,
    *,
    decision_id: str = "decision_20260801_later_mainline_landing_v4",
    intent_decision_id: str | None = None,
    bad_decision: bool = False,
    bad_plan: bool = False,
    plan_decision_id: str | None = None,
    decision_artifact: str | None = None,
    schema_version: int = 1,
    workflow_profile: str | None = None,
    decision_contract_profile: str | None = None,
) -> dict[str, Any]:
    repo = tmp_path / "repo"
    repo.mkdir()
    _git(repo, "init", "-b", "main")
    _git(repo, "config", "user.email", "test@example.com")
    _git(repo, "config", "user.name", "Test")
    (repo / "base.txt").write_text("base\n", encoding="utf-8")
    _git(repo, "add", "base.txt")
    _git(repo, "commit", "-m", "base")
    base = _git(repo, "rev-parse", "HEAD")
    _git(repo, "checkout", "-b", "feature")
    decision_path = repo / "project_state" / "decision_packet.md"
    plan_path = repo / "project_state" / "gates" / "command_plan.json"
    decision_path.parent.mkdir(parents=True)
    plan_path.parent.mkdir(parents=True)
    round_id = "round_20260801_later_mainline_landing_v4"
    if schema_version == 3 and workflow_profile is None:
        workflow_profile = "baseline"
    if schema_version == 3 and decision_contract_profile is None:
        decision_contract_profile = workflow_profile
    contract_block = ""
    if decision_contract_profile is not None:
        contract_block = (
            "```json decision_contract\n"
            + json.dumps(
                {"workflow_profile": decision_contract_profile},
                separators=(",", ":"),
            )
            + "\n```\n"
        )
    decision_text = decision_artifact or (
        "# Decision Packet\n\n"
        "```json decision_meta\n"
        + json.dumps(
            {
                "schema_version": 1,
                "decision_id": decision_id,
                "round_id": round_id,
                "status": "APPROVED",
                "mainline": "engineering_branch",
            },
            separators=(",", ":"),
        )
        + "\n```\n\n"
        + contract_block
    )
    decision_path.write_text(decision_text, encoding="utf-8")
    plan_path.write_text(
        json.dumps(
            {
                "schema_version": 1,
                "decision_id": plan_decision_id or decision_id,
                "round_id": round_id,
                "commands": [],
            },
            separators=(",", ":"),
        )
        + "\n",
        encoding="utf-8",
    )
    _git(repo, "add", "project_state")
    _git(repo, "commit", "-m", "authority")
    decision_digest = hashlib.sha256(
        subprocess.check_output(
            ["git", "show", "HEAD:project_state/decision_packet.md"], cwd=repo
        )
    ).hexdigest()
    plan_digest = hashlib.sha256(
        subprocess.check_output(
            ["git", "show", "HEAD:project_state/gates/command_plan.json"], cwd=repo
        )
    ).hexdigest()
    if schema_version == 1:
        workflow_policy = CANONICAL_WORKFLOW_POLICY
    elif schema_version == 3:
        try:
            workflow_policy = resolve_premerge_workflow_profile(workflow_profile)
        except ValueError:
            workflow_policy = CURRENT_PREMERGE_WORKFLOW_POLICY
    else:
        workflow_policy = CURRENT_PREMERGE_WORKFLOW_POLICY
    intent = {
        "schema_version": schema_version,
        "intent_id": "intent_pr67_v1",
        "repository": "dddd2024/reverse-agent",
        "source_pr": 67,
        "locked_base_sha": base,
        "allowed_merge_method": "merge",
        "decision_identity": {
            "decision_id": intent_decision_id or decision_id,
            "decision_content_sha256": "0" * 64 if bad_decision else decision_digest,
        },
        "command_plan_sha256": "0" * 64 if bad_plan else plan_digest,
        "merge_tree_policy": "equal_to_accepted_head_tree",
        "required_workflows": list(workflow_policy),
        "expires_at": "2026-08-28T00:00:00Z",
    }
    if schema_version == 3:
        intent["workflow_profile"] = workflow_profile
    intent_path = repo / "project_state" / "mainline_merge_intents" / "active.json"
    intent_path.parent.mkdir(parents=True)
    intent_path.write_text(json.dumps(intent, indent=2) + "\n", encoding="utf-8")
    (repo / "feature.txt").write_text("feature\n", encoding="utf-8")
    _git(repo, "add", "project_state/mainline_merge_intents/active.json", "feature.txt")
    _git(repo, "commit", "-m", "intent and implementation")
    head = _git(repo, "rev-parse", "HEAD")
    _git(repo, "checkout", "main")
    _git(repo, "merge", "--no-ff", "feature", "-m", "merge")
    merge = _git(repo, "rev-parse", "HEAD")
    approval_payload = {
        "repository": "dddd2024/reverse-agent",
        "source_pr": 67,
        "locked_base_sha": base,
        "accepted_exact_head_sha": head,
        "allowed_merge_method": "merge",
    }
    observations = []
    for index, (name, (workflow_file, event)) in enumerate(
        workflow_policy.items(), 1
    ):
        observations.append(
            {
                "name": name,
                "run_id": 1000 + index,
                "workflow_file": workflow_file,
                "event": event,
                "run_attempt": 1,
                "head_sha": head,
                "conclusion": "success",
            }
        )
    attestation = {
        "schema_version": schema_version,
        "attestation_id": "attestation_pr67_v1",
        "repository": "dddd2024/reverse-agent",
        "source_pr": 67,
        "locked_base_sha": base,
        "accepted_exact_head_sha": head,
        "allowed_merge_method": "merge",
        "intent_digest": canonical_digest(intent),
        "workflow_observations": observations,
        "human_r2_approval": {
            "approver": "dddd2024",
            "approval_object_id": 12345,
            "approval_payload": approval_payload,
            "approval_content_digest": canonical_digest(approval_payload),
        },
        "authorization_status": "active",
        "expires_at": "2026-08-28T00:00:00Z",
        "superseded_by": None,
        "_remote_comment_id": 12345,
        "_remote_author": "dddd2024",
    }
    if schema_version in {2, 3}:
        attestation["_remote_comment_created_at"] = "2026-07-25T00:00:00Z"
        attestation["_remote_comment_updated_at"] = "2026-07-26T00:00:00Z"
    attestation["content_digest"] = canonical_digest(
        attestation,
        omit=(
            "content_digest",
            "_remote_comment_id",
            "_remote_author",
            "_remote_comment_created_at",
            "_remote_comment_updated_at",
        ),
    )
    return {
        "repo": repo,
        "state_dir": repo / "project_state",
        "base": base,
        "head": head,
        "merge": merge,
        "intent": intent,
        "attestation": attestation,
    }


def _validate(bundle: dict[str, Any], *, verifier: FakeVerifier | None = None) -> dict[str, Any]:
    return validate_future_merge(
        repo_root=bundle["repo"],
        state_dir=bundle["state_dir"],
        attestation=bundle["attestation"],
        verifier=verifier or FakeVerifier(),
        commit_sha=bundle["merge"],
        validation_time=NOW,
    )


def _recommit_intent(bundle: dict[str, Any], intent: dict[str, Any]) -> None:
    """Amend the committed active intent and rebuild the two-parent merge."""

    repo = bundle["repo"]
    _git(repo, "checkout", "feature")
    intent_path = repo / "project_state" / "mainline_merge_intents" / "active.json"
    intent_path.write_text(json.dumps(intent, indent=2) + "\n", encoding="utf-8")
    _git(repo, "add", "project_state/mainline_merge_intents/active.json")
    _git(repo, "commit", "--amend", "--no-edit")
    new_head = _git(repo, "rev-parse", "HEAD")
    tree = _git(repo, "rev-parse", "HEAD^{tree}")
    new_merge = _git(
        repo,
        "commit-tree",
        tree,
        "-p",
        bundle["base"],
        "-p",
        new_head,
        "-m",
        "merge amended intent",
    )
    bundle["head"] = new_head
    bundle["merge"] = new_merge
    bundle["attestation"]["accepted_exact_head_sha"] = new_head


def test_normal_two_parent_merge_passes(tmp_path: Path) -> None:
    result = _validate(_future_repo(tmp_path))
    assert result["gate_status"] == "PASSED", result


def test_later_valid_decision_identity_passes(tmp_path: Path) -> None:
    bundle = _future_repo(
        tmp_path,
        decision_id="decision_20260815_future_exact_head_v7",
    )
    result = _validate(bundle)
    assert result["gate_status"] == "PASSED", result


def test_intent_decision_identity_mismatch_fails(tmp_path: Path) -> None:
    bundle = _future_repo(
        tmp_path,
        intent_decision_id="decision_20260801_other_authority_v1",
    )
    result = _validate(bundle)
    assert any("intent_decision_id" in item for item in result["blocking_reasons"])


def test_direct_push_fails(tmp_path: Path) -> None:
    bundle = _future_repo(tmp_path)
    bundle["merge"] = bundle["head"]
    result = _validate(bundle)
    assert result["gate_status"] == "BLOCKED"
    assert any("merge_structure" in item for item in result["blocking_reasons"])


def test_wrong_accepted_head_fails(tmp_path: Path) -> None:
    bundle = _future_repo(tmp_path)
    bundle["attestation"]["accepted_exact_head_sha"] = "0" * 40
    result = _validate(bundle)
    assert result["gate_status"] == "BLOCKED"
    assert any("second_parent_identity" in item for item in result["blocking_reasons"])


def test_wrong_locked_base_fails(tmp_path: Path) -> None:
    bundle = _future_repo(tmp_path)
    bundle["attestation"]["locked_base_sha"] = "0" * 40
    result = _validate(bundle)
    assert result["gate_status"] == "BLOCKED"
    assert any("first_parent_identity" in item for item in result["blocking_reasons"])


def test_wrong_parent_order_fails(tmp_path: Path) -> None:
    bundle = _future_repo(tmp_path)
    tree = _git(bundle["repo"], "rev-parse", f"{bundle['head']}^{{tree}}")
    bundle["merge"] = _git(
        bundle["repo"],
        "commit-tree",
        tree,
        "-p",
        bundle["head"],
        "-p",
        bundle["base"],
        "-m",
        "reversed parents",
    )
    result = _validate(bundle)
    assert result["gate_status"] == "BLOCKED"
    assert any("first_parent_identity" in item for item in result["blocking_reasons"])
    assert any("second_parent_identity" in item for item in result["blocking_reasons"])


def test_merge_tree_mismatch_fails(tmp_path: Path) -> None:
    bundle = _future_repo(tmp_path)
    (bundle["repo"] / "merge-only.txt").write_text("unexpected\n", encoding="utf-8")
    _git(bundle["repo"], "add", "merge-only.txt")
    _git(bundle["repo"], "commit", "--amend", "--no-edit")
    bundle["merge"] = _git(bundle["repo"], "rev-parse", "HEAD")
    result = _validate(bundle)
    assert result["gate_status"] == "BLOCKED"
    assert any("merge_tree_policy" in item for item in result["blocking_reasons"])


@pytest.mark.parametrize("field", ["authorization_status", "superseded_by", "expires_at"])
def test_stale_or_superseded_attestation_fails(tmp_path: Path, field: str) -> None:
    bundle = _future_repo(tmp_path)
    values = {
        "authorization_status": "expired",
        "superseded_by": "new-attestation",
        "expires_at": "2026-07-01T00:00:00Z",
    }
    bundle["attestation"][field] = values[field]
    result = _validate(bundle)
    assert result["gate_status"] == "BLOCKED"


def test_decision_digest_mismatch_fails(tmp_path: Path) -> None:
    result = _validate(_future_repo(tmp_path, bad_decision=True))
    assert any("intent_decision_digest" in item for item in result["blocking_reasons"])


def test_command_plan_digest_mismatch_fails(tmp_path: Path) -> None:
    result = _validate(_future_repo(tmp_path, bad_plan=True))
    assert any("intent_command_plan_digest" in item for item in result["blocking_reasons"])


def test_command_plan_identity_mismatch_fails_even_with_matching_digest(
    tmp_path: Path,
) -> None:
    result = _validate(
        _future_repo(
            tmp_path,
            plan_decision_id="decision_20260801_other_authority_v1",
        )
    )
    assert any(
        "intent_command_plan_identity" in item for item in result["blocking_reasons"]
    )


@pytest.mark.parametrize(
    "decision_artifact",
    [
        "# Decision Packet\n",
        "```json decision_meta\n{not-json}\n```\n",
        (
            "```json decision_meta\n"
            '{"schema_version":1,"decision_id":"decision_20260801_valid_v1",'
            '"round_id":"round_20260801_valid_v1","status":"APPROVED",'
            '"mainline":"engineering_branch"}\n```\n'
            "```json decision_meta\n"
            '{"schema_version":1,"decision_id":"decision_20260801_other_v1",'
            '"round_id":"round_20260801_other_v1","status":"APPROVED",'
            '"mainline":"engineering_branch"}\n```\n'
        ),
    ],
)
def test_missing_malformed_or_multiple_decision_metadata_fails_closed(
    tmp_path: Path,
    decision_artifact: str,
) -> None:
    result = _validate(
        _future_repo(tmp_path, decision_artifact=decision_artifact)
    )
    assert result["gate_status"] == "BLOCKED"
    assert result["blocking_reasons"][0].startswith("invalid_merge_evidence:")


def test_wrong_workflow_event_fails(tmp_path: Path) -> None:
    bundle = _future_repo(tmp_path)
    bundle["attestation"]["workflow_observations"][3]["event"] = "pull_request"
    result = _validate(bundle)
    assert result["gate_status"] == "BLOCKED"
    assert any("remote_workflow:State Gate (push)" in item for item in result["blocking_reasons"])


def test_duplicate_run_id_fails(tmp_path: Path) -> None:
    bundle = _future_repo(tmp_path)
    bundle["attestation"]["workflow_observations"][1]["run_id"] = bundle[
        "attestation"
    ]["workflow_observations"][0]["run_id"]
    result = _validate(bundle)
    assert any("workflow_run_uniqueness" in item for item in result["blocking_reasons"])


def test_remote_api_failure_fails_closed(tmp_path: Path) -> None:
    result = _validate(_future_repo(tmp_path), verifier=FakeVerifier(fail="workflow"))
    assert result["gate_status"] == "BLOCKED"
    assert any("remote_workflow:" in item for item in result["blocking_reasons"])


@pytest.mark.parametrize("historical_failure", ["comment", "ref"])
def test_future_merge_does_not_consult_pr60_historical_remote_evidence(
    tmp_path: Path,
    historical_failure: str,
) -> None:
    result = _validate(
        _future_repo(tmp_path),
        verifier=FakeVerifier(fail=historical_failure),
    )
    assert result["gate_status"] == "PASSED", result


def test_pr_binding_failure_fails_closed(tmp_path: Path) -> None:
    result = _validate(_future_repo(tmp_path), verifier=FakeVerifier(fail="pr"))
    assert any("remote_pr_binding" in item for item in result["blocking_reasons"])


def test_unauthorized_approval_author_fails(tmp_path: Path) -> None:
    bundle = _future_repo(tmp_path)
    bundle["attestation"]["_remote_author"] = "attacker"
    result = _validate(bundle)
    assert any("approval_remote_identity" in item for item in result["blocking_reasons"])


def test_approval_payload_digest_mismatch_fails(tmp_path: Path) -> None:
    bundle = _future_repo(tmp_path)
    bundle["attestation"]["human_r2_approval"]["approval_content_digest"] = (
        "sha256:" + "0" * 64
    )
    result = _validate(bundle)
    assert any("approval_content_digest" in item for item in result["blocking_reasons"])


def test_attestation_digest_mismatch_fails(tmp_path: Path) -> None:
    bundle = _future_repo(tmp_path)
    bundle["attestation"]["content_digest"] = "sha256:" + "0" * 64
    result = _validate(bundle)
    assert any("attestation_content_digest" in item for item in result["blocking_reasons"])


def test_unknown_attestation_field_fails(tmp_path: Path) -> None:
    bundle = _future_repo(tmp_path)
    bundle["attestation"]["untrusted_override"] = True
    bundle["attestation"]["content_digest"] = canonical_digest(
        bundle["attestation"],
        omit=(
            "content_digest",
            "_remote_comment_id",
            "_remote_author",
            "_remote_comment_created_at",
            "_remote_comment_updated_at",
        ),
    )
    result = _validate(bundle)
    assert any("attestation_fields" in item for item in result["blocking_reasons"])


def test_post_merge_receipt_is_output_only(tmp_path: Path) -> None:
    bundle = _future_repo(tmp_path)
    before = _git(bundle["repo"], "rev-parse", "HEAD")
    validation = _validate(bundle)
    receipt = emit_mainline_integration_receipt(validation, emitted_at=NOW)
    after = _git(bundle["repo"], "rev-parse", "HEAD")
    assert receipt["receipt_status"] == "EMITTED"
    assert before == after


def test_exact_pr60_recovery_passes_with_trusted_fixture() -> None:
    result = validate_pr60_recovery(
        repo_root=REPO_ROOT,
        state_dir=REPO_ROOT / "project_state",
        verifier=FakeVerifier(),
    )
    assert result["gate_status"] == "PASSED"
    assert result["merge_commit_sha"] == "68026521710c50fa9a70f3851472941605d9ead1"


@pytest.mark.parametrize("failure", ["pr", "workflow", "comment", "ref"])
def test_pr60_recovery_remote_failures_fail_closed(failure: str) -> None:
    result = validate_pr60_recovery(
        repo_root=REPO_ROOT,
        state_dir=REPO_ROOT / "project_state",
        verifier=FakeVerifier(fail=failure),
    )
    assert result["gate_status"] == "BLOCKED"


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("source_pr", 61),
        ("locked_base_sha", "0" * 40),
        ("accepted_head_sha", "1" * 40),
        ("merge_commit_sha", "2" * 40),
    ],
)
def test_pr60_recovery_record_cannot_authorize_other_identity(
    tmp_path: Path,
    field: str,
    value: Any,
) -> None:
    state_dir = tmp_path / "project_state"
    target = state_dir / "mainline_recoveries"
    target.mkdir(parents=True)
    payload = json.loads(
        (REPO_ROOT / "project_state/mainline_recoveries/pr60.json").read_text(
            encoding="utf-8"
        )
    )
    payload[field] = value
    (target / "pr60.json").write_text(json.dumps(payload), encoding="utf-8")
    result = validate_pr60_recovery(
        repo_root=REPO_ROOT,
        state_dir=state_dir,
        verifier=FakeVerifier(),
    )
    assert result["gate_status"] == "BLOCKED"


def test_pr60_recovery_rejects_unknown_field(tmp_path: Path) -> None:
    state_dir = tmp_path / "project_state"
    target = state_dir / "mainline_recoveries"
    target.mkdir(parents=True)
    payload = json.loads(
        (REPO_ROOT / "project_state/mainline_recoveries/pr60.json").read_text(
            encoding="utf-8"
        )
    )
    payload["wildcard_bypass"] = True
    (target / "pr60.json").write_text(json.dumps(payload), encoding="utf-8")
    result = validate_pr60_recovery(
        repo_root=REPO_ROOT,
        state_dir=state_dir,
        verifier=FakeVerifier(),
    )
    assert any("recovery_fields" in item for item in result["blocking_reasons"])


def test_state_gate_routes_branch_and_main_lifecycles() -> None:
    text = (REPO_ROOT / ".github/workflows/state-gate.yml").read_text(
        encoding="utf-8"
    )
    assert "github.ref != 'refs/heads/main'" in text
    assert "integration-baseline --state-dir project_state" in text
    assert "pr60-historical-recovery --state-dir project_state" not in text
    assert "mainline-merge-validation --state-dir project_state" in text
    assert "emit-mainline-integration-receipt" in text
    project_gate = (REPO_ROOT / "reverse_agent/project_gate.py").read_text(
        encoding="utf-8"
    )
    assert '"pr60-historical-recovery"' in project_gate


def _committed_blob(path: str) -> bytes:
    return subprocess.check_output(
        ["git", "cat-file", "blob", f"HEAD:{path}"],
        cwd=REPO_ROOT,
    )


def _committed_decision_requires_active_merge_intent() -> bool:
    """Only landing Decisions bind the global active merge-intent artifact."""

    decision_blob = _committed_blob("project_state/decision_packet.md")
    contract_matches = re.findall(
        rb"```json decision_contract\r?\n(.*?)\r?\n```",
        decision_blob,
        re.DOTALL,
    )
    assert len(contract_matches) == 1
    contract = json.loads(contract_matches[0])
    return contract.get("mainline_merge_intent_required", True) is not False


def _committed_active_intent_binds_current_decision() -> bool:
    """True once the post-publication binding commit lands the active intent.

    Issue #259 v3 defers the exact GitHub-assigned Draft PR number binding to a
    single post-publication commit; before that commit the active intent still
    preserves the previous landing's schema-v1 four-run binding.
    """

    intent = json.loads(
        _committed_blob("project_state/mainline_merge_intents/active.json")
    )
    decision_blob = _committed_blob("project_state/decision_packet.md")
    decision_matches = re.findall(
        rb"```json decision_meta\r?\n(.*?)\r?\n```",
        decision_blob,
        re.DOTALL,
    )
    assert len(decision_matches) == 1
    decision = json.loads(decision_matches[0])
    identity = intent.get("decision_identity", {})
    return identity.get("decision_id") == decision.get("decision_id")


def test_committed_pr67_archived_intent_preserves_exact_v5_authority() -> None:
    """The archived PR67 intent must preserve its historical v5 binding verbatim."""
    intent = json.loads(
        _committed_blob(
            "project_state/mainline_merge_intents/archive/pr67_v5.json"
        )
    )
    assert intent["intent_id"] == "mainline_merge_intent_pr67_v5"
    assert intent["source_pr"] == 67
    assert intent["locked_base_sha"] == "68026521710c50fa9a70f3851472941605d9ead1"
    assert (
        intent["decision_identity"]["decision_id"]
        == "decision_20260729_pr67_final_intent_rebind_v5"
    )
    assert (
        intent["decision_identity"]["decision_content_sha256"]
        == "8688d024d22f192841130bf2d3cb78f9eeb8084af41b2996802f705dc1f3b8c0"
    )
    assert (
        intent["command_plan_sha256"]
        == "b15e68f720ecb4b6325a03249b2824204ec8aac92ba78db4878e28fd40d5f821"
    )
    assert intent["merge_tree_policy"] == "equal_to_accepted_head_tree"
    assert intent["required_workflows"] == list(CANONICAL_WORKFLOW_POLICY)
    assert intent["expires_at"] == "2026-08-19T23:59:59Z"


def test_committed_pr93_archived_intent_preserves_exact_v10_authority() -> None:
    """The archived PR93 v10 intent must preserve its historical binding verbatim."""
    intent = json.loads(
        _committed_blob(
            "project_state/mainline_merge_intents/archive/pr93_v10.json"
        )
    )
    assert intent["intent_id"] == "mainline_merge_intent_pr93_v1"
    assert intent["source_pr"] == 93
    assert intent["locked_base_sha"] == "16526801bda2a816fc707342f903c1ad037de9bd"
    assert (
        intent["decision_identity"]["decision_id"]
        == "decision_20260802_issue95_pr93_merge_readiness_closure_v10"
    )
    assert (
        intent["decision_identity"]["decision_content_sha256"]
        == "4e6f283feb6c0fabde64b7e5086be992acfb2c250b04f354d702007b9c56c954"
    )
    assert (
        intent["command_plan_sha256"]
        == "6e2cdebfd8e2bd900fad6ec0ad0ba6051bde1c91190d0eee83ecc25af8283a60"
    )
    assert intent["merge_tree_policy"] == "equal_to_accepted_head_tree"
    assert intent["required_workflows"] == list(CANONICAL_WORKFLOW_POLICY)
    assert intent["expires_at"] == "2026-08-09T23:59:59Z"


@pytest.mark.skipif(
    not _committed_decision_requires_active_merge_intent(),
    reason="engineering Decision does not activate a mainline merge intent",
)
def test_committed_active_intent_binds_exact_current_authority() -> None:
    """The active merge intent must bind the current Decision and command plan."""
    intent = json.loads(
        _committed_blob("project_state/mainline_merge_intents/active.json")
    )
    decision_blob = _committed_blob("project_state/decision_packet.md")
    plan_blob = _committed_blob("project_state/gates/command_plan.json")
    decision_matches = re.findall(
        rb"```json decision_meta\r?\n(.*?)\r?\n```",
        decision_blob,
        re.DOTALL,
    )
    assert len(decision_matches) == 1
    decision = json.loads(decision_matches[0])
    plan = json.loads(plan_blob)

    if not _committed_active_intent_binds_current_decision():
        contract_matches = re.findall(
            rb"```json decision_contract\r?\n(.*?)\r?\n```",
            decision_blob,
            re.DOTALL,
        )
        assert len(contract_matches) == 1
        contract = json.loads(contract_matches[0])
        assert (
            contract.get("active_pr_binding_mode")
            == "post_draft_pr_exact_remote_number"
        )
        assert (
            contract.get("issue_number_must_not_substitute_for_pr_number") is True
        )
        assert intent["schema_version"] in {1, 2, 3}
        assert (
            intent["decision_identity"]["decision_id"] != decision["decision_id"]
        )
        assert intent["source_pr"] > 0
        assert intent["source_pr"] != contract.get("source_issue")
        return

    assert (
        intent["decision_identity"]["decision_id"]
        == decision["decision_id"]
    )
    assert intent["decision_identity"]["decision_content_sha256"] == hashlib.sha256(
        decision_blob
    ).hexdigest()
    assert intent["command_plan_sha256"] == hashlib.sha256(plan_blob).hexdigest()
    assert (plan["decision_id"], plan["round_id"]) == (
        decision["decision_id"],
        decision["round_id"],
    )

    checks = _validate_intent(
        intent,
        repo_root=REPO_ROOT,
        accepted_head="HEAD",
        source_pr=intent["source_pr"],
        locked_base=intent["locked_base_sha"],
        now=NOW,
    )
    assert all(check["status"] == "PASS" for check in checks), checks


@pytest.mark.parametrize(
    ("field", "stale_value", "expected_failure"),
    [
        (
            "decision_id",
            "decision_20260728_mainline_landing_semantic_rework_v3",
            "intent_decision_id",
        ),
        (
            "decision_content_sha256",
            "242598ee4bd180cc3514460f7a53de1df0e8651b3732d6a460875ef597d4d152",
            "intent_decision_digest",
        ),
        (
            "command_plan_sha256",
            "b461f01aa0e44f844f8f6e061c6ce6cfb5b9930c9e6ff1d2ef886e0364d10a67",
            "intent_command_plan_digest",
        ),
    ],
)
def test_committed_active_intent_rejects_stale_authority(
    field: str,
    stale_value: str,
    expected_failure: str,
) -> None:
    """The active intent must reject any stale authority values."""
    intent = json.loads(
        _committed_blob("project_state/mainline_merge_intents/active.json")
    )
    if field == "command_plan_sha256":
        intent[field] = stale_value
    else:
        intent["decision_identity"][field] = stale_value
    checks = _validate_intent(
        intent,
        repo_root=REPO_ROOT,
        accepted_head="HEAD",
        source_pr=intent["source_pr"],
        locked_base=intent["locked_base_sha"],
        now=NOW,
    )
    observed = {check["name"]: check["status"] for check in checks}
    assert observed[expected_failure] == "FAIL"


@pytest.mark.skipif(
    not _committed_decision_requires_active_merge_intent(),
    reason="engineering Decision does not activate a mainline merge intent",
)
def test_committed_active_intent_rejects_issue_number_substitution() -> None:
    """The Issue number must never substitute for the exact GitHub PR number."""
    intent = json.loads(
        _committed_blob("project_state/mainline_merge_intents/active.json")
    )
    decision_blob = _committed_blob("project_state/decision_packet.md")
    contract_matches = re.findall(
        rb"```json decision_contract\r?\n(.*?)\r?\n```",
        decision_blob,
        re.DOTALL,
    )
    assert len(contract_matches) == 1
    contract = json.loads(contract_matches[0])
    issue_number = int(contract["source_issue"])
    assert intent["source_pr"] > 0
    assert intent["source_pr"] != issue_number

    if not _committed_active_intent_binds_current_decision():
        pytest.skip("exact PR number binding commit not landed yet")

    substituted = dict(intent)
    substituted["source_pr"] = issue_number
    checks = _validate_intent(
        substituted,
        repo_root=REPO_ROOT,
        accepted_head="HEAD",
        source_pr=intent["source_pr"],
        locked_base=intent["locked_base_sha"],
        now=NOW,
    )
    observed = {check["name"]: check["status"] for check in checks}
    assert observed["intent_source_pr"] == "FAIL", checks


def test_committed_pr257_archived_intent_preserves_exact_v1_authority() -> None:
    """The archived PR257 v1 intent must preserve its four-run binding verbatim."""
    intent = json.loads(
        _committed_blob(
            "project_state/mainline_merge_intents/archive/pr257_v1.json"
        )
    )
    assert intent["schema_version"] == 1
    assert intent["intent_id"] == "pr257_issue250_platform_v2_landing_v1"
    assert intent["source_pr"] == 257
    assert intent["locked_base_sha"] == "706991ad0cb826d7c963a8ddfb7e770e97cdf60b"
    assert (
        intent["decision_identity"]["decision_id"]
        == "decision_20260819_issue250_platform_v2_landing_r2_v9"
    )
    assert intent["required_workflows"] == list(CANONICAL_WORKFLOW_POLICY)
    assert intent["expires_at"] == "2026-08-20T23:59:59Z"


def test_future_replacement_decision_without_matching_intent_fails(
    tmp_path: Path,
) -> None:
    bundle = _future_repo(
        tmp_path,
        decision_id="decision_20260815_future_exact_head_v7",
        intent_decision_id="decision_20260729_pr67_final_intent_rebind_v5",
    )
    result = _validate(bundle)
    assert result["gate_status"] == "BLOCKED"
    assert any("intent_decision_id" in item for item in result["blocking_reasons"])


@pytest.mark.skipif(
    not _committed_decision_requires_active_merge_intent(),
    reason="engineering Decision does not activate a mainline merge intent",
)
def test_production_pre_merge_simulation(tmp_path: Path) -> None:
    repo = tmp_path / "simulation"
    subprocess.run(
        ["git", "clone", "--no-hardlinks", str(REPO_ROOT), str(repo)],
        check=True,
        capture_output=True,
        text=True,
    )
    _git(repo, "config", "user.email", "simulation@example.com")
    _git(repo, "config", "user.name", "Simulation")
    head = _git(repo, "rev-parse", "HEAD")
    intent = json.loads(
        subprocess.check_output(
            [
                "git",
                "cat-file",
                "blob",
                f"{head}:project_state/mainline_merge_intents/active.json",
            ],
            cwd=repo,
        )
    )
    base = intent["locked_base_sha"]
    source_pr = intent["source_pr"]
    tree = _git(repo, "rev-parse", f"{head}^{{tree}}")
    merge = _git(
        repo,
        "commit-tree",
        tree,
        "-p",
        base,
        "-p",
        head,
        "-m",
        "temporary production pre-merge simulation",
    )
    approval_payload = {
        "repository": "dddd2024/reverse-agent",
        "source_pr": source_pr,
        "locked_base_sha": base,
        "accepted_exact_head_sha": head,
        "allowed_merge_method": "merge",
    }
    intent_schema_version = int(intent.get("schema_version") or 1)
    if intent_schema_version == 1:
        sim_workflow_policy = CANONICAL_WORKFLOW_POLICY
    elif intent_schema_version == 3:
        sim_workflow_policy = resolve_premerge_workflow_profile(
            intent.get("workflow_profile")
        )
    else:
        sim_workflow_policy = CURRENT_PREMERGE_WORKFLOW_POLICY
    observations = [
        {
            "name": name,
            "run_id": 7100 + index,
            "workflow_file": workflow_file,
            "event": event,
            "run_attempt": 1,
            "head_sha": head,
            "conclusion": "success",
        }
        for index, (name, (workflow_file, event)) in enumerate(
            sim_workflow_policy.items(),
            1,
        )
    ]
    attestation = {
        "schema_version": intent_schema_version,
        "attestation_id": "issue71_local_simulation_only",
        "repository": "dddd2024/reverse-agent",
        "source_pr": source_pr,
        "locked_base_sha": base,
        "accepted_exact_head_sha": head,
        "allowed_merge_method": "merge",
        "intent_digest": canonical_digest(intent),
        "workflow_observations": observations,
        "human_r2_approval": {
            "approver": "dddd2024",
            "approval_object_id": 71001,
            "approval_payload": approval_payload,
            "approval_content_digest": canonical_digest(approval_payload),
        },
        "authorization_status": "active",
        "expires_at": intent["expires_at"],
        "superseded_by": None,
        "_remote_comment_id": 71001,
        "_remote_author": "dddd2024",
    }
    if intent_schema_version in {2, 3}:
        attestation["_remote_comment_created_at"] = "2026-07-25T00:00:00Z"
        attestation["_remote_comment_updated_at"] = "2026-07-26T00:00:00Z"
    attestation["content_digest"] = canonical_digest(
        attestation,
        omit=(
            "content_digest",
            "_remote_comment_id",
            "_remote_author",
            "_remote_comment_created_at",
            "_remote_comment_updated_at",
        ),
    )
    result = validate_future_merge(
        repo_root=repo,
        state_dir=repo / "project_state",
        attestation=attestation,
        verifier=FakeVerifier(),
        commit_sha=merge,
        validation_time=NOW,
    )
    intent_checks = [
        check for check in result["checks"] if check["name"].startswith("intent_")
    ]
    if not _committed_active_intent_binds_current_decision():
        assert result["gate_status"] == "BLOCKED", result
        assert intent_checks
        assert any(
            check["status"] == "FAIL" and check["name"] == "intent_decision_id"
            for check in intent_checks
        ), intent_checks
        return
    assert result["gate_status"] == "PASSED", result
    assert intent_checks
    assert all(check["status"] == "PASS" for check in intent_checks), intent_checks


def test_state_gate_permissions_are_read_only_and_complete() -> None:
    text = (REPO_ROOT / ".github/workflows/state-gate.yml").read_text(
        encoding="utf-8"
    )
    for permission in (
        "contents: read",
        "actions: read",
        "pull-requests: read",
        "issues: read",
    ):
        assert permission in text
    assert "write" not in text.split("jobs:", 1)[0]


def test_production_verifier_requires_token(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("GITHUB_REPOSITORY", "dddd2024/reverse-agent")
    monkeypatch.delenv("GITHUB_TOKEN", raising=False)
    monkeypatch.delenv("GH_TOKEN", raising=False)
    with pytest.raises(GitHubEvidenceError, match="missing_github_token"):
        GitHubRemoteAcceptanceVerifier.from_env()


def test_production_verifier_rejects_wrong_workflow_identity() -> None:
    verifier = GitHubRemoteAcceptanceVerifier(
        repository="dddd2024/reverse-agent",
        token="test",
    )
    verifier._request_json = lambda _path: {  # type: ignore[method-assign]
        "repository": {"full_name": "dddd2024/reverse-agent"},
        "path": ".github/workflows/other.yml",
        "event": "pull_request",
        "head_sha": "a" * 40,
        "run_attempt": 1,
        "status": "completed",
        "conclusion": "success",
    }
    result = verifier.verify_workflow_run(
        run_id=1,
        expected_head_sha="a" * 40,
        expected_workflow_file=".github/workflows/ci.yml",
        expected_event="pull_request",
        expected_run_attempt=1,
    )
    assert result["verified"] is False


def test_load_merge_attestation_overwrites_all_runtime_comment_metadata() -> None:
    verifier = GitHubRemoteAcceptanceVerifier(
        repository="dddd2024/reverse-agent",
        token="test",
    )
    verifier._request_json = lambda _path: [  # type: ignore[method-assign]
        {
            "id": 71002,
            "user": {"login": "dddd2024"},
            "created_at": "2026-07-25T00:00:00Z",
            "updated_at": "2026-07-26T00:00:00Z",
            "body": (
                "MAINLINE_MERGE_APPROVAL_ATTESTATION\n"
                "```json mainline_merge_approval_attestation\n"
                + json.dumps(
                    {
                        "schema_version": 2,
                        "source_pr": 67,
                        "accepted_exact_head_sha": "a" * 40,
                        "authorization_status": "active",
                        "_remote_comment_id": 1,
                        "_remote_author": "forged",
                        "_remote_comment_created_at": "forged-created",
                        "_remote_comment_updated_at": "forged-updated",
                    }
                )
                + "\n```"
            ),
        }
    ]  # type: ignore[method-assign]
    payload = verifier.load_merge_attestation(
        pr_number=67,
        expected_head_sha="a" * 40,
    )
    assert payload["_remote_comment_id"] == 71002
    assert payload["_remote_author"] == "dddd2024"
    assert payload["_remote_comment_created_at"] == "2026-07-25T00:00:00Z"
    assert payload["_remote_comment_updated_at"] == "2026-07-26T00:00:00Z"


def _verify_contents_payload(
    payload: dict[str, object],
    *,
    expected_content: bytes = b"github contents api fixture",
    expected_sha256: str | None = None,
) -> dict[str, object]:
    verifier = GitHubRemoteAcceptanceVerifier(
        repository="dddd2024/reverse-agent",
        token="test",
    )
    verifier._request_json = lambda _path: payload  # type: ignore[method-assign]
    return verifier.verify_ref_file_sha256(
        ref="a" * 40,
        path="project_state/example.json",
        expected_sha256=expected_sha256
        or hashlib.sha256(expected_content).hexdigest(),
    )


@pytest.fixture
def github_contents_base64_payload() -> dict[str, object]:
    content = base64.b64encode(b"github contents api fixture").decode("ascii")
    return {
        "type": "file",
        "encoding": "base64",
        "content": content,
    }


@pytest.mark.parametrize("separator", ["\n", "\r\n", " ", "\t"])
def test_production_verifier_accepts_github_base64_formatting_whitespace(
    github_contents_base64_payload: dict[str, object],
    separator: str,
) -> None:
    raw_content = github_contents_base64_payload["content"]
    assert isinstance(raw_content, str)
    github_contents_base64_payload["content"] = separator.join(
        raw_content[index : index + 4]
        for index in range(0, len(raw_content), 4)
    )
    result = _verify_contents_payload(github_contents_base64_payload)
    assert result["verified"] is True


def test_production_verifier_accepts_unwrapped_base64(
    github_contents_base64_payload: dict[str, object],
) -> None:
    result = _verify_contents_payload(github_contents_base64_payload)
    assert result["verified"] is True


@pytest.mark.parametrize("content", ["YWJj*", "YWJj=", "YWJj===", "YWJ"])
def test_production_verifier_rejects_invalid_base64_content(content: str) -> None:
    result = _verify_contents_payload({"encoding": "base64", "content": content})
    assert result == {"verified": False, "reason": "invalid_base64_content"}


@pytest.mark.parametrize("separator", ["\v", "\f", "\u00a0"])
def test_production_verifier_rejects_non_ascii_formatting_whitespace(
    separator: str,
) -> None:
    result = _verify_contents_payload(
        {"encoding": "base64", "content": f"Z2l0{separator}aHVi"}
    )
    assert result == {"verified": False, "reason": "invalid_base64_content"}


# ---------------------------------------------------------------------------
# Issue #259 regression tests: three-run current pre-merge policy vs four-run historical
# ---------------------------------------------------------------------------


def test_v2_three_run_happy_path_passes(tmp_path: Path) -> None:
    bundle = _future_repo(tmp_path, schema_version=2)
    result = _validate(bundle)
    assert result["gate_status"] == "PASSED", result


def test_v2_missing_ci_blocks(tmp_path: Path) -> None:
    bundle = _future_repo(tmp_path, schema_version=2)
    bundle["attestation"]["workflow_observations"] = bundle[
        "attestation"
    ]["workflow_observations"][1:]
    result = _validate(bundle)
    assert result["gate_status"] == "BLOCKED"
    assert any("workflow_names" in item for item in result["blocking_reasons"])
    assert any("CI" in item for item in result["blocking_reasons"])


def test_v2_missing_decision_preflight_blocks(tmp_path: Path) -> None:
    bundle = _future_repo(tmp_path, schema_version=2)
    bundle["attestation"]["workflow_observations"] = (
        [bundle["attestation"]["workflow_observations"][0]]
        + bundle["attestation"]["workflow_observations"][2:]
    )
    result = _validate(bundle)
    assert result["gate_status"] == "BLOCKED"
    assert any("workflow_names" in item for item in result["blocking_reasons"])
    assert any("Decision Preflight" in item for item in result["blocking_reasons"])


def test_v2_missing_state_gate_pull_request_blocks(tmp_path: Path) -> None:
    bundle = _future_repo(tmp_path, schema_version=2)
    bundle["attestation"]["workflow_observations"] = bundle[
        "attestation"
    ]["workflow_observations"][:2]
    result = _validate(bundle)
    assert result["gate_status"] == "BLOCKED"
    assert any("workflow_names" in item for item in result["blocking_reasons"])
    assert any("State Gate (pull_request)" in item for item in result["blocking_reasons"])


def test_v2_wrong_head_sha_blocks(tmp_path: Path) -> None:
    bundle = _future_repo(tmp_path, schema_version=2)
    bundle["attestation"]["workflow_observations"][0]["head_sha"] = "0" * 40
    result = _validate(bundle)
    assert result["gate_status"] == "BLOCKED"
    assert any("remote_workflow:CI" in item for item in result["blocking_reasons"])


def test_v2_wrong_workflow_event_blocks(tmp_path: Path) -> None:
    bundle = _future_repo(tmp_path, schema_version=2)
    bundle["attestation"]["workflow_observations"][0]["event"] = "push"
    result = _validate(bundle)
    assert result["gate_status"] == "BLOCKED"
    assert any("remote_workflow:CI" in item for item in result["blocking_reasons"])


def test_v2_workflow_failure_blocks(tmp_path: Path) -> None:
    bundle = _future_repo(tmp_path, schema_version=2)
    bundle["attestation"]["workflow_observations"][1]["conclusion"] = "failure"
    result = _validate(bundle)
    assert result["gate_status"] == "BLOCKED"
    assert any("remote_workflow:Decision Preflight" in item for item in result["blocking_reasons"])


def test_v2_duplicate_run_id_blocks(tmp_path: Path) -> None:
    bundle = _future_repo(tmp_path, schema_version=2)
    bundle["attestation"]["workflow_observations"][1]["run_id"] = bundle[
        "attestation"
    ]["workflow_observations"][0]["run_id"]
    result = _validate(bundle)
    assert result["gate_status"] == "BLOCKED"
    assert any("workflow_run_uniqueness" in item for item in result["blocking_reasons"])


def test_v2_push_state_gate_cannot_be_pre_merge_evidence(tmp_path: Path) -> None:
    bundle = _future_repo(tmp_path, schema_version=2)
    for obs in bundle["attestation"]["workflow_observations"]:
        obs["name"] = "State Gate (push)"
        obs["event"] = "push"
    result = _validate(bundle)
    assert result["gate_status"] == "BLOCKED"
    assert any("workflow_names" in item for item in result["blocking_reasons"])


def test_v2_current_policy_does_not_require_state_gate_push(tmp_path: Path) -> None:
    bundle = _future_repo(tmp_path, schema_version=2)
    assert bundle["intent"]["required_workflows"] == list(CURRENT_PREMERGE_WORKFLOW_POLICY)
    assert "State Gate (push)" not in bundle["intent"]["required_workflows"]
    assert len(bundle["attestation"]["workflow_observations"]) == 3
    assert all(
        "State Gate (push)" not in obs.get("name", "")
        for obs in bundle["attestation"]["workflow_observations"]
    )
    result = _validate(bundle)
    assert result["gate_status"] == "PASSED", result


def _refresh_attestation_digest(bundle: dict[str, Any]) -> None:
    bundle["attestation"]["content_digest"] = canonical_digest(
        bundle["attestation"],
        omit=(
            "content_digest",
            "_remote_comment_id",
            "_remote_author",
            "_remote_comment_created_at",
            "_remote_comment_updated_at",
        ),
    )


def test_v2_requires_exact_merged_remote_pr_and_merge_commit(tmp_path: Path) -> None:
    bundle = _future_repo(tmp_path, schema_version=2)
    result = _validate(
        bundle,
        verifier=FakeVerifier(remote_merge_commit_sha="0" * 40),
    )
    assert result["gate_status"] == "BLOCKED"
    assert any("remote_pr_binding" in item for item in result["blocking_reasons"])


def test_v2_remote_merged_at_is_authoritative_over_local_future_time(
    tmp_path: Path,
) -> None:
    bundle = _future_repo(tmp_path, schema_version=2)
    result = _validate(
        bundle,
        verifier=FakeVerifier(merged_at="2026-07-27T00:00:00Z"),
    )
    assert result["gate_status"] == "PASSED", result


def test_v2_precreated_comment_updated_after_merge_blocks(tmp_path: Path) -> None:
    bundle = _future_repo(tmp_path, schema_version=2)
    bundle["attestation"]["_remote_comment_updated_at"] = "2026-07-27T00:00:00Z"
    _refresh_attestation_digest(bundle)
    result = _validate(bundle)
    assert result["gate_status"] == "BLOCKED"
    assert any(
        "attestation_updated_before_merge" in item
        for item in result["blocking_reasons"]
    )


def test_v2_comment_created_after_updated_blocks(tmp_path: Path) -> None:
    bundle = _future_repo(tmp_path, schema_version=2)
    bundle["attestation"]["_remote_comment_created_at"] = "2026-07-26T00:00:00Z"
    bundle["attestation"]["_remote_comment_updated_at"] = "2026-07-25T00:00:00Z"
    _refresh_attestation_digest(bundle)
    result = _validate(bundle)
    assert result["gate_status"] == "BLOCKED"
    assert any("attestation_comment_order" in item for item in result["blocking_reasons"])


@pytest.mark.parametrize(
    ("field", "value", "reason"),
    [
        ("_remote_comment_created_at", "2026-07-27T00:00:00Z", "created"),
        ("_remote_comment_created_at", "2026-07-28T00:00:00Z", "created"),
        ("_remote_comment_updated_at", "2026-07-27T00:00:00Z", "updated"),
        ("_remote_comment_updated_at", "2026-07-28T00:00:00Z", "updated"),
    ],
)
def test_v2_comment_timestamps_equal_or_after_merge_block(
    tmp_path: Path,
    field: str,
    value: str,
    reason: str,
) -> None:
    bundle = _future_repo(tmp_path, schema_version=2)
    bundle["attestation"][field] = value
    _refresh_attestation_digest(bundle)
    result = _validate(bundle)
    assert result["gate_status"] == "BLOCKED"
    assert any(f"attestation_{reason}_before_merge" in item for item in result["blocking_reasons"])


@pytest.mark.parametrize(
    ("field", "value", "reason"),
    [
        ("_remote_comment_created_at", None, "created"),
        ("_remote_comment_created_at", "not-a-timestamp", "created"),
        ("_remote_comment_updated_at", None, "updated"),
        ("_remote_comment_updated_at", "not-a-timestamp", "updated"),
    ],
)
def test_v2_missing_or_invalid_comment_timestamp_blocks(
    tmp_path: Path,
    field: str,
    value: str | None,
    reason: str,
) -> None:
    bundle = _future_repo(tmp_path, schema_version=2)
    if value is None:
        bundle["attestation"].pop(field)
    else:
        bundle["attestation"][field] = value
    _refresh_attestation_digest(bundle)
    result = _validate(bundle)
    assert result["gate_status"] == "BLOCKED"
    assert any(f"attestation_{reason}_before_merge" in item for item in result["blocking_reasons"])


@pytest.mark.parametrize("merged_at", [None, "not-a-timestamp", "2026-07-27T00:00:00"])
def test_v2_missing_or_invalid_remote_merged_at_blocks(
    tmp_path: Path,
    merged_at: str | None,
) -> None:
    bundle = _future_repo(tmp_path, schema_version=2)
    result = _validate(bundle, verifier=FakeVerifier(merged_at=merged_at))
    assert result["gate_status"] == "BLOCKED"
    assert any("remote_pr_merged_at" in item for item in result["blocking_reasons"])


def test_v1_four_run_still_passes(tmp_path: Path) -> None:
    bundle = _future_repo(tmp_path, schema_version=1)
    result = _validate(bundle)
    assert result["gate_status"] == "PASSED", result


def test_v1_and_v2_use_distinct_workflow_policies() -> None:
    assert len(CANONICAL_WORKFLOW_POLICY) == 4
    assert "State Gate (push)" in CANONICAL_WORKFLOW_POLICY
    assert len(CURRENT_PREMERGE_WORKFLOW_POLICY) == 3
    assert "State Gate (push)" not in CURRENT_PREMERGE_WORKFLOW_POLICY


def test_v1_attestation_rejects_v2_three_observation_count(tmp_path: Path) -> None:
    bundle = _future_repo(tmp_path, schema_version=1)
    bundle["attestation"]["workflow_observations"] = bundle[
        "attestation"
    ]["workflow_observations"][:3]
    result = _validate(bundle)
    assert result["gate_status"] == "BLOCKED"
    assert any("workflow_observation_fields" in item for item in result["blocking_reasons"])


def test_v2_attestation_rejects_four_observations(tmp_path: Path) -> None:
    bundle = _future_repo(tmp_path, schema_version=2)
    extra_obs = {
        "name": "State Gate (push)",
        "run_id": 9999,
        "workflow_file": ".github/workflows/state-gate.yml",
        "event": "push",
        "run_attempt": 1,
        "head_sha": bundle["head"],
        "conclusion": "success",
    }
    bundle["attestation"]["workflow_observations"].append(extra_obs)
    result = _validate(bundle)
    assert result["gate_status"] == "BLOCKED"
    assert any("workflow_observation_fields" in item for item in result["blocking_reasons"])


def test_v2_owner_approval_checks_still_fail_closed(tmp_path: Path) -> None:
    bundle = _future_repo(tmp_path, schema_version=2)
    bundle["attestation"]["_remote_author"] = "attacker"
    result = _validate(bundle)
    assert result["gate_status"] == "BLOCKED"
    assert any("approval_remote_identity" in item for item in result["blocking_reasons"])


def test_v2_approval_payload_digest_still_fail_closed(tmp_path: Path) -> None:
    bundle = _future_repo(tmp_path, schema_version=2)
    bundle["attestation"]["human_r2_approval"]["approval_content_digest"] = (
        "sha256:" + "0" * 64
    )
    result = _validate(bundle)
    assert result["gate_status"] == "BLOCKED"
    assert any("approval_content_digest" in item for item in result["blocking_reasons"])


def test_v2_attestation_digest_still_fail_closed(tmp_path: Path) -> None:
    bundle = _future_repo(tmp_path, schema_version=2)
    bundle["attestation"]["content_digest"] = "sha256:" + "0" * 64
    result = _validate(bundle)
    assert result["gate_status"] == "BLOCKED"
    assert any("attestation_content_digest" in item for item in result["blocking_reasons"])


def test_v2_merge_topology_checks_still_fail_closed(tmp_path: Path) -> None:
    bundle = _future_repo(tmp_path, schema_version=2)
    bundle["merge"] = bundle["head"]
    result = _validate(bundle)
    assert result["gate_status"] == "BLOCKED"
    assert any("merge_structure" in item for item in result["blocking_reasons"])


def test_v2_merge_tree_policy_still_fail_closed(tmp_path: Path) -> None:
    bundle = _future_repo(tmp_path, schema_version=2)
    (bundle["repo"] / "merge-only.txt").write_text("unexpected\n", encoding="utf-8")
    _git(bundle["repo"], "add", "merge-only.txt")
    _git(bundle["repo"], "commit", "--amend", "--no-edit")
    bundle["merge"] = _git(bundle["repo"], "rev-parse", "HEAD")
    result = _validate(bundle)
    assert result["gate_status"] == "BLOCKED"
    assert any("merge_tree_policy" in item for item in result["blocking_reasons"])


def test_v2_output_only_receipt_semantics(tmp_path: Path) -> None:
    bundle = _future_repo(tmp_path, schema_version=2)
    before = _git(bundle["repo"], "rev-parse", "HEAD")
    validation = _validate(bundle)
    receipt = emit_mainline_integration_receipt(validation, emitted_at=NOW)
    after = _git(bundle["repo"], "rev-parse", "HEAD")
    assert receipt["receipt_status"] == "EMITTED"
    assert before == after


def test_v2_wrong_locked_base_still_blocks(tmp_path: Path) -> None:
    bundle = _future_repo(tmp_path, schema_version=2)
    bundle["attestation"]["locked_base_sha"] = "0" * 40
    result = _validate(bundle)
    assert result["gate_status"] == "BLOCKED"
    assert any("first_parent_identity" in item for item in result["blocking_reasons"])


def test_v2_wrong_accepted_head_still_blocks(tmp_path: Path) -> None:
    bundle = _future_repo(tmp_path, schema_version=2)
    bundle["attestation"]["accepted_exact_head_sha"] = "0" * 40
    result = _validate(bundle)
    assert result["gate_status"] == "BLOCKED"
    assert any("second_parent_identity" in item for item in result["blocking_reasons"])


def test_unsupported_intent_schema_version_fails_closed(tmp_path: Path) -> None:
    bundle = _future_repo(tmp_path, schema_version=1)
    intent = dict(bundle["intent"])
    intent["schema_version"] = 4
    repo = bundle["repo"]
    _git(repo, "checkout", "feature")
    intent_path = repo / "project_state" / "mainline_merge_intents" / "active.json"
    intent_path.write_text(json.dumps(intent, indent=2) + "\n", encoding="utf-8")
    _git(repo, "add", "project_state/mainline_merge_intents/active.json")
    _git(repo, "commit", "--amend", "--no-edit")
    new_head = _git(repo, "rev-parse", "HEAD")
    tree = _git(repo, "rev-parse", "HEAD^{tree}")
    new_merge = _git(
        repo,
        "commit-tree",
        tree,
        "-p",
        bundle["base"],
        "-p",
        new_head,
        "-m",
        "merge unsupported intent schema",
    )
    bundle["head"] = new_head
    bundle["merge"] = new_merge
    bundle["attestation"]["accepted_exact_head_sha"] = new_head
    result = _validate(bundle)
    assert result["gate_status"] == "BLOCKED"
    assert any(
        "intent_schema_version: unsupported_version=4" in item
        for item in result["blocking_reasons"]
    )


def test_v2_attestation_unsupported_schema_version_fails_closed(
    tmp_path: Path,
) -> None:
    bundle = _future_repo(tmp_path, schema_version=2)
    bundle["attestation"]["schema_version"] = 4
    result = _validate(bundle)
    assert result["gate_status"] == "BLOCKED"
    assert any(
        "attestation_schema_version: unsupported_version=4" in item
        for item in result["blocking_reasons"]
    )


@pytest.mark.parametrize("encoding", ["utf-8", "BASE64", "", None])
def test_production_verifier_rejects_unexpected_content_encoding(
    encoding: object,
) -> None:
    result = _verify_contents_payload({"encoding": encoding, "content": "YWJj"})
    assert result == {
        "verified": False,
        "reason": "unexpected_content_encoding",
    }


@pytest.mark.parametrize("content", [None, 1, True, [], {}])
def test_production_verifier_rejects_non_string_content(content: object) -> None:
    result = _verify_contents_payload({"encoding": "base64", "content": content})
    assert result == {"verified": False, "reason": "invalid_content_type"}


def test_production_verifier_rejects_missing_content() -> None:
    result = _verify_contents_payload({"encoding": "base64"})
    assert result == {"verified": False, "reason": "invalid_content_type"}


def test_production_verifier_rejects_digest_mismatch(
    github_contents_base64_payload: dict[str, object],
) -> None:
    result = _verify_contents_payload(
        github_contents_base64_payload,
        expected_sha256="0" * 64,
    )
    observed = hashlib.sha256(b"github contents api fixture").hexdigest()
    assert result == {
        "verified": False,
        "reason": f"content_digest_mismatch:{observed}",
    }


def test_production_verifier_accepts_empty_base64_content() -> None:
    result = _verify_contents_payload(
        {"encoding": "base64", "content": ""},
        expected_content=b"",
    )
    assert result["verified"] is True


# ---------------------------------------------------------------------------
# Schema v3: scope-aware trusted workflow profile policy (Issue #345)
# ---------------------------------------------------------------------------


def test_trusted_profiles_are_baseline_supersets() -> None:
    baseline = list(TRUSTED_PREMERGE_WORKFLOW_PROFILES["baseline"])
    assert baseline == list(CURRENT_PREMERGE_WORKFLOW_POLICY)
    assert "State Gate (push)" not in TRUSTED_PREMERGE_WORKFLOW_PROFILES["baseline"]
    assert "State Gate (push)" not in TRUSTED_PREMERGE_WORKFLOW_PROFILES["browser_r3"]
    for name, profile in TRUSTED_PREMERGE_WORKFLOW_PROFILES.items():
        assert list(profile)[:3] == baseline, f"profile {name} must be baseline-first"
    browser_r3 = list(TRUSTED_PREMERGE_WORKFLOW_PROFILES["browser_r3"])
    assert "Frontend Playwright" in browser_r3
    assert "Model Access" in browser_r3
    assert len(browser_r3) == 5


def test_resolve_premerge_workflow_profile_rejects_unknown_names() -> None:
    for bad in ("", "unknown", "Baseline", "browser", "browser_r4", None, 3, {}):
        with pytest.raises(ValueError):
            resolve_premerge_workflow_profile(bad)
    assert resolve_premerge_workflow_profile("baseline") == (
        TRUSTED_PREMERGE_WORKFLOW_PROFILES["baseline"]
    )


def test_v3_baseline_round_resolves_and_accepts_three_workflow_baseline(
    tmp_path: Path,
) -> None:
    bundle = _future_repo(tmp_path, schema_version=3, workflow_profile="baseline")
    assert bundle["intent"]["workflow_profile"] == "baseline"
    assert bundle["intent"]["required_workflows"] == list(
        CURRENT_PREMERGE_WORKFLOW_POLICY
    )
    assert len(bundle["attestation"]["workflow_observations"]) == 3
    result = _validate(bundle)
    assert result["gate_status"] == "PASSED", result


def test_v3_browser_r3_round_resolves_exact_specialized_set(tmp_path: Path) -> None:
    bundle = _future_repo(
        tmp_path,
        schema_version=3,
        workflow_profile="browser_r3",
        decision_contract_profile="browser_r3",
    )
    observed = [obs["name"] for obs in bundle["attestation"]["workflow_observations"]]
    assert observed == list(TRUSTED_PREMERGE_WORKFLOW_PROFILES["browser_r3"])
    assert "Frontend Playwright" in observed
    assert "Model Access" in observed
    result = _validate(bundle)
    assert result["gate_status"] == "PASSED", result


def test_v3_missing_specialized_workflow_blocks(tmp_path: Path) -> None:
    bundle = _future_repo(
        tmp_path,
        schema_version=3,
        workflow_profile="browser_r3",
        decision_contract_profile="browser_r3",
    )
    bundle["attestation"]["workflow_observations"] = bundle["attestation"][
        "workflow_observations"
    ][:4]
    result = _validate(bundle)
    assert result["gate_status"] == "BLOCKED"
    assert any("workflow_names" in item for item in result["blocking_reasons"])
    assert any("Model Access" in item for item in result["blocking_reasons"])


def test_v3_deleted_specialized_workflow_from_intent_blocks(tmp_path: Path) -> None:
    bundle = _future_repo(
        tmp_path,
        schema_version=3,
        workflow_profile="browser_r3",
        decision_contract_profile="browser_r3",
    )
    amended = dict(bundle["intent"])
    amended["required_workflows"] = amended["required_workflows"][:4]
    _recommit_intent(bundle, amended)
    result = _validate(bundle)
    assert result["gate_status"] == "BLOCKED"
    assert any("intent_workflow_policy" in item for item in result["blocking_reasons"])


def test_v3_failing_specialized_workflow_blocks(tmp_path: Path) -> None:
    bundle = _future_repo(
        tmp_path,
        schema_version=3,
        workflow_profile="browser_r3",
        decision_contract_profile="browser_r3",
    )
    names = [obs["name"] for obs in bundle["attestation"]["workflow_observations"]]
    frontend = bundle["attestation"]["workflow_observations"][
        names.index("Frontend Playwright")
    ]
    frontend["conclusion"] = "failure"
    result = _validate(bundle)
    assert result["gate_status"] == "BLOCKED"
    assert any(
        "remote_workflow:Frontend Playwright" in item
        for item in result["blocking_reasons"]
    )


def test_v3_wrong_head_specialized_run_blocks(tmp_path: Path) -> None:
    bundle = _future_repo(
        tmp_path,
        schema_version=3,
        workflow_profile="browser_r3",
        decision_contract_profile="browser_r3",
    )
    names = [obs["name"] for obs in bundle["attestation"]["workflow_observations"]]
    model_access = bundle["attestation"]["workflow_observations"][
        names.index("Model Access")
    ]
    model_access["head_sha"] = "0" * 40
    result = _validate(bundle)
    assert result["gate_status"] == "BLOCKED"
    assert any(
        "remote_workflow:Model Access" in item
        for item in result["blocking_reasons"]
    )


def test_v3_wrong_file_or_event_specialized_run_blocks(tmp_path: Path) -> None:
    bundle = _future_repo(
        tmp_path,
        schema_version=3,
        workflow_profile="browser_r3",
        decision_contract_profile="browser_r3",
    )
    names = [obs["name"] for obs in bundle["attestation"]["workflow_observations"]]
    frontend = bundle["attestation"]["workflow_observations"][
        names.index("Frontend Playwright")
    ]
    frontend["workflow_file"] = ".github/workflows/ci.yml"
    frontend["event"] = "push"
    result = _validate(bundle)
    assert result["gate_status"] == "BLOCKED"
    assert any(
        "remote_workflow:Frontend Playwright" in item
        for item in result["blocking_reasons"]
    )


def test_v3_unknown_workflow_profile_name_fails_closed(tmp_path: Path) -> None:
    bundle = _future_repo(
        tmp_path,
        schema_version=3,
        workflow_profile="custom",
        decision_contract_profile="custom",
    )
    result = _validate(bundle)
    assert result["gate_status"] == "BLOCKED"
    assert any("intent_workflow_profile" in item for item in result["blocking_reasons"])
    assert any("intent_workflow_policy" in item for item in result["blocking_reasons"])


def test_v3_free_form_workflow_names_fail_closed(tmp_path: Path) -> None:
    bundle = _future_repo(tmp_path, schema_version=3, workflow_profile="baseline")
    amended = dict(bundle["intent"])
    amended["required_workflows"] = [
        "CI",
        "Decision Preflight",
        "State Gate (pull_request)",
        "Totally Custom Workflow",
    ]
    _recommit_intent(bundle, amended)
    result = _validate(bundle)
    assert result["gate_status"] == "BLOCKED"
    assert any("intent_workflow_policy" in item for item in result["blocking_reasons"])


def test_v3_missing_workflow_profile_field_blocks(tmp_path: Path) -> None:
    bundle = _future_repo(tmp_path, schema_version=3, workflow_profile="baseline")
    amended = dict(bundle["intent"])
    del amended["workflow_profile"]
    _recommit_intent(bundle, amended)
    result = _validate(bundle)
    assert result["gate_status"] == "BLOCKED"
    assert any("intent_fields" in item for item in result["blocking_reasons"])


def test_v3_intent_profile_must_equal_decision_declared_profile(
    tmp_path: Path,
) -> None:
    bundle = _future_repo(
        tmp_path,
        schema_version=3,
        workflow_profile="baseline",
        decision_contract_profile="browser_r3",
    )
    result = _validate(bundle)
    assert result["gate_status"] == "BLOCKED"
    assert any(
        "intent_workflow_profile" in item for item in result["blocking_reasons"]
    )


def test_v3_decision_without_declared_profile_fails_closed(tmp_path: Path) -> None:
    bundle = _future_repo(tmp_path, schema_version=3, workflow_profile="baseline")
    repo = bundle["repo"]
    _git(repo, "checkout", "feature")
    decision_path = repo / "project_state" / "decision_packet.md"
    decision_path.write_text(
        "# Decision Packet\n\n"
        "```json decision_meta\n"
        + json.dumps(
            {
                "schema_version": 1,
                "decision_id": "decision_20260801_later_mainline_landing_v4",
                "round_id": "round_20260801_later_mainline_landing_v4",
                "status": "APPROVED",
                "mainline": "engineering_branch",
            },
            separators=(",", ":"),
        )
        + "\n```\n\n"
        "```json decision_contract\n"
        + json.dumps({"risk_tier": "R2"}, separators=(",", ":"))
        + "\n```\n",
        encoding="utf-8",
    )
    _git(repo, "add", "project_state/decision_packet.md")
    _git(repo, "commit", "--amend", "--no-edit")
    new_head = _git(repo, "rev-parse", "HEAD")
    tree = _git(repo, "rev-parse", "HEAD^{tree}")
    new_merge = _git(
        repo,
        "commit-tree",
        tree,
        "-p",
        bundle["base"],
        "-p",
        new_head,
        "-m",
        "merge decision without declared profile",
    )
    bundle["head"] = new_head
    bundle["merge"] = new_merge
    bundle["attestation"]["accepted_exact_head_sha"] = new_head
    result = _validate(bundle)
    assert result["gate_status"] == "BLOCKED"
    assert any(
        "intent_workflow_profile" in item for item in result["blocking_reasons"]
    )


def test_v3_duplicate_run_id_blocks(tmp_path: Path) -> None:
    bundle = _future_repo(
        tmp_path,
        schema_version=3,
        workflow_profile="browser_r3",
        decision_contract_profile="browser_r3",
    )
    observations = bundle["attestation"]["workflow_observations"]
    observations[3]["run_id"] = observations[0]["run_id"]
    result = _validate(bundle)
    assert result["gate_status"] == "BLOCKED"
    assert any("workflow_run_uniqueness" in item for item in result["blocking_reasons"])


def test_v3_push_state_gate_cannot_be_pre_merge_evidence(tmp_path: Path) -> None:
    bundle = _future_repo(tmp_path, schema_version=3, workflow_profile="baseline")
    for obs in bundle["attestation"]["workflow_observations"]:
        obs["name"] = "State Gate (push)"
        obs["event"] = "push"
    result = _validate(bundle)
    assert result["gate_status"] == "BLOCKED"
    assert any("workflow_names" in item for item in result["blocking_reasons"])


def test_v3_baseline_excludes_state_gate_push_from_requirements(
    tmp_path: Path,
) -> None:
    bundle = _future_repo(tmp_path, schema_version=3, workflow_profile="baseline")
    assert "State Gate (push)" not in bundle["intent"]["required_workflows"]
    assert all(
        "State Gate (push)" not in obs["name"]
        for obs in bundle["attestation"]["workflow_observations"]
    )
    result = _validate(bundle)
    assert result["gate_status"] == "PASSED", result


def test_v3_attestation_with_unresolvable_intent_profile_fails_closed(
    tmp_path: Path,
) -> None:
    bundle = _future_repo(tmp_path, schema_version=3, workflow_profile="baseline")
    result = _validate(bundle)
    assert result["gate_status"] == "PASSED", result
    v2_intent = dict(bundle["intent"])
    v2_intent["schema_version"] = 2
    del v2_intent["workflow_profile"]
    _recommit_intent(bundle, v2_intent)
    result = _validate(bundle)
    assert result["gate_status"] == "BLOCKED"
    assert any(
        "attestation_schema_version: unresolved_workflow_profile" in item
        for item in result["blocking_reasons"]
    )


def test_v3_merge_topology_and_owner_checks_still_fail_closed(
    tmp_path: Path,
) -> None:
    bundle = _future_repo(tmp_path, schema_version=3, workflow_profile="baseline")
    bundle["attestation"]["_remote_author"] = "attacker"
    result = _validate(bundle)
    assert result["gate_status"] == "BLOCKED"
    assert any("approval_remote_identity" in item for item in result["blocking_reasons"])


def test_v3_post_merge_validation_runs_unchanged(tmp_path: Path) -> None:
    bundle = _future_repo(tmp_path, schema_version=3, workflow_profile="baseline")
    before = _git(bundle["repo"], "rev-parse", "HEAD")
    validation = _validate(bundle)
    receipt = emit_mainline_integration_receipt(validation, emitted_at=NOW)
    after = _git(bundle["repo"], "rev-parse", "HEAD")
    assert validation["gate_status"] == "PASSED", validation
    assert receipt["receipt_status"] == "EMITTED"
    assert before == after


def test_v3_premerge_attestation_does_not_require_merge_fields(
    tmp_path: Path,
) -> None:
    """Pre-merge checks keep owner/digest/workflow proof without post-merge facts."""

    bundle = _future_repo(tmp_path, schema_version=3, workflow_profile="baseline")
    checks = validate_premerge_attestation(
        bundle["attestation"],
        verifier=FakeVerifier(merged=False, merged_at=None),
        intent=bundle["intent"],
        accepted_head=bundle["head"],
        locked_base=bundle["base"],
        now=NOW,
    )
    assert all(check["status"] == "PASS" for check in checks), checks
    assert not any(check["name"] == "remote_pr_merged_at" for check in checks)


@pytest.mark.parametrize("schema_version", [1, 2])
def test_legacy_schema_premerge_rejection_is_explicit_but_postmerge_passes(
    tmp_path: Path, schema_version: int
) -> None:
    """Legacy evidence remains valid for history, never for the pre-merge gate."""

    bundle = _future_repo(tmp_path, schema_version=schema_version)
    intent_checks = validate_active_merge_intent(
        bundle["intent"],
        repo_root=bundle["repo"],
        accepted_head=bundle["head"],
        source_pr=67,
        locked_base=bundle["base"],
        now=NOW,
    )
    attestation_checks = validate_premerge_attestation(
        bundle["attestation"],
        verifier=FakeVerifier(merged=False, merged_at=None),
        intent=bundle["intent"],
        accepted_head=bundle["head"],
        locked_base=bundle["base"],
        now=NOW,
    )
    assert intent_checks == [
        {
            "name": "premerge_intent_schema_version",
            "status": "FAIL",
            "detail": f"observed={schema_version!r} expected=3",
        }
    ]
    assert attestation_checks == [
        {
            "name": "premerge_attestation_schema_version",
            "status": "FAIL",
            "detail": f"observed={schema_version!r} expected=3",
        }
    ]
    postmerge = _validate(bundle)
    assert postmerge["gate_status"] == "PASSED", postmerge


# ---------------------------------------------------------------------------
# Issue #156 post-merge validator cutover: false/none Owner landing authority
#
# A committed second-parent Decision with ``mainline_merge_intent_required=
# false`` + ``active_pr_binding_mode=none`` must be post-merge validated
# against a fresh pre-merge ``OWNER_LANDING_MERGE_ATTESTATION`` instead of the
# historical ``project_state/mainline_merge_intents/active.json``.  The legacy
# true/bound validator stays unchanged, and every contradictory or missing
# authority shape fails closed.
# ---------------------------------------------------------------------------


def _false_none_repo(tmp_path: Path, *, contract_extra: dict[str, Any] | None = None) -> dict[str, Any]:
    repo = tmp_path / "fnrepo"
    repo.mkdir()
    _git(repo, "init", "-b", "main")
    _git(repo, "config", "user.email", "test@example.com")
    _git(repo, "config", "user.name", "Test")
    (repo / "base.txt").write_text("base\n", encoding="utf-8")
    _git(repo, "add", "base.txt")
    _git(repo, "commit", "-m", "base")
    base = _git(repo, "rev-parse", "HEAD")
    _git(repo, "checkout", "-b", "feature")
    decision_path = repo / "project_state" / "decision_packet.md"
    decision_path.parent.mkdir(parents=True)
    contract = {
        "transition_kernel_required": True,
        "mainline_merge_intent_required": False,
        "active_pr_binding_mode": "none",
    }
    if contract_extra:
        contract.update(contract_extra)
    decision_id = "decision_20260903_issue156_postmerge_validator_cutover_r1"
    decision_text = (
        "# Decision Packet\n\n"
        "```json decision_meta\n"
        + json.dumps(
            {
                "schema_version": 1,
                "decision_id": decision_id,
                "round_id": "round_" + decision_id[len("decision_") :],
                "status": "APPROVED",
                "mainline": "engineering_branch",
            },
            separators=(",", ":"),
        )
        + "\n```\n\n"
        "```json decision_contract\n"
        + json.dumps(contract, separators=(",", ":"))
        + "\n```\n"
    )
    decision_path.write_text(decision_text, encoding="utf-8")
    (repo / "feature.txt").write_text("feature\n", encoding="utf-8")
    _git(repo, "add", "project_state/decision_packet.md", "feature.txt")
    _git(repo, "commit", "-m", "false-none feature")
    head = _git(repo, "rev-parse", "HEAD")
    _git(repo, "checkout", "main")
    _git(repo, "merge", "--no-ff", "feature", "-m", "merge false-none")
    merge = _git(repo, "rev-parse", "HEAD")
    decision_digest = hashlib.sha256(
        subprocess.check_output(
            ["git", "show", f"{head}:project_state/decision_packet.md"], cwd=repo
        )
    ).hexdigest()
    return {
        "repo": repo,
        "state_dir": repo / "project_state",
        "base": base,
        "head": head,
        "merge": merge,
        "decision_id": decision_id,
        "decision_digest": decision_digest,
    }


_FALSE_NONE_AUTHORITY_RUN_SPEC = [
    ("CI", 8101, ".github/workflows/ci.yml"),
    ("Decision Preflight", 8102, ".github/workflows/decision-preflight.yml"),
    ("State Gate (pull_request)", 8103, ".github/workflows/state-gate.yml"),
]


def _authority_decision_text(
    decision_id: str,
    *,
    target_pr: int,
    head: str,
    base: str,
    bind_target: bool = True,
    owner_scope: bool = True,
) -> str:
    contract: dict[str, Any] = {
        "transition_kernel_required": True,
        "decision_scope": "OWNER_LANDING_AUTHORITY_SIDECAR",
        "sidecar_authority": True,
        "target_pr": target_pr if bind_target else 0,
        "accepted_exact_head_sha": head if bind_target else "0" * 40,
        "base_sha": base if bind_target else "0" * 40,
        "integration_base_ref": "main",
        "mark_ready_allowed": owner_scope,
        "merge_allowed": owner_scope,
        "expected_head_protection_required": owner_scope,
        "allowed_merge_method": "merge",
        "workflow_rerun_allowed": False,
        "auto_merge_allowed": False,
        "direct_push_to_main_allowed": False,
        "force_push_allowed": False,
        "forbidden_operations": ["active_json_rewrite", "workflow_rerun", "direct_push_main"],
        "forbidden_mutated_paths": ["project_state/mainline_merge_intents/**"],
        "mainline_merge_intent_required": False,
        "active_pr_binding_mode": "none",
    }
    return (
        "# Decision Packet\n\n"
        "```json decision_meta\n"
        + json.dumps(
            {
                "schema_version": 1,
                "decision_id": decision_id,
                "round_id": "round_" + decision_id[len("decision_") :],
                "status": "APPROVED",
                "mainline": "engineering_branch",
            },
            separators=(",", ":"),
        )
        + "\n```\n\n"
        "```json decision_contract\n"
        + json.dumps(contract, separators=(",", ":"))
        + "\n```\n"
    )


class FalseNoneVerifier:
    def __init__(
        self,
        bundle: dict[str, Any],
        *,
        source_pr: int = 809,
        authority_pr: int = 810,
        authority_head: str = "5" * 40,
        authority_base: str = "6" * 40,
        authority_decision_id: str = "decision_20260903_issue156_postmerge_validator_cutover_r1_authority_v1",
        authority_merged: bool = False,
        bind_target: bool = True,
        owner_scope: bool = True,
        review_commit: str | None = None,
        review_author: str = "dddd2024",
        review_submitted_at: str = "2026-09-03T11:10:00Z",
        review_id: int = 555,
        ready_run_id: int = 7001,
        ready_run_ok: bool = True,
        ready_head_ok: bool = True,
        merged_at: str = "2026-09-03T11:30:00Z",
        check_names: set[str] | None = None,
        ruleset_ok: bool = True,
        authority_workflow_ok: bool = True,
        attestations: list[dict[str, Any]] | None = None,
    ) -> None:
        self.bundle = bundle
        self.source_pr = source_pr
        self.authority_pr = authority_pr
        self.authority_head = authority_head
        self.authority_base = authority_base
        self.authority_decision_id = authority_decision_id
        self.authority_merged = authority_merged
        self.bind_target = bind_target
        self.owner_scope = owner_scope
        self.review_commit = review_commit if review_commit is not None else bundle["head"]
        self.review_author = review_author
        self.review_submitted_at = review_submitted_at
        self.review_id = review_id
        self.ready_run_id = ready_run_id
        self.ready_run_ok = ready_run_ok
        self.ready_head_ok = ready_head_ok
        self.merged_at = merged_at
        self.check_names = (
            check_names if check_names is not None else set(FALSE_NONE_REQUIRED_CONTEXTS)
        )
        self.ruleset_ok = ruleset_ok
        self.authority_workflow_ok = authority_workflow_ok
        self.attestations = attestations
        self.authority_decision_text = _authority_decision_text(
            authority_decision_id,
            target_pr=source_pr,
            head=bundle["head"],
            base=bundle["base"],
            bind_target=bind_target,
            owner_scope=owner_scope,
        )
        self.authority_decision_sha = hashlib.sha256(
            self.authority_decision_text.encode("utf-8")
        ).hexdigest()

    def resolve_merged_pull_request(self, *, merge_commit_sha: str) -> dict[str, Any]:
        return {
            "number": self.source_pr,
            "merged": True,
            "merged_at": self.merged_at,
            "merge_commit_sha": self.bundle["merge"],
            "head": {"sha": self.bundle["head"]},
            "base": {"repo": {"full_name": "dddd2024/Nerelan"}, "sha": self.bundle["base"]},
        }

    def load_owner_landing_merge_attestations(self, *, pr_number: int) -> list[dict[str, Any]]:
        if pr_number != self.source_pr:
            return []
        return list(self.attestations or [])

    def verify_pr(self, **kwargs: Any) -> dict[str, Any]:
        pr_number = kwargs.get("pr_number")
        expected_merge = kwargs.get("expected_merge_commit_sha")
        require_merged = kwargs.get("require_merged")
        if pr_number == self.source_pr:
            merged = True
            head = self.bundle["head"]
            base = self.bundle["base"]
            merge_commit = self.bundle["merge"]
        elif pr_number == self.authority_pr:
            merged = self.authority_merged
            head = self.authority_head
            base = self.authority_base
            merge_commit = None
        else:
            return {"verified": False, "reason": f"pr_mismatch:pr={pr_number}"}
        checks = {
            "repository": True,
            "head": kwargs.get("expected_head_sha") == head,
            "base": kwargs.get("expected_base_sha") == base,
        }
        if expected_merge is not None:
            checks["merge_commit"] = merge_commit == expected_merge
        if require_merged is not None:
            checks["merged"] = merged is require_merged
        if not all(checks.values()):
            return {"verified": False, "reason": f"pr_mismatch:{checks}"}
        return {
            "verified": True,
            "pr": {
                "number": pr_number,
                "merged": merged,
                "merged_at": self.merged_at,
                "merge_commit_sha": merge_commit,
                "head": {"sha": head},
                "base": {"sha": base},
            },
        }

    def verify_workflow_run(self, **kwargs: Any) -> dict[str, Any]:
        run_id = int(kwargs.get("run_id") or 0)
        expected_head = kwargs.get("expected_head_sha")
        ok = False
        for name, spec_run_id, _workflow_file in _FALSE_NONE_AUTHORITY_RUN_SPEC:
            if run_id == spec_run_id:
                ok = (
                    self.authority_workflow_ok
                    and expected_head == self.authority_head
                    and kwargs.get("expected_workflow_file") == _workflow_file
                    and kwargs.get("expected_event") == "pull_request"
                )
                break
        if run_id == self.ready_run_id:
            ok = (
                self.ready_run_ok
                and self.ready_head_ok
                and expected_head == self.bundle["head"]
                and kwargs.get("expected_workflow_file") == ".github/workflows/state-gate.yml"
                and kwargs.get("expected_event") == "pull_request"
            )
        if not ok:
            return {"verified": False, "reason": "workflow_mismatch"}
        return {"verified": True, "reason": "", "run": kwargs}

    def verify_pull_request_review(self, **kwargs: Any) -> dict[str, Any]:
        ok = (
            kwargs.get("pr_number") == self.source_pr
            and self.review_author in kwargs.get("allowed_authors", ())
            and kwargs.get("expected_commit_sha") == self.review_commit
        )
        if not ok:
            return {"verified": False, "reason": "review_mismatch"}
        return {
            "verified": True,
            "review": {
                "user": {"login": self.review_author},
                "commit_id": self.review_commit,
                "submitted_at": self.review_submitted_at,
            },
        }

    def verify_check_run_contexts(self, *, head_sha: str, required_contexts: Any) -> dict[str, Any]:
        runs = [
            {"name": name, "status": "completed", "conclusion": "success"}
            for name in sorted(self.check_names)
        ]
        contexts = {context: (context in self.check_names) for context in required_contexts}
        ok = all(contexts.values())
        reason = "" if ok else f"check_contexts_missing:{[c for c, v in contexts.items() if not v]}"
        return {"verified": ok, "reason": reason, "contexts": contexts, "check_runs": runs}

    def verify_repository_ruleset(self, **kwargs: Any) -> dict[str, Any]:
        return {
            "verified": self.ruleset_ok,
            "reason": "" if self.ruleset_ok else "ruleset_mismatch",
            "ruleset": {},
        }

    def load_ref_file_bytes(self, *, ref: str, path: str) -> dict[str, Any]:
        if ref != self.authority_head:
            return {"verified": False, "reason": "ref_mismatch"}
        return {"verified": True, "bytes": self.authority_decision_text.encode("utf-8")}


def _false_none_attestation(bundle: dict[str, Any], verifier: FalseNoneVerifier) -> dict[str, Any]:
    att: dict[str, Any] = {
        "schema_version": 1,
        "attestation_id": f"owner_landing_{verifier.source_pr}_v1",
        "repository": "dddd2024/Nerelan",
        "source_pr": verifier.source_pr,
        "locked_base_sha": bundle["base"],
        "accepted_exact_head_sha": bundle["head"],
        "target_decision_id": bundle["decision_id"],
        "target_decision_content_sha256": bundle["decision_digest"],
        "allowed_merge_method": "merge",
        "authority_pr": verifier.authority_pr,
        "authority_head_sha": verifier.authority_head,
        "authority_base_sha": verifier.authority_base,
        "authority_decision_id": verifier.authority_decision_id,
        "authority_decision_content_sha256": verifier.authority_decision_sha,
        "authority_natural_runs": [
            {
                "name": name,
                "run_id": run_id,
                "workflow_file": workflow_file,
                "event": "pull_request",
                "run_attempt": 1,
                "head_sha": verifier.authority_head,
                "conclusion": "success",
            }
            for name, run_id, workflow_file in _FALSE_NONE_AUTHORITY_RUN_SPEC
        ],
        "owner_exact_head_review_id": verifier.review_id,
        "ready_state_gate_run_id": verifier.ready_run_id,
        "ruleset_id": 21023698,
        "required_status_contexts": list(FALSE_NONE_REQUIRED_CONTEXTS),
        "mainline_merge_intent_required": False,
        "active_pr_binding_mode": "none",
        "authorization_status": "active",
        "superseded_by": None,
        "_remote_comment_id": 71000,
        "_remote_author": verifier.review_author,
        "_remote_comment_created_at": "2026-09-03T11:00:00Z",
        "_remote_comment_updated_at": "2026-09-03T11:01:00Z",
        "_remote_comment_body": "OWNER_LANDING_MERGE_ATTESTATION\n```json owner_landing_merge_attestation\n{}\n```",
    }
    att["content_digest"] = owner_landing_content_digest(att)
    return att


def _false_none_pair(
    bundle: dict[str, Any],
    *,
    att_overrides: dict[str, Any] | None = None,
    **verifier_kwargs: Any,
) -> tuple[FalseNoneVerifier, dict[str, Any]]:
    verifier = FalseNoneVerifier(bundle, **verifier_kwargs)
    att = _false_none_attestation(bundle, verifier)
    if att_overrides:
        att.update(att_overrides)
    att["content_digest"] = owner_landing_content_digest(att)
    verifier.attestations = [att]
    return verifier, att


def _false_none_validate(bundle: dict[str, Any], verifier: FalseNoneVerifier) -> dict[str, Any]:
    return validate_future_merge(
        repo_root=bundle["repo"],
        state_dir=bundle["state_dir"],
        attestation={},
        verifier=verifier,
        commit_sha=bundle["merge"],
        validation_time=NOW,
    )


def test_false_none_valid_owner_landing_passes(tmp_path: Path) -> None:
    bundle = _false_none_repo(tmp_path)
    verifier, _ = _false_none_pair(bundle)
    result = _false_none_validate(bundle, verifier)
    assert result["gate_status"] == "PASSED", result
    by_name = {check["name"]: check["status"] for check in result["checks"]}
    assert by_name["landing_policy_mode"] == "PASS"
    assert by_name["false_none_target_pr_resolution"] == "PASS"
    assert by_name["false_none_attestation_unique"] == "PASS"
    assert by_name["false_none_authority_unmerged"] == "PASS"
    assert by_name["false_none_landing_context_is_formal"] == "PASS"
    assert result["target_pr"] == 809
    assert result["authority_pr"] == 810


def test_false_none_missing_attestation_blocks(tmp_path: Path) -> None:
    bundle = _false_none_repo(tmp_path)
    verifier, _ = _false_none_pair(bundle)
    verifier.attestations = []
    result = _false_none_validate(bundle, verifier)
    assert result["gate_status"] == "BLOCKED", result
    assert any(
        "false_none_attestation_unique: observed=0" in item
        for item in result["blocking_reasons"]
    )


def test_false_none_duplicate_attestation_blocks(tmp_path: Path) -> None:
    bundle = _false_none_repo(tmp_path)
    verifier, att = _false_none_pair(bundle)
    duplicate = dict(att)
    duplicate["attestation_id"] = "owner_landing_809_duplicate"
    verifier.attestations = [att, duplicate]
    result = _false_none_validate(bundle, verifier)
    assert result["gate_status"] == "BLOCKED", result
    assert any(
        "false_none_attestation_unique: observed=2" in item
        for item in result["blocking_reasons"]
    )


def test_false_none_wrong_target_pr_blocks(tmp_path: Path) -> None:
    bundle = _false_none_repo(tmp_path)
    verifier, _ = _false_none_pair(bundle, att_overrides={"source_pr": 999})
    result = _false_none_validate(bundle, verifier)
    assert result["gate_status"] == "BLOCKED", result
    assert any("false_none_attestation_unique" in item for item in result["blocking_reasons"])


def test_false_none_wrong_target_head_blocks(tmp_path: Path) -> None:
    bundle = _false_none_repo(tmp_path)
    verifier, _ = _false_none_pair(
        bundle, att_overrides={"accepted_exact_head_sha": "1" * 40}
    )
    result = _false_none_validate(bundle, verifier)
    assert result["gate_status"] == "BLOCKED", result
    assert any("false_none_attestation_unique" in item for item in result["blocking_reasons"])


def test_false_none_wrong_target_base_blocks(tmp_path: Path) -> None:
    bundle = _false_none_repo(tmp_path)
    verifier, _ = _false_none_pair(
        bundle, att_overrides={"locked_base_sha": "2" * 40}
    )
    result = _false_none_validate(bundle, verifier)
    assert result["gate_status"] == "BLOCKED", result
    assert any("false_none_attestation_locked_base" in item for item in result["blocking_reasons"])


def test_false_none_wrong_target_decision_id_blocks(tmp_path: Path) -> None:
    bundle = _false_none_repo(tmp_path)
    verifier, _ = _false_none_pair(
        bundle, att_overrides={"target_decision_id": "decision_other_target_v1"}
    )
    result = _false_none_validate(bundle, verifier)
    assert result["gate_status"] == "BLOCKED", result
    assert any("false_none_target_decision_id" in item for item in result["blocking_reasons"])


def test_false_none_wrong_target_decision_digest_blocks(tmp_path: Path) -> None:
    bundle = _false_none_repo(tmp_path)
    verifier, _ = _false_none_pair(
        bundle, att_overrides={"target_decision_content_sha256": "0" * 64}
    )
    result = _false_none_validate(bundle, verifier)
    assert result["gate_status"] == "BLOCKED", result
    assert any("false_none_target_decision_digest" in item for item in result["blocking_reasons"])


def test_false_none_attestation_created_after_merge_blocks(tmp_path: Path) -> None:
    bundle = _false_none_repo(tmp_path)
    verifier, _ = _false_none_pair(
        bundle, att_overrides={"_remote_comment_created_at": "2026-09-03T12:00:00Z"}
    )
    result = _false_none_validate(bundle, verifier)
    assert result["gate_status"] == "BLOCKED", result
    assert any(
        "false_none_attestation_created_before_merge" in item
        for item in result["blocking_reasons"]
    )


def test_false_none_attestation_updated_after_merge_blocks(tmp_path: Path) -> None:
    bundle = _false_none_repo(tmp_path)
    verifier, _ = _false_none_pair(
        bundle, att_overrides={"_remote_comment_updated_at": "2026-09-03T12:00:00Z"}
    )
    result = _false_none_validate(bundle, verifier)
    assert result["gate_status"] == "BLOCKED", result
    assert any(
        "false_none_attestation_updated_before_merge" in item
        for item in result["blocking_reasons"]
    )


def test_false_none_non_owner_comment_author_blocks(tmp_path: Path) -> None:
    bundle = _false_none_repo(tmp_path)
    verifier, _ = _false_none_pair(
        bundle, att_overrides={"_remote_author": "attacker"}
    )
    result = _false_none_validate(bundle, verifier)
    assert result["gate_status"] == "BLOCKED", result
    assert any("false_none_attestation_author" in item for item in result["blocking_reasons"])


def test_false_none_wrong_authority_pr_blocks(tmp_path: Path) -> None:
    bundle = _false_none_repo(tmp_path)
    verifier, _ = _false_none_pair(bundle, att_overrides={"authority_pr": 999})
    result = _false_none_validate(bundle, verifier)
    assert result["gate_status"] == "BLOCKED", result
    assert any("false_none_authority_pr_identity" in item for item in result["blocking_reasons"])


def test_false_none_wrong_authority_head_blocks(tmp_path: Path) -> None:
    bundle = _false_none_repo(tmp_path)
    verifier, _ = _false_none_pair(bundle, att_overrides={"authority_head_sha": "7" * 40})
    result = _false_none_validate(bundle, verifier)
    assert result["gate_status"] == "BLOCKED", result
    assert any("false_none_authority_pr_identity" in item for item in result["blocking_reasons"])


def test_false_none_wrong_authority_base_blocks(tmp_path: Path) -> None:
    bundle = _false_none_repo(tmp_path)
    verifier, _ = _false_none_pair(bundle, att_overrides={"authority_base_sha": "8" * 40})
    result = _false_none_validate(bundle, verifier)
    assert result["gate_status"] == "BLOCKED", result
    assert any("false_none_authority_pr_identity" in item for item in result["blocking_reasons"])


def test_false_none_wrong_authority_decision_blocks(tmp_path: Path) -> None:
    bundle = _false_none_repo(tmp_path)
    verifier, _ = _false_none_pair(
        bundle, att_overrides={"authority_decision_id": "decision_other_authority_v1"}
    )
    result = _false_none_validate(bundle, verifier)
    assert result["gate_status"] == "BLOCKED", result
    assert any("false_none_authority_decision_id" in item for item in result["blocking_reasons"])


def test_false_none_authority_sidecar_merged_blocks(tmp_path: Path) -> None:
    bundle = _false_none_repo(tmp_path)
    verifier, _ = _false_none_pair(bundle, authority_merged=True)
    result = _false_none_validate(bundle, verifier)
    assert result["gate_status"] == "BLOCKED", result
    assert any("false_none_authority_unmerged" in item for item in result["blocking_reasons"])


def test_false_none_authority_decision_not_binding_target_blocks(tmp_path: Path) -> None:
    bundle = _false_none_repo(tmp_path)
    verifier, _ = _false_none_pair(bundle, bind_target=False)
    result = _false_none_validate(bundle, verifier)
    assert result["gate_status"] == "BLOCKED", result
    assert any(
        "false_none_authority_decision_binds_target" in item
        for item in result["blocking_reasons"]
    )


def test_false_none_authority_workflow_missing_blocks(tmp_path: Path) -> None:
    bundle = _false_none_repo(tmp_path)
    verifier, _ = _false_none_pair(
        bundle,
        att_overrides={"authority_natural_runs": []},
    )
    result = _false_none_validate(bundle, verifier)
    assert result["gate_status"] == "BLOCKED", result
    assert any("false_none_authority_runs" in item for item in result["blocking_reasons"])


def test_false_none_authority_workflow_failed_blocks(tmp_path: Path) -> None:
    bundle = _false_none_repo(tmp_path)
    verifier, _ = _false_none_pair(bundle, authority_workflow_ok=False)
    result = _false_none_validate(bundle, verifier)
    assert result["gate_status"] == "BLOCKED", result
    assert any(
        "false_none_authority_workflow:CI" in item for item in result["blocking_reasons"]
    )


def test_false_none_authority_workflow_wrong_head_blocks(tmp_path: Path) -> None:
    bundle = _false_none_repo(tmp_path)
    att = _false_none_attestation(
        bundle, FalseNoneVerifier(bundle)
    )
    runs = att["authority_natural_runs"]
    runs[0] = {**runs[0], "head_sha": "0" * 40}
    verifier, _ = _false_none_pair(
        bundle, att_overrides={"authority_natural_runs": runs}
    )
    result = _false_none_validate(bundle, verifier)
    assert result["gate_status"] == "BLOCKED", result
    assert any(
        "false_none_authority_workflow:CI" in item for item in result["blocking_reasons"]
    )


def test_false_none_owner_review_wrong_commit_blocks(tmp_path: Path) -> None:
    bundle = _false_none_repo(tmp_path)
    verifier, _ = _false_none_pair(bundle, review_commit="0" * 40)
    result = _false_none_validate(bundle, verifier)
    assert result["gate_status"] == "BLOCKED", result
    assert any("false_none_owner_review" in item for item in result["blocking_reasons"])


def test_false_none_owner_review_wrong_author_blocks(tmp_path: Path) -> None:
    bundle = _false_none_repo(tmp_path)
    verifier, _ = _false_none_pair(bundle, review_author="attacker")
    result = _false_none_validate(bundle, verifier)
    assert result["gate_status"] == "BLOCKED", result
    assert any("false_none_owner_review_author" in item for item in result["blocking_reasons"])


def test_false_none_ready_state_gate_wrong_head_blocks(tmp_path: Path) -> None:
    bundle = _false_none_repo(tmp_path)
    verifier, _ = _false_none_pair(bundle, ready_head_ok=False)
    result = _false_none_validate(bundle, verifier)
    assert result["gate_status"] == "BLOCKED", result
    assert any("false_none_ready_state_gate_run" in item for item in result["blocking_reasons"])


def test_false_none_ready_state_gate_failed_blocks(tmp_path: Path) -> None:
    bundle = _false_none_repo(tmp_path)
    verifier, _ = _false_none_pair(bundle, ready_run_ok=False)
    result = _false_none_validate(bundle, verifier)
    assert result["gate_status"] == "BLOCKED", result
    assert any("false_none_ready_state_gate_run" in item for item in result["blocking_reasons"])


def test_false_none_formal_landing_state_gate_missing_blocks(tmp_path: Path) -> None:
    bundle = _false_none_repo(tmp_path)
    verifier, _ = _false_none_pair(
        bundle,
        check_names={"baseline", "state-gate"},
    )
    result = _false_none_validate(bundle, verifier)
    assert result["gate_status"] == "BLOCKED", result
    assert any(
        "false_none_required_contexts_executed" in item
        for item in result["blocking_reasons"]
    )
    assert any("false_none_landing_context_is_formal" in item for item in result["blocking_reasons"])


def test_false_none_only_draft_inert_landing_context_blocks(tmp_path: Path) -> None:
    bundle = _false_none_repo(tmp_path)
    verifier, _ = _false_none_pair(
        bundle,
        check_names={"baseline", "state-gate", "landing-state-gate-draft-inert"},
    )
    result = _false_none_validate(bundle, verifier)
    assert result["gate_status"] == "BLOCKED", result
    assert any(
        "false_none_required_contexts_executed" in item
        for item in result["blocking_reasons"]
    )
    assert any("false_none_landing_context_is_formal" in item for item in result["blocking_reasons"])


def test_false_none_required_baseline_missing_blocks(tmp_path: Path) -> None:
    bundle = _false_none_repo(tmp_path)
    verifier, _ = _false_none_pair(
        bundle,
        check_names={"state-gate", "landing-state-gate"},
    )
    result = _false_none_validate(bundle, verifier)
    assert result["gate_status"] == "BLOCKED", result
    assert any("false_none_required_contexts_executed" in item for item in result["blocking_reasons"])


def test_false_none_required_state_gate_missing_blocks(tmp_path: Path) -> None:
    bundle = _false_none_repo(tmp_path)
    verifier, _ = _false_none_pair(
        bundle,
        check_names={"baseline", "landing-state-gate"},
    )
    result = _false_none_validate(bundle, verifier)
    assert result["gate_status"] == "BLOCKED", result
    assert any("false_none_required_contexts_executed" in item for item in result["blocking_reasons"])


def test_false_plus_non_none_contradictory_combination_blocks(tmp_path: Path) -> None:
    bundle = _false_none_repo(
        tmp_path,
        contract_extra={"active_pr_binding_mode": "post_draft_pr_exact_remote_number"},
    )
    verifier, _ = _false_none_pair(bundle)
    result = _false_none_validate(bundle, verifier)
    assert result["gate_status"] == "BLOCKED", result
    assert any("landing_policy_mode" in item for item in result["blocking_reasons"])


def test_true_plus_none_contradictory_combination_blocks(tmp_path: Path) -> None:
    bundle = _false_none_repo(
        tmp_path,
        contract_extra={"mainline_merge_intent_required": True},
    )
    verifier, _ = _false_none_pair(bundle)
    result = _false_none_validate(bundle, verifier)
    assert result["gate_status"] == "BLOCKED", result
    assert any("landing_policy_mode" in item for item in result["blocking_reasons"])


def test_legacy_true_bound_normal_merge_still_passes(tmp_path: Path) -> None:
    bundle = _future_repo(tmp_path, schema_version=3, workflow_profile="baseline")
    result = _validate(bundle)
    assert result["gate_status"] == "PASSED", result


def _legacy_repo_no_active_intent(tmp_path: Path) -> dict[str, Any]:
    repo = tmp_path / "legacyrepo"
    repo.mkdir()
    _git(repo, "init", "-b", "main")
    _git(repo, "config", "user.email", "test@example.com")
    _git(repo, "config", "user.name", "Test")
    (repo / "base.txt").write_text("base\n", encoding="utf-8")
    _git(repo, "add", "base.txt")
    _git(repo, "commit", "-m", "base")
    base = _git(repo, "rev-parse", "HEAD")
    _git(repo, "checkout", "-b", "feature")
    decision_path = repo / "project_state" / "decision_packet.md"
    decision_path.parent.mkdir(parents=True)
    contract = {
        "transition_kernel_required": True,
        "mainline_merge_intent_required": True,
        "active_pr_binding_mode": "post_draft_pr_exact_remote_number",
    }
    decision_id = "decision_20260903_legacy_true_bound_v1"
    decision_text = (
        "# Decision Packet\n\n"
        "```json decision_meta\n"
        + json.dumps(
            {
                "schema_version": 1,
                "decision_id": decision_id,
                "round_id": "round_" + decision_id[len("decision_") :],
                "status": "APPROVED",
                "mainline": "engineering_branch",
            },
            separators=(",", ":"),
        )
        + "\n```\n\n"
        "```json decision_contract\n"
        + json.dumps(contract, separators=(",", ":"))
        + "\n```\n"
    )
    decision_path.write_text(decision_text, encoding="utf-8")
    (repo / "feature.txt").write_text("feature\n", encoding="utf-8")
    _git(repo, "add", "project_state/decision_packet.md", "feature.txt")
    _git(repo, "commit", "-m", "legacy feature without active intent")
    head = _git(repo, "rev-parse", "HEAD")
    _git(repo, "checkout", "main")
    _git(repo, "merge", "--no-ff", "feature", "-m", "merge legacy")
    merge = _git(repo, "rev-parse", "HEAD")
    return {
        "repo": repo,
        "state_dir": repo / "project_state",
        "base": base,
        "head": head,
        "merge": merge,
    }


def test_legacy_true_bound_missing_intent_still_blocks(tmp_path: Path) -> None:
    bundle = _legacy_repo_no_active_intent(tmp_path)
    result = validate_future_merge(
        repo_root=bundle["repo"],
        state_dir=bundle["state_dir"],
        attestation={},
        verifier=FakeVerifier(),
        commit_sha=bundle["merge"],
        validation_time=NOW,
    )
    assert result["gate_status"] == "BLOCKED", result
    assert any("merge_intent_present" in item for item in result["blocking_reasons"])


def test_legacy_true_bound_mismatched_intent_still_blocks(tmp_path: Path) -> None:
    bundle = _future_repo(
        tmp_path,
        intent_decision_id="decision_20260801_other_authority_v1",
    )
    result = _validate(bundle)
    assert result["gate_status"] == "BLOCKED", result
    assert any("intent_decision_id" in item for item in result["blocking_reasons"])


def test_false_none_receipt_is_output_only(tmp_path: Path) -> None:
    bundle = _false_none_repo(tmp_path)
    verifier, _ = _false_none_pair(bundle)
    before = _git(bundle["repo"], "rev-parse", "HEAD")
    result = _false_none_validate(bundle, verifier)
    receipt = emit_mainline_integration_receipt(result, emitted_at=NOW)
    after = _git(bundle["repo"], "rev-parse", "HEAD")
    assert result["gate_status"] == "PASSED", result
    assert receipt["receipt_status"] == "EMITTED"
    assert receipt["target_pr"] == "809"
    assert receipt["landing_policy"] == "false_none_owner_landing_authority"
    assert before == after
