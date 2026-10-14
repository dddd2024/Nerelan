"""Claude Code status line that records the account's official usage windows.

Claude Code runs the configured ``statusLine`` command with a JSON object on stdin. Its
``rate_limits`` field carries the subscription's official windows, the same figures the
Claude app shows under "Plan usage limits":

    {"rate_limits": {"five_hour": {"used_percentage": 88, "resets_at": ...},
                     "seven_day": {"used_percentage": 75, "resets_at": ...}}}

This script appends exactly those numbers (window, percent, reset time, when seen) to a
small local file that Nerelan reads, and prints a one-line summary for the status bar. It
never reads credentials, never calls the network and never fails the status line.

The file is standard-library only, so ``install`` copies it out of the repository:

    python -m reverse_agent.model_access.claude_statusline install
    python -m reverse_agent.model_access.claude_statusline uninstall
"""

from __future__ import annotations

from datetime import datetime, timezone
import json
import os
from pathlib import Path
import shutil
import sys
import time

MAX_STDIN = 1024 * 1024
MAX_LOG_BYTES = 512 * 1024
WINDOWS = {"five_hour": "five_hour", "seven_day": "weekly"}


def state_dir() -> Path:
    base = os.environ.get("LOCALAPPDATA") or os.environ.get("XDG_STATE_HOME") or str(Path.home() / ".local" / "state")
    return Path(base) / "Nerelan"


def log_path() -> Path:
    return state_dir() / "claude_rate_limits.jsonl"


def _epoch(value):
    if isinstance(value, bool):
        return None
    if isinstance(value, (int, float)) and 0 < value < 10**11:
        return int(value)
    if isinstance(value, (int, float)) and 10**11 <= value < 10**14:  # milliseconds
        return int(value // 1000)
    if isinstance(value, str) and len(value) <= 40:
        try:
            return int(datetime.fromisoformat(value.replace("Z", "+00:00")).timestamp())
        except ValueError:
            return None
    return None


def extract(payload) -> list[dict]:
    """Allowlisted official windows from a status line payload."""
    limits = payload.get("rate_limits") if isinstance(payload, dict) else None
    if not isinstance(limits, dict):
        return []
    now = int(time.time())
    records = []
    for key, window in WINDOWS.items():
        item = limits.get(key)
        if not isinstance(item, dict):
            continue
        used = item.get("used_percentage")
        if isinstance(used, bool) or not isinstance(used, (int, float)) or not 0 <= used <= 100:
            continue
        records.append({"at": now, "window": window, "used_percent": float(used),
                        "resets_at": _epoch(item.get("resets_at"))})
    return records


def record(records: list[dict], path: Path | None = None) -> None:
    if not records:
        return
    path = path or log_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    try:
        if path.stat().st_size > MAX_LOG_BYTES:  # keep the newest half, replaced in one step
            lines = path.read_bytes().splitlines()
            temp = path.with_name(f"{path.name}.{os.getpid()}.tmp")
            temp.write_bytes(b"\n".join(lines[len(lines) // 2:]) + b"\n")
            os.replace(temp, path)
    except OSError:
        pass
    with path.open("a", encoding="utf-8") as handle:
        for item in records:
            handle.write(json.dumps(item, separators=(",", ":")) + "\n")


def summary(records: list[dict]) -> str:
    labels = {"five_hour": "5h", "weekly": "7d"}
    parts = [f"{labels[r['window']]} {round(r['used_percent'])}%" for r in records]
    return " · ".join(parts) if parts else "Claude"


def run_statusline() -> int:
    """Always prints a line and returns 0: a status line must never break Claude Code."""
    line = "Claude"
    try:
        try:
            payload = json.loads(sys.stdin.read(MAX_STDIN) or "{}")
        except (ValueError, OSError, RecursionError):
            payload = {}
        if not isinstance(payload, dict):
            payload = {}
        records: list[dict] = []
        try:
            records = extract(payload)
            record(records)
        except Exception:  # noqa: BLE001 - recording is best effort
            pass
        model = payload.get("model")
        name = model.get("display_name") if isinstance(model, dict) else None
        line = summary(records)
        if isinstance(name, str) and name:
            line = f"{name[:60]} · {line}"
    except Exception:  # noqa: BLE001
        pass
    try:
        sys.stdout.reconfigure(encoding="utf-8")  # a piped stdout on Windows defaults to the ANSI code page
    except (AttributeError, ValueError):
        pass
    try:
        print(line)
    except Exception:  # noqa: BLE001
        pass
    return 0


def settings_path() -> Path:
    return Path(os.environ.get("CLAUDE_CONFIG_DIR") or Path.home() / ".claude") / "settings.json"


def _load(path: Path) -> dict:
    if not path.exists():
        return {}
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise SystemExit("settings.json is not a JSON object; not changed")
    return data


def _write(path: Path, data: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    backup = path.with_name(path.name + ".nerelan-backup")
    if path.exists() and not backup.exists():  # keep the Owner's original, not a later Nerelan write
        shutil.copy2(path, backup)
    temp = path.with_name(path.name + ".nerelan-tmp")
    temp.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    os.replace(temp, path)


def _ours(status_line) -> bool:
    command = status_line.get("command") if isinstance(status_line, dict) else None
    target = str(state_dir() / "claude_statusline.py")
    return isinstance(command, str) and command.rstrip().rstrip('"').endswith(target)


def install() -> int:
    target = state_dir() / "claude_statusline.py"
    path = settings_path()
    data = _load(path)
    current = data.get("statusLine")
    if current and not _ours(current):
        print(f"statusLine already set to {json.dumps(current)}; not replaced", file=sys.stderr)
        return 1
    target.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(__file__, target)
    data["statusLine"] = {"type": "command", "command": f'"{sys.executable}" "{target}"', "padding": 0}
    _write(path, data)
    print(f"installed: {path} statusLine -> {target}; records to {log_path()}")
    return 0


def uninstall() -> int:
    path = settings_path()
    data = _load(path)
    if not _ours(data.get("statusLine")):
        print("Nerelan statusLine not installed; nothing changed")
        return 0
    data.pop("statusLine", None)
    _write(path, data)
    print(f"removed Nerelan statusLine from {path}")
    return 0


if __name__ == "__main__":
    command = sys.argv[1] if len(sys.argv) > 1 else ""
    raise SystemExit(install() if command == "install" else uninstall() if command == "uninstall"
                     else run_statusline())
