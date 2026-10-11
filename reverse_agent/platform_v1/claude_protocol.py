"""Bounded, secret-free normalization of ``claude -p --output-format stream-json``.

Claude Code emits one JSON object per line: a ``system``/``init`` event, then
``assistant`` and ``user`` messages whose ``content`` blocks carry text and
tool activity, and a final ``result`` event with the final text and usage.
Only an allowlisted projection is relayed. As with Codex, a completed turn
proves neither functional correctness nor independent review, and
subscription usage is never converted into an invented dollar cost.
"""

from __future__ import annotations

import json
from typing import Any, Callable

from .codex_protocol import CodexProtocolError, CodexTurn, public_text
from .opencode_executor import redact_event


class ClaudeProtocolError(CodexProtocolError):
    """Finite classification; raw provider output is never part of the error."""


_USAGE_KEYS = ("input_tokens", "cache_read_input_tokens", "output_tokens")


class ClaudeStreamJson:
    """Incremental UTF-8 framing with independent line, stream and event bounds."""

    def __init__(
        self,
        callback: Callable[[dict[str, Any]], None] | None = None,
        *,
        max_frame_bytes: int = 512 * 1024,
        max_stream_bytes: int = 4 * 1024 * 1024,
        max_events: int = 4000,
    ) -> None:
        if not (0 < max_frame_bytes <= max_stream_bytes <= 8 * 1024 * 1024):
            raise ValueError("claude_protocol_limits_invalid")
        if not 0 < max_events <= 10000:
            raise ValueError("claude_protocol_limits_invalid")
        self.turn = CodexTurn()
        self._callback = callback
        self._frame_limit = max_frame_bytes
        self._stream_limit = max_stream_bytes
        self._event_limit = max_events
        self._buffer = bytearray()
        self._bytes = 0
        self._events = 0

    def feed(self, chunk: bytes) -> None:
        if not isinstance(chunk, bytes):
            raise TypeError("claude_protocol_requires_bytes")
        self._bytes += len(chunk)
        if self._bytes > self._stream_limit:
            raise ClaudeProtocolError("claude_code_stream_limit_exceeded")
        self._buffer.extend(chunk)
        while b"\n" in self._buffer:
            end = self._buffer.index(b"\n")
            line = bytes(self._buffer[:end])
            del self._buffer[:end + 1]
            self._line(line)
        if len(self._buffer) > self._frame_limit:
            raise ClaudeProtocolError("claude_code_frame_limit_exceeded")

    def finish(self) -> CodexTurn:
        if self._buffer:
            self._line(bytes(self._buffer))
            self._buffer.clear()
        if not (self.turn.completed or self.turn.failed):
            raise ClaudeProtocolError("claude_code_turn_incomplete")
        if self.turn.completed and not self.turn.final_text:
            raise ClaudeProtocolError("claude_code_final_message_missing")
        return self.turn

    def _publish(self, public: dict[str, Any]) -> None:
        public = redact_event(public)
        if len(self.turn.items) < 100:
            self.turn.items.append(public)
        if self._callback:
            self._callback(public)

    def _line(self, line: bytes) -> None:
        if len(line) > self._frame_limit:
            raise ClaudeProtocolError("claude_code_frame_limit_exceeded")
        if not line.strip():
            return
        self._events += 1
        if self._events > self._event_limit:
            raise ClaudeProtocolError("claude_code_event_limit_exceeded")
        try:
            event = json.loads(line.decode("utf-8"))
        except (UnicodeDecodeError, json.JSONDecodeError, RecursionError) as exc:
            raise ClaudeProtocolError("claude_code_invalid_jsonl") from exc
        if not isinstance(event, dict) or not isinstance(event.get("type"), str):
            raise ClaudeProtocolError("claude_code_invalid_event")
        kind = event["type"]
        if self.turn.completed or self.turn.failed:
            raise ClaudeProtocolError("claude_code_event_after_terminal")
        if kind == "system":
            if event.get("subtype") == "init":
                identity = event.get("session_id")
                if not isinstance(identity, str) or not identity or len(identity) > 200:
                    raise ClaudeProtocolError("claude_code_session_identity_invalid")
                if self.turn.thread_id:
                    raise ClaudeProtocolError("claude_code_duplicate_session")
                self.turn.thread_id = public_text(identity, 200)
            return
        if not self.turn.thread_id:
            raise ClaudeProtocolError("claude_code_session_identity_invalid")
        if kind == "assistant":
            message = event.get("message")
            content = message.get("content") if isinstance(message, dict) else None
            if not isinstance(content, list):
                raise ClaudeProtocolError("claude_code_invalid_message")
            for block in content[:50]:
                if not isinstance(block, dict):
                    continue
                block_type = block.get("type")
                if block_type == "text":
                    self._publish({"type": "assistant", "item_type": "agent_message",
                                   "text": public_text(block.get("text"), 64 * 1024)})
                elif block_type == "tool_use":
                    name = public_text(block.get("name"), 80)
                    public: dict[str, Any] = {"type": "assistant", "item_type": "tool_use", "tool": name}
                    arguments = block.get("input")
                    if name == "Bash" and isinstance(arguments, dict):
                        public["command"] = public_text(arguments.get("command"), 512)
                    elif isinstance(arguments, dict) and isinstance(arguments.get("file_path"), str):
                        public["path"] = public_text(arguments["file_path"], 512)
                    self._publish(public)
            return
        if kind == "user":
            # Tool results can echo file contents or command output; never relay them.
            return
        if kind == "result":
            subtype = event.get("subtype")
            is_error = event.get("is_error") is True
            self.turn.completed = subtype == "success" and not is_error
            self.turn.failed = not self.turn.completed
            if self.turn.completed:
                self.turn.final_text = public_text(event.get("result"), 64 * 1024)
            else:
                reason = subtype if isinstance(subtype, str) and subtype.replace("_", "").isalnum() else "error"
                self.turn.failure_classification = f"claude_code_turn_failed:{reason[:60]}"
            usage = event.get("usage")
            if isinstance(usage, dict) and all(type(usage.get(k)) is int and usage[k] >= 0 for k in _USAGE_KEYS):
                self.turn.usage = {
                    "input_tokens": usage["input_tokens"],
                    "cached_input_tokens": usage["cache_read_input_tokens"],
                    "output_tokens": usage["output_tokens"],
                }
            return
        # Unknown event kinds (e.g. stream_event, rate_limit notices) are ignored.
