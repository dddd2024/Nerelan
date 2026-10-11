"""Lean landing checks for Governance v2.

Two deterministic commands back the repository's required status checks:

``hygiene``
    Run by ``state-gate`` on every pull request. Checks the exact PR range for
    whitespace errors and for committed runtime/scratch artifacts.

``review``
    Run by ``landing-state-gate`` when a pull request is Ready. Requires an
    independent review verdict bound to the exact head commit::

        Nerelan-Review: ACCEPT <40-hex head sha>

    posted as a PR comment or review by an OWNER/MEMBER/COLLABORATOR. The most
    recent verdict for that head wins, so a later ``REJECT`` withdraws an
    earlier ``ACCEPT`` the next time the gate runs. A verdict for any other
    commit is ignored, which makes a new push invalidate the previous
    acceptance. The gate re-runs only on pull_request events, so whoever merges
    re-checks the verdict immediately before merging (``verdict`` command).

The verdict logic is pure (:func:`evaluate_review`) so it is testable without
network access; the CLI only gathers GitHub REST data with the workflow token.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import sys
import urllib.error
import urllib.request
from dataclasses import dataclass
from pathlib import PurePosixPath
from typing import Any, Iterable, Mapping, Sequence

# A verdict is the author's own line, as GitHub renders it: at most three
# spaces of indent (four is a code block), optional emphasis, never a quote
# ("> ..."), and nothing but closing emphasis after the sha.
VERDICT_RE = re.compile(
    r"^ {0,3}[*_`]*Nerelan-Review:[ \t]*(ACCEPT|REJECT)[ \t]+([0-9a-fA-F]{40})[ \t*_`]*\r?$",
    re.MULTILINE,
)
FENCE_OPEN_RE = re.compile(r"^ {0,3}(`{3,}|~{3,})")
IGNORED_REVIEW_STATES = frozenset({"PENDING", "DISMISSED"})
TRUSTED_ASSOCIATIONS = frozenset({"OWNER", "MEMBER", "COLLABORATOR"})

# Runtime state, caches and local scratch that must never be committed.
FORBIDDEN_PATH_PARTS = frozenset({
    ".platform_v1_runtime",
    "node_modules",
    "__pycache__",
    ".pytest_cache",
    ".vite-native-owned",
})
FORBIDDEN_SUFFIXES = (".sqlite3", ".sqlite3-wal", ".sqlite3-shm", ".pyc")
VITE_TIMESTAMP_RE = re.compile(r"\.timestamp-\d+-[0-9a-f]+\.mjs$")
MAX_ADDED_FILE_BYTES = 5 * 1024 * 1024


@dataclass(frozen=True)
class ReviewEntry:
    """One comment or review body with its author trust and timestamp."""

    body: str
    author: str
    association: str
    created_at: str


@dataclass(frozen=True)
class Verdict:
    accepted: bool
    reason: str
    reviewer: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {"accepted": self.accepted, "reason": self.reason, "reviewer": self.reviewer}


def strip_code_fences(body: str) -> str:
    """Drop fenced code blocks; an unclosed fence runs to the end, as GitHub renders it."""
    kept: list[str] = []
    fence: str | None = None
    for line in body.splitlines():
        match = FENCE_OPEN_RE.match(line)
        if fence is None:
            if match:
                fence = match.group(1)
            else:
                kept.append(line)
        elif match and match.group(1)[0] == fence[0] and len(match.group(1)) >= len(fence) \
                and not line.strip().lstrip(fence[0]):
            fence = None
    return "\n".join(kept)


def evaluate_review(head_sha: str, entries: Iterable[ReviewEntry]) -> Verdict:
    """Return the landing verdict for ``head_sha`` from trusted review entries."""
    head = head_sha.lower()
    if not re.fullmatch(r"[0-9a-f]{40}", head):
        return Verdict(False, "invalid_head_sha")
    latest: tuple[str, str, str] | None = None  # (created_at, decision, author)
    for entry in entries:
        if entry.association not in TRUSTED_ASSOCIATIONS or not entry.created_at:
            continue
        for decision, sha in VERDICT_RE.findall(strip_code_fences(entry.body or "")):
            if sha.lower() != head:
                continue
            if latest is None or entry.created_at >= latest[0]:
                latest = (entry.created_at, decision, entry.author)
    if latest is None:
        return Verdict(False, "no_review_verdict_for_exact_head")
    if latest[1] != "ACCEPT":
        return Verdict(False, "latest_review_verdict_rejects_head", latest[2])
    return Verdict(True, "accepted", latest[2])


def check_paths(paths: Sequence[str]) -> list[str]:
    """Return the committed paths that look like runtime state or scratch."""
    bad = []
    for path in paths:
        parts = PurePosixPath(path).parts
        if (FORBIDDEN_PATH_PARTS.intersection(parts) or path.endswith(FORBIDDEN_SUFFIXES)
                or VITE_TIMESTAMP_RE.search(path)):
            bad.append(path)
    return bad


def _git(*args: str) -> str:
    result = subprocess.run(["git", *args], check=False, capture_output=True, text=True,
                            encoding="utf-8", errors="replace")
    if result.returncode != 0:
        raise RuntimeError(f"git {args[0]} failed: {result.stderr.strip()[:400]}")
    return result.stdout


def run_hygiene(base: str, head: str) -> dict[str, Any]:
    merge_base = _git("merge-base", base, head).strip()
    problems: list[str] = []
    check = subprocess.run(["git", "diff", "--check", f"{merge_base}..{head}"],
                           capture_output=True, text=True, encoding="utf-8", errors="replace")
    if check.returncode != 0:
        problems.append("whitespace_errors:\n" + check.stdout.strip()[:4000])
    added = [p for p in _git("diff", "--name-only", "--diff-filter=AMR", f"{merge_base}..{head}").splitlines() if p]
    forbidden = check_paths(added)
    if forbidden:
        problems.append("forbidden_runtime_paths: " + ", ".join(forbidden[:50]))
    oversized = []
    for path in added:
        size = _git("cat-file", "-s", f"{head}:{path}").strip()
        if size.isdigit() and int(size) > MAX_ADDED_FILE_BYTES:
            oversized.append(f"{path} ({size} bytes)")
    if oversized:
        problems.append("oversized_files: " + ", ".join(oversized))
    return {"gate": "hygiene", "merge_base": merge_base, "head": head,
            "changed_files": len(added), "passed": not problems, "problems": problems}


def _api_get(url: str, token: str) -> Mapping[str, Any]:
    request = urllib.request.Request(url, headers={
        "Accept": "application/vnd.github+json",
        "Authorization": f"Bearer {token}",
        "X-GitHub-Api-Version": "2022-11-28",
    })
    with urllib.request.urlopen(request, timeout=30) as response:
        return json.loads(response.read().decode("utf-8"))


def run_verdict(repository: str, number: int, expected_head: str, token: str,
                api_url: str = "https://api.github.com") -> dict[str, Any]:
    """Pre-merge re-check: the PR's live head must equal ``expected_head`` and be accepted."""
    pr = _api_get(f"{api_url.rstrip('/')}/repos/{repository}/pulls/{number}", token)
    head = str((pr.get("head") or {}).get("sha", ""))
    base = {"gate": "verdict", "head": head}
    if head.lower() != expected_head.lower():
        return {**base, "passed": False, "reason": "live_head_differs_from_expected"}
    if pr.get("draft"):
        return {**base, "passed": False, "reason": "draft_pull_request"}
    if (pr.get("base") or {}).get("ref") != "main":
        return {**base, "passed": False, "reason": "base_is_not_main"}
    found = evaluate_review(head, fetch_review_entries(repository, number, token, api_url))
    return {**base, "passed": found.accepted, **found.to_dict()}


