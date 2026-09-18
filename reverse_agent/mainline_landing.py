"""Fail-closed mainline landing validation and output-only receipts.

This module separates three lifecycles:

* the frozen Architecture Spine historical invariant;
* normal future exact-head merge intent plus trusted external attestation;
* the exact, non-retroactive PR #60 recovery record.

Since Issue #156 post-merge cutover the current-main validator is also
policy-aware: a committed false/none Decision
(``mainline_merge_intent_required=false`` + ``active_pr_binding_mode=none``)
is validated against a fresh pre-merge Owner landing authority instead of the
historical ``project_state/mainline_merge_intents/active.json``.
"""

from __future__ import annotations

import fnmatch
import hashlib
import json
import re
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Mapping

from .github_remote_verifier import GitHubEvidenceError
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

# Production-owned trusted pre-merge workflow profiles (Issue #345).
# Every profile is a superset of the generic three-workflow baseline; a
# feature branch selects a profile by name but can never weaken, remove,
# or invent one.  ``State Gate (push)`` stays post-merge-only in every
# profile and therefore never appears here.
TRUSTED_PREMERGE_WORKFLOW_PROFILES: dict[str, dict[str, tuple[str, str]]] = {
    "baseline": {
        "CI": (".github/workflows/ci.yml", "pull_request"),
        "Decision Preflight": (
            ".github/workflows/decision-preflight.yml",
            "pull_request",
        ),
        "State Gate (pull_request)": (
            ".github/workflows/state-gate.yml",
            "pull_request",
        ),
    },
    "browser_r3": {
        "CI": (".github/workflows/ci.yml", "pull_request"),
        "Decision Preflight": (
            ".github/workflows/decision-preflight.yml",
            "pull_request",
        ),
        "State Gate (pull_request)": (
            ".github/workflows/state-gate.yml",
            "pull_request",
        ),
        "Frontend Playwright": (
            ".github/workflows/frontend-playwright.yml",
            "pull_request",
        ),
        "Model Access": (".github/workflows/model-access.yml", "pull_request"),
    },
}

# Owner landing merge attestation for the false/none post-merge authority.
OWNER_LANDING_ATTESTATION_MARKER = "OWNER_LANDING_MERGE_ATTESTATION"
OWNER_LANDING_ATTESTATION_BLOCK = "owner_landing_merge_attestation"
FALSE_NONE_REQUIRED_CONTEXTS: tuple[str, ...] = (
    "baseline",
    "state-gate",
    "landing-state-gate",
)
FALSE_NONE_ALLOWED_OWNERS: tuple[str, ...] = ("dddd2024",)
_FALSE_NONE_AUTHORITY_WORKFLOW_POLICY: dict[str, tuple[str, str]] = {
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
OWNER_LANDING_RUNTIME_FIELDS: tuple[str, ...] = (
    "_remote_comment_id",
    "_remote_author",
    "_remote_comment_created_at",
    "_remote_comment_updated_at",
    "_remote_comment_body",
)
SIGNED_BRANCH_BINDING_MODE = "post_draft_pr_exact_remote_number"
CUTOVER_NONE_BINDING_MODE = "none"

# Issue #721: safe non-overlap Owner landing base refresh authority.
BASE_REFRESH_ADMISSIBLE = "BASE_REFRESH_ADMISSIBLE"
BASE_REFRESH_BLOCKED_TARGET_OVERLAP = "BASE_REFRESH_BLOCKED_TARGET_OVERLAP"
BASE_REFRESH_BLOCKED_AUTHORITY_DRIFT = "BASE_REFRESH_BLOCKED_AUTHORITY_DRIFT"
BASE_REFRESH_BLOCKED_DEPENDENCY_DRIFT = "BASE_REFRESH_BLOCKED_DEPENDENCY_DRIFT"
BASE_REFRESH_BLOCKED_ANCESTRY = "BASE_REFRESH_BLOCKED_ANCESTRY"
BASE_REFRESH_BLOCKED_TARGET_HEAD_DRIFT = "BASE_REFRESH_BLOCKED_TARGET_HEAD_DRIFT"
BASE_REFRESH_BLOCKED_DECISION_DRIFT = "BASE_REFRESH_BLOCKED_DECISION_DRIFT"
BASE_REFRESH_BLOCKED_MAIN_REDRIFT = "BASE_REFRESH_BLOCKED_MAIN_REDRIFT"
BASE_REFRESH_BLOCKED_MERGE_CONFLICT = "BASE_REFRESH_BLOCKED_MERGE_CONFLICT"
BASE_REFRESH_BLOCKED_MERGE_TREE_MISMATCH = (
    "BASE_REFRESH_BLOCKED_MERGE_TREE_MISMATCH"
)
BASE_REFRESH_BLOCKED_OBJECT_INVALID = "BASE_REFRESH_BLOCKED_OBJECT_INVALID"
BASE_REFRESH_BLOCKED_SCHEMA = "BASE_REFRESH_BLOCKED_SCHEMA"

# Paths that grant or move authority.  A non-overlap refresh may never land
# main-side drift in these locations, because that would rewrite the authority
# surface the Owner reviewed.
AUTHORITY_SENSITIVE_PATH_PREFIXES: tuple[str, ...] = (
    ".github/",
    "project_state/",
    "reverse_agent/control_plane/",
)
AUTHORITY_SENSITIVE_PATH_EXACT: frozenset[str] = frozenset(
    {
        "agents.md",
        "reverse_agent/mainline_landing.py",
        "reverse_agent/project_gate.py",
        "reverse_agent/github_remote_verifier.py",
    }
)

# Dependency and lockfile manifests are blocked by exact basename first and
# then by deterministic case-sensitive basename globs.  Matching is performed
# on the basename only, so nested and root variants are treated identically.
# Workflow YAML is deliberately never consulted for dependency inference.
DEPENDENCY_MANIFEST_BASENAMES: frozenset[str] = frozenset(
    {
        "pyproject.toml",
        "requirements.txt",
        "uv.lock",
        "poetry.lock",
        "pipfile",
        "pipfile.lock",
        "package.json",
        "package-lock.json",
        "pnpm-lock.yaml",
        "yarn.lock",
        "cargo.toml",
        "cargo.lock",
    }
)
DEPENDENCY_MANIFEST_BASENAME_GLOBS: tuple[str, ...] = (
    "requirements*.txt",
    "requirements-*.txt",
)

# The complete refresh authority block; every field is required together and a
# partial block is rejected as an unknown-field attestation.
BASE_REFRESH_AUTHORITY_FIELDS: frozenset[str] = frozenset(
    {
        "refresh_authority_original_locked_base_sha",
        "refresh_authority_refreshed_base_sha",
        "refresh_authority_accepted_target_head_sha",
        "refresh_authority_expected_merge_tree_sha",
        "refresh_authority_decision_content_sha256",
        "refresh_authority_owner_exact_head_review_sha",
        "refresh_authority_sidecar_pr",
        "refresh_authority_sidecar_base_sha",
        "refresh_authority_allowed_merge_method",
        "refresh_authority_expected_head_protection_required",
    }
)


def resolve_premerge_workflow_profile(profile_name: Any) -> dict[str, tuple[str, str]]:
    """Resolve a bounded trusted pre-merge workflow profile by exact name."""

    if (
        not isinstance(profile_name, str)
        or profile_name not in TRUSTED_PREMERGE_WORKFLOW_PROFILES
    ):
        raise ValueError(f"unknown_workflow_profile:{profile_name!r}")
    return TRUSTED_PREMERGE_WORKFLOW_PROFILES[profile_name]


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


def _normalize_repo_path(path: str) -> str:
    value = path.strip()
    if value.startswith("./"):
        value = value[2:]
    if value.startswith("/"):
        value = value[1:]
    return value.strip("/")


def _changed_paths(repo_root: Path, base: str, head: str) -> set[str] | None:
    """Machine-computed changed-path set for ``base..head``.

    ``git diff --name-only -z`` is used so NUL separators keep the result
    deterministic for every path Git can quote.  Rename detection is
    deliberately not requested: a rename still surfaces both sides as
    authority-sensitive churn.
    """

    completed = subprocess.run(
        ["git", "diff", "--name-only", "-z", base, head],
        cwd=repo_root,
        capture_output=True,
        check=False,
    )
    if completed.returncode != 0:
        return None
    paths: set[str] = set()
    for raw in completed.stdout.split(b"\x00"):
        if not raw:
            continue
        try:
            decoded = raw.decode("utf-8")
        except UnicodeDecodeError:
            return None
        normalized = _normalize_repo_path(decoded)
        if normalized:
            paths.add(normalized)
    return paths


def _is_commit_object(repo_root: Path, sha: str) -> bool:
    """Require an exact 40-hex commit object, rejecting abbreviated refs."""

    if not isinstance(sha, str) or re.fullmatch(r"[0-9a-f]{40}", sha) is None:
        return False
    completed = subprocess.run(
        ["git", "cat-file", "-e", f"{sha}^{{commit}}"],
        cwd=repo_root,
        capture_output=True,
        check=False,
    )
    return completed.returncode == 0


def _is_commit_ancestor(repo_root: Path, ancestor: str, descendant: str) -> bool:
    completed = subprocess.run(
        ["git", "merge-base", "--is-ancestor", ancestor, descendant],
        cwd=repo_root,
        capture_output=True,
        check=False,
    )
    return completed.returncode == 0


def _merge_tree_sha(repo_root: Path, left: str, right: str) -> str | None:
    """Write-tree merge of two commits; ``None`` means conflict or malformed.

    A nonzero exit is the real merge-conflict signal.  A zero exit still has
    to be confirmed against a 40-hex tree id on the first line, so an empty or
    truncated stdout cannot be mistaken for a tree.
    """

    completed = subprocess.run(
        ["git", "merge-tree", "--write-tree", left, right],
        cwd=repo_root,
        capture_output=True,
        check=False,
    )
    if completed.returncode != 0:
        return None
    raw = completed.stdout.decode("utf-8", errors="strict").strip()
    first_line = raw.splitlines()[0] if raw else ""
    return first_line if re.fullmatch(r"[0-9a-f]{40}", first_line) else None


def _is_authority_sensitive_path(path: str) -> bool:
    normalized = _normalize_repo_path(path)
    if not normalized:
        return False
    lowered = normalized.lower()
    if lowered in AUTHORITY_SENSITIVE_PATH_EXACT:
        return True
    return any(
        lowered.startswith(prefix) for prefix in AUTHORITY_SENSITIVE_PATH_PREFIXES
    )


def _is_dependency_manifest_path(path: str) -> bool:
    """Block dependency manifests and lockfiles by basename and basename glob.

    Only the basename is consulted, so ``requirements-dev.txt`` and
    ``frontend/requirements-dev.txt`` are equivalent.  ``fnmatchcase`` keeps
    the glob semantics deterministic and case-sensitive after lowercasing.
    """

    normalized = _normalize_repo_path(path)
    if not normalized:
        return False
    basename = normalized.rsplit("/", 1)[-1].lower()
    if basename in DEPENDENCY_MANIFEST_BASENAMES:
        return True
    return any(
        fnmatch.fnmatchcase(basename, pattern)
        for pattern in DEPENDENCY_MANIFEST_BASENAME_GLOBS
    )


def _extract_base_refresh_authority(
    attestation: Mapping[str, Any],
) -> dict[str, Any] | None:
    """Return the refresh authority block, ``None`` when none is present."""

    present = set(attestation) & BASE_REFRESH_AUTHORITY_FIELDS
    if not present:
        return None
    authority: dict[str, Any] = {"source_pr": attestation.get("source_pr")}
    for field in sorted(BASE_REFRESH_AUTHORITY_FIELDS):
        authority[field] = attestation.get(field)
    return authority


def _refresh_locked_base_ok(
    attestation: Mapping[str, Any], *, first_parent: str
) -> bool:
    """Strict locked-base equality, relaxed only by a full refresh authority.

    Without a refresh authority this is byte-for-byte the legacy rule
    ``locked_base_sha == first_parent``.  With one, the attestation binds the
    *original* locked base and the landed first parent must be the refreshed
    base the authority named.
    """

    original = str(
        attestation.get("refresh_authority_original_locked_base_sha") or ""
    )
    refreshed = str(attestation.get("refresh_authority_refreshed_base_sha") or "")
    if original and refreshed:
        return (
            attestation.get("locked_base_sha") == original
            and refreshed == first_parent
        )
    return attestation.get("locked_base_sha") == first_parent


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


def _decision_contract_profile(repo_root: Path, commit_sha: str) -> Any:
    """Read the Decision-declared workflow_profile from a committed Decision contract.

    Returns ``None`` when the committed Decision contract predates the
    scope-aware profile policy and declares no ``workflow_profile``; a v3
    intent must never match such a Decision.
    """

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
        and "decision_contract" in line.strip()[3:].strip().split()
    )
    if match_count != 1:
        raise ValueError(f"expected_one_decision_contract:observed={match_count}")
    parsed = extract_markdown_json_block(text, "decision_contract")
    if not parsed.get("found") or parsed.get("parse_error"):
        raise ValueError(f"invalid_decision_contract:{parsed.get('parse_error')}")
    contract = {
        key: value
        for key, value in parsed.items()
        if key not in {"found", "parse_error"}
    }
    return contract.get("workflow_profile")


