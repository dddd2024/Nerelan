"""Host observation of the issue that Quick Start used to create a Goal."""

from collections import OrderedDict
from collections.abc import Callable, Mapping
import hashlib
import json
import re
import subprocess
from threading import Lock
import time
from typing import Any

from .control_store import GoalRecord

_TTL_SECONDS = 900
_CACHE_LIMIT = 512
_REPOSITORY = re.compile(r"[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+")


def source_issue(goal: GoalRecord) -> int | None:
    """Recognize the durable Quick Start identity, including existing rows."""

    if not _REPOSITORY.fullmatch(goal.repository):
        return None
    prefix = f"quick-start:{goal.repository}:issue-"
    if not goal.idempotency_key.startswith(prefix):
        return None
    match = re.fullmatch(r"([1-9][0-9]{0,6}):([0-9a-f]{16}):[1-9][0-9]*",
                         goal.idempotency_key.removeprefix(prefix))
    if match is None:
        return None
    number, digest = match.groups()
    first_line = goal.objective.partition("\n")[0]
    if first_line.casefold() != f"Resolve https://github.com/{goal.repository}/issues/{number}".casefold():
        return None
    if hashlib.sha256(goal.objective.encode("utf-8")).hexdigest()[:16] != digest:
        return None
    return int(number)


def _read_issue(repository: str, number: int) -> Mapping[str, Any]:
    result = subprocess.run(
        ["gh", "issue", "view", str(number), "--repo", repository, "--json", "number,state,url"],
        capture_output=True, timeout=5, text=True, encoding="utf-8", errors="replace", check=True,
    )
    return json.loads(result.stdout)


class GoalSourceIssues:
    """Cache bounded read observations. A failed or mismatched read is unknown."""

    def __init__(self, reader: Callable[[str, int], Mapping[str, Any]] = _read_issue) -> None:
        self._reader = reader
        self._cache: OrderedDict[tuple[str, int], tuple[float, bool]] = OrderedDict()
        self._lock = Lock()

    def closed(self, goal: GoalRecord, *, fresh: bool = False) -> bool:
        number = source_issue(goal)
        if number is None:
            return False
        key = (goal.repository, number)
        with self._lock:
            now = time.monotonic()
            cached = self._cache.get(key)
            if not fresh and cached is not None and now < cached[0]:
                return cached[1]
            try:
                issue = self._reader(goal.repository, number)
            except (OSError, subprocess.SubprocessError, ValueError):
                issue = {}
            url = f"https://github.com/{goal.repository}/issues/{number}"
            closed = (isinstance(issue, Mapping) and type(issue.get("number")) is int and issue["number"] == number
                      and str(issue.get("url", "")).casefold() == url.casefold()
                      and issue.get("state") == "CLOSED")
            self._cache[key] = (time.monotonic() + _TTL_SECONDS, closed)
            self._cache.move_to_end(key)
            if len(self._cache) > _CACHE_LIMIT:
                self._cache.popitem(last=False)
            return closed

    def cached_closed_issues(self, *, repository: str | None = None) -> set[int]:
        """Return unexpired cached closed issue numbers with zero network/subprocess calls."""
        now = time.monotonic()
        with self._lock:
            return {
                number
                for (repo, number), (expires_at, is_closed) in self._cache.items()
                if is_closed and now < expires_at and (repository is None or repo == repository)
            }
