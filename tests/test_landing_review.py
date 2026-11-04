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


@pytest.mark.parametrize("reject_body", [
    # Line starting with an inline code span: not a fence on GitHub.
    f"```x``` is wrong here.\n\nNerelan-Review: REJECT {HEAD}",
    # Bullet item opening a fenced block on its marker line.
    f"- Finding:\n  ```python\n  x = 1\n  ```\n\nNerelan-Review: REJECT {HEAD}",
    # Ordered item opening a fenced block on its marker line.
    f"1. ```\n   code\n   ```\n\nNerelan-Review: REJECT {HEAD}",
    # Even a genuinely unclosed fence cannot hide a REJECT.
    f"```\nunclosed\nNerelan-Review: REJECT {HEAD}",
])
def test_no_markdown_shape_can_hide_a_later_reject(reject_body: str) -> None:
    accept = entry(f"Nerelan-Review: ACCEPT {HEAD}", at="2026-10-11T10:00:00Z")
    reject = entry(reject_body, at="2026-10-11T11:00:00Z")
    assert evaluate_review(HEAD, [accept, reject]).reason == "latest_review_verdict_rejects_head"


def test_entry_with_both_verdicts_counts_as_reject() -> None:
    body = f"Nerelan-Review: ACCEPT {HEAD}\nNerelan-Review: REJECT {HEAD}"
    assert evaluate_review(HEAD, [entry(body)]).reason == "latest_review_verdict_rejects_head"


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


def commit_file(repo: Path, path: str, data: bytes = b"change\n") -> str:
    target = repo / path
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_bytes(data)
    _git(repo, "add", "--", path)
    _git(repo, "commit", "-q", "-m", "change")
    return _git(repo, "rev-parse", "HEAD")


def carry_chain(repo: Path, count: int = 1, path: str = "feature.bin") -> tuple[str, list[str]]:
    _git(repo, "checkout", "-q", "-b", "feature")
    accepted = commit_file(repo, path, b"feature\x00\xff\n")
    merges = []
    for index in range(count):
        _git(repo, "checkout", "-q", "main")
        commit_file(repo, f"main-{index}.txt")
        _git(repo, "update-ref", "refs/remotes/origin/main", "HEAD")
        _git(repo, "checkout", "-q", "feature")
        _git(repo, "merge", "--no-ff", "-q", "main", "-m", "update")
        merges.append(_git(repo, "rev-parse", "HEAD"))
    return accepted, merges


def carry(head: str, accepted: str, *extra: ReviewEntry):
    return landing_review.evaluate_review_with_carry_over(
        head, [entry(f"Nerelan-Review: ACCEPT {accepted}"), *extra])


@pytest.mark.parametrize("count", [1, 2, 20, 21])
def test_bounded_update_merges(repo: Path, count: int) -> None:
    accepted, merges = carry_chain(repo, count)
    result = carry(merges[-1], accepted)
    assert result.accepted == (count <= 20)
    if result.accepted:
        assert result.reason == "accepted_carried_over"
        assert result.to_dict()["accepted_head"] == accepted
        assert result.to_dict()["merge_commits"] == merges


@pytest.mark.parametrize("path", [
    "AGENTS.md", ".github/workflows/check.yml", ".github/workflows/nested/x.yml",
    "reverse_agent/landing_review.py",
])
def test_carry_excludes_sensitive_paths(repo: Path, path: str) -> None:
    accepted, merges = carry_chain(repo, path=path)
    assert not carry(merges[-1], accepted).accepted


@pytest.mark.parametrize("path", [
    "docs/agents/nested/a.md", "requirements.txt", "requirements-dev.txt",
    "pyproject.toml", "frontend/package.json", "frontend/package-lock.json",
])
def test_other_r2_paths_carry_over_pure_merge_main(repo: Path, path: str) -> None:
    # Owner decision 2026-10-21 (#1310 C): all other carry-over conditions still apply.
    accepted, merges = carry_chain(repo, path=path)
    result = carry(merges[-1], accepted)
    assert result.accepted and result.reason == "accepted_carried_over"


def test_normal_commit_cannot_carry(repo: Path) -> None:
    accepted, _ = carry_chain(repo)
    head = commit_file(repo, "extra")
    assert not carry(head, accepted).accepted


