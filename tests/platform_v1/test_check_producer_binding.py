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



# Full unprojected GitHub API response, fetched 2026-09-30 via the existing
# GitHub connection; compressed only to keep this authorized test path small.
# This is offline replay, not a live verifier-network or merge acceptance.
_LIVE_HEAD = "40afe79b2cc28989cdbf7a40e2e973dc9025325d"
_LIVE_PAYLOAD_SHA256 = "bd4953887f96a67fb93f162a408bdad5de02bfb277f4ade34019ff94c486271e"
_LIVE_PAYLOAD_ZLIB_BASE64 = (
    "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"
)


def live_payload():
    import base64
    import hashlib
    import zlib

    raw = zlib.decompress(base64.b64decode(_LIVE_PAYLOAD_ZLIB_BASE64, validate=True))
    assert hashlib.sha256(raw).hexdigest() == _LIVE_PAYLOAD_SHA256
    payload = json.loads(raw)
    assert payload["total_count"] == len(payload["check_runs"]) == 22
    return payload


def replay_live(payload, monkeypatch):
    requested = []

    def open_response(request, timeout):
        requested.append(request.full_url)
        assert request.get_method() == "GET"
        assert timeout == 30
        return Response(json.dumps(payload).encode())

    monkeypatch.setattr("urllib.request.urlopen", open_response)
    instance = GitHubRemoteAcceptanceVerifier(repository=REPO, token="test-placeholder")
    result = instance.verify_check_run_contexts(
        head_sha=_LIVE_HEAD, required_contexts=("baseline", "state-gate"),
    )
    assert requested == [
        f"{API}/repos/{REPO}/commits/{_LIVE_HEAD}/check-runs?per_page=100&filter=latest&page=1"
    ]
    return result


def test_complete_live_response_with_multiline_names_passes(monkeypatch):
    payload = live_payload()
    multiline = [r for r in payload["check_runs"] if "\n" in r["name"]]
    assert [r["id"] for r in multiline] == [109722833257, 109722745426]
    assert all(r["app"]["id"] == 15368 and r["head_sha"] == _LIVE_HEAD
               and r["conclusion"] == "skipped" for r in multiline)
    result = replay_live(payload, monkeypatch)
    assert result["verified"] is True
    assert result["check_runs"] == payload["check_runs"]
    assert result["context_check_ids"] == {
        "baseline": [109722746738], "state-gate": [109722830313, 109722747194],
    }
    assert result["skipped_check_ids"]["state-gate"] == [109722870711, 109722746111]
    assert result["blocking_check_ids"] == {"baseline": [], "state-gate": []}


@pytest.mark.parametrize("changes,reason", [
    ({"head_sha": "b" * 40}, "check_run_head_mismatch"),
    ({"url": f"{API}/repos/other/repo/check-runs/109722833257"}, "check_run_repository_identity_mismatch"),
    ({"id": True}, "invalid_check_run_id"),
    ({"app": None}, "invalid_check_run_producer"),
    ({"app": {"id": "15368", "slug": "github-actions"}}, "invalid_check_run_producer"),
])
def test_multiline_unrelated_live_record_still_requires_identity(changes, reason, monkeypatch):
    payload = live_payload()
    run = next(r for r in payload["check_runs"] if r["id"] == 109722833257)
    run.update(changes)
    result = replay_live(payload, monkeypatch)
    assert result["verified"] is False
    assert result["reason"] == reason


@pytest.mark.parametrize("changes", [
    {"app": {"id": 999, "slug": "github-actions"}},
    {"app": {"id": 15368, "slug": "foreign"}},
    {"status": "completed", "conclusion": "failure"},
    {"status": "queued", "conclusion": None},
    {"status": "completed", "conclusion": "skipped"},
])
def test_live_required_success_cannot_be_substituted(changes, monkeypatch):
    payload = live_payload()
    run = next(r for r in payload["check_runs"] if r["id"] == 109722746738)
    run.update(changes)
    result = replay_live(payload, monkeypatch)
    assert result["verified"] is False
    assert result["contexts"]["baseline"] is False


@pytest.mark.parametrize("status,conclusion", [
    ("completed", "failure"), ("queued", None), ("unknown", "success"),
])
def test_live_same_name_trusted_conflict_blocks_success(status, conclusion, monkeypatch):
    payload = live_payload()
    run = next(r for r in payload["check_runs"] if r["id"] == 109722833257)
    run.update(name="baseline", status=status, conclusion=conclusion)
    result = replay_live(payload, monkeypatch)
    assert result["verified"] is False
    assert result["context_check_ids"]["baseline"] == [109722746738]
    assert result["blocking_check_ids"]["baseline"] == [109722833257]


@pytest.mark.parametrize("name", ["\nbaseline", "baseline\n", "base\nline",
                                 "\tbaseline", " baseline ", "BASELINE"])
def test_observed_names_are_never_normalized_into_required_matches(name):
    result = check([record(name=name)])
    assert result["verified"] is False
    assert result["context_check_ids"] == {"baseline": []}


@pytest.mark.parametrize("name", ["extra\njob", "\t extra \r\njob ",
                                 "extra\tjob", "额外\n检查"])
def test_unrelated_whitespace_name_does_not_veto_success(name):
    result = check([record(), record(2, name)])
    assert result["verified"] is True
    assert result["context_check_ids"] == {"baseline": [1]}


@pytest.mark.parametrize("name", [None, "", " \t\r\n", "x" * 257,
                                 "extra\x00job", "extra\x1bjob", "extra\x7fjob"])
def test_malformed_unrelated_observed_name_still_fails_closed(name):
    result = check([record(), record(2, name)])
    assert result["verified"] is False
    assert result["reason"] == "invalid_check_run_name"


def test_live_response_truncation_and_duplicate_remain_rejected(monkeypatch):
    payload = live_payload()
    payload["check_runs"].pop()
    assert replay_live(payload, monkeypatch)["reason"] == "check_runs_pagination_incomplete"
    payload = live_payload()
    payload["check_runs"][-1] = copy.deepcopy(payload["check_runs"][0])
    assert replay_live(payload, monkeypatch)["reason"] == "duplicate_check_run_id"
