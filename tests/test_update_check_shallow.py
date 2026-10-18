"""Real local shallow checkout: incomplete ancestry must remain unverified."""

from __future__ import annotations

import subprocess

from reverse_agent import update_check


def test_shallow_boundary_with_both_objects_cannot_prove_divergence(tmp_path, monkeypatch):
    repo = tmp_path / "shallow_checkout"
    repo.mkdir()
    real_run = subprocess.run

    def git(*args):
        p = real_run(
            ["git", "-C", str(repo), *args],
            capture_output=True, text=True, check=True, timeout=10,
        )
        return p.stdout.strip()

    git("init", "-q")
    git("config", "user.name", "Fixture")
    git("config", "user.email", "fixture@localhost")
    (repo / "file.txt").write_text("A\n", encoding="utf-8")
    git("add", "file.txt")
    git("commit", "-qm", "A")
    previous = git("rev-parse", "HEAD")
    (repo / "file.txt").write_text("B\n", encoding="utf-8")
    git("add", "file.txt")
    git("commit", "-qm", "B")
    installed = git("rev-parse", "HEAD")
    git("remote", "add", "origin", "https://github.com/dddd2024/Nerelan.git")

    # Simulate a shallow boundary even though the original A object remains
    # locally present: Git now treats HEAD as parentless for graph traversal.
    (repo / ".git" / "shallow").write_text(installed + "\n", encoding="ascii")
    assert git("rev-parse", "--is-shallow-repository") == "true"
    assert git("cat-file", "-t", previous) == "commit"
    for before, after in ((previous, installed), (installed, previous)):
        verdict = real_run(
            ["git", "-C", str(repo), "merge-base", "--is-ancestor", before, after],
            capture_output=True, timeout=10,
        )
        assert verdict.returncode == 1

    def offline_remote(cmd, **kwargs):
        if "ls-remote" in cmd:
            return subprocess.CompletedProcess(
                cmd, 0, stdout=previous + "\trefs/heads/main\n", stderr=""
            )
        return real_run(cmd, **kwargs)

    monkeypatch.setattr(update_check.subprocess, "run", offline_remote)
    result = update_check.probe_checkout(repo)
    assert result["status"] == "REMOTE_CHANGE_UNVERIFIED"
    assert result["installed_sha"] == installed
    assert result["remote_main_sha"] == previous
    assert result["install_authorized"] is False
    assert result["verified_release"] is False
