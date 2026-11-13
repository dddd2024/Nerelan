"""Real local Git regression: a configured core.fsmonitor helper must not run.

The fixture owns everything it can execute: a benign shell helper that appends
to a tracked marker and to an out-of-tree call log. System config is disabled
and global config points at a fixture file. Only the remote main advertisement
is mocked (no network); origin, HEAD and status stay real Git subprocesses.
"""
from __future__ import annotations

import hashlib
from pathlib import Path
import subprocess

import pytest

from reverse_agent import update_check

_ORIGIN = "https://github.com/dddd2024/Nerelan.git"
_OVERRIDE = ["-c", "core.fsmonitor=false"]
_MARKER_BYTES = b"before\n"


def _snapshot(root: Path) -> dict[str, str]:
    return {p.relative_to(root).as_posix(): hashlib.sha256(p.read_bytes()).hexdigest()
            for p in sorted(root.rglob("*")) if p.is_file()}


def _refs(snapshot: dict[str, str]) -> dict[str, str]:
    return {k: v for k, v in snapshot.items()
            if k.startswith(".git/refs/") or k in (".git/HEAD", ".git/packed-refs")}


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
    marker = repo / "tracked-marker.txt"
    marker.write_bytes(_MARKER_BYTES)
    git("add", "tracked-marker.txt")
    git("commit", "-qm", "fixture")
    git("remote", "add", "origin", _ORIGIN)
    head = git("rev-parse", "HEAD")
    assert len(head) == 40

    # Benign test-owned helper; it emits a valid v2 reply ("everything changed").
    log = owned / "helper-calls.log"
    helper = owned / "fsmonitor-helper.sh"
    helper.write_bytes((
        "#!/bin/sh\n"
        f"printf 'helper called\\n' >> '{marker.as_posix()}'\n"
        f"printf 'helper called\\n' >> '{log.as_posix()}'\n"
        "printf 'fixture-token\\0/\\0'\n"
    ).encode("utf-8"))
    helper.chmod(0o700)
    # Git runs the hook through the shell; quoting keeps unusual temp paths intact.
    value = f"'{helper.as_posix()}'"
    if scope in ("repository", "both"):
        git("config", "core.fsmonitor", value)
    if scope in ("global", "both"):
        git("config", "--global", "core.fsmonitor", value)
    assert git("config", "core.fsmonitor") == value
    return repo, marker, log, head, real_run


@pytest.mark.parametrize("scope", ["repository", "global", "both"])
def test_probe_never_runs_configured_fsmonitor_helper(tmp_path, monkeypatch, scope):
    repo, marker, log, head, real_run = _fixture(tmp_path, monkeypatch, scope)
    before = _snapshot(repo)
    calls = []

    def offline_remote(cmd, **kwargs):
        calls.append((list(cmd), kwargs))
        if "ls-remote" in cmd:
            return subprocess.CompletedProcess(cmd, 0, f"{head}\trefs/heads/main\n", "")
        return real_run(cmd, **kwargs)

    monkeypatch.setattr(update_check.subprocess, "run", offline_remote)
    result = update_check.probe_checkout(repo)
    after = _snapshot(repo)

    assert not log.exists(), "configured fsmonitor helper ran during the probe"
    assert marker.read_bytes() == _MARKER_BYTES
    assert after == before, "read-only probe changed the working tree, index or refs"
    assert result["status"] == "UP_TO_DATE", result
    assert result["local_modified"] is False
    assert result["install_authorized"] is False
    assert result["verified_release"] is False
    # The real status observation was actually issued, with existing invariants.
    assert any("status" in cmd for cmd, _ in calls)
    for _, kwargs in calls:
        assert kwargs["env"]["GIT_NO_LAZY_FETCH"] == "1"
        assert kwargs["env"]["GIT_OPTIONAL_LOCKS"] == "0"
        assert kwargs["stdin"] == subprocess.DEVNULL
        assert kwargs["timeout"] == update_check._TIMEOUT

    # Control: the same probe without the command-scoped override (the old
    # behavior) really executes this fixture's helper, so the gate above is live.
    stripped = []

    def old_behavior(cmd, **kwargs):
        cmd = list(cmd)
        if cmd[3:5] == _OVERRIDE:
            del cmd[3:5]
            stripped.append(cmd)
        return offline_remote(cmd, **kwargs)

    monkeypatch.setattr(update_check.subprocess, "run", old_behavior)
    old = update_check.probe_checkout(repo)
    old_after = _snapshot(repo)

    assert any("status" in cmd for cmd in stripped)
    assert log.exists(), "fixture helper is not live; regression would be vacuous"
    assert marker.read_bytes() != _MARKER_BYTES
    # Optional locks still keep the index and refs untouched; only the helper's
    # working-tree write differs, which is exactly the defect being gated.
    assert old_after[".git/index"] == before[".git/index"]
    assert _refs(old_after) == _refs(before)
    assert old["install_authorized"] is False
    assert old["verified_release"] is False