def _api_get_all(url: str, token: str) -> list[Mapping[str, Any]]:
    items: list[Mapping[str, Any]] = []
    next_url: str | None = url + ("&" if "?" in url else "?") + "per_page=100"
    while next_url:
        request = urllib.request.Request(next_url, headers={
            "Accept": "application/vnd.github+json",
            "Authorization": f"Bearer {token}",
            "X-GitHub-Api-Version": "2022-11-28",
        })
        with urllib.request.urlopen(request, timeout=30) as response:
            items.extend(json.loads(response.read().decode("utf-8")))
            match = re.search(r'<([^>]+)>;\s*rel="next"', response.headers.get("Link", ""))
            next_url = match.group(1) if match else None
    return items


def fetch_review_entries(repository: str, number: int, token: str,
                         api_url: str = "https://api.github.com") -> list[ReviewEntry]:
    base = f"{api_url.rstrip('/')}/repos/{repository}"
    entries = []
    for item in _api_get_all(f"{base}/issues/{number}/comments", token):
        entries.append(ReviewEntry(str(item.get("body") or ""), str((item.get("user") or {}).get("login", "")),
                                   str(item.get("author_association", "")), str(item.get("created_at") or "")))
    for item in _api_get_all(f"{base}/pulls/{number}/reviews", token):
        if str(item.get("state", "")).upper() in IGNORED_REVIEW_STATES:
            continue
        entries.append(ReviewEntry(str(item.get("body") or ""), str((item.get("user") or {}).get("login", "")),
                                   str(item.get("author_association", "")), str(item.get("submitted_at") or "")))
    return entries


