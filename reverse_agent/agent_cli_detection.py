"""Installed agent CLI discovery shared by the launcher and trusted host.

Discovery only checks executable files; it never starts a CLI or inspects login
state. Windows includes npm shims even when PATHEXT omits their extensions.
"""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Mapping


AGENT_CLI_COMMANDS = {"opencode": "opencode", "codex": "codex", "claude_code": "claude"}


def detect_agent_clis(
    *, path: str | None = None, pathext: str | None = None,
    windows: bool | None = None, cwd: str | Path | None = None,
) -> Mapping[str, str]:
    """Return installed executor IDs and paths, using PATH then cwd on Windows.

    Explicit search inputs let tests use an isolated filesystem without depending
    on the developer's installed tools. POSIX requires an executable file.
    """
    windows = os.name == "nt" if windows is None else windows
    path = os.environ.get("PATH", "") if path is None else path
    directories = [Path(part.strip('"')) for part in path.split(";" if windows else os.pathsep) if part.strip()]
    extensions = [""]
    if windows:
        pathext = os.environ.get("PATHEXT", "") if pathext is None else pathext
        extensions = [ext if ext.startswith(".") else f".{ext}"
                      for ext in pathext.split(";") if ext.strip()]
        extensions = list(dict.fromkeys(ext.lower() for ext in [*extensions, ".cmd", ".ps1", ".bat", ".exe", ".com", ""]))
        directories.append(Path.cwd() if cwd is None else Path(cwd))
    found = {}
    for executor_id, command in AGENT_CLI_COMMANDS.items():
        for directory in directories:
            candidate = next((directory / f"{command}{ext}" for ext in extensions
                              if (directory / f"{command}{ext}").is_file()
                              and (windows or os.access(directory / f"{command}{ext}", os.X_OK))), None)
            if candidate is not None:
                found[executor_id] = str(candidate.resolve())
                break
    return found


if __name__ == "__main__":
    print(json.dumps(detect_agent_clis()))
