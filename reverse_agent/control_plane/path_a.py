"""Fail-closed Path-A R1 authority verification and task-scoped CI selection.

This module implements the ordinary R1 authority gate.  All live GitHub
state (Issue, PR, approval events, collaborator permission) is accepted as
parameters — the module performs no network I/O.  The only subprocess use is
``git diff --name-status`` inside :func:`changed_paths_for_event`.
"""

from __future__ import annotations

import hashlib
import json
import re
import subprocess
import unicodedata
from dataclasses import dataclass
from datetime import datetime
from fnmatch import fnmatchcase
from pathlib import Path
from typing import Any, Iterable, Mapping


SNAPSHOT_FIELDS = (
    "repository",
    "issue_number",
    "approval_state",
    "approved_by",
    "approval_event_or_time",
    "body_digest_sha256",
    "immutable_observation_ref",
    "work_item_identity",
    "target_branch",
    "base_sha",
    "exact_head_sha",
)
SHA256_RE = re.compile(r"^[0-9a-f]{64}$")
SHA_RE = re.compile(r"^[0-9a-f]{40}$")
SHELL_META_RE = re.compile(r"(?:&&|\|\||[;`|<>]|\$\(|\$\{)")

PRIVILEGED_OPERATION_TERMS = (
    "direct push to main",
    "force push",
    "rebase",
    "squash",
    "auto-merge",
    "automatic merge",
    "mark-ready",
    "mark ready",
    "merge",
    "tag",
    "release",
)

ORDINARY_R1_PATH_RISK_POLICY = (
    # R3 sensitive material and unknown native binaries.
    ("secrets/**", "R3"),
    ("**/secrets/**", "R3"),
    (".env", "R3"),
    (".env.*", "R3"),
    ("**/.env", "R3"),
    ("**/.env.*", "R3"),
    ("*credential*", "R3"),
    ("**/*credential*", "R3"),
    ("*secret*", "R3"),
    ("**/*secret*", "R3"),
    ("*.pem", "R3"),
    ("**/*.pem", "R3"),
    ("*.key", "R3"),
    ("**/*.key", "R3"),
    ("*.p12", "R3"),
    ("**/*.p12", "R3"),
    ("*.pfx", "R3"),
    ("**/*.pfx", "R3"),
    ("*.exe", "R3"),
    ("**/*.exe", "R3"),
    ("*.dll", "R3"),
    ("**/*.dll", "R3"),
    ("*.so", "R3"),
    ("**/*.so", "R3"),
    ("*.dylib", "R3"),
    ("**/*.dylib", "R3"),
    # R2 governance, authority, workflow, dependency, and packaging surfaces.
    ("project_state/**", "R2"),
    (".github/workflows/**", "R2"),
    (".github/actions/**", "R2"),
    (".github/ISSUE_TEMPLATE/**", "R2"),
    (".github/CODEOWNERS", "R2"),
    ("CODEOWNERS", "R2"),
    ("docs/CODEOWNERS", "R2"),
    (".codex-skills/**", "R2"),
    ("AGENTS.md", "R2"),
    ("reverse_agent/project_gate.py", "R2"),
    ("reverse_agent/control_plane/**", "R2"),
    ("reverse_agent/decision_preflight.py", "R2"),
    ("reverse_agent/project_ci.py", "R2"),
    ("reverse_agent/project_jobs.py", "R2"),
    ("reverse_agent/post_final_evidence_sync.py", "R2"),
    ("reverse_agent/github_adapter.py", "R2"),
    ("reverse_agent/architecture/risk.py", "R2"),
    ("reverse_agent/architecture/risk_classifier.py", "R2"),
    ("pyproject.toml", "R2"),
    ("requirements*.txt", "R2"),
    ("**/requirements*.txt", "R2"),
    ("setup.py", "R2"),
    ("setup.cfg", "R2"),
    ("pytest.ini", "R2"),
    ("poetry.lock", "R2"),
    ("Pipfile*", "R2"),
    ("uv.lock", "R2"),
    ("package.json", "R2"),
    ("**/package.json", "R2"),
    ("package-lock.json", "R2"),
    ("**/package-lock.json", "R2"),
    ("pnpm-lock.yaml", "R2"),
    ("**/pnpm-lock.yaml", "R2"),
    ("yarn.lock", "R2"),
    ("**/yarn.lock", "R2"),
    ("Dockerfile", "R2"),
    ("Dockerfile.*", "R2"),
    ("**/Dockerfile", "R2"),
    ("**/Dockerfile.*", "R2"),
)


class PathAGateError(ValueError):
    """A stable fail-closed Path-A validation error."""

    def __init__(self, code: str, detail: str = "") -> None:
        self.code = code
        self.detail = detail
        super().__init__(f"{code}:{detail}" if detail else code)


@dataclass(frozen=True)
class TaskCheck:
    check_id: str
    argv: tuple[str, ...]
    required_targets: tuple[str, ...]

    @property
    def command(self) -> str:
        return " ".join(self.argv)


BASELINE_TASK_CHECK = TaskCheck(
    check_id="baseline",
    argv=(
        "python", "-m", "pytest",
        "tests/test_project_gate.py",
        "tests/test_project_reports.py",
        "tests/test_project_jobs.py",
        "tests/test_post_final_evidence_sync.py",
        "tests/test_decision_preflight.py",
        "tests/test_project_state.py",
        "tests/test_control_plane_transition.py",
        "tests/test_architecture_contracts.py",
        "tests/test_risk_classifier.py",
        "tests/test_development_graph.py",
        "tests/test_trust_authorization_adapter.py",
        "tests/test_planning_and_github_adapters.py",
        "-q",
    ),
    required_targets=(
        "tests/test_project_gate.py",
        "tests/test_project_reports.py",
        "tests/test_project_jobs.py",
        "tests/test_post_final_evidence_sync.py",
        "tests/test_decision_preflight.py",
        "tests/test_project_state.py",
        "tests/test_control_plane_transition.py",
        "tests/test_architecture_contracts.py",
        "tests/test_risk_classifier.py",
        "tests/test_development_graph.py",
        "tests/test_trust_authorization_adapter.py",
        "tests/test_planning_and_github_adapters.py",
    ),
)
PATH_A_TASK_CHECK = TaskCheck(
    check_id="path_a_gate",
    argv=(
        "python", "-m", "pytest",
        "tests/test_path_a_gate.py",
        "tests/test_control_plane_transition.py",
        "tests/test_planning_and_github_adapters.py",
        "-q",
    ),
    required_targets=(
        "tests/test_path_a_gate.py",
        "tests/test_control_plane_transition.py",
        "tests/test_planning_and_github_adapters.py",
    ),
)

