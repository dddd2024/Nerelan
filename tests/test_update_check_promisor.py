"""Real Git promisor-clone regression: update discovery must not lazy-fetch.

No internet access: this fixture uses a local file URI and mocks only the
top-level remote main advertisement. Git object and ancestry probes stay real.
"""
from __future__ import annotations

import os
from pathlib import Path
import subprocess
from unittest.mock import patch

import pytest

from reverse_agent import update_check


def _git(real_run, checkout: Path, *args: str) -> str:
    result = real_run(
        ["git", "-C", str(checkout), *args],
        capture_output=True, text=True, check=True,
        env={**os.environ, "GIT_TERMINAL_PROMPT": "0", "GIT_NO_LAZY_FETCH": "1"},
        timeout=15,
    )
    return result.stdout.strip()


def _git_args(cmd) -> list[str]:
    """Subcommand args after ``git -C <root>`` and the known fsmonitor override."""
    args = list(cmd[3:])
    if args[:2] == ["-c", "core.fsmonitor=false"]:
        args = args[2:]
    return args


def test_no_lazy_fetch_or_promisor_object_writes(tmp_path):
    real_run = subprocess.run
    source = tmp_path / "local_source"
    source.mkdir()
    _git(real_run, source, "init", "-q")
    _git(real_run, source, "config", "user.email", "fixture@localhost")
    _git(real_run, source, "config", "user.name", "Fixture")
    (source / "a.txt").write_text("first\n", encoding="utf-8")
    _git(real_run, source, "add", "a.txt")
    _git(real_run, source, "commit", "-qm", "first")
    _git(real_run, source, "config", "uploadpack.allowFilter", "true")

    clone = tmp_path / "partial_clone"
    clone_result = real_run(
        ["git", "clone", "--filter=blob:none", source.as_uri(), str(clone)],
        capture_output=True, text=True, timeout=20,
        env={**os.environ, "GIT_TERMINAL_PROMPT": "0"},
    )
    if clone_result.returncode:
        pytest.skip("Git file URI partial clone unsupported on this test host")

    (source / "a.txt").write_text("second\n", encoding="utf-8")
    _git(real_run, source, "add", "a.txt")
    _git(real_run, source, "commit", "-qm", "second")
    remote_head = _git(real_run, source, "rev-parse", "HEAD")
    assert len(remote_head) == 40

    _git(real_run, clone, "remote", "set-url", "origin",
         "https://github.com/dddd2024/Nerelan.git")
    _git(real_run, clone, "config", "remote.origin.promisor", "false")
    _git(real_run, clone, "remote", "add", "fixture", source.as_uri())
    _git(real_run, clone, "config", "remote.fixture.promisor", "true")
    _git(real_run, clone, "config", "remote.fixture.partialclonefilter", "blob:none")

    object_dir = clone / ".git" / "objects"
    before = sorted(p.relative_to(object_dir).as_posix()
                    for p in object_dir.rglob("*") if p.is_file())
    real_calls = []

    def only_mock_remote_probe(cmd, **kwargs):
        args = _git_args(cmd)
        if args[0] == "ls-remote":
            return subprocess.CompletedProcess(
                cmd, 0, f"{remote_head}\trefs/heads/main\n", "")
        real_calls.append((args, kwargs["env"].get("GIT_NO_LAZY_FETCH")))
        return real_run(cmd, **kwargs)

    with patch.object(update_check.subprocess, "run", only_mock_remote_probe):
        result = update_check.probe_checkout(clone)

    after = sorted(p.relative_to(object_dir).as_posix()
                   for p in object_dir.rglob("*") if p.is_file())
    assert result["status"] == "REMOTE_CHANGE_UNVERIFIED", result
    assert result["install_authorized"] is False
    assert result["verified_release"] is False
    assert before == after, "supposedly read-only Git probe wrote fetched objects"
    assert real_calls
    assert all(value == "1" for _, value in real_calls)
    assert any(args[0] == "cat-file" for args, _ in real_calls)