"""Test-only fixed OpenAI-compatible fixture for one Gate 2 tool action."""

from __future__ import annotations

import json
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from typing import Any, Mapping

_MODEL = "provider-free-runtime-proof"
_AUTHORIZATION = "Bearer provider-free-fixture-only"
_MAX_REQUEST_BYTES = 1024 * 1024
_COMMAND = (
    "printf 'PROVIDER_FREE_RUNTIME_PROOF' > "
    "provider-free-runtime-proof.txt && "
    "test \"$(cat provider-free-runtime-proof.txt)\" = "
    "'PROVIDER_FREE_RUNTIME_PROOF'"
)


def _tool_arguments(function: Mapping[str, Any]) -> dict[str, Any]:
    parameters = function.get("parameters")
    if not isinstance(parameters, Mapping):
        raise ValueError("fixture_tool_parameters_missing")
    properties = parameters.get("properties")
    if not isinstance(properties, Mapping):
        raise ValueError("fixture_tool_properties_missing")
    required = parameters.get("required", [])
    if not isinstance(required, list):
        raise ValueError("fixture_tool_required_invalid")
    arguments: dict[str, Any] = {}
    for name in required:
        specification = properties.get(name)
        if not isinstance(name, str) or not isinstance(specification, Mapping):
            raise ValueError("fixture_tool_required_unknown")
        kind = specification.get("type")
        lowered = name.lower()
        if lowered == "command":
            arguments[name] = _COMMAND
        elif lowered == "commands":
            arguments[name] = [_COMMAND]
        elif lowered in {"timeout", "timeout_seconds"}:
            arguments[name] = 30
        elif kind == "boolean":
            arguments[name] = False
        elif kind == "integer":
            arguments[name] = 1
        elif kind == "array":
            arguments[name] = []
        elif kind == "string":
            arguments[name] = ""
        else:
            raise ValueError("fixture_tool_required_unsupported")
    if "command" in properties:
        arguments["command"] = _COMMAND
    elif "commands" in properties:
        arguments["commands"] = [_COMMAND]
    else:
        raise ValueError("fixture_terminal_command_missing")
    return arguments


def _select_terminal_tool(payload: Mapping[str, Any]) -> tuple[str, dict[str, Any]]:
    tools = payload.get("tools")
    if not isinstance(tools, list):
        raise ValueError("fixture_tools_missing")
    for tool in tools:
        if not isinstance(tool, Mapping):
            continue
        function = tool.get("function")
        if not isinstance(function, Mapping):
            continue
        name = function.get("name")
        if isinstance(name, str) and "terminal" in name.lower():
            return name, _tool_arguments(function)
    raise ValueError("fixture_terminal_tool_missing")


def build_completion(payload: Mapping[str, Any]) -> dict[str, Any]:
    if payload.get("model") != _MODEL:
        raise ValueError("fixture_model_forbidden")
    messages = payload.get("messages")
    if not isinstance(messages, list) or not messages:
        raise ValueError("fixture_messages_missing")
    rendered = json.dumps(messages, ensure_ascii=True)
    if (
        "provider-free-runtime-proof.txt" not in rendered
        and not any(
            isinstance(message, Mapping) and message.get("role") == "tool"
            for message in messages
        )
    ):
        raise ValueError("fixture_instruction_mismatch")
    tool_observed = any(
        isinstance(message, Mapping) and message.get("role") == "tool"
        for message in messages
    )
    if tool_observed:
        message: dict[str, Any] = {
            "role": "assistant",
            "content": "PROVIDER_FREE_RUNTIME_PROOF",
        }
        finish_reason = "stop"
    else:
        name, arguments = _select_terminal_tool(payload)
        message = {
            "role": "assistant",
            "content": None,
            "tool_calls": [
                {
                    "id": "provider_free_terminal_call",
                    "type": "function",
                    "function": {
                        "name": name,
                        "arguments": json.dumps(
                            arguments,
                            ensure_ascii=True,
                            separators=(",", ":"),
                        ),
                    },
                }
            ],
        }
        finish_reason = "tool_calls"
    return {
        "id": "provider-free-runtime-proof",
        "object": "chat.completion",
        "created": 1,
        "model": _MODEL,
        "choices": [
            {
                "index": 0,
                "message": message,
                "finish_reason": finish_reason,
            }
        ],
        "usage": {
            "prompt_tokens": 1,
            "completion_tokens": 1,
            "total_tokens": 2,
        },
    }


def _stream_chunks(completion: Mapping[str, Any]) -> bytes:
    choice = completion["choices"][0]
    message = choice["message"]
    chunk = {
        "id": completion["id"],
        "object": "chat.completion.chunk",
        "created": completion["created"],
        "model": completion["model"],
        "choices": [
            {
                "index": 0,
                "delta": message,
                "finish_reason": None,
            }
        ],
    }
    finished = {
        "id": completion["id"],
        "object": "chat.completion.chunk",
        "created": completion["created"],
        "model": completion["model"],
        "choices": [
            {
                "index": 0,
                "delta": {},
                "finish_reason": choice["finish_reason"],
            }
        ],
    }
    return (
        f"data: {json.dumps(chunk, separators=(',', ':'))}\n\n"
        f"data: {json.dumps(finished, separators=(',', ':'))}\n\n"
        "data: [DONE]\n\n"
    ).encode("utf-8")


class _Handler(BaseHTTPRequestHandler):
    server_version = "ProviderFreeRuntimeProof/1"

    def log_message(self, format: str, *args: object) -> None:
        return

    def do_GET(self) -> None:
        if self.path == "/health":
            self._json(200, {"status": "PASS"})
            return
        if self.path == "/v1/models" and self.headers.get(
            "Authorization"
        ) == _AUTHORIZATION:
            self._json(
                200,
                {
                    "object": "list",
                    "data": [
                        {
                            "id": _MODEL,
                            "object": "model",
                            "created": 1,
                            "owned_by": "provider-free-fixture",
                        }
                    ],
                },
            )
            return
        self._json(404, {"error": "not_found"})

    def do_POST(self) -> None:
        if (
            self.path != "/v1/chat/completions"
            or self.headers.get("Authorization") != _AUTHORIZATION
        ):
            self._json(404, {"error": "not_found"})
            return
        try:
            length = int(self.headers.get("Content-Length", "0"))
            if length <= 0 or length > _MAX_REQUEST_BYTES:
                raise ValueError("fixture_request_size")
            payload = json.loads(self.rfile.read(length))
            if not isinstance(payload, Mapping):
                raise ValueError("fixture_request_shape")
            completion = build_completion(payload)
        except Exception:
            self._json(400, {"error": "fixed_fixture_rejected"})
            return
        if payload.get("stream") is True:
            body = _stream_chunks(completion)
            self.send_response(200)
            self.send_header("Content-Type", "text/event-stream")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)
            return
        self._json(200, completion)

    def _json(self, status: int, payload: Mapping[str, Any]) -> None:
        body = json.dumps(payload, separators=(",", ":")).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)


def main() -> int:
    server = ThreadingHTTPServer(("0.0.0.0", 9000), _Handler)
    try:
        server.serve_forever()
    finally:
        server.server_close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