BASELINE_CHECK = BASELINE_TASK_CHECK.command
PATH_A_CHECK = PATH_A_TASK_CHECK.command

TASK_CHECK_MAPPING = (
    (
        (
            "reverse_agent/project_gate.py",
            "reverse_agent/control_plane/**",
            "tests/test_path_a_gate.py",
            "tests/test_control_plane_transition.py",
            "tests/test_planning_and_github_adapters.py",
            ".github/workflows/state-gate.yml",
            ".github/workflows/ci.yml",
        ),
        PATH_A_TASK_CHECK,
    ),
)


@dataclass(frozen=True)
class ImmutableWorkItemSnapshot:
    repository: str
    issue_number: int
    approval_state: str
    approved_by: str
    approval_event_or_time: str
    body_digest_sha256: str
    immutable_observation_ref: str
    work_item_identity: str
    target_branch: str
    base_sha: str
    exact_head_sha: str

    @classmethod
    def from_mapping(cls, payload: Mapping[str, str]) -> "ImmutableWorkItemSnapshot":
        missing = [field for field in SNAPSHOT_FIELDS if not str(payload.get(field, "")).strip()]
        if missing:
            raise PathAGateError("snapshot_missing_fields", ",".join(missing))
        try:
            issue_number = int(payload["issue_number"])
        except (TypeError, ValueError) as exc:
            raise PathAGateError("snapshot_invalid_issue_number") from exc
        snapshot = cls(
            repository=payload["repository"].strip(),
            issue_number=issue_number,
            approval_state=payload["approval_state"].strip(),
            approved_by=payload["approved_by"].strip(),
            approval_event_or_time=payload["approval_event_or_time"].strip(),
            body_digest_sha256=payload["body_digest_sha256"].strip().lower(),
            immutable_observation_ref=payload["immutable_observation_ref"].strip().lower(),
            work_item_identity=payload["work_item_identity"].strip(),
            target_branch=payload["target_branch"].strip(),
            base_sha=payload["base_sha"].strip().lower(),
            exact_head_sha=payload["exact_head_sha"].strip().lower(),
        )
        if snapshot.approval_state != "APPROVED":
            raise PathAGateError("snapshot_not_approved")
        if not SHA256_RE.fullmatch(snapshot.body_digest_sha256):
            raise PathAGateError("snapshot_invalid_body_digest")
        if snapshot.immutable_observation_ref != snapshot.body_digest_sha256:
            raise PathAGateError("snapshot_observation_ref_mismatch")
        if not SHA_RE.fullmatch(snapshot.base_sha) or not SHA_RE.fullmatch(snapshot.exact_head_sha):
            raise PathAGateError("snapshot_invalid_git_sha")
        expected_identity = (
            f"{snapshot.repository}#{snapshot.issue_number}@"
            f"{snapshot.immutable_observation_ref}"
        )
        if snapshot.work_item_identity != expected_identity:
            raise PathAGateError("snapshot_work_item_identity_mismatch")
        if snapshot.target_branch == "main":
            raise PathAGateError("snapshot_direct_main_forbidden")
        return snapshot


def normalize_issue_body(body: str) -> str:
    """Normalize GitHub Issue text exactly as the Path-A digest contract states."""

    return unicodedata.normalize("NFC", str(body).replace("\r\n", "\n").replace("\r", "\n"))


def issue_body_digest(body: str) -> str:
    return hashlib.sha256(normalize_issue_body(body).encode("utf-8")).hexdigest()


@dataclass(frozen=True)
class AuthorityRevision:
    """Canonical digest of every mutable live input to ordinary-R1 authority."""

    repository: str
    source_issue_number: int
    normalized_issue_body_digest: str
    current_risk_labels: tuple[str, ...]
    current_authority_labels: tuple[str, ...]
    latest_effective_r1_approved_event_id: int | str | None
    latest_effective_r1_approved_actor: str | None
    latest_effective_r1_approved_timestamp: str | None
    latest_r1_approved_transition: str | None
    source_issue_last_edited_at: str | None
    pr_number: int
    pr_body_digest: str
    pr_draft_state: bool | None
    pr_auto_merge_state: Any
    base_sha: str
    exact_head_sha: str

    def to_mapping(self) -> dict[str, Any]:
        payload: dict[str, Any] = {
            "repository": self.repository,
            "source_issue_number": self.source_issue_number,
            "normalized_issue_body_digest": self.normalized_issue_body_digest,
            "current_risk_labels": list(self.current_risk_labels),
            "current_authority_labels": list(self.current_authority_labels),
            "latest_effective_r1_approved_event_id": (
                self.latest_effective_r1_approved_event_id
            ),
            "latest_effective_r1_approved_actor": (
                self.latest_effective_r1_approved_actor
            ),
            "latest_effective_r1_approved_timestamp": (
                self.latest_effective_r1_approved_timestamp
            ),
            "latest_r1_approved_transition": self.latest_r1_approved_transition,
            "source_issue_last_edited_at": self.source_issue_last_edited_at,
            "pr_number": self.pr_number,
            "pr_body_digest": self.pr_body_digest,
            "pr_draft_state": self.pr_draft_state,
            "pr_auto_merge_state": self.pr_auto_merge_state,
            "base_sha": self.base_sha,
            "exact_head_sha": self.exact_head_sha,
        }
        canonical = json.dumps(
            payload,
            ensure_ascii=False,
            separators=(",", ":"),
            sort_keys=True,
        )
        payload["digest_sha256"] = hashlib.sha256(canonical.encode("utf-8")).hexdigest()
        return payload