def run_review(event: Mapping[str, Any], repository: str, token: str) -> dict[str, Any]:
    pr = event.get("pull_request") or {}
    head = str((pr.get("head") or {}).get("sha", ""))
    if pr.get("draft"):
        return {"gate": "review", "head": head, "passed": False, "reason": "draft_pull_request"}
    if (pr.get("base") or {}).get("ref") != "main":
        return {"gate": "review", "head": head, "passed": False, "reason": "base_is_not_main"}
    entries = fetch_review_entries(repository, int(pr["number"]), token)
    verdict = evaluate_review(head, entries)
    return {"gate": "review", "head": head, "passed": verdict.accepted, **verdict.to_dict()}


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="python -m reverse_agent.landing_review")
    sub = parser.add_subparsers(dest="command", required=True)
    hygiene = sub.add_parser("hygiene", help="check the exact PR range")
    hygiene.add_argument("--base", required=True)
    hygiene.add_argument("--head", required=True)
    review = sub.add_parser("review", help="require an exact-head independent review verdict")
    review.add_argument("--event-path", required=True)
    review.add_argument("--repository", required=True)
    verdict = sub.add_parser("verdict", help="re-check the verdict right before merging")
    verdict.add_argument("--repository", required=True)
    verdict.add_argument("--pr", type=int, required=True)
    verdict.add_argument("--head", required=True)
    args = parser.parse_args(argv)

    try:
        if args.command == "hygiene":
            result = run_hygiene(args.base, args.head)
        elif args.command == "verdict":
            token = os.environ.get("GITHUB_TOKEN") or os.environ.get("GH_TOKEN") or ""
            if not token:
                result = {"gate": "verdict", "passed": False, "reason": "missing_github_token"}
            else:
                result = run_verdict(args.repository, args.pr, args.head, token)
        else:
            with open(args.event_path, encoding="utf-8") as handle:
                event = json.load(handle)
            token = os.environ.get("GITHUB_TOKEN") or os.environ.get("GH_TOKEN") or ""
            if not token:
                result = {"gate": "review", "passed": False, "reason": "missing_github_token"}
            else:
                result = run_review(event, args.repository, token)
    except (RuntimeError, OSError, ValueError, KeyError, urllib.error.URLError) as exc:
        result = {"gate": args.command, "passed": False, "reason": f"{type(exc).__name__}: {exc}"[:500]}
    print(json.dumps(result, indent=2, ensure_ascii=False))
    return 0 if result.get("passed") else 1


if __name__ == "__main__":  # pragma: no cover
    sys.exit(main())
