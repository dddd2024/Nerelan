"""Fail-closed *read-only* Nerelan source version discovery.

This is not an installer. A newer merged source revision is NOT a verified,
signed desktop package. No working tree, git references, services or accounts
are changed; deployment requires a separate approved transactional updater.
"""
from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import re
import subprocess

_SHA = re.compile(r"^[0-9a-f]{40}$")
_ORIGINS = {
    "https://github.com/dddd2024/Nerelan.git",
    "https://github.com/dddd2024/Nerelan",
    "git@github.com:dddd2024/Nerelan.git",
}
_TIMEOUT = 8


def classify_revisions(*, installed: str, remote: str, ancestry: str,
                       local_modified: bool) -> dict[str, object]:
    """Decide the *source* state, not whether an unverified update can install."""
    base = {"installed_sha": installed, "remote_main_sha": remote,
            "local_modified": local_modified, "install_authorized": False,
            "verified_release": False}
    if not _SHA.fullmatch(installed) or not _SHA.fullmatch(remote):
        return dict(base, status="UNKNOWN", reason="unverified_revision")
    if installed == remote:
        return dict(base, status="UP_TO_DATE", reason="same_source_commit")
    if local_modified:
        return dict(base, status="LOCAL_CHANGES_PRESERVE",
                    reason="source_has_uncommitted_changes")
    labels = {
        "remote_descendant": ("SOURCE_UPDATE_AVAILABLE", "source_only_not_release"),
        "local_descendant": ("LOCAL_AHEAD", "local_commit_ahead_of_main"),
        "diverged": ("DIVERGED", "divergent_repository_history"),
        "unknown": ("REMOTE_CHANGE_UNVERIFIED", "remote_commit_not_locally_verified"),
    }
    status, reason = labels.get(ancestry, labels["unknown"])
    return dict(base, status=status, reason=reason)


def probe_checkout(repo: str | Path) -> dict[str, object]:
    root = Path(repo)
    result = {"status": "UNKNOWN", "reason": None, "install_authorized": False,
              "verified_release": False}
    if not root.is_dir():
        return result | {"reason": "missing_checkout"}

    def git(*args: str) -> tuple[int, str]:
        env = dict(os.environ)
        env.update(GIT_TERMINAL_PROMPT="0", GIT_OPTIONAL_LOCKS="0",
                   GIT_LFS_SKIP_SMUDGE="1")
        try:
            proc = subprocess.run(
                ["git", "-C", str(root), *args],
                capture_output=True, text=True, encoding="utf-8", errors="replace",
                stdin=subprocess.DEVNULL, timeout=_TIMEOUT, env=env, check=False)
        except (OSError, subprocess.TimeoutExpired):
            return -1, ""
        return proc.returncode, proc.stdout.strip()

    code, origin = git("remote", "get-url", "origin")
    if code != 0 or origin not in _ORIGINS:
        # Do not probe an unexpected remote or disclose credential-bearing URLs.
        return result | {"status": "UNTRUSTED_ORIGIN", "reason": "canonical_origin_required"}
    code, installed = git("rev-parse", "HEAD")
    if code != 0 or not _SHA.fullmatch(installed):
        return result | {"reason": "missing_installed_revision"}
    code, dirty = git("status", "--porcelain", "-uno")
    if code != 0:
        return result | {"reason": "local_status_unavailable"}
    modified = bool(dirty)
    code, remote_line = git("ls-remote", "--exit-code", "origin", "refs/heads/main")
    if code != 0:
        return result | {"status": "REMOTE_UNAVAILABLE",
                         "reason": "network_or_remote_unavailable",
                         "installed_sha": installed, "local_modified": modified}
    parts = remote_line.split()
    remote = parts[0] if len(parts) == 2 and parts[1] == "refs/heads/main" else ""
    if not _SHA.fullmatch(remote):
        return result | {"reason": "unexpected_remote_reply"}
    if remote == installed:
        ancestry = "remote_descendant"
    else:
        code, _ = git("cat-file", "-e", remote + "^{commit}")
        if code != 0:
            ancestry = "unknown"
        elif git("merge-base", "--is-ancestor", installed, remote)[0] == 0:
            ancestry = "remote_descendant"
        elif git("merge-base", "--is-ancestor", remote, installed)[0] == 0:
            ancestry = "local_descendant"
        else:
            ancestry = "diverged"
    return classify_revisions(installed=installed, remote=remote,
                              ancestry=ancestry, local_modified=modified)


def main() -> int:
    parser = argparse.ArgumentParser(description="Observe remote Nerelan source version only; never install.")
    parser.add_argument("--repo", default=str(Path(__file__).resolve().parents[1]))
    args = parser.parse_args()
    result = probe_checkout(args.repo)
    print(json.dumps(result, ensure_ascii=False, sort_keys=True))
    return 0 if result["status"] not in ("UNTRUSTED_ORIGIN", "UNKNOWN") else 2


if __name__ == "__main__":
    raise SystemExit(main())