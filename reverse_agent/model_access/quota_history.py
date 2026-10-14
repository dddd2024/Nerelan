"""Usage history behind the quota estimates, read from the official CLIs' local logs.

Only lines that carry the needed markers are decoded, and only allowlisted numbers and
timestamps are kept; prompts, replies and tool output are never decoded or returned:

* Codex (``$CODEX_HOME/sessions``): ``turn_context`` lines for the model and
  ``token_count`` lines for per-request usage, the account's windows and limit hits.
* Claude Code (``$CLAUDE_CONFIG_DIR`` or ``~/.claude``, ``projects/*/*.jsonl``): assistant
  lines for per-message usage (deduplicated by message id) and API error lines for
  ``usage_limit_reached``.

Reads are bounded: recent files only, a file count cap and a per-file byte cap.
"""

from __future__ import annotations

from dataclasses import dataclass, field
import json
import os
from pathlib import Path
import time
from typing import Any

from .quota_forecast import PercentSample, UsageEvent, parse_time, usage_units

MAX_AGE_SECONDS = 8 * 24 * 3600
MAX_FILES = 40
MAX_FILE_BYTES = 64 * 1024 * 1024
_WINDOWS = {300: "five_hour", 10080: "weekly"}


@dataclass
class History:
    usage: list[UsageEvent] = field(default_factory=list)
    percents: list[PercentSample] = field(default_factory=list)
    hits: list[dict[str, Any]] = field(default_factory=list)   # {"at": epoch, "window": str | None}
    latest: tuple[dict[str, Any], str | None] | None = None    # newest Codex token_count payload


def _recent(root: Path, pattern: str, now: float) -> list[Path]:
    try:
        files = [p for p in root.glob(pattern) if now - p.stat().st_mtime <= MAX_AGE_SECONDS]
        return sorted(files, key=lambda p: p.stat().st_mtime, reverse=True)[:MAX_FILES]
    except OSError:
        return []


def _lines(path: Path, markers: tuple[bytes, ...]):
    read = 0
    with path.open("rb") as handle:
        for raw in handle:
            read += len(raw)
            if read > MAX_FILE_BYTES:
                return
            if any(marker in raw for marker in markers):
                try:
                    entry = json.loads(raw.decode("utf-8"))
                except (UnicodeDecodeError, ValueError, RecursionError):
                    continue
                if isinstance(entry, dict):
                    yield entry


def _int(value: Any) -> int:
    return value if type(value) is int and value >= 0 else 0


def read_codex_history(codex_home: str | os.PathLike[str] | None = None, *, now: float | None = None) -> History:
    now = time.time() if now is None else now
    home = Path(codex_home or os.environ.get("CODEX_HOME") or Path.home() / ".codex")
    history = History()
    latest_at = -1.0
    for path in _recent(home / "sessions", "*/*/*/*.jsonl", now):
        model = ""
        try:
            for entry in _lines(path, (b'"turn_context"', b'"token_count"')):
                payload = entry.get("payload") if isinstance(entry.get("payload"), dict) else {}
                if entry.get("type") == "turn_context" and isinstance(payload.get("model"), str):
                    model = payload["model"][:120]
                    continue
                if payload.get("type") != "token_count":
                    continue
                at = parse_time(entry.get("timestamp"))
                limits = payload.get("rate_limits")
                if at is None or not isinstance(limits, dict):
                    continue
                if at > latest_at:
                    latest_at, history.latest = at, (payload, entry.get("timestamp"))
                last = (payload.get("info") or {}).get("last_token_usage") if isinstance(payload.get("info"), dict) else None
                units = 0.0
                if isinstance(last, dict) and model:
                    cached = _int(last.get("cached_input_tokens"))
                    tokens = {"input": max(_int(last.get("input_tokens")) - cached, 0), "cache_read": cached,
                              "cache_write": _int(last.get("cache_write_input_tokens")),
                              "output": _int(last.get("output_tokens"))}
                    units = usage_units(model, tokens) or 0.0
                if units:
                    history.usage.append(UsageEvent(at, units))
                for key in ("primary", "secondary"):
                    window = limits.get(key)
                    if not isinstance(window, dict):
                        continue
                    used, resets = window.get("used_percent"), window.get("resets_at")
                    if type(used) in (int, float) and type(resets) is int:
                        history.percents.append(PercentSample(at, _WINDOWS.get(window.get("window_minutes"), key),
                                                              resets, float(used), units))
                reached = limits.get("rate_limit_reached_type")
                if isinstance(reached, str) and reached:
                    history.hits.append({"at": at, "window": reached[:40], "source": "codex_session_log"})
        except OSError:
            continue
    return history


def read_claude_history(config_dir: str | os.PathLike[str] | None = None, *, now: float | None = None) -> History:
    now = time.time() if now is None else now
    home = Path(config_dir or os.environ.get("CLAUDE_CONFIG_DIR") or Path.home() / ".claude")
    history = History()
    seen: set[str] = set()
    for path in _recent(home / "projects", "*/*.jsonl", now):
        try:
            for entry in _lines(path, (b'"usage"', b'"isApiErrorMessage"')):
                at = parse_time(entry.get("timestamp"))
                if at is None:
                    continue
                if entry.get("isApiErrorMessage") is True:
                    if entry.get("error") == "rate_limit" and "usage_limit" in str(entry.get("apiError", ""))[:80]:
                        history.hits.append({"at": at, "window": None, "source": "claude_session_log"})
                    continue
                message = entry.get("message")
                if entry.get("type") != "assistant" or not isinstance(message, dict):
                    continue
                usage, model = message.get("usage"), message.get("model")
                key = str(message.get("id") or entry.get("requestId") or "")
                if not isinstance(usage, dict) or not isinstance(model, str) or model.startswith("<") or not key:
                    continue
                if key in seen:  # one message is logged once per content block
                    continue
                seen.add(key)
                units = usage_units(model, {"input": _int(usage.get("input_tokens")),
                                            "cache_read": _int(usage.get("cache_read_input_tokens")),
                                            "cache_write": _int(usage.get("cache_creation_input_tokens")),
                                            "output": _int(usage.get("output_tokens"))})
                if units:
                    history.usage.append(UsageEvent(at, units))
        except OSError:
            continue
    return history
