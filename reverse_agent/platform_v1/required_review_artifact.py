"""Opt-in host-enforced review artifact contract, independent of model exit code.

The report is a deliverable, not an independent PR verdict. A report with
WITHHELD/REJECT is evidence of a non-accepted review; no task success is claimed.
No model-authored text can modify this preapproved contract.
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
import re
from typing import Any

from .run_store import TaskStoreError

CATEGORY = "RequiredReviewArtifactContract"
VERSION = 1
_SHA = re.compile(r"[0-9a-f]{40}\Z")
_REVIEW = re.compile(r"(?m)^Nerelan-Review: (ACCEPT|REJECT|WITHHELD) ([0-9a-f]{40})\s*$")
_SAFE_PATH = re.compile(r"[A-Za-z0-9_.\-/]{1,180}\Z")


def normalize_required_artifacts(raw: Any) -> tuple[dict[str, str], ...]:
    if not isinstance(raw, (list, tuple)) or len(raw) > 2:
        raise TaskStoreError("required_artifact_contract_invalid")
    result = []
    paths = set()
    for item in raw:
        if not isinstance(item, dict) or set(item) != {"path", "kind", "expected_sha"}:
            raise TaskStoreError("required_artifact_fields_invalid")
        path, kind, sha = item["path"], item["kind"], item["expected_sha"]
        if (not isinstance(path, str) or not _SAFE_PATH.fullmatch(path)
                or not path.startswith("review_evidence/")
                or any(part in ("", ".", "..") for part in path.split("/"))
                or not path.endswith(".md") or path in paths):
            raise TaskStoreError("required_artifact_path_invalid")
        if kind != "review_report" or not isinstance(sha, str) or not _SHA.fullmatch(sha):
            raise TaskStoreError("required_artifact_identity_invalid")
        paths.add(path)
        result.append({"path": path, "kind": kind, "expected_sha": sha})
    return tuple(result)


def _serialize(obj: dict[str, Any]) -> str:
    return json.dumps(obj, sort_keys=True, separators=(",", ":"), ensure_ascii=True)


def _digest(obj: dict[str, Any]) -> str:
    return hashlib.sha256(_serialize(obj).encode("utf-8")).hexdigest()


def freeze_required_artifacts(store: Any, task: Any, *, goal: Any, plan_task: Any) -> None:
    files = normalize_required_artifacts(plan_task.required_artifacts)
    if not files:
        return
    contract = {"version": VERSION, "task_id": task.id, "goal_id": goal.id,
                "goal_revision": goal.revision, "files": list(files)}
    old = load_required_artifacts(store.get_task(task.id))
    if old is not None:
        if old != contract:
            raise TaskStoreError("required_artifact_contract_conflict")
        return
    token = _digest(contract)
    store.add_evidence(task.id, category=CATEGORY, label="planned_review_deliverables",
                       value=token, status="APPROVED",
                       detail=_serialize(contract), raw_json_digest=token)


def load_required_artifacts(task: Any) -> dict[str, Any] | None:
    refs = [r for r in task.evidence_refs if r.get("category") == CATEGORY]
    if not refs:
        return None
    if len(refs) != 1:
        raise TaskStoreError("required_artifact_contract_ambiguous")
    row = refs[0]
    try:
        contract = json.loads(row["detail"])
        valid = (
            isinstance(contract, dict)
            and set(contract) == {"version", "task_id", "goal_id", "goal_revision", "files"}
            and contract["version"] == VERSION
            and contract["task_id"] == task.id
            and isinstance(contract["goal_id"], str) and bool(contract["goal_id"])
            and type(contract["goal_revision"]) is int and contract["goal_revision"] > 0
            and isinstance(contract["files"], list) and bool(contract["files"])
            and list(normalize_required_artifacts(contract["files"])) == contract["files"]
            and row["value"] == row["raw_json_digest"] == _digest(contract)
            and row["status"] == "APPROVED"
        )
    except (ValueError, KeyError, TypeError, TaskStoreError):
        valid = False
    if not valid:
        raise TaskStoreError("required_artifact_contract_tampered")
    return contract


def validate_required_artifacts(task: Any, worktree: str | Path) -> tuple[bool, str]:
    """Check actual bounded worktree bytes; does not trust agent narrative."""
    contract = load_required_artifacts(task)
    if contract is None:
        return True, "not_required"
    try:
        root = Path(worktree).resolve(strict=True)
        if not root.is_dir():
            return False, "artifact_worktree_missing"
        for spec in contract["files"]:
            candidate = root.joinpath(*spec["path"].split("/"))
            if any(part.is_symlink() for part in (candidate, *candidate.parents) if part != root):
                return False, "artifact_symlink_rejected"
            candidate = candidate.resolve(strict=True)
            if not candidate.is_relative_to(root) or not candidate.is_file():
                return False, "artifact_outside_worktree"
            size = candidate.stat().st_size
            if not 40 <= size <= 128 * 1024:
                return False, "artifact_empty_or_oversized"
            content = candidate.read_text(encoding="utf-8", errors="strict")
            matches = _REVIEW.findall(content)
            if len(matches) != 1:
                return False, "review_verdict_missing_or_ambiguous"
            verdict, sha = matches[0]
            if sha != spec["expected_sha"]:
                return False, "review_exact_sha_mismatch"
            if verdict != "ACCEPT":
                return False, f"review_verdict_{verdict.lower()}"
    except (OSError, UnicodeError, ValueError, RuntimeError):
        return False, "required_artifact_missing_or_invalid"
    return True, "required_review_artifact_present"
