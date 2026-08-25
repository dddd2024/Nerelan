"""Fail-closed Path-A R1 authority verification and task-scoped CI selection."""

from __future__ import annotations

import hashlib
import json
import os
import re
import subprocess
import sys
import unicodedata
import urllib.request
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
    "integration_base_ref",
    "base_sha",
    "exact_head_sha",
)
SHA256_RE = re.compile(r"^[0-9a-f]{64}$")
SHA_RE = re.compile(r"^[0-9a-f]{40}$")
SHELL_META_RE = re.compile(r"(?:&&|\|\||[;`|<>]|\$\(|\$\{)")

ACTIVATION_DRAFT = "ACTIVATION_DRAFT"
IMPLEMENTATION_DRAFT = "IMPLEMENTATION_DRAFT"
READY_FINAL_READINESS = "READY_FINAL_READINESS"
LIFECYCLE_STAGES = (ACTIVATION_DRAFT, IMPLEMENTATION_DRAFT, READY_FINAL_READINESS)

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
BASE_PLATFORM_TASK_CHECK = TaskCheck(
    check_id="base_platform",
    argv=("python", "-m", "pytest", "tests/base_platform", "-q"),
    required_targets=("tests/base_platform",),
)
PLATFORM_V1_TASK_CHECK = TaskCheck(
    check_id="platform_v1",
    argv=("python", "-m", "pytest", "tests/platform_v1", "-q"),
    required_targets=("tests/platform_v1",),
)
TEAM_TARGETS_TASK_CHECK = TaskCheck(
    check_id="team_targets",
    argv=(
        "python", "-m", "pytest",
        "tests/test_development_graph.py",
        "tests/test_team_graph.py",
        "-q",
    ),
    required_targets=("tests/test_development_graph.py", "tests/test_team_graph.py"),
)

BASELINE_CHECK = BASELINE_TASK_CHECK.command
PATH_A_CHECK = PATH_A_TASK_CHECK.command
BASE_PLATFORM_CHECK = BASE_PLATFORM_TASK_CHECK.command
PLATFORM_V1_CHECK = PLATFORM_V1_TASK_CHECK.command
TEAM_TARGETS_CHECK = TEAM_TARGETS_TASK_CHECK.command

TASK_CHECK_MAPPING = (
    (
        ("reverse_agent/platform_v1/**", "tests/platform_v1/**"),
        PLATFORM_V1_TASK_CHECK,
    ),
    (
        (
            "reverse_agent/architecture/contracts.py",
            "reverse_agent/workflows/team_graph.py",
            "reverse_agent/workflows/nodes/acceptance_gate.py",
            "tests/test_development_graph.py",
            "tests/test_team_graph.py",
        ),
        TEAM_TARGETS_TASK_CHECK,
    ),
    (
        ("reverse_agent/base_platform/**", "tests/base_platform/**"),
        BASE_PLATFORM_TASK_CHECK,
    ),
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
    integration_base_ref: str
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
            integration_base_ref=payload["integration_base_ref"].strip(),
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
    integration_base_ref: str
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
            "integration_base_ref": self.integration_base_ref,
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
            str(issue.get("content_last_edited_at"))
            if issue.get("content_last_edited_at")
            else None
        ),
        pr_number=pr_number,
        pr_body_digest=issue_body_digest(str(pr.get("body") or "")),
        pr_draft_state=(
            pr.get("draft") if isinstance(pr.get("draft"), bool) else None
        ),
        pr_auto_merge_state=pr.get("auto_merge"),
        integration_base_ref=str((pr.get("base") or {}).get("ref") or ""),
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
        paths.append(normalized)
    if not paths:
        raise PathAGateError("issue_allowed_paths_empty")
    return tuple(paths)


def _path_matches(path: str, pattern: str) -> bool:
    normalized = path.replace("\\", "/").lstrip("./")
    candidate = pattern.replace("\\", "/").lstrip("./")
    if candidate.endswith("/**"):
        prefix = candidate[:-3].rstrip("/")
        return normalized == prefix or normalized.startswith(prefix + "/")
    return fnmatchcase(normalized, candidate)