def test_second_parent_must_be_on_main(repo: Path) -> None:
    accepted, merges = carry_chain(repo)
    _git(repo, "update-ref", "refs/remotes/origin/main", accepted + "^")
    assert not carry(merges[-1], accepted).accepted


@pytest.mark.parametrize("which", [0, 1])
def test_newer_reject_blocks_chain(repo: Path, which: int) -> None:
    accepted, merges = carry_chain(repo, 2)
    reject = entry(f"Nerelan-Review: REJECT {merges[which]}", at="2026-10-12T00:00:00Z")
    assert not carry(merges[-1], accepted, reject).accepted


def test_accept_and_reject_in_same_entry_blocks_chain(repo: Path) -> None:
    accepted, merges = carry_chain(repo, 2)
    both = entry(f"Nerelan-Review: ACCEPT {accepted}\nNerelan-Review: REJECT {merges[0]}")
    assert not landing_review.evaluate_review_with_carry_over(merges[-1], [both]).accepted


@pytest.mark.parametrize("reject_first", [True, False])
def test_equal_timestamp_reject_blocks_chain(repo: Path, reject_first: bool) -> None:
    accepted, merges = carry_chain(repo, 2)
    accept = entry(f"Nerelan-Review: ACCEPT {accepted}")
    reject = entry(f"Nerelan-Review: REJECT {merges[0]}")
    entries = [reject, accept] if reject_first else [accept, reject]
    assert not landing_review.evaluate_review_with_carry_over(merges[-1], entries).accepted


def test_latest_verdict_at_accepted_head(repo: Path) -> None:
    accepted, merges = carry_chain(repo)
    reject = entry(f"Nerelan-Review: REJECT {accepted}", at="2026-10-12T00:00:00Z")
    accept = entry(f"Nerelan-Review: ACCEPT {accepted}", at="2026-10-13T00:00:00Z")
    assert not carry(merges[-1], accepted, reject).accepted
    assert carry(merges[-1], accepted, reject, accept).accepted


@pytest.mark.parametrize("decision", ["ACCEPT", "REJECT"])
def test_exact_head_never_calls_git(monkeypatch: pytest.MonkeyPatch, decision: str) -> None:
    def forbidden(*args):
        raise AssertionError("git called for exact verdict")
    monkeypatch.setattr(landing_review, "_carry_git", forbidden)
    entries = [entry(f"Nerelan-Review: {decision} {HEAD}")]
    assert landing_review.evaluate_review_with_carry_over(HEAD, entries).to_dict() == evaluate_review(HEAD, entries).to_dict()
    monkeypatch.setattr(landing_review, "fetch_review_entries", lambda *a: entries)
    pr = {"number": 1, "head": {"sha": HEAD}, "base": {"ref": "main"}, "draft": False}
    monkeypatch.setattr(landing_review, "_api_get", lambda *a: pr)
    assert landing_review.run_review({"pull_request": pr}, "o/r", "t")["passed"] == (decision == "ACCEPT")
    assert landing_review.run_verdict("o/r", 1, HEAD, "t")["passed"] == (decision == "ACCEPT")


