"""Sanitized evidence helpers for the fixed OpenHands starting boundary."""

from __future__ import annotations

import re
from dataclasses import dataclass

_PROVIDER_ENV_NAMES = (
    "ANTHROPIC_API_KEY",
    "AZURE_OPENAI_API_KEY",
    "COHERE_API_KEY",
    "GEMINI_API_KEY",
    "GOOGLE_API_KEY",
    "MISTRAL_API_KEY",
    "OPENAI_API_KEY",
)


@dataclass(frozen=True, slots=True)
class StartingBoundaryEvidence:
    agent_server_docker_socket: bool
    terminal_llm_api_key: bool
    terminal_litellm_master_key: bool
    terminal_provider_key: bool

    def sanitized(self) -> dict[str, str]:
        """Return names and presence booleans only, never credential material."""

        return {
            "current_agent_server_docker_socket": _presence(
                self.agent_server_docker_socket
            ),
            "current_terminal_LLM_API_KEY": _presence(self.terminal_llm_api_key),
            "current_terminal_LITELLM_MASTER_KEY": _presence(
                self.terminal_litellm_master_key
            ),
            "current_terminal_provider_key": _presence(
                self.terminal_provider_key
            ),
        }


def inspect_starting_agent_server_compose(compose_text: str) -> StartingBoundaryEvidence:
    """Inspect exact-name presence in the starting Agent Server service.

    This deliberately does not parse or return environment values. It is only
    an evidence helper for the fixed unsafe starting head, not an acceptance
    check for the successor topology.
    """

    service = re.search(
        r"(?ms)^  agent-server:\s*(.*?)(?=^  [A-Za-z0-9_-]+:\s|^networks:|\Z)",
        compose_text,
    )
    if service is None:
        raise ValueError("agent_server_service_missing")
    block = service.group(0)
    return StartingBoundaryEvidence(
        agent_server_docker_socket="/var/run/docker.sock:/var/run/docker.sock"
        in block,
        terminal_llm_api_key=_has_environment_name(block, "LLM_API_KEY"),
        terminal_litellm_master_key=(
            _has_environment_name(block, "LITELLM_MASTER_KEY")
            or "OH_AGENT_SERVER_ENV" in block
            and "LITELLM_MASTER_KEY" in block
        ),
        terminal_provider_key=any(
            _has_environment_name(block, name) for name in _PROVIDER_ENV_NAMES
        ),
    )


def _has_environment_name(service_block: str, name: str) -> bool:
    return (
        re.search(
            rf"(?m)^\s+{re.escape(name)}\s*:",
            service_block,
        )
        is not None
    )


def _presence(value: bool) -> str:
    return "PRESENT" if value else "ABSENT"
