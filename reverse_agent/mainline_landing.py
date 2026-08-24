"""Fail-closed mainline landing validation and output-only receipts.

This module separates three lifecycles:

* the frozen Architecture Spine historical invariant;
* normal future exact-head merge intent plus trusted external attestation;
* the exact, non-retroactive PR #60 recovery record.
"""

from __future__ import annotations

import hashlib
import json
import re
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Mapping

from .project_state import extract_markdown_json_block


INTEGRATION_BASELINE_NAME = "architecture_spine_v1.json"
MERGE_INTENT_PATH = "project_state/mainline_merge_intents/active.json"
PR60_RECOVERY_NAME = "pr60.json"
CANONICAL_WORKFLOW_POLICY: dict[str, tuple[str, str]] = {
    "CI": (".github/workflows/ci.yml", "pull_request"),
    "Decision Preflight": (
        ".github/workflows/decision-preflight.yml",
        "pull_request",
    ),
    "State Gate (pull_request)": (
        ".github/workflows/state-gate.yml",
        "pull_request",
    ),
    "State Gate (push)": (".github/workflows/state-gate.yml", "push"),
}

CURRENT_PREMERGE_WORKFLOW_POLICY: dict[str, tuple[str, str]] = {
    "CI": (".github/workflows/ci.yml", "pull_request"),
    "Decision Preflight": (
        ".github/workflows/decision-preflight.yml",
        "pull_request",
    ),
    "State Gate (pull_request)": (
        ".github/workflows/state-gate.yml",
        "pull_request",
    ),
}

CURRENT_POSTMERGE_WORKFLOW_POLICY: dict[str, tuple[str, str]] = {
    "State Gate (push)": (".github/workflows/state-gate.yml", "push"),
}


def canonical_digest(payload: Mapping[str, Any], *, omit: tuple[str, ...] = ()) -> str:
    filtered = {key: value for key, value in payload.items() if key not in omit}
    raw = json.dumps(
        filtered, ensure_ascii=True, sort_keys=True, separators=(",", ":")
    ).encode("utf-8")
    return "sha256:" + hashlib.sha256(raw).hexdigest()


def _check(name: str, passed: bool, detail: str) -> dict[str, str]:
    return {"name": name, "status": "PASS" if passed else "FAIL", "detail": detail}


