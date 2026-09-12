"""Read-only Attention Center projection over existing platform truth.

This module deliberately owns no notification persistence or runtime state.
It derives bounded attention items from the existing TaskStore,
PlatformControlStore, and RunReadModel projections.
"""

from __future__ import annotations

import hashlib
import json
import re
import unicodedata
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from enum import StrEnum
from typing import Any, Mapping
from urllib.parse import quote, urlsplit

from .control_store import PlatformControlStore
from .run_read_model import MAX_RUNS, RunReadModel
from .run_store import TaskStore


MAX_ATTENTION_ITEMS = 100
MAX_SOURCE_RECORDS = 100
_MAX_TITLE = 160
_MAX_STATUS = 64
_MAX_URL = 512
_ACTIVE_RUN_STATUSES = frozenset(
    {"PREPARING_WORKSPACE", "RUNNING", "RUNNING_FIXTURE", "VALIDATING"}
)
_REVIEW_STATUSES = frozenset({"READY_FOR_REVIEW", "READY_FOR_REVIEW_FIXTURE"})
_SENSITIVE_TEXT_RE = re.compile(
    r"(?i)(authorization|bearer|api[_-]?key|access[_-]?token|password|secret|"
    r"credential|private[_-]?key|chain[_-]?of[_-]?thought|prompt|response|"
    r"worktree|checkpoint[_-]?db|lease[_-]?owner)"
)
_OPAQUE_SECRET_RE = re.compile(
    r"(?i)(?:"
    r"(?<![a-z0-9])(?:sk|rk|pk|gh[pousr]|github_pat|xox[baprs])[-_][a-z0-9_-]{8,}|"
    r"AKIA[0-9A-Z]{16}|"
    r"eyJ[a-z0-9_-]{8,}\.[a-z0-9_-]{8,}\.[a-z0-9_-]{8,}|"
    r"-----BEGIN [A-Z ]*PRIVATE KEY-----|"
    r"(?:https?|ssh)://[^/\s:@]+:[^/\s@]+@"
    r")"
)


class AttentionReadModelError(ValueError):
    """Invalid bounded read request."""


class AttentionSeverity(StrEnum):
    HIGH = "HIGH"
    MEDIUM = "MEDIUM"


class AttentionKind(StrEnum):
    APPROVAL_REQUIRED = "APPROVAL_REQUIRED"
    RECOVERY_REQUIRED = "RECOVERY_REQUIRED"
    RUN_BLOCKED = "RUN_BLOCKED"
    RUN_FAILED = "RUN_FAILED"
    RUN_STALLED = "RUN_STALLED"
    VERIFICATION_FAILED = "VERIFICATION_FAILED"
    REVIEW_REQUIRED = "REVIEW_REQUIRED"
    DRAFT_PR_READY = "DRAFT_PR_READY"
    PUBLICATION_FAILED = "PUBLICATION_FAILED"


@dataclass(frozen=True, slots=True)
class AttentionItem:
    attention_id: str
    kind: AttentionKind
    severity: AttentionSeverity
    entity_type: str
    entity_id: str
    goal_id: str
    task_id: str
    title: str
    summary: str
    deep_link: str
    external_url: str
    source_status: str
    observed_at: str

    def to_dict(self) -> dict[str, Any]:
        payload = asdict(self)
        payload["kind"] = self.kind.value
        payload["severity"] = self.severity.value
        return payload


