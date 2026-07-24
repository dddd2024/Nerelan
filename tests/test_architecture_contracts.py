from __future__ import annotations

import json

import pytest

from reverse_agent.architecture.authority import planning_reference_can_authorize
from reverse_agent.architecture.contracts import AuthorizationRequirement, GitHubWorkItem, PlanningReference, WorkflowIdentity, stable_json
from reverse_agent.architecture.risk import WorkflowRoute


def _planning_payload() -> dict[str, object]:
    return {
        "schema_version": 1,
        "artifact_type": "architecture",
        "path_or_uri": "docs/architecture/example.md",
        "digest": "a" * 64,
        "summary": "Bounded architecture context",
    }


def test_planning_reference_serialization_is_stable_and_non_authoritative() -> None:
    reference = PlanningReference.from_mapping(_planning_payload())
    encoded = stable_json(reference.to_dict())
    assert encoded == stable_json(json.loads(encoded))
    assert PlanningReference.from_mapping(json.loads(encoded)) == reference
    assert reference.to_dict()["command_authority"] is False
    assert planning_reference_can_authorize(reference) is False


def test_planning_reference_rejects_command_authority_and_bad_digest() -> None:
    payload = _planning_payload()
    payload["command_authority"] = True
    with pytest.raises(ValueError, match="cannot_authorize"):
        PlanningReference.from_mapping(payload)
    payload = _planning_payload()
    payload["digest"] = "not-a-digest"
    with pytest.raises(ValueError, match="digest"):
        PlanningReference.from_mapping(payload)


def test_github_work_item_and_workflow_identity_are_stable() -> None:
    item = GitHubWorkItem.from_mapping(
        {
            "schema_version": 1,
            "repository": "owner/repo",
            "item_number": 42,
            "immutable_observation_ref": "issue-node-id",
            "title": "Implement bounded change",
            "acceptance_criteria": ["tests pass"],
            "requested_operations": ["source_edit", "unit_test"],
            "requested_paths": ["reverse_agent/example.py"],
        }
    )
    assert item.identity == "owner/repo#42@issue-node-id"
    assert GitHubWorkItem.from_mapping(item.to_dict()) == item
    identity = WorkflowIdentity("workflow-1", item.identity)
    assert identity.to_dict()["attempt"] == 1


def test_authorization_requirement_matches_route() -> None:
    requirement = AuthorizationRequirement(True, WorkflowRoute.TRUST_AUTHORIZATION_REQUIRED, ("risk:R2",))
    assert requirement.to_dict()["required"] is True
    with pytest.raises(ValueError, match="route_mismatch"):
        AuthorizationRequirement(False, WorkflowRoute.TRUST_AUTHORIZATION_REQUIRED)


@pytest.mark.parametrize("field", ["repository", "immutable_observation_ref", "acceptance_criteria"])
def test_github_work_item_missing_identity_fails_closed(field: str) -> None:
    payload = {
        "schema_version": 1,
        "repository": "owner/repo",
        "item_number": 1,
        "immutable_observation_ref": "node",
        "title": "Task",
        "acceptance_criteria": ["done"],
        "requested_operations": ["review"],
        "requested_paths": ["README.md"],
    }
    payload.pop(field)
    with pytest.raises(ValueError):
        GitHubWorkItem.from_mapping(payload)