def _result(
    gate_name: str,
    checks: list[dict[str, str]],
    *,
    extra: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    blocking = [
        f"{item['name']}: {item['detail']}"
        for item in checks
        if item["status"] == "FAIL"
    ]
    result: dict[str, Any] = {
        "schema_version": 1,
        "gate_name": gate_name,
        "gate_status": "PASSED" if not blocking else "BLOCKED",
        "checks": checks,
        "blocking_reasons": blocking,
    }
    if extra:
        result.update(extra)
    return result


def _git(repo_root: Path, *args: str, check: bool = True) -> str:
    completed = subprocess.run(
        ["git", *args],
        cwd=repo_root,
        capture_output=True,
        check=False,
    )
    if check and completed.returncode != 0:
        raise ValueError(f"git_failed:{' '.join(args)}")
    return completed.stdout.decode("utf-8", errors="strict").strip()


def _parents(repo_root: Path, commit_sha: str) -> list[str]:
    raw = _git(repo_root, "rev-list", "--parents", "-n", "1", commit_sha)
    return raw.split()[1:]


def _tree(repo_root: Path, commit_sha: str) -> str:
    return _git(repo_root, "rev-parse", f"{commit_sha}^{{tree}}")


def _blob(repo_root: Path, commit_sha: str, path: str) -> bytes | None:
    completed = subprocess.run(
        ["git", "show", f"{commit_sha}:{path}"],
        cwd=repo_root,
        capture_output=True,
        check=False,
    )
    return completed.stdout if completed.returncode == 0 else None


def _json_blob(repo_root: Path, commit_sha: str, path: str) -> dict[str, Any] | None:
    raw = _blob(repo_root, commit_sha, path)
    if raw is None:
        return None
    payload = json.loads(raw.decode("utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"json_object_required:{path}")
    return payload


def _sha256_blob(repo_root: Path, commit_sha: str, path: str) -> str | None:
    raw = _blob(repo_root, commit_sha, path)
    return None if raw is None else hashlib.sha256(raw).hexdigest()


def _decision_meta_blob(repo_root: Path, commit_sha: str) -> dict[str, Any]:
    """Parse exactly one trusted Decision metadata block from a committed tree."""

    path = "project_state/decision_packet.md"
    raw = _blob(repo_root, commit_sha, path)
    if raw is None:
        raise ValueError(f"missing_decision_artifact:{path}")
    text = raw.decode("utf-8", errors="strict")
    match_count = sum(
        1
        for line in text.splitlines()
        if line.strip().startswith("```")
        and "json" in line.strip()[3:].strip().split()
        and "decision_meta" in line.strip()[3:].strip().split()
    )
    if match_count != 1:
        raise ValueError(f"expected_one_decision_meta:observed={match_count}")
    parsed = extract_markdown_json_block(text, "decision_meta")
    if not parsed.get("found") or parsed.get("parse_error"):
        raise ValueError(f"invalid_decision_meta:{parsed.get('parse_error')}")
    meta = {
        key: value
        for key, value in parsed.items()
        if key not in {"found", "parse_error"}
    }
    decision_id = meta.get("decision_id")
    round_id = meta.get("round_id")
    if (
        meta.get("schema_version") != 1
        or meta.get("status") != "APPROVED"
        or meta.get("mainline") != "engineering_branch"
        or not isinstance(decision_id, str)
        or re.fullmatch(r"decision_[A-Za-z0-9][A-Za-z0-9_.-]{2,190}", decision_id)
        is None
        or not isinstance(round_id, str)
        or re.fullmatch(r"round_[A-Za-z0-9][A-Za-z0-9_.-]{2,191}", round_id)
        is None
    ):
        raise ValueError("invalid_decision_meta_contract")
    return meta


def _sha(value: Any) -> bool:
    return isinstance(value, str) and re.fullmatch(r"[0-9a-f]{40}", value) is not None


def _sha256(value: Any) -> bool:
    return isinstance(value, str) and re.fullmatch(r"(?:sha256:)?[0-9a-f]{64}", value) is not None


def _read_object(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"json_object_required:{path}")
    return payload


def integration_baseline(
    *,
    state_dir: Path,
    repo_root: Path | None = None,
    baseline_name: str = INTEGRATION_BASELINE_NAME,
) -> dict[str, Any]:
    repo_root = repo_root or state_dir.parent
    try:
        receipt = _read_object(state_dir / "integration_baselines" / baseline_name)
        previous = str(receipt.get("previous_main_sha") or "")
        subject = str(receipt.get("subject_head_sha") or "")
        merge = str(receipt.get("merge_commit_sha") or "")
        parents = _parents(repo_root, merge)
        runs = receipt.get("successful_exact_head_runs")
        runs = runs if isinstance(runs, list) else []
        names = [item.get("name") for item in runs if isinstance(item, dict)]
        objects = all(
            subprocess.run(
                ["git", "cat-file", "-e", f"{sha}^{{commit}}"],
                cwd=repo_root,
                capture_output=True,
                check=False,
            ).returncode
            == 0
            for sha in (previous, subject, merge)
        )
        checks = [
            _check("schema_version", receipt.get("schema_version") == 1, f"observed={receipt.get('schema_version')}"),
            _check("frozen_status", receipt.get("status") == "FROZEN_BASELINE", f"status={receipt.get('status')}"),
            _check("git_objects_exist", objects, f"previous={previous} subject={subject} merge={merge}"),
            _check("declared_parent_identity", receipt.get("expected_parent_shas") == [previous, subject], f"declared={receipt.get('expected_parent_shas')}"),
            _check("merge_parent_identity", parents == [previous, subject], f"observed={parents}"),
            _check("tree_identity", _tree(repo_root, merge) == _tree(repo_root, subject) == receipt.get("expected_tree_sha"), f"merge={_tree(repo_root, merge)} subject={_tree(repo_root, subject)}"),
            _check("merge_reachable_from_head", subprocess.run(["git", "merge-base", "--is-ancestor", merge, "HEAD"], cwd=repo_root, capture_output=True, check=False).returncode == 0, f"merge={merge}"),
            _check("exact_head_runs", len(runs) == 4 and all(isinstance(item, dict) and item.get("head_sha") == subject and item.get("conclusion") == "success" for item in runs), f"count={len(runs)}"),
            _check("required_run_names", set(names) == set(CANONICAL_WORKFLOW_POLICY), f"observed={sorted(str(name) for name in names)}"),
        ]
        return _result(
            "integration-baseline",
            checks,
            extra={
                "baseline_id": receipt.get("baseline_id", ""),
                "merge_commit_sha": merge,
                "subject_head_sha": subject,
            },
        )
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        return {
            "schema_version": 1,
            "gate_name": "integration-baseline",
            "gate_status": "BLOCKED",
            "checks": [],
            "blocking_reasons": [f"invalid_baseline_artifact:{exc}"],
        }


def load_merge_intent(repo_root: Path, merge_commit: str) -> tuple[list[str], dict[str, Any] | None]:
    parents = _parents(repo_root, merge_commit)
    if len(parents) != 2:
        return parents, None
    return parents, _json_blob(repo_root, parents[1], MERGE_INTENT_PATH)


def _parse_time(value: str) -> datetime:
    return datetime.fromisoformat(value.replace("Z", "+00:00"))


def _validate_intent(
    intent: Mapping[str, Any],
    *,
    repo_root: Path,
    accepted_head: str,
    source_pr: int,
    locked_base: str,
    now: datetime,
) -> list[dict[str, str]]:
    decision = intent.get("decision_identity")
    decision = decision if isinstance(decision, Mapping) else {}
    required = intent.get("required_workflows")
    required = required if isinstance(required, list) else []
    expiry = str(intent.get("expires_at") or "")
    decision_digest = _sha256_blob(
        repo_root, accepted_head, "project_state/decision_packet.md"
    )
    accepted_decision = _decision_meta_blob(repo_root, accepted_head)
    plan_digest = _sha256_blob(
        repo_root, accepted_head, "project_state/gates/command_plan.json"
    )
    command_plan = _json_blob(
        repo_root, accepted_head, "project_state/gates/command_plan.json"
    )
    command_plan = command_plan if isinstance(command_plan, Mapping) else {}
    try:
        not_expired = bool(expiry) and _parse_time(expiry) > now
    except ValueError:
        not_expired = False
    intent_fields = {
        "schema_version",
        "intent_id",
        "repository",
        "source_pr",
        "locked_base_sha",
        "allowed_merge_method",
        "decision_identity",
        "command_plan_sha256",
        "merge_tree_policy",
        "required_workflows",
        "expires_at",
    }
    schema_version = int(intent.get("schema_version") or 1)
    if schema_version == 1:
        workflow_policy = CANONICAL_WORKFLOW_POLICY
    elif schema_version == 2:
        workflow_policy = CURRENT_PREMERGE_WORKFLOW_POLICY
    else:
        return [
            _check("intent_schema_version", False, f"unsupported_version={schema_version}"),
            _check("intent_fields", False, "unsupported_version"),
            _check("intent_repository", False, "unsupported_version"),
            _check("intent_source_pr", False, "unsupported_version"),
            _check("intent_locked_base", False, "unsupported_version"),
            _check("intent_merge_method", False, "unsupported_version"),
            _check("intent_decision_fields", False, "unsupported_version"),
            _check("intent_decision_id", False, "unsupported_version"),
            _check("intent_decision_digest", False, "unsupported_version"),
            _check("intent_command_plan_identity", False, "unsupported_version"),
            _check("intent_command_plan_digest", False, "unsupported_version"),
            _check("intent_merge_tree_policy", False, "unsupported_version"),
            _check("intent_workflow_policy", False, "unsupported_version"),
            _check("intent_expiry", False, "unsupported_version"),
        ]
    return [
        _check("intent_fields", set(intent) == intent_fields, f"observed={sorted(intent)}"),
        _check("intent_schema_version", schema_version in {1, 2}, f"observed={schema_version}"),
        _check("intent_repository", intent.get("repository") == "dddd2024/reverse-agent", f"observed={intent.get('repository')}"),
        _check("intent_source_pr", intent.get("source_pr") == source_pr, f"observed={intent.get('source_pr')} expected={source_pr}"),
        _check("intent_locked_base", intent.get("locked_base_sha") == locked_base, f"observed={intent.get('locked_base_sha')} expected={locked_base}"),
        _check("intent_merge_method", intent.get("allowed_merge_method") == "merge", f"observed={intent.get('allowed_merge_method')}"),
        _check("intent_decision_fields", set(decision) == {"decision_id", "decision_content_sha256"}, f"observed={sorted(decision)}"),
        _check("intent_decision_id", decision.get("decision_id") == accepted_decision.get("decision_id"), f"observed={decision.get('decision_id')} expected={accepted_decision.get('decision_id')}"),
        _check("intent_decision_digest", _sha256(decision.get("decision_content_sha256")) and decision.get("decision_content_sha256") == decision_digest, f"observed={decision.get('decision_content_sha256')} expected={decision_digest}"),
        _check("intent_command_plan_identity", command_plan.get("decision_id") == accepted_decision.get("decision_id") and command_plan.get("round_id") == accepted_decision.get("round_id"), f"plan={command_plan.get('decision_id')}/{command_plan.get('round_id')} decision={accepted_decision.get('decision_id')}/{accepted_decision.get('round_id')}"),
        _check("intent_command_plan_digest", _sha256(intent.get("command_plan_sha256")) and intent.get("command_plan_sha256") == plan_digest, f"observed={intent.get('command_plan_sha256')} expected={plan_digest}"),
        _check("intent_merge_tree_policy", intent.get("merge_tree_policy") == "equal_to_accepted_head_tree", f"observed={intent.get('merge_tree_policy')}"),
        _check("intent_workflow_policy", required == list(workflow_policy), f"observed={required}"),
        _check("intent_expiry", not_expired, f"expires_at={expiry} now={now.isoformat()}"),
    ]


def _validate_attestation(
    attestation: Mapping[str, Any],
    *,
    verifier: Any,
    intent: Mapping[str, Any],
    accepted_head: str,
    locked_base: str,
    now: datetime,
    merge_commit_sha: str,
) -> list[dict[str, str]]:
    checks: list[dict[str, str]] = []
    source_pr = int(intent.get("source_pr") or 0)
    observations = attestation.get("workflow_observations")
    observations = observations if isinstance(observations, list) else []
    observed_names = [
        item.get("name") for item in observations if isinstance(item, Mapping)
    ]
    run_ids = [
        int(item.get("run_id") or 0) for item in observations if isinstance(item, Mapping)
    ]
    approval = attestation.get("human_r2_approval")
    approval = approval if isinstance(approval, Mapping) else {}
    approval_payload = approval.get("approval_payload")
    approval_payload = (
        approval_payload if isinstance(approval_payload, Mapping) else {}
    )
    try:
        expires = _parse_time(str(attestation.get("expires_at") or ""))
        active_time = expires > now
    except ValueError:
        active_time = False
    remote_comment_id = int(attestation.get("_remote_comment_id") or 0)
    schema_version = int(attestation.get("schema_version") or 1)
    if schema_version == 1:
        workflow_policy = CANONICAL_WORKFLOW_POLICY
        required_observation_count = 4
    elif schema_version == 2:
        workflow_policy = CURRENT_PREMERGE_WORKFLOW_POLICY
        required_observation_count = 3
    else:
        return [
            _check("attestation_schema_version", False, f"unsupported_version={schema_version}"),
            _check("attestation_fields", False, "unsupported_version"),
            _check("attestation_repository", False, "unsupported_version"),
            _check("attestation_source_pr", False, "unsupported_version"),
            _check("attestation_base", False, "unsupported_version"),
            _check("attestation_head", False, "unsupported_version"),
            _check("attestation_method", False, "unsupported_version"),
            _check("attestation_intent_digest", False, "unsupported_version"),
            _check("attestation_content_digest", False, "unsupported_version"),
            _check("attestation_status", False, "unsupported_version"),
            _check("attestation_expiry", False, "unsupported_version"),
            _check("workflow_names", False, "unsupported_version"),
            _check("workflow_run_uniqueness", False, "unsupported_version"),
            _check("workflow_observation_fields", False, "unsupported_version"),
            _check("approval_remote_identity", False, "unsupported_version"),
            _check("approval_fields", False, "unsupported_version"),
            _check("approval_approver", False, "unsupported_version"),
            _check("approval_payload", False, "unsupported_version"),
            _check("approval_content_digest", False, "unsupported_version"),
        ]
    attestation_fields = {
        "schema_version",
        "attestation_id",
        "repository",
        "source_pr",
        "locked_base_sha",
        "accepted_exact_head_sha",
        "allowed_merge_method",
        "intent_digest",
        "workflow_observations",
        "human_r2_approval",
        "authorization_status",
        "expires_at",
        "superseded_by",
        "content_digest",
        "_remote_comment_id",
        "_remote_author",
    }
    runtime_timestamp_fields = {
        "_remote_comment_created_at",
        "_remote_comment_updated_at",
    }
    expected_fields = attestation_fields
    if schema_version == 2:
        expected_fields = attestation_fields | runtime_timestamp_fields
    observed_fields_valid = set(attestation) == expected_fields or (
        schema_version == 1 and set(attestation) == attestation_fields | runtime_timestamp_fields
    )
    observation_fields = {
        "name",
        "run_id",
        "workflow_file",
        "event",
        "run_attempt",
        "head_sha",
        "conclusion",
    }
    checks.extend(
        [
            _check("attestation_fields", observed_fields_valid, f"observed={sorted(attestation)}"),
            _check("attestation_schema_version", schema_version in {1, 2}, f"observed={schema_version}"),
            _check("attestation_repository", attestation.get("repository") == "dddd2024/reverse-agent", f"observed={attestation.get('repository')}"),
            _check("attestation_source_pr", attestation.get("source_pr") == source_pr, f"observed={attestation.get('source_pr')} expected={source_pr}"),
            _check("attestation_base", attestation.get("locked_base_sha") == locked_base, f"observed={attestation.get('locked_base_sha')}"),
            _check("attestation_head", attestation.get("accepted_exact_head_sha") == accepted_head, f"observed={attestation.get('accepted_exact_head_sha')}"),
            _check("attestation_method", attestation.get("allowed_merge_method") == "merge", f"observed={attestation.get('allowed_merge_method')}"),
            _check("attestation_intent_digest", attestation.get("intent_digest") == canonical_digest(intent), f"observed={attestation.get('intent_digest')}"),
            _check("attestation_content_digest", attestation.get("content_digest") == canonical_digest(attestation, omit=("content_digest", "_remote_comment_id", "_remote_author", "_remote_comment_created_at", "_remote_comment_updated_at")), f"observed={attestation.get('content_digest')}"),
            _check("attestation_status", attestation.get("authorization_status") == "active" and not attestation.get("superseded_by"), f"status={attestation.get('authorization_status')} superseded_by={attestation.get('superseded_by')}"),
            _check("attestation_expiry", active_time, f"expires_at={attestation.get('expires_at')}"),
            _check("workflow_names", observed_names == list(workflow_policy), f"observed={observed_names}"),
            _check("workflow_run_uniqueness", len(run_ids) == len(set(run_ids)) == len(workflow_policy), f"run_ids={run_ids}"),
            _check("workflow_observation_fields", len(observations) == required_observation_count and all(isinstance(item, Mapping) and set(item) == observation_fields for item in observations), f"count={len(observations)}"),
            _check("approval_remote_identity", remote_comment_id > 0 and approval.get("approval_object_id") == remote_comment_id and attestation.get("_remote_author") in {"dddd2024"}, f"comment={remote_comment_id} author={attestation.get('_remote_author')}"),
            _check("approval_fields", set(approval) == {"approver", "approval_object_id", "approval_payload", "approval_content_digest"}, f"observed={sorted(approval)}"),
            _check("approval_approver", approval.get("approver") == attestation.get("_remote_author") == "dddd2024", f"observed={approval.get('approver')}"),
            _check("approval_payload", approval_payload == {"repository":"dddd2024/reverse-agent","source_pr":source_pr,"locked_base_sha":locked_base,"accepted_exact_head_sha":accepted_head,"allowed_merge_method":"merge"}, f"observed={approval_payload}"),
            _check("approval_content_digest", approval.get("approval_content_digest") == canonical_digest(approval_payload), f"observed={approval.get('approval_content_digest')}"),
        ]
    )
    verify_kwargs: dict[str, Any] = {
        "pr_number": source_pr,
        "expected_head_sha": accepted_head,
        "expected_base_sha": locked_base,
    }
    if schema_version == 2:
        verify_kwargs.update(
            expected_merge_commit_sha=merge_commit_sha,
            require_merged=True,
        )
    pr = verifier.verify_pr(**verify_kwargs)
    checks.append(_check("remote_pr_binding", bool(pr.get("verified")), str(pr.get("reason") or "verified")))
    if schema_version == 2:
        remote_pr = pr.get("pr") if isinstance(pr.get("pr"), Mapping) else {}
        merged_at = remote_pr.get("merged_at")
        if not isinstance(merged_at, str) or not merged_at:
            checks.append(_check("remote_pr_merged_at", False, "missing"))
            merged_time = None
        else:
            try:
                merged_time = _parse_time(merged_at)
                if merged_time.tzinfo is None:
                    raise ValueError("timezone_required")
            except (TypeError, ValueError) as exc:
                checks.append(_check("remote_pr_merged_at", False, f"invalid:{exc}"))
                merged_time = None
        comment_times: dict[str, datetime] = {}
        for field, check_name in (
            ("_remote_comment_created_at", "attestation_created_before_merge"),
            ("_remote_comment_updated_at", "attestation_updated_before_merge"),
        ):
            value = attestation.get(field)
            if not isinstance(value, str) or not value:
                checks.append(_check(check_name, False, "missing"))
                continue
            try:
                comment_time = _parse_time(value)
                if comment_time.tzinfo is None:
                    raise ValueError("timezone_required")
            except (TypeError, ValueError) as exc:
                checks.append(_check(check_name, False, f"invalid:{exc}"))
                continue
            comment_times[field] = comment_time
            if merged_time is None:
                checks.append(_check(check_name, False, "remote_pr_merged_at_unavailable"))
            else:
                checks.append(
                    _check(
                        check_name,
                        comment_time < merged_time,
                        f"comment={comment_time.isoformat()} merged_at={merged_time.isoformat()}",
                    )
                )
        created_time = comment_times.get("_remote_comment_created_at")
        updated_time = comment_times.get("_remote_comment_updated_at")
        if created_time is not None and updated_time is not None:
            checks.append(
                _check(
                    "attestation_comment_order",
                    created_time <= updated_time,
                    f"created={created_time.isoformat()} updated={updated_time.isoformat()}",
                )
            )
    for index, name in enumerate(workflow_policy):
        if index >= len(observations) or not isinstance(observations[index], Mapping):
            checks.append(_check(f"remote_workflow:{name}", False, "missing"))
            continue
        observation = observations[index]
        expected_file, expected_event = workflow_policy[name]
        locally_bound = (
            observation.get("name") == name
            and observation.get("workflow_file") == expected_file
            and observation.get("event") == expected_event
            and observation.get("head_sha") == accepted_head
            and observation.get("conclusion") == "success"
            and int(observation.get("run_attempt") or 0) >= 1
        )
        verified = verifier.verify_workflow_run(
            run_id=int(observation.get("run_id") or 0),
            expected_head_sha=accepted_head,
            expected_workflow_file=expected_file,
            expected_event=expected_event,
            expected_run_attempt=int(observation.get("run_attempt") or 0),
        )
        checks.append(
            _check(
                f"remote_workflow:{name}",
                locally_bound and bool(verified.get("verified")),
                str(verified.get("reason") or "verified"),
            )
        )
    return checks


def validate_future_merge(
    *,
    repo_root: Path,
    state_dir: Path,
    attestation: Mapping[str, Any],
    verifier: Any,
    commit_sha: str = "HEAD",
    validation_time: datetime | None = None,
) -> dict[str, Any]:
    now = validation_time or datetime.now(timezone.utc)
    try:
        merge = _git(repo_root, "rev-parse", commit_sha)
        parents, intent = load_merge_intent(repo_root, merge)
        checks = [
            _check("merge_structure", len(parents) == 2, f"parents={parents}")
        ]
        if len(parents) != 2:
            return _result("mainline-merge-validation", checks, extra={"merge_commit_sha": merge})
        first_parent, second_parent = parents
        locked_base = str(attestation.get("locked_base_sha") or "")
        accepted_head = str(attestation.get("accepted_exact_head_sha") or "")
        checks.extend(
            [
                _check("first_parent_identity", first_parent == locked_base, f"observed={first_parent} expected={locked_base}"),
                _check("second_parent_identity", second_parent == accepted_head, f"observed={second_parent} expected={accepted_head}"),
                _check("merge_tree_policy", _tree(repo_root, merge) == _tree(repo_root, second_parent), f"merge={_tree(repo_root, merge)} accepted={_tree(repo_root, second_parent)}"),
            ]
        )
        if intent is None:
            checks.append(_check("merge_intent_present", False, f"path={MERGE_INTENT_PATH}"))
            return _result(
                "mainline-merge-validation",
                checks,
                extra={
                    "merge_commit_sha": merge,
                    "first_parent_sha": first_parent,
                    "second_parent_sha": second_parent,
                },
            )
        checks.append(_check("merge_intent_present", True, f"path={MERGE_INTENT_PATH}"))
        checks.extend(
            _validate_intent(
                intent,
                repo_root=repo_root,
                accepted_head=second_parent,
                source_pr=int(attestation.get("source_pr") or 0),
                locked_base=locked_base,
                now=now,
            )
        )
        checks.extend(
            _validate_attestation(
                attestation,
                verifier=verifier,
                intent=intent,
                accepted_head=second_parent,
                locked_base=first_parent,
                now=now,
                merge_commit_sha=merge,
            )
        )
        return _result(
            "mainline-merge-validation",
            checks,
            extra={
                "merge_commit_sha": merge,
                "first_parent_sha": first_parent,
                "second_parent_sha": second_parent,
                "intent_id": intent.get("intent_id", ""),
                "attestation_id": attestation.get("attestation_id", ""),
            },
        )
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        return {
            "schema_version": 1,
            "gate_name": "mainline-merge-validation",
            "gate_status": "BLOCKED",
            "checks": [],
            "blocking_reasons": [f"invalid_merge_evidence:{exc}"],
        }


def validate_pr60_recovery(
    *,
    repo_root: Path,
    state_dir: Path,
    verifier: Any,
    recovery_name: str = PR60_RECOVERY_NAME,
) -> dict[str, Any]:
    try:
        record = _read_object(state_dir / "mainline_recoveries" / recovery_name)
        merge = str(record.get("merge_commit_sha") or "")
        base = str(record.get("locked_base_sha") or "")
        head = str(record.get("accepted_head_sha") or "")
        parents = _parents(repo_root, merge)
        checks = [
            _check("recovery_fields", set(record) == {
                "schema_version", "recovery_id", "status", "non_retroactive",
                "repository", "source_pr", "accepted_head_sha", "locked_base_sha",
                "merge_commit_sha", "expected_parent_shas", "merge_method",
                "authorization_issue", "authorization_comment_id",
                "authorization_comment_body_sha256", "authorization_branch",
                "authorization_head_sha", "authorization_decision_id",
                "authorization_decision_sha256",
                "authorization_command_plan_sha256", "accepted_audit_head_sha",
                "workflow_observations", "allowed_approvers"
            }, f"observed={sorted(record)}"),
            _check("recovery_schema_version", record.get("schema_version") == 1, f"observed={record.get('schema_version')}"),
            _check("recovery_status", record.get("status") == "EXACT_HISTORICAL_RECOVERY", f"status={record.get('status')}"),
            _check("non_retroactive", record.get("non_retroactive") is True, f"observed={record.get('non_retroactive')}"),
            _check("exact_repository", record.get("repository") == "dddd2024/reverse-agent", f"observed={record.get('repository')}"),
            _check("exact_pr", record.get("source_pr") == 60, f"observed={record.get('source_pr')}"),
            _check("exact_merge", merge == "68026521710c50fa9a70f3851472941605d9ead1", f"observed={merge}"),
            _check("ordered_parents", parents == [base, head] == record.get("expected_parent_shas"), f"observed={parents}"),
            _check("merge_method", record.get("merge_method") == "merge", f"observed={record.get('merge_method')}"),
            _check("accepted_audit_head", record.get("accepted_audit_head_sha") == head, f"observed={record.get('accepted_audit_head_sha')}"),
            _check("authorization_identity", record.get("authorization_issue") == 63 and record.get("authorization_comment_id") == 5099339493 and record.get("authorization_branch") == "codex/pr60-final-merge-authorization-v1" and record.get("authorization_head_sha") == "7e2ef47b22d742fafc5a5e15808792cb62a2328a" and record.get("authorization_decision_id") == "decision_20260727_pr60_final_merge_authorization_v1", f"head={record.get('authorization_head_sha')}"),
            _check("authorization_digests", _sha256(record.get("authorization_comment_body_sha256")) and _sha256(record.get("authorization_decision_sha256")) and _sha256(record.get("authorization_command_plan_sha256")), "sha256 fields"),
            _check("allowed_approvers", record.get("allowed_approvers") == ["dddd2024"], f"observed={record.get('allowed_approvers')}"),
        ]
        pr = verifier.verify_pr(
            pr_number=60,
            expected_head_sha=head,
            expected_base_sha=base,
            expected_merge_commit_sha=merge,
            require_merged=True,
        )
        checks.append(_check("remote_pr60_binding", bool(pr.get("verified")), str(pr.get("reason") or "verified")))
        observations = record.get("workflow_observations")
        observations = observations if isinstance(observations, list) else []
        names = [item.get("name") for item in observations if isinstance(item, Mapping)]
        ids = [int(item.get("run_id") or 0) for item in observations if isinstance(item, Mapping)]
        checks.extend(
            [
                _check("workflow_names", names == list(CANONICAL_WORKFLOW_POLICY), f"observed={names}"),
                _check("workflow_run_uniqueness", len(ids) == len(set(ids)) == 4, f"run_ids={ids}"),
            ]
        )
        for index, name in enumerate(CANONICAL_WORKFLOW_POLICY):
            observation = observations[index] if index < len(observations) else {}
            expected_file, expected_event = CANONICAL_WORKFLOW_POLICY[name]
            verified = verifier.verify_workflow_run(
                run_id=int(observation.get("run_id") or 0),
                expected_head_sha=head,
                expected_workflow_file=expected_file,
                expected_event=expected_event,
                expected_run_attempt=int(observation.get("run_attempt") or 0),
            )
            local = (
                observation.get("name") == name
                and observation.get("workflow_file") == expected_file
                and observation.get("event") == expected_event
                and observation.get("head_sha") == head
                and observation.get("conclusion") == "success"
                and int(observation.get("run_attempt") or 0) >= 1
            )
            checks.append(_check(f"remote_workflow:{name}", local and bool(verified.get("verified")), str(verified.get("reason") or "verified")))
        comment = verifier.verify_issue_comment(
            comment_id=int(record.get("authorization_comment_id") or 0),
            expected_issue=int(record.get("authorization_issue") or 0),
            allowed_authors=tuple(record.get("allowed_approvers") or ()),
            expected_body_sha256=str(record.get("authorization_comment_body_sha256") or ""),
            required_text=(
                record.get("authorization_decision_id", ""),
                record.get("authorization_head_sha", ""),
                head,
                base,
                record.get("authorization_command_plan_sha256", ""),
                "FINAL_MERGE_AUTHORIZATION_READY_FOR_OWNER_ACTION",
            ),
        )
        checks.append(_check("remote_authorization_comment", bool(comment.get("verified")), str(comment.get("reason") or "verified")))
        for label, path, digest in (
            ("decision", "project_state/decision_packet.md", record.get("authorization_decision_sha256", "")),
            ("command_plan", "project_state/gates/command_plan.json", record.get("authorization_command_plan_sha256", "")),
        ):
            verified = verifier.verify_ref_file_sha256(
                ref=str(record.get("authorization_head_sha") or ""),
                path=path,
                expected_sha256=str(digest),
            )
            checks.append(_check(f"remote_authorization_{label}", bool(verified.get("verified")), str(verified.get("reason") or "verified")))
        return _result(
            "pr60-historical-recovery",
            checks,
            extra={
                "recovery_id": record.get("recovery_id", ""),
                "merge_commit_sha": merge,
                "first_parent_sha": base,
                "second_parent_sha": head,
            },
        )
    except (OSError, ValueError, json.JSONDecodeError, TypeError) as exc:
        return {
            "schema_version": 1,
            "gate_name": "pr60-historical-recovery",
            "gate_status": "BLOCKED",
            "checks": [],
            "blocking_reasons": [f"invalid_recovery_evidence:{exc}"],
        }


def emit_mainline_integration_receipt(
    validation: Mapping[str, Any],
    *,
    emitted_at: datetime | None = None,
) -> dict[str, Any]:
    """Build an output-only receipt without creating or requiring a Git commit."""

    now = emitted_at or datetime.now(timezone.utc)
    merge = str(validation.get("merge_commit_sha") or "")
    status = str(validation.get("gate_status") or "BLOCKED")
    return {
        "schema_version": 1,
        "receipt_id": f"mainline_{merge[:12]}",
        "receipt_status": "EMITTED" if status == "PASSED" else "BLOCKED",
        "validation_status": status,
        "merge_commit_sha": merge,
        "first_parent_sha": str(validation.get("first_parent_sha") or ""),
        "second_parent_sha": str(validation.get("second_parent_sha") or ""),
        "intent_id": str(validation.get("intent_id") or ""),
        "attestation_id": str(validation.get("attestation_id") or ""),
        "blocking_reasons": list(validation.get("blocking_reasons") or []),
        "emitted_at": now.astimezone(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
    }
