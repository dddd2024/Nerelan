"""Supervisor requests served by the running host (Owner decision 2026-11-10).

A supervising agent on the Owner's machine can ask the running host to draft Goals
from one sentence, run the Owner-window preflight, and activate a window, without
the launcher's client session and without a terminal:

    python -m reverse_agent.platform_v1.supervisor_requests --state-dir DIR draft \
        --text "#1411 #1412" --repository owner/repo --preset day
    python -m reverse_agent.platform_v1.supervisor_requests --state-dir DIR preflight \
        --preset day --goal G1 --goal G2
    python -m reverse_agent.platform_v1.supervisor_requests --state-dir DIR activate \
        --preset day --goal G1 --goal G2 --card-digest <from preflight>

The command writes ``<id>.request.json`` into ``supervisor_requests/`` beside the task
store and waits for ``<id>.result.json``. The host removes a request before acting on
it, so a request runs at most once.

What it is and is not:

- Off unless the Owner's ``owner_window_settings.json`` says
  ``"supervisor_activation": true``. Strict ``terminal`` confirmation also refuses it.
- Bounds are never in the request. A request names a preset; the host computes the
  window from it, so a supervisor gets the trial/day/week bounds or nothing.
- Activation runs the same admission as the confirmation card: the digest of the
  preflight must match the scope read now, one atomic commit, one receipt per Goal.
  The receipt records that a supervisor asked, and who it said it was.
- It authenticates nobody. Any process running as this OS user can write the file;
  the Owner accepted that when turning the setting on.
"""
from __future__ import annotations

import argparse
import json
import logging
import os
from pathlib import Path
import re
import secrets
import sys
import threading
import time
from typing import Any

from .autonomy import window_to_dict
from .run_store import TaskStoreError

LOG = logging.getLogger(__name__)
DIRECTORY = "supervisor_requests"
POLL_SECONDS = 3.0
MAX_REQUEST_BYTES = 64 * 1024
MAX_REQUESTS_PER_POLL = 20
KEPT_RESULTS = 50
_ID = re.compile(r"[a-z0-9]{8,32}")
_REQUEST, _RESULT = ".request.json", ".result.json"
_FIELDS = {
    "draft": {"action", "text", "repository", "preset"},
    "preflight": {"action", "goal_ids", "preset"},
    "activate": {"action", "goal_ids", "preset", "card_digest", "requested_by"},
}


def _write_atomic(path: Path, document: Any) -> None:
    temporary = path.with_name(f"{path.name}.{secrets.token_hex(4)}.tmp")
    temporary.write_text(json.dumps(document, ensure_ascii=False, sort_keys=True), encoding="utf-8")
    os.replace(temporary, path)