def _build_authority_revision(
    *,
    repository: str,
    issue: Mapping[str, Any],
    labels: Iterable[str],
    latest_approval_transition: Mapping[str, Any] | None,
    pr_number: int,
    pr: Mapping[str, Any],
) -> AuthorityRevision:
    canonical_labels = tuple(sorted({str(label).casefold() for label in labels}))
    event_name = (
        str(latest_approval_transition.get("event") or "")
        if latest_approval_transition is not None
        else None
    )
    effective = latest_approval_transition if event_name == "labeled" else None
    return AuthorityRevision(
        repository=repository,
        source_issue_number=int(issue.get("number") or 0),
        normalized_issue_body_digest=issue_body_digest(str(issue.get("body") or "")),
        current_risk_labels=tuple(
            label for label in canonical_labels if label in {"r0", "r1", "r2", "r3"}
        ),
        current_authority_labels=tuple(
            label
            for label in canonical_labels
            if label in {"r0", "r1", "r1-approved", "r2", "r3"}
        ),
        latest_effective_r1_approved_event_id=(
            effective.get("id") if effective is not None else None
        ),
        latest_effective_r1_approved_actor=(
            str((effective.get("actor") or {}).get("login") or "")
            if effective is not None
            else None
        ),
        latest_effective_r1_approved_timestamp=(
            str(effective.get("created_at") or "")
            if effective is not None
            else None
        ),
        latest_r1_approved_transition=event_name,
        source_issue_last_edited_at=(
            str(issue["lastEditedAt"])
            if "lastEditedAt" in issue and issue["lastEditedAt"] is not None
            else None
        ),
        pr_number=pr_number,
        pr_body_digest=issue_body_digest(str(pr.get("body") or "")),
        pr_draft_state=(
            pr.get("draft") if isinstance(pr.get("draft"), bool) else None
        ),
        pr_auto_merge_state=pr.get("autoMergeRequest") if pr.get("autoMergeRequest") is not None else pr.get("auto_merge"),
        base_sha=str((pr.get("base") or {}).get("sha") or "").lower(),
        exact_head_sha=str((pr.get("head") or {}).get("sha") or "").lower(),
    )


def _text_blocks(markdown: str) -> list[str]:
    return re.findall(r"```(?:text)?[ \t]*\n(.*?)\n```", markdown, flags=re.DOTALL | re.IGNORECASE)


def parse_snapshot(pr_body: str) -> ImmutableWorkItemSnapshot:
    candidates: list[dict[str, str]] = []
    malformed = False
    for block in _text_blocks(pr_body):
        if not any(re.search(rf"(?m)^\s*{re.escape(field)}\s*:", block) for field in SNAPSHOT_FIELDS):
            continue
        parsed: dict[str, str] = {}
        for raw_line in block.splitlines():
            if not raw_line.strip():
                continue
            if ":" not in raw_line:
                malformed = True
                continue
            key, value = raw_line.split(":", 1)
            key = key.strip()
            if key in parsed:
                raise PathAGateError("snapshot_duplicate_field", key)
            parsed[key] = value.strip()
        candidates.append(parsed)
    if not candidates:
        raise PathAGateError("snapshot_missing")
    if len(candidates) != 1:
        raise PathAGateError("snapshot_duplicate")
    if malformed:
        raise PathAGateError("snapshot_malformed")
    return ImmutableWorkItemSnapshot.from_mapping(candidates[0])


def _section_fenced_block(markdown: str, heading: str) -> str:
    pattern = (
        rf"(?ims)^##+\s+{re.escape(heading)}\s*$"
        rf".*?```(?:text)?[ \t]*\n(.*?)\n```"
    )
    match = re.search(pattern, markdown)
    if not match:
        raise PathAGateError("issue_missing_section", heading)
    return match.group(1)


def parse_allowed_paths(issue_body: str) -> tuple[str, ...]:
    """Parse the allowed-paths block with a strict grammar.

    Only two forms are accepted:
    - exact paths: ``docs/file.md``
    - subtree globs: ``directory/subtree/**``

    All other wildcard patterns (``*``, ``**``, ``**/*``, ``docs/*.md``,
    ``docs/**/file.md``, ``?``, ``[ab]``, ``src/*/file.py``) are rejected.
    The only permitted ``*`` is a trailing ``/**`` after a non-empty directory.
    """
    block = _section_fenced_block(issue_body, "Allowed paths")
    paths: list[str] = []
    for line in block.splitlines():
        if not line.strip() or line.lstrip().startswith("#"):
            continue
        raw_path = line.strip().replace("\\", "/")
        if raw_path.startswith("/") or re.match(r"^[A-Za-z]:", raw_path):
            raise PathAGateError("issue_allowed_paths_invalid", raw_path)
        normalized = re.sub(r"/+", "/", raw_path)
        while normalized.startswith("./"):
            normalized = normalized[2:]
        normalized = normalized.rstrip("/")
        if normalized in {"", ".", "*", "**", "**/*"}:
            raise PathAGateError("issue_allowed_paths_unbounded", raw_path)
        if normalized.startswith("/") or ".." in Path(normalized).parts:
            raise PathAGateError("issue_allowed_paths_invalid", raw_path)
        # Strict grammar: only exact paths and directory/subtree/**
        # The /** prefix must have at least two path components (e.g. docs/subtree/**)
        # to prevent overly broad single-directory globs like docs/**
        if normalized.endswith("/**"):
            prefix = normalized[:-3].rstrip("/")
            if not prefix or any(c in prefix for c in "*?[]"):
                raise PathAGateError("issue_allowed_paths_invalid", raw_path)
            prefix_parts = [p for p in prefix.split("/") if p]
            if len(prefix_parts) < 2:
                raise PathAGateError("issue_allowed_paths_invalid", raw_path)
        elif any(c in normalized for c in "*?[]"):
            raise PathAGateError("issue_allowed_paths_invalid", raw_path)
        paths.append(normalized)
    if not paths:
        raise PathAGateError("issue_allowed_paths_empty")
    return tuple(paths)


