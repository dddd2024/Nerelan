"""Exercise the actual required-check verifier; only HTTP is simulated.

No model, credential, GitHub mutation or network request is made. Transport
composition tests retain the real Request/JSON parser and replace urlopen only.
"""
from __future__ import annotations

import copy
import io
import json
import urllib.error

import pytest

from reverse_agent.github_remote_verifier import (
    GitHubEvidenceError,
    GitHubRemoteAcceptanceVerifier,
)

REPO = "dddd2024/Nerelan"
HEAD = "a" * 40
API = "https://api.github.com"


def record(run_id=1, name="baseline", **changes):
    result = {
        "id": run_id, "name": name, "head_sha": HEAD,
        "url": f"{API}/repos/{REPO}/check-runs/{run_id}",
        "status": "completed", "conclusion": "success",
        "app": {"id": 15368, "slug": "github-actions"},
    }
    result.update(changes)
    return result


def verifier(pages):
    instance = GitHubRemoteAcceptanceVerifier(repository=REPO, token="test-placeholder")
    calls = []
    iterator = iter(pages)

    def request(path):
        calls.append(path)
        response = next(iterator)
        if isinstance(response, Exception):
            raise response
        return copy.deepcopy(response)

    instance._request_json = request
    return instance, calls


def check(runs, contexts=("baseline",)):
    v, _ = verifier([{"total_count": len(runs), "check_runs": runs}])
    return v.verify_check_run_contexts(head_sha=HEAD, required_contexts=contexts)


def test_success_retains_actual_identity_and_does_not_grant_merge():
    result = check([record()])
    assert result["verified"] is True
    assert result["contexts"] == {"baseline": True}
    assert result["context_check_ids"] == {"baseline": [1]}
    assert result["required_producer"] == {"id": 15368, "slug": "github-actions"}
    assert not any(result.get(key) for key in ("merge_authority", "implementation_complete", "product_accepted"))


@pytest.mark.parametrize("app", [
    {"id": 999, "slug": "github-actions"},
    {"id": 15368, "slug": "not-github-actions"},
    {"id": 999, "slug": "foreign", "name": "GitHub Actions"},
    {"id": "15368", "slug": "github-actions"},
    {"id": 15368.0, "slug": "github-actions"},
    {"id": True, "slug": "github-actions"},
    {"id": 0, "slug": "github-actions"},
    {"id": -1, "slug": "github-actions"},
    {"id": 15368}, {"slug": "github-actions"}, None, [], "github-actions",
])
def test_wrong_missing_or_malformed_app_cannot_satisfy_context(app):
    assert check([record(app=app)])["verified"] is False


def test_missing_app_is_not_inferred_from_name():
    run = record()
    del run["app"]
    assert check([run])["verified"] is False


@pytest.mark.parametrize("status,conclusion", [
    ("completed", "failure"), ("in_progress", None), ("queued", None),
    ("completed", "cancelled"), ("completed", "timed_out"),
    ("completed", "action_required"), ("completed", "neutral"),
    ("completed", "stale"), ("completed", None), ("completed", ""),
    ("unknown", "success"), ("in_progress", "success"),
])
def test_trusted_non_success_is_not_hidden_by_success(status, conclusion):
    result = check([record(), record(2, status=status, conclusion=conclusion)])
    assert result["verified"] is False
    assert result["blocking_check_ids"]["baseline"] == [2]
    assert result["context_check_ids"]["baseline"] == [1]


def test_skipped_never_satisfies_but_separate_skipped_event_is_compatible():
    skipped = record(2, conclusion="skipped")
    assert check([skipped])["verified"] is False
    result = check([record(), skipped])
    assert result["verified"] is True
    assert result["context_check_ids"]["baseline"] == [1]
    assert result["skipped_check_ids"]["baseline"] == [2]


def test_all_successful_event_observations_are_retained_without_id_ranking():
    result = check([record(5), record(2)])
    assert result["verified"] is True
    assert result["context_check_ids"]["baseline"] == [5, 2]


def test_foreign_app_neither_satisfies_nor_overrides_expected_app():
    foreign = record(2, conclusion="failure", app={"id": 999, "slug": "other"})
    result = check([record(), foreign])
    assert result["verified"] is True
    assert result["ignored_foreign_check_ids"] == [2]
    assert result["context_check_ids"] == {"baseline": [1]}


