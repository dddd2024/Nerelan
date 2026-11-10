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
  ``"supervisor_activation": true``. The host reads that when it starts: turning it
  on needs a host restart, turning it off works at once. Strict ``terminal``
  confirmation refuses activation.
- Bounds are never in the request. A request names a preset; the host computes the
  window from it, so a supervisor gets the trial/day/week bounds (as the Owner's
  ``owner_window_presets.json`` may have changed them) or nothing.
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
TAKEN_GRACE_SECONDS = 900.0
_ID = re.compile(r"[a-z0-9]{8,32}")
_REQUEST, _RESULT = ".request.json", ".result.json"
_FIELDS = {
    "draft": {"action", "text", "repository", "preset"},
    "preflight": {"action", "goal_ids", "preset"},
    "activate": {"action", "goal_ids", "preset", "card_digest", "requested_by"},
}


def _write_atomic(path: Path, document: Any) -> None:
    temporary = path.with_name(f"{path.name}.{secrets.token_hex(4)}.tmp")
    try:
        temporary.write_text(json.dumps(document, ensure_ascii=False, sort_keys=True), encoding="utf-8")
        os.replace(temporary, path)
    except OSError:
        try:
            temporary.unlink()
        except OSError:
            pass
        raise


class SupervisorRequests:
    """Polls the request directory and answers each request once."""

    def __init__(self, host: Any, *, poll_seconds: float = POLL_SECONDS) -> None:
        self._host = host
        self._poll_seconds = poll_seconds
        self._stop: threading.Event | None = None
        self._thread: threading.Thread | None = None
        self._enabled_at_start: bool | None = None

    def directory(self) -> Path | None:
        state_path = getattr(self._host._store, "_state_path", None)
        return Path(state_path).parent / DIRECTORY if state_path else None

    def _latched(self) -> bool:
        """The Owner's switch as it was when this watcher first looked (host start).

        A task running later as the same OS user cannot turn the feature on by
        editing the settings file; the live check in the admission can still turn it off.
        """
        if self._enabled_at_start is None:
            try:
                self._enabled_at_start = self._host._owner_window_admission.supervisor_enabled()
            except TaskStoreError:
                self._enabled_at_start = False
        return self._enabled_at_start

    def start(self) -> None:
        if self._thread is not None or self.directory() is None:
            return
        self._latched()
        # One event per thread: a thread that outlived stop() can never be revived by a later start().
        self._stop = stop = threading.Event()
        self._thread = threading.Thread(target=self._run, args=(stop,), name="supervisor-requests", daemon=True)
        self._thread.start()

    def stop(self) -> None:
        stop, self._stop = self._stop, None
        thread, self._thread = self._thread, None
        if stop is not None:
            stop.set()
        if thread is not None:
            thread.join(timeout=5)

    def _run(self, stop: threading.Event) -> None:
        while not stop.wait(self._poll_seconds):
            try:
                self.poll_once()
            except Exception:  # noqa: BLE001 - the watcher must outlive one bad poll
                LOG.exception("supervisor request poll failed")

    def poll_once(self) -> int:
        """Answer the waiting requests; returns how many were answered."""
        directory = self.directory()
        if directory is None or not directory.is_dir():
            return 0
        answered = taken = 0
        for path in sorted(directory.glob(f"*{_REQUEST}")):
            if taken >= MAX_REQUESTS_PER_POLL:
                break
            name = path.name[:-len(_REQUEST)]
            try:
                if path.is_symlink() or not path.is_file():
                    continue
                raw = path.read_bytes() if path.stat().st_size <= MAX_REQUEST_BYTES else None
                path.unlink()  # before acting: a request runs at most once
            except OSError:
                continue
            taken += 1
            if not _ID.fullmatch(name):
                continue
            answer = self._answer(raw)
            try:
                _write_atomic(directory / f"{name}{_RESULT}", answer)
                answered += 1
            except OSError:
                # The action may already have happened (a window may be active): say so in the log.
                LOG.exception("supervisor request %s: result not written; outcome ok=%s action=%s",
                              name, answer.get("ok"), answer.get("action"))
        if answered:
            self._prune(directory)
        return answered

    @staticmethod
    def _prune(directory: Path) -> None:
        dated = []
        for item in directory.glob(f"*{_RESULT}"):
            try:
                dated.append((item.stat().st_mtime, item))
            except OSError:
                continue
        for _, stale in sorted(dated, key=lambda pair: pair[0])[:-KEPT_RESULTS]:
            try:
                stale.unlink()
            except OSError:
                pass

    def _answer(self, raw: bytes | None) -> dict[str, Any]:
        action = ""
        try:
            if raw is None:
                raise TaskStoreError("supervisor_request_too_large")
            try:
                payload = json.loads(raw.decode("utf-8-sig"))
            except (ValueError, UnicodeDecodeError) as exc:
                raise TaskStoreError("supervisor_request_invalid") from exc
            if not isinstance(payload, dict) or payload.get("action") not in _FIELDS:
                raise TaskStoreError("supervisor_request_invalid")
            action = payload["action"]
            if set(payload) - _FIELDS[action]:
                raise TaskStoreError("supervisor_request_invalid")
            admission = self._host._owner_window_admission
            if not self._latched() or not admission.supervisor_enabled():
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
        except Exception:  # noqa: BLE001 - reported as a fixed code, details in the host log
            LOG.exception("supervisor request failed (action=%s)", action)
            return {"ok": False, "action": action, "error": "supervisor_request_failed"}


def submit(state_dir: str | Path, payload: dict[str, Any], *, wait_seconds: float = 300.0,
           poll_seconds: float = 1.0, taken_grace_seconds: float = TAKEN_GRACE_SECONDS) -> dict[str, Any]:
    """Write one request beside the task store and wait for the host's answer.

    If nothing answers in time the request is withdrawn. If the host has already
    taken it, it may still act: this keeps waiting for a bounded grace period and,
    failing that, says the outcome is pending and where the result will appear,
    never that nothing happened.
    """
    root = Path(state_dir)
    if not root.is_dir():
        return {"ok": False, "action": payload.get("action", ""), "error": "supervisor_state_dir_missing"}
    directory = root / DIRECTORY
    directory.mkdir(exist_ok=True)
    name = secrets.token_hex(8)
    request, result = directory / f"{name}{_REQUEST}", directory / f"{name}{_RESULT}"
    _write_atomic(request, payload)

    def answer() -> dict[str, Any] | None:
        try:
            return {**json.loads(result.read_text(encoding="utf-8")), "request_id": name}
        except (OSError, ValueError):
            return None

    def wait(seconds: float) -> dict[str, Any] | None:
        deadline = time.monotonic() + seconds
        while True:
            found = answer()
            if found is not None or time.monotonic() >= deadline:
                return found
            time.sleep(poll_seconds)

    found = wait(wait_seconds)
    if found is not None:
        return found
    try:
        request.unlink()
        withdrawn = True
    except FileNotFoundError:
        withdrawn = False  # the host took it and may be acting on it now
    except OSError:
        if request.exists():  # still waiting and we could not remove it: it may run later
            return {"ok": False, "action": payload.get("action", ""), "request_id": name,
                    "error": "supervisor_request_not_withdrawn", "request_path": str(request)}
        withdrawn = False
    if withdrawn:
        return answer() or {"ok": False, "action": payload.get("action", ""), "request_id": name,
                            "error": "supervisor_request_unanswered"}
    return wait(taken_grace_seconds) or {
        "ok": False, "action": payload.get("action", ""), "request_id": name,
        "error": "supervisor_request_taken_result_pending", "result_path": str(result)}


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
