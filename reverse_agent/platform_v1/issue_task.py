"""Bounded GitHub Issue intake for the Platform V1 coordinator."""

from __future__ import annotations

import hashlib
import json
import re
import subprocess
from dataclasses import dataclass
from typing import Any, Callable

from .contracts import PlatformWorkItem
from .policy_adapter import validate_work_item


_TASK_BLOCK = re.compile(r"```json\s*(\{.*?\})\s*```", re.DOTALL | re.IGNORECASE)
_SHA1 = re.compile(r"^[0-9a-f]{40}$")
_SAFE_CHECK = re.compile(r"^(?:python -m pytest(?: [A-Za-z0-9_./:\\-]+)*(?: -q)?|git diff --check(?: [0-9a-f.]+)?|git diff --check)$")
_BROAD_PATHS = frozenset({"", ".", "./", "/", "*", "**", "**/*", "./**"})
_REQUIRED_DENIALS = frozenset({
    "push_main", "merge", "mark_ready", "auto_merge", "force_push",
    "release", "deployment", "credential_publication",
})


class IssueTaskError(Exception):
    def __init__(self, code: str, detail: str = "") -> None:
        self.code = code
        self.detail = detail
        super().__init__(f"{code}:{detail}" if detail else code)


@dataclass(frozen=True)
class ApprovalObservation:
    approved_by: str
    approved_at: str
    event_id: str


@dataclass(frozen=True)
class LoadedIssueTask:
    work_item: PlatformWorkItem
    schema_version: int
    publication: str
    max_rework_attempts: int
    approval: ApprovalObservation
    issue_body_sha256: str
    normalized_issue_body: str

    @property
    def execution_id(self) -> str:
        return self.work_item.execution_id

    @property
    def task_digest(self) -> str:
        return self.work_item.digest


def _normalize_body(body: str) -> str:
    return body.replace("\r\n", "\n").replace("\r", "\n")


def _label_names(issue: dict[str, Any]) -> set[str]:
    names: set[str] = set()
    for label in issue.get("labels", []):
        if isinstance(label, dict):
            names.add(str(label.get("name", "")))
        else:
            names.add(str(label))
    return names


def _validate_path(raw: str) -> str:
    path = raw.replace("\\", "/").strip()
    if path in _BROAD_PATHS:
        raise IssueTaskError("broad_path_rejected", path)
    if path.startswith("/") or re.match(r"^[A-Za-z]:/", path):
        raise IssueTaskError("absolute_path_rejected", path)
    if any(part == ".." for part in path.split("/")):
        raise IssueTaskError("path_traversal_rejected", path)
    if path.startswith("./"):
        path = path[2:]
    return path


