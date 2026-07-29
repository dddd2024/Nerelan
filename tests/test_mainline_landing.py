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
    _validate_intent,
    canonical_digest,
    emit_mainline_integration_receipt,
    validate_future_merge,
    validate_pr60_recovery,
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
    def __init__(self, *, fail: str = "") -> None:
        self.fail = fail

    def verify_pr(self, **_: Any) -> dict[str, Any]:
        return {"verified": self.fail != "pr", "reason": self.fail}

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
        + "\n```\n"
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
    intent = {
        "schema_version": 1,
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
        "required_workflows": list(CANONICAL_WORKFLOW_POLICY),
        "expires_at": "2026-08-28T00:00:00Z",
    }
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
        CANONICAL_WORKFLOW_POLICY.items(), 1
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
        "schema_version": 1,
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
    attestation["content_digest"] = canonical_digest(
        attestation,
        omit=("content_digest", "_remote_comment_id", "_remote_author"),
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
        omit=("content_digest", "_remote_comment_id", "_remote_author"),
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


def test_committed_pr67_intent_binds_exact_v5_authority() -> None:
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

    assert (
        intent["decision_identity"]["decision_id"]
        == decision["decision_id"]
        == "decision_20260729_pr67_final_intent_rebind_v5"
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
        source_pr=67,
        locked_base="68026521710c50fa9a70f3851472941605d9ead1",
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
def test_committed_pr67_intent_rejects_stale_v3_authority(
    field: str,
    stale_value: str,
    expected_failure: str,
) -> None:
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
        source_pr=67,
        locked_base="68026521710c50fa9a70f3851472941605d9ead1",
        now=NOW,
    )
    observed = {check["name"]: check["status"] for check in checks}
    assert observed[expected_failure] == "FAIL"


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


def test_production_pre_merge_simulation(tmp_path: Path) -> None:
    repo = tmp_path / "simulation"
    subprocess.run(
        ["git", "clone", "--no-hardlinks", str(REPO_ROOT), str(repo)],
        check=True,
        capture_output=True,
        text=True,
    )
    head = _git(repo, "rev-parse", "HEAD")
    base = "68026521710c50fa9a70f3851472941605d9ead1"
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
    approval_payload = {
        "repository": "dddd2024/reverse-agent",
        "source_pr": 67,
        "locked_base_sha": base,
        "accepted_exact_head_sha": head,
        "allowed_merge_method": "merge",
    }
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
            CANONICAL_WORKFLOW_POLICY.items(),
            1,
        )
    ]
    attestation = {
        "schema_version": 1,
        "attestation_id": "issue71_local_simulation_only",
        "repository": "dddd2024/reverse-agent",
        "source_pr": 67,
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
        "expires_at": "2026-08-19T23:59:59Z",
        "superseded_by": None,
        "_remote_comment_id": 71001,
        "_remote_author": "dddd2024",
    }
    attestation["content_digest"] = canonical_digest(
        attestation,
        omit=("content_digest", "_remote_comment_id", "_remote_author"),
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