def test_missing_required_and_draft_inert_do_not_pass():
    result = check([record(name="landing-state-gate-draft-inert")], ("landing-state-gate",))
    assert result["verified"] is False
    assert check([record()], ("baseline", "state-gate"))["verified"] is False


def test_unrelated_valid_record_does_not_veto_required_success():
    assert check([record(), record(2, "unrelated", conclusion="failure")])["verified"] is True


@pytest.mark.parametrize("contexts", [
    (), [], "baseline", {"baseline"}, {"baseline": True}, None,
    ["baseline", "baseline"], [""], [" baseline"], ["baseline "],
    ["base\nline"], ["base\x00line"], ["x" * 257], [None], [False],
    [f"context-{i}" for i in range(101)],
])
def test_invalid_requirements_fail_before_network(contexts):
    v, calls = verifier([])
    result = v.verify_check_run_contexts(head_sha=HEAD, required_contexts=contexts)
    assert result["verified"] is False
    assert calls == []


def test_names_are_exact_case_sensitive_and_support_spaces_unicode():
    assert check([record(name="CI / 功能验证")], ["CI / 功能验证"])["verified"] is True
    assert check([record(name="BASELINE")])["verified"] is False
    assert check([record()], ("baseline", "BASELINE"))["verified"] is False


@pytest.mark.parametrize("head", [None, False, 42, "", "HEAD", "a" * 39, "a" * 41, "A" * 40, HEAD + "\n", "main?x=y"])
def test_bad_head_fails_before_network(head):
    v, calls = verifier([])
    assert v.verify_check_run_contexts(head_sha=head, required_contexts=("baseline",))["verified"] is False
    assert calls == []


@pytest.mark.parametrize("host", ["http://api.github.com", "https://enterprise.example/api/v3", "https://api.github.com.evil.example"])
def test_no_github_dot_com_policy_fallback_for_other_hosts(host):
    v, calls = verifier([])
    v.api_url = host
    result = v.verify_check_run_contexts(head_sha=HEAD, required_contexts=("baseline",))
    assert result["reason"] == "check_producer_policy_unavailable"
    assert calls == []


@pytest.mark.parametrize("repo", ["owner/repo?token=x", "owner/..", "../repo", "owner/repo#x", "owner/repo/extra", "owner%2Fother/repo"])
def test_invalid_repository_rejected_before_request(repo):
    v, calls = verifier([])
    v.repository = repo
    assert v.verify_check_run_contexts(head_sha=HEAD, required_contexts=("baseline",))["verified"] is False
    assert calls == []


@pytest.mark.parametrize("changes", [
    {"head_sha": "b" * 40}, {"head_sha": None},
    {"url": "https://api.github.com/repos/other/repo/check-runs/1"},
    {"url": f"{API}/repos/{REPO}/check-runs/1?unexpected=1"},
    {"url": f"{API}/repos/{REPO}/check-runs/2"}, {"url": None},
    {"id": True}, {"id": "1"}, {"id": 1.0}, {"id": 0}, {"id": -1},
    {"name": None}, {"name": "\nbaseline"}, {"status": True}, {"conclusion": []},
])
def test_observed_identity_and_record_types_are_not_overwritten(changes):
    assert check([record(**changes)])["verified"] is False


@pytest.mark.parametrize("payload", [
    None, [], "response", {}, {"check_runs": []},
    {"total_count": True, "check_runs": []},
    {"total_count": "1", "check_runs": [record()]},
    {"total_count": 1.0, "check_runs": [record()]},
    {"total_count": -1, "check_runs": []},
    {"total_count": 1, "check_runs": {}},
    {"total_count": 1, "check_runs": [None]},
    {"total_count": 0, "check_runs": [record()]},
    {"total_count": 101, "check_runs": [record()]},
])
def test_malformed_or_incomplete_payload_never_passes(payload):
    v, _ = verifier([payload])
    assert v.verify_check_run_contexts(head_sha=HEAD, required_contexts=("baseline",))["verified"] is False