def _path_matches(path: str, pattern: str) -> bool:
    """Match a path against an allowed-path pattern.

    Only two pattern forms are supported:
    - exact path: ``docs/file.md`` matches only ``docs/file.md``
    - subtree glob: ``docs/sub/**`` matches ``docs/sub`` and ``docs/sub/...``

    ``*`` never crosses ``/``.  ``fnmatchcase`` is not used so that a stray
    ``*`` cannot match across directory boundaries.
    """
    normalized = path.replace("\\", "/").lstrip("./")
    candidate = pattern.replace("\\", "/").lstrip("./")
    if candidate.endswith("/**"):
        prefix = candidate[:-3].rstrip("/")
        return normalized == prefix or normalized.startswith(prefix + "/")
    return normalized == candidate


def flatten_paginated_events(raw_pages: Any) -> list[dict[str, Any]]:
    """Flatten ``gh api --paginate --slurp`` output into a deterministic array.

    The ``--slurp`` flag produces a JSON array of pages, where each page is a
    JSON array of events.  This function validates the structure and flattens
    it into a single deterministic list.  Malformed input fails closed.
    """
    if not isinstance(raw_pages, list):
        raise PathAGateError("pagination_pages_not_array")
    events: list[dict[str, Any]] = []
    for page_index, page in enumerate(raw_pages):
        if not isinstance(page, list):
            raise PathAGateError("pagination_page_not_array", str(page_index))
        for event in page:
            if not isinstance(event, dict):
                raise PathAGateError("pagination_event_not_object")
            events.append(event)
    return events


def _path_matches_risk(path: str, pattern: str) -> bool:
    """Match a path against a risk-policy pattern using fnmatch semantics.

    Risk policy patterns use wildcards (``**/*.exe``, ``*credential*``) that
    must match across directory boundaries.  This is distinct from
    :func:`_path_matches` which is strict for allowed-path grammar.
    """
    normalized = path.replace("\\", "/")
    candidate = pattern.replace("\\", "/")
    # fnmatchcase treats * as matching everything except / on some platforms,
    # but we need * to cross / for risk patterns like **/*.exe.
    # Use a translation that allows * to match any characters including /.
    return fnmatchcase(normalized, candidate)


def _minimum_path_risk(path: str) -> tuple[str, str] | None:
    canonical_path = path.replace("\\", "/").casefold()
    matches = tuple(
        (minimum_risk, pattern)
        for pattern, minimum_risk in ORDINARY_R1_PATH_RISK_POLICY
        if _path_matches_risk(canonical_path, pattern.casefold())
    )
    if not matches:
        return None
    return max(matches, key=lambda item: {"R2": 2, "R3": 3}[item[0]])


def _paths_outside(changed_paths: Iterable[str], allowed_paths: Iterable[str]) -> tuple[str, ...]:
    allowed = tuple(allowed_paths)
    return tuple(
        path for path in changed_paths
        if not any(_path_matches(path, pattern) for pattern in allowed)
    )


def _validate_issue_commands(issue_body: str) -> None:
    try:
        required_checks = _section_fenced_block(issue_body, "Required checks")
    except PathAGateError:
        required_checks = _section_fenced_block(issue_body, "Required deterministic checks")
    if SHELL_META_RE.search(required_checks):
        raise PathAGateError("issue_shell_command_forbidden")

    allowed_operations = re.search(
        r"(?ims)^##+\s+Allowed operations\s*$.*?```(?:text)?[ \t]*\n(.*?)\n```",
        issue_body,
    )
    if allowed_operations:
        lowered = allowed_operations.group(1).lower()
        privileged = [term for term in PRIVILEGED_OPERATION_TERMS if term in lowered]
        if privileged:
            raise PathAGateError("issue_privileged_operation_forbidden", ",".join(privileged))


