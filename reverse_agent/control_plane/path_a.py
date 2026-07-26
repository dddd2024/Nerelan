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
from fnmatch import fnmatch
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

ORDINARY_R1_FORBIDDEN_PATHS = (
    "project_state/**",
    ".github/workflows/**",
    "pyproject.toml",
    "requirements*.txt",
    "setup.py",
    "setup.cfg",
    "pytest.ini",
    "poetry.lock",
    "Pipfile*",
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

BASELINE_CHECK = BASELINE_TASK_CHECK.command
PATH_A_CHECK = PATH_A_TASK_CHECK.command
BASE_PLATFORM_CHECK = BASE_PLATFORM_TASK_CHECK.command

TASK_CHECK_MAPPING = (
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
    paths = tuple(
        line.strip().replace("\\", "/")
        for line in block.splitlines()
        if line.strip() and not line.lstrip().startswith("#")
    )
    if not paths:
        raise PathAGateError("issue_allowed_paths_empty")
    if any(path.startswith("/") or ".." in Path(path).parts for path in paths):
        raise PathAGateError("issue_allowed_paths_invalid")
    return paths


def _path_matches(path: str, pattern: str) -> bool:
    normalized = path.replace("\\", "/").lstrip("./")
    candidate = pattern.replace("\\", "/").lstrip("./")
    if candidate.endswith("/**"):
        prefix = candidate[:-3].rstrip("/")
        return normalized == prefix or normalized.startswith(prefix + "/")
    return fnmatch(normalized, candidate)


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
) -> dict[str, Any]:
    """Verify a complete ordinary R1 authority snapshot without executing Issue text."""

    if event_name != "pull_request" or not isinstance(event.get("pull_request"), Mapping):
        raise PathAGateError("event_not_pull_request")
    repository = str((event.get("repository") or {}).get("full_name") or "")
    if repository != expected_repository:
        raise PathAGateError("repository_mismatch", repository)

    pr = event["pull_request"]
    if pr.get("state") != "open" or pr.get("draft") is not True:
        raise PathAGateError("pr_must_be_open_draft")
    snapshot = parse_snapshot(str(pr.get("body") or ""))
    if snapshot.repository != expected_repository:
        raise PathAGateError("snapshot_repository_mismatch")

    issue_number = int(issue.get("number") or 0)
    if snapshot.issue_number != issue_number:
        raise PathAGateError("snapshot_issue_mismatch")
    if str(issue.get("state") or "").lower() != "open":
        raise PathAGateError("source_issue_not_open")
    labels = {
        str(label.get("name") if isinstance(label, Mapping) else label)
        for label in issue.get("labels", [])
    }
    if "r1" not in labels:
        raise PathAGateError("issue_not_r1")
    if "r1-approved" not in labels:
        raise PathAGateError("issue_not_r1_approved")
    disallowed_tiers = sorted(labels & {"r2", "r3"})
    if disallowed_tiers:
        raise PathAGateError("issue_privileged_risk_tier", ",".join(disallowed_tiers))
    if approver_permission not in {"admin", "maintain"}:
        raise PathAGateError("approver_not_owner_or_maintainer")

    approval_transitions = [
        item for item in approval_events
        if str(item.get("event") or "") in {"labeled", "unlabeled"}
        and str((item.get("label") or {}).get("name") or "") == "r1-approved"
    ]
    approval_transitions.sort(
        key=lambda item: (
            str(item.get("created_at") or ""),
            int(item.get("id") or 0),
        )
    )
    if not approval_transitions:
        raise PathAGateError("approval_event_missing")
    effective_approval = approval_transitions[-1]
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
        if last_edit > approval_time:
            raise PathAGateError("issue_body_edited_after_approval")

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
    if pr.get("auto_merge") not in (None, False):
        raise PathAGateError("auto_merge_forbidden")

    changed = tuple(dict.fromkeys(path.replace("\\", "/") for path in changed_paths))
    if not changed:
        raise PathAGateError("changed_paths_empty")
    outside = _paths_outside(changed, parse_allowed_paths(issue_body))
    if outside:
        raise PathAGateError("changed_paths_outside_allowed", ",".join(outside))
    forbidden = tuple(
        path for path in changed
        if any(_path_matches(path, pattern) for pattern in ORDINARY_R1_FORBIDDEN_PATHS)
    )
    if forbidden:
        raise PathAGateError("ordinary_r1_forbidden_paths", ",".join(forbidden))

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
        "changed_paths": list(changed),
        "selected_checks": list(select_task_checks(changed)["commands"]),
        "authority_source": "immutable_work_item_snapshot",
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


def changed_paths_for_event(event: Mapping[str, Any], repo_root: Path) -> tuple[tuple[str, ...], str, str]:
    """Return changed paths plus exact head/base bindings from a checked-out event."""

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
    if not changed:
        raise PathAGateError("changed_paths_empty")
    return changed, base_sha, head_sha


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
    snapshot = parse_snapshot(str((event.get("pull_request") or {}).get("body") or ""))
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
    changed, _, _ = changed_paths_for_event(event, repo_root)
    merge_base = subprocess.check_output(
        ["git", "merge-base", "HEAD", snapshot.base_sha],
        cwd=repo_root,
        text=True,
    ).strip()
    return verify_path_a_r1(
        event_name=os.environ.get("GITHUB_EVENT_NAME", ""),
        event=event,
        issue=issue,
        approval_events=approval_events,
        approver_permission=permission,
        changed_paths=changed,
        merge_base_sha=merge_base,
        expected_repository=repository,
    )


def write_task_check_outputs(
    *, event_path: Path, repo_root: Path, output_path: Path | None
) -> dict[str, Any]:
    event = json.loads(event_path.read_text(encoding="utf-8"))
    changed, base_sha, head_sha = changed_paths_for_event(event, repo_root)
    selected = select_task_checks(changed, repo_root=repo_root)
    payload = {
        "schema_version": 1,
        "gate_name": "task-scoped-check-selection",
        "gate_status": "TASK_CHECKS_SELECTED",
        "base_sha": base_sha,
        "exact_head_sha": head_sha,
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
