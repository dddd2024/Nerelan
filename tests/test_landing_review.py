"""Provider-free tests for the Governance v2 lean landing checks."""
from __future__ import annotations

import json
import subprocess
from pathlib import Path

import pytest

from reverse_agent import landing_review
from reverse_agent.landing_review import ReviewEntry, check_paths, evaluate_review, run_hygiene

HEAD = "a" * 40
OTHER = "b" * 40


def entry(body: str, *, association: str = "OWNER", at: str = "2026-10-11T10:00:00Z", author: str = "rev") -> ReviewEntry:
    return ReviewEntry(body=body, author=author, association=association, created_at=at)


def test_accepts_exact_head_verdict() -> None:
    verdict = evaluate_review(HEAD, [entry(f"Looks good.\n\nNerelan-Review: ACCEPT {HEAD}\n")])
    assert verdict.accepted and verdict.reviewer == "rev"


def test_verdict_for_other_commit_is_ignored() -> None:
    verdict = evaluate_review(HEAD, [entry(f"Nerelan-Review: ACCEPT {OTHER}")])
    assert not verdict.accepted and verdict.reason == "no_review_verdict_for_exact_head"


def test_untrusted_author_is_ignored() -> None:
    verdict = evaluate_review(HEAD, [entry(f"Nerelan-Review: ACCEPT {HEAD}", association="NONE")])
    assert not verdict.accepted


def test_latest_verdict_wins() -> None:
    accept = entry(f"Nerelan-Review: ACCEPT {HEAD}", at="2026-10-11T10:00:00Z")
    reject = entry(f"Nerelan-Review: REJECT {HEAD}", at="2026-10-11T11:00:00Z")
    assert not evaluate_review(HEAD, [accept, reject]).accepted
    later_accept = entry(f"Nerelan-Review: ACCEPT {HEAD}", at="2026-10-11T12:00:00Z")
    assert evaluate_review(HEAD, [accept, reject, later_accept]).accepted


def test_marker_must_start_a_line_and_head_is_case_insensitive() -> None:
    assert not evaluate_review(HEAD, [entry(f"quote: Nerelan-Review: ACCEPT {HEAD}")]).accepted
    assert evaluate_review(HEAD, [entry(f"**Nerelan-Review: ACCEPT {HEAD.upper()}**")]).accepted


def test_quoted_fenced_and_suffixed_verdicts_do_not_count() -> None:
    assert not evaluate_review(HEAD, [entry(f"> Nerelan-Review: ACCEPT {HEAD}")]).accepted
    assert not evaluate_review(HEAD, [entry(f"```text\nNerelan-Review: ACCEPT {HEAD}\n```")]).accepted
    assert not evaluate_review(HEAD, [entry(f"Nerelan-Review: ACCEPT {HEAD}-not")]).accepted
    assert evaluate_review(HEAD, [entry(f"Nerelan-Review: ACCEPT {HEAD}\r\n")]).accepted


def test_unclosed_fence_and_indented_code_do_not_count() -> None:
    assert not evaluate_review(HEAD, [entry(f"Findings:\n```\nNerelan-Review: ACCEPT {HEAD}")]).accepted
    assert not evaluate_review(HEAD, [entry(f"Findings:\n\n    Nerelan-Review: ACCEPT {HEAD}")]).accepted
    assert not evaluate_review(HEAD, [entry(f"\tNerelan-Review: ACCEPT {HEAD}")]).accepted
    assert evaluate_review(HEAD, [entry(f"```\ncode\n```\n   Nerelan-Review: ACCEPT {HEAD}")]).accepted
    # A shorter or different closing fence does not end a longer fence.
    assert not evaluate_review(HEAD, [entry(f"````\n```\nNerelan-Review: ACCEPT {HEAD}\n")]).accepted
    assert not evaluate_review(HEAD, [entry(f"~~~\n```\nNerelan-Review: ACCEPT {HEAD}\n")]).accepted


def test_reject_after_closed_fence_still_counts() -> None:
    accept = entry(f"Nerelan-Review: ACCEPT {HEAD}", at="2026-10-11T10:00:00Z")
    reject = entry(f"```\nx\n```\nNerelan-Review: REJECT {HEAD}", at="2026-10-11T11:00:00Z")
    assert evaluate_review(HEAD, [accept, reject]).reason == "latest_review_verdict_rejects_head"


def _verdict_fixture(monkeypatch: pytest.MonkeyPatch, pr: dict) -> None:
    monkeypatch.setattr(landing_review, "_api_get", lambda *_a, **_k: pr)
    monkeypatch.setattr(landing_review, "fetch_review_entries",
                        lambda *_a, **_k: [entry(f"Nerelan-Review: ACCEPT {HEAD}")])


def test_verdict_requires_live_head_ready_and_main(monkeypatch: pytest.MonkeyPatch) -> None:
    ready = {"head": {"sha": HEAD}, "draft": False, "base": {"ref": "main"}}
    _verdict_fixture(monkeypatch, ready)
    assert landing_review.run_verdict("o/r", 1, HEAD, "t")["passed"] is True
    assert landing_review.run_verdict("o/r", 1, OTHER, "t")["reason"] == "live_head_differs_from_expected"
    _verdict_fixture(monkeypatch, {**ready, "draft": True})
    assert landing_review.run_verdict("o/r", 1, HEAD, "t")["reason"] == "draft_pull_request"
    _verdict_fixture(monkeypatch, {**ready, "base": {"ref": "dev"}})
    assert landing_review.run_verdict("o/r", 1, HEAD, "t")["reason"] == "base_is_not_main"


