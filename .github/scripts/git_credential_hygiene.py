"""Fail closed when effective Git configuration can expose credentials."""

from __future__ import annotations

import re
import subprocess
import sys
from collections.abc import Sequence

_TOKEN_MATERIAL = re.compile(
    r"(?i)(?:"
    r"gh[pousr]_[A-Za-z0-9_]+|"
    r"x-access-token|oauth2:|"
    r"://[^/\s:@]+:[^@\s]+@|"
    r"://[^/@\s]+@"
    r")"
)
_ALLOWED_SCOPES = frozenset(
    {"system", "global", "local", "worktree", "command"}
)


class CredentialHygieneFailure(RuntimeError):
    """A category-only failure that never contains matched configuration."""


def _fail(category: str) -> None:
    raise CredentialHygieneFailure(category)


def _effective_entries() -> tuple[tuple[str, str, str], ...]:
    completed = subprocess.run(
        (
            "git",
            "config",
            "--includes",
            "--show-origin",
            "--show-scope",
            "--null",
            "--list",
        ),
        check=False,
        capture_output=True,
    )
    if completed.returncode != 0:
        _fail("effective_config_unreadable")

    fields = completed.stdout.split(b"\0")
    if fields and fields[-1] == b"":
        fields.pop()
    if len(fields) % 3:
        _fail("effective_config_malformed")

    entries: list[tuple[str, str, str]] = []
    for offset in range(0, len(fields), 3):
        scope = fields[offset].decode("utf-8", "surrogateescape")
        origin = fields[offset + 1].decode("utf-8", "surrogateescape")
        key, separator, value = fields[offset + 2].partition(b"\n")
        if scope not in _ALLOWED_SCOPES or not origin or not separator:
            _fail("effective_config_malformed")
        entries.append(
            (
                scope,
                key.decode("utf-8", "surrogateescape"),
                value.decode("utf-8", "surrogateescape"),
            )
        )
    return tuple(entries)


def _audit_entry(key: str, value: str) -> None:
    lowered = key.lower()
    combined = f"{key}\n{value}"
    if lowered.startswith("http.") and lowered.endswith(".extraheader"):
        _fail("authorization_extraheader")
    if lowered == "credential.helper" or (
        lowered.startswith("credential.") and lowered.endswith(".helper")
    ):
        _fail("credential_helper")
    if lowered.startswith("url.") and lowered.endswith(".insteadof"):
        if _TOKEN_MATERIAL.search(combined):
            _fail("credential_bearing_insteadof")
    if lowered == "core.sshcommand" or (
        lowered.startswith("remote.") and lowered.endswith(".sshcommand")
    ):
        _fail("ssh_command")
    if lowered.startswith("remote.") and lowered.endswith(
        (".url", ".pushurl")
    ):
        if _TOKEN_MATERIAL.search(combined):
            _fail("token_bearing_remote")
    if _TOKEN_MATERIAL.search(combined):
        _fail("token_bearing_effective_config")


def audit_effective_git_config() -> None:
    for _scope, key, value in _effective_entries():
        _audit_entry(key, value)

    remotes = subprocess.run(
        ("git", "remote"),
        check=False,
        capture_output=True,
        text=True,
    )
    if remotes.returncode != 0:
        _fail("remote_inventory_unreadable")
    for remote in remotes.stdout.splitlines():
        resolved = subprocess.run(
            ("git", "remote", "get-url", "--all", remote),
            check=False,
            capture_output=True,
            text=True,
        )
        if resolved.returncode != 0:
            _fail("resolved_remote_unreadable")
        if _TOKEN_MATERIAL.search(resolved.stdout):
            _fail("token_bearing_resolved_remote")


def main(argv: Sequence[str] | None = None) -> int:
    if argv:
        print("::error::git credential hygiene failed: unexpected_argument")
        return 1
    try:
        audit_effective_git_config()
    except CredentialHygieneFailure as error:
        print(f"::error::git credential hygiene failed: {error}")
        return 1
    print("credential_hygiene=PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
