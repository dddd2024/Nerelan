"""Bounded authoritative Goal/Run history query and non-destructive archive overlay."""

from __future__ import annotations

import base64
from contextlib import contextmanager
from dataclasses import dataclass
from datetime import datetime, timezone
import hashlib
import json
import re
import sqlite3
import unicodedata
from typing import Any, Sequence

from .control_store import GOAL_STATES, PlatformControlStore
from .run_store import TASK_STATUS_ORDER, TERMINAL_STATUSES, TaskStore, TaskStoreError


GOAL = "GOAL"
RUN = "RUN"
ACTIVE = "ACTIVE"
ARCHIVED = "ARCHIVED"
ALL = "ALL"
CREATED_DESC = "CREATED_DESC"
UPDATED_DESC = "UPDATED_DESC"

_KINDS = frozenset({GOAL, RUN})
_ARCHIVE_VIEWS = frozenset({ACTIVE, ARCHIVED, ALL})
_SORTS = frozenset({CREATED_DESC, UPDATED_DESC})
_GOAL_ARCHIVE_STATES = frozenset({"COMPLETED", "BLOCKED", "INVALIDATED"})
_RUN_ARCHIVE_STATES = frozenset(TERMINAL_STATUSES)
_TASK_STATES = frozenset(TASK_STATUS_ORDER)
_MAX_LIMIT = 100
_MAX_TEXT = 256
_MAX_FILTER_VALUES = 20
_MAX_SCALAR = 256
_MAX_CURSOR = 2048
_RFC3339_UTC_RE = re.compile(
    r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(?:\.\d{1,6})?Z$"
)


class HistoryQueryError(TaskStoreError):
    """Stable sanitized history-query/archive contract error."""


@dataclass(frozen=True)
class HistoryItem:
    kind: str
    id: str
    title: str
    repository: str
    status: str
    executor_kind: str
    orchestration_mode: str
    created_at: str
    updated_at: str
    archived: bool
    archived_at: str


@dataclass(frozen=True)
class HistoryPage:
    items: tuple[HistoryItem, ...]
    total: int
    next_cursor: str | None


@dataclass(frozen=True)
class ArchiveMarker:
    kind: str
    subject_id: str
    archived_at: str


