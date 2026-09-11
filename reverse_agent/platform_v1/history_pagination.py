"""Bounded opaque cursors for the existing Goal and Run history reads."""

from __future__ import annotations

import base64
from datetime import datetime
import json
import re
from urllib.parse import parse_qs

MAX_HISTORY_PAGE = 100


class HistoryPaginationError(ValueError):
    """An invalid history position or page size, safe to report as HTTP 400."""


def page_limit(limit: int) -> int:
    if type(limit) is not int or not 1 <= limit <= MAX_HISTORY_PAGE:
        raise HistoryPaginationError("invalid_history_pagination")
    return limit


def encode_cursor(kind: str, created_at: str, identifier: str) -> str:
    payload = json.dumps([1, kind, created_at, identifier], separators=(",", ":"))
    return base64.urlsafe_b64encode(payload.encode("utf-8")).decode("ascii").rstrip("=")


def decode_cursor(cursor: str | None, kind: str) -> tuple[str, str] | None:
    if cursor is None:
        return None
    try:
        if not isinstance(cursor, str) or not 1 <= len(cursor) <= 1024:
            raise ValueError
        payload = base64.b64decode(cursor + "=" * (-len(cursor) % 4), altchars=b"-_", validate=True)
        value = json.loads(payload.decode("utf-8"))
        if (not isinstance(value, list) or len(value) != 4
                or type(value[0]) is not int or value[0] != 1 or value[1] != kind):
            raise ValueError
        created_at, identifier = value[2:]
        if not isinstance(created_at, str) or not 1 <= len(created_at) <= 64:
            raise ValueError
        if not isinstance(identifier, str) or not 1 <= len(identifier) <= 256:
            raise ValueError
        if not identifier.isprintable():
            raise ValueError
        datetime.fromisoformat(created_at)
        return created_at, identifier
    except (ValueError, TypeError, UnicodeError) as exc:
        raise HistoryPaginationError("invalid_history_pagination") from exc


def parse_history_query(query: str) -> tuple[int, str | None]:
    try:
        values = parse_qs(query, keep_blank_values=True, max_num_fields=16)
        if any(len(values.get(key, [])) > 1 for key in ("limit", "cursor")):
            raise ValueError
        raw_limit = values.get("limit", [str(MAX_HISTORY_PAGE)])[0]
        if not re.fullmatch(r"[0-9]{1,3}", raw_limit):
            raise ValueError
        return page_limit(int(raw_limit)), values.get("cursor", [None])[0]
    except (ValueError, TypeError) as exc:
        raise HistoryPaginationError("invalid_history_pagination") from exc