def verify_path_a_r1(
    *,
    event_name: str,
    event: Mapping[str, Any],
    issue: Mapping[str, Any],
    approval_events: Iterable[Mapping[str, Any]],
    approver_permission: str,
    changed_paths: Iterable[str],
    merge_base_sha: str,
    expected_repository: str,
    expected_authority_revision: str | None = None,
) -> dict[str, Any]:
    """Verify a complete ordinary R1 authority snapshot without executing Issue text."""

    if event_name not in ("pull_request", "pull_request_target") or not isinstance(
        event.get("pull_request"), Mapping
    ):
        raise PathAGateError("event_not_pull_request")
    repository = str((event.get("repository") or {}).get("full_name") or "")
    if repository != expected_repository:
        raise PathAGateError("repository_mismatch", repository)

    pr = event["pull_request"]
    snapshot = parse_snapshot(str(pr.get("body") or ""))
    if snapshot.repository != expected_repository:
        raise PathAGateError("snapshot_repository_mismatch")

    issue_number = int(issue.get("number") or 0)
    if snapshot.issue_number != issue_number:
        raise PathAGateError("snapshot_issue_mismatch")
    labels = {
        str(label.get("name") if isinstance(label, Mapping) else label).casefold()
        for label in issue.get("labels", [])
    }
    approval_transitions = [
        item for item in approval_events
        if str(item.get("event") or "") in {"labeled", "unlabeled"}
        and str((item.get("label") or {}).get("name") or "").casefold()
        == "r1-approved"
    ]
    approval_transitions.sort(
        key=lambda item: (
            str(item.get("created_at") or ""),
            int(item.get("id") or 0),
        )
    )
    effective_approval = approval_transitions[-1] if approval_transitions else None
    pr_number = int(event.get("number") or pr.get("number") or 0)
    authority_revision = _build_authority_revision(
        repository=repository,
        issue=issue,
        labels=labels,
        latest_approval_transition=effective_approval,
        pr_number=pr_number,
        pr=pr,
    ).to_mapping()
    if (
        expected_authority_revision is not None
        and authority_revision["digest_sha256"] != expected_authority_revision
    ):
        raise PathAGateError(
            "authority_revision_mismatch",
            (
                f"expected={expected_authority_revision};"
                f"observed={authority_revision['digest_sha256']}"
            ),
        )

    if pr.get("state") != "open" or pr.get("draft") is not True:
        raise PathAGateError("pr_must_be_open_draft")
    if str(issue.get("state") or "").lower() != "open":
        raise PathAGateError("source_issue_not_open")
    if "r1" not in labels:
        raise PathAGateError("issue_not_r1")
    if "r1-approved" not in labels:
        raise PathAGateError("issue_not_r1_approved")
    disallowed_tiers = sorted(labels & {"r2", "r3"})
    if disallowed_tiers:
        raise PathAGateError("issue_privileged_risk_tier", ",".join(disallowed_tiers))
    if approver_permission not in {"admin", "maintain"}:
        raise PathAGateError("approver_not_owner_or_maintainer")

    if not approval_transitions:
        raise PathAGateError("approval_event_missing")
    assert effective_approval is not None
    if str(effective_approval.get("event") or "") != "labeled":
        raise PathAGateError("approval_event_superseded")
    if str((effective_approval.get("actor") or {}).get("login") or "") != snapshot.approved_by:
        raise PathAGateError("approval_actor_mismatch")
    if str(effective_approval.get("created_at") or "") != snapshot.approval_event_or_time:
        raise PathAGateError("approval_event_mismatch")

    if "lastEditedAt" not in issue:
        raise PathAGateError("issue_edit_identity_missing")
    last_edited_at = issue["lastEditedAt"]
    if last_edited_at is None:
        pass  # never-edited, continue
    elif isinstance(last_edited_at, str):
        try:
            last_edit = datetime.fromisoformat(last_edited_at.replace("Z", "+00:00"))
            approval_time = datetime.fromisoformat(
                snapshot.approval_event_or_time.replace("Z", "+00:00")
            )
        except ValueError as exc:
            raise PathAGateError("issue_edit_time_invalid") from exc
        if last_edit >= approval_time:
            raise PathAGateError("issue_body_edit_not_strictly_before_approval")
    else:
        raise PathAGateError("issue_edit_identity_missing")

    issue_body = str(issue.get("body") or "")
    if issue_body_digest(issue_body) != snapshot.body_digest_sha256:
        raise PathAGateError("issue_body_digest_mismatch")
    _validate_issue_commands(issue_body)

    head = pr.get("head") or {}
    base = pr.get("base") or {}
    head_repository = str((head.get("repo") or {}).get("full_name") or "")
    if head_repository and head_repository != expected_repository:
        raise PathAGateError("head_repository_mismatch")
    if str(head.get("ref") or "") != snapshot.target_branch:
        raise PathAGateError("head_branch_mismatch")
    if str(head.get("sha") or "").lower() != snapshot.exact_head_sha:
        raise PathAGateError("exact_head_mismatch")
    if str(base.get("ref") or "") != "main":
        raise PathAGateError("base_branch_not_main")
    if str(base.get("sha") or "").lower() != snapshot.base_sha:
        raise PathAGateError("base_sha_mismatch")
    if merge_base_sha.lower() != snapshot.base_sha:
        raise PathAGateError("merge_base_mismatch")
    _auto_merge = pr.get("autoMergeRequest") if pr.get("autoMergeRequest") is not None else pr.get("auto_merge")
    if _auto_merge not in (None, False):
        raise PathAGateError("auto_merge_forbidden")

    changed = tuple(dict.fromkeys(path.replace("\\", "/") for path in changed_paths))
    if not changed:
        raise PathAGateError("changed_paths_empty")
    allowed_paths = parse_allowed_paths(issue_body)
    for path in changed:
        path_risk = _minimum_path_risk(path)
        if path_risk is not None:
            minimum_risk, matched_pattern = path_risk
            raise PathAGateError(
                "path_risk_exceeds_r1",
                (
                    f"path={path};minimum_risk={minimum_risk};"
                    f"matched_pattern={matched_pattern}"
                ),
            )
    outside = _paths_outside(changed, allowed_paths)
    if outside:
        raise PathAGateError("changed_paths_outside_allowed", ",".join(outside))

    return {
        "schema_version": 1,
        "gate_name": "path-a-r1-gate",
        "gate_status": "PATH_A_R1_AUTHORIZED",
        "mode": "path_a_r1",
        "repository": expected_repository,
        "issue_number": snapshot.issue_number,
        "target_branch": snapshot.target_branch,
        "base_sha": snapshot.base_sha,
        "exact_head_sha": snapshot.exact_head_sha,
        "authority_revision": authority_revision,
        "authority_revalidation_required": True,
        "changed_paths": list(changed),
        "selected_checks": list(select_task_checks(changed)["commands"]),
        "authority_source": "live_github_authority_revision",
        "comments_authoritative": False,
        "issue_commands_executed": False,
    }


