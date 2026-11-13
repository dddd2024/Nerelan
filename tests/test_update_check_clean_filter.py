"""Real local Git regression: a configured content filter must not run.

``git status`` re-reads a tracked file's content to decide whether it is
modified, and that re-read runs the attribute-selected clean/process filter.
A filter is an arbitrary configured command, so a read-only observer must
never invoke one: doing so can write to other tracked files and contradicts
the read-only promise this checker explicitly makes.

The fixture owns everything it can execute: a benign shell helper that appends
to a tracked marker and to an out-of-tree call log, then copies its input
through unchanged. System config is disabled and global config points at a
fixture file. Only the remote main advertisement is mocked (no network);
origin, HEAD, config discovery and status stay real Git subprocesses.
"""
from __future__ import annotations

import os
from pathlib import Path
import subprocess
import time

import pytest

from reverse_agent import update_check

_ORIGIN = "https://github.com/dddd2024/Nerelan.git"
_DRIVER = "filter.owned-audit"
_MARKER_BYTES = b"untouched\n"
# Same byte length before and after, so only a content re-read can notice it.
_FILTERED_BEFORE = b"before\n"
_FILTERED_AFTER = b"after!\n"


def _fixture(tmp_path: Path, monkeypatch, scope: str):
    owned = tmp_path / "owned"
    owned.mkdir()
    global_config = owned / "global.gitconfig"
    global_config.write_bytes(b"")
    monkeypatch.setenv("GIT_CONFIG_NOSYSTEM", "1")
    monkeypatch.setenv("GIT_CONFIG_GLOBAL", str(global_config))
    monkeypatch.setenv("GIT_TERMINAL_PROMPT", "0")
    for name in ("GIT_CONFIG_PARAMETERS", "GIT_CONFIG_COUNT", "GIT_DIR",
                 "GIT_WORK_TREE", "GIT_INDEX_FILE"):
        monkeypatch.delenv(name, raising=False)

    repo = tmp_path / "repo"
    repo.mkdir()
    real_run = subprocess.run

    def git(*args: str) -> str:
        return real_run(
            ["git", "-C", str(repo), *args],
            capture_output=True, text=True, check=True,
            stdin=subprocess.DEVNULL, timeout=15,
        ).stdout.strip()

    git("init", "-q")
    git("config", "user.email", "fixture@localhost")
    git("config", "user.name", "Fixture")
    marker = repo / "z-tracked-marker.txt"
    marker.write_bytes(_MARKER_BYTES)
    filtered = repo / "a.filtered"
    filtered.write_bytes(_FILTERED_BEFORE)
    (repo / ".gitattributes").write_bytes(b"*.filtered filter=owned-audit\n")
    git("add", "z-tracked-marker.txt", "a.filtered", ".gitattributes")
    git("commit", "-qm", "fixture")
    git("remote", "add", "origin", _ORIGIN)
    head = git("rev-parse", "HEAD")
    assert len(head) == 40

    # Benign test-owned helper: records that it ran, then copies input through
    # so the file's own content is unchanged and only the side effect differs.
    log = owned / "clean-filter-calls.log"
    helper = owned / "owned-clean-filter.sh"
    helper.write_bytes((
        "#!/bin/sh\n"
        f"printf 'owned clean filter called\\n' >> '{marker.as_posix()}'\n"
        f"printf 'owned clean filter called\\n' >> '{log.as_posix()}'\n"
        "cat\n"
    ).encode("utf-8"))
    helper.chmod(0o700)
    value = f"'{helper.as_posix()}'"
    if scope in ("repository", "both"):
        git("config", f"{_DRIVER}.clean", value)
    if scope in ("global", "both"):
        git("config", "--global", f"{_DRIVER}.clean", value)

    # Same-size content edit plus a newer mtime, so native status must re-read
    # the content instead of trusting the cached stat entry.
    filtered.write_bytes(_FILTERED_AFTER)
    stamp = time.time() + 10
    os.utime(filtered, (stamp, stamp))
    return repo, marker, log, head, real_run


def _strip_filter_overrides(cmd: list[str]) -> list[str]:
    """Drop the command-scoped ``-c filter.*`` overrides (the old behavior)."""
    out: list[str] = []
    index = 0
    while index < len(cmd):
        if (cmd[index] == "-c" and index + 1 < len(cmd)
                and cmd[index + 1].startswith("filter.")):
            index += 2
            continue
        out.append(cmd[index])
        index += 1
    return out


def _has_driver_override(cmd: list[str], key: str) -> bool:
    return any(cmd[i] == "-c" and cmd[i + 1].startswith(f"{_DRIVER}.{key}=")
               for i in range(len(cmd) - 1))


