"""Bounded, secret-free normalization of native ``codex exec --json`` events.

Transport framing is separate from Task acceptance: a completed turn proves
neither functional correctness nor independent review. Unknown usage stays
unknown; subscription tokens are never converted to an invented dollar cost.
"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from typing import Any, Callable, Mapping

from .opencode_executor import redact_event, redact_secrets
from .task_runtime import ExecutorRuntimeError


class CodexProtocolError(ExecutorRuntimeError):
    """Finite classification; raw provider output is never part of the error."""


# The account's own answer that it is out of quota. This mirrors quota_guard.ACCOUNT_LIMIT,
# but matches the free-text wording the CLI turns carry instead of a classification string.
_USAGE_LIMIT_RE = re.compile(
    r"(?i)\b(?:usage|rate)[ -]+limit\b|"
    r"\byou['?]?ve\s+hit\s+your\s+limit\b|"
    r"\b(?:account|plan)\s+(?:quota|limit)\s+(?:exceeded|reached)\b|"
    r"\b(?:exceeded|exhausted)\s+(?:your\s+)?(?:current\s+|account\s+|plan\s+)?quota\b|"
    r"\bquota\s+(?:exceeded|exhausted)\b|"
    r"\b(?:HTTP(?:/\d(?:\.\d)?)?\s+|status\s*[:=]?\s*)429\b|"
    r"\b429\s+Too\s+Many\s+Requests\b"
)

# A stated reset time inside a usage-limit message: an ISO-8601 timestamp, or a
# "try again at HH:MM" style hint (the latter resolved against the current day).
_RESET_ISO_RE = re.compile(r"\b(\d{4}-\d{2}-\d{2}[T ]\d{2}:\d{2}(?::\d{2})?(?:Z|[+-]\d{2}:?\d{2})?)\b")
_RESET_CLOCK_RE = re.compile(r"(?i)try\s+again\s+at\s+(\d{1,2}):(\d{2})(?:\s*([ap])\.?m\b\.?)?")

_FAILURE_DETAIL_LIMIT = 500


def public_text(value: Any, limit: int = 4096) -> str:
    if not isinstance(value, str):
        return ""
    # Redact the whole bounded frame before truncating public evidence.
    # The shared redactor handles many provider patterns, but its generic
    # Authorization substitution can consume only 'Bearer', leaving the token.
    value = re.sub(r"(?im)\bauthorization\s*:\s*[^\r\n]*", "Authorization: [REDACTED]", value)
    value = re.sub(r"(?i)\bbearer\s+[A-Za-z0-9._~+/=-]+", "Bearer [REDACTED]", value)
    value = re.sub(r"[A-Za-z0-9.!#$%&'*+/=?^_`{|}~-]+@[A-Za-z0-9-]+(?:\.[A-Za-z0-9-]+)+", "[REDACTED EMAIL]", value)
    return redact_secrets(value).replace("\x00", "").encode("utf-8")[:limit].decode(
        "utf-8", errors="ignore"
    )


def _usage_limit_message(event: Mapping[str, Any] | None) -> str:
    """The bounded, redacted error message from an error/turn.failed event, or ''."""
    if not isinstance(event, Mapping):
        return ""
    error = event.get("error")
    if not isinstance(error, Mapping):
        return ""
    message = error.get("message")
    return public_text(message, _FAILURE_DETAIL_LIMIT) if isinstance(message, str) else ""


def usage_limit_hit(message: str) -> bool:
    return bool(_USAGE_LIMIT_RE.search(message))


def local_now() -> datetime:
    """Aware host-local time: the CLIs run on this host and state clock resets in its zone."""
    return datetime.now().astimezone()


def parse_reset_time(message: str, now: datetime | None = None) -> str | None:
    """Return a stated reset in UTC. Explicit offsets need no reference time.

    Clock forms and naive ISO timestamps require an explicitly supplied aware
    ``now`` and use its timezone. Ambiguous forms otherwise return None.
    """
    aware_now = now is not None and now.tzinfo is not None and now.utcoffset() is not None
    match = _RESET_ISO_RE.search(message)
    if match:
        try:
            parsed = datetime.fromisoformat(match.group(1).replace("Z", "+00:00").replace(" ", "T"))
            if parsed.tzinfo is None:
                if not aware_now:
                    return None
                parsed = parsed.replace(tzinfo=now.tzinfo)
            return parsed.astimezone(timezone.utc).isoformat().replace("+00:00", "Z")
        except (ValueError, OverflowError):
            return None
    clock = _RESET_CLOCK_RE.search(message)
    if clock:
        if not aware_now:
            return None
        try:
            hour, minute = int(clock.group(1)), int(clock.group(2))
            if clock.group(3):
                if not 1 <= hour <= 12:
                    return None
                hour = hour % 12 + (12 if clock.group(3).lower() == "p" else 0)
            reset = now.replace(hour=hour, minute=minute, second=0, microsecond=0)
            if reset <= now:
                reset += timedelta(days=1)
            return reset.astimezone(timezone.utc).isoformat().replace("+00:00", "Z")
        except (ValueError, OverflowError):
            return None
    return None


@dataclass
class CodexTurn:
    thread_id: str = ""
    completed: bool = False
    failed: bool = False
    # A tool runner that never created its child process is an infrastructure
    # failure, even when the model turn itself later reports completed.
    tool_launch_failed: bool = False
    final_text: str = ""
    failure_classification: str = ""
    # Bounded, redacted copy of the provider's error message (empty on success).
    failure_detail: str = ""
    # Reset timestamp the provider stated inside the failure message, when it did.
    failure_reset_at: str = ""
    usage: dict[str, int] | None = None
    items: list[dict[str, Any]] = field(default_factory=list)
    # Optional, allowlisted facts a CLI reports about the turn (empty when it says nothing).
    models: list[str] = field(default_factory=list)
    rate_limits: list[dict[str, Any]] = field(default_factory=list)
    reported_cost_usd: float | None = None


class CodexJsonl:
    """Incremental UTF-8 framing with independent line, stream and item bounds."""

    def __init__(
        self,
        callback: Callable[[dict[str, Any]], None] | None = None,
        *,
        max_frame_bytes: int = 256 * 1024,
        max_stream_bytes: int = 2 * 1024 * 1024,
        max_events: int = 2000,
        limit_classification: str = "codex_usage_limit",
    ) -> None:
        if not (0 < max_frame_bytes <= max_stream_bytes <= 8 * 1024 * 1024):
            raise ValueError("codex_protocol_limits_invalid")
        if not 0 < max_events <= 10000:
            raise ValueError("codex_protocol_limits_invalid")
        self.turn = CodexTurn()
        self._callback = callback
        self._frame_limit = max_frame_bytes
        self._stream_limit = max_stream_bytes
        self._event_limit = max_events
        self._limit_classification = limit_classification
        self._buffer = bytearray()
        self._bytes = 0
        self._events = 0
        self._started = False
        self._error_seen = False
        self._error_detail = ""
        self._error_fresh = False

    def _publish_failure(self, classification: str, detail: str, *, terminal: str | None = None) -> None:
        self.turn.failed = True
        self.turn.completed = False
        self.turn.failure_classification = classification
        evidence = detail
        if self._error_seen and (terminal is not None or not self._error_fresh):
            terminal_evidence = terminal if terminal is not None else detail
            evidence = (f"Terminal: {public_text(terminal_evidence, 220)}\n"
                        f"Earlier diagnostic: {public_text(self._error_detail, 240)}")
        self.turn.failure_detail = public_text(evidence, _FAILURE_DETAIL_LIMIT)
        reset_at = parse_reset_time(detail, local_now()) if detail else None
        self.turn.failure_reset_at = reset_at or ""
        if self.turn.failure_detail:
            public = redact_event({"type": "turn.error", "failure_classification": classification,
                                   "detail": self.turn.failure_detail,
                                   **({"resets_at": reset_at} if reset_at else {})})
            if len(self.turn.items) < 100:
                self.turn.items.append(public)
            if self._callback:
                self._callback(public)

    def feed(self, chunk: bytes) -> None:
        if not isinstance(chunk, bytes):
            raise TypeError("codex_protocol_requires_bytes")
        self._bytes += len(chunk)
        if self._bytes > self._stream_limit:
            raise CodexProtocolError("codex_stream_limit_exceeded")
        self._buffer.extend(chunk)
        while b"\n" in self._buffer:
            end = self._buffer.index(b"\n")
            line = bytes(self._buffer[:end])
            del self._buffer[:end + 1]
            self._line(line)
        if len(self._buffer) > self._frame_limit:
            raise CodexProtocolError("codex_frame_limit_exceeded")

    def finish(self) -> CodexTurn:
        if self._buffer:
            self._line(bytes(self._buffer))
            self._buffer.clear()
        if not (self.turn.completed or self.turn.failed):
            if self._error_seen:
                detail = self._error_detail if self._error_fresh else ""
                if usage_limit_hit(detail):
                    self._publish_failure(self._limit_classification, detail)
                else:
                    self._publish_failure("codex_turn_failed", detail)
                return self.turn
            raise CodexProtocolError("codex_turn_incomplete")
        if self.turn.completed and not self.turn.final_text:
            raise CodexProtocolError("codex_final_message_missing")
        return self.turn

    def _line(self, line: bytes) -> None:
        if len(line) > self._frame_limit:
            raise CodexProtocolError("codex_frame_limit_exceeded")
        if not line.strip():
            return
        self._events += 1
        if self._events > self._event_limit:
            raise CodexProtocolError("codex_event_limit_exceeded")
        try:
            event = json.loads(line.decode("utf-8"))
        except (UnicodeDecodeError, json.JSONDecodeError, RecursionError) as exc:
            raise CodexProtocolError("codex_invalid_jsonl") from exc
        if not isinstance(event, dict) or not isinstance(event.get("type"), str):
            raise CodexProtocolError("codex_invalid_event")
        kind = event["type"]
        # Concrete model metadata is transport evidence, never inferred from
        # model prose or tool output. Missing metadata remains unknown.
        if kind in {"thread.started", "turn.started", "turn.completed"} and "model" in event:
            model = event["model"]
            if not isinstance(model, str) or not re.fullmatch(r"[A-Za-z0-9._:/@-]{1,200}", model):
                raise CodexProtocolError("codex_model_identity_invalid")
            if model not in self.turn.models:
                self.turn.models.append(model)
        if self.turn.completed or self.turn.failed:
            raise CodexProtocolError("codex_event_after_terminal")
        if kind == "thread.started":
            identity = event.get("thread_id")
            if not isinstance(identity, str) or not identity or len(identity) > 200:
                raise CodexProtocolError("codex_thread_identity_invalid")
            if self.turn.thread_id:
                raise CodexProtocolError("codex_duplicate_thread")
            self.turn.thread_id = public_text(identity, 200)
        elif kind == "turn.started":
            if self._started or not self.turn.thread_id:
                raise CodexProtocolError("codex_turn_identity_invalid")
            self._started = True
        elif kind == "token_count":
            info = event.get("info")
            usage = info.get("total_token_usage") if isinstance(info, dict) else None
            keys = ("input_tokens", "cached_input_tokens", "output_tokens")
            if isinstance(usage, dict) and all(type(usage.get(k)) is int and usage[k] >= 0 for k in keys):
                # Cumulative counters are a projection signal, not a completed
                # native_summary observation (which would double-charge usage).
                if self._callback:
                    self._callback({"type": "quota.signal", "tokens": {k: usage[k] for k in keys}})
        elif kind == "error":
            # CLI diagnostics (including reconnect attempts) are not a turn
            # terminal. Only a later completed/failed event settles the turn;
            # EOF after a diagnostic remains a failure. Keep a bounded, redacted
            # copy so a usage-limit diagnostic is distinguishable from noise.
            self._error_seen = True
            detail = _usage_limit_message(event)
            self._error_detail = detail
            self._error_fresh = True
        elif kind in {"turn.completed", "turn.failed"}:
            if not self._started:
                raise CodexProtocolError("codex_turn_identity_invalid")
            if kind == "turn.failed":
                terminal = _usage_limit_message(event)
                detail = terminal or (self._error_detail if self._error_fresh else "")
                if detail and usage_limit_hit(detail):
                    self._publish_failure(self._limit_classification, detail, terminal=terminal)
                else:
                    self._publish_failure("codex_turn_failed", detail, terminal=terminal)
            else:
                self.turn.completed = True
                self.turn.failed = False
                self.turn.failure_classification = ""
            usage = event.get("usage")
            if isinstance(usage, dict):
                keys = ("input_tokens", "cached_input_tokens", "output_tokens")
                if all(type(usage.get(k)) is int and usage[k] >= 0 for k in keys):
                    self.turn.usage = {k: usage[k] for k in keys}
        elif kind in {"item.started", "item.updated", "item.completed"}:
            if not self._started:
                raise CodexProtocolError("codex_turn_identity_invalid")
            item = event.get("item")
            if not isinstance(item, dict) or not isinstance(item.get("type"), str):
                raise CodexProtocolError("codex_invalid_item")
            self._error_fresh = False
            item_type = item["type"]
            # Allowlisted projection only: never relay arbitrary provider/MCP data.
            public: dict[str, Any] = {"type": kind, "item_type": public_text(item_type, 80)}
            if item_type == "agent_message":
                text = public_text(item.get("text"), 64 * 1024)
                public["text"] = text
                if kind == "item.completed":
                    self.turn.final_text = text
            elif item_type == "command_execution":
                output = item.get("aggregated_output")
                exit_code = item.get("exit_code")
                setup_failed = (
                    kind == "item.completed" and isinstance(output, str)
                    and "helper_unknown_error" in output.casefold()
                    and "setup refresh had errors" in output.casefold()
                    # A nonnegative child exit code proves a command was
                    # launched. Its stdout may quote these diagnostic words.
                    and not (type(exit_code) is int and exit_code >= 0)
                )
                public["command"] = public_text(item.get("command"), 512)
                if type(item.get("exit_code")) is int:
                    public["exit_code"] = item["exit_code"]
                public["status"] = public_text(item.get("status"), 80)
                # An exit code of -1 on a failed command_execution is a CLI
                # helper/launch failure, not a normal nonzero command exit.
                # Do not let a later turn.completed erase this evidence.
                if (kind == "item.completed" and public["status"] == "failed"
                        and item.get("exit_code") == -1):
                    self.turn.tool_launch_failed = True
                if setup_failed:
                    # Inspect only the bounded command output, never model prose.
                    # Some CLI versions omit the launch exit code. Publish fixed
                    # evidence instead of helper output or a path-bearing command.
                    self.turn.tool_launch_failed = True
                    public["command"] = "[command omitted: helper setup failure]"
                    public["status"] = "failed"
                    public["failure_classification"] = "codex_tool_launch_failed"
                    public["diagnostic"] = "helper_unknown_error: setup refresh had errors"
            elif item_type == "file_change":
                public["status"] = public_text(item.get("status"), 80)
            else:
                public["text"] = "Codex activity"
            public = redact_event(public)
            if len(self.turn.items) < 100:
                self.turn.items.append(public)
            if self._callback:
                self._callback(public)