def select_task_checks(
    changed_paths: Iterable[str],
    *,
    repo_root: Path | None = None,
) -> dict[str, Any]:
    """Select stable repository-owned checks; runtime changes without a mapping fail."""

    changed = tuple(sorted(dict.fromkeys(path.replace("\\", "/") for path in changed_paths)))
    selected: list[TaskCheck] = []
    for patterns, check in TASK_CHECK_MAPPING:
        if any(any(_path_matches(path, pattern) for pattern in patterns) for path in changed):
            selected.append(check)
    unmatched_runtime = tuple(
        path for path in changed
        if path.startswith("reverse_agent/")
        and not any(
            any(_path_matches(path, pattern) for pattern in patterns)
            for patterns, _ in TASK_CHECK_MAPPING
        )
    )
    if unmatched_runtime:
        raise PathAGateError("runtime_change_without_task_check", ",".join(unmatched_runtime))
    if any(path.startswith(("reverse_agent/", "tests/")) for path in changed) and not selected:
        raise PathAGateError("task_checks_not_selected")
    if repo_root is not None:
        for check in selected:
            for target in check.required_targets:
                if not (repo_root / target).exists():
                    raise PathAGateError(
                        "mapped_test_target_missing",
                        f"{check.check_id}:{target}",
                    )
    return {
        "check_ids": tuple(check.check_id for check in selected),
        "commands": tuple(check.command for check in selected),
        "checks": tuple(selected),
    }


def _paths_from_diff_name_status(output: str) -> tuple[str, ...]:
    paths: list[str] = []
    for raw_line in output.splitlines():
        if not raw_line:
            continue
        fields = raw_line.split("\t")
        status = fields[0]
        if status.startswith(("R", "C")):
            if len(fields) != 3:
                raise PathAGateError("git_diff_name_status_malformed", raw_line)
            paths.extend((fields[1], fields[2]))
        else:
            if len(fields) != 2:
                raise PathAGateError("git_diff_name_status_malformed", raw_line)
            paths.append(fields[1])
    return tuple(dict.fromkeys(paths))


def _paths_from_api_file_entries(entries: Iterable[Mapping[str, Any]]) -> tuple[str, ...]:
    paths: list[str] = []
    for entry in entries:
        filename = str(entry.get("filename") or "")
        if not filename:
            raise PathAGateError("github_file_entry_missing_filename")
        paths.append(filename)
        status = str(entry.get("status") or "")
        previous = str(entry.get("previous_filename") or "")
        if status in {"renamed", "copied"}:
            if not previous:
                raise PathAGateError("github_file_entry_missing_previous_filename", filename)
            paths.append(previous)
    return tuple(dict.fromkeys(paths))


def changed_paths_for_event(
    event: Mapping[str, Any],
    repo_root: Path,
) -> tuple[tuple[str, ...], str, str]:
    """Return changed paths plus exact head/base bindings from a checked-out event.

    Uses local ``git diff --name-status`` only — no GitHub API calls.  This is
    the only subprocess use in the module.
    """

    pr = event.get("pull_request")
    if isinstance(pr, Mapping):
        base_sha = str((pr.get("base") or {}).get("sha") or "")
        head_sha = str((pr.get("head") or {}).get("sha") or "")
    else:
        base_sha = str(event.get("before") or "")
        head_sha = str(event.get("after") or "")
    if not SHA_RE.fullmatch(head_sha):
        raise PathAGateError("workflow_head_sha_missing")
    if not SHA_RE.fullmatch(base_sha):
        raise PathAGateError("workflow_base_sha_missing")
    actual_head = subprocess.check_output(
        ["git", "rev-parse", "HEAD"], cwd=repo_root, text=True
    ).strip()
    if actual_head != head_sha:
        raise PathAGateError("workflow_exact_head_mismatch", f"{actual_head}!={head_sha}")
    diff = subprocess.run(
        ["git", "diff", "--name-status", "-M", "-C", f"{base_sha}..{head_sha}"],
        cwd=repo_root,
        check=False,
        capture_output=True,
        text=True,
    )
    if diff.returncode != 0:
        raise PathAGateError("git_diff_failed", diff.stderr.strip())
    changed = _paths_from_diff_name_status(diff.stdout)
    if not changed:
        raise PathAGateError("changed_paths_empty")
    return changed, base_sha, head_sha


# ---------------------------------------------------------------------------
# Trusted changed-path observation (Section 八)
#
# A pure data object capturing changed paths observed from a *trusted base
# checkout*.  The trusted checkout HEAD must equal the event base SHA.  The
# candidate head Git object must exist but is NEVER checked out.  This is the
# single canonical observation reused by authority routing, Path-A, and the
# finalize receipt.
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class TrustedChangedPathObservation:
    """Canonical changed-path observation from a trusted base checkout."""

    repository: str
    base_sha: str
    head_sha: str
    merge_base_sha: str
    trusted_checkout_sha: str
    paths: tuple[str, ...]
    canonical_sha256: str

    def to_mapping(self) -> dict[str, Any]:
        return {
            "schema_version": 1,
            "repository": self.repository,
            "base_sha": self.base_sha,
            "head_sha": self.head_sha,
            "merge_base_sha": self.merge_base_sha,
            "trusted_checkout_sha": self.trusted_checkout_sha,
            "changed_paths": list(self.paths),
            "changed_paths_sha256": self.canonical_sha256,
        }


def _validate_observation_path(path: str) -> str:
    """Validate and canonicalize a single changed path for the trusted observation."""

    if not path:
        raise PathAGateError("observation_path_empty")
    if "\x00" in path:
        raise PathAGateError("observation_path_nul")
    normalized = path.replace("\\", "/")
    while normalized.startswith("./"):
        normalized = normalized[2:]
    normalized = re.sub(r"/+", "/", normalized)
    if not normalized or normalized == ".":
        raise PathAGateError("observation_path_empty")
    if normalized.startswith("/"):
        raise PathAGateError("observation_path_absolute")
    if re.match(r"^[A-Za-z]:", normalized):
        raise PathAGateError("observation_path_absolute")
    parts = [p for p in normalized.split("/") if p]
    if ".." in parts:
        raise PathAGateError("observation_path_traversal")
    return "/".join(parts)


