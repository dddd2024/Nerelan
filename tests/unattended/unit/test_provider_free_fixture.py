from __future__ import annotations

import json

import pytest

from reverse_agent.unattended.provider_free_fixture import build_completion


def _payload(*, tool_observed: bool = False) -> dict[str, object]:
    messages: list[dict[str, object]] = [
        {
            "role": "user",
            "content": "create provider-free-runtime-proof.txt",
        }
    ]
    if tool_observed:
        messages.append(
            {
                "role": "tool",
                "tool_call_id": "provider_free_terminal_call",
                "content": "exit_code=0",
            }
        )
    return {
        "model": "provider-free-runtime-proof",
        "messages": messages,
        "tools": [
            {
                "type": "function",
                "function": {
                    "name": "terminal",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "command": {"type": "string"},
                            "timeout": {"type": "integer"},
                        },
                        "required": ["command"],
                    },
                },
            }
        ],
    }


def test_fixture_first_turn_selects_only_terminal_action() -> None:
    completion = build_completion(_payload())
    choice = completion["choices"][0]
    call = choice["message"]["tool_calls"][0]
    arguments = json.loads(call["function"]["arguments"])
    assert choice["finish_reason"] == "tool_calls"
    assert call["function"]["name"] == "terminal"
    assert arguments["command"].count("provider-free-runtime-proof.txt") == 2
    assert "PROVIDER_FREE_RUNTIME_PROOF" in arguments["command"]


def test_fixture_second_turn_returns_fixed_completion() -> None:
    completion = build_completion(_payload(tool_observed=True))
    choice = completion["choices"][0]
    assert choice["finish_reason"] == "stop"
    assert choice["message"] == {
        "role": "assistant",
        "content": "PROVIDER_FREE_RUNTIME_PROOF",
    }


@pytest.mark.parametrize(
    "mutation",
    (
        {"model": "caller-model"},
        {"messages": []},
        {"tools": []},
    ),
)
def test_fixture_rejects_nonfixed_requests(mutation: dict[str, object]) -> None:
    payload = _payload()
    payload.update(mutation)
    with pytest.raises(ValueError):
        build_completion(payload)