def _canonical_json(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def _digest(domain: str, value: Any) -> str:
    raw = domain.encode("utf-8") + b"\0" + _canonical_json(value).encode("utf-8")
    return hashlib.sha256(raw).hexdigest()


def _kind(value: Any) -> str:
    normalized = str(value).strip().upper()
    if normalized not in _KINDS:
        raise HistoryQueryError("invalid_history_kind")
    return normalized


def _enum(value: Any, allowed: frozenset[str], code: str) -> str:
    normalized = str(value).strip().upper()
    if normalized not in allowed:
        raise HistoryQueryError(code)
    return normalized


def _bounded_scalar(value: Any, field: str, *, allow_empty: bool = False) -> str:
    if not isinstance(value, str):
        raise HistoryQueryError(f"invalid_history_{field}")
    normalized = unicodedata.normalize("NFC", value.strip())
    if (not allow_empty and not normalized) or len(normalized) > _MAX_SCALAR:
        raise HistoryQueryError(f"invalid_history_{field}")
    if normalized and not normalized.isprintable():
        raise HistoryQueryError(f"invalid_history_{field}")
    return normalized


def _filter_values(
    values: Sequence[str] | None,
    field: str,
    *,
    allowed: frozenset[str] | None = None,
) -> tuple[str, ...]:
    if values is None:
        return ()
    if isinstance(values, (str, bytes)) or not isinstance(values, Sequence):
        raise HistoryQueryError(f"invalid_history_{field}")
    if len(values) > _MAX_FILTER_VALUES:
        raise HistoryQueryError(f"invalid_history_{field}")
    normalized: set[str] = set()
    for raw in values:
        item = _bounded_scalar(raw, field)
        if allowed is not None:
            item = item.upper()
            if item not in allowed:
                raise HistoryQueryError(f"invalid_history_{field}")
        normalized.add(item)
    return tuple(sorted(normalized))


def _text(value: Any) -> str:
    if value is None:
        return ""
    if not isinstance(value, str):
        raise HistoryQueryError("invalid_history_text")
    normalized = unicodedata.normalize("NFC", value.strip())
    if len(normalized) > _MAX_TEXT:
        raise HistoryQueryError("invalid_history_text")
    if normalized and not normalized.isprintable():
        raise HistoryQueryError("invalid_history_text")
    return normalized


def _parse_utc(value: Any, field: str) -> str | None:
    if value is None:
        return None
    if not isinstance(value, str) or not _RFC3339_UTC_RE.fullmatch(value):
        raise HistoryQueryError(f"invalid_history_{field}")
    try:
        parsed = datetime.fromisoformat(value[:-1] + "+00:00").astimezone(timezone.utc)
    except ValueError as exc:
        raise HistoryQueryError(f"invalid_history_{field}") from exc
    return parsed.replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _now_utc() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _limit(value: Any) -> int:
    if type(value) is not int or not 1 <= value <= _MAX_LIMIT:
        raise HistoryQueryError("invalid_history_limit")
    return value


def _escape_like(value: str) -> str:
    return value.replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_")


def _encode_cursor(
    *, kind: str, query_digest: str, sort: str, timestamp: str, identifier: str
) -> str:
    payload = json.dumps(
        [1, kind, query_digest, sort, timestamp, identifier],
        separators=(",", ":"),
    ).encode("utf-8")
    return base64.urlsafe_b64encode(payload).decode("ascii").rstrip("=")


def _decode_cursor(
    cursor: str | None, *, kind: str, query_digest: str, sort: str
) -> tuple[str, str] | None:
    if cursor is None:
        return None
    try:
        if not isinstance(cursor, str) or not 1 <= len(cursor) <= _MAX_CURSOR:
            raise ValueError
        raw = base64.b64decode(
            cursor + "=" * (-len(cursor) % 4), altchars=b"-_", validate=True
        )
        value = json.loads(raw.decode("utf-8"))
        if (
            not isinstance(value, list)
            or len(value) != 6
            or type(value[0]) is not int
            or value[0] != 1
            or value[1] != kind
            or value[2] != query_digest
            or value[3] != sort
        ):
            raise ValueError
        timestamp, identifier = value[4], value[5]
        if not isinstance(timestamp, str) or not 1 <= len(timestamp) <= 64:
            raise ValueError
        if not isinstance(identifier, str) or not 1 <= len(identifier) <= _MAX_SCALAR:
            raise ValueError
        datetime.fromisoformat(timestamp.replace("Z", "+00:00"))
        if not identifier.isprintable():
            raise ValueError
        return timestamp, identifier
    except (ValueError, TypeError, UnicodeError, json.JSONDecodeError) as exc:
        raise HistoryQueryError("invalid_history_cursor") from exc


class HistoryQueryService:
    """Read authoritative Goal/Run history with a separate archive overlay."""

    def __init__(
        self,
        *,
        store: TaskStore,
        control_store: PlatformControlStore | None = None,
    ) -> None:
        self.store = store
        self.control_store = control_store or PlatformControlStore(store)
        if self.control_store.task_store is not store:
            raise HistoryQueryError("history_control_store_mismatch")
        self._conn = store._conn
        self._lock = store._lock
        with self._lock:
            if self._conn.in_transaction:
                raise HistoryQueryError("history_initialization_during_transaction")
            self._conn.execute(
                """
                CREATE TABLE IF NOT EXISTS platform_history_archive (
                    kind TEXT NOT NULL,
                    subject_id TEXT NOT NULL,
                    archived_at TEXT NOT NULL,
                    PRIMARY KEY(kind, subject_id)
                )
                """
            )
            self._conn.create_function(
                "nerelan_casefold",
                1,
                lambda value: "" if value is None else str(value).casefold(),
                deterministic=True,
            )

    def query(
        self,
        kind: str,
        *,
        text: str = "",
        statuses: Sequence[str] | None = None,
        repositories: Sequence[str] | None = None,
        executors: Sequence[str] | None = None,
        created_from_utc: str | None = None,
        created_to_utc: str | None = None,
        archive_view: str = ACTIVE,
        sort: str = CREATED_DESC,
        limit: int = 100,
        cursor: str | None = None,
    ) -> HistoryPage:
        normalized_kind = _kind(kind)
        normalized_archive = _enum(
            archive_view, _ARCHIVE_VIEWS, "invalid_history_archive_view"
        )
        normalized_sort = _enum(sort, _SORTS, "invalid_history_sort")
        bounded_limit = _limit(limit)
        normalized_text = _text(text)
        allowed_states = GOAL_STATES if normalized_kind == GOAL else _TASK_STATES
        normalized_statuses = _filter_values(
            statuses, "statuses", allowed=frozenset(allowed_states)
        )
        normalized_repositories = _filter_values(repositories, "repositories")
        normalized_executors = _filter_values(executors, "executors")
        created_from = _parse_utc(created_from_utc, "created_from_utc")
        created_to = _parse_utc(created_to_utc, "created_to_utc")
        if created_from is not None and created_to is not None and created_from > created_to:
            raise HistoryQueryError("invalid_history_created_range")

        query_identity = {
            "kind": normalized_kind,
            "text": normalized_text.casefold(),
            "statuses": normalized_statuses,
            "repositories": normalized_repositories,
            "executors": normalized_executors,
            "created_from_utc": created_from,
            "created_to_utc": created_to,
            "archive_view": normalized_archive,
            "sort": normalized_sort,
            "limit": bounded_limit,
        }
        query_digest = _digest("nerelan.history-query.v1", query_identity)
        position = _decode_cursor(
            cursor,
            kind=normalized_kind,
            query_digest=query_digest,
            sort=normalized_sort,
        )

        table = "platform_goals" if normalized_kind == GOAL else "tasks"
        sort_column = "created_at" if normalized_sort == CREATED_DESC else "updated_at"
        clauses: list[str] = []
        params: list[Any] = [normalized_kind]

        if normalized_archive == ACTIVE:
            clauses.append("a.subject_id IS NULL")
        elif normalized_archive == ARCHIVED:
            clauses.append("a.subject_id IS NOT NULL")

        if normalized_text:
            pattern = "%" + _escape_like(normalized_text.casefold()) + "%"
            clauses.append(
                "("
                "nerelan_casefold(s.id) LIKE ? ESCAPE '\\' OR "
                "nerelan_casefold(s.title) LIKE ? ESCAPE '\\' OR "
                "nerelan_casefold(s.repository) LIKE ? ESCAPE '\\'"
                ")"
            )
            params.extend([pattern, pattern, pattern])

        self._append_in_filter(clauses, params, "s.status", normalized_statuses)
        self._append_in_filter(
            clauses, params, "s.repository", normalized_repositories
        )
        self._append_in_filter(
            clauses, params, "s.executor_kind", normalized_executors
        )

        if created_from is not None:
            clauses.append("s.created_at >= ?")
            params.append(created_from)
        if created_to is not None:
            clauses.append("s.created_at <= ?")
            params.append(created_to)

        where_sql = " AND ".join(clauses) if clauses else "1=1"
        from_sql = (
            f" FROM {table} AS s "
            "LEFT JOIN platform_history_archive AS a "
            "ON a.kind = ? AND a.subject_id = s.id "
        )
        count_sql = "SELECT COUNT(*) AS c" + from_sql + "WHERE " + where_sql

        page_clauses = list(clauses)
        page_params = list(params)
        if position is not None:
            page_clauses.append(
                f"(s.{sort_column} < ? OR "
                f"(s.{sort_column} = ? AND s.id < ?))"
            )
            page_params.extend([position[0], position[0], position[1]])
        page_where = " AND ".join(page_clauses) if page_clauses else "1=1"

        select_sql = (
            "SELECT s.id, s.title, s.repository, s.status, s.executor_kind, "
            "s.orchestration_mode, s.created_at, s.updated_at, "
            "CASE WHEN a.subject_id IS NULL THEN 0 ELSE 1 END AS archived, "
            "COALESCE(a.archived_at, '') AS archived_at"
            + from_sql
            + "WHERE "
            + page_where
            + f" ORDER BY s.{sort_column} DESC, s.id DESC LIMIT ?"
        )
        page_params.append(bounded_limit + 1)

        with self._lock:
            total_row = self._conn.execute(count_sql, params).fetchone()
            rows = self._conn.execute(select_sql, page_params).fetchall()

        total = int(total_row["c"])
        visible_rows = rows[:bounded_limit]
        items = tuple(
            HistoryItem(
                kind=normalized_kind,
                id=row["id"],
                title=row["title"],
                repository=row["repository"],
                status=row["status"],
                executor_kind=row["executor_kind"],
                orchestration_mode=row["orchestration_mode"] or "single",
                created_at=row["created_at"],
                updated_at=row["updated_at"],
                archived=bool(row["archived"]),
                archived_at=row["archived_at"],
            )
            for row in visible_rows
        )
        next_cursor = None
        if len(rows) > bounded_limit and visible_rows:
            last = visible_rows[-1]
            next_cursor = _encode_cursor(
                kind=normalized_kind,
                query_digest=query_digest,
                sort=normalized_sort,
                timestamp=last[sort_column],
                identifier=last["id"],
            )
        return HistoryPage(items=items, total=total, next_cursor=next_cursor)

    def archive(self, kind: str, subject_id: str) -> ArchiveMarker:
        normalized_kind = _kind(kind)
        identifier = _bounded_scalar(subject_id, "subject_id")
        table = "platform_goals" if normalized_kind == GOAL else "tasks"
        allowed = (
            _GOAL_ARCHIVE_STATES
            if normalized_kind == GOAL
            else _RUN_ARCHIVE_STATES
        )
        with self._write_transaction():
            row = self._conn.execute(
                f"SELECT status FROM {table} WHERE id = ?", (identifier,)
            ).fetchone()
            if row is None:
                raise HistoryQueryError("history_subject_not_found")
            if row["status"] not in allowed:
                raise HistoryQueryError("history_subject_not_archivable")
            existing = self._conn.execute(
                "SELECT archived_at FROM platform_history_archive "
                "WHERE kind = ? AND subject_id = ?",
                (normalized_kind, identifier),
            ).fetchone()
            if existing is not None:
                return ArchiveMarker(
                    normalized_kind, identifier, existing["archived_at"]
                )
            archived_at = _now_utc()
            self._conn.execute(
                "INSERT INTO platform_history_archive(kind, subject_id, archived_at) "
                "VALUES (?, ?, ?)",
                (normalized_kind, identifier, archived_at),
            )
            return ArchiveMarker(normalized_kind, identifier, archived_at)

    def unarchive(self, kind: str, subject_id: str) -> bool:
        normalized_kind = _kind(kind)
        identifier = _bounded_scalar(subject_id, "subject_id")
        with self._write_transaction():
            cur = self._conn.execute(
                "DELETE FROM platform_history_archive "
                "WHERE kind = ? AND subject_id = ?",
                (normalized_kind, identifier),
            )
            return bool(cur.rowcount)

    def is_archived(self, kind: str, subject_id: str) -> bool:
        normalized_kind = _kind(kind)
        identifier = _bounded_scalar(subject_id, "subject_id")
        with self._lock:
            row = self._conn.execute(
                "SELECT 1 FROM platform_history_archive "
                "WHERE kind = ? AND subject_id = ?",
                (normalized_kind, identifier),
            ).fetchone()
        return row is not None

    @staticmethod
    def _append_in_filter(
        clauses: list[str], params: list[Any], column: str, values: tuple[str, ...]
    ) -> None:
        if not values:
            return
        placeholders = ",".join("?" for _ in values)
        clauses.append(f"{column} IN ({placeholders})")
        params.extend(values)

    @contextmanager
    def _write_transaction(self):
        with self._lock:
            if self._conn.in_transaction:
                raise HistoryQueryError("history_archive_during_active_transaction")
            try:
                self._conn.execute("BEGIN IMMEDIATE")
                yield
                self._conn.execute("COMMIT")
            except HistoryQueryError:
                if self._conn.in_transaction:
                    self._conn.execute("ROLLBACK")
                raise
            except sqlite3.Error as exc:
                if self._conn.in_transaction:
                    self._conn.execute("ROLLBACK")
                raise HistoryQueryError("history_archive_storage_error") from exc