def test_both_entrypoints_carry_and_keep_guards(repo: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    accepted, merges = carry_chain(repo, 2)
    head = merges[-1]
    entries = [entry(f"Nerelan-Review: ACCEPT {accepted}")]
    monkeypatch.setattr(landing_review, "fetch_review_entries", lambda *a: entries)
    pr = {"number": 1, "head": {"sha": head}, "base": {"ref": "main"}, "draft": False}
    monkeypatch.setattr(landing_review, "_api_get", lambda *a: pr)
    for result in (landing_review.run_review({"pull_request": pr}, "o/r", "t"),
                   landing_review.run_verdict("o/r", 1, head, "t")):
        assert result["passed"] and result["accepted_head"] == accepted
        assert result["merge_commits"] == merges
    assert landing_review.run_verdict("o/r", 1, accepted, "t")["reason"] == "live_head_differs_from_expected"
    for key, value, reason in [("draft", True, "draft_pull_request"),
                               ("base", {"ref": "dev"}, "base_is_not_main")]:
        old = pr[key]
        pr[key] = value
        assert landing_review.run_review({"pull_request": pr}, "o/r", "t")["reason"] == reason
        assert landing_review.run_verdict("o/r", 1, head, "t")["reason"] == reason
        pr[key] = old


@pytest.mark.parametrize("operation", ["rev-parse", "merge-base", "diff", "show", "merge-tree"])
def test_git_errors_fail_closed(repo: Path, monkeypatch: pytest.MonkeyPatch, operation: str) -> None:
    accepted, merges = carry_chain(repo)
    original = landing_review._carry_git
    def fail(*args):
        if args[0] == operation:
            raise RuntimeError("unsupported or missing object")
        return original(*args)
    monkeypatch.setattr(landing_review, "_carry_git", fail)
    assert not carry(merges[-1], accepted).accepted


def test_missing_main_and_missing_object(repo: Path) -> None:
    accepted, merges = carry_chain(repo)
    assert not carry(HEAD, accepted).accepted
    _git(repo, "update-ref", "-d", "refs/remotes/origin/main")
    assert not carry(merges[-1], accepted).accepted


def test_merge_with_extra_resolution_edit(repo: Path) -> None:
    accepted, merges = carry_chain(repo)
    # Manufacture a two-parent commit with the same parents but an edited tree.
    commit_file(repo, "extra")
    tree = _git(repo, "rev-parse", "HEAD^{tree}")
    parents = _git(repo, "show", "-s", "--format=%P", merges[-1]).split()
    bad = _git(repo, "commit-tree", tree, "-p", parents[0], "-p", parents[1], "-m", "edited merge")
    assert not carry(bad, accepted).accepted


def test_conflicted_merge_is_not_carried(repo: Path) -> None:
    _git(repo, "checkout", "-q", "-b", "feature")
    accepted = commit_file(repo, "a.txt", b"feature\n")
    _git(repo, "checkout", "-q", "main")
    commit_file(repo, "a.txt", b"main\n")
    _git(repo, "update-ref", "refs/remotes/origin/main", "HEAD")
    _git(repo, "checkout", "-q", "feature")
    result = subprocess.run(["git", "merge", "main", "-m", "conflict"], cwd=repo, capture_output=True)
    assert result.returncode != 0
    head = commit_file(repo, "a.txt", b"resolved\n")
    assert not carry(head, accepted).accepted


def test_changed_pr_diff_blocks_even_clean_merge(repo: Path) -> None:
    # Main independently takes part of the reviewed change: merge is clean,
    # but the PR diff relative to current main no longer equals the reviewed diff.
    _git(repo, "checkout", "-q", "-b", "feature")
    commit_file(repo, "shared.txt", b"shared\n")
    accepted = commit_file(repo, "feature.txt")
    _git(repo, "checkout", "-q", "main")
    commit_file(repo, "main-only.txt")
    commit_file(repo, "shared.txt", b"shared\n")
    _git(repo, "update-ref", "refs/remotes/origin/main", "HEAD")
    _git(repo, "checkout", "-q", "feature")
    _git(repo, "merge", "-q", "--no-ff", "main", "-m", "update")
    assert not carry(_git(repo, "rev-parse", "HEAD"), accepted).accepted


@pytest.mark.parametrize("kind", ["untrusted", "undated", "fenced", "both"])
def test_carry_preserves_entry_rules(repo: Path, kind: str) -> None:
    accepted, merges = carry_chain(repo)
    body = f"Nerelan-Review: ACCEPT {accepted}"
    candidate = entry(body)
    if kind == "untrusted":
        candidate = entry(body, association="NONE")
    elif kind == "undated":
        candidate = entry(body, at="")
    elif kind == "fenced":
        candidate = entry(f"```\n{body}\n```")
    else:
        candidate = entry(body + f"\nNerelan-Review: REJECT {accepted}")
    assert not landing_review.evaluate_review_with_carry_over(merges[-1], [candidate]).accepted


# --- Explicit local gh opt-in (--auth-source gh). Offline: subprocess.run is faked. ---

GH_REPO = "o/r"
GH_PR = "repos/o/r/pulls/1"
GH_COMMENTS = "repos/o/r/issues/1/comments"
GH_REVIEWS = "repos/o/r/pulls/1/reviews"
ACCEPT_LINE = f"Nerelan-Review: ACCEPT {HEAD}"


def gh_pull(head: str = HEAD, *, draft: bool = False, base: str = "main") -> dict:
    return {"head": {"sha": head}, "base": {"ref": base}, "draft": draft}


def gh_comment(body: str, *, association: str = "OWNER", at: str | None = "2026-10-11T10:00:00Z") -> dict:
    return {"body": body, "user": {"login": "rev"}, "author_association": association, "created_at": at}


def gh_review(body: str, *, state: str = "APPROVED", association: str = "OWNER",
              at: str | None = "2026-10-11T10:00:00Z") -> dict:
    return {"body": body, "user": {"login": "rev"}, "author_association": association,
            "state": state, "submitted_at": at}


def gh_routes(*, comments=(), reviews=(), pull=None) -> dict:
    return {GH_PR: pull or gh_pull(), GH_COMMENTS: [list(comments)], GH_REVIEWS: [list(reviews)]}


class FakeGh:
    """Stands in for ``subprocess.run`` for gh and serves synthetic REST data keyed by endpoint.

    A route is a dict (single object), a list of pages (served by the ``page`` field, empty
    past the end), or bytes (raw stdout). ``failure`` is raised or returned on every call.
    """

    def __init__(self, routes: dict, failure=None) -> None:
        self.routes = routes
        self.failure = failure
        self.calls: list[tuple[list[str], dict]] = []

    def __call__(self, argv, **kwargs):
        if argv[0] != "gh":
            # Carry-over probes git through the same seam; this offline suite keeps it out and
            # relies on its existing fail-closed handling of git errors.
            raise RuntimeError("offline gh test: git not available")
        self.calls.append((list(argv), kwargs))
        if isinstance(self.failure, BaseException):
            raise self.failure
        if self.failure is not None:
            return self.failure
        route = self.routes[argv[6]]
        if isinstance(route, bytes):
            return subprocess.CompletedProcess(argv, 0, stdout=route, stderr=b"")
        if isinstance(route, dict):
            payload = route
        else:
            fields = dict(part.split("=", 1) for part in argv[8::2])
            page = int(fields.get("page", "1"))
            payload = route[page - 1] if page <= len(route) else []
        return subprocess.CompletedProcess(argv, 0, stdout=json.dumps(payload).encode("utf-8"), stderr=b"")


def use_gh(monkeypatch: pytest.MonkeyPatch, routes: dict, failure=None) -> FakeGh:
    fake = FakeGh(routes, failure)
    monkeypatch.setattr(subprocess, "run", fake)
    return fake


def gh_verdict(head: str = HEAD) -> dict:
    return landing_review.run_verdict(GH_REPO, 1, head, landing_review.GhCli())


def test_gh_backend_accepts_exact_head_through_shared_evaluator(monkeypatch: pytest.MonkeyPatch) -> None:
    fake = use_gh(monkeypatch, gh_routes(comments=[gh_comment(ACCEPT_LINE)]))
    result = gh_verdict()
    assert result["passed"] is True and result["reviewer"] == "rev"
    assert {argv[6] for argv, _ in fake.calls} == {GH_PR, GH_COMMENTS, GH_REVIEWS}


def test_gh_pages_are_all_read_so_a_later_page_reject_blocks(monkeypatch: pytest.MonkeyPatch) -> None:
    routes = gh_routes()
    routes[GH_COMMENTS] = [[gh_comment(ACCEPT_LINE, at="2026-10-11T10:00:00Z")],
                           [gh_comment(f"Nerelan-Review: REJECT {HEAD}", at="2026-10-11T12:00:00Z")]]
    fake = use_gh(monkeypatch, routes)
    result = gh_verdict()
    assert result["passed"] is False and result["reason"] == "latest_review_verdict_rejects_head"
    # Page 3 is requested and is empty, which is what ends the walk (no silent truncation).
    assert any("page=3" in argv for argv, _ in fake.calls)


@pytest.mark.parametrize(("pull", "expected", "reason"), [
    (gh_pull(), OTHER, "live_head_differs_from_expected"),
    (gh_pull(draft=True), HEAD, "draft_pull_request"),
    (gh_pull(base="dev"), HEAD, "base_is_not_main"),
])
def test_gh_backend_keeps_live_head_ready_and_main_guards(
        monkeypatch: pytest.MonkeyPatch, pull: dict, expected: str, reason: str) -> None:
    fake = use_gh(monkeypatch, gh_routes(pull=pull, comments=[gh_comment(ACCEPT_LINE)]))
    result = landing_review.run_verdict(GH_REPO, 1, expected, landing_review.GhCli())
    assert result["passed"] is False and result["reason"] == reason
    assert [argv[6] for argv, _ in fake.calls] == [GH_PR]


def test_gh_backend_ignores_quoted_fenced_untrusted_pending_and_dismissed(monkeypatch: pytest.MonkeyPatch) -> None:
    comments = [gh_comment(f"> {ACCEPT_LINE}"), gh_comment(ACCEPT_LINE, association="NONE"),
                gh_comment(f"```\n{ACCEPT_LINE}\n```")]
    reviews = [gh_review(ACCEPT_LINE, state="PENDING", at=None), gh_review(ACCEPT_LINE, state="DISMISSED")]
    use_gh(monkeypatch, gh_routes(comments=comments, reviews=reviews))
    result = gh_verdict()
    assert result["passed"] is False and result["reason"] == "no_review_verdict_for_exact_head"


@pytest.mark.parametrize(("failure", "message"), [
    (subprocess.CompletedProcess(["gh"], 1, stdout=b"raw SECRET-OUT", stderr=b"SECRET-ERR token"),
     "gh api failed with exit status 1"),
    (subprocess.TimeoutExpired(["gh"], 60), "gh api timed out"),
    (FileNotFoundError("gh"), "gh executable is unavailable"),
])
def test_gh_process_failures_fail_closed_without_raw_output(
        monkeypatch: pytest.MonkeyPatch, failure, message: str) -> None:
    use_gh(monkeypatch, gh_routes(comments=[gh_comment(ACCEPT_LINE)]), failure=failure)
    with pytest.raises(RuntimeError) as info:
        gh_verdict()
    assert str(info.value) == message


_BAD_PULL = gh_pull()
del _BAD_PULL["head"]
_BAD_COMMENT = gh_comment(ACCEPT_LINE)
del _BAD_COMMENT["author_association"]


@pytest.mark.parametrize(("endpoint", "route"), [
    (GH_PR, b"not json"),
    (GH_PR, b"[]"),
    (GH_PR, _BAD_PULL),
    (GH_COMMENTS, b'[{"body": "Nerelan-Review: ACCEPT'),
    (GH_COMMENTS, b'{"message": "not a list"}'),
    (GH_COMMENTS, [[1]]),
    (GH_COMMENTS, [[_BAD_COMMENT]]),
    (GH_REVIEWS, [[{**gh_review(ACCEPT_LINE), "state": 3}]]),
])
def test_gh_malformed_or_partial_payloads_fail_closed(
        monkeypatch: pytest.MonkeyPatch, endpoint: str, route) -> None:
    routes = gh_routes(comments=[gh_comment(ACCEPT_LINE)])
    routes[endpoint] = route
    use_gh(monkeypatch, routes)
    with pytest.raises(ValueError) as info:
        gh_verdict()
    assert "Nerelan" not in str(info.value) and "not a list" not in str(info.value)


def test_gh_pagination_limit_fails_closed(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(landing_review, "GH_MAX_PAGES", 2)
    routes = gh_routes()
    routes[GH_COMMENTS] = [[gh_comment(ACCEPT_LINE)], [gh_comment(ACCEPT_LINE)]]
    use_gh(monkeypatch, routes)
    with pytest.raises(RuntimeError, match="pagination limit"):
        gh_verdict()


def test_gh_requests_are_fixed_get_without_shell_env_or_token(monkeypatch: pytest.MonkeyPatch) -> None:
    fake = use_gh(monkeypatch, gh_routes(comments=[gh_comment(ACCEPT_LINE)]))
    gh_verdict()
    assert len(fake.calls) == 4  # pull request, two comment pages (second empty), reviews page
    for argv, kwargs in fake.calls:
        assert argv[:6] == ["gh", "api", "--hostname", "github.com", "--method", "GET"]
        assert "auth" not in argv and "token" not in argv
        assert all(isinstance(part, str) for part in argv)
        assert kwargs["shell"] is False
        assert kwargs["timeout"] == landing_review.GH_TIMEOUT_SECONDS
        assert "env" not in kwargs


@pytest.mark.parametrize("repository", [
    "bad", "o/r;rm -rf", "../r", "o/..", "o/r/extra", "-o/r", "o/r --hostname evil.example",
])
def test_gh_rejects_unsafe_repository_before_spawning(monkeypatch: pytest.MonkeyPatch, repository: str) -> None:
    fake = use_gh(monkeypatch, {})
    with pytest.raises(ValueError):
        landing_review.run_verdict(repository, 1, HEAD, landing_review.GhCli())
    assert fake.calls == []


def test_gh_rejects_non_github_api_urls(monkeypatch: pytest.MonkeyPatch) -> None:
    fake = use_gh(monkeypatch, {})
    for api_url in ["https://ghe.example/api/v3", "https://api.github.com.evil.example", "https://api.github.com/?x"]:
        with pytest.raises(ValueError):
            landing_review.run_verdict(GH_REPO, 1, HEAD, landing_review.GhCli(), api_url=api_url)
    assert fake.calls == []


class SpyEnv(dict):
    """Records which environment names are looked up, so the test can prove none were read."""

    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self.reads: list[str] = []

    def __getitem__(self, key):
        self.reads.append(key)
        return super().__getitem__(key)

    def get(self, key, default=None):
        self.reads.append(key)
        return super().get(key, default)

    def __contains__(self, key):
        self.reads.append(key)
        return super().__contains__(key)


def test_explicit_gh_cli_path_reads_no_token_or_host_variables(
        monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture) -> None:
    spy = SpyEnv({"GITHUB_TOKEN": "sentinel-token-value", "GH_TOKEN": "sentinel-token-value",
                  "GH_HOST": "evil.example"})
    monkeypatch.setattr(landing_review.os, "environ", spy)
    fake = use_gh(monkeypatch, gh_routes(comments=[gh_comment(ACCEPT_LINE)]))
    code = landing_review.main(["verdict", "--repository", GH_REPO, "--pr", "1", "--head", HEAD,
                                "--auth-source", "gh"])
    assert code == 0
    assert not {"GITHUB_TOKEN", "GH_TOKEN", "GH_HOST"} & set(spy.reads)
    assert "sentinel-token-value" not in capsys.readouterr().out
    assert all("sentinel-token-value" not in str(argv) for argv, _ in fake.calls)


def test_cli_gh_opt_in_prints_verdict_and_exit_code(monkeypatch: pytest.MonkeyPatch,
                                                    capsys: pytest.CaptureFixture) -> None:
    monkeypatch.delenv("GITHUB_TOKEN", raising=False)
    monkeypatch.delenv("GH_TOKEN", raising=False)
    use_gh(monkeypatch, gh_routes(comments=[gh_comment(ACCEPT_LINE)]))
    code = landing_review.main(["verdict", "--repository", GH_REPO, "--pr", "1", "--head", HEAD,
                                "--auth-source", "gh"])
    printed = json.loads(capsys.readouterr().out)
    assert code == 0 and printed["passed"] is True and printed["reason"] == "accepted"


def test_cli_gh_failure_prints_sanitized_reason(monkeypatch: pytest.MonkeyPatch,
                                                capsys: pytest.CaptureFixture) -> None:
    failure = subprocess.CompletedProcess(["gh"], 1, stdout=b"SECRET-OUT", stderr=b"SECRET-ERR")
    use_gh(monkeypatch, {}, failure=failure)
    code = landing_review.main(["verdict", "--repository", GH_REPO, "--pr", "1", "--head", HEAD,
                                "--auth-source", "gh"])
    out = capsys.readouterr().out
    assert code == 1 and "gh api failed with exit status 1" in out
    assert "SECRET" not in out


def test_default_token_and_ci_review_never_invoke_gh(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    monkeypatch.delenv("GITHUB_TOKEN", raising=False)
    monkeypatch.delenv("GH_TOKEN", raising=False)
    fake = use_gh(monkeypatch, {})
    verdict_args = ["verdict", "--repository", GH_REPO, "--pr", "1", "--head", HEAD]
    assert landing_review.main(verdict_args) == 1
    assert landing_review.main([*verdict_args, "--auth-source", "token"]) == 1
    event = tmp_path / "event.json"
    event.write_text(json.dumps({"pull_request": {"number": 1}}), encoding="utf-8")
    assert landing_review.main(["review", "--event-path", str(event), "--repository", GH_REPO]) == 1
    assert fake.calls == []


def test_review_command_does_not_accept_gh_auth_source(tmp_path: Path) -> None:
    event = tmp_path / "event.json"
    event.write_text(json.dumps({"pull_request": {"number": 1}}), encoding="utf-8")
    with pytest.raises(SystemExit) as info:
        landing_review.main(["review", "--event-path", str(event), "--repository", GH_REPO,
                             "--auth-source", "gh"])
    assert info.value.code == 2
