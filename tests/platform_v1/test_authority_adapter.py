"""Exact-live-head Git-object behavior tests for Authority Bundle loading."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
import shutil
import subprocess

import pytest

from reverse_agent.platform_v1 import authority_adapter
from reverse_agent.platform_v1.authority_adapter import AuthorityBundleError


REPO_ROOT = Path(__file__).resolve().parents[2]
AUTHORITY_PATHS = (
    "project_state/decision_packet.md",
    "project_state/gates/command_plan.json",
    "project_state/mainline_merge_intents/active.json",
)
BASE = "1142dd324fdd4c4bf2a1353d9d5e93bc04b33507"
BRANCH = "agent/restore-path-a-state-gate-current-main-v1"


def _run(root: Path, *args: str, input_bytes: bytes | None = None) -> bytes:
    return subprocess.run(
        ["git", "-C", str(root), *args], input=input_bytes,
        check=True, capture_output=True,
    ).stdout


def _make_candidate(tmp_path: Path) -> tuple[Path, str]:
    root = tmp_path / "candidate"
    root.mkdir()
    _run(root, "init", "-q")
    _run(root, "config", "user.email", "test@example.invalid")
    _run(root, "config", "user.name", "Test")
    for relative in AUTHORITY_PATHS:
        destination = root / relative
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(REPO_ROOT / relative, destination)
    _run(root, "add", "--", *AUTHORITY_PATHS)
    _run(root, "commit", "-q", "-m", "authority")
    return root, _run(root, "rev-parse", "HEAD").decode().strip()


class _Issue:
    def fetch_issue(self, repository: str, issue_number: int) -> dict:
        return {
            "body": "approved issue",
            "state": "OPEN",
            "labels": ["work-item", "r2", "owner-accepted"],
        }


class _PR:
    def __init__(self, head: str, events: list[str] | None = None) -> None:
        self.head = head
        self.events = events

    def fetch_pr(self, repository: str, pr_number: int) -> dict:
        if self.events is not None:
            self.events.append("pr")
        return {
            "state": "OPEN", "isDraft": True, "autoMergeRequest": None,
            "baseRefName": "main", "baseRefOid": BASE,
            "headRefName": BRANCH, "headRefOid": self.head,
        }


def _load(root: Path, head: str):
    return authority_adapter.load_authority_bundle(
        repo_dir=str(root), repository="dddd2024/reverse-agent",
        issue_number=105, pr_number=106,
        issue_provider=_Issue(), pr_provider=_PR(head),
    )


def test_dirty_worktree_authority_cannot_change_exact_head_bundle(tmp_path: Path) -> None:
    root, head = _make_candidate(tmp_path)
    expected = _load(root, head)
    for relative in AUTHORITY_PATHS:
        (root / relative).write_text("candidate dirty replacement", encoding="utf-8")
    observed = _load(root, head)
    assert observed == expected


def test_bundle_digests_equal_exact_head_blob_bytes(tmp_path: Path) -> None:
    root, head = _make_candidate(tmp_path)
    bundle = _load(root, head)
    decision = _run(root, "cat-file", "blob", f"{head}:{AUTHORITY_PATHS[0]}")
    plan = _run(root, "cat-file", "blob", f"{head}:{AUTHORITY_PATHS[1]}")
    assert bundle.decision_content_sha256 == hashlib.sha256(decision).hexdigest()
    assert bundle.command_plan_sha256 == hashlib.sha256(plan).hexdigest()


def test_live_pr_is_observed_before_authority_blob_read(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    root, head = _make_candidate(tmp_path)
    events: list[str] = []
    original = authority_adapter._read_exact_authority_blob

    def recording(*args, **kwargs):
        events.append("blob")
        return original(*args, **kwargs)

    monkeypatch.setattr(authority_adapter, "_read_exact_authority_blob", recording)
    authority_adapter.load_authority_bundle(
        repo_dir=str(root), repository="dddd2024/reverse-agent",
        issue_number=105, pr_number=106, issue_provider=_Issue(),
        pr_provider=_PR(head, events),
    )
    assert events[0] == "pr"


def test_missing_exact_head_fails_closed(tmp_path: Path) -> None:
    root, _ = _make_candidate(tmp_path)
    with pytest.raises(AuthorityBundleError) as exc_info:
        _load(root, "a" * 40)
    assert exc_info.value.code == "authority_git_object_read_failed"


def test_missing_authority_blob_fails_closed(tmp_path: Path) -> None:
    root, _ = _make_candidate(tmp_path)
    _run(root, "rm", "-q", "--", AUTHORITY_PATHS[2])
    _run(root, "commit", "-q", "-m", "missing")
    head = _run(root, "rev-parse", "HEAD").decode().strip()
    with pytest.raises(AuthorityBundleError) as exc_info:
        _load(root, head)
    assert exc_info.value.code == "authority_tree_entry_count_invalid"


def test_committed_symlink_authority_entry_fails_closed(tmp_path: Path) -> None:
    root, _ = _make_candidate(tmp_path)
    target_oid = _run(root, "hash-object", "-w", "--stdin", input_bytes=b"elsewhere").decode().strip()
    _run(root, "update-index", "--add", "--cacheinfo", f"120000,{target_oid},{AUTHORITY_PATHS[2]}")
    _run(root, "commit", "-q", "-m", "symlink")
    head = _run(root, "rev-parse", "HEAD").decode().strip()
    with pytest.raises(AuthorityBundleError) as exc_info:
        _load(root, head)
    assert exc_info.value.code == "authority_tree_entry_not_regular_blob"


def test_non_blob_authority_entry_fails_closed(tmp_path: Path) -> None:
    root, _ = _make_candidate(tmp_path)
    relative = AUTHORITY_PATHS[2]
    _run(root, "rm", "-q", "--", relative)
    directory = root / relative
    directory.mkdir(parents=True)
    (directory / "child").write_text("not a blob entry", encoding="utf-8")
    _run(root, "add", "--", f"{relative}/child")
    _run(root, "commit", "-q", "-m", "tree")
    head = _run(root, "rev-parse", "HEAD").decode().strip()
    with pytest.raises(AuthorityBundleError) as exc_info:
        _load(root, head)
    assert exc_info.value.code == "authority_tree_entry_not_regular_blob"


def test_malformed_tree_entry_fails_closed(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    root, head = _make_candidate(tmp_path)
    original = authority_adapter._git_object_command

    def malformed(repo_root: Path, args: list[str]) -> bytes:
        if args[0] == "ls-tree":
            return b"malformed\0"
        return original(repo_root, args)

    monkeypatch.setattr(authority_adapter, "_git_object_command", malformed)
    with pytest.raises(AuthorityBundleError) as exc_info:
        _load(root, head)
    assert exc_info.value.code == "authority_tree_entry_malformed"


def test_git_replace_ref_cannot_substitute_authority(tmp_path: Path) -> None:
    root, original_head = _make_candidate(tmp_path)
    expected = _load(root, original_head)
    (root / AUTHORITY_PATHS[0]).write_text("invalid replacement", encoding="utf-8")
    _run(root, "add", "--", AUTHORITY_PATHS[0])
    _run(root, "commit", "-q", "-m", "replacement")
    replacement_head = _run(root, "rev-parse", "HEAD").decode().strip()
    _run(root, "replace", original_head, replacement_head)
    assert _load(root, original_head) == expected