class AttentionReadModel:
    """Derive user-action attention without creating another source of truth."""

    def __init__(
        self,
        *,
        store: TaskStore,
        control_store: PlatformControlStore,
        run_read_model: Any | None = None,
    ) -> None:
        self.store = store
        self.control_store = control_store
        self.run_read_model = run_read_model or RunReadModel(
            store=store, control_store=control_store
        )

    def list_items(self, *, limit: int = MAX_ATTENTION_ITEMS) -> tuple[AttentionItem, ...]:
        bounded = _validate_limit(limit)
        items: list[AttentionItem] = []

        for goal in self.control_store.list_goals(limit=MAX_SOURCE_RECORDS):
            item = self._goal_item(goal)
            if item is not None:
                items.append(item)

        run_page = self.run_read_model.list_runs(limit=min(MAX_RUNS, MAX_SOURCE_RECORDS))
        raw_runs = run_page.get("runs", ()) if isinstance(run_page, Mapping) else ()
        if isinstance(raw_runs, (list, tuple)):
            for run in raw_runs[:MAX_SOURCE_RECORDS]:
                if not isinstance(run, Mapping):
                    continue
                item = self._run_item(run)
                if item is not None:
                    items.append(item)

        items.sort(key=_sort_key)
        return tuple(items[:bounded])

    @staticmethod
    def _goal_item(goal: Any) -> AttentionItem | None:
        status = _safe_status(getattr(goal, "status", ""))
        if status != "PLANNED":
            return None
        goal_id = _safe_identifier(getattr(goal, "id", ""))
        if not goal_id:
            return None
        title = _safe_title(getattr(goal, "title", "")) or "Goal needs approval"
        observed_at = _safe_timestamp(getattr(goal, "updated_at", ""))
        revision = _safe_int(getattr(goal, "revision", 0))
        generation = {
            "status": status,
            "revision": revision,
        }
        return _build_item(
            kind=AttentionKind.APPROVAL_REQUIRED,
            severity=AttentionSeverity.MEDIUM,
            entity_type="GOAL",
            entity_id=goal_id,
            goal_id=goal_id,
            task_id="",
            title=title,
            summary="Goal plan is waiting for explicit Owner approval.",
            deep_link=f"/approvals?goal={quote(goal_id, safe='')}",
            external_url="",
            source_status=status,
            observed_at=observed_at,
            generation=generation,
        )

    def _run_item(self, run: Mapping[str, Any]) -> AttentionItem | None:
        task_id = _safe_identifier(run.get("task_id", ""))
        if not task_id:
            return None
        goal_id = _safe_identifier(run.get("goal_id", ""))
        status = _safe_status(run.get("status", ""))
        liveness = _safe_status(run.get("liveness", ""))
        title = _safe_title(run.get("title", "")) or "Run needs attention"
        observed_at = _safe_timestamp(run.get("updated_at", ""))
        run_id = _safe_identifier(run.get("run_id", ""))

        publication = (
            run.get("publication")
            if isinstance(run.get("publication"), Mapping)
            else {}
        )
        validation = (
            run.get("validation")
            if isinstance(run.get("validation"), Mapping)
            else {}
        )
        publication_status = _safe_status(publication.get("status", ""))
        validation_status = _safe_status(validation.get("status", ""))

        kind: AttentionKind | None = None
        severity: AttentionSeverity | None = None
        summary = ""
        source_status = status
        external_url = ""

        if publication_status == "FAILED":
            kind = AttentionKind.PUBLICATION_FAILED
            severity = AttentionSeverity.HIGH
            summary = "Draft publication failed and requires Owner attention."
            source_status = publication_status
        elif status == "FAILED":
            kind = AttentionKind.RUN_FAILED
            severity = AttentionSeverity.HIGH
            summary = "Run failed and requires review before another attempt."
        elif status == "BLOCKED":
            kind = AttentionKind.RUN_BLOCKED
            severity = AttentionSeverity.HIGH
            summary = "Run is blocked and requires Owner attention."
        elif status == "INTERRUPTED":
            kind = AttentionKind.RECOVERY_REQUIRED
            severity = AttentionSeverity.HIGH
            summary = "Run is interrupted and requires an explicit recovery decision."
        elif status in _ACTIVE_RUN_STATUSES and liveness == "STALE":
            kind = AttentionKind.RUN_STALLED
            severity = AttentionSeverity.HIGH
            summary = "Run appears stale and requires liveness or recovery review."
            source_status = "STALE"
        elif validation_status in {"FAILURE", "UNVERIFIED"}:
            kind = AttentionKind.VERIFICATION_FAILED
            severity = AttentionSeverity.HIGH
            summary = "Verification is not currently sufficient for acceptance."
            source_status = validation_status
        elif publication_status == "COMPLETE" and _positive_int(
            publication.get("pr_number")
        ):
            kind = AttentionKind.DRAFT_PR_READY
            severity = AttentionSeverity.MEDIUM
            summary = "A Draft PR is available for human review."
            source_status = publication_status
            external_url = _safe_github_url(publication.get("pr_url", ""))
        elif status in _REVIEW_STATUSES:
            kind = AttentionKind.REVIEW_REQUIRED
            severity = AttentionSeverity.MEDIUM
            summary = "Run is ready for human review."
        else:
            return None

        generation = {
            "kind": kind.value,
            "status": status,
            "run_id": run_id,
            "liveness": liveness,
            "validation": {
                "command_id": _safe_status(validation.get("command_id", "")),
                "status": validation_status,
                "exit_code": _safe_int(validation.get("exit_code")),
            },
            "publication": {
                "status": publication_status,
                "pr_number": _safe_int(publication.get("pr_number")),
                "commit_sha": _safe_reference(publication.get("commit_sha", "")),
            },
        }
        return _build_item(
            kind=kind,
            severity=severity,
            entity_type="RUN",
            entity_id=task_id,
            goal_id=goal_id,
            task_id=task_id,
            title=title,
            summary=summary,
            deep_link=f"/runs?task={quote(task_id, safe='')}",
            external_url=external_url,
            source_status=source_status,
            observed_at=observed_at,
            generation=generation,
        )


