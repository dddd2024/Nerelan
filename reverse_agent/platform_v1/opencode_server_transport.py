"""Bounded OpenCode Server transport for Platform V1.

The transport deliberately implements only the small official API surface the
executor needs: health, session creation, the project SSE stream, asynchronous
prompt submission, session abort, and instance disposal.  It never persists
raw events or content and it accepts only an executor-created loopback server.
"""

from __future__ import annotations

import base64
from dataclasses import dataclass
import hashlib
import json
import os
from pathlib import Path
import re
import secrets
import socket
import subprocess
import time
from typing import Any, Callable, Mapping, Sequence
from urllib.error import HTTPError, URLError
from urllib.parse import quote, urlencode, urlsplit
from urllib.request import (
    HTTPRedirectHandler,
    Request,
    build_opener,
)

from .model_availability import no_credits_error, provider_rate_limit_reply


MAX_JSON_BYTES = 1_048_576
MAX_SSE_EVENT_BYTES = 1_048_576
_OVERSIZED_SSE_PREFIX_BYTES = 2048
SERVER_USERNAME = "reverse-agent"
_VERSION_RE = re.compile(r"^[A-Za-z0-9._+-]{1,64}$")
_PROVIDER_ID_RE = re.compile(r"^[A-Za-z][A-Za-z0-9_-]{0,127}$")
_SSE_TYPE_RE = re.compile(r'"type"\s*:\s*"([^"]+)"')
_SSE_ROLE_RE = re.compile(r'"role"\s*:\s*"([^"]+)"')
_SSE_ASSISTANT_ROLE_RE = re.compile(r'"role"\s*:\s*"assistant"')
_SKIPPABLE_OVERSIZED_SSE_TYPES = frozenset({
    "message.part.updated",
    "message.part.delta",
    "session.diff",
})


def _is_skippable_oversized_sse(prefix: bytes) -> bool:
    """Allow non-accounting, non-terminal SSE payloads (e.g. large diffs/parts) to drain."""
    text = prefix.decode("utf-8", errors="replace")
    type_match = _SSE_TYPE_RE.search(text)
    if type_match is None:
        return False
    event_type = type_match.group(1)
    if event_type in _SKIPPABLE_OVERSIZED_SSE_TYPES:
        return True
    if event_type == "message.updated":
        role_match = _SSE_ROLE_RE.search(text)
        return (
            role_match is not None
            and role_match.group(1) == "user"
            and _SSE_ASSISTANT_ROLE_RE.search(text) is None
        )
    return False


def _session_error_texts(properties: Mapping[str, Any]) -> list[str]:
    error = properties.get("error")
    candidates: list[str] = []
    if isinstance(error, str):
        candidates.append(error)
    elif isinstance(error, Mapping):
        for key in ("message", "msg"):
            value = error.get(key)
            if isinstance(value, str):
                candidates.append(value)
        data = error.get("data")
        if isinstance(data, Mapping):
            for key in ("message", "msg"):
                value = data.get(key)
                if isinstance(value, str):
                    candidates.append(value)
    return candidates


def _session_error_no_credits(properties: Mapping[str, Any]) -> bool:
    return any(no_credits_error(text) for text in _session_error_texts(properties))


def _session_error_rate_limit(properties: Mapping[str, Any]) -> bool:
    candidates = _session_error_texts(properties)
    if any(no_credits_error(text) for text in candidates):
        return False
    return any(provider_rate_limit_reply(text) for text in candidates)


def _extract_rate_limit_reset_at(texts: Sequence[str]) -> str:
    """Return a validated UTC ISO reset timestamp from rate-limit text, or ''."""
    from .codex_protocol import local_now, parse_reset_time

    now = local_now()
    for text in texts:
        if not isinstance(text, str) or not text:
            continue
        reset = parse_reset_time(text, now)
        if reset:
            return reset
    return ""


def _account_no_credits_retry(status: Any) -> bool:
    if not isinstance(status, Mapping) or status.get("type") != "retry":
        return False
    message = status.get("message")
    return isinstance(message, str) and bool(no_credits_error(message))


def _account_rate_limit_retry(status: Any) -> bool:
    if not isinstance(status, Mapping) or status.get("type") != "retry":
        return False
    message = status.get("message")
    if not isinstance(message, str) or no_credits_error(message):
        return False
    action = status.get("action")
    return ((isinstance(action, Mapping) and action.get("reason") == "account_rate_limit")
            or provider_rate_limit_reply(message))


class OpenCodeServerTransportError(RuntimeError):
    """A sanitized, closed-classification server transport failure."""


@dataclass(frozen=True)
class ServerTransportResult:
    success: bool
    failure_classification: str = ""
    abort_state: str = "NOT_REQUESTED"
    server_version: str = ""
    session_digest: str = ""
    usage_event_count: int = 0
    failure_reset_at: str = ""
    session_id: str = ""


@dataclass(frozen=True)
class ProviderAuthMethod:
    """Sanitized provider-advertised authentication method."""

    index: int
    type: str
    label: str


@dataclass(frozen=True)
class ProviderAuthAuthorization:
    """Transient browser continuation returned by OpenCode."""

    url: str
    method: str
    instructions: str