def _sha(value: Any) -> bool:
    return isinstance(value, str) and re.fullmatch(r"[0-9a-f]{40}", value) is not None


def _sha256(value: Any) -> bool:
    return isinstance(value, str) and re.fullmatch(r"(?:sha256:)?[0-9a-f]{64}", value) is not None


def owner_landing_content_digest(payload: Mapping[str, Any]) -> str:
    """Canonical digest over an owner landing attestation without runtime fields."""

    return canonical_digest(
        payload,
        omit=("content_digest",) + OWNER_LANDING_RUNTIME_FIELDS,
    )


def _decision_contract_fields(repo_root: Path, commit_sha: str) -> dict[str, Any]:
    """Return the committed ``decision_contract`` block, ``{}`` when absent.

    Routing is conservative: an absent or malformed contract must take the
    legacy intent-required path rather than silently choosing the cutover path.
    """

    path = "project_state/decision_packet.md"
    raw = _blob(repo_root, commit_sha, path)
    if raw is None:
        return {}
    text = raw.decode("utf-8", errors="strict")
    match_count = sum(
        1
        for line in text.splitlines()
        if line.strip().startswith("```")
        and "json" in line.strip()[3:].strip().split()
        and "decision_contract" in line.strip()[3:].strip().split()
    )
    if match_count != 1:
        return {}
    parsed = extract_markdown_json_block(text, "decision_contract")
    if not parsed.get("found") or parsed.get("parse_error"):
        return {}
    return {
        key: value
        for key, value in parsed.items()
        if key not in {"found", "parse_error"}
    }


