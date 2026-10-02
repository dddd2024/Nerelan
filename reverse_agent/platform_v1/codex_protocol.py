"""Bounded, secret-free normalization of native ``codex exec --json`` events.

Transport framing is separate from Task acceptance: a completed turn proves
neither functional correctness nor independent review. Unknown usage stays
unknown; subscription tokens are never converted to an invented dollar cost.
"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass, field
from typing import Any, Callable

from .opencode_executor import redact_event, redact_secrets
from .task_runtime import ExecutorRuntimeError


class CodexProtocolError(ExecutorRuntimeError):
    """Finite classification; raw provider output is never part of the error."""


def public_text(value: Any, limit: int = 4096) -> str:
    if not isinstance(value, str):
        return ""
    # Redact the whole bounded frame before truncating public evidence.
    # The shared redactor handles many provider patterns, but its generic
    # Authorization substitution can consume only 'Bearer', leaving the token.
    value = re.sub(r"(?im)\bauthorization\s*:\s*[^\r\n]*", "Authorization: [REDACTED]", value)
    value = re.sub(r"(?i)\bbearer\s+[A-Za-z0-9._~+/=-]+", "Bearer [REDACTED]", value)
    return redact_secrets(value).replace("\x00", "").encode("utf-8")[:limit].decode(
        "utf-8", errors="ignore"
    )


@dataclass
class CodexTurn:
    thread_id: str = ""
    completed: bool = False
    failed: bool = False
    final_text: str = ""
    failure_classification: str = ""
    usage: dict[str, int] | None = None
    items: list[dict[str, Any]] = field(default_factory=list)


class CodexJsonl:
    """Incremental UTF-8 framing with independent line, stream and item bounds."""

    def __init__(
        self,
        callback: Callable[[dict[str, Any]], None] | None = None,
        *,
        max_frame_bytes: int = 256 * 1024,
        max_stream_bytes: int = 2 * 1024 * 1024,
        max_events: int = 2000,
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
        self._buffer = bytearray()
        self._bytes = 0
        self._events = 0
        self._started = False

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
        elif kind in {"turn.completed", "turn.failed", "error"}:
            if kind != "error" and not self._started:
                raise CodexProtocolError("codex_turn_identity_invalid")
            self.turn.completed = kind == "turn.completed"
            self.turn.failed = not self.turn.completed
            self.turn.failure_classification = "" if self.turn.completed else "codex_turn_failed"
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
            item_type = item["type"]
            # Allowlisted projection only: never relay arbitrary provider/MCP data.
            public: dict[str, Any] = {"type": kind, "item_type": public_text(item_type, 80)}
            if item_type == "agent_message":
                text = public_text(item.get("text"), 64 * 1024)
                public["text"] = text
                if kind == "item.completed":
                    self.turn.final_text = text
            elif item_type == "command_execution":
                public["command"] = public_text(item.get("command"), 512)
                if type(item.get("exit_code")) is int:
                    public["exit_code"] = item["exit_code"]
                public["status"] = public_text(item.get("status"), 80)
            elif item_type == "file_change":
                public["status"] = public_text(item.get("status"), 80)
            else:
                public["text"] = "Codex activity"
            public = redact_event(public)
            if len(self.turn.items) < 100:
                self.turn.items.append(public)
            if self._callback:
                self._callback(public)