def _minimum_path_risk(path: str) -> tuple[str, str] | None:
    canonical_path = path.replace("\\", "/").casefold()
    matches = tuple(
        (minimum_risk, pattern)
        for pattern, minimum_risk in ORDINARY_R1_PATH_RISK_POLICY
        if _path_matches(canonical_path, pattern.casefold())
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
    stage: str | None = None,
    empty_delta: bool | None = None,
) -> dict[str, Any]:
    """Verify a stage-aware Path-A R1 authority snapshot.

    Stages are mutually exclusive lifecycle outcomes and are inferred
    from live PR state plus live git truth unless the caller passes an
    explicit stage for unit-testing a specific branch.

    - ACTIVATION_DRAFT:  PASS with zero implementation delta; the gate
      returns implementation_authority=false and no product acceptance.
    - IMPLEMENTATION_DRAFT: preserves every existing Path-A R1 check
      and returns PATH_A_R1_AUTHORIZED.
    - READY_FINAL_READINESS: revalidates every live authority input
      against a freshly computed authority revision; the gate returns
      READY_FINAL_READINESS without granting implementation authority.
    """

    if stage is not None and stage not in LIFECYCLE_STAGES:
        raise PathAGateError("invalid_stage", stage)

    if event_name != "pull_request" or not isinstance(event.get("pull_request"), Mapping):
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

    pr_open = pr.get("state") == "open"
    pr_draft_state = (
        pr.get("draft") if isinstance(pr.get("draft"), bool) else None
    )
    pr_draft = pr_draft_state is True
    changed = tuple(dict.fromkeys(path.replace("\\", "/") for path in changed_paths))
    empty = bool(empty_delta) if empty_delta is not None else len(changed) == 0
    inferred_stage = infer_path_a_lifecycle_stage(
        pr_open=pr_open,
        pr_draft=pr_draft_state,
        empty_delta=empty,
    )
    if stage is not None and stage != inferred_stage:
        raise PathAGateError(
            "stage_mismatch",
            (
                f"expected={stage};inferred={inferred_stage};"
                f"empty_delta={empty};draft={pr_draft_state}"
            ),
        )
    stage_branch = stage if stage is not None else inferred_stage
    if stage_branch == ACTIVATION_DRAFT:
        if not pr_open:
            raise PathAGateError("pr_not_open")
        if not pr_draft:
            raise PathAGateError("activation_draft_pr_must_be_draft")
        if str(issue.get("state") or "").lower() != "open":
            raise PathAGateError("source_issue_not_open")
        if "r1" not in labels:
            raise PathAGateError("issue_not_r1")
        if "r1-approved" not in labels:
            raise PathAGateError("issue_not_r1_approved")
        disallowed_tiers = sorted(labels & {"r2", "r3"})
        if disallowed_tiers:
            raise PathAGateError(
                "issue_privileged_risk_tier", ",".join(disallowed_tiers)
            )
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
        last_edited_at = issue.get("content_last_edited_at")
        if last_edited_at:
            try:
                last_edit = datetime.fromisoformat(
                    str(last_edited_at).replace("Z", "+00:00")
                )
                approval_time = datetime.fromisoformat(
                    snapshot.approval_event_or_time.replace("Z", "+00:00")
                )
            except ValueError as exc:
                raise PathAGateError("issue_edit_time_invalid") from exc
            if last_edit >= approval_time:
                raise PathAGateError("issue_body_edit_not_strictly_before_approval")
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
        if str(base.get("ref") or "") != snapshot.integration_base_ref:
            raise PathAGateError("integration_base_ref_mismatch")
        if str(base.get("sha") or "").lower() != snapshot.base_sha:
            raise PathAGateError("base_sha_mismatch")
        if merge_base_sha.lower() != snapshot.base_sha:
            raise PathAGateError("merge_base_mismatch")
        if pr.get("auto_merge") not in (None, False):
            raise PathAGateError("auto_merge_forbidden")
        return {
            "schema_version": 1,
            "gate_name": "path-a-r1-gate",
            "gate_status": "PATH_A_R1_AUTHORIZED",
            "mode": "path_a_r1",
            "repository": expected_repository,
            "issue_number": snapshot.issue_number,
            "target_branch": snapshot.target_branch,
            "integration_base_ref": snapshot.integration_base_ref,
            "base_sha": snapshot.base_sha,
            "exact_head_sha": snapshot.exact_head_sha,
            "authority_revision": authority_revision,
            "authority_revalidation_required": True,
            "lifecycle_stage": ACTIVATION_DRAFT,
            "implementation_authority": False,
            "product_accepted": False,
            "implementation_complete": False,
            "merge_authority": False,
            "ready_authority": False,
            "no_task_checks": True,
            "empty_delta": True,
            "changed_paths": [],
            "selected_checks": [],
            "authority_source": "live_github_authority_revision",
            "comments_authoritative": False,
            "issue_commands_executed": False,
        }
    if stage_branch == READY_FINAL_READINESS:
        if not pr_open:
            raise PathAGateError("pr_not_open")
        if pr_draft:
            raise PathAGateError("ready_pr_must_be_ready_for_review")
    else:
        if not (pr_open and pr_draft):
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

    last_edited_at = issue.get("content_last_edited_at")
    if last_edited_at:
        try:
            last_edit = datetime.fromisoformat(str(last_edited_at).replace("Z", "+00:00"))
            approval_time = datetime.fromisoformat(
                snapshot.approval_event_or_time.replace("Z", "+00:00")
            )
        except ValueError as exc:
            raise PathAGateError("issue_edit_time_invalid") from exc
        if last_edit >= approval_time:
            raise PathAGateError("issue_body_edit_not_strictly_before_approval")

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
    if str(base.get("ref") or "") != snapshot.integration_base_ref:
        raise PathAGateError("integration_base_ref_mismatch")
    if str(base.get("sha") or "").lower() != snapshot.base_sha:
        raise PathAGateError("base_sha_mismatch")
    if merge_base_sha.lower() != snapshot.base_sha:
        raise PathAGateError("merge_base_mismatch")
    if pr.get("auto_merge") not in (None, False):
        raise PathAGateError("auto_merge_forbidden")

    if stage_branch == IMPLEMENTATION_DRAFT:
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

    lifecycle_stage = stage if stage is not None else inferred_stage
    is_ready = lifecycle_stage == READY_FINAL_READINESS
    return {
        "schema_version": 1,
        "gate_name": "path-a-r1-gate",
        "gate_status": "PATH_A_R1_AUTHORIZED",
        "mode": "path_a_r1",
        "repository": expected_repository,
        "issue_number": snapshot.issue_number,
        "target_branch": snapshot.target_branch,
        "integration_base_ref": snapshot.integration_base_ref,
        "base_sha": snapshot.base_sha,
        "exact_head_sha": snapshot.exact_head_sha,
        "authority_revision": authority_revision,
        "authority_revalidation_required": True,
        "lifecycle_stage": lifecycle_stage,
        "implementation_authority": not is_ready,
        "product_accepted": lifecycle_stage == IMPLEMENTATION_DRAFT,
        "implementation_complete": lifecycle_stage == IMPLEMENTATION_DRAFT,
        "merge_authority": False,
        "ready_authority": is_ready,
        "no_task_checks": is_ready,
        "empty_delta": empty,
        "changed_paths": list(changed),
        "selected_checks": list(select_task_checks(changed)["commands"])
        if lifecycle_stage == IMPLEMENTATION_DRAFT
        else [],
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


def _collect_paginated_list(
    path: str,
    *,
    expected_count: int | None = None,
) -> list[Mapping[str, Any]]:
    items: list[Mapping[str, Any]] = []
    next_path: str | None = path
    seen: set[str] = set()
    while next_path:
        if next_path in seen:
            raise PathAGateError("github_pagination_cycle")
        seen.add(next_path)
        payload, next_path = _github_get_page(next_path)
        if not isinstance(payload, list) or any(not isinstance(item, Mapping) for item in payload):
            raise PathAGateError("github_paginated_payload_invalid")
        items.extend(payload)
    if expected_count is not None and len(items) != expected_count:
        raise PathAGateError(
            "github_file_pagination_incomplete",
            f"observed={len(items)} expected={expected_count}",
        )
    return items


def _collect_paginated_compare_files(path: str) -> list[Mapping[str, Any]]:
    files: list[Mapping[str, Any]] = []
    next_path: str | None = path
    seen: set[str] = set()
    incomplete = False
    while next_path:
        if next_path in seen:
            raise PathAGateError("github_pagination_cycle")
        seen.add(next_path)
        payload, next_path = _github_get_page(next_path)
        if not isinstance(payload, Mapping):
            raise PathAGateError("github_compare_payload_invalid")
        page_files = payload.get("files")
        if not isinstance(page_files, list) or any(
            not isinstance(item, Mapping) for item in page_files
        ):
            incomplete = True
            continue
        files.extend(page_files)
    if incomplete or len(files) >= 300:
        raise PathAGateError("github_compare_files_may_be_truncated")
    return files


def _collect_changed_paths_for_event(
    event: Mapping[str, Any],
    repo_root: Path,
) -> tuple[tuple[str, ...], str, str]:
    """Collect changed paths plus exact head/base bindings from a checked-out event."""

    pr = event.get("pull_request")
    if isinstance(pr, Mapping):
        base_sha = str((pr.get("base") or {}).get("sha") or "")
        head_sha = str((pr.get("head") or {}).get("sha") or "")
    else:
        base_sha = str(event.get("before") or "")
        head_sha = str(event.get("after") or "")
    actual_head = subprocess.check_output(
        ["git", "rev-parse", "HEAD"], cwd=repo_root, text=True
    ).strip()
    if not SHA_RE.fullmatch(head_sha) or actual_head != head_sha:
        raise PathAGateError("workflow_exact_head_mismatch", f"{actual_head}!={head_sha}")
    if not SHA_RE.fullmatch(base_sha):
        raise PathAGateError("workflow_base_sha_missing")
    diff = subprocess.run(
        ["git", "diff", "--name-status", "-M", "-C", f"{base_sha}...{head_sha}"],
        cwd=repo_root,
        check=False,
        capture_output=True,
        text=True,
    )
    if diff.returncode == 0:
        changed = _paths_from_diff_name_status(diff.stdout)
    else:
        repository = str((event.get("repository") or {}).get("full_name") or "")
        if not repository:
            raise PathAGateError("event_repository_missing")
        if isinstance(pr, Mapping):
            number = int(pr.get("number") or event.get("number") or 0)
            if not number:
                raise PathAGateError("event_pull_request_number_missing")
            expected_count = int(pr.get("changed_files") or 0)
            if expected_count <= 0:
                raise PathAGateError("event_changed_file_count_missing")
            files = _collect_paginated_list(
                f"/repos/{repository}/pulls/{number}/files?per_page=100",
                expected_count=expected_count,
            )
        else:
            files = _collect_paginated_compare_files(
                f"/repos/{repository}/compare/{base_sha}...{head_sha}?per_page=100"
            )
        changed = _paths_from_api_file_entries(files)
    return changed, base_sha, head_sha


@dataclass(frozen=True)
class DeltaObservation:
    changed_paths: tuple[str, ...]
    base_sha: str
    head_sha: str
    empty_delta: bool


def changed_paths_for_event(
    event: Mapping[str, Any], repo_root: Path
) -> DeltaObservation:
    """Return a stage-aware delta observation plus exact head/base bindings."""

    changed, base_sha, head_sha = _collect_changed_paths_for_event(event, repo_root)
    return DeltaObservation(
        changed_paths=changed,
        base_sha=base_sha,
        head_sha=head_sha,
        empty_delta=(len(changed) == 0),
    )


def infer_path_a_lifecycle_stage(
    *,
    pr_open: bool,
    pr_draft: bool | None,
    empty_delta: bool,
) -> str:
    """Classify a Path-A event by its live PR state and git truth.

    The classifier trusts only current git/GitHub observations; it never
    carries stage state across workflow runs.  Draft + empty Delta is the
    normal ACTIVATION_DRAFT bootstrap.  A non-empty Draft Delta is the
    IMPLEMENTATION_DRAFT.  Once the PR is marked ready_for_review the
    gate may observe READY_FINAL_READINESS only when an actual
    implementation delta exists; a Ready-without-delta event is fail-closed
    with ready_without_implementation_delta.  A missing, None, or
    non-bool draft state is fail-closed with pr_draft_state_invalid.
    """

    if not pr_open:
        raise PathAGateError("pr_not_open")
    if not isinstance(pr_draft, bool):
        raise PathAGateError("pr_draft_state_invalid")
    if pr_draft:
        if empty_delta:
            return ACTIVATION_DRAFT
        return IMPLEMENTATION_DRAFT
    if empty_delta:
        raise PathAGateError("ready_without_implementation_delta")
    return READY_FINAL_READINESS


def _validate_stage_for_delta(
    *,
    stage: str,
    pr_open: bool,
    pr_draft: bool | None,
    empty_delta: bool,
) -> None:
    inferred = infer_path_a_lifecycle_stage(
        pr_open=pr_open,
        pr_draft=pr_draft,
        empty_delta=empty_delta,
    )
    if stage != inferred:
        raise PathAGateError(
            "stage_mismatch",
            (
                f"expected={stage};inferred={inferred};"
                f"empty_delta={empty_delta};draft={pr_draft}"
            ),
        )


def _github_headers() -> dict[str, str]:
    token = os.environ.get("GITHUB_TOKEN", "")
    if not token:
        raise PathAGateError("github_token_missing")
    return {
        "Accept": "application/vnd.github+json",
        "Authorization": f"Bearer {token}",
        "X-GitHub-Api-Version": "2022-11-28",
        "User-Agent": "reverse-agent-path-a-gate",
    }


def _github_get_page(path: str) -> tuple[Any, str | None]:
    url = path if path.startswith("https://") else f"https://api.github.com{path}"
    request = urllib.request.Request(
        url,
        headers=_github_headers(),
    )
    with urllib.request.urlopen(request, timeout=30) as response:
        payload = json.load(response)
        link = str(response.headers.get("Link") or "")
    next_match = re.search(r'<([^>]+)>;\s*rel="next"', link)
    return payload, next_match.group(1) if next_match else None


def _github_get(path: str) -> Any:
    payload, next_path = _github_get_page(path)
    if next_path:
        raise PathAGateError("github_unexpected_pagination", path)
    return payload


def _github_graphql(query: str, variables: Mapping[str, Any]) -> Mapping[str, Any]:
    request = urllib.request.Request(
        "https://api.github.com/graphql",
        data=json.dumps({"query": query, "variables": dict(variables)}).encode("utf-8"),
        headers={**_github_headers(), "Content-Type": "application/json"},
        method="POST",
    )
    with urllib.request.urlopen(request, timeout=30) as response:
        payload = json.load(response)
    if not isinstance(payload, Mapping) or payload.get("errors"):
        raise PathAGateError("github_graphql_error")
    return payload


def _issue_last_edited_at(repository: str, issue_number: int) -> str | None:
    owner, name = repository.split("/", 1)
    payload = _github_graphql(
        """
        query($owner: String!, $name: String!, $number: Int!) {
          repository(owner: $owner, name: $name) {
            issue(number: $number) { lastEditedAt }
          }
        }
        """,
        {"owner": owner, "name": name, "number": issue_number},
    )
    issue = ((payload.get("data") or {}).get("repository") or {}).get("issue")
    if not isinstance(issue, Mapping):
        raise PathAGateError("github_issue_edit_observation_missing")
    value = issue.get("lastEditedAt")
    return str(value) if value else None


def run_path_a_gate(*, event_path: Path, repository: str, repo_root: Path) -> dict[str, Any]:
    event = json.loads(event_path.read_text(encoding="utf-8"))
    event_pr = event.get("pull_request") or {}
    pr_number = int(event.get("number") or event_pr.get("number") or 0)
    if pr_number <= 0:
        raise PathAGateError("github_pr_number_missing")
    live_pr = _github_get(f"/repos/{repository}/pulls/{pr_number}")
    if not isinstance(live_pr, Mapping):
        raise PathAGateError("github_pr_payload_invalid")
    event = {**event, "number": pr_number, "pull_request": dict(live_pr)}
    snapshot = parse_snapshot(str(live_pr.get("body") or ""))
    issue = _github_get(f"/repos/{repository}/issues/{snapshot.issue_number}")
    if not isinstance(issue, Mapping):
        raise PathAGateError("github_issue_payload_invalid")
    issue = dict(issue)
    issue["content_last_edited_at"] = _issue_last_edited_at(
        repository,
        snapshot.issue_number,
    )
    approval_events = _collect_paginated_list(
        f"/repos/{repository}/issues/{snapshot.issue_number}/events?per_page=100"
    )
    owner = repository.split("/", 1)[0]
    if snapshot.approved_by == owner:
        permission = "admin"
    else:
        permission_payload = _github_get(
            f"/repos/{repository}/collaborators/{snapshot.approved_by}/permission"
        )
        permission = str(permission_payload.get("permission") or "")
    delta = changed_paths_for_event(event, repo_root)
    merge_base = subprocess.check_output(
        ["git", "merge-base", "HEAD", snapshot.base_sha],
        cwd=repo_root,
        text=True,
    ).strip()
    result = verify_path_a_r1(
        event_name=os.environ.get("GITHUB_EVENT_NAME", ""),
        event=event,
        issue=issue,
        approval_events=approval_events,
        approver_permission=permission,
        changed_paths=delta.changed_paths,
        merge_base_sha=merge_base,
        expected_repository=repository,
        expected_authority_revision=(
            os.environ.get("PATH_A_EXPECTED_AUTHORITY_REVISION") or None
        ),
        stage=infer_path_a_lifecycle_stage(
            pr_open=str(live_pr.get("state") or "").lower() == "open",
            pr_draft=(
                live_pr.get("draft") if isinstance(live_pr.get("draft"), bool) else None
            ),
            empty_delta=delta.empty_delta,
        ),
        empty_delta=delta.empty_delta,
    )
    result["live_github_state_observed"] = True
    return result


def write_task_check_outputs(
    *, event_path: Path, repo_root: Path, output_path: Path | None
) -> dict[str, Any]:
    event = json.loads(event_path.read_text(encoding="utf-8"))
    delta = changed_paths_for_event(event, repo_root)
    if delta.empty_delta:
        raise PathAGateError("changed_paths_empty")
    changed = delta.changed_paths
    selected = select_task_checks(changed, repo_root=repo_root)
    payload = {
        "schema_version": 1,
        "gate_name": "task-scoped-check-selection",
        "gate_status": "TASK_CHECKS_SELECTED",
        "base_sha": delta.base_sha,
        "exact_head_sha": delta.head_sha,
        "changed_paths": list(changed),
        "check_ids": list(selected["check_ids"]),
        "commands": [BASELINE_CHECK, *selected["commands"]],
    }
    if output_path is not None:
        with output_path.open("a", encoding="utf-8", newline="\n") as stream:
            stream.write(f"base_platform={'true' if 'base_platform' in selected['check_ids'] else 'false'}\n")
            stream.write(f"path_a_gate={'true' if 'path_a_gate' in selected['check_ids'] else 'false'}\n")
            stream.write(f"exact_head_sha={head_sha}\n")
            stream.write("selected_checks_json=" + json.dumps(payload["commands"], separators=(",", ":")) + "\n")
    return payload


def execute_task_checks(payload: Mapping[str, Any], *, repo_root: Path) -> None:
    """Execute only commands selected from the immutable repository mapping."""

    check_by_command = {check.command: check for _, check in TASK_CHECK_MAPPING}
    for command in payload.get("commands", []):
        if command == BASELINE_TASK_CHECK.command:
            continue
        check = check_by_command.get(str(command))
        if check is None:
            raise PathAGateError("untrusted_task_check_command", str(command))
        for target in check.required_targets:
            if not (repo_root / target).exists():
                raise PathAGateError(
                    "mapped_test_target_missing",
                    f"{check.check_id}:{target}",
                )
        argv = list(check.argv)
        if argv[0] == "python":
            argv[0] = sys.executable
        subprocess.run(argv, cwd=repo_root, check=True)