def build_trusted_changed_path_observation(
    event: Mapping[str, Any],
    repo_root: Path,
    *,
    expected_repository: str,
    authorized_base_sha: str | None = None,
) -> TrustedChangedPathObservation:
    """Build a trusted changed-path observation from a trusted base checkout.

    The trusted checkout HEAD must equal the event's base SHA.  The candidate
    head Git object must exist but is NEVER checked out.  ``git diff`` runs
    against the candidate object directly from the trusted base checkout.
    """

    repository = str((event.get("repository") or {}).get("full_name") or "")
    if repository != expected_repository:
        raise PathAGateError("observation_repository_mismatch", repository)

    pr = event.get("pull_request")
    if isinstance(pr, Mapping):
        base_sha = str((pr.get("base") or {}).get("sha") or "").lower()
        head_sha = str((pr.get("head") or {}).get("sha") or "").lower()
    else:
        base_sha = str(event.get("before") or "").lower()
        head_sha = str(event.get("after") or "").lower()

    if not SHA_RE.fullmatch(base_sha):
        raise PathAGateError("observation_base_sha_invalid")
    if not SHA_RE.fullmatch(head_sha):
        raise PathAGateError("observation_head_sha_invalid")

    trusted_checkout = subprocess.check_output(
        ["git", "rev-parse", "HEAD"], cwd=repo_root, text=True
    ).strip().lower()
    if trusted_checkout != base_sha:
        raise PathAGateError(
            "trusted_checkout_not_base",
            f"{trusted_checkout}!={base_sha}",
        )

    # Verify candidate commit object exists without checking it out.
    cat = subprocess.run(
        ["git", "cat-file", "-e", f"{head_sha}^{{commit}}"],
        cwd=repo_root,
        check=False,
        capture_output=True,
        text=True,
    )
    if cat.returncode != 0:
        raise PathAGateError("observation_candidate_object_missing", head_sha)

    merge_base = subprocess.check_output(
        ["git", "merge-base", base_sha, head_sha],
        cwd=repo_root,
        text=True,
    ).strip().lower()
    if authorized_base_sha is not None:
        if merge_base != authorized_base_sha.lower():
            raise PathAGateError(
                "observation_merge_base_not_authorized",
                f"{merge_base}!={authorized_base_sha}",
            )
    elif merge_base != base_sha:
        raise PathAGateError(
            "observation_merge_base_not_base",
            f"{merge_base}!={base_sha}",
        )

    diff = subprocess.run(
        ["git", "diff", "--name-status", "-M", "-C", f"{base_sha}..{head_sha}"],
        cwd=repo_root,
        check=False,
        capture_output=True,
        text=True,
    )
    if diff.returncode != 0:
        raise PathAGateError("observation_git_diff_failed", diff.stderr.strip())

    raw_paths: list[str] = []
    for raw_line in diff.stdout.splitlines():
        if not raw_line:
            continue
        fields = raw_line.split("\t")
        status = fields[0]
        if status.startswith(("R", "C")):
            if len(fields) != 3:
                raise PathAGateError("observation_diff_malformed", raw_line)
            raw_paths.extend((fields[1], fields[2]))
        else:
            if len(fields) != 2:
                raise PathAGateError("observation_diff_malformed", raw_line)
            raw_paths.append(fields[1])

    normalized = [_validate_observation_path(p) for p in raw_paths]
    # Deterministic dedup + sort.
    paths = tuple(sorted(dict.fromkeys(normalized)))
    if not paths:
        raise PathAGateError("observation_paths_empty")

    canonical = "\n".join(paths)
    digest = hashlib.sha256(canonical.encode("utf-8")).hexdigest()

    return TrustedChangedPathObservation(
        repository=repository,
        base_sha=base_sha,
        head_sha=head_sha,
        merge_base_sha=merge_base,
        trusted_checkout_sha=trusted_checkout,
        paths=paths,
        canonical_sha256=digest,
    )


def load_trusted_route_observation(path: Path) -> TrustedChangedPathObservation:
    """Load and validate a trusted route observation JSON file."""

    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise PathAGateError("observation_file_not_object")
    if int(payload.get("schema_version") or 0) != 1:
        raise PathAGateError("observation_file_schema_version")
    repository = str(payload.get("repository") or "")
    base_sha = str(payload.get("base_sha") or "").lower()
    head_sha = str(payload.get("head_sha") or "").lower()
    merge_base_sha = str(payload.get("merge_base_sha") or "").lower()
    trusted_checkout_sha = str(payload.get("trusted_checkout_sha") or "").lower()
    raw_paths = payload.get("changed_paths")
    if not isinstance(raw_paths, list):
        raise PathAGateError("observation_file_paths_not_array")
    paths_list = [str(p) for p in raw_paths]
    normalized = [_validate_observation_path(p) for p in paths_list]
    paths = tuple(sorted(dict.fromkeys(normalized)))
    if not paths:
        raise PathAGateError("observation_file_paths_empty")
    canonical_sha256 = str(payload.get("changed_paths_sha256") or "").lower()
    expected = hashlib.sha256("\n".join(paths).encode("utf-8")).hexdigest()
    if canonical_sha256 != expected:
        raise PathAGateError(
            "observation_file_digest_mismatch",
            f"{canonical_sha256}!={expected}",
        )
    for sha_value, field in (
        (base_sha, "base_sha"),
        (head_sha, "head_sha"),
        (merge_base_sha, "merge_base_sha"),
        (trusted_checkout_sha, "trusted_checkout_sha"),
    ):
        if not SHA_RE.fullmatch(sha_value):
            raise PathAGateError(f"observation_file_invalid_{field}")
    return TrustedChangedPathObservation(
        repository=repository,
        base_sha=base_sha,
        head_sha=head_sha,
        merge_base_sha=merge_base_sha,
        trusted_checkout_sha=trusted_checkout_sha,
        paths=paths,
        canonical_sha256=canonical_sha256,
    )


# ---------------------------------------------------------------------------
# GraphQL envelope normalization (Section 十二)
#
# Properly unwrap ``data.repository.issue`` and require complete label
# observation.  Fails closed on any malformation.
# ---------------------------------------------------------------------------