class _NoRedirect(HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):  # noqa: ANN001
        raise OpenCodeServerTransportError("server_redirect_forbidden")


class _DeadlineReader:
    """File-like wrapper that arms a socket for every underlying read.

    ``HTTPResponse`` parses chunk framing with buffered ``readline`` calls below
    ``read1``, so one relative socket timeout can be extended by a peer that
    dribbles bytes inside a chunk-size or extension line.  Recompute the
    remaining absolute deadline before every underlying read instead.
    """

    def __init__(self, fp: Any, sock: Any, deadline: Callable[[], float]) -> None:
        self._fp = fp
        self._sock = sock
        self._deadline = deadline
        self.pending = bytearray()

    def _arm(self) -> None:
        remaining = self._deadline() - time.monotonic()
        if remaining <= 0:
            raise TimeoutError
        if self._sock is not None:
            self._sock.settimeout(remaining)

    def _read1(self, size: int) -> bytes:
        if self.pending:
            take = len(self.pending) if size < 0 else min(size, len(self.pending))
            chunk = bytes(self.pending[:take])
            del self.pending[:take]
            return chunk
        self._arm()
        return self._fp.read1(size)

    def _fill(self, size: int) -> bytes:
        """Read fresh bytes from the underlying stream into ``pending``.

        ``_read1`` drains ``pending`` first, so a caller that wants to grow
        ``pending`` must bypass it and read the underlying stream directly.
        """

        self._arm()
        return self._fp.read1(size)

    def read1(self, size: int = -1) -> bytes:
        if size == 0:
            return b""
        return self._read1(size)

    def read(self, size: int = -1) -> bytes:
        if size is None or size < 0:
            chunks: list[bytes] = []
            while True:
                chunk = self._read1(-1)
                if not chunk:
                    return b"".join(chunks)
                chunks.append(chunk)
        chunks = []
        remaining = size
        while remaining > 0:
            chunk = self._read1(remaining)
            if not chunk:
                break
            chunks.append(chunk)
            remaining -= len(chunk)
        return b"".join(chunks)

    def readline(self, size: int = -1) -> bytes:
        limit = size if size is not None and size >= 0 else None
        while True:
            end = self.pending.find(b"\n")
            if end >= 0:
                take = end + 1 if limit is None else min(end + 1, limit)
                line = bytes(self.pending[:take])
                del self.pending[:take]
                return line
            if limit is not None and len(self.pending) >= limit:
                line = bytes(self.pending[:limit])
                del self.pending[:limit]
                return line
            # Keep the consumed bytes: HTTPResponse parses the chunk-size
            # and chunk-extension lines through this call, so dropping the
            # read result loses the framing and the payload.  Read the
            # underlying stream directly, because ``_read1`` drains
            # ``pending`` first and would only re-insert the same bytes.
            chunk = self._fill(4096)
            if not chunk:
                break
            self.pending.extend(chunk)
        take = len(self.pending) if limit is None else min(limit, len(self.pending))
        line = bytes(self.pending[:take])
        del self.pending[:take]
        return line

    def readinto(self, buffer: Any) -> int:
        data = self.read(len(buffer))
        buffer[: len(data)] = data
        return len(data)

    def peek(self, size: int = -1) -> bytes:
        if size >= 0:
            while len(self.pending) < size:
                # Read the underlying stream directly.  ``_read1`` drains
                # ``pending`` first, so reusing it here would remove and
                # re-insert the same bytes forever without ever arming the
                # deadline or reaching the socket.
                chunk = self._fill(4096)
                if not chunk:
                    break
                self.pending.extend(chunk)
            return bytes(self.pending[:size])
        return bytes(self.pending)

    def close(self) -> None:
        self._fp.close()

    def flush(self) -> None:
        flush = getattr(self._fp, "flush", None)
        if flush is not None:
            flush()

    def readable(self) -> bool:
        return True


class _DeadlineSSEStream:
    """Read bounded SSE lines without extending a deadline on partial bytes."""

    def __init__(self, response: Any) -> None:
        self.response = response
        self.pending = bytearray()
        self.deadline = 0.0
        self._reader: _DeadlineReader | None = None
        fp = getattr(response, "fp", None)
        sock = getattr(getattr(fp, "raw", None), "_sock", None)
        if callable(getattr(fp, "read1", None)) and sock is not None:
            self._reader = _DeadlineReader(fp, sock, lambda: self.deadline)
            response.fp = self._reader

    def readline(self, limit: int) -> bytes:
        while b"\n" not in self.pending and len(self.pending) < limit:
            remaining = self.deadline - time.monotonic()
            if remaining <= 0:
                raise TimeoutError
            if self._reader is None:
                sock = getattr(getattr(getattr(self.response, "fp", None), "raw", None), "_sock", None)
                if sock is not None:
                    sock.settimeout(remaining)
            # HTTPResponse.read1 returns after at most one buffered/raw read;
            # readline could wait forever on a peer dribbling an unfinished line.
            chunk = self.response.read1(min(65536, limit - len(self.pending)))
            if not chunk:
                break
            self.pending.extend(chunk)
        end = self.pending.find(b"\n")
        size = min(limit, end + 1 if end >= 0 else len(self.pending))
        line = bytes(self.pending[:size])
        del self.pending[:size]
        return line

    def close(self) -> None:
        self.response.close()