class IssueTaskLoader:
    def __init__(self, runner: Callable[..., subprocess.CompletedProcess[str]] = subprocess.run) -> None:
        self._runner = runner

    @staticmethod
    def parse(
        *,
        issue: dict[str, Any],
        events: list[dict[str, Any]],
        expected_repository: str,
        expected_base_sha: str,
    ) -> LoadedIssueTask:
        if str(issue.get("state", "")).upper() != "OPEN":
            raise IssueTaskError("issue_not_open")
        if "r1-approved" not in _label_names(issue):
            raise IssueTaskError("approval_label_missing")
        body = _normalize_body(str(issue.get("body", "")))
        blocks = _TASK_BLOCK.findall(body)
        if len(blocks) != 1:
            raise IssueTaskError("task_block_count_invalid", str(len(blocks)))
        try:
            task = json.loads(blocks[0])
        except json.JSONDecodeError as exc:
            raise IssueTaskError("task_json_invalid", str(exc)) from exc
        if not isinstance(task, dict):
            raise IssueTaskError("task_json_not_object")
        if int(task.get("schema_version", 0)) != 1:
            raise IssueTaskError("schema_version_unsupported")
        repository = str(task.get("repository", ""))
        if repository != expected_repository:
            raise IssueTaskError("repository_mismatch", repository)
        base_sha = str(task.get("base_sha") or task.get("base_ref") or "")
        if not _SHA1.fullmatch(base_sha) or base_sha != expected_base_sha:
            raise IssueTaskError("base_mismatch", base_sha)
        target_branch = str(task.get("target_branch", ""))
        if not target_branch or target_branch in {"main", "master"}:
            raise IssueTaskError("main_target_rejected", target_branch)
        publication = str(task.get("publication", ""))
        if publication != "draft_pr":
            raise IssueTaskError("publication_rejected", publication)
        raw_paths = task.get("allowed_paths", [])
        if not isinstance(raw_paths, list) or not raw_paths:
            raise IssueTaskError("empty_path_scope")
        allowed_paths = tuple(_validate_path(str(path)) for path in raw_paths)
        checks = task.get("required_checks", [])
        if not isinstance(checks, list) or not checks:
            raise IssueTaskError("required_checks_missing")
        required_checks = tuple(str(check).strip() for check in checks)
        for check in required_checks:
            if not _SAFE_CHECK.fullmatch(check) or any(token in check for token in (";", "&&", "||", "`", "$(`", ">", "<")):
                raise IssueTaskError("unbounded_shell_rejected", check)
        forbidden = tuple(str(value) for value in task.get("forbidden_operations", []))
        missing_denials = _REQUIRED_DENIALS - set(forbidden)
        if missing_denials:
            raise IssueTaskError("forbidden_operations_incomplete", ",".join(sorted(missing_denials)))
        risk_tier = str(task.get("risk_tier", ""))
        if risk_tier not in {"R0", "R1"}:
            raise IssueTaskError("risk_tier_rejected", risk_tier)
        max_rework_attempts = int(task.get("max_rework_attempts", -1))
        if max_rework_attempts < 0 or max_rework_attempts > 2:
            raise IssueTaskError("rework_limit_rejected", str(max_rework_attempts))
        owner = expected_repository.split("/", 1)[0]
        approval_events = [
            event for event in events
            if event.get("event") == "labeled"
            and isinstance(event.get("label"), dict)
            and event["label"].get("name") == "r1-approved"
            and isinstance(event.get("actor"), dict)
            and event["actor"].get("login") == owner
        ]
        if not approval_events:
            raise IssueTaskError("approval_event_missing")
        approval_event = approval_events[-1]
        digest = hashlib.sha256(body.encode("utf-8")).hexdigest()
        work_item = PlatformWorkItem(
            source_issue_number=int(issue.get("number", 0)),
            repository=repository,
            base_sha=base_sha,
            allowed_paths=allowed_paths,
            forbidden_operations=forbidden,
            acceptance_criteria=("approved_issue_task_complete",),
            goal=str(task.get("goal", "")),
            required_checks=required_checks,
            approved_issue_body_digest=digest,
            risk_tier=risk_tier,
            target_branch=target_branch,
        )
        validate_work_item(work_item)
        return LoadedIssueTask(
            work_item=work_item,
            schema_version=1,
            publication=publication,
            max_rework_attempts=max_rework_attempts,
            approval=ApprovalObservation(
                approved_by=owner,
                approved_at=str(approval_event.get("created_at", "")),
                event_id=str(approval_event.get("id", "")),
            ),
            issue_body_sha256=digest,
            normalized_issue_body=body,
        )

    def load(self, repository: str, issue_number: int, expected_base_sha: str) -> LoadedIssueTask:
        issue_result = self._runner(
            ["gh", "issue", "view", str(issue_number), "--repo", repository,
             "--json", "number,state,body,labels"],
            capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=60,
        )
        if issue_result.returncode != 0:
            raise IssueTaskError("gh_issue_view_failed", f"exit={issue_result.returncode}")
        events_result = self._runner(
            ["gh", "api", f"repos/{repository}/issues/{issue_number}/events?per_page=100"],
            capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=60,
        )
        if events_result.returncode != 0:
            raise IssueTaskError("gh_issue_events_failed", f"exit={events_result.returncode}")
        try:
            issue = json.loads(issue_result.stdout or "")
            events = json.loads(events_result.stdout or "")
        except json.JSONDecodeError as exc:
            raise IssueTaskError("gh_issue_json_invalid", str(exc)) from exc
        return self.parse(
            issue=issue,
            events=events,
            expected_repository=repository,
            expected_base_sha=expected_base_sha,
        )