def normalize_issue_graphql_envelope(
    raw: Mapping[str, Any],
    *,
    labels_rest_pages: Any = None,
) -> dict[str, Any]:
    """Normalize a raw GraphQL issue response.

    ``raw`` must follow ``{"data": {"repository": {"issue": {...}}}}``.  Top-
    level ``errors`` fail closed.  ``lastEditedAt`` must be present (may be
    ``None`` when the Issue was never edited).

    Labels are taken from ``labels_rest_pages`` (REST ``--paginate --slurp``
    output, an array of pages each an array of label objects) when supplied.
    Otherwise the GraphQL ``labels`` block is used, but it must report
    ``hasNextPage == false`` — an unpaginated partial label set fails closed.
    """

    if not isinstance(raw, Mapping):
        raise PathAGateError("graphql_response_not_object")
    if raw.get("errors"):
        raise PathAGateError("graphql_top_level_errors")
    data = raw.get("data")
    if not isinstance(data, Mapping):
        raise PathAGateError("graphql_missing_data")
    repository = data.get("repository")
    if not isinstance(repository, Mapping):
        raise PathAGateError("graphql_missing_repository")
    issue = repository.get("issue")
    if not isinstance(issue, Mapping):
        raise PathAGateError("graphql_missing_issue")
    for key in ("number", "state", "body", "createdAt", "lastEditedAt"):
        if key not in issue:
            raise PathAGateError("graphql_missing_issue_key", key)

    labels: list[dict[str, Any]] = []
    if labels_rest_pages is not None:
        if not isinstance(labels_rest_pages, list):
            raise PathAGateError("graphql_labels_rest_not_array")
        for page_index, page in enumerate(labels_rest_pages):
            if not isinstance(page, list):
                raise PathAGateError(
                    "graphql_labels_rest_page_not_array", str(page_index)
                )
            for entry in page:
                if not isinstance(entry, Mapping):
                    raise PathAGateError("graphql_labels_rest_entry_not_object")
                name = str(entry.get("name") or "")
                if not name:
                    raise PathAGateError("graphql_labels_rest_entry_missing_name")
                labels.append({"name": name})
    else:
        labels_obj = issue.get("labels")
        if not isinstance(labels_obj, Mapping):
            raise PathAGateError("graphql_labels_not_object")
        nodes = labels_obj.get("nodes")
        if not isinstance(nodes, list):
            raise PathAGateError("graphql_labels_nodes_not_array")
        page_info = labels_obj.get("pageInfo")
        if not isinstance(page_info, Mapping):
            raise PathAGateError("graphql_labels_page_info_missing")
        has_next = page_info.get("hasNextPage")
        if has_next is True:
            raise PathAGateError("graphql_labels_unpaginated_has_next")
        for entry in nodes:
            if not isinstance(entry, Mapping):
                raise PathAGateError("graphql_labels_node_not_object")
            name = str(entry.get("name") or "")
            if not name:
                raise PathAGateError("graphql_labels_node_missing_name")
            labels.append({"name": name})

    # Deterministic dedup + sort by casefolded name.
    seen: set[str] = set()
    unique: list[dict[str, Any]] = []
    for entry in sorted(labels, key=lambda e: str(e.get("name") or "").casefold()):
        name = str(entry.get("name") or "")
        cf = name.casefold()
        if cf in seen:
            continue
        seen.add(cf)
        unique.append({"name": name})

    last_edited = issue["lastEditedAt"]
    if last_edited is not None and not isinstance(last_edited, str):
        raise PathAGateError("graphql_last_edited_at_invalid_type")

    return {
        "number": issue["number"],
        "state": issue["state"],
        "body": issue["body"],
        "createdAt": issue["createdAt"],
        "lastEditedAt": last_edited,
        "labels": unique,
    }


# ---------------------------------------------------------------------------
# Path-A R1 verification reusing a trusted route observation (Section 十一)
# ---------------------------------------------------------------------------


def verify_path_a_r1_with_observation(
    *,
    event_name: str,
    event: Mapping[str, Any],
    issue: Mapping[str, Any],
    approval_events: Iterable[Mapping[str, Any]],
    approver_permission: str,
    observation: TrustedChangedPathObservation,
    expected_repository: str,
    expected_authority_revision: str | None = None,
) -> dict[str, Any]:
    """Verify ordinary R1 authority reusing a trusted route observation.

    The observation supplies the canonical changed paths and SHAs.  This never
    re-runs ``changed_paths_for_event`` (which would require HEAD == candidate
    head).  The event's base/head SHAs must match the observation.
    """

    if event_name not in ("pull_request", "pull_request_target") or not isinstance(
        event.get("pull_request"), Mapping
    ):
        raise PathAGateError("event_not_pull_request")
    repository = str((event.get("repository") or {}).get("full_name") or "")
    if repository != expected_repository:
        raise PathAGateError("repository_mismatch", repository)
    if observation.repository != expected_repository:
        raise PathAGateError("observation_repository_mismatch", observation.repository)

    pr = event["pull_request"]
    event_base = str((pr.get("base") or {}).get("sha") or "").lower()
    event_head = str((pr.get("head") or {}).get("sha") or "").lower()
    if event_base != observation.base_sha:
        raise PathAGateError(
            "observation_event_base_mismatch",
            f"{event_base}!={observation.base_sha}",
        )
    if event_head != observation.head_sha:
        raise PathAGateError(
            "observation_event_head_mismatch",
            f"{event_head}!={observation.head_sha}",
        )

    return verify_path_a_r1(
        event_name=event_name,
        event=event,
        issue=issue,
        approval_events=approval_events,
        approver_permission=approver_permission,
        changed_paths=observation.paths,
        merge_base_sha=observation.merge_base_sha,
        expected_repository=expected_repository,
        expected_authority_revision=expected_authority_revision,
    )