MAX_RECENT_USAGE_MESSAGES = 512
PROGRESS_FILTER_BYTES = 64 * 1024


class _ProgressFilter:
    """Fixed-size Bloom filter for identity/state pairs, never evicted.

    A false positive can withhold a progress refresh, never invent progress.
    Usage delivery must stay separate: this filter cannot discard accounting.
    """

    def __init__(self) -> None:
        self.bits = bytearray(PROGRESS_FILTER_BYTES)

    def remember(self, key: str, state: str) -> bool:
        digest = hashlib.sha256((key + "\0" + state).encode("utf-8")).digest()
        positions = [int.from_bytes(digest[offset:offset + 8], "big") % (len(self.bits) * 8)
                     for offset in range(0, 32, 8)]
        fresh = any(not self.bits[bit // 8] & (1 << (bit % 8)) for bit in positions)
        for bit in positions:
            self.bits[bit // 8] |= 1 << (bit % 8)
        return fresh


def _safe_digest(value: str, prefix: str) -> str:
    return prefix + hashlib.sha256(value.encode("utf-8")).hexdigest()


def _remember_recent_usage(memory: dict[str, str], key: str, state: str) -> bool:
    """Skip exact recent usage repeats; the ledger owns durable deduplication."""

    if memory.get(key) == state:
        return False
    if key not in memory and len(memory) >= MAX_RECENT_USAGE_MESSAGES:
        memory.pop(next(iter(memory)))
    memory[key] = state
    return True


def _state_digest(value: Any) -> str:
    return _safe_digest(json.dumps(value, sort_keys=True), "state-")


MAX_CONSECUTIVE_IDENTICAL_TOOL_CALLS = 5


def _part_progress(part: Mapping[str, Any]) -> tuple[str, str] | None:
    part_type = part.get("type")
    if part_type not in {"text", "reasoning", "tool"}:
        return None
    raw_id = part.get("id")
    if not isinstance(raw_id, str) or not raw_id:
        raw_id = part.get("partID")
    if not isinstance(raw_id, str) or not raw_id:
        raw_id = part.get("part_id")
    identity = raw_id if isinstance(raw_id, str) and raw_id else _state_digest(part)
    return _safe_digest(identity, "part-"), _state_digest(part)


def _completed_tool_signature(part: Mapping[str, Any]) -> tuple[str, str] | None:
    """Return ``(part_key, call_signature)`` for a completed/errored tool part, or None."""
    if part.get("type") != "tool":
        return None
    state = part.get("state")
    if not isinstance(state, Mapping):
        return None
    status = str(state.get("status") or "").lower()
    if status not in {"completed", "error"}:
        return None
    tool_name = part.get("tool") or part.get("name")
    if not isinstance(tool_name, str) or not tool_name.strip():
        return None
    raw_id = part.get("id") or part.get("partID") or part.get("part_id") or part.get("callID")
    part_key = _safe_digest(str(raw_id), "tool-") if isinstance(raw_id, str) and raw_id else _state_digest(part)
    sig = _state_digest({
        "tool": tool_name,
        "status": status,
        "input": state.get("input"),
        "error": state.get("error") if status == "error" else "",
    })
    return part_key, sig


def _message_progress(info: Mapping[str, Any], completed: Mapping[str, Any]) -> tuple[str, str]:
    raw_id = info.get("id")
    identity = raw_id if isinstance(raw_id, str) and raw_id else _state_digest(info)
    state = _state_digest(
        {
            "completed": completed.get("completed"),
            "cost": info.get("cost"),
            "tokens": info.get("tokens"),
        }
    )
    return _safe_digest(identity, "message-"), state


def _validate_child_id(value: Any, name: str) -> str:
    if not isinstance(value, str) or not value or len(value) > 1024:
        raise OpenCodeServerTransportError(f"invalid_server_{name}")
    return value


def _validate_loopback_base_url(base_url: str) -> str:
    try:
        parsed = urlsplit(base_url)
        port = parsed.port
    except ValueError as exc:
        raise OpenCodeServerTransportError("invalid_server_url") from exc
    if (
        parsed.scheme != "http"
        or parsed.hostname not in {"127.0.0.1", "::1"}
        or port is None
        or parsed.username is not None
        or parsed.password is not None
        or parsed.path not in {"", "/"}
        or parsed.query
        or parsed.fragment
    ):
        raise OpenCodeServerTransportError("server_endpoint_not_loopback")
    host = f"[{parsed.hostname}]" if ":" in parsed.hostname else parsed.hostname
    return f"http://{host}:{port}"


def _usage_projection(info: Mapping[str, Any]) -> dict[str, Any]:
    """Project one assistant message onto the closed numeric usage shape."""

    time_value = info.get("time")
    tokens_value = info.get("tokens")
    tokens = tokens_value if isinstance(tokens_value, Mapping) else {}
    cache_value = tokens.get("cache")
    cache = cache_value if isinstance(cache_value, Mapping) else {}
    return {
        "id": _validate_child_id(info.get("id"), "message_id"),
        "sessionID": _validate_child_id(info.get("sessionID"), "session_id"),
        "role": "assistant",
        "time": {
            "completed": (
                time_value.get("completed")
                if isinstance(time_value, Mapping)
                else None
            )
        },
        "cost": info.get("cost"),
        "tokens": {
            "input": tokens.get("input"),
            "output": tokens.get("output"),
            "reasoning": tokens.get("reasoning"),
            "cache": {
                "read": cache.get("read"),
                "write": cache.get("write"),
            },
        },
    }


class OpenCodeServerClient:
    """Minimal authenticated client for one executor-owned server process."""

    def __init__(
        self,
        *,
        base_url: str,
        username: str,
        password: str,
        timeout: float,
        idle_timeout: float = 900.0,
    ) -> None:
        self.base_url = _validate_loopback_base_url(base_url)
        if not username or not password:
            raise OpenCodeServerTransportError("server_basic_auth_required")
        self.timeout = max(0.1, float(timeout))
        self.idle_timeout = max(0.1, float(idle_timeout))
        token = base64.b64encode(f"{username}:{password}".encode("utf-8")).decode("ascii")
        self._authorization = f"Basic {token}"
        self._opener = build_opener(_NoRedirect())

    def health(self, *, timeout: float | None = None) -> str:
        payload = self._json_request("GET", "/global/health", timeout=timeout)
        if not isinstance(payload, Mapping) or payload.get("healthy") is not True:
            raise OpenCodeServerTransportError("server_health_invalid")
        version = payload.get("version")
        if not isinstance(version, str) or not _VERSION_RE.fullmatch(version):
            raise OpenCodeServerTransportError("server_version_invalid")
        return version

    def create_session(self, *, directory: str, title: str, timeout: float | None = None) -> str:
        payload = self._json_request(
            "POST",
            "/session",
            query={"directory": directory},
            body={"title": title[:128]},
            timeout=timeout,
        )
        if not isinstance(payload, Mapping):
            raise OpenCodeServerTransportError("session_create_invalid")
        session_id = _validate_child_id(payload.get("id"), "session_id")
        returned_directory = payload.get("directory")
        if not isinstance(returned_directory, str):
            raise OpenCodeServerTransportError("session_directory_missing")
        if Path(returned_directory).resolve() != Path(directory).resolve():
            raise OpenCodeServerTransportError("session_directory_mismatch")
        return session_id

    def prompt_async(
        self,
        *,
        directory: str,
        session_id: str,
        prompt: str,
        provider_id: str,
        model_id: str,
        agent: str,
        timeout: float | None = None,
    ) -> None:
        body: dict[str, Any] = {
            "parts": [{"type": "text", "text": prompt}],
        }
        if agent:
            body["agent"] = agent
        if provider_id and model_id:
            body["model"] = {"providerID": provider_id, "modelID": model_id}
        self._empty_request(
            "POST",
            f"/session/{quote(session_id, safe='')}/prompt_async",
            query={"directory": directory},
            body=body,
            expected_status=204,
            timeout=timeout,
        )

    def abort(self, *, directory: str, session_id: str, timeout: float | None = None) -> bool:
        payload = self._json_request(
            "POST",
            f"/session/{quote(session_id, safe='')}/abort",
            query={"directory": directory},
            timeout=timeout,
        )
        return payload is True

    def dispose(self, *, directory: str) -> bool:
        try:
            payload = self._json_request(
                "POST", "/instance/dispose", query={"directory": directory}, timeout=min(2.0, self.timeout)
            )
        except OpenCodeServerTransportError:
            return False
        return payload is True

    def provider_auth_methods(
        self, *, directory: str, provider_id: str
    ) -> tuple[ProviderAuthMethod, ...]:
        """Return only bounded methods advertised for one exact provider."""

        provider = _validate_provider_id(provider_id)
        payload = self._json_request(
            "GET", "/provider/auth", query={"directory": directory}
        )
        if not isinstance(payload, Mapping):
            raise OpenCodeServerTransportError("provider_auth_methods_invalid")
        raw_methods = payload.get(provider)
        if not isinstance(raw_methods, list):
            raise OpenCodeServerTransportError("provider_auth_method_missing")
        methods: list[ProviderAuthMethod] = []
        for index, raw in enumerate(raw_methods):
            if not isinstance(raw, Mapping):
                raise OpenCodeServerTransportError("provider_auth_method_invalid")
            method_type = raw.get("type")
            label = raw.get("label")
            if method_type not in {"oauth", "api"}:
                raise OpenCodeServerTransportError("provider_auth_type_invalid")
            if (
                not isinstance(label, str)
                or not label.strip()
                or len(label) > 200
                or any(ord(char) < 32 for char in label)
            ):
                raise OpenCodeServerTransportError("provider_auth_label_invalid")
            methods.append(
                ProviderAuthMethod(index=index, type=method_type, label=label.strip())
            )
        return tuple(methods)

    def provider_oauth_authorize(
        self, *, directory: str, provider_id: str, method_index: int
    ) -> ProviderAuthAuthorization:
        provider = _validate_provider_id(provider_id)
        index = _validate_method_index(method_index)
        payload = self._json_request(
            "POST",
            f"/provider/{quote(provider, safe='')}/oauth/authorize",
            query={"directory": directory},
            body={"method": index},
        )
        if not isinstance(payload, Mapping):
            raise OpenCodeServerTransportError("provider_oauth_authorization_invalid")
        url = payload.get("url")
        callback_method = payload.get("method")
        instructions = payload.get("instructions")
        try:
            parsed = urlsplit(url) if isinstance(url, str) else None
        except ValueError as exc:
            raise OpenCodeServerTransportError(
                "provider_oauth_authorization_url_invalid"
            ) from exc
        if (
            parsed is None
            or parsed.scheme != "https"
            or not parsed.netloc
            or parsed.username is not None
            or parsed.password is not None
            or parsed.fragment
            or len(url) > 8192
        ):
            raise OpenCodeServerTransportError(
                "provider_oauth_authorization_url_invalid"
            )
        if callback_method not in {"auto", "code"}:
            raise OpenCodeServerTransportError("provider_oauth_callback_method_invalid")
        if not isinstance(instructions, str) or len(instructions) > 2000:
            raise OpenCodeServerTransportError("provider_oauth_instructions_invalid")
        return ProviderAuthAuthorization(
            url=url,
            method=callback_method,
            instructions=instructions,
        )

    def provider_oauth_callback(
        self,
        *,
        directory: str,
        provider_id: str,
        method_index: int,
        code: str | None = None,
    ) -> bool:
        provider = _validate_provider_id(provider_id)
        index = _validate_method_index(method_index)
        body: dict[str, Any] = {"method": index}
        if code is not None:
            if not isinstance(code, str) or not code or len(code) > 4096:
                raise OpenCodeServerTransportError("provider_oauth_code_invalid")
            body["code"] = code
        payload = self._json_request(
            "POST",
            f"/provider/{quote(provider, safe='')}/oauth/callback",
            query={"directory": directory},
            body=body,
        )
        if not isinstance(payload, bool):
            raise OpenCodeServerTransportError("provider_oauth_callback_invalid")
        return payload

    def run_role(
        self,
        *,
        directory: str,
        title: str,
        prompt: str,
        provider_id: str,
        model_id: str,
        agent: str,
        usage_observer: Callable[[Mapping[str, Any]], bool],
    ) -> ServerTransportResult:
        """Run one exact-session role and return only sanitized control facts."""

        deadline = time.monotonic() + self.timeout
        version = self.health(timeout=self._remaining(deadline))
        stream = _DeadlineSSEStream(self._open_sse(
            directory=directory, timeout=min(self.idle_timeout, self._remaining(deadline))))
        session_id = ""
        usage_count = 0
        try:
            first = self._read_sse_event(stream, deadline)
            if first.get("type") != "server.connected":
                raise OpenCodeServerTransportError("server_connected_event_missing")
            session_id = self.create_session(directory=directory, title=title, timeout=self._remaining(deadline))
            self.prompt_async(
                directory=directory,
                session_id=session_id,
                prompt=prompt,
                provider_id=provider_id,
                model_id=model_id,
                agent=agent,
                timeout=self._remaining(deadline),
            )
            progress_deadline = time.monotonic() + self.idle_timeout
            progress = _ProgressFilter()
            seen_messages: dict[str, str] = {}
            seen_tool_parts: set[str] = set()
            last_tool_sig = ""
            repeat_tool_count = 0
            while True:
                event = self._read_sse_event(stream, min(deadline, progress_deadline))
                event_type = event.get("type")
                properties = event.get("properties")
                if not isinstance(properties, Mapping):
                    continue
                now = time.monotonic()
                if now >= min(deadline, progress_deadline):
                    raise OpenCodeServerTransportError("server_event_timeout")
                # Session-bound content and tool transitions are useful progress.
                # Keepalives, server.connected and other sessions never refresh it.
                part = properties.get("part")
                if event_type == "message.part.delta" and properties.get("sessionID") == session_id:
                    if properties.get("field") in {"text", "reasoning"} and isinstance(properties.get("delta"), str) and properties["delta"]:
                        progress_deadline = now + self.idle_timeout
                elif event_type == "message.part.updated" and isinstance(part, Mapping) and part.get("sessionID") == session_id:
                    update = _part_progress(part)
                    if update is not None and progress.remember(*update):
                        progress_deadline = now + self.idle_timeout
                    tool_sig = _completed_tool_signature(part)
                    if tool_sig is not None:
                        tool_key, sig = tool_sig
                        if tool_key not in seen_tool_parts:
                            seen_tool_parts.add(tool_key)
                            if sig == last_tool_sig:
                                repeat_tool_count += 1
                            else:
                                last_tool_sig = sig
                                repeat_tool_count = 1
                            if repeat_tool_count >= MAX_CONSECUTIVE_IDENTICAL_TOOL_CALLS:
                                confirmed = self._abort_stream_confirmed(directory=directory, session_id=session_id)
                                return ServerTransportResult(
                                    success=False,
                                    failure_classification="executor_tool_loop",
                                    abort_state="STREAM_ABORT_CONFIRMED" if confirmed else "STREAM_ABORT_UNKNOWN",
                                    server_version=version,
                                    session_digest=_safe_digest(session_id, "session-"),
                                    usage_event_count=usage_count,
                                    session_id=session_id,
                                )
                if event_type == "message.updated":
                    info = properties.get("info")
                    if not isinstance(info, Mapping):
                        continue
                    if info.get("sessionID") != session_id or info.get("role") != "assistant":
                        continue
                    completed = info.get("time")
                    if not isinstance(completed, Mapping) or not completed.get("completed"):
                        continue
                    update = _message_progress(info, completed)
                    if progress.remember(*update):
                        progress_deadline = now + self.idle_timeout
                    if not _remember_recent_usage(seen_messages, *update):
                        continue
                    projected = _usage_projection(info)
                    usage_count += 1
                    if usage_observer(projected):
                        confirmed = self._abort_stream_confirmed(directory=directory, session_id=session_id)
                        return ServerTransportResult(
                            success=False,
                            failure_classification=(
                                "stream_budget_abort_confirmed"
                                if confirmed
                                else "stream_budget_abort_unknown"
                            ),
                            abort_state=(
                                "STREAM_ABORT_CONFIRMED"
                                if confirmed
                                else "STREAM_ABORT_UNKNOWN"
                            ),
                            server_version=version,
                            session_digest=_safe_digest(session_id, "session-"),
                            usage_event_count=usage_count,
                            session_id=session_id,
                        )
                    continue
                bound_session = properties.get("sessionID")
                if event_type == "session.status" and bound_session == session_id:
                    status = properties.get("status")
                    if _account_no_credits_retry(status):
                        confirmed = self._abort_stream_confirmed(directory=directory, session_id=session_id)
                        return ServerTransportResult(
                            success=False,
                            failure_classification="provider_no_credits",
                            abort_state="STREAM_ABORT_CONFIRMED" if confirmed else "STREAM_ABORT_UNKNOWN",
                            server_version=version,
                            session_digest=_safe_digest(session_id, "session-"),
                            usage_event_count=usage_count,
                            session_id=session_id,
                        )
                    if _account_rate_limit_retry(status):
                        reset_at = _extract_rate_limit_reset_at((status.get("message", ""),))
                        confirmed = self._abort_stream_confirmed(directory=directory, session_id=session_id)
                        return ServerTransportResult(
                            success=False,
                            failure_classification="api_error_429",
                            abort_state="STREAM_ABORT_CONFIRMED" if confirmed else "STREAM_ABORT_UNKNOWN",
                            server_version=version,
                            session_digest=_safe_digest(session_id, "session-"),
                            usage_event_count=usage_count,
                            failure_reset_at=reset_at,
                            session_id=session_id,
                        )
                if event_type == "session.idle" and bound_session == session_id:
                    return ServerTransportResult(
                        success=True,
                        server_version=version,
                        session_digest=_safe_digest(session_id, "session-"),
                        usage_event_count=usage_count,
                        session_id=session_id,
                    )
                if event_type == "session.error" and bound_session == session_id:
                    classification = (
                        "provider_no_credits"
                        if _session_error_no_credits(properties)
                        else "api_error_429"
                        if _session_error_rate_limit(properties)
                        else "server_session_error"
                    )
                    reset_at = (
                        _extract_rate_limit_reset_at(_session_error_texts(properties))
                        if classification == "api_error_429"
                        else ""
                    )
                    return ServerTransportResult(
                        success=False,
                        failure_classification=classification,
                        server_version=version,
                        session_digest=_safe_digest(session_id, "session-"),
                        usage_event_count=usage_count,
                        failure_reset_at=reset_at,
                        session_id=session_id,
                    )
        except OpenCodeServerTransportError as exc:
            if str(exc) != "server_event_timeout" or not session_id:
                raise
            classification = "server_role_deadline_exceeded" if time.monotonic() >= deadline else "server_stream_stalled"
            confirmed = self._abort_stream_confirmed(directory=directory, session_id=session_id)
            return ServerTransportResult(
                success=False, failure_classification=classification,
                abort_state="STREAM_ABORT_CONFIRMED" if confirmed else "STREAM_ABORT_UNKNOWN",
                server_version=version, session_digest=_safe_digest(session_id, "session-"),
                usage_event_count=usage_count, session_id=session_id)
        finally:
            try:
                stream.close()
            except Exception:
                pass

    def _abort_stream_confirmed(self, *, directory: str, session_id: str) -> bool:
        try:
            return self.abort(directory=directory, session_id=session_id, timeout=min(2.0, self.timeout))
        except OpenCodeServerTransportError:
            return False

    def _open_sse(self, *, directory: str, timeout: float):
        request = self._request(
            "GET", "/event", query={"directory": directory}, accept="text/event-stream"
        )
        try:
            response = self._opener.open(request, timeout=timeout)
        except OpenCodeServerTransportError:
            raise
        except (HTTPError, URLError, TimeoutError, OSError) as exc:
            raise OpenCodeServerTransportError("server_event_connect_failed") from exc
        content_type = response.headers.get_content_type()
        if content_type != "text/event-stream":
            response.close()
            raise OpenCodeServerTransportError("server_event_content_type_invalid")
        return response

    def _read_sse_line(self, stream: Any, deadline: float, limit: int) -> bytes:
        if self._remaining(deadline) <= 0:
            raise OpenCodeServerTransportError("server_event_timeout")
        try:
            if isinstance(stream, _DeadlineSSEStream):
                stream.deadline = deadline
            line = stream.readline(limit)
        except (TimeoutError, OSError) as exc:
            raise OpenCodeServerTransportError("server_event_timeout") from exc
        if not line:
            raise OpenCodeServerTransportError("server_event_disconnected")
        return line

    def _read_sse_event(self, stream: Any, deadline: float) -> Mapping[str, Any]:
        data_lines: list[bytes] = []
        prefix = bytearray()
        total = 0
        oversized = False
        while True:
            line = self._read_sse_line(
                stream, deadline, 65536 if oversized else MAX_SSE_EVENT_BYTES + 1
            )
            if not line.endswith(b"\n"):
                if not oversized and line.startswith(b"data:"):
                    value = line[5:]
                    if value.startswith(b" "):
                        value = value[1:]
                    if len(prefix) < _OVERSIZED_SSE_PREFIX_BYTES:
                        prefix.extend(value[: _OVERSIZED_SSE_PREFIX_BYTES - len(prefix)])
                oversized = True
                data_lines.clear()
                while not line.endswith(b"\n"):
                    line = self._read_sse_line(stream, deadline, 65536)
                continue
            if line in {b"\n", b"\r\n"}:
                if oversized:
                    if _is_skippable_oversized_sse(bytes(prefix)):
                        return {"type": "server.event.oversized", "properties": {}}
                    raise OpenCodeServerTransportError("server_event_too_large")
                if not data_lines:
                    total = 0
                    prefix.clear()
                    continue
                raw = b"\n".join(data_lines)
                try:
                    event = json.loads(raw.decode("utf-8"))
                except (UnicodeDecodeError, json.JSONDecodeError) as exc:
                    raise OpenCodeServerTransportError("server_event_malformed") from exc
                if not isinstance(event, Mapping):
                    raise OpenCodeServerTransportError("server_event_shape_invalid")
                return event
            if oversized:
                continue
            total += len(line)
            if line.startswith(b"data:"):
                value = line[5:]
                if value.startswith(b" "):
                    value = value[1:]
                value = value.rstrip(b"\r\n")
                if len(prefix) < _OVERSIZED_SSE_PREFIX_BYTES:
                    prefix.extend(value[: _OVERSIZED_SSE_PREFIX_BYTES - len(prefix)])
                if total > MAX_SSE_EVENT_BYTES:
                    oversized = True
                    data_lines.clear()
                else:
                    data_lines.append(value)
            elif total > MAX_SSE_EVENT_BYTES:
                oversized = True
                data_lines.clear()

    def _json_request(
        self,
        method: str,
        path: str,
        *,
        query: Mapping[str, str] | None = None,
        body: Mapping[str, Any] | None = None,
        timeout: float | None = None,
    ) -> Any:
        request = self._request(method, path, query=query, body=body, accept="application/json")
        try:
            response = self._opener.open(request, timeout=timeout or self.timeout)
            with response:
                if response.headers.get_content_type() != "application/json":
                    raise OpenCodeServerTransportError("server_json_content_type_invalid")
                raw = response.read(MAX_JSON_BYTES + 1)
        except OpenCodeServerTransportError:
            raise
        except (HTTPError, URLError, TimeoutError, OSError) as exc:
            raise OpenCodeServerTransportError("server_http_request_failed") from exc
        if len(raw) > MAX_JSON_BYTES:
            raise OpenCodeServerTransportError("server_json_too_large")
        try:
            return json.loads(raw.decode("utf-8"))
        except (UnicodeDecodeError, json.JSONDecodeError) as exc:
            raise OpenCodeServerTransportError("server_json_malformed") from exc

    def _empty_request(
        self,
        method: str,
        path: str,
        *,
        query: Mapping[str, str],
        body: Mapping[str, Any],
        expected_status: int,
        timeout: float | None = None,
    ) -> None:
        request = self._request(method, path, query=query, body=body, accept="application/json")
        try:
            response = self._opener.open(request, timeout=timeout or self.timeout)
            with response:
                if response.status != expected_status:
                    raise OpenCodeServerTransportError("server_http_status_invalid")
                if response.read(1):
                    raise OpenCodeServerTransportError("server_empty_response_expected")
        except OpenCodeServerTransportError:
            raise
        except (HTTPError, URLError, TimeoutError, OSError) as exc:
            raise OpenCodeServerTransportError("server_http_request_failed") from exc

    def _request(
        self,
        method: str,
        path: str,
        *,
        query: Mapping[str, str] | None = None,
        body: Mapping[str, Any] | None = None,
        accept: str,
    ) -> Request:
        if not path.startswith("/") or "//" in path or "?" in path or "#" in path:
            raise OpenCodeServerTransportError("server_request_path_invalid")
        url = self.base_url + path
        if query:
            url += "?" + urlencode(query)
        data = None
        headers = {"Accept": accept, "Authorization": self._authorization}
        if body is not None:
            data = json.dumps(body, ensure_ascii=True, separators=(",", ":")).encode("utf-8")
            if len(data) > MAX_JSON_BYTES:
                raise OpenCodeServerTransportError("server_request_too_large")
            headers["Content-Type"] = "application/json"
        return Request(url, data=data, headers=headers, method=method)

    @staticmethod
    def _remaining(deadline: float) -> float:
        remaining = deadline - time.monotonic()
        if remaining <= 0:
            raise OpenCodeServerTransportError("server_event_timeout")
        return remaining


def _reserve_loopback_port() -> int:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.bind(("127.0.0.1", 0))
        return int(sock.getsockname()[1])


def _validate_provider_id(value: Any) -> str:
    if not isinstance(value, str) or not _PROVIDER_ID_RE.fullmatch(value):
        raise OpenCodeServerTransportError("provider_id_invalid")
    return value


def _validate_method_index(value: Any) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or not 0 <= value <= 100:
        raise OpenCodeServerTransportError("provider_auth_method_index_invalid")
    return value


@dataclass
class ManagedOpenCodeServer:
    """One authenticated loopback OpenCode child with deterministic cleanup."""

    process: Any
    client: OpenCodeServerClient
    directory: str
    _closed: bool = False

    def provider_auth_methods(
        self, *, provider_id: str
    ) -> tuple[ProviderAuthMethod, ...]:
        return self.client.provider_auth_methods(
            directory=self.directory, provider_id=provider_id
        )

    def provider_oauth_authorize(
        self, *, provider_id: str, method_index: int
    ) -> ProviderAuthAuthorization:
        return self.client.provider_oauth_authorize(
            directory=self.directory,
            provider_id=provider_id,
            method_index=method_index,
        )

    def provider_oauth_callback(
        self, *, provider_id: str, method_index: int, code: str | None = None
    ) -> bool:
        return self.client.provider_oauth_callback(
            directory=self.directory,
            provider_id=provider_id,
            method_index=method_index,
            code=code,
        )

    def close(self) -> None:
        if self._closed:
            return
        self._closed = True
        self.client.dispose(directory=self.directory)
        try:
            self.process.wait(timeout=2.0)
        except subprocess.TimeoutExpired:
            self.process.terminate()
            try:
                self.process.wait(timeout=2.0)
            except subprocess.TimeoutExpired:
                self.process.kill()
                self.process.wait(timeout=2.0)


def start_managed_server(
    *,
    cli_path: str,
    is_cmd: bool,
    cwd: str,
    child_env: Mapping[str, str],
    timeout: float,
) -> ManagedOpenCodeServer:
    """Start one authenticated loopback server and return after health passes."""

    password = secrets.token_urlsafe(32)
    env = dict(child_env)
    env["OPENCODE_SERVER_USERNAME"] = SERVER_USERNAME
    env["OPENCODE_SERVER_PASSWORD"] = password
    port = _reserve_loopback_port()
    server_args = ["serve", "--hostname", "127.0.0.1", "--port", str(port)]
    if is_cmd:
        comspec = os.environ.get("COMSPEC", "cmd.exe")
        argv = [comspec, "/d", "/s", "/c", cli_path, *server_args]
    else:
        argv = [cli_path, *server_args]
    try:
        process = subprocess.Popen(
            argv,
            cwd=cwd,
            env=env,
            stdin=subprocess.DEVNULL,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            shell=False,
        )
    except (FileNotFoundError, OSError) as exc:
        raise OpenCodeServerTransportError("server_process_start_failed") from exc
    client = OpenCodeServerClient(
        base_url=f"http://127.0.0.1:{port}",
        username=SERVER_USERNAME,
        password=password,
        timeout=timeout,
    )
    managed = ManagedOpenCodeServer(process=process, client=client, directory=cwd)
    try:
        deadline = time.monotonic() + min(float(timeout), 10.0)
        while True:
            if process.poll() is not None:
                raise OpenCodeServerTransportError("server_process_exited_before_health")
            try:
                client.health(timeout=min(0.25, max(0.1, deadline - time.monotonic())))
                return managed
            except OpenCodeServerTransportError:
                if time.monotonic() >= deadline:
                    raise OpenCodeServerTransportError("server_health_timeout")
                time.sleep(0.05)
    except Exception:
        managed.close()
        raise


def run_managed_server_role(
    *,
    cli_path: str,
    is_cmd: bool,
    cwd: str,
    child_env: Mapping[str, str],
    timeout: float,
    title: str,
    prompt: str,
    provider_id: str,
    model_id: str,
    agent: str,
    usage_observer: Callable[[Mapping[str, Any]], bool],
) -> ServerTransportResult:
    """Start, use, and stop exactly one authenticated loopback server child."""

    managed = start_managed_server(
        cli_path=cli_path,
        is_cmd=is_cmd,
        cwd=cwd,
        child_env=child_env,
        timeout=timeout,
    )
    try:
        return managed.client.run_role(
            directory=cwd,
            title=title,
            prompt=prompt,
            provider_id=provider_id,
            model_id=model_id,
            agent=agent,
            usage_observer=usage_observer,
        )
    finally:
        managed.close()
