from __future__ import annotations

import pytest

from reverse_agent.adapters.bmad_planning import load_planning_reference
from reverse_agent.adapters.github_truth import GitHubTruthObservation
from reverse_agent.adapters.github_work_item import load_github_work_item


def test_bmad_adapter_accepts_structured_context_only() -> None:
    reference = load_planning_reference(
        {
            "schema_version": 1,
            "artifact_type": "prd",
            "path_or_uri": "planning/prd.md",
            "digest": "a" * 64,
            "summary": "Product requirements",
        }
    )
    assert reference.to_dict()["command_authority"] is False
    with pytest.raises(ValueError, match="unsupported_planning_artifact"):
        load_planning_reference({**reference.to_dict(), "artifact_type": "shell_script"})


def test_github_work_item_adapter_requires_complete_identity() -> None:
    payload = {
        "schema_version": 1,
        "repository": "owner/repo",
        "item_number": 7,
        "immutable_observation_ref": "I_kwDO",
        "title": "Architecture task",
        "acceptance_criteria": ["focused tests pass"],
        "requested_operations": ["source_edit"],
        "requested_paths": ["reverse_agent/architecture/**"],
    }
    assert load_github_work_item(payload).item_number == 7
    with pytest.raises(ValueError, match="repository"):
        load_github_work_item({**payload, "repository": ""})


def test_github_truth_observation_has_provenance_and_is_not_authority() -> None:
    observation = GitHubTruthObservation.from_mapping(
        {
            "schema_version": 1,
            "repository": "owner/repo",
            "observation_kind": "pull_request",
            "subject_ref": "refs/pull/9/head",
            "head_sha": "b" * 40,
            "source": "github_api",
            "observed_at": "2026-07-20T16:00:00Z",
        }
    )
    payload = observation.to_dict()
    assert payload["authority"] == "CACHE_OBSERVATION"
    assert payload["authoritative"] is False
    with pytest.raises(ValueError, match="timezone"):
        GitHubTruthObservation.from_mapping({**payload, "observed_at": "2026-07-20T16:00:00"})
