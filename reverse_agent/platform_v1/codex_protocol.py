"""Bounded, secret-free normalization of native ``codex exec --json`` events.

Transport framing is separate from Task acceptance: a completed turn proves
neither functional correctness nor independent review. Unknown usage stays
unknown; subscription tokens are never converted to an invented dollar cost.
"""

from __future__ import annotations

import json
import re
from collections import deque
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from typing import Any, Callable, Mapping

from .model_availability import OVERLOADED, provider_overloaded
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


def _truncate_command_output(output: str, keep_bytes: int) -> str:
    """Keep the first and last ``keep_bytes`` of a command output string.

    The output is UTF-8 byte-truncated, not character-truncated, to keep the
    retained size bounded. The two halves are joined with a marker so the
    middle gap is unambiguous. Decode errors are ignored.
    """
    if not isinstance(output, str):
        return ""
    raw = output.encode("utf-8", errors="replace")
    if len(raw) <= keep_bytes * 2:
        return output
    head = raw[:keep_bytes].decode("utf-8", errors="ignore")
    tail = raw[-keep_bytes:].decode("utf-8", errors="ignore")
    return f"{head}\n... [output truncated, {len(raw)} bytes total] ...\n{tail}"


class _OversizedItemFrame:
    """Stream-accumulates a frame that exceeds the JSON line limit.

    Only item frames carrying command output are eligible: their output is
    truncated rather than failing the turn. Other oversized frame types fail
    closed. The parser keeps at most ``keep_bytes`` at the head and tail of
    the raw line, so memory is bounded regardless of frame size.
    """

    _ITEM_KINDS = frozenset({"item.started", "item.updated", "item.completed"})
    _TRUNCATABLE_TYPES = frozenset({"command_execution"})
    _EVENT_TYPE_RE = re.compile(rb'"type"\s*:\s*"(item\.(?:started|updated|completed))"')
    _ITEM_TYPE_RE = re.compile(rb'"item"\s*:\s*\{[^}]*?"type"\s*:\s*"(\w+)"')

    def __init__(self, *, frame_limit: int, keep_bytes: int) -> None:
        self._frame_limit = frame_limit
        self._keep = keep_bytes
        self._head = bytearray()
        self._tail = deque(maxlen=keep_bytes)
        self._total = 0
        self._truncated = False
        self._complete: bytes | None = None

    def feed(self, chunk: bytes) -> None:
        self._total += len(chunk)
        if len(self._head) < self._keep:
            space = self._keep - len(self._head)
            self._head.extend(chunk[:space])
            chunk = chunk[space:]
        if chunk:
            self._tail.extend(chunk)
            self._truncated = True

    def set_complete_line(self, line: bytes) -> None:
        """Store the full line when it arrived complete (not streamed)."""
        self._complete = line
        self.feed(line)

    def is_oversized(self) -> bool:
        return self._total > self._frame_limit

    @classmethod
    def line_is_truncatable(cls, line: bytes) -> bool:
        """Check a complete oversized line for truncatability using regex."""
        event_match = cls._EVENT_TYPE_RE.search(line)
        if event_match is None:
            return False
        if event_match.group(1).decode() not in cls._ITEM_KINDS:
            return False
        item_match = cls._ITEM_TYPE_RE.search(line)
        if item_match is None:
            return False
        return item_match.group(1).decode() in cls._TRUNCATABLE_TYPES

    def is_truncatable(self) -> bool:
        return self.line_is_truncatable(bytes(self._head))

    def build_event(self) -> dict[str, Any]:
        """Reconstruct the item event with its aggregated_output truncated."""
        if self._complete is not None:
            raw = self._complete
        else:
            raw = bytes(self._head) + bytes(self._tail)
        try:
            event = json.loads(raw.decode("utf-8"))
        except (UnicodeDecodeError, json.JSONDecodeError):
            event = self._reconstruct_from_head()
        item = event.get("item")
        if isinstance(item, dict):
            output = item.get("aggregated_output")
            if isinstance(output, str):
                item["aggregated_output"] = _truncate_command_output(output, self._keep)
                item["output_truncated"] = True
        return event

    def _reconstruct_from_head(self) -> dict[str, Any]:
        """Best-effort rebuild of an item event from the head bytes when the
        full frame is not valid JSON (e.g. streamed with a split tail)."""
        head = bytes(self._head)
        event_match = self._EVENT_TYPE_RE.search(head)
        kind = event_match.group(1).decode() if event_match else "item.completed"
        item: dict[str, Any] = {"type": "command_execution", "aggregated_output": ""}
        m = re.search(rb'"command"\s*:\s*"((?:[^"\\]|\\.)*)"', head)
        if m:
            item["command"] = m.group(1).decode("utf-8", errors="ignore")
        m = re.search(rb'"status"\s*:\s*"(\w+)"', head)
        if m:
            item["status"] = m.group(1).decode("utf-8", errors="ignore")
        m = re.search(rb'"exit_code"\s*:\s*(-?\d+)', head)
        if m:
            item["exit_code"] = int(m.group(1))
        return {"type": kind, "item": item}


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
        item_output_keep_bytes: int | None = None,
    ) -> None:
        if not (0 < max_frame_bytes <= max_stream_bytes <= 8 * 1024 * 1024):
            raise ValueError("codex_protocol_limits_invalid")
        if not 0 < max_events <= 10000:
            raise ValueError("codex_protocol_limits_invalid")
        if item_output_keep_bytes is None:
            item_output_keep_bytes = min(16 * 1024, max_frame_bytes)
        if not (0 < item_output_keep_bytes <= max_frame_bytes):
            raise ValueError("codex_protocol_limits_invalid")
        self.turn = CodexTurn()
        self._callback = callback
        self._frame_limit = max_frame_bytes
        self._stream_limit = max_stream_bytes
        self._event_limit = max_events
        self._limit_classification = limit_classification
        self._item_keep_bytes = item_output_keep_bytes
        self._buffer = bytearray()
        self._bytes = 0
        self._events = 0
        self._started = False
        self._error_seen = False
        self._error_detail = ""
        self._error_fresh = False
        self._oversized: _OversizedItemFrame | None = None

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
        if self._oversized is not None:
            nl = chunk.find(b"\n")
            if nl == -1:
                self._oversized.feed(chunk)
            else:
                self._oversized.feed(chunk[:nl])
                self._consume_oversized()
                rest = chunk[nl + 1:]
                if rest:
                    self.feed(rest)
            return
        self._buffer.extend(chunk)
        while b"\n" in self._buffer:
            end = self._buffer.index(b"\n")
            line = bytes(self._buffer[:end])
            del self._buffer[:end + 1]
            if len(line) > self._frame_limit:
                if not _OversizedItemFrame.line_is_truncatable(line):
                    raise CodexProtocolError("codex_frame_limit_exceeded")
                oversized = _OversizedItemFrame(
                    frame_limit=self._frame_limit, keep_bytes=self._item_keep_bytes,
                )
                oversized.set_complete_line(line)
                self._oversized = oversized
                self._consume_oversized()
                continue
            self._line(line)
        if len(self._buffer) > self._frame_limit:
            head = bytes(self._buffer[:min(len(self._buffer), self._item_keep_bytes * 4)])
            if not _OversizedItemFrame.line_is_truncatable(head):
                raise CodexProtocolError("codex_frame_limit_exceeded")
            oversized = _OversizedItemFrame(
                frame_limit=self._frame_limit, keep_bytes=self._item_keep_bytes,
            )
            oversized.feed(bytes(self._buffer))
            self._buffer.clear()
            self._oversized = oversized

    def _consume_oversized(self) -> None:
        assert self._oversized is not None
        oversized = self._oversized
        self._oversized = None
        event = oversized.build_event()
        self._process_event(event)

    def finish(self) -> CodexTurn:
        if self._oversized is not None:
            self._consume_oversized()
        if self._buffer:
            self._line(bytes(self._buffer))
            self._buffer.clear()
        if not (self.turn.completed or self.turn.failed):
            if self._error_seen:
                detail = self._error_detail if self._error_fresh else ""
                if usage_limit_hit(detail):
                    self._publish_failure(self._limit_classification, detail)
                elif provider_overloaded(detail):
                    self._publish_failure(OVERLOADED, detail)
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
        try:
            event = json.loads(line.decode("utf-8"))
        except (UnicodeDecodeError, json.JSONDecodeError, RecursionError) as exc:
            raise CodexProtocolError("codex_invalid_jsonl") from exc
        self._process_event(event)

    def _process_event(self, event: Any) -> None:
        if not isinstance(event, dict) or not isinstance(event.get("type"), str):
            raise CodexProtocolError("codex_invalid_event")
        self._events += 1
        if self._events > self._event_limit:
            raise CodexProtocolError("codex_event_limit_exceeded")
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
                elif detail and provider_overloaded(detail):
                    self._publish_failure(OVERLOADED, detail, terminal=terminal)
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
                if item.get("output_truncated") is True:
                    public["output_truncated"] = True
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