def _post_merge_landing_policy(
    repo_root: Path, commit_sha: str
) -> tuple[str, dict[str, Any]]:
    """Classify the committed second-parent Decision post-merge policy."""

    contract = _decision_contract_fields(repo_root, commit_sha)
    intent_required = contract.get("mainline_merge_intent_required", True) is not False
    binding_mode = contract.get("active_pr_binding_mode")
    if binding_mode is None:
        mode = "cutover" if not intent_required else "legacy"
    elif binding_mode == CUTOVER_NONE_BINDING_MODE:
        mode = "cutover" if not intent_required else "incoherent"
    elif binding_mode == SIGNED_BRANCH_BINDING_MODE:
        mode = "legacy" if intent_required else "incoherent"
    else:
        mode = "incoherent"
    return mode, contract


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
    intent_profile = intent.get("workflow_profile")
    if schema_version == 1:
        workflow_policy = CANONICAL_WORKFLOW_POLICY
    elif schema_version == 2:
        workflow_policy = CURRENT_PREMERGE_WORKFLOW_POLICY
    elif schema_version == 3:
        try:
            workflow_policy = resolve_premerge_workflow_profile(intent_profile)
        except ValueError:
            workflow_policy = {}
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
    if schema_version == 3:
        intent_fields = intent_fields | {"workflow_profile"}
    checks = [
        _check("intent_fields", set(intent) == intent_fields, f"observed={sorted(intent)}"),
        _check("intent_schema_version", schema_version in {1, 2, 3}, f"observed={schema_version}"),
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
    if schema_version == 3:
        decision_profile = _decision_contract_profile(repo_root, accepted_head)
        checks.append(
            _check(
                "intent_workflow_profile",
                isinstance(intent_profile, str)
                and intent_profile in TRUSTED_PREMERGE_WORKFLOW_PROFILES
                and intent_profile == decision_profile,
                f"observed={intent_profile!r} decision={decision_profile!r}",
            )
        )
    return checks


def _validate_attestation(
    attestation: Mapping[str, Any],
    *,
    verifier: Any,
    intent: Mapping[str, Any],
    accepted_head: str,
    locked_base: str,
    now: datetime,
    merge_commit_sha: str,
    premerge: bool = False,
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
    elif schema_version == 3:
        try:
            workflow_policy = resolve_premerge_workflow_profile(
                intent.get("workflow_profile")
            )
        except ValueError as exc:
            return [
                _check("attestation_schema_version", False, f"unresolved_workflow_profile:{exc}"),
                _check("attestation_fields", False, "unresolved_workflow_profile"),
                _check("attestation_repository", False, "unresolved_workflow_profile"),
                _check("attestation_source_pr", False, "unresolved_workflow_profile"),
                _check("attestation_base", False, "unresolved_workflow_profile"),
                _check("attestation_head", False, "unresolved_workflow_profile"),
                _check("attestation_method", False, "unresolved_workflow_profile"),
                _check("attestation_intent_digest", False, "unresolved_workflow_profile"),
                _check("attestation_content_digest", False, "unresolved_workflow_profile"),
                _check("attestation_status", False, "unresolved_workflow_profile"),
                _check("attestation_expiry", False, "unresolved_workflow_profile"),
                _check("workflow_names", False, "unresolved_workflow_profile"),
                _check("workflow_run_uniqueness", False, "unresolved_workflow_profile"),
                _check("workflow_observation_fields", False, "unresolved_workflow_profile"),
                _check("approval_remote_identity", False, "unresolved_workflow_profile"),
                _check("approval_fields", False, "unresolved_workflow_profile"),
                _check("approval_approver", False, "unresolved_workflow_profile"),
                _check("approval_payload", False, "unresolved_workflow_profile"),
                _check("approval_content_digest", False, "unresolved_workflow_profile"),
            ]
        required_observation_count = len(workflow_policy)
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
    if schema_version in {2, 3}:
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
            _check("attestation_schema_version", schema_version in {1, 2, 3}, f"observed={schema_version}"),
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
    if schema_version in {2, 3}:
        verify_kwargs.update(
            expected_merge_commit_sha=merge_commit_sha,
            require_merged=True,
        )
    if premerge:
        # A pre-merge landing check must prove that the exact PR is still
        # unmerged, while the historical/post-merge validator retains its
        # merge-commit and timestamp checks below unchanged.
        verify_kwargs.pop("expected_merge_commit_sha", None)
        verify_kwargs["require_merged"] = False
    pr = verifier.verify_pr(**verify_kwargs)
    checks.append(_check("remote_pr_binding", bool(pr.get("verified")), str(pr.get("reason") or "verified")))
    if schema_version in {2, 3} and not premerge:
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


def validate_active_merge_intent(
    intent: Mapping[str, Any],
    *,
    repo_root: Path,
    accepted_head: str,
    source_pr: int,
    locked_base: str,
    now: datetime | None = None,
) -> list[dict[str, str]]:
    """Expose the canonical intent validator for the pre-merge gate.

    Transition landing has no merge commit yet, but it still uses exactly
    the same schema, profile, digest, expiry, and Decision/plan binding
    checks as post-merge validation.  The wrapper gives callers a stable
    check list when malformed evidence makes the canonical validator raise.
    """

    schema_version = intent.get("schema_version")
    if (
        isinstance(schema_version, bool)
        or not isinstance(schema_version, int)
        or schema_version != 3
    ):
        return [
            _check(
                "premerge_intent_schema_version",
                False,
                f"observed={schema_version!r} expected=3",
            )
        ]
    try:
        return _validate_intent(
            intent,
            repo_root=repo_root,
            accepted_head=accepted_head,
            source_pr=source_pr,
            locked_base=locked_base,
            now=now or datetime.now(timezone.utc),
        )
    except Exception as exc:  # noqa: BLE001 - malformed authority fails closed
        return [
            _check("intent_canonical_validation", False, f"{type(exc).__name__}:{exc}"),
        ]


def validate_premerge_attestation(
    attestation: Mapping[str, Any],
    *,
    verifier: Any,
    intent: Mapping[str, Any],
    accepted_head: str,
    locked_base: str,
    now: datetime | None = None,
) -> list[dict[str, str]]:
    """Run canonical attestation checks at the pre-merge landing boundary.

    The only semantic difference from :func:`_validate_attestation` is that
    pre-merge evidence must verify an unmerged PR and does not require
    ``merged_at`` or a merge commit.  All schema, raw digest, workflow,
    owner-identity, and remote workflow-run checks remain canonical.
    """

    schema_version = attestation.get("schema_version")
    if (
        isinstance(schema_version, bool)
        or not isinstance(schema_version, int)
        or schema_version != 3
    ):
        return [
            _check(
                "premerge_attestation_schema_version",
                False,
                f"observed={schema_version!r} expected=3",
            )
        ]
    try:
        return _validate_attestation(
            attestation,
            verifier=verifier,
            intent=intent,
            accepted_head=accepted_head,
            locked_base=locked_base,
            now=now or datetime.now(timezone.utc),
            merge_commit_sha="",
            premerge=True,
        )
    except Exception as exc:  # noqa: BLE001 - remote evidence fails closed
        return [
            _check("attestation_canonical_validation", False, f"{type(exc).__name__}:{exc}"),
        ]


_OWNER_LANDING_ATTESTATION_FIELDS: set[str] = {
    "schema_version",
    "attestation_id",
    "repository",
    "source_pr",
    "locked_base_sha",
    "accepted_exact_head_sha",
    "target_decision_id",
    "target_decision_content_sha256",
    "allowed_merge_method",
    "authority_pr",
    "authority_head_sha",
    "authority_base_sha",
    "authority_decision_id",
    "authority_decision_content_sha256",
    "authority_natural_runs",
    "owner_exact_head_review_id",
    "ready_state_gate_run_id",
    "ruleset_id",
    "required_status_contexts",
    "mainline_merge_intent_required",
    "active_pr_binding_mode",
    "authorization_status",
    "superseded_by",
    "content_digest",
    "_remote_comment_id",
    "_remote_author",
    "_remote_comment_created_at",
    "_remote_comment_updated_at",
    "_remote_comment_body",
}

_FALSE_NONE_RUN_FIELDS: set[str] = {
    "name",
    "run_id",
    "workflow_file",
    "event",
    "run_attempt",
    "head_sha",
    "conclusion",
}


def _load_remote_decision_contract(verifier: Any, ref: str) -> dict[str, Any]:
    """Read and parse the committed Decision at a remote exact ref."""

    result = verifier.load_ref_file_bytes(ref=ref, path="project_state/decision_packet.md")
    if not result.get("verified"):
        return {"verified": False, "reason": str(result.get("reason") or "load_failed")}
    raw = result.get("bytes")
    if not isinstance(raw, bytes):
        return {"verified": False, "reason": "missing_content"}
    try:
        text = raw.decode("utf-8", errors="strict")
    except UnicodeDecodeError as exc:
        return {"verified": False, "reason": f"undecodable:{exc}"}
    parsed_meta = extract_markdown_json_block(text, "decision_meta")
    parsed_contract = extract_markdown_json_block(text, "decision_contract")
    if not parsed_meta.get("found") or parsed_meta.get("parse_error"):
        return {"verified": False, "reason": "invalid_decision_meta"}
    if not parsed_contract.get("found") or parsed_contract.get("parse_error"):
        return {"verified": False, "reason": "invalid_decision_contract"}
    meta = {
        key: value
        for key, value in parsed_meta.items()
        if key not in {"found", "parse_error"}
    }
    contract = {
        key: value
        for key, value in parsed_contract.items()
        if key not in {"found", "parse_error"}
    }
    return {
        "verified": True,
        "sha256": hashlib.sha256(raw).hexdigest(),
        "meta_id": str(meta.get("decision_id") or ""),
        "contract": contract,
    }


def _authority_contract_binds_target(
    contract: Mapping[str, Any],
    *,
    source_pr: int,
    accepted_head: str,
    locked_base: str,
) -> bool:
    target_pr = contract.get("target_pr", contract.get("source_pr"))
    return (
        target_pr == source_pr
        and contract.get("accepted_exact_head_sha") == accepted_head
        and contract.get("base_sha") == locked_base
    )


def _authority_contract_owner_merge_scope(contract: Mapping[str, Any]) -> bool:
    forbidden = contract.get("forbidden_operations")
    forbidden = forbidden if isinstance(forbidden, list) else []
    forbidden_paths = contract.get("forbidden_mutated_paths")
    forbidden_paths = forbidden_paths if isinstance(forbidden_paths, list) else []
    return (
        contract.get("mark_ready_allowed") is True
        and contract.get("merge_allowed") is True
        and contract.get("expected_head_protection_required") is True
        and contract.get("allowed_merge_method") == "merge"
        and contract.get("workflow_rerun_allowed") is False
        and contract.get("auto_merge_allowed") is False
        and contract.get("direct_push_to_main_allowed") is False
        and contract.get("force_push_allowed") is False
        and "active_json_rewrite" in forbidden
        and any("mainline_merge_intents" in str(path) for path in forbidden_paths)
    )


def _validate_false_none_attestation(
    att: Mapping[str, Any],
    *,
    verifier: Any,
    repo_root: Path,
    source_pr: int,
    first_parent: str,
    second_parent: str,
    target_decision_id: str,
    target_decision_digest: str,
    merged_time: datetime | None,
    now: datetime,
    premerge: bool = False,
) -> list[dict[str, str]]:
    """Validate the single active Owner landing merge attestation and every
    remote truth it binds (authority PR/Decision/runs, Owner review, Ready
    State Gate, required contexts, Ruleset).

    When ``premerge`` is true, post-merge-only time-ordering checks that
    require ``merged_at`` are skipped so the validator can run on an
    unmerged Ready PR; all other schema, digest, binding, workflow, review,
    context and ruleset checks remain canonical."""

    checks: list[dict[str, str]] = []

    # Issue #721: a full refresh authority block extends the attestation
    # schema; a partial block is an unknown field and fails closed.  Without
    # any refresh field the legacy field set applies unchanged.
    refresh_present = bool(set(att) & BASE_REFRESH_AUTHORITY_FIELDS)
    allowed_fields = (
        _OWNER_LANDING_ATTESTATION_FIELDS | BASE_REFRESH_AUTHORITY_FIELDS
        if refresh_present
        else _OWNER_LANDING_ATTESTATION_FIELDS
    )
    fields_valid = set(att) == allowed_fields
    schema_ok = att.get("schema_version") == 1
    author_ok = att.get("_remote_author") in FALSE_NONE_ALLOWED_OWNERS
    repo_ok = att.get("repository") == "dddd2024/Nerelan"
    status_ok = (
        att.get("authorization_status") == "active" and not att.get("superseded_by")
    )
    policy_ok = (
        att.get("mainline_merge_intent_required") is False
        and att.get("active_pr_binding_mode") == CUTOVER_NONE_BINDING_MODE
    )
    digest_ok = att.get("content_digest") == owner_landing_content_digest(att)
    locked_base_ok = _refresh_locked_base_ok(att, first_parent=first_parent)
    refresh_base_label = (
        str(att.get("refresh_authority_refreshed_base_sha") or "")
        if refresh_present
        else first_parent
    )
    checks.extend(
        [
            _check(
                "false_none_attestation_schema_version",
                schema_ok,
                f"observed={att.get('schema_version')!r}",
            ),
            _check("false_none_attestation_fields", fields_valid, f"observed={sorted(att)}"),
            _check("false_none_attestation_repository", repo_ok, f"observed={att.get('repository')}"),
            _check(
                "false_none_attestation_source_pr",
                att.get("source_pr") == source_pr,
                f"observed={att.get('source_pr')} expected={source_pr}",
            ),
            _check(
                "false_none_attestation_locked_base",
                locked_base_ok,
                f"observed={att.get('locked_base_sha')} expected={refresh_base_label}",
            ),
            _check(
                "false_none_attestation_accepted_head",
                att.get("accepted_exact_head_sha") == second_parent,
                f"observed={att.get('accepted_exact_head_sha')}",
            ),
            _check(
                "false_none_attestation_merge_method",
                att.get("allowed_merge_method") == "merge",
                f"observed={att.get('allowed_merge_method')}",
            ),
            _check(
                "false_none_attestation_author",
                author_ok,
                f"author={att.get('_remote_author')}",
            ),
            _check("false_none_attestation_status", status_ok, f"status={att.get('authorization_status')} superseded_by={att.get('superseded_by')}"),
            _check(
                "false_none_attestation_policy_declaration",
                policy_ok,
                f"mainline_merge_intent_required={att.get('mainline_merge_intent_required')} active_pr_binding_mode={att.get('active_pr_binding_mode')}",
            ),
            _check("false_none_attestation_content_digest", digest_ok, "content_digest"),
        ]
    )

    # Target Decision binding (committed second-parent truth vs attestation).
    target_digest = str(att.get("target_decision_content_sha256") or "")
    checks.extend(
        [
            _check(
                "false_none_target_decision_id",
                att.get("target_decision_id") == target_decision_id,
                f"observed={att.get('target_decision_id')} expected={target_decision_id}",
            ),
            _check(
                "false_none_target_decision_digest",
                _sha256(target_digest) and target_digest == target_decision_digest,
                f"observed={target_digest}",
            ),
        ]
    )

    # Attestation comment timestamps must all predate the remote merged_at.
    comment_times: dict[str, datetime] = {}
    for field, check_name in (
        ("_remote_comment_created_at", "false_none_attestation_created_before_merge"),
        ("_remote_comment_updated_at", "false_none_attestation_updated_before_merge"),
    ):
        value = att.get(field)
        if not isinstance(value, str) or not value:
            checks.append(_check(check_name, False, "missing"))
            continue
        try:
            parsed = _parse_time(value)
            if parsed.tzinfo is None:
                raise ValueError("timezone_required")
        except (TypeError, ValueError) as exc:
            checks.append(_check(check_name, False, f"invalid:{exc}"))
            continue
        comment_times[field] = parsed
        if premerge:
            checks.append(_check(check_name, True, "premerge_skip_merged_at"))
        elif merged_time is None:
            checks.append(_check(check_name, False, "remote_pr_merged_at_unavailable"))
        else:
            checks.append(
                _check(
                    check_name,
                    parsed < merged_time,
                    f"comment={parsed.isoformat()} merged_at={merged_time.isoformat()}",
                )
            )
    created_time = comment_times.get("_remote_comment_created_at")
    updated_time = comment_times.get("_remote_comment_updated_at")
    if created_time is not None and updated_time is not None:
        checks.append(
            _check(
                "false_none_attestation_comment_order",
                created_time <= updated_time,
                f"created={created_time.isoformat()} updated={updated_time.isoformat()}",
            )
        )

    # Independent Owner landing authority sidecar PR.
    authority_pr = int(att.get("authority_pr") or 0)
    authority_head = str(att.get("authority_head_sha") or "")
    authority_base = str(att.get("authority_base_sha") or "")
    authority_decision_id = str(att.get("authority_decision_id") or "")
    authority_decision_digest = str(att.get("authority_decision_content_sha256") or "")
    authority_pr_result = verifier.verify_pr(
        pr_number=authority_pr,
        expected_head_sha=authority_head,
        expected_base_sha=authority_base,
        require_merged=False,
    )
    checks.append(
        _check(
            "false_none_authority_pr_identity",
            bool(authority_pr_result.get("verified")),
            str(authority_pr_result.get("reason") or "verified"),
        )
    )
    remote_authority_pr = (
        authority_pr_result.get("pr") if isinstance(authority_pr_result.get("pr"), Mapping) else {}
    )
    checks.append(
        _check(
            "false_none_authority_unmerged",
            remote_authority_pr.get("merged") is False,
            f"merged={remote_authority_pr.get('merged')}",
        )
    )

    # Authority committed Decision identity, digest, and binding contract.
    authority_decision = _load_remote_decision_contract(verifier, authority_head)
    if authority_decision.get("verified"):
        ad_meta_id = str(authority_decision.get("meta_id") or "")
        ad_sha = str(authority_decision.get("sha256") or "")
        ad_contract = authority_decision.get("contract")
        ad_contract = ad_contract if isinstance(ad_contract, Mapping) else {}
        checks.extend(
            [
                _check(
                    "false_none_authority_decision_id",
                    ad_meta_id == authority_decision_id,
                    f"observed={ad_meta_id} expected={authority_decision_id}",
                ),
                _check(
                    "false_none_authority_decision_digest",
                    _sha256(authority_decision_digest)
                    and ad_sha == authority_decision_digest,
                    f"observed={ad_sha}",
                ),
            ]
        )
        if (
            ad_meta_id == authority_decision_id
            and authority_decision_digest == ad_sha
            and ad_contract.get("mainline_merge_intent_required") is False
            and ad_contract.get("active_pr_binding_mode") == CUTOVER_NONE_BINDING_MODE
        ):
            checks.extend(
                [
                    _check(
                        "false_none_authority_decision_binds_target",
                        _authority_contract_binds_target(
                            ad_contract,
                            source_pr=source_pr,
                            accepted_head=second_parent,
                            locked_base=first_parent,
                        ),
                        f"target_pr={ad_contract.get('target_pr') or ad_contract.get('source_pr')} head={ad_contract.get('accepted_exact_head_sha')} base={ad_contract.get('base_sha')}",
                    ),
                    _check(
                        "false_none_authority_decision_owner_scope",
                        _authority_contract_owner_merge_scope(ad_contract),
                        "mark_ready_allowed+merge_allowed+expected_head+merge_method+no_rerun+no_active_json",
                    ),
                    _check(
                        "false_none_authority_decision_policy",
                        True,
                        "false/none authority Decision",
                    ),
                ]
            )
        else:
            checks.append(
                _check(
                    "false_none_authority_decision_policy",
                    False,
                    "authority Decision digest/identity/policy mismatch",
                )
            )
    else:
        checks.append(
            _check(
                "false_none_authority_decision_read",
                False,
                str(authority_decision.get("reason") or "load_failed"),
            )
        )

    # Authority natural run observations (CI / Decision Preflight / State Gate).
    runs = att.get("authority_natural_runs")
    runs = runs if isinstance(runs, list) else []
    run_names = [item.get("name") for item in runs if isinstance(item, Mapping)]
    run_ids = [
        int(item.get("run_id") or 0) for item in runs if isinstance(item, Mapping)
    ]
    checks.extend(
        [
            _check(
                "false_none_authority_runs",
                len(runs) == 3
                and set(run_names) == set(_FALSE_NONE_AUTHORITY_WORKFLOW_POLICY),
                f"names={run_names}",
            ),
            _check(
                "false_none_authority_runs_unique",
                len(run_ids) == len(set(run_ids)) == 3,
                f"run_ids={run_ids}",
            ),
        ]
    )
    for index, (name, (expected_file, expected_event)) in enumerate(
        _FALSE_NONE_AUTHORITY_WORKFLOW_POLICY.items()
    ):
        if index >= len(runs) or not isinstance(runs[index], Mapping):
            checks.append(_check(f"false_none_authority_workflow:{name}", False, "missing"))
            continue
        observation = runs[index]
        locally_bound = (
            observation.get("name") == name
            and observation.get("workflow_file") == expected_file
            and observation.get("event") == expected_event
            and observation.get("head_sha") == authority_head
            and observation.get("conclusion") == "success"
            and int(observation.get("run_attempt") or 0) >= 1
            and set(observation) == _FALSE_NONE_RUN_FIELDS
        )
        verified = verifier.verify_workflow_run(
            run_id=int(observation.get("run_id") or 0),
            expected_head_sha=authority_head,
            expected_workflow_file=expected_file,
            expected_event=expected_event,
            expected_run_attempt=int(observation.get("run_attempt") or 0),
        )
        checks.append(
            _check(
                f"false_none_authority_workflow:{name}",
                locally_bound and bool(verified.get("verified")),
                str(verified.get("reason") or "verified"),
            )
        )

    # Owner exact-head review.
    review_id = int(att.get("owner_exact_head_review_id") or 0)
    review_result = verifier.verify_pull_request_review(
        review_id=review_id,
        pr_number=source_pr,
        allowed_authors=FALSE_NONE_ALLOWED_OWNERS,
        expected_commit_sha=second_parent,
    )
    checks.append(
        _check(
            "false_none_owner_review_binding",
            bool(review_result.get("verified")),
            str(review_result.get("reason") or "verified"),
        )
    )
    review = review_result.get("review") if isinstance(review_result.get("review"), Mapping) else {}
    checks.append(
        _check(
            "false_none_owner_review_author",
            str((review.get("user") or {}).get("login") or "")
            in FALSE_NONE_ALLOWED_OWNERS,
            f"author={review.get('user')}",
        )
    )
    checks.append(
        _check(
            "false_none_owner_review_commit",
            review.get("commit_id") == second_parent,
            f"observed={review.get('commit_id')} expected={second_parent}",
        )
    )
    submitted_at = str(review.get("submitted_at") or "")
    if submitted_at:
        try:
            submitted_time = _parse_time(submitted_at)
            if submitted_time.tzinfo is None:
                raise ValueError("timezone_required")
        except (TypeError, ValueError) as exc:
            checks.append(
                _check("false_none_owner_review_before_merge", False, f"invalid:{exc}")
            )
            submitted_time = None
        else:
            submitted_time = submitted_time
    else:
        submitted_time = None
        checks.append(
            _check(
                "false_none_owner_review_before_merge",
                False,
                "missing_submitted_at",
            )
        )
    if premerge:
        if submitted_time is not None:
            checks.append(
                _check(
                    "false_none_owner_review_before_merge",
                    True,
                    "premerge_skip_merged_at",
                )
            )
    elif submitted_at and merged_time is not None:
        try:
            submitted_time = _parse_time(submitted_at)
            checks.append(
                _check(
                    "false_none_owner_review_before_merge",
                    submitted_time < merged_time,
                    f"submitted={submitted_time.isoformat()} merged_at={merged_time.isoformat()}",
                )
            )
        except (TypeError, ValueError) as exc:
            checks.append(
                _check("false_none_owner_review_before_merge", False, f"invalid:{exc}")
            )
    else:
        checks.append(
            _check(
                "false_none_owner_review_before_merge",
                False,
                "missing_submitted_at_or_merged_at",
            )
        )

    # Ready-triggered State Gate run on the exact target head.
    ready_run_id = int(att.get("ready_state_gate_run_id") or 0)
    ready_result = verifier.verify_workflow_run(
        run_id=ready_run_id,
        expected_head_sha=second_parent,
        expected_workflow_file=".github/workflows/state-gate.yml",
        expected_event="pull_request",
        expected_run_attempt=1,
    )
    checks.append(
        _check(
            "false_none_ready_state_gate_run",
            bool(ready_result.get("verified")),
            str(ready_result.get("reason") or "verified"),
        )
    )

    # Required exact-head status contexts (never the draft-inert name).
    declared_contexts = att.get("required_status_contexts")
    declared_contexts = declared_contexts if isinstance(declared_contexts, list) else []
    expected_contexts = list(FALSE_NONE_REQUIRED_CONTEXTS)
    checks.append(
        _check(
            "false_none_required_contexts_declared",
            declared_contexts == expected_contexts,
            f"observed={declared_contexts}",
        )
    )
    # For premerge validation the landing-state-gate is currently executing,
    # so only previously completed contexts (baseline, state-gate) are
    # verified here.  The current formal landing-state-gate execution is
    # verified by the trusted execution context check in project_gate.py.
    if premerge:
        completed_contexts = ("baseline", "state-gate")
    else:
        completed_contexts = tuple(expected_contexts)
    check_runs_payload: Any = None
    if declared_contexts == expected_contexts:
        context_result = verifier.verify_check_run_contexts(
            head_sha=second_parent, required_contexts=completed_contexts
        )
        checks.append(
            _check(
                "false_none_required_contexts_executed",
                bool(context_result.get("verified")),
                str(context_result.get("reason") or "verified"),
            )
        )
        check_runs_payload = context_result
    else:
        checks.append(
            _check("false_none_required_contexts_executed", False, "contexts_not_declared")
        )
    if premerge:
        # The landing-state-gate formal execution is verified by the
        # trusted execution context check in project_gate.py; the
        # completed landing-state-gate context is not required here.
        checks.append(
            _check(
                "false_none_landing_context_is_formal",
                True,
                "premerge_trusted_execution_verified_in_project_gate",
            )
        )
    else:
        runs_payload = (
            check_runs_payload.get("check_runs")
            if isinstance(check_runs_payload, Mapping)
            else None
        )
        if isinstance(runs_payload, list):
            names_seen = {
                str(run.get("name") or "")
                for run in runs_payload
                if isinstance(run, Mapping)
            }
            checks.append(
                _check(
                    "false_none_landing_context_is_formal",
                    "landing-state-gate" in names_seen,
                    f"check_names={sorted(names_seen)}",
                )
            )
        else:
            checks.append(
                _check(
                    "false_none_landing_context_is_formal",
                    False,
                    "check_runs_unavailable",
                )
            )

    # Live repository Ruleset agreement.
    ruleset_id = int(att.get("ruleset_id") or 0)
    ruleset_result = verifier.verify_repository_ruleset(
        ruleset_id=ruleset_id,
        required_status_contexts=tuple(expected_contexts),
        allowed_merge_methods=("merge",),
    )
    checks.append(
        _check(
            "false_none_ruleset_verify",
            bool(ruleset_result.get("verified")),
            str(ruleset_result.get("reason") or "verified"),
        )
    )
    return checks


def validate_base_refresh_landing(
    *,
    repo_root: Path,
    attestation: Mapping[str, Any],
    first_parent: str,
    second_parent: str,
    merge_commit_sha: str | None = None,
) -> dict[str, Any]:
    """Offline deterministic base-refresh landing gate (Issue #721).

    This gate is pure local git computation: no GitHub network access, no
    provider call, no credential read.  It answers one question — is a non-
    overlap base refresh of an already-accepted exact target head admissible?

    Every fact the gate relies on is machine-computed from the repository:
    ``original..target`` and ``original..refreshed`` path sets, ancestor
    relation, ``git cat-file -e <sha>^{commit}`` object identity, and the
    ``git merge-tree --write-tree`` result.  Nothing is inferred from
    workflow YAML.  Authority-side and Owner-review identity are bound as
    explicit attestation claims cross-checked against those local facts; their
    live remote verification remains the Owner landing attestation path.
    """

    checks: list[dict[str, str]] = []

    original = str(attestation.get("refresh_authority_original_locked_base_sha") or "")
    refreshed = str(attestation.get("refresh_authority_refreshed_base_sha") or "")
    target = str(attestation.get("refresh_authority_accepted_target_head_sha") or "")
    expected_tree = str(attestation.get("refresh_authority_expected_merge_tree_sha") or "")
    decision_digest = str(attestation.get("refresh_authority_decision_content_sha256") or "")
    review_sha = str(attestation.get("refresh_authority_owner_exact_head_review_sha") or "")
    sidecar_pr = attestation.get("refresh_authority_sidecar_pr")
    sidecar_base = str(attestation.get("refresh_authority_sidecar_base_sha") or "")
    merge_method = attestation.get("refresh_authority_allowed_merge_method")
    expected_head_protection = attestation.get(
        "refresh_authority_expected_head_protection_required"
    )
    source_pr = attestation.get("source_pr")

    field_set_ok = set(attestation) == BASE_REFRESH_AUTHORITY_FIELDS | {"source_pr"}
    values_ok = all(
        attestation.get(field) not in (None, "")
        for field in BASE_REFRESH_AUTHORITY_FIELDS
    )
    source_pr_ok = (
        isinstance(source_pr, int)
        and not isinstance(source_pr, bool)
        and source_pr > 0
    )
    sidecar_ok = (
        isinstance(sidecar_pr, int)
        and not isinstance(sidecar_pr, bool)
        and sidecar_pr > 0
        and source_pr_ok
        and sidecar_pr != source_pr
    )
    checks.extend(
        [
            _check(
                "base_refresh_schema",
                field_set_ok and values_ok,
                BASE_REFRESH_ADMISSIBLE
                if field_set_ok and values_ok
                else f"{BASE_REFRESH_BLOCKED_SCHEMA}:observed={sorted(attestation)}",
            ),
            _check(
                "base_refresh_merge_method",
                merge_method == "merge",
                BASE_REFRESH_ADMISSIBLE
                if merge_method == "merge"
                else f"merge_method_required:observed={merge_method!r}",
            ),
            _check(
                "base_refresh_expected_head_protection",
                expected_head_protection is True,
                BASE_REFRESH_ADMISSIBLE
                if expected_head_protection is True
                else f"expected_head_protection_required:observed={expected_head_protection!r}",
            ),
            _check(
                "base_refresh_authority_sidecar_pr",
                sidecar_ok,
                BASE_REFRESH_ADMISSIBLE
                if sidecar_ok
                else f"distinct_authority_sidecar_required:sidecar={sidecar_pr} source_pr={source_pr}",
            ),
        ]
    )

    # N9: every bound revision must be an exact 40-hex commit object.
    bound_objects: dict[str, str] = {
        "original_locked_base": original,
        "refreshed_base": refreshed,
        "accepted_target_head": target,
    }
    invalid_objects = sorted(
        label
        for label, sha in bound_objects.items()
        if not _is_commit_object(repo_root, sha)
    )
    objects_valid = not invalid_objects
    checks.append(
        _check(
            "base_refresh_object_validation",
            objects_valid,
            BASE_REFRESH_ADMISSIBLE
            if objects_valid
            else f"{BASE_REFRESH_BLOCKED_OBJECT_INVALID}:{','.join(invalid_objects)}",
        )
    )

    # N5: the refreshed base must descend from the original locked base.
    ancestry_ok = (
        _is_commit_ancestor(repo_root, original, refreshed) if objects_valid else False
    )
    checks.append(
        _check(
            "base_refresh_ancestry",
            objects_valid and ancestry_ok,
            BASE_REFRESH_ADMISSIBLE
            if objects_valid and ancestry_ok
            else f"{BASE_REFRESH_BLOCKED_ANCESTRY}:original={original} refreshed={refreshed}",
        )
    )

    # N3: the authority binds the exact accepted target head that landed.
    target_head_ok = objects_valid and target == second_parent
    checks.append(
        _check(
            "base_refresh_target_head_binding",
            target_head_ok,
            BASE_REFRESH_ADMISSIBLE
            if target_head_ok
            else f"{BASE_REFRESH_BLOCKED_TARGET_HEAD_DRIFT}:observed={target} landed={second_parent}",
        )
    )

    # N1/N2: machine-computed path sets on both sides of the refresh.
    target_paths = (
        _changed_paths(repo_root, original, target) if objects_valid else None
    )
    intervening_paths = (
        _changed_paths(repo_root, original, refreshed) if objects_valid else None
    )
    paths_valid = (
        objects_valid and target_paths is not None and intervening_paths is not None
    )
    overlap = sorted((target_paths or set()) & (intervening_paths or set()))
    checks.append(
        _check(
            "base_refresh_target_overlap",
            paths_valid and not overlap,
            BASE_REFRESH_ADMISSIBLE
            if paths_valid and not overlap
            else (
                f"{BASE_REFRESH_BLOCKED_TARGET_OVERLAP}:paths={overlap}"
                if paths_valid
                else f"{BASE_REFRESH_BLOCKED_TARGET_OVERLAP}:path_sets_unavailable"
            ),
        )
    )
    authority_drift = sorted(
        path
        for path in (intervening_paths or set())
        if _is_authority_sensitive_path(path)
    )
    checks.append(
        _check(
            "base_refresh_authority_sensitive_drift",
            paths_valid and not authority_drift,
            BASE_REFRESH_ADMISSIBLE
            if paths_valid and not authority_drift
            else (
                f"{BASE_REFRESH_BLOCKED_AUTHORITY_DRIFT}:paths={authority_drift}"
                if paths_valid
                else f"{BASE_REFRESH_BLOCKED_AUTHORITY_DRIFT}:path_sets_unavailable"
            ),
        )
    )
    dependency_drift = sorted(
        path
        for path in (intervening_paths or set())
        if _is_dependency_manifest_path(path)
    )
    checks.append(
        _check(
            "base_refresh_dependency_drift",
            paths_valid and not dependency_drift,
            BASE_REFRESH_ADMISSIBLE
            if paths_valid and not dependency_drift
            else (
                f"{BASE_REFRESH_BLOCKED_DEPENDENCY_DRIFT}:paths={dependency_drift}"
                if paths_valid
                else f"{BASE_REFRESH_BLOCKED_DEPENDENCY_DRIFT}:path_sets_unavailable"
            ),
        )
    )

    # N4: the authority binds the target's own committed Decision digest.
    actual_decision_digest = (
        _sha256_blob(repo_root, target, "project_state/decision_packet.md")
        if objects_valid
        else None
    )
    decision_digest_ok = (
        objects_valid
        and re.fullmatch(r"[0-9a-f]{64}", decision_digest) is not None
        and actual_decision_digest is not None
        and decision_digest == actual_decision_digest
    )
    checks.append(
        _check(
            "base_refresh_decision_digest",
            decision_digest_ok,
            BASE_REFRESH_ADMISSIBLE
            if decision_digest_ok
            else f"{BASE_REFRESH_BLOCKED_DECISION_DRIFT}:observed={decision_digest} committed={actual_decision_digest}",
        )
    )

    # Owner exact-head review binding and fresh authority-sidecar binding.
    owner_review_ok = objects_valid and review_sha == second_parent
    checks.append(
        _check(
            "base_refresh_owner_review_binding",
            owner_review_ok,
            BASE_REFRESH_ADMISSIBLE
            if owner_review_ok
            else f"owner_exact_head_review_required:observed={review_sha} landed={second_parent}",
        )
    )
    sidecar_base_ok = objects_valid and sidecar_base == refreshed
    checks.append(
        _check(
            "base_refresh_authority_sidecar_base",
            sidecar_base_ok,
            BASE_REFRESH_ADMISSIBLE
            if sidecar_base_ok
            else f"authority_sidecar_base_required:observed={sidecar_base} refreshed={refreshed}",
        )
    )

    # N6: no redrift between authorization and landing.
    main_binding_ok = objects_valid and refreshed == first_parent
    checks.append(
        _check(
            "base_refresh_current_main_binding",
            main_binding_ok,
            BASE_REFRESH_ADMISSIBLE
            if main_binding_ok
            else f"{BASE_REFRESH_BLOCKED_MAIN_REDRIFT}:observed={refreshed} landed={first_parent}",
        )
    )

    # N7/N8: ordinary write-tree merge plus exact expected tree identity.
    computed_tree = (
        _merge_tree_sha(repo_root, refreshed, target) if objects_valid else None
    )
    merge_tree_ok = computed_tree is not None
    checks.append(
        _check(
            "base_refresh_merge_tree",
            merge_tree_ok,
            computed_tree or BASE_REFRESH_BLOCKED_MERGE_CONFLICT,
        )
    )
    tree_identity_ok = computed_tree is not None and expected_tree == computed_tree
    checks.append(
        _check(
            "base_refresh_merge_tree_identity",
            tree_identity_ok,
            BASE_REFRESH_ADMISSIBLE
            if tree_identity_ok
            else f"{BASE_REFRESH_BLOCKED_MERGE_TREE_MISMATCH}:computed={computed_tree} expected={expected_tree}",
        )
    )

    # merge_tree_policy: the landed tree must be the authorized merge tree.
    if merge_commit_sha and _is_commit_object(repo_root, merge_commit_sha):
        landed_tree = _tree(repo_root, merge_commit_sha)
    else:
        landed_tree = computed_tree
    merge_tree_policy_ok = bool(landed_tree) and landed_tree == expected_tree
    checks.append(
        _check(
            "merge_tree_policy",
            merge_tree_policy_ok,
            f"merge={landed_tree or '-'} expected={expected_tree}",
        )
    )

    core_checks = [item for item in checks if item["name"] != "merge_tree_policy"]
    failing = [item for item in core_checks if item["status"] == "FAIL"]
    authority_detail = (
        BASE_REFRESH_ADMISSIBLE if not failing else failing[0]["detail"]
    )
    checks.append(
        _check("base_refresh_authority", not failing, authority_detail)
    )

    return _result(
        "base-refresh-landing",
        checks,
        extra={
            "landing_policy": "false_none_owner_landing_base_refresh",
            "refresh_original_locked_base_sha": original,
            "refresh_refreshed_base_sha": refreshed,
            "refresh_accepted_target_head_sha": target,
            "refresh_expected_merge_tree_sha": expected_tree,
            "refresh_computed_merge_tree_sha": computed_tree or "",
            "refresh_intervening_path_count": len(intervening_paths or set()),
        },
    )


def _validate_false_none_landing(
    *,
    repo_root: Path,
    verifier: Any,
    merge_commit_sha: str,
    first_parent: str,
    second_parent: str,
    contract: Mapping[str, Any],
    now: datetime,
) -> tuple[list[dict[str, str]], dict[str, Any]]:
    """Run the false/none post-merge validation on the actual merged target."""

    checks: list[dict[str, str]] = []

    # ``merge_tree_policy`` is appended after the Owner landing attestation is
    # resolved: with no base-refresh authority it stays the strict legacy rule
    # (landed tree == accepted target tree), and with one it binds the tree the
    # authority authorized.  See the base-refresh block near the end.

    # Resolve the true merged PR from the exact merge topology.  Ambiguity and
    # repository mismatch fail closed; the historical active.json is never used
    # as the landing identity on this path.
    try:
        resolved_pr = verifier.resolve_merged_pull_request(merge_commit_sha=merge_commit_sha)
        resolved_pr = resolved_pr if isinstance(resolved_pr, Mapping) else {}
        source_pr = int(resolved_pr.get("number") or 0)
        remote_merged_at = str(resolved_pr.get("merged_at") or "")
        if not source_pr or not remote_merged_at:
            raise GitHubEvidenceError("resolved_pr_missing_number_or_merged_at")
        checks.append(_check("false_none_target_pr_resolution", True, f"pr={source_pr}"))
    except GitHubEvidenceError as exc:
        checks.append(_check("false_none_target_pr_resolution", False, str(exc)))
        source_pr = 0
        remote_merged_at = ""
        resolved_pr = {}

    # Remote PR binding: exact repo, PR, head, base, merge commit, merged state.
    merged_time: datetime | None = None
    if source_pr:
        pr_result = verifier.verify_pr(
            pr_number=source_pr,
            expected_head_sha=second_parent,
            expected_base_sha=first_parent,
            expected_merge_commit_sha=merge_commit_sha,
            require_merged=True,
        )
        checks.append(
            _check(
                "false_none_remote_pr_binding",
                bool(pr_result.get("verified")),
                str(pr_result.get("reason") or "verified"),
            )
        )
        if remote_merged_at:
            try:
                merged_time = _parse_time(remote_merged_at)
                if merged_time.tzinfo is None:
                    raise ValueError("timezone_required")
                checks.append(
                    _check("false_none_remote_pr_merged_at", True, remote_merged_at)
                )
            except (TypeError, ValueError) as exc:
                checks.append(
                    _check("false_none_remote_pr_merged_at", False, f"invalid:{exc}")
                )
                merged_time = None
        else:
            checks.append(_check("false_none_remote_pr_merged_at", False, "missing"))
    else:
        checks.append(_check("false_none_remote_pr_binding", False, "no_resolved_pr"))
        checks.append(_check("false_none_remote_pr_merged_at", False, "no_resolved_pr"))

    # Second-parent committed Decision identity + digest + false/none policy.
    decision_digest = (
        _sha256_blob(repo_root, second_parent, "project_state/decision_packet.md") or ""
    )
    try:
        decision_meta = _decision_meta_blob(repo_root, second_parent)
        target_decision_id = str(decision_meta.get("decision_id") or "")
        checks.append(_check("false_none_target_decision_read", True, target_decision_id))
    except ValueError as exc:
        target_decision_id = ""
        checks.append(_check("false_none_target_decision_read", False, str(exc)))
    checks.append(
        _check(
            "false_none_target_decision_policy",
            contract.get("mainline_merge_intent_required") is False
            and contract.get("active_pr_binding_mode") == CUTOVER_NONE_BINDING_MODE,
            f"mainline_merge_intent_required={contract.get('mainline_merge_intent_required')} active_pr_binding_mode={contract.get('active_pr_binding_mode')}",
        )
    )

    # Exactly one active OWNER_LANDING_MERGE_ATTESTATION on the resolved PR.
    if source_pr:
        try:
            attestations = verifier.load_owner_landing_merge_attestations(
                pr_number=source_pr
            )
            checks.append(_check("false_none_attestation_load", True, f"comments={len(attestations)}"))
        except GitHubEvidenceError as exc:
            checks.append(_check("false_none_attestation_load", False, str(exc)))
            attestations = []
    else:
        attestations = []
    candidates = [
        att
        for att in attestations
        if isinstance(att, Mapping)
        and att.get("source_pr") == source_pr
        and att.get("accepted_exact_head_sha") == second_parent
        and att.get("authorization_status") == "active"
    ]
    checks.append(
        _check(
            "false_none_attestation_unique",
            len(candidates) == 1,
            f"observed={len(candidates)}",
        )
    )
    if len(candidates) == 1:
        checks.extend(
            _validate_false_none_attestation(
                candidates[0],
                verifier=verifier,
                repo_root=repo_root,
                source_pr=source_pr,
                first_parent=first_parent,
                second_parent=second_parent,
                target_decision_id=target_decision_id,
                target_decision_digest=decision_digest,
                merged_time=merged_time,
                now=now,
            )
        )

    # Issue #721: safe non-overlap base refresh.  A full refresh authority
    # block in the single active attestation routes to the offline base-refresh
    # gate; anything else keeps the strict legacy merge-tree rule untouched.
    refresh_authority = (
        _extract_base_refresh_authority(candidates[0])
        if len(candidates) == 1
        else None
    )
    if refresh_authority is not None:
        refresh_result = validate_base_refresh_landing(
            repo_root=repo_root,
            attestation=refresh_authority,
            first_parent=first_parent,
            second_parent=second_parent,
            merge_commit_sha=merge_commit_sha,
        )
        checks.extend(refresh_result["checks"])
        landing_policy = "false_none_owner_landing_base_refresh"
    else:
        landed_tree = _tree(repo_root, merge_commit_sha)
        accepted_tree = _tree(repo_root, second_parent)
        checks.append(
            _check(
                "merge_tree_policy",
                landed_tree == accepted_tree,
                f"merge={landed_tree} accepted={accepted_tree}",
            )
        )
        landing_policy = "false_none_owner_landing_authority"
    extra: dict[str, Any] = {
        "target_pr": source_pr,
        "attestation_id": str(
            candidates[0].get("attestation_id") if len(candidates) == 1 else ""
        ),
        "authority_pr": int(
            candidates[0].get("authority_pr") if len(candidates) == 1 else 0
        ),
        "landing_policy": landing_policy,
    }
    return checks, extra


def validate_false_none_premerge_landing(
    *,
    repo_root: Path,
    verifier: Any,
    source_pr: int,
    accepted_head: str,
    locked_base: str,
    now: datetime,
) -> tuple[list[dict[str, str]], dict[str, Any]]:
    """Validate the false/none pre-merge Owner landing attestation.

    Called from :func:`_check_landing_authority` in cutover mode after the
    remote PR/head/base binding has already been verified.  Reuses the
    existing :func:`_validate_false_none_attestation` with ``premerge=True``
    so post-merge-only time-ordering checks are skipped while all schema,
    digest, binding, workflow, review, context and ruleset checks remain
    canonical.
    """

    checks: list[dict[str, str]] = []

    # Target Decision identity from the committed second-parent tree.
    decision_digest = (
        _sha256_blob(repo_root, accepted_head, "project_state/decision_packet.md")
        or ""
    )
    try:
        decision_meta = _decision_meta_blob(repo_root, accepted_head)
        target_decision_id = str(decision_meta.get("decision_id") or "")
        checks.append(
            _check("false_none_target_decision_read", True, target_decision_id)
        )
    except ValueError as exc:
        target_decision_id = ""
        checks.append(
            _check("false_none_target_decision_read", False, str(exc))
        )

    # Exactly one active OWNER_LANDING_MERGE_ATTESTATION on the target PR.
    try:
        attestations = verifier.load_owner_landing_merge_attestations(
            pr_number=source_pr
        )
        checks.append(
            _check(
                "false_none_attestation_load", True, f"comments={len(attestations)}"
            )
        )
    except GitHubEvidenceError as exc:
        checks.append(_check("false_none_attestation_load", False, str(exc)))
        attestations = []

    candidates = [
        att
        for att in attestations
        if isinstance(att, Mapping)
        and att.get("source_pr") == source_pr
        and att.get("accepted_exact_head_sha") == accepted_head
        and att.get("authorization_status") == "active"
    ]
    checks.append(
        _check(
            "false_none_attestation_unique",
            len(candidates) == 1,
            f"observed={len(candidates)}",
        )
    )

    if len(candidates) == 1:
        checks.extend(
            _validate_false_none_attestation(
                candidates[0],
                verifier=verifier,
                repo_root=repo_root,
                source_pr=source_pr,
                first_parent=locked_base,
                second_parent=accepted_head,
                target_decision_id=target_decision_id,
                target_decision_digest=decision_digest,
                merged_time=None,
                now=now,
                premerge=True,
            )
        )

    extra: dict[str, Any] = {
        "target_pr": source_pr,
        "attestation_id": str(
            candidates[0].get("attestation_id") if len(candidates) == 1 else ""
        ),
        "authority_pr": int(
            candidates[0].get("authority_pr") if len(candidates) == 1 else 0
        ),
        "landing_policy": "false_none_owner_landing_authority",
    }
    return checks, extra


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

        # Issue #156 post-merge cutover: route by the committed second-parent
        # Decision policy contract. The legacy path is byte-for-byte the prior
        # validator; only a committed false/none Decision chooses the new
        # independent Owner-landing-authority path, and contradictory policy
        # combinations always block.
        policy_mode, contract = _post_merge_landing_policy(repo_root, second_parent)
        if policy_mode == "incoherent":
            checks.append(
                _check(
                    "landing_policy_mode",
                    False,
                    f"mainline_merge_intent_required={contract.get('mainline_merge_intent_required', 'missing')} active_pr_binding_mode={contract.get('active_pr_binding_mode', 'missing')}",
                )
            )
            return _result(
                "mainline-merge-validation",
                checks,
                extra={
                    "merge_commit_sha": merge,
                    "first_parent_sha": first_parent,
                    "second_parent_sha": second_parent,
                    "landing_policy": "incoherent",
                },
            )
        checks.append(_check("landing_policy_mode", True, policy_mode))
        if policy_mode == "cutover":
            found_checks, extra = _validate_false_none_landing(
                repo_root=repo_root,
                verifier=verifier,
                merge_commit_sha=merge,
                first_parent=first_parent,
                second_parent=second_parent,
                contract=contract,
                now=now,
            )
            checks.extend(found_checks)
            extra["merge_commit_sha"] = merge
            extra["first_parent_sha"] = first_parent
            extra["second_parent_sha"] = second_parent
            return _result("mainline-merge-validation", checks, extra=extra)

        # Legacy mainline-merge-intent path (unchanged fail-closed behavior).
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
        "target_pr": str(validation.get("target_pr") or ""),
        "authority_pr": str(validation.get("authority_pr") or ""),
        "landing_policy": str(validation.get("landing_policy") or "legacy_intent"),
        "blocking_reasons": list(validation.get("blocking_reasons") or []),
        "emitted_at": now.astimezone(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
    }
