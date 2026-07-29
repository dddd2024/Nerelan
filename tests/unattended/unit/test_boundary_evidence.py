from reverse_agent.unattended.boundary_evidence import (
    StartingBoundaryEvidence,
    inspect_starting_agent_server_compose,
)


def test_fixed_starting_head_boundary_is_recorded_without_values() -> None:
    compose = """
services:
  agent-server:
    environment:
      LLM_API_KEY:
      OH_AGENT_SERVER_ENV: LITELLM_MASTER_KEY
    volumes:
      - /var/run/docker.sock:/var/run/docker.sock
  agent-canvas:
    image: fixed
"""

    evidence = inspect_starting_agent_server_compose(compose).sanitized()

    assert evidence == {
        "current_agent_server_docker_socket": "PRESENT",
        "current_terminal_LLM_API_KEY": "PRESENT",
        "current_terminal_LITELLM_MASTER_KEY": "PRESENT",
        "current_terminal_provider_key": "ABSENT",
    }
    assert set(evidence.values()) <= {"PRESENT", "ABSENT"}


def test_sanitized_evidence_never_contains_source_material() -> None:
    evidence = StartingBoundaryEvidence(True, True, True, False).sanitized()

    assert set(evidence) == {
        "current_agent_server_docker_socket",
        "current_terminal_LLM_API_KEY",
        "current_terminal_LITELLM_MASTER_KEY",
        "current_terminal_provider_key",
    }
    assert set(evidence.values()) == {"PRESENT", "ABSENT"}