def _build_item(
    *,
    kind: AttentionKind,
    severity: AttentionSeverity,
    entity_type: str,
    entity_id: str,
    goal_id: str,
    task_id: str,
    title: str,
    summary: str,
    deep_link: str,
    external_url: str,
    source_status: str,
    observed_at: str,
    generation: Mapping[str, Any],
) -> AttentionItem:
    identity = {
        "v": 1,
        "kind": kind.value,
        "entity_type": entity_type,
        "entity_id": entity_id,
        "generation": generation,
    }
    canonical = json.dumps(
        identity, ensure_ascii=False, sort_keys=True, separators=(",", ":")
    )
    attention_id = "attn-" + hashlib.sha256(
        canonical.encode("utf-8")
    ).hexdigest()[:24]
    return AttentionItem(
        attention_id=attention_id,
        kind=kind,
        severity=severity,
        entity_type=entity_type,
        entity_id=entity_id,
        goal_id=goal_id,
        task_id=task_id,
        title=title,
        summary=summary,
        deep_link=deep_link,
        external_url=external_url,
        source_status=_safe_status(source_status),
        observed_at=observed_at,
    )


def _validate_limit(value: int) -> int:
    if type(value) is not int or not 1 <= value <= MAX_ATTENTION_ITEMS:
        raise AttentionReadModelError("invalid_attention_limit")
    return value


def _safe_identifier(value: Any) -> str:
    if not isinstance(value, str):
        return ""
    value = unicodedata.normalize("NFC", value.strip())
    if not 1 <= len(value) <= 256:
        return ""
    if any(unicodedata.category(char).startswith("C") for char in value):
        return ""
    if not re.fullmatch(r"[A-Za-z0-9._:/#-]+", value):
        return ""
    return value


def _safe_title(value: Any) -> str:
    if not isinstance(value, str):
        return ""
    value = unicodedata.normalize("NFC", value)
    if _SENSITIVE_TEXT_RE.search(value) or _OPAQUE_SECRET_RE.search(value):
        return ""
    cleaned = " ".join(
        "".join(
            char if not unicodedata.category(char).startswith("C") else " "
            for char in value
        ).split()
    )
    return cleaned[:_MAX_TITLE]


def _safe_status(value: Any) -> str:
    if not isinstance(value, str):
        return ""
    value = value.strip().upper()
    if not value or len(value) > _MAX_STATUS:
        return ""
    if not re.fullmatch(r"[A-Z0-9_:-]+", value):
        return ""
    return value


def _safe_reference(value: Any) -> str:
    if not isinstance(value, str):
        return ""
    value = value.strip()
    if not value or len(value) > 128:
        return ""
    if not re.fullmatch(r"[A-Za-z0-9._:/#-]+", value):
        return ""
    return value


def _safe_timestamp(value: Any) -> str:
    if not isinstance(value, str) or not value.strip():
        return ""
    text = value.strip()
    try:
        parsed = datetime.fromisoformat(text.replace("Z", "+00:00"))
    except ValueError:
        return ""
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(timezone.utc).replace(microsecond=0).isoformat().replace(
        "+00:00", "Z"
    )


def _safe_int(value: Any) -> int | None:
    if type(value) is bool:
        return None
    try:
        return int(value)
    except (TypeError, ValueError, OverflowError):
        return None


def _positive_int(value: Any) -> bool:
    number = _safe_int(value)
    return number is not None and number > 0


def _safe_github_url(value: Any) -> str:
    if not isinstance(value, str):
        return ""
    value = value.strip()
    if not value or len(value) > _MAX_URL:
        return ""
    if any(unicodedata.category(char).startswith("C") for char in value):
        return ""
    try:
        parsed = urlsplit(value)
        port = parsed.port
    except ValueError:
        return ""
    if (
        parsed.scheme != "https"
        or parsed.hostname != "github.com"
        or parsed.username is not None
        or parsed.password is not None
        or port not in (None, 443)
        or not parsed.path.startswith("/")
        or parsed.query
        or parsed.fragment
    ):
        return ""
    return value


def _sort_key(item: AttentionItem) -> tuple[int, float, str]:
    severity_rank = 0 if item.severity is AttentionSeverity.HIGH else 1
    try:
        parsed = datetime.fromisoformat(item.observed_at.replace("Z", "+00:00"))
        timestamp = parsed.timestamp()
    except (ValueError, OSError, OverflowError):
        timestamp = 0.0
    return severity_rank, -timestamp, item.attention_id