def test_complete_two_page_observation_uses_latest_filter():
    first = [record(i, f"extra-{i}") for i in range(1, 101)]
    v, calls = verifier([
        {"total_count": 101, "check_runs": first},
        {"total_count": 101, "check_runs": [record(101)]},
    ])
    result = v.verify_check_run_contexts(head_sha=HEAD, required_contexts=("baseline",))
    assert result["verified"] is True
    assert result["context_check_ids"] == {"baseline": [101]}
    assert len(result["check_runs"]) == 101
    assert calls == [f"/repos/{REPO}/commits/{HEAD}/check-runs?per_page=100&filter=latest&page={p}" for p in (1, 2)]


@pytest.mark.parametrize("second", [
    {"total_count": 102, "check_runs": [record(101), record(102)]},
    {"total_count": 101, "check_runs": []},
    {"total_count": 101, "check_runs": [record(1)]},
    GitHubEvidenceError("github_api_failure:TimeoutError"),
])
def test_first_page_success_cannot_hide_later_collection_failure(second):
    v, calls = verifier([
        {"total_count": 101, "check_runs": [record(i) for i in range(1, 101)]}, second,
    ])
    assert v.verify_check_run_contexts(head_sha=HEAD, required_contexts=("baseline",))["verified"] is False
    assert len(calls) == 2


def test_second_page_failure_conflicts_with_first_page_success():
    first = [record(i) for i in range(1, 101)]
    v, _ = verifier([
        {"total_count": 101, "check_runs": first},
        {"total_count": 101, "check_runs": [record(101, conclusion="failure")]},
    ])
    result = v.verify_check_run_contexts(head_sha=HEAD, required_contexts=("baseline",))
    assert result["verified"] is False
    assert result["blocking_check_ids"]["baseline"] == [101]


def test_duplicate_identity_is_not_multiple_evidence():
    assert check([record(), record()])["reason"] == "duplicate_check_run_id"


def test_maximum_complete_observation_and_overflow_bound():
    pages = [{"total_count": 1000, "check_runs": [record(i) for i in range(p * 100 + 1, p * 100 + 101)]} for p in range(10)]
    v, calls = verifier(pages)
    assert v.verify_check_run_contexts(head_sha=HEAD, required_contexts=("baseline",))["verified"] is True
    assert len(calls) == 10
    v, calls = verifier([{"total_count": 1001, "check_runs": [record()]}])
    result = v.verify_check_run_contexts(head_sha=HEAD, required_contexts=("baseline",))
    assert result["reason"] == "check_runs_observation_limit"
    assert len(calls) == 1


class Response(io.BytesIO):
    status = 200


def test_real_request_and_json_parser_are_composed(monkeypatch):
    requested = []

    def open_response(request, timeout):
        assert request.get_method() == "GET"
        assert timeout == 30
        requested.append(request.full_url)
        return Response(json.dumps({"total_count": 1, "check_runs": [record()]}).encode())

    monkeypatch.setattr("urllib.request.urlopen", open_response)
    v = GitHubRemoteAcceptanceVerifier(repository=REPO, token="test-placeholder")
    result = v.verify_check_run_contexts(head_sha=HEAD, required_contexts=("baseline",))
    assert result["verified"] is True
    assert requested == [f"{API}/repos/{REPO}/commits/{HEAD}/check-runs?per_page=100&filter=latest&page=1"]


@pytest.mark.parametrize("body", [b"not JSON", b"null", b"[]", b"{\"check_runs\":[]}", b"\xff"])
def test_transport_malformed_bytes_fail_closed(body, monkeypatch):
    monkeypatch.setattr("urllib.request.urlopen", lambda *args, **kwargs: Response(body))
    v = GitHubRemoteAcceptanceVerifier(repository=REPO, token="test-placeholder")
    assert v.verify_check_run_contexts(head_sha=HEAD, required_contexts=("baseline",))["verified"] is False


def test_network_error_does_not_become_a_success(monkeypatch):
    def unavailable(*args, **kwargs):
        raise urllib.error.URLError("simulated offline boundary")
    monkeypatch.setattr("urllib.request.urlopen", unavailable)
    v = GitHubRemoteAcceptanceVerifier(repository=REPO, token="test-placeholder")
    assert v.verify_check_run_contexts(head_sha=HEAD, required_contexts=("baseline",))["verified"] is False