@pytest.mark.parametrize("scope", ["repository", "global", "both"])
def test_probe_never_runs_configured_clean_filter(tmp_path, monkeypatch, scope):
    repo, marker, log, head, real_run = _fixture(tmp_path, monkeypatch, scope)
    calls = []

    def offline_remote(cmd, **kwargs):
        calls.append((list(cmd), kwargs))
        if "ls-remote" in cmd:
            return subprocess.CompletedProcess(cmd, 0, f"{head}\trefs/heads/main\n", "")
        return real_run(cmd, **kwargs)

    monkeypatch.setattr(update_check.subprocess, "run", offline_remote)
    result = update_check.probe_checkout(repo)

    assert not log.exists(), "configured clean filter ran during the probe"
    assert marker.read_bytes() == _MARKER_BYTES
    assert result["local_modified"] is True, result
    assert result["install_authorized"] is False
    assert result["verified_release"] is False
    # The real status observation was actually issued, carrying every existing
    # invariant plus the command-scoped driver suppression.
    statuses = [cmd for cmd, _ in calls if "status" in cmd]
    assert statuses, "no native status observation was issued"
    for cmd in statuses:
        assert _has_driver_override(cmd, "clean"), cmd
        assert _has_driver_override(cmd, "smudge"), cmd
        assert _has_driver_override(cmd, "process"), cmd
        assert _has_driver_override(cmd, "required"), cmd
    for cmd, kwargs in calls:
        assert kwargs["env"]["GIT_NO_LAZY_FETCH"] == "1"
        assert kwargs["env"]["GIT_OPTIONAL_LOCKS"] == "0"
        assert kwargs["stdin"] == subprocess.DEVNULL
        assert kwargs["timeout"] == update_check._TIMEOUT

    # Control: the same probe without the command-scoped driver overrides (the
    # old behavior) really executes this fixture's helper, so the gate above
    # is live rather than vacuous.
    stripped: list[list[str]] = []

    def old_behavior(cmd, **kwargs):
        original = list(cmd)
        reduced = _strip_filter_overrides(original)
        if reduced != original:
            stripped.append(reduced)
        return offline_remote(reduced, **kwargs)

    monkeypatch.setattr(update_check.subprocess, "run", old_behavior)
    old = update_check.probe_checkout(repo)

    assert any("status" in cmd for cmd in stripped)
    assert log.exists(), "fixture helper is not live; regression would be vacuous"
    assert marker.read_bytes() != _MARKER_BYTES
    assert old["install_authorized"] is False
    assert old["verified_release"] is False


def test_probe_suppresses_required_filter_without_failing(tmp_path, monkeypatch):
    """A required driver must not turn the blanked command into a status failure."""
    repo, marker, log, head, real_run = _fixture(tmp_path, monkeypatch, "repository")
    real_run(["git", "-C", str(repo), "config", f"{_DRIVER}.required", "true"],
             capture_output=True, check=True)

    def offline_remote(cmd, **kwargs):
        if "ls-remote" in cmd:
            return subprocess.CompletedProcess(cmd, 0, f"{head}\trefs/heads/main\n", "")
        return real_run(cmd, **kwargs)

    monkeypatch.setattr(update_check.subprocess, "run", offline_remote)
    result = update_check.probe_checkout(repo)

    assert not log.exists()
    assert marker.read_bytes() == _MARKER_BYTES
    assert result["reason"] != "local_status_unavailable", result
    assert result["local_modified"] is True


def test_probe_fails_closed_when_filter_discovery_unavailable(tmp_path, monkeypatch):
    """If driver discovery cannot be completed, refuse to observe through a filter."""
    repo, marker, log, head, real_run = _fixture(tmp_path, monkeypatch, "repository")

    def broken_discovery(cmd, **kwargs):
        if "config" in cmd and "--name-only" in cmd:
            return subprocess.CompletedProcess(cmd, 128, "", "fatal: unavailable\n")
        if "ls-remote" in cmd:
            return subprocess.CompletedProcess(cmd, 0, f"{head}\trefs/heads/main\n", "")
        return real_run(cmd, **kwargs)

    monkeypatch.setattr(update_check.subprocess, "run", broken_discovery)
    result = update_check.probe_checkout(repo)

    assert result["status"] == "UNKNOWN"
    assert result["reason"] == "filter_discovery_unavailable", result
    assert not log.exists(), "filter ran despite failed driver discovery"
    assert marker.read_bytes() == _MARKER_BYTES