def test_verdict_cli_without_token_fails_closed(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("GITHUB_TOKEN", raising=False)
    monkeypatch.delenv("GH_TOKEN", raising=False)
    assert landing_review.main(["verdict", "--repository", "o/r", "--pr", "1", "--head", HEAD]) == 1


def test_checker_module_is_present_for_base_checkout() -> None:
    # landing-state-gate falls back to the candidate's checker when the base
    # lacks this file, so it must never be deleted from main.
    assert (Path(__file__).resolve().parents[1] / "reverse_agent" / "landing_review.py").is_file()


def test_entry_without_timestamp_is_ignored() -> None:
    reject = entry(f"Nerelan-Review: REJECT {HEAD}", at="2026-10-11T11:00:00Z")
    undated_accept = entry(f"Nerelan-Review: ACCEPT {HEAD}", at="")
    assert evaluate_review(HEAD, [reject, undated_accept]).reason == "latest_review_verdict_rejects_head"


def test_fetch_skips_dismissed_and_pending_reviews(monkeypatch: pytest.MonkeyPatch) -> None:
    def fake_get_all(url: str, _token: str):
        if url.endswith("/comments"):
            return []
        body = f"Nerelan-Review: ACCEPT {HEAD}"
        return [
            {"body": body, "user": {"login": "a"}, "author_association": "OWNER", "state": "DISMISSED", "submitted_at": "2026-10-11T10:00:00Z"},
            {"body": body, "user": {"login": "b"}, "author_association": "OWNER", "state": "PENDING", "submitted_at": None},
        ]

    monkeypatch.setattr(landing_review, "_api_get_all", fake_get_all)
    assert landing_review.fetch_review_entries("o/r", 1, "t") == []


def test_invalid_head_fails_closed() -> None:
    assert evaluate_review("not-a-sha", [entry(f"Nerelan-Review: ACCEPT {HEAD}")]).reason == "invalid_head_sha"


@pytest.mark.parametrize("path", [
    ".platform_v1_runtime/tasks.sqlite3",
    "frontend/node_modules/x/index.js",
    "reverse_agent/__pycache__/a.cpython-313.pyc",
    "data/store.sqlite3-wal",
    "frontend/vite.config.ts.timestamp-1790668472090-88843cecd186.mjs",
])
def test_runtime_paths_are_forbidden(path: str) -> None:
    assert check_paths([path]) == [path]


def test_ordinary_paths_are_allowed() -> None:
    assert check_paths(["reverse_agent/landing_review.py", "docs/a.md", "frontend/src/app.tsx"]) == []


def test_run_review_rejects_draft_and_non_main_without_network(monkeypatch: pytest.MonkeyPatch) -> None:
    def no_network(*_args, **_kwargs):
        raise AssertionError("network must not be used")

    monkeypatch.setattr(landing_review, "fetch_review_entries", no_network)
    draft = {"pull_request": {"number": 1, "draft": True, "head": {"sha": HEAD}, "base": {"ref": "main"}}}
    assert landing_review.run_review(draft, "o/r", "t")["reason"] == "draft_pull_request"
    other = {"pull_request": {"number": 1, "draft": False, "head": {"sha": HEAD}, "base": {"ref": "dev"}}}
    assert landing_review.run_review(other, "o/r", "t")["reason"] == "base_is_not_main"


def test_run_review_uses_fetched_entries(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(landing_review, "fetch_review_entries",
                        lambda *_a, **_k: [entry(f"Nerelan-Review: ACCEPT {HEAD}")])
    ready = {"pull_request": {"number": 7, "draft": False, "head": {"sha": HEAD}, "base": {"ref": "main"}}}
    assert landing_review.run_review(ready, "o/r", "t")["passed"] is True


def _git(cwd: Path, *args: str) -> str:
    return subprocess.run(["git", *args], cwd=cwd, check=True, capture_output=True, text=True).stdout.strip()


@pytest.fixture()
def repo(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    _git(tmp_path, "init", "-q", "-b", "main")
    _git(tmp_path, "config", "user.email", "t@example.invalid")
    _git(tmp_path, "config", "user.name", "t")
    _git(tmp_path, "config", "core.autocrlf", "false")
    (tmp_path / "a.txt").write_bytes(b"one\n")
    _git(tmp_path, "add", ".")
    _git(tmp_path, "commit", "-q", "-m", "base")
    monkeypatch.chdir(tmp_path)
    return tmp_path


def test_hygiene_passes_clean_change(repo: Path) -> None:
    base = _git(repo, "rev-parse", "HEAD")
    (repo / "b.txt").write_bytes(b"two\n")
    _git(repo, "add", ".")
    _git(repo, "commit", "-q", "-m", "change")
    result = run_hygiene(base, _git(repo, "rev-parse", "HEAD"))
    assert result["passed"], result["problems"]


def test_hygiene_blocks_whitespace_and_runtime_files(repo: Path) -> None:
    base = _git(repo, "rev-parse", "HEAD")
    (repo / "b.txt").write_bytes(b"trailing   \n")
    (repo / ".platform_v1_runtime").mkdir()
    (repo / ".platform_v1_runtime" / "tasks.sqlite3").write_bytes(b"x")
    _git(repo, "add", "-f", ".")
    _git(repo, "commit", "-q", "-m", "bad")
    result = run_hygiene(base, _git(repo, "rev-parse", "HEAD"))
    assert not result["passed"]
    joined = json.dumps(result["problems"])
    assert "whitespace_errors" in joined and "forbidden_runtime_paths" in joined


def test_cli_returns_nonzero_without_token(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("GITHUB_TOKEN", raising=False)
    monkeypatch.delenv("GH_TOKEN", raising=False)
    event = tmp_path / "event.json"
    event.write_text(json.dumps({"pull_request": {"number": 1}}), encoding="utf-8")
    assert landing_review.main(["review", "--event-path", str(event), "--repository", "o/r"]) == 1
