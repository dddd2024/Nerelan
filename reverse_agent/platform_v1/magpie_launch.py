"""Owner-configured Magpie lifecycle. Never accesses gateway configuration or login files."""
from __future__ import annotations

from collections import deque
from collections.abc import Callable
from datetime import datetime, timezone
import json
import os
import subprocess
import threading
import time
from typing import Any
from urllib.request import Request

from ..model_access.http_safe import urlopen
from ..model_access.magpie import validate_settings


def probe_models(base_url: str, timeout: float = 2.0) -> int:
    request = Request(base_url + "/v1/models", headers={"Authorization": "Bearer magpie-nerelan"}, method="GET")
    with urlopen(request, timeout=timeout) as response:
        if response.status != 200:
            raise ValueError("models_http_error")
        data = json.loads(response.read(1_048_577))
    models = data.get("data") if isinstance(data, dict) else None
    if not isinstance(models, list) or any(not isinstance(m, dict) or not isinstance(m.get("id"), str) for m in models):
        raise ValueError("invalid_models_response")
    return len(models)


def process_running(executable: str) -> bool:
    """Compare full image paths, never just executable names. Fail closed off Windows."""
    if os.name != "nt":
        raise OSError("Magpie process inspection requires Windows")
    import ctypes
    from ctypes import wintypes
    kernel = ctypes.WinDLL("kernel32", use_last_error=True)
    psapi = ctypes.WinDLL("psapi", use_last_error=True)
    kernel.OpenProcess.argtypes = [wintypes.DWORD, wintypes.BOOL, wintypes.DWORD]
    kernel.OpenProcess.restype = wintypes.HANDLE
    kernel.CloseHandle.argtypes = [wintypes.HANDLE]
    kernel.QueryFullProcessImageNameW.argtypes = [wintypes.HANDLE, wintypes.DWORD, wintypes.LPWSTR, ctypes.POINTER(wintypes.DWORD)]
    ids = (wintypes.DWORD * 65536)()
    used = wintypes.DWORD()
    if not psapi.EnumProcesses(ids, ctypes.sizeof(ids), ctypes.byref(used)) or used.value >= ctypes.sizeof(ids):
        raise OSError("process_inspection_failed")
    target = os.path.normcase(os.path.realpath(executable))
    for pid in ids[:used.value // ctypes.sizeof(wintypes.DWORD)]:
        handle = kernel.OpenProcess(0x1000, False, pid)
        if not handle:
            continue
        try:
            name = ctypes.create_unicode_buffer(32768)
            size = wintypes.DWORD(len(name))
            if kernel.QueryFullProcessImageNameW(handle, 0, name, ctypes.byref(size)):
                if os.path.normcase(os.path.realpath(name.value)) == target:
                    return True
        finally:
            kernel.CloseHandle(handle)
    return False


def launch_process(executable: str) -> None:
    subprocess.Popen([executable], stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL,
                     stderr=subprocess.DEVNULL, close_fds=True,
                     creationflags=subprocess.DETACHED_PROCESS | subprocess.CREATE_NEW_PROCESS_GROUP)


class MagpieLaunch:
    def __init__(
        self,
        settings: Callable[[], dict[str, Any]],
        *,
        probe: Callable[[str, float], int] = probe_models,
        launcher: Callable[[str], None] = launch_process,
        running: Callable[[str], bool] = process_running,
        clock: Callable[[], float] = time.monotonic,
        sleep: Callable[[float], object] = time.sleep,
    ) -> None:
        self.settings = settings
        self.probe, self.launcher, self.running = probe, launcher, running
        self.clock = clock
        self.sleep = sleep
        self._restarts: deque[float] = deque()
        self._initial = True
        self._lock = threading.RLock()
        self._stop = threading.Event()
        if sleep is time.sleep:
            self.sleep = self._stop.wait
        self._thread: threading.Thread | None = None
        self._status = {"status": "MAGPIE_DISABLED", "reason": "", "last_probe_at": None, "model_count": 0}

    def status(self) -> dict[str, Any]:
        return dict(self._status)

    def _healthy(self, config: dict[str, Any], timeout: float = 2.0) -> bool:
        self._status["last_probe_at"] = datetime.now(timezone.utc).isoformat()
        try:
            count = self.probe(config["base_url"], timeout)
            if type(count) is not int or count < 0:
                raise ValueError("invalid_model_count")
            self._status["model_count"] = count
            return True
        except Exception:
            self._status["model_count"] = 0
            return False

    def check(self) -> None:
        with self._lock:
            config = self.settings()
            if not config["enabled"]:
                self._status.update(status="MAGPIE_DISABLED", reason="", model_count=0)
                return
            if self._healthy(config):
                if self._status["status"] != "STARTED":
                    self._status.update(status="ALREADY_RUNNING", reason="")
                self._initial = False
                return
            self._status.update(status="UNREACHABLE", reason="")
            try:
                # An existing process with a dead port must never be duplicated.
                if self.running(config["executable"]):
                    self._initial = False
                    self._status["reason"] = "process_running_but_unreachable"
                    return
                now = self.clock()
                while self._restarts and now - self._restarts[0] >= 3600:
                    self._restarts.popleft()
                if not self._initial and len(self._restarts) >= 3:
                    self._status["reason"] = "restart_budget_exhausted: 3 restarts per hour"
                    return
                if not self._initial:
                    self._restarts.append(now)
                self._initial = False
                config = validate_settings(config)
                self.launcher(config["executable"])
                deadline = self.clock() + 30
                while not self._stop.is_set():
                    remaining = deadline - self.clock()
                    if remaining <= 0:
                        break
                    if self._healthy(config, min(2.0, remaining)):
                        self._status.update(status="STARTED", reason="")
                        return
                    self.sleep(min(1.0, max(0, deadline - self.clock())))
                self._status.update(status="START_FAILED", reason="health_timeout")
            except Exception as exc:
                # Keep exception messages (which may contain local details) out of public status.
                self._initial = False
                self._status.update(status="START_FAILED", reason=type(exc).__name__)

    def start(self) -> None:
        self._stop.clear()
        self.check()

        def watch() -> None:
            while not self._stop.wait(60):
                self.check()
        self._thread = threading.Thread(target=watch, name="magpie-watch", daemon=True)
        self._thread.start()

    def stop(self) -> None:
        # Only stop our observer, never the Owner's Magpie process.
        self._stop.set()
        if self._thread:
            self._thread.join(timeout=3)