class SupervisorRequests:
    """Polls the request directory and answers each request once."""

    def __init__(self, host: Any, *, poll_seconds: float = POLL_SECONDS) -> None:
        self._host = host
        self._poll_seconds = poll_seconds
        self._stop = threading.Event()
        self._thread: threading.Thread | None = None

    def directory(self) -> Path | None:
        state_path = getattr(self._host._store, "_state_path", None)
        return Path(state_path).parent / DIRECTORY if state_path else None

    def start(self) -> None:
        if self._thread is not None or self.directory() is None:
            return
        self._stop.clear()
        self._thread = threading.Thread(target=self._run, name="supervisor-requests", daemon=True)
        self._thread.start()

    def stop(self) -> None:
        self._stop.set()
        thread, self._thread = self._thread, None
        if thread is not None:
            thread.join(timeout=5)

    def _run(self) -> None:
        while not self._stop.wait(self._poll_seconds):
            try:
                self.poll_once()
            except Exception:  # noqa: BLE001 - the watcher must outlive one bad poll
                LOG.exception("supervisor request poll failed")

    def poll_once(self) -> int:
        """Answer the waiting requests; returns how many were answered."""
        directory = self.directory()
        if directory is None or not directory.is_dir():
            return 0
        answered = 0
        for path in sorted(directory.glob(f"*{_REQUEST}"))[:MAX_REQUESTS_PER_POLL]:
            name = path.name[:-len(_REQUEST)]
            try:
                if path.is_symlink() or not path.is_file():
                    continue
                raw = path.read_bytes() if path.stat().st_size <= MAX_REQUEST_BYTES else None
                path.unlink()  # before acting: a request runs at most once
            except OSError:
                continue
            if not _ID.fullmatch(name):
                continue
            _write_atomic(directory / f"{name}{_RESULT}", self._answer(raw))
            answered += 1
        if answered:
            results = sorted(directory.glob(f"*{_RESULT}"), key=lambda item: item.stat().st_mtime)
            for stale in results[:-KEPT_RESULTS]:
                try:
                    stale.unlink()
                except OSError:
                    pass
        return answered

    def _answer(self, raw: bytes | None) -> dict[str, Any]:
        action = ""
        try:
            if raw is None:
                raise TaskStoreError("supervisor_request_too_large")
            payload = json.loads(raw.decode("utf-8"))
            if not isinstance(payload, dict) or payload.get("action") not in _FIELDS:
                raise TaskStoreError("supervisor_request_invalid")
            action = payload["action"]
            if set(payload) - _FIELDS[action]:
                raise TaskStoreError("supervisor_request_invalid")
            admission = self._host._owner_window_admission
            if not admission.supervisor_enabled():
                raise TaskStoreError("owner_window_supervisor_activation_disabled")
            if action == "draft":
                text, repository, preset = (payload.get(key, "") for key in ("text", "repository", "preset"))
                if not all(isinstance(value, str) for value in (text, repository, preset)):
                    raise TaskStoreError("supervisor_request_invalid")
                result = self._host._quick_start().draft(text, repository, preset=preset)
            elif action == "preflight":
                goal_ids = payload.get("goal_ids")
                result = admission.preflight(goal_ids, **admission.supervisor_request(goal_ids, payload.get("preset")))
            else:
                result = window_to_dict(admission.admit_from_supervisor(
                    payload.get("goal_ids"), preset=payload.get("preset"),
                    card_digest=payload.get("card_digest"), requested_by=payload.get("requested_by", "")))
            return {"ok": True, "action": action, "result": result}
        except TaskStoreError as exc:
            return {"ok": False, "action": action, "error": str(exc)}
        except (ValueError, UnicodeDecodeError):
            return {"ok": False, "action": action, "error": "supervisor_request_invalid"}
        except Exception:  # noqa: BLE001 - reported as a fixed code, details in the host log
            LOG.exception("supervisor request failed")
            return {"ok": False, "action": action, "error": "supervisor_request_failed"}


def submit(state_dir: str | Path, payload: dict[str, Any], *, wait_seconds: float = 300.0,
           poll_seconds: float = 1.0) -> dict[str, Any]:
    """Write one request beside the task store and wait for the host's answer."""
    directory = Path(state_dir) / DIRECTORY
    directory.mkdir(parents=True, exist_ok=True)
    name = secrets.token_hex(8)
    request, result = directory / f"{name}{_REQUEST}", directory / f"{name}{_RESULT}"
    _write_atomic(request, payload)
    deadline = time.monotonic() + wait_seconds
    while time.monotonic() < deadline:
        if result.is_file():
            return json.loads(result.read_text(encoding="utf-8"))
        time.sleep(poll_seconds)
    try:
        request.unlink()  # unanswered: withdraw it so it cannot run later unobserved
    except OSError:
        pass
    if result.is_file():
        return json.loads(result.read_text(encoding="utf-8"))
    return {"ok": False, "action": payload.get("action", ""), "error": "supervisor_request_unanswered"}


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--state-dir", default=os.environ.get("REVERSE_AGENT_TASK_DB_DIR", ""),
                        help="directory of the host's task store (default: REVERSE_AGENT_TASK_DB_DIR)")
    parser.add_argument("--wait", type=float, default=300.0, help="seconds to wait for the host")
    actions = parser.add_subparsers(dest="action", required=True)
    draft = actions.add_parser("draft")
    draft.add_argument("--text", required=True)
    draft.add_argument("--repository", required=True)
    draft.add_argument("--preset", default="")
    for name in ("preflight", "activate"):
        sub = actions.add_parser(name)
        sub.add_argument("--preset", required=True)
        sub.add_argument("--goal", action="append", required=True, dest="goal_ids")
        if name == "activate":
            sub.add_argument("--card-digest", required=True)
            sub.add_argument("--requested-by", default="")
    args = parser.parse_args(argv)
    if not args.state_dir:
        parser.error("--state-dir or REVERSE_AGENT_TASK_DB_DIR is required")
    payload = {key: value for key, value in vars(args).items() if key not in {"state_dir", "wait"}}
    answer = submit(args.state_dir, payload, wait_seconds=args.wait)
    sys.stdout.write(json.dumps(answer, ensure_ascii=False, indent=1) + "\n")
    return 0 if answer.get("ok") else 1


if __name__ == "__main__":
    raise SystemExit(main())
